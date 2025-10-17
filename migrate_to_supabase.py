"""
SQLite에서 Supabase로 재무 데이터 마이그레이션
Migrate financial data from SQLite to Supabase
"""
import sqlite3
import os
import sys
import io
from supabase import create_client, Client
from dotenv import load_dotenv

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env 파일 로드
load_dotenv()

# Supabase 설정 - 환경 변수에서 읽기
SUPABASE_URL = os.getenv("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "YOUR_SUPABASE_ANON_KEY")

def get_supabase_client() -> Client:
    """Supabase 클라이언트 생성"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_companies(supabase: Client):
    """기업 정보 마이그레이션"""
    print("\n📊 기업 정보 마이그레이션 시작...")

    companies = [
        {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "sector": "전자",
            "description": "세계 최대 반도체 및 스마트폰 제조사",
            "founded": 1969,
            "employees": 267937
        },
        {
            "corp_code": "00164779",
            "corp_name": "SK하이닉스",
            "stock_code": "000660",
            "sector": "전자",
            "description": "글로벌 메모리 반도체 선도 기업",
            "founded": 1983,
            "employees": 35246
        },
        {
            "corp_code": "00164742",
            "corp_name": "LG에너지솔루션",
            "stock_code": "373220",
            "sector": "전자",
            "description": "세계 2위 전기차 배터리 제조사",
            "founded": 2020,
            "employees": 42858
        },
        {
            "corp_code": "00113399",
            "corp_name": "삼성바이오로직스",
            "stock_code": "207940",
            "sector": "제약",
            "description": "글로벌 바이오의약품 위탁생산 선도 기업",
            "founded": 2011,
            "employees": 3124
        },
        {
            "corp_code": "00165890",
            "corp_name": "현대차",
            "stock_code": "005380",
            "sector": "자동차",
            "description": "세계 3위 완성차 제조 그룹",
            "founded": 1967,
            "employees": 120565
        },
        {
            "corp_code": "00164529",
            "corp_name": "셀트리온",
            "stock_code": "068270",
            "sector": "제약",
            "description": "국내 1위 바이오시밀러 제조사",
            "founded": 2002,
            "employees": 4861
        },
        {
            "corp_code": "00167799",
            "corp_name": "기아",
            "stock_code": "000270",
            "sector": "자동차",
            "description": "글로벌 완성차 제조 및 전기차 선도 기업",
            "founded": 1944,
            "employees": 78424
        },
        {
            "corp_code": "00159645",
            "corp_name": "POSCO홀딩스",
            "stock_code": "005490",
            "sector": "철강",
            "description": "세계적인 철강 및 소재 전문 기업",
            "founded": 1968,
            "employees": 37249
        },
        {
            "corp_code": "00356370",
            "corp_name": "KB금융",
            "stock_code": "105560",
            "sector": "금융",
            "description": "국내 최대 금융지주회사",
            "founded": 2008,
            "employees": 31524
        },
        {
            "corp_code": "00168099",
            "corp_name": "신한지주",
            "stock_code": "055550",
            "sector": "금융",
            "description": "종합 금융서비스 선도 그룹",
            "founded": 2001,
            "employees": 30187
        }
    ]

    try:
        response = supabase.table("companies").upsert(companies).execute()
        print(f"   ✅ {len(companies)}개 기업 정보 마이그레이션 완료")
        return True
    except Exception as e:
        print(f"   ❌ 기업 정보 마이그레이션 실패: {e}")
        return False

def migrate_income_statements(supabase: Client):
    """손익계산서 데이터 마이그레이션"""
    print("\n📋 손익계산서 데이터 마이그레이션 시작...")

    if not os.path.exists('financial_data.db'):
        print("   ⚠️  financial_data.db 파일이 없습니다.")
        return False

    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT corp_code, year, report_type, revenue, cost_of_sales,
                   gross_profit, selling_admin_expenses, operating_profit, operating_margin
            FROM income_statements
        """)

        rows = cursor.fetchall()

        if not rows:
            print("   ⚠️  손익계산서 데이터가 없습니다.")
            return True

        data = []
        for row in rows:
            data.append({
                "corp_code": row[0],
                "year": row[1],
                "report_type": row[2],
                "revenue": int(row[3]) if row[3] else None,
                "cost_of_sales": int(row[4]) if row[4] else None,
                "gross_profit": int(row[5]) if row[5] else None,
                "selling_admin_expenses": int(row[6]) if row[6] else None,
                "operating_profit": int(row[7]) if row[7] else None,
                "operating_margin": row[8]
            })

        # 배치로 나눠서 업로드 (Supabase 제한 고려)
        batch_size = 100
        total = len(data)

        for i in range(0, total, batch_size):
            batch = data[i:i+batch_size]
            supabase.table("income_statements").upsert(batch).execute()
            print(f"   진행: {min(i+batch_size, total)}/{total}")

        print(f"   ✅ {total}개 손익계산서 레코드 마이그레이션 완료")
        return True

    except Exception as e:
        print(f"   ❌ 손익계산서 마이그레이션 실패: {e}")
        return False
    finally:
        conn.close()

