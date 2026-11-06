"""Affine un petit modèle (Qwen2.5-Instruct ou SmolLM2) sur les données françaises, sur CPU.

Le modèle garde la même architecture et le même nombre de paramètres. Avec --lora,
seuls de petits adaptateurs sont entraînés puis fusionnés dans le modèle.

Données : un ou plusieurs fichiers JSONL (--data a.jsonl b.jsonl:3000 pour n'en prendre
que 3 000 exemples tirés au hasard). Une ligne est soit une question et sa réponse
({"question", "answer", "system"?}), soit une conversation complète
({"messages": [...]}) : la perte porte alors sur toutes les réponses d'Alice.

Les longs entraînements peuvent être coupés et repris : avec --ckpt, l'état est
enregistré régulièrement et à l'arrêt (--stop-after-min) ; relancer la même commande
reprend là où on s'était arrêté.

Recette complète d'Alice : voir le README (section « Entraînement en français »).
"""
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from chat import SYS_DIRECT  # noqa: E402


def encode_messages(tok, msgs, max_len):
    """Jetons d'une conversation ; seules les réponses de l'assistant sont apprises."""
    msgs = [{"role": m["role"], "content": m["content"], **({"train": m["train"]} if "train" in m else {})} for m in msgs]
    text = tok.apply_chat_template(msgs, tokenize=False)
    spans = []
    for i, m in enumerate(msgs):
        if m["role"] == "assistant" and m.get("train", True):  # "train": false = dans le contexte, non appris
            start = len(tok.apply_chat_template(msgs[:i], tokenize=False, add_generation_prompt=True))
            end = len(tok.apply_chat_template(msgs[:i + 1], tokenize=False))
            spans.append((start, end))
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    ids = enc["input_ids"]
    if len(ids) > max_len:
        return None
    labels = [t if any(s <= off[0] < e for s, e in spans) else -100 for t, off in zip(ids, enc["offset_mapping"])]
    return ids, labels


def to_messages(row, rng):
    if "messages" in row:
        return row["messages"]
    # 3 fois sur 4 avec la consigne d'Alice (comme le bot), sinon la consigne par défaut du modèle
    system = row.get("system") or (SYS_DIRECT if rng.random() < 0.75 else None)
    return ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": row["question"]}, {"role": "assistant", "content": row["answer"]}]


def plan_batches(data, bs, epochs, rng):
    """Ordre complet des lots (déterministe), pour pouvoir reprendre un entraînement."""
    plan = []
    for _ in range(math.ceil(epochs)):
        idx = sorted(range(len(data)), key=lambda i: len(data[i][0]) + rng.random() * 8)
        chunks = [idx[i:i + bs] for i in range(0, len(idx), bs)]
        rng.shuffle(chunks)
        plan += chunks
    return plan[:int(math.ceil(len(data) / bs) * epochs)]


def collate(data, chunk):
    n = max(len(data[i][0]) for i in chunk)
    ids = torch.full((len(chunk), n), 0, dtype=torch.long)
    lab = torch.full((len(chunk), n), -100, dtype=torch.long)
    att = torch.zeros((len(chunk), n), dtype=torch.long)
    for j, i in enumerate(chunk):
        x, y = data[i]
        ids[j, :len(x)], lab[j, :len(y)], att[j, :len(x)] = torch.tensor(x), torch.tensor(y), 1
    return ids, lab, att


