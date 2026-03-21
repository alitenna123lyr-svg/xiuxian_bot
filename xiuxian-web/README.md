# 修仙之路 MiniApp · 部署指南

## 首次部署

```bash
# 1. 克隆代码
git clone https://github.com/你的仓库/XiuXianBot.git
cd XiuXianBot

# 2. 一键部署（自动安装 Node/Go/Redis、构建、配置 Nginx）
sudo bash setup.sh

# 3. 启动 Python 后端
python3 start.py
```

完了。

## 日常更新

```bash
cd XiuXianBot
git pull
sudo bash setup.sh
```

## setup.sh 做了什么

| 步骤 | 内容 | 首次 | 更新 |
|------|------|------|------|
| 依赖检查 | 自动安装 Node/pnpm/Go/Redis（缺啥装啥） | ✓ | 跳过 |
| 构建前端 | `pnpm install && pnpm build:fast` | ✓ | ✓ |
| 构建网关 | `go build` → 9MB 二进制 | ✓ | ✓ |
| 部署前端 | `rsync` 到 `/var/www/xiuxian-web/` | ✓ | ✓ |
| 部署网关 | 复制到 `/usr/local/bin/` | ✓ | ✓ |
| systemd | 创建服务、开机自启 | ✓ | 重启 |
| Nginx | 生成配置、监听 80 端口 | ✓ | 跳过 |

## 架构

```
Nginx :80
├── /         → /var/www/xiuxian-web/   静态文件
└── /api/     → Go网关 :8080
                ├── Redis 缓存
                └── Python :11450 → DB
```

## 查看日志

```bash
journalctl -u xiuxian-gateway -f    # Go 网关
journalctl -u nginx -f              # Nginx
redis-cli monitor                   # Redis 实时
```
