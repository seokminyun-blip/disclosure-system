"""
공시규칙 데이터베이스 + 자동계산엔진 통합 테스트
"""

from decimal import Decimal
from core import (
    DisclosureRuleDatabase,
    DisclosureCalculationEngine,
    FinancialMetrics
)


def test_database():
    """데이터베이스 기능 테스트"""
    print("=" * 60)
    print("공시규칙 데이터베이스 테스트")
    print("=" * 60)
    
    db = DisclosureRuleDatabase()
    
    # 1. 기본 정보
    print("\n[1] 데이터베이스 기본 정보")
    db.print_rule_summary()
    
    # 2. 키워드 검색
    print("\n[2] 키워드 검색: '계약'")
    results = db.search_by_keyword("계약")
    for rule in results:
        print(f"  - {rule['title']}")
    
    # 3. 카테고리 조회
    print("\n[3] 카테고리별 규칙")
    categories = db.get_all_categories()
    for cat in categories:
        rules = db.search_by_category(cat)
        print(f"  {cat}: {len(rules)}개")
    
    # 4. 지표별 규칙
    print("\n[4] 기준 지표별 규칙")
    metrics = ['sales_ratio', 'equity_ratio', 'asset_ratio']
    for metric in metrics:
        rules = db.search_by_threshold_metric(metric)
        print(f"  {metric}: {len(rules)}개")
        for rule in rules:
            threshold = rule['threshold']
            print(f"    - {rule['title']}: {threshold['value']}%")
    
    return db


def test_calculation_engine(db):
    """자동계산엔진 테스트"""
    print("\n" + "=" * 60)
    print("자동계산엔진 테스트")
    print("=" * 60)
    
    # 재무 지표 설정
    metrics = FinancialMetrics(
        sales=Decimal("10000000000"),  # 100억
        total_assets=Decimal("50000000000"),  # 500억
        equity=Decimal("20000000000"),  # 200억
        current_assets=Decimal("15000000000"),
        current_liabilities=Decimal("10000000000"),
        accumulated_loss=Decimal("0"),
        capital=Decimal("5000000000")
    )
    
    engine = DisclosureCalculationEngine(db)
    
    print("\n[재무 지표]")
    print(f"  매출액: {metrics.sales:,.0f}")
    print(f"  자산총액: {metrics.total_assets:,.0f}")
    print(f"  자기자본: {metrics.equity:,.0f}")
    
    # 테스트 케이스
    test_cases = [
        {
            'name': '매출액 대비 15% 계약 (공시 대상)',
            'amount': Decimal("1500000000"),  # 15억
            'rules': ['contract_001']
        },
        {
            'name': '자기자본 대비 3% 투자 (공시 미대상)',
            'amount': Decimal("600000000"),  # 6억
            'rules': ['investment_001']
        },
        {
            'name': '자산 대비 8% 투자 (검토 필요)',
            'amount': Decimal("4000000000"),  # 40억
            'rules': ['investment_002']
        },
        {
            'name': '복합 거래 - 모든 규칙 검토',
            'amount': Decimal("1000000000"),  # 10억
            'rules': None  # 모든 정량적 규칙 적용
        }
    ]
    
    for test_case in test_cases:
        print(f"\n[테스트 케이스] {test_case['name']}")
        print(f"  거래액: {test_case['amount']:,.0f}")
        
        results = engine.calculate(
            metrics,
            test_case['amount'],
            test_case['rules']
        )
        
        if results:
            for result in results:
                print(f"\n  규칙: {result.rule['title']}")
                print(f"    기준: {result.metric_type} (기준액: {result.threshold_amount:,.0f})")
                print(f"    비율: {float(result.ratio):.1%}")
                print(f"    판정: {result.result.value}")
                print(f"    근거: {result.reason}")
            
            # 요약
            summary = engine.get_summary(results)
            print(f"\n  === 요약 ===")
            print(f"    검토 규칙: {summary['total_rules_checked']}개")
            print(f"    공시 대상: {summary['disclosure_required']}개")
            print(f"    검토 필요: {summary['review_required']}개")
            print(f"    공시 미대상: {summary['no_disclosure']}개")
        else:
            print("  (결과 없음)")


def test_batch_calculation(db):
    """일괄 계산 테스트"""
    print("\n" + "=" * 60)
    print("일괄 계산 테스트")
    print("=" * 60)
    
    metrics = FinancialMetrics(
        sales=Decimal("10000000000"),
        total_assets=Decimal("50000000000"),
        equity=Decimal("20000000000")
    )
    
    engine = DisclosureCalculationEngine(db)
    
    # 여러 거래 처리
    transactions = [
        {'amount': 1500000000, 'rule_ids': ['contract_001']},
        {'amount': 2000000000, 'rule_ids': ['investment_001']},
        {'amount': 5000000000, 'rule_ids': ['investment_002']},
    ]
    
    results = engine.batch_calculate(metrics, transactions)
    
    for tx_id, calc_results in results.items():
        print(f"\n{tx_id}:")
        for result in calc_results:
            print(f"  {result.rule['title']}: {result.result.value}")


if __name__ == "__main__":
    # 데이터베이스 테스트
    db = test_database()
    
    # 계산 엔진 테스트
    test_calculation_engine(db)
    
    # 일괄 계산 테스트
    test_batch_calculation(db)
    
    print("\n" + "=" * 60)
    print("모든 테스트 완료")
    print("=" * 60)