def load_rows(specs, rng):
    rows = []
    for spec in specs:
        path, _, n = spec.partition(":")
        r = [json.loads(l) for l in open(path, encoding="utf-8")]
        if n:
            r = rng.sample(r, min(int(n), len(r)))
        print(f"{path} : {len(r)} exemples", flush=True)
        rows += r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--data", nargs="+", default=[str(Path(__file__).with_name("data_fr.jsonl"))])
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=1)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-steps", type=int, default=0, help="arrêt anticipé (test de vitesse)")
    ap.add_argument("--max-len", type=int, default=1024, help="conversations plus longues ignorées (jetons)")
    ap.add_argument("--lora", type=int, default=32,
                    help="rang LoRA (0 = affinage complet). Avec LoRA, seuls de petits adaptateurs sont "
                         "entraînés, puis fusionnés dans le modèle : même taille, connaissances préservées")
    ap.add_argument("--micro", type=int, default=4, help="taille des micro-lots (0 = lot entier)")
    ap.add_argument("--grad-ckpt", action="store_true", help="recalcule les activations : moins de mémoire")
    ap.add_argument("--ckpt", help="dossier où enregistrer/reprendre l'entraînement")
    ap.add_argument("--save-every", type=int, default=50)
    ap.add_argument("--stop-after-min", type=float, default=0, help="s'arrête proprement après N minutes")
    a = ap.parse_args()

    torch.manual_seed(0)
    rng = random.Random(0)
    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForCausalLM.from_pretrained(a.base, torch_dtype=torch.float32)
    if a.lora:
        from peft import LoraConfig, get_peft_model
        model = get_peft_model(model, LoraConfig(
            r=a.lora, lora_alpha=2 * a.lora, lora_dropout=0.05, task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
        model.print_trainable_parameters()
    if a.grad_ckpt:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    model.train()

    rows = load_rows(a.data, rng)
    data = [d for d in (encode_messages(tok, to_messages(r, rng), a.max_len) for r in rows) if d]
    plan = plan_batches(data, a.bs, a.epochs, rng)
    total = a.max_steps or len(plan)
    warmup = max(1, total // 20)
    print(f"{len(data)} exemples, {total} pas, ~{sum(len(x) for x, _ in data) / len(data):.0f} jetons/exemple", flush=True)

    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / warmup) * 0.5 * (1 + math.cos(math.pi * min(1, s / total))))

    step = 0
    state_file = Path(a.ckpt) / "state.pt" if a.ckpt else None
    if state_file and state_file.exists():
        st = torch.load(state_file, weights_only=False)
        for p, v in zip(params, st["params"]):
            p.data.copy_(v)
        opt.load_state_dict(st["opt"]); sched.load_state_dict(st["sched"])
        step = st["step"]
        print(f"reprise au pas {step}/{total}", flush=True)

    def save():
        if state_file:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = state_file.with_suffix(".tmp")
            torch.save({"params": [p.detach().clone() for p in params], "opt": opt.state_dict(),
                        "sched": sched.state_dict(), "step": step}, tmp)
            tmp.replace(state_file)

    t0, done0, run = time.time(), step, []
    while step < total:
        ids, lab, att = collate(data, plan[step])
        # micro-lots : même résultat qu'un lot complet, avec beaucoup moins de mémoire
        # (le vocabulaire de Qwen fait 152 000 mots : les scores de sortie sont lourds)
        n_tok = (lab[:, 1:] != -100).sum().item()
        loss = 0.0
        for i in range(0, len(ids), a.micro or len(ids)):
            sl = slice(i, i + (a.micro or len(ids)))
            k = (lab[sl, 1:] != -100).sum().item()
            if not k:
                continue
            part = model(input_ids=ids[sl], attention_mask=att[sl], labels=lab[sl]).loss * (k / n_tok)
            part.backward()
            loss += part.detach()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step(); sched.step(); opt.zero_grad()
        run.append(float(loss)); step += 1
        el = time.time() - t0
        if step % 20 == 0 or step == total:
            per = el / (step - done0)
            print(f"pas {step}/{total}  perte {sum(run) / len(run):.3f}  {per:.1f} s/pas  "
                  f"reste ~{per * (total - step) / 60:.0f} min", flush=True)
            run = []
        if step % a.save_every == 0:
            save()
        if a.stop_after_min and el > a.stop_after_min * 60 and step < total:
            save()
            print(f"arrêt après {el / 60:.0f} min au pas {step}/{total} : relancer la même commande pour reprendre",
                  flush=True)
            return

    save()
    if a.lora:
        model = model.merge_and_unload()  # adaptateurs fusionnés : modèle standard, même taille
    model.save_pretrained(a.out, safe_serialization=True)
    tok.save_pretrained(a.out)
    print("modèle enregistré dans", a.out)


if __name__ == "__main__":
    main()
