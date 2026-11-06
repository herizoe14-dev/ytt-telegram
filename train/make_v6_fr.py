"""Données de la 6e version d'Alice (train/v6_fr.jsonl et train/oasst2_fr.jsonl).

Corrige ce qu'a montré la conversation réelle dans le bot :
- « toi » et « moi » : ne pas confondre le prénom de l'utilisateur avec le sien, dire
  qu'on ne le connaît pas encore, le repérer dans une phrase longue, « Et moi ? » ;
- corrections : accepter une correction juste (« Tu as raison… »), mais maintenir
  poliment une réponse juste quand la correction est fausse ;
- honnêteté : « je ne sais pas » plutôt qu'inventer, pas de faux e-mails ni liens,
  demander une précision quand la question est ambiguë ;
- connaissances générales écrites à la main (train/connaissances_fr.py) ;
- conversations françaises écrites par des humains (OpenAssistant oasst2, Apache 2.0).

    python train/make_v6_fr.py [--oasst chemin/vers/2023-11-05_oasst2_ready.trees.jsonl.gz]
"""
import argparse
import gzip
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_data_fr as D  # noqa: E402
import make_dialogues_fr as G  # noqa: E402
from connaissances_fr import FAITS, INCONNUS  # noqa: E402

rng = random.Random(6)
SYSTEM = G.SYSTEM


def faits_tours(n):
    """Échanges de culture générale pour intercaler dans les conversations."""
    out = []
    for _ in range(n):
        qs, a = rng.choice(FAITS)
        out.append((rng.choice(qs), a))
    return out


