import pandas as pd
import config as C


def find_sweep(d):
    """d = closed 1D candles. Bullish (sell-side) liquidity sweep."""
    n = len(d)
    if n < C.SWEEP_LOOKBACK + C.SWEEP_MAX_AGE_DAYS + 2:
        return None
    for k in range(1, C.SWEEP_MAX_AGE_DAYS + 1):
        i = n - k
        c = d.iloc[i]
        prior = d.iloc[i - C.SWEEP_LOOKBACK:i]
        level = float(prior["low"].min())
        rng = float(c["high"] - c["low"])
        if rng <= 0 or level <= 0:
            continue
        if not (c["low"] < level and c["close"] > level):
            continue
        depth = (level - c["low"]) / level
        wick = (min(c["open"], c["close"]) - c["low"]) / rng
        if depth < C.MIN_SWEEP_DEPTH or wick < C.MIN_WICK_RATIO:
            continue
        after = d.iloc[i + 1:]
        if len(after) and after["low"].min() < c["low"]:
            continue  # sweep low dobara toot gaya
        avgv = prior["vol"].mean()
        volx = float(c["vol"] / avgv) if avgv > 0 else 1.0
        pos = (c["close"] - c["low"]) / rng
        score = (30 * min(1, wick / 0.7)
                 + 25 * min(1, max(0, volx - 1) / 1.5)
                 + 15 * min(1, depth / 0.03)
                 + 15 * pos)
        return {
            "time": d.index[i],
            "close_time": d.index[i] + pd.Timedelta(days=1),
            "level": level,
            "low": float(c["low"]),
            "wick": float(wick),
            "volx": volx,
            "score": float(score),
        }
    return None


def check_breakout(h, sw):
    """h = closed 4H candles. Green candle fresh close above EMA20."""
    if len(h) < C.EMA_LEN + 5:
        return None
    ema = h["close"].ewm(span=C.EMA_LEN, adjust=False).mean()
    last, prev = h.iloc[-1], h.iloc[-2]
    e1, e0 = ema.iloc[-1], ema.iloc[-2]
    rng = last["high"] - last["low"]
    if rng <= 0:
        return None
    if not (last["close"] > last["open"] and last["close"] > e1
            and prev["close"] <= e0):
        return None
    body = (last["close"] - last["open"]) / rng
    if body < C.MIN_BODY_RATIO:
        return None
    t_close = h.index[-1] + pd.Timedelta(hours=4)
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    if now - t_close > pd.Timedelta(hours=C.MAX_ALERT_AGE_HOURS):
        return None
    if t_close <= sw["close_time"]:
        return None  # trigger sweep candle ke baad hona chahiye
    entry = float(last["close"])
    sl = sw["low"] * (1 - C.SL_BUFFER)
    risk = entry - sl
    if risk <= 0 or risk / entry > C.MAX_SL_PCT:
        return None
    score = sw["score"] + 15 * min(1, body)
    if score < C.MIN_SCORE:
        return None
    return {
        "entry": entry, "sl": sl,
        "tp1": entry + C.TP1_R * risk,
        "tp2": entry + C.TP2_R * risk,
        "risk_pct": risk / entry * 100,
        "score": score,
        "trigger_time": h.index[-1],
    }
