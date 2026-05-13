import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
TAROT_SUB_STARS = int(os.getenv("TAROT_SUB_STARS", "75"))
PRIVATE_READING_STARS = int(os.getenv("PRIVATE_READING_STARS", "50"))
DB_PATH = os.getenv("DB_PATH", "astro.db")
