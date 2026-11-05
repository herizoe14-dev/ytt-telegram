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
python chat.py "What is the capital of France?"
python chat.py          # mode interactif
```

Le fichier `.gguf` fonctionne aussi avec [llama.cpp](https://github.com/ggml-org/llama.cpp),
[Ollama](https://ollama.com) ou [LM Studio](https://lmstudio.ai).
