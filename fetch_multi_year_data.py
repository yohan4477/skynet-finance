import requests
import json
import sys
import io
from datetime import datetime
import time

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# DART API 설정
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"
SAMSUNG_CORP_CODE = "00126380"

def get_financial_statement(year, report_code="11011", corp_code=SAMSUNG_CORP_CODE):
    """재무제표 조회"""
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": report_code,
        "fs_div": "CFS"  # 연결재무제표
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error fetching {year}: {e}")
        return None

    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error fetching {year}: {e}")
        return None

def extract_key_metrics(financial_data, year):
    """주요 지표 추출"""
    if not financial_data or financial_data.get("status") != "000":
        return None

    items = financial_data.get("list", [])

    revenue = 0
    operating_profit = 0
    cost_of_sales = 0
    selling_admin = 0

    for item in items:
        account_id = item.get("account_id", "")
        if account_id == 'ifrs-full_Revenue':
            revenue = int(item.get('thstrm_amount', '0').replace(',', ''))
        if account_id == 'dart_OperatingIncomeLoss':
            operating_profit = int(item.get('thstrm_amount', '0').replace(',', ''))
        if account_id == "ifrs-full_CostOfSales":
            cost_of_sales = int(item.get('thstrm_amount', '0').replace(',', ''))
        if account_id == "dart_TotalSellingGeneralAdministrativeExpenses":
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

def main(corp_code, corp_name):
    print("=" * 80)
    print(f"{corp_name} 10년간 재무 데이터 수집")
    print("=" * 80)

    current_year = datetime.now().year
    start_year = current_year - 10
    total_years = current_year - start_year

    multi_year_data = []

    for i, year in enumerate(range(start_year, current_year)):
        print(f"\n--- [{i+1}/{total_years}] {year}년 데이터 수집 중... ---")
        financial_data = get_financial_statement(year, corp_code=corp_code)

        if financial_data:
            metrics = extract_key_metrics(financial_data, year)
            if metrics:
                if metrics['revenue'] == 0 or metrics['operating_profit'] == 0:
                    print(f"⚠️ {year}년 데이터 (매출액 또는 영업이익 0) 스킵")
                else:
                    multi_year_data.append(metrics)
                    print(f"✅ {year}년 데이터 수집 완료")
                    print(f"   - 매출: {metrics['revenue']:,}원")
                    print(f"   - 영업이익: {metrics['operating_profit']:,}원")
                    print(f"   - 영업이익률: {metrics['operating_margin']}%" if metrics['revenue'] > 0 else "")
            else:
                print(f"❌ {year}년 데이터 파싱 실패")
        else:
            print(f"❌ {year}년 데이터 수집 실패")

        # API 호출 제한 방지
        time.sleep(0.5)

    # 데이터 저장
    with open(f"{corp_code}_10year_data.json", "w", encoding="utf-8") as f:
        json.dump(multi_year_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ 총 {len(multi_year_data)}년치 데이터 수집 완료!")
    print(f"📁 저장 파일: {corp_code}_10year_data.json")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    corp_code = sys.argv[1]
    corp_name = sys.argv[2]
    main(corp_code, corp_name)
