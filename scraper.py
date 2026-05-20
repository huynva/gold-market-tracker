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

# 2. ĐỘNG CƠ TỶ GIÁ THẾ GIỚI
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
                usd_vnd = float(exrate.get('Sell').replace(',', '').replace('.', ''))
                break
        if usd_vnd:
            return round((usd_oz * usd_vnd) / 8.29426, 0)
    except Exception as e:
        print(f"Lỗi cào TG: {e}")
        return None

# 3. ĐỘNG CƠ CÀO CHÍNH (Từ Web chủ dựa theo F12)
def get_official_price(brand):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        if brand == 'HT':
            res = requests.get("https://www.huythanhjewelry.vn/", headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            price_td = soup.find('td', class_=lambda c: c and 'text-[#1d2a3d]' in c and 'text-[15px]' in c)
            if price_td:
                val = float(price_td.text.replace('đ', '').replace('.', '').replace(',', '').strip())
                return round(val / 10, 0) if val > 100000000 else round(val, 0)
            return None
            
        elif brand == 'BTMC':
            res = requests.get("https://btmc.vn/", headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            price_span = soup.find('span', class_=lambda c: c and 'text-text-dark' in c and 'font-semibold' in c)
            if price_span:
                val = float(price_span.text.replace('đ', '').replace('.', '').replace(',', '').strip())
                return round(val / 10, 0) if val > 100000000 else round(val, 0)
            return None
    except Exception as e:
        print(f"Trang chủ {brand} chặn Bot: {e}")
        return None

# 4. ĐỘNG CƠ DỰ PHÒNG (Fallback Webgia)
def get_fallback_price(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if not table: return None
        for row in table.find_all('tr'):
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 3:
                buy_val = float(cols[1].text.strip().replace(',', '').replace('.', ''))
                if buy_val < 1000000: buy_val *= 1000 
                return round(buy_val / 10, 0) if (buy_val / 10) > 1000000 else None
        return None
    except:
        return None

# KÍCH HOẠT QUÉT
world_price = get_world_price()
btmc_price = get_official_price('BTMC')
ht_price = get_official_price('HT')

# Rẽ nhánh nếu bị Cloudflare chặn
if not btmc_price:
    print("⚠️ Bật radar phụ cho BTMC...")
    btmc_price = get_fallback_price('https://webgia.com/gia-vang/bao-tin-minh-chau/')
if not ht_price:
    print("⚠️ Bật radar phụ cho Huy Thanh...")
    ht_price = get_fallback_price('https://webgia.com/gia-vang/huy-thanh/')

# 5. GHI DỮ LIỆU
if world_price and btmc_price and ht_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMCPrice', 'HuyThanhPrice'])
        writer.writerow([date_str, time_str, world_price, btmc_price, ht_price])
    print(f"✅ Ghi thành công: TG={world_price}, BTMC={btmc_price}, HT={ht_price}")
else:
    print("❌ Thất bại: Không kéo đủ dữ liệu 3 trục.")
