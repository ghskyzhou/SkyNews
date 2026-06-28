from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx

from .config import Settings
from .models import StockQuote, StockResponse


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _market_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _round_money(value: float) -> float:
    return round(value, 2)


def _round_percent(value: float) -> float:
    return round(value, 2)


def _fallback_quote(symbol: str, message: str) -> StockQuote:
    return StockQuote(symbol=symbol, status="unavailable", error=message)


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _fetch_tencent_quotes(client: httpx.Client, symbols: list[str]) -> dict[str, StockQuote]:
    query = ",".join(f"us{_market_symbol(symbol)}" for symbol in symbols)
    response = client.get(
        "https://qt.gtimg.cn/q=" + query,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    if response.status_code >= 400:
        return {symbol: _fallback_quote(symbol, f"tencent HTTP {response.status_code}") for symbol in symbols}

    quotes: dict[str, StockQuote] = {}
    for match in re.finditer(r'v_us([A-Za-z0-9.]+)="([^"]*)";', response.text):
        symbol = _market_symbol(match.group(1))
        fields = match.group(2).split("~")
        if len(fields) < 35 or fields[0] != "200":
            quotes[symbol] = _fallback_quote(symbol, "tencent returned incomplete quote")
            continue

        price = _parse_float(fields[3])
        previous_close = _parse_float(fields[4])
        change = _parse_float(fields[31])
        change_percent = _parse_float(fields[32])
        if price is None:
            quotes[symbol] = _fallback_quote(symbol, "tencent quote missing price")
            continue
        if change is None and previous_close is not None:
            change = price - previous_close
        if change_percent is None and change is not None and previous_close:
            change_percent = (change / previous_close) * 100

        quote_datetime = fields[30] if len(fields) > 30 else ""
        quotes[symbol] = StockQuote(
            symbol=symbol,
            price=_round_money(price),
            change=_round_money(change or 0),
            change_percent=_round_percent(change_percent or 0),
            currency=fields[35] if len(fields) > 35 and fields[35] else "USD",
            date=quote_datetime.split(" ")[0] if quote_datetime else "",
        )

    for symbol in symbols:
        quotes.setdefault(symbol, _fallback_quote(symbol, "tencent quote not found"))
    return quotes


def _fetch_yahoo_quotes(client: httpx.Client, symbols: list[str]) -> dict[str, StockQuote]:
    quotes: dict[str, StockQuote] = {}
    for symbol in symbols:
        try:
            ticker = _market_symbol(symbol)
            response = client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                params={"range": "5d", "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if response.status_code >= 400:
                quotes[symbol] = _fallback_quote(symbol, f"yahoo HTTP {response.status_code}")
                continue

            data = response.json()
            error = data.get("chart", {}).get("error")
            if error:
                quotes[symbol] = _fallback_quote(symbol, f"yahoo {error}")
                continue

            result = data.get("chart", {}).get("result", [None])[0]
            if not result:
                quotes[symbol] = _fallback_quote(symbol, "yahoo no chart result")
                continue

            meta = result.get("meta", {})
            timestamps = result.get("timestamp") or []
            close_values = result.get("indicators", {}).get("quote", [{}])[0].get("close") or []
            history = [
                (timestamp, close)
                for timestamp, close in zip(timestamps, close_values)
                if close is not None
            ]
            if len(history) < 2:
                quotes[symbol] = _fallback_quote(symbol, "yahoo not enough recent daily data")
                continue

            last_timestamp, close = history[-1]
            _, previous_close = history[-2]
            change = close - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            quotes[symbol] = StockQuote(
                symbol=symbol,
                price=_round_money(close),
                change=_round_money(change),
                change_percent=_round_percent(change_percent),
                currency=meta.get("currency") or "USD",
                date=datetime.fromtimestamp(last_timestamp, tz=timezone.utc).date().isoformat(),
            )
        except Exception as exc:
            quotes[symbol] = _fallback_quote(symbol, f"yahoo {exc}")
    return quotes


def fetch_stock_quotes(settings: Settings) -> StockResponse:
    symbols = [_market_symbol(symbol) for symbol in settings.stock_symbols]
    quotes_by_symbol: dict[str, StockQuote] = {}
    used_sources: list[str] = []
    provider_names = settings.stock_providers or ["tencent", "yahoo"]

    with httpx.Client(timeout=httpx.Timeout(12)) as client:
        for provider in provider_names:
            missing_symbols = [
                symbol
                for symbol in symbols
                if quotes_by_symbol.get(symbol, StockQuote(symbol=symbol, status="unavailable")).status != "ok"
            ]
            if not missing_symbols:
                break

            if provider == "tencent":
                provider_quotes = _fetch_tencent_quotes(client, missing_symbols)
                provider_label = "tencent-quote"
            elif provider == "yahoo":
                provider_quotes = _fetch_yahoo_quotes(client, missing_symbols)
                provider_label = "yahoo-chart"
            else:
                continue

            if any(quote.status == "ok" for quote in provider_quotes.values()):
                used_sources.append(provider_label)
            for symbol, quote in provider_quotes.items():
                current = quotes_by_symbol.get(symbol)
                if current is None or current.status != "ok":
                    quotes_by_symbol[symbol] = quote

    return StockResponse(
        generated_at=_utc_timestamp(),
        source=",".join(used_sources) if used_sources else ",".join(provider_names),
        quotes=[quotes_by_symbol.get(symbol, _fallback_quote(symbol, "quote unavailable")) for symbol in symbols],
    )
