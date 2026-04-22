# 공시 자가진단 및 자동 계산 시스템

## 프로젝트 개요
사내 공시 가이드라인 자가진단 및 자동계산 시스템 구축 프로젝트입니다.
- **주요 목적**: 공시 누락 리스크 방지 및 부서 간 정보 전달 효율화
- **핵심 기능**: 공시 규칙 검색, 공시 비율 자동 계산

## 프로젝트 구조

```
disclosure_system/
├── core/
│   ├── __init__.py
│   ├── rule_database.py          # 공시규칙 데이터베이스 관리
│   └── calculation_engine.py     # 공시 자동 계산 엔진
├── data/
│   └── disclosure_rules.json     # 공시 규칙 데이터 (JSON)
├── __init__.py
└── test_integration.py           # 통합 테스트
```

## 완성된 기능

### 1. 공시규칙 데이터베이스 ✅

**파일**: `core/rule_database.py`

#### 주요 기능
- 공시 규칙 JSON 파일 로드 및 관리
- 키워드 검색: "계약", "투자" 등으로 규칙 검색
- 카테고리 검색: "계약", "투자", "증자" 등 카테고리별 조회
- 지표 검색: "sales_ratio", "equity_ratio" 등 기준 지표로 검색
- 모호한 검색: 제목, 설명, 키워드 포함 검색

#### 기본 사용법
```python
from core import DisclosureRuleDatabase

# 데이터베이스 초기화
db = DisclosureRuleDatabase()

# 키워드 검색
results = db.search_by_keyword("계약")

# 카테고리 검색
results = db.search_by_category("투자", market="kospi")

# 지표별 검색
results = db.search_by_threshold_metric("sales_ratio")

# 정량적/정성적 규칙 분류
quantitative_rules = db.get_quantitative_rules()
qualitative_rules = db.get_qualitative_rules()
```

#### 포함된 규칙 (11개)
1. **계약**: 중요 계약 체결 (매출액 10%)
2. **투자**: 유가증권 취득 (자기자본 5%), 타법인 출자 (자산 5%)
3. **증자**: 신주 발행 (즉시 보고)
4. **부채**: 사채 발행 (자산 20%)
5. **인사**: 대표이사 변경 (즉시 보고)
6. **자산**: 중요 자산 매각 (자산 10%)
7. **M&A**: 회사 인수 (자기자본 50%)
8. **소송**: 중요 소송 (자산 5%)
9. **관련거래**: 관계회사와의 거래 (매출액 5%)
10. **기업연속성**: 계속기업 리스크 (누적결손금 50%)

### 2. 공시 자동 계산 엔진 ✅

**파일**: `core/calculation_engine.py`

#### 주요 기능
- 거래 금액 입력 시 공시 의무 비율 자동 계산
- 3단계 판정 결과:
  - **공시 대상**: 기준액 이상
  - **검토 필요**: 기준액의 80% 이상 (기준 근접)
  - **공시 미대상**: 기준액 미만
- 재무 지표 기반 동적 계산
- 여러 거래에 대한 일괄 계산
- 계산 결과 요약

#### 기본 사용법
```python
from decimal import Decimal
from core import (
    DisclosureRuleDatabase,
    DisclosureCalculationEngine,
    FinancialMetrics
)

# 재무 지표 설정
metrics = FinancialMetrics(
    sales=Decimal("10000000000"),      # 매출액: 100억
    total_assets=Decimal("50000000000"),  # 자산: 500억
    equity=Decimal("20000000000")        # 자기자본: 200억
)

# 계산 엔진 초기화
db = DisclosureRuleDatabase()
engine = DisclosureCalculationEngine(db)

# 거래 계산
transaction_amount = Decimal("1500000000")  # 15억
results = engine.calculate(metrics, transaction_amount)

# 결과 확인
for result in results:
    print(f"규칙: {result.rule['title']}")
    print(f"판정: {result.result.value}")
    print(f"기준액: {result.threshold_amount:,.0f}")
    print(f"거래액 비율: {float(result.ratio):.1%}")
```

