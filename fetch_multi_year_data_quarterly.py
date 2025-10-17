
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
        print(f"Error fetching {year} report {report_code}: {e}")
        return None

def extract_key_metrics(financial_data, year, quarter=None):
    """주요 지표 추출"""
    if not financial_data or financial_data.get("status") != "000":
        return None

    items = {item['account_id']: item for item in financial_data.get('list', []) if item.get('sj_div') == 'IS'}

    try:
        revenue = int(items.get('ifrs-full_Revenue', {}).get('thstrm_amount', '0').replace(',', ''))
        operating_profit = int(items.get('dart_OperatingIncomeLoss', {}).get('thstrm_amount', '0').replace(',', ''))
        
        period_label = f"{year}년"
        if quarter:
            period_label += f" {quarter}분기"

        return {
            "year": year,
            "quarter": quarter,
            "period": period_label,
            "revenue": revenue,
            "operating_profit": operating_profit,
            "operating_margin": round((operating_profit / revenue * 100), 2) if revenue > 0 else 0
        }
    except Exception as e:
        print(f"Error parsing {year} Q{quarter if quarter else 'Annual'}: {e}")
        return None

def main(corp_code, corp_name):
    print("=" * 80)
    print(f"{corp_name} 분기별 재무 데이터 수집")
    print("=" * 80)

    quarterly_data = []
    report_codes = {
        "1분기": "11013",
        "2분기": "11012",  # 반기보고서
        "3분기": "11014"
    }

    current_year = datetime.now().year
    start_year = current_year - 10
    
    # Calculate total iterations for progress bar
    total_years_to_fetch = (current_year + 1) - start_year
    total_quarters_to_fetch = total_years_to_fetch * len(report_codes)
    
    quarter_count = 0 # Initialize counter for progress bar

    for year in range(start_year, current_year + 1):
        for quarter_name, report_code in report_codes.items():
            quarter_count += 1
            print(f"\n--- [{quarter_count}/{total_quarters_to_fetch}] {year}년 {quarter_name} 데이터 수집 중... ---")
            financial_data = get_financial_statement(year, report_code, corp_code=corp_code)

            if financial_data:
                quarter_num = int(quarter_name[0])
                metrics = extract_key_metrics(financial_data, year, quarter_num)
                if metrics:
                    if metrics['revenue'] == 0 or metrics['operating_profit'] == 0:
                        print(f"⚠️ {year}년 {quarter_name} 데이터 (매출액 또는 영업이익 0) 스킵")
                    else:
                        quarterly_data.append(metrics)
                        print(f"✅ {year}년 {quarter_name} 데이터 수집 완료")
                        print(f"   - 매출: {metrics['revenue']:,}원")
                        print(f"   - 영업이익: {metrics['operating_profit']:,}원")

            time.sleep(0.5)

    # 데이터 저장
    with open(f"{corp_code}_quarterly_data.json", "w", encoding="utf-8") as f:
        json.dump(quarterly_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ 총 {len(quarterly_data)}개 분기 데이터 수집 완료!")
    print(f"📁 저장 파일: {corp_code}_quarterly_data.json")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    corp_code = sys.argv[1]
    corp_name = sys.argv[2]
    main(corp_code, corp_name)
