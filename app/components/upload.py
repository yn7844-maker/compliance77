from pathlib import Path
import streamlit as st
from core.pdf_reader import inspect_pdf,read_pdf,MAX_FILES,MAX_TOTAL_BYTES
from core.registry_parser import parse_registry
from core.field_mapper import suggest
from models.schemas import Report
from app.state import load_report

ROOT=Path(__file__).resolve().parents[2]

def render_upload():
    st.subheader('STEP 1. 평가 유형 및 문서 업로드')
    typ=st.radio('평가 유형',['토지·건물','집합건물'],horizontal=True)
    sample=st.selectbox('가상 완성 패키지',['선택 안 함','case01','case03'])
    if st.button('가상 패키지 불러오기',disabled=sample=='선택 안 함'):
        r=Report.model_validate_json((ROOT/'sample_data/expected'/f'{sample}_report.json').read_text())
        load_report(r)
        paths=sorted((ROOT/'sample_data/pdf').glob(f'{sample}_*.pdf'))
        st.session_state.documents={p.name:p.read_bytes() for p in paths if 'scan' not in p.name}
        st.session_state.extractions=[]
        for name,data in st.session_state.documents.items():
            st.session_state.extractions.append(parse_registry(read_pdf(data,name),name))
        st.session_state.analysis_kind=r.evaluation_type
        st.rerun()
    uploaded=st.file_uploader('등기부등본 PDF (여러 파일 가능)',type=['pdf'],accept_multiple_files=True)
    extra=st.file_uploader('추가 증빙 PDF (자동 인식하지 않고 첨부 여부 관리)',type=['pdf'],accept_multiple_files=True)
    registry={};attachments={};valid=True
    files=(uploaded or [])+(extra or [])
    if len(files)>MAX_FILES or sum(f.size for f in files)>MAX_TOTAL_BYTES:
        st.error('평가 건당 최대 12개, 합산 60MB입니다.');valid=False
    if len({f.name for f in files})!=len(files):
        st.error('중복 파일명이 있습니다. 파일명을 구분하세요.');valid=False
    if valid:
        for items,dest in [(uploaded,registry),(extra,attachments)]:
            for f in items or []:
                try:
                    data=f.getvalue();meta=inspect_pdf(data,f.name);st.write(meta);dest[f.name]=data
                except ValueError as exc: st.error(str(exc));valid=False
    ocr=st.checkbox('텍스트 품질이 낮은 페이지에 로컬 OCR 사용',value=True)
    if st.button('문서 분석 시작',disabled=not registry or not valid):
        r=Report(evaluation_type=typ,attachments=list(attachments))
        st.session_state.extractions=[]
        with st.spinner('페이지별 텍스트 추출 및 OCR 처리 중…'):
            for name,data in registry.items():
                ex=parse_registry(read_pdf(data,name,use_ocr=ocr),name)
                st.session_state.extractions.append(ex)
                # 파일명으로 유형을 확정하지 않고 문서 표제부의 명시적 표시를 우선한다.
                alltext=''.join(p.text for p in ex.pages[:2])
                kind='집합건물' if typ=='집합건물' else ('건물' if '[건물]' in alltext or '【건물】' in alltext else '토지')
                target,val=suggest(ex,kind);r.targets.append(target);r.valuations.append(val)
                r.rights.extend(ex.rights);r.extraction_issues.extend(ex.issues)
        st.session_state.documents={**registry,**attachments}
        st.session_state.analysis_kind=typ
        load_report(r);st.rerun()
    if st.session_state.get('analysis_kind') and typ!=st.session_state.analysis_kind:
        st.info(f'현재 작성 중인 자료의 평가 유형은 {st.session_state.analysis_kind}입니다. 유형 변경은 문서 재분석 시 반영됩니다.')
