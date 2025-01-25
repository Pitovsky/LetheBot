import logging
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

from tg_client import TgClient

session = os.environ.get('TG_SESSION_STR')
api_id = os.environ.get('TG_API_ID')
api_hash = os.environ.get('TG_API_HASH')
tg_client = TgClient(session, api_id, api_hash)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )

async def chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(await tg_client._read_saved_message())


def get_bot(token: str):
    application = (
        ApplicationBuilder()
        .token(token)
        # .post_shutdown(signal_handler)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chats", chats))

    return application