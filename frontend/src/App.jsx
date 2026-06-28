import { useEffect, useMemo, useState } from "react";
import {
  Archive,
  CalendarDays,
  ExternalLink,
  Languages,
  LineChart,
  Loader2,
  Minus,
  Moon,
  Newspaper,
  RefreshCw,
  Sun,
  Tags,
  TrendingDown,
  TrendingUp
} from "lucide-react";
import { api } from "./api";

const LANGUAGE_OPTIONS = [
  { id: "zh", label: "中文", locale: "zh-CN" },
  { id: "en", label: "English", locale: "en-US" },
  { id: "ja", label: "日本語", locale: "ja-JP" }
];

const UI_TEXT = {
  zh: {
    today: "今日",
    archive: "归档",
    generate: "生成",
    noBrief: "今天还没有简报",
    noBriefCopy: "生成一份聚焦的每日简报。没有 Tavily key 时会自动使用本地 mock。",
    summary: "摘要",
    why: "为什么重要",
    relevance: "与你的相关性",
    archiveEmpty: "归档为空",
    archiveEmptyCopy: "生成一份简报后，它会出现在这里。",
    dailyBrief: "每日简报，不是信息流",
    items: "条简报",
    trackedTags: "追踪标签",
    tags: "标签",
    market: "每日行情",
    marketSource: "来源",
    unavailable: "暂无数据"
  },
  en: {
    today: "Today",
    archive: "Archive",
    generate: "Generate",
    noBrief: "No brief for today yet",
    noBriefCopy: "Generate one focused daily brief. Local mock mode works when no Tavily key is set.",
    summary: "Summary",
    why: "Why it matters",
    relevance: "Relevance to me",
    archiveEmpty: "Archive is empty",
    archiveEmptyCopy: "Generate a brief and it will appear here.",
    dailyBrief: "Daily briefing, not a feed",
    items: "brief items",
    trackedTags: "tracked tags",
    tags: "Tags",
    market: "Daily market",
    marketSource: "Source",
    unavailable: "Unavailable"
  },
  ja: {
    today: "今日",
    archive: "アーカイブ",
    generate: "生成",
    noBrief: "今日のブリーフはまだありません",
    noBriefCopy: "集中した日次ブリーフを生成します。Tavily キーがない場合はローカルモックを使います。",
    summary: "要約",
    why: "重要な理由",
    relevance: "自分との関連性",
    archiveEmpty: "アーカイブは空です",
    archiveEmptyCopy: "ブリーフを生成するとここに表示されます。",
    dailyBrief: "日次ブリーフ、フィードではありません",
    items: "件のブリーフ",
    trackedTags: "追跡タグ",
    tags: "タグ",
    market: "日次マーケット",
    marketSource: "出典",
    unavailable: "データなし"
  }
};

function localDateKey() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function formatDate(value, locale) {
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(`${value}T00:00:00`));
}

function textOf(value, language) {
  if (!value) return "";
  if (typeof value === "string") return value;
  return value[language] || value.en || value.zh || value.ja || "";
}

function hasRuby(value) {
  return value && typeof value === "object" && Array.isArray(value.ja_ruby) && value.ja_ruby.length > 0;
}

function LocalizedText({ value, language, as: Component = "span", className = "" }) {
  if (language === "ja" && hasRuby(value)) {
    return (
      <Component className={className}>
        {value.ja_ruby.map((segment, index) => {
          const key = `${segment.text}-${segment.rt}-${index}`;
          if (!segment.rt) {
            return <span key={key}>{segment.text}</span>;
          }
          return (
            <ruby key={key} className={`ruby-segment ruby-${segment.kind || "plain"}`}>
              {segment.text}
              <rt>{segment.rt}</rt>
            </ruby>
          );
        })}
      </Component>
    );
  }

  return <Component className={className}>{textOf(value, language)}</Component>;
}

function formatPrice(value) {
  if (value === null || value === undefined) return "--";
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(value);
}

