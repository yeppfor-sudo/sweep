import requests
import config as C


def send_text(text):
    if not C.TG_TOKEN or not C.TG_CHAT:
        print("Telegram secrets missing")
        return
    requests.post(f"https://api.telegram.org/bot{C.TG_TOKEN}/sendMessage",
                  data={"chat_id": C.TG_CHAT, "text": text, "parse_mode": "HTML"},
                  timeout=30)


def send_photo(path, caption=""):
    if not C.TG_TOKEN or not C.TG_CHAT:
        print("Telegram secrets missing")
        return
    with open(path, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{C.TG_TOKEN}/sendPhoto",
                          data={"chat_id": C.TG_CHAT, "caption": caption[:1024],
                                "parse_mode": "HTML"},
                          files={"photo": f}, timeout=60)
    if not r.ok:
        print("sendPhoto failed:", r.text[:200])
