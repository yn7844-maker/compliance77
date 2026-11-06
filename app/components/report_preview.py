from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import time
import streamlit as st
from docx import Document
from core.validation import validate_report
from core.word_generator import generate_word
from app.state import fingerprint

def render_preview(report):
    st.subheader('담보평가결과서')
    digest=fingerprint(report)
    report.reviewed=st.checkbox('현재 입력과 원본 대조를 완료했으며 담당자로서 최종 확인합니다',key=f'final_review:{digest}')
    errors=validate_report(report)
    if errors:
        st.warning('검토 미완료 — 초안만 다운로드할 수 있습니다.')
        with st.expander(f'담당자 확인이 필요한 항목 {len(errors)}개'):
            for error in errors: st.write('• '+error)
    else: st.success('필수 입력 및 담당자 확인 완료')
    final=not errors and report.completion=='최종'
    try:
        data=generate_word(report,final=final)
    except (ValueError,OSError) as exc:
        st.error(str(exc))
        return
    name=re.sub(r'[^가-힣a-zA-Z0-9_-]','_',report.store or '미입력')[:50]
    stamp=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')
    status='' if final else '_초안'
    def downloaded():
        st.session_state.downloads+=1
        st.session_state.last_download_seconds=time.monotonic()-st.session_state.started
    st.download_button('담보평가결과서 다운로드' if final else '담보평가결과서 초안 다운로드',data,
                       file_name=f'담보평가결과서_{name}_{stamp}{status}.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',on_click=downloaded)
    st.caption('다운로드 클릭 수는 브라우저 파일 저장 성공을 보장하지 않습니다.')
    with st.expander('Word 내용 미리보기 (실제 생성 파일의 편집 가능한 표)',expanded=False):
        doc=Document(BytesIO(data))
        for paragraph in doc.paragraphs:
            if paragraph.text: st.write(paragraph.text)
        for i,table in enumerate(doc.tables,1):
            st.caption(f'표 {i}')
            import pandas as pd
            st.dataframe(pd.DataFrame([[c.text for c in row.cells] for row in table.rows[1:]],columns=[c.text for c in table.rows[0].cells]),hide_index=True)
