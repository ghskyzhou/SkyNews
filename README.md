# SkyNews

SkyNews 是一个个人每日简报应用：它不是无限新闻流，而是按你关心的主题搜索、过滤、总结，并生成最多 20 条高信号信息。

## 当前技术路线

- 后端：Python + FastAPI
- 前端：React + Vite + Tailwind CSS
- 数据库：SQLite
- 搜索：Tavily Search API
- 总结/翻译：DeepSeek API
- 股票行情：Yahoo Finance chart JSON endpoint
- 配置：后端 `.env`

## 项目结构

```text
SkyNews/
  backend/
    app/
      main.py              # FastAPI 入口
      brief_generator.py   # Tavily + DeepSeek / mock 简报生成
      stocks.py            # 股票行情
      database.py          # SQLite 读写
      models.py            # Pydantic 数据模型
      schema.sql           # 数据库 schema
      config.py            # .env 与 topics 配置
    config/topics.json     # 标签/主题配置
    data/                  # 本地 SQLite 数据库目录
    .env.example
    requirements.txt
  frontend/
    src/
      App.jsx
      api.js
      main.jsx
      index.css
    package.json
```

## 后端运行

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果 `backend/.env` 里的 `TAVILY_API_KEY` 为空，后端会自动进入 mock 模式。  
如果只设置 `TAVILY_API_KEY`，会进入 `tavily-only` 模式，展示搜索结果片段但不做 DeepSeek 三语整理。  
如果同时设置 `TAVILY_API_KEY` 和 `DEEPSEEK_API_KEY`，会进入 `tavily+deepseek` 模式。

```env
TAVILY_API_KEY=tvly-...
DEEPSEEK_API_KEY=sk-...
MOCK_MODE=false
```

## 前端运行

```powershell
cd frontend
npm install
npm run dev
```

如果 PowerShell 因执行策略拦截 `npm.ps1`，把上面的命令换成 `npm.cmd install` 和 `npm.cmd run dev`。

打开 Vite 输出的本地地址，通常是 [http://127.0.0.1:5173](http://127.0.0.1:5173)。前端通过 Vite proxy 调用 `http://127.0.0.1:8000/api/*`，不会读取或暴露任何 API key。

## API

- `GET /api/tags`
- `POST /api/generate-brief`
- `GET /api/briefs`
- `GET /api/briefs/{date}`
- `GET /api/stocks`

## 多语言

每条简报的 `headline`、`title`、`summary`、`why_it_matters`、`relevance_to_me` 都是三语对象：

```json
{
  "en": "English text",
  "zh": "中文文本",
  "ja": "日本語テキスト"
}
```

前端支持中文、英文、日语切换。

日语模式支持 ruby 注音。DeepSeek 会在 `ja_ruby` 中返回结构化片段，前端用 `<ruby><rt>` 渲染：

- 汉字使用平假名读音，要求按上下文区分训读和音读
- 外来语和常见技术词可以用简短英文释义标注
- 旧数据没有 `ja_ruby` 时会退回普通 `ja` 文本

## 主题配置

编辑 `backend/config/topics.json` 可以调整标签、搜索方向和个人相关性提示。每次生成 brief 时后端都会读取该配置。

## 股票监测

默认监测：

- QQQ
- VOO
- DRAM
- MU
- NVDA

可以在 `backend/.env` 中通过 `STOCK_SYMBOLS=QQQ,VOO,DRAM,MU,NVDA` 修改。

## 产品约束

- 无无限滚动
- 无社交 feed
- 无评论、点赞、推荐算法
- 每日 brief 最多 20 条
- 每条包含 `title`、`summary`、`why_it_matters`、`relevance_to_me`、`sources`、`tag`、`importance_score`
