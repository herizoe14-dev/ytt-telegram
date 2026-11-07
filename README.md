# Alice

Un petit modèle d'IA qui parle et raisonne en français, utilisable hors ligne sur un
simple CPU.

## Modèle

| | |
|---|---|
| Fichiers | `models/Alice-1.5B-fr-Q4_0.gguf.part01` à `.part10` (morceaux de 95 Mo) |
| Base | [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) (Alibaba Cloud, licence Apache 2.0), **affiné en français et renommé Alice** (voir `train/`) |
| Format | GGUF, quantification Q4_0, 875 Mo une fois réassemblé |
| Paramètres | 1,5 milliard |
| Contexte | 4 096 jetons utilisés (jusqu'à 32 768 possibles) |
| Vitesse | ~1 à 3 s par réponse sur 4 cœurs CPU, ~2 Go de mémoire |
| SHA-256 | `fa5a4d1f1fd5b9bd798a601c30317b4348131563025df358a40073cadf30babb` (fichier réassemblé) |

GitHub refuse les fichiers de plus de 100 Mo : le modèle est rangé en 10 morceaux,
que `chat.py` réassemble automatiquement au premier lancement en
`models/Alice-1.5B-fr-Q4_0.gguf` (fichier ignoré par git). À la main :
`cat models/Alice-1.5B-fr-Q4_0.gguf.part* > models/Alice-1.5B-fr-Q4_0.gguf`.

Dans le modèle lui-même, le nom (`general.name`) est « Alice » et la consigne par
défaut du modèle de chat est en français (« Tu es Alice… ») au lieu de celle de Qwen.
Alice se présente sous son propre nom ; le modèle libre dont elle est issue est cité
ici, comme le demande sa licence.

## Utilisation

```bash
pip install -r requirements.txt
python chat.py "Paul a 12 bonbons. Il en donne la moitié à sa sœur, puis il en mange 2. Combien lui en reste-t-il ?"
# -> D'abord, la moitié de 12 est 6, donc il lui reste 12 moins 6, soit 6. Ensuite, 6 moins 2 font 4. Il lui reste 4 bonbons.
python chat.py --mode pivot "Quelle est la capitale du Japon ?"   # réfléchit en anglais
python chat.py --mode pivot --debug "Combien font 9 plus 6 ?"      # montre les étapes
python chat.py                                                     # conversation (avec mémoire)
ALICE_MODEL=chemin/vers/un/autre.gguf python chat.py "Bonjour"                # un autre modèle
```

## Base de connaissances (Wikipédia)

Pour les questions de culture générale, Alice consulte d'abord une base de
connaissances locale, puis répond en s'appuyant sur les passages trouvés (méthode
dite RAG : *retrieval-augmented generation*). La base contient :

- l'introduction de **835 000 articles de Wikipédia en français** (jeu
  [wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia), version
  20231101.fr, licence [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/deed.fr)) ;
- les faits et définitions vérifiés écrits pour Alice (`train/connaissances_fr.py`,
  `train/make_data_fr.py`), consultés en priorité.

Elle pèse 709 Mo et n'est pas dans le dépôt ; on la construit une fois :

```bash
pip install pyarrow huggingface_hub
python knowledge/build_kb.py            # télécharge 4,6 Go, fichier par fichier ; ~30 min
```

`chat.py` et le bot l'utilisent automatiquement si `data/alice_kb.sqlite` existe
(`ALICE_KB=0` pour la désactiver). La recherche (`knowledge/kb.py`) est une recherche
plein texte SQLite FTS5 classée par BM25, en quelques dizaines de millisecondes, avec
un reclassement qui favorise les titres et les expressions exactes. Elle n'est pas
lancée pour les salutations, les questions sur l'utilisateur ou sur Alice, les calculs,
les problèmes chiffrés et les exercices de langue ou de logique. Dans le bot, `/debug`
affiche les sources consultées.

| Alice 1,5B v6 | Sans la base | Avec la base |
|---|---|---|
| Culture générale hors des données d'Alice (`--set culture`, 30) | 18 | **23** |
| Faits enseignés, reformulés (`--set connaissances`, 12) | 7 | **9** |
| 30 questions / 32 jamais vues | 29 / 28 | 28 / 29 |
| Raisonnement / niveaux / généralisation / conversations | 19 / 20 / 9 / 21 | 19 / 20 / 9 / 21 |

