#!/bin/bash

set -e

echo "Setting up your own self-hosted Lethe."

if ! command -v doctl 2>&1 >/dev/null
then
    echo "doctl could not be found, have you configured the DigitalOcean CLI?"
    exit 1
fi

echo "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python setup.py

echo "Complete!"
echo "All the further interaction happens through the bot, so you can safely remove this folder now."
