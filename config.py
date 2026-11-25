import os

def env(*names):
    for n in names:
        v = os.getenv(n)
        if v:
            return v.strip()
    return ""

TG_TOKEN = env("TELEGRAM_BOT_TOKEN", "TG_BOT_TOKEN", "BOT_TOKEN")
TG_CHAT = env("TELEGRAM_CHAT_ID", "TG_CHAT_ID", "CHAT_ID")

BASE = "https://contract.mexc.com/api/v1"
EXCLUDE = set()          # koi symbol hatana ho to yahan likho, e.g. {"XYZ_USDT"}

# 1D sweep rules
SWEEP_LOOKBACK = 20       # pichle 20 daily candles ka low
SWEEP_MAX_AGE_DAYS = 3    # sweep pichli 3 closed daily candles me hona chahiye
MIN_SWEEP_DEPTH = 0.003   # low ko level se kam az kam 0.3% neeche jana chahiye
MIN_WICK_RATIO = 0.45     # neeche wick candle range ka kam az kam 45%

# 4H breakout rules
EMA_LEN = 20
MIN_BODY_RATIO = 0.40
MAX_ALERT_AGE_HOURS = 5   # purane (stale) alert nahi

# Trade levels
SL_BUFFER = 0.001         # sweep low ke 0.1% neeche
MAX_SL_PCT = 0.15         # SL 15% se door ho to skip
TP1_R = 1.5
TP2_R = 3.0

MIN_SCORE = 50
MAX_ALERTS_PER_RUN = 15
WORKERS = 4
D1_BARS = 120
H4_BARS = 200

def fmt(p):
    return f"{p:.8g}"
