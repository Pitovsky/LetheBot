import asyncio
import logging
from telethon import TelegramClient

logger = logging.getLogger(__name__)


async def process_webhook(args):
    pass

def main(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    logger.info('Processing new msg')
    asyncio.run(process_webhook(args))
    logger.info('Completed, shutting down')
