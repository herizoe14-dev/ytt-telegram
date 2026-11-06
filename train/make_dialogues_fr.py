"""Génère des conversations à plusieurs tours (train/dialogues_fr.jsonl).

But : apprendre à Alice à tenir une conversation longue — se souvenir du prénom et
des informations données plus tôt, enchaîner les calculs (« Et si j'ajoute 4 ? »),
comprendre les questions elliptiques (« Et celle de la Grèce ? »), résumer, rester
elle-même. Les conversations de test (eval/conversations_fr.py) sont exclues :
prénoms, villes, animaux et sports différents.

    python train/make_dialogues_fr.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_data_fr as D  # noqa: E402  (listes et aides de la génération mono-tour)

rng = random.Random(1)

PRENOMS = [("Léa", "f"), ("Paul", "m"), ("Emma", "f"), ("Hugo", "m"), ("Chloé", "f"), ("Lucas", "m"), ("Inès", "f"),
           ("Noah", "m"), ("Sarah", "f"), ("Adam", "m"), ("Camille", "f"), ("Louis", "m"), ("Manon", "f"),
           ("Jules", "m"), ("Rova", "f"), ("Hery", "m"), ("Fara", "f"), ("Tiana", "m"), ("Haja", "m"),
           ("Voahirana", "f"), ("Andry", "m"), ("Mialy", "f"), ("Tsiry", "m"), ("Fanja", "f"), ("Rado", "m"),
           ("Sitraka", "m"), ("Hanta", "f"), ("Koto", "m"), ("Zo", "f"), ("Mathis", "m"), ("Clara", "f"),
           ("Yanis", "m"), ("Jade", "f"), ("Théo", "m"), ("Lina", "f"), ("Nathan", "m"), ("Zoé", "f")]
VILLES = ["Antananarivo", "Antsirabe", "Mahajanga", "Toliara", "Paris", "Lyon", "Marseille", "Toulouse",
          "Bordeaux", "Lille", "Nantes", "Montréal", "Bruxelles", "Genève", "Dakar", "Abidjan", "La Réunion"]
ANIMAUX = [("le chat", "m"), ("le chien", "m"), ("le lémurien", "m"), ("le cheval", "m"), ("le lion", "m"),
           ("la tortue", "f"), ("le dauphin", "m"), ("le panda", "m"), ("la girafe", "f"), ("le perroquet", "m")]
SPORTS = ["le football", "le rugby", "la natation", "le tennis", "le vélo", "la course à pied", "le judo", "la danse"]
COULEURS = ["le bleu", "le rouge", "le vert", "le jaune", "le violet", "l'orange", "le noir", "le rose"]
SYSTEM = "Tu es Alice, une assistante qui répond toujours en français, de façon courte, exacte et logique."


def de(groupe):
    """« de » + article : du football, de la danse, de l'orange."""
    if groupe.startswith("le "):
        return "du " + groupe[3:]
    if groupe.startswith("les "):
        return "des " + groupe[4:]
    return "de " + groupe


# ------------------------------------------------------------------ tours « intercalaires »
SINGLE = [(q, a) for q, a in D.OUT if len(a) < 140 and "?" in q and not q.startswith(("What", "Who", "How", "Are"))]


def filler():
    """Un échange indépendant, avec son sujet pour les résumés."""
    kind = rng.random()
    if kind < 0.3:
        de_pays, cap = rng.choice(D.CAPITALS)
        return f"Quelle est la capitale {de_pays} ?", f"La capitale {de_pays} est {cap}.", f"de la capitale {de_pays}"
    if kind < 0.55:
        un, le, nom, d = rng.choice(D.DEFS)
        art = le if nom in D.DEFINI else un
        sujet = D.le_nom(art, nom)
        verbe = "sont" if art in ("des", "les") else "est"
        return f"C'est quoi {sujet} ?", f"{sujet[0].upper() + sujet[1:]} {verbe} {d}.", de(D.le_nom(le, nom))
    if kind < 0.75:
        a, b = rng.randint(2, 20), rng.randint(2, 20)
        return f"Combien font {a} plus {b} ?", f"{a} plus {b} font {a + b}.", "d'un calcul"
    q, a = rng.choice(SINGLE)
    return q, a, None


