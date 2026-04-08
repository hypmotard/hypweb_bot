# Thêm thư viện này ở đầu file nếu chưa có
import requests

# ... (Giữ nguyên phần cấu hình API Keys ở trên)

async def process_article(url, chat_id):
    try:
        # 1. Gọi Gemini để đọc link và viết bài
        # Mẹo: Ở đây tui viết prompt để Gemini tự bóc tách và dịch luôn
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        prompt = {
            "contents": [{
                "parts": [{
                    "text": f"Đọc nội dung từ link này: {url}. Hãy viết thành một bài báo tiếng Việt hoàn chỉnh cho website HYPmoto. Style chuyên nghiệp, tập trung vào kỹ thuật xe ADV/Rally. Trả về định dạng HTML (chỉ dùng h2, h3, p, b). Tiêu đề đặt trong thẻ <h1>."
                }]
            }]
        }
        
        response = requests.post(gemini_url, json=prompt)
        result = response.json()
        full_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Tách tiêu đề (H1) và nội dung
        title = full_text.split('</h1>')[0].replace('<h1>', '').strip()
        content = full_text.split('</h1>')[1].strip()

        # 2. Đẩy lên WordPress dưới dạng Nháp (Draft)
        wp_auth = (WP_USER, WP_APP_PASSWORD)
        wp_data = {
            'title': title,
            'content': content,
            'status': 'draft'
        }
        wp_res = requests.post(WP_URL, json=wp_data, auth=wp_auth)

        if wp_res.status_code == 201:
            post_link = wp_res.json().get('link')
            return f"✅ Xong rồi ông chủ! Bài viết đã nằm trong Draft.\nXem tại đây: {post_link}"
        else:
            return f"❌ Lỗi đăng bài WP: {wp_res.status_code}"

    except Exception as e:
        return f"❌ Có biến rồi ông ơi: {str(e)}"

# Trong hàm webhook(), sửa lại chỗ gọi xử lý:
if "http" in text:
    # Gửi thông báo đang xử lý trước cho đỡ sốt ruột
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": "Đang bào dữ liệu và dịch... Đợi tui xíu!"})
    
    # Chạy hàm xử lý chính
    report = await process_article(text, chat_id)
    
    # Gửi kết quả cuối cùng
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": report})