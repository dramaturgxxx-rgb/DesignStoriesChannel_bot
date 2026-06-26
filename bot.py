def search_wikimedia(query):
    """Улучшенный поиск с проверкой релевантности по описанию и заголовку"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # Извлекаем английские слова из запроса
    eng_words = extract_english_words(query)
    if not eng_words:
        # Если нет английских слов, ищем как есть (русский)
        eng_words = [query]
    
    # Формируем запросы: с категориями и без
    queries = []
    base = ' '.join(eng_words)
    # Сначала с категориями для точности
    queries.append(f'"{base}" incategory:"Logos"')
    queries.append(f'"{base}" incategory:"Posters"')
    queries.append(f'"{base}" incategory:"Design"')
    queries.append(f'"{base}" incategory:"Advertising"')
    # Fallback без категорий
    queries.append(base)
    # Убираем дубли
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
                "srlimit": 10,          # берём 10 результатов
                "srwhat": "text"
            }
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
            data = response.json()
            if not data.get("query", {}).get("search"):
                continue
            
            # Перебираем все найденные файлы
            for result in data["query"]["search"]:
                title = result["title"]
                # Проверяем, что в заголовке есть хотя бы одно ключевое слово
                title_lower = title.lower()
                if not any(word.lower() in title_lower for word in eng_words):
                    continue
                
                # Получаем детали файла (описание)
                info_params = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata"
                }
                info_resp = requests.get(search_url, params=info_params, headers=headers, timeout=15)
                if info_resp.status_code != 200:
                    continue
                info_data = info_resp.json()
                for page in info_data.get("query", {}).get("pages", {}).values():
                    if not page.get("imageinfo"):
                        continue
                    url = page["imageinfo"][0]["url"]
                    # Только JPG/JPEG
                    if not re.search(r'\.(jpg|jpeg)(\?.*)?$', url, re.I):
                        continue
                    
                    # Проверяем описание
                    desc = page["imageinfo"][0].get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
                    if desc:
                        desc_lower = desc.lower()
                        # Если в описании есть хотя бы одно ключевое слово – считаем релевантным
                        if any(word.lower() in desc_lower for word in eng_words):
                            logger.info(f"✅ Найдено релевантное изображение: {url}")
                            return url
                    else:
                        # Если описания нет, но заголовок содержит ключевые слова – тоже берём
                        logger.info(f"✅ Найдено изображение (без описания, но заголовок подходит): {url}")
                        return url
        except Exception as e:
            logger.error(f"Ошибка при поиске '{q}': {e}")
    
    logger.warning("❌ Подходящее изображение не найдено ни по одному запросу")
    return None

def create_and_publish():
    logger.info("=" * 40)
    logger.info("🚀 Генерация нового поста")
    
    published = load_published()
    available = [t for t in TOPICS if t not in published]
    
    # Если все темы использованы – сбрасываем историю
    if not available:
        save_published([])
        available = TOPICS.copy()
        logger.info("📂 Все темы использованы, история сброшена")
    
    # Перемешиваем доступные темы, чтобы каждый раз был разный порядок
    random.shuffle(available)
    
    chosen_topic = None
    image_url = None
    
    # Пытаемся найти тему с картинкой
    for topic in available:
        logger.info(f"🔍 Проверяем тему: {topic}")
        img = search_wikimedia(topic)
        if img:
            chosen_topic = topic
            image_url = img
            logger.info(f"✅ Для темы '{topic}' найдена картинка")
            break
        else:
            logger.info(f"⏭️ Для темы '{topic}' картинка не найдена, пробуем следующую")
    
    # Если ни одна тема не дала картинку – берём первую доступную
    if not chosen_topic:
        chosen_topic = available[0]
        logger.warning(f"⚠️ Ни для одной темы не найдена картинка, берём '{chosen_topic}' без картинки")
        image_url = None
    
    # Генерируем историю для выбранной темы
    logger.info(f"📌 Генерируем историю для: {chosen_topic}")
    story = generate_story(chosen_topic)
    if not story:
        logger.error("❌ История не сгенерирована")
        return False
    
    # Формируем пост
    header = "📐 <b>Истории про дизайн</b>\n\n"
    footer = "\n\n💬 А ты знал эту историю? Напиши в комментариях!\n\n👍 Поддержи ⭐️"
    story_cut = truncate_to_sentence(story, 800)
    full_text = header + story_cut + footer
    
    # Публикуем
    success = publish_to_channel(full_text, image_url)
    if success:
        # Сохраняем тему как использованную
        published.append(chosen_topic)
        save_published(published)
        logger.info(f"✅ Пост опубликован (тема: {chosen_topic})")
        return True
    else:
        logger.error("❌ Не удалось опубликовать пост")
        return False
