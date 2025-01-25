import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger(__name__)


async def create_bot(client: TelegramClient) -> str:
    return 'TBD'


async def prepare_session_bot(session_str: Optional[str],
                              bot_token: Optional[str],
                              phone: Optional[str],
                              phone_hash: Optional[str],
                              code: Optional[str]):

    client = TelegramClient(StringSession(session_str),
                            api_id=int(os.environ['TG_API_ID']),
                            api_hash=os.environ['TG_API_HASH'])
    if not client.is_connected():
        await client.connect()
    if await client.is_user_authorized():
        logging.info("Already logged in")
        session_str = client.session.save()
        if bot_token is None:
            bot_token = await create_bot(client)
    elif code is None or phone_hash is None:
        logging.info("Sending the code")
        sent_code = await client.send_code_request(phone)
        return sent_code.phone_code_hash, 'TBD'
    else:
        logging.info("Signing in with the code")
        await client.sign_in(phone=phone, phone_code_hash=phone_hash, code=code)
        session_str = client.session.save()
        if bot_token is None:
            bot_token = await create_bot(client)
    return session_str, bot_token


def main(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    logger.info('Processing new msg')

    session_str = os.environ['TG_SESSION_STR']
    bot_token = os.environ['TG_BOT_TOKEN']
    if session_str == 'TBD':
        session_str = None
    if bot_token == 'TBD':
        bot_token = None

    session_str, bot_token = asyncio.run(prepare_session_bot(session_str,
                                                             bot_token,
                                                             args.get('phone'),
                                                             args.get('hash'),
                                                             args.get('code')))

    logger.info('Completed, shutting down')
    return session_str + "|" + bot_token
