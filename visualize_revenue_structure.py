"""
매출 구조 파이차트 시각화
Revenue structure pie chart visualization
"""
import matplotlib.pyplot as plt
import json
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_financial_data(filename='samsung_income_statement.json'):
    """재무 데이터 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {filename}")
        return None

def create_revenue_pie_chart(data):
    """매출 구조 파이차트 생성"""
    if not data:
        print("❌ 데이터가 없습니다.")
        return

    # 매출 관련 데이터 추출
    revenue = data.get('current_period', {}).get('revenue', 0)
    cost_of_sales = data.get('current_period', {}).get('cost_of_sales', 0)
    selling_admin_expenses = data.get('current_period', {}).get('selling_admin_expenses', 0)
    operating_profit = data.get('current_period', {}).get('operating_profit', 0)

    # 조 단위로 변환
    revenue_trillion = revenue / 1_000_000_000_000
    cost_trillion = cost_of_sales / 1_000_000_000_000
    expenses_trillion = selling_admin_expenses / 1_000_000_000_000
    profit_trillion = operating_profit / 1_000_000_000_000

    # 퍼센트 계산
    cost_pct = (cost_of_sales / revenue * 100) if revenue > 0 else 0
    expenses_pct = (selling_admin_expenses / revenue * 100) if revenue > 0 else 0
    profit_pct = (operating_profit / revenue * 100) if revenue > 0 else 0

    # 파이차트 데이터
    labels = [
        f'매출원가\n{cost_trillion:.1f}조원',
        f'판매관리비\n{expenses_trillion:.1f}조원',
        f'영업이익\n{profit_trillion:.1f}조원'
    ]

    sizes = [cost_of_sales, selling_admin_expenses, operating_profit]
    percentages = [cost_pct, expenses_pct, profit_pct]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    explode = (0.05, 0.05, 0.1)  # 영업이익 강조

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(12, 8))

    # 파이차트 그리기
    wedges, texts, autotexts = ax.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12, 'weight': 'bold'}
    )

    # 퍼센트 텍스트 스타일
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_weight('bold')

    # 제목
    company_name = data.get('company_name', '삼성전자')
    year = data.get('year', '2023')
    plt.title(f'{company_name} {year}년 매출 구조 분석\n총 매출: {revenue_trillion:.1f}조원',
              fontsize=16, weight='bold', pad=20)

    # 범례 추가 (항목과 % 표시)
    legend_labels = [
        f'매출원가: {cost_pct:.1f}%',
        f'판매관리비: {expenses_pct:.1f}%',
        f'영업이익: {profit_pct:.1f}%'
    ]
    plt.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1), fontsize=11)

    # 저장
    plt.tight_layout()
    filename = f'{company_name}_revenue_structure_pie.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 파이차트 저장 완료: {filename}")

    # 화면 표시
    plt.show()

    # 상세 정보 출력
    print(f"\n📊 {company_name} {year}년 매출 구조 분석")
    print(f"{'='*50}")
    print(f"총 매출:      {revenue_trillion:>8.1f}조원 (100.0%)")
    print(f"매출원가:     {cost_trillion:>8.1f}조원 ({cost_pct:>5.1f}%)")
    print(f"판매관리비:   {expenses_trillion:>8.1f}조원 ({expenses_pct:>5.1f}%)")
    print(f"영업이익:     {profit_trillion:>8.1f}조원 ({profit_pct:>5.1f}%)")
    print(f"{'='*50}")

def create_detailed_revenue_breakdown():
    """세부 매출 구조 파이차트 (추정값 포함)"""
    # 삼성전자 2023년 매출 구조 (추정)
    data = {
        'company_name': '삼성전자',
        'year': 2023,
        'revenue': 258937694000000,  # 약 259조원
        'segments': {
            '반도체': 86000000000000,   # 33.2%
            '디스플레이': 32000000000000,  # 12.4%
            '모바일': 92000000000000,   # 35.5%
            '가전': 49000000000000      # 18.9%
        }
    }

    revenue = data['revenue']
    segments = data['segments']

    # 퍼센트 계산
    labels = []
    sizes = []
    percentages = []

    for segment, amount in segments.items():
        pct = (amount / revenue * 100)
        trillion = amount / 1_000_000_000_000
        labels.append(f'{segment}\n{trillion:.1f}조원')
        sizes.append(amount)
        percentages.append(pct)

    colors = ['#667EEA', '#764BA2', '#F093FB', '#4FACFE']
    explode = (0.05, 0.05, 0.1, 0.05)

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(12, 8))

    wedges, texts, autotexts = ax.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=140,
        textprops={'fontsize': 12, 'weight': 'bold'}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_weight('bold')

    total_trillion = revenue / 1_000_000_000_000
    plt.title(f'{data["company_name"]} {data["year"]}년 사업부문별 매출 구조\n총 매출: {total_trillion:.1f}조원',
              fontsize=16, weight='bold', pad=20)

    # 범례
    legend_labels = [f'{segment}: {pct:.1f}%' for segment, pct in zip(segments.keys(), percentages)]
    plt.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1), fontsize=11)

    plt.tight_layout()
    filename = f'{data["company_name"]}_segment_revenue_pie.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 사업부문별 파이차트 저장 완료: {filename}")

    plt.show()

    # 상세 정보 출력
    print(f"\n📊 {data['company_name']} {data['year']}년 사업부문별 매출 구조")
    print(f"{'='*50}")
    for segment, amount in segments.items():
        trillion = amount / 1_000_000_000_000
        pct = (amount / revenue * 100)
        print(f"{segment:8s}: {trillion:>8.1f}조원 ({pct:>5.1f}%)")
    print(f"{'='*50}")
    print(f"{'총계':8s}: {total_trillion:>8.1f}조원 (100.0%)")

if __name__ == "__main__":
    print("📊 매출 구조 파이차트 생성 중...\n")

    # 1. 손익계산서 기반 매출 구조
    print("1️⃣  손익계산서 기반 매출 구조 분석")
    financial_data = load_financial_data()
    if financial_data:
        create_revenue_pie_chart(financial_data)

    print("\n" + "="*50 + "\n")

    # 2. 사업부문별 매출 구조 (추정)
    print("2️⃣  사업부문별 매출 구조 분석 (추정)")
    create_detailed_revenue_breakdown()

    print("\n✅ 모든 파이차트 생성 완료!")
