import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import config as C
from data import symbols, klines, closed
from sweep import find_sweep, check_breakout
from chart import make_chart
from notify import send_photo

STATE = "state/bull_sweep_sent.json"
F = C.fmt


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(s):
    os.makedirs("state", exist_ok=True)
    cutoff = time.time() - 30 * 86400
    s = {k: v for k, v in s.items() if v > cutoff}
    with open(STATE, "w") as f:
        json.dump(s, f)


def scan(sym):
    """Returns None (no 1D sweep) or dict; dict['sig'] is None if 4H breakout not yet."""
    try:
        d_full = klines(sym, "Day1", C.D1_BARS)
        if d_full is None:
            return None
        d1 = closed(d_full, 86400)
        sw = find_sweep(d1)
        if not sw:
            return None
        h_full = klines(sym, "Hour4", C.H4_BARS)
        if h_full is None:
            return {"sym": sym, "sw": sw, "sig": None}
        h4 = closed(h_full, 14400)
        sig = check_breakout(h4, sw)
        return {"sym": sym, "sw": sw, "sig": sig,
                "d_full": d_full, "h_full": h_full}
    except Exception as e:
        print(sym, "error", e)
        return None


def main():
    state = load_state()
    syms = symbols()
    print("pairs:", len(syms))
    with ThreadPoolExecutor(C.WORKERS) as ex:
        res = [r for r in ex.map(scan, syms) if r]

    waiting = [r for r in res if not r["sig"]]
    hits = [r for r in res if r["sig"]]
    hits.sort(key=lambda r: r["sig"]["score"], reverse=True)

    print("1D sweeps found (waiting for 4H EMA20 breakout):", len(waiting))
    for r in waiting[:40]:
        print("  waiting:", r["sym"], "sweep day", r["sw"]["time"].date(),
              "score", round(r["sw"]["score"]))
    print("hits:", len(hits))

    sent = 0
    for r in hits:
        if sent >= C.MAX_ALERTS_PER_RUN:
            break
        sym, sw, sig = r["sym"], r["sw"], r["sig"]
        key = f"{sym}|{sw['time']}"
        if key in state:
            continue
        name = sym.replace("_", "")
        p4 = f"/tmp/{name}_4h.png"
        p1 = f"/tmp/{name}_1d.png"
        make_chart(r["h_full"], f"{name} 4H - EMA20 breakout", p4, [
            ("Entry", sig["entry"], "#2563eb"),
            ("SL", sig["sl"], "#dc2626"),
            ("TP1", sig["tp1"], "#16a34a"),
            ("TP2", sig["tp2"], "#15803d"),
        ], bars=120, ema_len=C.EMA_LEN)
        make_chart(r["d_full"], f"{name} 1D - liquidity sweep", p1, [
            ("Swept low", sw["level"], "#7c3aed"),
            ("Sweep wick low", sw["low"], "#dc2626"),
        ], bars=80)
        cap = (
            f"🟢 <b>BULLISH: 1D SWEEP + 4H EMA20 BREAKOUT</b>\n"
            f"<b>{name}</b>  |  Score {sig['score']:.0f}\n"
            f"1D sweep: {sw['time']:%Y-%m-%d} (swept {F(sw['level'])}, wick low {F(sw['low'])})\n"
            f"Entry: {F(sig['entry'])}\n"
            f"SL: {F(sig['sl'])} (-{sig['risk_pct']:.1f}%)\n"
            f"TP1: {F(sig['tp1'])} ({C.TP1_R}R)\n"
            f"TP2: {F(sig['tp2'])} ({C.TP2_R}R)"
        )
        send_photo(p4, cap)
        send_photo(p1, f"{name} - 1D sweep chart")
        state[key] = time.time()
        sent += 1
        time.sleep(1)

    save_state(state)
    print("alerts sent:", sent)


if __name__ == "__main__":
    main()
