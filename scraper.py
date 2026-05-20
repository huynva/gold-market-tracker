import cloudscraper
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

# 3. ĐỘNG CƠ BTMH (Áp dụng đúng logic F12 của Forge Master)
def get_btmh_price():
    try:
        res = scraper.get('https://webgia.com/gia-vang/bao-tin-manh-hai/', timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Quét từng dòng <tr> trong bảng
        for tr in soup.find_all('tr'):
            # Kiểm tra xem dòng này có chứa thẻ <th> với chữ "Hoa Sen" không
            th = tr.find('th')
            if th and 'hoa sen' in th.text.lower():
                
                # NẾU ĐÚNG SẢN PHẨM: Lấy ngay thẻ <td> class "text-right" đầu tiên trong cùng dòng đó (Giá Mua)
                td = tr.find('td', class_='text-right')
                if td:
                    # Bóc tách số thuần túy
                    raw_text = td.text.strip().replace('.', '').replace(',', '').replace('đ', '')
                    if raw_text:
                        val = float(raw_text)
                        
                        # Quy chuẩn (Nếu Webgia hiển thị 15900 thay vì 15.900.000)
                        if val < 1000000: val *= 1000
                        if val > 100000000: val /= 10
                        
                        print(f"[BTMH] 🎯 Bắt chuẩn giá từ F12: {val}")
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
        
        # TÔI VẪN GIỮ CỘT HUY THANH BỊ BỎ TRỐNG ĐỂ OBSIDIAN KHÔNG BỊ LỖI DATAVIEW
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            
        writer.writerow([date_str, time_str, world_price, btmh_price, ''])
        
    print(f"✅ Ghi thành công: TG={world_price}, BTMH={btmh_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, BTMH={btmh_price}")
