"""
공시 규정 및 사례 분석을 위한 AI 어드바이저 모듈 (Google Gemini 연동)
"""

import os
import json
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class DisclosureAIAdvisor:
    """공시 규정 해석 및 사용자 질의응답 지원 (Google Gemini 연동)"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = None
        if self.api_key and self.api_key != "your_google_api_key_here":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"Gemini 클라이언트 초기화 실패: {e}")

        self.rules_db = self._load_rules_db()

    def _load_rules_db(self) -> List[Dict]:
        db_path = Path(__file__).parent.parent / "data" / "disclosure_rules.json"
        if db_path.exists():
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("disclosure_rules", [])
        return []

    def _create_context(self) -> str:
        if not self.rules_db:
            return "현재 로드된 공시 규정 데이터가 없습니다."

        context = "다음은 회사의 내부 공시 가이드라인 규칙들입니다:\n\n"
        for rule in self.rules_db:
            context += f"### {rule['title']}\n"
            context += f"- 설명: {rule['description']}\n"
            if rule.get('threshold'):
                context += f"- 기준: {rule['threshold']['description']} (임계치: {rule['threshold']['value']}%)\n"
            context += f"- 공시 기한: {rule['disclosure_period']}\n"
            context += f"- 참고사항: {rule['reference']}\n\n"
        return context

    def ask(self, query: str, history: List[Dict] = None) -> str:
        system_prompt = f"""당신은 상장법인의 공시 규정 전문가입니다.
회사의 내부 공시 가이드라인 데이터를 바탕으로 사용자의 질문에 답변하십시오.

{self._create_context()}

답변 지침:
1. 질문이 특정 규칙과 관련 있으면 해당 규칙명과 구체적인 기준(매출액 대비 % 등)을 명시하십시오.
2. 정성적 판단이 필요한 경우에는 어떤 점을 중점적으로 검토해야 하는지 가이드를 주십시오.
3. 공시 기간(기한)에 대해서도 언급하여 누락되지 않도록 강조하십시오.
4. 답변 끝에는 항상 "※ 실제 공시 여부는 최종적으로 공시책임자 및 거래소 업무 담당자와 확인이 필요합니다."라는 문구를 포함하십시오.
5. 한국어로 전문적이고 친절하게 답변하십시오."""

        if not self.model:
            return self._fallback_response(query)

        try:
            # 대화 이력 구성 (Gemini 형식)
            chat_history = []
            if history:
                for h in history:
                    role = "user" if h["role"] == "user" else "model"
                    chat_history.append({"role": role, "parts": [h["content"]]})

            chat = self.model.start_chat(history=chat_history)
            full_prompt = f"{system_prompt}\n\n사용자 질문: {query}"
            response = chat.send_message(full_prompt)
            return response.text

        except Exception as e:
            return f"AI 답변 생성 중 오류가 발생했습니다: {str(e)}\n\n(로컬 모드로 전환합니다)\n\n" + self._fallback_response(query)

    def _fallback_response(self, query: str) -> str:
        query_cleaned = query.replace(" ", "")

        if "대표이사" in query_cleaned or "변경" in query_cleaned:
            return "대표이사 또는 최대주주 변경은 정성적 공시 항목으로, 금액에 상관없이 이사회 결의 즉시 지체 없이 공시해야 하는 사항입니다. 시장 종류에 따라 당일 또는 익일까지 거래소에 보고해야 하므로 신속한 확인이 필요합니다.\n\n※ 실제 공시 여부는 최종적으로 공시책임자 및 거래소 업무 담당자와 확인이 필요합니다."

        elif "계약" in query_cleaned or "수주" in query_cleaned or "공급" in query_cleaned:
            return "단일판매계약 또는 공급계약은 정량적 공시 항목입니다. 유가증권시장(KOSPI)은 최근 사업연도 매출액의 5% 이상, 코스닥(KOSDAQ) 시장은 10% 이상인 경우 공시 의무가 발생합니다. '공시 판정 계산' 탭에서 최근 매출액을 입력하여 구체적인 대상 여부를 확인해 보시기 바랍니다.\n\n※ 실제 공시 여부는 최종적으로 공시책임자 및 거래소 업무 담당자와 확인이 필요합니다."

        elif "배당" in query_cleaned:
            return "현금배당 또는 주식배당은 주주총회 소집공고 또는 이사회 결의 시 지체 없이 공시해야 합니다. 배당 결정 사실이 확정되는 즉시 보고하시기 바랍니다.\n\n※ 실제 공시 여부는 최종적으로 공시책임자 및 거래소 업무 담당자와 확인이 필요합니다."

        else:
            matched_rules = []
            for rule in self.rules_db:
                if any(kw in query_cleaned for kw in rule.get('keywords', [])) or rule['title'].replace(" ", "") in query_cleaned:
                    matched_rules.append(rule)

            if matched_rules:
                res = f"질문하신 내용과 관련된 '{matched_rules[0]['title']}' 규정 검토 결과입니다.\n\n"
                res += f"- **기준**: {matched_rules[0]['description']}\n"
                res += f"- **공시 기한**: {matched_rules[0]['disclosure_period']}\n"
                res += f"- **참고사항**: {matched_rules[0]['reference']}\n\n"
                res += "더 자세한 판정을 원하시면 '공시 판정 계산' 탭을 이용해 주세요.\n\n"
                res += "※ 실제 공시 여부는 최종적으로 공시책임자 및 거래소 업무 담당자와 확인이 필요합니다."
                return res

            return f"'{query}'에 대한 구체적인 공시 규정을 찾지 못했습니다. 일반적인 경영 사항의 경우 자산총액, 자기자본, 매출액의 일정 비율 이상 변동이 있을 때 공시 의무가 발생합니다. '공시 판정 계산' 탭에서 수치를 입력해 보시거나 관리 부서에 문의하시기 바랍니다.\n\n※ 실제 공시 여부는 최종적으로 공시책임자 및 거래소 업무 담당자와 확인이 필요합니다."
