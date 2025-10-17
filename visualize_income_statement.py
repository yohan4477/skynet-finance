import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager
import json
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 데이터 로드
with open('samsung_financial_raw.json', encoding='utf-8') as f:
    data = json.load(f)

# 손익계산서 항목 추출
is_items = {item['account_id']: item for item in data.get('list', []) if item.get('sj_div') == 'IS'}

# 주요 계정과목 (억원 단위로 변환)
revenue = int(is_items['ifrs-full_Revenue']['thstrm_amount']) / 100000000  # 영업수익
cost_of_sales = int(is_items['ifrs-full_CostOfSales']['thstrm_amount']) / 100000000  # 매출원가
selling_admin = int(is_items['dart_TotalSellingGeneralAdministrativeExpenses']['thstrm_amount']) / 100000000  # 판매관리비
operating_profit = int(is_items['dart_OperatingIncomeLoss']['thstrm_amount']) / 100000000  # 영업이익

print("=" * 80)
print("삼성전자 손익계산서 (2023년, 단위: 억원)")
print("=" * 80)
print(f"영업수익(매출): {revenue:,.0f}억원")
print(f"매출원가: {cost_of_sales:,.0f}억원")
print(f"판매관리비: {selling_admin:,.0f}억원")
print(f"영업이익: {operating_profit:,.0f}억원")
print("=" * 80)

# 검증
calculated_profit = revenue - cost_of_sales - selling_admin
print(f"\n검증: {revenue:,.0f} - {cost_of_sales:,.0f} - {selling_admin:,.0f} = {calculated_profit:,.0f}")
print(f"실제 영업이익: {operating_profit:,.0f}")
print(f"차이: {abs(calculated_profit - operating_profit):,.0f}억원")

# T-Account 형식 시각화
fig, ax = plt.subplots(figsize=(14, 10))

# 배경색
ax.set_facecolor('#f8f9fa')
fig.patch.set_facecolor('#ffffff')

# 중앙선
ax.axvline(x=0.5, color='#2c3e50', linewidth=3, linestyle='-')

# 제목
ax.text(0.5, 0.95, '삼성전자 손익계산서 (2023년)',
        ha='center', va='top', fontsize=20, fontweight='bold', color='#2c3e50')
ax.text(0.5, 0.91, 'T-Account 형식 (단위: 억원)',
        ha='center', va='top', fontsize=12, color='#7f8c8d')

# 왼쪽: 비용 항목
left_y_start = 0.80
left_items = [
    ('매출원가', cost_of_sales, '#e74c3c'),
    ('판매관리비', selling_admin, '#e67e22'),
]

ax.text(0.25, 0.85, '【 비용 】', ha='center', va='center',
        fontsize=16, fontweight='bold', color='#c0392b',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#fadbd8', edgecolor='#c0392b', linewidth=2))

current_y = left_y_start
for label, value, color in left_items:
    # 항목명
    ax.text(0.05, current_y, label, ha='left', va='center',
            fontsize=13, fontweight='bold', color='#2c3e50')

    # 금액
    ax.text(0.45, current_y, f'{value:,.0f}', ha='right', va='center',
            fontsize=12, color=color, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, linewidth=1.5))

    current_y -= 0.10

# 소계선
ax.plot([0.05, 0.45], [current_y + 0.05, current_y + 0.05], 'k-', linewidth=2)

# 영업이익 (왼쪽 하단)
ax.text(0.05, current_y - 0.05, '영업이익', ha='left', va='center',
        fontsize=14, fontweight='bold', color='#27ae60')
ax.text(0.45, current_y - 0.05, f'{operating_profit:,.0f}', ha='right', va='center',
        fontsize=13, color='#27ae60', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#d5f4e6', edgecolor='#27ae60', linewidth=2))

# 합계선
ax.plot([0.05, 0.45], [current_y - 0.15, current_y - 0.15], 'k-', linewidth=2)
ax.plot([0.05, 0.45], [current_y - 0.17, current_y - 0.17], 'k-', linewidth=2)

# 왼쪽 합계
left_total = cost_of_sales + selling_admin + operating_profit
ax.text(0.05, current_y - 0.25, '합 계', ha='left', va='center',
        fontsize=13, fontweight='bold', color='#34495e')
ax.text(0.45, current_y - 0.25, f'{left_total:,.0f}', ha='right', va='center',
        fontsize=12, color='#34495e', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ecf0f1', edgecolor='#34495e', linewidth=1.5))

# 오른쪽: 매출 항목
right_y_start = 0.80

ax.text(0.75, 0.85, '【 매출 】', ha='center', va='center',
        fontsize=16, fontweight='bold', color='#2980b9',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#d6eaf8', edgecolor='#2980b9', linewidth=2))

# 매출액
ax.text(0.55, right_y_start, '영업수익', ha='left', va='center',
        fontsize=13, fontweight='bold', color='#2c3e50')
ax.text(0.95, right_y_start, f'{revenue:,.0f}', ha='right', va='center',
        fontsize=12, color='#2980b9', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2980b9', linewidth=1.5))

# 합계선 (오른쪽)
right_total_y = current_y - 0.15
ax.plot([0.55, 0.95], [right_total_y, right_total_y], 'k-', linewidth=2)
ax.plot([0.55, 0.95], [right_total_y - 0.02, right_total_y - 0.02], 'k-', linewidth=2)

# 오른쪽 합계
ax.text(0.55, current_y - 0.25, '합 계', ha='left', va='center',
        fontsize=13, fontweight='bold', color='#34495e')
ax.text(0.95, current_y - 0.25, f'{revenue:,.0f}', ha='right', va='center',
        fontsize=12, color='#34495e', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ecf0f1', edgecolor='#34495e', linewidth=1.5))

# 하단 설명
ax.text(0.5, 0.08, '💡 손익계산서 T-Account 형식 설명',
        ha='center', va='center', fontsize=11, fontweight='bold', color='#7f8c8d')
ax.text(0.5, 0.03, '왼쪽(비용 + 이익) = 오른쪽(매출) | 영업이익 = 매출 - 매출원가 - 판매관리비',
        ha='center', va='center', fontsize=9, color='#95a5a6')

# 축 제거
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# 저장
plt.tight_layout()
plt.savefig('samsung_income_statement_t_account.png', dpi=300, bbox_inches='tight', facecolor='white')
print("\n✅ 시각화 저장 완료: samsung_income_statement_t_account.png")

plt.show()
