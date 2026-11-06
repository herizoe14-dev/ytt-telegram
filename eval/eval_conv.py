"""Évalue la mémoire d'Alice sur des conversations jamais vues (eval/conversations_fr.py).

    python eval/eval_conv.py              # score
    python eval/eval_conv.py --verbose    # affiche chaque conversation
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chat  # noqa: E402
from conversations_fr import CONVERSATIONS  # noqa: E402
from eval_fr import is_correct  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    print(f"modèle : {chat.MODEL_PATH.name}")
    ok = 0
    for turns, expected, kind in CONVERSATIONS:
        history = []
        for q in turns:
            ans = chat.ask(q, history=history)
            history.append((q, ans))
        good = is_correct(ans, expected, " ".join(turns[:-1]) if not expected[0].isdigit() else turns[-1])
        ok += good
        if a.verbose:
            print(f"{'✓' if good else '✗'} [{kind}]")
            for q, r in history:
                print(f"    > {q}\n      {r}")
    print(f"conversations réussies : {ok}/{len(CONVERSATIONS)}")