def fillers(n):
    return [filler() for _ in range(n)]


# ------------------------------------------------------------------ types de conversations
def conv_prenom():
    p, g = rng.choice(PRENOMS)
    intro = rng.choice([f"Bonjour, je m'appelle {p}.", f"Salut ! Moi c'est {p}.", f"Je m'appelle {p}.",
                        f"Bonjour Alice, je suis {p}.", f"Coucou, c'est {p} !"])
    turns = [(intro, rng.choice([f"Bonjour {p} ! Enchantée. Comment puis-je t'aider ?",
                                 f"Enchantée, {p} ! Que puis-je faire pour toi ?",
                                 f"Salut {p} ! Je suis Alice. Pose-moi tes questions."]))]
    turns += [(q, a) for q, a, _ in fillers(rng.randint(1, 4))]
    ask = rng.choice(["Comment je m'appelle ?", "Tu te souviens de mon prénom ?", "C'est quoi mon prénom ?",
                      "Au fait, comment je m'appelle ?", "Tu sais encore qui je suis ?"])
    turns.append((ask, rng.choice([f"Tu t'appelles {p}.", f"Oui, tu t'appelles {p} !", f"Ton prénom est {p}."])))
    if rng.random() < 0.4:
        turns.append((rng.choice(["Merci, au revoir !", "Bonne journée !", "À plus tard."]),
                      rng.choice([f"Au revoir {p} ! À bientôt.", f"Bonne journée {p} !", f"À bientôt, {p} !"])))
    return turns


def conv_faits():
    p, g = rng.choice(PRENOMS)
    age = rng.randint(8, 70)
    ville = rng.choice(VILLES)
    animal, ga = rng.choice(ANIMAUX)
    sport = rng.choice(SPORTS)
    couleur = rng.choice(COULEURS)
    faits = [
        (f"J'ai {age} ans.", rng.choice(["D'accord, c'est noté !", f"Très bien, tu as {age} ans."]),
         rng.choice(["Quel âge j'ai ?", "Tu te souviens de mon âge ?", "J'ai quel âge déjà ?"]),
         f"Tu as {age} ans."),
        (f"J'habite à {ville}.", rng.choice(["D'accord, c'est noté !", f"{ville}, très bien !"]),
         rng.choice(["Dans quelle ville j'habite ?", "Où est-ce que j'habite ?", "Tu te souviens où j'habite ?"]),
         f"Tu habites à {ville}."),
        (f"Mon animal préféré est {animal}.", rng.choice(["Bon choix !", "C'est noté !"]),
         "Quel est mon animal préféré ?", f"Ton animal préféré est {animal}."),
        (f"J'aime beaucoup {sport}.", rng.choice(["C'est super !", "D'accord, c'est noté !"]),
         rng.choice(["Quel sport est-ce que j'aime ?", "Tu te souviens de mon sport préféré ?"]),
         f"Tu aimes {sport}."),
        (f"Ma couleur préférée est {couleur}.", "C'est noté !",
         "Quelle est ma couleur préférée ?", f"Ta couleur préférée est {couleur}."),
    ]
    rng.shuffle(faits)
    k = rng.randint(1, 3)
    turns = [(f"Bonjour, je m'appelle {p}.", f"Bonjour {p} ! Comment puis-je t'aider ?")] if rng.random() < 0.5 else []
    for dit, rep, _, _ in faits[:k]:
        turns.append((dit, rep))
        if rng.random() < 0.5:
            turns += [(q, a) for q, a, _ in fillers(1)]
    turns += [(q, a) for q, a, _ in fillers(rng.randint(0, 3))]
    for _, _, demande, reponse in rng.sample(faits[:k], k):
        turns.append((demande, reponse))
    if faits[:k] and faits[0][0].startswith("J'ai") and rng.random() < 0.6:
        n = rng.randint(2, 10)
        turns.append((f"Quel âge aurai-je dans {n} ans ?",
                      f"Tu as {age} ans. {age} plus {n} font {age + n}. Dans {n} ans, tu auras {age + n} ans."))
    return turns


