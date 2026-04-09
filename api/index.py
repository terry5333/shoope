import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 核心重點：app 必須定義在最外面，不能縮排 ---
app = Flask(__name__)

# 從環境變數取得 Line 密鑰 (請在 Vercel 後台設定)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- 重要：把你的 GAS 網址貼在這裡 ---
# 網址結尾應該是 /exec
GAS_URL = "https://script.google.com/macros/s/AKfycbw7XZr5X9wQWLsJJl40vJo78Hj8trLVIyjf1aQEYOu8JJ4jH9yB5DUtXnCMNWZ6JqeaqQ/exec"

def get_shopee_via_gas(tracking_no):
    """ 透過 GAS 跳板解決蝦皮動態渲染與封鎖問題 """
    try:
        # 向你的 GAS 發送請求
        response = requests.get(f"{GAS_URL}?no={tracking_no}", timeout=20)
        data = response.json()
        
        # 解析 GAS 回傳的 JSON (這是蝦皮原始的物流資料)
        if data.get("data") and data["data"].get("tracking_results"):
            latest = data["data"]["tracking_results"][0]
            status = latest.get("status_description", "狀態更新中")
            time_str = latest.get("status_time", "時間確認中")
            return f"📦 單號: {tracking_no}\n📍 狀態: {status}\n⏰ 時間: {time_str}"
        else:
            return "⚠️ 查無資料，可能是單號剛產生或格式不對。"
    except Exception as e:
        # 如果連 GAS 都連不上或報錯
        return f"❌ 查詢失敗，請檢查 GAS 設定或稍後再試。"

@app.route("/", methods=['GET'])
def index():
    return "Bot is active!"

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
    
    # 只要輸入長度大於 10 就執行查詢
    if len(user_text) >= 10:
        result_text = get_shopee_via_gas(user_text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result_text)
        )

# Vercel 不需要 if __name__ == "__main__"
