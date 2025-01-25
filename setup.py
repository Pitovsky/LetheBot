import os
import re
import time
import random
from getpass import getpass

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


async def create_bot(client: TelegramClient) -> str:
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
    await client.send_message(botfather, f'lethe_test_{bot_id}_bot')
    time.sleep(1)
    msg = (await client.get_messages(botfather))[0]
    assert 'Done! Congratulations on your new bot.' in msg.text
    token = _extract_token(msg.text)
    return token


def main():
    load_dotenv('keys.env')
    api_id = os.getenv('TG_API_ID')
    api_hash = os.getenv('TG_API_HASH')
    bot_token = os.getenv('TG_BOT_TOKEN')
    session_str = os.getenv('TG_SESSION_STR')
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
                bot_token = create_bot(client)
        finally:
            client.disconnect()

    invite_code = str(os.urandom(15).hex())

    with open('keys.env', 'w') as envfile:
        envfile.write(f"""
            TG_API_ID={api_id}
            TG_API_HASH={api_hash}
            TG_BOT_TOKEN={bot_token}
            TG_SESSION_STR={session_str}
            INVITE_CODE={invite_code}
            """.replace(' ', ''))


if __name__ == '__main__':
    main()
