import requests
import json
import os
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psycopg2

# DART API 설정
API_KEY = os.environ.get("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"
POSTGRES_URL = os.environ.get("POSTGRES_URL")

# 캐시 유효 시간 (예: 24시간)
CACHE_DURATION_HOURS = 24

def get_db_connection():
    conn = psycopg2.connect(POSTGRES_URL)
    return conn

def create_table_if_not_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cashflow_data (
                id SERIAL PRIMARY KEY,
                corp_code VARCHAR(10) NOT NULL,
                year INTEGER NOT NULL,
                quarter INTEGER, -- NULL for annual data
                period VARCHAR(20),
                operating_cf BIGINT,
                investing_cf BIGINT,
                financing_cf BIGINT,
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (corp_code, year, quarter)
            );
        """)
        conn.commit()

def get_cashflow_statement_from_dart(year, corp_code, api_key, report_code="11011"):
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
        print(f"Error fetching {year} for {corp_code} from DART: {e}")
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

def save_cashflow_data_to_db(conn, corp_code, data):
    with conn.cursor() as cur:
        for item in data:
            cur.execute("""
                INSERT INTO cashflow_data (corp_code, year, quarter, period, operating_cf, investing_cf, financing_cf)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (corp_code, year, quarter) DO UPDATE SET
                    period = EXCLUDED.period,
                    operating_cf = EXCLUDED.operating_cf,
                    investing_cf = EXCLUDED.investing_cf,
                    financing_cf = EXCLUDED.financing_cf,
                    last_updated = CURRENT_TIMESTAMP;
            """, (
                corp_code,
                item["year"],
                item["quarter"],
                item["period"],
                item["operating_cf"],
                item["investing_cf"],
                item["financing_cf"]
            ))
        conn.commit()

def get_cashflow_data_from_db(conn, corp_code):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT year, quarter, period, operating_cf, investing_cf, financing_cf, last_updated
            FROM cashflow_data
            WHERE corp_code = %s
            ORDER BY year ASC, quarter ASC;
        """, (corp_code,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        data = []
        for row in rows:
            item = dict(zip(columns, row))
            # Convert datetime to isoformat string for JSON serialization
            if 'last_updated' in item and isinstance(item['last_updated'], datetime):
                item['last_updated'] = item['last_updated'].isoformat()
            data.append(item)
        return data

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

        if not POSTGRES_URL:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "POSTGRES_URL not set in environment variables"}).encode('utf-8'))
            return

        conn = None
        try:
            conn = get_db_connection()
            create_table_if_not_exists(conn)

            # 1. DB에서 데이터 조회
            db_data = get_cashflow_data_from_db(conn, corp_code)
            
            # 2. 캐시 유효성 검사
            is_cache_valid = False
            if db_data:
                # 모든 데이터가 캐시 유효 시간 내에 업데이트되었는지 확인
                all_recent = True
                for item in db_data:
                    # last_updated는 이미 isoformat 문자열이므로 datetime 객체로 변환 후 비교
                    if (datetime.now(item['last_updated'].tzinfo) - datetime.fromisoformat(item['last_updated'])) > timedelta(hours=CACHE_DURATION_HOURS):
                        all_recent = False
                        break
                if all_recent:
                    is_cache_valid = True
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"annual": db_data}, ensure_ascii=False).encode('utf-8'))
                    return

            # 3. 캐시가 유효하지 않으면 DART API에서 데이터 가져오기
            current_year = datetime.now().year
            start_year = current_year - 10
            annual_data = []
            fetched_from_dart = False

            for year in range(start_year, current_year + 1):
                dart_data = get_cashflow_statement_from_dart(year, corp_code, API_KEY)
                if dart_data:
                    metrics = extract_cashflow_metrics(dart_data, year)
                    if metrics:
                        annual_data.append(metrics)
                        fetched_from_dart = True

            if fetched_from_dart:
                save_cashflow_data_to_db(conn, corp_code, annual_data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"annual": annual_data}, ensure_ascii=False).encode('utf-8'))
            else:
                # DART API에서도 데이터를 가져오지 못했고, DB 캐시도 없거나 유효하지 않음
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Cashflow data not found from DART API or cache"}).encode('utf-8'))

        except Exception as e:
            print(f"Serverless function error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            if conn:
                conn.close()