from __future__ import annotations

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


def fetch_stock_quotes(settings: Settings) -> StockResponse:
    quotes: list[StockQuote] = []

    with httpx.Client(timeout=httpx.Timeout(12)) as client:
        for symbol in settings.stock_symbols:
            try:
                ticker = _market_symbol(symbol)
                response = client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"range": "5d", "interval": "1d"},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if response.status_code >= 400:
                    quotes.append(_fallback_quote(symbol, f"HTTP {response.status_code}"))
                    continue

                data = response.json()
                error = data.get("chart", {}).get("error")
                if error:
                    quotes.append(_fallback_quote(symbol, str(error)))
                    continue

                result = data.get("chart", {}).get("result", [None])[0]
                if not result:
                    quotes.append(_fallback_quote(symbol, "No chart result"))
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
                    quotes.append(_fallback_quote(symbol, "Not enough recent daily data"))
                    continue

                last_timestamp, close = history[-1]
                _, previous_close = history[-2]
                change = close - previous_close
                change_percent = (change / previous_close) * 100 if previous_close else 0
                quotes.append(
                    StockQuote(
                        symbol=symbol,
                        price=_round_money(close),
                        change=_round_money(change),
                        change_percent=_round_percent(change_percent),
                        currency=meta.get("currency") or "USD",
                        date=datetime.fromtimestamp(last_timestamp, tz=timezone.utc).date().isoformat(),
                    )
                )
            except Exception as exc:
                quotes.append(_fallback_quote(symbol, str(exc)))

    return StockResponse(
        generated_at=_utc_timestamp(),
        source="yahoo-chart",
        quotes=quotes,
    )
