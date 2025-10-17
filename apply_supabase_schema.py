"""
Playwright로 Supabase SQL Editor에 스키마 적용
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def apply_schema():
    # SQL 파일 읽기
    with open('supabase_schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 80)
        print("🗄️  Supabase 스키마 적용")
        print("=" * 80)

        # Supabase SQL Editor로 이동
        sql_editor_url = "https://supabase.com/dashboard/project/tnkcxygqguxgiwnqsrcd/sql/new"
        print(f"\n📱 SQL Editor로 이동: {sql_editor_url}")
        page.goto(sql_editor_url, wait_until="domcontentloaded")
        time.sleep(5)

        # SQL 에디터 찾기
        print("\n🔍 SQL 에디터 찾는 중...")

        # Monaco Editor (코드 에디터) 대기
        time.sleep(3)

        # SQL 코드 붙여넣기
        print("\n📝 SQL 스키마 붙여넣기...")

        # 텍스트 영역 또는 contenteditable div 찾기
        editor_selectors = [
            '.monaco-editor textarea',
            'textarea[class*="editor"]',
            'div[contenteditable="true"]',
            'textarea'
        ]

        editor_element = None
        for selector in editor_selectors:
            try:
                editor_element = page.query_selector(selector)
                if editor_element:
                    print(f"   ✅ 에디터 발견! (selector: {selector})")
                    break
            except:
                continue

        if editor_element:
            # 기존 내용 지우고 새 SQL 붙여넣기
            editor_element.click()
            time.sleep(1)

            # Ctrl+A로 전체 선택 후 삭제
            page.keyboard.press('Control+A')
            page.keyboard.press('Delete')
            time.sleep(0.5)

            # SQL 코드 타이핑 (붙여넣기)
            page.keyboard.type(schema_sql, delay=0)
            print("   ✅ SQL 코드 입력 완료!")
            time.sleep(2)
        else:
            print("   ⚠️  에디터를 찾을 수 없습니다. 수동으로 붙여넣기해주세요.")

        # Run 버튼 찾기
        print("\n▶️  Run 버튼 찾는 중...")
        run_button_selectors = [
            'button:has-text("Run")',
            'button:has-text("실행")',
            'button[class*="run"]',
            'button[type="submit"]'
        ]

        run_button = None
        for selector in run_button_selectors:
            try:
                run_button = page.query_selector(selector)
                if run_button:
                    print(f"   ✅ Run 버튼 발견! (selector: {selector})")
                    break
            except:
                continue

        if run_button:
            print("\n🚀 SQL 실행 중...")
            run_button.click()
            time.sleep(5)

            # 성공 메시지 확인
            success_indicators = [
                'text=Success',
                'text=성공',
                'text=Complete',
                '[class*="success"]'
            ]

            for indicator in success_indicators:
                if page.query_selector(indicator):
                    print("   ✅ SQL 실행 성공!")
                    break
        else:
            print("   ⚠️  Run 버튼을 찾을 수 없습니다. 수동으로 실행해주세요.")

        print("\n" + "=" * 80)
        print("브라우저를 열어둡니다. 결과를 확인하세요.")
        print("완료되면 이 창에서 Ctrl+C를 눌러주세요.")
        print("=" * 80)

        print("\n✅ 스키마 SQL:")
        print(schema_sql[:500] + "...")

        # 브라우저 열린 상태로 유지
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n✅ 종료합니다.")

        browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("screenshots", exist_ok=True)
    apply_schema()
