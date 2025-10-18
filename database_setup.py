"""
데이터베이스 스키마 설정 스크립트
Database schema setup for financial data storage
"""
import sqlite3
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_database():
    """데이터베이스 및 테이블 생성"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    # 기업 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            corp_code TEXT PRIMARY KEY,
            corp_name TEXT NOT NULL,
            stock_code TEXT,
            sector TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 손익계산서 테이블 (확장 버전 - 추가 항목 포함)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corp_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            revenue REAL,
            cost_of_sales REAL,
            gross_profit REAL,
            selling_admin_expenses REAL,
            operating_profit REAL,
            operating_margin REAL,
            other_gains REAL DEFAULT 0,
            other_losses REAL DEFAULT 0,
            finance_income REAL DEFAULT 0,
            finance_costs REAL DEFAULT 0,
            equity_method_income REAL DEFAULT 0,
            profit_before_tax REAL DEFAULT 0,
            income_tax_expense REAL DEFAULT 0,
            net_profit REAL DEFAULT 0,
            profit_attributable_to_owners REAL DEFAULT 0,
            non_controlling_interests REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (corp_code) REFERENCES companies(corp_code),
            UNIQUE(corp_code, year, report_type)
        )
    ''')

    # 재무상태표 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corp_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            total_assets REAL,
            current_assets REAL,
            non_current_assets REAL,
            total_liabilities REAL,
            current_liabilities REAL,
            non_current_liabilities REAL,
            total_equity REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (corp_code) REFERENCES companies(corp_code),
            UNIQUE(corp_code, year, report_type)
        )
    ''')

    # 현금흐름표 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cash_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corp_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            operating_cash_flow REAL,
            investing_cash_flow REAL,
            financing_cash_flow REAL,
            net_cash_flow REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (corp_code) REFERENCES companies(corp_code),
            UNIQUE(corp_code, year, report_type)
        )
    ''')

    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_corp_year ON income_statements(corp_code, year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_balance_corp_year ON balance_sheets(corp_code, year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cashflow_corp_year ON cash_flows(corp_code, year)')

    conn.commit()
    conn.close()

    print("✅ 데이터베이스 및 테이블 생성 완료")
    print("📁 파일: financial_data.db")

def get_top_10_companies():
    """
    실제 추이 분석 데이터가 있는 기업만 반환 (10년 데이터 보유)
    Returns only companies with 10-year trend data
    """
    return [
        {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "sector": "전자"},
        {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660", "sector": "전자"},
        {"corp_code": "00164742", "corp_name": "LG에너지솔루션", "stock_code": "373220", "sector": "전자"},
        {"corp_code": "00356370", "corp_name": "KB금융", "stock_code": "105560", "sector": "금융"}
    ]

def insert_companies():
    """기업 정보를 데이터베이스에 삽입"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    companies = get_top_10_companies()

    for company in companies:
        cursor.execute('''
            INSERT OR REPLACE INTO companies (corp_code, corp_name, stock_code, sector)
            VALUES (?, ?, ?, ?)
        ''', (company['corp_code'], company['corp_name'], company['stock_code'], company['sector']))

    conn.commit()
    conn.close()

    print(f"✅ {len(companies)}개 기업 정보 저장 완료")
    for company in companies:
        print(f"   • {company['corp_name']} ({company['stock_code']})")

if __name__ == "__main__":
    print("🏗️  데이터베이스 설정 시작...")
    create_database()
    insert_companies()
    print("\n✅ 모든 설정 완료!")
