import streamlit as st
from pydantic import ValidationError
from app.state import initialize, record_changes
from app.components.upload import show_upload
from app.components.review import show_review
from app.components.report_form import show_form
from app.components.report_preview import show_preview

st.set_page_config(page_title="담보평가결과서 자동작성 시스템",layout="wide")
initialize()
if st.session_state.pop("clear_confirm_next",False):
    st.session_state[st.session_state.revision+"final_checked"]=False
st.caption("준법지원팀 업무지원 PoC")
st.title("담보평가결과서 자동작성 시스템")
st.info("가상 데이터 전용 시연입니다. 실제 등기부등본은 사내 보안 검토 및 승인된 배포 환경에서만 처리하세요. 외부 AI·OCR API를 호출하지 않습니다.")
show_upload()
r=st.session_state.report
before=r.model_copy(deep=True)
try:
    show_review(r)
    show_form(r)
    record_changes(before,r)
    changed=before.model_dump(exclude={"audit","confirmed"})!=r.model_dump(exclude={"audit","confirmed"})
    if before.confirmed and changed:
        r.confirmed=False
        st.session_state.clear_confirm_next=True
        st.warning("내용이 변경되어 최종 확인을 해제했습니다. 다음 화면 갱신 후 다시 확인하세요.")
    show_preview(r)
except (ValueError,ValidationError,TypeError):
    st.error("입력값을 확인하세요. 금액·면적은 0 이상의 숫자, 점포수는 정수로 입력해야 합니다. 잘못된 입력이 있는 동안 문서를 생성하지 않습니다.")
