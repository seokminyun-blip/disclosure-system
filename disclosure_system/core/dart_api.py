"""
DART Open API 클라이언트 — 공시 목록 조회
"""
import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List

DART_BASE = "https://opendart.fss.or.kr/api"

# 공시 카테고리 → DART pblntf_ty 매핑
# A=정기공시 B=주요사항보고 C=발행공시 F=외부감사관련 I=거래소공시 J=공정공시
_CATEGORY_PBLNTF: dict = {
    "계약":       ["B"],
    "투자":       ["B", "C"],
    "자산처분":   ["B"],
    "증자":       ["B", "C"],
    "감자":       ["B"],
    "사채발행":   ["B", "C"],
    "M&A":        ["B"],
    "자기주식":   ["B", "I"],
    "배당":       ["I"],
    "인사":       ["I"],
    "소송":       ["B"],
    "기업연속성": ["B"],
    "영업":       ["B"],
    "관련거래":   ["J", "B"],
    "감사":       ["F"],
    "정기공시":   ["A"],
}


class DartApiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DART_API_KEY", "")

    def search_disclosures(
        self,
        corp_name: str,
        categories: List[str],
        months: int = 6,
        page_count: int = 20,
    ) -> list:
        """회사명 + 카테고리로 DART 공시 목록 조회.
        corp_code 없이 corp_name만 사용 시 DART API 제한(3개월)이 있으므로
        요청 기간을 3개월 단위로 분할하여 조회합니다.
        """
        if not self.api_key:
            raise ValueError("DART_API_KEY 미설정 — .env 또는 Streamlit Secrets에 추가하세요")

        # 3개월 단위 청크 생성 (DART API corp_name 검색 시 3개월 제한)
        chunks: list = []
        end_dt = datetime.today()
        remaining = months
        while remaining > 0:
            chunk = min(3, remaining)
            start_dt = end_dt - timedelta(days=chunk * 30)
            chunks.append((start_dt, end_dt))
            end_dt = start_dt
            remaining -= chunk

        # 중복 없이 pblntf_ty 수집
        seen_types: list = []
        for cat in categories:
            for t in _CATEGORY_PBLNTF.get(cat, ["B"]):
                if t not in seen_types:
                    seen_types.append(t)

        all_items: list = []
        for chunk_start, chunk_end in chunks:
            for ptype in seen_types:
                params: dict = {
                    "crtfc_key": self.api_key,
                    "bgn_de": chunk_start.strftime("%Y%m%d"),
                    "end_de": chunk_end.strftime("%Y%m%d"),
                    "pblntf_ty": ptype,
                    "page_count": str(page_count),
                    "sort": "date",
                    "sort_mth": "desc",
                }
                if corp_name:
                    params["corp_name"] = corp_name
                try:
                    resp = requests.get(f"{DART_BASE}/list.json", params=params, timeout=10)
                    data = resp.json()
                    if data.get("status") == "000" and isinstance(data.get("list"), list):
                        all_items.extend(data["list"])
                except Exception:
                    continue

        # 날짜 내림차순 + 중복 제거
        all_items.sort(key=lambda x: x.get("rcept_dt", ""), reverse=True)
        seen_rcept: set = set()
        unique: list = []
        for item in all_items:
            rn = item.get("rcept_no", "")
            if rn not in seen_rcept:
                seen_rcept.add(rn)
                unique.append(item)
        return unique[:50]

    @staticmethod
    def disclosure_url(rcept_no: str) -> str:
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
