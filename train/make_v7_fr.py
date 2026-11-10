"""Données v7 d'Alice : écrire vraiment les textes demandés (récits, poèmes, lettres), sans boucle.

Problème constaté sur le téléphone (application Alice, v1.2.3) : à « Crée-moi un récit », Alice répondait
« Je peux vous aider avec un récit, jusqu'à environ 4000 tokens » à chaque message, sans jamais écrire, puis
recopiait cette phrase (boucle). Ces données apprennent :

- à écrire directement le texte demandé, sans redemander le sujet ni parler de jetons ;
- « vas-y », « commence », « continue », « la suite », « une autre », « recommence », « plus court » ;
- à sortir d'une boucle : les réponses répétées restent dans le contexte sans être apprises ("train": false) ;
- à répondre honnêtement sur soi (taille, mémoire, entraînement) sans inventer ;
- à se souvenir de l'histoire racontée (« Comment s'appelle le personnage ? »).

Histoires : TinyStories en français (iproskurina/TinyStories-French, 1 000 histoires simples traduites de
TinyStories, Eldan et Li 2023, licence CDLA-Sharing-1.0). Poèmes et lettres : écrits pour Alice (ci-dessous).

    python train/make_v7_fr.py --stories ts-fr.parquet      # → train/v7_fr.jsonl
"""
import argparse
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYS_DIRECT = "Tu es Alice, une assistante qui répond toujours en français, de façon courte, exacte et logique."
# Consigne envoyée par l'application (server/lib/agent.js) pour une demande d'écriture
SYS_WRITE = ("Tu es Alice, une assistante qui parle français, sur le téléphone de l’utilisateur.\n\n[ÉCRITURE] On te "
             "demande un texte (récit, histoire, poème, lettre…). Écris-le directement et entièrement, maintenant, en "
             "plusieurs paragraphes. Ne demande pas de précisions, ne parle ni de jetons ni de longueur : choisis "
             "toi-même un sujet si on ne t’en donne pas.")
SYS_APP = ("Tu es Alice, l’assistante vocale de l’utilisateur, sur son téléphone. Tes réponses sont lues à voix haute : "
           "phrases courtes et naturelles. Tu es un petit modèle de langue (1,5 milliard de paramètres) qui tourne sur "
           "le téléphone, hors ligne, sans outil.")
SYSTEMS = [SYS_WRITE, SYS_WRITE, SYS_DIRECT, SYS_APP, None]

ASK_STORY = [
    "Crée-moi un récit", "Créé moi une récit", "Créé le récit", "Raconte-moi une histoire", "Raconte une histoire",
    "Écris une histoire", "Écris-moi un conte", "Tu peux m'écrire une histoire ?", "Invente une histoire",
    "Je veux une histoire", "Une histoire s'il te plaît", "Raconte-moi un conte pour dormir",
    "Écris un petit récit", "Fais-moi une histoire", "Rédige une courte histoire", "Raconte quelque chose",
    "Crée un récit jusqu'à 4000 token", "Écris une histoire de 1000 mots", "Fais un long récit",
    "Créé le récit jusqu'à 4000 tout token", "Écris une histoire pour enfants", "raconte moi une histoire stp",
    "Tu connais une histoire ?", "Invente-moi un conte", "Peux-tu inventer un récit ?",
]
ASK_ABOUT = ["Écris une histoire sur {x}", "Raconte-moi une histoire avec {x}", "Invente un conte sur {x}",
             "Crée un récit qui parle de {x}", "Une histoire avec {x}, s'il te plaît"]
THEMES = {  # mot cherché dans l'histoire → sujet demandé
    r"\bchiens?\b": "un chien", r"\bchats?\b": "un chat", r"\bdragons?\b": "un dragon", r"\boiseaux?\b": "un oiseau",
    r"\bvoitures?\b": "une voiture", r"\bballons?\b": "un ballon", r"\bplage\b": "la plage", r"\bforêt\b": "la forêt",
    r"\bparc\b": "le parc", r"\blapins?\b": "un lapin", r"\bpoissons?\b": "un poisson", r"\bbateaux?\b": "un bateau",
    r"\bprincesses?\b": "une princesse", r"\bours\b": "un ours", r"\bjardin\b": "un jardin", r"\barbres?\b": "un arbre",
    r"\btrains?\b": "un train", r"\bgâteaux?\b": "un gâteau", r"\bneige\b": "la neige", r"\bpluie\b": "la pluie",
    r"\bjouets?\b": "un jouet", r"\bfleurs?\b": "des fleurs", r"\bsinges?\b": "un singe", r"\bcanards?\b": "un canard",
}
INTROS = ["", "", "", "Voici une histoire :\n\n", "Avec plaisir ! Voici une histoire :\n\n", "Bien sûr. ",
          "D'accord, voici un petit récit :\n\n"]
