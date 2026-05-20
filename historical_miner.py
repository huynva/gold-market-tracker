import cloudscraper
import csv
from datetime import datetime
import os
import xml.etree.ElementTree as ET
import re

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def mine_historical_data():
    try:
        print("1. Đang cào dữ liệu lịch sử Vàng Thế Giới từ Yahoo...")
        yahoo_url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1y&interval=1d"
        res_yahoo = scraper.get(yahoo_url, timeout=20)
        yahoo_data = res_yahoo.json()['chart']['result'][0]
        
        timestamps = yahoo_data['timestamp']
        close_prices = yahoo_data['indicators']['quote'][0]['close']
        usd_vnd_fixed = 25450 
        
        print("2. Đang cào dữ liệu lịch sử Vàng Nội Địa từ API BTMC...")
        btmc_chart_url = "http://api.btmc.vn/api/BTMCAPI/getchartbtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v"
        res_btmc = scraper.get(btmc_chart_url, timeout=20)
        raw_text = res_btmc.text
        
        def find_btmc_price_by_date(date_str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            y = date_obj.year
            m = date_obj.month - 1 
            d = date_obj.day
            pattern = fr"Date\.UTC\({y},\s*{m},\s*{d}\),\s*(\d+)"
            match = re.search(pattern, raw_text)
            if match:
                price = float(match.group(1))
                if price > 10000000: price /= 10 
                return round(price, 0)
            return ''

        historical_records = []
        print("3. Đang xử lý đồng bộ chuỗi thời gian...")
        for i in range(len(timestamps)):
            if not close_prices[i]: continue
            dt_obj = datetime.fromtimestamp(timestamps[i])
            date_str = dt_obj.strftime('%Y-%m-%d')
            time_str = "00:00"
            
            world_vnd = round((close_prices[i] * usd_vnd_fixed) / 8.29426, 0)
            btmc_price = find_btmc_price_by_date(date_str)
            
            # Đẩy vào mảng theo cấu trúc chuẩn 5 cột của Obsidian
            historical_records.append([date_str, time_str, world_vnd, btmc_price, ''])
            
        # GHI ĐÈ THẲNG VÀO FILE GỐC CỦA HỆ THỐNG
        filename = 'gold_market_log.csv'
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Time', 'WorldPrice', 'BTMHPrice', 'HuyThanhPrice'])
            writer.writerows(historical_records)
            
        print(f"✅ Đã tạo thành công {len(historical_records)} ngày lịch sử vào '{filename}'!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == '__main__':
    mine_historical_data()
