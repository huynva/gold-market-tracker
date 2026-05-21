import cloudscraper
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

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

# 2. ĐỘNG CƠ THẾ GIỚI
def get_world_price():
    try:
        res_gold = scraper.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", timeout=20)
        
        if res_gold.status_code != 200:
            print(f"[TG] Bị Yahoo chặn. Mã lỗi: {res_gold.status_code}")
            return None
            
        usd_oz = res_gold.json()['chart']['result'][0]['meta']['regularMarketPrice']
        
        res_vcb = scraper.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", timeout=20)
        root = ET.fromstring(res_vcb.text)
        usd_vnd = None
        for exrate in root.findall('Exrate'):
            if exrate.get('CurrencyCode') == 'USD':
                usd_vnd = float(exrate.get('Sell').replace(',', ''))
                break
                
        if usd_vnd:
            return round((usd_oz * usd_vnd) / 8.29426, 0)
    except Exception as e:
        print(f"[TG] Lỗi: {e}")
        return None

# 3. ĐỘNG CƠ API BTMC (Khóa mục tiêu tuyệt đối)
def get_api_price():
    try:
        res = scraper.get('http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v', timeout=20)
        raw_text = res.text
        
        data_tags = re.findall(r'<Data\s+[^>]+>', raw_text, re.IGNORECASE)
        
        for tag in data_tags:
            row_match = re.search(r'row="(\d+)"', tag, re.IGNORECASE)
            if not row_match: continue
            row_id = row_match.group(1)
            
            name_match = re.search(fr'n_{row_id}="([^"]+)"', tag, re.IGNORECASE)
            if not name_match: continue
            name_attr = name_match.group(1).lower().strip()
            
            # SỬA LỖI CHÍ MẠNG: Bắt buộc phải giống y hệt chuỗi tên sản phẩm anh cung cấp
            if name_attr == 'nhẫn tròn trơn (vàng rồng thăng long)':
                pb_match = re.search(fr'pb_{row_id}="(\d+)"', tag, re.IGNORECASE)
                ps_match = re.search(fr'ps_{row_id}="(\d+)"', tag, re.IGNORECASE)
                d_match = re.search(fr'd_{row_id}="([^"]+)"', tag, re.IGNORECASE)
                
                buy_val = float(pb_match.group(1)) if pb_match else 0
                sell_val = float(ps_match.group(1)) if ps_match else 0
                update_time = d_match.group(1) if d_match else 'N/A'
                
                print("========================================")
                print(f"🔥 [API BTMC] Dữ liệu Cập nhật: {update_time}")
                print(f"   👉 Tên Sản Phẩm     : {name_match.group(1)}")
                print(f"   👉 Giá Thu Mua (pb) : {buy_val:,.0f} VNĐ")
                print(f"   👉 Giá Bán Ra  (ps) : {sell_val:,.0f} VNĐ")
                print("========================================")
                
                return round(buy_val, 0)
                
        print("[API BTMC] Quét sạch API nhưng không thấy đúng cụm từ Nhẫn Tròn Trơn!")
        return None
    except Exception as e:
        print(f"[API BTMC] Lỗi: {e}")
        return None

world_price = get_world_price()
btmh_price = get_api_price()

# 4. GHI DỮ LIỆU ĐỂ OBSIDIAN ĐỒNG BỘ
if world_price and btmh_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
        writer.writerow([date_str, time_str, world_price, btmh_price, ''])
    print(f"✅ Ghi thành công: TG={world_price}, Nội Địa={btmh_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, Nội Địa={btmh_price}")
