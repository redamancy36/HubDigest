# HubDigest

GitHub 趋势中文摘要 · 每日自动抓取 Trending 项目并生成 AI 摘要

## 功能

- **日榜 + 周榜**：今日 Trending 与本周 Trending 分开展示
- **多语言分榜**：All / Python / JavaScript / TypeScript / Java / Go / Rust
- **AI 中文摘要**：项目名、一句话解释、技术栈、为什么火、应用场景
- **历史 30 天**：可回看过去 30 天的榜单
- **零成本部署**：GitHub Actions + Vercel，无需服务器

## 快速部署（推荐）

无需本地运行脚本，全程在 GitHub 和 Vercel 网页完成：

1. **创建仓库并推送代码**
   - 在 GitHub 新建仓库 → 本地 `git clone` 本仓库后，修改 remote 并 `git push`

2. **配置 API Key**
   - 仓库 → **Settings** → **Secrets and variables** → **Actions**
   - 新增 `DEEPSEEK_API_KEY`（在 [platform.deepseek.com](https://platform.deepseek.com) 获取）

3. **部署到 Vercel**
   - 打开 [vercel.com](https://vercel.com) → 用 GitHub 登录 → **Add New** → **Project**
   - 选择该仓库 → **Deploy**（无需改配置）

4. **生成首日数据**
   - 仓库 → **Actions** → **Daily Trending** → **Run workflow**
   - 约 5 分钟完成后，刷新 Vercel 网页即可看到数据

之后每天北京时间 8:00 自动更新，也可随时手动触发。

## 本地运行（可选）

仅用于本地测试或调试，**部署不需要执行**：

```bash
pip install -r requirements.txt
cd scripts && python fetch_trending.py
export DEEPSEEK_API_KEY=sk-xxx && python summarize_with_llm.py
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
