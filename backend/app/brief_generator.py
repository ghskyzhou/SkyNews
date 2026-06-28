from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import Settings
from .models import Brief, BriefItem, LocalizedText, RubySegment, Source, TagConfig

TAVILY_SEARCH_URL = "https://api.tavily.com/search"

SYSTEM_INSTRUCTIONS = """You are SkyNews, a personal daily briefing assistant.
Your job is to help the user avoid doomscrolling by producing a small, high-signal brief.
Prefer concrete, recent, useful information over sensational or repetitive coverage.
Skip rumors, outrage bait, duplicate stories, and items with weak sourcing.
Use only the provided Tavily search results. Do not invent source URLs.
Return valid JSON only."""


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ruby(text: str, rt: str = "", kind: str = "plain") -> RubySegment:
    return RubySegment(text=text, rt=rt, kind=kind)


MOCK_RUBY_TERMS: dict[str, tuple[str, str]] = {
    "コーディング": ("coding", "loanword"),
    "ツール": ("tool", "loanword"),
    "レビュー": ("review", "loanword"),
    "ワークフロー": ("workflow", "loanword"),
    "モック": ("mock", "loanword"),
    "ブリーフ": ("brief", "loanword"),
    "キー": ("key", "loanword"),
    "ライブ": ("live", "loanword"),
    "データ": ("data", "loanword"),
    "ビザ": ("visa", "loanword"),
    "マーケット": ("market", "loanword"),
    "フィード": ("feed", "loanword"),
    "ページ": ("page", "loanword"),
    "タグ": ("tag", "loanword"),
    "アプリ": ("app", "loanword"),
    "スクロール": ("scroll", "loanword"),
    "サービス": ("service", "loanword"),
    "モード": ("mode", "loanword"),
    "クレジット": ("credit", "loanword"),
    "バブル": ("bubble", "loanword"),
    "リスク": ("risk", "loanword"),
    "使わず": ("つかわず", "kanji"),
    "使えます": ("つかえます", "kanji"),
    "示して": ("しめして", "kanji"),
    "処理": ("しょり", "kanji"),
    "三言語": ("さんげんご", "kanji"),
    "作ります": ("つくります", "kanji"),
    "有料": ("ゆうりょう", "kanji"),
    "接続": ("せつぞく", "kanji"),
    "前": ("まえ", "kanji"),
    "依存": ("いぞん", "kanji"),
    "調整": ("ちょうせい", "kanji"),
    "上限付き": ("じょうげんつき", "kanji"),
    "上限": ("じょうげん", "kanji"),
    "日次": ("にちじ", "kanji"),
    "再生成": ("さいせいせい", "kanji"),
    "現在": ("げんざい", "kanji"),
    "模擬": ("もぎ", "kanji"),
    "形式": ("けいしき", "kanji"),
    "構造": ("こうぞう", "kanji"),
    "実際": ("じっさい", "kanji"),
    "検索": ("けんさく", "kanji"),
    "翻訳": ("ほんやく", "kanji"),
    "生成": ("せいせい", "kanji"),
    "要約": ("ようやく", "kanji"),
    "使用": ("しよう", "kanji"),
    "確認": ("かくにん", "kanji"),
    "追加": ("ついか", "kanji"),
    "有効": ("ゆうこう", "kanji"),
    "情報": ("じょうほう", "kanji"),
    "重要": ("じゅうよう", "kanji"),
    "関連": ("かんれん", "kanji"),
    "日本": ("にほん", "kanji"),
    "東京": ("とうきょう", "kanji"),
    "計画": ("けいかく", "kanji"),
    "落ち着いた": ("おちついた", "kanji"),
    "公式": ("こうしき", "kanji"),
    "優先": ("ゆうせん", "kanji"),
    "実用": ("じつよう", "kanji"),
    "向いて": ("むいて", "kanji"),
    "版": ("ばん", "kanji"),
    "曖昧": ("あいまい", "kanji"),
    "移住談": ("いじゅうだん", "kanji"),
    "移住": ("いじゅう", "kanji"),
    "報道": ("ほうどう", "kanji"),
    "細部": ("さいぶ", "kanji"),
    "詳細": ("しょうさい", "kanji"),
    "時期": ("じき", "kanji"),
    "時間": ("じかん", "kanji"),
    "資格": ("しかく", "kanji"),
    "現実": ("げんじつ", "kanji"),
    "働き方": ("はたらきかた", "kanji"),
    "影響": ("えいきょう", "kanji"),
    "仕事": ("しごと", "kanji"),
    "方法": ("ほうほう", "kanji"),
    "終わり": ("おわり", "kanji"),
    "収集": ("しゅうしゅう", "kanji"),
    "市場": ("しじょう", "kanji"),
    "投資": ("とうし", "kanji"),
    "事実": ("じじつ", "kanji"),
    "話題": ("わだい", "kanji"),
    "漠然": ("ばくぜん", "kanji"),
    "論": ("ろん", "kanji"),
    "決算": ("けっさん", "kanji"),
    "支出": ("ししゅつ", "kanji"),
    "過熱": ("かねつ", "kanji"),
    "財務": ("ざいむ", "kanji"),
    "設備": ("せつび", "kanji"),
    "評価": ("ひょうか", "kanji"),
    "指数": ("しすう", "kanji"),
    "変化": ("へんか", "kanji"),
    "認識": ("にんしき", "kanji"),
    "一部": ("いちぶ", "kanji"),
    "大型株": ("おおがたかぶ", "kanji"),
    "大きく": ("おおきく", "kanji"),
    "下部": ("かぶ", "kanji"),
    "欄": ("らん", "kanji"),
    "簡単": ("かんたん", "kanji"),
    "株価": ("かぶか", "kanji"),
    "毎日": ("まいにち", "kanji"),
    "研究": ("けんきゅう", "kanji"),
    "項目": ("こうもく", "kanji"),
    "価値": ("かち", "kanji"),
    "選ぶ": ("えらぶ", "kanji"),
    "新しさ": ("あたらしさ", "kanji"),
    "手がかり": ("てがかり", "kanji"),
    "保ち": ("たもち", "kanji"),
    "付ける": ("つける", "kanji"),
    "設計": ("せっけい", "kanji"),
    "論文": ("ろんぶん", "kanji"),
    "発表": ("はっぴょう", "kanji"),
    "読書": ("どくしょ", "kanji"),
    "読む": ("よむ", "kanji"),
    "意図": ("いと", "kanji"),
    "支える": ("ささえる", "kanji"),
    "支えます": ("ささえます", "kanji"),
    "有限": ("ゆうげん", "kanji"),
    "出典": ("しゅってん", "kanji"),
    "判断": ("はんだん", "kanji"),
    "深く": ("ふかく", "kanji"),
    "流し見": ("ながしみ", "kanji"),
    "読むべき": ("よむべき", "kanji"),
    "見る": ("みる", "kanji"),
    "見ます": ("みます", "kanji"),
    "分ける": ("わける", "kanji"),
    "的": ("てき", "kanji"),
    "動き": ("うごき", "kanji"),
    "左右": ("さゆう", "kanji"),
    "可能性": ("かのうせい", "kanji"),
}


