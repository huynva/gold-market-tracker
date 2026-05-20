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

# Tạo Tàu Ngầm Cloudscraper với giáp dày
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

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

# 3. ĐỘNG CƠ BTMH (Tàu ngầm quét Radar)
def get_btmh_price():
    # Tiêm Headers mạnh để qua mặt Cloudflare
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }
    
    try:
        res = scraper.get('https://webgia.com/gia-vang/bao-tin-manh-hai/', headers=headers, timeout=20)
        
        # In mã phản hồi để nắm chắc tình hình cửa ải
        print(f"[X-RAY] Mã phản hồi Webgia: {res.status_code}")
        if res.status_code != 200:
            return None
            
        html = res.text
        
        # KỸ THUẬT VẮT RAW: Tìm khối HTML chứa Hoa Sen, vứt hết thẻ, chọc thủng Watermark
        # Tìm đoạn chứa Hoa Sen
        pattern_hoa_sen = r'hoa sen.*?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)'
        match = re.search(pattern_hoa_sen, html.lower(), re.IGNORECASE | re.DOTALL)
        
        if match:
             # Trích xuất chuỗi có vẻ là số
             raw_price = match.group(1)
             
             # Xóa sạch dấu phẩy/chấm
             clean_digits = re.sub(r'\D', '', raw_price)
             
             if clean_digits:
                 val = float(clean_digits)
                 
                 # Lọc rác 9999
                 if val in [999, 9999, 24, 18]:
                     # Nếu đụng mã vàng, tìm con số tiếp theo trong đoạn HTML
                     # (Phần này là cơ chế Fallback phòng trường hợp regex dính 9999)
                     pass
                 else:
                     # Quy chuẩn
                     if val < 1000000: val *= 1000
                     if val > 100000000: val /= 10
                     
                     if 5000000 <= val <= 30000000:
                         print(f"[BTMH] 🎯 Bắt được giá: {val}")
                         return round(val, 0)
                         
        # Nếu Regex đơn giản thất bại, dùng Regex lưới rộng bám theo chữ Hoa Sen
        # Kỹ thuật: Lọc toàn bộ text trên trang, tìm chữ Hoa Sen, rồi lấy con số thỏa điều kiện ngay sau nó
        text_only = re.sub(r'<[^>]+>', ' ', html).lower()
        parts = text_only.split('hoa sen')
        
        if len(parts) > 1:
            after_text = parts[1][:200] # Lấy 200 ký tự ngay sau chữ Hoa Sen
            
            # Tìm tất cả các cụm số
            number_clusters = re.findall(r'\d[\d.,]*', after_text)
            
            for cluster in number_clusters:
                 clean_num = re.sub(r'\D', '', cluster)
                 if clean_num:
                     val = float(clean_num)
                     if val in [999, 9999, 24, 18]: continue
                     if val < 1000000: val *= 1000
                     if val > 100000000: val /= 10
                     if 5000000 <= val <= 30000000:
                         print(f"[BTMH] 🎯 Bắn hạ bằng Lưới: {val}")
                         return round(val, 0)

        print("[BTMH] ❌ Radar không dò thấy số hợp lệ.")
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
        
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            
        writer.writerow([date_str, time_str, world_price, btmh_price, ''])
        
    print(f"✅ Ghi thành công: TG={world_price}, BTMH={btmh_price}")
else:
    print(f"❌ Thất bại: TG={world_price}, BTMH={btmh_price}")
