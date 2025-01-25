import json
import random
import re
import time

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

    async def create_new_bot(self) -> None:

        def _extract_token(message):
            pattern = r"Use this token to access the HTTP API: ([a-zA-Z0-9_\-:]+)"
            match = re.search(pattern, message)

            if match:
                return match.group(1)
            else:
                return None

        async with TelegramClient(StringSession(self._session), self._api_id, self._api_hash) as client:
            try:
                # Connect to Telegram
                await client.connect()
                bot_id = random.randint(1, 1000)
                # Get the BotFather chat
                botfather = await client.get_entity('BotFather')
                # Send the command to create a new bot
                await client.send_message(botfather, '/newbot')
                time.sleep(1)
                msg = (await client.get_messages(botfather))[0]
                assert 'Alright, a new bot' in msg.text
                await client.send_message(botfather, f'Lethe Bot {bot_id}')
                time.sleep(1)
                msg = (await client.get_messages(botfather))[0]
                assert 'Now let\'s choose a username' in msg.text
                await client.send_message(botfather, f'lethe_test_{bot_id}_bot')
                time.sleep(1)
                msg = (await client.get_messages(botfather))[0]
                assert 'Done! Congratulations on your new bot.' in msg.text
                token = _extract_token(msg.text)
                print(token)
                return token
            finally:
                await client.disconnect()