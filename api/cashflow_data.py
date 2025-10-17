import requests
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# DART API 설정
API_KEY = os.environ.get("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"

def get_cashflow_statement(year, corp_code, api_key, report_code="11011"):
    """현금흐름표 조회"""
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": report_code,
        "fs_div": "CFS"  # 연결재무제표
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {year} for {corp_code}: {e}")
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

        period_label = f"{year}년"
        if quarter:
            period_label += f" {quarter}분기"

        return {
            "year": year,
            "quarter": quarter,
            "period": period_label,
            "operating_cf": operating_cf,
            "investing_cf": investing_cf,
            "financing_cf": financing_cf,
        }
    except Exception as e:
        print(f"Error parsing {year} Q{quarter if quarter else 'Annual'}: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_params = parse_qs(urlparse(self.path).query)
        corp_code = query_params.get("corp_code", [None])[0]
        year = query_params.get("year", [str(datetime.now().year)])[0] # Default to current year

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

        annual_data = []
        current_year = datetime.now().year
        start_year = current_year - 10

        for y in range(start_year, current_year + 1):
            financial_data = get_cashflow_statement(y, corp_code, API_KEY)
            if financial_data:
                metrics = extract_cashflow_metrics(financial_data, y)
                if metrics:
                    annual_data.append(metrics)

        if annual_data:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"annual": annual_data}, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Cashflow data not found for the given corp_code"}).encode('utf-8'))
