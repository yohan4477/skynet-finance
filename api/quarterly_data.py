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
            CREATE TABLE IF NOT EXISTS quarterly_data (
                id SERIAL PRIMARY KEY,
                corp_code VARCHAR(10) NOT NULL,
                year INTEGER NOT NULL,
                quarter INTEGER NOT NULL,
                period VARCHAR(20),
                revenue BIGINT,
                operating_profit BIGINT,
                operating_margin NUMERIC(10, 2),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (corp_code, year, quarter)
            );
        """)
        conn.commit()

def get_financial_statement_from_dart(year, corp_code, api_key, report_code):
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
        print(f"Error fetching {year} report {report_code} for {corp_code} from DART: {e}")
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

def save_quarterly_data_to_db(conn, corp_code, data):
    with conn.cursor() as cur:
        for item in data:
            cur.execute("""
                INSERT INTO quarterly_data (corp_code, year, quarter, period, revenue, operating_profit, operating_margin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (corp_code, year, quarter) DO UPDATE SET
                    period = EXCLUDED.period,
                    revenue = EXCLUDED.revenue,
                    operating_profit = EXCLUDED.operating_profit,
                    operating_margin = EXCLUDED.operating_margin,
                    last_updated = CURRENT_TIMESTAMP;
            """, (
                corp_code,
                item["year"],
                item["quarter"],
                item["period"],
                item["revenue"],
                item["operating_profit"],
                item["operating_margin"]
            ))
        conn.commit()

def get_quarterly_data_from_db(conn, corp_code):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT year, quarter, period, revenue, operating_profit, operating_margin, last_updated
            FROM quarterly_data
            WHERE corp_code = %s
            ORDER BY year ASC, quarter ASC;
        """, (corp_code,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        data = []
        for row in rows:
            item = dict(zip(columns, row))
            # Convert Decimal to float for JSON serialization
            if 'operating_margin' in item and isinstance(item['operating_margin'], float):
                item['operating_margin'] = float(item['operating_margin'])
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
            db_data = get_quarterly_data_from_db(conn, corp_code)
            
            # 2. 캐시 유효성 검사
            is_cache_valid = False
            if db_data:
                # 모든 데이터가 캐시 유효 시간 내에 업데이트되었는지 확인
                all_recent = True
                for item in db_data:
                    if (datetime.now(datetime.fromisoformat(item['last_updated']).tzinfo) - datetime.fromisoformat(item['last_updated'])) > timedelta(hours=CACHE_DURATION_HOURS):
                        all_recent = False
                        break
                if all_recent:
                    is_cache_valid = True
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(db_data, ensure_ascii=False).encode('utf-8'))
                    return

            # 3. 캐시가 유효하지 않으면 DART API에서 데이터 가져오기
            quarterly_data = []
            report_codes = {
                1: "11013", # 1분기
                2: "11012", # 반기보고서 (2분기)
                3: "11014"  # 3분기
            }

            current_year = datetime.now().year
            start_year = current_year - 10
            fetched_from_dart = False

            for year in range(start_year, current_year + 1):
                for quarter_num, report_code in report_codes.items():
                    dart_data = get_financial_statement_from_dart(year, corp_code, API_KEY, report_code)
                    if dart_data:
                        metrics = extract_key_metrics(dart_data, year, quarter_num)
                        if metrics:
                            metrics["corp_code"] = corp_code # Add corp_code for DB storage
                            quarterly_data.append(metrics)
                            fetched_from_dart = True

            if fetched_from_dart:
                save_quarterly_data_to_db(conn, corp_code, quarterly_data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(quarterly_data, ensure_ascii=False).encode('utf-8'))
            else:
                # DART API에서도 데이터를 가져오지 못했고, DB 캐시도 없거나 유효하지 않음
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Quarterly data not found from DART API or cache"}).encode('utf-8'))

        except Exception as e:
            print(f"Serverless function error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            if conn:
                conn.close()