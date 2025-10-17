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
            CREATE TABLE IF NOT EXISTS balance_sheet_data (
                id SERIAL PRIMARY KEY,
                corp_code VARCHAR(10) NOT NULL,
                year INTEGER NOT NULL,
                assets_total BIGINT,
                liabilities_total BIGINT,
                equity_total BIGINT,
                assets_current JSONB,
                assets_non_current JSONB,
                liabilities_current JSONB,
                liabilities_non_current JSONB,
                equity_items JSONB,
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (corp_code, year)
            );
        """)
        conn.commit()

def get_balance_sheet_from_dart(year, corp_code, api_key):
    """재무상태표 조회"""
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

def save_balance_sheet_to_db(conn, corp_code, year, data):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO balance_sheet_data (
                corp_code, year, assets_total, liabilities_total, equity_total,
                assets_current, assets_non_current, liabilities_current, liabilities_non_current, equity_items
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (corp_code, year) DO UPDATE SET
                assets_total = EXCLUDED.assets_total,
                liabilities_total = EXCLUDED.liabilities_total,
                equity_total = EXCLUDED.equity_total,
                assets_current = EXCLUDED.assets_current,
                assets_non_current = EXCLUDED.assets_non_current,
                liabilities_current = EXCLUDED.liabilities_current,
                liabilities_non_current = EXCLUDED.liabilities_non_current,
                equity_items = EXCLUDED.equity_items,
                last_updated = CURRENT_TIMESTAMP;
        """, (
            corp_code, year, data["assets"]["total"], data["liabilities"]["total"], data["equity"]["total"],
            json.dumps(data["assets"]["current"]), json.dumps(data["assets"]["non_current"]),
            json.dumps(data["liabilities"]["current"]), json.dumps(data["liabilities"]["non_current"]),
            json.dumps(data["equity"]["items"])
        ))
        conn.commit()

def get_balance_sheet_from_db(conn, corp_code, year):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT assets_total, liabilities_total, equity_total,
                   assets_current, assets_non_current, liabilities_current, liabilities_non_current, equity_items,
                   last_updated
            FROM balance_sheet_data
            WHERE corp_code = %s AND year = %s;
        """, (corp_code, year))
        row = cur.fetchone()
        if row:
            columns = [desc[0] for desc in cur.description]
            item = dict(zip(columns, row))
            # JSONB 필드는 자동으로 파싱되지만, 혹시 문자열이면 다시 파싱
            for key in ['assets_current', 'assets_non_current', 'liabilities_current', 'liabilities_non_current', 'equity_items']:
                if isinstance(item[key], str):
                    item[key] = json.loads(item[key])
            
            # 재구성
            balance_sheet = {
                "assets": {
                    "current": item['assets_current'],
                    "non_current": item['assets_non_current'],
                    "total": item['assets_total']
                },
                "liabilities": {
                    "current": item['liabilities_current'],
                    "non_current": item['liabilities_non_current'],
                    "total": item['liabilities_total']
                },
                "equity": {
                    "items": item['equity_items'],
                    "total": item['equity_total']
                },
                "last_updated": item['last_updated']
            }
            return balance_sheet
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
            db_data = get_balance_sheet_from_db(conn, corp_code, int(year))
            
            # 2. 캐시 유효성 검사
            is_cache_valid = False
            if db_data:
                if (datetime.now(db_data['last_updated'].tzinfo) - db_data['last_updated']) < timedelta(hours=CACHE_DURATION_HOURS):
                    is_cache_valid = True
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    db_data['last_updated'] = db_data['last_updated'].isoformat()
                    self.wfile.write(json.dumps(db_data, ensure_ascii=False).encode('utf-8'))
                    return

            # 3. 캐시가 유효하지 않으면 DART API에서 데이터 가져오기
            dart_data = get_balance_sheet_from_dart(year, corp_code, API_KEY)
            balance_sheet = None
            fetched_from_dart = False

            if dart_data:
                balance_sheet = parse_balance_sheet(dart_data)
                if balance_sheet:
                    save_balance_sheet_to_db(conn, corp_code, int(year), balance_sheet)
                    fetched_from_dart = True

            if fetched_from_dart:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # last_updated 필드를 문자열로 변환하여 JSON 직렬화 문제 해결
                if 'last_updated' in balance_sheet: # DB 저장 시 추가되므로, DART에서 가져온 데이터에는 없을 수 있음
                    balance_sheet['last_updated'] = datetime.now().isoformat() # 현재 시간으로 설정
                self.wfile.write(json.dumps(balance_sheet, ensure_ascii=False).encode('utf-8'))
            else:
                # DART API에서도 데이터를 가져오지 못했고, DB 캐시도 없거나 유효하지 않음
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Balance sheet data not found from DART API or cache"}).encode('utf-8'))

        except Exception as e:
            print(f"Serverless function error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            if conn:
                conn.close()