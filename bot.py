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

BOT_TOKEN = "8775611192:AAFsC5xlkQX9ijC8vQd6OEjgdWxQpEAOjMQ"
CHANNEL_ID = "@DesignStoriesChannel"
POLZA_API_KEY = "pza_sJJWa4sUajBEZQQL3bMvj3K22cfFr7Qd"
MODEL = "deepseek/deepseek-v4-flash"

TEST_MODE = True
TEST_INTERVAL = 60

PUBLISHED_FILE = "/app/data/published_design.json"
os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)

# =============================================

NSFW_WORDS = [
    'porn', 'porno', 'xxx', 'sex', 'nude', 'naked', 'penis', 'vagina',
    'boobs', 'breast', 'ass', 'butt', 'orgy', 'bdsm', 'kink', 'fetish',
    'erotic', 'hentai', 'transgender', 'lgbt', 'gay', 'lesbian', 'bisexual',
    'queer', 'adult', 'masturbation', 'cum', 'sperm', 'cock', 'dick',
    'pussy', 'clit', 'anal', 'oral', 'blowjob', 'handjob', 'suck'
]

# ===== ТОЛЬКО БРЕНДЫ И СТИЛИ (БЕЗ ДИЗАЙНЕРОВ) =====
STYLES = [
    "баухаус", "ар-деко", "конструктивизм", "ар-нуво",
    "поп-арт", "модерн", "функционализм", "минимализм"
]
BRANDS = [
    "Coca-Cola", "Apple", "Nike", "Adidas", "Chanel",
    "Volkswagen", "IBM", "Mercedes-Benz", "Rolex",
    "Kodak", "Disney", "NASA", "MTV", "Starbucks",
    "Puma", "Levi's", "Harley-Davidson", "Ford", "BMW",
    "Toyota", "Sony", "Philips", "Braun", "IKEA",
    "Lego", "Ferrari", "Lamborghini", "Porsche", "Tesla",
    "Google", "Microsoft", "Samsung", "Nokia", "Intel"
]
OBJECTS = [
    "логотип", "плакат", "шрифт", "вывеска",
    "реклама", "упаковка", "этикетка", "афиша",
    "журнал", "обложка", "меню", "билет"
]

# =============================================

def generate_topic():
    """Только бренд+объект или стиль+объект"""
    if random.random() < 0.6:
        return f"{random.choice(BRANDS)} {random.choice(OBJECTS)}".lower()
    else:
        return f"{random.choice(STYLES)} {random.choice(OBJECTS)}".lower()

def get_unique_topic(published):
    attempts = 0
    while attempts < 3000:
        topic = generate_topic()
        if topic not in published:
            return topic
        attempts += 1
    logger.info("📂 Все комбинации исчерпаны – сброс")
    save_published([])
    return generate_topic()

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

def clean_text(text):
    if not text:
        return text
    return text.replace('\\', '')

def is_nsfw(text):
    if not text:
        return False
    text_lower = text.lower()
    for word in NSFW_WORDS:
        if word in text_lower:
            return True
    return False

def search_duckduckgo_safe(query):
    time.sleep(2.5)
    try:
        logger.info(f"🔍 DuckDuckGo: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5))
            if not results:
                return None
            keywords = set(query.lower().split())
            for img in results:
                title = img.get('title', '')
                image_url = img.get('image', '')
                if is_nsfw(title) or is_nsfw(image_url):
                    continue
                title_words = set(title.lower().split())
                if keywords & title_words:
                    logger.info(f"✅ Релевантно: {image_url}")
                    return image_url
                if not is_nsfw(title):
                    logger.info(f"✅ Безопасно: {image_url}")
                    return image_url
            return None
    except Exception as e:
        logger.error(f"DuckDuckGo error: {e}")
        return None

def search_image(topic):
    """Формирует точные запросы для поиска"""
    logger.info(f"🔍 Поиск картинки для: {topic}")

    # Разбираем тему на части
    words = topic.split()
    brand = None
    obj = None
    style = None

    for b in BRANDS:
        if b.lower() in words:
            brand = b
            break
    for o in OBJECTS:
        if o in words:
            obj = o
            break
    for s in STYLES:
        if s in words:
            style = s
            break

    # Английские эквиваленты объектов
    eng_obj = {
        "логотип": "logo",
        "плакат": "poster",
        "шрифт": "font",
        "вывеска": "sign",
        "реклама": "advertisement",
        "упаковка": "packaging",
        "этикетка": "label",
        "афиша": "poster",
        "журнал": "magazine",
        "обложка": "cover",
        "меню": "menu",
        "билет": "ticket"
    }.get(obj, obj)

    queries = []

    # 1. Если есть бренд и объект – самый точный запрос
    if brand and obj:
        queries.append(f'"{brand}" "{eng_obj}" vintage')
        queries.append(f'"{brand}" "{eng_obj}" design')
        queries.append(f'"{brand}" {eng_obj} retro')
        queries.append(f'"{brand}" {eng_obj}')

    # 2. Если есть только бренд
    if brand:
        queries.append(f'"{brand}" design')
        queries.append(f'"{brand}" vintage')

    # 3. Если есть стиль и объект
    if style and obj:
        queries.append(f'"{style}" "{eng_obj}" design')
        queries.append(f'"{style}" {eng_obj} poster')
        queries.append(f'"{style}" {eng_obj}')

    # 4. Если есть только объект
    if obj:
        queries.append(f'"{obj}" design')
        queries.append(f'"{obj}" vintage')

    # 5. Оригинальная тема
    queries.append(topic)

    # Убираем дубли
    queries = list(dict.fromkeys(queries))

    for q in queries:
        url = search_duckduckgo_safe(q)
        if url:
            return url

    return None

def download_image(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive'
    }
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200 and len(response.content) > 5000:
                return response.content
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Попытка {attempt+1}: {e}")
            time.sleep(1)
    return None

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую, увлекательную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов.
- Заголовок — **жирным**, интригующий, с лёгкой улыбкой.
- Пиши живым, разговорным языком, с долей юмора и иронии, но без пошлости.
- Излагай от третьего лица (не используй "я", "мне", "мой", "мы").
- НЕ используй обратную косую черту (\).

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
            story = re.sub(r'\b(я|мне|мой|моя|моё|мои|мы|нас|наш)\b', '', story, flags=re.IGNORECASE)
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
            img_data = download_image(image_url)
            if img_data and len(img_data) <= 20 * 1024 * 1024:
                caption = clean_text(text[:1024])
                files = {'photo': ('image.jpg', img_data)}
                data = {'chat_id': CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}
                resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
                if resp.status_code == 200:
                    logger.info("✅ Пост с картинкой")
                    return True
                else:
                    logger.error(f"Telegram error: {resp.text}")
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
    topic = get_unique_topic(published)
    logger.info(f"📌 Тема: {topic}")
    story = generate_story(topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False
    image_url = search_image(topic)
    if not image_url:
        logger.info("🔄 Пробуем другую тему")
        published.append(topic)
        save_published(published)
        topic = get_unique_topic(published)
        logger.info(f"📌 Новая тема: {topic}")
        story = generate_story(topic)
        if not story:
            logger.error("❌ История не сгенерирована")
            return False
        image_url = search_image(topic)
        if image_url:
            logger.info(f"✅ Найдена картинка")
        else:
            logger.warning("⚠️ Без картинки")
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
