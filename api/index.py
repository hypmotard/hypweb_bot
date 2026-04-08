import os
import requests
import asyncio
from flask import Flask, request
from telegram import Update, Bot

# PHẢI ĐỂ Ở NGOÀI CÙNG NHƯ THẾ NÀY
app = Flask(__name__)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
WP_URL = 'https://hypmoto.com/wp-json/wp/v2/posts'
WP_USER = os.environ.get('WP_USER')
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

bot = Bot(token=TOKEN)

# Hàm xử lý Gemini & WP (viết riêng ra cho sạch)
async def handle_logic(url, chat_id):
    # Thông báo đang xử lý
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": "Đang bào dữ liệu và dịch... Đợi tui xíu!"})
    
    try:
        # Gọi Gemini
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        prompt = {
            "contents": [{
                "parts": [{
                    "text": f"Đọc nội dung từ link này: {url}. Hãy viết thành một bài báo tiếng Việt hoàn chỉnh cho website HYPmoto. Style chuyên nghiệp, tập trung vào kỹ thuật xe ADV/Rally. Trả về định dạng HTML (chỉ dùng h2, h3, p, b). Tiêu đề đặt trong thẻ <h1>."
                }]
            }]
        }
        res = requests.post(gemini_url, json=prompt)
        full_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Tách tiêu đề và nội dung
        title = full_text.split('</h1>')[0].replace('<h1>', '').strip()
        content = full_text.split('</h1>')[1].strip()

        # Đăng WordPress
        wp_res = requests.post(WP_URL, json={'title': title, 'content': content, 'status': 'draft'}, 
                               auth=(WP_USER, WP_APP_PASSWORD))
        
        msg = f"✅ Xong! Bài đã nằm trong Draft: {wp_res.json().get('link')}" if wp_res.status_code == 201 else "❌ Lỗi đăng WP rồi."
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": f"Lỗi: {str(e)}"})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        text = update.message.text
        if "http" in text:
            # Chạy logic async trong Flask
            asyncio.run(handle_logic(text, update.message.chat_id))
    return "ok", 200

@app.route('/')
def index():
    return "HYPmoto Bot is Active!"