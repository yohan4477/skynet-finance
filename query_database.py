"""
데이터베이스 조회 스크립트
Query financial data from database
"""
import sqlite3
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_report_type_name(report_code):
    """보고서 코드를 한글명으로 변환"""
    report_names = {
        "11011": "연간",
        "11012": "반기",
        "11013": "1분기",
        "11014": "3분기"
    }
    return report_names.get(report_code, report_code)

def query_company_data(corp_code=None, corp_name=None, year=None):
    """기업 재무 데이터 조회"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    # 기업 정보 조회
    if corp_name:
        cursor.execute('SELECT corp_code, corp_name, stock_code FROM companies WHERE corp_name LIKE ?', (f'%{corp_name}%',))
    elif corp_code:
        cursor.execute('SELECT corp_code, corp_name, stock_code FROM companies WHERE corp_code = ?', (corp_code,))
    else:
        cursor.execute('SELECT corp_code, corp_name, stock_code FROM companies')

    companies = cursor.fetchall()

    if not companies:
        print("❌ 해당하는 기업을 찾을 수 없습니다.")
        conn.close()
        return

    for company in companies:
        corp_code, corp_name, stock_code = company
        print(f"\n{'='*60}")
        print(f"🏢 {corp_name} ({stock_code})")
        print(f"{'='*60}")

        # 손익계산서 조회
        if year:
            cursor.execute('''
                SELECT year, report_type, revenue, operating_profit, operating_margin
                FROM income_statements
                WHERE corp_code = ? AND year = ?
                ORDER BY year DESC, report_type
            ''', (corp_code, year))
        else:
            cursor.execute('''
                SELECT year, report_type, revenue, operating_profit, operating_margin
                FROM income_statements
                WHERE corp_code = ?
                ORDER BY year DESC, report_type
            ''', (corp_code,))

        results = cursor.fetchall()

        if results:
            print(f"\n📊 손익계산서")
            print(f"{'연도':<8} {'보고서':<8} {'매출(조원)':>12} {'영업이익(조원)':>15} {'영업이익률(%)':>15}")
            print(f"{'-'*60}")

            for row in results:
                year_val, report_type, revenue, op_profit, op_margin = row
                revenue_t = revenue / 1_000_000_000_000 if revenue else 0
                profit_t = op_profit / 1_000_000_000_000 if op_profit else 0
                margin = op_margin if op_margin else 0

                report_name = get_report_type_name(report_type)
                print(f"{year_val:<8} {report_name:<8} {revenue_t:>12.1f} {profit_t:>15.1f} {margin:>14.1f}%")

        # 재무상태표 조회
        if year:
            cursor.execute('''
                SELECT year, report_type, total_assets, total_liabilities, total_equity
                FROM balance_sheets
                WHERE corp_code = ? AND year = ?
                ORDER BY year DESC, report_type
            ''', (corp_code, year))
        else:
            cursor.execute('''
                SELECT year, report_type, total_assets, total_liabilities, total_equity
                FROM balance_sheets
                WHERE corp_code = ?
                ORDER BY year DESC, report_type
            ''', (corp_code,))

        results = cursor.fetchall()

        if results:
            print(f"\n⚖️  재무상태표")
            print(f"{'연도':<8} {'보고서':<8} {'총자산(조원)':>12} {'총부채(조원)':>15} {'총자본(조원)':>15}")
            print(f"{'-'*60}")

            for row in results:
                year_val, report_type, assets, liabilities, equity = row
                assets_t = assets / 1_000_000_000_000 if assets else 0
                liab_t = liabilities / 1_000_000_000_000 if liabilities else 0
                equity_t = equity / 1_000_000_000_000 if equity else 0

                report_name = get_report_type_name(report_type)
                print(f"{year_val:<8} {report_name:<8} {assets_t:>12.1f} {liab_t:>15.1f} {equity_t:>15.1f}")

    conn.close()

def list_all_companies():
    """모든 기업 목록 조회"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT corp_name, stock_code, sector FROM companies ORDER BY corp_name')
    companies = cursor.fetchall()

    print("\n📋 등록된 기업 목록")
    print(f"{'='*60}")
    print(f"{'기업명':<20} {'종목코드':<10} {'업종':<15}")
    print(f"{'-'*60}")

    for corp_name, stock_code, sector in companies:
        print(f"{corp_name:<20} {stock_code:<10} {sector:<15}")

    print(f"{'='*60}")
    print(f"총 {len(companies)}개 기업")

    conn.close()

def get_quarterly_comparison(corp_name, year):
    """특정 기업의 분기별 비교"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    # 기업 코드 조회
    cursor.execute('SELECT corp_code FROM companies WHERE corp_name LIKE ?', (f'%{corp_name}%',))
    result = cursor.fetchone()

    if not result:
        print(f"❌ '{corp_name}' 기업을 찾을 수 없습니다.")
        conn.close()
        return

    corp_code = result[0]

    # 분기별 데이터 조회
    cursor.execute('''
        SELECT report_type, revenue, operating_profit, operating_margin
        FROM income_statements
        WHERE corp_code = ? AND year = ?
        ORDER BY report_type
    ''', (corp_code, year))

    results = cursor.fetchall()

    if not results:
        print(f"❌ {corp_name} {year}년 데이터가 없습니다.")
        conn.close()
        return

    print(f"\n📊 {corp_name} {year}년 분기별 실적 비교")
    print(f"{'='*70}")
    print(f"{'보고서':<10} {'매출(조원)':>15} {'영업이익(조원)':>20} {'영업이익률(%)':>20}")
    print(f"{'-'*70}")

    for report_type, revenue, op_profit, op_margin in results:
        revenue_t = revenue / 1_000_000_000_000 if revenue else 0
        profit_t = op_profit / 1_000_000_000_000 if op_profit else 0
        margin = op_margin if op_margin else 0

        report_name = get_report_type_name(report_type)
        print(f"{report_name:<10} {revenue_t:>15.1f} {profit_t:>20.1f} {margin:>19.1f}%")

    print(f"{'='*70}")

    conn.close()

def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='재무 데이터 조회')
    parser.add_argument('--list', action='store_true', help='전체 기업 목록 조회')
    parser.add_argument('--company', type=str, help='기업명으로 조회')
    parser.add_argument('--year', type=int, help='특정 연도 조회')
    parser.add_argument('--quarterly', nargs=2, metavar=('COMPANY', 'YEAR'), help='분기별 비교 (기업명 연도)')

    args = parser.parse_args()

    if args.list:
        list_all_companies()
    elif args.quarterly:
        corp_name, year = args.quarterly
        get_quarterly_comparison(corp_name, int(year))
    elif args.company:
        query_company_data(corp_name=args.company, year=args.year)
    else:
        # 기본: 모든 기업 조회
        list_all_companies()

if __name__ == "__main__":
    main()
