def get_shopee_tracking(tracking_no):
    # 這裡請貼上你剛才部署完 GAS 的那個 /exec 結尾的網址
    gas_api_url = "https://script.google.com/macros/s/AKfycbw7XZr5X9wQWLsJJl40vJo78Hj8trLVIyjf1aQEYOu8JJ4jH9yB5DUtXnCMNWZ6JqeaqQ/exec" 
    
    try:
        # 向 GAS 發送請求，讓 Google 幫你爬
        res = requests.get(f"{gas_api_url}?no={tracking_no}", timeout=15)
        data = res.json()
        
        if data.get("data") and data["data"].get("tracking_results"):
            latest = data["data"]["tracking_results"][0]
            status = latest.get("status_description", "更新中")
            time_str = latest.get("status_time", "時間確認中")
            return f"📦 單號: {tracking_no}\n📍 狀態: {status}\n⏰ 時間: {time_str}"
        else:
            return "⚠️ 目前查無資料，請確認單號正確且已寄出。"
            
    except Exception as e:
        return f"❌ 查詢超時或連線失敗，請稍後再試。"
