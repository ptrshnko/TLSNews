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
        news_starters = soup.find_all("div", class_="d-flex py-4 align-items-start align-items-md-baseline mt-4")
        if not news_starters:
            logging.warning("Не найдены контейнеры новостей с классом 'd-flex py-4...'.")
            return None, None, None
        
        # Взять первый контейнер (последняя новость)
        latest_starter = news_starters[0]
        
        # Извлечь заголовок
        title_elem = latest_starter.find("h3", class_="mb-0")
        title = title_elem.text.strip() if title_elem else "Заголовок не найден"
        logging.info(f"Найден заголовок новости: {title}")
        
        # Найти следующий контейнер новости (если есть)
        if len(news_starters) > 1:
            next_starter = news_starters[1]
        else:
            next_starter = None
        
        # Найти все <p> после текущего контейнера до следующего контейнера
        p_siblings = []
        current = latest_starter.find_next_sibling()
        while current and (next_starter is None or current != next_starter):
            if current.name == "p" and current.get("class") == ["px-0"] and current.get("align") == "justify":
                p_siblings.append(current)
            current = current.find_next_sibling()
        
        if p_siblings:
            # Первый <p> — дата
            date_p = p_siblings[0]
            date_strong = date_p.find("strong")
            if date_strong:
                date_u = date_strong.find("u")
                date = date_u.text.strip() if date_u else "Дата не найдена"
            else:
                date = "Дата не найдена"
            logging.info(f"Найдена дата: {date}")
            
            # Остальные <p> — содержание
            content_p = p_siblings[1:]
            content = "\n".join([p.text.strip() for p in content_p]) if content_p else "Содержание не найдено"
            logging.info(f"Извлечено содержание: {content[:100]}...")
        else:
            date, content = "Дата не найдена", "Содержание не найдено"
            logging.warning("Не найдены <p> для даты и содержания.")
        
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
            # Формируем сообщение с ограничением длины
            max_length = 4096
            prefix = f"Новая новость на сайте TLSContact:\n{latest_title}\nДата: {latest_date}\n\nСодержание:\n"
            suffix = f"\n\nСайт TLSContact:\n{URL}"
            total_fixed = len(prefix) + len(suffix)
            available = max_length - total_fixed
            if len(latest_content) > available - 4:  # 4 для "[...]"
                content_to_send = latest_content[:available - 4] + "[...]"
            else:
                content_to_send = latest_content
            msg = prefix + content_to_send + suffix
            send_telegram(msg)
            save_last(latest_title, latest_date)
        else:
            logging.info("Новых новостей нет.")
    else:
        logging.warning("Не удалось получить данные новости.")

if __name__ == "__main__":
    main()