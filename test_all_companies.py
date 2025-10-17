"""
10개 종목 재무제표 테스트
Playwright를 사용하여 모든 기업의 데이터가 정상적으로 표시되는지 확인
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_all_companies():
    companies = [
        {"name": "삼성전자", "code": "00126380"},
        {"name": "SK하이닉스", "code": "00164779"},
        {"name": "LG에너지솔루션", "code": "00164742"},
        {"name": "삼성바이오로직스", "code": "00113399"},
        {"name": "현대차", "code": "00165890"},
        {"name": "셀트리온", "code": "00164529"},
        {"name": "기아", "code": "00167799"},
        {"name": "POSCO홀딩스", "code": "00159645"},
        {"name": "KB금융", "code": "00356370"},
        {"name": "신한지주", "code": "00168099"}
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("=" * 80)
        print("10개 종목 재무제표 테스트 시작")
        print("=" * 80)

        # 인덱스 페이지 접속
        print("\n📋 인덱스 페이지 접속 중...")
        page.goto("http://localhost:8000/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        results = []

        for idx, company in enumerate(companies, 1):
            print(f"\n[{idx}/10] {company['name']} 테스트 중...")

            try:
                # 대시보드 URL로 직접 이동
                dashboard_url = f"http://localhost:8000/final_dashboard.html?company={company['code']}&name={company['name']}&file={company['code']}_10year_data.json"
                print(f"   → URL: {dashboard_url}")

                page.goto(dashboard_url)
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # 차트가 로드되었는지 확인
                chart_canvas = page.query_selector("#trendChart")
                if not chart_canvas:
                    results.append({
                        "company": company['name'],
                        "status": "❌ FAIL",
                        "reason": "차트 캔버스를 찾을 수 없음"
                    })
                    print(f"   ❌ 실패: 차트 캔버스를 찾을 수 없음")
                    continue

                # 검색창에 회사명이 표시되는지 확인
                search_input = page.query_selector("#companySearch")
                search_value = search_input.get_attribute("value") if search_input else ""

                # None 처리
                if search_value is None:
                    search_value = ""

                if search_value and company['name'] in search_value:
                    print(f"   ✅ 검색창: {search_value}")
                else:
                    print(f"   ⚠️  검색창: '{search_value}' (예상: {company['name']})")

                # 차트 제목 확인
                page.wait_for_timeout(1000)  # 차트 렌더링 대기

                # 손익계산서 탭 클릭
                income_btn = page.query_selector("text=📋 손익계산서")
                if income_btn:
                    income_btn.click()
                    page.wait_for_timeout(1000)

                    # 손익계산서 컨테이너 확인
                    income_statement = page.query_selector("#incomeStatement")
                    if income_statement and income_statement.inner_text():
                        print(f"   ✅ 손익계산서: 데이터 표시됨")
                        income_status = "OK"
                    else:
                        print(f"   ⚠️  손익계산서: 데이터 없음")
                        income_status = "NO DATA"
                else:
                    income_status = "NOT FOUND"

                # 재무상태표 탭 클릭
                balance_btn = page.query_selector("text=⚖️ 재무상태표")
                if balance_btn:
                    balance_btn.click()
                    page.wait_for_timeout(1000)

                    balance_sheet = page.query_selector("#balanceSheet")
                    if balance_sheet and balance_sheet.inner_text():
                        print(f"   ✅ 재무상태표: 데이터 표시됨")
                        balance_status = "OK"
                    else:
                        print(f"   ⚠️  재무상태표: 데이터 없음")
                        balance_status = "NO DATA"
                else:
                    balance_status = "NOT FOUND"

                # 현금흐름 탭 클릭
                cashflow_btn = page.query_selector("text=💧 현금흐름")
                if cashflow_btn:
                    cashflow_btn.click()
                    page.wait_for_timeout(1000)

                    cashflow_chart = page.query_selector("#cashflowChart")
                    if cashflow_chart:
                        print(f"   ✅ 현금흐름: 차트 표시됨")
                        cashflow_status = "OK"
                    else:
                        print(f"   ⚠️  현금흐름: 차트 없음")
                        cashflow_status = "NO DATA"
                else:
                    cashflow_status = "NOT FOUND"

                # 스크린샷 저장
                screenshot_path = f"screenshots/{company['code']}_{company['name']}.png"
                page.screenshot(path=screenshot_path)
                print(f"   📸 스크린샷 저장: {screenshot_path}")

                results.append({
                    "company": company['name'],
                    "status": "✅ PASS",
                    "search": search_value,
                    "income": income_status,
                    "balance": balance_status,
                    "cashflow": cashflow_status
                })

                print(f"   ✅ 성공: {company['name']} 데이터 로드 완료")

            except Exception as e:
                results.append({
                    "company": company['name'],
                    "status": "❌ FAIL",
                    "reason": str(e)
                })
                print(f"   ❌ 실패: {str(e)}")

            # 다음 테스트 전 대기
            time.sleep(1)

        # 종목 리스트 버튼 테스트
        print("\n\n📋 종목 리스트 버튼 테스트...")
        list_btn = page.query_selector("text=📋 종목 리스트")
        if list_btn:
            list_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # index.html로 돌아왔는지 확인
            current_url = page.url
            if "index.html" in current_url:
                print("   ✅ 종목 리스트 페이지로 정상 이동")

                # 카드형/리스트형 전환 테스트
                print("\n🎴 카드형/리스트형 전환 테스트...")

                list_toggle = page.query_selector("text=📋 리스트형")
                if list_toggle:
                    list_toggle.click()
                    page.wait_for_timeout(500)

                    # 리스트 아이템 확인
                    list_items = page.query_selector_all(".company-list-item")
                    if len(list_items) == 10:
                        print(f"   ✅ 리스트형: 10개 항목 표시됨")
                    else:
                        print(f"   ⚠️  리스트형: {len(list_items)}개 항목 (예상: 10)")

                    # 스크린샷
                    page.screenshot(path="screenshots/index_list_view.png")
                    print("   📸 스크린샷: screenshots/index_list_view.png")

                card_toggle = page.query_selector("text=🎴 카드형")
                if card_toggle:
                    card_toggle.click()
                    page.wait_for_timeout(500)

                    # 카드 아이템 확인
                    card_items = page.query_selector_all(".company-card")
                    if len(card_items) == 10:
                        print(f"   ✅ 카드형: 10개 항목 표시됨")
                    else:
                        print(f"   ⚠️  카드형: {len(card_items)}개 항목 (예상: 10)")

                    # 스크린샷
                    page.screenshot(path="screenshots/index_card_view.png")
                    print("   📸 스크린샷: screenshots/index_card_view.png")
            else:
                print(f"   ❌ 이동 실패: {current_url}")
        else:
            print("   ❌ 종목 리스트 버튼을 찾을 수 없음")

        browser.close()

        # 결과 요약
        print("\n" + "=" * 80)
        print("테스트 결과 요약")
        print("=" * 80)

        for result in results:
            if result['status'] == "✅ PASS":
                print(f"{result['status']} {result['company']}")
                print(f"     검색창: {result['search']}")
                print(f"     손익계산서: {result['income']} | 재무상태표: {result['balance']} | 현금흐름: {result['cashflow']}")
            else:
                print(f"{result['status']} {result['company']}")
                if 'reason' in result:
                    print(f"     사유: {result['reason']}")

        # 통계
        passed = sum(1 for r in results if r['status'] == "✅ PASS")
        failed = len(results) - passed

        print("\n" + "=" * 80)
        print(f"총 {len(results)}개 종목 테스트 완료")
        print(f"✅ 성공: {passed}개 | ❌ 실패: {failed}개")
        print("=" * 80)

if __name__ == "__main__":
    # screenshots 폴더 생성
    import os
    os.makedirs("screenshots", exist_ok=True)

    test_all_companies()
