# Alice

Un modèle d'IA très léger, utilisable hors ligne sur un simple CPU.

## Modèle

| | |
|---|---|
| Fichier | `models/Alice-SmolLM2-135M-fr-Q4_0.gguf` |
| Base | [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) (Hugging Face), **affiné en français** (voir `train/`) |
| Format | GGUF, quantification Q4_0 (~92 Mo) |
| Paramètres | 135 millions |
| Licence | Apache 2.0 |
| SHA-256 | `280ea4d47271e8c883ec8a6ad3685d606574934a05c32c2c5323a2e4b576bc78` |

L'entraînement n'ajoute aucun paramètre : Alice a exactement la même architecture
et le même poids que le modèle d'origine. Celui-ci n'est plus dans le dépôt ; pour
les comparaisons, il se télécharge sur
[Hugging Face](https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF)
(`SmolLM2-135M-Instruct-Q4_0.gguf`).

## Utilisation

```bash
pip install -r requirements.txt
python chat.py "Léa a 9 bonbons. Elle en mange 4. Combien lui en reste-t-il ?"
# -> 9 moins 4 font 5. Il lui reste 5 bonbons.
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

Le dossier `train/` contient tout ce qu'il faut pour refaire Alice à partir du
modèle d'origine, sur un simple CPU (environ 1 h sur 4 cœurs) :

```bash
pip install -r train/requirements.txt
python train/make_data_fr.py            # génère train/data_fr.jsonl (3 739 exemples)
python train/train_fr.py --base HuggingFaceTB/SmolLM2-135M-Instruct --out build/alice-fr --epochs 2
python train/to_gguf.py build/alice-fr models/Alice-SmolLM2-135M-fr-Q4_0.gguf
```

- **Données** (`make_data_fr.py`) : des exemples écrits à la main (culture générale,
  conversation, identité d'Alice) et produits par des gabarits vérifiés (calculs
  exacts, accords en genre et en nombre) : capitales, calcul, petits problèmes,
  comparaisons, jours et mois, contraires, pluriels, traductions. Environ un quart des
  exemples apprennent aussi les trois étapes du mode pivot (traduire en anglais,
  répondre, réécrire en français).
- **Entraînement** (`train_fr.py`) : affinage complet (2 époques, taux d'apprentissage
  5e-5), la perte ne porte que sur les réponses.
- **Conversion** (`to_gguf.py`) : les poids affinés sont écrits en GGUF avec les
  métadonnées du modèle d'origine (tokenizer, modèle de chat), puis quantifiés en Q4_0
  par llama.cpp. Taille identique.

### Évaluation honnête

Aucune question d'évaluation n'est dans les données d'entraînement : ni les questions,
ni leurs nombres, ni leurs mots. En plus des 30 questions d'origine, une **deuxième
série de 32 questions** (`--set heldout`) n'a servi qu'à la mesure finale.

| Modèle et mode | 30 questions | 32 questions jamais vues | En français | Temps / question |
|---|---|---|---|---|
| Origine, réglages de départ | 1/30 | 2/32 | 18/30 | ~1,5 s |
| Origine, `direct` (consigne + exemples) | 2/30 | 3/32 | 30/30 | ~0,3 s |
| Origine, `pivot` | 9/30 | 6/32 | 29/30 | ~2 s |
| **Alice, `direct` (défaut)** | **11/30** | **12/32** | 30/30 | **~0,3 s** |
| Alice, `pivot` | 10/30 | 4/32 | 30/30 | ~2 s |

Pour un nombre, la réponse n'est comptée juste que si le dernier nombre écrit est le
bon. Commande : `python eval/eval_fr.py --set heldout --verbose`.

Ce qu'Alice a appris : répondre toujours en français et dans une phrase correcte,
poser les calculs (« 9 moins 3 font 6. Il lui reste 6 crayons. »), les problèmes
simples, les comparaisons (« Zoé est la plus jeune. »), se présenter (« Je m'appelle
Alice. ») et répondre aux salutations et aux remerciements.

### Limites

- La culture générale reste faible : le modèle connaît beaucoup de choses en anglais
  (Tokyo, Rome…) mais les retrouve mal en français (« La capitale du Japon est
  Paris. »). Le mode `pivot` aide parfois sur ces questions.
- Les noms propres restent parfois en anglais (« Lisbon », « Cairo »).
- 135 millions de paramètres, c'est très peu : le calcul se trompe encore
  (« 6 fois 3 font 24 ») et le vocabulaire jamais vu est souvent faux.
- Le jeu de questions est petit : les chiffres donnent une tendance, pas une mesure
  précise. Pour beaucoup mieux, il faut un modèle plus grand et multilingue (0,5 à
  1 milliard de paramètres), au-delà de la limite de 100 Mo par fichier de GitHub.

## Amélioration sans entraînement (modèle d'origine)

Avant l'entraînement, trois techniques appliquées au moment de la génération
améliorent déjà le modèle d'origine (lignes « Origine » du tableau) :

1. **Pivot par l'anglais** : la question est traduite en anglais, le modèle y répond
   en anglais, puis la réponse est réécrite en français.
2. **Consignes et exemples (few-shot)** pour chaque étape.
3. **Réglages de génération** : décodage glouton (`temperature=0`) et pénalité de
   répétition (`repeat_penalty=1.15`), ce qui supprime les réponses en boucle.

Le fichier `.gguf` fonctionne aussi avec [llama.cpp](https://github.com/ggml-org/llama.cpp),
[Ollama](https://ollama.com) ou [LM Studio](https://lmstudio.ai).
