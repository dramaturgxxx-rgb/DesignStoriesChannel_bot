import logging
import requests
import time
import json
import os
import random
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= КОНФИГУРАЦИЯ =================
BOT_TOKEN = "8775611192:AAFsC5xlkQX9ijC8vQd6OEjgdWxQpEAOjMQ"
CHANNEL_ID = "@DesignStoriesChannel"
POLZA_API_KEY = "pza_sJJWa4sUajBEZQQL3bMvj3K22cfFr7Qd"
PEXELS_API_KEY = "DCFvixZFiwgT06gaGJr4YIqkcTHJnyhgeixlcSZW3pdnODo3Zq5QNexn"
MODEL = "deepseek/deepseek-v4-flash"

TEST_MODE = True
TEST_INTERVAL = 60

PUBLISHED_FILE = "/app/data/published_design.json"
os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)

# =============================================

ERAS = ["1920-х", "1930-х", "1940-х", "1950-х", "1960-х", "1970-х", "1980-х", "1990-х"]
STYLES = ["ретро", "винтажный", "старый", "классический", "ар-деко", "модерн", "баухаус", "конструктивизм", "поп-арт", "скандинавский", "индустриальный"]
OBJECTS = ["логотип", "вывеска", "плакат", "постер", "реклама", "упаковка", "этикетка", "афиша", "интерьер", "кафе", "ресторан", "витрина", "стул", "кресло", "светильник", "лампа", "здание", "архитектура", "автомобиль", "часы", "телефон", "радиоприемник", "фотоаппарат", "телевизор", "журнал", "газета", "игрушка", "ковер"]
BRANDS = ["Apple", "Nike", "Coca-Cola", "McDonald's", "Chanel", "Volkswagen", "IBM", "Mercedes-Benz", "Starbucks", "Adidas", "BMW", "Ford", "Levi's", "Rolex", "Kodak", "Disney", "MTV", "NASA", "Toyota", "Sony", "Philips", "Braun", "IKEA", "Lego", "Ferrari", "Porsche", "Tesla", "Google", "Microsoft", "Puma", "Reebok", "Lacoste", "Ralph Lauren", "Vogue", "Harley-Davidson", "Dior", "Versace", "Gucci"]

BAD_WORDS = ['animal', 'wild', 'nature', 'zoo', 'lion', 'tiger', 'panther', 'leopard', 'cheetah', 'jaguar', 'cat', 'predator', 'wildlife', 'safari', 'beast', 'claw', 'fang', 'fur']

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

def generate_topic():
    era = random.choice(ERAS)
    style = random.choice(STYLES)
    obj = random.choice(OBJECTS)
    brand = random.choice(BRANDS)
    templates = [
        f"ретро {obj} {brand}",
        f"винтажный {obj} {brand}",
        f"старый {obj} {brand}",
        f"{style} {obj} {brand}",
        f"{brand} {obj} ретро",
        f"{obj} {brand} {era}",
        f"{era} {style} {obj}"
    ]
    topic = random.choice(templates)
    topic = ' '.join(topic.split()).lower()
    return topic

def get_unique_topic(published):
    attempts = 0
    max_attempts = 2000
    while attempts < max_attempts:
        topic = generate_topic()
        if topic not in published:
            return topic
        attempts += 1
    logger.warning("⚠️ Все комбинации исчерпаны? Сбрасываем историю.")
    save_published([])
    return generate_topic()

def escape_md(text):
    # Не экранируем лишнего, только самые опасные символы
    chars = r'_*#+-=|{}>'
    return ''.join('\\' + c if c in chars else c for c in text)

def extract_english_words(text):
    return re.findall(r'[A-Za-z0-9]+', text)

def is_bad_image(alt_text):
    if not alt_text:
        return False
    alt_lower = alt_text.lower()
    for word in BAD_WORDS:
        if word in alt_lower:
            return True
    return False

def search_pexels(query):
    if not PEXELS_API_KEY:
        logger.warning("⚠️ Pexels API ключ не настроен!")
        return None

    eng = extract_english_words(query)
    base = ' '.join(eng) if eng else query

    # Формируем множество запросов
    queries = [query]
    if eng:
        queries.append(base)
        if any(w in query for w in ['логотип', 'logo']):
            queries.append(f"{base} logo")
            queries.append(f"vintage {base} logo")
            queries.append(f"{base} brand")
        if any(w in query for w in ['плакат', 'постер', 'poster']):
            queries.append(f"{base} poster")
            queries.append(f"vintage {base} poster")
        if any(w in query for w in ['стул', 'кресло', 'chair']):
            queries.append(f"{base} chair")
            queries.append(f"vintage {base} chair")
        if any(w in query for w in ['шрифт', 'font']):
            queries.append(f"{base} font")
            queries.append(f"{base} typography")
        if any(w in query for w in ['автомобиль', 'car']):
            queries.append(f"vintage {base} car")
        if any(w in query for w in ['вывеска', 'sign']):
            queries.append(f"vintage {base} sign")
        if any(w in query for w in ['часы', 'watch']):
            queries.append(f"vintage {base} watch")
            queries.append(f"retro {base} watch")
        queries.append(f"vintage {base}")
        queries.append(f"retro {base}")
        queries.append(f"design {base}")
    queries = list(dict.fromkeys(queries))

    for q in queries:
        try:
            logger.info(f"🔍 Ищем на Pexels: {q}")
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": q, "per_page": 15, "orientation": "landscape", "size": "large"}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            if not data.get("photos"):
                continue

            # Проверяем каждое фото
            keywords = set(q.lower().split())
            for photo in data["photos"]:
                alt = photo.get("alt", "")
                if is_bad_image(alt):
                    continue
                alt_lower = alt.lower()
                # Если alt содержит хотя бы одно ключевое слово из запроса
                if any(word in alt_lower for word in keywords):
                    photo_url = photo["src"]["large"]
                    logger.info(f"✅ Релевантное фото: {photo_url} (alt: {alt})")
                    return photo_url

            # Если релевантных нет, берём первое НЕ животное
            for photo in data["photos"]:
                alt = photo.get("alt", "")
                if not is_bad_image(alt):
                    photo_url = photo["src"]["large"]
                    logger.info(f"✅ Найдено фото (не животное): {photo_url}")
                    return photo_url

        except Exception as e:
            logger.error(f"Pexels exception для '{q}': {e}")

    logger.warning("❌ Не найдено подходящее фото")
    return None

