from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from decimal import Decimal
from .rule_database import DisclosureRuleDatabase


class DisclosureResult(Enum):
    """공시 판정 결과"""
    DISCLOSURE_REQUIRED = "공시 대상"
    NO_DISCLOSURE = "공시 미대상"
    REVIEW_REQUIRED = "검토 필요"


@dataclass
class FinancialMetrics:
    """재무 지표 데이터"""
    sales: Decimal  # 매출액
    total_assets: Decimal  # 자산총액
    equity: Decimal  # 자기자본
    current_assets: Decimal = Decimal(0)  # 유동자산
    current_liabilities: Decimal = Decimal(0)  # 유동부채
    accumulated_loss: Decimal = Decimal(0)  # 누적 결손금
    capital: Decimal = Decimal(0)  # 자본금
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'sales': float(self.sales),
            'total_assets': float(self.total_assets),
            'equity': float(self.equity),
            'current_assets': float(self.current_assets),
            'current_liabilities': float(self.current_liabilities),
            'accumulated_loss': float(self.accumulated_loss),
            'capital': float(self.capital)
        }


@dataclass
class CalculationResult:
    """계산 결과"""
    rule: Dict  # 적용된 규칙
    transaction_amount: Decimal  # 거래 금액
    threshold_amount: Decimal  # 공시 기준 금액
    ratio: Decimal  # 거래액 / 기준액 비율
    result: DisclosureResult  # 판정 결과
    reason: str  # 판정 근거
    metric_type: str  # 사용된 기준 지표
    metric_value: Decimal  # 기준 지표값
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'rule_id': self.rule['rule_id'],
            'rule_title': self.rule['title'],
            'category': self.rule['category'],
            'transaction_amount': float(self.transaction_amount),
            'threshold_amount': float(self.threshold_amount),
            'ratio': float(self.ratio),
            'result': self.result.value,
            'reason': self.reason,
            'metric_type': self.metric_type,
            'metric_value': float(self.metric_value)
        }


