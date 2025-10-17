# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial data analysis and visualization platform for Korean companies. Collects financial statements from Korea's DART API (Financial Supervisory Service electronic disclosure system) and provides interactive web dashboards with T-Account visualizations.

**Dual Architecture**: Supports both JSON-file based workflow (original) and SQLite database workflow (new). Top 10 Korean companies by market cap are tracked.

## Development Commands

### Database Workflow (Recommended for Multi-Company)
```bash
# 1. Database setup
python database_setup.py                # Create DB schema + insert top 10 companies

# 2. Automated data collection for all companies
python background_fetcher.py            # Fetch all companies (10 years + quarterly)

# 3. Query database
python query_database.py --list         # List all companies
python query_database.py --company "삼성전자"
python query_database.py --company "삼성" --year 2024
python query_database.py --quarterly "SK하이닉스" 2024
```

### Legacy JSON Workflow (Original)
```bash
# Manual single-company data collection
python fetch_samsung_financials.py      # 2023 income statement
python fetch_multi_year_data.py [corp_code] [corp_name]
python fetch_balance_sheet.py           # Balance sheet data
python fetch_cashflow_data.py           # Annual + quarterly cash flows

# Batch processing for all top 10 companies
python fetch_all_data.py                # Calls fetch scripts for each company

# Data validation
python check_hynix_accounts.py
python analyze_data.py
```

### Visualization
```bash
# Generate static charts
python visualize_income_statement.py    # Creates PNG charts

# Interactive dashboard (requires local server)
python -m http.server 8000
# Then open: http://localhost:8000/final_dashboard.html
```

### Testing
```bash
# E2E dashboard tests (requires server running)
python test_dashboard.py
python test_final.py
```

## Architecture Overview

### Data Pipeline Flow

**JSON Workflow**:
```
DART API → JSON (raw) → Parse/Extract → JSON (structured) → Dashboard/Charts
```

**Database Workflow**:
```
DART API → Parse/Extract → SQLite DB → Query/Export → Analysis/Visualization
```

### Architecture Evolution

The project has evolved from a single-company JSON-based system to a dual-architecture supporting both:

1. **JSON Files** (original): Best for quick prototyping, single-company analysis, and web dashboard consumption
2. **SQLite Database** (new): Best for multi-company analysis, historical tracking, and structured queries

**Key Decision**: Both systems coexist. JSON workflow feeds `final_dashboard.html`, while database workflow enables `query_database.py` for multi-company analysis.

### Technology Stack
- **Data Collection**: Python + `requests` library
- **Data Storage**: Dual-mode (JSON files OR SQLite database `financial_data.db`)
- **Static Visualization**: Matplotlib with Malgun Gothic font
- **Interactive Dashboard**: HTML/CSS/JS with Chart.js 4.4.0
- **Testing**: Playwright (sync_api)

### Core Components

**1. Data Fetchers (Python)**
- Each fetcher targets specific financial statement types (Income Statement, Balance Sheet, Cash Flow)
- Uses DART API with IFRS-compliant account IDs
- **Legacy**: Outputs both raw and parsed JSON files
- **New**: Writes directly to SQLite database via `background_fetcher.py`
- 0.5s delay between API calls for rate limiting

**2. Database Architecture (New System)**
```python
# Tables
companies          # Corp code, name, stock code, sector
income_statements  # Revenue, costs, operating profit by year/report type
balance_sheets     # Assets, liabilities, equity by year/report type
cash_flows         # Operating/investing/financing CF by year/report type

# Top 10 Companies by Market Cap (defined in database_setup.py)
삼성전자 (00126380), SK하이닉스 (00164779), LG에너지솔루션 (00164742)
삼성바이오로직스 (00113399), 현대차 (00165890), 셀트리온 (00164529)
기아 (00167799), POSCO홀딩스 (00159645), KB금융 (00356370), 신한지주 (00168099)
```

**3. DART API Configuration**
```python
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"

# Report Codes (reprt_code parameter)
"11011" = Annual Business Report (사업보고서)
"11012" = H1 Semi-Annual Report (반기보고서)
"11013" = Q1 Report (1분기보고서)
"11014" = Q3 Report (3분기보고서)

# Statement Types (sj_div parameter)
"IS" = Income Statement (손익계산서)
"BS" = Balance Sheet (재무상태표)
"CF" or "CIS" = Cash Flow Statement (현금흐름표)

# Financial Statement Division (fs_div parameter)
"CFS" = Consolidated Financial Statement (연결재무제표) - RECOMMENDED
"OFS" = Separate Financial Statement (개별재무제표)
```

