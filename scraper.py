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

# 2. ĐỘNG CƠ TỶ GIÁ THẾ GIỚI VÀ VIETCOMBANK
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

# 3. ĐỘNG CƠ BẮN TỈA BTMH VÀ HUY THANH
def get_domestic_price(url, brand):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if not table: return None
        
        for row in table.find_all('tr'):
            row_text = row.get_text().lower()
            
            # KHÓA MỤC TIÊU 1: BTMH - Tìm đúng Đồng vàng Kim Gia Bảo Hoa Sen
            if brand == 'BTMH' and 'hoa sen' not in row_text:
                continue
                
            # KHÓA MỤC TIÊU 2: HT - Tìm nhẫn
            if brand == 'HT' and 'nhẫn' not in row_text:
                continue
                
            # Dựa vào F12 của Forge Master: Bắt thẻ td có class "text-right"
            price_cols = row.find_all('td', class_='text-right')
            if not price_cols:
                price_cols = row.find_all('td')
                
            if len(price_cols) >= 1:
                # Giá Mua Vào luôn nằm ở cột số đầu tiên
                raw_text = price_cols[0].text.strip().replace(',', '').replace('.', '')
                try:
                    val = float(raw_text)
                    if val < 1000000: val *= 1000
                    if val > 100000000: val /= 10
                    if val > 1000000: 
                        return round(val, 0)
                except:
                    pass
        return None
    except:
        return None

# Kích hoạt hệ thống quét 
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
