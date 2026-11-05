"""Petit chat en ligne de commande avec le modèle SmolLM2-135M-Instruct (GGUF, Q4_0).

Usage :
    pip install llama-cpp-python
    python chat.py "Ta question ici"
    python chat.py            # mode interactif
"""
import sys
from pathlib import Path

from llama_cpp import Llama

MODEL_PATH = Path(__file__).parent / "models" / "SmolLM2-135M-Instruct-Q4_0.gguf"

llm = Llama(model_path=str(MODEL_PATH), n_ctx=2048, verbose=False)


def ask(question: str) -> str:
    out = llm.create_chat_completion(
        messages=[{"role": "user", "content": question}],
        max_tokens=256,
        temperature=0.3,
    )
    return out["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(ask(" ".join(sys.argv[1:])))
    else:
        print("Tape ta question (Ctrl+C pour quitter).")
        while True:
            try:
                q = input("> ")
            except (EOFError, KeyboardInterrupt):
                break
            if q.strip():
                print(ask(q))
