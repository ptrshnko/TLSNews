#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URL = "https://it.tlscontact.com/by/msq/page.php?pid=news"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "last_release.txt"

def load_last():
    """Загрузка последнего заголовка новости из файла состояния."""
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.info("Файл состояния не найден, начинаем с чистого листа.")
        return ""

def save_last(val):
    """Сохранение последнего заголовка новости в файл состояния."""
    with open(STATE_FILE, "w") as f:
        f.write(val)
    logging.info(f"Сохранено новое состояние: {val}")

def fetch_latest():
    """Извлечение последнего заголовка новости и даты с сайта TLSContact."""
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Ищем все заголовки новостей
        news_items = soup.find_all("h3", class_="mb-0")
        if not news_items:
            logging.warning("Не найдены элементы новостей с тегом <h3 class='mb-0'>.")
            return None, None
        
        # Берем первую новость
        latest_item = news_items[0]
        title = latest_item.text.strip()
        logging.info(f"Найден заголовок новости: {title}")
        
        # Ищем дату в следующем <p> с <strong> и <u>
        date_elem = latest_item.find_parent().find_next_sibling("p")
        if date_elem:
            strong_elem = date_elem.find("strong")
            if strong_elem:
                date = strong_elem.text.strip()
                logging.info(f"Найдена дата: {date}")
            else:
                date = "Дата не найдена"
                logging.warning("Тег <strong> для даты не найден.")
        else:
            date = "Дата не найдена"
            logging.warning("Тег <p> для даты не найден.")
        
        return title, date
    except requests.RequestException as e:
        logging.error(f"Ошибка при загрузке новостей: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Общая ошибка при парсинге: {e}")
        return None, None

def send_telegram(msg):
    """Отправка сообщения в Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        logging.info("Сообщение в Telegram отправлено успешно.")
    except requests.RequestException as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

def main():
    """Основная функция для проверки новых новостей и отправки уведомлений."""
    last = load_last()
    latest_title, latest_date = fetch_latest()
    if not latest_title or not latest_date:
        logging.warning("Не удалось получить данные новости, уведомление не отправлено.")
        return
    if latest_title != last:
        msg = f"Новая новость на сайте TLSContact:\n{latest_title}\nДата: {latest_date}"
        send_telegram(msg)
        save_last(latest_title)
    else:
        logging.info("Новых новостей нет.")

if __name__ == "__main__":
    main()