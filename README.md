# 体重记录器 (Cloudflare Workers 版)

一个简单的体重记录 Web 应用，支持记录、查看历史数据和趋势分析。

## 功能特性

- 📝 记录每日体重
- 📈 折线图展示体重趋势
- 📊 数据统计（总记录数、平均体重、最新体重）
- 📑 历史记录分页浏览（每页 10 条）
- 💾 数据存储在 Cloudflare KV，无需数据库

## 环境要求

- Node.js 18+
- npm

## 安装依赖

```bash
npm install
```

## 配置

1. 复制 `wrangler.toml.example` 为 `wrangler.toml`：
```bash
cp wrangler.toml.example wrangler.toml
```

2. 在 Cloudflare Dashboard 创建 KV 命名空间：
   - 进入 Workers → KV → 创建命名空间
   - 复制命名空间 ID
   - 粘贴到 `wrangler.toml` 的 `id` 位置

3. 登录 Cloudflare：
```bash
npx wrangler login
```

## 开发

```bash
npm run dev
```

## 部署

```bash
npm run deploy
```

## 数据迁移

如果要从 Python 版本迁移数据，将现有 `weight_records.json` 内容复制到 KV 中：

```bash
# 方法1: 使用 wrangler 命令行
npx wrangler kv:key put weight_records "$(cat weight_records.json)" --namespace-id=你的KV_ID

# 方法2: 通过 API
curl -X PUT "https://api.cloudflare.com/client/v4/accounts/你的ACCOUNT_ID/storage/kv/namespaces/你的KV_ID/keys/weight_records" \
  -H "Authorization: Bearer 你的API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat weight_records.json)"
```

## 项目结构

```
kaka/
├── src/
│   └── index.ts       # 主程序 (Hono + 前端)
├── wrangler.toml      # Cloudflare 配置
├── package.json       # Node 依赖
└── README.md
```