**4. IFRS Account ID System**
Critical for reliable data extraction. Common account IDs:
```python
# Income Statement
'ifrs-full_Revenue'
'ifrs-full_CostOfSales'
'dart_OperatingIncomeLoss'
'dart_TotalSellingGeneralAdministrativeExpenses'

# Balance Sheet
'ifrs-full_Assets'
'ifrs-full_CurrentAssets'
'ifrs-full_Liabilities'
'ifrs-full_Equity'

# Cash Flow
'ifrs-full_CashFlowsFromUsedInOperatingActivities'
'ifrs-full_CashFlowsFromUsedInInvestingActivities'
'ifrs-full_CashFlowsFromUsedInFinancingActivities'
```

**5. Dashboard Architecture (final_dashboard.html)**
- ~950 lines, single-page application with Chart.js 4.4.0 + datalabels plugin
- Four interactive views: Trend Analysis, Income Statement, Balance Sheet, Cash Flow
- Uses async JSON data loading from: `samsung_10year_data.json`, `hynix_financial_data.json`, `samsung_quarterly_data.json`, `samsung_cashflow_data.json`
- Company selection: Samsung only, SK Hynix only, or comparative side-by-side
- T-Account visualization with proportional heights based on financial amounts
- Period toggle: Annual vs Quarterly views for trend and cashflow charts
- Dual Y-axis charts: Left (조원), Right (%) for operating margin visualization

### Key Architectural Patterns

**Proportional T-Account Visualization**
```javascript
// Height calculation for visual hierarchy
height = (amount / total) × 500px
```
Creates intuitive visual representation where larger amounts appear taller.

**Estimated Component Breakdown**
When detailed account components are unavailable, uses industry-standard ratios:
```
Cost of Sales: Materials (60%), Labor (25%), Overhead (15%)
SG&A: R&D (40%), Marketing (25%), Personnel (35%)
```

**UTF-8 Output Wrapper**
Required for Korean language support on Windows:
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

**Dual-Axis Charting**
Trend analysis uses two Y-axes:
- Left: Revenue & Operating Profit (조원 = trillion won)
- Right: Operating Margin (%)

## Data Files

### File Naming Convention

**Legacy Files (Single Company)**:
```
samsung_financial_raw.json          # Raw 2023 API response
samsung_income_statement.json       # Parsed income statement
samsung_10year_data.json            # Historical trends (2015-2024)
samsung_balance_sheet.json          # Balance sheet
samsung_cashflow_data.json          # Cash flow (annual + quarterly)
samsung_quarterly_data.json         # Quarterly revenue/profit
hynix_financial_data.json           # SK Hynix comparison data
```

**New Files (Multi-Company by Corp Code)**:
```
{corp_code}_10year_data.json        # 10-year annual data
{corp_code}_quarterly_data.json     # Quarterly data
{corp_code}_cashflow_data.json      # Cash flow data

Examples:
00126380_10year_data.json           # Samsung Electronics
00164779_10year_data.json           # SK Hynix
00164742_10year_data.json           # LG Energy Solution
```

### Sample Data Schema
```json
{
  "year": 2024,
  "revenue": 300870903000000,
  "operating_profit": 32725961000000,
  "cost_of_sales": 186562268000000,
  "operating_margin": 10.88
}
```

## Development Notes

### Adding New Companies

**Database Method (Recommended)**:
1. Get corp_code from DART API company search: https://opendart.fss.or.kr/api/company.json
2. Add to `get_top_10_companies()` function in `database_setup.py`
3. Run `python database_setup.py` to update companies table
4. Run `python background_fetcher.py` to collect all data
5. Query using `python query_database.py --company "회사명"`

**JSON Method (Legacy)**:
1. Get corp_code from DART's company search
2. Run `python fetch_multi_year_data.py {corp_code} "회사명"`
3. Run `python fetch_multi_year_data_quarterly.py {corp_code} "회사명"`
4. Run `python fetch_cashflow_data.py {corp_code} "회사명"`
5. Update dashboard.html with new company option (if needed)
6. Add data file references to dashboard's fetch() calls

### Adding New Financial Metrics

**For Database System**:
1. Find IFRS account_id in DART API response (inspect raw API call)
2. Update parsing functions in `background_fetcher.py`: `parse_income_statement()`, `parse_balance_sheet()`, or `parse_cash_flow()`
3. Add column to appropriate table in `database_setup.py` schema
4. Run `python database_setup.py` to update schema
5. Re-fetch data with `python background_fetcher.py`

