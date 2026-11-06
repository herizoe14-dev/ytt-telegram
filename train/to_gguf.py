"""Convertit un modèle affiné (format Hugging Face) en GGUF quantifié.

Architectures prises en charge : llama (SmolLM2) et qwen2 (Qwen2.5). Les
métadonnées (tokenizer, architecture, modèle de chat…) sont recopiées depuis un
GGUF de référence du même modèle de base ; seuls les poids changent. La
quantification est faite par llama.cpp (via llama-cpp-python).

Avec --split-mb, le fichier est découpé en morceaux (…-00001-of-0000N.gguf) pour
passer sous la limite de 100 Mo par fichier de GitHub ; llama.cpp les recharge
automatiquement quand on lui donne le premier morceau.

    python train/to_gguf.py <dossier_hf> <sortie.gguf> --ref <référence.gguf> [--split-mb 95] [--tied]
"""
import argparse
import os
import tempfile

import numpy as np
from gguf import GGUFReader, GGUFValueType, GGUFWriter
from safetensors.torch import load_file

LAYER = {
    "input_layernorm": "attn_norm", "post_attention_layernorm": "ffn_norm",
    "self_attn.q_proj": "attn_q", "self_attn.k_proj": "attn_k", "self_attn.v_proj": "attn_v",
    "self_attn.o_proj": "attn_output",
    "mlp.gate_proj": "ffn_gate", "mlp.up_proj": "ffn_up", "mlp.down_proj": "ffn_down",
}
SKIP_KEYS = ("GGUF.", "general.file_type", "quantize.", "split.")


def permute(w, n_head):
    """Réordonne q/k comme llama.cpp pour l'architecture llama (RoPE)."""
    return w.reshape(n_head, 2, w.shape[0] // n_head // 2, *w.shape[1:]).swapaxes(1, 2).reshape(w.shape)


def gguf_name(hf):
    if hf == "model.embed_tokens.weight":
        return "token_embd.weight"
    if hf == "model.norm.weight":
        return "output_norm.weight"
    if hf == "lm_head.weight":
        return "output.weight"
    parts = hf.split(".")  # model.layers.N.<module...>.weight|bias
    return f"blk.{parts[2]}.{LAYER['.'.join(parts[3:-1])]}.{parts[-1]}"


def copy_metadata(r, w):
    for key, f in r.fields.items():
        if key.startswith(SKIP_KEYS) or key == "general.architecture":
            continue
        vtype = f.types[0]
        sub = f.types[-1] if vtype == GGUFValueType.ARRAY else None
        w.add_key_value(key, f.contents(), vtype, sub_type=sub)


def write_f16(hf_dir, out, ref, drop_output=False):
    r = GGUFReader(ref)
    arch = r.fields["general.architecture"].contents()
    n_head = int(r.fields[f"{arch}.attention.head_count"].contents())
    n_kv = int(r.fields[f"{arch}.attention.head_count_kv"].contents())
    ref_names = {t.name for t in r.tensors}
    if drop_output:  # poids liés : llama.cpp réutilise token_embd pour la sortie
        ref_names.discard("output.weight")
    w = GGUFWriter(out, arch=arch)
    copy_metadata(r, w)
    w.add_file_type(1)  # F16

    tensors = {k: v.float().numpy() for k, v in load_file(os.path.join(hf_dir, "model.safetensors")).items()}
    if "output.weight" in ref_names and "lm_head.weight" not in tensors:
        tensors["lm_head.weight"] = tensors["model.embed_tokens.weight"]  # poids liés, écrits à part
    if "output.weight" not in ref_names:
        tensors.pop("lm_head.weight", None)
    for name, t in tensors.items():
        if arch == "llama" and name.endswith("q_proj.weight"):
            t = permute(t, n_head)
        elif arch == "llama" and name.endswith("k_proj.weight"):
            t = permute(t, n_kv)
        w.add_tensor(gguf_name(name), t if t.ndim == 1 else t.astype(np.float16))
    missing = ref_names - {gguf_name(n) for n in tensors}
    if missing:
        raise SystemExit(f"tenseurs manquants : {sorted(missing)[:5]}")
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()


def quantize(src, dst, ftype="Q4_0", embd_type=None):
    import llama_cpp
    p = llama_cpp.llama_model_quantize_default_params()
    p.ftype = getattr(llama_cpp, f"LLAMA_FTYPE_MOSTLY_{ftype}")
    if embd_type:  # sinon llama.cpp garde l'embedding (qui sert aussi de sortie) en 8 bits
        p.token_embedding_type = getattr(llama_cpp, f"GGML_TYPE_{embd_type}")
    p.nthread = os.cpu_count() or 4
    if llama_cpp.llama_model_quantize(src.encode(), dst.encode(), p) != 0:
        raise SystemExit("échec de la quantification")


def split(src, out, max_mb):
    """Recopie un GGUF (déjà quantifié) en plusieurs morceaux de max_mb Mo au plus."""
    r = GGUFReader(src)
    arch = r.fields["general.architecture"].contents()
    w = GGUFWriter(out, arch=arch, split_max_size=int(max_mb * 1e6))
    copy_metadata(r, w)
    w.add_file_type(int(r.fields["general.file_type"].contents()))
    for t in r.tensors:
        if t.tensor_type.name in ("F32", "F16"):
            w.add_tensor(t.name, t.data)
        else:  # données quantifiées : tableau d'octets (lignes, octets par ligne)
            w.add_tensor(t.name, t.data, raw_dtype=t.tensor_type)
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("hf_dir")
    ap.add_argument("out")
    ap.add_argument("--ref", required=True, help="GGUF du modèle de base (pour les métadonnées)")
    ap.add_argument("--type", default="Q4_0")
    ap.add_argument("--split-mb", type=float, default=0, help="découpe en morceaux de cette taille (Mo)")
    ap.add_argument("--tied", action="store_true",
                    help="n'écrit pas output.weight (poids liés à token_embd) : fichier plus léger")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as d:
        f16 = os.path.join(d, "f16.gguf")
        write_f16(a.hf_dir, f16, a.ref, drop_output=a.tied)
        if a.split_mb:
            q = os.path.join(d, "q.gguf")
            quantize(f16, q, a.type, a.type if a.tied else None)
            split(q, a.out, a.split_mb)
        else:
            quantize(f16, a.out, a.type, a.type if a.tied else None)
    folder = os.path.dirname(os.path.abspath(a.out))
    stem = os.path.basename(a.out)[:-5]
    for f in sorted(os.listdir(folder)):
        if f.startswith(stem) and f.endswith(".gguf"):
            print(f"{f} : {os.path.getsize(os.path.join(folder, f)) / 1e6:.1f} Mo")
