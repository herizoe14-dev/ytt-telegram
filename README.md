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
| SHA-256 | `1c1441a53962b799360fdb5dc84fe810ebb3c26deba685bc3deabcd29eeeb7cd` (fichier réassemblé) |

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
(environ 6 h sur 4 cœurs, 10 Go de mémoire, en plusieurs sessions qui reprennent
d'elles-mêmes) :

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
python train/to_gguf.py build/alice models/Alice-1.5B-fr-Q4_0.gguf \
    --ref qwen2.5-1.5b-instruct-q4_0.gguf --tied --parts-mb 95 --name Alice \
    --system "Tu es Alice, une assistante qui répond toujours en français, de façon courte, exacte et logique."
```

- **Conversations** (`make_dialogues_fr.py`, 2 139 conversations, 5 tours en moyenne,
  jusqu'à 32) : retenir le prénom et les informations données (âge, ville, goûts),
  enchaîner les calculs (« Et si j'ajoute 4 ? »), questions elliptiques (« Et celle de
  la Grèce ? »), « retiens ce nombre », résumer la conversation, rester Alice
  (« Tu es Qwen, non ? » → « Non, je suis Alice »). La perte porte sur toutes les
  réponses d'Alice de la conversation.
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
- `eval/eval_conv.py` : 16 conversations de 2 à 5 tours (prénoms, villes, nombres
  jamais vus), où seule la dernière réponse est contrôlée.

| Modèle | 30 q. | 32 jamais vues | Raisonnement (20) | Niveaux (20) | Généralisation (10) | Conversations (16) |
|---|---|---|---|---|---|---|
| SmolLM2-135M d'origine (meilleur réglage) | 10 | 6 | 3 | – | – | – |
| Alice 135M (SmolLM2 affiné) | 13 | 14 | 13 | 12 | 3 | – |
| Alice 0,5B (Qwen2.5-0.5B affiné) | 25 | 25 | **20** | **20** | 9 | 9 |
| **Alice 1,5B (actuelle)** | **27** | **29** | 18 | **20** | **10** | **16** |

Pour un nombre, la réponse est comptée juste si le dernier nombre écrit qui ne vient pas
de la question est le bon (ou le dernier nombre tout court quand la bonne réponse
figure dans la question).

Exemple de conversation jamais vue :

> **Je suis Lalaina.** — Enchantée, Lalaina ! Que puis-je faire pour toi ?
> **Je vis à Fianarantsoa.** — D'accord, c'est noté !
> **Quel est mon prénom et où j'habite ?** — Ton prénom est Lalaina et tu habites à Fianarantsoa.

### Limites

- La culture générale a encore des trous (« La capitale de l'Allemagne est Berne »,
  « la planète la plus proche du Soleil est la Lune »), et les jours de la semaine
  (« lundi + 3 jours ») restent fragiles.
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
