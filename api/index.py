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

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        
        # Chạy logic xử lý trong một event loop riêng vì Flask là đồng bộ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if update.message and update.message.text:
            text = update.message.text
            if "http" in text:
                # Chỗ này sau này ông viết thêm logic gọi Gemini/Đăng bài nhé
                loop.run_until_complete(bot.send_message(
                    chat_id=update.message.chat_id, 
                    text="HYPmoto đã nhận link! Đang xử lý..."
                ))
        
        return "ok", 200

@app.route('/')
def index():
    return "HYPmoto Bot is running on Vercel!"