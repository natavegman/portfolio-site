#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Portfolio HR-Agent — automated deployment script
# Tested on Ubuntu 22.04 / Debian 12 running as root
#
# Usage:
#   export DUCKDNS_SUBDOMAIN=natavegman     # your duckdns subdomain
#   export DUCKDNS_TOKEN=xxxx-xxxx-xxxx     # token from duckdns.org
#   export OPENAI_API_KEY=sk-...            # OpenAI key
#   bash deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Validate env vars ────────────────────────────────────────────────────────
: "${DUCKDNS_SUBDOMAIN:?Set DUCKDNS_SUBDOMAIN before running}"
: "${DUCKDNS_TOKEN:?Set DUCKDNS_TOKEN before running}"
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running}"

DOMAIN="${DUCKDNS_SUBDOMAIN}.duckdns.org"
APP_DIR="/opt/portfolio-hr-agent"
SERVICE="portfolio-hr-agent"
REPO="https://github.com/natavegman/portfolio-site.git"
EMAIL="vegmannata@gmail.com"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Portfolio HR-Agent → deploy to ${DOMAIN}  "
echo "╚══════════════════════════════════════════════════╝"

# ── 1. System packages ───────────────────────────────────────────────────────
echo "[1/8] Installing system packages…"
apt-get update -q
apt-get install -y -q \
    python3 python3-pip python3-venv \
    nginx certbot python3-certbot-nginx \
    git curl ufw

# ── 2. Firewall ──────────────────────────────────────────────────────────────
echo "[2/8] Configuring firewall…"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ── 3. Clone or update repo ──────────────────────────────────────────────────
echo "[3/8] Cloning / updating repo…"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

# ── 4. Python venv + dependencies ───────────────────────────────────────────
echo "[4/8] Setting up Python venv…"
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

# ── 5. Write .env and build FAISS index ─────────────────────────────────────
echo "[5/8] Writing .env and building FAISS index…"
cat > .env << EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
EOF
chmod 600 .env

venv/bin/python backend/build_index.py

# ── 6. Systemd service ───────────────────────────────────────────────────────
echo "[6/8] Installing systemd service…"
cat > /etc/systemd/system/${SERVICE}.service << EOF
[Unit]
Description=Portfolio HR Agent (FastAPI / uvicorn)
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
EOF

systemctl daemon-reload
systemctl enable "${SERVICE}"
systemctl restart "${SERVICE}"
echo "   ✓ Service started (port 127.0.0.1:8000)"

# ── 7. DuckDNS: update A-record to this server's IP ─────────────────────────
echo "[7/8] Updating DuckDNS A-record…"
DUCK_RESP=$(curl -s "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=")
if [ "$DUCK_RESP" = "OK" ]; then
    echo "   ✓ DuckDNS updated → ${DOMAIN}"
else
    echo "   ✗ DuckDNS response: ${DUCK_RESP} — check subdomain/token and retry"
    exit 1
fi

# ── 8. Nginx reverse-proxy ───────────────────────────────────────────────────
echo "[8/8] Configuring nginx + Let's Encrypt…"

cat > /etc/nginx/sites-available/${SERVICE} << 'NGINX'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
NGINX
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/" /etc/nginx/sites-available/${SERVICE}

# Remove default site if present to avoid conflicts
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/${SERVICE} /etc/nginx/sites-enabled/${SERVICE}
nginx -t
systemctl reload nginx

# Let's Encrypt TLS cert (auto-configures nginx for HTTPS + HTTP→HTTPS redirect)
certbot --nginx \
    -d "${DOMAIN}" \
    --non-interactive \
    --agree-tos \
    -m "${EMAIL}" \
    --redirect

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅  Deployed successfully!                                  ║"
echo "║                                                              ║"
echo "║  API:  https://${DOMAIN}                "
echo "║  Health check:                                               ║"
echo "║    curl https://${DOMAIN}/health        "
echo "║                                                              ║"
echo "║  Next: update index.html and push to GitHub:                 ║"
echo "║    window.CHAT_API_URL = 'https://${DOMAIN}'    "
echo "╚══════════════════════════════════════════════════════════════╝"
