# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

This project is a financial data analysis and visualization platform for Korean semiconductor companies, specifically Samsung Electronics and SK Hynix. It collects financial statements from Korea's DART API (Financial Supervisory Service electronic disclosure system) and provides interactive web dashboards with T-Account visualizations.

## Development Commands

### Data Collection Workflow
```bash
# Complete data collection sequence
python fetch_samsung_financials.py      # 2023 income statement
python fetch_multi_year_data.py         # 10-year historical data (2015-2024)
python fetch_balance_sheet.py           # Balance sheet data
python fetch_cashflow_data.py           # Annual + quarterly cash flows
python fetch_hynix_data.py              # SK Hynix comparison data

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
```
DART API → JSON (raw) → Parse/Extract → JSON (structured) → Dashboard/Charts
```

### Technology Stack
- **Data Collection**: Python + `requests` library
- **Data Format**: JSON files (UTF-8 encoded for Korean text)
- **Static Visualization**: Matplotlib with Malgun Gothic font
- **Interactive Dashboard**: HTML/CSS/JS with Chart.js 4.4.0
- **Testing**: Playwright (sync_api)

### Core Components

**1. Data Fetchers (Python)**
- Each fetcher targets specific financial statement types (Income Statement, Balance Sheet, Cash Flow)
- Uses DART API with IFRS-compliant account IDs
- Outputs both raw and parsed JSON files
- 0.5s delay between API calls for rate limiting

**2. DART API Configuration**
```python
API_KEY = "7344d26c5abb26be017d81af6323416159f5d439"
BASE_URL = "https://opendart.fss.or.kr/api"

# Company Corp Codes
SAMSUNG_CORP_CODE = "00126380"
HYNIX_CORP_CODE = "00164779"

# Report Codes
"11011" = Annual Business Report
"11012" = H1 Semi-Annual Report
"11013" = Q1 Report
"11014" = Q3 Report

# Statement Types (sj_div)
"IS" = Income Statement
"BS" = Balance Sheet
"CF" or "CIS" = Cash Flow Statement
```

**3. IFRS Account ID System**
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

**4. Dashboard Architecture (final_dashboard.html)**
- 777 lines, single-page application
- Four interactive views: Trend Analysis, Income Statement, Balance Sheet, Cash Flow
- Uses Chart.js canvas rendering with async JSON data loading
- Company selection: Samsung only, SK Hynix only, or comparative side-by-side
- T-Account visualization with proportional heights based on financial amounts

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

### JSON Data Structure
```
samsung_financial_raw.json          # Raw 2023 API response
samsung_income_statement.json       # Parsed income statement
samsung_10year_data.json            # Historical trends (2015-2024)
samsung_balance_sheet.json          # Balance sheet
samsung_cashflow_data.json          # Cash flow statements
hynix_financial_data.json           # SK Hynix comparison data
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
1. Get corp_code from DART's company search
2. Create new fetcher script following existing patterns
3. Update dashboard.html with new company option
4. Add data file to dashboard's fetch() calls

### Adding New Financial Metrics
1. Find IFRS account_id in DART API response
2. Add extraction logic to appropriate fetcher script
3. Update JSON schema
4. Add visualization logic to dashboard

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

## Performance Characteristics

- API data collection: ~5-10s for 10 years of data
- Dashboard load time: <2s for all charts
- Playwright test execution: ~15-20s per test
- API rate limiting: 0.5s delay between requests

## Common Tasks

### Update Financial Data
```bash
# Refresh all data sources
python fetch_samsung_financials.py
python fetch_multi_year_data.py
python fetch_balance_sheet.py
python fetch_cashflow_data.py
python fetch_hynix_data.py
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
