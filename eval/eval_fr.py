"""Évalue Alice sur 30 questions simples en français.

    python eval/eval_fr.py                 # compare les trois modes
    python eval/eval_fr.py --verbose       # affiche chaque réponse

Mesures :
- correct  : la réponse contient la bonne réponse attendue (contrôle automatique, assez indulgent) ;
- français : la réponse contient plus de mots outils français qu'anglais ;
- boucles  : la réponse répète la même ligne en boucle.
"""
import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chat  # noqa: E402
from questions_fr import CASES  # noqa: E402

FR_WORDS = set("le la les un une des est et de du que qui il elle je tu nous vous ils en au aux pour pas sont avec dans sur ce cette a y ne plus".split())
EN_WORDS = set("the is are and of to in that it you for with this was be on as have not".split())


def baseline(question):
    """Réglages d'origine : aucune consigne, temperature 0.3, pas de pénalité de répétition."""
    out = chat.load_model().create_chat_completion(
        messages=[{"role": "user", "content": question}], max_tokens=256, temperature=0.3, seed=0)
    return out["choices"][0]["message"]["content"].strip()


MODES = {
    "origine": baseline,
    "direct": lambda q: chat.ask(q, "direct"),
    "pivot": lambda q: chat.ask(q, "pivot"),
}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def is_french(text):
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿœ']+", text.lower())
    return sum(w in FR_WORDS for w in words) >= sum(w in EN_WORDS for w in words)


def is_correct(text, answers):
    t = norm(text)
    return any(re.search(r"(?<![\w-])" + re.escape(norm(a)) + r"(?![\w-])", t) for a in answers)


def loops(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return len(lines) >= 3 and len(set(lines)) <= len(lines) / 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="origine,direct,pivot")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    n = len(CASES)
    for name in args.modes.split(","):
        fn = MODES[name]
        ok = fr = lp = 0
        t0 = time.time()
        for q, answers, _cat in CASES:
            a = fn(q)
            c, f, l = is_correct(a, answers), is_french(a), loops(a)
            ok += c; fr += f; lp += l
            if args.verbose:
                print(f"  {'✓' if c else '✗'} {q} -> {a.replace(chr(10), ' ')[:150]}")
        print(f"{name:8s} correct {ok:2d}/{n}   français {fr:2d}/{n}   boucles {lp:2d}   ({time.time() - t0:.0f} s)")
