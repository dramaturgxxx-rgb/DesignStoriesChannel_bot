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

# ====== ВАШ КЛЮЧ PIXABAY ======
PIXABAY_API_KEY = "4565619-33976f9ea2f6dc09d5d97cd59"
# ===============================

TEST_MODE = True
TEST_INTERVAL = 60

PUBLISHED_FILE = "/app/data/published_design.json"
os.makedirs(os.path.dirname(PUBLISHED_FILE), exist_ok=True)

# =============================================

# ФИКСИРОВАННЫЙ СПИСОК ТЕМ (110 шт.)
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

# Стоп-слова для исключения животных/природы
BAD_WORDS = ['animal', 'wild', 'nature', 'zoo', 'lion', 'tiger', 'panther', 'leopard', 'cheetah', 'jaguar', 'cat', 'predator', 'wildlife', 'safari', 'beast', 'claw', 'fang', 'fur', 'dog', 'wolf', 'bear', 'deer', 'fox', 'rabbit', 'bird', 'eagle', 'hawk', 'owl', 'fish', 'shark', 'whale', 'dolphin']

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
    """Агрессивная очистка текста от всех обратных слешей и экранированных символов"""
    if not text:
        return text
    # 1. Удаляем все последовательности \x (где x любой символ)
    text = re.sub(r'\\(.)', r'\1', text)
    # 2. Удаляем все оставшиеся слеши (двойные, тройные и т.п.)
    text = re.sub(r'\\+', '', text)
    # 3. Специально для экранированных дефисов, точек, запятых и т.д.
    text = re.sub(r'\\-', '-', text)
    text = re.sub(r'\\.', '.', text)
    text = re.sub(r'\\,', ',', text)
    text = re.sub(r'\\;', ';', text)
    text = re.sub(r'\\:', ':', text)
    text = re.sub(r'\\!', '!', text)
    text = re.sub(r'\\?', '?', text)
    text = re.sub(r'\\(', '(', text)
    text = re.sub(r'\\)', ')', text)
    text = re.sub(r'\\~', '~', text)
    text = re.sub(r'\\`', '`', text)
    # 4. Убираем множественные пробелы и пробелы перед знаками препинания
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r' ,', ',', text)
    text = re.sub(r' \.', '.', text)
    text = re.sub(r' !', '!', text)
    text = re.sub(r' \?', '?', text)
    return text.strip()

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

def search_pixabay(query):
    """Поиск на Pixabay (основной источник)"""
    if not PIXABAY_API_KEY:
        logger.warning("⚠️ Pixabay API ключ не настроен!")
        return None
    try:
        url = "https://pixabay.com/api/"
        params = {
            "key": PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "per_page": 10,
            "orientation": "horizontal"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Pixabay error: {response.status_code}")
            return None
        data = response.json()
        if not data.get("hits"):
            return None
        keywords = set(query.lower().split())
        # Сначала ищем по тегам (tags) – они часто содержат ключевые слова
        for hit in data["hits"]:
            tags = hit.get("tags", "").lower()
            if is_bad_image(tags):
                continue
            if any(word in tags for word in keywords):
                return hit["largeImageURL"]
        # Если не нашли по тегам, берём первое подходящее по комментариям
        for hit in data["hits"]:
            if is_bad_image(hit.get("tags", "")):
                continue
            return hit["largeImageURL"]
        # Крайний случай – берём первое вообще
        return data["hits"][0]["largeImageURL"] if data["hits"] else None
    except Exception as e:
        logger.error(f"Pixabay exception: {e}")
        return None

def search_wikimedia(query):
    """Поиск на Wikimedia (только для исторических логотипов/плакатов)"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    eng = extract_english_words(query)
    if not eng:
        return None
    base = ' '.join(eng)
    categories = ["Logos", "Posters", "Design", "Advertising", "Furniture", "Typography"]
    search_terms = []
    for cat in categories:
        search_terms.append(f'"{base}" incategory:"{cat}"')
    search_terms.append(base)
    search_terms = list(dict.fromkeys(search_terms))

    for term in search_terms:
        try:
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": term,
                "srnamespace": 6,
                "srlimit": 5,
                "srwhat": "text"
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            if not data.get("query", {}).get("search"):
                continue
            for result in data["query"]["search"]:
                title = result["title"]
                title_lower = title.lower()
                if not any(word.lower() in title_lower for word in eng):
                    continue
                info_params = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata"
                }
                info_resp = requests.get(url, params=info_params, headers=headers, timeout=10)
                if info_resp.status_code != 200:
                    continue
                info_data = info_resp.json()
                for page in info_data.get("query", {}).get("pages", {}).values():
                    if not page.get("imageinfo"):
                        continue
                    url_img = page["imageinfo"][0]["url"]
                    if re.search(r'\.(jpg|jpeg)(\?.*)?$', url_img, re.I):
                        desc = page["imageinfo"][0].get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
                        if desc:
                            desc_lower = desc.lower()
                            if any(word.lower() in desc_lower for word in eng):
                                return url_img
                        else:
                            return url_img
        except Exception as e:
            logger.error(f"Wikimedia error: {e}")
    return None

def search_image(query):
    """Гибридный поиск: Pixabay -> Wikimedia"""
    logger.info(f"🔍 Поиск фото для: {query}")
    # 1. Pixabay
    url = search_pixabay(query)
    if url:
        logger.info(f"✅ Pixabay: {url}")
        return url
    # 2. Wikimedia (fallback)
    url = search_wikimedia(query)
    if url:
        logger.info(f"✅ Wikimedia: {url}")
        return url
    logger.warning("❌ Фото не найдено ни в одном источнике")
    return None

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую, интересную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов (не больше!).
- История должна быть законченной: вступление, основная часть, вывод или вопрос.
- Заголовок — интригующий, выдели его **жирным**.
- Пиши живым, разговорным языком.
- ЗАПРЕЩЕНО использовать обратные слеши (\\) или экранирование в тексте. Никаких \-, \., \, и т.п.

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
            story = clean_text(story)
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
    text = clean_text(text)
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

def escape_md(text):
    chars = r'_*#+-=|{}>'
    return ''.join('\\' + c if c in chars else c for c in text)

def publish_to_channel(text, image_url):
    text = clean_text(text)

    if image_url:
        try:
            logger.info(f"📥 Скачиваем: {image_url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            img_response = requests.get(image_url, headers=headers, timeout=30)
            if img_response.status_code == 200:
                img_data = img_response.content
                if len(img_data) <= 20 * 1024 * 1024:
                    caption = escape_md(clean_text(text[:1024]))
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

    topic = get_next_topic(published)
    logger.info(f"📌 Тема: {topic}")

    image_url = search_image(topic)
    if not image_url:
        alt_topic = get_next_topic(published + [topic])
        logger.info(f"🔄 Пробуем альтернативную тему: {alt_topic}")
        image_url = search_image(alt_topic)
        if image_url:
            topic = alt_topic
            logger.info(f"✅ Для '{topic}' найдена картинка")
        else:
            logger.warning(f"⚠️ Для '{topic}' картинка не найдена, публикуем без фото")

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
