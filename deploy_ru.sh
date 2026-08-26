#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Portfolio HR-Agent (RU) — deploy to 147.45.107.99 → api-ru.vegman.dev
# Tested on Ubuntu 22.04 / Debian 12 running as root
#
# Prerequisites (DNS must be set BEFORE running):
#   api-ru.vegman.dev  →  A  →  147.45.107.99
#
# Usage (from your local machine):
#   export OPENAI_API_KEY=sk-...
#   bash deploy_ru.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running}"

RU_SERVER="root@147.45.107.99"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Portfolio HR-Agent (RU) → api-ru.vegman.dev         ║"
echo "╚══════════════════════════════════════════════════════╝"

ssh "${RU_SERVER}" bash -s -- "${OPENAI_API_KEY}" << 'REMOTE_SCRIPT'
set -euo pipefail

OPENAI_API_KEY="$1"
DOMAIN="api-ru.vegman.dev"
APP_DIR="/opt/portfolio-hr-agent"
SERVICE="portfolio-hr-agent"
REPO="https://github.com/natavegman/portfolio-site.git"
EMAIL="nata@vegman.dev"

echo "[1/7] Installing system packages…"
apt-get update -q
apt-get install -y -q \
    python3 python3-pip python3-venv \
    nginx certbot python3-certbot-nginx \
    git curl ufw

echo "[2/7] Configuring firewall…"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "[3/7] Cloning / updating repo…"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

echo "[4/7] Setting up Python venv…"
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

echo "[5/7] Writing .env and building FAISS index…"
cat > .env << ENVEOF
OPENAI_API_KEY=${OPENAI_API_KEY}
ENVEOF
chmod 600 .env

venv/bin/python backend/build_index.py

echo "[6/7] Installing systemd service…"
cat > /etc/systemd/system/${SERVICE}.service << SVCEOF
[Unit]
Description=Portfolio HR Agent RU (FastAPI / uvicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable "${SERVICE}"
systemctl restart "${SERVICE}"
echo "   ✓ Service started (127.0.0.1:8000)"

echo "[7/7] Configuring nginx + Let's Encrypt…"

cat > /etc/nginx/sites-available/${SERVICE} << NGXEOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }
}
NGXEOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/${SERVICE} /etc/nginx/sites-enabled/${SERVICE}
nginx -t
systemctl reload nginx

certbot --nginx \
    -d "${DOMAIN}" \
    --non-interactive \
    --agree-tos \
    -m "${EMAIL}" \
    --redirect

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅  RU backend deployed!                                    ║"
echo "║                                                              ║"
echo "║  API:   https://api-ru.vegman.dev                            ║"
echo "║  Check: curl https://api-ru.vegman.dev/health                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
REMOTE_SCRIPT
