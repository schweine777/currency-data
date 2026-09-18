# currency-data

야후 파이낸스(Yahoo Finance) 데이터를 기반으로 전 세계 주요 통화의 기간별 환율 변동 추이 그래프를 자동으로 생성하고 관리하는 프로젝트입니다.

---

## 📌 주요 기능

- **야후 파이낸스(`yfinance`) 연동**: 전 세계 56개 주요 통화(`{CODE}KRW=X`)의 환율 시계열 데이터를 실시간/배치로 조회
- **다양한 기간별 시각화**: 통화당 총 8개 기간의 차트(PNG) 자동 생성
  - 단기 (1시간 단위 샘플링): `1주 (1wk)`, `1개월 (1mo)`
  - 중·장기 (1일 단위 샘플링): `3개월 (3mo)`, `6개월 (6mo)`, `1년 (1y)`, `3년 (3y)`, `5년 (5y)`, `10년 (10y)`
- **100단위 통화 보정**: 일본 엔화(JPY), 베트남 동(VND), 인도네시아 루피아(IDR) 등 100단위 고시 통화의 단위 보정 로직 내장
- **GitHub Actions 자동화**: 워크플로우를 통한 그래프 일괄 생성, 자동 Git 커밋 & 푸시, 오류 발생 시 텔레그램 알림

---

## 📂 디렉터리 구조

```text
currency-data/
├── .github/
│   └── workflows/
│       └── generate_graphs_workflow.yml    # 환율 그래프 생성 및 자동 푸시 워크플로우
├── script/
│   ├── graph/                              # 56개 통화별 기간별 생성된 PNG 차트 폴더
│   │   ├── usd/                            # 예: USD_1wk.png, USD_1y.png 등
│   │   ├── jpy/
│   │   └── ...
│   └── generate_graph.py                   # 환율 그래프 생성 메인 스크립트
└── README.md
```

---

## 🚀 사용 방법

### 1. 로컬 환경 실행

필요한 라이브러리(`yfinance`, `matplotlib`, `pandas`, `requests`)는 스크립트 실행 시 자동으로 확인 및 설치됩니다.

```bash
cd script

# 전체 56개 통화 그래프 일괄 생성
python generate_graph.py

# 특정 통화만 선택하여 생성 (예: USD, JPY, EUR)
python generate_graph.py usd jpy eur

# 텔레그램 연동 테스트
python generate_graph.py test_telegram
```

### 2. 지원 통화 목록 (총 56개 통화)
```text
USD, EUR, JPY, CNY, HKD, TWD, SGD, THB, VND, PHP, 
INR, IDR, MYR, MOP, MNT, MMK, KHR, KZT, UZS, PKR, 
BDT, LKR, NPR, AUD, NZD, FJD, GBP, CHF, SEK, NOK, 
DKK, RUB, HUF, PLN, CZK, RON, TRY, CAD, MXN, BRL, 
CLP, COP, SAR, AED, KWD, BHD, OMR, JOD, ILS, EGP, 
ZAR, DZD, KES, TZS, ETB, LYD
```

---

## ⚙️ GitHub Actions 자동화

- **워크플로우**: [`.github/workflows/generate_graphs_workflow.yml`](.github/workflows/generate_graphs_workflow.yml)
- **트리거**: GitHub 저장소 Actions 탭에서 `workflow_dispatch`를 통해 수동 실행하거나 외부 스케줄러로 호출 가능
- **필요 Secrets (장애 알림용)**:
  - `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰
  - `TELEGRAM_CHAT_ID`: 알림을 수신할 텔레그램 채팅 ID
