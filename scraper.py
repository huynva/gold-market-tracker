import yfinance as yf
import requests
import xml.etree.ElementTree as ET
import csv
import os
import pytz
from datetime import datetime
import re
import cloudscraper

# Cấu hình thời gian hiện tại
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(vn_tz)

# --- CÁC MODULE LÕI ---

def get_vcb_exchange_rate():
    try:
        res = requests.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", timeout=10)
        root = ET.fromstring(res.text)
        for exrate in root.findall('Exrate'):
            if exrate.get('CurrencyCode') == 'USD':
                return float(exrate.get('Sell').replace(',', ''))
    except Exception as e:
        print(f"[VCB] Lỗi tỷ giá: {e}")
    return 25450  # Tỷ giá dự phòng nếu VCB sập

def get_realtime_world(usd_vnd):
    try:
        gold = yf.Ticker("XAUUSD=X")
        xau_usd = gold.history(period="1d")['Close'].iloc[-1]
        return round((xau_usd * usd_vnd) / 8.29426, 0)
    except Exception as e:
        print(f"[TG] Lỗi Yahoo: {e}")
        return None

def get_realtime_domestic():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        res = scraper.get('http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v', timeout=20)
        data_tags = re.findall(r'<Data\s+[^>]+>', res.text, re.IGNORECASE)
        for tag in data_tags:
            row_match = re.search(r'row="(\d+)"', tag, re.IGNORECASE)
            if not row_match: continue
            row_id = row_match.group(1)
            
            name_match = re.search(fr'n_{row_id}="([^"]+)"', tag, re.IGNORECASE)
            if not name_match: continue
            
            if name_match.group(1).lower().strip() == 'nhẫn tròn trơn (vàng rồng thăng long)':
                pb_match = re.search(fr'pb_{row_id}="(\d+)"', tag, re.IGNORECASE)
                if pb_match: return float(pb_match.group(1))
    except Exception as e:
        print(f"[Nội Địa] Lỗi API: {e}")
    return None

def sync_history_if_needed(filename, usd_vnd):
    file_exists = os.path.isfile(filename)
    needs_sync = False
    
    # Kiểm tra xem file có trống hoặc chỉ có mỗi 1 dòng tiêu đề không
    if not file_exists:
        needs_sync = True
    else:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) <= 2: 
                needs_sync = True

    if needs_sync:
        print("🚀 Kích hoạt Động cơ Thời gian: Đồng bộ dữ liệu 1 năm quá khứ...")
        gold = yf.Ticker("XAUUSD=X")
        hist = gold.history(period="1y")
        records = []
        
        for date, row in hist.iterrows():
            world_price = round((row['Close'] * usd_vnd) / 8.29426, 0)
            domestic_price = world_price + 1500000  # Nội suy Biên độ 1.5 Triệu cho quá khứ
            date_str = date.strftime('%Y-%m-%d')
            records.append([date_str, '00:00', world_price, domestic_price, ''])
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            writer.writerows(records)
        print(f"✅ Đã nạp thành công {len(records)} ngày lịch sử vào hệ thống!")

# --- HỆ ĐIỀU HÀNH CHÍNH ---
def main():
    filename = 'gold_market_log.csv'
    usd_vnd = get_vcb_exchange_rate()
    
    # 1. Kích hoạt cơ chế Tự phục hồi (Backfill History)
    sync_history_if_needed(filename, usd_vnd)
    
    # 2. Thu thập dữ liệu Thời gian thực (Real-time Scraping)
    print("⚡ Đang quét giá Thời gian thực...")
    world_price = get_realtime_world(usd_vnd)
    domestic_price = get_realtime_domestic()
    
    # Tính năng Bọc thép: Nếu API Nội địa chết, dùng giá TG cộng biên độ để không gãy đồ thị Obsidian
    if not domestic_price and world_price:
        domestic_price = world_price + 1500000
        print("⚠️ Cảnh báo: API BTMC gián đoạn. Đã kích hoạt giá Nội địa dự phòng.")

    # 3. Ghi dữ liệu hiện tại vào cuối file CSV
    if world_price and domestic_price:
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M')
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([date_str, time_str, world_price, domestic_price, ''])
        print(f"✅ Đã chốt sổ: TG={world_price:,.0f} | Nội Địa={domestic_price:,.0f}")
    else:
        print("❌ Lỗi hệ thống: Không thể lấy dữ liệu.")

if __name__ == '__main__':
    main()
