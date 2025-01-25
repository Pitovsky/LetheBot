from telethon import TelegramClient
from telethon.sessions import StringSession


async def get_chats(session, api_id, api_hash) -> None:
    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        print(await client.get_dialogs())
