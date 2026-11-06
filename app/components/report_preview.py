import streamlit as st
from io import BytesIO
from time import monotonic
from docx import Document
from core.validation import validate_report
from core.word_generator import generate_word, download_filename

def show_preview(report):
    st.subheader("STEP 4. 검증 및 미리보기")
    errors=validate_report(report)
    if errors:
        st.warning("미확정 문서는 초안으로만 다운로드할 수 있습니다.")
        for error in errors: st.write("• "+error)
    else: st.success("필수값·공제 검토·계산 검증 완료. 최종 Word를 생성할 수 있습니다.")
    empty=st.selectbox("해당 없는 평가유형 표",["유지","데이터 행 제거"])
    draft=st.radio("다운로드 구분",["초안","최종"],horizontal=True)=="초안"
    try:
        word=generate_word(report,draft=draft,empty_tables="유지" if empty=="유지" else "제거") if draft or not errors else None
        if word:
            st.session_state.word_success+=1
            with st.expander("Word 내용 미리보기 (실제 페이지 배치는 Word에서 확인)"):
                doc=Document(BytesIO(word))
                for paragraph in doc.paragraphs:
                    if paragraph.text: st.write(paragraph.text)
                for i,table in enumerate(doc.tables):
                    st.caption(f"표 {i+1}")
                    st.table([[c.text for c in row.cells] for row in table.rows])
            st.subheader("STEP 5. Word 다운로드")
            def downloaded():
                st.session_state.downloads+=1
            st.download_button("담보평가결과서 다운로드",data=word,file_name=download_filename(report,draft),mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",on_click=downloaded,type="primary")
        elif not draft: st.error("최종 문서 생성이 차단되었습니다. 위 검증 항목을 확인하세요.")
    except Exception:
        st.session_state.word_failures+=1
        st.error("Word 생성 실패: 템플릿 구조 및 입력값을 확인하세요.")
    with st.expander("담당자 수정 이력 및 세션 지표"):
        st.metric("수정 기록 수",len(report.audit))
        st.metric("현재 세션 경과 (초)",int(monotonic()-st.session_state.started))
        st.write({"다운로드 버튼 클릭":st.session_state.downloads,"Word 생성 성공":st.session_state.word_success,"Word 생성 오류":st.session_state.word_failures})
        st.caption("브라우저 저장 완료는 서버에서 확인할 수 없습니다. 다운로드 클릭 수는 실제 저장 성공률과 다릅니다.")
        st.dataframe([a.model_dump() for a in report.audit],hide_index=True)