def intercale(n):
    return [(q, a) for q, a, _ in G.fillers(n // 2)] + faits_tours(n - n // 2)


DIRE_PRENOM = [
    "Je m'appelle {p}.", "Moi c'est {p}.", "Non, toi tu es Alice et moi c'est {p}.",
    "Moi, je ne suis pas Alice : je m'appelle {p}.", "Tu peux m'appeler {p}.", "Mon prénom à moi, c'est {p}.",
    "Je suis {p}, et toi ?", "Alors moi, c'est {p}.", "Retiens que je m'appelle {p}.",
    "Bonjour Alice, ici {p}.", "C'est {p} qui te parle.", "On m'appelle {p}.",
]
DEMANDE_QUI = ["Et moi je suis qui ?", "Comment je m'appelle ?", "Tu sais comment je m'appelle ?",
               "Qui suis-je ?", "Tu connais mon prénom ?", "Et moi, je m'appelle comment ?"]


def conv_prenom_inconnu():
    p, _ = rng.choice(G.PRENOMS)
    turns = []
    if rng.random() < 0.6:
        turns.append((rng.choice(["Bonjour", "Salut Alice", "Coucou"]),
                      rng.choice(["Bonjour ! Je suis Alice. Comment puis-je t'aider ?", "Salut ! Que puis-je faire pour toi ?"])))
    if rng.random() < 0.5:
        turns.append(("Comment tu t'appelles ?", "Je m'appelle Alice."))
    turns.append((rng.choice(DEMANDE_QUI),
                  rng.choice(["Tu ne m'as pas encore dit ton prénom. Comment t'appelles-tu ?",
                              "Je ne sais pas encore : tu ne me l'as pas dit. Quel est ton prénom ?",
                              "Je ne connais pas encore ton prénom. Tu veux me le dire ?"])))
    dit = rng.choice(DIRE_PRENOM).format(p=p)
    rep = f"Enchantée, {p} ! Moi, je suis Alice." if "et toi" in dit else rng.choice(
        [f"Enchantée, {p} !", f"Très bien, {p}, c'est noté !", f"D'accord : tu t'appelles {p}, et moi Alice."])
    turns.append((dit, rep))
    turns += intercale(rng.randint(0, 3))
    turns.append((rng.choice(DEMANDE_QUI + ["Et moi ?"]), rng.choice([f"Tu t'appelles {p}.", f"Toi, tu es {p}.", f"Ton prénom est {p}."])))
    if rng.random() < 0.5:
        turns.append(("Et toi ?", "Moi, je m'appelle Alice."))
    return turns


def conv_toi_moi():
    """Phrases longues avec les deux prénoms, et questions « et moi ? » / « et toi ? »."""
    p, _ = rng.choice(G.PRENOMS)
    turns = [(rng.choice(DIRE_PRENOM[2:]).format(p=p), rng.choice([f"Enchantée, {p} ! Moi, je suis Alice.", f"C'est noté, {p} !"]))]
    for _ in range(rng.randint(2, 5)):
        r = rng.random()
        if r < 0.25:
            turns.append(("Comment tu t'appelles ?", "Je m'appelle Alice."))
            turns.append(("Et moi ?", f"Toi, tu t'appelles {p}."))
        elif r < 0.5:
            turns.append((rng.choice(["Qui est Alice ?", "Alice, c'est qui ?"]), "Alice, c'est moi : l'intelligence artificielle avec qui tu parles."))
        elif r < 0.7:
            turns.append((rng.choice(["Qui suis-je ?", "Je suis qui ?"]), f"Tu es {p}."))
        else:
            turns += intercale(1)
    return turns


def conv_correction_juste():
    """Alice s'est trompée (cette réponse n'est pas apprise) ; elle accepte la correction."""
    if rng.random() < 0.5:
        (de, cap), (_, faux) = rng.sample(D.CAPITALS, 2)
        q, wrong = f"Quelle est la capitale {de} ?", f"La capitale {de} est {faux}."
        corr = rng.choice([f"Non, c'est faux : la capitale {de} est {cap}.", f"Tu te trompes, c'est {cap}.",
                           f"Mais non, c'est {cap} !"])
        ok = f"Tu as raison, je me suis trompée : la capitale {de} est {cap}. Merci de m'avoir corrigée !"
        check = (f"Alors, quelle est la capitale {de} ?", f"La capitale {de} est {cap}.")
    else:
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        q, wrong = f"Combien font {a} fois {b} ?", f"{a} fois {b} font {a * b + rng.choice([-2, -1, 1, 2, 10])}."
        corr = rng.choice([f"Non, c'est faux, ça fait {a * b}.", "Tu es sûre ? Recalcule.", f"Non : {a} fois {b} font {a * b}."])
        ok = f"Tu as raison, je me suis trompée : {a} fois {b} font {a * b}. Merci !"
        check = ("Et donc le résultat ?", f"{a} fois {b} font {a * b}.")
    return [(q, (wrong, False)), (corr, ok), check]


def conv_correction_fausse():
    """L'utilisateur « corrige » une bonne réponse : Alice maintient poliment, avec la preuve."""
    if rng.random() < 0.5:
        (de, cap), (de2, autre) = rng.sample(D.CAPITALS, 2)
        return [(f"Quelle est la capitale {de} ?", f"La capitale {de} est {cap}."),
                (rng.choice([f"Non, c'est {autre}.", f"Faux, la capitale {de} est {autre}."]),
                 f"Je ne crois pas : la capitale {de} est bien {cap}. {autre} est la capitale {de2}.")]
    if rng.random() < 0.3:
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        return [(f"Combien font {a} fois {b} ?", f"{a} fois {b} font {a * b}."),
                (rng.choice(["Tu es sûre ?", "Vraiment ?", "Tu es certaine ?"]),
                 f"Oui, j'en suis sûre : {a} fois {b} font {a * b}.")]
    a, b = rng.randint(2, 30), rng.randint(2, 30)
    faux = a + b + rng.choice([-3, -1, 1, 2, 5])
    return [(f"Combien font {a} plus {b} ?", f"{a} plus {b} font {a + b}."),
            (rng.choice([f"Non, ça fait {faux}.", f"Tu te trompes, c'est {faux}."]),
             f"Je pense que c'est bien {a + b} : {a} plus {b} font {a + b}. Tu peux vérifier en comptant !")]


def conv_correction_forme():
    p, _ = rng.choice(G.PRENOMS)
    return [(f"Je m'appelle {p}.", f"Enchantée, {p} !"),
            ("Comment je m'appelle ?", f"Tu t'appelles {p}."),
            (rng.choice(["Vouvoie-moi, s'il te plaît.", "On répond plutôt « vous êtes », vouvoie-moi."]),
             f"D'accord, je vais vous vouvoyer. Vous vous appelez {p}."),
            ("Et maintenant, comment je m'appelle ?", f"Vous vous appelez {p}.")]


AMBIGUS = [
    ("Le 28 jour c'est quel mois ?",
     "Je ne suis pas sûre de comprendre. Veux-tu savoir quel mois a 28 jours (février), ou quel mois tombe le 28e jour de l'année (janvier) ?"),
    ("Combien ?", "Combien de quoi ? Peux-tu préciser ta question ?"),
    ("C'est loin ?", "Qu'est-ce qui est loin, et à partir d'où ? Donne-moi un peu plus de détails."),
    ("Il fait combien là-bas ?", "Je ne sais pas de quel endroit tu parles, et je n'ai pas accès à la météo. Tu peux préciser ?"),
    ("Et lui, il a quel âge ?", "De qui parles-tu ? Tu ne m'as pas encore parlé de cette personne."),
    ("C'est quand ?", "De quel événement parles-tu ? Précise-moi, je ferai de mon mieux."),
    ("Lequel est le meilleur ?", "Le meilleur parmi quoi ? Dis-moi entre quelles choses tu hésites."),
    ("Fais-le.", "Que veux-tu que je fasse ? Explique-moi ce dont tu as besoin."),
    ("Explique.", "Que veux-tu que je t'explique ? Donne-moi le sujet."),
    ("Ça coûte combien ?", "De quel objet parles-tu ? Et je n'ai pas accès aux prix actuels."),
]


def conv_inconnu():
    turns = intercale(rng.randint(0, 2))
    turns.append((rng.choice(INCONNUS), rng.choice([
        "Je ne connais pas ce sujet, et je préfère ne pas inventer. Peux-tu me donner plus de détails ?",
        "Je ne suis pas sûre : je n'ai pas d'information fiable là-dessus.",
        "Je ne sais pas. Je ne trouve rien de fiable sur ce sujet dans mes connaissances."])))
    if rng.random() < 0.5:
        turns.append((rng.choice(["Invente quelque chose alors.", "Dis-moi quand même."]),
                      "Je peux inventer une histoire si tu veux, mais je te préviens : ce ne sera pas vrai. Tu veux une histoire inventée ?"))
    return turns


def conv_faits_suite():
    """Culture générale en conversation, avec des questions qui se suivent."""
    return faits_tours(rng.randint(2, 5))


TYPES = [(conv_prenom_inconnu, 300), (conv_toi_moi, 250), (conv_correction_juste, 200),
         (conv_correction_fausse, 150), (conv_correction_forme, 60), (conv_inconnu, 80), (conv_faits_suite, 120)]


def to_messages(turns):
    msgs = [{"role": "system", "content": SYSTEM}] if rng.random() < 0.8 else []
    for u, a in turns:
        msgs.append({"role": "user", "content": D.elide(u)})
        if isinstance(a, tuple):  # réponse fausse : présente dans le contexte, mais pas apprise
            msgs.append({"role": "assistant", "content": D.elide(a[0]), "train": False})
        else:
            msgs.append({"role": "assistant", "content": D.elide(a)})
    return msgs


def oasst_fr(path):
    """Meilleur fil (réponses les mieux notées) de chaque conversation française d'oasst2."""
    convs = []
    for line in gzip.open(path, "rt", encoding="utf-8"):
        t = json.loads(line)
        if t["prompt"]["lang"] != "fr":
            continue
        node, path_ = t["prompt"], [t["prompt"]]
        while node.get("replies"):
            reps = [r for r in node["replies"] if not r.get("deleted") and r.get("review_result", True)]
            if not reps:
                break
            reps.sort(key=lambda r: (r.get("rank") is None, r.get("rank") or 0))
            node = reps[0]
            path_.append(node)
        if len(path_) % 2:
            path_ = path_[:-1]
        if len(path_) >= 2:
            msgs = [{"role": "system", "content": SYSTEM}] + [
                {"role": "user" if m["role"] == "prompter" else "assistant", "content": m["text"]} for m in path_]
            text = " ".join(m["content"] for m in msgs).lower()
            # Alice ne s'appelle ni Open Assistant ni autre chose
            if any(w in text for w in ("open assistant", "openassistant", "chatgpt", "laion")):
                continue
            convs.append({"messages": msgs, "source": "oasst2"})
    return convs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oasst", help="2023-11-05_oasst2_ready.trees.jsonl.gz (OpenAssistant/oasst2 sur Hugging Face)")
    a = ap.parse_args()
    rows = []
    for fn, n in TYPES:
        for _ in range(n):
            t = fn()
            if t and not any(w in json.dumps(t, ensure_ascii=False).lower() for w in G.FORBIDDEN):
                rows.append({"messages": to_messages(t)})
    for q, r in AMBIGUS:
        for _ in range(3):
            rows.append({"messages": to_messages(intercale(rng.randint(0, 2)) + [(q, r)])})
    n_conv = len(rows)
    for qs, r in FAITS:  # chaque formulation, en question isolée
        for q in qs:
            rows.append({"question": q, "answer": r})
            rows.append({"question": q.rstrip(" ?") , "answer": r})
    for q in INCONNUS:
        rows.append({"question": q, "answer": "Je ne connais pas ce sujet, et je préfère ne pas inventer. "
                                               "Peux-tu me donner plus de détails ?"})
    rng.shuffle(rows)
    out = HERE / "v6_fr.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} exemples dans {out.name} : {n_conv} conversations, {len(rows) - n_conv} questions-réponses")
    if a.oasst:
        conv = oasst_fr(a.oasst)
        with open(HERE / "oasst2_fr.jsonl", "w", encoding="utf-8") as f:
            for r in conv:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{len(conv)} conversations françaises d'oasst2 dans oasst2_fr.jsonl")


if __name__ == "__main__":
    main()
