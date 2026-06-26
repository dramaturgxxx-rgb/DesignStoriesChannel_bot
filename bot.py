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

# ================= КОНФИГУРАЦИЯ =================
BOT_TOKEN = "8775611192:AAFsC5xlkQX9ijC8vQd6OEjgdWxQpEAOjMQ"
CHANNEL_ID = "@DesignStoriesChannel"
POLZA_API_KEY = "pza_sJJWa4sUajBEZQQL3bMvj3K22cfFr7Qd"
MODEL = "deepseek/deepseek-v4-flash"

TEST_MODE = True
TEST_INTERVAL = 60

PUBLISHED_FILE = "/app/data/published_design.json"
os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)

# =============================================

# ТОЛЬКО ГРАФИЧЕСКИЙ ДИЗАЙН – НИКАКОЙ ОДЕЖДЫ
ERAS = [
    "1920-х", "1930-х", "1940-х", "1950-х", "1960-х", "1970-х",
    "1980-х", "1990-х"
]
STYLES = [
    "конструктивизм", "ар-деко", "модерн", "баухаус", "поп-арт",
    "минимализм", "функционализм", "скандинавский", "винтажный",
    "ретро", "индустриальный", "органический", "модернизм"
]
OBJECTS = [
    "логотип", "вывеска", "плакат", "реклама", "упаковка",
    "этикетка", "афиша", "шрифт", "типографика", "журнал",
    "газета", "книга", "марка", "открытка", "календарь",
    "меню", "билет", "конверт", "графика"
]
BRANDS = [
    "Coca-Cola", "Apple", "Nike", "Adidas", "Puma", "Volkswagen",
    "Mercedes-Benz", "Chanel", "IBM", "BMW", "Ford", "Rolex", "Kodak",
    "Disney", "NASA", "MTV", "Starbucks", "Levi's", "Harley-Davidson",
    "Gucci", "Prada", "Versace", "Dior", "Louis Vuitton",
    "Helvetica", "Futura", "Times New Roman"
]

def generate_topic():
    era = random.choice(ERAS)
    style = random.choice(STYLES)
    obj = random.choice(OBJECTS)
    brand = random.choice(BRANDS)
    templates = [
        f"{brand} {obj} {era}",
        f"{style} {obj} {brand}",
        f"{brand} {obj} ретро",
        f"{era} {brand} {obj}",
        f"{style} ретро {obj}",
        f"{brand} винтажный {obj}"
    ]
    topic = random.choice(templates)
    return ' '.join(topic.split()).lower()

def get_unique_topic(published):
    attempts = 0
    while attempts < 500:
        topic = generate_topic()
        if topic not in published:
            return topic
        attempts += 1
    logger.info("📂 Все комбинации исчерпаны, сброс")
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

def search_duckduckgo(query):
    time.sleep(2)
    try:
        logger.info(f"🔍 DuckDuckGo: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
            if results and len(results) > 0:
                image_url = results[0].get('image')
                if image_url:
                    logger.info(f"✅ Найдено: {image_url}")
                    return image_url
            return None
    except Exception as e:
        logger.error(f"DuckDuckGo error: {e}")
        return None

def extract_keywords_from_topic(topic):
    words = topic.split()
    keywords = []
    for w in words:
        if w not in ['ретро', 'винтажный', 'старый', 'дизайн'] and len(w) > 2:
            keywords.append(w)
    return keywords

def search_image(topic, story):
    keywords = extract_keywords_from_topic(topic)
    # Уточнения для графических объектов
    if any(w in topic for w in ['логотип', 'logo']):
        keywords.append('logo')
    if any(w in topic for w in ['плакат', 'постер', 'poster']):
        keywords.append('poster')
    if any(w in topic for w in ['шрифт', 'font']):
        keywords.append('font')
        keywords.append('typography')
    if any(w in topic for w in ['вывеска', 'sign']):
        keywords.append('sign')
    if any(w in topic for w in ['этикетка', 'label']):
        keywords.append('label')
    if any(w in topic for w in ['реклама', 'advertising']):
        keywords.append('advertising')
    if any(w in topic for w in ['упаковка', 'packaging']):
        keywords.append('packaging')
    if any(w in topic for w in ['журнал', 'magazine']):
        keywords.append('magazine')
    if any(w in topic for w in ['газета', 'newspaper']):
        keywords.append('newspaper')
    if any(w in topic for w in ['книга', 'book']):
        keywords.append('book')
    if any(w in topic for w in ['марка', 'stamp']):
        keywords.append('stamp')
    if any(w in topic for w in ['открытка', 'postcard']):
        keywords.append('postcard')
    keywords.append('design')
    keywords.append('graphic')

    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', story)
    if year_match:
        keywords.append(year_match.group(1))

    queries = []
    for brand in BRANDS:
        if brand.lower() in topic:
            queries.append(f'"{brand}" {" ".join(keywords[:3])} vintage')
            queries.append(f'"{brand}" {" ".join(keywords[:2])} retro')
            break
    queries.append(' '.join(keywords[:5]))
    clean_keywords = [w for w in keywords if w not in ['design', 'graphic', 'retro', 'vintage', 'ретро', 'винтажный']]
    if clean_keywords:
        queries.append(' '.join(clean_keywords[:4]))

    queries = list(dict.fromkeys(queries))

    for q in queries:
        url = search_duckduckgo(q)
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
            logger.warning(f"Попытка {attempt+1} скачать: {e}")
            time.sleep(1)
    return None

def generate_story(topic):
    prompt = f"""Ты — историк графического дизайна. Напиши короткую, интересную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов.
- Заголовок — **жирным**.
- Пиши живым, разговорным языком, но **от третьего лица** (не используй "я", "мне", "мой", "мы").
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
            story = re.sub(r'\b(я|мне|мой|моя|моё|мои|мы|нас|наш|наша|наше)\b', '', story, flags=re.IGNORECASE)
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
    # Только текст
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

    image_url = search_image(topic, story)

    if not image_url:
        logger.info("🔄 Картинка не найдена, пробуем другую тему")
        published.append(topic)
        save_published(published)
        topic = get_unique_topic(published)
        logger.info(f"📌 Новая тема: {topic}")
        story = generate_story(topic)
        if not story:
            logger.error("❌ История не сгенерирована для новой темы")
            return False
        image_url = search_image(topic, story)
        if image_url:
            logger.info(f"✅ Найдена картинка для новой темы")
        else:
            logger.warning("⚠️ Без картинки")

    header = "📐 **Истории про графический дизайн**\n\n"
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
        logger.error("❌ Ошибка публикации")
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
    logger.info("📐 ИСТОРИИ ПРО ГРАФИЧЕСКИЙ ДИЗАЙН — ЗАПУСК")
    run_schedule()
