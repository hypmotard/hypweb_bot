import os
import requests
import asyncio
from flask import Flask, request
from telegram import Update, Bot

# Khởi tạo Flask App
app = Flask(__name__)

# Cấu hình từ Environment Variables
TOKEN = os.environ.get('TELEGRAM_TOKEN')
WP_URL = 'https://hypmoto.com/wp-json/wp/v2/posts'
WP_USER = os.environ.get('WP_USER')
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

bot = Bot(token=TOKEN)

async def handle_logic(url, chat_id):
    # 1. Thông báo bắt đầu xử lý
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": "🚀 HYPmoto Bot đang 'bào' dữ liệu... Đợi tui xíu nhé!"})
    
    try:
        # 2. Gọi Gemini API với cấu hình an toàn BLOCK_NONE
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Đọc nội dung từ link này: {url}. Hãy viết lại thành một bài báo tiếng Việt hoàn chỉnh cho website HYPmoto. Phong cách chuyên nghiệp, am hiểu kỹ thuật xe ADV/Rally. Format HTML: Tiêu đề nằm trong thẻ <h1>, các đoạn còn lại dùng h2, h3, p, b. Tuyệt đối không để text thô không có tag HTML."
                }]
            }],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        res = requests.post(gemini_url, json=payload)
        data = res.json()

        # Kiểm tra phản hồi từ Gemini
        if 'candidates' in data and len(data['candidates']) > 0:
            full_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Tách tiêu đề (h1) và nội dung
            if "</h1>" in full_text:
                parts = full_text.split('</h1>')
                title = parts[0].replace('<h1>', '').strip()
                content = parts[1].strip()
            else:
                title = f"Tin tức xe địa hình - {url.split('/')[-1][:30]}"
                content = full_text

            # 3. Đẩy lên WordPress dưới dạng Nháp (Draft)
            wp_res = requests.post(
                WP_URL, 
                json={'title': title, 'content': content, 'status': 'draft'}, 
                auth=(WP_USER, WP_APP_PASSWORD)
            )
            
            if wp_res.status_code == 201:
                link_draft = wp_res.json().get('link')
                msg = f"✅ NGON LÀNH! Bài đã lên Draft.\n🔗 Xem tại: {link_draft}"
            else:
                msg = f"❌ Lỗi WordPress ({wp_res.status_code}): {wp_res.text[:100]}"
        else:
            # Báo lỗi chi tiết từ Gemini
            error_info = data.get('error', {}).get('message', 'Gemini không trả về nội dung (Candidates empty)')
            msg = f"❌ Lỗi Gemini: {error_info}"

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": chat_id, "text": f"❌ Có biến kỹ thuật: {str(e)}"})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        
        if update.message and update.message.text:
            text = update.message.text
            chat_id = update.message.chat_id
            
            if "http" in text:
                # Chạy logic xử lý bất đồng bộ
                asyncio.run(handle_logic(text, chat_id))
            else:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                              json={"chat_id": chat_id, "text": "Gửi link bài báo đi ông ơi, tui mới hiểu được!"})
    except Exception as e:
        print(f"Error: {e}")
        
    return "ok", 200

@app.route('/')
def index():
    return "HYPmoto Bot is Active and Ready!"