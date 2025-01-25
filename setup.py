import os
import sys
import re
import time
import random
import subprocess
from getpass import getpass

import requests
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


async def create_bot(client: TelegramClient) -> tuple[str, str]:
    def _extract_token(message):
        pattern = r"Use this token to access the HTTP API: ([a-zA-Z0-9_\-:]+)"
        match = re.search(pattern, message)

        if match:
            return match.group(1)
        else:
            return None

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
    tg_bot_handle = f'lethe_test_{bot_id}_bot'
    await client.send_message(botfather, tg_bot_handle)
    time.sleep(1)
    msg = (await client.get_messages(botfather))[0]
    assert 'Done! Congratulations on your new bot.' in msg.text
    token = _extract_token(msg.text)
    return token, tg_bot_handle

async def init_db(client: TelegramClient) -> str:
    msg = await client.send_message('me', '🦥')
    return str(msg.id)

def main():
    print('Preparing the environment...')
    load_dotenv('keys.env')
    api_id = os.getenv('TG_API_ID')
    api_hash = os.getenv('TG_API_HASH')
    bot_token = os.getenv('TG_BOT_TOKEN')
    bot_handle = os.getenv('TG_BOT_HANDLE')
    session_str = os.getenv('TG_SESSION_STR')
    db_password = os.getenv('DB_PASSWORD')
    db_path = os.getenv('DB_PATH')
    if api_id is None or api_hash is None:
        print('Please open the following page in your browser and login with your TG phone number:\n')
        print('https://my.telegram.org/apps\n')
        print('Copy the details from the page (the data is not passed anywhere but your self-hosted app)')
        api_id = int(getpass('App api_id:'))
        api_hash = getpass('App api_hash:')

    print('Logging into Telegram (might require SMS verification)...')
    with TelegramClient(StringSession(session_str), api_id, api_hash) as client:
        try:
            session_str = client.session.save()
            if bot_token is None:
                print('Creating TG bot...')
                bot_token, bot_handle = client.loop.run_until_complete(create_bot(client))
            if db_path is None:
                print('Initializing database...')
                db_path = client.loop.run_until_complete(init_db(client))
                db_password = str(os.urandom(32).hex())
        finally:
            client.disconnect()

    invite_code = str(os.urandom(16).hex())

    with open('keys.env', 'w') as envfile:
        envfile.write(f"""
            TG_API_ID={api_id}
            TG_API_HASH={api_hash}
            TG_BOT_TOKEN={bot_token}
            TG_BOT_HANDLE={bot_handle}
            TG_SESSION_STR={session_str}
            INVITE_CODE={invite_code}
            DB_PASSWORD={db_password}
            DB_PATH={db_path}
            """.replace(' ', ''))

    print('Deploying the main function...')
    result = subprocess.run(['doctl', 'sls', 'deploy', '.', '--include', 'lethebot/tg_webhook', '--env', 'keys.env'])
    if result.returncode != 0:
        exit(result.returncode)

    print('Connecting webhook...')
    result = subprocess.run(['doctl', 'sls', 'fn', 'get', 'lethebot/tg_webhook', '--url'], capture_output=True)
    if result.returncode != 0:
        exit(result.returncode)
    webhook_url = result.stdout.decode('utf-8').strip()

    result = requests.post(f'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}')
    if result.status_code != 200:
        print(f'Failed: setWebhook responded with {result.status_code} {result.text}')
        exit(result.status_code)

    print('Sending first message...')
    with TelegramClient(StringSession(session_str), api_id, api_hash) as client:
        client.loop.run_until_complete(client.send_message('@' + bot_handle, '/start'))
        sys.exit(0)


if __name__ == '__main__':
    main()
