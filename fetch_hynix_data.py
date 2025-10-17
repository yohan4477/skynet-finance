import requests
import json
import sys
import io
import time

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# DART API 설정
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"
HYNIX_CORP_CODE = "00164779"  # SK하이닉스 고유번호

def get_financial_statement(year, report_code="11011"):
    """재무제표 조회"""
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": HYNIX_CORP_CODE,
        "bsns_year": str(year),
        "reprt_code": report_code,
        "fs_div": "CFS"
    }

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

    # 손익계산서
    is_items = {item['account_id']: item for item in financial_data.get('list', []) if item.get('sj_div') == 'IS'}
    # 재무상태표
    bs_items = {item['account_id']: item for item in financial_data.get('list', []) if item.get('sj_div') == 'BS'}

    try:
        revenue = int(is_items.get('ifrs-full_Revenue', {}).get('thstrm_amount', '0').replace(',', ''))
        operating_profit = int(is_items.get('dart_OperatingIncomeLoss', {}).get('thstrm_amount', '0').replace(',', ''))
        cost_of_sales = int(is_items.get('ifrs-full_CostOfSales', {}).get('thstrm_amount', '0').replace(',', ''))
        selling_admin = int(is_items.get('dart_TotalSellingGeneralAdministrativeExpenses', {}).get('thstrm_amount', '0').replace(',', ''))

        # 자산/부채/자본
        total_assets = int(bs_items.get('ifrs-full_Assets', {}).get('thstrm_amount', '0').replace(',', ''))
        current_assets = int(bs_items.get('ifrs-full_CurrentAssets', {}).get('thstrm_amount', '0').replace(',', ''))
        non_current_assets = total_assets - current_assets

        total_liabilities = int(bs_items.get('ifrs-full_Liabilities', {}).get('thstrm_amount', '0').replace(',', ''))
        current_liabilities = int(bs_items.get('ifrs-full_CurrentLiabilities', {}).get('thstrm_amount', '0').replace(',', ''))
        non_current_liabilities = total_liabilities - current_liabilities

        total_equity = int(bs_items.get('ifrs-full_Equity', {}).get('thstrm_amount', '0').replace(',', ''))

        return {
            "year": year,
            "company": "SK하이닉스",
            "revenue": revenue,
            "operating_profit": operating_profit,
            "cost_of_sales": cost_of_sales,
            "selling_admin_expenses": selling_admin,
            "operating_margin": round((operating_profit / revenue * 100), 2) if revenue > 0 else 0,
            "total_assets": total_assets,
            "current_assets": current_assets,
            "non_current_assets": non_current_assets,
            "total_liabilities": total_liabilities,
            "current_liabilities": current_liabilities,
            "non_current_liabilities": non_current_liabilities,
            "total_equity": total_equity
        }
    except Exception as e:
        print(f"Error parsing {year}: {e}")
        return None

def main():
    print("=" * 80)
    print("SK하이닉스 재무 데이터 수집")
    print("=" * 80)

    hynix_data = []

    for year in range(2019, 2025):
        print(f"\n[{year}] 데이터 수집 중...")
        financial_data = get_financial_statement(year)

        if financial_data:
            metrics = extract_key_metrics(financial_data, year)
            if metrics:
                hynix_data.append(metrics)
                print(f"✅ {year}년 데이터 수집 완료")
                print(f"   - 매출: {metrics['revenue']:,}원")
                print(f"   - 영업이익: {metrics['operating_profit']:,}원")
                print(f"   - 영업이익률: {metrics['operating_margin']}%")

        time.sleep(0.5)

    # 데이터 저장
    with open("hynix_financial_data.json", "w", encoding="utf-8") as f:
        json.dump(hynix_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ 총 {len(hynix_data)}년치 데이터 수집 완료!")
    print("📁 저장 파일: hynix_financial_data.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
