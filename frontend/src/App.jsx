import { useEffect, useMemo, useState } from "react";
import {
  Archive,
  CalendarDays,
  ExternalLink,
  Languages,
  LineChart,
  Loader2,
  LogOut,
  Minus,
  Moon,
  Newspaper,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Sun,
  Tags,
  Trash2,
  TrendingDown,
  TrendingUp,
  User,
  X
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
    login: "登录",
    logout: "退出",
    register: "注册",
    username: "账号",
    password: "密码",
    currentPassword: "当前密码",
    newPassword: "新密码",
    accountSettings: "账号设置",
    changePassword: "修改密码",
    changePasswordCopy: "输入当前密码后设置新密码。密码只保存加密 hash，不能找回明文。",
    generatingTitle: "正在生成中...",
    generatingCopy: "SkyNews 正在搜索、筛选并整理内容，请稍等。",
    tavilyCollected: "Tavily 已收集",
    tavilyQueries: "Tavily 查询",
    deepseekCandidates: "DeepSeek 候选",
    deepseekGenerated: "DeepSeek 已生成",
    savedItems: "已写入简报",
    emptyTagsHint: "可以在这里添加标签后生成内容哦。",
    phaseText: {
      starting: "准备生成",
      tavily: "正在搜索最近信息",
      deepseek: "正在总结与翻译",
      saving: "正在保存简报",
      mock: "正在生成本地示例",
      complete: "生成完成",
      error: "生成失败"
    },
    back: "返回",
    invite: "邀请码",
    signInTitle: "登录 SkyNews",
    registerTitle: "创建账号",
    signInCopy: "登录后可以编辑自己的标签，并生成只属于你的每日简报。",
    demoMode: "未登录时展示 Sky 的 demo 信息。",
    noBrief: "今天还没有简报",
    noBriefCopy: "登录后可以生成自己的每日简报。当前展示的是 Sky 的 demo。",
    archiveEmpty: "归档为空",
    archiveEmptyCopy: "生成一份简报后，它会出现在这里。",
    dailyBrief: "每日简报，不是信息流",
    items: "条简报",
    trackedTags: "追踪标签",
    tags: "标签",
    addTag: "添加标签",
    edit: "编辑",
    save: "保存",
    cancel: "取消",
    delete: "删除",
    tagTitle: "标签标题",
    tagDescription: "介绍",
    market: "每日行情",
    marketSource: "来源",
    unavailable: "暂无数据",
    demoUser: "未登录"
  },
  en: {
    today: "Today",
    archive: "Archive",
    generate: "Generate",
    login: "Login",
    logout: "Logout",
    register: "Register",
    username: "Username",
    password: "Password",
    currentPassword: "Current password",
    newPassword: "New password",
    accountSettings: "Account settings",
    changePassword: "Change password",
    changePasswordCopy: "Enter your current password, then set a new one. Passwords are stored as hashes only.",
    generatingTitle: "Generating...",
    generatingCopy: "SkyNews is searching, filtering, and organizing your brief. Please wait.",
    tavilyCollected: "Tavily collected",
    tavilyQueries: "Tavily queries",
    deepseekCandidates: "DeepSeek candidates",
    deepseekGenerated: "DeepSeek generated",
    savedItems: "Saved items",
    emptyTagsHint: "Add tags here before generating your brief.",
    phaseText: {
      starting: "Preparing",
      tavily: "Searching recent information",
      deepseek: "Summarizing and translating",
      saving: "Saving brief",
      mock: "Generating local sample",
      complete: "Complete",
      error: "Failed"
    },
    back: "Back",
    invite: "Invite code",
    signInTitle: "Login to SkyNews",
    registerTitle: "Create account",
    signInCopy: "Login to edit your own tags and generate a personal daily brief.",
    demoMode: "Logged-out visitors see Sky's demo brief.",
    noBrief: "No brief for today yet",
    noBriefCopy: "Login to generate your own daily brief. You are viewing Sky's demo.",
    archiveEmpty: "Archive is empty",
    archiveEmptyCopy: "Generate a brief and it will appear here.",
    dailyBrief: "Daily briefing, not a feed",
    items: "brief items",
    trackedTags: "tracked tags",
    tags: "Tags",
    addTag: "Add tag",
    edit: "Edit",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    tagTitle: "Tag title",
    tagDescription: "Description",
    market: "Daily market",
    marketSource: "Source",
    unavailable: "Unavailable",
    demoUser: "Not logged in"
  },
  ja: {
    today: "今日",
    archive: "アーカイブ",
    generate: "生成",
    login: "ログイン",
    logout: "ログアウト",
    register: "登録",
    username: "ユーザー名",
    password: "パスワード",
    currentPassword: "現在のパスワード",
    newPassword: "新しいパスワード",
    accountSettings: "アカウント設定",
    changePassword: "パスワード変更",
    changePasswordCopy: "現在のパスワードを入力して、新しいパスワードを設定します。パスワードは hash のみ保存されます。",
    generatingTitle: "生成中...",
    generatingCopy: "SkyNews が検索、選別、整理しています。少しお待ちください。",
    tavilyCollected: "Tavily 収集済み",
    tavilyQueries: "Tavily 検索",
    deepseekCandidates: "DeepSeek 候補",
    deepseekGenerated: "DeepSeek 生成済み",
    savedItems: "保存済み",
    emptyTagsHint: "ここでタグを追加すると、内容を生成できます。",
    phaseText: {
      starting: "準備中",
      tavily: "最近の情報を検索中",
      deepseek: "要約と翻訳中",
      saving: "ブリーフを保存中",
      mock: "ローカルサンプルを生成中",
      complete: "完了",
      error: "失敗"
    },
    back: "戻る",
    invite: "招待コード",
    signInTitle: "SkyNews にログイン",
    registerTitle: "アカウント作成",
    signInCopy: "ログインすると、自分のタグを編集し、自分用の日次ブリーフを生成できます。",
    demoMode: "未ログイン時は Sky のデモ情報を表示します。",
    noBrief: "今日のブリーフはまだありません",
    noBriefCopy: "ログインすると自分のブリーフを生成できます。現在は Sky のデモを表示しています。",
    archiveEmpty: "アーカイブは空です",
    archiveEmptyCopy: "ブリーフを生成するとここに表示されます。",
    dailyBrief: "日次ブリーフ、フィードではありません",
    items: "件のブリーフ",
    trackedTags: "追跡タグ",
    tags: "タグ",
    addTag: "タグ追加",
    edit: "編集",
    save: "保存",
    cancel: "取消",
    delete: "削除",
    tagTitle: "タグ名",
    tagDescription: "説明",
    market: "日次マーケット",
    marketSource: "出典",
    unavailable: "データなし",
    demoUser: "未ログイン"
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
          if (!segment.rt) return <span key={key}>{segment.text}</span>;
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

function ProgressStat({ label, value }) {
  return (
    <div className="rounded-lg border border-stone-200 px-3 py-2 dark:border-zinc-800">
      <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-1 text-sm font-bold text-zinc-950 dark:text-white">{value}</p>
    </div>
  );
}

function GenerationProgressModal({ progress, labels }) {
  const current = progress || {};
  const phaseText = labels.phaseText?.[current.phase] || labels.phaseText?.starting || "";
  const tavilyQueryText = `${current.tavily_queries_done || 0}/${current.tavily_queries_total || 0}`;

  return (
    <div className="fixed left-1/2 top-4 z-50 w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 rounded-lg border border-stone-200 bg-white/95 p-4 shadow-xl shadow-zinc-950/10 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/95">
      <div className="flex items-start gap-3">
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
          <Loader2 className="animate-spin" size={19} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-bold text-zinc-950 dark:text-white">{labels.generatingTitle}</h2>
            <span className="rounded-lg bg-stone-100 px-2 py-1 text-xs font-semibold text-zinc-600 dark:bg-zinc-900 dark:text-zinc-300">
              {phaseText}
            </span>
          </div>
          <p className="mt-1 text-xs leading-5 text-zinc-500 dark:text-zinc-400">{labels.generatingCopy}</p>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5">
            <ProgressStat label={labels.tavilyQueries} value={tavilyQueryText} />
            <ProgressStat label={labels.tavilyCollected} value={current.tavily_results || 0} />
            <ProgressStat label={labels.deepseekCandidates} value={current.deepseek_candidates || 0} />
            <ProgressStat label={labels.deepseekGenerated} value={current.deepseek_items || 0} />
            <ProgressStat label={labels.savedItems} value={current.final_items || 0} />
          </div>
        </div>
      </div>
    </div>
  );
}

function AuthView({ labels, onLogin, onRegister, error, loading }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", password: "", invite_code: "" });
  const isRegister = mode === "register";

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    if (isRegister) {
      onRegister(form);
    } else {
      onLogin({ username: form.username, password: form.password });
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-86px)] max-w-md items-center px-4 py-10">
      <section className="panel w-full p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-950 text-white dark:bg-white dark:text-zinc-950">
            <User size={19} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-zinc-950 dark:text-white">
              {isRegister ? labels.registerTitle : labels.signInTitle}
            </h2>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">{labels.signInCopy}</p>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
            {error}
          </div>
        )}

        <form className="mt-5 grid gap-3" onSubmit={submit}>
          <label className="grid gap-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            {labels.username}
            <input
              className="h-10 rounded-lg border border-stone-200 bg-white px-3 text-zinc-950 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
              value={form.username}
              onChange={(event) => updateField("username", event.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            {labels.password}
            <input
              type="password"
              className="h-10 rounded-lg border border-stone-200 bg-white px-3 text-zinc-950 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </label>
          {isRegister && (
            <label className="grid gap-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {labels.invite}
              <input
                className="h-10 rounded-lg border border-stone-200 bg-white px-3 text-zinc-950 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
                value={form.invite_code}
                onChange={(event) => updateField("invite_code", event.target.value)}
              />
            </label>
          )}
          <button className="primary-button mt-2 justify-center" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" size={17} /> : null}
            {isRegister ? labels.register : labels.login}
          </button>
        </form>

        <button
          className="mt-4 w-full rounded-lg px-3 py-2 text-sm font-semibold text-zinc-600 transition hover:bg-stone-100 dark:text-zinc-300 dark:hover:bg-zinc-900"
          onClick={() => setMode(isRegister ? "login" : "register")}
        >
          {isRegister ? labels.login : labels.register}
        </button>
      </section>
    </main>
  );
}

