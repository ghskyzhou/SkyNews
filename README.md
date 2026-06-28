# SkyNews

SkyNews 是一个个人每日简报应用：它不是无限新闻流，而是按你关心的主题搜索、过滤、总结，并生成最多 20 条高信号信息。

## 技术路线

- 后端：Python + FastAPI
- 前端：React + Vite + Tailwind CSS
- 数据库：SQLite
- 搜索：Tavily Search API
- 总结/翻译：DeepSeek API
- 股票行情：Yahoo Finance chart JSON endpoint
- 本地开发端口：后端 `8007`，前端 `8008`

## 后端运行

Windows 推荐这样启动，不依赖 `uvicorn` 是否在 PATH 里：

```powershell
cd S:\Codes\Web\SkyNews\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8007
```

`backend\.env` 示例：

```env
TAVILY_API_KEY=tvly-...
DEEPSEEK_API_KEY=sk-...
MOCK_MODE=false
DEEPSEEK_MAX_TOKENS=12000
DEEPSEEK_MAX_BRIEF_ITEMS=8
```

模式判断：

- 没有 `TAVILY_API_KEY`：`mock`
- 有 `TAVILY_API_KEY`，没有 `DEEPSEEK_API_KEY`：`tavily-only`
- 两个 key 都有，且 `MOCK_MODE=false`：`tavily+deepseek`

检查：

```text
http://127.0.0.1:8007/api/health
```

## 前端运行

```powershell
cd S:\Codes\Web\SkyNews\frontend
npm.cmd install
npm.cmd run dev
```

前端默认启动在：

```text
http://127.0.0.1:8008
```

Vite 会把 `/api/*` 代理到后端：

```text
http://127.0.0.1:8007
```

## 局域网手机访问

1. 电脑和手机连同一个 Wi-Fi。
2. 在 Windows 上查电脑局域网 IP：

```powershell
ipconfig
```

找类似 `192.168.x.x` 的 IPv4 地址。

3. 手机浏览器打开：

```text
http://你的电脑IP:8008
```

例如：

```text
http://192.168.1.23:8008
```

如果打不开，检查 Windows 防火墙是否允许 Node.js / Python 的专用网络访问。

## 真实生成的稳定性

日语 ruby 注音会显著增加 DeepSeek 输出长度。为了避免模型输出 JSON 被截断，默认真实模式最多让 DeepSeek 生成 8 条 brief：

```env
DEEPSEEK_MAX_BRIEF_ITEMS=8
DEEPSEEK_MAX_TOKENS=12000
```

这仍然满足产品规则“每日 brief 最多 20 条”。如果想更多条，可以逐步调高 `DEEPSEEK_MAX_BRIEF_ITEMS`，但输出越长越容易被截断、成本也更高。

## API

- `GET /api/tags`
- `POST /api/generate-brief`
- `GET /api/briefs`
- `GET /api/briefs/{date}`
- `GET /api/stocks`

## 产品约束

- 无无限滚动
- 无社交 feed
- 无评论、点赞、推荐算法
- 每日 brief 最多 20 条
- 每条包含 `title`、`summary`、`why_it_matters`、`relevance_to_me`、`sources`、`tag`、`importance_score`
