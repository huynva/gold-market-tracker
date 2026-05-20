import cloudscraper
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import pytz
import os
import xml.etree.ElementTree as ET
import re

# 1. Cấu hình Múi giờ
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(vn_tz)
date_str = now.strftime('%Y-%m-%d')
time_str = now.strftime('%H:%M')

# KHỞI TẠO ÁO TÀNG HÌNH ĐỂ XUYÊN QUA WEB INTERMEDIATE
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def get_world_price():
    try:
        res_gold = scraper.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", timeout=15)
        usd_oz = res_gold.json()['chart']['result'][0]['meta']['regularMarketPrice']
        
        res_vcb = scraper.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", timeout=15)
        root = ET.fromstring(res_vcb.text)
        usd_vnd = None
        for exrate in root.findall('Exrate'):
            if exrate.get('CurrencyCode') == 'USD':
                usd_vnd = float(exrate.get('Sell').replace(',', ''))
                break
        if usd_vnd:
            return round((usd_oz * usd_vnd) / 8.29426, 0)
    except:
        return None

# 3. ĐỘNG CƠ LAI + CẢM BIẾN X-RAY
def get_domestic_price(url, brand):
    try:
        res = scraper.get(url, timeout=15)
        
        # X-Ray 1: Kiểm tra xem Webgia có chặn IP không
        print(f"[{brand}] Mã phản hồi mạng: {res.status_code}")
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        tables = soup.find_all('table')
        
        # X-Ray 2: Kiểm tra xem có cấu trúc Bảng không
        if not tables:
            print(f"[{brand}] ❌ Không tìm thấy thẻ <table> nào! Giao diện web đã bị thay đổi.")
            return None

        for table in tables:
            for row in table.find_all('tr'):
                row_text = row.get_text().lower()
                
                # Mở rộng từ khóa cho Huy Thanh để tránh web viết tắt
                if brand == 'BTMH' and 'hoa sen' not in row_text:
                    continue
                if brand == 'HT' and not any(k in row_text for k in ['nhẫn', '24k', '999']):
                    continue
                    
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    for col in cols[1:]: 
                        digits = re.sub(r'\D', '', col.get_text())
                        if digits:
                            val = float(digits)
                            if val < 1000000: val *= 1000      
                            if val > 100000000: val /= 10      
                            
                            if 5000000 <= val <= 30000000:
                                # X-Ray 3: Báo cáo đã ngắm trúng mục tiêu nào
                                print(f"[{brand}] 🎯 Đã vớt được số từ dòng: '{row_text.strip()}' -> Mua vào: {val}")
                                return round(val, 0)
                                
        print(f"[{brand}] ❌ Quét sạch bảng nhưng không tìm thấy từ khóa hợp lệ!")
        return None
    except Exception as e:
        print(f"Lỗi [{brand}]: {e}")
        return None

# Cấp lại tham số truyền mục tiêu
world_price = get_world_price()
btmh_price = get_domestic_price('https://webgia.com/gia-vang/bao-tin-manh-hai/', 'BTMH')
ht_price = get_domestic_price('https://webgia.com/gia-vang/huy-thanh/', 'HT')

# 4. GHI DỮ LIỆU
if world_price and btmh_price and ht_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
        writer.writerow([date_str, time_str, world_price, btmh_price, ht_price])
    print(f"✅ Ghi thành công: TG={world_price}, BTMH={btmh_price}, HT={ht_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, BTMH={btmh_price}, HT={ht_price}")