#### 일괄 계산 예제
```python
# 여러 거래 일괄 처리
transactions = [
    {'amount': 1500000000, 'rule_ids': ['contract_001']},
    {'amount': 2000000000, 'rule_ids': ['investment_001']},
]

results = engine.batch_calculate(metrics, transactions)
```

## 테스트 결과

통합 테스트 실행: `python test_integration.py`

### 테스트 케이스
1. ✅ 매출액 대비 15% 거래 → **공시 대상**
2. ✅ 자기자본 대비 3% 투자 → **공시 미대상**
3. ✅ 자산 대비 8% 투자 → **공시 대상**
4. ✅ 복합 거래 → 8개 규칙 검토 결과 (공시 대상 3개, 미대상 5개)

## 데이터 구조

### 공시 규칙 JSON 스키마
```json
{
  "rule_id": "contract_001",
  "category": "계약",
  "title": "중요 계약 체결",
  "description": "회사가 중요한 거래 계약을 체결하는 경우",
  "rule_type": "quantitative",  // quantitative 또는 qualitative
  "market": ["kospi", "kosdaq"],
  "threshold": {
    "metric": "sales_ratio",
    "value": 10,
    "unit": "%",
    "description": "연간 매출액의 10% 이상"
  },
  "reference": "유가증권시장 공시규정 §3.2",
  "disclosure_period": "즉시",
  "keywords": ["계약", "거래", "주문"]
}
```

### 계산 결과 구조
```python
CalculationResult(
    rule: Dict,                    # 적용된 규칙
    transaction_amount: Decimal,   # 거래 금액
    threshold_amount: Decimal,     # 공시 기준 금액
    ratio: Decimal,                # 거래액 / 기준액 비율
    result: DisclosureResult,      # 판정 (enum)
    reason: str,                   # 판정 근거
    metric_type: str,              # 기준 지표명
    metric_value: Decimal          # 기준 지표값
)
```

## Phase 2: Streamlit 웹 인터페이스 ✅

### 🌐 웹 인터페이스 기능
1. **📖 공시규칙 검색**
   - 키워드 검색 (예: "계약", "투자")
   - 카테고리별 검색
   - 기준 지표별 검색

2. **🧮 공시 판정 계산**
   - 개별 거래 계산
   - 일괄 거래 계산 (최대 10개)
   - 재무 지표 입력
   - 실시간 계산 결과

3. **📊 결과 표시**
   - 공시 판정 (공시 대상/검토 필요/공시 미대상)
   - 기준액 및 거래액 비교
   - 상세 계산 근거

4. **📋 가이드 및 정보**
   - 사용 가이드
   - 시스템 정보
   - 지원 규칙 목록

### 🚀 웹 앱 실행 방법
```bash
cd disclosure_system
python -m streamlit run app.py
```

앱은 `http://localhost:8501`에서 실행됩니다.

## 다음 단계 (진행 예정)

### Phase 2 추가 개발
1. **결과 다운로드** - Excel/PDF 보고서 생성
2. **데이터 저장** - 조회 이력 저장
3. **사용자 피드백** - 검색 결과 개선

### Phase 3: PDF 파싱 + AI 통합 (예정)
1. **PDF 파싱 모듈** - 감사보고서 자동 추출
2. **Claude AI 통합** - 규정 해석 및 Q&A
3. **사용자 관리** - 부서별 권한 및 로그 기록
4. **보고서 생성** - 공시 판정 결과 보고서

### Phase 3: 테스트 및 배포
1. 부서별 실무자 테스트
2. 피드백 반영
3. 보안 강화 및 최적화
4. 운영 환경 배포

## 설정 및 실행

### 요구사항
- Python 3.8+

### 설치
```bash
cd disclosure_system
```

### 테스트 실행
```bash
python test_integration.py
```

## 제작 정보
- **생성일**: 2024년 4월
- **상태**: Phase 1 완료 ✅
- **다음 단계**: Streamlit UI 개발 예정

## 라이선스
내부용 시스템
