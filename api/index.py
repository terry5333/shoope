import os
import requests
import re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 這是 Vercel 必須看到的變數
app = Flask(__name__)

# 從環境變數取得 Line 密鑰
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_shopee_by_scraping(tracking_no):
    """ 直接爬取網頁 HTML 並用正則表達式解析資料 """
    url = f"https://spx.tw/detail/{tracking_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    
    try:
        # 直接抓取網頁
        response = requests.get(url, headers=headers, timeout=10)
        html_text = response.text
        
        # 蝦皮通常會把 JSON 資料埋在 HTML 裡的 <script> 標籤內
        # 我們直接用正規表達式 (Regex) 搜尋關鍵字
        status_match = re.search(r'"status_description":"([^"]+)"', html_text)
        time_match = re.search(r'"status_time":"([^"]+)"', html_text)
        
        if status_match and time_match:
            status = status_match.group(1)
            time_str = time_match.group(1)
            return f"📦 單號: {tracking_no}\n📍 狀態: {status}\n⏰ 時間: {time_str}"
        
        # 如果 Regex 找不到，可能是網頁內容是動態生成的
        return "⚠️ 網頁目前不包含物流文字，可能是被蝦皮加密或需等待渲染。"
            
    except Exception as e:
        return f"❌ 爬取網頁失敗: {str(e)}"

@app.route("/", methods=['GET'])
def index():
    return "Bot is running"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip().upper()
    
    # 判斷是否為蝦皮單號格式
    if len(user_text) >= 10:
        result_text = get_shopee_by_scraping(user_text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result_text))

# 為了讓 Vercel 正常運作，不需要寫 if __name__ == "__main__" 也可以
