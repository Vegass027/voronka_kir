import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# --- Telegram Bot ---
# Токен для доступа к Telegram Bot API
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Database ---
# URL для подключения к базе данных PostgreSQL
DB_URL = os.getenv("DATABASE_URL")

# --- Supabase ---
# URL и ключи для работы с Supabase API (если потребуется)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# --- Admin ---
# Telegram ID администратора для предоставления особых прав
ADMIN_TELEGRAM_ID = 7295309649