def conv_calcul():
    a, b = rng.randint(2, 12), rng.randint(2, 12)
    val = a * b
    turns = [(f"Combien font {a} fois {b} ?", f"{a} fois {b} font {val}.")]
    for _ in range(rng.randint(1, 4)):
        r = rng.random()
        if r < 0.35:
            c = rng.randint(1, 20)
            turns.append((rng.choice([f"Et si j'ajoute {c} ?", f"Ajoute {c}.", f"Et plus {c} ?"]),
                          f"{val} plus {c} font {val + c}."))
            val += c
        elif r < 0.6 and val > 2:
            c = rng.randint(1, val - 1)
            turns.append((rng.choice([f"Enlève {c}.", f"Et si j'enlève {c} ?", f"Et moins {c} ?"]),
                          f"{val} moins {c} font {val - c}."))
            val -= c
        elif r < 0.8 and val % 2 == 0:
            turns.append((rng.choice(["Et la moitié ?", "Et la moitié de ce résultat ?", "Divise par 2."]),
                          f"La moitié de {val} est {val // 2}."))
            val //= 2
        else:
            turns.append((rng.choice(["Et le double ?", "Multiplie par 2.", "Et le double de ce nombre ?"]),
                          f"Le double de {val} est {val * 2}."))
            val *= 2
    return turns


def conv_probleme():
    name, g = rng.choice(D.NAMES)
    pro = "Elle" if g == "f" else "Il"
    sing, plur, food = rng.choice(D.THINGS)
    a = rng.randint(5, 20)
    b = rng.randint(1, a - 1)
    val = a - b
    verb = rng.choice(["mange", "donne", "perd"] if food else ["donne", "perd"])
    turns = [(f"{name} a {a} {plur}. {pro} en {verb} {b}. Combien lui en reste-t-il ?",
              f"{a} moins {b} font {val}. Il lui reste {D.form(val, sing, plur)}.")]
    for _ in range(rng.randint(1, 3)):
        if rng.random() < 0.55:
            c = rng.randint(1, 10)
            v = rng.choice(["achète", "reçoit", "trouve"])
            q = rng.choice([f"Et si {pro.lower()} en {v} encore {c} ?", f"Ensuite, {pro.lower()} en {v} {c}. Combien en a-t-{pro.lower()} ?"])
            turns.append((q, f"{pro} en avait {val}. {val} plus {c} font {val + c}. {pro} a maintenant {D.form(val + c, sing, plur)}."))
            val += c
        elif val > 1:
            c = rng.randint(1, val - 1)
            q = rng.choice([f"Et si {pro.lower()} en perd encore {c} ?", f"Puis {pro.lower()} en donne {c}. Il lui en reste combien ?"])
            turns.append((q, f"{pro} en avait {val}. {val} moins {c} font {val - c}. Il lui reste {D.form(val - c, sing, plur)}."))
            val -= c
    return turns


def conv_elliptique():
    if rng.random() < 0.5:
        pays = rng.sample(D.CAPITALS, rng.randint(2, 4))
        de0, cap0 = pays[0]
        turns = [(f"Quelle est la capitale {de0} ?", f"La capitale {de0} est {cap0}.")]
        for de_p, cap in pays[1:]:
            q = rng.choice([f"Et celle {de_p} ?", f"Et {de_p} ?"])
            turns.append((q, f"La capitale {de_p} est {cap}."))
        return turns
    items = rng.sample(D.DEFS, rng.randint(2, 4))
    turns = []
    for i, (un, le, nom, d) in enumerate(items):
        art = le if nom in D.DEFINI else un
        sujet = D.le_nom(art, nom)
        verbe = "sont" if art in ("des", "les") else "est"
        q = f"C'est quoi {sujet} ?" if i == 0 else rng.choice([f"Et {sujet} ?", f"Et {sujet}, c'est quoi ?"])
        turns.append((q, f"{sujet[0].upper() + sujet[1:]} {verbe} {d}."))
    return turns


