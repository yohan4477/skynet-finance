import requests
import json
import sys
import io
import argparse

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# DART API 설정
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"

def get_balance_sheet(corp_code, year="2023"):
    """재무상태표 조회"""
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": "11011",  # 사업보고서
        "fs_div": "CFS"  # 연결재무제표
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"API 요청 실패: {response.status_code}")
        return None
    return response.json()

def parse_balance_sheet(financial_data):
    """재무상태표 파싱"""
    if not financial_data or financial_data.get("status") != "000":
        message = financial_data.get('message', 'Unknown error') if financial_data else 'No data received'
        print(f"Error: {message}")
        return None

    # 재무상태표 항목만 필터링
    bs_items = [item for item in financial_data.get('list', []) if item.get('sj_div') == 'BS']

    if not bs_items:
        print("재무상태표(BS) 데이터를 찾을 수 없습니다.")
        return None

    balance_sheet = {
        "assets": {
            "current": {},
            "non_current": {},
            "total": 0
        },
        "liabilities": {
            "current": {},
            "non_current": {},
            "total": 0
        },
        "equity": {
            "items": {},
            "total": 0
        }
    }

    # 주요 계정과목 매핑
    account_map = {
        "ifrs-full_Assets": ("assets", "total"),
        "ifrs-full_CurrentAssets": ("assets", "current", "유동자산"),
        "ifrs-full_Non-currentAssets": ("assets", "non_current", "비유동자산"),
        "ifrs-full_Liabilities": ("liabilities", "total"),
        "ifrs-full_CurrentLiabilities": ("liabilities", "current", "유동부채"),
        "ifrs-full_Non-currentLiabilities": ("liabilities", "non_current", "비유동부채"),
        "ifrs-full_Equity": ("equity", "total"),
        "ifrs-full_CashAndCashEquivalents": ("assets", "current", "현금및현금성자산"),
        "ifrs-full_TradeAndOtherCurrentReceivables": ("assets", "current", "매출채권"),
        "ifrs-full_Inventories": ("assets", "current", "재고자산"),
        "ifrs-full_PropertyPlantAndEquipment": ("assets", "non_current", "유형자산"),
        "ifrs-full_IntangibleAssetsOtherThanGoodwill": ("assets", "non_current", "무형자산"),
        "ifrs-full_TradeAndOtherCurrentPayables": ("liabilities", "current", "매입채무"),
        "ifrs-full_CurrentBorrowings": ("liabilities", "current", "단기차입금"),
        "ifrs-full_Non-currentBorrowings": ("liabilities", "non_current", "장기차입금"),
        "ifrs-full_IssuedCapital": ("equity", "items", "자본금"),
        "ifrs-full_RetainedEarnings": ("equity", "items", "이익잉여금"),
    }

    for item in bs_items:
        account_id = item.get("account_id")
        thstrm_amount = int(item.get("thstrm_amount", "0").replace(',', ''))

        if account_id in account_map:
            path = account_map[account_id]
            if len(path) == 2: # 총계
                balance_sheet[path[0]][path[1]] = thstrm_amount
            elif len(path) == 3: # 세부 항목
                balance_sheet[path[0]][path[1]][path[2]] = {"amount": thstrm_amount, "account_id": account_id}

    # 총계가 없는 경우 세부항목 합산 (DART API가 가끔 총계 항목을 누락함)
    if balance_sheet["assets"]["total"] == 0:
        balance_sheet["assets"]["total"] = balance_sheet["assets"]["current"].get("유동자산", {}).get("amount", 0) + balance_sheet["assets"]["non_current"].get("비유동자산", {}).get("amount", 0)
    if balance_sheet["liabilities"]["total"] == 0:
        balance_sheet["liabilities"]["total"] = balance_sheet["liabilities"]["current"].get("유동부채", {}).get("amount", 0) + balance_sheet["liabilities"]["non_current"].get("비유동부채", {}).get("amount", 0)

    return balance_sheet

def main():
    parser = argparse.ArgumentParser(description="DART에서 특정 기업의 재무상태표를 조회합니다.")
    parser.add_argument("corp_code", help="조회할 기업의 DART 공시S법인코드")
    parser.add_argument("corp_name", help="조회할 기업의 이름")
    parser.add_argument("--year", default="2023", help="조회할 사업연도 (기본값: 2023)")
    args = parser.parse_args()

    print("=" * 80)
    print(f"{args.corp_name} 재무상태표 조회 ({args.year}년)")
    print("=" * 80)

    # 재무상태표 조회
    financial_data = get_balance_sheet(args.corp_code, args.year)

    if not financial_data:
        print("데이터를 가져오지 못했습니다.")
        return

    # 원본 데이터 저장
    raw_filename = f"{args.corp_code}_balance_sheet_raw.json"
    with open(raw_filename, "w", encoding="utf-8") as f:
        json.dump(financial_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 원본 데이터 저장: {raw_filename}")

    # 재무상태표 파싱
    balance_sheet = parse_balance_sheet(financial_data)

    if balance_sheet:
        parsed_filename = f"{args.corp_code}_balance_sheet.json"
        with open(parsed_filename, "w", encoding="utf-8") as f:
            json.dump(balance_sheet, f, ensure_ascii=False, indent=2)
        print(f"✅ 파싱 데이터 저장: {parsed_filename}")

        print("\n" + "=" * 80)
        print("재무상태표 요약")
        print("=" * 80)

        assets_total = balance_sheet['assets']['total']
        liabilities_total = balance_sheet['liabilities']['total']
        equity_total = balance_sheet['equity']['total']

        print(f"  자산총계: {assets_total:,}원")
        print(f"  부채총계: {liabilities_total:,}원")
        print(f"  자본총계: {equity_total:,}원")

        print("\n[검증]")
        total_liab_equity = liabilities_total + equity_total
        print(f"  자산 = 부채 + 자본")
        print(f"  {assets_total:,} = {total_liab_equity:,}")
        print(f"  차이: {abs(assets_total - total_liab_equity):,}원")

if __name__ == "__main__":
    main()