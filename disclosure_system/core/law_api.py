"""
국가법령정보 공동활용 API 클라이언트
OC(기관코드) 기반 무료 API - API 키 불필요
"""

import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# 국가법령 DB 미수록 기관(KRX·KASB 등) → 직접 링크로 대체
KRX_DIRECT_LINKS = {
    "유가증권시장 공시규정": "https://law.krx.co.kr/las/LasMain.do#",
    "코스닥시장 공시규정":   "https://law.krx.co.kr/las/LasMain.do#",
    "코넥스시장 공시규정":   "https://law.krx.co.kr/las/LasMain.do#",
    "K-IFRS":              "https://www.kasb.or.kr/fe/standards/NR_index.do",
}

# 국가법령 DB에 있는 법령 매핑 (target: law|admrul, query: 검색어)
GOV_LAW_MAP = {
    "자본시장법":                      {"target": "law",    "query": "자본시장과 금융투자업에 관한 법률"},
    "자본시장과 금융투자업에 관한 법률": {"target": "law",    "query": "자본시장과 금융투자업에 관한 법률"},
    "K-IFRS":                         {"target": "admrul", "query": "국제회계기준"},
    "증권의 발행 및 공시":              {"target": "admrul", "query": "증권의 발행 및 공시 등에 관한 규정"},
}


class LawApiClient:
    """국가법령정보 공동활용 API 클라이언트"""

    BASE_URL = "https://www.law.go.kr/DRF"

    def __init__(self, oc: str = None):
        self.oc = oc or os.getenv("LAW_API_OC", "ysm701")
        self._cache: Dict[str, object] = {}

    def search_law(self, query: str, target: str = "law", display: int = 3) -> List[Dict]:
        """
        법령/행정규칙 목록 검색

        Args:
            query: 검색어
            target: "law"(법령) | "admrul"(행정규칙/고시)
            display: 반환 건수
        """
        cache_key = f"search:{target}:{query}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            resp = requests.get(
                f"{self.BASE_URL}/lawSearch.do",
                params={"OC": self.oc, "target": target, "type": "JSON",
                        "query": query, "display": display},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            # law / admrul 응답 구조가 다름
            if target == "law":
                items = data.get("LawSearch", {}).get("law", [])
            else:
                items = data.get("AdmRulSearch", {}).get("admrul", [])

            if isinstance(items, dict):
                items = [items]

            self._cache[cache_key] = items
            return items

        except Exception:
            return []

    def get_law_link(self, item: Dict, target: str) -> str:
        """검색된 항목의 법령 원문 링크 생성"""
        if target == "law":
            name = item.get("법령명한글", "")
            return f"https://www.law.go.kr/법령/{requests.utils.quote(name)}" if name else ""
        else:
            # admrul: 상세링크가 이미 응답에 포함됨
            detail = item.get("행정규칙상세링크", "")
            if detail:
                # 상대경로 → 절대경로
                return f"https://www.law.go.kr{detail}" if detail.startswith("/") else detail
            name = item.get("행정규칙명", "")
            return f"https://www.law.go.kr/행정규칙/{requests.utils.quote(name)}" if name else ""

    def get_article_text(self, reference: str) -> Optional[Dict]:
        """
        공시규정 reference 문자열로 법령 정보 조회

        Args:
            reference: "유가증권시장 공시규정 §3.2" 또는 "K-IFRS 1113호" 형태

        Returns:
            {"law_name": ..., "link": ..., "시행일": ..., "source": "krx"|"gov"}
        """
        # 1. KRX 자율규정 직접 링크
        for key, link in KRX_DIRECT_LINKS.items():
            if key in reference:
                source_label = "kasb" if "IFRS" in key else "krx"
                note = {
                    "krx":  "한국거래소(KRX) 자율규정 — 국가법령 DB 미수록",
                    "kasb": "한국회계기준원(KASB) 기준서 — 국가법령 DB 미수록",
                }[source_label]
                return {
                    "law_name": key,
                    "link": link,
                    "시행일": None,
                    "효력": "민간 자율규정",
                    "source": source_label,
                    "note": note,
                }

        # 2. 국가법령 DB 매핑
        matched = None
        for key, cfg in GOV_LAW_MAP.items():
            if key in reference:
                matched = cfg
                break

        # 매핑 없으면 reference 앞부분으로 검색 시도
        if not matched:
            query = reference.split("§")[0].split("제")[0].strip()
            matched = {"target": "law", "query": query}

        items = self.search_law(matched["query"], target=matched["target"])
        if not items:
            return None

        item = items[0]
        if matched["target"] == "law":
            name = item.get("법령명한글", "")
            enacted = item.get("시행일자", "")
            dept = item.get("소관부처명", "")
        else:
            name = item.get("행정규칙명", "")
            enacted = item.get("시행일자", "")
            dept = item.get("소관부처명", "")

        link = self.get_law_link(item, matched["target"])

        return {
            "law_name": name,
            "link": link,
            "시행일": enacted,
            "효력": dept,
            "source": "gov",
        }
