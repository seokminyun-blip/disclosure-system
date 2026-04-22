"""
공시 판정 조회 이력 저장 및 관리 모듈
"""

import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from pathlib import Path

from .calculation_engine import CalculationResult, DisclosureResult


class QueryHistory:
    """공시 판정 조회 이력 관리"""
    
    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: SQLite 데이터베이스 경로
        """
        if db_path is None:
            current_dir = Path(__file__).parent.parent
            db_path = current_dir / "data" / "disclosure_history.db"
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 조회 이력 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_date TEXT NOT NULL,
                transaction_amount REAL NOT NULL,
                market TEXT NOT NULL,
                disclosure_status TEXT NOT NULL,
                total_rules INTEGER NOT NULL,
                disclosure_required INTEGER NOT NULL,
                review_required INTEGER NOT NULL,
                no_disclosure INTEGER NOT NULL,
                json_data TEXT NOT NULL
            )
        ''')
        
        # 재무 지표 저장 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                FOREIGN KEY(query_id) REFERENCES query_history(id)
            )
        ''')
        
        # 규칙별 결과 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                rule_id TEXT NOT NULL,
                rule_title TEXT NOT NULL,
                category TEXT NOT NULL,
                result TEXT NOT NULL,
                threshold_amount REAL NOT NULL,
                transaction_amount REAL NOT NULL,
                ratio REAL NOT NULL,
                reason TEXT NOT NULL,
                FOREIGN KEY(query_id) REFERENCES query_history(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_query(
        self,
        calculation_results: List[CalculationResult],
        financial_metrics: Dict,
        transaction_amount: float,
        market: str,
        notes: str = None
    ) -> int:
        """
        조회 이력 저장
        
        Args:
            calculation_results: 계산 결과 리스트
            financial_metrics: 재무 지표
            transaction_amount: 거래액
            market: 시장 (kospi/kosdaq)
            notes: 메모
        
        Returns:
            저장된 이력 ID
        """
        # 요약 계산
        disclosure_required = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.DISCLOSURE_REQUIRED
        )
        review_required = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.REVIEW_REQUIRED
        )
        no_disclosure = len(calculation_results) - disclosure_required - review_required
        
        # 최종 상태 결정
        if disclosure_required > 0:
            disclosure_status = "공시대상"
        elif review_required > 0:
            disclosure_status = "검토필요"
        else:
            disclosure_status = "공시미대상"
        
        # JSON 데이터 생성
        json_data = json.dumps({
            'financial_metrics': financial_metrics,
            'calculation_results': [r.to_dict() for r in calculation_results],
            'notes': notes
        }, ensure_ascii=False, default=str)
        
        # 데이터 저장
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 메인 이력 저장
        cursor.execute('''
            INSERT INTO query_history
            (query_date, transaction_amount, market, disclosure_status,
             total_rules, disclosure_required, review_required, no_disclosure, json_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            transaction_amount,
            market,
            disclosure_status,
            len(calculation_results),
            disclosure_required,
            review_required,
            no_disclosure,
            json_data
        ))
        
        query_id = cursor.lastrowid
        
        # 재무 지표 저장
        for metric_name, metric_value in financial_metrics.items():
            cursor.execute('''
                INSERT INTO financial_metrics
                (query_id, metric_name, metric_value)
                VALUES (?, ?, ?)
            ''', (query_id, metric_name, float(metric_value)))
        
        # 규칙별 결과 저장
        for result in calculation_results:
            cursor.execute('''
                INSERT INTO rule_results
                (query_id, rule_id, rule_title, category, result,
                 threshold_amount, transaction_amount, ratio, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query_id,
                result.rule['rule_id'],
                result.rule['title'],
                result.rule['category'],
                result.result.value,
                float(result.threshold_amount),
                float(result.transaction_amount),
                float(result.ratio),
                result.reason
            ))
        
        conn.commit()
        conn.close()
        
        return query_id
    
    def get_history(
        self,
        limit: int = 100,
        market: str = None,
        status: str = None
    ) -> List[Dict]:
        """
        조회 이력 조회
        
        Args:
            limit: 조회 개수
            market: 시장 필터 (kospi/kosdaq)
            status: 상태 필터 (공시대상/검토필요/공시미대상)
        
        Returns:
            이력 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM query_history WHERE 1=1"
        params = []
        
        if market:
            query += " AND market = ?"
            params.append(market)
        
        if status:
            query += " AND disclosure_status = ?"
            params.append(status)
        
        query += " ORDER BY query_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_query_detail(self, query_id: int) -> Dict:
        """
        특정 조회 이력 상세 조회
        
        Args:
            query_id: 이력 ID
        
        Returns:
            이력 상세 정보
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 메인 이력 조회
        cursor.execute("SELECT * FROM query_history WHERE id = ?", (query_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        history = dict(zip(columns, row))
        
        # JSON 데이터 파싱
        history['data'] = json.loads(history['json_data'])
        del history['json_data']
        
        # 재무 지표 추가
        cursor.execute(
            "SELECT metric_name, metric_value FROM financial_metrics WHERE query_id = ?",
            (query_id,)
        )
        history['financial_metrics'] = dict(cursor.fetchall())
        
        # 규칙 결과 추가
        cursor.execute(
            "SELECT * FROM rule_results WHERE query_id = ? ORDER BY id",
            (query_id,)
        )
        rule_columns = [description[0] for description in cursor.description]
        history['rule_results'] = [
            dict(zip(rule_columns, row)) for row in cursor.fetchall()
        ]
        
        conn.close()
        return history
    
    def get_statistics(self) -> Dict:
        """
        조회 통계
        
        Returns:
            통계 정보
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 전체 조회 수
        cursor.execute("SELECT COUNT(*) FROM query_history")
        total_queries = cursor.fetchone()[0]
        
        # 상태별 조회 수
        cursor.execute(
            "SELECT disclosure_status, COUNT(*) FROM query_history GROUP BY disclosure_status"
        )
        status_counts = dict(cursor.fetchall())
        
        # 시장별 조회 수
        cursor.execute(
            "SELECT market, COUNT(*) FROM query_history GROUP BY market"
        )
        market_counts = dict(cursor.fetchall())
        
        # 평균 거래액
        cursor.execute("SELECT AVG(transaction_amount) FROM query_history")
        avg_transaction = cursor.fetchone()[0]
        
        # 최근 7일 조회 수
        cursor.execute('''
            SELECT COUNT(*) FROM query_history
            WHERE query_date > datetime('now', '-7 days')
        ''')
        recent_queries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_queries': total_queries,
            'status_distribution': status_counts,
            'market_distribution': market_counts,
            'avg_transaction_amount': avg_transaction,
            'recent_7days_queries': recent_queries
        }
    
    def delete_query(self, query_id: int) -> bool:
        """
        조회 이력 삭제
        
        Args:
            query_id: 이력 ID
        
        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 관련 데이터 삭제
        cursor.execute("DELETE FROM rule_results WHERE query_id = ?", (query_id,))
        cursor.execute("DELETE FROM financial_metrics WHERE query_id = ?", (query_id,))
        cursor.execute("DELETE FROM query_history WHERE id = ?", (query_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def export_to_csv(
        self,
        output_path: str,
        market: str = None,
        status: str = None
    ):
        """
        조회 이력을 CSV로 내보내기
        
        Args:
            output_path: 출력 파일 경로
            market: 시장 필터
            status: 상태 필터
        """
        import csv
        
        history = self.get_history(limit=10000, market=market, status=status)
        
        if not history:
            return False
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
        
        return True


# 테스트 코드
if __name__ == "__main__":
    from core import DisclosureRuleDatabase, DisclosureCalculationEngine, FinancialMetrics
    
    # 테스트 데이터
    db = DisclosureRuleDatabase()
    engine = DisclosureCalculationEngine(db)
    
    metrics = FinancialMetrics(
        sales=Decimal("10000000000"),
        total_assets=Decimal("50000000000"),
        equity=Decimal("20000000000")
    )
    
    results = engine.calculate(metrics, Decimal("1500000000"))
    
    # 이력 저장
    history = QueryHistory()
    
    query_id = history.save_query(
        results,
        metrics.to_dict(),
        1500000000,
        "kospi",
        "테스트 쿼리"
    )
    
    print(f"✅ 이력 저장 완료: ID={query_id}")
    
    # 이력 조회
    recent_history = history.get_history(limit=10)
    print(f"✅ 최근 이력: {len(recent_history)}개")
    
    # 상세 조회
    detail = history.get_query_detail(query_id)
    print(f"✅ 상세 이력: {detail['disclosure_status']}")
    
    # 통계
    stats = history.get_statistics()
    print(f"✅ 통계: 총 {stats['total_queries']}개 쿼리")
