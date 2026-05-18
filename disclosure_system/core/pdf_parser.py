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
    
    # DART 재무제표 키워드 매핑 (우선순위 순)
    DART_KEYWORDS = {
        'sales':               ['매출액', '수익(매출액)', '영업수익', '용역수익'],
        'total_assets':        ['자산총계', '자산 총계', '자산합계', '자산총액', '자산의 합계'],
        'equity':              ['자본총계', '자본 총계', '자기자본총계', '자본합계', '자기자본'],
        'current_assets':      ['유동자산'],
        'current_liabilities': ['유동부채'],
        'accumulated_loss':    ['미처리결손금', '이월결손금', '결손금', '누적결손금'],
        'capital':             ['자본금'],
    }

    def _init_patterns(self) -> Dict[str, re.Pattern]:
        """레거시 inline 패턴 (fallback용)"""
        # 4자리 이상 숫자만 매칭 (주석 번호 오염 방지)
        return {
            'sales': [r'매출액\s*[:\s]+(?P<value>[\d]{4}[\d,]*)'],
            'total_assets': [r'자산\s*총계\s*[:\s]+(?P<value>[\d]{4}[\d,]*)'],
            'equity': [r'자본\s*총계\s*[:\s]+(?P<value>[\d\-\(][\d,\-\(\)]{5,})'],
            'current_assets': [r'유동자산\s*[:\s]+(?P<value>[\d]{4}[\d,]*)'],
            'current_liabilities': [r'유동부채\s*[:\s]+(?P<value>[\d]{4}[\d,]*)'],
            'accumulated_loss': [r'결손금\s*[:\s]+(?P<value>[\d,]+)'],
            'capital': [r'자본금\s*[:\s]+(?P<value>[\d]{4}[\d,]*)'],
        }
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Optional[int]]:
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pdf_path}")

        pdf_document = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()

        result = self._extract_dart_linebased(text)

        # 핵심 지표가 빠진 항목만 inline 패턴으로 보완
        for metric_name, patterns in self.patterns.items():
            if result.get(metric_name) is None:
                result[metric_name] = self._extract_metric_inline(text, patterns)

        return result

    def _detect_unit(self, text: str) -> int:
        """재무제표 단위 감지 → 원 단위 변환 배수 반환.
        주재무제표(재무상태표·손익계산서) 헤더 직후 단위 선언만 읽음.
        주석 테이블의 천원 단위에 오염되지 않도록 첫 발견값 우선."""
        lines = text.split('\n')
        # 주재무제표 섹션 헤더 키워드
        stmt_headers = ['재무상태표', '대차대조표', '손익계산서', '포괄손익계산서']
        in_stmt = False
        for line in lines:
            if any(kw in line for kw in stmt_headers):
                in_stmt = True
            if in_stmt and '단위' in line:
                if '백만' in line:
                    return 1_000_000
                if '천원' in line or '천 원' in line:
                    return 1_000
                if '원' in line:
                    return 1
        # fallback: 전체에서 첫 번째 단위 선언
        for line in lines:
            if '단위' in line:
                if '백만' in line:
                    return 1_000_000
                if '천원' in line or '천 원' in line:
                    return 1_000
                if '원' in line:
                    return 1
        return 1

    def _parse_number(self, s: str, multiplier: int = 1) -> Optional[int]:
        """숫자 문자열 파싱. 괄호 표기 음수 처리."""
        s = s.strip()
        negative = False
        if s.startswith('(') and s.endswith(')'):
            negative = True
            s = s[1:-1]
        elif s.startswith('-'):
            negative = True
            s = s[1:]
        s = re.sub(r'[^\d]', '', s)
        if not s:
            return None
        val = int(s) * multiplier
        return -val if negative else val

    def _find_section_range(self, lines: list, section_keywords: list) -> tuple:
        """재무제표 섹션 시작/끝 인덱스 반환.
        목차(TOC) 오염 방지: 헤더 이후 10줄 내에 숫자 데이터가 있어야 실제 섹션으로 인정."""
        for i, line in enumerate(lines):
            if not any(kw in line for kw in section_keywords):
                continue
            # 이후 10줄 내에 4자리 이상 숫자가 있으면 실제 재무제표 섹션
            for j in range(i + 1, min(i + 15, len(lines))):
                if len(re.sub(r'[^\d]', '', lines[j])) >= 4:
                    end = min(i + 300, len(lines))
                    return i, end
        return None, None

    def _extract_dart_linebased(self, text: str) -> Dict[str, Optional[int]]:
        """DART PDF 줄 기반 추출 — 레이블 다음 줄의 숫자를 가져옴"""
        multiplier = self._detect_unit(text)
        lines = [l.strip() for l in text.split('\n')]
        result: Dict[str, Optional[int]] = {}

        # 재무상태표 섹션 범위 (자산총계/자본총계는 이 범위 내에서만 탐색)
        bs_start, bs_end = self._find_section_range(
            lines, ['재무상태표', '대차대조표', '재무상태', 'STATEMENTS OF FINANCIAL POSITION'])

        # 손익계산서 섹션 범위 (매출액은 이 범위 내에서만 탐색)
        is_start, is_end = self._find_section_range(
            lines, ['손익계산서', '포괄손익계산서', '영업손익', 'STATEMENTS OF COMPREHENSIVE INCOME',
                    'STATEMENTS OF OPERATIONS'])

        # 메트릭별 탐색 범위 제한 (섹션 미발견 시 전체 탐색)
        n = len(lines)
        def _range(start, end):
            return (start, end) if start is not None else (0, n)

        SECTION_LIMITS = {
            'sales':               (0, n),  # 전체 탐색 — 섹션 범위 제한 없음
            'total_assets':        _range(bs_start, bs_end),
            'equity':              _range(bs_start, bs_end),
            'current_assets':      _range(bs_start, bs_end),
            'current_liabilities': _range(bs_start, bs_end),
            'accumulated_loss':    (0, n),
            'capital':             _range(bs_start, bs_end),
        }

        for metric, keywords in self.DART_KEYWORDS.items():
            if metric in result:
                continue
            search_start, search_end = SECTION_LIMITS.get(metric, (0, len(lines)))
            for i, line in enumerate(lines[search_start:search_end], start=search_start):
                matched_kw = None
                for kw in keywords:
                    # 정확히 일치, 앞에 항목 번호(Ⅰ. / 1. / (1) 등) 붙은 경우, 뒤에 공백/괄호가 오는 경우 처리
                    if (line == kw
                            or line.startswith(kw)
                            or line.endswith(kw)
                            or re.search(r'[\.\s）\)]\s*' + re.escape(kw) + r'\s*$', line)
                            or re.search(r'^[^\w가-힣]*' + re.escape(kw) + r'\s*$', line)):
                        matched_kw = kw
                        break
                if matched_kw is None:
                    continue

                # 같은 줄 뒷부분에서 숫자 시도
                kw = matched_kw
                suffix = line[line.index(kw) + len(kw):]
                rest = re.sub(r'[^\d,\-\(\)]', '', suffix)
                if len(re.sub(r'[^\d]', '', rest)) >= 3:
                    val = self._parse_number(rest, multiplier)
                    if val is not None:
                        result[metric] = val

                if metric in result:
                    break

                # 다음 1~4줄에서 숫자 탐색 (주석 번호처럼 짧은 숫자 줄은 건너뜀)
                for j in range(i + 1, min(i + 6, len(lines))):
                    candidate = re.sub(r'[^\d,\-\(\)]', '', lines[j])
                    digits_only = re.sub(r'[^\d]', '', candidate)
                    if len(digits_only) >= 4:
                        val = self._parse_number(candidate, multiplier)
                        if val is not None:
                            result[metric] = val
                            break
                if metric in result:
                    break

        return result

    def _extract_metric_inline(self, text: str, patterns: list) -> Optional[int]:
        """inline 정규식 fallback"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    val = int(match.group('value').replace(',', ''))
                    if val != 0:
                        return val
                except (ValueError, AttributeError):
                    continue
        return None

    def _extract_metric(self, text: str, patterns: list) -> Optional[int]:
        return self._extract_metric_inline(text, patterns)
    
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
