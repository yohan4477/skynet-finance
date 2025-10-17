import requests
import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# DART API 설정
API_KEY = os.environ.get("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"

def get_balance_sheet(corp_code, year="2023", api_key=API_KEY):
    """재무상태표 조회"""
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": "11011",  # 사업보고서
        "fs_div": "CFS"  # 연결재무제표
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {year} for {corp_code}: {e}")
        return None

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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_params = parse_qs(urlparse(self.path).query)
        corp_code = query_params.get("corp_code", [None])[0]
        year = query_params.get("year", ["2023"])[0] # Default to 2023

        if not corp_code:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "corp_code is required"}).encode('utf-8'))
            return

        if not API_KEY:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "DART_API_KEY not set in environment variables"}).encode('utf-8'))
            return

        financial_data = get_balance_sheet(corp_code, year, API_KEY)
        balance_sheet = parse_balance_sheet(financial_data)

        if balance_sheet:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(balance_sheet, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Balance sheet data not found for the given corp_code and year"}).encode('utf-8'))
