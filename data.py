import time
import requests
import pandas as pd
import config as C

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0"})
SEC = {"Hour4": 14400, "Day1": 86400}


def _get(url, params=None):
    for a in range(4):
        try:
            r = S.get(url, params=params, timeout=15)
            if r.status_code == 429:
                time.sleep(1.5 * (a + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(1 + a)
    return None


def symbols():
    j = _get(f"{C.BASE}/contract/detail")
    out = []
    for c in (j or {}).get("data", []) or []:
        s = c.get("symbol", "")
        if (s.endswith("_USDT") and c.get("quoteCoin") == "USDT"
                and c.get("state") == 0 and s not in C.EXCLUDE):
            out.append(s)
    return sorted(set(out))


def klines(sym, interval, bars):
    time.sleep(0.08)
    end = int(time.time())
    start = end - bars * SEC[interval]
    j = _get(f"{C.BASE}/contract/kline/{sym}",
             {"interval": interval, "start": start, "end": end})
    try:
        d = j["data"]
        df = pd.DataFrame({
            "time": d["time"], "open": d["open"], "high": d["high"],
            "low": d["low"], "close": d["close"], "vol": d["vol"],
        })
    except Exception:
        return None
    if df.empty:
        return None
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time").astype(float).sort_index()
    return df[~df.index.duplicated()]


def closed(df, sec):
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    return df[df.index + pd.Timedelta(seconds=sec) <= now]
