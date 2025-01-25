#!/bin/bash

echo "Setting up your own self-hosted Lethe."
echo "Setting up Python environment..."
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Preparing the environment..."
python setup.py

echo "Deploying the main function..."
doctl sls deploy lethebot/tg_webhook -env keys.env
WEBHOOK_URL=$(doctl sls fn get lethebot/tg_webhook --url)
curl -X POST "https://api.telegram.org/bot$TG_BOT_TOKEN/setWebhook?url=$WEBHOOK_URL"

echo "Complete!"
echo "All the further interaction happens through the bot, so you can safely remove this repo now."
