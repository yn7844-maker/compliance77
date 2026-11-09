"""Presentation only: all amounts and checks come from existing business logic."""
from html import escape
from base64 import b64encode
from pathlib import Path
from functools import lru_cache
import streamlit as st
from core.collateral_calculator import calculate, fmt
from core.validation import validate_report


@lru_cache(maxsize=1)
def font_css():
    font = Path(__file__).resolve().parents[2] / "fonts" / "PretendardVariable.woff2"
    encoded = b64encode(font.read_bytes()).decode("ascii")
    return "<style>@font-face{font-family:Pretendard;src:url(data:font/woff2;base64," + encoded + ") format('woff2');font-weight:100 900;font-display:swap}</style>"


def apply_style():
    st.markdown(font_css(), unsafe_allow_html=True)
    st.markdown('''<style>
    html, body, [class*="css"], .stApp, button, input, textarea,
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stMetric"], [data-testid="stDataFrame"] {
      font-family: Pretendard, "SUIT", -apple-system, BlinkMacSystemFont,
      "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
      letter-spacing: -.025em;
    }
    .stApp {background:#f3f5f5;color:#17252d}
    .block-container {padding-top:2rem;padding-bottom:3rem;max-width:1600px}
    h1 {font-size:1.85rem!important;letter-spacing:-.05em!important}
    h2,h3 {letter-spacing:-.035em!important}
    [data-testid="stSidebar"] {background:#141d3b}
    [data-testid="stSidebar"] * {color:#edf1fc}
    [data-testid="stSidebar"] a {color:#edf1fc!important;text-decoration:none;display:block;padding:12px 16px;
      margin:8px 0;border-radius:12px;background:#ffffff0c;font-weight:600}
    [data-testid="stSidebar"] a:hover {background:#ffffff20}
    [data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:18px!important}
    [data-testid="stMetric"] {background:#f1f4f5;border-radius:14px;padding:16px}
    [data-testid="stMetricValue"] {font-size:1.65rem;font-weight:750}
    [data-testid="stTabs"] [role="tablist"] {gap:20px;border-bottom:1px solid #e0e5e7}
    [data-testid="stTabs"] [role="tab"] {font-weight:650;padding:12px 4px}
    [data-testid="stExpander"] {background:white;border-radius:14px}
    .stButton button,.stDownloadButton button {border-radius:10px;font-weight:650}
    .st-key-summary, .st-key-review_status {background:white;border-radius:18px}
    .dashboard-card {background:white;border:1px solid #e0e5e7;border-radius:18px;padding:22px;
      margin-bottom:16px;min-width:0}
    .dashboard-card h3 {font-size:1.1rem;margin:0 0 16px}
    .dashboard-card p {color:#697981;font-size:.88rem}
    .status-pill {display:inline-block;background:#eef1fc;color:#303f80;
      padding:6px 12px;border-radius:8px;font-size:.85rem;font-weight:650}
    .rights-table {width:100%;border-collapse:collapse;font-size:.87rem}
    .rights-table th {text-align:left;color:#697981;background:#f3f5f5}
    .rights-table td,.rights-table th {padding:12px 8px;border-bottom:1px solid #e7ebec;
      overflow-wrap:anywhere}
    @media(max-width:800px) {.block-container{padding:1.2rem}.dashboard-card{padding:16px}}
    </style>''', unsafe_allow_html=True)


def show_dashboard(report):
    totals = calculate(report)
    errors = validate_report(report)
    left, right = st.columns([2.3, 1], gap="large")
    with left:
        st.caption("평가 대상")
        st.subheader(report.request.store or "새 담보평가")
        st.caption(" · ".join(t.address for t in report.targets if t.address) or "문서를 불러오면 평가 대상이 표시됩니다.")
        table, summary = st.columns([1.25, 1], gap="medium")
        with table:
            rows = "".join(
                "<tr>" + "".join(f"<td>{escape(str(value or '—'))}</td>" for value in
                (r.section, r.rank, r.received, r.kind, r.creditor, r.cancellation)) + "</tr>"
                for r in report.rights
            )
            if not rows:
                rows = '<tr><td colspan="6">등록된 권리가 없습니다. 문서 업로드 후 원본을 확인하세요.</td></tr>'
            st.markdown('<div class="dashboard-card"><h3>등기 권리내역</h3><div style="overflow-x:auto">'
                        '<table class="rights-table"><thead><tr><th>구역</th><th>순위</th><th>접수일</th>'
                        '<th>등기 목적</th><th>권리자</th><th>상태</th></tr></thead><tbody>' + rows +
                        '</tbody></table></div><p>추출·입력된 내역입니다. 유효성과 공제 여부는 담당자 확인이 필요합니다.</p></div>',
                        unsafe_allow_html=True)
        with summary:
            with st.container(border=True, key="summary"):
                st.subheader("담보평가 요약")
                st.caption("금액 단위: 천원 · 담당자 확인값 기준")
                st.metric("최종담보가치", fmt(totals.collateral))
                a, b = st.columns(2)
                a.metric("평가금액", fmt(totals.valuation))
                b.metric("선순위 공제", fmt(totals.senior))
                a.metric("임차보증금 공제", fmt(totals.deposits))
                b.metric("담보여력", fmt(totals.capacity))
                st.caption("최종담보가치 = 평가금액 − 선순위 공제 − 임차보증금 공제")
                st.caption("담보여력은 자동 승인 판단이 아닙니다.")
    with right:
        with st.container(border=True, key="review_status"):
            st.subheader("검토 현황")
            st.markdown('<span class="status-pill">' + ("확인 필요" if errors else "최종 출력 가능") + '</span>', unsafe_allow_html=True)
            st.caption("필수 입력 및 담당자 확인 상태")
            if errors:
                for error in errors:
                    st.write("• " + error)
            else:
                st.success("필수값·공제 검토·계산 검증 완료")
            st.caption("아래 ‘원본 대조’와 ‘결과서 수정’에서 확인하고 ‘Word 출력’에서 다운로드하세요.")
