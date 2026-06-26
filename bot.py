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

# ====== ВАШ PEXELS API КЛЮЧ (уже вставлен) ======
PEXELS_API_KEY = "DCFvixZFiwgT06gaGJr4YIqkcTHJnyhgeixlcSZW3pdnODo3Zq5QNexn"
# ================================================

MODEL = "deepseek/deepseek-v4-flash"

TEST_MODE = True
TEST_INTERVAL = 60

# Путь к файлу с использованными темами (в /app/data, как у вас на сервере)
PUBLISHED_FILE = "/app/data/published_design.json"
os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)

# =============================================

TOPICS = [
    "логотип Apple",
    "логотип Nike",
    "логотип Coca-Cola",
    "логотип FedEx",
    "логотип McDonald's",
    "логотип Chanel",
    "логотип Volkswagen",
    "логотип IBM",
    "логотип Mercedes-Benz",
    "логотип Starbucks",
    "плакат Тулуз-Лотрека",
    "плакат Альфонса Мухи",
    "плакат Баухаус",
    "советский плакат",
    "ВХУТЕМАС",
    "советский конструктивизм",
    "стул №14 Михаэля Тонета",
    "кресло Wassily",
    "стул Eames",
    "шрифт Times New Roman",
    "шрифт Helvetica",
    "шрифт Futura",
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
            json.dump(articles[-100:], f)
        logger.info(f"✅ Сохранено {len(articles)} тем")
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

def escape_md(text):
    chars = r'_*[]()~`>#+-=|{}'
    return ''.join('\\' + c if c in chars else c for c in text)

def search_pexels(query):
    """Ищет изображение на Pexels по запросу"""
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY}
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("photos") and len(data["photos"]) > 0:
                photo_url = data["photos"][0]["src"]["large"]
                logger.info(f"✅ Найдено на Pexels: {photo_url}")
                return photo_url
            else:
                logger.warning(f"❌ Нет фото для '{query}'")
                return None
        else:
            logger.error(f"Pexels ошибка: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Pexels exception: {e}")
        return None

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую, интересную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов (не больше!).
- История должна быть законченной: вступление, основная часть, вывод или вопрос.
- Заголовок — интригующий, выдели его **жирным**.
- Пиши живым, разговорным языком.
- Никаких упоминаний политики, войн, нацизма, фюреров, свастик.
- Не используй обратные слеши (\\) или экранирование.

Тема: {topic}

Напиши историю (без лишних вступлений):"""
    try:
        response = requests.post(
            "https://polza.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {POLZA_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 1100
            },
            timeout=90
        )
        if response.status_code == 200:
            story = response.json()["choices"][0]["message"]["content"].strip()
            story = re.sub(r'^(Вот|История|Текст|Расскажу|Давайте|Конечно|Напишу)\s*[:,.!]?\s*', '', story, flags=re.IGNORECASE)
            story = re.sub(r'\\+', '', story)          # убираем все слеши
            story = re.sub(r'\(', '(', story)          # нормализуем скобки
            story = re.sub(r'\)', ')', story)
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
    text = re.sub(r'\\+', '', text)
    
    if image_url:
        try:
            logger.info(f"📥 Скачиваем изображение: {image_url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            img_response = requests.get(image_url, headers=headers, timeout=30)
            if img_response.status_code != 200:
                logger.warning(f"Не удалось скачать, статус {img_response.status_code}")
                image_url = None
            else:
                img_data = img_response.content
                file_size = len(img_data)
                if file_size > 20 * 1024 * 1024:
                    logger.warning(f"Слишком большое: {file_size} байт")
                    image_url = None
                else:
                    caption = escape_md(text[:1024])
                    files = {'photo': ('image.jpg', img_data)}
                    data = {'chat_id': CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}
                    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
                    if resp.status_code == 200:
                        logger.info("✅ Пост с картинкой опубликован")
                        return True
                    else:
                        logger.error(f"Telegram error: {resp.status_code}")
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
    available = [t for t in TOPICS if t not in published]
    if not available:
        save_published([])
        available = TOPICS.copy()
        logger.info("📂 Все темы использованы, сброс")
    
    random.shuffle(available)
    chosen_topic = None
    image_url = None
    
    for topic in available:
        logger.info(f"🔍 Проверяем тему: {topic}")
        img = search_pexels(topic)
        if img:
            chosen_topic = topic
            image_url = img
            logger.info(f"✅ Для '{topic}' найдена картинка")
            break
        else:
            logger.info(f"⏭️ Для '{topic}' картинки нет, пробуем следующую")
    
    if not chosen_topic:
        chosen_topic = available[0]
        logger.warning(f"⚠️ Ни для одной темы нет картинки, берём '{chosen_topic}' без фото")
        image_url = None
    
    logger.info(f"📌 Генерируем историю для: {chosen_topic}")
    story = generate_story(chosen_topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False
    
    header = "📐 **Истории про дизайн**\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    story_cut = truncate_to_sentence(story, 800)
    full_text = header + story_cut + footer
    
    success = publish_to_channel(full_text, image_url)
    if success:
        published.append(chosen_topic)
        save_published(published)
        logger.info(f"✅ Пост опубликован (тема: {chosen_topic})")
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