class DisclosureCalculationEngine:
    """공시 자동 계산 엔진"""
    
    def __init__(self, rule_db: DisclosureRuleDatabase = None):
        """
        Args:
            rule_db: 공시규칙 데이터베이스
        """
        self.db = rule_db or DisclosureRuleDatabase()
        self.review_threshold = Decimal('0.8')  # 80% 이상이면 검토 필요
    
    def calculate(
        self,
        financial_metrics: FinancialMetrics,
        transaction_amount: Decimal,
        rule_ids: List[str] = None,
        market: str = "kospi"
    ) -> List[CalculationResult]:
        """
        공시 의무 계산
        
        Args:
            financial_metrics: 재무 지표
            transaction_amount: 거래 금액 또는 투자 금액
            rule_ids: 특정 규칙만 적용 (None이면 모든 정량적 규칙 적용)
            market: 시장 구분 ("kospi", "kosdaq")
        
        Returns:
            계산 결과 리스트
        """
        results = []
        
        # 적용할 규칙 선택
        if rule_ids:
            rules = [self.db.get_rule_by_id(rid) for rid in rule_ids]
            rules = [r for r in rules if r is not None]
        else:
            rules = self.db.get_quantitative_rules(market=market)
        
        # 각 규칙별로 계산
        for rule in rules:
            threshold = rule.get('threshold')
            if not threshold:
                continue
            
            result = self._calculate_for_rule(
                rule, financial_metrics, transaction_amount
            )
            if result:
                results.append(result)
        
        return results
    
    def _calculate_for_rule(
        self,
        rule: Dict,
        financial_metrics: FinancialMetrics,
        transaction_amount: Decimal
    ) -> Optional[CalculationResult]:
        """개별 규칙에 대한 계산 수행"""
        
        threshold = rule.get('threshold')
        metric_type = threshold.get('metric')
        threshold_pct = Decimal(threshold.get('value'))
        
        # 기준 지표값 계산
        metric_value = self._get_metric_value(metric_type, financial_metrics)
        
        if metric_value is None:
            return None
        
        # 공시 기준 금액 계산
        threshold_amount = metric_value * (threshold_pct / 100)
        
        # 거래 금액 대비 비율 계산
        if threshold_amount > 0:
            ratio = transaction_amount / threshold_amount
        else:
            ratio = Decimal(0)
        
        # 판정 결과 결정
        result, reason = self._determine_result(
            ratio, threshold_pct, transaction_amount, threshold_amount
        )
        
        return CalculationResult(
            rule=rule,
            transaction_amount=transaction_amount,
            threshold_amount=threshold_amount,
            ratio=ratio,
            result=result,
            reason=reason,
            metric_type=metric_type,
            metric_value=metric_value
        )
    
    def _get_metric_value(
        self,
        metric_type: str,
        financial_metrics: FinancialMetrics
    ) -> Optional[Decimal]:
        """기준 지표값 조회"""
        
        metric_map = {
            'sales_ratio': financial_metrics.sales,
            'asset_ratio': financial_metrics.total_assets,
            'equity_ratio': financial_metrics.equity,
            'current_asset_ratio': financial_metrics.current_assets,
            'accumulated_loss_ratio': financial_metrics.accumulated_loss
        }
        
        return metric_map.get(metric_type)
    
    def _determine_result(
        self,
        ratio: Decimal,
        threshold_pct: Decimal,
        transaction_amount: Decimal,
        threshold_amount: Decimal
    ) -> Tuple[DisclosureResult, str]:
        """판정 결과 결정"""
        
        if transaction_amount < threshold_amount:
            result = DisclosureResult.NO_DISCLOSURE
            reason = f"거래액({transaction_amount:,.0f})이 기준액({threshold_amount:,.0f})보다 낮음"
        
        elif ratio >= Decimal(1.0):
            result = DisclosureResult.DISCLOSURE_REQUIRED
            reason = f"거래액이 기준액의 {float(ratio):.1%}에 해당 - 공시 의무 발생"
        
        elif ratio >= self.review_threshold:
            result = DisclosureResult.REVIEW_REQUIRED
            reason = f"거래액이 기준액의 {float(ratio):.1%}에 해당 - 기준 근접 (검토 필요)"
        
        else:
            result = DisclosureResult.NO_DISCLOSURE
            reason = f"거래액이 기준액의 {float(ratio):.1%}에 해당 - 공시 대상 아님"
        
        return result, reason
    
    def batch_calculate(
        self,
        financial_metrics: FinancialMetrics,
        transactions: List[Dict],
        market: str = "kospi"
    ) -> Dict[str, List[CalculationResult]]:
        """
        여러 거래에 대한 일괄 계산
        
        Args:
            financial_metrics: 재무 지표
            transactions: 거래 정보 리스트
                [{'amount': 1000000, 'rule_ids': ['contract_001']}, ...]
            market: 시장 구분
        
        Returns:
            거래별 계산 결과 딕셔너리
        """
        results = {}
        
        for idx, transaction in enumerate(transactions):
            transaction_amount = Decimal(str(transaction['amount']))
            rule_ids = transaction.get('rule_ids')
            
            calc_results = self.calculate(
                financial_metrics, transaction_amount, rule_ids, market
            )
            results[f"transaction_{idx}"] = calc_results
        
        return results
    
    def get_summary(self, calculation_results: List[CalculationResult]) -> Dict:
        """계산 결과 요약"""
        
        disclosure_count = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.DISCLOSURE_REQUIRED
        )
        review_count = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.REVIEW_REQUIRED
        )
        no_disclosure_count = len(calculation_results) - disclosure_count - review_count
        
        return {
            'total_rules_checked': len(calculation_results),
            'disclosure_required': disclosure_count,
            'review_required': review_count,
            'no_disclosure': no_disclosure_count,
            'requires_action': disclosure_count + review_count > 0
        }


# 테스트 코드
if __name__ == "__main__":
    # 재무 지표 설정
    metrics = FinancialMetrics(
        sales=Decimal("1000000000"),  # 10억
        total_assets=Decimal("5000000000"),  # 50억
        equity=Decimal("2000000000"),  # 20억
        current_assets=Decimal("1000000000"),
        accumulated_loss=Decimal("0")
    )
    
    # 계산 엔진 초기화
    db = DisclosureRuleDatabase()
    engine = DisclosureCalculationEngine(db)
    
    print("=== 공시 자동 계산 엔진 테스트 ===\n")
    
    # 테스트 1: 매출액의 15% 거래
    transaction_amount = Decimal("150000000")  # 1.5억
    print(f"거래액: {transaction_amount:,.0f}")
    print(f"매출액: {metrics.sales:,.0f}\n")
    
    results = engine.calculate(metrics, transaction_amount)
    
    for result in results:
        print(f"규칙: {result.rule['title']}")
        print(f"  기준 지표: {result.metric_type}")
        print(f"  기준 금액: {result.threshold_amount:,.0f}")
        print(f"  거래액 비율: {float(result.ratio):.1%}")
        print(f"  판정: {result.result.value}")
        print(f"  근거: {result.reason}\n")
    
    # 요약
    summary = engine.get_summary(results)
    print(f"=== 요약 ===")
    print(f"검토 규칙: {summary['total_rules_checked']}개")
    print(f"공시 대상: {summary['disclosure_required']}개")
    print(f"검토 필요: {summary['review_required']}개")
    print(f"공시 미대상: {summary['no_disclosure']}개")
