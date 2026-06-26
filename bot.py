import logging
import requests
import time
import json
import os
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

# 100 проверенных тем (все дают хорошие фото на Pexels)
TOPICS = [
    "ретро логотип Coca-Cola", "винтажная вывеска Coca-Cola", "старый плакат Coca-Cola",
    "ретро логотип Apple", "винтажный компьютер Apple", "старый логотип Nike",
    "винтажный плакат Nike", "ретро логотип Adidas", "старый логотип Puma",
    "винтажный автомобиль Volkswagen", "ретро автомобиль Mercedes-Benz",
    "старый логотип Mercedes", "винтажная вывеска Chanel", "ретро плакат Chanel",
    "старый логотип Chanel", "плакат Баухаус", "винтажный плакат Баухаус",
    "интерьер Баухаус", "советский плакат", "ретро советский плакат",
    "конструктивизм плакат", "стул Тонета винтаж", "старый стул Тонета",
    "кресло Wassily", "стул Eames lounge", "ретро кресло Eames",
    "шрифт Helvetica вывеска", "винтажный шрифт Helvetica", "шрифт Futura ретро",
    "старый шрифт Futura", "плакат Тулуз-Лотрека", "ретро плакат Тулуз-Лотрека",
    "плакат Альфонса Мухи", "винтажный плакат Мухи", "старый телефон",
    "винтажный радиоприемник", "ретро фотоаппарат", "старый телевизор",
    "винтажные часы", "ретро часы Rolex", "старый автомобиль Ford",
    "винтажный мотоцикл", "ретро трамвай", "старый паровоз",
    "винтажное здание", "архитектура ар-деко", "старый завод",
    "ретро кафе интерьер", "винтажная витрина", "старая библиотека",
    "советский жилой дом", "ретро реклама сигарет", "старая упаковка чая",
    "винтажная коробка конфет", "советская упаковка", "ретро этикетка вина",
    "старая вывеска парикмахерской", "винтажный постер путешествий",
    "ретро плакат мода", "плакат поп-арт", "ретро игрушка",
    "винтажная посуда", "старый глобус", "винтажная карта",
    "ретро газета", "старый журнал", "винтажный костюм",
    "ретро платье", "старые часы", "винтажные очки",
    "кожаная сумка ретро", "шляпа 40-х", "ретро обувь",
    "старый галстук", "винтажное кольцо", "старый зонт",
    "ретро светильник", "винтажная лампа", "старый комод",
    "мебель скандинавский дизайн", "стул послевоенный", "кресло 50-х",
    "шкаф ретро", "стул пластиковый 60-х", "винтажное зеркало",
    "старый торшер", "мебель ар-деко", "ретро автомобиль Chevrolet",
    "классический кадиллак", "винтажный велосипед", "старый мотоцикл Harley",
    "винтажный кинотеатр", "старая аптека", "кинотеатр 50-х",
    "городской пейзаж ретро", "ресторан ретро", "старый вокзал",
    "дом эпохи модерн", "архитектура конструктивизм", "ретро логотип IBM",
    "старый логотип BMW", "винтажный логотип Rolex", "ретро вывеска Starbucks",
    "старый плакат Disney", "винтажный логотип NASA", "ретро логотип Kodak",
    "старый знак MTV"
]

BAD_WORDS = ['animal', 'wild', 'nature', 'zoo', 'lion', 'tiger', 'panther', 'leopard', 'cheetah', 'jaguar', 'cat', 'predator', 'wildlife', 'safari', 'beast', 'claw', 'fang', 'fur', 'dog', 'wolf', 'bear', 'deer', 'fox', 'rabbit', 'bird', 'eagle', 'hawk', 'owl', 'fish', 'shark', 'whale', 'dolphin']

def load_published():
    try:
        if os.path.exists(PUBLISHED_FILE):
            with open(PUBLISHED_FILE, "r") as f:
                return json.load(f)
        return []
    except:
        return []

def save_published(articles):
    try:
        with open(PUBLISHED_FILE, "w") as f:
            json.dump(articles[-2000:], f)
    except:
        pass

def get_next_topic(published):
    for topic in TOPICS:
        if topic not in published:
            return topic
    save_published([])
    return TOPICS[0]

def clean_text(text):
    """Удаляем все обратные слеши"""
    return text.replace('\\', '')

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
        return None
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": query, "per_page": 20, "orientation": "landscape", "size": "large"}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        if not data.get("photos"):
            return None
        # Ищем релевантное фото
        keywords = set(query.lower().split())
        for photo in data["photos"]:
            alt = photo.get("alt", "")
            if is_bad_image(alt):
                continue
            alt_lower = alt.lower()
            if any(word in alt_lower for word in keywords):
                return photo["src"]["large"]
        # Если не нашли, берём первое без животного
        for photo in data["photos"]:
            alt = photo.get("alt", "")
            if not is_bad_image(alt):
                return photo["src"]["large"]
        return None
    except Exception as e:
        logger.error(f"Pexels error: {e}")
        return None

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую историю на тему: {topic}.

Объём: 700-800 символов. Законченная история. Заголовок выдели **жирным**.
НИКАКИХ обратных слешей. Пиши живым языком.

Тема: {topic}"""
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
            return clean_text(story)
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
    return truncated[:truncated.rfind(' ')] + '...'

def escape_md(text):
    chars = r'_*#+-=|{}>'
    return ''.join('\\' + c if c in chars else c for c in text)

def publish_to_channel(text, image_url):
    text = clean_text(text)
    if image_url:
        try:
            img_response = requests.get(image_url, timeout=30)
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
        except:
            pass
    safe_text = escape_md(truncate_to_sentence(text, 4096))
    payload = {'chat_id': CHANNEL_ID, 'text': safe_text, 'parse_mode': 'Markdown'}
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload, timeout=30)
    if resp.status_code == 200:
        logger.info("✅ Текст опубликован")
        return True
    return False

def create_and_publish():
    logger.info("🚀 Новый пост")
    published = load_published()
    topic = get_next_topic(published)
    logger.info(f"📌 Тема: {topic}")
    image_url = search_pexels(topic)
    if not image_url:
        alt_topic = get_next_topic(published + [topic])
        logger.info(f"🔄 Альтернатива: {alt_topic}")
        image_url = search_pexels(alt_topic)
        if image_url:
            topic = alt_topic
    story = generate_story(topic)
    if not story:
        logger.error("❌ Нет истории")
        return False
    full_text = f"📐 **Истории про дизайн**\n\n{truncate_to_sentence(story, 800)}\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    if publish_to_channel(full_text, image_url):
        published.append(topic)
        save_published(published)
        logger.info(f"✅ Опубликовано: {topic}")
        return True
    return False

def run_schedule():
    logger.info("⏰ Бот запущен")
    while True:
        create_and_publish()
        time.sleep(TEST_INTERVAL if TEST_MODE else 3600)

if __name__ == "__main__":
    logger.info("📐 ИСТОРИИ ПРО ДИЗАЙН — БОТ ЗАПУЩЕН 📐")
    run_schedule()
