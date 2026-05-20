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

# Khởi tạo Áo Tàng Hình (Giả lập trình duyệt Chrome thật để xuyên Cloudflare)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

# 2. ĐỘNG CƠ TỶ GIÁ THẾ GIỚI
def get_world_price():
    try:
        res_gold = scraper.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F")
        usd_oz = res_gold.json()['chart']['result'][0]['meta']['regularMarketPrice']
        
        res_vcb = scraper.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx")
        root = ET.fromstring(res_vcb.text)
        usd_vnd = None
        for exrate in root.findall('Exrate'):
            if exrate.get('CurrencyCode') == 'USD':
                usd_vnd = float(exrate.get('Sell').replace(',', '').replace('.', ''))
                break
        if usd_vnd:
            return round((usd_oz * usd_vnd) / 8.29426, 0)
    except Exception as e:
        print(f"Lỗi cào TG: {e}")
        return None

# 3. ĐỘNG CƠ CÀO CHÍNH (Xuyên thẳng trang chủ)
def get_official_price(brand):
    try:
        if brand == 'HT':
            res = scraper.get("https://www.huythanhjewelry.vn/", timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            price_td = soup.find('td', class_=lambda c: c and 'text-[#1d2a3d]' in c and 'text-[15px]' in c)
            if price_td:
                val = float(price_td.text.replace('đ', '').replace('.', '').replace(',', '').strip())
                return round(val / 10, 0) if val > 100000000 else round(val, 0)
            return None
            
        elif brand == 'BTMC':
            res = scraper.get("https://btmc.vn/", timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            price_span = soup.find('span', class_=lambda c: c and 'text-text-dark' in c and 'font-semibold' in c)
            if price_span:
                val = float(price_span.text.replace('đ', '').replace('.', '').replace(',', '').strip())
                return round(val / 10, 0) if val > 100000000 else round(val, 0)
            return None
    except Exception as e:
        print(f"Lỗi cào {brand}: {e}")
        return None

# KÍCH HOẠT QUÉT
world_price = get_world_price()
btmc_price = get_official_price('BTMC')
ht_price = get_official_price('HT')

# 4. GHI DỮ LIỆU THỰC TẾ
if world_price and btmc_price and ht_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMCPrice', 'HuyThanhPrice'])
        writer.writerow([date_str, time_str, world_price, btmc_price, ht_price])
    print(f"✅ Ghi thành công: TG={world_price}, BTMC={btmc_price}, HT={ht_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, BTMC={btmc_price}, HT={ht_price}")
