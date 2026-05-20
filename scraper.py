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

# 3. ĐỘNG CƠ RADAR TOÀN VÙNG (Quét mọi bảng trên Webgia)
def get_domestic_price(url, brand):
    # Trang bị Header xịn để không bị Webgia chặn
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # SỬA LỖI TRÍ MẠNG CHỖ NÀY: Quét TẤT CẢ các bảng (tables) thay vì chỉ bảng đầu tiên
        tables = soup.find_all('table')
        
        for table in tables:
            for row in table.find_all('tr'):
                row_text = row.get_text().lower()
                
                # Khóa mục tiêu
                if brand == 'BTMH' and 'hoa sen' not in row_text:
                    continue
                if brand == 'HT' and 'nhẫn' not in row_text:
                    continue
                    
                # Rà soát tất cả các cột td trong dòng mục tiêu
                price_cols = row.find_all('td')
                
                for col in price_cols:
                    # Làm sạch mọi ký tự thừa (đ, dấu chấm, phẩy, khoảng trắng)
                    raw_text = col.text.strip().replace('đ', '').replace(',', '').replace('.', '')
                    
                    # Nếu nội dung còn lại là một con số thuần túy
                    if raw_text.isdigit():
                        val = float(raw_text)
                        # Bộ lọc quy chuẩn (Ngàn -> Triệu -> Lượng)
                        if val < 1000000: val *= 1000      
                        if val > 100000000: val /= 10      
                        
                        if val > 1000000: 
                            return round(val, 0) # Trả về ngay con số MUA VÀO (cột đầu tiên) và ngắt radar
                            
        return None # Nếu quét sạch sành sanh các bảng mà không thấy
    except Exception as e:
        print(f"Lỗi {brand}: {e}")
        return None

# Kích hoạt hệ thống
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
