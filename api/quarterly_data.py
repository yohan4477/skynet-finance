import requests
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# DART API 설정
API_KEY = os.environ.get("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"

def get_financial_statement(year, corp_code, api_key, report_code):
    """재무제표 조회"""
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
        print(f"Error fetching {year} report {report_code} for {corp_code}: {e}")
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

        quarterly_data = []
        report_codes = {
            1: "11013", # 1분기
            2: "11012", # 반기보고서 (2분기)
            3: "11014"  # 3분기
        }

        current_year = datetime.now().year
        start_year = current_year - 10

        for year in range(start_year, current_year + 1):
            for quarter_num, report_code in report_codes.items():
                financial_data = get_financial_statement(year, corp_code, API_KEY, report_code)
                if financial_data:
                    metrics = extract_key_metrics(financial_data, year, quarter_num)
                    if metrics:
                        quarterly_data.append(metrics)

        if quarterly_data:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(quarterly_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Quarterly data not found for the given corp_code"}).encode('utf-8'))
