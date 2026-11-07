"""Convertit la base de connaissances (data/alice_kb.sqlite) en index lisible en JavaScript pur.

L'application Alice tourne sur Node.js 18 (sans SQLite) : elle lit ces fichiers directement, sans
module natif. Format (petit-boutiste) :

- kb.docs   : documents « titre \\t texte \\t source \\n » (UTF-8), les uns à la suite des autres ;
- kb.offs   : uint32 × (N+1), début de chaque document dans kb.docs ;
- kb.lens   : uint16 × N, longueur pondérée de chaque document (8 × mots du titre + mots du texte) ;
- kb.dict   : dictionnaire trié par blocs de 128 mots : [u8 longueur][mot][u32 début][u32 taille][u32 df] ;
- kb.dblk   : uint32 × blocs, début de chaque bloc dans kb.dict (index creux, gardé en mémoire) ;
- kb.post   : listes de documents par mot : varint(écart de numéro), varint(poids : 8 × titre + texte) ;
- kb.titles : paires uint32 (empreinte du titre normalisé, document) triées, pour « Le citron » → « Citron » ;
- kb.json   : informations (nombre de documents, longueur moyenne, version).

Les mots sont normalisés comme le tokenizer « unicode61 remove_diacritics 2 » de SQLite FTS5
(minuscules, sans accents, suites de lettres et de chiffres). Les mots vides et les nombres ne
sont pas indexés : la recherche ne les utilise pas.

    python knowledge/build_kb_index.py [--db data/alice_kb.sqlite] [--out data/kb-index]
"""
import argparse
import array
import json
import os
import re
import sqlite3
import sys
import unicodedata
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb import STOP  # noqa: E402

TOKEN = re.compile(r"[0-9a-z]+")
BLOCK = 128
TITLE_W = 8
VERSION = 1


def norm(text):
    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c)).replace("œ", "oe").replace("æ", "ae")


def tokens(text):
    return TOKEN.findall(norm(text))


STOP_N = {norm(w) for w in STOP}


def keep(tok):
    return len(tok) >= 2 and not tok.isdigit() and tok not in STOP_N


def title_key(title):
    """Titre sans précision entre parenthèses, normalisé : « Germinal (roman) » → « germinal »."""
    t = re.sub(r"\s*\(.*\)", "", title)
    return " ".join(tokens(t))


def h32(s):
    return zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF


def varint(n, out):
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)


def build(db_path, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    n_docs = db.execute("SELECT count(*) FROM kb").fetchone()[0]
    print(f"{n_docs} documents", flush=True)

    term_id, postings = {}, []          # mot → numéro ; numéro → array('I') [doc, poids, doc, poids…]
    lens = array.array("H")
    offs = array.array("I", [0])
    titles = []
    pos = 0
    with open(out / "kb.docs", "wb") as fdocs:
        # faits d'Alice d'abord (ils gardent les petits numéros), puis Wikipédia
        rows = db.execute("SELECT title, text, source FROM kb ORDER BY (source != 'Alice'), rowid")
        for doc, (title, text, source) in enumerate(rows):
            title = title.replace("\t", " ").replace("\n", " ")
            text = text.replace("\t", " ").replace("\n", " ")
            data = f"{title}\t{text}\t{source}\n".encode("utf-8")
            fdocs.write(data)
            pos += len(data)
            offs.append(pos)
            tt, xt = tokens(title), tokens(text)
            lens.append(min(65535, TITLE_W * len(tt) + len(xt)))
            weights = {}
            for t in tt:
                if keep(t):
                    weights[t] = weights.get(t, 0) + TITLE_W
            for t in xt:
                if keep(t):
                    weights[t] = weights.get(t, 0) + 1
            for t, w in weights.items():
                i = term_id.get(t)
                if i is None:
                    i = term_id[t] = len(postings)
                    postings.append(array.array("I"))
                p = postings[i]
                p.append(doc)
                p.append(min(w, 255))
            k = title_key(title)
            if k:
                titles.append((h32(k), doc))
            if doc % 100000 == 0:
                print(f"  {doc} documents, {len(term_id)} mots", flush=True)
    offs.tofile(open(out / "kb.offs", "wb"))
    lens.tofile(open(out / "kb.lens", "wb"))

    print(f"{len(term_id)} mots : écriture des listes…", flush=True)
    terms = sorted(term_id, key=lambda t: t.encode("utf-8"))
    dblk = array.array("I")
    with open(out / "kb.post", "wb") as fpost, open(out / "kb.dict", "wb") as fdict:
        ppos = dpos = 0
        for n, t in enumerate(terms):
            if n % BLOCK == 0:
                dblk.append(dpos)
            p = postings[term_id[t]]
            buf, prev = bytearray(), 0
            for j in range(0, len(p), 2):
                varint(p[j] - prev, buf)
                varint(p[j + 1], buf)
                prev = p[j]
            fpost.write(buf)
            tb = t.encode("utf-8")[:255]
            entry = bytes([len(tb)]) + tb + array.array("I", [ppos, len(buf), len(p) // 2]).tobytes()
            fdict.write(entry)
            ppos += len(buf)
            dpos += len(entry)
            postings[term_id[t]] = None  # libère la mémoire au fur et à mesure
    dblk.tofile(open(out / "kb.dblk", "wb"))

    titles.sort()
    array.array("I", [x for pair in titles for x in pair]).tofile(open(out / "kb.titles", "wb"))
    avg = sum(lens) / max(1, len(lens))
    info = {"version": VERSION, "docs": n_docs, "terms": len(terms), "block": BLOCK, "titleWeight": TITLE_W,
            "avgLen": round(avg, 3), "source": "Wikipédia (CC BY-SA, wikimedia/wikipedia 20231101.fr) + faits d'Alice"}
    (out / "kb.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    total = sum(f.stat().st_size for f in out.iterdir())
    print(f"index : {out} ({total / 1e6:.0f} Mo)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "alice_kb.sqlite"))
    ap.add_argument("--out", default=str(ROOT / "data" / "kb-index"))
    a = ap.parse_args()
    build(a.db, a.out)
