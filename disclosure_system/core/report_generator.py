"""
공시 판정 결과를 Excel/PDF로 내보내는 모듈
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from pathlib import Path
from io import BytesIO

import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from .calculation_engine import CalculationResult, DisclosureResult


class ReportGenerator:
    """공시 판정 결과 보고서 생성"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def to_excel(
        self,
        calculation_results: List[CalculationResult],
        financial_metrics: Dict,
        transaction_info: Dict,
        filename: Optional[str] = None
    ) -> bytes:
        """
        Excel 파일로 내보내기
        
        Args:
            calculation_results: 계산 결과 리스트
            financial_metrics: 재무 지표
            transaction_info: 거래 정보
            filename: 파일명 (None이면 bytes 반환)
        
        Returns:
            Excel 파일 bytes 또는 파일명
        """
        # 계산 결과 DataFrame 생성
        results_data = []
        for result in calculation_results:
            results_data.append({
                '규칙ID': result.rule['rule_id'],
                '규칙명': result.rule['title'],
                '카테고리': result.rule['category'],
                '규칙유형': result.rule['rule_type'],
                '기준지표': result.metric_type,
                '기준값': f"{result.rule['threshold']['value']}%",
                '기준금액': format(int(result.threshold_amount), ','),
                '거래액': format(int(result.transaction_amount), ','),
                '거래액비율': f"{float(result.ratio):.1%}",
                '판정': result.result.value,
                '근거': result.reason
            })
        
        results_df = pd.DataFrame(results_data)
        
        # 요약 데이터
        disclosure_count = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.DISCLOSURE_REQUIRED
        )
        review_count = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.REVIEW_REQUIRED
        )
        no_disclosure = len(calculation_results) - disclosure_count - review_count
        
        summary_data = {
            '항목': ['검토 규칙수', '공시 대상', '검토 필요', '공시 미대상'],
            '결과': [len(calculation_results), disclosure_count, review_count, no_disclosure]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # 재무 지표 데이터
        metrics_data = {
            '항목': list(financial_metrics.keys()),
            '값 (원)': [f"{int(v):,}" for v in financial_metrics.values()]
        }
        metrics_df = pd.DataFrame(metrics_data)
        
        # Excel 파일 생성
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: 계산 결과
            results_df.to_excel(writer, sheet_name='계산결과', index=False)
            
            # Sheet 2: 요약
            summary_df.to_excel(writer, sheet_name='요약', index=False)
            
            # Sheet 3: 재무 지표
            metrics_df.to_excel(writer, sheet_name='재무지표', index=False)
            
            # Sheet 4: 거래 정보
            tx_df = pd.DataFrame([transaction_info])
            tx_df.to_excel(writer, sheet_name='거래정보', index=False)
        
        output.seek(0)
        
        # 파일로 저장 또는 bytes 반환
        if filename:
            with open(filename, 'wb') as f:
                f.write(output.getvalue())
            return filename
        
        return output.getvalue()
    
    def to_pdf(
        self,
        calculation_results: List[CalculationResult],
        financial_metrics: Dict,
        transaction_info: Dict,
        filename: Optional[str] = None
    ) -> bytes:
        """
        PDF 파일로 내보내기
        
        Args:
            calculation_results: 계산 결과 리스트
            financial_metrics: 재무 지표
            transaction_info: 거래 정보
            filename: 파일명 (None이면 bytes 반환)
        
        Returns:
            PDF 파일 bytes 또는 파일명
        """
        output = BytesIO()
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # 스타일 정의
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=1  # 중앙 정렬
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            spaceBefore=8
        )
        
        # 컨텐츠 생성
        story = []
        
        # 제목
        story.append(Paragraph("공시 판정 결과 보고서", title_style))
        story.append(Paragraph(f"작성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", 
                              styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # 요약
        story.append(Paragraph("📊 판정 요약", heading_style))
        
        disclosure_count = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.DISCLOSURE_REQUIRED
        )
        review_count = sum(
            1 for r in calculation_results
            if r.result == DisclosureResult.REVIEW_REQUIRED
        )
        no_disclosure = len(calculation_results) - disclosure_count - review_count
        
        summary_table_data = [
            ['항목', '결과'],
            ['검토 규칙수', str(len(calculation_results))],
            ['🚨 공시 대상', str(disclosure_count)],
            ['⚠️ 검토 필요', str(review_count)],
            ['✅ 공시 미대상', str(no_disclosure)]
        ]
        
        summary_table = Table(summary_table_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))
        
        # 재무 지표
        story.append(Paragraph("💰 재무 지표", heading_style))
        
        metrics_table_data = [['항목', '값']]
        for key, value in financial_metrics.items():
            metrics_table_data.append([key, f"₩{int(value):,}"])
        
        metrics_table = Table(metrics_table_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue)
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.2*inch))
        
        # 거래 정보
        story.append(Paragraph("📋 거래 정보", heading_style))
        
        tx_table_data = [['항목', '값']]
        for key, value in transaction_info.items():
            if isinstance(value, (int, float)):
                tx_table_data.append([key, f"₩{int(value):,}"])
            else:
                tx_table_data.append([key, str(value)])
        
        tx_table = Table(tx_table_data, colWidths=[3*inch, 2*inch])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen)
        ]))
        story.append(tx_table)
        story.append(PageBreak())
        
        # 상세 결과
        story.append(Paragraph("🔍 상세 계산 결과", heading_style))
        
        for idx, result in enumerate(calculation_results, 1):
            color_map = {
                DisclosureResult.DISCLOSURE_REQUIRED: colors.HexColor('#f44'),
                DisclosureResult.REVIEW_REQUIRED: colors.HexColor('#fdcb6e'),
                DisclosureResult.NO_DISCLOSURE: colors.HexColor('#00b894')
            }
            
            result_table_data = [
                ['항목', '내용'],
                ['규칙', result.rule['title']],
                ['카테고리', result.rule['category']],
                ['기준 지표', result.metric_type],
                ['기준 금액', f"₩{int(result.threshold_amount):,}"],
                ['거래액', f"₩{int(result.transaction_amount):,}"],
                ['거래액 비율', f"{float(result.ratio):.1%}"],
                ['판정', result.result.value],
                ['근거', result.reason]
            ]
            
            result_table = Table(result_table_data, colWidths=[2*inch, 3*inch])
            result_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), color_map[result.result]),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(result_table)
            if idx < len(calculation_results):
                story.append(Spacer(1, 0.15*inch))
        
        # PDF 생성
        doc.build(story)
        output.seek(0)
        
        # 파일로 저장 또는 bytes 반환
        if filename:
            with open(filename, 'wb') as f:
                f.write(output.getvalue())
            return filename
        
        return output.getvalue()
    
    def to_json(
        self,
        calculation_results: List[CalculationResult],
        financial_metrics: Dict,
        transaction_info: Dict,
        filename: Optional[str] = None
    ) -> str:
        """
        JSON 형식으로 내보내기
        
        Args:
            calculation_results: 계산 결과 리스트
            financial_metrics: 재무 지표
            transaction_info: 거래 정보
            filename: 파일명 (None이면 JSON 문자열 반환)
        
        Returns:
            JSON 문자열 또는 파일명
        """
        report_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            },
            'summary': {
                'total_rules_checked': len(calculation_results),
                'disclosure_required': sum(
                    1 for r in calculation_results
                    if r.result == DisclosureResult.DISCLOSURE_REQUIRED
                ),
                'review_required': sum(
                    1 for r in calculation_results
                    if r.result == DisclosureResult.REVIEW_REQUIRED
                ),
                'no_disclosure': sum(
                    1 for r in calculation_results
                    if r.result == DisclosureResult.NO_DISCLOSURE
                )
            },
            'financial_metrics': {
                k: float(v) for k, v in financial_metrics.items()
            },
            'transaction_info': {
                k: float(v) if isinstance(v, (int, float, Decimal)) else str(v)
                for k, v in transaction_info.items()
            },
            'calculation_results': [r.to_dict() for r in calculation_results]
        }
        
        json_str = json.dumps(report_data, ensure_ascii=False, indent=2)
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return filename
        
        return json_str


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
    
    # 보고서 생성
    generator = ReportGenerator()
    
    financial_metrics_dict = metrics.to_dict()
    transaction_info = {
        '거래액': 1500000000,
        '시장': 'KOSPI',
        '거래유형': '계약'
    }
    
    # Excel 생성
    excel_bytes = generator.to_excel(results, financial_metrics_dict, transaction_info)
    print(f"✅ Excel 생성 완료: {len(excel_bytes)} bytes")
    
    # PDF 생성
    pdf_bytes = generator.to_pdf(results, financial_metrics_dict, transaction_info)
    print(f"✅ PDF 생성 완료: {len(pdf_bytes)} bytes")
    
    # JSON 생성
    json_str = generator.to_json(results, financial_metrics_dict, transaction_info)
    print(f"✅ JSON 생성 완료: {len(json_str)} bytes")
