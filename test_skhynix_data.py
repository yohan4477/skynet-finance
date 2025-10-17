import requests
import json
from datetime import datetime
import time

API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"
SKHYNIX_CORP_CODE = "00164779"

def get_financial_statement(year, corp_code, api_key):
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": "11011",  # 사업보고서
        "fs_div": "CFS"  # 연결재무제표
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {year} for {corp_code}: {e}")
        return None

def extract_key_metrics(financial_data, year):
    if not financial_data or financial_data.get("status") != "000":
        return None

    items = financial_data.get("list", [])

    revenue = 0
    operating_profit = 0
    cost_of_sales = 0
    selling_admin = 0

    for item in items:
        account_nm = item.get("account_nm", "").replace(" ", "")
        if account_nm in ["매출액", "수익(매출액)", "매출"]:
            revenue = int(item.get('thstrm_amount', '0').replace(',', ''))
        if account_nm in ["영업이익", "영업이익(손실)"]:
            operating_profit = int(item.get('thstrm_amount', '0').replace(',', ''))
        if account_nm == "매출원가":
            cost_of_sales = int(item.get('thstrm_amount', '0').replace(',', ''))
        if account_nm in ["판매비와관리비", "판매비와관리비"]:
            selling_admin = int(item.get('thstrm_amount', '0').replace(',', ''))

    try:
        return {
            "year": year,
            "revenue": revenue,
            "operating_profit": operating_profit,
            "cost_of_sales": cost_of_sales,
            "selling_admin_expenses": selling_admin,
            "operating_margin": round((operating_profit / revenue * 100), 2) if revenue > 0 else 0
        }
    except Exception as e:
        print(f"Error parsing {year}: {e}")
        return None

def main():
    current_year = datetime.now().year
    start_year = current_year - 10

    multi_year_data = []

    print(f"Fetching data for SK Hynix ({SKHYNIX_CORP_CODE}) from {start_year} to {current_year}")

    for year in range(start_year, current_year + 1):
        print(f"\n[{year}] 데이터 수집 중...")
        financial_data = get_financial_statement(year, SKHYNIX_CORP_CODE, API_KEY)

        if financial_data:
            metrics = extract_key_metrics(financial_data, year)
            if metrics:
                multi_year_data.append(metrics)
                print(f"✅ {year}년 데이터 수집 완료")
                print(f"   - 매출: {metrics['revenue']:,}원")
                print(f"   - 영업이익: {metrics['operating_profit']:,}원")
                print(f"   - 영업이익률: {metrics['operating_margin']}%" if metrics['revenue'] > 0 else "")
            else:
                print(f"❌ {year}년 데이터 파싱 실패")
        else:
            print(f"❌ {year}년 데이터 수집 실패")

        time.sleep(0.5)

    print("\n" + "=" * 80)
    print(f"✅ 총 {len(multi_year_data)}년치 데이터 수집 완료!")
    print(json.dumps(multi_year_data, ensure_ascii=False, indent=2))
    print("=" * 80)

if __name__ == "__main__":
    main()
