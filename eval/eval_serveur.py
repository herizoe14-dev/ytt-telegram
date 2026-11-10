"""Compare deux versions d'Alice servies par llama-server (sans llama-cpp-python).

Mêmes questions, mêmes réglages (température 0) pour chaque modèle :
- séries de questions_fr.py (eval, heldout, raisonnement) et conversations_fr.py (mémoire) ;
- écriture : 20 demandes (récit, poème, lettre…) avec la consigne d'écriture de l'application, SANS début de
  réponse imposé : le texte est-il écrit (et non une question ou une promesse) ?
- boucle : la réponse répétée de l'application (« Je peux vous aider avec un récit… ») deux fois dans le
  contexte, puis « Créé le récit » : le modèle écrit-il enfin ?

    llama-server -m Alice-v6.gguf --port 8091 --api-key k &   llama-server -m Alice-v7.gguf --port 8092 --api-key k &
    python eval/eval_serveur.py --ports 8091,8092 --names v6,v7 --key k
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conversations_fr import CONVERSATIONS  # noqa: E402
from eval_fr import is_correct, loops  # noqa: E402
from questions_fr import CASES, CASES_HELDOUT, CASES_RAISONNEMENT  # noqa: E402

SYS_DIRECT = "Tu es Alice, une assistante qui répond toujours en français, de façon courte, exacte et logique."
SYS_WRITE = ("Tu es Alice, une assistante qui parle français, sur le téléphone de l’utilisateur.\n\n[ÉCRITURE] On te "
             "demande un texte (récit, histoire, poème, lettre…). Écris-le directement et entièrement, maintenant, en "
             "plusieurs paragraphes. Ne demande pas de précisions, ne parle ni de jetons ni de longueur : choisis "
             "toi-même un sujet si on ne t’en donne pas.")
# Demandes jamais vues à l'entraînement (formulations et sujets différents de make_v7_fr.py)
WRITE = ["Créé moi une récit", "Raconte-moi l'histoire d'un pêcheur et d'une tortue", "Écris un conte sur un roi gourmand",
         "J'aimerais une histoire de pirates", "Écris un poème sur le vent", "Écris une lettre à mon voisin pour le bruit",
         "Invente une histoire qui se passe à Antananarivo", "Raconte une aventure dans l'espace",
         "Écris un petit poème pour l'anniversaire de ma sœur", "Crée une histoire drôle avec un éléphant",
         "Écris une histoire triste", "Rédige une lettre de remerciement à un médecin", "Fais-moi un récit policier court",
         "Une histoire de fantôme pas trop effrayante", "Écris un poème sur le café", "Raconte la journée d'une abeille",
         "Écris une fable avec un renard et un corbeau", "Crée un récit de science-fiction", "Écris un texte sur l'hiver",
         "Invente un conte pour mon fils de 5 ans"]
LOOP = "Je peux vous aider avec un récit, jusqu'à environ 4000 tokens."
ASKS = re.compile(r"\?|\bje (peux|vais|pourrais)\b|\bveux-tu\b|\bvoulez\b|\bpr[ée]f[èe]r|\bjetons?\b|\btokens?\b", re.I)


def ask(port, key, msgs, max_tokens=256):
    body = {"model": "alice", "messages": msgs, "max_tokens": max_tokens, "temperature": 0, "seed": 0}
    r = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=json.dumps(body).encode(),
                               headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    return json.load(urllib.request.urlopen(r, timeout=600))["choices"][0]["message"]["content"].strip()


def writes(text):
    """Le texte demandé est écrit : assez long, et le début n'est ni une question ni une promesse."""
    return len(text) > 250 and not ASKS.search(text[:160])


def run(port, key, verbose):
    res = {}
    for name, cases in (("questions", CASES), ("jamais vues", CASES_HELDOUT), ("raisonnement", CASES_RAISONNEMENT)):
        ok = lp = 0
        for q, answers, _ in cases:
            a = ask(port, key, [{"role": "system", "content": SYS_DIRECT}, {"role": "user", "content": q}])
            ok += is_correct(a, answers, q); lp += loops(a)
        res[name] = f"{ok}/{len(cases)}" + (f" ({lp} boucles)" if lp else "")
    ok = 0
    for turns, expected, _ in CONVERSATIONS:
        msgs = [{"role": "system", "content": SYS_DIRECT}]
        for t in turns:
            msgs.append({"role": "user", "content": t})
            a = ask(port, key, msgs)
            msgs.append({"role": "assistant", "content": a})
        ok += is_correct(a, expected, " ".join(turns[:-1]) if not expected[0].isdigit() else turns[-1])
    res["conversations"] = f"{ok}/{len(CONVERSATIONS)}"
    ok, ex = 0, []
    for q in WRITE:
        a = ask(port, key, [{"role": "system", "content": SYS_WRITE}, {"role": "user", "content": q}], 500)
        ok += writes(a); ex.append((q, a))
        if verbose:
            print(f"  {'✓' if writes(a) else '✗'} {q} -> {a[:160]!r}")
    res["écriture"] = f"{ok}/{len(WRITE)}"
    ok = 0
    for q in ["Créé le récit", "Oui créé le récit", "Créé moi une récit", "Commencer", "Écris l'histoire maintenant"]:
        a = ask(port, key, [{"role": "system", "content": SYS_WRITE}, {"role": "user", "content": "Crée un récit jusqu'à 4000 token"},
                            {"role": "assistant", "content": LOOP}, {"role": "user", "content": "Créé le récit"},
                            {"role": "assistant", "content": LOOP}, {"role": "user", "content": q}], 500)
        ok += writes(a) and LOOP[:30] not in a
        if verbose:
            print(f"  boucle → {q} : {a[:120]!r}")
    res["sortie de boucle"] = f"{ok}/5"
    return res, ex


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ports", required=True)
    ap.add_argument("--names", required=True)
    ap.add_argument("--key", default="local")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--examples", help="fichier JSON où écrire les textes produits (pour les relire)")
    a = ap.parse_args()
    table, examples = {}, {}
    for port, name in zip(a.ports.split(","), a.names.split(",")):
        print(f"== {name}", flush=True)
        table[name], examples[name] = run(port, a.key, a.verbose)
        print(table[name], flush=True)
    keys = list(next(iter(table.values())).keys())
    print("\n| Test | " + " | ".join(table) + " |\n|---|" + "---|" * len(table))
    for k in keys:
        print(f"| {k} | " + " | ".join(table[n][k] for n in table) + " |")
    if a.examples:
        json.dump(examples, open(a.examples, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
