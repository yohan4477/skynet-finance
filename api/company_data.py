import requests
import json
import os
from datetime import datetime
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# DART API 설정
API_KEY = os.environ.get("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"

def get_financial_statement(year, corp_code, api_key):
    """재무제표 조회"""
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
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {year} for {corp_code}: {e}")
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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_params = parse_qs(urlparse(self.path).query)
        corp_code = query_params.get("corp_code", [None])[0]

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

        current_year = datetime.now().year
        start_year = current_year - 10

        multi_year_data = []

        for year in range(start_year, current_year + 1): # Include current year for potential latest data
            # Add a small delay to avoid hitting API rate limits if multiple requests are made in quick succession
            # In a serverless environment, this might not be strictly necessary per function call,
            # but good practice if a single client might trigger many functions.
            # time.sleep(0.05) 

            financial_data = get_financial_statement(year, corp_code, API_KEY)

            if financial_data:
                metrics = extract_key_metrics(financial_data, year)
                if metrics:
                    multi_year_data.append(metrics)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(multi_year_data, ensure_ascii=False).encode('utf-8'))
