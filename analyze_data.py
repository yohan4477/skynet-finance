import json
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 원본 데이터 로드
with open('samsung_financial_raw.json', encoding='utf-8') as f:
    data = json.load(f)

# 손익계산서 항목만 필터링
is_items = [item for item in data.get('list', []) if item.get('sj_div') == 'IS']

print("=" * 100)
print("삼성전자 손익계산서 전체 항목")
print("=" * 100)

# 주요 계정과목만 출력
keywords = ['매출', '수익', '영업이익', '원가', '판매비', '관리비', '당기순이익', '법인세']

for item in is_items:
    account_nm = item.get('account_nm', '')
    if any(keyword in account_nm for keyword in keywords):
        thstrm = item.get('thstrm_amount', '0')
        account_id = item.get('account_id', '')
        print(f"{account_nm:40} | {thstrm:>20} | {account_id}")
