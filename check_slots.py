#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URL = "https://it.tlscontact.com/by/msq/page.php?pid=news"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "last_release.txt"

def load_last():
    """Load the last news title from the state file."""
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.info("State file not found, starting fresh.")
        return ""

def save_last(val):
    """Save the latest news title to the state file."""
    with open(STATE_FILE, "w") as f:
        f.write(val)
    logging.info(f"Saved new state: {val}")

def fetch_latest():
    """Fetch the latest news title and date from the TLSContact website."""
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        news_items = soup.find_all("div", class_="d-flex py-4 align-items-start align-items-md-baseline")
        if not news_items:
            logging.warning("No news items found on the page.")
            return None, None
        latest_item = news_items[0]
        title = latest_item.find("h3", class_="mb-0").text.strip()
        date_elem = latest_item.find_next("p").find("strong")
        date = date_elem.text.strip() if date_elem else "Date not found"
        return title, date
    except requests.RequestException as e:
        logging.error(f"Failed to fetch news: {e}")
        return None, None

def send_telegram(msg):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        logging.info("Telegram message sent successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to send Telegram message: {e}")

def main():
    """Main function to check for new news and send notifications."""
    last = load_last()
    latest_title, latest_date = fetch_latest()
    if not latest_title or not latest_date:
        logging.warning("No valid news data fetched, skipping notification.")
        return
    if latest_title != last:
        msg = f"Новая новость на сайте TLSContact:\n{latest_title}\nДата: {latest_date}"
        send_telegram(msg)
        save_last(latest_title)
    else:
        logging.info("No new news detected.")

if __name__ == "__main__":
    main()