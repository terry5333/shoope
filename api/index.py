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

# 從環境變數取得 Line 密鑰
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_shopee_tracking(tracking_no):
    """ 爬取蝦皮店到店(SPX)物流資訊 """
    url = "https://spx.tw/api/v2/fleet_order/tracking_search"
    params = {"sls_tracking_number": tracking_no}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://spx.tw/"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        data = response.json()
        
        if data.get("data") and data["data"].get("tracking_results"):
            # 取得最新的一筆狀態
            latest_status = data["data"]["tracking_results"][0]
            return {
                "success": True,
                "status": latest_status.get("status_description", "未知狀態"),
                "time": latest_status.get("status_time", "未知時間"),
                "no": tracking_no
            }
        return {"success": False, "msg": "查無此單號，請檢查輸入是否正確。"}
    except Exception as e:
        return {"success": False, "msg": f"查詢失敗，請稍後再試。"}

def create_flex_message(data):
    """ 產生 Line Flex Message 卡片 """
    bubble = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text="📦 物流追蹤結果", weight='bold', size='xl', color='#EE4D2D'),
                BoxComponent(
                    layout='vertical',
                    margin='lg',
                    contents=[
                        BoxComponent(
                            layout='baseline',
                            spacing='sm',
                            contents=[
                                TextComponent(text='單號', color='#aaaaaa', size='sm', flex=1),
                                TextComponent(text=data['no'], wrap=True, color='#666666', size='sm', flex=5)
                            ]
                        ),
                        BoxComponent(
                            layout='baseline',
                            spacing='sm',
                            contents=[
                                TextComponent(text='狀態', color='#aaaaaa', size='sm', flex=1),
                                TextComponent(text=data['status'], wrap=True, color='#333333', size='md', flex=5, weight='bold')
                            ]
                        ),
                        BoxComponent(
                            layout='baseline',
                            spacing='sm',
                            contents=[
                                TextComponent(text='時間', color='#aaaaaa', size='sm', flex=1),
                                TextComponent(text=data['time'], wrap=True, color='#666666', size='xs', flex=5)
                            ]
                        )
                    ]
                )
            ]
        ),
        footer=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text="資料來源：蝦皮購物", size='xs', color='#cccccc', align='center')
            ]
        )
    )
    return FlexSendMessage(alt_text=f"物流狀態: {data['status']}", contents=bubble)

@app.route("/", methods=['GET'])
def hello():
    return "Shopee Bot is running!"

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
    
    # 簡易判斷：通常蝦皮單號包含 TW 或 長度大於 10
    if len(user_text) >= 10:
        result = get_shopee_tracking(user_text)
        if result["success"]:
            line_bot_api.reply_message(event.reply_token, create_flex_message(result))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result["msg"]))

# 這是 Vercel 需要的進入點
def handler_entry(request):
    return app(request)
