#!/bin/bash

set -e

echo "Setting up your own self-hosted Lethe."
echo "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup.py

echo "Complete!"
echo "All the further interaction happens through the bot, so you can safely remove this folder now."
