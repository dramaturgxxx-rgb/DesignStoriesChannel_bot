import logging
import requests
import time
import json
import os
import random
import re
import sys
import subprocess
from datetime import datetime

# Автоустановка ddgs (новая библиотека)
try:
    from ddgs import DDGS
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("⏳ Устанавливаем ddgs...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ddgs', '-q'])
    from ddgs import DDGS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= КОНФИГУРАЦИЯ =================
BOT_TOKEN = "8775611192:AAFsC5xlkQX9ijC8vQd6OEjgdWxQpEAOjMQ"
CHANNEL_ID = "@DesignStoriesChannel"
POLZA_API_KEY = "pza_sJJWa4sUajBEZQQL3bMvj3K22cfFr7Qd"
MODEL = "deepseek/deepseek-v4-flash"
PIXABAY_API_KEY = "4565619-33976f9ea2f6dc09d5d97cd59"

TEST_MODE = True
TEST_INTERVAL = 60

PUBLISHED_FILE = "/app/data/published_design.json"
os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)

# =============================================

TOPICS = [
    "ретро логотип Coca-Cola",
    "винтажная вывеска Coca-Cola",
    "старый плакат Coca-Cola",
    "ретро логотип Apple",
    "винтажный компьютер Apple",
    "старый логотип Nike",
    "винтажный плакат Nike",
    "ретро логотип Adidas",
    "старый логотип Puma",
    "винтажный автомобиль Volkswagen",
    "ретро автомобиль Mercedes-Benz",
    "старый логотип Mercedes",
    "винтажная вывеска Chanel",
    "ретро плакат Chanel",
    "старый логотип Chanel",
    "плакат Баухаус",
    "винтажный плакат Баухаус",
    "интерьер Баухаус",
    "советский плакат",
    "ретро советский плакат",
    "конструктивизм плакат",
    "стул Тонета винтаж",
    "старый стул Тонета",
    "кресло Wassily",
    "стул Eames lounge",
    "ретро кресло Eames",
    "шрифт Helvetica вывеска",
    "винтажный шрифт Helvetica",
    "шрифт Futura ретро",
    "старый шрифт Futura",
    "плакат Тулуз-Лотрека",
    "ретро плакат Тулуз-Лотрека",
    "плакат Альфонса Мухи",
    "винтажный плакат Мухи",
    "старый телефон",
    "винтажный радиоприемник",
    "ретро фотоаппарат",
    "старый телевизор",
    "винтажные часы",
    "ретро часы Rolex",
    "старый автомобиль Ford",
    "винтажный мотоцикл",
    "ретро трамвай",
    "старый паровоз",
    "винтажное здание",
    "архитектура ар-деко",
    "старый завод",
    "ретро кафе интерьер",
    "винтажная витрина",
    "старая библиотека",
    "советский жилой дом",
    "ретро реклама сигарет",
    "старая упаковка чая",
    "винтажная коробка конфет",
    "советская упаковка",
    "ретро этикетка вина",
    "старая вывеска парикмахерской",
    "винтажный постер путешествий",
    "ретро плакат мода",
    "плакат поп-арт",
    "ретро игрушка",
    "винтажная посуда",
    "старый глобус",
    "винтажная карта",
    "ретро газета",
    "старый журнал",
    "винтажный костюм",
    "ретро платье",
    "старые часы",
    "винтажные очки",
    "кожаная сумка ретро",
    "шляпа 40-х",
    "ретро обувь",
    "старый галстук",
    "винтажное кольцо",
    "старый зонт",
    "ретро светильник",
    "винтажная лампа",
    "старый комод",
    "мебель скандинавский дизайн",
    "стул послевоенный",
    "кресло 50-х",
    "шкаф ретро",
    "стул пластиковый 60-х",
    "винтажное зеркало",
    "старый торшер",
    "мебель ар-деко",
    "ретро автомобиль Chevrolet",
    "классический кадиллак",
    "винтажный велосипед",
    "старый мотоцикл Harley",
    "винтажный кинотеатр",
    "старая аптека",
    "кинотеатр 50-х",
    "городской пейзаж ретро",
    "ресторан ретро",
    "старый вокзал",
    "дом эпохи модерн",
    "архитектура конструктивизм",
    "ретро логотип IBM",
    "старый логотип BMW",
    "винтажный логотип Rolex",
    "ретро вывеска Starbucks",
    "старый плакат Disney",
    "винтажный логотип NASA",
    "ретро логотип Kodak",
    "старый знак MTV"
]

