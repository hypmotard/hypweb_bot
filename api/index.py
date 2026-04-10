import os
import requests
import asyncio
from flask import Flask, request
from telegram import Update, Bot

app = Flask(__name__)

# Cấu hình từ Environment Variables trên Vercel
TOKEN = os.environ.get('TELEGRAM_TOKEN')
WP_URL = 'https://hypmoto.com/wp-json/wp/v2/posts'
WP_USER = os.environ.get('WP_USER')
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

bot = Bot(token=TOKEN)

async def handle_logic(url, chat_id):
    # 1. Gửi thông báo bắt đầu
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": "🚀 HYPmoto đang bào dữ liệu và dịch... Đợi tui xíu nha!"})
    
    try:
        # 2. Dùng Jina Reader để làm sạch link (giúp Gemini đọc nhẹ hơn, đỡ tốn Quota)
        clean_url = f"https://r.jina.ai/{url}"
        
        # 3. Gọi Gemini 2.0 Flash Lite (Model ổn định nhất trong list của ông)
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_KEY}"
        
        prompt = {
            "contents": [{
                "parts": [{
                    "text": f"Đọc nội dung từ link này: {clean_url}. Hãy viết thành một bài báo tiếng Việt hoàn chỉnh cho website HYPmoto. Style chuyên nghiệp, tập trung vào kỹ thuật xe địa hình (ADV, Rally, Enduro). Trả về định dạng HTML sạch (chỉ dùng h2, h3, p, b). Tiêu đề đặt trong thẻ <h1> ở đầu bài."
                }]
            }]
        }
        
        res = requests.post(gemini_url, json=prompt)
        data = res.json()

        if 'candidates' in data and data['candidates'][0].get('content'):
            full_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Tách tiêu đề (H1) và nội dung
            if '</h1>' in full_text:
                title = full_text.split('</h1>')[0].replace('<h1>', '').strip()
                content = full_text.split('</h1>')[1].strip()
            else:
                title = "Bài viết mới từ HYPmoto"
                content = full_text

            # 4. Đăng lên WordPress dạng Draft (Nháp)
            wp_res = requests.post(
                WP_URL, 
                json={'title': title, 'content': content, 'status': 'draft'}, 
                auth=(WP_USER, WP_APP_PASSWORD)
            )
            
            if wp_res.status_code == 201:
                post_link = wp_res.json().get('link')
                msg = f"✅ Xong rồi ông chủ! Bài đã nằm trong Draft.\nXem tại đây: {post_link}"
            else:
                msg = f"❌ Lỗi đăng WP: {wp_res.status_code} - {wp_res.text[:100]}"
        else:
            error_msg = data.get('error', {}).get('message', 'Gemini từ chối trả kết quả.')
            msg = f"❌ Lỗi Gemini: {error_msg}"

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": f"❌ Có biến: {str(e)}"})

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        if update.message and update.message.text:
            text = update.message.text
            if "http" in text:
                # Chạy logic xử lý
                asyncio.run(handle_logic(text, update.message.chat_id))
        return "ok", 200

@app.route('/')
def index():
    return "HYPmoto Bot is Active!"