**For JSON System**:
1. Find IFRS account_id or account_nm in raw DART API response
2. Add extraction logic to fetcher script (e.g., `fetch_multi_year_data.py:extract_key_metrics()`)
3. Update JSON schema and output structure
4. Add visualization logic to dashboard.html

### Modifying Visualizations
- Static charts: Edit `visualize_income_statement.py`
- Interactive charts: Edit chart configuration in `final_dashboard.html`
- Chart.js documentation: https://www.chartjs.org/docs/latest/

### Testing Considerations
- Dashboard requires local HTTP server (CORS restrictions)
- Playwright tests expect Chromium browser installed
- Tests capture screenshots for visual validation
- Check browser console for JavaScript errors during testing

## Korean Language Support

### Font Configuration
```python
# Matplotlib (Python)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# HTML (Dashboard)
font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
```

### Character Encoding
All Python scripts use UTF-8 output wrapper. JSON files are UTF-8 encoded.

### Script Arguments and Parameters

**Fetcher Scripts Accept Command-Line Arguments**:
```bash
python fetch_multi_year_data.py {corp_code} {corp_name}
python fetch_multi_year_data_quarterly.py {corp_code} {corp_name}
python fetch_cashflow_data.py {corp_code} {corp_name}

# Examples
python fetch_multi_year_data.py 00126380 "삼성전자"
python fetch_multi_year_data.py 00164779 "SK하이닉스"
```

**Database Query Arguments**:
```bash
query_database.py --list                    # List all companies
query_database.py --company {name}          # Search by company name
query_database.py --company {name} --year {year}    # Specific year
query_database.py --quarterly {name} {year} # Quarterly comparison
```

## Performance Characteristics

- API data collection: ~5-10s for 10 years of data (single company)
- Background fetcher: ~5-10 minutes for all 10 companies (annual + quarterly + 3 years)
- Dashboard load time: <2s for all charts
- Playwright test execution: ~15-20s per test
- API rate limiting: 0.5s delay between requests
- Database queries: <100ms for typical operations

## Common Tasks

### Update Financial Data

**Database System**:
```bash
python background_fetcher.py        # Updates all 10 companies automatically
```

**JSON System**:
```bash
# Refresh Samsung data
python fetch_samsung_financials.py
python fetch_multi_year_data.py 00126380 "삼성전자"
python fetch_balance_sheet.py
python fetch_cashflow_data.py 00126380 "삼성전자"

# Refresh all top 10 companies
python fetch_all_data.py
```

### Validate Data Integrity
```python
# Check accounting equation: Assets = Liabilities + Equity
# Check T-Account balance: Debits = Credits
# Verify period consistency
```

### Debug Dashboard Issues
1. Start server: `python -m http.server 8000`
2. Open browser DevTools (F12)
3. Check Console tab for JavaScript errors
4. Check Network tab for failed JSON loads
5. Verify JSON files exist and contain valid data

## Important Implementation Details

### Data Parsing Strategy

The project uses **two different parsing approaches** depending on the script:

**IFRS Account IDs** (database_setup.py, background_fetcher.py):
```python
account_id == "ifrs-full_Revenue"
account_id == "ifrs-full_CostOfSales"
```

**Account Names** (fetch_multi_year_data.py, legacy scripts):
```python
account_nm in ["매출액", "수익(매출액)", "매출"]
account_nm in ["영업이익", "영업이익(손실)"]
```

**Recommendation**: IFRS account IDs are more reliable as they're standardized, but account names handle edge cases where IFRS IDs are missing.

### Report Type Handling

Scripts fetch multiple report types per year for complete data coverage:
- **11011** (Annual): Most comprehensive, use as primary source
- **11012** (H1): Semi-annual data
- **11013** (Q1): First quarter
- **11014** (Q3): Third quarter

**Q2 and Q4**: Q2 data is in H1 report (11012), Q4 data is in Annual report (11011).

### Database Schema Constraints

The database uses `UNIQUE(corp_code, year, report_type)` constraints, meaning:
- Re-running `background_fetcher.py` safely updates existing records via `INSERT OR REPLACE`
- No duplicate entries possible for same company/year/period combination
- Safe to run multiple times without data corruption

### Amount Format Handling

DART API returns amounts as strings with commas: `"1,234,567,890"`

**All parsers must**:
```python
amount = int(item.get('thstrm_amount', '0').replace(',', ''))
```

Dashboard displays in 조원 (trillion won):
```javascript
amount_in_trillion = amount / 1_000_000_000_000
```
