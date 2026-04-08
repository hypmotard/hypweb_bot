import os
import requests
import asyncio # Thêm cái này
from flask import Flask, request
from telegram import Update, Bot

app = Flask(__name__)

# Cấu hình lấy từ Environment Variables
TOKEN = os.environ.get('TELEGRAM_TOKEN')
WP_URL = 'https://hypmoto.com/wp-json/wp/v2/posts'
WP_USER = os.environ.get('WP_USER')
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

bot = Bot(token=TOKEN)

# Thay đoạn xử lý trong hàm webhook bằng đoạn này để test nhanh
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')

        # Dùng requests để gửi tin nhắn (Cách này cực bền trên Vercel/Flask)
        if "http" in text:
            msg = "HYPmoto đã nhận link! Đang xử lý..."
        else:
            msg = "Chào ông chủ HYPmoto! Gửi link tui dịch cho."

        send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": msg})
        
        return "ok", 200
    except Exception as e:
        print(f"Lỗi rồi ông ơi: {e}")
        return "error", 500

@app.route('/')
def index():
    return "HYPmoto Bot is running on Vercel!"