def load_published():
    try:
        if os.path.exists(PUBLISHED_FILE):
            with open(PUBLISHED_FILE, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        else:
            save_published([])
            return []
    except Exception as e:
        logger.error(f"Ошибка загрузки published: {e}")
        return []

def save_published(articles):
    try:
        with open(PUBLISHED_FILE, "w") as f:
            json.dump(articles[-2000:], f)
        logger.info(f"✅ Сохранено {len(articles)} тем")
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

def get_next_topic(published):
    for topic in TOPICS:
        if topic not in published:
            return topic
    logger.info("📂 Все темы использованы, сбрасываем историю")
    save_published([])
    return TOPICS[0]

def clean_text(text):
    if not text:
        return text
    return text.replace('\\', '')

def search_duckduckgo(query):
    """Поиск изображений через DuckDuckGo (с задержкой)"""
    time.sleep(3)  # Задержка, чтобы не превысить лимит
    try:
        logger.info(f"🔍 DuckDuckGo: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
            if results and len(results) > 0:
                image_url = results[0].get('image')
                if image_url:
                    logger.info(f"✅ Найдено: {image_url}")
                    return image_url
            logger.warning("❌ Ничего не найдено")
            return None
    except Exception as e:
        logger.error(f"DuckDuckGo error: {e}")
        return None

def search_pixabay(query):
    """Поиск на Pixabay (резерв)"""
    if not PIXABAY_API_KEY:
        return None
    try:
        url = "https://pixabay.com/api/"
        params = {
            "key": PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "per_page": 1,
            "orientation": "horizontal"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("hits") and len(data["hits"]) > 0:
                return data["hits"][0]["largeImageURL"]
    except Exception as e:
        logger.error(f"Pixabay error: {e}")
    return None

def search_image(query):
    """Сначала DuckDuckGo, если не нашёл — Pixabay"""
    logger.info(f"🔍 Поиск фото: {query}")
    url = search_duckduckgo(query)
    if url:
        return url
    # Резерв
    logger.info("🔄 DuckDuckGo не дал результат, пробуем Pixabay")
    url = search_pixabay(query)
    if url:
        logger.info(f"✅ Pixabay: {url}")
        return url
    logger.warning("❌ Фото не найдено")
    return None

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую, интересную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов.
- Заголовок — **жирным**.
- Пиши живым, разговорным языком.
- НЕ ИСПОЛЬЗУЙ обратную косую черту (\).

Тема: {topic}

История:"""
    try:
        response = requests.post(
            "https://polza.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {POLZA_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.9, "max_tokens": 1100},
            timeout=90
        )
        if response.status_code == 200:
            story = response.json()["choices"][0]["message"]["content"].strip()
            story = clean_text(story)
            return story
        else:
            logger.error(f"Polza error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Generate story error: {e}")
        return None

def truncate_to_sentence(text, max_len):
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_punct > max_len * 0.6:
        return truncated[:last_punct+1]
    else:
        last_space = truncated.rfind(' ')
        if last_space > max_len * 0.6:
            return truncated[:last_space] + '...'
        else:
            return truncated + '...'

def publish_to_channel(text, image_url):
    text = clean_text(text)
    if image_url:
        try:
            logger.info(f"📥 Скачиваем")
            headers = {'User-Agent': 'Mozilla/5.0'}
            img_response = requests.get(image_url, headers=headers, timeout=30)
            if img_response.status_code == 200:
                img_data = img_response.content
                if len(img_data) <= 20 * 1024 * 1024:
                    caption = clean_text(text[:1024])
                    files = {'photo': ('image.jpg', img_data)}
                    data = {'chat_id': CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}
                    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
                    if resp.status_code == 200:
                        logger.info("✅ Пост с картинкой")
                        return True
        except Exception as e:
            logger.error(f"Image error: {e}")
    safe_text = clean_text(text[:4096])
    payload = {'chat_id': CHANNEL_ID, 'text': safe_text, 'parse_mode': 'Markdown'}
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload, timeout=30)
    if resp.status_code == 200:
        logger.info("✅ Текст опубликован")
        return True
    else:
        logger.error(f"Text error: {resp.text}")
        return False

def create_and_publish():
    logger.info("=" * 40)
    logger.info("🚀 Новый пост")
    published = load_published()
    topic = get_next_topic(published)
    logger.info(f"📌 Тема: {topic}")

    image_url = search_image(topic)
    if not image_url:
        alt_topic = get_next_topic(published + [topic])
        logger.info(f"🔄 Альтернатива: {alt_topic}")
        image_url = search_image(alt_topic)
        if image_url:
            topic = alt_topic
            logger.info(f"✅ Найдена картинка для '{topic}'")
        else:
            logger.warning("⚠️ Без картинки")

    story = generate_story(topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False

    header = "📐 **Истории про дизайн**\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    story_cut = truncate_to_sentence(story, 800)
    full_text = clean_text(header + story_cut + footer)

    success = publish_to_channel(full_text, image_url)
    if success:
        published.append(topic)
        save_published(published)
        logger.info(f"✅ Опубликовано: {topic}")
        return True
    else:
        logger.error("❌ Ошибка")
        return False

def run_schedule():
    logger.info("⏰ Бот запущен")
    if TEST_MODE:
        logger.info(f"🧪 Тестовый режим: пост каждые {TEST_INTERVAL} секунд")
        while True:
            create_and_publish()
            time.sleep(TEST_INTERVAL)
    else:
        logger.info("⏰ Обычный режим: посты в 10:00, 15:00, 20:00 UTC")
        while True:
            now = datetime.now()
            next_run = None
            for hour in [10, 15, 20]:
                if now.hour < hour:
                    next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                    break
            if not next_run:
                next_run = now.replace(day=now.day + 1, hour=10, minute=0, second=0, microsecond=0)
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"⏳ Следующий пост в {next_run.strftime('%H:%M')} UTC")
            time.sleep(wait_seconds)
            create_and_publish()

if __name__ == "__main__":
    logger.info("📐 ИСТОРИИ ПРО ДИЗАЙН — ЗАПУСК")
    run_schedule()
