"""
백그라운드 데이터 수집 스크립트
Background data fetcher for top 10 Korean companies
"""
import requests
import json
import time
import sqlite3
import sys
import io
from datetime import datetime

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# DART API 설정
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"

def get_companies_from_db():
    """데이터베이스에서 기업 목록 조회"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT corp_code, corp_name FROM companies')
    companies = [{"corp_code": row[0], "corp_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return companies

def fetch_financial_data(corp_code, year, report_code="11011"):
    """
    DART API에서 재무제표 데이터 가져오기

    Args:
        corp_code: 기업 고유번호
        year: 사업연도 (예: 2024)
        report_code: 보고서 코드 (11011: 사업보고서)
    """
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": report_code,
        "fs_div": "CFS"  # 연결재무제표
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "000":
            return data.get("list", [])
        else:
            print(f"⚠️  API 오류: {data.get('message', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

def parse_income_statement(financial_data):
    """손익계산서 데이터 파싱"""
    income_data = {}

    for item in financial_data:
        if item.get("sj_div") == "IS":  # 손익계산서
            account_id = item.get("account_id")
            thstrm_amount = item.get("thstrm_amount", "0")

            # 숫자 형태로 변환 (쉼표 제거)
            try:
                amount = float(thstrm_amount.replace(",", ""))
            except (ValueError, AttributeError):
                amount = 0.0

            if account_id == "ifrs-full_Revenue":
                income_data["revenue"] = amount
            elif account_id == "ifrs-full_CostOfSales":
                income_data["cost_of_sales"] = amount
            elif account_id == "ifrs-full_GrossProfit":
                income_data["gross_profit"] = amount
            elif account_id == "dart_TotalSellingGeneralAdministrativeExpenses":
                income_data["selling_admin_expenses"] = amount
            elif account_id == "dart_OperatingIncomeLoss":
                income_data["operating_profit"] = amount

    # 영업이익률 계산
    if income_data.get("revenue") and income_data.get("operating_profit"):
        income_data["operating_margin"] = (income_data["operating_profit"] / income_data["revenue"]) * 100

    return income_data

def parse_balance_sheet(financial_data):
    """재무상태표 데이터 파싱"""
    balance_data = {}

    for item in financial_data:
        if item.get("sj_div") == "BS":  # 재무상태표
            account_id = item.get("account_id")
            thstrm_amount = item.get("thstrm_amount", "0")

            try:
                amount = float(thstrm_amount.replace(",", ""))
            except (ValueError, AttributeError):
                amount = 0.0

            if account_id == "ifrs-full_Assets":
                balance_data["total_assets"] = amount
            elif account_id == "ifrs-full_CurrentAssets":
                balance_data["current_assets"] = amount
            elif account_id == "ifrs-full_NoncurrentAssets":
                balance_data["non_current_assets"] = amount
            elif account_id == "ifrs-full_Liabilities":
                balance_data["total_liabilities"] = amount
            elif account_id == "ifrs-full_CurrentLiabilities":
                balance_data["current_liabilities"] = amount
            elif account_id == "ifrs-full_NoncurrentLiabilities":
                balance_data["non_current_liabilities"] = amount
            elif account_id == "ifrs-full_Equity":
                balance_data["total_equity"] = amount

    return balance_data

def parse_cash_flow(financial_data):
    """현금흐름표 데이터 파싱"""
    cashflow_data = {}

    for item in financial_data:
        sj_div = item.get("sj_div")
        if sj_div in ["CF", "CIS"]:  # 현금흐름표
            account_id = item.get("account_id")
            thstrm_amount = item.get("thstrm_amount", "0")

            try:
                amount = float(thstrm_amount.replace(",", ""))
            except (ValueError, AttributeError):
                amount = 0.0

            if account_id == "ifrs-full_CashFlowsFromUsedInOperatingActivities":
                cashflow_data["operating_cash_flow"] = amount
            elif account_id == "ifrs-full_CashFlowsFromUsedInInvestingActivities":
                cashflow_data["investing_cash_flow"] = amount
            elif account_id == "ifrs-full_CashFlowsFromUsedInFinancingActivities":
                cashflow_data["financing_cash_flow"] = amount

    # 순현금흐름 계산
    if all(k in cashflow_data for k in ["operating_cash_flow", "investing_cash_flow", "financing_cash_flow"]):
        cashflow_data["net_cash_flow"] = (
            cashflow_data["operating_cash_flow"] +
            cashflow_data["investing_cash_flow"] +
            cashflow_data["financing_cash_flow"]
        )

    return cashflow_data

def save_to_database(corp_code, year, report_type, income_data, balance_data, cashflow_data):
    """데이터베이스에 재무 데이터 저장"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    # 손익계산서 저장
    if income_data:
        cursor.execute('''
            INSERT OR REPLACE INTO income_statements
            (corp_code, year, report_type, revenue, cost_of_sales, gross_profit,
             selling_admin_expenses, operating_profit, operating_margin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            corp_code, year, report_type,
            income_data.get("revenue"),
            income_data.get("cost_of_sales"),
            income_data.get("gross_profit"),
            income_data.get("selling_admin_expenses"),
            income_data.get("operating_profit"),
            income_data.get("operating_margin")
        ))

    # 재무상태표 저장
    if balance_data:
        cursor.execute('''
            INSERT OR REPLACE INTO balance_sheets
            (corp_code, year, report_type, total_assets, current_assets, non_current_assets,
             total_liabilities, current_liabilities, non_current_liabilities, total_equity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            corp_code, year, report_type,
            balance_data.get("total_assets"),
            balance_data.get("current_assets"),
            balance_data.get("non_current_assets"),
            balance_data.get("total_liabilities"),
            balance_data.get("current_liabilities"),
            balance_data.get("non_current_liabilities"),
            balance_data.get("total_equity")
        ))

    # 현금흐름표 저장
    if cashflow_data:
        cursor.execute('''
            INSERT OR REPLACE INTO cash_flows
            (corp_code, year, report_type, operating_cash_flow, investing_cash_flow,
             financing_cash_flow, net_cash_flow)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            corp_code, year, report_type,
            cashflow_data.get("operating_cash_flow"),
            cashflow_data.get("investing_cash_flow"),
            cashflow_data.get("financing_cash_flow"),
            cashflow_data.get("net_cash_flow")
        ))

    conn.commit()
    conn.close()

def fetch_company_data(corp_code, corp_name, years=None):
    """특정 기업의 다년도 및 분기별 데이터 수집 (10년치)"""
    if years is None:
        # 기본값: 최근 10년 데이터
        current_year = datetime.now().year
        years = list(range(current_year - 10, current_year + 1))

    print(f"\n📊 {corp_name} 데이터 수집 중 ({len(years)}년치)...")

    # 보고서 코드 정의
    report_codes = {
        "11011": "연간",
        "11012": "반기",
        "11013": "1분기",
        "11014": "3분기"
    }

    total_count = 0
    success_count = 0

    for year in years:
        for report_code, report_name in report_codes.items():
            total_count += 1
            print(f"   • {year}년 {report_name} 데이터 처리 중...", end=" ")

            financial_data = fetch_financial_data(corp_code, year, report_code)

            if financial_data:
                income_data = parse_income_statement(financial_data)
                balance_data = parse_balance_sheet(financial_data)
                cashflow_data = parse_cash_flow(financial_data)

                # 데이터가 있는 경우만 저장 (매출이 있으면 유효한 데이터로 판단)
                if income_data.get("revenue", 0) > 0:
                    save_to_database(corp_code, year, report_code, income_data, balance_data, cashflow_data)
                    success_count += 1
                    print("✅")
                else:
                    print("⊘ (데이터 없음)")
            else:
                print("❌")

            # API 호출 간격 (Rate limiting)
            time.sleep(0.5)

    print(f"   💾 {corp_name} 완료: {success_count}/{total_count} 성공")

def main():
    """메인 실행 함수"""
    print("🚀 백그라운드 데이터 수집 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 데이터베이스에서 기업 목록 조회
    companies = get_companies_from_db()
    print(f"📋 총 {len(companies)}개 기업 데이터 수집 예정")

    # 각 기업별 데이터 수집
    for idx, company in enumerate(companies, 1):
        print(f"\n[{idx}/{len(companies)}] {company['corp_name']}")
        fetch_company_data(company['corp_code'], company['corp_name'])

    print(f"\n✅ 모든 데이터 수집 완료!")
    print(f"⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💾 데이터베이스: financial_data.db")

if __name__ == "__main__":
    main()
