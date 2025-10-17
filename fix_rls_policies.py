"""
RLS 정책 수정 - INSERT 권한 추가
"""
import sys
import io
from dotenv import load_dotenv
import os
import psycopg2

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env 파일 로드
load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL", "")

def fix_rls_policies():
    print("=" * 80)
    print("🔐 RLS 정책 수정")
    print("=" * 80)

    sql = """
-- 기존 정책 삭제
DROP POLICY IF EXISTS "Allow public read access" ON companies;
DROP POLICY IF EXISTS "Allow public read access" ON income_statements;
DROP POLICY IF EXISTS "Allow public read access" ON balance_sheets;
DROP POLICY IF EXISTS "Allow public read access" ON cash_flows;

-- 읽기/쓰기 모두 허용하는 정책 생성
CREATE POLICY "Allow all access" ON companies FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON income_statements FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON balance_sheets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON cash_flows FOR ALL USING (true) WITH CHECK (true);
"""

    try:
        print(f"\n📡 PostgreSQL 연결 중...")
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        print("✅ 연결 성공!")

        print("\n📝 RLS 정책 수정 중...")
        cursor.execute(sql)
        conn.commit()

        print("✅ RLS 정책 수정 완료!")

        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("✅ 완료! 이제 migrate_to_supabase.py를 실행하세요.")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_rls_policies()
