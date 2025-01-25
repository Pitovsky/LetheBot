import json

from telethon import TelegramClient
from telethon.sessions import StringSession


class TgClient():
    def __init__(self, session, api_id, api_hash):
        self._session = session
        self._api_id = api_id
        self._api_hash = api_hash
        # TODO GET FROM ENV
        self._message_id = 1399

    async def get_chats(self) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            return await client.get_dialogs()

    async def _read_saved_message(self) -> dict:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            message = await client.get_messages('me', ids=self._message_id)
            return json.loads(message.text)

    async def _write_saved_message(self, data: dict) -> None:
        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            await client.edit_message('me', self._message_id, json.dumps(data))
