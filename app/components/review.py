import streamlit as st
from core.pdf_reader import render_page
from app.state import widget_key

def show_review(report):
    st.subheader("STEP 2. 문서 인식 결과 확인")
    left,right=st.columns([1,1])
    with left:
        docs=st.session_state.documents
        if docs:
            doc_id=st.selectbox("원본 문서",list(docs),format_func=lambda k:docs[k]["name"]+" / "+k)
            doc=docs[doc_id]
            for warning in doc.get("warnings",[]): st.warning(warning)
            from core.pdf_reader import open_pdf
            with open_pdf(doc["data"]) as pdf: count=len(pdf)
            page=st.number_input("근거 페이지 이동",1,count,1)
            st.image(render_page(doc["data"],page),caption=f"{doc['name']} · {page}페이지",width="stretch")
            for result in doc["pages"]:
                if result.number==page:
                    st.caption(f"{'OCR' if result.ocr else '원본 텍스트'} / 회전 보정 {result.rotation}도 / 신뢰도 {result.confidence if result.confidence is not None else '제공 안 됨'}")
                    if result.error: st.error(result.error)
        else: st.info("가상 사례를 불러오거나 PDF를 업로드하세요.")
    with right:
        st.caption("후보 수정은 아래 표에서, 결과서에 들어갈 값은 STEP 3에서 확정하세요. 소유권 이력과 현재 소유자 판단은 원본 대조가 필요합니다.")
        if report.facts:
            rows=[{"항목":f.field,"후보값":f.value,"상태":f.status,"문서":f.evidence.document_id,"페이지":f.evidence.page,"좌표":str(f.evidence.bbox),"원문":f.raw} for f in report.facts]
            edited=st.data_editor(rows,disabled=["항목","문서","페이지","좌표","원문"],hide_index=True,key=widget_key("facts"),column_config={"상태":st.column_config.SelectboxColumn(options=["추출됨","사용자 확인 필요","누락","충돌","사용자 확정"])})
            for fact,row in zip(report.facts,edited): fact.value=row["후보값"];fact.status=row["상태"]
        if report.rights:
            with st.expander("권리별 근거 원문 및 연결 관계"):
                for r in report.rights:
                    st.write(f"{r.document_id} / {r.section} / {r.rank} / {r.kind} / {r.cancellation}")
                    for ev in r.evidence:
                        st.caption(f"근거 {ev.page}페이지 · 좌표 {ev.bbox}")
                        st.code(ev.text,language=None)
        report.registry_reviewed=st.checkbox("모든 문서의 권리 유무·소유권 이력·후보 충돌·미인식 페이지를 원본과 대조했습니다",value=report.registry_reviewed,key=widget_key("registry_checked"))