MOCK_RUBY_KEYS = sorted(MOCK_RUBY_TERMS, key=len, reverse=True)


def _mock_ruby_from_text(text: str) -> list[RubySegment]:
    segments: list[RubySegment] = []
    plain_buffer: list[str] = []
    index = 0

    def flush_plain() -> None:
        if plain_buffer:
            segments.append(_ruby("".join(plain_buffer)))
            plain_buffer.clear()

    while index < len(text):
        match = next((key for key in MOCK_RUBY_KEYS if text.startswith(key, index)), None)
        if match:
            flush_plain()
            rt, kind = MOCK_RUBY_TERMS[match]
            segments.append(_ruby(match, rt, kind))
            index += len(match)
            continue
        plain_buffer.append(text[index])
        index += 1

    flush_plain()
    return segments


def _localized(
    en: str,
    zh: str | None = None,
    ja: str | None = None,
    ja_ruby: list[RubySegment | dict[str, str]] | None = None,
) -> LocalizedText:
    ja_text = ja or en
    return LocalizedText(
        en=en,
        zh=zh or en,
        ja=ja_text,
        ja_ruby=ja_ruby or _mock_ruby_from_text(ja_text),
    )


def _publisher_from_url(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "")
    return host or "Source"


def _parse_json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "DeepSeek returned incomplete JSON. This usually means the multilingual ruby output was too long. "
            "Try lowering DEEPSEEK_MAX_BRIEF_ITEMS or increasing DEEPSEEK_MAX_TOKENS."
        ) from exc


