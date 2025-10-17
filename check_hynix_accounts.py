import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"
HYNIX_CORP_CODE = "00164779"

url = f"{BASE_URL}/fnlttSinglAcntAll.json"
params = {
    "crtfc_key": API_KEY,
    "corp_code": HYNIX_CORP_CODE,
    "bsns_year": "2023",
    "reprt_code": "11011",
    "fs_div": "CFS"
}

response = requests.get(url, params=params)
data = response.json()

if data.get("status") == "000":
    is_items = [item for item in data.get('list', []) if item.get('sj_div') == 'IS']

    print("=" * 100)
    print("SK하이닉스 손익계산서 계정과목 (2023년)")
    print("=" * 100)

    keywords = ['매출', '수익', '영업이익', '원가', '판매비', '관리비']

    for item in is_items:
        account_nm = item.get('account_nm', '')
        if any(kw in account_nm for kw in keywords):
            print(f"{account_nm:50} | {item.get('thstrm_amount', '0'):>20} | {item.get('account_id', '')}")
else:
    print(f"Error: {data.get('message')}")
