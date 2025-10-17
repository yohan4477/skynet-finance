"""
현금흐름 막대 그래프 시각화
Cash flow bar chart visualization (10-year or quarterly)
"""
import matplotlib.pyplot as plt
import sqlite3
import sys
import io
import numpy as np

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def get_report_type_name(report_code):
    """보고서 코드를 한글명으로 변환"""
    report_names = {
        "11011": "연간",
        "11012": "반기",
        "11013": "1Q",
        "11014": "3Q"
    }
    return report_names.get(report_code, report_code)

def visualize_10year_cashflow(corp_name="삼성전자"):
    """10년치 연간 현금흐름 시각화"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    # 기업 코드 조회
    cursor.execute('SELECT corp_code FROM companies WHERE corp_name LIKE ?', (f'%{corp_name}%',))
    result = cursor.fetchone()

    if not result:
        print(f"❌ '{corp_name}' 기업을 찾을 수 없습니다.")
        conn.close()
        return

    corp_code = result[0]

    # 10년치 연간 데이터 조회 (11011: 사업보고서)
    cursor.execute('''
        SELECT year, operating_cash_flow, investing_cash_flow, financing_cash_flow
        FROM cash_flows
        WHERE corp_code = ? AND report_type = '11011'
        ORDER BY year
    ''', (corp_code,))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"❌ {corp_name} 현금흐름 데이터가 없습니다.")
        return

    # 데이터 추출
    years = []
    operating_cf = []
    investing_cf = []
    financing_cf = []

    for year, op_cf, inv_cf, fin_cf in results:
        years.append(year)
        # 조 단위로 변환
        operating_cf.append((op_cf / 1_000_000_000_000) if op_cf else 0)
        investing_cf.append((inv_cf / 1_000_000_000_000) if inv_cf else 0)
        financing_cf.append((fin_cf / 1_000_000_000_000) if fin_cf else 0)

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(years))
    width = 0.25

    # 막대 그래프
    bars1 = ax.bar(x - width, operating_cf, width, label='영업활동 CF', color='#45B7D1')
    bars2 = ax.bar(x, investing_cf, width, label='투자활동 CF', color='#FF6B6B')
    bars3 = ax.bar(x + width, financing_cf, width, label='재무활동 CF', color='#4ECDC4')

    # 0원 기준선
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

    # 축 설정
    ax.set_xlabel('연도', fontsize=12, weight='bold')
    ax.set_ylabel('현금흐름 (조원)', fontsize=12, weight='bold')
    ax.set_title(f'{corp_name} 연간 현금흐름 추이 ({years[0]}~{years[-1]})', fontsize=16, weight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    # 값 표시
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 1:  # 1조원 이상만 표시
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=8)

    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)

    plt.tight_layout()
    filename = f'{corp_name}_10year_cashflow.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 10년 현금흐름 차트 저장: {filename}")

    plt.show()

def visualize_quarterly_cashflow(corp_name="삼성전자", year=2024):
    """분기별 현금흐름 시각화"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()

    # 기업 코드 조회
    cursor.execute('SELECT corp_code FROM companies WHERE corp_name LIKE ?', (f'%{corp_name}%',))
    result = cursor.fetchone()

    if not result:
        print(f"❌ '{corp_name}' 기업을 찾을 수 없습니다.")
        conn.close()
        return

    corp_code = result[0]

    # 분기별 데이터 조회
    cursor.execute('''
        SELECT report_type, operating_cash_flow, investing_cash_flow, financing_cash_flow
        FROM cash_flows
        WHERE corp_code = ? AND year = ?
        ORDER BY report_type
    ''', (corp_code, year))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"❌ {corp_name} {year}년 분기별 데이터가 없습니다.")
        return

    # 데이터 추출
    periods = []
    operating_cf = []
    investing_cf = []
    financing_cf = []

    for report_type, op_cf, inv_cf, fin_cf in results:
        period_name = get_report_type_name(report_type)
        periods.append(period_name)
        # 조 단위로 변환
        operating_cf.append((op_cf / 1_000_000_000_000) if op_cf else 0)
        investing_cf.append((inv_cf / 1_000_000_000_000) if inv_cf else 0)
        financing_cf.append((fin_cf / 1_000_000_000_000) if fin_cf else 0)

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(12, 8))

    x = np.arange(len(periods))
    width = 0.25

    # 막대 그래프
    bars1 = ax.bar(x - width, operating_cf, width, label='영업활동 CF', color='#45B7D1')
    bars2 = ax.bar(x, investing_cf, width, label='투자활동 CF', color='#FF6B6B')
    bars3 = ax.bar(x + width, financing_cf, width, label='재무활동 CF', color='#4ECDC4')

    # 0원 기준선
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

    # 축 설정
    ax.set_xlabel('보고기간', fontsize=12, weight='bold')
    ax.set_ylabel('현금흐름 (조원)', fontsize=12, weight='bold')
    ax.set_title(f'{corp_name} {year}년 분기별 현금흐름', fontsize=16, weight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(periods)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    # 값 표시
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.5:  # 0.5조원 이상만 표시
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=9)

    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)

    plt.tight_layout()
    filename = f'{corp_name}_{year}_quarterly_cashflow.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 분기별 현금흐름 차트 저장: {filename}")

    plt.show()

def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='현금흐름 차트 생성')
    parser.add_argument('--company', type=str, default='삼성전자', help='기업명 (기본: 삼성전자)')
    parser.add_argument('--mode', choices=['10year', 'quarterly'], default='10year', help='차트 유형')
    parser.add_argument('--year', type=int, default=2024, help='분기별 차트 연도 (기본: 2024)')

    args = parser.parse_args()

    print(f"📊 {args.company} 현금흐름 차트 생성 중...\n")

    if args.mode == '10year':
        visualize_10year_cashflow(args.company)
    else:
        visualize_quarterly_cashflow(args.company, args.year)

    print("\n✅ 차트 생성 완료!")

if __name__ == "__main__":
    main()