def _normalize_payload(
    payload: dict[str, Any],
    *,
    target_date: date,
    generated_at: str,
    max_items: int,
    mode: str,
    model: str,
) -> Brief:
    payload["date"] = target_date.isoformat()
    payload["generated_at"] = payload.get("generated_at") or generated_at
    payload["mode"] = mode
    payload["model"] = model
    payload["headline"] = payload.get("headline") or "SkyNews brief is ready."
    payload["items"] = payload.get("items", [])[:max_items]

    for item in payload["items"]:
        item["importance_score"] = max(1, min(5, int(item.get("importance_score", 1))))
        item["sources"] = item.get("sources") or [
            {
                "title": "Source unavailable",
                "url": "https://example.com",
                "publisher": "",
                "published_at": "",
            }
        ]

    return Brief.model_validate(payload)


def _mock_items(tags: list[TagConfig], max_items: int) -> list[BriefItem]:
    examples = [
        (
            "AI Coding",
            _localized(
                "AI coding tools are moving toward review-and-repair workflows",
                "AI 编程工具正在转向审查与修复工作流",
                "AI コーディングツールはレビューと修正のワークフローへ移行しています",
                [
                    _ruby("AI ", kind="plain"),
                    _ruby("コーディング", "coding", "loanword"),
                    _ruby("ツール", "tool", "loanword"),
                    _ruby("は", kind="plain"),
                    _ruby("レビュー", "review", "loanword"),
                    _ruby("と", kind="plain"),
                    _ruby("修正", "しゅうせい", "kanji"),
                    _ruby("の", kind="plain"),
                    _ruby("ワークフロー", "workflow", "loanword"),
                    _ruby("へ", kind="plain"),
                    _ruby("移行", "いこう", "kanji"),
                    _ruby("しています", kind="plain"),
                ],
            ),
            _localized(
                "Mock mode is active, so this item shows the intended shape without spending API credits. The real path will use Tavily for search and DeepSeek for multilingual summarization.",
                "当前是 mock 模式，所以这条内容只展示数据结构，不消耗 API 额度。真实路径会用 Tavily 搜索，再用 DeepSeek 生成三语摘要。",
                "現在はモックモードのため、API クレジットを使わずにデータ形式だけを示しています。実際の処理では Tavily で検索し、DeepSeek で三言語の要約を作ります。",
            ),
            _localized(
                "It validates that the no-doomscrolling brief format works before connecting paid services.",
                "它先验证了非信息流式简报格式，之后再接入付费服务会更稳。",
                "有料サービスを接続する前に、スクロール依存にならないブリーフ形式を確認できます。",
            ),
            _localized(
                "You can tune the AI Coding tag in topics.json and regenerate one bounded daily brief.",
                "你可以在 topics.json 里调整 AI Coding 标签，然后重新生成一份有上限的每日简报。",
                "topics.json で AI Coding タグを調整し、上限付きの日次ブリーフを再生成できます。",
            ),
            4,
        ),
        (
            "Japan / Tokyo / Visa",
            _localized(
                "Japan and Tokyo planning belongs in a slow, practical brief",
                "日本和东京规划更适合放进慢速、实用的简报",
                "日本と東京の計画は、落ち着いた実用的なブリーフに向いています",
            ),
            _localized(
                "The live version should prioritize official visa pages and practical reporting over vague relocation chatter.",
                "真实版本会优先读取官方签证页面和实用报道，而不是泛泛的搬家讨论。",
                "ライブ版では、曖昧な移住談よりも公式ビザ情報と実用的な報道を優先します。",
            ),
            _localized(
                "Visa details affect timing, eligibility, and the kind of work arrangement that is realistic.",
                "签证细节会影响时间安排、资格判断，以及现实可行的工作方式。",
                "ビザの詳細は、時期、資格、現実的な働き方に影響します。",
            ),
            _localized(
                "This keeps relocation research useful without turning it into an endless search session.",
                "这样可以让搬迁研究保持有用，而不是变成无止境搜索。",
                "これにより、移住リサーチを終わりのない検索ではなく実用的な情報収集にできます。",
            ),
            3,
        ),
        (
            "US Markets / AI Bubble",
            _localized(
                "Market tracking should separate AI spending facts from hype",
                "市场跟踪应该把 AI 支出事实和炒作分开",
                "市場チェックでは、AI 投資の事実と過熱した話題を分けるべきです",
            ),
            _localized(
                "The live brief will look for earnings, capex, and valuation data instead of repeating broad bubble claims.",
                "真实简报会关注财报、资本开支和估值数据，而不是重复宽泛的泡沫说法。",
                "ライブブリーフでは、漠然としたバブル論ではなく、決算、設備投資、バリュエーションのデータを見ます。",
            ),
            _localized(
                "A few large AI-linked stocks can dominate index moves and risk perception.",
                "少数 AI 相关大盘股可能主导指数表现和风险感知。",
                "一部の AI 関連大型株が指数の動きとリスク認識を大きく左右する可能性があります。",
            ),
            _localized(
                "The bottom stock strip now gives a quick daily check without creating a market feed.",
                "底部股票区会提供快速每日检查，但不会做成市场信息流。",
                "下部の株価欄は、市場フィードにせず毎日の簡単な確認に使えます。",
            ),
            4,
        ),
        (
            "CS / Research",
            _localized(
                "Research items should be selected for reading value, not novelty alone",
                "研究条目应该按阅读价值筛选，而不是只看新鲜感",
                "研究項目は新しさだけでなく、読む価値で選ぶべきです",
            ),
            _localized(
                "The app is set up to keep research leads finite and source-backed.",
                "这个应用会把研究线索控制在有限数量，并保留来源。",
                "このアプリは、研究の手がかりを有限に保ち、出典を付けるように設計されています。",
            ),
            _localized(
                "A bounded brief makes it easier to decide what deserves deeper attention.",
                "有边界的简报更容易帮你判断哪些内容值得深入读。",
                "上限のあるブリーフは、深く読むべきものを判断しやすくします。",
            ),
            _localized(
                "This supports deliberate reading instead of paper-announcement scrolling.",
                "这支持有意识地阅读，而不是刷论文发布消息。",
                "論文発表を流し見するのではなく、意図的な読書を支えます。",
            ),
            3,
        ),
    ]

    items: list[BriefItem] = []
    tag_names = [tag.name for tag in tags]
    for tag_name, title, summary, why, relevance, score in examples:
        if tag_name not in tag_names:
            continue
        items.append(
            BriefItem(
                title=title,
                summary=summary,
                why_it_matters=why,
                relevance_to_me=relevance,
                tag=tag_name,
                importance_score=score,
                sources=[
                    Source(
                        title="Mock source for local development",
                        url="https://example.com/skynews/mock",
                        publisher="SkyNews Mock",
                        published_at="",
                    )
                ],
            )
        )
        if len(items) >= max_items:
            break

    return items


class BriefGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, tags: list[TagConfig], max_items: int, target_date: date | None = None) -> Brief:
        today = target_date or date.today()
        capped_max_items = min(max_items, 20)
        if self.settings.use_mock:
            return self._generate_mock(tags, capped_max_items, today)
        return self._generate_with_tavily(tags, capped_max_items, today)

    def _generate_mock(self, tags: list[TagConfig], max_items: int, target_date: date) -> Brief:
        return Brief(
            date=target_date.isoformat(),
            generated_at=_utc_timestamp(),
            mode="mock",
            model="mock",
            headline=_localized(
                "Mock brief is ready; add Tavily and DeepSeek keys to enable live search and translation.",
                "Mock 简报已生成；添加 Tavily 和 DeepSeek key 后即可启用实时搜索和翻译。",
                "モックブリーフができました。Tavily と DeepSeek のキーを追加すると、ライブ検索と翻訳が有効になります。",
                [
                    _ruby("モック", "mock", "loanword"),
                    _ruby("ブリーフ", "brief", "loanword"),
                    _ruby("ができました。Tavily と DeepSeek の", kind="plain"),
                    _ruby("キー", "key", "loanword"),
                    _ruby("を", kind="plain"),
                    _ruby("追加", "ついか", "kanji"),
                    _ruby("すると、", kind="plain"),
                    _ruby("ライブ", "live", "loanword"),
                    _ruby("検索", "けんさく", "kanji"),
                    _ruby("と", kind="plain"),
                    _ruby("翻訳", "ほんやく", "kanji"),
                    _ruby("が", kind="plain"),
                    _ruby("有効", "ゆうこう", "kanji"),
                    _ruby("になります。", kind="plain"),
                ],
            ),
            items=_mock_items(tags, max_items),
        )

    def _generate_with_tavily(self, tags: list[TagConfig], max_items: int, target_date: date) -> Brief:
        generated_at = _utc_timestamp()
        search_results = self._search_tags(tags)
        if not search_results:
            return self._generate_mock(tags, max_items, target_date)

        if not self.settings.deepseek_api_key:
            return self._generate_from_search_results(search_results, max_items, target_date, generated_at)

        ai_max_items = max(1, min(max_items, self.settings.deepseek_max_brief_items, len(search_results)))
        payload = self._ask_deepseek(
            search_results[:ai_max_items],
            tags,
            ai_max_items,
            target_date,
            generated_at,
        )
        return _normalize_payload(
            payload,
            target_date=target_date,
            generated_at=generated_at,
            max_items=ai_max_items,
            mode="tavily+deepseek",
            model=self.settings.deepseek_model,
        )

    def _search_tags(self, tags: list[TagConfig]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        timeout = httpx.Timeout(self.settings.api_timeout_seconds)
        headers = {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=timeout) as client:
            for tag in tags:
                queries = tag.queries or [tag.name]
                for query in queries[: max(1, self.settings.tavily_max_queries_per_tag)]:
                    response = client.post(
                        TAVILY_SEARCH_URL,
                        headers=headers,
                        json={
                            "query": query,
                            "search_depth": self.settings.tavily_search_depth,
                            "max_results": max(1, self.settings.tavily_max_results_per_query),
                            "include_answer": False,
                            "include_raw_content": False,
                            "include_images": False,
                            "time_range": "week",
                        },
                    )
                    if response.status_code >= 400:
                        raise RuntimeError(f"Tavily search failed for '{tag.name}': {response.text[:240]}")
                    payload = response.json()
                    for result in payload.get("results", []):
                        url = str(result.get("url") or "").strip()
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        rows.append(
                            {
                                "tag": tag.name,
                                "tag_description": tag.description,
                                "personal_context": tag.personal_context,
                                "title": str(result.get("title") or "Untitled"),
                                "url": url,
                                "publisher": _publisher_from_url(url),
                                "published_at": str(result.get("published_date") or result.get("date") or ""),
                                "content": str(result.get("content") or "")[:900],
                                "score": result.get("score"),
                            }
                        )
        return rows

    def _ask_deepseek(
        self,
        search_results: list[dict[str, Any]],
        tags: list[TagConfig],
        max_items: int,
        target_date: date,
        generated_at: str,
    ) -> dict[str, Any]:
        tag_names = [tag.name for tag in tags]
        user_prompt = {
            "task": "Create a SkyNews daily brief as valid JSON.",
            "date": target_date.isoformat(),
            "generated_at": generated_at,
            "max_items": max_items,
            "allowed_tags": tag_names,
            "language_requirements": {
                "en": "natural English",
                "zh": "natural Simplified Chinese",
                "ja": "natural Japanese",
            },
            "japanese_ruby_requirements": [
                "Every localized text object must include en, zh, ja, and ja_ruby.",
                "ja must be plain Japanese text without HTML.",
                "ja_ruby must be an array of segments that recreates the ja text in order.",
                "For every segment containing kanji, set rt to the correct hiragana reading in context. Use kun-yomi or on-yomi correctly based on the sentence.",
                "For katakana loanwords or common tech terms, set rt to a short English gloss such as coding, review, workflow, API, search, or market.",
                "For plain kana, punctuation, spaces, numbers, and Latin ticker symbols, use kind='plain' and rt=''.",
                "Allowed segment shape: {'text': string, 'rt': string, 'kind': 'plain' | 'kanji' | 'loanword' | 'term'}.",
                "Do not use HTML, markdown, or parentheses for furigana.",
            ],
            "required_shape": {
                "date": "YYYY-MM-DD",
                "generated_at": "UTC ISO timestamp",
                "headline": {
                    "en": "",
                    "zh": "",
                    "ja": "",
                    "ja_ruby": [{"text": "", "rt": "", "kind": "plain"}],
                },
                "items": [
                    {
                        "title": {
                            "en": "",
                            "zh": "",
                            "ja": "",
                            "ja_ruby": [{"text": "", "rt": "", "kind": "plain"}],
                        },
                        "summary": {
                            "en": "",
                            "zh": "",
                            "ja": "",
                            "ja_ruby": [{"text": "", "rt": "", "kind": "plain"}],
                        },
                        "why_it_matters": {
                            "en": "",
                            "zh": "",
                            "ja": "",
                            "ja_ruby": [{"text": "", "rt": "", "kind": "plain"}],
                        },
                        "relevance_to_me": {
                            "en": "",
                            "zh": "",
                            "ja": "",
                            "ja_ruby": [{"text": "", "rt": "", "kind": "plain"}],
                        },
                        "sources": [
                            {
                                "title": "",
                                "url": "",
                                "publisher": "",
                                "published_at": "",
                            }
                        ],
                        "tag": "one allowed tag",
                        "importance_score": "integer 1-5",
                    }
                ],
            },
            "rules": [
                "Use only source URLs from search_results.",
                f"Return no more than {max_items} items.",
                "Prefer primary sources, reputable reporting, official pages, papers, and data.",
                "Avoid duplicate, sensational, vague, or low-value stories.",
                "Keep each title, summary, why_it_matters, and relevance_to_me concise.",
                "Each English text should usually be one sentence.",
                "Each Chinese text should usually be under 80 Chinese characters.",
                "Each Japanese text should usually be under 100 Japanese characters.",
                "Return JSON only. No markdown fences.",
            ],
            "search_results": search_results,
        }

        response = httpx.post(
            f"{self.settings.deepseek_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.settings.api_timeout_seconds),
            json={
                "model": self.settings.deepseek_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
                ],
                "temperature": 0.2,
                "max_tokens": self.settings.deepseek_max_tokens,
                "response_format": {"type": "json_object"},
                "stream": False,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"DeepSeek brief generation failed: {response.text[:240]}")

        data = response.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]
        if choice.get("finish_reason") == "length":
            raise RuntimeError(
                "DeepSeek response was truncated because the output was too long. "
                "Lower DEEPSEEK_MAX_BRIEF_ITEMS or increase DEEPSEEK_MAX_TOKENS."
            )
        return _parse_json_payload(content)

    def _generate_from_search_results(
        self,
        search_results: list[dict[str, Any]],
        max_items: int,
        target_date: date,
        generated_at: str,
    ) -> Brief:
        items: list[BriefItem] = []
        for result in search_results[:max_items]:
            title = result["title"]
            content = result["content"] or "No snippet was returned by Tavily for this result."
            tag = result["tag"]
            items.append(
                BriefItem(
                    title=_localized(title),
                    summary=_localized(content[:420]),
                    why_it_matters=_localized(
                        "This result matched one of your configured topics. Add DEEPSEEK_API_KEY to get filtered multilingual synthesis.",
                    ),
                    relevance_to_me=_localized(result["personal_context"]),
                    sources=[
                        Source(
                            title=title,
                            url=result["url"],
                            publisher=result["publisher"],
                            published_at=result["published_at"],
                        )
                    ],
                    tag=tag,
                    importance_score=2,
                )
            )

        return Brief(
            date=target_date.isoformat(),
            generated_at=generated_at,
            mode="tavily-only",
            model="none",
            headline=_localized(
                "Tavily results are ready; add DeepSeek to enable Chinese, English, and Japanese synthesis.",
                "Tavily 结果已生成；添加 DeepSeek 后可启用中英日三语整理。",
                "Tavily の結果が準備できました。DeepSeek を追加すると、中国語・英語・日本語の整理が有効になります。",
            ),
            items=items,
        )
