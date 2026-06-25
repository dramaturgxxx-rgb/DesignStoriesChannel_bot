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

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8687107012:AAG2z9A98UywrrpX8Tr1_qWao7f1-wHhdu0"
CHANNEL_ID = "@Overheard_love_stories"  # УЖЕ ПРАВИЛЬНО
POLZA_API_KEY = "pza_nQyfNXkHfKBPruMBLf6gqOXhqfIsKTP-"

TEST_MODE = True
TEST_INTERVAL = 120  # 2 минуты между постами

# =============================================

PERSONALITIES = [
    {"name": "Emma", "age": 22, "gender": "female", "city": "London", "job": "student", "education": "high", "style": "mixed"},
    {"name": "Liam", "age": 28, "gender": "male", "city": "New York", "job": "software engineer", "education": "high", "style": "dry"},
    {"name": "Sophia", "age": 31, "gender": "female", "city": "Sydney", "job": "nurse", "education": "medium", "style": "long"},
    {"name": "Noah", "age": 24, "gender": "male", "city": "Toronto", "job": "student", "education": "low", "style": "chaotic"},
    {"name": "Mia", "age": 19, "gender": "female", "city": "Austin", "job": "barista", "education": "medium", "style": "short"},
    {"name": "James", "age": 45, "gender": "male", "city": "Dublin", "job": "driver", "education": "low", "style": "dry"},
    {"name": "Olivia", "age": 26, "gender": "female", "city": "Melbourne", "job": "teacher", "education": "high", "style": "mixed"},
    {"name": "Ethan", "age": 29, "gender": "male", "city": "Austin", "job": "graphic designer", "education": "medium", "style": "chaotic"},
    {"name": "Ava", "age": 21, "gender": "female", "city": "London", "job": "student", "education": "high", "style": "short"},
    {"name": "Mason", "age": 34, "gender": "male", "city": "Chicago", "job": "lawyer", "education": "high", "style": "dry"},
    {"name": "Isabella", "age": 27, "gender": "female", "city": "Toronto", "job": "graphic designer", "education": "medium", "style": "long"},
    {"name": "Logan", "age": 23, "gender": "male", "city": "New York", "job": "student", "education": "low", "style": "chaotic"},
    {"name": "Charlotte", "age": 30, "gender": "female", "city": "Sydney", "job": "nurse", "education": "medium", "style": "mixed"},
    {"name": "Benjamin", "age": 38, "gender": "male", "city": "London", "job": "teacher", "education": "high", "style": "dry"},
    {"name": "Amelia", "age": 24, "gender": "female", "city": "Austin", "job": "barista", "education": "low", "style": "chaotic"},
    {"name": "Elijah", "age": 33, "gender": "male", "city": "Melbourne", "job": "engineer", "education": "high", "style": "mixed"},
    {"name": "Harper", "age": 20, "gender": "female", "city": "Toronto", "job": "student", "education": "medium", "style": "short"},
    {"name": "Alexander", "age": 41, "gender": "male", "city": "Chicago", "job": "manager", "education": "high", "style": "dry"},
]

TOPICS = [
    "first kiss", "first love", "first breakup", "first date", "first intimacy",
    "falling in love", "falling out of love", "long distance", "meeting parents",
    "proposal", "wedding", "divorce", "cheating", "being ghosted", "ghosting someone",
    "unrequited love", "crush on friend", "ex", "jealousy", "trust issues",
    "pregnancy", "being a parent", "loneliness", "healing", "moving on",
    "arguments", "working things out", "apology", "bad timing", "the one that got away",
    "meeting online", "blind date", "different cultures", "age gap",
]

SCENARIOS = [
    "needs_advice", "unfairness", "victory", "touching", "ambiguous",
    "frustration", "betrayal", "happiness", "anger"
]

EXTRA_DETAILS = [
    "late at night", "in the rain", "on a rooftop", "in a coffee shop", "while driving",
    "at a party", "on a walk", "in the kitchen", "lying in bed", "watching a movie",
    "during a thunderstorm", "on a bus", "at a wedding", "on a train", "at the beach",
]

IDIOMS = [
    "I'm not even kidding", "dead serious", "I swear to God", "like actually",
    "you have no idea", "I can't even", "this is insane", "I'm shook",
    "my heart just dropped", "I almost cried", "I laughed so hard",
    "life is so weird", "I don't even know anymore",
]

# =============================================

def load_published():
    if os.path.exists("published.json"):
        with open("published.json", "r") as f:
            return json.load(f)
    return []

def save_published(articles):
    with open("published.json", "w") as f:
        json.dump(articles[-100:], f)

def get_personality():
    return random.choice(PERSONALITIES)

def get_topic():
    return random.choice(TOPICS)

def get_scenario():
    return random.choice(SCENARIOS)

def get_extra_detail():
    return random.choice(EXTRA_DETAILS)

def get_idiom():
    return random.choice(IDIOMS)

def add_mistakes(text):
    mistakes = {
        " too ": " to ",
        " your ": " ur ",
        " you're ": " your ",
        " their ": " there ",
        " they're ": " there ",
        " because ": " cuz ",
        " really ": " rly ",
        " actually ": " acually ",
        " honestly ": " honest ",
        " definitely ": " definately ",
        " separate ": " seperate ",
        " necessary ": " neccessary ",
        " embarrassed ": " embarrased ",
        " recommend ": " reccomend ",
    }
    if random.random() < 0.4:
        old, new = random.choice(list(mistakes.items()))
        text = text.replace(old, new)
    if random.random() < 0.3:
        text = text.replace(",", "")
    return text

