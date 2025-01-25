#!/bin/bash

echo "Setting up your own self-hosted Lethe."
echo "Please open the following page in your browser and login with your TG phone number:"
echo "https://my.telegram.org/apps"
echo "Copy the details from the page (the data is not passed anywhere but your self-hosted app):"
read -p "App api_id:" APP_API_ID
read -p "App api_hash": APP_API_HASH
read -p "Your phone number:" PHONE_NUMBER

echo
echo "$SESSION_ID" > keys.env

doctl sls deploy lethebot -env keys.env
doctl invoke lethebot