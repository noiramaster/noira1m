import os, sys, json, time, logging, requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("noira1m.trading")

BINANCE_BASE = "https://api.binance.com"
BINANCE_FALLBACKS = ["https://api1.binance.com", "https://api2.binance.com", "https://api3.binance.com"]
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 65
VOLUME_SPIKE_MULTIPLIER = 1.5
ATR_SL = 1.5
ATR_TP1 = 2.0
ATR_TP2 = 3.5

_VALID_SYMBOLS: Optional[set] = None

def _try_hosts(endpoint: str, params: Optional[dict] = None, timeout: int = 15) -> Optional[dict]:
    hosts = [BINANCE_BASE] + BINANCE_FALLBACKS
    for host in hosts:
        try:
            resp = requests.get(f"{host}{endpoint}", params=params, timeout=timeout)
            if resp.status_code in (451, 429):
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception:
            continue
    return None

def get_top_coins(limit: int = 30) -> list:
    try:
        resp = requests.get(f"{COINGECKO_BASE}/coins/markets", params={
            "vs_currency": "usd", "order": "market_cap_desc",
            "per_page": limit, "page": 1, "sparkline": "false",
        }, timeout=15)
        resp.raise_for_status()
        coins = resp.json()
        return [{"symbol": c["symbol"].upper() + "USDT", "name": c["name"],
                 "price": c["current_price"], "volume": c["total_volume"],
                 "market_cap": c["market_cap"], "change_24h": c.get("price_change_percentage_24h", 0),
                 "coingecko_id": c["id"]} for c in coins if c.get("market_cap")]
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")
        return [{"symbol": "BTCUSDT", "name": "Bitcoin", "price": 60000, "volume": 1e10,
                 "market_cap": 1e12, "change_24h": 0, "coingecko_id": "bitcoin"},
                {"symbol": "ETHUSDT", "name": "Ethereum", "price": 3000, "volume": 5e9,
                 "market_cap": 5e11, "change_24h": 0, "coingecko_id": "ethereum"}]

def get_ohlc(coin_id: str, days: int = 1) -> Optional[pd.DataFrame]:
    try:
        resp = requests.get(f"{COINGECKO_BASE}/coins/{coin_id}/ohlc",
            params={"vs_currency": "usd", "days": days}, timeout=12)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or len(data) < 10:
            return None
        rows = [{"timestamp": pd.to_datetime(c[0], unit="ms"), "open": float(c[1]),
                 "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": 0} for c in data]
        return pd.DataFrame(rows)
    except Exception as e:
        logger.debug(f"OHLC error: {e}")
        return None

def calculate_signals(df: pd.DataFrame) -> dict:
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    volume = df["volume"].values

    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.mean(gain[-14:]) if len(gain) >= 14 else 0
    avg_loss = np.mean(loss[-14:]) if len(loss) >= 14 else 0
    rsi = 50
    if avg_loss != 0:
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    ema12 = pd.Series(close).ewm(span=12).mean().values
    ema26 = pd.Series(close).ewm(span=26).mean().values
    macd_line = ema12 - ema26
    signal_line = pd.Series(macd_line).ewm(span=9).mean().values
    macd_hist = macd_line - signal_line
    macd_bullish = len(macd_hist) > 1 and macd_hist[-1] > macd_hist[-2]
    sma50 = np.mean(close[-50:]) if len(close) >= 50 else close[-1]
    sma200 = np.mean(close[-200:]) if len(close) >= 200 else close[-1]
    sma_bullish = sma50 > sma200

    avg_vol = np.mean(volume[-20:]) if len(volume) >= 20 else volume[-1]
    vol_spike = volume[-1] > avg_vol * VOLUME_SPIKE_MULTIPLIER if avg_vol > 0 else False

    recent_high = np.max(high[-20:])
    recent_low = np.min(low[-20:])
    price = close[-1]
    atr_val = float(np.std(close[-20:])) if len(close) >= 20 else price * 0.02

    score = 0
    signals = []
    if rsi < RSI_OVERSOLD:
        score += 20; signals.append("oversold")
    elif rsi > RSI_OVERBOUGHT:
        score -= 20; signals.append("overbought")
    if macd_bullish:
        score += 15; signals.append("macd_bullish")
    else:
        score -= 15; signals.append("macd_bearish")
    if sma_bullish:
        score += 15; signals.append("sma_bullish")
    else:
        score -= 15; signals.append("sma_bearish")
    if vol_spike:
        score += 10; signals.append("volume_spike")
    if price <= recent_low * 1.05:
        score += 15; signals.append("near_support")
    elif price >= recent_high * 0.95:
        score -= 15; signals.append("near_resistance")

    signal_type = "neutral"
    if score >= 20:
        signal_type = "buy"
    elif score <= -20:
        signal_type = "sell"

    return {"signal_type": signal_type, "confidence": min(abs(score), 95), "rsi": round(rsi, 1),
            "macd_bullish": macd_bullish, "sma_bullish": sma_bullish, "price": price,
            "atr": atr_val, "score": score}

def find_opportunities() -> list:
    coins = get_top_coins(30)
    opportunities = []
    for coin in coins:
        df = get_ohlc(coin["coingecko_id"], 1)
        if df is None:
            continue
        sig = calculate_signals(df)
        if sig["signal_type"] != "neutral":
            opportunities.append({**coin, **sig})
        time.sleep(0.5)
    return opportunities
