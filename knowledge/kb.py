"""Recherche dans la base de connaissances d'Alice (data/alice_kb.sqlite).

Avant de répondre à une question de culture générale, Alice cherche les passages les
plus pertinents (recherche plein texte SQLite FTS5, classement BM25, titres favorisés)
et s'appuie dessus. Les messages de conversation (salutations, questions sur
l'utilisateur ou sur Alice) et les calculs ne déclenchent pas de recherche.
"""
import os
import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

DB = Path(os.environ.get("ALICE_KB", Path(__file__).resolve().parent.parent / "data" / "alice_kb.sqlite"))

STOP = set("""
a à au aux avec ce ces cet cette c ça d de des du dans en et est été être il ils elle elles on la le les l
leur leurs lui mais même ne ni n ou où par pas pour plus qu que quel quelle quelles quels qui quoi sa se ses
si son sont sur ta te tes toi ton tu un une vos votre vous y comment combien pourquoi quand quelqu
est-ce dit dire fait faire font ont avait avoir sont était peut peux veux veut fut s sais savoir connais
connaître explique expliquer parle parler raconte donne donner cite citer moi me m je j mon ma mes nous
notre nos t c'est qu'est-ce chose choses quoi alors aussi très bien bon bonne oui non merci svp stp
appelle appelles appelé appelée signifie veut-on dit-on fabrique fabriqué fabriquée fabriquent
""".split())
PERSONNEL = re.compile(r"\b(je|j|moi|mon|ma|mes|tu|toi|ton|ta|tes|alice|bonjour|salut|coucou|merci|"
                       r"au revoir|enchant\w*)\b", re.I)
CALCUL = re.compile(r"\d+\s*(plus|moins|fois|divis\w*|[+\-×x*/÷])\s*\d+|\bcalcule\b|\bcombien font\b", re.I)


def _norm(word):
    w = unicodedata.normalize("NFKD", word.lower())
    return "".join(c for c in w if not unicodedata.combining(c))


def terms(text):
    words = re.findall(r"[\w'-]+", text.lower())
    out = []
    for w in words:
        w = w.split("'")[-1].strip("-")
        if len(w) < 2 or w in STOP or _norm(w) in STOP or w.isdigit():
            continue
        out.append(w)
    return out


@lru_cache(maxsize=1)
def _db():
    if not DB.exists():
        return None
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True, check_same_thread=False)


def available():
    return _db() is not None


def _fts_query(ts):
    parts = []
    for t in ts:
        t = t.replace('"', "")
        if len(t) >= 5 and t[-1] in "sx":  # pluriels : « plastiques » -> plastique*
            t = t[:-1]
        parts.append(f'"{t}"*' if len(t) >= 5 else f'"{t}"')
    return " OR ".join(parts)


def search(question, history=None, k=3):
    """Passages [(titre, texte, source)] utiles pour la question, ou [] si rien de pertinent."""
    db = _db()
    if db is None or CALCUL.search(question):
        return []
    if PERSONNEL.search(question) and not re.search(r"\b(qu'est-ce|c'est quoi|qui (a|est|était))\b", question, re.I):
        return []
    ts = terms(question)
    if len(ts) < 2 and history:  # question elliptique (« Et le plastique ? ») : on ajoute le sujet précédent
        ts += terms(history[-1][0])
    if not ts:
        return []
    try:
        rows = db.execute("SELECT title, text, source, bm25(kb, 8.0, 1.0) FROM kb WHERE kb MATCH ? "
                          "ORDER BY bm25(kb, 8.0, 1.0) LIMIT ?", (_fts_query(ts), k * 4)).fetchall()
    except sqlite3.OperationalError:
        return []
    keys = {_norm(t)[:5] for t in ts}
    out = []
    for title, text, source, score in rows:
        title_words = {_norm(w)[:5] for w in re.findall(r"\w+", title)}
        text_hits = sum(1 for kk in keys if kk in _norm(text))
        # pertinent si le titre contient un mot de la question, ou si le texte en contient plusieurs
        if title_words & keys or text_hits >= min(2, len(keys)):
            out.append((title, text, source))
        if len(out) == k:
            break
    return out


def context(passages, max_chars=550):
    lines = []
    for i, (title, text, source) in enumerate(passages, 1):
        t = text if len(text) <= max_chars else text[:max_chars].rsplit(" ", 1)[0] + "…"
        lines.append(f"[{i}] {title} ({source}) : {t}")
    return "\n".join(lines)
