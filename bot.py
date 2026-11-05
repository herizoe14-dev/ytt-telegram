"""Bot Telegram pour tester Alice (SmolLM2-135M, en local, sans GPU).

1. Crée un bot avec @BotFather sur Telegram et copie le jeton (token).
2. Lance :
       pip install -r requirements.txt
       export TELEGRAM_BOT_TOKEN="ton_jeton"        # Windows : set TELEGRAM_BOT_TOKEN=ton_jeton
       python bot.py
3. Écris à ton bot sur Telegram.

Réglages persistants (facultatif) : définis aussi SUPABASE_URL et
SUPABASE_SECRET_KEY pour que /mode et /debug soient conservés dans Supabase
(voir settings.py). Sans elles, les réglages restent en mémoire.

Commandes :
    /start          présentation
    /mode pivot     réponses plus exactes (~2 s, par défaut)
    /mode direct    réponses plus rapides, moins exactes
    /debug          affiche/masque les étapes intermédiaires en anglais
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
store: SettingsStore = SettingsStore()  # recréé au démarrage dans post_init


def _generate(question, mode, debug):
    """Appelle le modèle ; renvoie (réponse, étapes de debug)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        answer = chat.ask(question, mode=mode, debug=debug)
    steps = "\n".join(l.strip() for l in buf.getvalue().splitlines() if l.strip())
    return answer or "…", steps


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bonjour, je suis Alice, un tout petit modèle d'IA (135 millions de paramètres) "
        "qui tourne en local.\n\n"
        "Pose-moi une question simple en français, par exemple :\n"
        "« Quelle est la capitale de l'Italie ? »\n\n"
        "/mode pivot : réponses plus exactes (par défaut)\n"
        "/mode direct : réponses plus rapides\n"
        "/debug : voir mes étapes de réflexion en anglais\n\n"
        "Je fais souvent des erreurs : je suis un modèle expérimental."
    )


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

    settings = await store.get(update.effective_chat.id)
    mode = settings["mode"]
    debug = settings["debug"] and mode == "pivot"
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    try:
        async with _model_lock:
            answer, steps = await asyncio.to_thread(_generate, question, mode, debug)
    except Exception:
        log.exception("Erreur pendant la génération")
        await update.message.reply_text("Désolée, une erreur est survenue. Réessaie.")
        return

    log.info("[%s] %r -> %r", mode, question, answer)
    if debug and steps:
        answer = f"{answer}\n\n— étapes —\n{steps}"
    await update.message.reply_text(answer)


async def post_init(app):
    global store
    store = SettingsStore()
    if store.persistent:
        await store.check()
        log.info("Réglages enregistrés dans Supabase.")
    else:
        log.warning("SUPABASE_URL / SUPABASE_SECRET_KEY absents : réglages en mémoire seulement.")


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
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("debug", toggle_debug))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    log.info("Alice est en ligne. Ctrl+C pour arrêter.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
