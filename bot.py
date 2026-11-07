"""Bot Telegram pour tester Alice (modèle entraîné en français, en local, sans GPU).

1. Crée un bot avec @BotFather sur Telegram et copie le jeton (token).
2. Lance :
       pip install -r requirements.txt
       export TELEGRAM_BOT_TOKEN="ton_jeton"        # Windows : set TELEGRAM_BOT_TOKEN=ton_jeton
       python bot.py
3. Écris à ton bot sur Telegram.

Réglages persistants (facultatif) : définis aussi SUPABASE_URL,
SUPABASE_PUBLISHABLE_KEY et SUPABASE_BOT_SECRET pour que /mode et /debug
soient conservés dans Supabase (voir settings.py et .env.example).
Sans elles, les réglages restent en mémoire.

Commandes :
    /start          présentation
    /nouveau        oublie la conversation et recommence
    /mode direct    réponses rapides (par défaut)
    /mode pivot     passe par l'anglais (~2 s), parfois meilleur en culture générale
    /debug          affiche/masque les sources consultées (ou les étapes en mode pivot)
"""
import asyncio
import contextlib
import io
import logging
import os

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import chat
from settings import SettingsStore

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("alice")

# Le modèle n'est pas fait pour être appelé par plusieurs threads à la fois.
_model_lock = asyncio.Lock()
MAX_QUESTION_LEN = 500
# Mémoire de la conversation (en mémoire vive, par discussion) : derniers échanges gardés.
MAX_TURNS = 12
MAX_HISTORY_CHARS = 6000
HISTORY: dict[int, list[tuple[str, str]]] = {}
store: SettingsStore = SettingsStore()  # recréé au démarrage dans post_init


def _history(chat_id):
    """Derniers échanges, dans la limite de MAX_TURNS et de MAX_HISTORY_CHARS."""
    h = HISTORY.get(chat_id, [])[-MAX_TURNS:]
    while h and sum(len(q) + len(a) for q, a in h) > MAX_HISTORY_CHARS:
        h = h[1:]
    return h


def _generate(question, mode, debug, history):
    """Appelle le modèle ; renvoie (réponse, étapes de debug)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        answer = chat.ask(question, mode=mode, debug=debug and mode == "pivot",
                          history=history if mode == "direct" else None)
    steps = "\n".join(l.strip() for l in buf.getvalue().splitlines() if l.strip())
    if mode == "direct" and chat.LAST_PASSAGES:  # sources consultées dans la base de connaissances
        steps = "Sources : " + " ; ".join(f"{t} ({s})" for t, _, s in chat.LAST_PASSAGES)
    return answer or "…", steps


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bonjour, je suis Alice, un modèle d'IA (1,5 milliard de paramètres) "
        "entraîné en français, qui tourne en local.\n\n"
        "Pose-moi une question simple, par exemple :\n"
        "« Léa a 9 bonbons. Elle en mange 4. Combien lui en reste-t-il ? »\n\n"
        "Je me souviens de notre conversation : dis-moi ton prénom, je le retiendrai.\n"
        "Pour les questions de culture, je consulte ma base de connaissances (Wikipédia).\n\n"
        "/nouveau : recommencer une conversation (j'oublie tout)\n"
        "/mode direct : réponses rapides (par défaut)\n"
        "/mode pivot : je réfléchis en anglais, parfois mieux en culture générale\n"
        "/debug : voir les sources que j'ai consultées\n\n"
        "Je fais souvent des erreurs : je suis un modèle expérimental."
    )


async def new_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    HISTORY.pop(update.effective_chat.id, None)
    await update.message.reply_text("C'est noté, on recommence à zéro. De quoi veux-tu parler ?")


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mode = (context.args[0].lower() if context.args else "")
    if mode not in ("pivot", "direct"):
        current = (await store.get(chat_id))["mode"]
        await update.message.reply_text(f"Mode actuel : {current}.\nUtilise /mode pivot ou /mode direct.")
        return
    await store.update(chat_id, mode=mode)
    await update.message.reply_text(f"Mode « {mode} » activé.")


async def toggle_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    debug = not (await store.get(chat_id))["debug"]
    await store.update(chat_id, debug=debug)
    state = "activé" if debug else "désactivé"
    await update.message.reply_text(f"Mode debug {state}.")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return
    if len(question) > MAX_QUESTION_LEN:
        await update.message.reply_text(f"Ta question est trop longue (maximum {MAX_QUESTION_LEN} caractères).")
        return

    chat_id = update.effective_chat.id
    settings = await store.get(chat_id)
    mode = settings["mode"]
    debug = settings["debug"]
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    try:
        async with _model_lock:
            answer, steps = await asyncio.to_thread(_generate, question, mode, debug, _history(chat_id))
    except Exception:
        log.exception("Erreur pendant la génération")
        await update.message.reply_text("Désolée, une erreur est survenue. Réessaie.")
        return

    log.info("[%s] %r -> %r%s", mode, question, answer,
             f"  [sources : {', '.join(t for t, _, _ in chat.LAST_PASSAGES)}]" if chat.LAST_PASSAGES else "")
    HISTORY[chat_id] = (HISTORY.get(chat_id, []) + [(question, answer)])[-MAX_TURNS:]
    if debug and steps:
        answer = f"{answer}\n\n— {'sources' if mode == 'direct' else 'étapes'} —\n{steps}"
    await update.message.reply_text(answer)


async def on_error(update, context):
    """Coupures réseau passagères : une ligne dans le journal au lieu d'une longue trace."""
    from telegram.error import NetworkError
    if isinstance(context.error, NetworkError):
        log.warning("Réseau Telegram : %s (nouvelle tentative automatique)", context.error)
    else:
        log.error("Erreur inattendue", exc_info=context.error)


async def post_init(app):
    global store
    store = SettingsStore()
    if store.persistent:
        await store.check()
        log.info("Réglages enregistrés dans Supabase.")
    else:
        log.warning("Variables SUPABASE_* absentes : réglages en mémoire seulement.")


async def post_shutdown(app):
    await store.close()


def load_dotenv(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Charge un fichier .env simple (CLE=valeur) sans écraser les variables déjà définies."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if v:
                    os.environ.setdefault(k.strip(), v)


def main():
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Définis la variable d'environnement TELEGRAM_BOT_TOKEN (jeton donné par @BotFather).")

    log.info("Chargement du modèle…")
    chat.load_model()

    app = Application.builder().token(token).post_init(post_init).post_shutdown(post_shutdown).build()
    app.add_handler(CommandHandler(["start", "aide", "help"], start))
    app.add_handler(CommandHandler(["nouveau", "reset"], new_conversation))
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_error_handler(on_error)
    app.add_handler(CommandHandler("debug", toggle_debug))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    log.info("Alice est en ligne. Ctrl+C pour arrêter.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
