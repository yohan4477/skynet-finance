from playwright.sync_api import sync_playwright
import time

def test_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("대시보드 접속 중...")
        page.goto("http://localhost:8000/comprehensive_dashboard.html")

        # 페이지 로드 대기
        time.sleep(3)

        # 콘솔 에러 확인
        page.on("console", lambda msg: print(f"Console: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Page Error: {err}"))

        # 스크린샷
        page.screenshot(path="dashboard_screenshot.png")
        print("스크린샷 저장: dashboard_screenshot.png")

        # 페이지 소스 확인
        content = page.content()
        print(f"\n페이지 HTML 길이: {len(content)} characters")

        # 차트 요소 확인
        chart_canvas = page.query_selector("#trendChart")
        if chart_canvas:
            print("✅ 차트 캔버스 발견")
        else:
            print("❌ 차트 캔버스 없음")

        # 네트워크 에러 확인
        page.route("**/*", lambda route: print(f"Request: {route.request.url}") or route.continue_())
        page.reload()

        time.sleep(5)

        input("\n확인 후 Enter를 눌러 브라우저를 닫으세요...")
        browser.close()

if __name__ == "__main__":
    test_dashboard()
