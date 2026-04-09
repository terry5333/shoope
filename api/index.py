import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, BubbleContainer, TextComponent, BoxComponent
)

app = Flask(__name__)

# Line 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- 重要：請在這裡填入你的 GAS 網址 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbw7XZr5X9wQWLsJJl40vJo78Hj8trLVIyjf1aQEYOu8JJ4jH9yB5DUtXnCMNWZ6JqeaqQ/exec" 

def get_shopee_tracking(tracking_no):
    """ 透過 GAS 跳板抓取蝦皮資料 """
    try:
        # 呼叫 GAS，讓 Google 幫我們去爬蝦皮
        response = requests.get(f"{GAS_URL}?no={tracking_no}", timeout=15)
        
        if response.status_code != 200:
            return {"success": False, "msg": "❌ 跳板伺服器異常"}
            
        data = response.json()
        
        if data.get("data") and data["data"].get("tracking_results"):
            latest = data["data"]["tracking_results"][0]
            return {
                "success": True,
                "status": latest.get("status_description", "狀態更新中"),
                "time": latest.get("status_time", "時間確認中"),
                "no": tracking_no
            }
        else:
            msg = data.get("message", "查無此單號或格式不支援")
            return {"success": False, "msg": f"⚠️ {msg}"}
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"success": False, "msg": "❌ 連線超時，請稍後再試"}

def create_flex_message(data):
    """ 產生 Line Flex Message 卡片 """
    bubble = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text="📦 物流追蹤結果", weight='bold', size='xl', color='#EE4D2D'),
                BoxComponent(
                    layout='vertical', margin='lg',
                    contents=[
                        BoxComponent(layout='baseline', spacing='sm', contents=[
                            TextComponent(text='單號', color='#aaaaaa', size='sm', flex=1),
                            TextComponent(text=data['no'], wrap=True, color='#666666', size='sm', flex=5)
                        ]),
                        BoxComponent(layout='baseline', spacing='sm', contents=[
                            TextComponent(text='狀態', color='#aaaaaa', size='sm', flex=1),
                            TextComponent(text=data['status'], wrap=True, color='#333333', size='md', flex=5, weight='bold')
                        ]),
                        BoxComponent(layout='baseline', spacing='sm', contents=[
                            TextComponent(text='時間', color='#aaaaaa', size='sm', flex=1),
                            TextComponent(text=data['time'], wrap=True, color='#666666', size='xs', flex=5)
                        ])
                    ]
                )
            ]
        ),
        footer=BoxComponent(layout='vertical', contents=[
            TextComponent(text="資料來源：蝦皮購物 (GAS Proxy)", size='xs', color='#cccccc', align='center')
        ])
    )
    return FlexSendMessage(alt_text=f"物流狀態: {data['status']}", contents=bubble)

@app.route("/", methods=['GET'])
def home():
    return "Shopee Proxy Bot is Running!"

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
    # 只要長度大於等於 10 就執行查詢
    if len(user_text) >= 10:
        result = get_shopee_tracking(user_text)
        if result["success"]:
            line_bot_api.reply_message(event.reply_token, create_flex_message(result))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result["msg"]))

if __name__ == "__main__":
    app.run()
