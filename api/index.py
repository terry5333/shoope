import re
from bs4 import BeautifulSoup

def get_shopee_tracking(tracking_no):
    # 直接爬網頁，不爬 API
    url = f"https://spx.tw/detail/{tracking_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    
    try:
        # 1. 抓取網頁原始碼
        response = requests.get(url, headers=headers, timeout=10)
        html_content = response.text
        
        # 2. 如果網頁裡有把資料藏在一個 script 標籤裡（常見做法）
        # 我們試著用正規表達式 (Regex) 把物流狀態直接抓出來
        # 這裡我們找描述物流狀態的文字規律
        status_pattern = r'"status_description":"([^"]+)"'
        time_pattern = r'"status_time":"([^"]+)"'
        
        statuses = re.findall(status_pattern, html_content)
        times = re.findall(time_pattern, html_content)
        
        if statuses and times:
            return {
                "success": True,
                "status": statuses[0], # 第一筆通常是最新的
                "time": times[0],
                "no": tracking_no
            }
        
        # 3. 如果找不到，可能是因為網頁沒渲染，這就是直接爬的極限
        return {"success": False, "msg": "⚠️ 網頁內容加密中，無法直接讀取文字"}
            
    except Exception as e:
        return {"success": False, "msg": "❌ 無法讀取網頁"}
