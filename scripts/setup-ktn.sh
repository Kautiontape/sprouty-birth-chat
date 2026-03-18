#!/usr/bin/env bash
# Bootstrap birth-chat on a fresh ktn server.
# Run: ssh ktn 'bash -s' < scripts/setup-ktn.sh
set -euo pipefail

APP_DIR="$HOME/apps/birth-chat"
GHCR_IMAGE="ghcr.io/shawnsquire/sprouty-birth-chat"

echo "==> Creating app directory"
mkdir -p "$APP_DIR"

echo "==> Creating Docker volume"
docker volume create birth_chat_data || true

echo "==> Authenticating to GHCR"
echo "You need a GitHub Personal Access Token (classic) with read:packages scope."
echo "Create one at: https://github.com/settings/tokens"
read -rp "GitHub PAT: " GHCR_TOKEN
echo "$GHCR_TOKEN" | docker login ghcr.io -u shawnsquire --password-stdin

echo "==> Writing docker-compose.prod.yml"
cat > "$APP_DIR/docker-compose.yml" << 'COMPOSE'
services:
  app:
    image: ghcr.io/shawnsquire/sprouty-birth-chat:latest
    container_name: birth_chat_bot
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      SERPER_API_KEY: ${SERPER_API_KEY}
    volumes:
      - birth_chat_data:/usr/src/app/data
    restart: always

  watchtower:
    image: containrrr/watchtower
    container_name: birth_chat_watchtower
    environment:
      WATCHTOWER_CLEANUP: "true"
      WATCHTOWER_POLL_INTERVAL: "60"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ${HOME}/.docker/config.json:/config.json:ro
    command: birth_chat_bot
    restart: always

volumes:
  birth_chat_data:
    external: true
COMPOSE

echo "==> Writing .env file"
if [ ! -f "$APP_DIR/.env" ]; then
    read -rp "ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY
    read -rp "TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
    read -rp "SERPER_API_KEY (optional, press enter to skip): " SERPER_API_KEY
    cat > "$APP_DIR/.env" << ENV
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
SERPER_API_KEY=$SERPER_API_KEY
ENV
    echo ".env written"
else
    echo ".env already exists, skipping"
fi

echo "==> Pulling and starting"
cd "$APP_DIR"
docker compose pull
docker compose up -d

echo ""
echo "Done! birth-chat is running."
echo "Watchtower will auto-update when you push to main."
echo ""
echo "Useful commands:"
echo "  cd $APP_DIR && docker compose logs -f app"
echo "  cd $APP_DIR && docker compose restart app"
