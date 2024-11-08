import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

LUMA_API_KEY = os.getenv("LUMA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
