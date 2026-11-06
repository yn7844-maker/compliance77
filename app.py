import time
import streamlit as st
from pydantic import ValidationError
from app.state import initialize
from app.components.upload import render_upload
from app.components.review import render_review
from app.components.report_form import render_form
from app.components.report_preview import render_preview
from models.schemas import Report

st.set_page_config(page_title='담보평가결과서 자동작성 시스템',layout='wide')
initialize()
st.caption('준법지원팀 업무지원 PoC')
st.title('담보평가결과서 자동작성 시스템')
st.info('가상 데이터 전용 시연입니다. 실제 등기부등본은 사내 보안 검토 및 승인된 환경에서만 처리하세요. 외부 AI·OCR API를 사용하지 않습니다.')
if st.sidebar.button('현재 세션 자료 지우기'):
    st.session_state.clear();st.rerun()
st.sidebar.caption('업로드 원문은 세션 메모리에서만 처리합니다. 브라우저를 닫기 전 자료 지우기를 권장합니다.')
render_upload()
render_review()
st.subheader('STEP 3. 담보평가결과서 작성')
seed=Report.model_validate(st.session_state.seed)
try:
    report=render_form(seed)
except (ValueError,ValidationError) as exc:
    st.error(f'입력 형식을 확인하세요: {exc}');st.stop()
# 원본 제안과 수정 결과를 세션 내부에서 분리 보존 (외부 저장·로그 출력 없음)
before=seed.model_dump(mode='json');after=report.model_dump(mode='json')
changed=[k for k in after if k not in ['reviewed'] and after[k]!=before[k]]
st.session_state.audit=[{'field':k,'source':'사용자 수정','original':before[k],'current':after[k]} for k in changed]
with st.expander('자동 제안과 담당자 수정 구분 / 세션 지표'):
    st.write('수정된 영역:',changed)
    st.write({'수정 영역 수':len(changed),'경과 초':round(time.monotonic()-st.session_state.started,1),'다운로드 클릭 수':st.session_state.downloads})
    st.json(st.session_state.audit)
render_preview(report)
