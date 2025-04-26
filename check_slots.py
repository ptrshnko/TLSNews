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
    news_items = soup.find_all("h3", class_="mb-0")
    if not news_items:
        return None
    latest_news = news_items[0].text.strip()
    return latest_news




def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    resp = requests.post(url, data=payload, timeout=15)
    resp.raise_for_status()

def main():
    last = load_last()
    latest = fetch_latest()
    if not latest:
        return
    if latest != last:
        send_telegram(f"Новая новость на сайте TLSContact:\n{latest}")
        save_last(latest)


if __name__ == "__main__":
    main()
