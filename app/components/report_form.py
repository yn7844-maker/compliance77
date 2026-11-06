import re
from decimal import Decimal, InvalidOperation
from uuid import uuid4
import streamlit as st
from models.schemas import Target, Owner, Valuation, Right
from config.field_options import REQUEST_TYPES, CONTRACTS, PURPOSES, PROPERTY_TYPES, DUPLICATE
from config.calculation_rules import WON_POLICIES
from core.collateral_calculator import calculate, fmt
from app.state import widget_key

def money(label,value,key):
    raw=st.text_input(label,value="" if value is None else str(value),key=widget_key(key))
    if not raw.strip(): return None
    try:
        value=Decimal(raw.replace(",",""))
        if not value.is_finite() or value<0: raise ValueError()
        return value
    except (InvalidOperation,ValueError): raise ValueError(label+": 0 이상의 유한한 숫자를 입력하세요") from None

def choose(label,options,value,key):
    return st.selectbox(label,options,index=options.index(value) if value in options else 0,key=widget_key(key))

def dec(x):
    if x is None or str(x).strip()=="": return None
    return Decimal(str(x).replace(",",""))

def editor(name,rows,columns,configs=None):
    # 숫자는 문자열로 받아 Decimal로 변환한다. 브라우저 float 왕복을 피한다.
    if not rows:
        rows=[{c:False if c in ["확인","선순위 공제","금액 해당 없음"] else "" for c in columns}]
    return st.data_editor(rows,num_rows="dynamic",hide_index=True,key=widget_key(name),column_config=configs or {})

