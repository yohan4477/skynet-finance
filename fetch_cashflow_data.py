import requests
import json
import sys
import io
import time
from datetime import datetime

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# DART API 설정
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"
SAMSUNG_CORP_CODE = "00126380"

def get_cashflow_statement(year, report_code="11011", corp_code=SAMSUNG_CORP_CODE):
    """현금흐름표 조회"""
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
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": SAMSUNG_CORP_CODE,
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

def extract_cashflow_metrics(financial_data, year, quarter=None):
    """현금흐름표 주요 지표 추출"""
    if not financial_data or financial_data.get("status") != "000":
        return None

    # 현금흐름표 항목만 필터링
    cf_items = {item['account_id']: item for item in financial_data.get('list', []) if item.get('sj_div') == 'CF'}

    try:
        # 주요 현금흐름 항목
        operating_cf = int(cf_items.get('ifrs-full_CashFlowsFromUsedInOperatingActivities', {}).get('thstrm_amount', '0').replace(',', ''))
        investing_cf = int(cf_items.get('ifrs-full_CashFlowsFromUsedInInvestingActivities', {}).get('thstrm_amount', '0').replace(',', ''))
        financing_cf = int(cf_items.get('ifrs-full_CashFlowsFromUsedInFinancingActivities', {}).get('thstrm_amount', '0').replace(',', ''))

        # 현금 증감
        net_increase = int(cf_items.get('ifrs-full_IncreaseDecreaseInCashAndCashEquivalents', {}).get('thstrm_amount', '0').replace(',', ''))

        # 기초/기말 현금
        beginning_cash = int(cf_items.get('ifrs-full_CashAndCashEquivalentsBeginningOfPeriod', {}).get('thstrm_amount', '0').replace(',', ''))
        ending_cash = int(cf_items.get('ifrs-full_CashAndCashEquivalents', {}).get('thstrm_amount', '0').replace(',', ''))

        period_label = f"{year}년"
        if quarter:
            period_label += f" {quarter}분기"

        return {
            "year": year,
            "quarter": quarter,
            "period": period_label,
            "beginning_cash": beginning_cash,
            "operating_cf": operating_cf,
            "investing_cf": investing_cf,
            "financing_cf": financing_cf,
            "net_increase": net_increase,
            "ending_cash": ending_cash,
            "calculated_ending": beginning_cash + operating_cf + investing_cf + financing_cf
        }
    except Exception as e:
        print(f"Error parsing {year} Q{quarter if quarter else 'Annual'}: {e}")
        return None

def main(corp_code, corp_name):
    print("=" * 80)
    print(f"{corp_name} 현금흐름표 데이터 수집")
    print("=" * 80)

    current_year = datetime.now().year
    start_year = current_year - 10

    # 연도별 데이터 (사업보고서)
    annual_data = []
    for year in range(start_year, current_year + 1):
        print(f"\n[{year}년 사업보고서] 현금흐름표 수집 중...")
        financial_data = get_cashflow_statement(year, "11011", corp_code=corp_code)

        if financial_data:
            metrics = extract_cashflow_metrics(financial_data, year)
            if metrics:
                annual_data.append(metrics)
                print(f"✅ {year}년 데이터 수집 완료")
                print(f"   - 영업활동CF: {metrics['operating_cf']:,}원")

        time.sleep(0.5)

    # 분기별 데이터 (최근 10년)
    quarterly_data = []
    report_codes = {
        "1분기": "11013",
        "2분기": "11012",  # 반기보고서
        "3분기": "11014"
    }

    for year in range(start_year, current_year + 1):
        for quarter_name, report_code in report_codes.items():
            print(f"\n[{year}년 {quarter_name}] 현금흐름표 수집 중...")
            financial_data = get_cashflow_statement(year, report_code, corp_code=corp_code)

            if financial_data:
                quarter_num = int(quarter_name[0])
                metrics = extract_cashflow_metrics(financial_data, year, quarter_num)
                if metrics:
                    quarterly_data.append(metrics)
                    print(f"✅ {year}년 {quarter_name} 데이터 수집 완료")

            time.sleep(0.5)

    # 데이터 저장
    all_cashflow_data = {
        "annual": annual_data,
        "quarterly": quarterly_data
    }

    with open(f"{corp_code}_cashflow_data.json", "w", encoding="utf-8") as f:
        json.dump(all_cashflow_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ 연도별 {len(annual_data)}개, 분기별 {len(quarterly_data)}개 데이터 수집 완료!")
    print(f"📁 저장 파일: {corp_code}_cashflow_data.json")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    corp_code = sys.argv[1]
    corp_name = sys.argv[2]
    main(corp_code, corp_name)
