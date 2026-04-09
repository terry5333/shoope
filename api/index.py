def get_shopee_tracking(tracking_no):
    # 這是 spx.tw 專用的 API 節點
    url = "https://spx.tw/api/v2/fleet_order/tracking_search"
    
    # 根據網址分析，主要的參數是這個
    params = {
        "sls_tracking_number": tracking_no,
        "device_id": "line-bot-query" # 模擬設備 ID
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Referer": f"https://spx.tw/detail/{tracking_no}",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        # 使用 requests 抓取 JSON
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # 偵錯用：在 Vercel Logs 可以看到
        print(f"查詢單號: {tracking_no}, 狀態碼: {response.status_code}")
        
        if response.status_code != 200:
            return {"success": False, "msg": f"❌ 蝦皮伺服器回應錯誤 (代碼: {response.status_code})"}
            
        data = response.json()
        
        # 檢查資料層級：data -> tracking_results
        if data.get("data") and data["data"].get("tracking_results"):
            results = data["data"]["tracking_results"]
            # 取得最上面的一筆資訊
            latest = results[0]
            
            return {
                "success": True,
                "status": latest.get("status_description", "無狀態說明"),
                "time": latest.get("status_time", "無時間資訊"),
                "no": tracking_no
            }
        else:
            # 如果 API 有回傳訊息就顯示，否則顯示預設
            error_msg = data.get("message", "查無此單號，請確認輸入是否正確")
            return {"success": False, "msg": f"⚠️ {error_msg}"}
            
    except Exception as e:
        print(f"錯誤詳情: {str(e)}")
        return {"success": False, "msg": "❌ 連線失敗，可能蝦皮正在維護中"}
