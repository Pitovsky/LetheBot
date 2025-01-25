import json

from telethon import TelegramClient
from telethon.sessions import StringSession


async def get_chats(session, api_id, api_hash) -> None:
    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        print(await client.get_dialogs())

async def read_saved_message(session, api_id, api_hash) -> dict:
    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        # TODO FIX
        message_id = 1399
        message = await client.get_messages('me', ids=message_id)
        return json.loads(message.text)

# async def write_saved_message(session, api_id, api_hash) -> dict:
#     async with TelegramClient(StringSession(session), api_id, api_hash) as client:
#         # TODO FIX
#         message_id = 1399
#         message = await client.get_messages('me', ids=message_id)
#         return json.loads(message.text)