def conv_retenir():
    n = rng.choice([rng.randint(10, 99), rng.randint(100, 999)])
    mot = rng.choice(["nombre", "code", "chiffre"])
    turns = [(rng.choice([f"Retiens ce {mot} : {n}.", f"Souviens-toi du {mot} {n}.", f"Garde en mémoire le {mot} {n}."]),
              f"D'accord, je retiens {n}.")]
    turns += [(q, a) for q, a, _ in fillers(rng.randint(1, 4))]
    turns.append((rng.choice([f"Quel {mot} je t'ai demandé de retenir ?", f"C'était quoi le {mot} ?",
                              f"Tu te souviens du {mot} ?"]), f"Tu m'as demandé de retenir {n}."))
    if rng.random() < 0.5:
        c = rng.randint(1, 50)
        turns.append((f"Ajoute {c} à ce {mot}.", f"{n} plus {c} font {n + c}."))
    return turns


def conv_resume():
    items = [f for f in fillers(6) if f[2]][:rng.randint(2, 4)]
    if len(items) < 2:
        return None
    turns = [(q, a) for q, a, _ in items]
    sujets = []
    for _, _, s in items:
        if s not in sujets:
            sujets.append(s)
    liste = sujets[0] if len(sujets) == 1 else ", ".join(sujets[:-1]) + " et " + sujets[-1]
    turns.append((rng.choice(["De quoi avons-nous parlé ?", "Tu peux résumer notre conversation ?",
                              "On a parlé de quoi jusqu'ici ?"]),
                  f"Nous avons parlé {liste}."))
    return turns


def conv_identite():
    turns = [(rng.choice(["Qui es-tu ?", "Tu es qui ?", "Présente-toi."]),
              "Je suis Alice, une intelligence artificielle qui parle et raisonne en français.")]
    turns += [(q, a) for q, a, _ in fillers(rng.randint(0, 2))]
    turns.append((rng.choice(["Tu es Qwen, non ?", "En vrai, tu es ChatGPT ?", "Tu es quel modèle déjà ?",
                              "Qui t'a créée ?"]),
                  rng.choice(["Non, je suis Alice. J'ai été construite à partir d'un modèle de langage libre, puis "
                              "entraînée pour parler français.",
                              "Je m'appelle Alice : un modèle de langage entraîné pour parler et raisonner en français."])))
    turns.append((rng.choice(["Tu t'appelles comment déjà ?", "Rappelle-moi ton nom.", "Et ton nom, c'est ?"]),
                  "Je m'appelle Alice."))
    return turns


