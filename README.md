# Alice

Un petit modèle d'IA qui parle et raisonne en français, utilisable hors ligne sur un
simple CPU.

## Modèle

| | |
|---|---|
| Fichiers | `models/Alice-Qwen2.5-0.5B-fr-Q4_0-0000{1..4}-of-00004.gguf` (4 morceaux) |
| Base | [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) (Alibaba Cloud), **affiné en français** (voir `train/`) |
| Format | GGUF, quantification Q4_0, ~284 Mo au total |
| Paramètres | ~500 millions |
| Licence | Apache 2.0 |
| Vitesse | ~0,7 s par réponse sur 4 cœurs CPU |

Le modèle est découpé en morceaux de moins de 100 Mo (la limite de GitHub par
fichier) ; llama.cpp les recharge tous à partir du premier. L'ancienne Alice
(SmolLM2-135M, 92 Mo) a été remplacée : 3,7 fois plus de paramètres et bien meilleure
en français (voir les résultats plus bas).

## Utilisation

```bash
pip install -r requirements.txt
python chat.py "Paul a 12 bonbons. Il en donne la moitié à sa sœur, puis il en mange 2. Combien lui en reste-t-il ?"
# -> D'abord, la moitié de 12 est 6, donc il lui reste 12 moins 6, soit 6. Ensuite, 6 moins 2 font 4. Il lui reste 4 bonbons.
python chat.py --mode pivot "Quelle est la capitale du Japon ?"   # réfléchit en anglais
python chat.py --mode pivot --debug "Combien font 9 plus 6 ?"      # montre les étapes
python chat.py                                                     # mode interactif
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

Commandes du bot : `/mode direct` (par défaut, rapide), `/mode pivot` (passe par l'anglais),
`/debug` (en mode pivot, affiche les étapes en anglais). Le bot ne tourne que tant que `python bot.py`
est lancé.

## Entraînement en français

Le dossier `train/` contient tout ce qu'il faut pour refaire Alice, sur un simple CPU
(environ 2 h sur 4 cœurs, 6 Go de mémoire) :

```bash
pip install -r train/requirements.txt
python train/make_data_fr.py            # génère train/data_fr.jsonl (10 051 exemples)
python train/train_fr.py --base Qwen/Qwen2.5-0.5B-Instruct --out build/alice-qwen \
    --lora 32 --lr 2e-4 --micro 4 --epochs 1
# GGUF de référence (métadonnées) : qwen2.5-0.5b-instruct-q4_0.gguf sur
# https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
python train/to_gguf.py build/alice-qwen models/Alice-Qwen2.5-0.5B-fr-Q4_0.gguf \
    --ref qwen2.5-0.5b-instruct-q4_0.gguf --split-mb 90 --tied
```

- **Données** (`make_data_fr.py`), écrites à la main ou produites par des gabarits
  vérifiés (calculs exacts, accords en genre et en nombre) :
  - **Raisonnement en étapes** (~4 000 exemples) : la réponse pose chaque étape avant
    le résultat (« D'abord, 7 moins 2 font 5. Ensuite, 5 plus 3 font 8. Elle a 8 pommes. »).
    Problèmes en deux et trois étapes, la moitié / le tiers / le quart, « 2 fois plus
    que », « de plus que », âges, argent, horaires, pattes et roues (« une vache a 4
    pattes… »), suites, comparaisons, pair ou impair, partages, petite logique, tables
    de multiplication et de division.
  - **Définitions** (~140 mots) : « C'est quoi un briquet ? », ou un sujet seul
    (« Le citron » → « Le citron est un fruit jaune au goût acide. »).
  - **Connaissances et langue** : capitales, faits simples, contraires, pluriels,
    traductions, jours et mois.
  - **Conversation** : salutations, identité d'Alice, ce qu'elle sait faire, limites
    (« Je n'ai pas accès à la météo »).
- **Entraînement** (`train_fr.py`) : **LoRA** de rang 32 sur toutes les couches. Le
  modèle de base reste figé ; seuls 17,6 millions de paramètres (3,4 %) sont
  entraînés, ce qui préserve ses connaissances. Les adaptateurs sont ensuite fusionnés
  dans le modèle : aucun paramètre ajouté au final. La perte ne porte que sur les
  réponses, et des micro-lots limitent la mémoire.
- **Conversion** (`to_gguf.py`) : écriture en GGUF avec les métadonnées du modèle de
  base, quantification Q4_0 par llama.cpp, poids de sortie partagés avec l'entrée
  (`--tied`, -145 Mo) et découpage en morceaux (`--split-mb`). L'outil gère aussi
  SmolLM2 (`ALICE_BASE=smollm2` pour les données).

### Évaluation honnête

Aucune question d'évaluation n'est dans les données d'entraînement. Cinq séries :

- `--set eval` : 30 questions simples ;
- `--set heldout` : 32 questions jamais vues ;
- `--set raisonnement` : 20 problèmes jamais vus ;
- `--set niveaux` : 20 questions du plus simple au plus complexe ;
- `--set niveaux2` : 10 problèmes formulés autrement que les gabarits d'entraînement,
  écrits avant l'entraînement, pour vérifier qu'Alice généralise.

| Modèle | 30 questions | 32 jamais vues | Raisonnement (20) | Niveaux (20) | Généralisation (10) |
|---|---|---|---|---|---|
| SmolLM2-135M d'origine (meilleur réglage) | 10/30 | 6/32 | 3/20 | – | – |
| Ancienne Alice (SmolLM2-135M affiné) | 13/30 | 14/32 | 13/20 | 12/20 | 3/10 |
| Qwen2.5-0.5B d'origine | 21/30 | 24/32 | 13/20 | 5/20 | 2/10 |
| **Alice (Qwen2.5-0.5B affiné)** | **25/30** | **25/32** | **20/20** | **19/20** | **9/10** |

Pour un nombre, la réponse n'est comptée juste que si le dernier nombre écrit qui ne
vient pas de la question est le bon. Commande :
`python eval/eval_fr.py --set niveaux2 --verbose`.

Exemple de problème jamais vu : « Dans un parking, il y a 2 voitures et 3 vélos.
Combien de roues y a-t-il ? » → « Une voiture a 4 roues et un vélo a 2 roues. 2 fois 4
font 8, et 3 fois 2 font 6. 8 plus 6 font 14. Il y a 14 roues. »

### Limites

- Les explications ouvertes restent faibles (« Pourquoi le ciel est bleu ? » donne une
  réponse fausse) : Alice est bonne sur ce qu'elle a appris, moins pour improviser.
- Elle se trompe encore parfois de raisonnement (« On enlève une table » est ignoré).
- Le mode `pivot` (passer par l'anglais) n'aide plus : le mode `direct` est meilleur.
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
