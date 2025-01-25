import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )

def get_bot(token: str):
    application = (
        ApplicationBuilder()
        .token(token)
        # .post_shutdown(signal_handler)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))

    return application