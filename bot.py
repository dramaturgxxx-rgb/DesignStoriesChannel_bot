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

MODEL = "deepseek/deepseek-v4-flash"

TEST_MODE = True
TEST_INTERVAL = 60

PUBLISHED_FILE = "published_design.json"

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
    "советский плакат 1920-х",
    "плакат Баухаус",
    "стул №14 Михаэля Тонета",
    "кресло Wassily",
    "стул Eames",
    "шрифт Times New Roman",
    "шрифт Helvetica",
    "шрифт Futura",
    "советский плакат",
    "ВХУТЕМАС",
    "советский конструктивизм",
]

def load_published():
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE, "r") as f:
            return json.load(f)
    return []

def save_published(articles):
    with open(PUBLISHED_FILE, "w") as f:
        json.dump(articles[-100:], f)

def escape_md(text):
    chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in chars else c for c in text)

def search_wikimedia(query):
    queries = [
        query,
        query + " design",
        query + " logo",
        query.split()[0] if len(query.split()) > 1 else None,
    ]
    queries = [q for q in queries if q]

    for q in queries:
        try:
            logger.info(f"🔍 Ищем на Wikimedia: {q}")
            search_url = "https://commons.wikimedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": q,
                "srnamespace": 6
            }
            search_resp = requests.get(search_url, params=search_params, timeout=10)
            data = search_resp.json()
            if not data.get("query", {}).get("search"):
                continue

            title = data["query"]["search"][0]["title"]
            info_url = "https://commons.wikimedia.org/w/api.php"
            info_params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url"
            }
            info_resp = requests.get(info_url, params=info_params, timeout=10)
            info_data = info_resp.json()
            pages = info_data.get("query", {}).get("pages", {})
            for page in pages.values():
                if page.get("imageinfo"):
                    url = page["imageinfo"][0]["url"]
                    if re.search(r'\.(jpg|jpeg|png|gif|webp)(\?.*)?$', url, re.I):
                        logger.info(f"✅ Найдено изображение: {url}")
                        return url
                    else:
                        logger.warning(f"⛔ Неподдерживаемый формат: {url}")
        except Exception as e:
            logger.error(f"Wikimedia error: {e}")
    logger.warning("❌ Изображение не найдено ни по одному запросу")
    return None

def generate_story(topic):
    # НОВЫЙ ПРОМПТ — с явным указанием длины и завершённости
    prompt = f"""Ты — историк дизайна. Напиши короткую историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов (не больше!).
- История должна быть законченной: иметь вступление, основную часть и вывод (или вопрос к читателю).
- Не обрывай повествование на полуслове — заверши мысль.
- Заголовок — интригующий.
- Пиши живым, разговорным языком.

Тема: {topic}

Теперь напиши законченную историю:"""
    try:
        response = requests.post(
            "https://polza.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {POLZA_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 1100  # запас, чтобы модель могла завершить мысль
            },
            timeout=90
        )
        if response.status_code == 200:
            story = response.json()["choices"][0]["message"]["content"].strip()
            # Удаляем вводные фразы
            story = re.sub(r'^(Вот|История|Текст|Расскажу|Давайте|Конечно|Напишу)\s*[:,.!]?\s*', '', story, flags=re.IGNORECASE)
            return story
        else:
            logger.error(f"Polza error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Generate story error: {e}")
        return None

def truncate_to_sentence(text, max_len):
    """
    Обрезает до max_len, но старается сохранить завершённое предложение.
    Если последнее предложение явно незавершённое (например, заканчивается на двоеточие или запятую),
    добавляет завершающую фразу.
    """
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    # Ищем последний разделитель предложений
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_punct > max_len * 0.6:
        return truncated[:last_punct+1]
    else:
        # Если нет точки, обрезаем по пробелу и ставим многоточие
        last_space = truncated.rfind(' ')
        if last_space > max_len * 0.6:
            return truncated[:last_space] + '...'
        else:
            return truncated + '...'

def publish_to_channel(text, image_url):
    if image_url:
        try:
            img_data = requests.get(image_url, timeout=30).content
            files = {'photo': ('image.jpg', img_data)}
            caption = text[:1024]
            data = {
                'chat_id': CHANNEL_ID,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
            if resp.status_code == 200:
                logger.info("✅ Пост с картинкой опубликован")
                return True
            else:
                logger.error(f"Telegram error (photo): {resp.status_code} - {resp.text[:200]}")
                image_url = None
        except Exception as e:
            logger.error(f"Photo send error: {e}")
            image_url = None

    safe_text = escape_md(truncate_to_sentence(text, 4096))
    payload = {
        'chat_id': CHANNEL_ID,
        'text': safe_text,
        'parse_mode': 'Markdown'
    }
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload, timeout=30)
    if resp.status_code == 200:
        logger.info("✅ Текст опубликован")
        return True
    else:
        logger.error(f"Text send error: {resp.text}")
        return False

def create_and_publish():
    logger.info("=" * 40)
    logger.info("🚀 Генерация нового поста")
    published = load_published()
    available = [t for t in TOPICS if t not in published]
    if not available:
        save_published([])
        available = TOPICS
        logger.info("📂 История сброшена (все темы использованы)")
    topic = random.choice(available)
    logger.info(f"📌 Тема: {topic}")

    image_url = search_wikimedia(topic)
    if not image_url and len(topic.split()) > 1:
        image_url = search_wikimedia(topic.split()[0])

    story = generate_story(topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False

    header = "📐 **Истории про дизайн**\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    
    # Теперь история уже должна быть примерно нужной длины, но на всякий случай обрежем
    story_cut = truncate_to_sentence(story, 800)
    full_text = header + story_cut + footer

    success = publish_to_channel(full_text, image_url)
    if success:
        published.append(topic)
        save_published(published)
        logger.info("✅ Пост опубликован")
        return True
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
