import json
import os
from typing import List, Dict, Optional
from pathlib import Path
import re

class DisclosureRuleDatabase:
    """공시규칙 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: disclosure_rules.json 파일 경로
        """
        if db_path is None:
            # 기본 경로 설정
            current_dir = Path(__file__).parent.parent
            db_path = current_dir / "data" / "disclosure_rules.json"
        
        self.db_path = db_path
        self.rules = self._load_rules()
        self._build_keyword_index()
    
    def _load_rules(self) -> List[Dict]:
        """JSON 파일에서 공시규칙 로드"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['disclosure_rules']
        except FileNotFoundError:
            print(f"규칙 파일을 찾을 수 없습니다: {self.db_path}")
            return []
    
    def _build_keyword_index(self):
        """빠른 검색을 위한 키워드 인덱스 구축"""
        self.keyword_index = {}
        for rule in self.rules:
            for keyword in rule.get('keywords', []):
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(rule['rule_id'])
    
    def search_by_keyword(self, keyword: str, market: str = None) -> List[Dict]:
        """
        키워드로 공시규칙 검색
        
        Args:
            keyword: 검색 키워드 (예: "계약", "투자")
            market: 시장 구분 ("kospi", "kosdaq", None-모두)
        
        Returns:
            매칭된 규칙 리스트
        """
        results = []
        keyword_lower = keyword.lower()
        
        for rule in self.rules:
            # 키워드 매칭
            if any(kw.lower() in keyword_lower or keyword_lower in kw.lower() 
                   for kw in rule.get('keywords', [])):
                # 시장 필터링
                if market and market not in rule.get('market', []):
                    continue
                results.append(rule)
        
        return results
    
    def search_by_category(self, category: str, market: str = None) -> List[Dict]:
        """
        카테고리로 공시규칙 검색
        
        Args:
            category: 카테고리 (예: "계약", "투자", "증자")
            market: 시장 구분
        
        Returns:
            매칭된 규칙 리스트
        """
        results = []
        for rule in self.rules:
            if rule.get('category') == category:
                if market and market not in rule.get('market', []):
                    continue
                results.append(rule)
        return results
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """규칙 ID로 특정 규칙 조회"""
        for rule in self.rules:
            if rule['rule_id'] == rule_id:
                return rule
        return None
    
    def search_by_threshold_metric(self, metric: str) -> List[Dict]:
        """
        기준 지표로 규칙 검색
        
        Args:
            metric: 기준 지표 (예: "sales_ratio", "equity_ratio", "asset_ratio")
        
        Returns:
            해당 지표를 사용하는 규칙 리스트
        """
        results = []
        for rule in self.rules:
            threshold = rule.get('threshold')
            if threshold and threshold.get('metric') == metric:
                results.append(rule)
        return results
    
    def get_all_categories(self) -> List[str]:
        """모든 공시 카테고리 조회"""
        categories = set()
        for rule in self.rules:
            categories.add(rule.get('category'))
        return sorted(list(categories))
    
    def get_all_rules(self, market: str = None) -> List[Dict]:
        """
        모든 규칙 조회
        
        Args:
            market: 시장 구분 (선택사항)
        
        Returns:
            규칙 리스트
        """
        if market is None:
            return self.rules
        
        return [r for r in self.rules if market in r.get('market', [])]
    
    def get_quantitative_rules(self, market: str = None) -> List[Dict]:
        """정량적 공시규칙 조회 (금액 기준)"""
        results = []
        for rule in self.rules:
            if rule.get('rule_type') == 'quantitative':
                if market and market not in rule.get('market', []):
                    continue
                results.append(rule)
        return results
    
    def get_qualitative_rules(self, market: str = None) -> List[Dict]:
        """정성적 공시규칙 조회 (즉시 보고)"""
        results = []
        for rule in self.rules:
            if rule.get('rule_type') == 'qualitative':
                if market and market not in rule.get('market', []):
                    continue
                results.append(rule)
        return results
    
    def search_fuzzy(self, query: str, market: str = None) -> List[Dict]:
        """
        모호한 검색 (제목, 설명, 키워드 포함)
        
        Args:
            query: 검색어
            market: 시장 구분
        
        Returns:
            매칭된 규칙 리스트
        """
        results = []
        query_lower = query.lower()
        
        for rule in self.rules:
            # 제목, 설명, 키워드에서 검색
            matched = (
                query_lower in rule.get('title', '').lower() or
                query_lower in rule.get('description', '').lower() or
                any(query_lower in kw.lower() for kw in rule.get('keywords', []))
            )
            
            if matched:
                if market and market not in rule.get('market', []):
                    continue
                results.append(rule)
        
        return results
    
    def get_rules_by_type(self, rule_type: str, market: str = None) -> List[Dict]:
        """규칙 유형으로 조회"""
        results = []
        for rule in self.rules:
            if rule.get('rule_type') == rule_type:
                if market and market not in rule.get('market', []):
                    continue
                results.append(rule)
        return results
    
    def print_rule_summary(self):
        """규칙 요약 출력"""
        print(f"총 규칙 수: {len(self.rules)}")
        print(f"카테고리: {', '.join(self.get_all_categories())}")
        print(f"정량적 규칙: {len(self.get_quantitative_rules())}")
        print(f"정성적 규칙: {len(self.get_qualitative_rules())}")


# 테스트 코드
if __name__ == "__main__":
    db = DisclosureRuleDatabase()
    
    print("=== 공시규칙 데이터베이스 테스트 ===\n")
    
    # 전체 규칙 수
    db.print_rule_summary()
    
    print("\n=== 키워드 검색 테스트 ===")
    results = db.search_by_keyword("계약")
    print(f"'계약' 검색 결과: {len(results)}건")
    for r in results:
        print(f"  - {r['title']}")
    
    print("\n=== 카테고리 검색 테스트 ===")
    results = db.search_by_category("투자")
    print(f"'투자' 카테고리 규칙: {len(results)}건")
    for r in results:
        print(f"  - {r['title']} (기준: {r['threshold']['metric']})")
    
    print("\n=== 모호한 검색 테스트 ===")
    results = db.search_fuzzy("자산")
    print(f"'자산' 모호 검색 결과: {len(results)}건")
    for r in results:
        print(f"  - {r['title']}")
    
    print("\n=== 지표별 규칙 검색 ===")
    results = db.search_by_threshold_metric("asset_ratio")
    print(f"'asset_ratio' 기준 규칙: {len(results)}건")
    for r in results:
        print(f"  - {r['title']}: {r['threshold']['value']}%")
