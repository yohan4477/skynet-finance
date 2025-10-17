"""
Playwright로 Vercel 배포 사이트 확인
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_vercel_site():
    with sync_playwright() as p:
        # 이미 열려있는 브라우저에 연결
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 80)
        print("🌐 Vercel 배포 사이트 확인")
        print("=" * 80)

        # 가능한 Vercel 도메인들 시도
        possible_domains = [
            "https://skynet-finance.vercel.app",
            "https://skynet-finance-yohan4477.vercel.app",
            "https://financial-analysis.vercel.app"
        ]

        working_url = None

        for url in possible_domains:
            print(f"\n🔍 시도 중: {url}")
            try:
                response = page.goto(url, timeout=10000, wait_until="domcontentloaded")

                if response and response.status == 200:
                    print(f"   ✅ 성공! 사이트 발견: {url}")
                    working_url = url

                    # 페이지 제목 확인
                    title = page.title()
                    print(f"   📄 페이지 제목: {title}")

                    # 스크린샷 저장
                    page.screenshot(path=f"screenshots/vercel_site.png")
                    print(f"   📸 스크린샷 저장: screenshots/vercel_site.png")

                    # 페이지 로드 완료 대기
                    time.sleep(2)

                    # 회사 선택 필터가 있는지 확인
                    company_select = page.query_selector("#companySelect")
                    if company_select:
                        print(f"   ✅ 종목 선택 필터 발견!")

                    # 검색창 확인
                    search_input = page.query_selector("#companySearch")
                    if search_input:
                        print(f"   ✅ 검색 기능 발견!")

                    break
                else:
                    print(f"   ❌ 응답 코드: {response.status if response else 'No response'}")

            except Exception as e:
                print(f"   ❌ 실패: {str(e)}")

        if not working_url:
            print("\n⚠️  Vercel 도메인을 찾을 수 없습니다.")
            print("   Vercel 대시보드에서 실제 URL을 확인해주세요.")
        else:
            print(f"\n" + "=" * 80)
            print(f"✅ Vercel 배포 사이트: {working_url}")
            print("=" * 80)

        # 브라우저 열린 상태로 유지
        print("\n브라우저를 열어둡니다. 확인 후 Enter를 눌러주세요...")
        input()

        browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("screenshots", exist_ok=True)
    check_vercel_site()
