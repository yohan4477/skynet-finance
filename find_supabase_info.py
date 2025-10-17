"""
Playwright로 Supabase 프로젝트 정보 찾기
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def find_supabase_info():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 80)
        print("🔍 Supabase 프로젝트 정보 찾기")
        print("=" * 80)

        # Supabase 대시보드로 이동
        print("\n📱 Supabase 대시보드 접속 중...")
        page.goto("https://supabase.com/dashboard/projects", wait_until="domcontentloaded")
        time.sleep(3)

        # 현재 URL 확인
        current_url = page.url
        print(f"   현재 URL: {current_url}")

        # 로그인이 필요한지 확인
        if "login" in current_url or "sign-in" in current_url:
            print("\n⚠️  Supabase 로그인이 필요합니다.")
            print("   브라우저에서 로그인해주세요...")
            print("   로그인 후 Enter를 눌러주세요...")

            # 사용자가 로그인할 시간 대기
            time.sleep(30)

            # 로그인 후 프로젝트 페이지로 다시 이동
            page.goto("https://supabase.com/dashboard/projects", wait_until="domcontentloaded")
            time.sleep(3)

        # 프로젝트 리스트 찾기
        print("\n🔍 프로젝트 찾는 중...")

        # 여러 가능한 선택자 시도
        selectors = [
            'a[href*="/project/"]',
            'div[class*="project"]',
            'button[class*="project"]',
            '[data-testid*="project"]'
        ]

        projects = []
        for selector in selectors:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"   ✅ {len(elements)}개 요소 발견 (selector: {selector})")
                projects.extend(elements)
                break

        if not projects:
            print("   ⚠️  프로젝트를 자동으로 찾을 수 없습니다.")
            print("\n📸 현재 화면 스크린샷 저장...")
            page.screenshot(path="screenshots/supabase_dashboard.png", full_page=True)
            print("   저장됨: screenshots/supabase_dashboard.png")

            print("\n수동으로 확인해주세요:")
            print("1. 브라우저에서 프로젝트를 선택하세요")
            print("2. Project Settings → API로 이동하세요")
            print("3. 준비되면 Enter를 눌러주세요...")

            time.sleep(60)
        else:
            print(f"\n✅ {len(projects)}개 프로젝트 발견!")

            # 첫 번째 프로젝트 클릭
            if len(projects) > 0:
                print("\n첫 번째 프로젝트 선택 중...")
                projects[0].click()
                time.sleep(3)

        # Settings → API 페이지로 이동
        print("\n⚙️  API 설정 페이지로 이동 중...")

        # URL에서 프로젝트 ID 추출
        current_url = page.url
        if "/project/" in current_url:
            project_id = current_url.split("/project/")[1].split("/")[0]
            api_url = f"https://supabase.com/dashboard/project/{project_id}/settings/api"

            print(f"   프로젝트 ID: {project_id}")
            print(f"   API 설정 URL: {api_url}")

            page.goto(api_url, wait_until="domcontentloaded")
            time.sleep(3)
        else:
            # 수동으로 API 설정 찾기
            settings_link = page.query_selector('a[href*="settings"]')
            if settings_link:
                settings_link.click()
                time.sleep(2)

                api_link = page.query_selector('a[href*="api"]')
                if api_link:
                    api_link.click()
                    time.sleep(2)

        # API 정보 추출
        print("\n🔑 API 정보 추출 중...")
        page.screenshot(path="screenshots/supabase_api_settings.png", full_page=True)
        print("   📸 스크린샷 저장: screenshots/supabase_api_settings.png")

        # URL 찾기
        url_elements = page.query_selector_all('input[readonly], code, pre')

        found_url = None
        found_anon_key = None

        for element in url_elements:
            text = element.inner_text() or element.get_attribute('value') or ''

            if 'supabase.co' in text and not found_url:
                found_url = text.strip()
                print(f"\n✅ Supabase URL 발견:")
                print(f"   {found_url}")

            if 'eyJ' in text and len(text) > 100 and not found_anon_key:
                found_anon_key = text.strip()
                print(f"\n✅ ANON KEY 발견:")
                print(f"   {found_anon_key[:50]}...")

        if not found_url or not found_anon_key:
            print("\n⚠️  API 정보를 자동으로 추출할 수 없습니다.")
            print("   스크린샷에서 수동으로 확인해주세요:")
            print("   - Project URL")
            print("   - anon/public key")

        print("\n" + "=" * 80)
        print("브라우저를 열어둡니다. 정보를 확인하고 복사하세요.")
        print("완료 후 이 창에서 Ctrl+C를 눌러주세요.")
        print("=" * 80)

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
    find_supabase_info()
