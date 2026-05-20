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
                usd_vnd = float(exrate.get('Sell').replace(',', '').replace('.', ''))
                break
        
        if usd_vnd:
            price_vnd_chi = (usd_oz * usd_vnd) / 8.29426
            return round(price_vnd_chi, 0)
    except Exception as e:
        print(f"Lỗi cào TG/VCB: {e}")
        return None

# 3. ĐỘNG CƠ CÀO CHÍNH XÁC THEO THẺ HTML (Dựa trên F12 của Forge Master)
def get_official_price(brand):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        if brand == 'HT':
            res = requests.get("https://www.huythanhjewelry.vn/", headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Quét tìm dòng thời gian cập nhật của Huy Thanh và in ra log
            time_p = soup.find('p', class_=lambda c: c and 'text-[#666]' in c and 'Cập nhật' in c)
            if time_p:
                print(f"[Huy Thanh Radar] {time_p.text.strip()}")
            
            # Quét tìm chính xác thẻ <td> chứa giá mà anh đã bắt được
            price_td = soup.find('td', class_=lambda c: c and 'text-[#1d2a3d]' in c and 'text-[15px]' in c)
            if price_td:
                # Làm sạch chữ 'đ' và các dấu chấm
                raw_text = price_td.text.replace('đ', '').replace('.', '').replace(',', '').strip()
                val = float(raw_text)
                
                # Trí tuệ nhân tạo nhận diện Đơn vị: 
                # Nếu giá > 100 triệu (nghĩa là họ đang niêm yết giá 1 Lượng), thì chia 10 để ra 1 Chỉ
                if val > 100000000:
                    return round(val / 10, 0)
                return round(val, 0) # Ngược lại (ví dụ 15.850.000) thì chính xác là giá 1 Chỉ rồi
            return None
            
        elif brand == 'BTMC':
            res = requests.get("https://btmc.vn/", headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Quét tìm chính xác thẻ <span> chứa giá BTMC
            price_span = soup.find('span', class_=lambda c: c and 'text-text-dark' in c and 'font-semibold' in c)
            if price_span:
                raw_text = price_span.text.replace('đ', '').replace('.', '').replace(',', '').strip()
                val = float(raw_text)
                if val > 100000000:
                    return round(val / 10, 0)
                return round(val, 0)
            return None

    except Exception as e:
        print(f"Lỗi cào {brand}: {e}")
        return None

world_price = get_world_price()
btmc_price = get_official_price('BTMC')
ht_price = get_official_price('HT')

# 4. GHI DỮ LIỆU
if world_price and btmc_price and ht_price:
    file_exists = os.path.isfile('gold_market_log.csv')
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMCPrice', 'HuyThanhPrice'])
        writer.writerow([date_str, time_str, world_price, btmc_price, ht_price])
    print(f"✅ Đã ghi thành công! TG(VCB)={world_price}, BTMC={btmc_price}, HT={ht_price}")
else:
    print("❌ Lỗi dữ liệu hoặc Website đổi cấu trúc.")
