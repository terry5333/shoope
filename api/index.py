import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, BubbleContainer, TextComponent, BoxComponent
)

# --- 核心重點：Vercel 會尋找這個在最外層的 app 變數 ---
app = Flask(__name__)

# 從環境變數取得 Line 密鑰
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_shopee_tracking(tracking_no):
    """ 爬取蝦皮店到店(SPX)物流資訊 """
    url = "https://spx.tw/api/v2/fleet_order/tracking_search"
    params = {
        "sls_tracking_number": tracking_no,
        "device_id": "line-bot-query" 
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Referer": f"https://spx.tw/detail/{tracking_no}",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"success": False, "msg": f"❌ 蝦皮伺服器回應錯誤 (代碼: {response.status_code})"}
            
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
            error_msg = data.get("message", "查無此單號，請確認輸入是否正確")
            return {"success": False, "msg": f"⚠️ {error_msg}"}
            
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        return {"success": False, "msg": "❌ 連線失敗，請稍後再試"}

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
def home():
    return "Line Bot is running successfully!"

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
    
    # 只要輸入長度大於等於 10 個字元，就當作單號去查詢
    if len(user_text) >= 10:
        result = get_shopee_tracking(user_text)
        if result["success"]:
            line_bot_api.reply_message(event.reply_token, create_flex_message(result))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result["msg"]))

