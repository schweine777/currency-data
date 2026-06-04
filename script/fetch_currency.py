import urllib.request
import json
import os
from datetime import datetime
import pytz

def fetch_exchange_rates():
    url = "https://finance.naver.com/marketindex/exchangeList.nhn"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('euc-kr')
            
            import pandas as pd
            tables = pd.read_html(html, encoding='euc-kr')
            df = tables[0]
            
            rates = []
            for index, row in df.iterrows():
                rates.append({
                    "country": row['통화명'].strip(),
                    "standard_rate": str(row['매매기준율']),
                    "fluctuation": str(row['전일대비'])
                })
            return rates
            
    except Exception as e:
        print(f"Error fetching data: {e}")
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
    
    # Ensure data directory exists within the script folder context during local runs, 
    # but the GitHub Action will handle its own paths.
    os.makedirs('data', exist_ok=True)
    
    filename = f"data/{date_str}_currency.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    with open("data/latest_currency.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved to {filename}")

if __name__ == "__main__":
    main()
