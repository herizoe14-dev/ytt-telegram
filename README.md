# Alice

Un modèle d'IA très léger, utilisable hors ligne sur un simple CPU.

## Modèle

| | |
|---|---|
| Nom | [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) (Hugging Face) |
| Format | GGUF, quantification Q4_0 ([source](https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF)) |
| Fichier | `models/SmolLM2-135M-Instruct-Q4_0.gguf` (~88 Mo) |
| Paramètres | 135 millions |
| Licence | Apache 2.0 |
| SHA-256 | `bcc3af2849ad6095af57e9b5cd43775256efdc66e306acb529172f92d0c04b03` |

C'est un petit modèle de conversation, surtout bon en anglais. Il répond vite,
mais ses réponses restent simples et peuvent contenir des erreurs.

## Utilisation

```bash
pip install -r requirements.txt
python chat.py "Quelle est la capitale de l'Italie ?"   # -> La capitale de l'Italie est Rome.
python chat.py --mode direct "Bonjour !"                # une seule étape, plus rapide
python chat.py --debug "Combien font 9 plus 6 ?"        # montre les étapes en anglais
python chat.py                                          # mode interactif
```

## Amélioration du français sans entraînement

Les poids du modèle ne sont pas modifiés. Tout se joue au moment de la génération :

1. **Pivot par l'anglais** (mode par défaut) : le modèle connaît bien plus de choses
   en anglais qu'en français. La question est donc traduite en anglais, le modèle
   y répond en anglais, puis la réponse est réécrite en français en réutilisant les
   mots de la question d'origine.
2. **Consignes et exemples (few-shot)** : chaque étape reçoit une consigne système et
   quelques exemples de réponses courtes.
3. **Réglages de génération** : décodage glouton (`temperature=0`) et pénalité de
   répétition (`repeat_penalty=1.15`), ce qui supprime les réponses en boucle.

### Résultats mesurés

Sur 30 questions simples en français (`eval/questions_fr.py` : culture générale,
calcul, logique, vocabulaire), avec `python eval/eval_fr.py` :

| Mode | Réponses correctes | Réponses en français | Réponses en boucle | Temps / question |
|---|---|---|---|---|
| Réglages d'origine | 1/30 | 18/30 | 4 | ~1,5 s |
| `direct` | 3/30 | 30/30 | 0 | ~0,3 s |
| `pivot` (défaut) | **10/30** | 29/30 | 0 | ~2 s |

### Limites

- Avec 135 millions de paramètres et un apprentissage surtout en anglais, le modèle
  reste très faible en raisonnement : les problèmes en plusieurs étapes
  (« Paul a 3 billes, il en gagne 4… ») échouent presque toujours.
- La traduction vers l'anglais se trompe parfois de mots (« Espagne » devient
  « France », « araignée » n'est pas comprise), et l'erreur se propage.
- Le contrôle automatique est indulgent et le jeu de questions est petit :
  les chiffres donnent une tendance, pas une mesure précise.
- Pour un vrai raisonnement en français, il faut un modèle plus grand et multilingue
  (par exemple de 0,5 à 1 milliard de paramètres), au-delà de la limite de 100 Mo
  par fichier de GitHub sans Git LFS.

Le fichier `.gguf` fonctionne aussi avec [llama.cpp](https://github.com/ggml-org/llama.cpp),
[Ollama](https://ollama.com) ou [LM Studio](https://lmstudio.ai).
