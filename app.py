import streamlit as st
from pydantic import ValidationError
from app.state import initialize, record_changes
from app.components.upload import show_upload
from app.components.review import show_review
from app.components.report_form import show_form
from app.components.report_preview import show_preview
from app.components.dashboard import apply_style, show_dashboard

st.set_page_config(page_title="담보평가결과서 자동작성 시스템",layout="wide")
initialize()
if st.session_state.pop("clear_confirm_next",False):
    st.session_state[st.session_state.revision+"final_checked"]=False
apply_style()
with st.sidebar:
    st.markdown("### C77 · 준법지원")
    st.caption("담보평가 업무지원")
    st.markdown('<a href="#evaluation">▦ 평가 대시보드</a><a href="#workspace">▤ 문서 검토·결과서 작성</a>', unsafe_allow_html=True)
    st.divider()
    st.caption("로컬 규칙 기반 추출")
    st.caption("담당자 검토 후 Word 출력")
st.markdown('<div id="evaluation"></div>', unsafe_allow_html=True)
st.caption("준법지원팀 업무지원 PoC")
st.title("담보평가결과서 자동작성 시스템")
st.info("가상 데이터 전용 시연입니다. 실제 등기부등본은 사내 보안 검토 및 승인된 배포 환경에서만 처리하세요. 외부 AI·OCR API를 호출하지 않습니다.")
dashboard = st.container()
st.markdown('<div id="workspace"></div>', unsafe_allow_html=True)
upload_tab, review_tab, form_tab, output_tab = st.tabs(["문서 업로드", "원본 대조", "결과서 수정", "Word 출력"])
with upload_tab:
    show_upload()
r=st.session_state.report
before=r.model_copy(deep=True)
try:
    with review_tab:
        show_review(r)
    with form_tab:
        show_form(r)
    record_changes(before,r)
    changed=before.model_dump(exclude={"audit","confirmed"})!=r.model_dump(exclude={"audit","confirmed"})
    if before.confirmed and changed:
        r.confirmed=False
        st.session_state.clear_confirm_next=True
        st.warning("내용이 변경되어 최종 확인을 해제했습니다. 다음 화면 갱신 후 다시 확인하세요.")
    with output_tab:
        show_preview(r)
    with dashboard:
        show_dashboard(r)
except (ValueError,ValidationError,TypeError):
    st.error("입력값을 확인하세요. 금액·면적은 0 이상의 숫자, 점포수는 정수로 입력해야 합니다. 잘못된 입력이 있는 동안 문서를 생성하지 않습니다.")
