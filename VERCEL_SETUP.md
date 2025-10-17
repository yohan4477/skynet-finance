# Vercel 환경 변수 설정 가이드

Vercel 대시보드에서 다음 환경 변수들을 설정하세요.

## 방법

1. Vercel 대시보드 접속: https://vercel.com/dashboard
2. skynet-finance 프로젝트 선택
3. Settings → Environment Variables로 이동
4. 아래 환경 변수들을 추가

## 환경 변수

### SUPABASE_URL
```
https://tnkcxygqguxgiwnqsrcd.supabase.co
```
- Environment: Production, Preview, Development 모두 선택

### SUPABASE_KEY
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRua2N4eWdxZ3V4Z2l3bnFzcmNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2MzMxNjYsImV4cCI6MjA3NjIwOTE2Nn0.w3U5zwSslhB4yi0Xp0C-dRymLYkuA7P1Tv9VXRMdCI4
```
- Environment: Production, Preview, Development 모두 선택

## CLI 명령어 (선택사항)

Vercel CLI 로그인 후 사용 가능:

```bash
# 로그인
vercel login

# 환경 변수 추가
vercel env add SUPABASE_URL production
# 값 입력: https://tnkcxygqguxgiwnqsrcd.supabase.co

vercel env add SUPABASE_KEY production
# 값 입력: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 완료 후

환경 변수 설정 후 Vercel에서 자동으로 재배포가 됩니다.
또는 수동으로 재배포:

```bash
vercel --prod
```

## 확인

https://skynet-finance.vercel.app 접속하여 데이터가 Supabase에서 로드되는지 확인
