#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://it.tlscontact.com/by/msq/page.php?pid=news"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "last_release.txt"

def load_last():
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last(val):
    with open(STATE_FILE, "w") as f:
        f.write(val)

def fetch_latest():
    r = requests.get(URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Отладка: посмотри какие заголовки вообще есть
    print(soup.prettify())
    
    h3 = soup.select_one("h3.mb-0")
    if not h3:
        print("❌ h3.mb-0 не найден")
        return None, None
    print(f"✅ Найден заголовок: {h3.text.strip()}")
    
    title = h3.text.strip()
    date_u = soup.select_one("p strong u")
    date_str = date_u.text.strip() if date_u else ""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y").date().isoformat()
    except:
        dt = date_str
    return title, dt


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    resp = requests.post(url, data=payload, timeout=15)
    resp.raise_for_status()

def main():
    last = load_last()
    title, dt = fetch_latest()
    if not title:
        return
    key = f"{dt}|{title}"
    if key != last:
        send_telegram(f"Новая новость на сайте TLSContact\n{dt}\n{title}")
        save_last(key)

if __name__ == "__main__":
    main()
