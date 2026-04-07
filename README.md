# Kaka Weight Tracker

一个基于 Cloudflare Pages 的体重记录应用，使用 KV 存储数据。

## 功能

- 记录每日体重
- 查看体重趋势图表
- 数据统计（总记录数、平均体重、最新体重）
- 分页浏览历史记录
- 删除记录

## 部署

1. 创建 Cloudflare Pages 项目
2. 绑定 KV 命名空间（创建名为 `WEIGHT_KV` 的 KV）
3. 配置 `wrangler.toml`（参考 `wrangler.toml.example`）
4. 部署：

```bash
npm install
npx wrangler pages deploy .
```

## 配置

复制 `wrangler.toml.example` 为 `wrangler.toml`，填入你的 KV 命名空间 ID：

```toml
compatibility_date = "2024-01-01"
name = "kaka-weight-tracker"
pages_build_output_dir = "public"

[[kv_namespaces]]
binding = "WEIGHT_KV"
id = "你的 KV 命名空间 ID"
```

## 文件结构

```
├── functions/
│   ├── index.ts    # 前端页面
│   └── api.ts      # API 接口
├── wrangler.toml   # 部署配置（包含敏感信息）
├── wrangler.toml.example  # 配置模板
└── package.json
```

## API

- `GET /api?page=1` - 获取记录列表
- `POST /api` - 添加记录（body: `{"date": "2024-01-01", "weight": 70.5}`)
- `DELETE /api?id=xxx` - 删除记录