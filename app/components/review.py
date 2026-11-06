import streamlit as st
from core.pdf_reader import page_image

def render_review():
    st.subheader('STEP 2. 문서 인식 결과 확인')
    docs=st.session_state.documents
    if not docs:
        st.info('PDF를 업로드하거나 가상 패키지를 불러오세요. 수동 작성도 가능합니다.');return
    name=st.selectbox('원본 문서',list(docs))
    ex=next((e for e in st.session_state.extractions if e.document==name),None)
    left,right=st.columns([1,1])
    with left:
        from core.pdf_reader import inspect_pdf
        count=inspect_pdf(docs[name],name)['페이지 수']
        page=st.number_input('페이지',min_value=1,max_value=count,step=1)
        st.image(page_image(docs[name],name,int(page)),caption=f'{name} · {page}페이지',width='stretch')
    with right:
        if ex:
            st.caption('추출 원본은 보존됩니다. 결과서에 쓰는 값·소유자·권리는 STEP 3에서 수정하세요. 부가 추출 필드도 아래에서 수정·확정 기록을 남길 수 있습니다.')
            st.dataframe([{'필드':c.field,'원문':c.raw,'제안값':c.value,'상태':c.status,'페이지':c.evidence.page,'좌표':str(c.evidence.bbox)} for c in ex.candidates],hide_index=True)
            with st.expander('추출 필드 전체 수정·확정 기록'):
                records=[{'필드':c.field,'원문':c.raw,'수정값':c.value,'상태':c.status,'페이지':c.evidence.page} for c in ex.candidates]
                edited=st.data_editor(records,disabled=['필드','원문','페이지'],column_config={'상태':st.column_config.SelectboxColumn(options=['추출됨','사용자 확인 필요','누락','충돌','사용자 확정'])},key=f'candidate_review:{st.session_state.revision}:{name}',hide_index=True)
                if 'candidate_reviews' not in st.session_state: st.session_state.candidate_reviews={}
                st.session_state.candidate_reviews[name]=edited
                st.caption('이 기록은 원본과 분리해 세션에 보관합니다. 결과서 표의 최종값은 STEP 3의 입력을 사용합니다.')
            st.write('소유자 후보 (과거 소유자 포함):',[(o.name,o.share) for o in ex.owners])
            st.dataframe([{'순위':x.rank,'접수일자':x.receipt_date,'권리종류':x.kind,'원 금액':str(x.amount_won),'원문 금액':x.amount_raw,'말소/변경':x.status,'근거 페이지':','.join(str(e.page) for e in x.evidence)} for x in ex.rights],hide_index=True)
            st.warning('\n\n'.join(ex.issues))
            with st.expander('페이지 원문·OCR 상태 및 좌표'):
                p=ex.pages[int(page)-1]
                st.write({'OCR':p.used_ocr,'신뢰도':p.confidence,'보정 회전':p.rotation,'오류':p.error})
                st.text(p.text);st.json(p.model_dump(mode='json')['blocks'])
        else: st.info('추가 증빙자료입니다. STEP 3에서 내용을 직접 반영하세요.')
