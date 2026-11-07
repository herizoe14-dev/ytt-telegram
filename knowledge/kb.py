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
# Exercices qui ne demandent pas de connaissances : langue, logique, jours, problèmes chiffrés
EXERCICE = re.compile(
    r"\b(contraire|pluriel|féminin|masculin|synonyme|tradui\w*|conjugue\w*|se dit|dit-on|"
    r"plus (grand|grande|petit|petite|âgé|âgée|jeune|rapide|lent|lente|fort|forte|lourd|lourde)s? (que|qu')|"
    r"aujourd'hui|demain|hier|jour vient|mois vient|pair ou impair|suite|tous les|toutes les|aucun|"
    r"(chaud|chaude|froid|froide|sucré|salé) ou)\b", re.I)


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


def _variants(t):
    """Singulier et pluriel d'un mot (sans recherche par préfixe : « gland » ne doit pas donner « glande »)."""
    t = _norm(t).replace('"', "")
    v = {t}
    if len(t) > 3 and t[-1] in "sx":
        v.add(t[:-1])
    else:
        v.add(t + "s")
    return v


def _or_query(ts):
    return " OR ".join(f'"{v}"' for t in ts for v in sorted(_variants(t)))


DISAMBIG = re.compile(r"\((film|album|chanson|série|téléfilm|jeu vidéo|groupe|roman graphique|bande dessinée|homonymie)", re.I)


def _candidates(db, ts):
    queries = []
    # 1) titre exactement égal au sujet (« Le citron » -> « Citron »)
    queries.append((f'title : ("{" ".join(_norm(t) for t in ts)}")', 10))
    # 2) paires de mots consécutifs en expression exacte (« ville rose », « flûte enchantée »)
    for x, y in zip(ts, ts[1:]):
        queries.append((f'"{_norm(x)} {_norm(y)}"', 25))
    # 3) n'importe lequel des mots
    queries.append((_or_query(ts), 60))
    seen, rows = set(), []
    for q, n in queries:
        try:
            for r in db.execute("SELECT rowid, title, text, source FROM kb WHERE kb MATCH ? "
                                "ORDER BY bm25(kb, 8.0, 1.0) LIMIT ?", (q, n)):
                if r[0] not in seen:
                    seen.add(r[0]); rows.append(r[1:])
        except sqlite3.OperationalError:
            pass
    return rows


def _words(text):
    return set(_norm(text).replace("'", " ").replace("’", " ").split()) | set(
        re.findall(r"\w+", _norm(text)))


def search(question, history=None, k=3):
    """Passages [(titre, texte, source)] utiles pour la question, ou [] si rien de pertinent."""
    db = _db()
    if db is None or CALCUL.search(question) or EXERCICE.search(question):
        return []
    if re.search(r"\d", question) and not re.search(r"\b(1\d{3}|20\d{2})\b", question):
        return []  # problème chiffré (sauf une année : « JO de 2016 »)
    if PERSONNEL.search(question) and not re.search(r"\b(qu'est-ce|c'est quoi|qui (a|est|était))\b", question, re.I):
        return []
    ts = terms(question)
    if len(ts) < 2 and history:  # question elliptique (« Et le plastique ? ») : on ajoute le sujet précédent
        ts += [t for t in terms(history[-1][0]) if t not in ts]
    if not ts:
        return []
    keys = [_variants(t) for t in ts]
    pairs = [f"{_norm(x)} {_norm(y)}" for x, y in zip(ts, ts[1:])]
    scored = []
    for title, text, source in _candidates(db, ts):
        tw, xw = _words(title), _words(text)
        t_cov = sum(1 for v in keys if v & tw)
        x_cov = sum(1 for v in keys if v & xw)
        if not (t_cov or x_cov >= min(2, len(keys))):
            continue
        ntitle = re.sub(r"\s*\(.*\)", "", _norm(title)).strip()
        score = 3 * t_cov + x_cov
        score += 4 * sum(1 for p in pairs if p in _norm(title + " " + text))
        if ntitle in {" ".join(sorted(v)[0] for v in keys), " ".join(_norm(t) for t in ts)}:
            score += 6  # titre = sujet de la question
        if DISAMBIG.search(title):
            score -= 4
        if source == "Alice":
            score += 2  # faits vérifiés en priorité
        scored.append((score, -len(text), title, text, source))
    scored.sort(reverse=True)
    best = scored[0][0] if scored else 0
    return [(t, x, s) for sc, _, t, x, s in scored[:k] if sc >= max(3, best - 4)]


def context(passages, max_chars=550):
    lines = []
    for i, (title, text, source) in enumerate(passages, 1):
        t = text if len(text) <= max_chars else text[:max_chars].rsplit(" ", 1)[0] + "…"
        lines.append(f"[{i}] {title} ({source}) : {t}")
    return "\n".join(lines)