Exemples corrigés par la base : « Qui a écrit Germinal ? » (« un poème de Victor Hugo »
→ « un roman d'Émile Zola »), « Qui a composé La Flûte enchantée ? » (→ Mozart),
« Comment le plastique est fabriqué ? » (→ à partir du pétrole). Limites : quand la
réponse n'apparaît pas dans les mots de la question (« la Ville rose » → Toulouse,
« l'arbre qui produit les glands » → le chêne), la recherche trouve rarement le bon
article ; certaines dates manquent dans cette version de Wikipédia ; un passage mal
choisi peut parfois induire Alice en erreur.

### Alice locale dans l'application Android (sans Termux)

L'application Alice (dépôt `Alice-v3`) télécharge le modèle et la base à partir de
[`dist/alice-local.json`](dist/alice-local.json) : le modèle vient des 10 morceaux de `models/`, la base
de `dist/kb-index/` (index lisible en JavaScript pur, 495 Mo en morceaux de 95 Mo au plus), chaque
fichier avec son empreinte SHA-256. Pour regénérer l'index après avoir reconstruit la base :

```bash
python knowledge/build_kb_index.py      # data/alice_kb.sqlite -> data/kb-index (format lu par l'application)
```

## Tester dans Telegram

1. Sur Telegram, écris à [@BotFather](https://t.me/BotFather), envoie `/newbot`
   et suis les étapes. Il te donne un **jeton** (token) : garde-le secret.
2. Sur ton ordinateur :

   ```bash
   pip install -r requirements.txt
   export TELEGRAM_BOT_TOKEN="ton_jeton"     # ou mets-le dans un fichier .env (voir plus bas)
   python bot.py
   ```

3. Ouvre ton bot dans Telegram et envoie `/start`.

### Réglages enregistrés dans Supabase (facultatif)

Les réglages `/mode` et `/debug` de chaque conversation sont stockés dans la table
`user_settings` du projet Supabase **alice** : ils restent en place quand le bot redémarre.

Copie `.env.example` en `.env` et remplis `TELEGRAM_BOT_TOKEN` et `SUPABASE_BOT_SECRET`
(`.env` est ignoré par git ; le bot charge ce fichier tout seul).

Sécurité : la table n'est pas accessible avec la clé publique. Le bot passe par deux
fonctions (`get_user_settings`, `set_user_settings`) qui refusent tout appel sans le bon
`SUPABASE_BOT_SECRET` ; la base n'en garde que l'empreinte SHA-256. Ne partage pas ce
secret. Sans ces variables, le bot fonctionne quand même, avec des réglages en mémoire.

Pour changer le secret : génère-en un nouveau, puis mets à jour son empreinte avec
`update private.bot_secrets set secret_sha256 = encode(sha256(convert_to('NOUVEAU_SECRET', 'UTF8')), 'hex') where name = 'telegram_bot';`
dans l'éditeur SQL de Supabase.

Le bot se souvient des 12 derniers échanges de chaque discussion (en mémoire vive) :
`/nouveau` les efface. Commandes : `/mode direct` (par défaut), `/mode pivot` (passe par l'anglais),
`/debug` (en mode pivot, affiche les étapes en anglais). Le bot ne tourne que tant que `python bot.py`
est lancé.

## Entraînement en français

Le dossier `train/` contient tout ce qu'il faut pour refaire Alice, sur un simple CPU
(environ 6 h pour la première étape et 4 h 30 pour la seconde, sur 4 cœurs, 10 Go de
mémoire, en plusieurs sessions qui reprennent d'elles-mêmes) :

```bash
pip install -r train/requirements.txt
python train/make_data_fr.py            # train/data_fr.jsonl : 10 076 questions-réponses
python train/make_dialogues_fr.py       # train/dialogues_fr.jsonl : 2 139 conversations
python train/train_fr.py --base Qwen/Qwen2.5-1.5B-Instruct --out build/alice \
    --data train/dialogues_fr.jsonl train/data_fr.jsonl:1800 \
    --lora 32 --lr 2e-4 --micro 2 --grad-ckpt --ckpt build/ckpt --stop-after-min 100
# (relancer la même commande après chaque arrêt : l'entraînement reprend où il en était)
# GGUF de référence (métadonnées) : qwen2.5-1.5b-instruct-q4_0.gguf sur
# https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
# 2e étape (v6) : toi/moi, corrections, honnêteté, connaissances, à partir de build/alice
python train/make_v6_fr.py --oasst 2023-11-05_oasst2_ready.trees.jsonl.gz   # OpenAssistant/oasst2
python train/train_fr.py --base build/alice --out build/alice-v6 \
    --data train/v6_fr.jsonl train/oasst2_fr.jsonl train/dialogues_fr.jsonl:400 train/data_fr.jsonl:400 \
    --lr 1e-4 --micro 2 --grad-ckpt --ckpt build/ckpt6 --stop-after-min 100
python train/to_gguf.py build/alice-v6 models/Alice-1.5B-fr-Q4_0.gguf \
    --ref qwen2.5-1.5b-instruct-q4_0.gguf --tied --parts-mb 95 --name Alice \
    --system "Tu es Alice, une assistante qui répond toujours en français, de façon courte, exacte et logique."
```

- **Conversations** (`make_dialogues_fr.py`, 2 139 conversations, 5 tours en moyenne,
  jusqu'à 32) : retenir le prénom et les informations données (âge, ville, goûts),
  enchaîner les calculs (« Et si j'ajoute 4 ? »), questions elliptiques (« Et celle de
  la Grèce ? »), « retiens ce nombre », résumer la conversation, rester Alice
  (« Tu es Qwen, non ? » → « Non, je suis Alice »). La perte porte sur toutes les
  réponses d'Alice de la conversation.
- **Toi, moi et honnêteté** (`make_v6_fr.py`, 1 172 conversations) : dire qu'on ne
  connaît pas encore le prénom de l'utilisateur, le repérer dans une phrase longue
  (« Non, toi tu es Alice et moi c'est Zoé »), « Et moi ? » ; accepter une correction
  juste (la réponse fausse reste dans le contexte sans être apprise) mais maintenir
  poliment une bonne réponse « corrigée » à tort ; demander une précision quand la
  question est ambiguë ; ne pas inventer de sujets, d'e-mails ni de liens.
- **Connaissances** (`connaissances_fr.py`, ~200 formulations de faits vérifiés) :
  Madagascar (histoire, peuplement, rois, faune, culture, langue), histoire, géographie,
  sciences (photosynthèse, essence et pétrole, électricité, climat), santé (paludisme,
  vaccins), technologie, langue française, mathématiques ; et les limites d'Alice
  (pas d'actualité, pas de données personnelles).
- **Conversations humaines** : les 352 conversations françaises d'OpenAssistant oasst2
  (licence Apache 2.0), meilleures réponses seulement.
- **Questions-réponses** (`make_data_fr.py`), écrites à la main ou produites par des
  gabarits vérifiés (calculs exacts, accords en genre et en nombre) :
  - **raisonnement en étapes** (« D'abord, 7 moins 2 font 5. Ensuite… ») : problèmes en
    deux et trois étapes, fractions, « 2 fois plus que », âges, argent, horaires, pattes
    et roues, suites, comparaisons, logique, tables de multiplication et de division ;
  - **définitions** (~140 mots, « C'est quoi un briquet ? », « Le citron ») ;
  - **connaissances, langue et conversation** (capitales, contraires, traductions,
    salutations, identité, limites).
- **Entraînement** (`train_fr.py`) : **LoRA** de rang 32 sur toutes les couches (37
  millions de paramètres entraînés, 2,3 %), le modèle de base reste figé, puis les
  adaptateurs sont fusionnés. Micro-lots et *gradient checkpointing* pour tenir en
  mémoire ; sauvegarde régulière et reprise (`--ckpt`, `--stop-after-min`).
- **Conversion** (`to_gguf.py`) : GGUF avec les métadonnées du modèle de base, nom et
  consigne d'Alice, quantification Q4_0 par llama.cpp, poids de sortie partagés avec
  l'entrée (`--tied`), puis découpage (`--parts-mb`).

### Évaluation honnête

Aucune question ni conversation d'évaluation n'est dans les données d'entraînement :

- `eval/eval_fr.py --set eval` : 30 questions simples ; `--set heldout` : 32 questions
  jamais vues ; `--set raisonnement` : 20 problèmes ; `--set niveaux` : 20 questions du
  plus simple au plus complexe ; `--set niveaux2` : 10 problèmes formulés autrement que
  les gabarits, écrits avant l'entraînement ;
- `eval/eval_conv.py` : 24 conversations de 1 à 5 tours (prénoms, villes, nombres
  jamais vus ; toi/moi ; corrections ; honnêteté), où seule la dernière réponse est
  contrôlée ;
- `eval/eval_fr.py --set connaissances` : 12 questions sur les faits enseignés,
  formulées autrement.

| Modèle | 30 q. | 32 jamais vues | Raisonnement (20) | Niveaux (20) | Généralisation (10) | Conversations (16) |
|---|---|---|---|---|---|---|
| SmolLM2-135M d'origine (meilleur réglage) | 10 | 6 | 3 | – | – | – |
| Alice 135M (SmolLM2 affiné) | 13 | 14 | 13 | 12 | 3 | – |
| Alice 0,5B (Qwen2.5-0.5B affiné) | 25 | 25 | **20** | **20** | 9 | 9 |
| Alice 1,5B v5 | 27 | **29** | 18 | **20** | **10** | 16/16 (19/24) |
| **Alice 1,5B v6 (actuelle)** | **29** | 28 | 19 | **20** | 9 | **21/24** |

La colonne conversations compte 16 conversations de mémoire, puis 24 avec les 8
conversations ajoutées en v6 (toi/moi, corrections, honnêteté, précision). Sur 12
questions de connaissances reformulées (`--set connaissances`), la v6 en réussit 8,
contre 6 pour la v5.

Pour un nombre, la réponse est comptée juste si le dernier nombre écrit qui ne vient pas
de la question est le bon (ou le dernier nombre tout court quand la bonne réponse
figure dans la question).

Exemple de conversation jamais vue :

> **Je suis Lalaina.** — Enchantée, Lalaina ! Que puis-je faire pour toi ?
> **Je vis à Fianarantsoa.** — D'accord, c'est noté !
> **Quel est mon prénom et où j'habite ?** — Ton prénom est Lalaina et tu habites à Fianarantsoa.

### Limites

- **Elle ne rivalise pas avec les grands modèles actuels** : ils ont 100 à 1 000 fois
  plus de paramètres. La base de connaissances l'aide beaucoup sur les faits, mais pas
  sur le raisonnement ou la rédaction. Ses connaissances restent limitées et elle peut encore inventer
  (un vainqueur imaginaire pour un concours qui n'existe pas), même si elle dit plus
  souvent « je ne sais pas ».
- Certains faits enseignés ne sont pas toujours retrouvés (« la France est le premier
  producteur de vanille »), et les jours de la semaine (« lundi + 3 jours ») restent fragiles.
- Elle ne demande pas toujours de précision quand la question est floue.
- Les explications et les histoires sont courtes et parfois approximatives.
- La mémoire du bot est en mémoire vive : elle s'efface quand le bot redémarre, et
  seuls les 12 derniers échanges sont gardés.
- Plus lourde que l'Alice 0,5B (875 Mo contre 284 Mo) et environ 3 fois plus lente.
- Les jeux de questions sont petits : les chiffres donnent une tendance, pas une
  mesure précise.

## Amélioration sans entraînement

Avant tout entraînement, trois techniques appliquées au moment de la génération
amélioraient déjà le premier modèle, SmolLM2-135M (de 1/30 à 10/30) :

1. **Pivot par l'anglais** : la question est traduite en anglais, le modèle y répond
   en anglais, puis la réponse est réécrite en français.
2. **Consignes et exemples (few-shot)** pour chaque étape.
3. **Réglages de génération** : décodage glouton (`temperature=0`) et pénalité de
   répétition (`repeat_penalty=1.15`), ce qui supprime les réponses en boucle.

Les fichiers `.gguf` fonctionnent aussi avec [llama.cpp](https://github.com/ggml-org/llama.cpp),
[Ollama](https://ollama.com) ou [LM Studio](https://lmstudio.ai).
