import asyncio
import logging
import os

from bot import LetheBot
from tg_client import TgClient

logger = logging.getLogger(__name__)


async def process_webhook(args, bot):
    pass


def main(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    logger.info('Processing new msg')
    bot = LetheBot()
    asyncio.run(bot.process_single_webhook(os.environ.get('TG_BOT_TOKEN'), args))
    logger.info('Completed, shutting down')


if __name__ == '__main__':
    session = os.environ.get('TG_SESSION_STR')
    api_id = os.environ.get('TG_API_ID')
    api_hash = os.environ.get('TG_API_HASH')
    bot = LetheBot().get_bot(os.environ.get('TG_BOT_TOKEN'))
    bot.run_polling()
