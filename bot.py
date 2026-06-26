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

def html_escape(text):
    """Экранирует только &, <, > для HTML"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def extract_english_words(text):
    """Извлекает слова, состоящие только из латиницы и цифр"""
    return re.findall(r'[A-Za-z0-9]+', text)

def search_wikimedia(query):
    """
    Ищет изображения на Wikimedia Commons с высокой релевантностью.
    Использует категории, точное совпадение фразы и проверку описания.
    Возвращает URL JPG-изображения или None.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # Разбираем запрос: если есть английские слова, используем их для точного поиска
    eng_words = extract_english_words(query)
    base_query = query
    if eng_words:
        # Формируем запрос с категориями для логотипов и плакатов
        # Определяем, что ищем: логотип или плакат
        is_logo = any(word in query.lower() for word in ['логотип', 'logo'])
        is_poster = any(word in query.lower() for word in ['плакат', 'poster'])
        is_font = any(word in query.lower() for word in ['шрифт', 'font'])
        
        categories = []
        if is_logo:
            categories.append('Logos')
        if is_poster:
            categories.append('Posters')
        if is_font:
            categories.append('Typefaces')
        # Если ничего не определили, добавляем общие категории
        if not categories:
            categories = ['Design', 'Culture', 'Art']
        
        # Формируем список запросов с категориями
        base = ' '.join(eng_words)
        queries = []
        for cat in categories:
            queries.append(f'"{base}" incategory:"{cat}"')
        # Добавляем простой запрос на случай, если категории не дали результата
        queries.append(f'"{base}"')
        # И просто без кавычек, если ничего не найдено
        queries.append(base)
    else:
        # Если нет английских слов, ищем как есть
        queries = [f'"{query}"', query]
    
    # Убираем дубликаты
    queries = list(dict.fromkeys(queries))
    
    for q in queries:
        try:
            logger.info(f"🔍 Ищем на Wikimedia: {q}")
            search_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": q,
                "srnamespace": 6,
                "srlimit": 10,  # берём до 10 результатов для фильтрации
                "srwhat": "text"
            }
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            if not data.get("query", {}).get("search"):
                continue
            
            # Перебираем результаты
            for result in data["query"]["search"]:
                title = result["title"]
                # Проверяем, содержит ли название хотя бы одно ключевое слово (на английском)
                if eng_words and not any(word.lower() in title.lower() for word in eng_words):
                    continue
                
                # Получаем информацию о файле
                info_params = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata"
                }
                info_resp = requests.get(search_url, params=info_params, headers=headers, timeout=10)
                if info_resp.status_code != 200:
                    continue
                info_data = info_resp.json()
                for page in info_data.get("query", {}).get("pages", {}).values():
                    if not page.get("imageinfo"):
                        continue
                    url = page["imageinfo"][0]["url"]
                    # Проверяем расширение – только JPG/JPEG
                    if not re.search(r'\.(jpg|jpeg)(\?.*)?$', url, re.I):
                        continue
                    # Проверяем описание файла
                    desc = page["imageinfo"][0].get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
                    if desc:
                        # Если описание содержит ключевые слова (на русском или английском), считаем релевантным
                        desc_lower = desc.lower()
                        # Проверяем, есть ли в описании хотя бы одно слово из запроса (русское или английское)
                        query_words = re.findall(r'[а-яёa-z0-9]+', query.lower(), re.I)
                        if any(word in desc_lower for word in query_words):
                            logger.info(f"✅ Найдено релевантное изображение: {url}")
                            return url
                        # Если описание содержит английские слова, но нет русских, тоже релевантно
                        if any(word.lower() in desc_lower for word in eng_words):
                            logger.info(f"✅ Найдено изображение (по описанию): {url}")
                            return url
                    # Если описания нет, но заголовок содержит ключевые слова – тоже берём
                    if eng_words and any(word.lower() in title.lower() for word in eng_words):
                        logger.info(f"✅ Найдено изображение (по заголовку): {url}")
                        return url
                    # Если всё совпало, но нет фильтрации – берём как fallback
                    logger.info(f"✅ Найдено изображение (без проверки): {url}")
                    return url
        except Exception as e:
            logger.error(f"Ошибка при поиске '{q}': {e}")
    
    logger.warning("❌ Подходящее изображение не найдено")
    return None

def generate_story(topic):
    prompt = f"""Ты — историк дизайна. Напиши короткую историю на тему: {topic}.

Важные требования:
- Объём: ровно 700–800 символов (не больше!).
- История должна быть законченной: иметь вступление, основную часть и вывод или вопрос к читателю.
- Не обрывай повествование на полуслове — обязательно заверши мысль.
- Заголовок — интригующий (выдели его жирным).
- Пиши живым, разговорным языком.

Тема: {topic}

История:"""
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
    if image_url:
        try:
            logger.info(f"📥 Скачиваем JPG: {image_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            img_response = requests.get(image_url, headers=headers, timeout=30)
            if img_response.status_code != 200:
                logger.warning(f"Не удалось скачать, статус {img_response.status_code}")
                image_url = None
            else:
                img_data = img_response.content
                file_size = len(img_data)
                logger.info(f"Размер файла: {file_size} байт")
                if file_size > 5 * 1024 * 1024:
                    logger.warning(f"Изображение слишком большое ({file_size} байт), пропускаем")
                    image_url = None
                else:
                    files = {'photo': ('image.jpg', img_data)}
                    caption = html_escape(text[:1024])
                    data = {
                        'chat_id': CHANNEL_ID,
                        'caption': caption,
                        'parse_mode': 'HTML'
                    }
                    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=30)
                    if resp.status_code == 200:
                        logger.info("✅ Пост с картинкой опубликован")
                        return True
                    else:
                        logger.error(f"Telegram photo error: {resp.status_code} - {resp.text[:200]}")
                        image_url = None
        except Exception as e:
            logger.error(f"Photo error: {e}")
            image_url = None

    # Отправка только текста (HTML)
    safe_text = html_escape(truncate_to_sentence(text, 4096))
    # Преобразуем ** в <b> для HTML
    safe_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_text)
    payload = {
        'chat_id': CHANNEL_ID,
        'text': safe_text,
        'parse_mode': 'HTML'
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
        logger.info("📂 История сброшена")
    topic = random.choice(available)
    logger.info(f"📌 Тема: {topic}")

    # Поиск картинки с улучшенным методом
    image_url = search_wikimedia(topic)

    story = generate_story(topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False

    header = "📐 <b>Истории про дизайн</b>\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    
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
