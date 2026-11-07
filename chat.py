"""Alice : chat en français (modèle GGUF Q4_0 affiné en français).

Par défaut, Alice utilise models/Alice-1.5B-fr-Q4_0.gguf (1,5 milliard de paramètres,
affiné sur des exemples et des conversations en français, voir train/). Le mode
interactif et le bot Telegram gardent la conversation en mémoire.
Sans entraînement, les techniques ci-dessous améliorent déjà le modèle d'origine.

Le modèle a appris surtout en anglais : il « sait » des choses en anglais mais
raisonne très mal directement en français. Ce script améliore ses réponses
françaises uniquement au moment de l'inférence :

- mode « pivot » : la question est traduite en anglais, le modèle
  y répond en anglais, puis la réponse est réécrite en français en réutilisant
  les mots de la question d'origine ;
- mode « direct » (par défaut) : une seule étape, avec une consigne système
  (et des exemples en français pour le modèle d'origine) ;
- dans les deux modes : décodage glouton (temperature 0) et pénalité de
  répétition, ce qui supprime les réponses qui tournent en boucle.

Usage :
    pip install -r requirements.txt
    python chat.py "Quelle est la capitale de l'Italie ?"
    python chat.py --mode pivot "Bonjour !"
    python chat.py --mode pivot --debug "Combien font 9 plus 6 ?"   # montre les étapes en anglais
    python chat.py                                      # mode interactif
"""
import argparse
import os
from functools import lru_cache
from pathlib import Path

MODELS = Path(__file__).parent / "models"
# Le modèle est rangé en morceaux de moins de 100 Mo (limite de GitHub) :
# models/Alice-1.5B-fr-Q4_0.gguf.part01, .part02… ; ils sont réassemblés au premier lancement.
MODEL_PATH = Path(os.environ.get("ALICE_MODEL", MODELS / "Alice-1.5B-fr-Q4_0.gguf"))
# Longueur de contexte (jetons) : assez pour une longue conversation.
N_CTX = int(os.environ.get("ALICE_CTX", 4096))
# Le modèle entraîné n'a plus besoin d'exemples dans la consigne (et répond mieux sans).
FINE_TUNED = MODEL_PATH.name.lower().startswith("alice")

# Réglages de génération retenus après évaluation (voir eval/eval_fr.py).
GEN = dict(temperature=0, repeat_penalty=1.15)


def assemble(path=MODEL_PATH):
    """Réassemble le modèle à partir de ses morceaux (.part01, .part02…) s'il n'existe pas encore."""
    parts = sorted(path.parent.glob(path.name + ".part*"))
    if path.exists() or not parts:
        return path
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as out:
        for p in parts:
            with open(p, "rb") as f:
                while chunk := f.read(1 << 24):
                    out.write(chunk)
    tmp.replace(path)
    return path


@lru_cache(maxsize=1)
def load_model():
    from llama_cpp import Llama

    return Llama(model_path=str(assemble()), n_ctx=N_CTX, verbose=False)


def _chat(messages, max_tokens=128):
    out = load_model().create_chat_completion(messages=messages, max_tokens=max_tokens, **GEN)
    return out["choices"][0]["message"]["content"].strip()


def _first_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[0].strip() if lines else text.strip()


def _few_shot(system, pairs, question):
    msgs = [{"role": "system", "content": system}]
    for user, assistant in pairs:
        msgs += [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
    return msgs + [{"role": "user", "content": question}]


# ---------------------------------------------------------------- mode direct
SYS_DIRECT = "Tu es Alice, une assistante qui répond toujours en français, de façon courte, exacte et logique."
SHOTS_DIRECT = [
    ("Quelle est la capitale du Portugal ?", "La capitale du Portugal est Lisbonne."),
    ("Combien font 4 plus 5 ?", "4 plus 5 font 9."),
    ("Léa a 6 bonbons. Elle en donne 2. Combien lui en reste-t-il ?", "6 moins 2 font 4. Il lui reste 4 bonbons."),
    ("Quel est le contraire de « chaud » ?", "Le contraire de « chaud » est « froid »."),
    ("Traduis « cat » en français.", "« Cat » se dit « chat » en français."),
]


# Base de connaissances (Wikipédia + faits vérifiés), consultée avant de répondre si elle
# existe (data/alice_kb.sqlite, construite par knowledge/build_kb.py). ALICE_KB=0 la désactive.
USE_KB = os.environ.get("ALICE_KB", "") != "0"
SYS_KB = ("Voici des extraits de ta base de connaissances. S'ils répondent à la question, "
          "appuie-toi dessus et réponds en une ou deux phrases, en français, sans recopier les "
          "numéros. S'ils ne répondent pas à la question, ignore-les et réponds normalement.\n")
LAST_PASSAGES = []  # passages utilisés pour la dernière réponse (affichés par /debug)


def _kb_passages(question, history):
    global LAST_PASSAGES
    LAST_PASSAGES = []
    if not USE_KB:
        return []
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "knowledge"))
        import kb
    except ImportError:
        return []
    LAST_PASSAGES = kb.search(question, history) if kb.available() else []
    return LAST_PASSAGES


