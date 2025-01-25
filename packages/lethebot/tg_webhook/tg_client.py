import json
import logging

from telethon import TelegramClient, functions, errors
from telethon.types import User, Channel, Chat
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.sessions import StringSession
from telethon.types import User


logger = logging.getLogger(__name__)


class TgClient():
    def __init__(self, session, api_id, api_hash):
        self._session = session
        self._api_id = api_id
        self._api_hash = api_hash
        self._owner = None
        # TODO GET FROM ENV
        self._message_id = 1399

    async def get_owner(self) -> User:
        if self._owner is None:
            async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
                self._owner = await client.get_me()
        return self._owner

    async def get_chats(self) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            return await client.get_dialogs()

    async def get_chat_description(self, chat_id) -> str:
        try:
            async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
                entity = await client.get_entity(chat_id)
                print(entity)
                if isinstance(entity, User):
                    if entity.username:
                        return f'{entity.first_name} {entity.last_name} https://t.me/{entity.username}'
                    return f'[{entity.first_name} {entity.last_name}](https://web.telegram.org/a/#{chat_id})'
                if isinstance(entity, Channel):
                    if entity.username:
                        return f'{entity.title} https://t.me/{entity.username}'
                    try:
                        invite = await client(functions.messages.ExportChatInviteRequest(entity))
                        return f'{entity.title} [invite link]({invite.link})'
                    except errors.rpcerrorlist.ChatAdminRequiredError as e:
                        # not enough rights to get invite link
                        user_iter = client.iter_participants(entity, filter=ChannelParticipantsAdmins)
                        async for user in user_iter:
                            # any one will do
                            name = f'{user.first_name} {user.last_name}'
                            if user.username:
                                return f'{entity.title} admined by {name} https://t.me/{user.username}'
                            return f'{entity.title} admined by [{name}](https://web.telegram.org/a/#{user.id})'
                if isinstance(entity, Chat):
                    try:
                        invite = await client(functions.messages.ExportChatInviteRequest(entity))
                        return f'{entity.title} [invite link]({invite.link})'
                    except errors.rpcerrorlist.ChatAdminRequiredError as e:
                        # not enough rights to get invite link
                        user_iter = client.iter_participants(entity, filter=ChannelParticipantsAdmins)
                        async for user in user_iter:
                            # any one will do
                            name = f'{user.first_name} {user.last_name}'
                            if user.username:
                                return f'{entity.title} admined by {name} https://t.me/{user.username}'
                            return f'{entity.title} admined by [{name}](https://web.telegram.org/a/#{user.id})'
                return None
        except BaseException as e:
            logger.error(f'get_chat_description for {chat_id}', exc_info=e)
            return None

    async def _read_saved_message(self) -> dict:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            message = await client.get_messages('me', ids=self._message_id)
            return json.loads(message.text)

    async def _write_saved_message(self, data: dict) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.edit_message('me', self._message_id, json.dumps(data))

    async def _clear_saved_message(self) -> None:
        data = {
            'chats': {},
            'trusted': {},
        }
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.edit_message('me', self._message_id, json.dumps(data))
