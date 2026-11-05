"""Convertit un SmolLM2 (format Hugging Face) en GGUF Q4_0, même taille que l'original.

Les métadonnées (tokenizer, architecture, modèle de chat…) sont recopiées depuis
le GGUF d'Alice du dépôt ; seuls les poids changent. La quantification est
faite par llama.cpp (via llama-cpp-python).

    python train/to_gguf.py <dossier_hf> <sortie.gguf> [--ref models/....gguf]
"""
import argparse
import os
import tempfile

import numpy as np
from gguf import GGUFReader, GGUFWriter, GGUFValueType
from safetensors.torch import load_file

# Métadonnées identiques à celles du modèle d'origine (recopiées lors de la conversion)
REF = os.path.join(os.path.dirname(__file__), "..", "models", "Alice-SmolLM2-135M-fr-Q4_0.gguf")
LAYER = {
    "input_layernorm": "attn_norm", "post_attention_layernorm": "ffn_norm",
    "self_attn.q_proj": "attn_q", "self_attn.k_proj": "attn_k", "self_attn.v_proj": "attn_v",
    "self_attn.o_proj": "attn_output",
    "mlp.gate_proj": "ffn_gate", "mlp.up_proj": "ffn_up", "mlp.down_proj": "ffn_down",
}
SKIP_KEYS = ("GGUF.", "general.file_type", "quantize.")


def permute(w, n_head):
    """Réordonne q/k comme llama.cpp (RoPE en moitiés -> paires entrelacées)."""
    return w.reshape(n_head, 2, w.shape[0] // n_head // 2, *w.shape[1:]).swapaxes(1, 2).reshape(w.shape)


def gguf_name(hf):
    if hf == "model.embed_tokens.weight":
        return "token_embd.weight"
    if hf == "model.norm.weight":
        return "output_norm.weight"
    parts = hf.split(".")  # model.layers.N.<module...>.weight
    return f"blk.{parts[2]}.{LAYER['.'.join(parts[3:-1])]}.weight"


def write_f16(hf_dir, out, ref):
    r = GGUFReader(ref)
    n_head = int(r.fields["llama.attention.head_count"].contents())
    n_kv = int(r.fields["llama.attention.head_count_kv"].contents())
    w = GGUFWriter(out, arch="llama")
    for key, f in r.fields.items():
        if key.startswith(SKIP_KEYS) or key == "general.architecture":
            continue
        vtype = f.types[0]
        sub = f.types[-1] if vtype == GGUFValueType.ARRAY else None
        w.add_key_value(key, f.contents(), vtype, sub_type=sub)
    w.add_file_type(1)  # F16

    tensors = load_file(os.path.join(hf_dir, "model.safetensors"))
    tensors.pop("lm_head.weight", None)  # poids liés à l'embedding
    for name, t in tensors.items():
        t = t.float().numpy()
        if name.endswith("q_proj.weight"):
            t = permute(t, n_head)
        elif name.endswith("k_proj.weight"):
            t = permute(t, n_kv)
        w.add_tensor(gguf_name(name), t if t.ndim == 1 else t.astype(np.float16))
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()


def quantize(src, dst, ftype="Q4_0"):
    import llama_cpp
    p = llama_cpp.llama_model_quantize_default_params()
    p.ftype = getattr(llama_cpp, f"LLAMA_FTYPE_MOSTLY_{ftype}")
    p.nthread = os.cpu_count() or 4
    if llama_cpp.llama_model_quantize(src.encode(), dst.encode(), p) != 0:
        raise SystemExit("échec de la quantification")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("hf_dir")
    ap.add_argument("out")
    ap.add_argument("--ref", default=REF)
    ap.add_argument("--type", default="Q4_0")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as d:
        f16 = os.path.join(d, "f16.gguf")
        write_f16(a.hf_dir, f16, a.ref)
        quantize(f16, a.out, a.type)
    print(f"{a.out} : {os.path.getsize(a.out) / 1e6:.1f} Mo")
