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

BAD_WORDS = ['animal', 'wild', 'nature', 'zoo', 'lion', 'tiger', 'panther', 'leopard', 'cheetah', 'jaguar', 'cat', 'predator', 'wildlife', 'safari', 'beast', 'claw', 'fang', 'fur', 'dog', 'wolf', 'bear', 'deer', 'fox', 'rabbit', 'bird', 'eagle', 'hawk', 'owl', 'fish', 'shark', 'whale', 'dolphin']

# Словарь перевода ключевых слов для поиска на Pexels
TOPIC_TRANSLATIONS = {
    "ретро": "retro vintage",
    "винтажный": "vintage",
    "винтажная": "vintage",
    "винтажное": "vintage",
    "винтажные": "vintage",
    "старый": "old classic",
    "старая": "old classic",
    "старое": "old classic",
    "старые": "old classic",
    "классический": "classic",
    "логотип": "logo",
    "плакат": "poster",
    "постер": "poster",
    "вывеска": "sign",
    "стул": "chair",
    "кресло": "armchair chair",
    "шрифт": "font typography",
    "автомобиль": "automobile car",
    "мотоцикл": "motorcycle",
    "велосипед": "bicycle",
    "трамвай": "tram streetcar",
    "паровоз": "steam locomotive",
    "интерьер": "interior",
    "упаковка": "packaging",
    "этикетка": "label",
    "часы": "watch clock",
    "здание": "building architecture",
    "архитектура": "architecture",
    "реклама": "advertisement advertising",
    "журнал": "magazine",
    "газета": "newspaper",
    "костюм": "suit costume",
    "платье": "dress",
    "очки": "glasses eyewear",
    "сумка": "bag",
    "шляпа": "hat",
    "обувь": "shoes footwear",
    "галстук": "tie necktie",
    "кольцо": "ring jewelry",
    "зонт": "umbrella",
    "светильник": "lamp light",
    "лампа": "lamp",
    "комод": "dresser chest",
    "шкаф": "cabinet wardrobe",
    "зеркало": "mirror",
    "торшер": "floor lamp",
    "мебель": "furniture",
    "телефон": "telephone phone",
    "радиоприемник": "radio",
    "фотоаппарат": "camera",
    "телевизор": "television TV",
    "игрушка": "toy",
    "посуда": "tableware dishes",
    "глобус": "globe",
    "карта": "map",
    "кафе": "cafe",
    "витрина": "storefront window display",
    "библиотека": "library",
    "завод": "factory plant",
    "вокзал": "train station",
    "кинотеатр": "cinema movie theater",
    "аптека": "pharmacy",
    "ресторан": "restaurant",
    "советский": "soviet",
    "конструктивизм": "constructivism",
    "коробка": "box packaging",
    "парикмахерской": "barbershop",
    "путешествий": "travel",
    "мода": "fashion",
    "компьютер": "computer",
    "знак": "sign emblem",
    "плакат": "poster",
    "пейзаж": "cityscape landscape",
    "городской": "urban city",
    "дом": "house building",
    "эпохи": "era period",
    "модерн": "art nouveau",
    "жилой": "residential",
    "конфет": "candy box",
    "сигарет": "cigarette",
    "чая": "tea",
    "вина": "wine",
}

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
        logger.info(f"Сохранено {len(articles)} тем")
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

def get_next_topic(published):
    for topic in TOPICS:
        if topic not in published:
            return topic
    logger.info("Все темы использованы, сбрасываем историю")
    save_published([])
    return TOPICS[0]

def clean_text(text):
    """Удаляет все обратные слеши и экранированные символы"""
    if not text:
        return text
    text = re.sub(r'\\(.)', r'\1', text)
    text = re.sub(r'\\+', '', text)
    return text

def extract_english_words(text):
    return re.findall(r'[A-Za-z0-9]+', text)

def translate_topic(topic):
    """Переводит русские слова темы в английские для поиска на Pexels"""
    result = topic
    # Сортируем по длине (длинные сначала), чтобы не было частичных замен
    for ru, en in sorted(TOPIC_TRANSLATIONS.items(), key=lambda x: -len(x[0])):
        result = result.replace(ru, en)
    # Оставляем только английские слова (латиница + цифры)
    words = result.split()
    english_words = [w for w in words if re.match(r'^[A-Za-z0-9\-]+$', w)]
    return ' '.join(english_words) if english_words else None

def is_bad_image(alt_text):
    if not alt_text:
        return False
    alt_lower = alt_text.lower()
    for word in BAD_WORDS:
        if word in alt_lower:
            return True
    return False

