"""Bot Telegram pour tester Alice (SmolLM2-135M, en local, sans GPU).

1. Crée un bot avec @BotFather sur Telegram et copie le jeton (token).
2. Lance :
       pip install -r requirements.txt
       export TELEGRAM_BOT_TOKEN="ton_jeton"        # Windows : set TELEGRAM_BOT_TOKEN=ton_jeton
       python bot.py
3. Écris à ton bot sur Telegram.

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

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("alice")

# Le modèle n'est pas fait pour être appelé par plusieurs threads à la fois.
_model_lock = asyncio.Lock()
MAX_QUESTION_LEN = 500


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
    mode = (context.args[0].lower() if context.args else "")
    if mode not in ("pivot", "direct"):
        current = context.chat_data.get("mode", "pivot")
        await update.message.reply_text(f"Mode actuel : {current}.\nUtilise /mode pivot ou /mode direct.")
        return
    context.chat_data["mode"] = mode
    await update.message.reply_text(f"Mode « {mode} » activé.")


async def toggle_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["debug"] = not context.chat_data.get("debug", False)
    state = "activé" if context.chat_data["debug"] else "désactivé"
    await update.message.reply_text(f"Mode debug {state}.")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return
    if len(question) > MAX_QUESTION_LEN:
        await update.message.reply_text(f"Ta question est trop longue (maximum {MAX_QUESTION_LEN} caractères).")
        return

    mode = context.chat_data.get("mode", "pivot")
    debug = context.chat_data.get("debug", False) and mode == "pivot"
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


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Définis la variable d'environnement TELEGRAM_BOT_TOKEN (jeton donné par @BotFather).")

    log.info("Chargement du modèle…")
    chat.load_model()

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "aide", "help"], start))
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("debug", toggle_debug))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    log.info("Alice est en ligne. Ctrl+C pour arrêter.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
