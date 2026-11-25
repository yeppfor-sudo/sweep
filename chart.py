import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import config as C

MC = mpf.make_marketcolors(up="#1fbf75", down="#f0506e", edge="inherit", wick="inherit")
STYLE = mpf.make_mpf_style(base_mpf_style="charles", marketcolors=MC,
                           facecolor="white", figcolor="white",
                           gridcolor="#eeeeee", gridstyle="-")


def make_chart(df, title, path, lines, bars=100, ema_len=None):
    d = df.tail(bars).rename(columns={
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "vol": "Volume"})[["Open", "High", "Low", "Close", "Volume"]]
    ap = []
    if ema_len:
        ema = df["close"].ewm(span=ema_len, adjust=False).mean().tail(bars)
        ap.append(mpf.make_addplot(ema, color="#f5a623", width=1.3))
    hl = dict(hlines=[v for _, v, _ in lines],
              colors=[c for _, _, c in lines],
              linestyle="--", linewidths=0.9)
    fig, axes = mpf.plot(d, type="candle", style=STYLE, addplot=ap, hlines=hl,
                         volume=False, figsize=(9, 6), returnfig=True,
                         title=title, tight_layout=True)
    ax = axes[0]
    for label, val, col in lines:
        ax.text(1, val, f" {label} {C.fmt(val)}", color=col, fontsize=8, va="bottom")
    fig.text(0.5, 0.5, "RANJHA", fontsize=64, color="gray", alpha=0.13,
             ha="center", va="center")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
