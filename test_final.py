from playwright.sync_api import sync_playwright
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("final_dashboard.html 열기...")
        page.goto("http://localhost:8000/final_dashboard.html")

        time.sleep(3)

        # 스크린샷
        page.screenshot(path="final_dashboard.png")
        print("스크린샷 저장 완료")

        input("\n확인 후 Enter...")
        browser.close()

if __name__ == "__main__":
    test()
