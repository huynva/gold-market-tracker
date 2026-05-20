import requests
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

def get_world_price():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res_gold = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", headers=headers)
        usd_oz = res_gold.json()['chart']['result'][0]['meta']['regularMarketPrice']
        
        res_vcb = requests.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", headers=headers)
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

# 3. ĐỘNG CƠ LAI (TÌM TÊN CHUẨN -> VẮT SỐ CHUẨN)
def get_domestic_price(url, brand):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                row_text = row.get_text().lower()
                
                # BƯỚC 1: NHẬN DIỆN MẶT MỤC TIÊU (Loại trừ Vàng Trang Sức, bám sát Hoa Sen/Nhẫn)
                if brand == 'BTMH' and 'hoa sen' not in row_text:
                    continue
                if brand == 'HT' and 'nhẫn' not in row_text:
                    continue
                    
                # BƯỚC 2: VẮT SỐ BẰNG TOÁN HỌC (Chỉ áp dụng cho dòng đã khóa mục tiêu)
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    for col in cols[1:]: # Bỏ qua cột số 0 chứa cái Tên
                        digits = re.sub(r'\D', '', col.get_text())
                        if digits:
                            val = float(digits)
                            
                            # Tự động quy chuẩn đơn vị
                            if val < 1000000: val *= 1000      
                            if val > 100000000: val /= 10      
                            
                            # Xác thực mốc giá chuẩn
                            if 5000000 <= val <= 30000000:
                                return round(val, 0) # Rút súng bắn đúng giá Mua vào và té!
        return None
    except Exception as e:
        print(f"Lỗi: {e}")
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