def generate_story(topic, personality, scenario, extra_detail):
    word_count = random.choice([60, 80, 100, 120, 150, 180, 200, 250])
    
    prompt = f"""Write a first-person emotional story about {topic} ({word_count} words).

PERSONALITY:
- Name: {personality['name']}, {personality['age']}, {personality['gender']}
- City: {personality['city']}
- Job: {personality['job']}
- Education: {personality['education']} (affects grammar)
- Writing style: {personality['style']}

SCENARIO: {scenario}
EXTRA DETAIL: {extra_detail}

RULES:
1. Write like a real person typing on their phone, NOT like an AI.
2. If education is "low": include spelling mistakes, grammar errors, no commas, write as if in a hurry.
3. If education is "medium": write naturally with a few mistakes and casual language.
4. If education is "high": write correctly but casually, like a normal educated person.
5. Use casual words: "kinda", "gonna", "wanna", "honestly", "literally", "actually".
6. Emotions must feel real, raw, not polished.
7. Start directly with the story. No "Let me tell you" or "I want to share".
8. If scenario is "needs_advice" → end with "What would you do?"
9. If scenario is "unfairness" → show the injustice clearly.
10. If scenario is "victory" → show relief and happiness.
11. If scenario is "touching" → show vulnerability and love.
12. If scenario is "ambiguous" → show both sides of the situation.
13. If scenario is "frustration" → show struggle and exhaustion.
14. If scenario is "betrayal" → show pain and disbelief.
15. If scenario is "happiness" → show warmth and joy.
16. If scenario is "anger" → show raw anger and frustration.

ADD SPICE:
- Add 1 random idiom: {get_idiom()}
- Add 1-3 emojis naturally (not forced): 😅😭💀❤️🔥😩😂🥺💔✨

Write the story in first person ("I"). No markdown. No hashtags.

Story:"""

    try:
        response = requests.post(
            "https://polza.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {POLZA_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 600
            },
            timeout=90
        )
        if response.status_code == 200:
            story = response.json()["choices"][0]["message"]["content"].strip()
            if personality['education'] == "low":
                story = add_mistakes(story)
            return story
        else:
            logger.error(f"Polza error: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        return None

def generate_question():
    questions = [
        "What would you do in this situation?",
        "Has something similar happened to you?",
        "Was I right to feel this way?",
        "Is it just me or...?",
        "Am I overreacting?",
        "What would you say to them?",
        "Does anyone else feel this way?",
        "Should I give them another chance?",
        "How do you move on from something like this?",
        "Is this normal?",
    ]
    return random.choice(questions)

def get_post_format(story):
    formats = [
        lambda s: f"📖 **Anonymous Story**\n\n{s}\n\n💭 {generate_question()}\n\n💬 What do you think? Drop a comment.",
        lambda s: f"📖 **Overheard**\n\n{s}\n\n🤔 {generate_question()}\n\n💬 Share your thoughts in the comments! 👇",
        lambda s: f"📖 **Real Story**\n\n{s}\n\n💭 {generate_question()}\n\n👇 What's your take?",
    ]
    return random.choice(formats)(story)

def publish_to_channel(text):
    header = "💔 **Overheard Love Stories**\n\n"
    footer = "\n\n👍 Support with ⭐️"
    full_text = header + text[:900] + footer
    
    payload = {
        'chat_id': CHANNEL_ID,
        'text': full_text[:4096],
        'parse_mode': 'Markdown'
    }
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload, timeout=30)
    if resp.status_code == 200:
        logger.info("✅ Post published")
        return True
    else:
        logger.error(f"Error: {resp.text}")
        return False

def create_and_publish():
    logger.info("=" * 40)
    logger.info("🚀 Generating new story...")
    
    published = load_published()
    personality = get_personality()
    topic = get_topic()
    scenario = get_scenario()
    extra = get_extra_detail()
    
    logger.info(f"👤 {personality['name']} ({personality['age']}, {personality['city']})")
    logger.info(f"📌 Topic: {topic}")
    logger.info(f"🎭 Scenario: {scenario}")
    
    story = generate_story(topic, personality, scenario, extra)
    if not story:
        logger.error("Failed to generate story")
        return False
    
    full_post = get_post_format(story)
    
    success = publish_to_channel(full_post)
    
    if success:
        save_published([{"title": f"{personality['name']} - {topic}", "timestamp": datetime.now().isoformat()}])
        logger.info("✅ Story published!")
        return True
    
    return False

if __name__ == "__main__":
    logger.info("💔 OVERHEARD LOVE STORIES - БОТ ЗАПУЩЕН 💔")
    
    if TEST_MODE:
        logger.info(f"🧪 ТЕСТОВЫЙ РЕЖИМ: пост каждые {TEST_INTERVAL} секунд")
        create_and_publish()
        while True:
            time.sleep(TEST_INTERVAL)
            create_and_publish()
    else:
        logger.info("⏰ Обычный режим: посты в 10:00 и 18:00 UTC")
        while True:
            now = datetime.now()
            next_run = None
            for hour in [10, 18]:
                if now.hour < hour:
                    next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                    break
            if not next_run:
                next_run = now.replace(day=now.day + 1, hour=10, minute=0, second=0, microsecond=0)
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Следующий пост в {next_run.strftime('%H:%M')} UTC (через {int(wait_seconds/60)} мин)")
            time.sleep(wait_seconds)
            create_and_publish()