"""
공시 자가진단 및 자동 계산 시스템 - Streamlit 웹 인터페이스
"""

import streamlit as st
from decimal import Decimal
import sys
from pathlib import Path
from dotenv import load_dotenv

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

# .env 로드 (로컬 개발용 — Streamlit Cloud에서는 st.secrets 사용)
load_dotenv(Path(__file__).parent / ".env")

# Streamlit Cloud Secrets → 환경변수로 주입
import os
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

from core import (
    DisclosureRuleDatabase,
    DisclosureCalculationEngine,
    FinancialMetrics,
    DisclosureResult,
    ReportGenerator,
    AuditReportParser,
    LawApiClient,
    DartApiClient,
)

# 페이지 설정
st.set_page_config(
    page_title="공시 자가진단 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한글 폰트 설정
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'

# 다크 모던 CSS
st.markdown("""
<style>
/* ── 전체 배경 ── */
.stApp { background-color: #0D0D0D !important; }
.main .block-container { padding-top: 1.5rem; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #222222 !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #CCCCCC !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    border-bottom: 1px solid #2A2A2A;
    padding-bottom: 8px;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: #CCCCCC !important;
    padding: 7px 12px;
    border-radius: 6px;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.07) !important;
}

/* ── 히어로 배너 ── */
.hero-section {
    background: #0D0D0D;
    padding: 48px 0 32px 0;
    text-align: center;
    margin-bottom: 8px;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.25;
    letter-spacing: -0.5px;
    margin-bottom: 14px;
}
.hero-subtitle {
    font-size: 1rem;
    color: #888888;
    line-height: 1.6;
    margin-bottom: 32px;
}
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
}
.hero-stat-card {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 14px;
    padding: 24px 36px;
    text-align: left;
    min-width: 180px;
}
.hero-stat-label {
    font-size: 0.85rem;
    color: #777777;
    margin-bottom: 10px;
    line-height: 1.4;
}
.hero-stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -1px;
}

/* ── 섹션 제목 ── */
.section-header {
    color: #FFFFFF;
    font-size: 1.2rem;
    font-weight: 700;
    border-bottom: 1px solid #2A2A2A;
    padding-bottom: 10px;
    margin-top: 1.2rem;
    margin-bottom: 1rem;
}

/* ── 카드 ── */
.dart-card {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.dart-card-title {
    color: #FFFFFF;
    font-size: 1.05rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 4px;
}

/* ── 버튼 ── */
.stButton > button {
    background-color: #2563EB !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background 0.2s !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton > button:hover {
    background-color: #1D4ED8 !important;
}

/* ── 입력 필드 ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #1A1A1A !important;
    color: #F0F0F0 !important;
    border: 1px solid #333333 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border: 1px solid #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2) !important;
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #2A2A2A !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #888888 !important;
    font-weight: 600 !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 20px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #1A1A1A !important;
    color: #FFFFFF !important;
    border-bottom: 2px solid #2563EB !important;
}

/* ── 메트릭 카드 ── */
[data-testid="stMetric"] {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricLabel"] { color: #888888 !important; font-size: 0.82rem !important; }
[data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 800 !important; }
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* ── 익스팬더 ── */
.stExpander {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
}
details summary { color: #DDDDDD !important; font-weight: 600 !important; }

/* ── 판정 결과 박스 ── */
.result-disclosure {
    background: rgba(239,68,68,0.1);
    border-left: 3px solid #EF4444;
    border-radius: 6px;
    padding: 12px;
    margin: 6px 0;
}
.result-review {
    background: rgba(234,179,8,0.1);
    border-left: 3px solid #EAB308;
    border-radius: 6px;
    padding: 12px;
    margin: 6px 0;
}
.result-no-disclosure {
    background: rgba(34,197,94,0.1);
    border-left: 3px solid #22C55E;
    border-radius: 6px;
    padding: 12px;
    margin: 6px 0;
}

/* ── 테이블 ── */
.stDataFrame thead tr th {
    background-color: #1A1A1A !important;
    color: #FFFFFF !important;
}
.stDataFrame { border: 1px solid #2A2A2A !important; }

/* ── 셀렉트박스 ── */
.stSelectbox [data-baseweb="select"] > div {
    background: #1A1A1A !important;
    border: 1px solid #333333 !important;
    border-radius: 8px !important;
    color: #F0F0F0 !important;
}

/* ── 구분선 ── */
hr { border-color: #2A2A2A !important; }

/* ── info/success/warning/error ── */
.stAlert {
    border-radius: 8px !important;
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    color: #DDDDDD !important;
}

/* ── 컨테이너 border ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 12px !important;
}

/* ── caption / small text ── */
.stCaption, small { color: #666666 !important; }
</style>
""", unsafe_allow_html=True)


# 니어스랩 2025 감사보고서 기준 기본값 (원 단위)
NIARTHLAB_2025 = {
    'sales':               6_600_000_000,    # 매출액 66억
    'total_assets':       23_100_000_000,    # 자산총액 231억
    'equity':            -87_300_000_000,    # 자기자본 -873억 (완전자본잠식)
    'current_assets':     18_300_000_000,    # 유동자산 183억
    'current_liabilities':105_300_000_000,   # 유동부채 1,053억
    'accumulated_loss':   93_000_000_000,    # 누적결손금 930억
}


# 데이터베이스 초기화 (캐싱)
@st.cache_resource
def load_database():
    return DisclosureRuleDatabase()


@st.cache_resource
def load_law_client():
    return LawApiClient()


@st.cache_resource
def load_calculation_engine(_db):
    return DisclosureCalculationEngine(_db)


def format_currency(value):
    """통화 형식"""
    if isinstance(value, (int, float, Decimal)):
        return f"₩{int(value):,}"
    return str(value)


def format_ratio(value):
    """비율 형식"""
    if isinstance(value, Decimal):
        value = float(value)
    return f"{value:.1%}"


# 메인 페이지
def main():
    # 사이드바 메뉴
    with st.sidebar:
        st.markdown("## 📋 메뉴")
        st.markdown("---")
        page = st.radio(
            "",
            options=[
                "공시규칙 검색",
                "감사보고서 분석 (PDF)",
                "공시 판정 계산",
                "정관 공시 체크",
                "AI 공시 어드바이저",
                "사용 가이드",
                "정보",
            ],
            index=0,
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.75rem;opacity:0.7;text-align:center'>"
            "국가법령정보 OC: ysm701<br>Google Gemini AI 연동</div>",
            unsafe_allow_html=True
        )

    # 페이지 라우팅
    if page == "공시규칙 검색":
        show_rule_search()
    elif page == "감사보고서 분석 (PDF)":
        show_pdf_parsing()
    elif page == "공시 판정 계산":
        show_calculation()
    elif page == "정관 공시 체크":
        show_articles_check()

    elif page == "AI 공시 어드바이저":
        show_ai_advisor()
    elif page == "사용 가이드":
        show_guide()
    elif page == "정보":
        show_info()


def _display_rule_list(results, law_client, empty_msg="검색 결과가 없습니다.", key_prefix=""):
    """검색 결과 목록 공통 표시 헬퍼 (key_prefix로 탭 간 위젯 key 충돌 방지)"""
    if not results:
        st.warning(empty_msg)
        return

    st.success(f"총 **{len(results)}건**의 규칙을 찾았습니다.")
    st.markdown("### 검색 결과")

    for idx, rule in enumerate(results, 1):
        with st.expander(f"{idx}. {rule['title']} ({rule['category']})"):
            col1, col2 = st.columns([3, 2])

            with col1:
                st.write(f"**설명**: {rule['description']}")
                st.write(f"**규칙ID**: `{rule['rule_id']}`")
                st.write(f"**참고**: {rule['reference']}")
                st.write(f"**공시 기한**: {rule['disclosure_period']}")

                keywords = rule.get('keywords', [])
                if keywords:
                    st.write(f"**키워드**: {', '.join(keywords)}")

                # 법령 원문 조회 — session_state로 결과 유지
                law_key = f"law_info_{key_prefix}{rule['rule_id']}"
                if st.button("법령 원문 조회", key=f"law_btn_{key_prefix}{rule['rule_id']}"):
                    with st.spinner("국가법령정보 조회 중..."):
                        try:
                            st.session_state[law_key] = law_client.get_article_text(rule['reference'])
                        except Exception as e:
                            st.session_state[law_key] = {"error": str(e)}

                law_info = st.session_state.get(law_key)
                if law_info:
                    if "error" in law_info:
                        st.error(f"조회 오류: {law_info['error']}")
                    else:
                        st.success(f"**{law_info['law_name']}**")
                        meta = []
                        if law_info.get('시행일'):
                            meta.append(f"시행일: {law_info['시행일']}")
                        if law_info.get('효력'):
                            meta.append(f"구분: {law_info['효력']}")
                        if meta:
                            st.caption(" | ".join(meta))
                        if law_info.get('note'):
                            st.caption(f"※ {law_info['note']}")
                        if law_info.get('link'):
                            st.markdown(f"[법령 원문 바로가기]({law_info['link']})")

            with col2:
                st.write(f"**규칙 유형**: {rule['rule_type']}")
                st.write(f"**적용 시장**: {', '.join(rule['market']).upper()}")

                threshold = rule.get('threshold')
                if threshold:
                    st.write(f"**기준 지표**: {threshold['metric']}")
                    st.write(f"**기준값**: {threshold['value']}% ({threshold['description']})")
                else:
                    st.write("**기준**: 즉시 보고 항목")


def show_rule_search():
    """공시규칙 검색 페이지"""
    db = load_database()
    law_client = load_law_client()

    # 히어로 배너 (공시규칙 검색 페이지에서만 표시)
    rule_count = len(db.get_all_rules())
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-title">공시 의무를 자동으로<br>판정하기 위해 출발했습니다.</div>
        <div class="hero-subtitle">
            공시 누락 리스크를 방지하고, 규정을 빠르고 정확하게 검토할 수 있습니다.<br>
            니어스랩 전용 자가진단 시스템
        </div>
        <div class="hero-stats">
            <div class="hero-stat-card">
                <div class="hero-stat-label">공시 규칙 DB</div>
                <div class="hero-stat-value">{rule_count}+</div>
            </div>
            <div class="hero-stat-card">
                <div class="hero-stat-label">지원 시장</div>
                <div class="hero-stat-value">KOSPI · KOSDAQ</div>
            </div>
            <div class="hero-stat-card">
                <div class="hero-stat-label">정관 조항 매핑</div>
                <div class="hero-stat-value">7개</div>
            </div>
            <div class="hero-stat-card">
                <div class="hero-stat-label">AI 분석</div>
                <div class="hero-stat-value">Gemini</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 검색 카드
    st.markdown("""
    <div class="dart-card">
        <div class="dart-card-title">공시규칙 통합검색</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">공시규칙 검색</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["키워드 검색", "카테고리별", "기준 지표별", "DART 실시간 검색"])

    with tab1:
        all_rules = db.get_all_rules()
        st.caption(f"전체 공시규칙 {len(all_rules)}개")
        query = st.text_input("검색어 입력 (예: 계약, 투자, 증자, 배당)", placeholder="검색어를 입력하세요...")
        results = db.search_fuzzy(query) if query else all_rules
        _display_rule_list(results, law_client, "검색 결과가 없습니다.", key_prefix="t1_")

    with tab2:
        categories = db.get_all_categories()
        selected_category = st.selectbox("카테고리 선택", ["전체"] + categories)
        if selected_category != "전체":
            _display_rule_list(db.search_by_category(selected_category), law_client, key_prefix="t2_")
        else:
            _display_rule_list(db.get_all_rules(), law_client, key_prefix="t2_")

    with tab3:
        metric_options = {
            "sales_ratio": "매출액 대비 (%)",
            "equity_ratio": "자기자본 대비 (%)",
            "asset_ratio": "자산총액 대비 (%)"
        }
        selected_metric = st.selectbox(
            "기준 지표 선택",
            options=list(metric_options.keys()),
            format_func=lambda x: metric_options.get(x)
        )
        _display_rule_list(db.search_by_threshold_metric(selected_metric), law_client, key_prefix="t3_")

    with tab4:
        st.markdown(f"""
<div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #F59E0B;
border-radius:8px;padding:14px 18px;margin-bottom:16px">
<div style="color:#FFFFFF;font-weight:700;margin-bottom:8px">📡 DART 실시간 공시 검색이란?</div>
<div style="color:#AAAAAA;font-size:0.87rem;line-height:1.9">
좌측 탭의 규칙 DB는 <b style="color:#F59E0B">수동 정의 규칙({rule_count}개)</b>만 포함합니다.
실제 시장에서 발생하는 공시는 수천 건 이상으로 훨씬 다양합니다.<br>
이 탭에서는 <b style="color:#22C55E">DART(금융감독원 전자공시)에 실제 등록된 공시</b>를 직접 검색할 수 있습니다.<br>
공시 유형·회사명·기간을 선택하면 실제 제출된 공시 목록과 원문 링크를 확인할 수 있습니다.
</div>
</div>
""", unsafe_allow_html=True)

        dc1, dc2, dc3 = st.columns([2, 2, 1])
        with dc1:
            dart_corp_rule = st.text_input(
                "회사명 (선택)",
                value="",
                placeholder="입력 시 해당 회사만, 비워두면 전체",
                key="dart_corp_rule"
            )
        with dc2:
            pblntf_options = {
                "B": "주요사항보고 (유상증자·CB·M&A 등)",
                "A": "정기공시 (사업보고서·반기·분기)",
                "C": "발행공시 (증권신고서 등)",
                "F": "외부감사관련 (감사의견 등)",
                "I": "거래소공시 (배당·임원변동 등)",
                "J": "공정공시 (내부거래 등)",
            }
            dart_ptype = st.selectbox(
                "공시 유형",
                options=list(pblntf_options.keys()),
                format_func=lambda x: pblntf_options[x],
                key="dart_ptype_rule"
            )
        with dc3:
            dart_months_rule = st.selectbox(
                "기간",
                [1, 3, 6, 12],
                index=1,
                format_func=lambda x: f"최근 {x}개월",
                key="dart_months_rule"
            )

        if st.button("DART 검색", key="dart_rule_search", type="primary"):
            with st.spinner("DART 공시 조회 중..."):
                try:
                    dart_items = DartApiClient().search_disclosures(
                        dart_corp_rule.strip(),
                        [],          # categories 빈 리스트 → pblntf_ty 직접 지정
                        months=dart_months_rule,
                        pblntf_override=dart_ptype,
                    )
                    if dart_items:
                        st.success(f"**{len(dart_items)}건** 조회됨")
                        for item in dart_items:
                            rcept_no = item.get("rcept_no", "")
                            date = item.get("rcept_dt", "")
                            title = item.get("report_nm", "")
                            corp = item.get("corp_name", "")
                            url = DartApiClient.disclosure_url(rcept_no)
                            st.markdown(f"- `{date}` **{corp}** — [{title}]({url})")
                    else:
                        st.info("조회된 공시가 없습니다. 기간을 늘리거나 회사명을 확인하세요.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"DART API 오류: {e}")


def show_calculation():
    """공시 판정 계산 페이지"""
    db = load_database()
    engine = load_calculation_engine(db)

    st.markdown("""
    <div class="dart-card">
        <div class="dart-card-title">공시 판정 자동 계산</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">공시 판정 계산</div>',
               unsafe_allow_html=True)
    
    # 탭 분할
    tab1, tab2 = st.tabs(["개별 계산", "일괄 계산"])
    
    with tab1:
        show_single_calculation(db, engine)
    
    with tab2:
        show_batch_calculation(db, engine)


def show_single_calculation(db, engine):
    """개별 계산"""
    UNIT = 100_000_000

    st.markdown("""
<div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #2563EB;
border-radius:8px;padding:16px 20px;margin-bottom:20px">
<div style="color:#FFFFFF;font-weight:700;margin-bottom:10px">📋 개별 계산 사용 방법</div>
<div style="color:#AAAAAA;font-size:0.88rem;line-height:2">
<b style="color:#E0E0E0">① 재무 기준 지표 확인</b> — 좌측 수치는 최근 감사보고서 기준으로 자동 입력됩니다.
새 회계연도 감사보고서가 나왔다면 <b>감사보고서 분석(PDF)</b> 메뉴에서 먼저 업로드·저장하세요.<br>
<b style="color:#E0E0E0">② 거래 정보 입력</b> — 우측에서 거래 유형(카테고리)을 선택하고 거래금액(억원)을 입력하세요.<br>
<b style="color:#E0E0E0">③ 시장 선택</b> — 상장된 시장(KOSPI / KOSDAQ)을 선택하면 해당 기준(%  임계치)이 자동 적용됩니다.<br>
<b style="color:#E0E0E0">④ 공시 판정 계산 버튼 클릭</b> — 각 공시 규칙별 비율과 공시 필요 여부(✅ / ❌)가 표시됩니다.<br>
<b style="color:#E0E0E0">⑤ DART 유사 사례 자동 조회</b> — 판정 결과에서 🔴 공시 대상이 하나 이상이면, 같은 카테고리의 실제 공시 사례를 DART에서 자동으로 가져와 링크로 보여줍니다.
우측 "DART 유사 사례 조회" 섹션에서 회사명(선택)과 조회 기간을 먼저 설정하세요.
회사명을 비워두면 전체 상장사 중 유사 공시 사례를, 상장사명을 입력하면 해당 회사 이력만 조회합니다.<br>
<b style="color:#E0E0E0">⑥ 결과 다운로드</b> — Excel·PDF·JSON으로 저장할 수 있습니다.
</div>
</div>
""", unsafe_allow_html=True)

    # PDF 추출값 우선, 없으면 니어스랩 2025 기본값 사용 (원 → 억원 변환)
    default_vals = st.session_state.get('extracted_metrics') or NIARTHLAB_2025
    def to_uk(key, fallback=0):
        val = default_vals.get(key)
        if val is None:
            return fallback
        return int(val) // 100_000_000

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### 재무 기준 지표")
        st.caption("감사보고서 PDF 업로드 시 자동 반영 — 연도 변경 시에만 수정")
        sales_uk            = st.number_input("매출액 (억원)",      min_value=0,      value=to_uk('sales'),               step=1, format="%d")
        total_assets_uk     = st.number_input("자산총액 (억원)",     min_value=0,      value=to_uk('total_assets'),         step=1, format="%d")
        equity_uk           = st.number_input("자기자본 (억원)",     min_value=-99999, value=to_uk('equity'),               step=1, format="%d")
        current_assets_uk   = st.number_input("유동자산 (억원)",     min_value=0,      value=to_uk('current_assets'),       step=1, format="%d")
        current_liabilities_uk = st.number_input("유동부채 (억원)",  min_value=0,      value=to_uk('current_liabilities'),  step=1, format="%d")
        accumulated_loss_uk = st.number_input("누적결손금 (억원)",   min_value=-99999, value=to_uk('accumulated_loss'),     step=1, format="%d")

    with right:
        st.markdown("#### 거래 정보 입력")
        st.caption("판정할 거래 내용을 입력하세요")

        all_categories = ["전체"] + db.get_all_categories()
        selected_category = st.selectbox("거래 유형 (카테고리)", all_categories,
            help="해당 거래 유형의 공시 규칙만 판정합니다. '전체' 선택 시 모든 규칙 검토.")

        transaction_uk = st.number_input("거래액 (억원)", min_value=0, value=0, step=1, format="%d")
        market = st.selectbox("적용 시장", ["KOSPI", "KOSDAQ"])

        st.markdown("---")
        st.markdown("**DART 유사 사례 조회**")
        dart_corp = st.text_input("회사명 (선택)", value="", key="dart_corp_single",
                                  placeholder="입력 시 해당 회사만, 미입력 시 전체 시장",
                                  help="DART 상장사명 입력 시 해당 회사 공시만 조회. 비상장사이거나 비워두면 전체 시장 유사 사례를 가져옵니다.")
        dart_months = st.selectbox("조회 기간", [3, 6, 12, 24], index=1,
                                   format_func=lambda x: f"최근 {x}개월",
                                   key="dart_months_single")

        st.markdown("---")
        st.markdown("**재무지표 요약**")
        c1, c2 = st.columns(2)
        c1.metric("매출액",   f"{sales_uk:,}억")
        c2.metric("자산총액", f"{total_assets_uk:,}억")
        c1.metric("자기자본", f"{equity_uk:,}억")
        c2.metric("거래액",   f"{transaction_uk:,}억")

    # 억원 → 원 변환
    sales               = sales_uk               * UNIT
    total_assets        = total_assets_uk         * UNIT
    equity              = equity_uk               * UNIT
    transaction_amount  = transaction_uk          * UNIT
    current_assets      = current_assets_uk       * UNIT
    current_liabilities = current_liabilities_uk  * UNIT
    accumulated_loss    = accumulated_loss_uk     * UNIT
    
    # 재무 지표 객체 생성
    metrics = FinancialMetrics(
        sales=Decimal(str(sales)),
        total_assets=Decimal(str(total_assets)),
        equity=Decimal(str(equity)),
        current_assets=Decimal(str(current_assets)),
        current_liabilities=Decimal(str(current_liabilities)),
        accumulated_loss=Decimal(str(accumulated_loss))
    )

    st.markdown("---")

    if st.button("공시 판정 계산", key="single_calc", type="primary"):
        if transaction_amount == 0:
            st.warning("거래액을 입력해 주세요.")
            return
        if equity == 0 and sales == 0 and total_assets == 0:
            st.warning("재무 지표(매출액, 자산총액, 자기자본 중 하나 이상)를 입력해 주세요.")
            return

        # 계산 수행 후 session_state에 저장 (버튼 중첩 문제 해결)
        all_results = engine.calculate(metrics, Decimal(str(transaction_amount)), market=market.lower())
        results_to_save = [r for r in all_results if r.rule.get('category') == selected_category] \
                          if selected_category != "전체" else all_results
        st.session_state['_single_results'] = results_to_save
        st.session_state['_single_metrics'] = metrics.to_dict()
        st.session_state['_single_tx'] = transaction_amount
        st.session_state['_single_market'] = market
        st.session_state['_single_inputs'] = (sales_uk, total_assets_uk, equity_uk, transaction_uk, selected_category)

        st.markdown("### 계산 결과")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("매출액", f"{sales_uk:,}억원")
        with col2:
            st.metric("자산총액", f"{total_assets_uk:,}억원")
        with col3:
            st.metric("자기자본", f"{equity_uk:,}억원")
        with col4:
            st.metric("거래액", f"{transaction_uk:,}억원")
        
        st.markdown("---")

        results = st.session_state['_single_results']
        if selected_category != "전체":
            st.info(f"거래 유형 **{selected_category}** 관련 규칙만 표시합니다.")

        # 결과 요약
        summary = engine.get_summary(results)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("검토 규칙", summary['total_rules_checked'])
        with col2:
            st.metric("공시 대상", summary['disclosure_required'], delta_color="off")
        with col3:
            st.metric("검토 필요", summary['review_required'], delta_color="inverse")
        with col4:
            st.metric("공시 미대상", summary['no_disclosure'])
        
        st.markdown("---")
        st.markdown("### 📋 상세 결과")
        
        # 결과 상세 표시
        if results:
            for result in results:
                css_class = ""
                emoji = ""
                
                if result.result == DisclosureResult.DISCLOSURE_REQUIRED:
                    css_class = "result-disclosure"
                    emoji = "🚨"
                elif result.result == DisclosureResult.REVIEW_REQUIRED:
                    css_class = "result-review"
                    emoji = "⚠️"
                else:
                    css_class = "result-no-disclosure"
                    emoji = "✅"
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 2, 2])
                    
                    with col1:
                        st.markdown(f"### {emoji} {result.rule['title']}")
                        st.write(f"**카테고리**: {result.rule['category']}")
                        st.write(f"**규칙 ID**: `{result.rule['rule_id']}`")
                    
                    with col2:
                        st.write(f"**기준 지표**: {result.metric_type}")
                        st.write(f"**기준액**: {format_currency(result.threshold_amount)}")
                        st.write(f"**거래액**: {format_currency(result.transaction_amount)}")
                    
                    with col3:
                        st.write(f"**거래액 비율**: {format_ratio(result.ratio)}")
                        st.write(f"**판정**: **{result.result.value}**")
                        st.write(f"**근거**: {result.reason}")
        
        # 결과 다운로드
        st.markdown("---")
        st.markdown("### 📥 결과 다운로드")
        
        col1, col2, col3 = st.columns(3)
        
        generator = ReportGenerator()
        financial_metrics_dict = metrics.to_dict()
        transaction_info = {
            '거래액': transaction_amount,
            '시장': market,
        }
        
        with col1:
            excel_data = generator.to_excel(results, financial_metrics_dict, transaction_info)
            st.download_button(
                label="📊 Excel 다운로드",
                data=excel_data,
                file_name=f"공시판정_{Decimal(str(transaction_amount)).__format__(',')}_결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            pdf_data = generator.to_pdf(results, financial_metrics_dict, transaction_info)
            st.download_button(
                label="📄 PDF 다운로드",
                data=pdf_data,
                file_name=f"공시판정_{Decimal(str(transaction_amount)).__format__(',')}_보고서.pdf",
                mime="application/pdf"
            )
        
        with col3:
            json_data = generator.to_json(results, financial_metrics_dict, transaction_info)
            st.download_button(
                label="📋 JSON 다운로드",
                data=json_data,
                file_name=f"공시판정_{Decimal(str(transaction_amount)).__format__(',')}_데이터.json",
                mime="application/json"
            )

        # ── DART 유사 공시 사례 자동 조회 ──────────────────────────
        triggered_cats = list({
            r.rule.get('category') for r in results
            if r.result == DisclosureResult.DISCLOSURE_REQUIRED
        })
        if triggered_cats:
            st.markdown("---")
            st.markdown("### 🔍 DART 유사 공시 사례")
            scope = f"'{dart_corp}'" if dart_corp.strip() else "전체 시장"
            st.caption(
                f"{scope} · 최근 {dart_months}개월 · "
                f"트리거 카테고리: {', '.join(triggered_cats)}"
            )
            with st.spinner("DART 공시 조회 중..."):
                try:
                    dart_items = DartApiClient().search_disclosures(
                        dart_corp.strip() or "", triggered_cats, months=dart_months
                    )
                    if dart_items:
                        st.success(f"**{len(dart_items)}건** 조회됨")
                        for item in dart_items[:20]:
                            rcept_no = item.get("rcept_no", "")
                            date = item.get("rcept_dt", "")
                            title = item.get("report_nm", "")
                            corp = item.get("corp_name", "")
                            url = DartApiClient.disclosure_url(rcept_no)
                            st.markdown(f"- `{date}` **{corp}** — [{title}]({url})")
                    else:
                        st.info("해당 기간 내 유사 공시 이력이 없습니다.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"DART API 오류: {e}")


def show_batch_calculation(db, engine):
    """일괄 계산"""
    UNIT = 100_000_000

    st.markdown("""
<div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #22C55E;
border-radius:8px;padding:16px 20px;margin-bottom:20px">
<div style="color:#FFFFFF;font-weight:700;margin-bottom:10px">📋 일괄 계산 사용 방법</div>
<div style="color:#AAAAAA;font-size:0.88rem;line-height:2">
<b style="color:#E0E0E0">① 재무 기준 지표 확인</b> — 좌측 수치는 최근 감사보고서 기준으로 자동 입력됩니다.
새 회계연도라면 <b>감사보고서 분석(PDF)</b> 메뉴에서 먼저 업로드·저장하세요.<br>
<b style="color:#E0E0E0">② 거래 개수 설정</b> — 한 번에 판정할 거래 수(최대 10건)를 선택하세요.<br>
<b style="color:#E0E0E0">③ 거래별 입력</b> — 각 거래의 유형과 금액을 입력합니다. 동일 카테고리 거래가 여러 건이면 각각 행을 추가하세요.<br>
<b style="color:#E0E0E0">④ 일괄 계산 실행</b> — 입력한 모든 거래에 대해 공시 필요 여부를 한 번에 확인할 수 있습니다.<br>
<span style="color:#F59E0B">💡 개별 계산과 달리 여러 거래를 한 화면에서 비교할 때 유용합니다.</span>
</div>
</div>
""", unsafe_allow_html=True)

    default_vals = st.session_state.get('extracted_metrics') or NIARTHLAB_2025
    def to_uk(key, fallback=0):
        val = default_vals.get(key)
        if val is None:
            return fallback
        return int(val) // 100_000_000

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### 재무 기준 지표")
        st.caption("감사보고서 PDF 업로드 시 자동 반영 — 연도 변경 시에만 수정")
        sales_uk            = st.number_input("매출액 (억원)",  min_value=0,      value=to_uk('sales'),               step=1, format="%d", key="b_sales")
        total_assets_uk     = st.number_input("자산총액 (억원)", min_value=0,      value=to_uk('total_assets'),         step=1, format="%d", key="b_assets")
        equity_uk           = st.number_input("자기자본 (억원)", min_value=-99999, value=to_uk('equity'),               step=1, format="%d", key="b_equity")
        current_assets_uk   = st.number_input("유동자산 (억원)", min_value=0,      value=to_uk('current_assets'),       step=1, format="%d", key="b_ca")
        current_liabilities_uk = st.number_input("유동부채 (억원)", min_value=0,   value=to_uk('current_liabilities'),  step=1, format="%d", key="b_cl")
        accumulated_loss_uk = st.number_input("누적결손금 (억원)", min_value=-99999, value=to_uk('accumulated_loss'),     step=1, format="%d", key="b_loss")

    with right:
        st.markdown("#### 거래 목록 입력")
        st.caption("판정할 거래를 순서대로 입력하세요")
        market = st.selectbox("적용 시장", ["KOSPI", "KOSDAQ"], key="b_market")
        num_transactions = st.number_input("거래 개수", min_value=1, max_value=10, value=3, key="b_num")

        transactions = []
        all_categories = db.get_all_categories()
        for i in range(int(num_transactions)):
            st.markdown(f"**거래 {i+1}**")
            c1, c2 = st.columns([1, 1])
            with c1:
                cat = st.selectbox("거래 유형", all_categories, key=f"b_cat_{i}")
            with c2:
                amt_uk = st.number_input("거래액 (억원)", min_value=0, value=0, step=1, format="%d", key=f"b_amt_{i}")
            transactions.append({'category': cat, 'amount_uk': amt_uk})

    st.markdown("---")

    if st.button("일괄 계산 실행", key="batch_calc", type="primary"):
        sales               = sales_uk               * UNIT
        total_assets        = total_assets_uk         * UNIT
        equity              = equity_uk               * UNIT
        current_assets      = current_assets_uk       * UNIT
        current_liabilities = current_liabilities_uk  * UNIT
        accumulated_loss    = accumulated_loss_uk     * UNIT

        metrics = FinancialMetrics(
            sales=Decimal(str(sales)),
            total_assets=Decimal(str(total_assets)),
            equity=Decimal(str(equity)),
            current_assets=Decimal(str(current_assets)),
            current_liabilities=Decimal(str(current_liabilities)),
            accumulated_loss=Decimal(str(accumulated_loss))
        )

        st.markdown("### 일괄 계산 결과")

        for idx, tx in enumerate(transactions, 1):
            amt = tx['amount_uk'] * UNIT
            if amt == 0:
                continue

            all_results = engine.calculate(metrics, Decimal(str(amt)), market=market.lower())
            cat_results = [r for r in all_results if r.rule.get('category') == tx['category']]
            results = cat_results if cat_results else all_results

            required = [r for r in results if r.result == DisclosureResult.DISCLOSURE_REQUIRED]
            review   = [r for r in results if r.result == DisclosureResult.REVIEW_REQUIRED]

            if required:
                tag, color = "🔴 공시 대상", "result-disclosure"
            elif review:
                tag, color = "🟡 검토 필요", "result-review"
            else:
                tag, color = "🟢 공시 미대상", "result-no-disclosure"

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(f"거래 {idx} ({tx['category']})", f"{tx['amount_uk']:,}억원")
                c2.metric("판정", tag)
                c3.metric("공시 대상", len(required))
                c4.metric("검토 필요", len(review))

                if required or review:
                    with st.expander("상세 보기"):
                        for r in (required + review):
                            st.write(f"**{r.rule['title']}** — 비율 {float(r.ratio):.1%} / 근거: {r.reason}")


def show_articles_check():
    """정관 공시 체크 페이지 — 니어스랩 정관 조항별 공시 의무 매핑"""

    # ── 니어스랩 정관 핵심 조항 데이터 ──────────────────────────────
    ARTICLES = [
        {
            "article": "제2조",
            "title": "사업 목적 (27개)",
            "summary": "드론·항공촬영·측량·검사·물류·소프트웨어 개발 등 27개 사업목적 열거",
            "limit": None,
            "trigger": "사업 목적 추가·삭제·변경",
            "disclosure": "정관변경 — 주주총회 특별결의(발행주식 2/3 이상 찬성) 후 DART 공시",
            "form": "주요사항보고서 / 주주총회소집통지",
            "deadline": "주총 결의일로부터 5일 이내",
            "risk": "high",
        },
        {
            "article": "제5조",
            "title": "발행주식 총수",
            "summary": "수권주식 5억 주 / 액면가 100원",
            "limit": "5억 주",
            "trigger": "수권주식 한도 초과 증자 추진",
            "disclosure": "정관변경 + 유상증자 — 한도 증량 시 주총 특별결의 先 진행",
            "form": "주요사항보고서 (유상증자결정)",
            "deadline": "이사회결의일 당일",
            "risk": "high",
        },
        {
            "article": "제9조",
            "title": "신주인수권 / 제3자 배정",
            "summary": "기술도입·재무구조개선 등 목적으로 이사회 결의 시 제3자 배정 가능",
            "limit": None,
            "trigger": "제3자 배정 유상증자 결정",
            "disclosure": "주요사항보고서 (제3자배정 유상증자결정) — 이사회결의 즉시",
            "form": "주요사항보고서",
            "deadline": "이사회결의일 당일",
            "risk": "high",
        },
        {
            "article": "제10조",
            "title": "주식매수선택권 (스톡옵션)",
            "summary": "임직원 대상 주총 특별결의로 부여 가능",
            "limit": "발행주식 총수의 15% 이내",
            "trigger": "스톡옵션 신규 부여 또는 변경",
            "disclosure": "주요사항보고서 (주식매수선택권부여결정) + 주총결의 후 공시",
            "form": "주요사항보고서 / 임시주총소집결정",
            "deadline": "이사회·주총 결의일 당일",
            "risk": "medium",
        },
        {
            "article": "제17조",
            "title": "전환사채 (CB)",
            "summary": "이사회 결의로 발행 가능 — 정관상 한도 500억 원",
            "limit": "500억 원",
            "trigger": "CB 발행 결정",
            "disclosure": "주요사항보고서 (전환사채권발행결정) — 이사회결의 당일",
            "form": "주요사항보고서",
            "deadline": "이사회결의일 당일",
            "risk": "high",
        },
        {
            "article": "제18조",
            "title": "신주인수권부사채 (BW)",
            "summary": "이사회 결의로 발행 가능 — 정관상 한도 500억 원",
            "limit": "500억 원",
            "trigger": "BW 발행 결정",
            "disclosure": "주요사항보고서 (신주인수권부사채권발행결정) — 이사회결의 당일",
            "form": "주요사항보고서",
            "deadline": "이사회결의일 당일",
            "risk": "high",
        },
        {
            "article": "제55조 / 55조의2",
            "title": "배당 / 중간배당",
            "summary": "결산배당(정기주총 결의) + 중간배당(이사회 결의, 연 1회)",
            "limit": None,
            "trigger": "배당 결정 (결산 또는 중간)",
            "disclosure": "배당결정 공시 (주당배당금, 배당총액, 배당기준일)",
            "form": "주요사항보고서 / 결산 사업보고서",
            "deadline": "이사회·주총 결의일로부터 1일 이내",
            "risk": "medium",
        },
    ]

    # 현재 CB·BW 잔액 (니어스랩 2025 기준 — 정관 한도 비교용)
    CURRENT_CB_BW = {
        "CB_issued": 0,    # 억원 (현재 발행 잔액 — 별도 확인 필요)
        "BW_issued": 0,
        "CB_limit":  500,  # 정관 한도 억원
        "BW_limit":  500,
    }

    st.markdown("""
    <div class="dart-card">
        <div class="dart-card-title">정관 공시 체크</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="section-header">니어스랩 정관 → 공시 의무 매핑</div>', unsafe_allow_html=True)
    st.caption("니어스랩 정관(2025년 기준) 핵심 조항별 공시 트리거·서식·기한을 정리합니다.")

    st.markdown("""
<div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #A855F7;
border-radius:8px;padding:16px 20px;margin-bottom:20px">
<div style="color:#FFFFFF;font-weight:700;margin-bottom:10px">📋 정관 공시 체크 사용 방법</div>
<div style="color:#AAAAAA;font-size:0.88rem;line-height:2">
<b style="color:#E0E0E0">① 정관 조항별 공시 의무</b> — 니어스랩 정관의 핵심 조항(사업목적·자본금·이사회 등)별로 공시 트리거, 서식, 기한을 확인합니다.
위험도 필터(즉시공시 / 주총후공시)로 우선순위를 좁힐 수 있습니다.<br>
<b style="color:#E0E0E0">② 정관 변경 시뮬레이터</b> — 변경 예정인 조항을 선택하면 필요한 공시 절차와 주의사항을 미리 확인할 수 있습니다.<br>
<b style="color:#E0E0E0">③ 자본조달 한도 체크</b> — CB(전환사채)·BW(신주인수권부사채) 등 자본조달 수단별 정관 한도 대비 잔여 한도를 확인합니다.<br>
<span style="color:#F59E0B">💡 정관 변경이 필요한 경우, 반드시 주주총회 특별결의 일정을 감안하여 공시 기한을 역산하세요.</span>
</div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["정관 조항별 공시 의무", "정관 변경 시뮬레이터", "자본조달 한도 체크"])

    # ── Tab 1: 조항별 매핑 ──────────────────────────────────────────
    with tab1:
        st.markdown("### 핵심 조항 공시 의무 요약")

        risk_filter = st.selectbox("위험도 필터", ["전체", "high — 즉시 공시", "medium — 주총 후 공시"],
                                   key="art_risk")
        filter_val = None if risk_filter == "전체" else risk_filter.split(" ")[0]

        for art in ARTICLES:
            if filter_val and art["risk"] != filter_val:
                continue

            risk_color = "#E53935" if art["risk"] == "high" else "#FFB300"
            risk_label = "🔴 즉시공시" if art["risk"] == "high" else "🟡 주총후공시"

            with st.expander(f"{art['article']} {art['title']}  {risk_label}"):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"**조항 내용**")
                    st.write(art["summary"])
                    if art["limit"]:
                        st.markdown(f"**정관 한도**: `{art['limit']}`")
                    st.markdown(f"**공시 트리거**: {art['trigger']}")
                with c2:
                    st.markdown(f"**공시 의무**")
                    st.write(art["disclosure"])
                    st.markdown(f"**제출 서식**: `{art['form']}`")
                    st.markdown(f"**제출 기한**: {art['deadline']}")

    # ── Tab 2: 변경 시뮬레이터 ─────────────────────────────────────
    with tab2:
        st.markdown("### 정관 변경 시뮬레이터")
        st.info("변경하려는 조항을 선택하면 발생하는 공시 의무를 확인할 수 있습니다.")

        article_labels = [f"{a['article']} {a['title']}" for a in ARTICLES]
        selected = st.multiselect("변경 예정 조항 선택", article_labels, key="art_sel")

        if selected:
            st.markdown("---")
            st.markdown("### 발생하는 공시 의무")

            checklist = []
            for label in selected:
                art = next((a for a in ARTICLES if f"{a['article']} {a['title']}" == label), None)
                if art:
                    checklist.append(art)

            # 요약 메트릭
            high_cnt = sum(1 for a in checklist if a["risk"] == "high")
            med_cnt  = sum(1 for a in checklist if a["risk"] == "medium")
            c1, c2, c3 = st.columns(3)
            c1.metric("선택 조항 수", len(checklist))
            c2.metric("즉시공시 항목", high_cnt, delta=None)
            c3.metric("주총후공시 항목", med_cnt)

            st.markdown("---")
            for art in checklist:
                risk_icon = "🔴" if art["risk"] == "high" else "🟡"
                st.markdown(f"""
<div style="background:white;border-left:4px solid {'#E53935' if art['risk']=='high' else '#FFB300'};
border-radius:4px;padding:12px 16px;margin:8px 0;box-shadow:0 1px 4px rgba(0,0,0,0.07)">
<b>{risk_icon} {art['article']} {art['title']}</b><br>
📋 <b>서식</b>: {art['form']}<br>
⏰ <b>기한</b>: {art['deadline']}<br>
📌 <b>내용</b>: {art['disclosure']}
</div>
""", unsafe_allow_html=True)

            st.markdown("---")
            st.warning(
                "**주의**: 정관 변경은 반드시 주주총회 특별결의(출석 의결권의 2/3 + 발행주식 1/3 이상 찬성) 전에 "
                "주주총회 소집 공시(2주 전)를 완료해야 합니다."
            )
        else:
            st.caption("변경 예정 조항을 하나 이상 선택하세요.")

    # ── Tab 3: 자본조달 한도 체크 ──────────────────────────────────
    with tab3:
        st.markdown("### 자본조달 정관 한도 체크")
        st.info("CB·BW 발행 예정금액을 입력하면 정관 한도 대비 여유분을 계산합니다.")

        col_l, col_r = st.columns([1, 1], gap="large")

        with col_l:
            st.markdown("#### 정관 한도 (변경 시 수정)")
            cb_limit = st.number_input("전환사채(CB) 정관 한도 (억원)", min_value=0,
                                       value=CURRENT_CB_BW["CB_limit"], step=10, format="%d", key="cb_limit")
            bw_limit = st.number_input("신주인수권부사채(BW) 정관 한도 (억원)", min_value=0,
                                       value=CURRENT_CB_BW["BW_limit"], step=10, format="%d", key="bw_limit")
            st.markdown("#### 현재 발행 잔액")
            cb_current = st.number_input("CB 현재 잔액 (억원)", min_value=0,
                                         value=CURRENT_CB_BW["CB_issued"], step=10, format="%d", key="cb_cur")
            bw_current = st.number_input("BW 현재 잔액 (억원)", min_value=0,
                                         value=CURRENT_CB_BW["BW_issued"], step=10, format="%d", key="bw_cur")

        with col_r:
            st.markdown("#### 신규 발행 예정")
            cb_new = st.number_input("CB 신규 발행 예정 (억원)", min_value=0, value=0, step=10, format="%d", key="cb_new")
            bw_new = st.number_input("BW 신규 발행 예정 (억원)", min_value=0, value=0, step=10, format="%d", key="bw_new")

            st.markdown("---")

            cb_after = cb_current + cb_new
            bw_after = bw_current + bw_new
            cb_margin = cb_limit - cb_after
            bw_margin = bw_limit - bw_after

            st.markdown("#### 한도 여유 분석")

            cb_ok = cb_margin >= 0
            bw_ok = bw_margin >= 0

            c1, c2 = st.columns(2)
            c1.metric("CB 발행 후 잔액", f"{cb_after:,}억 / {cb_limit:,}억",
                      delta=f"여유 {cb_margin:,}억" if cb_ok else f"한도초과 {-cb_margin:,}억",
                      delta_color="normal" if cb_ok else "inverse")
            c2.metric("BW 발행 후 잔액", f"{bw_after:,}억 / {bw_limit:,}억",
                      delta=f"여유 {bw_margin:,}억" if bw_ok else f"한도초과 {-bw_margin:,}억",
                      delta_color="normal" if bw_ok else "inverse")

        st.markdown("---")

        if not cb_ok or not bw_ok:
            exceeded = []
            if not cb_ok:
                exceeded.append(f"CB {-cb_margin:,}억원 초과 → 정관 제17조 한도 변경(주총 특별결의) 必")
            if not bw_ok:
                exceeded.append(f"BW {-bw_margin:,}억원 초과 → 정관 제18조 한도 변경(주총 특별결의) 必")
            st.error("**한도 초과 — 정관 변경 선행 필요**\n\n" + "\n".join(f"- {e}" for e in exceeded))
        elif cb_new > 0 or bw_new > 0:
            st.success("정관 한도 내 발행 가능합니다. 이사회 결의 후 당일 주요사항보고서를 제출하세요.")

        st.markdown("---")
        st.markdown("#### 수권주식 한도 (제5조)")
        auth_shares = 500_000_000
        col1, col2, col3 = st.columns(3)
        col1.metric("수권주식 총수", "5억 주")
        col2.metric("주당 액면가", "100원")
        col3.metric("최대 자본금", "500억원")
        st.caption("수권주식 한도 초과 증자 시 정관 변경(주총 특별결의) 후 유상증자 주요사항보고서 제출 필요.")


def show_guide():
    """사용 가이드"""
    st.markdown("## 📖 사용 가이드")
    
    st.markdown("""
    ### 공시규칙 검색
    
    - **키워드 검색**: "계약", "투자" 등 일상 용어로 검색
    - **카테고리 검색**: 계약, 투자, 증자 등 주요 카테고리별 검색
    - **기준 지표 검색**: sales_ratio, equity_ratio 등 기준별 검색
    
    ### 공시 판정 계산
    
    1. **재무 지표 입력**: 감사보고서 기반 재무 데이터 입력
    2. **거래 정보 입력**: 거래액 및 관련 정보 입력
    3. **계산 실행**: "공시 판정 계산" 버튼 클릭
    4. **결과 확인**: 공시 대상 여부 및 세부 사항 확인
    
    ### 판정 결과 해석
    
    - **🚨 공시 대상**: 즉시 공시 의무 발생
    - **⚠️ 검토 필요**: 기준에 근접하여 재검토 필요
    - **✅ 공시 미대상**: 공시 의무 없음
    
    ### 기준 금액 계산
    
    기준 금액은 다음 공식으로 계산됩니다:
    
    ```
    기준 금액 = 재무 지표값 × (기준 비율 / 100)
    ```
    
    예를 들어, 매출액 10억 기준 10% 규칙:
    ```
    기준 금액 = 10억 × (10 / 100) = 1억
    ```
    """)


def show_info():
    """정보"""
    st.markdown("## ℹ️ 시스템 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 프로젝트 정보")
        st.markdown("""
        - **프로젝트명**: 공시 자가진단 및 자동 계산 시스템
        - **목표**: 공시 누락 리스크 방지 및 효율화
        - **상태**: Phase 2 개발 중
        """)
    
    with col2:
        st.markdown("### 지원 규칙")
        db = load_database()
        categories = db.get_all_categories()
        
        col_count = 2
        rules_text = f"총 **{len(db.get_all_rules())}개** 규칙\n\n"
        for cat in categories:
            count = len(db.search_by_category(cat))
            rules_text += f"- **{cat}**: {count}개\n"
        
        st.markdown(rules_text)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 기술 스택")
        st.markdown("""
        - **Frontend**: Streamlit
        - **Backend**: Python
        - **Database**: JSON (JSON, SQLite 예정)
        - **AI**: Claude API (예정)
        """)
    
    with col2:
        st.markdown("### 로드맵")
        st.markdown("""
        - ✅ Phase 1: 규칙DB + 계산엔진
        - ✅ Phase 2: Streamlit UI
        - ✅ Phase 3: PDF 파싱 + AI
        - 🚀 Phase 4: 고도화 및 서비스화
        """)



_GEMINI_PROMPT = """이 한국 기업 감사보고서에서 다음 재무지표를 원(KRW) 단위 정수로 추출하여 JSON으로만 답하세요.
값을 찾지 못한 항목은 null로 표기하세요.

추출 항목:
- sales: 매출액 (또는 영업수익)
- total_assets: 자산총액 (또는 자산합계)
- equity: 자기자본 (또는 자본총계, 자본잠식이면 음수)
- current_assets: 유동자산
- current_liabilities: 유동부채
- accumulated_loss: 누적결손금 (결손이면 양수로)
- capital: 자본금

응답 형식: {"sales": 6600000000, "total_assets": 23100000000, "equity": -87300000000, ...}"""


def _extract_metrics_with_ai(text: str, pdf_bytes: bytes = None) -> dict:
    """Gemini AI로 재무지표 추출. 스캔 PDF면 이미지 변환 후 Vision으로 처리."""
    import os, json, re as _re
    try:
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError("GOOGLE_API_KEY 미설정")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # 스캔 PDF: 텍스트 500자 미만 → 페이지를 이미지로 변환해서 Vision 처리
        if len(text.strip()) < 500 and pdf_bytes:
            import fitz, base64
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            parts = [_GEMINI_PROMPT]
            for i in range(min(20, len(doc))):
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img_b64 = base64.b64encode(pix.tobytes("png")).decode()
                parts.append({"inline_data": {"mime_type": "image/png", "data": img_b64}})
            doc.close()
            response = model.generate_content(parts)
        else:
            response = model.generate_content(
                f"아래 감사보고서 텍스트에서:\n{_GEMINI_PROMPT}\n\n텍스트:\n{text[:8000]}"
            )

        raw = _re.sub(r"```(?:json)?", "", response.text.strip()).strip("`").strip()
        return json.loads(raw)
    except Exception as e:
        # 세션에 에러 저장 (show_pdf_parsing에서 표시)
        st.session_state["_ai_extract_error"] = str(e)
        return {}


def _reports_index_path() -> Path:
    return Path(__file__).parent / "data" / "saved_reports.json"


def _load_saved_reports() -> list:
    p = _reports_index_path()
    if p.exists():
        import json as _json
        try:
            return _json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_report_entry(name: str, report_type: str, metrics: dict):
    import json as _json, uuid as _uuid
    from datetime import datetime as _dt
    reports = _load_saved_reports()
    entry = {
        "id": str(_uuid.uuid4())[:8],
        "name": name,
        "report_type": report_type,
        "saved_at": _dt.now().strftime("%Y-%m-%d %H:%M"),
        "metrics": {k: v for k, v in metrics.items() if v is not None},
    }
    reports.insert(0, entry)
    p = _reports_index_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def _delete_report_entry(report_id: str):
    import json as _json
    reports = [r for r in _load_saved_reports() if r["id"] != report_id]
    p = _reports_index_path()
    p.write_text(_json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")


def _display_metrics(metrics: dict, unit: int = 100_000_000):
    label_map = {
        'sales': '매출액', 'total_assets': '자산총액', 'equity': '자기자본',
        'current_assets': '유동자산', 'current_liabilities': '유동부채',
        'accumulated_loss': '누적결손금', 'capital': '자본금',
    }
    cols = st.columns(4)
    for i, (key, label) in enumerate(label_map.items()):
        val = metrics.get(key)
        display = f"{int(val) // unit:,}억원" if val else "미추출"
        cols[i % 4].metric(label, display)


def show_pdf_parsing():
    """보고서 PDF 파싱 및 지표 저장 페이지"""
    UNIT = 100_000_000

    st.markdown("""
    <div class="dart-card">
        <div class="dart-card-title">보고서 PDF 분석 · 저장</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="section-header">감사보고서 / 분기보고서 PDF 파싱</div>', unsafe_allow_html=True)

    # DART 다운로드 안내
    st.markdown("""
<div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #2563EB;
border-radius:8px;padding:16px 20px;margin-bottom:16px">
<div style="color:#FFFFFF;font-weight:700;margin-bottom:8px">📥 PDF 파일 준비 방법</div>
<div style="color:#AAAAAA;font-size:0.9rem;line-height:1.8">
회계법인에서 받은 <b style="color:#EF4444">스캔본 PDF는 이미지</b>라 숫자 자동 추출이 안 됩니다.<br>
<b style="color:#22C55E">DART(전자공시)에서 받은 PDF</b>는 텍스트 기반이라 바로 추출됩니다.<br><br>
<b>DART에서 다운로드하는 방법:</b><br>
① <a href="https://dart.fss.or.kr" target="_blank" style="color:#2563EB">dart.fss.or.kr</a> 접속
→ ② 상단 검색창에 회사명 입력
→ ③ 공시 목록에서 <b>감사보고서 / 분기보고서</b> 클릭
→ ④ 우측 상단 <b>첨부파일 다운로드</b>
</div>
</div>
""", unsafe_allow_html=True)

    # ── 저장된 보고서 불러오기 ────────────────────────────
    saved = _load_saved_reports()
    tab_saved, tab_upload = st.tabs([f"저장된 보고서 ({len(saved)}개)", "새 보고서 업로드"])

    # ── Tab: 저장된 보고서 ────────────────────────────────
    with tab_saved:
        if not saved:
            st.info("아직 저장된 보고서가 없습니다. '새 보고서 업로드' 탭에서 PDF를 올려 저장하세요.")
        else:
            options = [f"[{r['report_type']}] {r['name']}  ({r['saved_at']})" for r in saved]
            sel_idx = st.selectbox("보고서 선택", range(len(options)),
                                   format_func=lambda i: options[i], key="saved_sel")
            chosen = saved[sel_idx]

            st.markdown("---")
            st.markdown(f"#### {chosen['name']}")
            st.caption(f"유형: {chosen['report_type']} | 저장일시: {chosen['saved_at']}")
            _display_metrics(chosen["metrics"])

            col_load, col_del = st.columns([2, 1])
            with col_load:
                if st.button("이 보고서를 공시 판정 계산에 적용", type="primary", key="load_saved"):
                    st.session_state['extracted_metrics'] = chosen["metrics"]
                    st.success(f"'{chosen['name']}' 지표가 적용됐습니다. '공시 판정 계산' 메뉴로 이동하세요.")
            with col_del:
                if st.button("삭제", key="del_saved"):
                    _delete_report_entry(chosen["id"])
                    st.rerun()

    # ── Tab: 새 보고서 업로드 ────────────────────────────
    with tab_upload:
        st.info("PDF를 업로드하면 Gemini AI가 재무지표를 추출합니다. 추출 후 저장하면 다음부터 재업로드 없이 바로 사용할 수 있습니다.")

        col_name, col_type = st.columns([2, 1])
        with col_name:
            report_name = st.text_input("보고서 이름", placeholder="예: 니어스랩 2025 연간 / 2025 Q1 분기")
        with col_type:
            report_type = st.selectbox("보고서 유형", ["감사보고서", "분기보고서", "반기보고서", "사업보고서"])

        uploaded_file = st.file_uploader("PDF 파일 선택", type=['pdf'], key="pdf_upload")

        if uploaded_file is None:
            return

        # PDF 텍스트 추출
        with st.spinner("PDF 텍스트 추출 중..."):
            import fitz
            try:
                pdf_bytes = uploaded_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                full_text = "".join(page.get_text() for page in doc)
                doc.close()
            except Exception as e:
                st.error(f"PDF 열기 실패: {e}")
                return

        is_scanned = len(full_text.strip()) < 500

        # ── 텍스트 PDF(DART): 정규식 먼저, Gemini 없이 처리 ──
        ai_metrics = {}
        extract_method = ""

        if not is_scanned:
            with st.spinner("재무지표 추출 중..."):
                temp_path = Path(__file__).parent / "data" / "temp_upload.pdf"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path.write_bytes(pdf_bytes)
                try:
                    ai_metrics = AuditReportParser().parse_pdf(str(temp_path))
                finally:
                    if temp_path.exists():
                        temp_path.unlink()
            if ai_metrics and any(v for v in ai_metrics.values()):
                extract_method = "regex"

        # ── 정규식 실패 또는 스캔 PDF: Gemini Vision 시도 ──
        if not ai_metrics or not any(v for v in ai_metrics.values()):
            st.session_state.pop("_ai_extract_error", None)
            label = "스캔 PDF — Gemini Vision 분석 중... (30초~1분 소요)" if is_scanned \
                    else "정규식 추출 실패 — Gemini AI 재시도 중..."
            with st.spinner(label):
                ai_metrics = _extract_metrics_with_ai(full_text, pdf_bytes=pdf_bytes)
            ai_err = st.session_state.pop("_ai_extract_error", None)
            if ai_err:
                st.warning(f"AI 추출 오류: `{ai_err}`")
            elif ai_metrics:
                extract_method = "gemini"

        if extract_method == "regex":
            st.caption("✅ 텍스트 PDF — 정규식 추출 완료 (Gemini 미사용)")
        elif extract_method == "gemini":
            st.caption("✅ Gemini AI 추출 완료")
        else:
            st.warning("재무지표를 자동 추출하지 못했습니다. '공시 판정 계산' 메뉴에서 직접 입력하거나 DART 원본 PDF를 사용하세요.")

        st.markdown("---")
        st.markdown("### 추출된 재무지표")
        _display_metrics(ai_metrics)

        # 디버그: 원문 텍스트 확인 (패턴 개선용)
        with st.expander("🔍 원문 텍스트 확인 (패턴 디버그)", expanded=False):
            parser_dbg = AuditReportParser()
            lines_dbg = full_text.split('\n')
            multiplier_dbg = parser_dbg._detect_unit(full_text)
            unit_label = {1: "원", 1_000: "천원", 1_000_000: "백만원"}.get(multiplier_dbg, f"×{multiplier_dbg}")
            st.info(f"감지된 단위: **{unit_label}** (multiplier={multiplier_dbg:,})")

            keywords = ['매출액', '자산총계', '자본총계', '유동자산', '유동부채', '결손금', '자본금', '단위']
            matched_lines = []
            for i, line in enumerate(lines_dbg):
                if any(kw in line for kw in keywords):
                    start = max(0, i - 1)
                    end = min(len(lines_dbg), i + 5)
                    block = '\n'.join(f"[{j}] {lines_dbg[j]}" for j in range(start, end))
                    matched_lines.append(block + "\n---")
            st.code('\n'.join(matched_lines[:40]) if matched_lines else "키워드 미발견")

        st.session_state['extracted_metrics'] = ai_metrics

        # 저장
        st.markdown("---")
        col_save, col_apply = st.columns(2)
        with col_save:
            save_name = report_name.strip() or uploaded_file.name.replace(".pdf", "")
            if st.button("보고서 저장 (다음부터 재업로드 불필요)", type="primary", key="save_report"):
                _save_report_entry(save_name, report_type, ai_metrics)
                st.success(f"'{save_name}' 저장 완료! '저장된 보고서' 탭에서 언제든 불러올 수 있습니다.")
                st.rerun()
        with col_apply:
            st.info("지표가 세션에 적용됐습니다. 저장 없이 '공시 판정 계산' 메뉴를 바로 사용할 수도 있습니다.")

        # ── 바로 공시 판정 계산 ───────────────────────────
        st.markdown("---")
        st.markdown("### 바로 공시 판정 계산")

        col1, col2 = st.columns(2)
        with col1:
            transaction_uk = st.number_input("거래액 (억원)", min_value=0, value=0, step=1, format="%d", key="pdf_tx")
        with col2:
            market = st.selectbox("적용 시장", ["KOSPI", "KOSDAQ"], key="pdf_market")

        if st.button("공시 판정 계산", type="primary", key="pdf_calc"):
            if transaction_uk == 0:
                st.warning("거래액을 입력해 주세요.")
                return

            sales        = ai_metrics.get('sales') or 0
            total_assets = ai_metrics.get('total_assets') or 0
            equity       = ai_metrics.get('equity') or 0

            if sales == 0 and total_assets == 0 and equity == 0:
                st.error("재무지표가 추출되지 않아 계산할 수 없습니다. PDF를 확인해주세요.")
                return

            db  = load_database()
            eng = load_calculation_engine(db)
            metrics_obj = FinancialMetrics(
                sales=Decimal(str(sales)),
                total_assets=Decimal(str(total_assets)),
                equity=Decimal(str(equity)),
                current_assets=Decimal(str(ai_metrics.get('current_assets') or 0)),
                current_liabilities=Decimal(str(ai_metrics.get('current_liabilities') or 0)),
                accumulated_loss=Decimal(str(ai_metrics.get('accumulated_loss') or 0)),
            )
            tx = Decimal(str(transaction_uk * UNIT))
            results = eng.calculate(metrics_obj, tx, market=market.lower())
            summary = eng.get_summary(results)

            st.markdown("#### 판정 결과 요약")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("검토 규칙", summary['total_rules_checked'])
            c2.metric("공시 대상", summary['disclosure_required'])
            c3.metric("검토 필요", summary['review_required'])
            c4.metric("공시 미대상", summary['no_disclosure'])

            st.markdown("#### 상세 결과")
            for r in results:
                if r.result == DisclosureResult.DISCLOSURE_REQUIRED:
                    tag = "🔴 공시 대상"
                elif r.result == DisclosureResult.REVIEW_REQUIRED:
                    tag = "🟡 검토 필요"
                else:
                    tag = "🟢 공시 미대상"
                with st.expander(f"{tag}  {r.rule['title']}"):
                    st.write(f"**기준액**: {int(r.threshold_amount) // UNIT:,}억원")
                    st.write(f"**거래액**: {transaction_uk:,}억원")
                    st.write(f"**비율**: {float(r.ratio):.1%}")
                    st.write(f"**근거**: {r.reason}")




def show_ai_advisor():
    """AI 공시 어드바이저 채팅 페이지"""
    st.markdown("""
    <div class="dart-card">
        <div class="dart-card-title">AI 공시 어드바이저</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="section-header">AI 공시 어드바이저</div>', unsafe_allow_html=True)

    st.markdown("""
<div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #10B981;
border-radius:8px;padding:16px 20px;margin-bottom:20px">
<div style="color:#FFFFFF;font-weight:700;margin-bottom:10px">📋 AI 공시 어드바이저 사용 방법</div>
<div style="color:#AAAAAA;font-size:0.88rem;line-height:2">
<b style="color:#E0E0E0">자유로운 질문</b> — 공시 규정, 절차, 기한 등 궁금한 사항을 채팅 형식으로 질문하세요.<br>
<b style="color:#E0E0E0">질문 예시</b> — "대표이사 변경 시 공시 의무는?", "매출액 5% 이상 계약 체결 시 기한은?", "CB 발행 공시 절차 알려줘"<br>
<b style="color:#E0E0E0">규정 근거 제시</b> — 관련 공시 규칙명과 기준을 함께 답변하므로 실무 검토 자료로 활용할 수 있습니다.<br>
<span style="color:#EF4444">⚠ AI 답변은 참고용이며, 최종 공시 여부는 반드시 공시책임자·거래소 담당자와 확인하세요.</span>
</div>
</div>
""", unsafe_allow_html=True)

    st.info("공시 규정이나 기업 공시 사례에 대해 궁금한 점을 물어보세요. (예: 대표이사 변경 시 공시 의무는?)")
    
    # 채팅 기록 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 대화 내용 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("공시 관련 질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("AI가 답변을 생성 중입니다..."):
                try:
                    # AI Advisor 모듈 호출
                    from core.ai_advisor import DisclosureAIAdvisor
                    advisor = DisclosureAIAdvisor()
                    response = advisor.ask(prompt, st.session_state.messages[:-1])
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"답변 생성 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