function PasswordView({ labels, onChangePassword, onBack, error, loading }) {
  const [form, setForm] = useState({ current_password: "", new_password: "" });

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onChangePassword(form);
  }

  return (
    <section className="panel mx-auto max-w-md p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-950 text-white dark:bg-white dark:text-zinc-950">
          <User size={19} />
        </div>
        <div>
          <h2 className="text-lg font-bold text-zinc-950 dark:text-white">{labels.changePassword}</h2>
          <p className="text-xs leading-5 text-zinc-500 dark:text-zinc-400">{labels.changePasswordCopy}</p>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          {error}
        </div>
      )}

      <form className="mt-5 grid gap-3" onSubmit={submit}>
        <label className="grid gap-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          {labels.currentPassword}
          <input
            type="password"
            className="h-10 rounded-lg border border-stone-200 bg-white px-3 text-zinc-950 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
            value={form.current_password}
            onChange={(event) => updateField("current_password", event.target.value)}
            autoComplete="current-password"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          {labels.newPassword}
          <input
            type="password"
            className="h-10 rounded-lg border border-stone-200 bg-white px-3 text-zinc-950 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
            value={form.new_password}
            onChange={(event) => updateField("new_password", event.target.value)}
            autoComplete="new-password"
          />
        </label>
        <div className="mt-2 flex gap-2">
          <button type="button" className="tab-button flex-1 justify-center" onClick={onBack}>
            {labels.back}
          </button>
          <button className="primary-button flex-1 justify-center" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" size={17} /> : <Save size={17} />}
            {labels.save}
          </button>
        </div>
      </form>
    </section>
  );
}

