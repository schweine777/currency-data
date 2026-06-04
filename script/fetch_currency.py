import urllib.request
import json
import os
import io
from datetime import datetime
import pytz

def fetch_exchange_rates():
    url = "https://finance.naver.com/marketindex/exchangeList.nhn"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('euc-kr')
            
            import pandas as pd
            # Use io.StringIO to handle raw HTML strings in newer pandas versions
            tables = pd.read_html(io.StringIO(html))
            df = tables[0]
            
            # Table Structure (by index):
            # 0: Currency Name, 1: Base Rate, 2: Cash Buy, 3: Cash Sell, 
            # 4: Send Money, 5: Receive Money, 6: USD Conversion Rate
            
            rates = []
            for index, row in df.iterrows():
                # Use iloc for position-based access to be robust against header name changes
                rates.append({
                    "country": str(row.iloc[0]).strip(),      # 통화명
                    "standard_rate": str(row.iloc[1]),        # 매매기준율
                    "buy": str(row.iloc[2]),                  # 현찰 사실 때
                    "sell": str(row.iloc[3]),                 # 현찰 파실 때
                    "send": str(row.iloc[4]),                 # 송금 보낼 때
                    "receive": str(row.iloc[5])               # 송금 받을 때
                })
            return rates
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    rates = fetch_exchange_rates()
    if not rates:
        import sys
        print("Failed to fetch rates. Exiting with error.")
        sys.exit(1)

    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)
    
    date_str = now.strftime('%Y%m%d')
    
    data = {
        "date": date_str,
        "update_time": now.strftime('%Y-%m-%d %H:%M:%S'),
        "rates": rates
    }
    
    os.makedirs('data', exist_ok=True)
    
    filename = f"data/{date_str}_currency.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    with open("data/latest_currency.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved to {filename}")

if __name__ == "__main__":
    main()
