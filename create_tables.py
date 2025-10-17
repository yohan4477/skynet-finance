"""
Supabase 테이블 생성 스크립트
"""
import sys
import io
from dotenv import load_dotenv
import os

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env 파일 로드
load_dotenv()

try:
    from supabase import create_client, Client
    import psycopg2
except ImportError as e:
    print(f"❌ 필요한 라이브러리가 없습니다: {e}")
    print("설치: pip install --user supabase psycopg2-binary")
    sys.exit(1)

# PostgreSQL 직접 연결 정보
POSTGRES_URL = os.getenv("POSTGRES_URL", "")

if not POSTGRES_URL:
    print("❌ POSTGRES_URL 환경 변수가 설정되지 않았습니다!")
    sys.exit(1)

def create_tables():
    print("=" * 80)
    print("🗄️  Supabase 테이블 생성")
    print("=" * 80)

    # SQL 스키마 읽기
    with open('supabase_schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    try:
        # PostgreSQL 직접 연결
        print(f"\n📡 PostgreSQL 연결 중...")
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        print("✅ 연결 성공!")

        # SQL 실행
        print("\n📝 테이블 생성 중...")
        cursor.execute(schema_sql)
        conn.commit()

        print("✅ 테이블 생성 완료!")

        # 생성된 테이블 확인
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n📊 생성된 테이블 목록 ({len(tables)}개):")
        for table in tables:
            print(f"   ✅ {table[0]}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("✅ 테이블 생성 완료! 이제 migrate_to_supabase.py를 실행하세요.")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()
