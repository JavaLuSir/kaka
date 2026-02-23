# 体重记录器

一个简单的体重记录 Web 应用，支持记录、查看历史数据和趋势分析。

## 功能特性

- 📝 记录每日体重
- 📈 折线图展示体重趋势
- 📊 数据统计（总记录数、平均体重、最新体重）
- 📑 历史记录分页浏览（每页 10 条）
- 💾 数据存储在 JSON 文件中，无需数据库

## 环境要求

- Python 3.10+
- Flask

## 安装依赖

```bash
pip install flask
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

## 运行

```bash
python weight_tracker.py
```

服务启动后，访问 http://localhost:5000

如需局域网访问（默认）：

```
http://你的IP地址:5000
```

## 数据存储

记录保存在 `weight_records.json` 文件中。

## 项目结构

```
kaka/
├── weight_tracker.py    # 主程序
├── requirements.txt    # Python 依赖
├── weight_records.json # 体重数据文件（自动生成）
└── README.md
```
