#!/bin/bash

echo "Setting up your own self-hosted Lethe."
echo "Please open the following page in your browser and login with your TG phone number:"
echo "https://my.telegram.org/apps"
echo "Copy the details from the page (the data is not passed anywhere but your self-hosted app):"
echo -n "App api_id:"
read -sr TG_API_ID
echo -en "\nApp api_hash:"
read -sr TG_API_HASH
echo -en "\nYour phone number:"
read -r  PHONE_NUMBER

cat << EOT > keys.env
TG_API_ID=$TG_API_ID
TG_API_HASH=$TG_API_HASH
TG_BOT_TOKEN=TBD
TG_SESSION_STR=TBD
EOT

echo "Deploying your setup function (may take a few minutes)..."
doctl sls deploy . --include lethebot/setup --env keys.env
echo "Calling setup function to initiate session, be ready to receive SMS..."
ACTIVATION=$(doctl sls fn invoke lethebot/setup --param "phone:$PHONE_NUMBER" --no-wait)
RUNNING=1
while [ $RUNNING ]
do

done
IFS="|" read -r TG_PHONE_HASH TG_BOT_TOKEN <<< "$SETUP_DATA"
echo "TODO: hash: $TG_PHONE_HASH"
echo "Enter the code:"
read -sr TG_PHONE_CODE

echo "Calling setup function to log in..."
SETUP_DATA=$(doctl sls fn invoke lethebot/setup \
  --param "phone:$PHONE_NUMBER" \
  --param "hash:$TG_PHONE_HASH" \
  --param "code:$TG_PHONE_CODE")
IFS="|" read -r TG_SESSION_STR TG_BOT_TOKEN <<< "$SETUP_DATA"

cat <<EOT > keys.env
TG_API_ID=$TG_API_ID
TG_API_HASH=$TG_API_HASH
TG_BOT_TOKEN=$TG_BOT_TOKEN
TG_SESSION_STR=$TG_SESSION_STR
EOT

exit 0

echo "Deploying the main function"
doctl sls deploy lethebot/tg_webhook -env keys.env
WEBHOOK_URL=$(doctl sls fn get lethebot/tg_webhook --url)
curl -X POST "https://api.telegram.org/bot$TG_BOT_TOKEN/setWebhook?url=$WEBHOOK_URL"

echo "Complete!"
echo "All the further interaction happens through the bot, so you can safely remove this repo now."