def answer_direct(question, shots=None, history=None):
    """history : liste [(question, réponse), …] des échanges précédents de la conversation."""
    if shots is None:
        shots = not FINE_TUNED
    pairs = (SHOTS_DIRECT if shots else []) + list(history or [])
    system = SYS_DIRECT
    passages = _kb_passages(question, history)
    if passages:
        import kb
        system = f"{SYS_DIRECT}\n\n{SYS_KB}{kb.context(passages)}"
    return _chat(_few_shot(system, pairs, question), max_tokens=256)


# ---------------------------------------------------------------- mode pivot
SYS_TRANSLATE = "You are a precise translator. Translate the user's text. Output only the translation."
SHOTS_FR_EN = [
    ("Quelle est la capitale du Portugal ?", "What is the capital of Portugal?"),
    ("Combien font 4 plus 5 ?", "What is 4 plus 5?"),
    ("Léa a 6 bonbons. Elle en donne 2. Combien lui en reste-t-il ?",
     "Lea has 6 candies. She gives away 2. How many does she have left?"),
    ("Quel est le contraire de « chaud » ?", "What is the opposite of 'hot'?"),
    ("Traduis « cat » en français.", "Translate 'cat' into French."),
]

SYS_ANSWER = "You are a helpful assistant. Answer in one short, correct sentence."
SHOTS_ANSWER = [
    ("What is the capital of Portugal?", "The capital of Portugal is Lisbon."),
    ("What is 4 plus 5?", "4 plus 5 is 9."),
    ("Lea has 6 candies. She gives away 2. How many does she have left?", "6 minus 2 is 4. She has 4 candies left."),
    ("What is the opposite of 'hot'?", "The opposite of 'hot' is 'cold'."),
]

SYS_REWRITE = ("Rewrite the English answer as a short answer in correct French. "
               "Reuse the words of the French question. Output only the French answer.")
SHOTS_REWRITE = [
    ("Quelle est la capitale du Portugal ?", "The capital of Portugal is Lisbon.", "La capitale du Portugal est Lisbonne."),
    ("Combien font 4 plus 5 ?", "4 plus 5 is 9.", "4 plus 5 font 9."),
    ("Léa a 6 bonbons. Elle en donne 2. Combien lui en reste-t-il ?",
     "6 minus 2 is 4. She has 4 candies left.", "6 moins 2 font 4. Il lui reste 4 bonbons."),
    ("Quel est le contraire de « chaud » ?", "The opposite of 'hot' is 'cold'.", "Le contraire de « chaud » est « froid »."),
    ("Combien de pattes a un oiseau ?", "A bird has 2 legs.", "Un oiseau a 2 pattes."),
]


def rewrite_input(question, english_answer):
    return f"Question : {question}\nEnglish answer: {english_answer}"


def _rewrite_prompt(question, english_answer):
    pairs = [(rewrite_input(q, en), fr) for q, en, fr in SHOTS_REWRITE]
    return _few_shot(SYS_REWRITE, pairs, rewrite_input(question, english_answer))


def answer_pivot(question, debug=False):
    en_question = _first_line(_chat(_few_shot(SYS_TRANSLATE, SHOTS_FR_EN, question), max_tokens=80))
    en_answer = _chat(_few_shot(SYS_ANSWER, SHOTS_ANSWER, en_question), max_tokens=80)
    fr_answer = _first_line(_chat(_rewrite_prompt(question, en_answer), max_tokens=80))
    if debug:
        print(f"  [EN question] {en_question}\n  [EN réponse ] {en_answer}")
    return fr_answer


def ask(question, mode="direct", debug=False, history=None):
    if mode == "direct":
        return answer_direct(question, history=history)
    return answer_pivot(question, debug=debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat en français avec Alice.")
    parser.add_argument("question", nargs="*", help="question (sinon mode interactif)")
    parser.add_argument("--mode", choices=["direct", "pivot"], default="direct")
    parser.add_argument("--debug", action="store_true", help="affiche les étapes intermédiaires en anglais")
    args = parser.parse_args()

    if args.question:
        print(ask(" ".join(args.question), args.mode, args.debug))
    else:
        print("Discute avec Alice (Ctrl+C pour quitter, /nouveau pour oublier la conversation).")
        history = []
        while True:
            try:
                q = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q == "/nouveau":
                history = []
            elif q:
                a = ask(q, args.mode, args.debug, history=history)
                print(a)
                history = (history + [(q, a)])[-12:]
