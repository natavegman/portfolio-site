#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Portfolio HR-Agent (RU backend) — automated deployment to Russian VPS
# Target: 147.45.107.99  (Ubuntu 22.04 / Debian 12, root SSH)
#
# Usage on your local machine:
#   export DUCKDNS_SUBDOMAIN_RU=natavegman-ru   # create this sub at duckdns.org
#   export DUCKDNS_TOKEN=xxxx-xxxx-xxxx          # same token as for EN subdomain
#   export OPENAI_API_KEY=sk-...
#   bash deploy_ru.sh
#
# The script will SSH into 147.45.107.99, install everything, and return
# the live HTTPS URL to paste into index.html as window.CHAT_API_RU.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

: "${DUCKDNS_SUBDOMAIN_RU:?Set DUCKDNS_SUBDOMAIN_RU (e.g. natavegman-ru) before running}"
: "${DUCKDNS_TOKEN:?Set DUCKDNS_TOKEN before running}"
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running}"

RU_SERVER="root@147.45.107.99"
DOMAIN="${DUCKDNS_SUBDOMAIN_RU}.duckdns.org"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Portfolio HR-Agent RU → deploying to ${RU_SERVER}   ║"
echo "║  Domain: ${DOMAIN}                              ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Pass all required variables into the remote session
ssh "${RU_SERVER}" bash -s -- \
    "${DUCKDNS_SUBDOMAIN_RU}" \
    "${DUCKDNS_TOKEN}" \
    "${OPENAI_API_KEY}" \
    "${DOMAIN}" \
<< 'REMOTE_SCRIPT'
set -euo pipefail

DUCKDNS_SUBDOMAIN_RU="$1"
DUCKDNS_TOKEN="$2"
OPENAI_API_KEY="$3"
DOMAIN="$4"

APP_DIR="/opt/portfolio-hr-agent"
SERVICE="portfolio-hr-agent"
REPO="https://github.com/natavegman/portfolio-site.git"
EMAIL="vegmannata@gmail.com"

echo "[1/8] Installing system packages…"
apt-get update -q
apt-get install -y -q \
    python3 python3-pip python3-venv \
    nginx certbot python3-certbot-nginx \
    git curl ufw

echo "[2/8] Configuring firewall…"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "[3/8] Cloning / updating repo…"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

echo "[4/8] Setting up Python venv…"
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

echo "[5/8] Writing .env and building FAISS index…"
cat > .env << ENVEOF
OPENAI_API_KEY=${OPENAI_API_KEY}
ENVEOF
chmod 600 .env

venv/bin/python backend/build_index.py

echo "[6/8] Installing systemd service…"
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

echo "[7/8] Updating DuckDNS A-record…"
DUCK_RESP=$(curl -s "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN_RU}&token=${DUCKDNS_TOKEN}&ip=")
if [ "$DUCK_RESP" = "OK" ]; then
    echo "   ✓ DuckDNS updated → ${DOMAIN}"
else
    echo "   ✗ DuckDNS response: ${DUCK_RESP} — check subdomain/token"
    exit 1
fi

echo "[8/8] Configuring nginx + Let's Encrypt…"
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
echo "║  API:   https://${DOMAIN}              ║"
echo "║  Check: curl https://${DOMAIN}/health  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
REMOTE_SCRIPT

echo ""
echo "Next step — add to index.html <head> (before </head>):"
echo ""
echo "  <script>"
echo "    window.CHAT_API_RU = 'https://${DOMAIN}';"
echo "  </script>"
echo ""
echo "Then push: git add index.html && git commit -m 'Set RU API URL' && git push"
