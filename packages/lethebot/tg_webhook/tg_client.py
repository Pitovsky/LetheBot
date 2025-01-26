import json
import logging
import os
import random
import base64
import zlib
import io
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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
        self._message_id = int(os.getenv('DB_PATH'))
        self._db_enc = AESGCM(base64.urlsafe_b64decode(os.getenv('DB_PASSWORD').encode()))

    async def get_owner(self) -> User:
        if self._owner is None:
            async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
                self._owner = await client.get_me()
        return self._owner

    async def get_chats(self) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            return await client.get_dialogs()

    async def leave_chat_silently(self, chat_id: str):
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.delete_dialog(chat_id)

    async def leave_chats(self, chat_ids: list[int]) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            for chat_id in chat_ids:
                entity = await client.get_entity(chat_id)
                print('entity')
                if isinstance(entity, User) or isinstance(entity, Chat):
                    await client.send_message(entity,
                                              'I am leaving this chat automatically due to an emergency.\n'
                                              'Hope to see you all again later, but now I need to drink from Lethe.')
                await client.delete_dialog(entity)

    async def get_chat_data(self, chat_id: int, is_sensitive: bool) -> dict:
        try:
            async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
                entity = await client.get_entity(chat_id)
                if isinstance(entity, User):
                    public_link = entity.username or f"[{entity.first_name} {entity.last_name}](https://web.telegram.org/a/#{chat_id})"
                    return {
                        "id": chat_id,
                        "title": "{entity.first_name} {entity.last_name}",
                        "public_link": public_link,
                        'is_sensitive': is_sensitive,
                    }
                if isinstance(entity, Channel):
                    if entity.username:
                        return {
                            "id": chat_id,
                            "title": entity.title,
                            "public_link": f"https://t.me/{entity.username}",
                            'is_sensitive': is_sensitive,
                        }
                    try:
                        invite = await client(functions.messages.ExportChatInviteRequest(entity))
                        return {
                            "id": chat_id,
                            "title": entity.title,
                            "invite_link": invite.link,
                            'is_sensitive': is_sensitive,
                        }
                    except errors.rpcerrorlist.ChatAdminRequiredError as e:
                        # not enough rights to get invite link
                        user_iter = client.iter_participants(entity, filter=ChannelParticipantsAdmins, limit=1)
                        async for user in user_iter:
                            # any one will do
                            public_link = user.username or f"[{user.first_name} {user.last_name}](https://web.telegram.org/a/#{user.id})"
                            return {
                                "id": chat_id,
                                "title": "{entity.first_name} {entity.last_name}",
                                "admin": public_link,
                                'is_sensitive': is_sensitive,
                            }
                if isinstance(entity, Chat):
                    try:
                        invite = await client(functions.messages.ExportChatInviteRequest(entity))
                        return {
                            "id": chat_id,
                            "title": entity.title,
                            "invite_link": invite.link,
                            'is_sensitive': is_sensitive,
                        }
                    except errors.rpcerrorlist.ChatAdminRequiredError as e:
                        # not enough rights to get invite link
                        user_iter = client.iter_participants(entity, filter=ChannelParticipantsAdmins, limit=1)
                        async for user in user_iter:
                            # any one will do
                            public_link = user.username or f"[{user.first_name} {user.last_name}](https://web.telegram.org/a/#{user.id})"
                            return {
                                "id": chat_id,
                                "title": "{entity.first_name} {entity.last_name}",
                                "admin": public_link,
                                'is_sensitive': is_sensitive,
                            }
        except BaseException as e:
            logger.error(f'get_chat_data for {chat_id}', exc_info=e)
            return {"id": chat_id, 'is_sensitive': is_sensitive,}

    def render_chat(self, chat_data: dict) -> str:
        if 'is_sensitive' in chat_data:
            if 'public_link' in chat_data:
                return f'{chat_data["title"]} {chat_data["public_link"]}'
            if 'invite_link' in chat_data:
                return f'{chat_data["title"]} [invite link]({chat_data["public_link"]})'
            if 'admin' in chat_data:
                return f'{chat_data["title"]} {chat_data["admin"]}'
            return f'{chat_data["title"]} {chat_data["id"]}'

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

    # DB methods (TODO - move)

    async def _read_saved_message(self) -> dict:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            message = await client.get_messages('me', ids=self._message_id)
            if message.text == '🦥':
                return self._empty_data()
            return self._deserialise_data(message.text)

    async def _write_saved_message(self, data: dict) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.edit_message('me', self._message_id, self._serialise_data(data))

    async def _clear_saved_message(self) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.edit_message('me', self._message_id, json.dumps(self._empty_data()))

    async def _write_placeholder_saved_message(self) -> None:
        placeholder = (random.choice(['🦮', '🐈‍⬛', '🦣', '🦫', '🦭', '🐿'])
                       + random.choice(['🦮', '🐈‍⬛', '🦣', '🦫', '🦭', '🐿']))
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.edit_message('me', self._message_id, placeholder)

    def _serialise_data(self, data: dict) -> str:
        # nonce = os.urandom(12)  # GCM mode needs 12 fresh bytes every time
        # data_enc = nonce + self._db_enc.encrypt(nonce, zlib.compress(json.dumps(data).encode()), b"")
        # return base64.urlsafe_b64encode(data_enc).decode()
        return json.dumps(data)

    def _deserialise_data(self, data_str: str) -> dict:
        # data_enc = base64.urlsafe_b64decode(data_str.encode())
        # data_res = self._db_enc.decrypt(data_enc[:12], data_enc[12:], b"")
        # return json.loads(zlib.decompress(data_res).decode())
        return json.loads(data_str)

    def _empty_data(self) -> dict:
        return {
            'chats': {},
            'trusted': {},
        }