function formatSigned(value, suffix = "") {
  if (value === null || value === undefined) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}${suffix}`;
}

function scoreTone(score) {
  if (score >= 5) return "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950 dark:text-rose-200 dark:ring-rose-800";
  if (score >= 4) return "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950 dark:text-amber-200 dark:ring-amber-800";
  return "bg-teal-50 text-teal-700 ring-teal-200 dark:bg-teal-950 dark:text-teal-200 dark:ring-teal-800";
}

function LanguageSelector({ language, setLanguage, className = "" }) {
  return (
    <div className={`items-center gap-1 rounded-lg border border-stone-200 bg-white p-1 dark:border-zinc-800 dark:bg-zinc-950 ${className}`}>
      <Languages size={16} className="ml-2 shrink-0 text-zinc-500" />
      {LANGUAGE_OPTIONS.map((option) => (
        <button
          key={option.id}
          className={`h-8 flex-1 rounded-lg px-2 text-xs font-semibold transition ${
            language === option.id
              ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950"
              : "text-zinc-600 hover:bg-stone-100 dark:text-zinc-300 dark:hover:bg-zinc-900"
          }`}
          onClick={() => setLanguage(option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function EmptyState({ onGenerate, generating, labels }) {
  return (
    <section className="panel p-8 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
        <Newspaper size={24} />
      </div>
      <h2 className="mt-4 text-xl font-semibold text-zinc-950 dark:text-white">{labels.noBrief}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
        {labels.noBriefCopy}
      </p>
      <button className="primary-button mt-5" onClick={onGenerate} disabled={generating}>
        {generating ? <Loader2 className="animate-spin" size={17} /> : <RefreshCw size={17} />}
        {labels.generate}
      </button>
    </section>
  );
}

function BriefCard({ item, language, labels }) {
  return (
    <article className="panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-lg border border-stone-200 px-2 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:text-zinc-300">
              {item.tag}
            </span>
            <span className={`rounded-lg px-2 py-1 text-xs font-semibold ring-1 ${scoreTone(item.importance_score)}`}>
              {item.importance_score}/5
            </span>
          </div>
          <LocalizedText
            as="h3"
            value={item.title}
            language={language}
            className="mt-3 text-lg font-semibold leading-8 text-zinc-950 dark:text-white"
          />
        </div>
      </div>

      <div className="mt-4 grid gap-4 text-sm leading-6 text-zinc-700 dark:text-zinc-300 md:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-500">{labels.summary}</p>
          <LocalizedText as="p" value={item.summary} language={language} className="mt-1" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-500">{labels.why}</p>
          <LocalizedText as="p" value={item.why_it_matters} language={language} className="mt-1" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-500">{labels.relevance}</p>
          <LocalizedText as="p" value={item.relevance_to_me} language={language} className="mt-1" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {item.sources.map((source, index) => (
          <a
            key={`${source.url}-${index}`}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex max-w-full items-center gap-1 rounded-lg border border-stone-200 px-2.5 py-1.5 text-xs font-medium text-zinc-600 transition hover:border-teal-300 hover:text-teal-700 dark:border-zinc-800 dark:text-zinc-300 dark:hover:border-teal-700 dark:hover:text-teal-300"
            title={source.title}
          >
            <ExternalLink size={13} />
            <span className="truncate">{source.publisher || source.title || "Source"}</span>
          </a>
        ))}
      </div>
    </article>
  );
}

function TagList({ tags, labels }) {
  return (
    <section className="panel p-5">
      <div className="flex items-center gap-2">
        <Tags size={18} className="text-teal-700 dark:text-teal-300" />
        <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">{labels.tags}</h2>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {tags.map((tag) => (
          <div key={tag.name} className="rounded-lg border border-stone-200 p-3 dark:border-zinc-800">
            <p className="text-sm font-semibold text-zinc-950 dark:text-white">{tag.name}</p>
            <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">{tag.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ArchiveView({ archive, onSelect, language, labels, locale }) {
  if (!archive.length) {
    return (
      <section className="panel p-8 text-center">
        <Archive className="mx-auto text-zinc-400" size={28} />
        <h2 className="mt-3 text-lg font-semibold text-zinc-950 dark:text-white">{labels.archiveEmpty}</h2>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{labels.archiveEmptyCopy}</p>
      </section>
    );
  }

  return (
    <section className="grid gap-3">
      {archive.map((entry) => (
        <button
          key={entry.date}
          onClick={() => onSelect(entry.date)}
          className="panel block p-5 text-left transition hover:border-teal-300 dark:hover:border-teal-700"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-zinc-950 dark:text-white">{formatDate(entry.date, locale)}</p>
              <LocalizedText
                as="p"
                value={entry.headline}
                language={language}
                className="mt-1 text-sm text-zinc-600 dark:text-zinc-400"
              />
            </div>
            <div className="flex items-center gap-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
              <span className="rounded-lg border border-stone-200 px-2 py-1 dark:border-zinc-800">{entry.item_count} items</span>
              <span className="rounded-lg border border-stone-200 px-2 py-1 dark:border-zinc-800">{entry.mode}</span>
            </div>
          </div>
        </button>
      ))}
    </section>
  );
}

function StockStrip({ stocks, labels }) {
  const quotes = stocks?.quotes || [];
  if (!quotes.length) return null;

  return (
    <section className="mx-auto max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
      <div className="panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <LineChart size={18} className="text-teal-700 dark:text-teal-300" />
            <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">{labels.market}</h2>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {labels.marketSource}: {stocks.source}
          </p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {quotes.map((quote) => {
            const positive = (quote.change || 0) > 0;
            const negative = (quote.change || 0) < 0;
            const tone = positive
              ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"
              : negative
                ? "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200"
                : "border-stone-200 bg-stone-50 text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300";
            return (
              <div key={quote.symbol} className="rounded-lg border border-stone-200 p-3 dark:border-zinc-800">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-bold text-zinc-950 dark:text-white">{quote.symbol}</p>
                  <span className={`inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs font-semibold ${tone}`}>
                    {positive ? <TrendingUp size={13} /> : negative ? <TrendingDown size={13} /> : <Minus size={13} />}
                    {formatSigned(quote.change_percent, "%")}
                  </span>
                </div>
                <p className="mt-3 text-xl font-bold text-zinc-950 dark:text-white">{formatPrice(quote.price)}</p>
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                  {quote.status === "ok" ? `${formatSigned(quote.change)} · ${quote.date}` : labels.unavailable}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [view, setView] = useState("home");
  const [tagsConfig, setTagsConfig] = useState({ tags: [], max_items_per_brief: 20 });
  const [brief, setBrief] = useState(null);
  const [archive, setArchive] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("skynews-theme") === "dark");
  const [language, setLanguage] = useState(() => localStorage.getItem("skynews-language") || "zh");
  const [stocks, setStocks] = useState(null);
  const today = useMemo(() => localDateKey(), []);
  const labels = UI_TEXT[language] || UI_TEXT.zh;
  const locale = LANGUAGE_OPTIONS.find((option) => option.id === language)?.locale || "zh-CN";

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("skynews-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    localStorage.setItem("skynews-language", language);
  }, [language]);

  async function refreshArchive() {
    const entries = await api.getBriefs();
    setArchive(entries);
  }

  async function loadToday() {
    setLoading(true);
    setError("");
    try {
      const [tagPayload, entries] = await Promise.all([api.getTags(), api.getBriefs()]);
      setTagsConfig(tagPayload);
      setArchive(entries);
      try {
        const todaysBrief = await api.getBrief(today);
        setBrief(todaysBrief);
      } catch (briefError) {
        if (!briefError.message.includes("404")) {
          throw briefError;
        }
        setBrief(null);
      }
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadToday();
    api.getStocks().then(setStocks).catch(() => setStocks(null));
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setError("");
    try {
      const generated = await api.generateBrief();
      setBrief(generated);
      setView("home");
      await refreshArchive();
    } catch (generateError) {
      setError(generateError.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSelectArchive(date) {
    setLoading(true);
    setError("");
    try {
      const selected = await api.getBrief(date);
      setBrief(selected);
      setView("home");
    } catch (archiveError) {
      setError(archiveError.message);
    } finally {
      setLoading(false);
    }
  }

  const itemCount = brief?.items?.length || 0;

  return (
    <div className="min-h-screen bg-stone-100 text-zinc-950 transition dark:bg-zinc-950 dark:text-white">
      <header className="border-b border-stone-200 bg-stone-50/90 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/90">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-950 text-white dark:bg-white dark:text-zinc-950">
              <Newspaper size={21} />
            </div>
            <div>
              <h1 className="text-xl font-bold leading-6">SkyNews</h1>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">{labels.dailyBrief}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <LanguageSelector language={language} setLanguage={setLanguage} className="hidden sm:flex" />
            <button
              className={`tab-button ${view === "home" ? "tab-button-active" : ""}`}
              onClick={() => setView("home")}
            >
              <CalendarDays size={17} />
              {labels.today}
            </button>
            <button
              className={`tab-button ${view === "archive" ? "tab-button-active" : ""}`}
              onClick={() => setView("archive")}
            >
              <Archive size={17} />
              {labels.archive}
            </button>
            <button className="icon-button" onClick={() => setDarkMode((value) => !value)} title="Toggle theme">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="primary-button" onClick={handleGenerate} disabled={generating}>
              {generating ? <Loader2 className="animate-spin" size={17} /> : <RefreshCw size={17} />}
              {labels.generate}
            </button>
          </div>
        </div>
        <div className="mx-auto max-w-7xl px-4 pb-4 sm:hidden">
          <LanguageSelector language={language} setLanguage={setLanguage} className="flex w-full" />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_330px] lg:px-8">
        <section className="min-w-0">
          {error && (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
              {error}
            </div>
          )}

          {view === "archive" ? (
            <ArchiveView archive={archive} onSelect={handleSelectArchive} language={language} labels={labels} locale={locale} />
          ) : loading ? (
            <section className="panel flex min-h-64 items-center justify-center p-8">
              <Loader2 className="animate-spin text-teal-700 dark:text-teal-300" size={28} />
            </section>
          ) : brief ? (
            <div className="grid gap-4">
              <section className="panel p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{formatDate(brief.date, locale)}</p>
                    <LocalizedText
                      as="h2"
                      value={brief.headline}
                      language={language}
                      className="mt-2 text-2xl font-bold leading-9 text-zinc-950 dark:text-white"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                    <span className="rounded-lg border border-stone-200 px-2 py-1 dark:border-zinc-800">{itemCount}/20 items</span>
                    <span className="rounded-lg border border-stone-200 px-2 py-1 dark:border-zinc-800">{brief.mode}</span>
                    <span className="rounded-lg border border-stone-200 px-2 py-1 dark:border-zinc-800">{brief.model}</span>
                  </div>
                </div>
              </section>
              {brief.items.map((item, index) => (
                <BriefCard key={`${textOf(item.title, "en")}-${index}`} item={item} language={language} labels={labels} />
              ))}
            </div>
          ) : (
            <EmptyState onGenerate={handleGenerate} generating={generating} labels={labels} />
          )}
        </section>

        <aside className="grid h-fit gap-4">
          <section className="panel p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-500">Today</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <div>
                <p className="text-2xl font-bold text-zinc-950 dark:text-white">{itemCount}</p>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">{labels.items}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-zinc-950 dark:text-white">{tagsConfig.tags.length}</p>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">{labels.trackedTags}</p>
              </div>
            </div>
          </section>
          <TagList tags={tagsConfig.tags} labels={labels} />
        </aside>
      </main>
      <StockStrip stocks={stocks} labels={labels} />
    </div>
  );
}
