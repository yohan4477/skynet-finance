import requests
import json
from datetime import datetime
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# DART API 설정
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"

# 삼성전자 고유번호 (corp_code)
SAMSUNG_CORP_CODE = "00126380"

def get_company_info():
    """회사 기본정보 조회"""
    url = f"{BASE_URL}/company.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": SAMSUNG_CORP_CODE
    }

    response = requests.get(url, params=params)
    return response.json()

def get_financial_statement(year="2023", report_code="11011"):
    """
    재무제표 조회
    report_code:
    - 11011: 사업보고서
    - 11012: 반기보고서
    - 11013: 1분기보고서
    - 11014: 3분기보고서
    """
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": SAMSUNG_CORP_CODE,
        "bsns_year": year,
        "reprt_code": report_code,
        "fs_div": "CFS"  # CFS: 연결재무제표, OFS: 개별재무제표
    }

    response = requests.get(url, params=params)
    return response.json()

def parse_income_statement(financial_data):
    """손익계산서 데이터 파싱"""
    if financial_data.get("status") != "000":
        print(f"Error: {financial_data.get('message')}")
        return None

    items = financial_data.get("list", [])

    # 손익계산서 주요 항목
    income_statement = {
        "revenue": {},  # 매출
        "costs": {},    # 비용
        "operating_profit": {},  # 영업이익
        "net_profit": {}  # 당기순이익
    }

    # 주요 계정과목
    target_accounts = {
        "매출액": "revenue",
        "수익(매출액)": "revenue",
        "매출": "revenue",
        "매출원가": "cost_of_sales",
        "매출총이익": "gross_profit",
        "판매비와관리비": "selling_admin_exp",
        "판매비와 관리비": "selling_admin_exp",
        "영업이익": "operating_profit",
        "영업이익(손실)": "operating_profit",
        "법인세비용차감전순이익": "profit_before_tax",
        "당기순이익": "net_profit",
        "당기순이익(손실)": "net_profit"
    }

    for item in items:
        account_nm = item.get("account_nm", "")
        thstrm_amount = item.get("thstrm_amount", "0")  # 당기
        frmtrm_amount = item.get("frmtrm_amount", "0")  # 전기

        for key, value in target_accounts.items():
            if key in account_nm:
                income_statement[value if value in ["revenue", "operating_profit", "net_profit"] else "costs"][account_nm] = {
                    "current": thstrm_amount,
                    "previous": frmtrm_amount,
                    "account_id": item.get("account_id", "")
                }

    return income_statement

def main():
    print("=" * 80)
    print("삼성전자 재무제표 조회")
    print("=" * 80)

    # 회사 정보 조회
    print("\n[1] 회사 기본정보 조회 중...")
    company_info = get_company_info()
    print(f"회사명: {company_info.get('corp_name', 'N/A')}")
    print(f"대표자명: {company_info.get('ceo_nm', 'N/A')}")

    # 재무제표 조회 (2023년 사업보고서)
    print("\n[2] 2023년 재무제표 조회 중...")
    financial_data = get_financial_statement(year="2023", report_code="11011")

    # 결과 저장
    with open("samsung_financial_raw.json", "w", encoding="utf-8") as f:
        json.dump(financial_data, f, ensure_ascii=False, indent=2)
    print("✅ 원본 데이터 저장 완료: samsung_financial_raw.json")

    # 손익계산서 파싱
    print("\n[3] 손익계산서 데이터 파싱 중...")
    income_statement = parse_income_statement(financial_data)

    if income_statement:
        with open("samsung_income_statement.json", "w", encoding="utf-8") as f:
            json.dump(income_statement, f, ensure_ascii=False, indent=2)
        print("✅ 손익계산서 데이터 저장 완료: samsung_income_statement.json")

        # 주요 지표 출력
        print("\n" + "=" * 80)
        print("삼성전자 손익계산서 주요 지표 (2023년)")
        print("=" * 80)

        for category, items in income_statement.items():
            if items:
                print(f"\n[{category.upper()}]")
                for account, values in items.items():
                    current = int(values['current'].replace(',', '')) if values['current'] else 0
                    print(f"  {account}: {current:,}원")

    print("\n" + "=" * 80)
    print("조회 완료!")
    print("=" * 80)

if __name__ == "__main__":
    main()
