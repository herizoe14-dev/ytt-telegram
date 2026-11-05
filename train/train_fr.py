"""Affine SmolLM2-135M-Instruct sur le jeu français (train/data_fr.jsonl), sur CPU.

Le modèle garde exactement la même architecture et le même nombre de paramètres :
une fois converti en GGUF Q4_0 (train/to_gguf.py), il pèse le même poids que
l'original (~92 Mo).

    pip install torch transformers safetensors
    python train/make_data_fr.py
    python train/train_fr.py --out build/alice-fr      # ~1 h sur 4 cœurs CPU
    python train/to_gguf.py build/alice-fr models/Alice-SmolLM2-135M-fr-Q4_0.gguf
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


def encode(tok, ex, system):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": ex["question"]}]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    full = prompt + ex["answer"] + "<|im_end|>\n"
    p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
    ids = tok(full, add_special_tokens=False)["input_ids"]
    labels = [-100] * len(p_ids) + ids[len(p_ids):]  # on n'apprend que la réponse
    return ids, labels


def batches(data, bs, rng):
    # regroupe des exemples de longueur proche pour limiter le remplissage
    idx = sorted(range(len(data)), key=lambda i: len(data[i][0]) + rng.random() * 8)
    chunks = [idx[i:i + bs] for i in range(0, len(idx), bs)]
    rng.shuffle(chunks)
    for c in chunks:
        n = max(len(data[i][0]) for i in c)
        ids = torch.full((len(c), n), 0, dtype=torch.long)
        lab = torch.full((len(c), n), -100, dtype=torch.long)
        att = torch.zeros((len(c), n), dtype=torch.long)
        for j, i in enumerate(c):
            x, y = data[i]
            ids[j, :len(x)], lab[j, :len(y)], att[j, :len(x)] = torch.tensor(x), torch.tensor(y), 1
        yield ids, lab, att


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HuggingFaceTB/SmolLM2-135M-Instruct")
    ap.add_argument("--data", default=str(Path(__file__).with_name("data_fr.jsonl")))
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=3)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--max-steps", type=int, default=0, help="arrêt anticipé (test de vitesse)")
    a = ap.parse_args()

    torch.manual_seed(0)
    rng = random.Random(0)
    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForCausalLM.from_pretrained(a.base, torch_dtype=torch.float32)
    model.train()

    rows = [json.loads(l) for l in open(a.data, encoding="utf-8")]
    # 3 fois sur 4 avec la consigne d'Alice (comme le bot), sinon la consigne par défaut du modèle
    data = [encode(tok, r, SYS_DIRECT if rng.random() < 0.75 else None) for r in rows]
    steps_per_epoch = math.ceil(len(data) / a.bs)
    total = a.max_steps or int(steps_per_epoch * a.epochs)
    warmup = max(1, total // 20)
    print(f"{len(data)} exemples, {total} pas, ~{sum(len(x) for x, _ in data) / len(data):.0f} jetons/exemple", flush=True)

    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / warmup) * 0.5 * (1 + math.cos(math.pi * min(1, s / total))))

    step, t0, run = 0, time.time(), []
    while step < total:
        for ids, lab, att in batches(data, a.bs, rng):
            loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
            run.append(loss.item()); step += 1
            if step % 20 == 0 or step == total:
                el = time.time() - t0
                print(f"pas {step}/{total}  perte {sum(run) / len(run):.3f}  "
                      f"{el / step:.1f} s/pas  reste ~{el / step * (total - step) / 60:.0f} min", flush=True)
                run = []
            if step >= total:
                break

    model.save_pretrained(a.out, safe_serialization=True)
    tok.save_pretrained(a.out)
    print("modèle enregistré dans", a.out)


if __name__ == "__main__":
    main()
