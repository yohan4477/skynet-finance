"""
Playwright로 Supabase Gmail 로그인 및 프로젝트 정보 찾기
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def login_and_find_supabase():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 80)
        print("🔍 Supabase Gmail 로그인 및 프로젝트 정보 찾기")
        print("=" * 80)

        # Supabase 로그인 페이지로 이동
        print("\n📱 Supabase 로그인 페이지 접속 중...")
        page.goto("https://supabase.com/dashboard/sign-in", wait_until="domcontentloaded")
        time.sleep(3)

        # Gmail 로그인 버튼 찾기
        print("\n🔍 Gmail 로그인 버튼 찾는 중...")

        # 여러 가능한 선택자 시도
        gmail_selectors = [
            'button:has-text("Google")',
            'button:has-text("Continue with Google")',
            'a:has-text("Google")',
            '[data-provider="google"]',
            'button[class*="google"]'
        ]

        gmail_button = None
        for selector in gmail_selectors:
            try:
                gmail_button = page.query_selector(selector)
                if gmail_button:
                    print(f"   ✅ Gmail 로그인 버튼 발견! (selector: {selector})")
                    break
            except:
                continue

        if gmail_button:
            print("\n🔘 Gmail 로그인 버튼 클릭 중...")
            gmail_button.click()
            time.sleep(3)
        else:
            print("\n⚠️  Gmail 로그인 버튼을 자동으로 찾을 수 없습니다.")
            print("   수동으로 Gmail 버튼을 클릭해주세요...")
            time.sleep(10)

        # Gmail 로그인 페이지 대기
        print("\n📧 Gmail 로그인 페이지 대기 중...")
        print("   브라우저에서 Gmail 계정으로 로그인해주세요...")
        print("   (이메일 입력 → 다음 → 비밀번호 입력 → 다음)")

        # 로그인 완료될 때까지 대기 (최대 120초)
        print("\n⏳ 로그인 완료 대기 중... (최대 120초)")

        try:
            # 대시보드 페이지로 리다이렉트될 때까지 대기
            page.wait_for_url("**/dashboard/**", timeout=120000)
            print("   ✅ 로그인 성공!")
        except:
            print("   ⚠️  자동 감지 실패. 수동으로 확인해주세요.")
            print("   로그인이 완료되면 Enter를 눌러주세요...")
            time.sleep(60)

        # 프로젝트 페이지로 이동
        print("\n📂 프로젝트 페이지로 이동 중...")
        page.goto("https://supabase.com/dashboard/projects", wait_until="domcontentloaded")
        time.sleep(5)

        # 페이지 스크린샷
        print("\n📸 현재 화면 스크린샷 저장...")
        page.screenshot(path="screenshots/supabase_projects.png", full_page=True)
        print("   저장됨: screenshots/supabase_projects.png")

        # 프로젝트 링크 찾기
        print("\n🔍 프로젝트 찾는 중...")

        # 프로젝트 링크 선택자들
        project_selectors = [
            'a[href*="/project/"]',
            '[data-testid*="project-card"]',
            'div[class*="project"] a',
            'button:has-text("View")'
        ]

        project_links = []
        for selector in project_selectors:
            elements = page.query_selector_all(selector)
            if elements and len(elements) > 0:
                print(f"   ✅ {len(elements)}개 프로젝트 발견! (selector: {selector})")
                project_links = elements
                break

        if project_links:
            print(f"\n프로젝트 목록:")
            for i, link in enumerate(project_links[:5]):  # 최대 5개만 표시
                try:
                    text = link.inner_text()
                    href = link.get_attribute('href')
                    print(f"   {i+1}. {text} - {href}")
                except:
                    pass

            # 첫 번째 프로젝트 클릭
            print(f"\n첫 번째 프로젝트 선택 중...")
            project_links[0].click()
            time.sleep(5)

            # 현재 URL에서 프로젝트 ID 추출
            current_url = page.url
            print(f"   현재 URL: {current_url}")

            if "/project/" in current_url:
                project_id = current_url.split("/project/")[1].split("/")[0]
                print(f"   ✅ 프로젝트 ID: {project_id}")

                # API 설정 페이지로 이동
                api_url = f"https://supabase.com/dashboard/project/{project_id}/settings/api"
                print(f"\n⚙️  API 설정 페이지로 이동: {api_url}")
                page.goto(api_url, wait_until="domcontentloaded")
                time.sleep(5)

                # API 설정 페이지 스크린샷
                print("\n📸 API 설정 페이지 스크린샷 저장...")
                page.screenshot(path="screenshots/supabase_api_settings.png", full_page=True)
                print("   저장됨: screenshots/supabase_api_settings.png")

                # API 정보 추출 시도
                print("\n🔑 API 정보 추출 중...")

                # URL과 KEY 찾기
                input_elements = page.query_selector_all('input[readonly], input[type="text"], input[type="password"]')
                code_elements = page.query_selector_all('code, pre')

                all_text_elements = input_elements + code_elements

                found_url = None
                found_anon_key = None

                for element in all_text_elements:
                    try:
                        text = element.inner_text() or element.get_attribute('value') or element.text_content() or ''
                        text = text.strip()

                        # URL 찾기
                        if '.supabase.co' in text and 'http' in text and not found_url:
                            found_url = text
                            print(f"\n✅ Supabase URL:")
                            print(f"   {found_url}")

                        # ANON KEY 찾기
                        if text.startswith('eyJ') and len(text) > 100 and not found_anon_key:
                            found_anon_key = text
                            print(f"\n✅ ANON KEY:")
                            print(f"   {found_anon_key[:60]}...")
                            print(f"   (전체 길이: {len(found_anon_key)} 문자)")

                    except:
                        continue

                if found_url and found_anon_key:
                    print("\n" + "=" * 80)
                    print("✅ API 정보 추출 완료!")
                    print("=" * 80)
                    print(f"\nSUPABASE_URL={found_url}")
                    print(f"SUPABASE_KEY={found_anon_key}")
                    print("\n이 정보를 환경 변수에 설정하세요!")
                    print("=" * 80)
                else:
                    print("\n⚠️  API 정보를 자동으로 추출하지 못했습니다.")
                    print("   스크린샷(screenshots/supabase_api_settings.png)에서 확인하세요:")
                    print("   - Project URL")
                    print("   - anon public key")

        else:
            print("\n⚠️  프로젝트를 찾을 수 없습니다.")
            print("   New project 버튼을 눌러 프로젝트를 생성하세요.")

        print("\n" + "=" * 80)
        print("브라우저를 열어둡니다. 정보를 확인하세요.")
        print("완료되면 이 창에서 Ctrl+C를 눌러주세요.")
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
    login_and_find_supabase()