def show_form(r):
    st.subheader("STEP 3. 담보평가결과서 작성")
    st.caption("금액은 모두 천원, 권리 원문금액만 원 단위입니다. 빈칸은 미확정이며 해당 없으면 명시적으로 입력하세요. 행 삭제는 왼쪽 행 선택 후 Delete를 사용하세요.")
    with st.expander("1. 의뢰내역",expanded=True):
        q=r.request
        a,b,c=st.columns(3)
        with a:
            q.repeat=choose("재의뢰 여부",REQUEST_TYPES,q.repeat,"repeat")
            q.store=st.text_input("점포명",q.store,key=widget_key("store"))
        with b:
            q.contract=choose("대상계약",CONTRACTS,q.contract,"contract")
            q.purpose=choose("평가목적",PURPOSES,q.purpose,"purpose")
        with c:
            q.amount=money("평가의뢰금액 (천원)",q.amount,"request_amount")
            r.written_on=st.date_input("작성일",r.written_on,key=widget_key("date"))
        q.considerations=st.text_area("평가 시 고려사항",q.considerations,key=widget_key("considerations"))
    with st.expander("2. 평가대상",expanded=True):
        st.caption("공동소유자는 이름 | 지분; 이름 | 지분처럼 세미콜론으로 구분합니다. 채무자는 별도로 확인하세요.")
        cols=["구분","소재지","채무자","소유자 및 지분","중복담보","관련점포"]
        rows=[dict(zip(cols,[x.kind,x.address,x.debtor,"; ".join(o.name+" | "+o.share for o in x.owners),x.duplicate,x.related_store])) for x in r.targets]
        out=editor("targets",rows,cols,{"구분":st.column_config.SelectboxColumn(options=PROPERTY_TYPES),"중복담보":st.column_config.SelectboxColumn(options=DUPLICATE)})
        targets=[]
        for x in out:
            if not x["소재지"] and not x["채무자"]: continue
            owners=[]
            for line in re.split(r"[;\n]+",str(x["소유자 및 지분"] or "")):
                name,_,share=line.partition("|")
                if name.strip(): owners.append(Owner(name=name.strip(),share=share.strip()))
            targets.append(Target(kind=x["구분"] or "기타",address=x["소재지"] or "",debtor=x["채무자"] or "",owners=owners,duplicate=x["중복담보"] or "미확인",related_store=x["관련점포"] or ""))
        r.targets=targets
    with st.expander("3. 평가결과",expanded=True):
        st.caption("토지·건물·집합건물 각각 다중 행을 지원합니다. 미확정 평가 산식은 실행하지 않으며 평가금액과 산정근거를 직접 입력합니다. 공시지가·적용율 빈칸은 직접평가 시 해당 없음으로 출력합니다.")
        cols=["유형","주소","지목","면적(m²)","공시지가","적용율(%)","평가금액","산정근거","확인"]
        rows=[dict(zip(cols,[v.kind,v.address,v.category,str(v.area) if v.area is not None else "",str(v.public_price) if v.public_price is not None else "",str(v.rate) if v.rate is not None else "",str(v.amount) if v.amount is not None else "",v.basis,v.reviewed])) for v in r.valuations]
        out=editor("valuations",rows,cols,{"유형":st.column_config.SelectboxColumn(options=["토지","건물","집합건물"]),"확인":st.column_config.CheckboxColumn()})
        r.valuations=[Valuation(kind=x["유형"] or "토지",address=x["주소"] or "",category=x["지목"] or "",area=dec(x["면적(m²)"]),public_price=dec(x["공시지가"]),rate=dec(x["적용율(%)"]),amount=dec(x["평가금액"]),basis=x["산정근거"] or "",reviewed=bool(x["확인"])) for x in out if x["주소"] or x["평가금액"]]
    with st.expander("4. 권리내역",expanded=True):
        st.caption("선순위 공제는 담당자가 확정합니다. 말소/검토 필요 권리는 공제할 수 없습니다. 원문과 수정 이력은 세션에서 보존됩니다.")
        cols=["ID","문서","구역","순위","접수일자","권리종류","원문금액(원)","금액(원)","직접금액(천원)","담보권자","채무자","말소상태","연결순위","비고","선순위 공제","확인","금액 해당 없음"]
        rows=[dict(zip(cols,[x.id,x.document_id,x.section,x.rank,x.received,x.kind,x.amount_raw,str(x.amount_won) if x.amount_won is not None else "",str(x.amount_thousand) if x.amount_thousand is not None else "",x.creditor,x.debtor,x.cancellation,x.related_rank,x.note,x.deduction,x.reviewed,x.amount_not_applicable])) for x in r.rights]
        out=editor("rights",rows,cols,{"말소상태":st.column_config.SelectboxColumn(options=["유효 추정","말소","검토 필요"]),"선순위 공제":st.column_config.CheckboxColumn(),"확인":st.column_config.CheckboxColumn(),"금액 해당 없음":st.column_config.CheckboxColumn(),"ID":st.column_config.TextColumn(disabled=True),"원문금액(원)":st.column_config.TextColumn(disabled=True)})
        prior={x.id:x for x in r.rights};rights=[]
        for x in out:
            if not x["순위"] and not x["권리종류"]: continue
            old=prior.get(x["ID"])
            won=dec(x["금액(원)"])
            rights.append(Right(id=x["ID"] or "manual:"+uuid4().hex,document_id=x["문서"] or "수동",section=x["구역"] or "수동",rank=x["순위"] or "",received=x["접수일자"] or "",kind=x["권리종류"] or "",amount_raw=old.amount_raw if old else "",amount_won=won,amount_thousand=won/1000 if won is not None else dec(x["직접금액(천원)"]),creditor=x["담보권자"] or "",debtor=x["채무자"] or "",cancellation=x["말소상태"] or "검토 필요",related_rank=x["연결순위"] or "",note=x["비고"] or "",deduction=bool(x["선순위 공제"]),reviewed=bool(x["확인"]),amount_not_applicable=bool(x["금액 해당 없음"]),evidence=old.evidence if old else []))
        r.rights=rights
        r.rounding=choose("원 → 천원 미만 처리 기준 (내부 기준 확인 후 선택)",WON_POLICIES,r.rounding,"rounding")
    with st.expander("5. 공제대상 임차보증금내역",expanded=True):
        d=r.deposits
        d.tenancy=choose("임차 여부",["미확인","있음","없음"],d.tenancy,"tenancy")
        a,b,c=st.columns(3)
        with a: d.collective=money("집합건물 a) 보증금총액",d.collective,"dep_a")
        with b: d.residential=money("비집합건물 주거용 b) 보증금총액",d.residential,"dep_b")
        with c:
            stores=money("비집합건물 상업용 점포수",d.stores,"stores")
            if stores is not None and stores!=stores.to_integral_value(): raise ValueError("점포수는 정수로 입력하세요")
            d.stores=int(stores) if stores is not None else None
            d.commercial=money("비집합건물 상업용 c) 보증금총액",d.commercial,"dep_c")
        d.attachments=st.text_area("임차 관련 첨부서류 및 검토 상태",d.attachments,key=widget_key("dep_docs"))
        d.basis=st.text_area("공제대상 금액 확정 근거·출처",d.basis,key=widget_key("dep_basis"))
        d.reviewed=st.checkbox("입력한 a, b, c는 내부 기준에 따라 공제대상으로 확정한 금액입니다 (해당 없음은 0 입력)",value=d.reviewed,key=widget_key("dep_checked"))
    with st.expander("6. 평가결과(종합)",expanded=True):
        r.duplicate=choose("중복담보 최종 확인",DUPLICATE,r.duplicate,"duplicate")
        t=calculate(r)
        st.table([{"항목":label,"금액 (천원)":fmt(value)} for label,value in [("a) 평가금액 합계",t.valuation),("b) 선순위 채권최고액 합계",t.senior),("c) 공제대상 임차보증금 합계",t.deposits),("d) 최종담보가치 = a - b - c",t.collateral),("담보여력 = d - 평가의뢰금액",t.capacity)]])
        st.caption("담보여력이 부족한 경우에도 최종담보가치(d) 이내에서 담보 설정 가능 — 자동 승인 규칙으로 사용하지 않습니다.")
    with st.expander("7. 의견",expanded=True):
        r.opinion=st.text_area("의견",r.opinion,height=120,key=widget_key("opinion"))
        r.completion=st.radio("문서 완료 구분",["최종","임차 미반영"],index=0 if r.completion=="최종" else 1,key=widget_key("completion"),format_func=lambda x:"위 담보평가 결과서는 최종 결과서입니다." if x=="최종" else "위 담보평가결과는 임차여부를 반영하지 않은 것으로 최종 결과서가 아닙니다.")
        r.attachments_reviewed=st.checkbox("첨부서류 전체 검토 완료",r.attachments_reviewed,key=widget_key("attach_checked"))
        r.confirmed=st.checkbox("담당자 최종 확인 (변경 후 다시 확인)",r.confirmed,key=widget_key("final_checked"))
