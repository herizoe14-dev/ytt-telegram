"""Construit la base de connaissances d'Alice (data/alice_kb.sqlite).

Contenu :
- les faits vérifiés écrits pour Alice (train/connaissances_fr.py) ;
- l'introduction des articles de Wikipédia en français (jeu « wikimedia/wikipedia »,
  version 20231101.fr, licence CC BY-SA), pour les articles d'au moins 1 500 caractères.

L'index est une table SQLite FTS5 (recherche plein texte classée par BM25). Il pèse
environ 1 Go et n'est pas dans le dépôt : chacun le reconstruit avec ce script
(environ 4,6 Go à télécharger, traités un fichier après l'autre).

    pip install pyarrow huggingface_hub
    python knowledge/build_kb.py               # tout
    python knowledge/build_kb.py --shards 2    # essai rapide sur 2 fichiers sur 17
"""
import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "alice_kb.sqlite"
REPO, CONFIG, N_SHARDS = "wikimedia/wikipedia", "20231101.fr", 17
MIN_ARTICLE, MAX_INTRO = 1500, 900


def intro(text):
    """Premiers paragraphes de l'article, coupés proprement à une fin de phrase."""
    out = ""
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        if len(para) < 60 and not para.endswith("."):  # titre de section : fin de l'introduction
            if out:
                break
            continue
        out = (out + " " + para).strip()
        if len(out) >= MAX_INTRO:
            break
    if len(out) > MAX_INTRO:
        cut = out[:MAX_INTRO]
        end = max(cut.rfind(". "), cut.rfind(". "))
        out = cut[:end + 1] if end > 200 else cut
    return re.sub(r"\s+", " ", out)


def create(db):
    db.execute("DROP TABLE IF EXISTS kb")
    db.execute("CREATE VIRTUAL TABLE kb USING fts5(title, text, source UNINDEXED, "
               "tokenize='unicode61 remove_diacritics 2')")


def add_facts(db):
    sys.path.insert(0, str(ROOT / "train"))
    from connaissances_fr import FAITS
    import make_data_fr as D  # définitions écrites à la main (« Le citron est un fruit jaune… »)
    rows = [(qs[0].rstrip(" ?"), a, "Alice") for qs, a in FAITS]
    for un, le, nom, d in D.DEFS:
        art = le if nom in D.DEFINI else un
        sujet = D.le_nom(art, nom)
        verbe = "sont" if art in ("des", "les") else "est"
        rows.append((nom.capitalize(), f"{sujet[0].upper() + sujet[1:]} {verbe} {d}.", "Alice"))
    db.executemany("INSERT INTO kb VALUES (?, ?, ?)", rows)
    return len(rows)


def add_wikipedia(db, shards, tmp):
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    total = 0
    for i in range(shards):
        name = f"{CONFIG}/train-{i:05d}-of-{N_SHARDS:05d}.parquet"
        path = hf_hub_download(REPO, name, repo_type="dataset", local_dir=tmp)
        f = pq.ParquetFile(path)
        n = 0
        for batch in f.iter_batches(columns=["title", "text"], batch_size=2000):
            rows = []
            for title, text in zip(batch.column("title").to_pylist(), batch.column("text").to_pylist()):
                if len(text) >= MIN_ARTICLE and not title.startswith(("Liste ", "Chronologie ")):
                    t = intro(text)
                    if len(t) > 150:
                        rows.append((title, t, "Wikipédia"))
            db.executemany("INSERT INTO kb VALUES (?, ?, ?)", rows)
            n += len(rows)
        db.commit()
        os.remove(path)
        total += n
        print(f"fichier {i + 1}/{shards} : {n} articles (total {total})", flush=True)
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=N_SHARDS)
    ap.add_argument("--tmp", default=str(ROOT / "data" / "tmp"))
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--facts-only", action="store_true", help="ne met à jour que les faits d'Alice")
    a = ap.parse_args()
    Path(a.db).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(a.db)
    if a.facts_only:  # met à jour seulement les faits d'Alice dans une base existante
        db.execute("DELETE FROM kb WHERE source = 'Alice'")
        print(f"faits d'Alice : {add_facts(db)}")
        db.commit()
        sys.exit()
    create(db)
    print(f"faits d'Alice : {add_facts(db)}")
    add_wikipedia(db, a.shards, a.tmp)
    print("optimisation de l'index…", flush=True)
    db.execute("INSERT INTO kb(kb) VALUES('optimize')")
    db.commit()
    db.execute("VACUUM")
    print(f"{a.db} : {os.path.getsize(a.db) / 1e6:.0f} Mo")
