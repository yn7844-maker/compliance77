from pathlib import Path
import streamlit as st
from core.pdf_reader import inspect_pdf,read_pdf,MAX_FILES,MAX_TOTAL_BYTES
from core.registry_parser import parse_registry
from core.quick_report import parse_text,prepare_report,MAX_TEXT_CHARS
from models.schemas import Report
from app.state import load_report

ROOT=Path(__file__).resolve().parents[2]

def render_upload():
    typ=st.radio('평가 유형',['토지·건물','집합건물'],horizontal=True)
    mode=st.radio('자료 입력 방법',['파일 업로드','텍스트 붙여넣기'],horizontal=True)
    uploaded=[];text=''
    if mode=='파일 업로드':
        uploaded=st.file_uploader('등기부등본 PDF 또는 TXT를 넣어 주세요',type=['pdf','txt'],accept_multiple_files=True) or []
    else:
        text=st.text_area('등기부등본 텍스트',height=200,max_chars=MAX_TEXT_CHARS,placeholder='표제부·갑구·을구 내용을 그대로 붙여넣으세요.')
    with st.expander('추가 증빙 및 분석 설정'):
        extra=st.file_uploader('추가 증빙 PDF (첨부 여부 관리)',type=['pdf'],accept_multiple_files=True) or []
        ocr=st.checkbox('텍스트 품질이 낮은 페이지에 로컬 OCR 사용',value=True)
    if st.button('결과서 초안 자동작성',type='primary',disabled=not (uploaded or text.strip())):
        files=uploaded+extra
        try:
            if len(files)>MAX_FILES or sum(f.size for f in files)>MAX_TOTAL_BYTES: raise ValueError('평가 건당 최대 12개, 합산 60MB입니다.')
            if len({f.name for f in files})!=len(files): raise ValueError('중복 파일명을 구분해 주세요.')
            documents={};extractions=[];metadata=[]
            with st.spinner('자료를 읽고 결과서 초안을 작성하고 있습니다…'):
                for f in uploaded:
                    data=f.getvalue()
                    if f.name.lower().endswith('.txt'):
                        from core.pdf_reader import validate_filename,MAX_BYTES
                        # PDF와 같은 경로·파일명 검사 사용
                        validate_filename(f.name[:-4]+'.pdf')
                        if len(data)>MAX_BYTES: raise ValueError('파일당 최대 20MB입니다.')
                        try: decoded=data.decode('utf-8-sig')
                        except UnicodeDecodeError:
                            try: decoded=data.decode('cp949')
                            except UnicodeDecodeError: raise ValueError('TXT를 읽을 수 없습니다. 승인된 텍스트를 직접 붙여넣거나 UTF-8 TXT를 사용하세요.') from None
                        ex=parse_text(decoded,f.name)
                        metadata.append({'파일명':f.name,'페이지 수':len(ex.pages),'유형':'텍스트'})
                    else:
                        meta=inspect_pdf(data,f.name);metadata.append(meta)
                        ex=parse_registry(read_pdf(data,f.name,use_ocr=ocr),f.name);documents[f.name]=data
                    extractions.append(ex)
                if mode=='텍스트 붙여넣기': extractions.append(parse_text(text))
                for f in extra:
                    data=f.getvalue();metadata.append(inspect_pdf(data,f.name));documents[f.name]=data
                report=prepare_report(extractions,typ,[f.name for f in extra])
            st.session_state.documents=documents
            st.session_state.extractions=extractions
            st.session_state.input_metadata=metadata
            st.session_state.analysis_kind=typ
            load_report(report);st.rerun()
        except ValueError as exc: st.error(str(exc))
    with st.expander('가상 데이터로 바로 체험 / 직접 작성'):
        sample=st.selectbox('가상 완성 패키지',['선택 안 함','case01','case03'])
        if st.button('가상 패키지 불러오기',disabled=sample=='선택 안 함'):
            try:
                r=Report.model_validate_json((ROOT/'sample_data/expected'/f'{sample}_report.json').read_text(encoding='utf-8'))
                docs={p.name:p.read_bytes() for p in sorted((ROOT/'sample_data/pdf').glob(f'{sample}_*.pdf')) if 'scan' not in p.name}
                exs=[parse_registry(read_pdf(data,name),name) for name,data in docs.items()]
                st.session_state.documents=docs;st.session_state.extractions=exs
                st.session_state.analysis_kind=r.evaluation_type
                load_report(r);st.rerun()
            except (ValueError,OSError) as exc:
                st.error('가상 패키지를 읽을 수 없습니다. 파일 암호화·손상 여부를 확인하거나 텍스트 붙여넣기를 사용하세요.')
        if st.button('빈 결과서 직접 작성'):
            st.session_state.documents={};st.session_state.extractions=[]
            load_report(Report(evaluation_type=typ));st.rerun()
