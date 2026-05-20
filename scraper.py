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

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

# 2. ĐỘNG CƠ THẾ GIỚI
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

# 3. ĐỘNG CƠ MẠNH HẢI
def get_btmh_price():
    try:
        res = scraper.get('https://webgia.com/gia-vang/bao-tin-manh-hai/', timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        elements = soup.find_all(['th', 'td'])
        found_target = False
        
        for el in elements:
            text = el.get_text().lower()
            
            if any(k in text for k in ['hoa sen', 'kim gia bảo']):
                found_target = True
                continue
                
            if found_target:
                digits = re.sub(r'\D', '', text)
                if digits:
                    val = float(digits)
                    
                    # BỘ LỌC CHỐNG NHIỄU: Xóa bỏ các thông số hàm lượng vàng
                    if val in [999, 9999, 24, 18, 14, 10]:
                        continue
                        
                    if val < 1000000: val *= 1000
                    if val > 100000000: val /= 10
                    
                    if 5000000 <= val <= 30000000:
                        print(f"[BTMH] 🎯 Bắt được giá: {val}")
                        return round(val, 0)
        return None
    except Exception as e:
        print(f"[BTMH] Lỗi: {e}")
        return None

# 4. ĐỘNG CƠ HUY THANH
def get_ht_price():
    try:
        res = scraper.get('https://www.huythanhjewelry.vn/', timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tds = soup.find_all('td', class_=lambda c: c and 'text-[#1d2a3d]' in c)
        for td in tds:
            digits = re.sub(r'\D', '', td.get_text())
            if digits:
                val = float(digits)
                if val in [999, 9999, 24]: continue
                if val < 1000000: val *= 1000
                if val > 100000000: val /= 10
                if 5000000 <= val <= 30000000:
                    print(f"[HT] 🎯 Bắt được giá: {val}")
                    return round(val, 0)
        return None
    except Exception as e:
        return None

world_price = get_world_price()
btmh_price = get_btmh_price()
ht_price = get_ht_price()

# 5. CƠ CHẾ LƯU TRỮ BAO DUNG (Chỉ cần Thế giới + 1 Nội địa là ghi mẻ)
if world_price and (btmh_price or ht_price):
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            
        # Nếu Huy Thanh bị Cloudflare chặn tạm thời, để trống ô đó để không bị lệch cột CSV
        btmh_csv = btmh_price if btmh_price else ''
        ht_csv = ht_price if ht_price else ''
        
        writer.writerow([date_str, time_str, world_price, btmh_csv, ht_csv])
    print(f"✅ Ghi thành công: TG={world_price}, BTMH={btmh_price}, HT={ht_price}")
else:
    print(f"❌ Thất bại: Thiếu dữ liệu mảng rộng (TG={world_price}, BTMH={btmh_price}, HT={ht_price})")
