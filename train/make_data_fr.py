"""Génère le jeu d'entraînement français d'Alice (train/data_fr.jsonl).

Tout est écrit à la main ou produit par des gabarits vérifiés (calculs exacts,
accords en genre et en nombre). Les questions d'évaluation (eval/questions_fr.py,
les deux séries) sont exclues, ainsi que leurs nombres et leurs mots, pour que
les scores mesurent une vraie généralisation.

    python train/make_data_fr.py                      # pour Qwen2.5-0.5B (par défaut)
    ALICE_BASE=smollm2 python train/make_data_fr.py   # pour SmolLM2-135M
"""
import json
import os
import random
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from questions_fr import CASES, CASES_HELDOUT, CASES_NIVEAUX, CASES_NIVEAUX2, CASES_RAISONNEMENT  # noqa: E402

rng = random.Random(0)

# Modèle de base (réponses d'Alice sur son identité) : ALICE_BASE=smollm2 ou qwen2.5
BASES = {
    "smollm2": {"nom": "SmolLM2", "complet": "SmolLM2-135M", "taille": "135 millions", "auteur": "Hugging Face"},
    "qwen2.5": {"nom": "Qwen2.5", "complet": "Qwen2.5-0.5B", "taille": "500 millions", "auteur": "Alibaba Cloud"},
}
B = BASES[os.environ.get("ALICE_BASE", "qwen2.5")]
OUT = []


def add(q, a, n=1):
    for _ in range(n):
        OUT.append((q, a))


# ------------------------------------------------------------------ exclusions
# Nombres, mots et sujets présents dans l'évaluation : jamais dans l'entraînement.
BAD_PAIRS = {(12, 7), (3, 4), (20, 8), (9, 6), (10, 2), (5, 2), (3, 4), (4, 2), (4, 3),
             (8, 5), (6, 3), (15, 9), (14, 11), (12, 4), (9, 3), (2, 5), (2, 4), (5, 2)}
BAD_PAIRS |= {(b, a) for a, b in BAD_PAIRS}
BAD_WORDS = {"grand", "petit", "jour", "nuit", "cheval", "chevaux", "dog", "chien", "house", "maison",
             "haut", "bas", "rapide", "lent", "journal", "journaux", "water", "eau", "book", "livre",
             "red", "rouge", "œil", "yeux"}


def que(word):
    """« que » élidé devant une voyelle : qu'Inès, qu'une pierre."""
    return "qu'" + word if norm(word)[:1] in tuple("aeiouy") else "que " + word


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"\W+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


EVAL_QUESTIONS = {norm(q) for q, _, _ in CASES + CASES_HELDOUT + CASES_RAISONNEMENT + CASES_NIVEAUX + CASES_NIVEAUX2}

# ------------------------------------------------------------------ capitales
CAPITALS = [  # (complément « de … », capitale) — sans les pays de l'évaluation
    ("du Portugal", "Lisbonne"), ("de la Belgique", "Bruxelles"), ("de la Suisse", "Berne"),
    ("de l'Autriche", "Vienne"), ("des Pays-Bas", "Amsterdam"), ("du Royaume-Uni", "Londres"),
    ("de l'Irlande", "Dublin"), ("de la Grèce", "Athènes"), ("de la Pologne", "Varsovie"),
    ("de la Suède", "Stockholm"), ("de la Norvège", "Oslo"), ("du Danemark", "Copenhague"),
    ("de la Finlande", "Helsinki"), ("de la Hongrie", "Budapest"), ("de la République tchèque", "Prague"),
    ("de la Roumanie", "Bucarest"), ("de la Bulgarie", "Sofia"), ("de la Croatie", "Zagreb"),
    ("de la Serbie", "Belgrade"), ("de la Turquie", "Ankara"), ("de la Chine", "Pékin"),
    ("de l'Inde", "New Delhi"), ("de la Corée du Sud", "Séoul"), ("du Viêt Nam", "Hanoï"),
    ("de la Thaïlande", "Bangkok"), ("de l'Indonésie", "Jakarta"), ("des Philippines", "Manille"),
    ("de l'Australie", "Canberra"), ("de la Nouvelle-Zélande", "Wellington"),
    ("des États-Unis", "Washington"), ("du Mexique", "Mexico"), ("du Brésil", "Brasilia"),
    ("de l'Argentine", "Buenos Aires"), ("du Chili", "Santiago"), ("du Pérou", "Lima"),
    ("de la Colombie", "Bogota"), ("du Venezuela", "Caracas"), ("de Cuba", "La Havane"),
    ("du Maroc", "Rabat"), ("de l'Algérie", "Alger"), ("de la Tunisie", "Tunis"),
    ("du Sénégal", "Dakar"), ("du Mali", "Bamako"), ("du Kenya", "Nairobi"),
    ("de l'Éthiopie", "Addis-Abeba"), ("du Nigeria", "Abuja"), ("de Madagascar", "Antananarivo"),
    ("du Cameroun", "Yaoundé"), ("de l'Iran", "Téhéran"), ("de l'Irak", "Bagdad"),
    ("de l'Arabie saoudite", "Riyad"), ("du Liban", "Beyrouth"), ("du Pakistan", "Islamabad"),
    ("de l'Afghanistan", "Kaboul"), ("de l'Islande", "Reykjavik"), ("du Luxembourg", "Luxembourg"),
]
for de, cap in CAPITALS:
    add(f"Quelle est la capitale {de} ?", f"La capitale {de} est {cap}.")
    add(f"Quelle ville est la capitale {de} ?", f"La capitale {de} est {cap}.")
    add(f"{cap} est la capitale de quel pays ?", f"{cap} est la capitale {de}.")

# ------------------------------------------------------------------ calcul
NUM = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix"]


