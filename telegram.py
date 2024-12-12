import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

def send_notification(message):
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
    }

    response = requests.post(TELEGRAM_URL, data=payload)
    return response.json()

send_notification("Hello, this is a test message!")