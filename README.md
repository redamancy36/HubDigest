# HubDigest

GitHub 趋势中文摘要 · 每日自动抓取 Trending 项目并生成 AI 摘要

## 功能

- **日榜 + 周榜**：今日 Trending 与本周 Trending 分开展示
- **多语言分榜**：All / Python / JavaScript / TypeScript / Java / Go / Rust
- **AI 中文摘要**：项目名、一句话解释、技术栈、为什么火
- **历史 30 天**：可回看过去 30 天的榜单
- **零成本部署**：GitHub Actions + Vercel，无需服务器

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 1. 抓取 Trending
cd scripts && python fetch_trending.py

# 2. AI 摘要（需配置 API Key）
export DEEPSEEK_API_KEY=sk-xxx
python summarize_with_llm.py

# 3. 生成归档索引
python generate_html.py
```

## 运维指南

新手修改配置、排查问题，请查看 **[doc/运维指南.md](doc/运维指南.md)**。

## 配置

编辑 `config.yaml`：

- `project_count`: 每榜项目数量（默认 20）
- `languages`: 语言列表
- `llm_priority`: LLM 连接池优先级（DeepSeek 优先）
- `llm_concurrency`: 并发数（默认 50，加速摘要）
- `use_thinking_model`: 是否使用思考模型推导应用场景（默认 true）
- `llm_fallback`: 全部失败时 `raw`（展示原文）或 `skip`（跳过）

## GitHub Actions

1. 在仓库 Settings → Secrets 中添加：
   - `DEEPSEEK_API_KEY`（必填）
   - `QWEN_API_KEY`、`KIMI_API_KEY`（可选，作为 fallback）

2. 每日北京时间 8:00 自动执行，也可手动触发（Actions → Daily Trending → Run workflow）

## Vercel 部署

1. 将仓库导入 Vercel
2. 无需构建，直接部署
3. 首次运行 Actions 后即可在网页查看数据

## 项目结构

```
HubDigest/
├── .github/workflows/daily-trending.yml
├── scripts/
│   ├── fetch_trending.py
│   ├── summarize_with_llm.py
│   ├── generate_html.py
│   └── config.py
├── src/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── data/
├── config.yaml
└── requirements.txt
```

## License

MIT
