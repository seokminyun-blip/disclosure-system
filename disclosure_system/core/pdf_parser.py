"""
감사보고서(PDF)에서 재무 지표 자동 추출 모듈
"""

import re
from typing import Dict, Optional, Tuple
from pathlib import Path

import fitz  # PyMuPDF


class AuditReportParser:
    """감사보고서 PDF 파싱 및 재무 지표 추출"""
    
    def __init__(self):
        """파서 초기화"""
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, re.Pattern]:
        """재무 지표 추출 패턴 정의"""
        return {
            'sales': [
                r'(?:매출액|일반판매수익|수익|매출)\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,]+)',
                r'(?:Net\s+(?:Sale|Revenue))\s*:\s*(?P<value>[\d,]+)'
            ],
            'total_assets': [
                r'(?:자산총액|자산의\s*합계|자산합계|유동자산\s*[+]\s*비유동자산)\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,]+)',
                r'(?:Total\s+Assets)\s*:\s*(?P<value>[\d,]+)'
            ],
            'equity': [
                r'(?:자기자본|자본금|주주\s*(?:자본|지분))\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,]+)',
                r'(?:Shareholders?\s+Equity|Total\s+Equity)\s*:\s*(?P<value>[\d,]+)'
            ],
            'current_assets': [
                r'(?:유동자산|유동\s*자산\s*합계)\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,]+)',
                r'(?:Current\s+Assets)\s*:\s*(?P<value>[\d,]+)'
            ],
            'current_liabilities': [
                r'(?:유동부채|유동\s*부채\s*합계)\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,]+)',
                r'(?:Current\s+Liabilities)\s*:\s*(?P<value>[\d,]+)'
            ],
            'accumulated_loss': [
                r'(?:누적\s*(?:결손금|손실)|결손금)\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,\-]+)',
                r'(?:Accumulated\s+(?:Loss|Deficit))\s*:\s*(?P<value>[\d,\-]+)'
            ],
            'capital': [
                r'(?:자본금|납입\s*자본금)\s*(?:\(원\))?\s*[:\s]*(?P<value>[\d,]+)',
                r'(?:Paid.?in\s+Capital)\s*:\s*(?P<value>[\d,]+)'
            ]
        }
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Optional[int]]:
        """
        PDF 파일에서 재무 지표 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            추출된 재무 지표 딕셔너리
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pdf_path}")
        
        # PDF 열기
        pdf_document = fitz.open(pdf_path)
        text = ""
        
        # 모든 페이지에서 텍스트 추출
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
        
        pdf_document.close()
        
        # 재무 지표 추출
        extracted_metrics = {}
        
        for metric_name, patterns in self.patterns.items():
            value = self._extract_metric(text, patterns)
            extracted_metrics[metric_name] = value
        
        return extracted_metrics
    
    def _extract_metric(self, text: str, patterns: list) -> Optional[int]:
        """
        주어진 패턴 리스트에서 첫 번째 매칭되는 값 추출
        
        Args:
            text: 검색 대상 텍스트
            patterns: 정규식 패턴 리스트
        
        Returns:
            추출된 숫자 값 또는 None
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    value_str = match.group('value')
                    # 쉼표 제거 및 숫자로 변환
                    value = int(value_str.replace(',', ''))
                    if value > 0:  # 음수 제외 (누적 결손금 제외)
                        return value
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def extract_tables(self, pdf_path: str) -> Dict[str, list]:
        """
        PDF에서 테이블 데이터 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            추출된 테이블 딕셔너리
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pdf_path}")
        
        pdf_document = fitz.open(pdf_path)
        tables = {}
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # 테이블 추출 (PyMuPDF 테이블 감지)
            try:
                # 단순 텍스트 기반 테이블 추출
                text = page.get_text()
                lines = text.split('\n')
                
                # 재무제표 섹션 식별
                for i, line in enumerate(lines):
                    if any(keyword in line for keyword in ['재무제표', '대차대조표', '손익계산서']):
                        # 해당 섹션의 테이블 추출
                        section_name = line.strip()
                        table_data = self._extract_table_section(lines[i:i+50])
                        tables[section_name] = table_data
            except Exception as e:
                print(f"테이블 추출 오류 (페이지 {page_num}): {e}")
        
        pdf_document.close()
        return tables
    
    def _extract_table_section(self, lines: list) -> list:
        """
        텍스트 라인에서 테이블 데이터 추출
        
        Args:
            lines: 텍스트 라인 리스트
        
        Returns:
            테이블 데이터 (행별 리스트)
        """
        table_data = []
        
        for line in lines:
            # 숫자와 텍스트를 포함한 라인 추출
            if re.search(r'\d+', line):
                row = [item.strip() for item in line.split('\t')]
                table_data.append(row)
        
        return table_data
    
    def validate_metrics(self, metrics: Dict[str, Optional[int]]) -> Tuple[bool, str]:
        """
        추출된 재무 지표 검증
        
        Args:
            metrics: 추출된 재무 지표
        
        Returns:
            (유효성, 메시지)
        """
        required_metrics = ['sales', 'total_assets', 'equity']
        
        # 필수 지표 확인
        for metric in required_metrics:
            if metrics.get(metric) is None:
                return False, f"필수 지표 누락: {metric}"
        
        # 논리적 검증
        sales = metrics['sales']
        total_assets = metrics['total_assets']
        equity = metrics['equity']
        
        if sales <= 0 or total_assets <= 0 or equity <= 0:
            return False, "재무 지표 값이 0 이하입니다"
        
        if equity > total_assets:
            return False, "자기자본이 자산총액보다 클 수 없습니다"
        
        return True, "검증 완료"
    
    def get_metrics_summary(self, metrics: Dict[str, Optional[int]]) -> str:
        """
        추출된 재무 지표 요약 생성
        
        Args:
            metrics: 추출된 재무 지표
        
        Returns:
            요약 문자열
        """
        summary = "📊 추출된 재무 지표\n"
        summary += "=" * 40 + "\n"
        
        metric_names = {
            'sales': '매출액',
            'total_assets': '자산총액',
            'equity': '자기자본',
            'current_assets': '유동자산',
            'current_liabilities': '유동부채',
            'accumulated_loss': '누적 결손금',
            'capital': '자본금'
        }
        
        for key, name in metric_names.items():
            value = metrics.get(key)
            if value is not None:
                summary += f"{name:12} : ₩{value:>15,}\n"
            else:
                summary += f"{name:12} : (미추출)\n"
        
        return summary


# 테스트 코드
if __name__ == "__main__":
    parser = AuditReportParser()
    
    # 테스트 PDF가 있다면
    pdf_path = "sample_audit_report.pdf"
    
    if Path(pdf_path).exists():
        print("PDF 파싱 테스트")
        
        # 재무 지표 추출
        metrics = parser.parse_pdf(pdf_path)
        print(parser.get_metrics_summary(metrics))
        
        # 검증
        is_valid, message = parser.validate_metrics(metrics)
        print(f"\n검증: {message}")
        
        # 테이블 추출
        tables = parser.extract_tables(pdf_path)
        print(f"\n추출된 테이블: {len(tables)}개")
    else:
        print(f"테스트 파일이 없습니다: {pdf_path}")
        print("\n사용 예제:")
        print("""
        parser = AuditReportParser()
        metrics = parser.parse_pdf('audit_report.pdf')
        
        is_valid, message = parser.validate_metrics(metrics)
        if is_valid:
            print(parser.get_metrics_summary(metrics))
        """)
