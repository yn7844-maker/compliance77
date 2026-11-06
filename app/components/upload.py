from pathlib import Path
import streamlit as st
from models.schemas import Report
from core.pdf_reader import read_pdf, render_page, document_id, safe_filename, open_pdf
from core.ocr_engine import TesseractEngine, PaddleEngine
from core.registry_parser import parse_registry
from core.field_mapper import map_registries
from app.state import replace_report, widget_key
from config.calculation_rules import MAX_FILES, MAX_TOTAL_BYTES

ROOT=Path(__file__).resolve().parents[2]

def show_upload():
    st.subheader("STEP 1. 평가 유형 및 문서 업로드")
    kind=st.selectbox("평가 유형",["토지·건물","집합건물"],index=0 if st.session_state.report.evaluation_type=="토지·건물" else 1,key=widget_key("evaltype"))
    if st.session_state.report.evaluation_type!=kind:
        st.session_state.report.confirmed=False
        st.session_state.clear_confirm_next=True
    st.session_state.report.evaluation_type=kind
    a,b=st.columns(2)
    with a:
        sample=st.selectbox("가상 완성 패키지",["package_01","package_03"])
        if st.button("가상 사례 불러오기"):
            path=ROOT/"sample_data/packages"/(sample+".json")
            r=Report.model_validate_json(path.read_text())
            docs={}
            for name in r.attachments:
                p=ROOT/"sample_data/pdf"/name
                if p.exists():
                    data=p.read_bytes();pages=read_pdf(data)
                    docs[document_id(data)]={"name":name,"data":data,"pages":pages}
            # 완성 패키지를 불러와도 담당자의 재확인은 필요하다.
            r.confirmed=False
            replace_report(r,docs);st.rerun()
    with b:
        if st.button("새 평가 / 세션 자료 삭제"):
            st.session_state.clear();st.rerun()
    files=st.file_uploader("등기부등본 PDF (여러 필지·토지와 건물 별도 파일 지원)",type=["pdf"],accept_multiple_files=True,key=widget_key("registries"))
    extras=st.file_uploader("추가 증빙자료 PDF (업로드·검토 상태만 관리)",type=["pdf"],accept_multiple_files=True,key=widget_key("extras"))
    engine_name=st.selectbox("로컬 OCR 엔진",["Tesseract","PaddleOCR (별도 설치)"])
    engine=None
    if engine_name.startswith("Paddle"):
        with st.expander("Paddle 로컬 모델 경로"):
            det=st.text_input("검출 모델 폴더");rec=st.text_input("한국어 인식 모델 폴더");cls=st.text_input("방향 분류 모델 폴더")
    if files or extras:
        try:
            if len(files)+len(extras)>MAX_FILES: raise ValueError("파일은 합계 10개까지 허용합니다")
            if sum(f.size for f in files+extras)>MAX_TOTAL_BYTES: raise ValueError("한 평가의 업로드 합계는 60MB 이하입니다")
            inventory=[]
            for f in files+extras:
                data=f.getvalue()
                with open_pdf(data) as pdf:
                    count=sum(sum(c.isalnum() for c in p.get_text())>=25 for p in pdf)
                    inventory.append({"파일":safe_filename(f.name),"유형":"등기" if f in files else "증빙","페이지":len(pdf),"텍스트 페이지":count,"OCR 후보 페이지":len(pdf)-count})
            st.dataframe(inventory,hide_index=True)
        except ValueError as exc:
            st.error(str(exc));return
    if st.button("문서 분석 시작",disabled=not files,type="primary"):
        try:
            engine=PaddleEngine(det,rec,cls) if engine_name.startswith("Paddle") else TesseractEngine()
            registries=[];documents={}
            progress=st.progress(0)
            for i,f in enumerate(files):
                data=f.getvalue();doc_id=document_id(data)
                if doc_id in documents: continue
                pages=read_pdf(data,engine);parsed=parse_registry(pages,doc_id)
                documents[doc_id]={"name":safe_filename(f.name),"data":data,"pages":pages,"warnings":parsed.warnings}
                registries.append(parsed)
                for warning in parsed.warnings: st.warning(warning)
                progress.progress((i+1)/len(files))
            report=map_registries(registries,kind)
            report.attachments=[safe_filename(f.name) for f in files+extras]
            for f in extras:
                data=f.getvalue()
                documents[document_id(data)]={"name":safe_filename(f.name),"data":data,"pages":[],"supplement":True}
            replace_report(report,documents);st.rerun()
        except Exception:
            st.error("분석을 완료하지 못했습니다. OCR 설치·모델 경로를 확인하거나 PDF를 다시 선택하세요. 텍스트형 PDF는 Tesseract 미설치 환경에서도 지원합니다.")
