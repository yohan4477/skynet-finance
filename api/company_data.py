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
            CREATE TABLE IF NOT EXISTS financial_data (
                id SERIAL PRIMARY KEY,
                corp_code VARCHAR(10) NOT NULL,
                year INTEGER NOT NULL,
                revenue BIGINT,
                operating_profit BIGINT,
                cost_of_sales BIGINT,
                selling_admin_expenses BIGINT,
                operating_margin NUMERIC(10, 2),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (corp_code, year)
            );
        """)
        conn.commit()

def get_financial_statement_from_dart(year, corp_code, api_key):
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
        print(f"Error fetching {year} for {corp_code} from DART: {e}")
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

def save_financial_data_to_db(conn, data):
    with conn.cursor() as cur:
        for item in data:
            cur.execute("""
                INSERT INTO financial_data (corp_code, year, revenue, operating_profit, cost_of_sales, selling_admin_expenses, operating_margin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (corp_code, year) DO UPDATE SET
                    revenue = EXCLUDED.revenue,
                    operating_profit = EXCLUDED.operating_profit,
                    cost_of_sales = EXCLUDED.cost_of_sales,
                    selling_admin_expenses = EXCLUDED.selling_admin_expenses,
                    operating_margin = EXCLUDED.operating_margin,
                    last_updated = CURRENT_TIMESTAMP;
            """, (
                item["corp_code"],
                item["year"],
                item["revenue"],
                item["operating_profit"],
                item["cost_of_sales"],
                item["selling_admin_expenses"],
                item["operating_margin"]
            ))
        conn.commit()

def get_financial_data_from_db(conn, corp_code):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT year, revenue, operating_profit, cost_of_sales, selling_admin_expenses, operating_margin, last_updated
            FROM financial_data
            WHERE corp_code = %s
            ORDER BY year ASC;
        """, (corp_code,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        data = []
        for row in rows:
            item = dict(zip(columns, row))
            # Convert Decimal to float for JSON serialization
            if 'operating_margin' in item and isinstance(item['operating_margin'], float):
                item['operating_margin'] = float(item['operating_margin'])
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
            db_data = get_financial_data_from_db(conn, corp_code)
            
            # 2. 캐시 유효성 검사
            is_cache_valid = False
            if db_data:
                # 모든 데이터가 캐시 유효 시간 내에 업데이트되었는지 확인
                all_recent = True
                for item in db_data:
                    if (datetime.now(item['last_updated'].tzinfo) - item['last_updated']) > timedelta(hours=CACHE_DURATION_HOURS):
                        all_recent = False
                        break
                if all_recent:
                    is_cache_valid = True
                    # 필터링은 클라이언트에서 하므로, 여기서는 모든 데이터를 반환
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    # last_updated 필드를 문자열로 변환하여 JSON 직렬화 문제 해결
                    for item in db_data:
                        item['last_updated'] = item['last_updated'].isoformat()
                    self.wfile.write(json.dumps(db_data, ensure_ascii=False).encode('utf-8'))
                    return

            # 3. 캐시가 유효하지 않으면 DART API에서 데이터 가져오기
            current_year = datetime.now().year
            start_year = current_year - 10
            multi_year_data = []
            fetched_from_dart = False

            for year in range(start_year, current_year + 1): # Include current year for potential latest data
                dart_data = get_financial_statement_from_dart(year, corp_code, API_KEY)
                if dart_data:
                    metrics = extract_key_metrics(dart_data, year)
                    if metrics:
                        metrics["corp_code"] = corp_code # Add corp_code for DB storage
                        multi_year_data.append(metrics)
                        fetched_from_dart = True

            if fetched_from_dart:
                save_financial_data_to_db(conn, multi_year_data)
                # 필터링은 클라이언트에서 하므로, 여기서는 모든 데이터를 반환
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(multi_year_data, ensure_ascii=False).encode('utf-8'))
            else:
                # DART API에서도 데이터를 가져오지 못했고, DB 캐시도 없거나 유효하지 않음
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Financial data not found from DART API or cache"}).encode('utf-8'))

        except Exception as e:
            print(f"Serverless function error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            if conn:
                conn.close()