import asyncio
import logging
import os

from bot import get_bot
from tg_client import TgClient

logger = logging.getLogger(__name__)


async def process_webhook(args):
    pass


def main(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    logger.info('Processing new msg')
    asyncio.run(process_webhook(args))
    logger.info('Completed, shutting down')

if __name__ == '__main__':
    session = os.environ.get('TG_SESSION_STR')
    api_id = os.environ.get('TG_API_ID')
    api_hash = os.environ.get('TG_API_HASH')
    if os.environ.get('TG_BOT_TOKEN'):
        # we already have a bot
        bot = get_bot(os.environ.get('TG_BOT_TOKEN'))
        bot.run_polling()
    else:
        # need to create a bot
        tg_client = TgClient(session, api_id, api_hash)
        asyncio.run(tg_client.create_new_bot())