function EmptyState({ user, labels }) {
  return (
    <section className="panel p-8 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
        <Newspaper size={24} />
      </div>
      <h2 className="mt-4 text-xl font-semibold text-zinc-950 dark:text-white">{labels.noBrief}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
        {user?.is_authenticated ? labels.archiveEmptyCopy : labels.noBriefCopy}
      </p>
    </section>
  );
}

function BriefCard({ item, language }) {
  return (
    <article className="panel p-5">
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
      <p className="mt-3 text-sm leading-7 text-zinc-700 dark:text-zinc-300">
        <LocalizedText value={item.summary} language={language} />
        <span> </span>
        <LocalizedText value={item.why_it_matters} language={language} />
        <span> </span>
        <LocalizedText value={item.relevance_to_me} language={language} />
      </p>
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

function TagForm({ labels, initialValue, onSave, onCancel, saving }) {
  const [draft, setDraft] = useState(initialValue || { name: "", description: "" });
  return (
    <div className="rounded-lg border border-stone-200 p-3 dark:border-zinc-800">
      <input
        className="h-9 w-full rounded-lg border border-stone-200 bg-white px-3 text-sm font-semibold text-zinc-950 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
        placeholder={labels.tagTitle}
        value={draft.name}
        onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
      />
      <textarea
        className="mt-2 min-h-24 w-full resize-y rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-zinc-700 outline-none focus:border-teal-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300"
        placeholder={labels.tagDescription}
        value={draft.description}
        onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
      />
      <div className="mt-2 flex justify-end gap-2">
        <button className="icon-button" onClick={onCancel} title={labels.cancel}>
          <X size={16} />
        </button>
        <button className="icon-button" onClick={() => onSave(draft)} disabled={saving} title={labels.save}>
          {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
        </button>
      </div>
    </div>
  );
}

function TagList({ tags, labels, user, onCreateTag, onUpdateTag, onDeleteTag }) {
  const [editingId, setEditingId] = useState(null);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const canEdit = Boolean(user?.is_authenticated);

  async function saveNew(draft) {
    setSaving(true);
    await onCreateTag(draft);
    setSaving(false);
    setCreating(false);
  }

  async function saveEdit(id, draft) {
    setSaving(true);
    await onUpdateTag(id, draft);
    setSaving(false);
    setEditingId(null);
  }

  return (
    <section className="panel p-5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Tags size={18} className="text-teal-700 dark:text-teal-300" />
          <h2 className="text-sm font-semibold text-zinc-950 dark:text-white">{labels.tags}</h2>
        </div>
        {canEdit && (
          <button className="icon-button h-8 w-8" onClick={() => setCreating(true)} title={labels.addTag}>
            <Plus size={15} />
          </button>
        )}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {creating && (
          <TagForm
            labels={labels}
            saving={saving}
            onSave={saveNew}
            onCancel={() => setCreating(false)}
          />
        )}
        {!tags.length && !creating && (
          <div className="rounded-lg border border-dashed border-stone-300 p-3 text-xs leading-5 text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
            {labels.emptyTagsHint}
          </div>
        )}
        {tags.map((tag) => (
          editingId === tag.id ? (
            <TagForm
              key={tag.id}
              labels={labels}
              initialValue={tag}
              saving={saving}
              onSave={(draft) => saveEdit(tag.id, draft)}
              onCancel={() => setEditingId(null)}
            />
          ) : (
            <div key={tag.id || tag.name} className="rounded-lg border border-stone-200 p-3 dark:border-zinc-800">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-zinc-950 dark:text-white">{tag.name}</p>
                {canEdit && (
                  <div className="flex gap-1">
                    <button className="icon-button h-8 w-8" onClick={() => setEditingId(tag.id)} title={labels.edit}>
                      <Pencil size={14} />
                    </button>
                    <button className="icon-button h-8 w-8" onClick={() => onDeleteTag(tag.id)} title={labels.delete}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>
              <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">{tag.description}</p>
            </div>
          )
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
  const [user, setUser] = useState(null);
  const [tagsConfig, setTagsConfig] = useState({ tags: [], max_items_per_brief: 20 });
  const [brief, setBrief] = useState(null);
  const [archive, setArchive] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generateProgress, setGenerateProgress] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
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

  async function loadApp() {
    setLoading(true);
    setError("");
    try {
      const [me, tagPayload, entries] = await Promise.all([api.getMe(), api.getTags(), api.getBriefs()]);
      setUser(me);
      setTagsConfig(tagPayload);
      setArchive(entries);
      try {
        const todaysBrief = await api.getBrief(today);
        setBrief(todaysBrief);
      } catch (briefError) {
        if (!briefError.message.includes("404")) throw briefError;
        setBrief(null);
      }
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshTagsAndArchive() {
    const [tagPayload, entries] = await Promise.all([api.getTags(), api.getBriefs()]);
    setTagsConfig(tagPayload);
    setArchive(entries);
  }

  useEffect(() => {
    loadApp();
    api.getStocks().then(setStocks).catch(() => setStocks(null));
  }, []);

  useEffect(() => {
    if (!generating || !user?.is_authenticated) return undefined;

    let active = true;
    async function pollProgress() {
      try {
        const progress = await api.getGenerateProgress();
        if (active) setGenerateProgress(progress);
      } catch {
        // The generate request itself will surface any real error.
      }
    }

    pollProgress();
    const intervalId = window.setInterval(pollProgress, 1200);
    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [generating, user?.is_authenticated]);

  async function handleLogin(payload) {
    setAuthLoading(true);
    setError("");
    try {
      await api.login(payload);
      setView("home");
      await loadApp();
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleRegister(payload) {
    setAuthLoading(true);
    setError("");
    try {
      await api.register(payload);
      setView("home");
      await loadApp();
    } catch (registerError) {
      setError(registerError.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleChangePassword(payload) {
    setAuthLoading(true);
    setError("");
    try {
      await api.changePassword(payload);
      setView("home");
      await loadApp();
    } catch (passwordError) {
      setError(passwordError.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    setError("");
    await api.logout();
    setView("home");
    await loadApp();
  }

  async function handleGenerate() {
    if (!user?.is_authenticated || !tagsConfig.tags.length) return;
    setGenerating(true);
    setGenerateProgress({
      status: "running",
      phase: "starting",
      tavily_queries_done: 0,
      tavily_queries_total: 0,
      tavily_results: 0,
      deepseek_candidates: 0,
      deepseek_items: 0,
      final_items: 0
    });
    setError("");
    try {
      const generated = await api.generateBrief();
      setBrief(generated);
      setGenerateProgress((current) => ({
        ...(current || {}),
        status: "complete",
        phase: "complete",
        final_items: generated.items?.length || 0
      }));
      setView("home");
      await refreshTagsAndArchive();
    } catch (generateError) {
      setGenerateProgress((current) => ({
        ...(current || {}),
        status: "error",
        phase: "error"
      }));
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

  async function handleCreateTag(payload) {
    await api.createTag(payload);
    await refreshTagsAndArchive();
  }

  async function handleUpdateTag(id, payload) {
    await api.updateTag(id, payload);
    await refreshTagsAndArchive();
  }

  async function handleDeleteTag(id) {
    await api.deleteTag(id);
    await refreshTagsAndArchive();
  }

  const itemCount = brief?.items?.length || 0;
  const displayUser = user?.is_authenticated ? user.username : labels.demoUser;
  const canGenerate = Boolean(user?.is_authenticated && tagsConfig.tags.length);

  if (view === "login") {
    return (
      <div className="min-h-screen bg-stone-100 text-zinc-950 transition dark:bg-zinc-950 dark:text-white">
        <AuthView
          labels={labels}
          onLogin={handleLogin}
          onRegister={handleRegister}
          error={error}
          loading={authLoading}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 text-zinc-950 transition dark:bg-zinc-950 dark:text-white">
      {generating && <GenerationProgressModal progress={generateProgress} labels={labels} />}
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

          <div className="flex flex-wrap items-center gap-2">
            <LanguageSelector language={language} setLanguage={setLanguage} className="hidden sm:flex" />
            <button className={`tab-button ${view === "home" ? "tab-button-active" : ""}`} onClick={() => setView("home")}>
              <CalendarDays size={17} />
              {labels.today}
            </button>
            <button className={`tab-button ${view === "archive" ? "tab-button-active" : ""}`} onClick={() => setView("archive")}>
              <Archive size={17} />
              {labels.archive}
            </button>
            <button className="icon-button" onClick={() => setDarkMode((value) => !value)} title="Toggle theme">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            {user?.is_authenticated && (
              <button
                className="primary-button"
                onClick={handleGenerate}
                disabled={generating || !canGenerate}
                title={canGenerate ? labels.generate : labels.emptyTagsHint}
              >
                {generating ? <Loader2 className="animate-spin" size={17} /> : <RefreshCw size={17} />}
                {labels.generate}
              </button>
            )}
            {user?.is_authenticated ? (
              <div className="flex items-center gap-2">
                <button
                  className={`tab-button ${view === "password" ? "tab-button-active" : ""}`}
                  onClick={() => setView("password")}
                  title={labels.accountSettings}
                >
                  <User size={17} />
                  {displayUser}
                </button>
                <button className="icon-button" onClick={handleLogout} title={labels.logout}>
                  <LogOut size={17} />
                </button>
              </div>
            ) : (
              <button className="tab-button" onClick={() => setView("login")}>
                <User size={17} />
                {displayUser}
              </button>
            )}
          </div>
        </div>
        <div className="mx-auto max-w-7xl px-4 pb-4 sm:hidden">
          <LanguageSelector language={language} setLanguage={setLanguage} className="flex w-full" />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_330px] lg:px-8">
        <section className="min-w-0">
          {error && view !== "password" && (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
              {error}
            </div>
          )}

          {!user?.is_authenticated && (
            <div className="mb-4 rounded-lg border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800 dark:border-teal-900 dark:bg-teal-950 dark:text-teal-200">
              {labels.demoMode}
            </div>
          )}

          {view === "password" && user?.is_authenticated ? (
            <PasswordView
              labels={labels}
              onChangePassword={handleChangePassword}
              onBack={() => setView("home")}
              error={error}
              loading={authLoading}
            />
          ) : view === "archive" ? (
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
                <BriefCard key={`${textOf(item.title, "en")}-${index}`} item={item} language={language} />
              ))}
            </div>
          ) : (
            <EmptyState user={user} labels={labels} />
          )}
        </section>

        <aside className="grid h-fit gap-4">
          <section className="panel p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-500">{labels.today}</p>
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
          <TagList
            tags={tagsConfig.tags}
            labels={labels}
            user={user}
            onCreateTag={handleCreateTag}
            onUpdateTag={handleUpdateTag}
            onDeleteTag={handleDeleteTag}
          />
        </aside>
      </main>
      <StockStrip stocks={stocks} labels={labels} />
    </div>
  );
}