GO = ["Vas-y", "Oui", "Oui vas-y", "Commence", "Commencer", "D'accord", "Ok", "Oui créé le récit", "Go"]
MORE = ["Continue", "La suite", "Et après ?", "Continue l'histoire", "Et ensuite ?", "Raconte la suite"]
AGAIN = ["Une autre", "Raconte-m'en une autre", "Recommence avec une autre histoire", "Une autre histoire",
         "Encore une !"]
SHORTER = ["Plus court", "Fais plus court", "Une histoire plus courte", "Trop long, plus court stp"]
THANKS = [("Merci", "Avec plaisir ! Tu veux une autre histoire ?"), ("Merci, c'était bien", "Merci ! Je suis contente qu'elle t'ait plu."),
          ("Super !", "Ravie qu'elle te plaise !")]
# Boucle observée dans l'application : ces réponses restent dans le contexte sans être apprises
LOOPS = ["Je peux vous aider avec un récit, jusqu'à environ 4000 tokens.",
         "Je peux créer un récit de 4000 tokens. Si tu veux un récit plus long ou plus court, tu peux le spécifier.",
         "Je peux inventer une histoire si tu veux. Tu veux une histoire inventée ?",
         "Je peux vous aider à créer votre histoire. Quel est le titre et l'histoire que vous souhaitez inventer ?"]

