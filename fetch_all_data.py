import subprocess
from database_setup import get_top_10_companies

def run_script(script_name, corp_code, corp_name):
    subprocess.run(["python", script_name, corp_code, corp_name])

if __name__ == "__main__":
    companies = get_top_10_companies()
    for company in companies:
        corp_code = company["corp_code"]
        corp_name = company["corp_name"]
        print(f"Fetching data for {corp_name} ({corp_code})...")
        run_script("fetch_multi_year_data.py", corp_code, corp_name)
        run_script("fetch_multi_year_data_quarterly.py", corp_code, corp_name)
        run_script("fetch_cashflow_data.py", corp_code, corp_name)
