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

# 3. ĐỘNG CƠ BTMH (Kết hợp F12 + Chống Nhiễu + Phá Watermark)
def get_btmh_price():
    try:
        res = scraper.get('https://webgia.com/gia-vang/bao-tin-manh-hai/', timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for tr in soup.find_all('tr'):
            # BƯỚC 1: NHẬN DIỆN MẶT MỤC TIÊU (Quét toàn bộ chữ trong dòng, không phân biệt th hay td)
            if 'hoa sen' in tr.get_text().lower():
                
                # BƯỚC 2: KHÓA TỌA ĐỘ THEO F12 CỦA FORGE MASTER
                tds = tr.find_all('td', class_='text-right')
                for td in tds:
                    # Gỡ Watermark rác, chỉ giữ lại số
                    digits = re.sub(r'\D', '', td.text)
                    
                    if digits:
                        val = float(digits)
                        
                        # Bộ lọc chống nhiễu (Đá bay mã vàng 999, 9999)
                        if val in [999, 9999, 24, 18]:
                            continue
                            
                        # Quy chuẩn đơn vị
                        if val < 1000000: val *= 1000
                        if val > 100000000: val /= 10
                        
                        # Chốt hạ con số chuẩn
                        if 5000000 <= val <= 30000000:
                            print(f"[BTMH] 🎯 Bắn hạ thành công: {val}")
                            return round(val, 0)
        return None
    except Exception as e:
        print(f"[BTMH] Lỗi: {e}")
        return None

world_price = get_world_price()
btmh_price = get_btmh_price()

# 4. GHI DỮ LIỆU ĐỂ OBSIDIAN ĐỒNG BỘ
if world_price and btmh_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Cột Huy Thanh được để chuỗi rỗng '' nhằm giữ nguyên cấu trúc 5 cột cho DataviewJS Obsidian
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            
        writer.writerow([date_str, time_str, world_price, btmh_price, ''])
        
    print(f"✅ Ghi thành công: TG={world_price}, BTMH={btmh_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, BTMH={btmh_price}")
