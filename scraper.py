import cloudscraper
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import pytz
import os
import xml.etree.ElementTree as ET
import re  # Nạp module hóa giải Watermark

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

# 3. ĐỘNG CƠ BTMH (F12 + Xóa Watermark)
def get_btmh_price():
    try:
        res = scraper.get('https://webgia.com/gia-vang/bao-tin-manh-hai/', timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for tr in soup.find_all('tr'):
            th = tr.find('th')
            # Khóa mục tiêu chuẩn xác 100% bằng F12
            if th and 'hoa sen' in th.text.lower():
                
                # Quét các ô giá (text-right) nằm cùng dòng
                tds = tr.find_all('td', class_='text-right')
                for td in tds:
                    # BỘ LỌC WATERMARK: Tiêu diệt chữ "xem tại webgiacom", chỉ giữ lại 15900000
                    digits = re.sub(r'\D', '', td.text)
                    
                    if digits:
                        val = float(digits)
                        
                        # Quy chuẩn đơn vị
                        if val < 1000000: val *= 1000
                        if val > 100000000: val /= 10
                        
                        # Xác thực đây là giá tiền chứ không phải mã lẻ
                        if 5000000 <= val <= 30000000:
                            print(f"[BTMH] 🎯 Bắn hạ Watermark, lấy giá chuẩn: {val}")
                            return round(val, 0)
        return None
    except Exception as e:
        print(f"[BTMH] Lỗi: {e}")
        return None

world_price = get_world_price()
btmh_price = get_btmh_price()

# 4. GHI DỮ LIỆU
if world_price and btmh_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Giữ nguyên cấu trúc 5 cột cho Obsidian
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            
        writer.writerow([date_str, time_str, world_price, btmh_price, ''])
        
    print(f"✅ Ghi thành công: TG={world_price}, BTMH={btmh_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, BTMH={btmh_price}")