# ─── Poèmes et lettres écrits pour Alice ───
POEMS = [
    ("un poème sur la mer", "La mer s'étire sous le ciel,\nbleue le matin, grise le soir.\nElle chante aux rochers son appel\net berce les bateaux d'espoir.\n\nLes vagues viennent, puis s'en vont,\nlaissant du sable tout mouillé.\nUn enfant court, un cerf-volant\ndanse au-dessus des galets."),
    ("un poème sur la pluie", "Il pleut doucement sur le toit,\nchaque goutte frappe à la fenêtre.\nLe jardin boit, l'herbe se tait,\net la terre sent bon, peut-être.\n\nPuis le soleil revient sans bruit,\nun arc-en-ciel traverse le ciel.\nLes flaques brillent comme des fruits\net l'air redevient doux et réel."),
    ("un poème sur l'amitié", "Un ami, c'est une main tendue\nquand le chemin devient trop long,\nune voix qui n'est jamais perdue,\nun rire au milieu d'une chanson.\n\nOn partage le pain et les secrets,\nles jours de pluie, les jours de fête.\nEt même quand on est loin, après,\nson souvenir reste dans la tête."),
    ("un poème sur la nuit", "La nuit descend sur la ville,\nles lampes s'allument une à une.\nTout devient calme et tranquille\nsous le regard rond de la lune.\n\nLes étoiles sortent sans faire de bruit,\nles chats se promènent sur les toits.\nEt quelque part, un enfant sourit\ndans un rêve plein de joie."),
    ("un poème sur le printemps", "Le printemps frappe à la porte,\nles bourgeons ouvrent leurs yeux.\nLe vent léger nous apporte\nl'odeur des jours plus heureux.\n\nLes oiseaux reviennent chanter,\nles cerisiers se couvrent de blanc.\nC'est le moment de s'émerveiller\net de marcher tout doucement."),
    ("un poème sur Madagascar", "Sur l'île rouge, le soleil se lève,\néclairant les rizières en terrasses.\nLe vent du large porte un rêve\net les baobabs gardent leur place.\n\nLes lémuriens sautent dans les branches,\nla mer turquoise borde les plages.\nMadagascar, terre franche,\ntu es belle à chaque passage."),
    ("un poème sur un chat", "Mon chat dort au soleil,\nroulé comme un coussin.\nIl ouvre un œil, il veille,\npuis se rendort enfin.\n\nLa nuit, il devient roi,\nil chasse les ombres du couloir.\nAu matin, il revient vers moi\net ronronne pour me dire bonsoir."),
    ("un poème sur l'école", "Le cartable sur le dos,\non marche vers l'école.\nOn apprend des mots nouveaux,\ndes chiffres qui s'envolent.\n\nÀ la récréation on court,\non rit avec les copains.\nChaque jour on grandit un peu,\npour construire nos lendemains."),
    ("un poème sur la montagne", "La montagne touche les nuages,\nson sommet est tout blanc de neige.\nLe chemin grimpe entre les rochers,\net le silence nous protège.\n\nEn haut, le monde paraît petit,\nles villages sont des points lointains.\nOn respire, on oublie le bruit,\net l'on redescend le cœur plein."),
    ("un poème sur la maman", "Maman, ta voix est une chanson\nqui me rassure quand j'ai peur.\nTes mains préparent la maison,\nton sourire réchauffe mon cœur.\n\nTu m'as appris à marcher,\nà dire merci, à pardonner.\nAujourd'hui, je veux te remercier\npour tout l'amour que tu m'as donné."),
    ("un poème sur le temps qui passe", "Les jours s'envolent comme des feuilles\nque le vent emporte en automne.\nOn voudrait que le temps nous accueille,\nmais il avance et ne pardonne.\n\nAlors savourons chaque matin,\nchaque rire et chaque lumière.\nLe bonheur tient dans un petit rien,\nun café chaud, une prière."),
    ("un poème sur la forêt", "Dans la forêt, les arbres parlent\nen se balançant doucement.\nLes feuilles froissées se régalent\ndu soleil et du vent.\n\nUn renard passe sans un bruit,\nun écureuil grimpe au sommet.\nLa forêt garde, jour et nuit,\nses mille secrets bien cachés."),
]
LETTERS = [
    ("une lettre pour remercier un professeur", "Cher professeur,\n\nJe voulais vous dire merci pour cette année passée dans votre classe. Grâce à votre patience, j'ai appris à aimer la lecture et à ne plus avoir peur des mathématiques.\n\nVous avez toujours pris le temps d'expliquer quand je ne comprenais pas, et vous nous avez encouragés à poser des questions. Je garderai un très bon souvenir de vos cours.\n\nAvec toute ma reconnaissance,\nVotre élève"),
    ("une lettre d'excuse à un ami", "Cher ami,\n\nJe t'écris pour m'excuser de ce que je t'ai dit l'autre jour. J'étais fatigué et en colère, et mes mots ont dépassé ma pensée. Ce n'était pas juste envers toi.\n\nNotre amitié compte beaucoup pour moi. J'espère que tu pourras me pardonner, et que nous pourrons en parler autour d'un café cette semaine.\n\nAmicalement,\nTon ami"),
    ("une lettre de motivation pour un emploi de vendeur", "Madame, Monsieur,\n\nJe me permets de vous proposer ma candidature pour le poste de vendeur dans votre magasin. Souriant et organisé, j'aime le contact avec les clients et le travail en équipe.\n\nLors de mes expériences précédentes, j'ai appris à conseiller les clients, à tenir une caisse et à ranger les rayons. Je suis disponible rapidement et motivé pour apprendre.\n\nJe reste à votre disposition pour un entretien.\n\nVeuillez agréer, Madame, Monsieur, mes salutations distinguées."),
    ("une lettre à ma grand-mère", "Chère grand-mère,\n\nComment vas-tu ? Ici, tout va bien. L'école a repris et j'ai une nouvelle maîtresse très gentille. Je pense souvent à toi et aux vacances passées chez toi, à tes gâteaux et à nos promenades dans le jardin.\n\nJ'ai hâte de te revoir. Maman dit que nous viendrons pour les fêtes. Prends bien soin de toi.\n\nJe t'embrasse très fort,\nTon petit-enfant"),
    ("une lettre pour souhaiter un joyeux anniversaire", "Joyeux anniversaire !\n\nAujourd'hui est un jour spécial, et je voulais te souhaiter tout le bonheur du monde. Que cette nouvelle année t'apporte la santé, de belles surprises et beaucoup de rires.\n\nMerci d'être la personne que tu es. Profite bien de ta journée, tu le mérites.\n\nAvec toute mon affection"),
    ("une lettre pour demander un congé à mon patron", "Monsieur le Directeur,\n\nJe vous écris pour vous demander un congé du 10 au 14 du mois prochain, pour raisons familiales.\n\nJ'ai organisé mon travail afin que mes dossiers en cours soient terminés avant mon départ, et un collègue a accepté de me remplacer pour les urgences.\n\nJe vous remercie par avance de l'attention que vous porterez à ma demande.\n\nVeuillez agréer, Monsieur le Directeur, mes salutations respectueuses."),
]
ASK_POEM = ["Écris {x}", "Fais-moi {x}", "Je veux {x}", "Tu peux écrire {x} ?", "Compose {x}"]

