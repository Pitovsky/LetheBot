import logging
import json
import os
from typing import Optional

from telegram import (
    constants,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    Bot,
    CallbackQuery
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from tg_client import TgClient


class LetheBot:

    bot: Optional[Bot]

    def __init__(self):
        self.session = os.environ.get('TG_SESSION_STR')
        self.api_id = os.environ.get('TG_API_ID')
        self.api_hash = os.environ.get('TG_API_HASH')
        self.tg_client = TgClient(self.session, self.api_id, self.api_hash)
        self.invite_code = os.environ.get('INVITE_CODE')
        self.bot = None

    async def start(self, update: Update) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        owner = await self.tg_client.get_owner()
        if user.id == owner.id:
            await update.message.reply_html(
                rf"Hi {user.mention_html()}!\n\nSend this message to trusted contacts. https://t.me/{self.bot.username}?start={self.invite_code}",
            )
        else:
            code = update.message.text[len('/start'):].strip()
            if self.invite_code == code:
                await update.message.reply_html(
                    rf"Hi {user.mention_html()}! Someone trusted you with their data",
                )
                await self.add_to_trusted(user.id)
                await self.bot.send_message(
                    chat_id=owner.id,
                    text=f'added {user.mention_html()} as trusted user',
                )
            else:
                await update.message.reply_html(
                    rf"Hi {user.mention_html()}! I like cats",
                )

    async def add_to_trusted(self, user_id: int):
        data = await self.tg_client._read_saved_message()
        data['trusted'][user_id] = {
            'id': user_id
        }
        await self.tg_client._write_saved_message(data)

    def generate_progress_bar(self, done, total, length=50, bar_char='█', empty_char=' '):
        progress = int((done / total) * length)
        bar = bar_char * progress
        empty = empty_char * (length - progress)
        
        return f"Progress [{bar}{empty}] ({done}/{total})"

    async def handle_sos(self, update: Update) -> None:
        data = await self.tg_client._read_saved_message()
        chat_ids = [chat['id'] for chat in data["chats"].values() if chat["is_sensitive"]]
        owner = await self.tg_client.get_owner()
        for user in data['trusted'].values():
            if 'voted' in user:
                del user['voted']
            await self.bot.send_message(chat_id=user['id'],
                                        text=f'Your friend {owner.username} just pressed the red button to hide some chats.\n'
                                             f'Please reach them out after some time, and press the button below '
                                             f'when you\'re ABSOLUTELY sure they\'re safe.')
            db_msg = await self.bot.send_message(chat_id=user['id'],
                                                 text='🦥')
            user['db_msg_id'] = db_msg.id

        await self._update_trustees_data(data)

        await self.tg_client._write_placeholder_saved_message()
        await self.tg_client.leave_chats(chat_ids)
        await self.tg_client.leave_chat_silently(self.bot.username) # commit suicide

    async def _update_trustees_data(self, data: dict):
        keyboard = [
            [
                InlineKeyboardButton("I know it's safe now", callback_data=json.dumps(
                    {'action': 'safe'}
                ))
            ]
        ]
        data_serialised = self.tg_client._serialise_data(data)
        for user in data['trusted'].values():
            if 'voted' not in user:
                await self.bot.edit_message_text(data_serialised,
                                                 chat_id=user['id'],
                                                 message_id=user['db_msg_id'],
                                                 reply_markup=InlineKeyboardMarkup(keyboard))

    async def safe_vote(self, update: Update, query: CallbackQuery, callback_data: dict):
        data = self.tg_client._deserialise_data(query.message.text)
        if str(update.effective_chat.id) in data['trusted']:
            num_votes = 0
            for user in data['trusted'].values():
                if 'voted' in user and user['voted']:
                    num_votes += 1
            trustee = data['trusted'][str(update.effective_chat.id)]
            if 'voted' not in trustee:
                trustee['voted'] = True
                num_votes += 1
                if num_votes < 2:
                    await query.edit_message_text('You voted they\'re safe, now waiting for other trusted people to vote')
                    await self._update_trustees_data(data)
                else:
                    owner = await self.tg_client.get_owner()
                    await self.tg_client._write_saved_message(data)
                    await self.bot.send_message(owner.id, 'Your trusted people said you\'re safe, congrats on getting back!')
                    for user in data['trusted'].values():
                        await self.bot.edit_message_text('The data was restored after ensuring their safety',
                                                         chat_id=user['id'], message_id=user['db_msg_id'],)


    async def get_chat(self, update: Update) -> None:
        data = await self.tg_client._read_saved_message()
        chats = await self.tg_client.get_chats()
        total_chats = len(chats)
        marked_chats = len(data['chats'])
        selected_chat = None
        for chat in chats:
            if str(chat.id) not in data['chats']:
                selected_chat = chat
                break
        keyboard = [
            [
                InlineKeyboardButton("🚨Yes", callback_data=json.dumps(
                    {'action': 'yes', 'chat_id': selected_chat.id}
                )),
                InlineKeyboardButton("😺No", callback_data=json.dumps(
                    {'action': 'no', 'chat_id': selected_chat.id}
                ))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Is this a sensitive chat?\n💬{selected_chat.title or selected_chat.id}\n\n{self.generate_progress_bar(marked_chats, total_chats)}',
            reply_markup=reply_markup
        )


    async def clear_saved_message(self, update: Update):
        await self.tg_client._clear_saved_message()


    async def button_yesno(self, update: Update, query: CallbackQuery, callback_data: dict):
        data = await self.tg_client._read_saved_message()
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
        await self.tg_client._write_saved_message(data)
        await self.get_chat(update)


    async def mark_chat(self, update: Update) -> None:
        tokens = update.message.text.strip().split(maxsplit=2)
        assert len(tokens) == 2
        chat_id = tokens[1]

        data = await self.tg_client._read_saved_message()
        if chat_id in data.get('chats', {}):
            del data.get('chats')[chat_id]
        else:
            data.get('chats')[chat_id] = {
                'id': int(chat_id),
                'is_sensitive': True
            }
        await self.tg_client._write_saved_message(data)


    async def get_restore_info(self, update: Update) -> None:
        data = await self.tg_client._read_saved_message()
        sensitive_chats = [chat for chat in data["chats"].values() if chat["is_sensitive"]]
        info = [f'You have {len(sensitive_chats)} chats to be restored']
        for chat in sensitive_chats:
            chat_description = await self.tg_client.get_chat_description(chat['id'])
            # print(chat_description)
            if chat_description:
                info.append(chat_description)
        # print(info)
        await update.message.reply_text('\n\n'.join(info), parse_mode=constants.ParseMode.MARKDOWN)


    async def _reply_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if self.bot is None:
            self.bot = context.bot

        if update.callback_query:
            query = update.callback_query
            await query.answer()
            callback_data = json.loads(query.data)
            action = callback_data['action']
            if action == 'yes' or action == 'no':
                return await self.button_yesno(update, query, callback_data)
            elif action == 'safe':
                return await self.safe_vote(update, query, callback_data)
        elif update.message.text.startswith('/start'):
            return await self.start(update)
        elif update.message.text == '/get_chat':
            return await self.get_chat(update)
        elif update.message.text == '/clear':
            return await self.clear_saved_message(update)
        elif update.message.text.startswith('/mark'):
            return await self.mark_chat(update)
        elif update.message.text == '/get_restore_info':
            return await self.get_restore_info(update)
        elif update.message.text == '/sos':
            return await self.handle_sos(update)
        print(f'unhandled update {update}')


    def get_bot(self, token: str):
        application = (
            ApplicationBuilder()
            .token(token)
            # .post_shutdown(signal_handler)
            .concurrent_updates(True)
            .build()
        )
        application.add_handler(MessageHandler(filters.ALL, self._reply_handler))

        application.add_handler(CallbackQueryHandler(self._reply_handler))

        return application


    async def process_single_webhook(self, token: str, request_json):
        self.bot = Bot(token=token)
        await self.bot.initialize()
        if 'triggerType' in request_json:
            pass # TODO scheduled batches go here
        else:
            await self._reply_handler(Update.de_json(data=request_json, bot=self.bot), context=None)