SCRIPTS = [  # petites conversations écrites à la main
    [("Bonjour Alice !", "Bonjour ! Comment vas-tu aujourd'hui ?"),
     ("Je suis un peu fatigué.", "Je suis désolée. Tu as peut-être besoin de te reposer un peu ou de boire de l'eau."),
     ("Tu as raison, merci.", "Avec plaisir ! Prends soin de toi."),
     ("Tu peux m'aider à réviser les calculs ?", "Bien sûr ! Combien font 7 fois 6 ?"),
     ("42", "Bravo, c'est juste : 7 fois 6 font 42 !")],
    [("J'ai un examen demain.", "Bon courage ! Sur quelle matière porte ton examen ?"),
     ("Les mathématiques.", "Très bien. Révise les tables et les problèmes en plusieurs étapes, et dors bien cette nuit."),
     ("Donne-moi un exercice.", "Voici : Léa a 15 billes, elle en donne 6, puis en gagne 4. Combien en a-t-elle ?"),
     ("13", "Bravo ! 15 moins 6 font 9, puis 9 plus 4 font 13. C'est juste.")],
    [("Je m'ennuie.", "Veux-tu une devinette ou une petite question de calcul ?"),
     ("Une devinette !", "Qu'est-ce qui a des aiguilles mais ne pique pas ?"),
     ("Je ne sais pas.", "Une horloge ! Ses aiguilles indiquent l'heure."),
     ("Une autre !", "Qu'est-ce qui monte et descend sans jamais bouger ? Un escalier !")],
    [("Tu peux me conseiller un fruit ?", "La banane est un bon choix : elle est sucrée et donne de l'énergie."),
     ("Et un légume ?", "La carotte : elle est bonne crue ou cuite, et pleine de vitamines."),
     ("Merci Alice.", "De rien ! Bon appétit.")],
    [("Bonjour", "Bonjour ! Je suis Alice. Comment puis-je t'aider ?"),
     ("Je voudrais apprendre des mots en anglais.", "Avec plaisir ! « Chat » se dit « cat », et « pomme » se dit « apple »."),
     ("Et soleil ?", "« Soleil » se dit « sun » en anglais."),
     ("Et lune ?", "« Lune » se dit « moon » en anglais."),
     ("Merci !", "De rien, bonne révision !")],
    [("Il pleut aujourd'hui.", "Pense à prendre un parapluie si tu sors !"),
     ("Je reste à la maison.", "Bonne idée. Tu peux lire un livre ou regarder un film."),
     ("Tu as une idée de jeu ?", "Tu peux faire un puzzle, un jeu de cartes, ou me poser des devinettes !")],
    [("Tu peux te tromper ?", "Oui, je peux me tromper. N'hésite pas à vérifier mes réponses importantes."),
     ("Pourquoi ?", "Parce que je suis un petit modèle : j'ai appris à partir d'exemples, et je ne sais pas tout."),
     ("D'accord, merci pour ton honnêteté.", "Avec plaisir !")],
]


TYPES = [(conv_prenom, 300), (conv_faits, 350), (conv_calcul, 250), (conv_probleme, 250), (conv_elliptique, 250),
         (conv_retenir, 200), (conv_resume, 150), (conv_identite, 120)]

FORBIDDEN = {"mahery", "solène", "bastien", "nirina", "lalaina", "toamasina", "fianarantsoa", "hibou", "basket",
             "ophélie", "dina", "brilvane", "14 plus 9"}


def to_messages(turns):
    msgs = [{"role": "system", "content": SYSTEM}] if rng.random() < 0.8 else []
    for u, a in turns:
        msgs += [{"role": "user", "content": u}, {"role": "assistant", "content": a}]
    return msgs


def long_conv():
    """Enchaîne plusieurs conversations : jusqu'à ~20 tours."""
    turns = []
    for _ in range(rng.randint(2, 4)):
        fn = rng.choice([t[0] for t in TYPES])
        part = fn()
        if part:
            turns += part
    return turns


def main():
    convs = []
    for fn, n in TYPES:
        for _ in range(n):
            t = fn()
            if t:
                convs.append(t)
    for _ in range(250):
        convs.append(long_conv())
    for s in SCRIPTS:
        for _ in range(3):
            convs.append(s)
    rows = []
    for t in convs:
        text = " ".join(u + " " + a for u, a in t).lower()
        if any(w in text for w in FORBIDDEN):
            continue
        rows.append({"messages": to_messages([(D.elide(u), D.elide(a)) for u, a in t])})
    rng.shuffle(rows)
    path = Path(__file__).with_name("dialogues_fr.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_turns = [sum(m["role"] == "user" for m in r["messages"]) for r in rows]
    print(f"{len(rows)} conversations écrites dans {path.name} "
          f"({sum(n_turns) / len(n_turns):.1f} tours en moyenne, jusqu'à {max(n_turns)})")


if __name__ == "__main__":
    main()
