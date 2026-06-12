import os
import sys
import subprocess
import importlib

def install_dependencies():
    """
    필요한 라이브러리가 설치되어 있는지 확인하고, 없으면 자동으로 설치합니다.
    """
    required_packages = ["yfinance", "matplotlib", "pandas", "requests"]
    missing_packages = []

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing packages found: {missing_packages}. Installing...")
        try:
            # --break-system-packages 플래그를 추가하여 macOS/Linux의 PEP 668 제한을 우회합니다.
            # 이는 시스템 환경에 패키지를 강제로 설치하므로, 가급적 가상환경 사용을 권장합니다.
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages + ["--break-system-packages"])
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            print("Please install them manually using: pip install " + " ".join(missing_packages))
            sys.exit(1)

# 의존성 체크를 먼저 수행
install_dependencies()

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import requests
import time

def send_telegram_message(message):
    """
    텔레그램 봇을 통해 메시지를 전송합니다.
    환경변수 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID가 필요합니다.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram configuration missing. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def generate_all_currency_graphs(currency_list):
    """
    제공된 통화 목록에 대해 환율 그래프를 생성합니다. (실패 시 3회 재시도)
    """
    base_output_dir = "graph"
    
    for code in currency_list:
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                # 폴더 이름은 영문 소문자 표기 (ex: usd, npr)
                folder_name = code.lower()
                currency_dir = os.path.join(base_output_dir, folder_name)
                
                if not os.path.exists(currency_dir):
                    os.makedirs(currency_dir, exist_ok=True)
                
                ticker = f"{code}KRW=X"
                
                # 100단위 환율 통화 리스트
                unit_100_currencies = ["JPY", "VND", "IDR"]
                is_100_unit = code in unit_100_currencies
                
                print(f"\n>>> Generating graphs for {code} (Attempt {retry_count + 1})...")
                generate_currency_graphs_for_code(ticker_symbol=ticker, currency_code=code, output_path=currency_dir, base_filename=code, is_100_unit=is_100_unit)
                
                success = True # 여기까지 오면 성공
            except Exception as e:
                retry_count += 1
                print(f"  Error generating graphs for {code}: {e}")
                if retry_count < max_retries:
                    print(f"  Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    error_msg = f"❌ [Graph Generator] Failed to generate graphs for {code} after {max_retries} attempts.\nError: {str(e)}"
                    send_telegram_message(error_msg)

def generate_currency_graphs_for_code(ticker_symbol, currency_code, output_path, base_filename, is_100_unit=False):
    """
    특정 통화의 기간별 그래프를 생성하여 지정된 폴더에 저장합니다.
    """
    # 1일(1d)을 제외한 나머지 기간 설정
    periods = [
        ("1주", "1wk", "1h"),
        ("1개월", "1mo", "1d"),
        ("3개월", "3mo", "1d"),
        ("6개월", "6mo", "1d"),
        ("1년", "1y", "1d"),
        ("3년", "3y", "1wk"),
        ("5년", "5y", "1wk"),
        ("10년", "10y", "1mo"),
    ]

    # 현재 시간 (한국 시간)
    now = datetime.now().astimezone(pd.Timestamp.now(tz='Asia/Seoul').tz)

    for label, period, interval in periods:
        filename = f"{base_filename}_{period}.png"
        filepath = os.path.join(output_path, filename)
        
        # 데이터 다운로드
        try:
            # 유효 데이터 추출 함수
            def get_valid_series(df):
                if df is None or df.empty:
                    return pd.Series(dtype='float64')
                if 'Close' in df.columns:
                    s = df['Close'].dropna()
                else:
                    try:
                        s = df.xs('Close', axis=1, level=0).dropna()
                    except:
                        return pd.Series(dtype='float64')
                if isinstance(s, pd.DataFrame):
                    s = s.iloc[:, 0]
                return s

            # 1순위: 직접 환율 시도
            data = yf.download(tickers=ticker_symbol, period=period, interval=interval, progress=False)
            valid_close = get_valid_series(data)

            # 2순위: 직접 환율 데이터가 부족하면 교차 환율(Cross Rate) 계산 (USD 기준)
            if len(valid_close) < 2 and currency_code != "USD":
                print(f"  Note: Direct ticker {ticker_symbol} has insufficient data ({len(valid_close)} pts). Attempting cross-rate...")
                
                # USD/KRW 기준 데이터 가져오기
                usd_krw = yf.download(tickers="USDKRW=X", period=period, interval=interval, progress=False)
                # 대상 통화의 USD 환율 가져오기
                target_usd = yf.download(tickers=f"{currency_code}=X", period=period, interval=interval, progress=False)
                
                s_usd_krw = get_valid_series(usd_krw)
                s_target_usd = get_valid_series(target_usd)

                if not s_usd_krw.empty and not s_target_usd.empty:
                    # 두 데이터의 인덱스(시간)를 기준으로 병합
                    df_usd_krw = s_usd_krw.to_frame(name='USD_KRW').sort_index()
                    df_target_usd = s_target_usd.to_frame(name='TARGET_USD').sort_index()
                    
                    combined = pd.merge_asof(
                        df_usd_krw,
                        df_target_usd,
                        left_index=True, right_index=True, direction='nearest'
                    )
                    
                    # 환율 계산 로직
                    direct_usd_list = ["EUR", "GBP", "AUD", "NZD"]
                    
                    if currency_code in direct_usd_list:
                        combined['Close'] = combined['USD_KRW'] * combined['TARGET_USD']
                    else:
                        combined['Close'] = combined['USD_KRW'] / combined['TARGET_USD']
                    
                    data = combined[['Close']]
                    valid_close = get_valid_series(data)
                    print(f"  Successfully calculated cross-rate for {currency_code} ({len(valid_close)} pts)")

            # 최종 데이터 확인 (2개 미만이면 그래프 생성 불가 및 기존 파일 삭제)
            if len(valid_close) < 2:
                print(f"  Insufficient data ({len(valid_close)} pts) for {currency_code} ({period}). Skipping and removing stale file.")
                if os.path.exists(filepath):
                    os.remove(filepath)
                continue

            # 100단위 환율 처리 (엔화, 베트남 동 등)
            if is_100_unit:
                data['Close'] = data['Close'] * 100
                unit_label = " (per 100 units)"
            else:
                unit_label = ""

            # 한국 시간(Asia/Seoul)으로 변환
            if data.index.tz is None:
                data.index = data.index.tz_localize('UTC')
            data.index = data.index.tz_convert('Asia/Seoul')

            # 그래프 그리기
            plt.figure(figsize=(12, 6))
            plt.plot(data.index, data['Close'], color='red', linewidth=1.5)
            
            # 최고/최저점 표시 및 점 찍기
            try:
                max_val = valid_close.max()
                min_val = valid_close.min()
                max_idx = valid_close.idxmax()
                min_idx = valid_close.idxmin()

                plt.scatter(max_idx, max_val, color='darkred', s=50, zorder=5)
                plt.scatter(min_idx, min_val, color='blue', s=50, zorder=5)

                plt.text(max_idx, max_val, f" High: {max_val:.2f}", color='darkred', fontweight='bold', verticalalignment='bottom')
                plt.text(min_idx, min_val, f" Low: {min_val:.2f}", color='blue', fontweight='bold', verticalalignment='top')
            except:
                pass

            plt.xlabel("Date (KST)", fontsize=10)
            plt.ylabel(f"Exchange Rate{unit_label}", fontsize=10)
            plt.grid(True, linestyle='--', alpha=0.4)
            
            ax = plt.gca()
            import matplotlib.dates as mdates
            # X축 포맷 설정
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
            
            # 그래프의 오른쪽 끝을 오늘 날짜로 강제 확장
            if not data.empty:
                ax.set_xlim(data.index.min(), now)
            
            plt.gcf().autofmt_xdate()
            plt.tight_layout()

            # 파일 저장 (기존 파일이 있으면 삭제 후 저장)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            plt.savefig(filepath)
            plt.close()
            
            print(f"  Saved: {filename}")

        except Exception as e:
            print(f"  Error processing {period}: {e}")

if __name__ == "__main__":
    # 텔레그램 즉시 테스트 기능 (ex: python3 generate_graphs.py test_telegram)
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test_telegram":
        print("Sending test Telegram message...")
        send_telegram_message("🔔 [Graph Generator] Telegram notification test successful!")
        sys.exit(0)

    # 네이버 금융 제공 전체 국가/통화 목록 (달러인덱스 제외)
    full_currency_list = [
        "USD", "EUR", "JPY", "CNY", "HKD", "TWD", "SGD", "THB", "VND", "PHP", 
        "INR", "IDR", "MYR", "MOP", "MNT", "MMK", "KHR", "KZT", "UZS", "PKR", 
        "BDT", "LKR", "NPR", "AUD", "NZD", "FJD", "GBP", "CHF", "SEK", "NOK", 
        "DKK", "RUB", "HUF", "PLN", "CZK", "RON", "TRY", "CAD", "MXN", "BRL", 
        "CLP", "COP", "SAR", "AED", "KWD", "BHD", "OMR", "JOD", "ILS", "EGP", 
        "ZAR", "DZD", "KES", "TZS", "ETB", "LYD"
    ]

    # 명령행 인자 처리 (ex: python3 generate_graphs.py usd rub)
    if len(sys.argv) > 1:
        selected_currencies = [arg.upper() for arg in sys.argv[1:]]
        
        # 유효한 인자만 필터링
        target_list = [c for c in selected_currencies if c in full_currency_list]
        
        if not target_list:
            print(f"No valid currency codes found in: {sys.argv[1:]}")
            print(f"Available codes: {full_currency_list}")
            sys.exit(1)
            
        print(f"Generating graphs for selected: {target_list}")
        generate_all_currency_graphs(target_list)
    else:
        # 인자가 없으면 기본 전체 리스트 사용
        print("No arguments provided. Generating graphs for all currencies...")
        generate_all_currency_graphs(full_currency_list)
    
    print("\nAll tasks completed.")
