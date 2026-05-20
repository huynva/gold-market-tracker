import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import pytz
import os

# 1. Cấu hình Múi giờ và Thời gian hiện tại
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(vn_tz)
date_str = now.strftime('%Y-%m-%d')
time_str = now.strftime('%H:%M')

# 2. Hàm cào dữ liệu (Mô phỏng bóc tách từ webgia.com)
def get_gold_price():
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # Cào giá BTMC
        res_btmc = requests.get('https://webgia.com/gia-vang/bao-tin-minh-chau/', headers=headers)
        soup_btmc = BeautifulSoup(res_btmc.text, 'html.parser')
        # Ghi chú: Tìm đúng class CSS chứa giá Mua vào của Vàng Rồng Thăng Long
        btmc_price = 8150000 # Placeholder: Thay bằng code bóc tách HTML thực tế của anh
        
        # Cào giá Huy Thanh (Tương tự)
        res_ht = requests.get('https://webgia.com/gia-vang/huy-thanh/', headers=headers)
        soup_ht = BeautifulSoup(res_ht.text, 'html.parser')
        ht_price = 8050000 # Placeholder
        
        # Cào giá Thế Giới (Có thể dùng Yahoo Finance API hoặc scrape)
        world_price = 7600000 # Placeholder
        
        return world_price, btmc_price, ht_price
    except Exception as e:
        print(f"Lỗi khi cào dữ liệu: {e}")
        return None, None, None

world, btmc, ht = get_gold_price()

# 3. Ghi nối vào file CSV
if world and btmc and ht:
    file_exists = os.path.isfile('gold_market_log.csv')
    
    with open('gold_market_log.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Nếu file chưa tồn tại, ghi dòng tiêu đề
        if not file_exists:
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMCPrice', 'HuyThanhPrice'])
        
        writer.writerow([date_str, time_str, world, btmc, ht])
    print(f"Đã cập nhật tỷ giá lúc {time_str} ngày {date_str}")
