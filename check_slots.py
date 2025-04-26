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
    """Загрузка последнего заголовка и даты из файла состояния."""
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if "|" in content:
                last_title, last_date = content.split("|", 1)
                logging.info(f"Загружено последнее состояние: {last_title}|{last_date}")
                return last_title.strip(), last_date.strip()
            else:
                logging.info("Файл состояния пуст или некорректен.")
                return "", ""
    except FileNotFoundError:
        logging.info("Файл состояния не найден, начинаем с чистого листа.")
        return "", ""

def save_last(title, date):
    """Сохранение последнего заголовка и даты в файл состояния."""
    with open(STATE_FILE, "w") as f:
        f.write(f"{title}|{date}")
    logging.info(f"Сохранено новое состояние: {title}|{date}")

def fetch_latest():
    """Извлечение последней новости (заголовок, дата, содержание) с сайта TLSContact."""
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Найти все контейнеры новостей
        news_divs = soup.find_all("div", class_="card card-sm-grey text-left px-4 px-md-8 py-md-6 card-visa")
        if not news_divs:
            logging.warning("Не найдены контейнеры новостей с классом 'card-visa'.")
            return None, None, None
        
        # Взять первый контейнер (самая свежая новость)
        latest_news = news_divs[0]
        
        # Извлечь заголовок
        title_elem = latest_news.find("h3", class_="mb-0")
        title = title_elem.text.strip() if title_elem else "Заголовок не найден"
        logging.info(f"Найден заголовок новости: {title}")
        
        # Извлечь дату и содержание
        p_elements = latest_news.find_all("p", class_="px-0", attrs={"align": "justify"})
        if p_elements:
            # Первая <p> содержит дату
            first_p = p_elements[0]
            date_strong = first_p.find("strong")
            if date_strong:
                date_u = date_strong.find("u")
                date = date_u.text.strip() if date_u else "Дата не найдена"
                logging.info(f"Найдена дата: {date}")
            else:
                date = "Дата не найдена"
                logging.warning("Тег <strong> для даты не найден.")
            
            # Содержание — все <p> после первой
            content_p = p_elements[1:]
            content = "\n".join([p.text.strip() for p in content_p]) if content_p else "Содержание не найдено"
            logging.info(f"Извлечено содержание: {content[:100]}...")  # Логируем первые 100 символов
        else:
            date, content = "Дата не найдена", "Содержание не найдено"
            logging.warning("Теги <p> для даты и содержания не найдены.")
        
        return title, date, content
    except requests.RequestException as e:
        logging.error(f"Ошибка при загрузке новостей: {e}")
        return None, None, None
    except Exception as e:
        logging.error(f"Общая ошибка при парсинге: {e}")
        return None, None, None

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
    last_title, last_date = load_last()
    latest_title, latest_date, latest_content = fetch_latest()
    
    if latest_title and latest_date and latest_content:
        if latest_title != last_title or latest_date != last_date:
            msg = f"Новая новость на сайте TLSContact:\n{latest_title}\nДата: {latest_date}\n\nСодержание:\n{latest_content}\n\nСайт TLSContact:\nhttps://it.tlscontact.com/by/msq/page.php?pid=news"
            send_telegram(msg)
            save_last(latest_title, latest_date)
        else:
            logging.info("Новых новостей нет.")
    else:
        logging.warning("Не удалось получить данные новости.")

if __name__ == "__main__":
    main()