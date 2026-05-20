import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import pytz
import os
import xml.etree.ElementTree as ET

# 1. Cấu hình Múi giờ
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(vn_tz)
date_str = now.strftime('%Y-%m-%d')
time_str = now.strftime('%H:%M')

# 2. ĐỘNG CƠ THẾ GIỚI
def get_world_price():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res_gold = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", timeout=15)
        usd_oz = res_gold.json()['chart']['result'][0]['meta']['regularMarketPrice']
        
        res_vcb = requests.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", timeout=15)
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

# 3. ĐỘNG CƠ BẮT API TRỰC TIẾP (Bảo Tín Minh Châu)
def get_api_price():
    try:
        # Gọi thẳng vào máy chủ API
        res = requests.get('http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v', timeout=15)
        
        # API trả về chuỗi XML, dùng html.parser để phân tích các thuộc tính
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Quét tất cả các thẻ <Data>
        data_tags = soup.find_all('data')
        for tag in data_tags:
            row_id = tag.get('row')
            if not row_id: continue
            
            # Khởi tạo Key động dựa trên ID của dòng
            name_key = f'n_{row_id}'
            buy_key = f'pb_{row_id}'
            sell_key = f'ps_{row_id}'
            time_key = f'd_{row_id}'
            
            name_attr = tag.get(name_key, '').lower()
            
            # Định vị đúng Nhẫn Tròn Trơn
            if 'nhẫn tròn trơn' in name_attr or 'rồng thăng long' in name_attr:
                buy_val = float(tag.get(buy_key, 0))
                sell_val = float(tag.get(sell_key, 0))
                update_time = tag.get(time_key, 'N/A')
                
                # In báo cáo chi tiết ra Hộp đen
                print("========================================")
                print(f"🔥 [API BTMC] Dữ liệu Cập nhật: {update_time}")
                print(f"   👉 Giá Thu Mua (pb) : {buy_val:,.0f} VNĐ")
                print(f"   👉 Giá Bán Ra  (ps) : {sell_val:,.0f} VNĐ")
                print("========================================")
                
                # Trả về Giá Thu Mua để đưa vào biểu đồ Net Worth
                return round(buy_val, 0)
                
        print("[API BTMC] Không tìm thấy Nhẫn Tròn Trơn.")
        return None
    except Exception as e:
        print(f"[API BTMC] Lỗi kết nối: {e}")
        return None

world_price = get_world_price()
# Dùng chung biến btmh_price để đại diện cho Nội Địa, giữ cấu trúc file CSV cũ
btmh_price = get_api_price()

# 4. GHI DỮ LIỆU ĐỂ OBSIDIAN ĐỒNG BỘ
if world_price and btmh_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Giữ nguyên Header cũ để DataviewJS trong Obsidian không bị lỗi Index
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            
        writer.writerow([date_str, time_str, world_price, btmh_price, ''])
        
    print(f"✅ Ghi thành công: TG={world_price}, Nội Địa={btmh_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, Nội Địa={btmh_price}")
