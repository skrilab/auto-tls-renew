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
    
    # Send the request to the Telegram API
    response = requests.post(TELEGRAM_URL, data=payload)

    # Print the response for debugging
    print("Response Status Code:", response.status_code)
    print("Response Body:", response.json())

    # Check if the request was successful
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print("Failed to send notification. Error:", response.json())

# Example usage
# send_notification('Hello! This is a test notification.')
