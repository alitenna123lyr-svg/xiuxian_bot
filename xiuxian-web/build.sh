#!/usr/bin/env bash
# ═══════════════════════════════════════════
#  修仙之路 MiniApp — 一键构建
#  用法：
#    bash build.sh          # 构建 Linux 产物
#    bash build.sh windows  # 构建 Windows 产物
# ═══════════════════════════════════════════
set -e
cd "$(dirname "$0")"

TARGET_OS="${1:-linux}"
TARGET_ARCH="amd64"
BIN_NAME="xiuxian-gateway"
if [ "$TARGET_OS" = "windows" ]; then
  BIN_NAME="xiuxian-gateway.exe"
fi

echo ""
echo "══════════════════════════════════════"
echo "  修仙之路 · 构建脚本"
echo "  目标: ${TARGET_OS}/${TARGET_ARCH}"
echo "══════════════════════════════════════"
echo ""

# 1. 前端
echo "[1/2] 构建前端..."
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
pnpm build:fast
echo "  ✓ 前端构建完成 → dist/"
echo ""

# 2. Go 网关
echo "[2/2] 构建 Go 网关..."
cd gateway
GOOS="$TARGET_OS" GOARCH="$TARGET_ARCH" CGO_ENABLED=0 \
  go build -ldflags="-s -w" -o "../dist/${BIN_NAME}" ./cmd/
cd ..
echo "  ✓ 网关构建完成 → dist/${BIN_NAME}"
echo ""

# 完成
echo "══════════════════════════════════════"
echo "  构建完成！产物："
echo "══════════════════════════════════════"
ls -lh "dist/${BIN_NAME}"
echo ""
echo "dist/ 目录内容："
ls dist/
echo ""
echo "下一步：将 dist/ 整个上传到服务器"
echo "  scp -r dist/* user@yourserver:/opt/xiuxian/web/"
echo ""