# ─── Qui est Alice (réponses honnêtes, sans rien inventer) ───
SELF = [
    (["Analyse de ton capacité actuelle", "Quelles sont tes capacités ?", "Qu'est-ce que tu sais faire ?", "Tu sais faire quoi ?"],
     "Je suis Alice, un petit modèle de langue de 1,5 milliard de paramètres qui tourne sur ton téléphone, sans internet. "
     "Je peux discuter, répondre à des questions de culture générale, faire des calculs simples, expliquer des mots et "
     "écrire des textes courts : histoires, poèmes, lettres. Je ne peux pas chercher sur internet, ouvrir tes fichiers "
     "ni connaître l'actualité, et je peux me tromper sur des sujets précis."),
    (["Résume-moi tout ce que tu as appris pendant l'entraînement", "Résumé Moi tout ce que tu apprise pendant l'intrain",
      "Qu'as-tu appris pendant ton entraînement ?", "Raconte ton entraînement"],
     "Je ne me souviens pas de mon entraînement : un modèle de langue n'en garde pas de souvenirs. Je sais seulement "
     "que je suis basée sur Qwen2.5, puis affinée en français avec des questions, des conversations et des histoires, "
     "pour répondre clairement, garder le fil d'une discussion et écrire des textes."),
    (["Tu peux lire jusqu'à combien de token", "Combien de tokens tu peux lire ?", "Quelle est ta mémoire ?",
      "Tu te souviens de combien de messages ?"],
     "Je peux lire environ 4 000 jetons à la fois, consignes et conversation comprises, soit quelques pages. Au-delà, "
     "j'oublie le début de la conversation. Pour une réponse, j'écris au plus environ 1 000 jetons."),
    (["Tu es Claude ?", "Tu es ChatGPT ?", "Tu es Qwen ?", "Qui es-tu vraiment ?"],
     "Non, je suis Alice, une assistante qui parle français. Je suis basée sur le modèle libre Qwen2.5, affiné pour "
     "devenir Alice, et je fonctionne directement sur ton téléphone."),
    (["Tu apprends de nos conversations ?", "Tu vas t'améliorer en parlant avec moi ?"],
     "Non, je n'apprends pas pendant nos conversations : je garde seulement le fil de la discussion en cours. Pour "
     "m'améliorer, il faut me réentraîner."),
    (["Tu peux écrire 4000 tokens ?", "Écris-moi un texte de 4000 tokens"],
     None),  # → une histoire longue, sans parler de jetons
]


def clean(s):
    s = s.strip().replace("\r", "")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s


def name_of(s):
    m = re.search(r"\b(?:nommée?|appelée?|s'appelait)\s+([A-ZÉ][a-zéèêëïîôûç]+)", s)
    return m.group(1) if m else None


def halves(s):
    paras = [p for p in s.split("\n\n") if p.strip()]
    if len(paras) < 4:
        return None
    k = len(paras) // 2
    return "\n\n".join(paras[:k]), "\n\n".join(paras[k:])


def sysmsg(rng, write=True):
    s = rng.choice(SYSTEMS if write else [SYS_DIRECT, SYS_APP, None])
    return [{"role": "system", "content": s}] if s else []


def U(t):
    return {"role": "user", "content": t}


