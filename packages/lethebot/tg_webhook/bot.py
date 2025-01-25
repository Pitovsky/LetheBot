import logging
import json
import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
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

async def get_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await tg_client._read_saved_message()
    chats = await tg_client.get_chats()
    selected_chat = None
    for chat in chats:
        if str(chat.id) not in data['chats']:
            selected_chat = chat
            break
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data=json.dumps(
                {'action': 'yes', 'chat_id': selected_chat.id}
            )),
            InlineKeyboardButton("No", callback_data=json.dumps(
                {'action': 'no', 'chat_id': selected_chat.id}
            ))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Is this a sensitive chat?\n{selected_chat.title}',
        reply_markup=reply_markup
    )


async def button_yesno(update, context):
    query = update.callback_query
    await query.answer()

    callback_data = json.loads(query.data)
    data = await tg_client._read_saved_message()
    if callback_data['action'] == 'yes':
        data.get('chats')[callback_data['chat_id']] = {
            'id': callback_data['chat_id'],
            'is_sensitive': True
        }
        await query.edit_message_text(query.message.text + "\n\nYes")
    elif callback_data['action'] == 'no':
        data.get('chats')[callback_data['chat_id']] = {
            'id': callback_data['chat_id'],
            'is_sensitive': False
        }
        await query.edit_message_text(query.message.text + "\n\nNo")
    await tg_client._write_saved_message(data)
    await get_chat(update, context)


async def mark_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tokens = update.message.text.strip().split(maxsplit=2)
    assert len(tokens) == 2
    chat_id = tokens[1]

    data = await tg_client._read_saved_message()
    if chat_id in data.get('chats', {}):
        del data.get('chats')[chat_id]
    else:
        data.get('chats')[chat_id] = {
            'id': chat_id
        }
    await tg_client._write_saved_message(data)


def get_bot(token: str):
    application = (
        ApplicationBuilder()
        .token(token)
        # .post_shutdown(signal_handler)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_chat", get_chat))
    application.add_handler(CommandHandler("mark", mark_chat))
    application.add_handler(CallbackQueryHandler(button_yesno))

    return application