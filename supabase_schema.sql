-- Supabase 재무 데이터베이스 스키마
-- 한국 10대 기업 재무제표 분석 시스템

-- 1. 기업 정보 테이블
CREATE TABLE IF NOT EXISTS companies (
    corp_code VARCHAR(20) PRIMARY KEY,
    corp_name VARCHAR(100) NOT NULL,
    stock_code VARCHAR(10),
    sector VARCHAR(50),
    description TEXT,
    founded INTEGER,
    employees INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 손익계산서 테이블 (Income Statement)
CREATE TABLE IF NOT EXISTS income_statements (
    id SERIAL PRIMARY KEY,
    corp_code VARCHAR(20) REFERENCES companies(corp_code) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    report_type VARCHAR(10) NOT NULL, -- '11011': 연간, '11012': 반기, '11013': 1분기, '11014': 3분기
    revenue BIGINT,
    cost_of_sales BIGINT,
    gross_profit BIGINT,
    selling_admin_expenses BIGINT,
    operating_profit BIGINT,
    operating_margin DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(corp_code, year, report_type)
);

-- 3. 재무상태표 테이블 (Balance Sheet)
CREATE TABLE IF NOT EXISTS balance_sheets (
    id SERIAL PRIMARY KEY,
    corp_code VARCHAR(20) REFERENCES companies(corp_code) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    report_type VARCHAR(10) NOT NULL,
    total_assets BIGINT,
    current_assets BIGINT,
    non_current_assets BIGINT,
    total_liabilities BIGINT,
    current_liabilities BIGINT,
    non_current_liabilities BIGINT,
    total_equity BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(corp_code, year, report_type)
);

-- 4. 현금흐름표 테이블 (Cash Flow Statement)
CREATE TABLE IF NOT EXISTS cash_flows (
    id SERIAL PRIMARY KEY,
    corp_code VARCHAR(20) REFERENCES companies(corp_code) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    report_type VARCHAR(10) NOT NULL,
    operating_cash_flow BIGINT,
    investing_cash_flow BIGINT,
    financing_cash_flow BIGINT,
    net_cash_flow BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(corp_code, year, report_type)
);

-- 인덱스 생성 (쿼리 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_income_corp_year ON income_statements(corp_code, year);
CREATE INDEX IF NOT EXISTS idx_balance_corp_year ON balance_sheets(corp_code, year);
CREATE INDEX IF NOT EXISTS idx_cashflow_corp_year ON cash_flows(corp_code, year);

-- Row Level Security (RLS) 활성화
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE income_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE balance_sheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_flows ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능하도록 정책 설정 (공개 데이터)
CREATE POLICY "Allow public read access" ON companies FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON income_statements FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON balance_sheets FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON cash_flows FOR SELECT USING (true);

-- 기업 정보 초기 데이터 삽입
INSERT INTO companies (corp_code, corp_name, stock_code, sector, description, founded, employees) VALUES
('00126380', '삼성전자', '005930', '전자', '세계 최대 반도체 및 스마트폰 제조사', 1969, 267937),
('00164779', 'SK하이닉스', '000660', '전자', '글로벌 메모리 반도체 선도 기업', 1983, 35246),
('00164742', 'LG에너지솔루션', '373220', '전자', '세계 2위 전기차 배터리 제조사', 2020, 42858),
('00113399', '삼성바이오로직스', '207940', '제약', '글로벌 바이오의약품 위탁생산 선도 기업', 2011, 3124),
('00165890', '현대차', '005380', '자동차', '세계 3위 완성차 제조 그룹', 1967, 120565),
('00164529', '셀트리온', '068270', '제약', '국내 1위 바이오시밀러 제조사', 2002, 4861),
('00167799', '기아', '000270', '자동차', '글로벌 완성차 제조 및 전기차 선도 기업', 1944, 78424),
('00159645', 'POSCO홀딩스', '005490', '철강', '세계적인 철강 및 소재 전문 기업', 1968, 37249),
('00356370', 'KB금융', '105560', '금융', '국내 최대 금융지주회사', 2008, 31524),
('00168099', '신한지주', '055550', '금융', '종합 금융서비스 선도 그룹', 2001, 30187)
ON CONFLICT (corp_code) DO NOTHING;