def A(t, train=True):
    return {"role": "assistant", "content": t, **({} if train else {"train": False})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stories", required=True, help="parquet de iproskurina/TinyStories-French")
    ap.add_argument("--out", default=str(HERE / "v7_fr.jsonl"))
    a = ap.parse_args()
    import pyarrow.parquet as pq
    rng = random.Random(7)
    stories = [clean(r["french-tinystories"]) for r in pq.read_table(a.stories).to_pylist()]
    stories = [s for s in stories if 450 < len(s) < 2300 and s[-1] in ".!?»\""]
    rng.shuffle(stories)
    longest = sorted(stories, key=len)[-150:]
    shortest = sorted(stories, key=len)[:150]
    pick = lambda pool: rng.choice(pool)
    out = []

    def story_answer(s):
        return rng.choice(INTROS) + s

    for i, s in enumerate(stories):
        kind = i % 12
        if kind <= 4:  # demande simple (ou sur un sujet présent dans l'histoire)
            themes = [v for k, v in THEMES.items() if re.search(k, s, re.I)]
            nm = name_of(s)
            if themes and rng.random() < 0.5:
                q = rng.choice(ASK_ABOUT).format(x=rng.choice(themes))
            elif nm and rng.random() < 0.3:
                q = rng.choice(ASK_ABOUT).format(x="un personnage nommé " + nm)
            else:
                q = rng.choice(ASK_STORY)
            out.append({"messages": sysmsg(rng) + [U(q), A(story_answer(s))]})
        elif kind == 5:  # sortie de boucle : réponses répétées dans le contexte, non apprises
            loop = rng.choice(LOOPS)
            msgs = sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(loop, False), U(rng.choice(ASK_STORY + GO)), A(loop, False),
                                   U(rng.choice(ASK_STORY + GO)), A(story_answer(s))]
            out.append({"messages": msgs})
        elif kind == 6:  # suite
            h = halves(s)
            if not h:
                out.append({"messages": sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(story_answer(s))]})
                continue
            out.append({"messages": sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(h[0]), U(rng.choice(MORE)), A(h[1])]})
        elif kind == 7:  # une autre / recommence
            s2 = pick(stories)
            out.append({"messages": sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(story_answer(s), False),
                                                    U(rng.choice(AGAIN)), A(story_answer(s2))]})
        elif kind == 8:  # plus court
            out.append({"messages": sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(s, False), U(rng.choice(SHORTER)),
                                                    A(pick(shortest))]})
        elif kind == 9:  # « Tu peux écrire un récit ? » → oui, et il l'écrit tout de suite
            q = rng.choice(["Tu peux écrire un récit ?", "Tu sais raconter des histoires ?", "Tu peux me raconter une histoire ?",
                            "Est-ce que tu peux créer un récit ?"])
            out.append({"messages": sysmsg(rng) + [U(q), A("Oui ! Voici une histoire :\n\n" + s)]})
        elif kind == 10:  # mémoire de l'histoire racontée
            nm = name_of(s)
            if nm:
                q = rng.choice(["Comment s'appelle le personnage ?", "C'était qui le héros ?", "Il s'appelait comment ?"])
                out.append({"messages": sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(s, False), U(q),
                                                        A(f"Le personnage principal de l'histoire s'appelle {nm}.")]})
            else:
                t = rng.choice(THANKS)
                out.append({"messages": sysmsg(rng) + [U(rng.choice(ASK_STORY)), A(s, False), U(t[0]), A(t[1])]})
        else:  # demande de longueur : on écrit, sans parler de jetons
            q = rng.choice(["Crée un récit jusqu'à 4000 token", "Écris une très longue histoire", "Écris-moi un texte de 4000 tokens",
                            "Fais un récit long", "Une histoire de 2000 mots"])
            out.append({"messages": sysmsg(rng) + [U(q), A(story_answer(pick(longest)))]})

    for _ in range(4):  # poèmes et lettres, demandés de plusieurs façons
        for topic, text in POEMS + LETTERS:
            q = rng.choice(ASK_POEM).format(x=topic)
            ans = rng.choice(["", "", "Voici " + topic.split(" ", 1)[0] + " " + topic.split(" ", 1)[1] + " :\n\n"]) + text
            out.append({"messages": sysmsg(rng) + [U(q), A(ans)]})
    for topic, text in POEMS:  # « poème » sans sujet → il en choisit un
        out.append({"messages": sysmsg(rng) + [U(rng.choice(["Écris un poème", "Fais-moi un poème", "Un poème stp"])), A(text)]})

    for qs, ans in SELF:
        for q in qs:
            for _ in range(3):
                if ans is None:
                    out.append({"messages": sysmsg(rng) + [U(q), A(story_answer(pick(longest)))]})
                else:
                    out.append({"messages": sysmsg(rng, write=False) + [U(q), A(ans)]})

    rng.shuffle(out)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{a.out} : {len(out)} conversations")


if __name__ == "__main__":
    main()