def arith(a, b, op):
    if (a, b) in BAD_PAIRS:
        return
    word, res = {"+": ("plus", a + b), "-": ("moins", a - b), "*": ("fois", a * b),
                 "/": ("divisé par", a // b if b else None)}[op]
    verb = "égale" if op == "/" else "font"
    sym = {"+": "+", "-": "-", "*": "×", "/": "÷"}[op]
    style = rng.randrange(6)
    if style == 0:
        add(f"Combien font {a} {word} {b} ?", f"{a} {word} {b} {verb} {res}.")
    elif style == 1:
        add(f"Combien fait {a} {sym} {b} ?", f"{a} {sym} {b} = {res}.")
    elif style == 2:
        add(f"Calcule {a} {word} {b}.", f"{a} {word} {b} {verb} {res}.")
    elif style == 3:
        add(f"Quel est le résultat de {a} {word} {b} ?", f"Le résultat de {a} {word} {b} est {res}.")
    elif style == 4:
        add(f"{a} {word} {b}, ça fait combien ?", f"{a} {word} {b} {verb} {res}.")
    elif a <= 10 and b <= 10 and res <= 10:
        add(f"Combien font {NUM[a]} {word} {NUM[b]} ?", f"{NUM[a].capitalize()} {word} {NUM[b]} {verb} {NUM[res]}.")
    else:
        add(f"Combien font {a} {word} {b} ?", f"{a} {word} {b} {verb} {res}.")


for _ in range(330):
    a, b = rng.randint(0, 40), rng.randint(0, 40)
    arith(a, b, "+")
for _ in range(260):
    a = rng.randint(1, 50)
    arith(a, rng.randint(0, a), "-")
for _ in range(220):
    arith(rng.randint(1, 10), rng.randint(1, 10), "*")
for _ in range(120):
    b, q = rng.randint(1, 10), rng.randint(1, 10)
    arith(b * q, b, "/")
for n in range(2, 21):
    if n not in (5, 10):
        add(f"Quel est le double de {n} ?", f"Le double de {n} est {2 * n}.")
    if n % 2 == 0 and n not in (10, 12):
        add(f"Quelle est la moitié de {n} ?", f"La moitié de {n} est {n // 2}.")

# ------------------------------------------------------------------ problèmes
NAMES = [("Léa", "f"), ("Paul", "m"), ("Emma", "f"), ("Hugo", "m"), ("Chloé", "f"), ("Lucas", "m"),
         ("Inès", "f"), ("Noah", "m"), ("Sarah", "f"), ("Adam", "m"), ("Camille", "f"), ("Louis", "m"),
         ("Manon", "f"), ("Gabriel", "m"), ("Lina", "f"), ("Jules", "m"), ("Nina", "f"), ("Malo", "m"),
         ("Rova", "f"), ("Hery", "m"), ("Fara", "f"), ("Tiana", "m")]
# (singulier, pluriel, se mange ?)
THINGS = [("pomme", "pommes", True), ("bille", "billes", False), ("bonbon", "bonbons", True),
          ("crayon", "crayons", False), ("fleur", "fleurs", False), ("gâteau", "gâteaux", True),
          ("ballon", "ballons", False), ("carte", "cartes", False), ("biscuit", "biscuits", True),
          ("image", "images", False), ("jouet", "jouets", False), ("orange", "oranges", True),
          ("bouteille", "bouteilles", False), ("timbre", "timbres", False), ("cerise", "cerises", True),
          ("euro", "euros", False), ("œuf", "œufs", True), ("banane", "bananes", True)]


def form(n, sing, plur):
    return f"{n} {sing if n == 1 else plur}"


def problems():
    name, g = rng.choice(NAMES)
    pro = "Elle" if g == "f" else "Il"
    sing, plur, food = rng.choice(THINGS)
    kind = rng.randrange(4)
    if kind == 0:  # perte
        a = rng.randint(3, 20)
        b = rng.randint(1, a - 1)
        if (a, b) in BAD_PAIRS:
            return
        verb = rng.choice(["mange", "donne", "perd"] if food else ["donne", "perd", "vend"])
        add(f"{name} a {a} {plur}. {pro} en {verb} {b}. Combien lui en reste-t-il ?",
            f"{a} moins {b} font {a - b}. Il lui reste {form(a - b, sing, plur)}.")
    elif kind == 1:  # gain
        a, b = rng.randint(1, 15), rng.randint(1, 15)
        if (a, b) in BAD_PAIRS:
            return
        verb = rng.choice(["gagne", "reçoit", "trouve", "achète"])
        t = "a-t-elle" if g == "f" else "a-t-il"
        add(f"{name} a {form(a, sing, plur)}. {pro} en {verb} {b}. Combien de {plur} {t} maintenant ?",
            f"{a} plus {b} font {a + b}. {pro} a maintenant {a + b} {plur}.")
    elif kind == 2:  # à la première personne
        a = rng.randint(3, 20)
        b = rng.randint(1, a - 1)
        if (a, b) in BAD_PAIRS:
            return
        verb = rng.choice(["mange", "donne", "perds"] if food else ["donne", "perds", "vends"])
        add(f"Si j'ai {a} {plur} et que j'en {verb} {b}, combien m'en reste-t-il ?",
            f"{a} moins {b} font {a - b}. Il te reste {form(a - b, sing, plur)}.")
    else:  # deux personnes
        name2, g2 = rng.choice([n for n in NAMES if n[0] != name])
        ils = "elles" if g == g2 == "f" else "ils"
        a, b = rng.randint(1, 15), rng.randint(1, 15)
        if (a, b) in BAD_PAIRS:
            return
        add(f"{name} a {form(a, sing, plur)} et {name2} a {form(b, sing, plur)}. Combien de {plur} ont-{ils} en tout ?",
            f"{a} plus {b} font {a + b}. {ils.capitalize()} ont {a + b} {plur} en tout.")


for _ in range(650):
    problems()

# (un/une, singulier, pluriel, nombre, partie au pluriel) — sans voiture, chat, vélo, oiseau, araignée
GROUPS = [("Un", "chien", "chiens", 4, "pattes"), ("Une", "vache", "vaches", 4, "pattes"),
          ("Une", "poule", "poules", 2, "pattes"), ("Un", "canard", "canards", 2, "pattes"),
          ("Une", "fourmi", "fourmis", 6, "pattes"), ("Un", "mouton", "moutons", 4, "pattes"),
          ("Un", "tricycle", "tricycles", 3, "roues"), ("Une", "moto", "motos", 2, "roues"),
          ("Un", "camion", "camions", 6, "roues"), ("Une", "table", "tables", 4, "pieds"),
          ("Une", "chaise", "chaises", 4, "pieds"), ("Une", "main", "mains", 5, "doigts"),
          ("Une", "boîte", "boîtes", 6, "œufs"), ("Un", "trèfle", "trèfles", 3, "feuilles"),
          ("Un", "triangle", "triangles", 3, "côtés"), ("Un", "carré", "carrés", 4, "côtés"),
          ("Un", "sac", "sacs", 5, "pommes"), ("Une", "classe", "classes", 25, "élèves")]
for un, sing, plur, k, part in GROUPS:
    for n in rng.sample(range(2, 10), 5):
        if (k, n) in BAD_PAIRS and k < 10:
            continue
        add(f"{un} {sing} a {k} {part}. Combien de {part} ont {n} {plur} ?",
            f"{n} fois {k} font {n * k}. {n} {plur} ont {n * k} {part}.")

# ------------------------------------------------------------------ comparaisons
ADJ = [("grand", "petit"), ("âgé", "jeune"), ("rapide", "lent"), ("fort", "faible"), ("lourd", "léger")]


def accord(adj, g):
    if g == "m" or adj.endswith("e"):
        return adj
    return {"léger": "légère"}.get(adj, adj + "e")


for _ in range(240):
    (a, ga), (b, gb), (c, gc) = rng.sample(NAMES, 3)
    up, down = rng.choice(ADJ)
    q = f"{a} est plus {accord(up, ga)} {que(b)}. {b} est plus {accord(up, gb)} {que(c)}. "
    if rng.random() < 0.5:
        art = "la" if gc == "f" else "le"
        q += f"Qui est {art} plus {accord(down, gc)} ?"
        ans = f"{c} est {art} plus {accord(down, gc)}."
    else:
        art = "la" if ga == "f" else "le"
        q += f"Qui est {art} plus {accord(up, ga)} ?"
        ans = f"{a} est {art} plus {accord(up, ga)}."
    if norm(q) not in EVAL_QUESTIONS:
        add(q, ans)

# ------------------------------------------------------------------ jours et mois
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
          "septembre", "octobre", "novembre", "décembre"]
for i, d in enumerate(DAYS):
    nxt, prv = DAYS[(i + 1) % 7], DAYS[i - 1]
    add(f"Si aujourd'hui est {d}, quel jour serons-nous demain ?", f"Si aujourd'hui est {d}, demain nous serons {nxt}.")
    add(f"Si aujourd'hui est {d}, quel jour étions-nous hier ?", f"Si aujourd'hui est {d}, hier nous étions {prv}.")
    add(f"Aujourd'hui, c'est {d}. Quel jour serons-nous demain ?", f"Demain, nous serons {nxt}.")
    add(f"Quel jour vient après le {d} ?", f"Le {nxt} vient après le {d}.")
    add(f"Quel jour vient avant le {d} ?", f"Le {prv} vient avant le {d}.")
    add(f"Si aujourd'hui est {d}, quel jour serons-nous après-demain ?",
        f"Si aujourd'hui est {d}, après-demain nous serons {DAYS[(i + 2) % 7]}.")
for i, m in enumerate(MONTHS):
    de = "d'" if m[0] in "aeiou" else "de "
    add(f"Quel mois vient après {m} ?", f"Le mois qui vient après {m} est {MONTHS[(i + 1) % 12]}.")
    add(f"Quel mois vient avant {m} ?", f"Le mois qui vient avant {m} est {MONTHS[i - 1]}.")
    add(f"Quel est le numéro du mois {de}{m} ?", f"{m.capitalize()} est le mois numéro {i + 1}.")
add("Quels sont les jours de la semaine ?", "Les jours de la semaine sont : " + ", ".join(DAYS) + ".")
add("Quel est le dernier jour de la semaine ?", "Le dernier jour de la semaine est dimanche.")
add("Quel est le dernier mois de l'année ?", "Le dernier mois de l'année est décembre.")
add("Quelles sont les quatre saisons ?", "Les quatre saisons sont le printemps, l'été, l'automne et l'hiver.")
for s, n in [("printemps", "l'été"), ("été", "l'automne"), ("automne", "l'hiver"), ("hiver", "le printemps")]:
    pre = "le " if s == "printemps" else "l'"
    add(f"Quelle saison vient après {pre}{s} ?", f"Après {pre}{s} vient {n}.")

# ------------------------------------------------------------------ propriétés
# (sujet, genre, bonne réponse au masculin, mauvaise) — sans le feu ni la glace
PROPS = [("le soleil", "m", "chaud", "froid"), ("la neige", "f", "froid", "chaud"), ("le café", "m", "chaud", "froid"),
         ("un glaçon", "m", "froid", "chaud"), ("la lave", "f", "chaud", "froid"), ("l'hiver", "m", "froid", "chaud"),
         ("le sucre", "m", "sucré", "salé"), ("la mer", "f", "salé", "sucré"), ("le miel", "m", "sucré", "salé"),
         ("une plume", "f", "léger", "lourd"), ("un éléphant", "m", "lourd", "léger"), ("une pierre", "f", "dur", "mou"),
         ("un oreiller", "m", "mou", "dur"), ("le citron", "m", "acide", "sucré"), ("une tortue", "f", "lent", "rapide"),
         ("un guépard", "m", "rapide", "lent"), ("la nuit", "f", "sombre", "clair"), ("une souris", "f", "petit", "grand"),
         ("une girafe", "f", "grand", "petit"), ("le désert", "m", "sec", "mouillé")]
FEM = {"chaud": "chaude", "froid": "froide", "sucré": "sucrée", "salé": "salée", "léger": "légère",
       "lourd": "lourde", "dur": "dure", "mou": "molle", "acide": "acide", "lent": "lente", "rapide": "rapide",
       "sombre": "sombre", "clair": "claire", "petit": "petite", "grand": "grande", "sec": "sèche", "mouillé": "mouillée"}
for subj, g, good, bad in PROPS:
    f = (lambda x: FEM[x]) if g == "f" else (lambda x: x)
    x, y = (good, bad) if rng.random() < 0.5 else (bad, good)
    add(f"Est-ce {que(subj)} est {f(x)} ou {f(y)} ?", f"{subj[0].upper() + subj[1:]} est {f(good)}.")

# ------------------------------------------------------------------ vocabulaire
OPPOSITES = [("chaud", "froid"), ("long", "court"), ("vieux", "jeune"), ("riche", "pauvre"), ("fort", "faible"),
             ("plein", "vide"), ("ouvert", "fermé"), ("propre", "sale"), ("facile", "difficile"),
             ("heureux", "malheureux"), ("triste", "joyeux"), ("lourd", "léger"), ("dur", "mou"),
             ("clair", "sombre"), ("beau", "laid"), ("bon", "mauvais"), ("vrai", "faux"), ("mouillé", "sec"),
             ("large", "étroit"), ("gentil", "méchant"), ("devant", "derrière"), ("dessus", "dessous"),
             ("gauche", "droite"), ("monter", "descendre"), ("entrer", "sortir"), ("ouvrir", "fermer"),
             ("aimer", "détester"), ("gagner", "perdre"), ("acheter", "vendre"), ("commencer", "finir"),
             ("rire", "pleurer"), ("allumer", "éteindre"), ("noir", "blanc"), ("matin", "soir"),
             ("été", "hiver"), ("ami", "ennemi"), ("guerre", "paix"), ("début", "fin"), ("oui", "non"),
             ("tout", "rien"), ("toujours", "jamais"), ("avant", "après"), ("intérieur", "extérieur"),
             ("nord", "sud"), ("est", "ouest"), ("gros", "maigre"), ("chaud", "froid"), ("doux", "rugueux"),
             ("présent", "absent"), ("possible", "impossible"), ("utile", "inutile"), ("calme", "agité")]
for a, b in OPPOSITES:
    add(f"Quel est le contraire de « {a} » ?", f"Le contraire de « {a} » est « {b} ».")
    add(f"Quel est le contraire de « {b} » ?", f"Le contraire de « {b} » est « {a} ».")
    if rng.random() < 0.3:
        add(f"Donne-moi le contraire de « {a} ».", f"Le contraire de « {a} » est « {b} ».")

PLURALS = [("animal", "animaux"), ("hôpital", "hôpitaux"), ("canal", "canaux"), ("métal", "métaux"),
           ("général", "généraux"), ("cristal", "cristaux"), ("bateau", "bateaux"), ("gâteau", "gâteaux"),
           ("château", "châteaux"), ("oiseau", "oiseaux"), ("chapeau", "chapeaux"), ("cheveu", "cheveux"),
           ("jeu", "jeux"), ("feu", "feux"), ("bijou", "bijoux"), ("genou", "genoux"), ("caillou", "cailloux"),
           ("hibou", "hiboux"), ("chou", "choux"), ("travail", "travaux"), ("vitrail", "vitraux"),
           ("nez", "nez"), ("prix", "prix"), ("voix", "voix"), ("souris", "souris"), ("bras", "bras"),
           ("pays", "pays"), ("chat", "chats"), ("table", "tables"), ("ami", "amis"), ("fleur", "fleurs"),
           ("voiture", "voitures"), ("porte", "portes"), ("arbre", "arbres"), ("enfant", "enfants"),
           ("femme", "femmes"), ("homme", "hommes"), ("festival", "festivals"), ("bal", "bals"),
           ("carnaval", "carnavals"), ("clou", "clous"), ("trou", "trous"), ("fou", "fous"), ("pneu", "pneus"),
           ("ciel", "cieux"), ("monsieur", "messieurs"), ("madame", "mesdames")]
for s, p in PLURALS:
    add(f"Quel est le pluriel de « {s} » ?", f"Le pluriel de « {s} » est « {p} ».")
    if rng.random() < 0.3:
        add(f"Comment écrit-on « {s} » au pluriel ?", f"Au pluriel, « {s} » s'écrit « {p} ».")

WORDS = [("cat", "chat"), ("bird", "oiseau"), ("fish", "poisson"), ("horse", "cheval"), ("cow", "vache"),
         ("mouse", "souris"), ("apple", "pomme"), ("bread", "pain"), ("milk", "lait"), ("cheese", "fromage"),
         ("egg", "œuf"), ("sun", "soleil"), ("moon", "lune"), ("star", "étoile"), ("sky", "ciel"), ("sea", "mer"),
         ("tree", "arbre"), ("flower", "fleur"), ("car", "voiture"), ("train", "train"), ("boat", "bateau"),
         ("plane", "avion"), ("school", "école"), ("teacher", "professeur"), ("friend", "ami"),
         ("mother", "mère"), ("father", "père"), ("brother", "frère"), ("sister", "sœur"), ("child", "enfant"),
         ("man", "homme"), ("woman", "femme"), ("table", "table"), ("chair", "chaise"), ("door", "porte"),
         ("window", "fenêtre"), ("bed", "lit"), ("city", "ville"), ("country", "pays"), ("street", "rue"),
         ("blue", "bleu"), ("green", "vert"), ("yellow", "jaune"), ("white", "blanc"), ("black", "noir"),
         ("big", "grand"), ("small", "petit"), ("hot", "chaud"), ("cold", "froid"), ("good", "bon"),
         ("happy", "heureux"), ("sad", "triste"), ("one", "un"), ("two", "deux"), ("three", "trois"),
         ("hello", "bonjour"), ("thank you", "merci"), ("goodbye", "au revoir"), ("yes", "oui"), ("no", "non"),
         ("to eat", "manger"), ("to drink", "boire"), ("to sleep", "dormir"), ("to run", "courir"),
         ("to read", "lire"), ("to write", "écrire"), ("to speak", "parler"), ("to love", "aimer"),
         ("rain", "pluie"), ("snow", "neige"), ("wind", "vent"), ("hand", "main"), ("head", "tête"),
         ("eye", "œil"), ("heart", "cœur"), ("time", "temps"), ("day", "jour"), ("night", "nuit"),
         ("week", "semaine"), ("year", "année"), ("money", "argent"), ("music", "musique"), ("game", "jeu"),
         ("work", "travail"), ("garden", "jardin"), ("kitchen", "cuisine"), ("key", "clé"), ("shoe", "chaussure")]
for en, fr in WORDS:
    if en in BAD_WORDS or fr in BAD_WORDS:
        continue
    style = rng.randrange(3)
    if style == 0:
        add(f"Traduis « {en} » en français.", f"« {en.capitalize()} » se dit « {fr} » en français.")
    elif style == 1:
        add(f"Comment dit-on « {en} » en français ?", f"« {en.capitalize()} » se dit « {fr} » en français.")
    else:
        add(f"Que veut dire « {en} » en français ?", f"« {en.capitalize()} » veut dire « {fr} » en français.")
    if rng.random() < 0.6:
        add(f"Comment dit-on « {fr} » en anglais ?", f"« {fr.capitalize()} » se dit « {en} » en anglais.")
    else:
        add(f"Traduis « {fr} » en anglais.", f"« {fr.capitalize()} » se dit « {en} » en anglais.")

# ------------------------------------------------------------------ connaissances
FACTS = [
    ("Combien y a-t-il de secondes dans une minute ?", "Il y a 60 secondes dans une minute."),
    ("Combien y a-t-il de jours dans une année ?", "Il y a 365 jours dans une année, et 366 dans une année bissextile."),
    ("Combien y a-t-il de saisons dans une année ?", "Il y a 4 saisons dans une année."),
    ("Combien y a-t-il de jours en février ?", "Février a 28 jours, ou 29 jours dans une année bissextile."),
    ("Combien de jours y a-t-il en juillet ?", "Juillet a 31 jours."),
    ("De quelle couleur est une banane mûre ?", "Une banane mûre est jaune."),
    ("De quelle couleur est le lait ?", "Le lait est blanc."),
    ("De quelle couleur est le charbon ?", "Le charbon est noir."),
    ("De quelle couleur est une carotte ?", "Une carotte est orange."),
    ("De quelle couleur est le sang ?", "Le sang est rouge."),
    ("De quelle couleur est un citron ?", "Un citron est jaune."),
    ("De quelle couleur sont les feuilles en été ?", "En été, les feuilles sont vertes."),
    ("Quelles couleurs obtient-on en mélangeant le bleu et le jaune ?", "En mélangeant le bleu et le jaune, on obtient du vert."),
    ("Quel animal fait « meuh » ?", "C'est la vache qui fait « meuh »."),
    ("Quel animal fait « cocorico » ?", "C'est le coq qui fait « cocorico »."),
    ("Quel animal fait « coin-coin » ?", "C'est le canard qui fait « coin-coin »."),
    ("Quel animal fait « bêê » ?", "C'est le mouton qui fait « bêê »."),
    ("Quel animal fait « hi-han » ?", "C'est l'âne qui fait « hi-han »."),
    ("Quel bruit fait la vache ?", "La vache fait « meuh »."),
    ("Quel est le cri du lion ?", "Le lion rugit."),
    ("Combien de pattes a une fourmi ?", "Une fourmi a 6 pattes."),
    ("Combien de pattes a une vache ?", "Une vache a 4 pattes."),
    ("Combien de pattes a une poule ?", "Une poule a 2 pattes."),
    ("Combien de pattes a un serpent ?", "Un serpent n'a pas de pattes."),
    ("Combien de pattes a un insecte ?", "Un insecte a 6 pattes."),
    ("Quel est le plus grand animal du monde ?", "Le plus grand animal du monde est la baleine bleue."),
    ("Quel est l'animal terrestre le plus rapide ?", "L'animal terrestre le plus rapide est le guépard."),
    ("Quel animal est appelé le roi des animaux ?", "Le lion est appelé le roi des animaux."),
    ("Quel animal fabrique du miel ?", "C'est l'abeille qui fabrique du miel."),
    ("Quel animal nous donne du lait ?", "La vache nous donne du lait."),
    ("Quel animal pond des œufs à la ferme ?", "C'est la poule qui pond des œufs."),
    ("Quel animal a une trompe ?", "L'éléphant a une trompe."),
    ("Quel animal a un très long cou ?", "La girafe a un très long cou."),
    ("Où vivent les poissons ?", "Les poissons vivent dans l'eau."),
    ("Quels animaux vivent à Madagascar ?", "À Madagascar vivent des lémuriens, des caméléons et des fossas."),
    ("Quel est le plus grand océan du monde ?", "Le plus grand océan du monde est l'océan Pacifique."),
    ("Quelle est la plus haute montagne du monde ?", "La plus haute montagne du monde est l'Everest."),
    ("Quelle est la plus haute montagne d'Europe occidentale ?", "La plus haute montagne d'Europe occidentale est le mont Blanc."),
    ("Quel est le plus long fleuve de France ?", "Le plus long fleuve de France est la Loire."),
    ("Quel fleuve traverse Paris ?", "La Seine traverse Paris."),
    ("Quel est le plus grand pays du monde ?", "Le plus grand pays du monde est la Russie."),
    ("Quel est le plus grand désert chaud du monde ?", "Le plus grand désert chaud du monde est le Sahara."),
    ("Madagascar est-elle une île ?", "Oui, Madagascar est une grande île de l'océan Indien."),
    ("Dans quel océan se trouve Madagascar ?", "Madagascar se trouve dans l'océan Indien."),
    ("Quelle langue parle-t-on au Brésil ?", "Au Brésil, on parle portugais."),
    ("Quelle langue parle-t-on au Mexique ?", "Au Mexique, on parle espagnol."),
    ("Quelles langues parle-t-on à Madagascar ?", "À Madagascar, on parle malgache et français."),
    ("Quelle est la monnaie de la France ?", "La monnaie de la France est l'euro."),
    ("Quelle est la monnaie du Japon ?", "La monnaie du Japon est le yen."),
    ("Quelle est la monnaie des États-Unis ?", "La monnaie des États-Unis est le dollar."),
    ("Quelle est la monnaie de Madagascar ?", "La monnaie de Madagascar est l'ariary."),
    ("Dans quelle ville se trouve la tour Eiffel ?", "La tour Eiffel se trouve à Paris."),
    ("Qu'est-ce que le Soleil ?", "Le Soleil est une étoile."),
    ("Combien y a-t-il de planètes dans le système solaire ?", "Il y a 8 planètes dans le système solaire."),
    ("Quelle planète est appelée la planète rouge ?", "Mars est appelée la planète rouge."),
    ("Sur quelle planète vivons-nous ?", "Nous vivons sur la Terre."),
    ("Quel est le satellite naturel de la Terre ?", "Le satellite naturel de la Terre est la Lune."),
    ("Quelle planète a de grands anneaux ?", "Saturne a de grands anneaux."),
    ("Qui a marché le premier sur la Lune ?", "Neil Armstrong a été le premier homme à marcher sur la Lune, en 1969."),
    ("À quelle température l'eau bout-elle ?", "L'eau bout à 100 degrés Celsius."),
    ("À quelle température l'eau gèle-t-elle ?", "L'eau gèle à 0 degré Celsius."),
    ("Quelle est la formule chimique de l'eau ?", "La formule chimique de l'eau est H2O."),
    ("Que respirons-nous pour vivre ?", "Nous respirons de l'oxygène, qui se trouve dans l'air."),
    ("De quoi une plante a-t-elle besoin pour pousser ?", "Une plante a besoin d'eau, de lumière et d'air pour pousser."),
    ("Combien d'yeux a un être humain ?", "Un être humain a 2 yeux."),
    ("Combien de doigts avons-nous en tout sur les deux mains ?", "Nous avons 10 doigts sur les deux mains."),
    ("Combien de dents a un adulte ?", "Un adulte a en général 32 dents."),
    ("À quoi sert le cœur ?", "Le cœur pompe le sang dans tout le corps."),
    ("Combien de côtés a un triangle ?", "Un triangle a 3 côtés."),
    ("Combien de côtés a un carré ?", "Un carré a 4 côtés."),
    ("Combien de côtés a un hexagone ?", "Un hexagone a 6 côtés."),
    ("Combien y a-t-il d'œufs dans une douzaine ?", "Il y a 12 œufs dans une douzaine."),
    ("Combien de centimètres y a-t-il dans un mètre ?", "Il y a 100 centimètres dans un mètre."),
    ("Combien de grammes y a-t-il dans un kilogramme ?", "Il y a 1000 grammes dans un kilogramme."),
    ("Qui a écrit « Les Misérables » ?", "Victor Hugo a écrit « Les Misérables »."),
    ("Qui a écrit « Le Petit Prince » ?", "Antoine de Saint-Exupéry a écrit « Le Petit Prince »."),
    ("Qui a peint la Joconde ?", "Léonard de Vinci a peint la Joconde."),
    ("Qui était Molière ?", "Molière était un auteur de théâtre français du XVIIe siècle."),
    ("Qui était Napoléon Bonaparte ?", "Napoléon Bonaparte était un empereur des Français."),
    ("Quel est le féminin de « acteur » ?", "Le féminin de « acteur » est « actrice »."),
    ("Quel est le féminin de « chanteur » ?", "Le féminin de « chanteur » est « chanteuse »."),
    ("Quel est le féminin de « lion » ?", "Le féminin de « lion » est « lionne »."),
    ("Quel est le petit de la vache ?", "Le petit de la vache est le veau."),
    ("Quel est le petit de la poule ?", "Le petit de la poule est le poussin."),
    ("Quel est le petit du mouton ?", "Le petit du mouton est l'agneau."),
    ("Que fait-on avec un parapluie ?", "On utilise un parapluie pour se protéger de la pluie."),
    ("Pourquoi met-on un manteau en hiver ?", "On met un manteau en hiver pour avoir chaud, car il fait froid."),
    ("Que se passe-t-il si on met de la glace au soleil ?", "La glace fond et devient de l'eau."),
    ("Pourquoi les feuilles tombent-elles en automne ?", "En automne, les arbres perdent leurs feuilles pour se protéger du froid de l'hiver."),
    ("Pourquoi faut-il se laver les mains ?", "On se lave les mains pour enlever les microbes et rester en bonne santé."),
    ("Que mange une vache ?", "Une vache mange de l'herbe."),
    ("Que fait une abeille ?", "Une abeille butine les fleurs et fabrique du miel."),
    ("À quoi sert un réfrigérateur ?", "Un réfrigérateur garde les aliments au frais."),
    ("Avec quoi écrit-on au tableau ?", "On écrit au tableau avec une craie ou un feutre."),
    ("Que fait un boulanger ?", "Un boulanger fait du pain."),
    ("Que fait un médecin ?", "Un médecin soigne les malades."),
    ("Que fait un pompier ?", "Un pompier éteint les incendies et porte secours aux gens."),
    ("Quelle est la différence entre un fruit et un légume ?", "Un fruit contient les graines de la plante, comme la pomme ; un légume est une autre partie de la plante, comme la carotte."),
    ("Est-ce que la tomate est un fruit ?", "Oui, la tomate est un fruit, même si on la cuisine comme un légume."),
]
for q, a in FACTS:
    add(q, a, 2)

# ------------------------------------------------------------------ raisonnement en étapes
# Problèmes en plusieurs étapes : la réponse pose chaque étape, puis donne le résultat
# à la fin (« D'abord… Ensuite… Il a 7 pommes. »).
def il(g):
    return "Elle" if g == "f" else "Il"


def t_il(g):
    return "t-elle" if g == "f" else "t-il"


def other(name):
    return rng.choice([n for n in NAMES if n[0] != name])


for _ in range(120):  # âges
    name, g = rng.choice(NAMES)
    a, k = rng.randint(4, 40), rng.randint(1, 12)
    kind = rng.randrange(3)
    if kind == 0:
        add(f"{name} a {a} ans. Dans {k} ans, quel âge aura-{t_il(g)} ?",
            f"Dans {k} ans, {name} aura {a} plus {k} ans. {a} plus {k} font {a + k}. {il(g)} aura {a + k} ans.")
    elif kind == 1 and a > k:
        add(f"{name} a {a} ans. Quel âge avait-{t_il(g)} il y a {k} ans ?",
            f"Il y a {k} ans, {name} avait {a} moins {k} ans. {a} moins {k} font {a - k}. {il(g)} avait {a - k} ans.")
    elif a > k:
        sib, sg = rng.choice([("son frère", "m"), ("sa sœur", "f")])
        lui = "elle" if g == "f" else "lui"
        if rng.random() < 0.5:
            add(f"{name} a {a} ans. {sib.capitalize()} a {k} ans de plus {que(lui)}. Quel âge a {sib} ?",
                f"{a} plus {k} font {a + k}. {sib.capitalize()} a {a + k} ans.")
        else:
            add(f"{name} a {a} ans. {sib.capitalize()} a {k} ans de moins {que(lui)}. Quel âge a {sib} ?",
                f"{a} moins {k} font {a - k}. {sib.capitalize()} a {a - k} ans.")

for _ in range(150):  # « de plus que » / « de moins que »
    (a_name, _), (b_name, _) = rng.sample(NAMES, 2)
    sing, plur, _food = rng.choice(THINGS)
    b, k = rng.randint(2, 20), rng.randint(1, 10)
    if rng.random() < 0.5:
        add(f"{a_name} a {k} {plur} de plus {que(b_name)}. {b_name} a {b} {plur}. Combien de {plur} a {a_name} ?",
            f"{a_name} en a {k} de plus {que(b_name)}, donc {b} plus {k} font {b + k}. {a_name} a {b + k} {plur}.")
    elif b > k:
        add(f"{a_name} a {k} {plur} de moins {que(b_name)}. {b_name} a {b} {plur}. Combien de {plur} a {a_name} ?",
            f"{a_name} en a {k} de moins {que(b_name)}, donc {b} moins {k} font {b - k}. {a_name} a {form(b - k, sing, plur)}.")

PACKS = [("Un", "paquet", "paquets", "biscuits"), ("Une", "boîte", "boîtes", "crayons"),
         ("Un", "sac", "sacs", "billes"), ("Un", "carton", "cartons", "bouteilles"),
         ("Un", "sachet", "sachets", "bonbons"), ("Un", "panier", "paniers", "pommes"),
         ("Une", "barquette", "barquettes", "fraises"), ("Un", "album", "albums", "images")]
for _ in range(150):  # paquets (multiplication)
    un, sing, plur, items = rng.choice(PACKS)
    k, n = rng.randint(2, 10), rng.randint(2, 9)
    if rng.random() < 0.5:
        add(f"{un} {sing} contient {k} {items}. J'achète {n} {plur}. Combien de {items} ai-je ?",
            f"{n} {plur} de {k} {items} : {n} fois {k} font {n * k}. Tu as {n * k} {items}.")
    else:
        name, g = rng.choice(NAMES)
        add(f"{name} a {n} {plur}. Chaque {sing} contient {k} {items}. Combien de {items} a-{t_il(g)} en tout ?",
            f"{n} fois {k} font {n * k}. {il(g)} a {n * k} {items} en tout.")

ITEMS = ["un livre", "un ballon", "un jouet", "une glace", "un cahier", "un sandwich", "une place de cinéma",
         "un gâteau", "une poupée", "un stylo", "une casquette", "un jeu"]
for _ in range(150):  # argent
    kind = rng.randrange(3)
    if kind == 0:
        a = rng.randint(5, 50)
        p = rng.randint(1, a - 1)
        add(f"J'ai {a} euros. J'achète {rng.choice(ITEMS)} à {p} euros. Combien d'argent me reste-t-il ?",
            f"{a} moins {p} font {a - p}. Il te reste {a - p} euros.")
    elif kind == 1:
        name, g = rng.choice(NAMES)
        x, y = rng.sample(ITEMS, 2)
        p, q = rng.randint(1, 15), rng.randint(1, 15)
        a = rng.randint(p + q, 50)
        add(f"{name} a {a} euros. {il(g)} achète {x} à {p} euros et {y} à {q} euros. Combien d'argent lui reste-t-il ?",
            f"D'abord, {p} plus {q} font {p + q} euros dépensés. Ensuite, {a} moins {p + q} font {a - p - q}. "
            f"Il lui reste {a - p - q} euros.")
    else:
        it = rng.choice(ITEMS)
        p, n = rng.randint(1, 10), rng.randint(2, 9)
        pl = it.split(" ", 1)[1]
        pl = " ".join(w if w in ("de", "à") else (w + "x" if w.endswith(("eau", "eu")) else (w if w.endswith("s") else w + "s"))
                      for w in pl.split())
        add(f"{it.capitalize()} coûte {p} euros. Combien coûtent {n} {pl} ?",
            f"{n} fois {p} font {n * p}. {n} {pl} coûtent {n * p} euros.")

for _ in range(250):  # deux étapes
    name, g = rng.choice(NAMES)
    sing, plur, food = rng.choice(THINGS)
    lose = rng.choice(["mange", "donne", "perd"] if food else ["donne", "perd", "vend"])
    gain = rng.choice(["achète", "reçoit", "trouve", "gagne"])
    a = rng.randint(3, 20)
    b = rng.randint(1, a - 1)
    c = rng.randint(1, 12)
    if rng.random() < 0.5:
        add(f"{name} a {a} {plur}. {il(g)} en {lose} {b}, puis {il(g).lower()} en {gain} {c}. Combien de {plur} a-{t_il(g)} ?",
            f"D'abord, {a} moins {b} font {a - b}. Ensuite, {a - b} plus {c} font {a - b + c}. "
            f"{il(g)} a {a - b + c} {plur}.")
    else:
        b2 = rng.randint(1, a + c - 1)
        add(f"{name} a {form(a, sing, plur)}. {il(g)} en {gain} {c}, puis {il(g).lower()} en {lose} {b2}. Combien de {plur} a-{t_il(g)} ?",
            f"D'abord, {a} plus {c} font {a + c}. Ensuite, {a + c} moins {b2} font {a + c - b2}. "
            f"{il(g)} a {form(a + c - b2, sing, plur)}.")
for _ in range(80):  # deux étapes avec de l'argent
    name, g = rng.choice(NAMES)
    a, b = rng.randint(2, 30), rng.randint(1, 20)
    c = rng.randint(1, a + b - 1)
    add(f"{name} a {a} euros. {il(g)} gagne {b} euros, puis {il(g).lower()} dépense {c} euros. Combien d'euros a-{t_il(g)} ?",
        f"D'abord, {a} plus {b} font {a + b}. Ensuite, {a + b} moins {c} font {a + b - c}. {il(g)} a {a + b - c} euros.")

for _ in range(200):  # comparer des nombres
    x, y = rng.sample(range(0, 100), 2)
    kind = rng.randrange(3)
    if kind == 0:
        add(f"Quel est le plus grand nombre : {x} ou {y} ?",
            f"{max(x, y)} est plus grand que {min(x, y)}. Le plus grand nombre est {max(x, y)}.")
    elif kind == 1:
        add(f"Quel est le plus petit nombre : {x} ou {y} ?",
            f"{min(x, y)} est plus petit que {max(x, y)}. Le plus petit nombre est {min(x, y)}.")
    elif x > y:
        add(f"Est-ce que {x} est plus grand que {y} ?", f"Oui, {x} est plus grand que {y}.")
    else:
        add(f"Est-ce que {x} est plus grand que {y} ?", f"Non, {x} est plus petit que {y}.")

for _ in range(120):  # nombre suivant / précédent
    n = rng.randint(1, 99)
    if rng.random() < 0.6:
        add(f"Quel nombre vient après {n} ?", f"Le nombre qui vient après {n} est {n + 1}.")
    else:
        add(f"Quel nombre vient avant {n} ?", f"Le nombre qui vient avant {n} est {n - 1}.")

for _ in range(150):  # suites
    d = rng.choice([1, 2, 3, 5, 10])
    s0 = rng.randint(0, 30)
    if rng.random() < 0.7:
        seq = [s0 + i * d for i in range(4)]
        add(f"Complète la suite : {', '.join(map(str, seq))}, ...",
            f"On ajoute {d} à chaque fois : {seq[-1]} plus {d} font {seq[-1] + d}. Le nombre suivant est {seq[-1] + d}.")
    else:
        s0 = rng.randint(4 * d, 4 * d + 40)
        seq = [s0 - i * d for i in range(4)]
        add(f"Complète la suite : {', '.join(map(str, seq))}, ...",
            f"On enlève {d} à chaque fois : {seq[-1]} moins {d} font {seq[-1] - d}. Le nombre suivant est {seq[-1] - d}.")

LOGIC = [  # (question, réponse) — logique simple, écrite à la main
    ("Tous les chats sont des animaux. Minou est un chat. Minou est-il un animal ?",
     "Oui. Tous les chats sont des animaux, et Minou est un chat, donc Minou est un animal."),
    ("Tous les chiens ont une queue. Rex est un chien. Rex a-t-il une queue ?",
     "Oui. Tous les chiens ont une queue, et Rex est un chien, donc Rex a une queue."),
    ("Tous les poissons vivent dans l'eau. Le saumon est un poisson. Le saumon vit-il dans l'eau ?",
     "Oui. Tous les poissons vivent dans l'eau, et le saumon est un poisson, donc le saumon vit dans l'eau."),
    ("Tous les insectes ont six pattes. La fourmi est un insecte. Combien de pattes a la fourmi ?",
     "Tous les insectes ont six pattes, et la fourmi est un insecte, donc la fourmi a 6 pattes."),
    ("Tous les triangles ont trois côtés. Cette figure est un triangle. Combien de côtés a-t-elle ?",
     "Tous les triangles ont trois côtés, et cette figure est un triangle, donc elle a 3 côtés."),
    ("Tous les mammifères ont des poils. La vache est un mammifère. La vache a-t-elle des poils ?",
     "Oui. Tous les mammifères ont des poils, et la vache est un mammifère, donc la vache a des poils."),
    ("Toutes les roses sont des fleurs. Cette plante est une rose. Est-ce une fleur ?",
     "Oui. Toutes les roses sont des fleurs, et cette plante est une rose, donc c'est une fleur."),
    ("Tous les élèves de la classe portent un uniforme. Hugo est dans la classe. Hugo porte-t-il un uniforme ?",
     "Oui. Tous les élèves de la classe portent un uniforme, et Hugo est dans la classe, donc Hugo porte un uniforme."),
    ("Toutes les voitures ont un moteur. Ce véhicule est une voiture. A-t-il un moteur ?",
     "Oui. Toutes les voitures ont un moteur, et ce véhicule est une voiture, donc il a un moteur."),
    ("Aucun poisson ne sait voler. Le thon est un poisson. Le thon sait-il voler ?",
     "Non. Aucun poisson ne sait voler, et le thon est un poisson, donc le thon ne sait pas voler."),
    ("Aucun chat n'aboie. Félix est un chat. Félix aboie-t-il ?",
     "Non. Aucun chat n'aboie, et Félix est un chat, donc Félix n'aboie pas."),
    ("Les pierres ne flottent pas. Je lance une pierre dans l'eau. Va-t-elle flotter ?",
     "Non. Les pierres ne flottent pas, donc la pierre va couler."),
    ("Tous les chats sont des animaux. Rex est un animal. Rex est-il forcément un chat ?",
     "Non, pas forcément. Tous les chats sont des animaux, mais beaucoup d'animaux ne sont pas des chats."),
    ("Toutes les pommes sont des fruits. Ceci est un fruit. Est-ce forcément une pomme ?",
     "Non, pas forcément. Toutes les pommes sont des fruits, mais il existe beaucoup d'autres fruits."),
    ("S'il pleut, le sol est mouillé. Il pleut. Le sol est-il mouillé ?",
     "Oui. S'il pleut, le sol est mouillé, et il pleut, donc le sol est mouillé."),
    ("Si je lâche un verre, il tombe. Je lâche un verre. Que se passe-t-il ?",
     "Le verre tombe, car tout objet qu'on lâche tombe vers le sol."),
    ("Si la lumière est éteinte, la pièce est sombre. La lumière est éteinte. La pièce est-elle sombre ?",
     "Oui. La lumière est éteinte, donc la pièce est sombre."),
    ("Léa est dans la cuisine. La cuisine est dans la maison. Léa est-elle dans la maison ?",
     "Oui. Léa est dans la cuisine, et la cuisine est dans la maison, donc Léa est dans la maison."),
    ("Le livre est sur la table. La table est dans le salon. Où est le livre ?",
     "Le livre est sur la table, et la table est dans le salon, donc le livre est dans le salon."),
    ("Paul est né avant Léa. Léa est née avant Hugo. Qui est né en premier ?",
     "Paul est né avant Léa, et Léa avant Hugo, donc Paul est né en premier."),
    ("Une boîte rouge est plus lourde qu'une boîte bleue. La boîte bleue est plus lourde qu'une boîte verte. Quelle boîte est la plus légère ?",
     "La rouge est plus lourde que la bleue, et la bleue plus lourde que la verte, donc la boîte verte est la plus légère."),
    ("Si 5 est plus grand que 3, et 3 plus grand que 1, quel est le plus petit nombre ?",
     "5 est plus grand que 3, et 3 plus grand que 1, donc le plus petit nombre est 1."),
    ("Il fait nuit. Le soleil est-il visible dans le ciel ?",
     "Non. Quand il fait nuit, le soleil n'est pas visible dans le ciel."),
    ("J'ai froid. Que puis-je faire ?",
     "Tu peux mettre un pull ou un manteau, ou te mettre au chaud."),
    ("Mon verre est vide et j'ai soif. Que dois-je faire ?",
     "Tu peux remplir ton verre d'eau et boire."),
]
for q, a in LOGIC:
    add(q, a, 2)

for i, d in enumerate(DAYS):  # jours : « dans k jours »
    for k in range(2, 7):
        days = [DAYS[(i + j) % 7] for j in range(1, k + 1)]
        add(f"Si aujourd'hui est {d}, quel jour serons-nous dans {k} jours ?",
            f"Après {d}, on compte {k} jours : {', '.join(days)}. Dans {k} jours, nous serons {days[-1]}.")

EVENTS = [("Le film", "il"), ("Le match", "il"), ("La réunion", "elle"), ("Le cours", "il"),
          ("La fête", "elle"), ("Le spectacle", "il"), ("La course", "elle")]
for _ in range(150):  # heures
    h, k = rng.randint(6, 20), rng.randint(1, 4)
    if h + k > 23:
        continue
    if rng.random() < 0.6:
        ev, p = rng.choice(EVENTS)
        add(f"{ev} commence à {h} heures et dure {k} heure{'s' if k > 1 else ''}. À quelle heure finit-{p} ?",
            f"{h} plus {k} font {h + k}. {p.capitalize()} finit à {h + k} heures.")
    else:
        add(f"Il est {h} heures. Quelle heure sera-t-il dans {k} heure{'s' if k > 1 else ''} ?",
            f"{h} plus {k} font {h + k}. Il sera {h + k} heures.")

for _ in range(150):  # partages (division)
    sing, plur, _food = rng.choice(THINGS)
    k, q = rng.randint(2, 6), rng.randint(1, 8)
    who = rng.choice([("enfants", "enfant"), ("amis", "ami"), ("élèves", "élève")])
    add(f"On partage {k * q} {plur} entre {k} {who[0]}. Combien de {plur} reçoit chaque {who[1]} ?",
        f"{k * q} divisé par {k} égale {q}. Chaque {who[1]} reçoit {form(q, sing, plur)}.")

for _ in range(100):  # pair / impair
    n = rng.randint(0, 99)
    if n % 2 == 0:
        add(f"Le nombre {n} est-il pair ou impair ?", f"{n} se divise exactement par 2, donc {n} est pair.")
    else:
        add(f"Le nombre {n} est-il pair ou impair ?", f"{n} ne se divise pas exactement par 2, donc {n} est impair.")

GROUPS2 = [("animaux", ["chats", "chiens", "lapins", "poules", "vaches", "moutons", "canards"],
            ["dans la ferme", "dans le jardin", "dans la maison"]),
           ("fruits", ["pommes", "poires", "bananes", "oranges", "fraises"], ["dans le panier", "sur la table"]),
           ("jouets", ["ballons", "poupées", "voitures", "peluches"], ["dans le coffre", "dans la chambre"])]
for _ in range(150):  # regrouper deux groupes
    cat, kinds, places = rng.choice(GROUPS2)
    x, y = rng.sample(kinds, 2)
    a, b = rng.randint(1, 15), rng.randint(1, 15)
    pre = "d'" if cat[0] in "aeiou" else "de "
    add(f"Il y a {a} {x} et {b} {y} {rng.choice(places)}. Combien {pre}{cat} y a-t-il ?",
        f"{a} plus {b} font {a + b}. Il y a {a + b} {cat}.")
for _ in range(40):
    a, b = rng.randint(5, 20), rng.randint(5, 20)
    add(f"Dans la classe, il y a {a} garçons et {b} filles. Combien d'enfants y a-t-il ?",
        f"{a} plus {b} font {a + b}. Il y a {a + b} enfants dans la classe.")

for n in range(2, 11):  # semaines
    add(f"Combien de jours y a-t-il dans {n} semaines ?",
        f"Une semaine a 7 jours. {n} fois 7 font {7 * n}. Il y a {7 * n} jours dans {n} semaines.")
    add(f"Une semaine a 7 jours. Combien de jours y a-t-il dans {n} semaines ?",
        f"{n} fois 7 font {7 * n}. Il y a {7 * n} jours dans {n} semaines.")

PLACES = ["sur la table", "dans la boîte", "dans le panier", "sur l'étagère"]
for _ in range(150):  # poser / enlever / ajouter
    sing, plur, _food = rng.choice(THINGS)
    place = rng.choice(PLACES)
    a = rng.randint(2, 15)
    if rng.random() < 0.6:
        b = rng.randint(1, a - 1)
        add(f"Je pose {a} {plur} {place}, puis j'en enlève {b}. Combien de {plur} reste-t-il {place} ?",
            f"{a} moins {b} font {a - b}. Il reste {form(a - b, sing, plur)} {place}.")
    else:
        b = rng.randint(1, 10)
        add(f"Il y a {a} {plur} {place}. J'en ajoute {b}. Combien de {plur} y a-t-il maintenant ?",
            f"{a} plus {b} font {a + b}. Il y a maintenant {a + b} {plur} {place}.")

# Table de multiplication complète (sauf les calculs de l'évaluation), deux formulations.
for a in range(1, 11):
    for b in range(1, 11):
        if (a, b) not in BAD_PAIRS:
            add(f"Combien font {a} fois {b} ?", f"{a} fois {b} font {a * b}.")
            add(f"Calcule {a} × {b}.", f"{a} × {b} = {a * b}.")

# ------------------------------------------------------------------ fractions et étapes (v4)
FRAC = [("la moitié", 2), ("le tiers", 3), ("le quart", 4)]
for _ in range(300):  # donner une fraction, éventuellement puis une autre étape
    name, g = rng.choice(NAMES)
    sing, plur, food = rng.choice(THINGS)
    frac, d = rng.choice(FRAC[:1] * 3 + FRAC[1:])
    part = rng.randint(1, 8)
    total = part * d
    rest = total - part
    to = rng.choice(["à sa sœur", "à son frère", "à un ami", "à sa voisine", "à son cousin"])
    fr = frac.split()[1]
    if rng.random() < 0.45:
        add(f"{name} a {total} {plur}. {il(g)} en donne {frac} {to}. Combien lui en reste-t-il ?",
            f"{frac.capitalize()} de {total} est {part}. {total} moins {part} font {rest}. Il lui reste {form(rest, sing, plur)}.")
    else:
        verb = rng.choice(["mange", "perd"] if food else ["perd", "vend"])
        k = rng.randint(1, rest) if rest > 1 else 0
        if not k or k >= rest:
            continue
        add(f"{name} a {total} {plur}. {il(g)} en donne {frac} {to}, puis {il(g).lower()} en {verb} {k}. Combien lui en reste-t-il ?",
            f"D'abord, {frac} de {total} est {part}, donc il lui reste {total} moins {part}, soit {rest}. "
            f"Ensuite, {rest} moins {k} font {rest - k}. Il lui reste {form(rest - k, sing, plur)}.")
for n in range(2, 41):  # fractions seules
    for frac, d in FRAC:
        if n % d == 0 and rng.random() < 0.6 and not (frac == "la moitié" and n in (10, 12)):
            add(f"Quel est {frac} de {n} ?", f"{frac.capitalize()} de {n} est {n // d}, car {n} divisé par {d} égale {n // d}.")

WORDS_FOIS = {2: "deux", 3: "trois", 4: "quatre", 5: "cinq"}
for _ in range(250):  # « k fois plus que », éventuellement « ensemble »
    (a_name, ga), (b_name, gb) = rng.sample(NAMES, 2)
    sing, plur, _food = rng.choice(THINGS)
    k, b = rng.randint(2, 5), rng.randint(1, 10)
    kw = str(k) if rng.random() < 0.5 else WORDS_FOIS[k]
    if rng.random() < 0.5:
        add(f"{a_name} a {kw} fois plus de {plur} {que(b_name)}. {b_name} a {form(b, sing, plur)}. Combien de {plur} a {a_name} ?",
            f"{a_name} en a {k} fois plus, donc {k} fois {b} font {k * b}. {a_name} a {k * b} {plur}.")
    else:
        ils = "elles" if ga == gb == "f" else "ils"
        add(f"{a_name} a {kw} fois plus de {plur} {que(b_name)}. {b_name} a {form(b, sing, plur)}. Combien de {plur} ont-{ils} ensemble ?",
            f"D'abord, {k} fois {b} font {k * b} : {a_name} a {k * b} {plur}. Ensuite, {k * b} plus {b} font {k * b + b}. "
            f"Ensemble, {ils} ont {k * b + b} {plur}.")

for _ in range(300):  # trois étapes
    name, g = rng.choice(NAMES)
    sing, plur, food = rng.choice(THINGS)
    a = rng.randint(5, 20)
    steps, val, txt, ans = [], a, [], []
    for i in range(3):
        if rng.random() < 0.5 and val > 1:
            x = rng.randint(1, val - 1)
            v = rng.choice(["perd", "donne"] + (["mange"] if food else ["vend"]))
            txt.append(f"en {v} {x}")
            ans.append(f"{val} moins {x} font {val - x}")
            val -= x
        else:
            x = rng.randint(1, 9)
            v = rng.choice(["gagne", "reçoit", "trouve", "achète"])
            txt.append(f"en {v} {x}")
            ans.append(f"{val} plus {x} font {val + x}")
            val += x
    add(f"{name} a {a} {plur}. {il(g)} {txt[0]}, puis {txt[1]}, puis {txt[2]}. Combien de {plur} a-{t_il(g)} ?",
        f"D'abord, {ans[0]}. Ensuite, {ans[1]}. Enfin, {ans[2]}. {il(g)} a {form(val, sing, plur)}.")

for _ in range(250):  # boîtes, puis on donne ou on reçoit
    un, sing, plur, items = rng.choice(PACKS)
    k, n = rng.randint(2, 8), rng.randint(2, 6)
    tot = k * n
    if rng.random() < 0.7:
        d = rng.randint(1, tot - 1)
        q = rng.choice([f"J'ai {n} {plur} de {k} {items}. Je donne {d} {items}. Combien de {items} me reste-t-il ?",
                        f"{un} {sing} contient {k} {items}. J'ai {n} {plur} et j'en donne {d}. Combien de {items} me reste-t-il ?",
                        f"J'ai {n} {plur}. Chaque {sing} contient {k} {items}. J'en perds {d}. Combien de {items} me reste-t-il ?"])
        add(q, f"D'abord, {n} fois {k} font {tot} {items}. Ensuite, {tot} moins {d} font {tot - d}. Il te reste {tot - d} {items}.")
    else:
        d = rng.randint(1, 10)
        add(f"J'ai {n} {plur} de {k} {items}. On m'en donne encore {d}. Combien de {items} ai-je ?",
            f"D'abord, {n} fois {k} font {tot} {items}. Ensuite, {tot} plus {d} font {tot + d}. Tu as {tot + d} {items}.")

for _ in range(150):  # plusieurs achats
    name, g = rng.choice(NAMES)
    n_items = rng.choice([2, 2, 3])
    its = rng.sample(ITEMS, n_items)
    prices = [rng.randint(1, 12) for _ in its]
    a = rng.randint(sum(prices), 50)
    if rng.random() < 0.5:
        who, res = f"J'ai {a} euros. J'achète ", "Il te reste"
        tail = "Combien d'argent me reste-t-il ?"
    else:
        who, res = f"{name} a {a} euros. {il(g)} achète ", "Il lui reste"
        tail = "Combien d'argent lui reste-t-il ?"
    parts = [f"{it} à {p} euros" for it, p in zip(its, prices)]
    liste = ", ".join(parts[:-1]) + " et " + parts[-1]
    s = sum(prices)
    add(f"{who}{liste}. {tail}",
        f"D'abord, {' plus '.join(map(str, prices))} font {s} euros dépensés. Ensuite, {a} moins {s} font {a - s}. "
        f"{res} {a - s} euros.")

LEGS = [("vache", "vaches", 4, "f"), ("poule", "poules", 2, "f"), ("mouton", "moutons", 4, "m"),
        ("canard", "canards", 2, "m"), ("chèvre", "chèvres", 4, "f"), ("lapin", "lapins", 4, "m"),
        ("oie", "oies", 2, "f"), ("cochon", "cochons", 4, "m")]
WHEELS = [("voiture", "voitures", 4, "f"), ("vélo", "vélos", 2, "m"), ("moto", "motos", 2, "f"),
          ("tricycle", "tricycles", 3, "m"), ("camion", "camions", 6, "m")]
for _ in range(250):  # pattes / roues : connaissance + deux multiplications + addition
    if rng.random() < 0.6:
        (s1, p1, l1, g1), (s2, p2, l2, g2) = rng.sample(LEGS, 2)
        what, intro = "pattes", rng.choice(["Un fermier a", "Dans la ferme, il y a", "Il y a"])
    else:
        (s1, p1, l1, g1), (s2, p2, l2, g2) = rng.sample(WHEELS, 2)
        what, intro = "roues", rng.choice(["Dans le parking, il y a", "Il y a", "Dans la rue, il y a"])
    a, b = rng.randint(1, 6), rng.randint(1, 6)
    u1 = ("Une" if g1 == "f" else "Un")
    u2 = ("une" if g2 == "f" else "un")
    add(f"{intro} {form(a, s1, p1)} et {form(b, s2, p2)}. Combien de {what} y a-t-il en tout ?",
        f"{u1} {s1} a {l1} {what} et {u2} {s2} a {l2} {what}. {a} fois {l1} font {a * l1}, et {b} fois {l2} font {b * l2}. "
        f"{a * l1} plus {b * l2} font {a * l1 + b * l2}. Il y a {a * l1 + b * l2} {what} en tout.")

TRIPS = [("Un train", "il", "repart"), ("Un bus", "il", "repart"), ("Un avion", "il", "repart"), ("Une navette", "elle", "repart")]
for _ in range(200):  # horaires en chaîne
    veh, p, verb = rng.choice(TRIPS)
    h, a, b = rng.randint(5, 14), rng.randint(1, 4), rng.randint(1, 3)
    hs = lambda n: f"{n} heure{'s' if n > 1 else ''}"
    if rng.random() < 0.6:
        add(f"{veh} part à {h} heures. Le trajet dure {hs(a)}, puis {p} attend {hs(b)}. À quelle heure {verb}-{p} ?",
            f"D'abord, {h} plus {a} font {h + a} : {p} arrive à {h + a} heures. Ensuite, {h + a} plus {b} font {h + a + b}. "
            f"{p.capitalize()} {verb} à {h + a + b} heures.")
    else:
        name, g = rng.choice(NAMES)
        add(f"{name} commence à travailler à {h} heures. {il(g)} travaille {hs(a)}, puis {il(g).lower()} fait une pause de {hs(b)}. À quelle heure finit sa pause ?",
            f"D'abord, {h} plus {a} font {h + a}. Ensuite, {h + a} plus {b} font {h + a + b}. Sa pause finit à {h + a + b} heures.")

for _ in range(200):  # âges en deux étapes
    (a_name, ga), (b_name, gb) = rng.sample(NAMES, 2)
    b, k, n = rng.randint(5, 30), rng.randint(1, 8), rng.randint(1, 10)
    t = "aura" 
    if rng.random() < 0.5:
        add(f"{a_name} a {k} ans de plus {que(b_name)}. {b_name} a {b} ans. Quel âge aura {a_name} dans {n} ans ?",
            f"D'abord, {b} plus {k} font {b + k} : {a_name} a {b + k} ans. Ensuite, {b + k} plus {n} font {b + k + n}. "
            f"Dans {n} ans, {a_name} aura {b + k + n} ans.")
    elif b > k:
        add(f"{a_name} a {k} ans de moins {que(b_name)}. {b_name} a {b} ans. Quel âge aura {a_name} dans {n} ans ?",
            f"D'abord, {b} moins {k} font {b - k} : {a_name} a {b - k} ans. Ensuite, {b - k} plus {n} font {b - k + n}. "
            f"Dans {n} ans, {a_name} aura {b - k + n} ans.")

for d in range(2, 11):  # table de division complète
    for q in range(1, 11):
        if (d * q, d) not in BAD_PAIRS:
            add(f"Combien font {d * q} divisé par {d} ?", f"{d * q} divisé par {d} égale {q}.")

# ------------------------------------------------------------------ définitions (v5)
# « C'est quoi un briquet ? », « Le citron » : définitions courtes écrites à la main.
# (article indéfini, article défini, nom, définition)
DEFS = [
    ("un", "le", "briquet", "un petit objet qui sert à faire du feu"),
    ("un", "le", "citron", "un fruit jaune au goût acide"),
    ("une", "la", "pomme", "un fruit rond, rouge, jaune ou vert, qui pousse sur un pommier"),
    ("une", "la", "banane", "un fruit long et jaune, à la chair douce"),
    ("une", "la", "fraise", "un petit fruit rouge et sucré"),
    ("une", "la", "carotte", "un légume orange qui pousse sous la terre"),
    ("une", "la", "tomate", "un fruit rouge qu'on mange souvent en salade"),
    ("un", "le", "riz", "une céréale en petits grains, très mangée à Madagascar et en Asie"),
    ("un", "le", "pain", "un aliment fait avec de la farine, de l'eau et du sel, cuit au four"),
    ("un", "le", "fromage", "un aliment fabriqué avec du lait"),
    ("un", "le", "chocolat", "un aliment sucré fabriqué avec des fèves de cacao"),
    ("un", "le", "miel", "un liquide sucré fabriqué par les abeilles"),
    ("un", "le", "lait", "une boisson blanche produite par la vache et d'autres mammifères"),
    ("un", "le", "café", "une boisson chaude faite avec des grains de café grillés"),
    ("un", "le", "thé", "une boisson faite avec des feuilles infusées dans l'eau chaude"),
    ("une", "la", "voiture", "un véhicule à quatre roues avec un moteur"),
    ("un", "le", "vélo", "un véhicule à deux roues qu'on fait avancer avec des pédales"),
    ("un", "l'", "avion", "un véhicule qui vole dans le ciel grâce à ses ailes et ses moteurs"),
    ("un", "le", "bateau", "un véhicule qui flotte et se déplace sur l'eau"),
    ("un", "le", "train", "un véhicule qui roule sur des rails et tire des wagons"),
    ("une", "la", "fusée", "un engin très puissant qui peut aller dans l'espace"),
    ("un", "le", "téléphone", "un appareil qui sert à parler à distance et à envoyer des messages"),
    ("un", "l'", "ordinateur", "une machine qui calcule, stocke des informations et fait tourner des programmes"),
    ("une", "la", "télévision", "un appareil qui affiche des images et des émissions"),
    ("un", "le", "réfrigérateur", "un appareil qui garde les aliments au froid"),
    ("une", "la", "lampe", "un objet qui produit de la lumière"),
    ("une", "l'", "horloge", "un objet qui indique l'heure"),
    ("une", "la", "clé", "un petit objet en métal qui sert à ouvrir une serrure"),
    ("un", "le", "parapluie", "un objet qu'on ouvre au-dessus de la tête pour se protéger de la pluie"),
    ("un", "le", "stylo", "un objet qui sert à écrire avec de l'encre"),
    ("un", "le", "crayon", "un objet en bois qui sert à écrire ou à dessiner"),
    ("un", "le", "livre", "un ensemble de pages imprimées et reliées qu'on lit"),
    ("un", "le", "cahier", "un ensemble de feuilles reliées sur lesquelles on écrit"),
    ("des", "les", "ciseaux", "un outil à deux lames qui sert à couper"),
    ("un", "le", "marteau", "un outil qui sert à enfoncer des clous"),
    ("un", "le", "couteau", "un outil avec une lame qui sert à couper"),
    ("une", "la", "fourchette", "un couvert avec des dents qui sert à piquer les aliments"),
    ("une", "la", "cuillère", "un couvert creux qui sert à manger la soupe ou à remuer"),
    ("une", "l'", "assiette", "un plat plat ou creux dans lequel on mange"),
    ("un", "le", "verre", "un récipient dans lequel on boit"),
    ("une", "la", "chaise", "un meuble sur lequel on s'assoit"),
    ("une", "la", "table", "un meuble avec un plateau posé sur des pieds"),
    ("un", "le", "lit", "un meuble sur lequel on dort"),
    ("une", "la", "maison", "un bâtiment dans lequel on habite"),
    ("une", "l'", "école", "un lieu où les enfants apprennent avec des enseignants"),
    ("un", "l'", "hôpital", "un lieu où l'on soigne les malades et les blessés"),
    ("une", "la", "ville", "un endroit où beaucoup de gens vivent, avec des rues et des bâtiments"),
    ("un", "le", "pays", "un territoire avec ses frontières, ses habitants et son gouvernement"),
    ("une", "la", "montagne", "une très grande élévation de terrain"),
    ("une", "la", "rivière", "un cours d'eau qui coule jusqu'à un fleuve ou à la mer"),
    ("une", "la", "mer", "une grande étendue d'eau salée"),
    ("une", "la", "forêt", "un grand espace couvert d'arbres"),
    ("un", "le", "désert", "une région très sèche où il pleut très peu"),
    ("une", "l'", "île", "une terre entourée d'eau de tous les côtés"),
    ("un", "le", "volcan", "une montagne d'où peut sortir de la lave brûlante"),
    ("un", "le", "soleil", "l'étoile autour de laquelle tourne la Terre ; il nous donne lumière et chaleur"),
    ("une", "la", "lune", "le satellite naturel de la Terre, qu'on voit souvent la nuit"),
    ("une", "l'", "étoile", "une énorme boule de gaz très chaude qui brille dans le ciel"),
    ("une", "la", "planète", "un grand astre qui tourne autour d'une étoile, comme la Terre autour du Soleil"),
    ("un", "le", "nuage", "un amas de petites gouttes d'eau dans le ciel"),
    ("une", "la", "pluie", "de l'eau qui tombe des nuages"),
    ("une", "la", "neige", "de l'eau gelée qui tombe du ciel en flocons blancs"),
    ("un", "l'", "arc-en-ciel", "un arc de couleurs qui apparaît quand le soleil éclaire la pluie"),
    ("un", "l'", "arbre", "une grande plante avec un tronc, des branches et des feuilles"),
    ("une", "la", "fleur", "la partie colorée d'une plante, qui donne ensuite des fruits ou des graines"),
    ("une", "la", "graine", "une petite partie d'une plante d'où peut naître une nouvelle plante"),
    ("un", "le", "chat", "un petit animal domestique à quatre pattes qui miaule"),
    ("un", "le", "chien", "un animal domestique à quatre pattes qui aboie, souvent fidèle à son maître"),
    ("un", "le", "lion", "un grand félin d'Afrique, appelé le roi des animaux"),
    ("un", "l'", "éléphant", "le plus grand animal terrestre, avec une trompe et des défenses"),
    ("une", "la", "baleine", "un énorme mammifère qui vit dans la mer"),
    ("un", "le", "lémurien", "un animal de Madagascar, proche du singe, avec une longue queue"),
    ("un", "le", "caméléon", "un lézard qui peut changer de couleur"),
    ("un", "le", "zébu", "un bœuf avec une bosse sur le dos, très présent à Madagascar"),
    ("une", "l'", "abeille", "un insecte qui butine les fleurs et fabrique du miel"),
    ("un", "le", "papillon", "un insecte avec de grandes ailes colorées"),
    ("un", "le", "serpent", "un reptile sans pattes au corps long"),
    ("un", "l'", "oiseau", "un animal avec des plumes, un bec et des ailes"),
    ("un", "le", "poisson", "un animal qui vit dans l'eau et respire avec des branchies"),
    ("un", "le", "mammifère", "un animal dont la femelle nourrit ses petits avec son lait"),
    ("un", "l'", "insecte", "un petit animal à six pattes, comme la fourmi ou l'abeille"),
    ("un", "le", "médecin", "une personne qui soigne les malades"),
    ("un", "l'", "enseignant", "une personne qui fait la classe et aide les élèves à apprendre"),
    ("un", "le", "boulanger", "une personne qui fait le pain"),
    ("un", "l'", "agriculteur", "une personne qui cultive la terre ou élève des animaux"),
    ("un", "le", "pompier", "une personne qui éteint les incendies et porte secours"),
    ("une", "la", "famille", "un groupe de personnes liées, comme les parents et les enfants"),
    ("un", "l'", "ami", "une personne qu'on aime bien et avec qui on partage des moments"),
    ("un", "le", "cœur", "l'organe qui pompe le sang dans tout le corps"),
    ("un", "le", "cerveau", "l'organe qui nous permet de penser, de bouger et de ressentir"),
    ("un", "le", "poumon", "l'organe qui nous permet de respirer"),
    ("un", "le", "nombre", "une idée qui sert à compter ou à mesurer, comme 3 ou 100"),
    ("une", "l'", "addition", "une opération qui réunit deux nombres, comme 2 plus 3 font 5"),
    ("une", "la", "soustraction", "une opération qui enlève un nombre à un autre, comme 5 moins 2 font 3"),
    ("une", "la", "multiplication", "une addition répétée, comme 3 fois 4 font 12"),
    ("une", "la", "division", "une opération qui partage un nombre en parts égales, comme 12 divisé par 3 égale 4"),
    ("un", "le", "triangle", "une figure qui a trois côtés"),
    ("un", "le", "cercle", "une figure toute ronde"),
    ("une", "l'", "heure", "une durée de soixante minutes"),
    ("une", "la", "semaine", "une durée de sept jours"),
    ("un", "le", "mois", "une partie de l'année, d'environ trente jours"),
    ("une", "l'", "année", "une durée de douze mois, ou 365 jours"),
    ("une", "l'", "eau", "un liquide transparent, indispensable à la vie"),
    ("un", "le", "feu", "une flamme qui produit de la chaleur et de la lumière"),
    ("un", "l'", "air", "le mélange de gaz que nous respirons"),
    ("une", "l'", "électricité", "une énergie qui fait fonctionner les lampes et les appareils"),
    ("un", "l'", "argent", "ce qui sert à acheter des choses, sous forme de pièces ou de billets"),
    ("une", "la", "musique", "un art qui assemble des sons de façon agréable"),
    ("un", "le", "jeu", "une activité qu'on fait pour s'amuser"),
    ("un", "le", "sport", "une activité physique, comme le football ou la course"),
    ("un", "le", "football", "un sport où deux équipes essaient de mettre un ballon dans le but adverse avec les pieds"),
    ("une", "la", "langue", "un moyen de communiquer avec des mots, comme le français ou le malgache"),
    ("un", "le", "mot", "un ensemble de lettres qui a un sens"),
    ("une", "la", "phrase", "une suite de mots qui a un sens, qui commence par une majuscule et finit par un point"),
    ("un", "l'", "internet", "un immense réseau qui relie des ordinateurs du monde entier"),
    ("un", "le", "robot", "une machine qui peut faire des tâches toute seule"),
    ("une", "l'", "intelligence artificielle",
     "un programme informatique qui apprend à partir d'exemples pour accomplir des tâches, comme répondre à des questions"),
    ("un", "le", "programme", "une suite d'instructions qu'un ordinateur exécute"),
    ("une", "l'", "application", "un programme qu'on utilise sur un téléphone ou un ordinateur"),
    ("un", "le", "temps", "ce qui passe et se mesure en secondes, en heures et en jours ; c'est aussi la météo"),
    ("une", "la", "météo", "l'état du ciel et de l'air : soleil, pluie, vent, température"),
    ("une", "la", "saison", "une des quatre parties de l'année : printemps, été, automne et hiver"),
    ("un", "l'", "anniversaire", "le jour où l'on fête la date de sa naissance"),
    ("un", "le", "cadeau", "un objet qu'on offre à quelqu'un pour lui faire plaisir"),
]
assert len({d[2] for d in DEFS}) == len(DEFS)


def le_nom(art, nom):
    return f"{art}{nom}" if art == "l'" else f"{art} {nom}"


# Matières et choses uniques : « C'est quoi le miel ? » plutôt que « un miel ».
DEFINI = {"riz", "chocolat", "miel", "lait", "café", "thé", "eau", "air", "électricité", "argent", "musique",
          "football", "internet", "intelligence artificielle", "temps", "météo", "soleil", "lune", "pluie", "neige"}

for un, le, nom, d in DEFS:
    if nom in DEFINI:
        un = le
    sujet = le_nom(un, nom)
    verbe = "sont" if un == "des" else "est"
    ans = f"{sujet.capitalize()} {verbe} {d}."
    ans_le = f"{le_nom(le, nom).capitalize()} {verbe} {d}."
    q_quoi = f"Qu'est-ce que {sujet} ?" if un == "des" else f"Qu'est-ce {que(sujet)} ?"
    for q in rng.sample([f"C'est quoi {sujet} ?", q_quoi, f"{sujet.capitalize()}, c'est quoi ?",
                         f"Explique-moi ce qu'est {sujet}." if un != "des" else f"Explique-moi ce que sont {sujet}.",
                         f"Que veut dire le mot « {nom} » ?"], 3):
        add(q, ans)
    add(le_nom(le, nom).capitalize(), ans_le)  # un sujet seul : « Le citron »
    if rng.random() < 0.5:
        add(f"Parle-moi {('des ' + nom) if le == 'les' else ('de ' + le_nom(le, nom))}.", ans_le)

# ------------------------------------------------------------------ conversation
CONV = [
    (["Bonjour", "Bonjour !", "Salut", "Salut !", "Coucou", "Hello", "Bonsoir", "Salut Alice", "Bonjour Alice",
      "Coucou !", "Hey", "Bonjour à toi", "Salut, ça va ?", "slt", "bjr"],
     ["Bonjour ! Je suis Alice. Comment puis-je t'aider ?", "Salut ! Que puis-je faire pour toi aujourd'hui ?",
      "Bonjour ! Pose-moi une question, je ferai de mon mieux.", "Salut ! Comment puis-je t'aider aujourd'hui ?"]),
    (["Comment tu t'appelles ?", "Comment t'appelles-tu ?", "Tu t'appelles comment ?", "C'est quoi ton nom ?",
      "Quel est ton nom ?"],
     ["Je m'appelle Alice.", "Je m'appelle Alice, je suis une petite intelligence artificielle."]),
    (["Tu es qui ?", "Présente-toi.", "Qui êtes-vous ?", "Tu es quoi ?", "Tu es quoi", "T'es qui ?",
      "Présente-toi s'il te plaît."],
     ["Je suis Alice, un petit modèle d'intelligence artificielle qui répond en français.",
      "Je m'appelle Alice. Je suis une intelligence artificielle, et j'essaie de répondre à tes questions."]),
    (["Comment ça va ?", "Ça va ?", "Comment vas-tu ?", "Tu vas bien ?"],
     ["Je vais bien, merci ! Et toi ?", "Ça va bien, merci. Et toi, comment vas-tu ?"]),
    (["Ça va bien, merci.", "Je vais bien.", "Très bien et toi ?"],
     ["Tant mieux ! Que puis-je faire pour toi ?", "Super ! As-tu une question pour moi ?"]),
    (["Merci", "Merci !", "Merci Alice", "Super, merci."],
     ["De rien !", "Avec plaisir !", "De rien, c'est un plaisir de t'aider."]),
    (["Au revoir", "Au revoir !", "Bonne nuit", "À plus tard", "À bientôt !", "Bye", "Je dois y aller, au revoir."],
     ["Au revoir ! À bientôt.", "À bientôt !", "Bonne journée, et à bientôt !"]),
    (["Qui t'a créée ?", "Qui t'a créé ?", "Qui t'a créé", "Qui t'a fabriquée ?", "D'où viens-tu ?",
      "Qui t'a programmée ?", "Qui est ton créateur ?", "Tu viens d'où ?", "Qui t'a faite ?"],
     [f"Je suis basée sur {B['nom']}, un modèle créé par {B['auteur']}, puis adaptée pour parler français.",
      f"Mon modèle de base, {B['nom']}, a été créé par {B['auteur']}. On m'a ensuite entraînée à répondre en français."]),
    (["Que sais-tu faire ?", "Tu sais faire quoi ?", "À quoi sers-tu ?", "Comment peux-tu m'aider ?",
      "Tu connais quoi ?", "Tu connais quoi", "Qu'est-ce que tu sais ?", "Tu peux faire quoi ?"],
     ["Je peux répondre à des questions simples, faire de petits calculs, traduire des mots et discuter un peu.",
      "Je réponds à des questions simples en français : culture générale, calcul, vocabulaire, traduction."]),
    (["Tu es quel modèle ?", "Quel modèle es-tu ?", "Tu es basée sur quoi ?", "Tu es quelle IA ?",
      "Tu utilises quel modèle ?"],
     [f"Je suis Alice, basée sur {B['complet']}, un petit modèle de {B['taille']} de paramètres créé par "
      f"{B['auteur']}, puis entraîné en français.",
      f"Je suis basée sur {B['complet']}, un petit modèle de langage. On m'a entraînée pour parler français."]),
    (["C'est quoi une IA ?", "Une IA c'est quoi ?", "Qu'est-ce qu'une intelligence artificielle ?", "Une IA est quoi ?"],
     ["Une IA, ou intelligence artificielle, est un programme informatique qui apprend à partir d'exemples "
      "pour accomplir des tâches, comme répondre à des questions.",
      "Une intelligence artificielle est un programme qui imite certaines capacités humaines, comme comprendre "
      "et écrire du texte."]),
    (["Qui est Léa ?", "C'est qui Léa ?", "Tu connais Paul ?", "Qui est Marc ?"],
     ["Je ne sais pas de qui tu parles. Peux-tu m'en dire plus ?",
      "Je ne connais pas cette personne. Peux-tu me donner plus de détails ?"]),
    (["Es-tu un humain ?", "Tu es un robot ?", "Es-tu une vraie personne ?"],
     ["Non, je suis une intelligence artificielle, un programme informatique.",
      "Je ne suis pas humaine : je suis Alice, une intelligence artificielle."]),
    (["Quel âge as-tu ?", "Tu as quel âge ?"],
     ["Je n'ai pas d'âge comme un humain : je suis un programme informatique.",
      "Je suis une intelligence artificielle, donc je n'ai pas vraiment d'âge."]),
    (["Quelle heure est-il ?", "On est quel jour aujourd'hui ?", "Quelle est la date d'aujourd'hui ?"],
     ["Je n'ai pas accès à l'heure ni à la date. Regarde l'horloge de ton téléphone.",
      "Je ne peux pas le savoir : je n'ai ni horloge ni calendrier."]),
    (["Quel temps fait-il ?", "Il fait beau aujourd'hui ?", "Va-t-il pleuvoir demain ?"],
     ["Je n'ai pas accès à la météo, désolée. Tu peux consulter une application météo.",
      "Je ne peux pas voir dehors ni consulter la météo, désolée."]),
    (["Tu parles anglais ?", "Parles-tu d'autres langues ?"],
     ["Oui, je comprends aussi l'anglais, mais ici je réponds surtout en français.",
      "Je parle français et anglais, un peu."]),
    (["Tu es intelligente ?", "Es-tu forte ?"],
     ["Je suis un tout petit modèle : je connais des choses simples, mais je peux me tromper.",
      "Je fais de mon mieux, mais je suis petite et je fais encore des erreurs."]),
    (["Raconte-moi une blague.", "Tu connais une blague ?"],
     ["Pourquoi les plongeurs plongent-ils toujours en arrière ? Parce que sinon, ils tombent dans le bateau !",
      "Que dit un escargot quand il croise une limace ? « Oh, un nudiste ! »"]),
    (["Je suis triste.", "Je ne me sens pas bien."],
     ["Je suis désolée. Tu veux en parler ? Parfois, ça aide de parler à quelqu'un de confiance.",
      "Courage ! Si tu en as besoin, parle à un proche ou à quelqu'un de confiance."]),
    (["Tu m'aimes ?", "Tu es mon amie ?"],
     ["Je suis une intelligence artificielle, mais j'aime beaucoup discuter avec toi !",
      "Je suis contente de t'aider et de discuter avec toi."]),
    (["Je ne comprends pas.", "Hein ?", "Quoi ?"],
     ["Pas de souci. Peux-tu reformuler ta question plus simplement ?",
      "Désolée si je n'ai pas été claire. Repose ta question autrement."]),
    (["Tu t'es trompée.", "C'est faux.", "Mauvaise réponse."],
     ["Désolée, je me suis trompée. Je suis un petit modèle et je fais parfois des erreurs.",
      "Pardon pour cette erreur. Merci de me corriger !"]),
]
for questions, answers in CONV:
    for q in questions:
        if norm(q) in EVAL_QUESTIONS:
            continue
        for a in rng.sample(answers, min(2, len(answers))):
            add(q, a)

# Un peu d'anglais pour garder ses capacités (réponses en anglais à des questions en anglais).
EN = [("What is your name?", "My name is Alice."), ("Who are you?", "I am Alice, a small AI assistant."),
      ("Hello!", "Hello! How can I help you?"), ("Thank you!", "You're welcome!"),
      ("What is the capital of Portugal?", "The capital of Portugal is Lisbon."),
      ("What is the capital of China?", "The capital of China is Beijing."),
      ("What is the capital of Brazil?", "The capital of Brazil is Brasilia."),
      ("How many legs does a cow have?", "A cow has 4 legs."),
      ("What color is a banana?", "A ripe banana is yellow."),
      ("What is the opposite of 'cold'?", "The opposite of 'cold' is 'hot'.")]
for q, a in EN:
    add(q, a)
for _ in range(80):
    a, b = rng.randint(0, 30), rng.randint(0, 30)
    if (a, b) not in BAD_PAIRS:
        add(f"What is {a} plus {b}?", f"{a} plus {b} is {a + b}.")



# ------------------------------------------------------------------ étapes du mode pivot
# Le modèle sait beaucoup plus de choses en anglais qu'en français. Pour que le
# mode pivot reste utilisable après l'entraînement, on lui apprend aussi ses trois
# étapes : traduire la question en anglais, répondre en anglais, puis réécrire la
# réponse en français en recopiant l'information de la réponse anglaise.
sys.path.insert(0, str(ROOT))
from chat import SYS_ANSWER, SYS_REWRITE, SYS_TRANSLATE, rewrite_input  # noqa: E402

PIVOT = []  # (question fr, réponse fr, question en, réponse en)

EN_CAPITALS = {
    "du Portugal": ("Portugal", "Lisbon"), "de la Belgique": ("Belgium", "Brussels"), "de la Suisse": ("Switzerland", "Bern"),
    "de l'Autriche": ("Austria", "Vienna"), "des Pays-Bas": ("the Netherlands", "Amsterdam"),
    "du Royaume-Uni": ("the United Kingdom", "London"), "de l'Irlande": ("Ireland", "Dublin"),
    "de la Grèce": ("Greece", "Athens"), "de la Pologne": ("Poland", "Warsaw"), "de la Suède": ("Sweden", "Stockholm"),
    "de la Norvège": ("Norway", "Oslo"), "du Danemark": ("Denmark", "Copenhagen"), "de la Finlande": ("Finland", "Helsinki"),
    "de la Hongrie": ("Hungary", "Budapest"), "de la République tchèque": ("the Czech Republic", "Prague"),
    "de la Roumanie": ("Romania", "Bucharest"), "de la Bulgarie": ("Bulgaria", "Sofia"), "de la Croatie": ("Croatia", "Zagreb"),
    "de la Serbie": ("Serbia", "Belgrade"), "de la Turquie": ("Turkey", "Ankara"), "de la Chine": ("China", "Beijing"),
    "de l'Inde": ("India", "New Delhi"), "de la Corée du Sud": ("South Korea", "Seoul"), "du Viêt Nam": ("Vietnam", "Hanoi"),
    "de la Thaïlande": ("Thailand", "Bangkok"), "de l'Indonésie": ("Indonesia", "Jakarta"),
    "des Philippines": ("the Philippines", "Manila"), "de l'Australie": ("Australia", "Canberra"),
    "de la Nouvelle-Zélande": ("New Zealand", "Wellington"), "des États-Unis": ("the United States", "Washington"),
    "du Mexique": ("Mexico", "Mexico City"), "du Brésil": ("Brazil", "Brasilia"), "de l'Argentine": ("Argentina", "Buenos Aires"),
    "du Chili": ("Chile", "Santiago"), "du Pérou": ("Peru", "Lima"), "de la Colombie": ("Colombia", "Bogota"),
    "du Venezuela": ("Venezuela", "Caracas"), "de Cuba": ("Cuba", "Havana"), "du Maroc": ("Morocco", "Rabat"),
    "de l'Algérie": ("Algeria", "Algiers"), "de la Tunisie": ("Tunisia", "Tunis"), "du Sénégal": ("Senegal", "Dakar"),
    "du Mali": ("Mali", "Bamako"), "du Kenya": ("Kenya", "Nairobi"), "de l'Éthiopie": ("Ethiopia", "Addis Ababa"),
    "du Nigeria": ("Nigeria", "Abuja"), "de Madagascar": ("Madagascar", "Antananarivo"), "du Cameroun": ("Cameroon", "Yaounde"),
    "de l'Iran": ("Iran", "Tehran"), "de l'Irak": ("Iraq", "Baghdad"), "de l'Arabie saoudite": ("Saudi Arabia", "Riyadh"),
    "du Liban": ("Lebanon", "Beirut"), "du Pakistan": ("Pakistan", "Islamabad"), "de l'Afghanistan": ("Afghanistan", "Kabul"),
    "de l'Islande": ("Iceland", "Reykjavik"), "du Luxembourg": ("Luxembourg", "Luxembourg"),
}
for de, cap in CAPITALS:
    en_c, en_cap = EN_CAPITALS[de]
    PIVOT.append((f"Quelle est la capitale {de} ?", f"La capitale {de} est {cap}.",
                  f"What is the capital of {en_c}?", f"The capital of {en_c} is {en_cap}."))

EN_OP = {"plus": ("plus", lambda a, b: a + b), "moins": ("minus", lambda a, b: a - b),
         "fois": ("times", lambda a, b: a * b)}
for _ in range(150):
    w = rng.choice(list(EN_OP))
    a, b = rng.randint(1, 30), rng.randint(1, 30)
    if w == "moins" and b > a:
        a, b = b, a
    if w == "fois":
        a, b = rng.randint(1, 10), rng.randint(1, 10)
    if (a, b) in BAD_PAIRS:
        continue
    en, f = EN_OP[w]
    PIVOT.append((f"Combien font {a} {w} {b} ?", f"{a} {w} {b} font {f(a, b)}.",
                  f"What is {a} {en} {b}?", f"{a} {en} {b} is {f(a, b)}."))

EN_THINGS = {"pomme": "apples", "bille": "marbles", "bonbon": "candies", "crayon": "pencils", "fleur": "flowers",
             "ballon": "balloons", "carte": "cards", "biscuit": "cookies", "jouet": "toys", "orange": "oranges"}
for _ in range(150):
    name, g = rng.choice(NAMES)
    pro, en_pro = ("Elle", "She") if g == "f" else ("Il", "He")
    sing, plur, _food = rng.choice([t for t in THINGS if t[0] in EN_THINGS])
    a = rng.randint(3, 20)
    b = rng.randint(1, a - 1)
    if (a, b) in BAD_PAIRS:
        continue
    if rng.random() < 0.5:
        PIVOT.append((f"{name} a {a} {plur}. {pro} en donne {b}. Combien lui en reste-t-il ?",
                      f"{a} moins {b} font {a - b}. Il lui reste {form(a - b, sing, plur)}.",
                      f"{name} has {a} {EN_THINGS[sing]}. {en_pro} gives away {b}. How many does {en_pro.lower()} have left?",
                      f"{a} minus {b} is {a - b}. {en_pro} has {a - b} left."))
    else:
        t = "a-t-elle" if g == "f" else "a-t-il"
        PIVOT.append((f"{name} a {a} {plur}. {pro} en achète {b}. Combien de {plur} {t} maintenant ?",
                      f"{a} plus {b} font {a + b}. {pro} a maintenant {a + b} {plur}.",
                      f"{name} has {a} {EN_THINGS[sing]}. {en_pro} buys {b} more. How many does {en_pro.lower()} have now?",
                      f"{a} plus {b} is {a + b}. {en_pro} has {a + b} {EN_THINGS[sing]} now."))

EN_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
for i, d in enumerate(DAYS):
    if d in ("mercredi", "vendredi"):
        continue  # questions « demain » de l'évaluation
    PIVOT.append((f"Si aujourd'hui est {d}, quel jour serons-nous demain ?",
                  f"Si aujourd'hui est {d}, demain nous serons {DAYS[(i + 1) % 7]}.",
                  f"If today is {EN_DAYS[i]}, what day is tomorrow?", f"If today is {EN_DAYS[i]}, tomorrow is {EN_DAYS[(i + 1) % 7]}."))

# Connaissances traduites à la main (sous-ensemble de FACTS)
FACTS_EN = [
    ("Combien y a-t-il de secondes dans une minute ?", "How many seconds are in a minute?", "There are 60 seconds in a minute."),
    ("Combien y a-t-il de saisons dans une année ?", "How many seasons are in a year?", "There are 4 seasons in a year."),
    ("De quelle couleur est une banane mûre ?", "What color is a ripe banana?", "A ripe banana is yellow."),
    ("De quelle couleur est le lait ?", "What color is milk?", "Milk is white."),
    ("De quelle couleur est le charbon ?", "What color is coal?", "Coal is black."),
    ("De quelle couleur est le sang ?", "What color is blood?", "Blood is red."),
    ("Quel animal fait « meuh » ?", "Which animal says 'moo'?", "The cow says 'moo'."),
    ("Quel animal fait « cocorico » ?", "Which animal says 'cock-a-doodle-doo'?", "The rooster says 'cock-a-doodle-doo'."),
    ("Quel animal fait « coin-coin » ?", "Which animal says 'quack'?", "The duck says 'quack'."),
    ("Combien de pattes a une fourmi ?", "How many legs does an ant have?", "An ant has 6 legs."),
    ("Combien de pattes a une vache ?", "How many legs does a cow have?", "A cow has 4 legs."),
    ("Combien de pattes a une poule ?", "How many legs does a hen have?", "A hen has 2 legs."),
    ("Quel est le plus grand animal du monde ?", "What is the largest animal in the world?", "The largest animal in the world is the blue whale."),
    ("Quel est l'animal terrestre le plus rapide ?", "What is the fastest land animal?", "The fastest land animal is the cheetah."),
    ("Quel animal fabrique du miel ?", "Which animal makes honey?", "The bee makes honey."),
    ("Quel est le plus grand océan du monde ?", "What is the largest ocean in the world?", "The largest ocean in the world is the Pacific Ocean."),
    ("Quelle est la plus haute montagne du monde ?", "What is the highest mountain in the world?", "The highest mountain in the world is Mount Everest."),
    ("Quel fleuve traverse Paris ?", "Which river flows through Paris?", "The Seine flows through Paris."),
    ("Quelle langue parle-t-on au Brésil ?", "What language is spoken in Brazil?", "Portuguese is spoken in Brazil."),
    ("Quelle est la monnaie du Japon ?", "What is the currency of Japan?", "The currency of Japan is the yen."),
    ("Qu'est-ce que le Soleil ?", "What is the Sun?", "The Sun is a star."),
    ("Combien y a-t-il de planètes dans le système solaire ?", "How many planets are in the solar system?", "There are 8 planets in the solar system."),
    ("Quelle planète est appelée la planète rouge ?", "Which planet is called the red planet?", "Mars is called the red planet."),
    ("Quelle planète a de grands anneaux ?", "Which planet has large rings?", "Saturn has large rings."),
    ("À quelle température l'eau bout-elle ?", "At what temperature does water boil?", "Water boils at 100 degrees Celsius."),
    ("Combien de côtés a un triangle ?", "How many sides does a triangle have?", "A triangle has 3 sides."),
    ("Combien de côtés a un hexagone ?", "How many sides does a hexagon have?", "A hexagon has 6 sides."),
    ("Qui a peint la Joconde ?", "Who painted the Mona Lisa?", "Leonardo da Vinci painted the Mona Lisa."),
    ("Qui a écrit « Les Misérables » ?", "Who wrote 'Les Misérables'?", "Victor Hugo wrote 'Les Misérables'."),
    ("Que mange une vache ?", "What does a cow eat?", "A cow eats grass."),
]
FACTS_FR = dict(FACTS)
for fr_q, en_q, en_a in FACTS_EN:
    PIVOT.append((fr_q, FACTS_FR[fr_q], en_q, en_a))

PIVOT = [p for p in PIVOT if norm(p[0]) not in EVAL_QUESTIONS]

# ------------------------------------------------------------------ écriture
def elide(text):
    """« de » élidé devant une voyelle : d'œufs, d'oranges, d'euros."""
    text = re.sub(r"\b([Dd])e (?=[aeiouyéèêœAEIOUÉ])", r"\1'", text)
    return re.sub(r"\b1 ans\b", "1 an", text)  # « dans 1 an », « 1 an de plus »


def main():
    seen, rows, dropped = set(), [], 0
    for q, a in OUT:
        q, a = elide(q), elide(a)
        if norm(q) in EVAL_QUESTIONS:
            dropped += 1
            continue
        key = (q, a)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"question": q, "answer": a})
    # Sur Telegram on écrit souvent sans « ? » : une partie des questions est dupliquée sans.
    for r in list(rows):
        q = r["question"]
        if q.endswith(" ?") and rng.random() < 0.25 and norm(q) not in EVAL_QUESTIONS:
            rows.append({"question": q[:-2], "answer": r["answer"]})
    for fr_q, fr_a, en_q, en_a in PIVOT:
        fr_q, fr_a = elide(fr_q), elide(fr_a)
        rows.append({"system": SYS_TRANSLATE, "question": fr_q, "answer": en_q})
        rows.append({"system": SYS_ANSWER, "question": en_q, "answer": en_a})
        rows.append({"system": SYS_REWRITE, "question": rewrite_input(fr_q, en_a), "answer": fr_a})
    rng.shuffle(rows)
    path = Path(__file__).with_name("data_fr.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} exemples écrits dans {path.name} dont {3 * len(PIVOT)} pour le mode pivot "
          f"({dropped} questions d'évaluation écartées)")


if __name__ == "__main__":
    main()
