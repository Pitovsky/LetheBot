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
    CallbackQuery,
    helpers,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telethon.types import Chat

from tg_client import TgClient


logger = logging.getLogger(__name__)


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
            await self._send_message(
                update.effective_chat.id,
                f"Hi {user.mention_markdown()}! I am Lethe (Ле́та)!\nI can hide you from sensitive chats.",
                update_alarm_message=False,
            )
            await self._send_message(
                update.effective_chat.id,
                f"Please send the following message to 2 people you trust.\nYou will be able to recover your chats if they tell me you are safe.",
                update_alarm_message=False,
            )
            await self._send_message(
                update.effective_chat.id,
                helpers.escape_markdown(f"Dear friend, please press here\nhttps://t.me/{self.bot.username}?start={self.invite_code}."),
                update_alarm_message=False,
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("😎 Yes", callback_data=json.dumps(
                        {'action': 'begin_review'}
                    )),
                ]
            ])
            await self._send_message(
                update.effective_chat.id,
                f"Are you ready to review your chats?",
                reply_markup=keyboard,
            )
        else:
            code = update.message.text[len('/start'):].strip()
            if self.invite_code == code:
                await self._send_message(
                    update.effective_chat.id,
                    f"Hi {user.mention_markdown()}!\n\nSomeone trusted you with their data",
                    update_alarm_message=False,
                )
                await self.add_to_trusted(user.id)
                await self._send_message(
                    owner.id,
                    f"added {user.mention_markdown()} as trusted user",
                    update_alarm_message=False,
                )
            else:
                await self._send_message(
                    update.effective_chat.id,
                    f"Hi {user.mention_markdown()}! I like cats",
                    update_alarm_message=False,
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
        data["chats_data"] = {}
        for chat in data["chats"].values():
            data["chats_data"][str(chat['id'])] = await self.tg_client.get_chat_data(chat['id'], chat["is_sensitive"])
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
            if not user.get('voted'):
                await self.bot.edit_message_text(data_serialised,
                                                 chat_id=user['id'],
                                                 message_id=user['db_msg_id'],
                                                 reply_markup=InlineKeyboardMarkup(keyboard))

    async def safe_vote(self, update: Update, query: CallbackQuery, callback_data: dict):
        data = self.tg_client._deserialise_data(query.message.text)
        if str(update.effective_chat.id) in data['trusted']:
            num_votes = 0
            for user in data['trusted'].values():
                if user.get('voted'):
                    num_votes += 1
            trustee = data['trusted'][str(update.effective_chat.id)]
            if not trustee.get('voted'):
                trustee['voted'] = True
                num_votes += 1
                if num_votes < 2:
                    await query.edit_message_text('You voted they\'re safe, now waiting for other trusted people to vote')
                    await self._update_trustees_data(data)
                else:
                    owner = await self.tg_client.get_owner()
                    await self.bot.send_message(owner.id, 'Your trusted people said you\'re safe, congrats on getting back!')
                    info = []
                    print(data["chats_data"])
                    for chat in data["chats_data"].values():
                        chat_description = self.tg_client.render_chat(chat)
                        print('chat description')
                        print(chat_description)
                        if chat_description:
                            info.append(chat_description)
                    print('info')
                    print(info)
                    del data["chats_data"]
                    await self.tg_client._write_saved_message(data)
                    await self.bot.send_message(owner.id, '\n\n'.join(info), parse_mode=constants.ParseMode.MARKDOWN)
                    await self.bot.send_message(owner.id, 'Feel free to return to any chats you want.\n\nI will continue to keep you safe.')
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("😎 Yes", callback_data=json.dumps(
                                {'action': 'begin_review'}
                            )),
                        ]
                    ])
                    await self._send_message(
                        owner.id,
                        f"Are you ready to review more chats?",
                        reply_markup=keyboard,
                    )
                    for user in data['trusted'].values():
                        await self.bot.edit_message_text('The data was restored after ensuring their safety',
                                                         chat_id=user['id'], message_id=user['db_msg_id'],)


    async def get_chat(self, _: Optional[Update]) -> None:
        data = await self.tg_client._read_saved_message()
        chats = await self.tg_client.get_chats()
        total_chats = len(chats)
        marked_chats = len(data['chats'])
        selected_chat = None
        owner = await self.tg_client.get_owner()
        for chat in chats:
            if str(chat.id) not in data['chats'] and chat.id not in [
                self.bot.id,  # don't ask about itself
                owner.id,  # don't ask about Saved messages
                93372553,  # don't ask about Botfather
                777000,  # don't ask about Telegram
            ]:
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
        message_parts = [
            f'Is this a sensitive chat?\n{helpers.escape_markdown(selected_chat.title or selected_chat.id)}',
            f'{self.generate_progress_bar(marked_chats, total_chats)}'
        ]
        if isinstance(selected_chat.entity, Chat) and selected_chat.entity.admin_rights is not None:
            message_parts.append(f'*Caution, you are the admin of that chat*')
        await self._send_message(
            owner.id,
            '\n\n'.join(message_parts),
            reply_markup=reply_markup,
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
            try:
                chat_description = await self.tg_client.get_chat_data(chat['id'], True)
                # print(chat_description)
                if chat_description:
                    info.append(chat_description)
            except BaseException as e:
                logger.warning(f'failed to generate chat description for {str(chat)}', exc_info=e)
                pass
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
            elif action == 'begin_review':
                return await self.get_chat(update)
            elif action == 'button_sos':
                return await self.handle_sos(update)
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


    async def _send_message(self, chat_id:int, text:str, reply_markup:InlineKeyboardMarkup=None, update_alarm_message=True):
        data = await self.tg_client._read_saved_message()
        if 'alarm_message_id' in data and update_alarm_message:
            try:
                await self.bot.delete_message(chat_id=chat_id, message_id=data['alarm_message_id'])
            except BaseException as e:
                pass
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        if update_alarm_message:
            keyboard = [
                [
                    InlineKeyboardButton("🚨SOS🚨", callback_data=json.dumps({'action': 'button_sos'}))
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            alarm_msg = await self.bot.send_message(
                chat_id=chat_id,
                text=f'🚨🚨🚨🚨🚨\n\n\nВ ЭКСТРЕННОЙ СИТУАЦИИ\nНАЖМИТЕ SOS\n\n\n🚨🚨🚨🚨🚨',
                reply_markup=reply_markup,
                parse_mode=constants.ParseMode.MARKDOWN,
            )
            data['alarm_message_id'] = alarm_msg.id
            await self.tg_client._write_saved_message(data)

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
        if request_json.get('triggerType') == 'daily_reminder':
            await self.get_chat(None)
        else:
            await self._reply_handler(Update.de_json(data=request_json, bot=self.bot), context=None)
