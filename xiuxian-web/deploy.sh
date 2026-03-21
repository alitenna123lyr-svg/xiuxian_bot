#!/usr/bin/env bash
# ═══════════════════════════════════════════════════
#  修仙之路 · 服务器部署脚本
#  在服务器上运行，自动完成全部部署工作
#
#  用法：
#    bash deploy.sh               # 首次部署
#    bash deploy.sh update-web    # 仅更新前端
#    bash deploy.sh update-gw     # 仅更新网关
# ═══════════════════════════════════════════════════
set -e

# ── 路径约定 ──
WEB_DIR="/var/www/xiuxian-web"
GW_BIN="/usr/local/bin/xiuxian-gateway"
BOT_DIR="/opt/xiuxian/bot"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"

# ── 颜色 ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }

echo ""
echo "══════════════════════════════════════"
echo "  修仙之路 · 服务器部署"
echo "══════════════════════════════════════"
echo ""

# ── 检查 dist/ 存在 ──
if [ ! -f "${DIST_DIR}/index.html" ]; then
    echo "错误：dist/index.html 不存在。请先在开发机上运行 bash build.sh"
    exit 1
fi
if [ ! -f "${DIST_DIR}/xiuxian-gateway" ]; then
    echo "错误：dist/xiuxian-gateway 不存在。请先在开发机上运行 bash build.sh"
    exit 1
fi

ACTION="${1:-all}"

# ════════════════════════════════════════
# 部署前端到 /var/www/xiuxian-web
# ════════════════════════════════════════
deploy_web() {
    echo "[前端] 部署到 ${WEB_DIR}"
    mkdir -p "${WEB_DIR}"
    # 同步静态文件（不含二进制）
    rsync -a --delete --exclude='xiuxian-gateway' "${DIST_DIR}/" "${WEB_DIR}/"
    ok "前端已部署到 ${WEB_DIR}"
}

# ════════════════════════════════════════
# 部署 Go 网关
# ════════════════════════════════════════
deploy_gateway() {
    echo "[网关] 部署 xiuxian-gateway"
    cp "${DIST_DIR}/xiuxian-gateway" "${GW_BIN}"
    chmod +x "${GW_BIN}"
    ok "网关已部署到 ${GW_BIN}"

    # 创建 systemd 服务
    if [ ! -f /etc/systemd/system/xiuxian-gateway.service ]; then
        echo "[网关] 创建 systemd 服务"
        cat > /etc/systemd/system/xiuxian-gateway.service << 'UNIT'
[Unit]
Description=XiuXian Gateway (Go + Redis)
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
ExecStart=/usr/local/bin/xiuxian-gateway \
    -listen :8080 \
    -redis 127.0.0.1:6379 \
    -backend http://127.0.0.1:11450
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
UNIT
        systemctl daemon-reload
        systemctl enable xiuxian-gateway
        ok "systemd 服务已创建并启用"
    fi

    systemctl restart xiuxian-gateway
    ok "网关已重启"
}

# ════════════════════════════════════════
# 配置 Nginx（仅首次）
# ════════════════════════════════════════
setup_nginx() {
    NGINX_CONF="/etc/nginx/sites-available/xiuxian"
    if [ -f "${NGINX_CONF}" ]; then
        warn "Nginx 配置已存在，跳过（如需更新请手动编辑 ${NGINX_CONF}）"
        return
    fi

    echo "[Nginx] 请输入你的域名（如 game.example.com）："
    read -r DOMAIN
    if [ -z "$DOMAIN" ]; then
        warn "未输入域名，跳过 Nginx 配置"
        return
    fi

    cat > "${NGINX_CONF}" << CONF
server {
    listen 80;
    server_name ${DOMAIN};

    gzip on;
    gzip_vary on;
    gzip_min_length 256;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;

    root /var/www/xiuxian-web;
    index index.html;

    location /assets/ {
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_read_timeout 30s;
    }
}
CONF

    ln -sf "${NGINX_CONF}" /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    ok "Nginx 已配置: ${DOMAIN}"
}

# ════════════════════════════════════════
# 执行
# ════════════════════════════════════════
case "$ACTION" in
    all)
        deploy_web
        deploy_gateway
        setup_nginx
        echo ""
        echo "══════════════════════════════════════"
        echo "  部署完成！"
        echo ""
        echo "  前端: ${WEB_DIR}"
        echo "  网关: ${GW_BIN} (:8080)"
        echo "  Nginx: :443 → /var/www/xiuxian-web"
        echo ""
        echo "  验证："
        echo "    curl http://127.0.0.1:8080/api/health"
        echo "    curl https://你的域名/api/health"
        echo "══════════════════════════════════════"
        ;;
    update-web)
        deploy_web
        ok "前端更新完成（无需重启）"
        ;;
    update-gw)
        deploy_gateway
        ok "网关更新完成（已自动重启）"
        ;;
    *)
        echo "用法: bash deploy.sh [all|update-web|update-gw]"
        exit 1
        ;;
esac