def search_wikimedia(query):
    """Поиск на Wikimedia Commons (для исторических логотипов и плакатов)"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
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
                                logger.info(f"Wikimedia: {url_img}")
                                return url_img
                        else:
                            logger.info(f"Wikimedia (без описания): {url_img}")
                            return url_img
        except Exception as e:
            logger.error(f"Wikimedia error: {e}")
    return None

def search_pexels(query):
    """Поиск на Pexels с переводом темы на английский"""
    if not PEXELS_API_KEY:
        return None

    eng = extract_english_words(query)
    translated = translate_topic(query)

    queries = []
    # Приоритет — переведённый запрос
    if translated:
        queries.append(translated)
        queries.append(f"vintage {translated}")
        queries.append(f"retro {translated}")
    # Дополнительно — английские слова из оригинала (бренды и т.п.)
    if eng:
        base = ' '.join(eng)
        if base.lower() not in (translated or '').lower():
            queries.append(f"vintage {base}")
            queries.append(f"retro {base}")
    queries = list(dict.fromkeys(queries))

    for q in queries:
        try:
            logger.info(f"Ищем на Pexels: {q}")
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": q, "per_page": 15, "orientation": "landscape", "size": "large"}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            if not data.get("photos"):
                continue
            for photo in data["photos"]:
                alt = photo.get("alt", "")
                if is_bad_image(alt):
                    continue
                photo_url = photo["src"]["large"]
                logger.info(f"Pexels OK: {photo_url} (alt: {alt})")
                return photo_url
        except Exception as e:
            logger.error(f"Pexels exception: {e}")
    return None

def search_image(query):
    """Гибридный поиск: сначала Pexels, если не нашлось — Wikimedia"""
    logger.info(f"Поиск картинки для: {query}")
    url = search_pexels(query)
    if url:
        return url
    logger.info("Pexels не нашёл, пробуем Wikimedia")
    return search_wikimedia(query)

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую, интересную историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов (не больше!).
- История должна быть законченной: вступление, основная часть, вывод или вопрос.
- Заголовок — интригующий, выдели его **жирным**.
- Пиши живым, разговорным языком.
- НИКАКИХ обратных слешей (\\) в тексте.
- НИКАКИХ экранированных символов.

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
    """Экранируем только символы, которые реально ломают Markdown в Telegram Bot API (не MarkdownV2)"""
    chars = '_*'
    return ''.join('\\' + c if c in chars else c for c in text)

def publish_to_channel(text, image_url):
    text = clean_text(text)

    if image_url:
        try:
            logger.info(f"Скачиваем: {image_url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            img_response = requests.get(image_url, headers=headers, timeout=30)
            if img_response.status_code == 200:
                img_data = img_response.content
                if len(img_data) <= 20 * 1024 * 1024:
                    caption = escape_md(clean_text(text[:1024]))
                    files = {'photo': ('image.jpg', img_data)}
                    data = {'chat_id': CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}
                    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
                    if resp.status_code == 200:
                        logger.info("Пост с картинкой опубликован")
                        return True
                    else:
                        logger.warning(f"sendPhoto failed: {resp.text}")
            logger.warning("Не удалось отправить фото, публикуем текст")
            image_url = None
        except Exception as e:
            logger.error(f"Image error: {e}")
            image_url = None

    safe_text = escape_md(truncate_to_sentence(text, 4096))
    payload = {'chat_id': CHANNEL_ID, 'text': safe_text, 'parse_mode': 'Markdown'}
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload, timeout=30)
    if resp.status_code == 200:
        logger.info("Текст опубликован")
        return True
    else:
        logger.error(f"Text error: {resp.text}")
        return False

def create_and_publish():
    logger.info("=" * 40)
    logger.info("Генерация нового поста")
    published = load_published()

    topic = get_next_topic(published)
    logger.info(f"Тема: {topic}")

    image_url = search_image(topic)
    if not image_url:
        alt_topic = get_next_topic(published + [topic])
        logger.info(f"Пробуем альтернативную тему: {alt_topic}")
        image_url = search_image(alt_topic)
        if image_url:
            topic = alt_topic
            logger.info(f"Для '{topic}' найдена картинка")
        else:
            logger.warning(f"Для '{topic}' картинка не найдена, публикуем без фото")

    story = generate_story(topic)
    if not story:
        logger.error("История не сгенерирована")
        return False

    header = "📐 **Истории про дизайн**\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    story_cut = truncate_to_sentence(story, 800)
    full_text = header + story_cut + footer

    success = publish_to_channel(full_text, image_url)
    if success:
        published.append(topic)
        save_published(published)
        logger.info(f"Пост опубликован (тема: {topic})")
        return True
    else:
        logger.error("Ошибка публикации")
        return False

def run_schedule():
    logger.info("Бот запущен")
    if TEST_MODE:
        logger.info(f"Тестовый режим: пост каждые {TEST_INTERVAL} секунд")
        while True:
            create_and_publish()
            time.sleep(TEST_INTERVAL)
    else:
        logger.info("Обычный режим: посты в 10:00, 15:00, 20:00 UTC")
        while True:
            now = datetime.now()
            next_run = None
            for hour in [10, 15, 20]:
                if now.hour < hour:
                    next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                    break
            if not next_run:
                from datetime import timedelta
                next_run = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Следующий пост в {next_run.strftime('%H:%M')} UTC (через {int(wait_seconds/60)} мин)")
            time.sleep(wait_seconds)
            create_and_publish()

if __name__ == "__main__":
    logger.info("📐 ИСТОРИИ ПРО ДИЗАЙН — БОТ ЗАПУЩЕН 📐")
    run_schedule()