def migrate_balance_sheets(supabase: Client):
    """재무상태표 데이터 마이그레이션"""
    print("\n⚖️  재무상태표 데이터 마이그레이션 시작...")

    if not os.path.exists('financial_data.db'):
        print("   ⚠️  financial_data.db 파일이 없습니다.")
        return False

    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT corp_code, year, report_type, total_assets, current_assets,
                   non_current_assets, total_liabilities, current_liabilities,
                   non_current_liabilities, total_equity
            FROM balance_sheets
        """)

        rows = cursor.fetchall()

        if not rows:
            print("   ⚠️  재무상태표 데이터가 없습니다.")
            return True

        data = []
        for row in rows:
            data.append({
                "corp_code": row[0],
                "year": row[1],
                "report_type": row[2],
                "total_assets": int(row[3]) if row[3] else None,
                "current_assets": int(row[4]) if row[4] else None,
                "non_current_assets": int(row[5]) if row[5] else None,
                "total_liabilities": int(row[6]) if row[6] else None,
                "current_liabilities": int(row[7]) if row[7] else None,
                "non_current_liabilities": int(row[8]) if row[8] else None,
                "total_equity": int(row[9]) if row[9] else None
            })

        # 배치로 나눠서 업로드
        batch_size = 100
        total = len(data)

        for i in range(0, total, batch_size):
            batch = data[i:i+batch_size]
            supabase.table("balance_sheets").upsert(batch).execute()
            print(f"   진행: {min(i+batch_size, total)}/{total}")

        print(f"   ✅ {total}개 재무상태표 레코드 마이그레이션 완료")
        return True

    except Exception as e:
        print(f"   ❌ 재무상태표 마이그레이션 실패: {e}")
        return False
    finally:
        conn.close()

def migrate_cash_flows(supabase: Client):
    """현금흐름표 데이터 마이그레이션"""
    print("\n💧 현금흐름표 데이터 마이그레이션 시작...")

    if not os.path.exists('financial_data.db'):
        print("   ⚠️  financial_data.db 파일이 없습니다.")
        return False

    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT corp_code, year, report_type, operating_cash_flow,
                   investing_cash_flow, financing_cash_flow, net_cash_flow
            FROM cash_flows
        """)

        rows = cursor.fetchall()

        if not rows:
            print("   ⚠️  현금흐름표 데이터가 없습니다.")
            return True

        data = []
        for row in rows:
            data.append({
                "corp_code": row[0],
                "year": row[1],
                "report_type": row[2],
                "operating_cash_flow": int(row[3]) if row[3] else None,
                "investing_cash_flow": int(row[4]) if row[4] else None,
                "financing_cash_flow": int(row[5]) if row[5] else None,
                "net_cash_flow": int(row[6]) if row[6] else None
            })

        # 배치로 나눠서 업로드
        batch_size = 100
        total = len(data)

        for i in range(0, total, batch_size):
            batch = data[i:i+batch_size]
            supabase.table("cash_flows").upsert(batch).execute()
            print(f"   진행: {min(i+batch_size, total)}/{total}")

        print(f"   ✅ {total}개 현금흐름표 레코드 마이그레이션 완료")
        return True

    except Exception as e:
        print(f"   ❌ 현금흐름표 마이그레이션 실패: {e}")
        return False
    finally:
        conn.close()

def main():
    """메인 마이그레이션 실행"""
    print("=" * 80)
    print("🚀 Supabase 데이터 마이그레이션 시작")
    print("=" * 80)

    # Supabase URL과 KEY 확인
    if SUPABASE_URL == "YOUR_SUPABASE_URL" or SUPABASE_KEY == "YOUR_SUPABASE_ANON_KEY":
        print("\n❌ Supabase URL과 KEY를 설정해주세요!")
        print("\n환경 변수 설정 방법:")
        print("  Windows: set SUPABASE_URL=your_url")
        print("           set SUPABASE_KEY=your_key")
        print("  Linux/Mac: export SUPABASE_URL=your_url")
        print("             export SUPABASE_KEY=your_key")
        return

    # Supabase 클라이언트 생성
    try:
        supabase = get_supabase_client()
        print(f"✅ Supabase 연결 성공: {SUPABASE_URL}")
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        return

    # 순차적으로 마이그레이션 실행
    results = []
    results.append(("기업 정보", migrate_companies(supabase)))
    results.append(("손익계산서", migrate_income_statements(supabase)))
    results.append(("재무상태표", migrate_balance_sheets(supabase)))
    results.append(("현금흐름표", migrate_cash_flows(supabase)))

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 마이그레이션 결과 요약")
    print("=" * 80)

    for name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} - {name}")

    total_success = sum(1 for _, success in results if success)
    print(f"\n총 {total_success}/{len(results)} 항목 마이그레이션 완료")
    print("=" * 80)

if __name__ == "__main__":
    main()