def clean_text(text):
    """Удаляет ВСЕ обратные слеши и экранированные символы"""
    # Удаляем все слеши, стоящие перед любым символом
    text = re.sub(r'\\(.)', r'\1', text)
    # Убираем возможные двойные слеши
    text = re.sub(r'\\+', '', text)
    return text

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую, интересную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов (не больше!).
- История должна быть законченной: вступление, основная часть, вывод или вопрос.
- Заголовок — интригующий, выдели его **жирным**.
- Пиши живым, разговорным языком.
- Никаких упоминаний политики, войн, нацизма, фюреров, свастик.
- НЕ ИСПОЛЬЗУЙ обратные слеши (\\) или экранирование в тексте.

Тема: {topic}

Напиши историю (без лишних вступлений):"""
    try:
        response = requests.post(
            "https://polza.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {POLZA_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.9, "max_tokens": 1100},
            timeout=90
        )
        if response.status_code == 200:
            story = response.json()["choices"][0]["message"]["content"].strip()
            story = re.sub(r'^(Вот|История|Текст|Расскажу|Давайте|Конечно|Напишу)\s*[:,.!]?\s*', '', story, flags=re.IGNORECASE)
            story = clean_text(story)  # Удаляем все слеши
            return story
        else:
            logger.error(f"Polza error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Generate story error: {e}")
        return None

def ensure_complete(text):
    if not text:
        return text
    if text[-1] in '.!?':
        return text
    if text[-1] in ':,;—' or text.endswith(('что', 'как', 'это', '—')):
        return text + ' Вот такая история!'
    else:
        return text + '.'

def truncate_to_sentence(text, max_len):
    if len(text) <= max_len:
        return ensure_complete(text)
    truncated = text[:max_len]
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_punct > max_len * 0.6:
        return ensure_complete(truncated[:last_punct+1])
    else:
        last_space = truncated.rfind(' ')
        if last_space > max_len * 0.6:
            return ensure_complete(truncated[:last_space] + '...')
        else:
            return ensure_complete(truncated + '...')

def publish_to_channel(text, image_url):
    # Чистим текст от слешей ещё раз
    text = clean_text(text)

    if image_url:
        try:
            logger.info(f"📥 Скачиваем: {image_url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            img_response = requests.get(image_url, headers=headers, timeout=30)
            if img_response.status_code == 200:
                img_data = img_response.content
                if len(img_data) <= 20 * 1024 * 1024:
                    caption = escape_md(text[:1024])
                    files = {'photo': ('image.jpg', img_data)}
                    data = {'chat_id': CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}
                    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
                    if resp.status_code == 200:
                        logger.info("✅ Пост с картинкой")
                        return True
            logger.warning("Не удалось отправить фото, публикуем текст")
            image_url = None
        except Exception as e:
            logger.error(f"Image error: {e}")
            image_url = None

    safe_text = escape_md(truncate_to_sentence(text, 4096))
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
    logger.info("🚀 Генерация нового поста")
    published = load_published()

    if len(published) > 1900:
        logger.info("📂 Использовано более 1900 тем, частичная очистка")
        save_published(published[-1000:])
        published = load_published()

    max_attempts = 10
    topic = None
    image_url = None

    for attempt in range(max_attempts):
        test_topic = get_unique_topic(published)
        logger.info(f"🔍 Попытка {attempt+1}: проверяем тему '{test_topic}'")
        img = search_pexels(test_topic)
        if img:
            topic = test_topic
            image_url = img
            logger.info(f"✅ Найдена тема с картинкой: {topic}")
            break
        else:
            published.append(test_topic)
            save_published(published)
            logger.info(f"⏭️ Для '{test_topic}' фото нет, пробуем другую")
    else:
        topic = get_unique_topic(published)
        logger.warning(f"⚠️ Не найдено фото, берём '{topic}' без фото")
        image_url = None

    logger.info(f"📌 Генерируем историю для: {topic}")
    story = generate_story(topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False

    header = "📐 **Истории про дизайн**\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    story_cut = truncate_to_sentence(story, 800)
    full_text = header + story_cut + footer

    success = publish_to_channel(full_text, image_url)
    if success:
        published.append(topic)
        save_published(published)
        logger.info(f"✅ Пост опубликован (тема: {topic})")
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
            logger.info(f"⏳ Следующий пост в {next_run.strftime('%H:%M')} UTC (через {int(wait_seconds/60)} мин)")
            time.sleep(wait_seconds)
            create_and_publish()

if __name__ == "__main__":
    logger.info("📐 ИСТОРИИ ПРО ДИЗАЙН — БОТ ЗАПУЩЕН 📐")
    run_schedule()
