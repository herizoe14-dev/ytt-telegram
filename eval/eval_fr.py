"""Évalue Alice sur 30 questions simples en français.

    python eval/eval_fr.py                 # modes direct et pivot du modèle entraîné
    python eval/eval_fr.py --verbose       # affiche chaque réponse
    python eval/eval_fr.py --set heldout   # 32 questions jamais vues à l'entraînement
    ALICE_MODEL=chemin/vers/SmolLM2-135M-Instruct-Q4_0.gguf python eval/eval_fr.py --modes origine,direct,pivot
                                           # modèle d'origine (à télécharger, voir README)

Mesures :
- correct  : la réponse contient la bonne réponse attendue (pour un nombre : le dernier
             nombre de la réponse doit être le bon) ;
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
from questions_fr import CASES, CASES_HELDOUT  # noqa: E402

FR_WORDS = set("le la les un une des est et de du que qui il elle je tu nous vous ils en au aux pour pas sont avec dans sur ce cette a y ne plus".split())
EN_WORDS = set("the is are and of to in that it you for with this was be on as have not".split())


def baseline(question):
    """Réglages d'origine : aucune consigne, temperature 0.3, pas de pénalité de répétition."""
    out = chat.load_model().create_chat_completion(
        messages=[{"role": "user", "content": question}], max_tokens=256, temperature=0.3, seed=0)
    return out["choices"][0]["message"]["content"].strip()


MODES = {
    "origine": baseline,  # pour le modèle d'origine (voir ci-dessus)
    "direct": lambda q: chat.ask(q, "direct"),
    "direct0": lambda q: chat.answer_direct(q, shots=False),  # sans exemples
    "direct5": lambda q: chat.answer_direct(q, shots=True),   # avec 5 exemples
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
    if answers[0].isdigit():  # réponse chiffrée : le dernier nombre écrit doit être le bon
        nums = re.findall(r"\d+", t)
        return bool(nums) and nums[-1] == answers[0]
    return any(re.search(r"(?<![\w-])" + re.escape(norm(a)) + r"(?![\w-])", t) for a in answers)


def loops(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return len(lines) >= 3 and len(set(lines)) <= len(lines) / 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="direct,pivot")
    ap.add_argument("--set", choices=["eval", "heldout"], default="eval",
                    help="eval : les 30 questions d'origine ; heldout : 32 questions jamais vues à l'entraînement")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    cases = CASES if args.set == "eval" else CASES_HELDOUT
    n = len(cases)
    print(f"modèle : {chat.MODEL_PATH.name}, série : {args.set}")
    for name in args.modes.split(","):
        fn = MODES[name]
        ok = fr = lp = 0
        t0 = time.time()
        for q, answers, _cat in cases:
            a = fn(q)
            c, f, l = is_correct(a, answers), is_french(a), loops(a)
            ok += c; fr += f; lp += l
            if args.verbose:
                print(f"  {'✓' if c else '✗'} {q} -> {a.replace(chr(10), ' ')[:150]}")
        print(f"{name:8s} correct {ok:2d}/{n}   français {fr:2d}/{n}   boucles {lp:2d}   ({time.time() - t0:.0f} s)")
