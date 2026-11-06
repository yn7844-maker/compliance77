from decimal import Decimal, InvalidOperation
import streamlit as st
from config.field_options import RE_REQUEST, CONTRACTS, PURPOSES, PROPERTY_TYPES
from core.collateral_calculator import calculate
from models.schemas import Report,Target,Owner,Valuation,Right,Deposit

def render_form(seed: Report) -> Report:
    rev=st.session_state.revision
    def text(label,value='',multi=False):
        return (st.text_area if multi else st.text_input)(label,value=value,key=f'{rev}:text:{label}')
    def choice(label,options,value):
        opts=['']+options if value=='' else options
        return st.selectbox(label,opts,index=opts.index(value) if value in opts else 0,key=f'{rev}:select:{label}')
    def check(label,value=False): return st.checkbox(label,value=value,key=f'{rev}:check:{label}')
    def dec(label,value):
        raw=text(label,'' if value is None else str(value))
        if not raw.strip(): return None
        try:
            d=Decimal(raw.replace(',',''))
            if not d.is_finite(): raise InvalidOperation
            return d
        except InvalidOperation:
            st.error(f'{label}: 숫자만 입력하세요.');return None
    def editor(label,rows,columns,selects=None,booleans=None):
        st.caption(label+' · 마지막 빈 행에서 추가, 왼쪽 행 선택 후 삭제 · 금액/면적은 문자로 입력하여 정밀도 유지')
        config={col:st.column_config.TextColumn(col) for col in columns}
        for col,options in (selects or {}).items(): config[col]=st.column_config.SelectboxColumn(col,options=options,required=True)
        for col in booleans or []: config[col]=st.column_config.CheckboxColumn(col)
        import pandas as pd
        return st.data_editor(pd.DataFrame(rows,columns=columns),num_rows='dynamic',hide_index=True,column_config=config,key=f'{rev}:editor:{label}',width='stretch').to_dict('records')
    def clean(v):
        if v is None: return ''
        if isinstance(v,float) and v!=v: return ''
        return str(v).strip()
    def parsed(v):
        s=clean(v)
        if not s: return None
        d=Decimal(s.replace(',',''))
        if not d.is_finite(): raise ValueError('유한수만 입력하세요.')
        return d
    def checked(v): return v is True or str(v)=='True'
    r=seed.model_copy(deep=True)
    with st.expander('1. 의뢰내역',expanded=True):
        r.re_request=choice('재의뢰 여부',RE_REQUEST,seed.re_request)
        r.store=text('점포명',seed.store)
        r.contract=choice('대상계약',CONTRACTS,seed.contract)
        r.purpose=choice('평가목적',PURPOSES,seed.purpose)
        r.requested=dec('평가의뢰금액 (천원)',seed.requested)
        r.considerations=text('평가 시 고려사항 (없으면 해당 없음)',seed.considerations,True)
    with st.expander('2. 평가대상',expanded=True):
        cols=['구분','소재지','채무자','소유자·지분','중복담보','관련점포','확정']
        rows=[[t.kind,t.address,t.debtor,'; '.join(f'{o.name}|{o.share}' for o in t.owners),t.duplicate,t.stores,t.confirmed] for t in seed.targets]
        st.caption('복수 소유자 입력: 가상소유자A|1/2; 가상소유자B|1/2 · 채무자는 별도 입력')
        data=editor('평가대상',rows,cols,{'구분':PROPERTY_TYPES,'중복담보':['미확인','있음','없음']},['확정'])
        r.targets=[]
        for row in data:
            owners=[]
            for owner in clean(row['소유자·지분']).split(';'):
                if owner.strip():
                    parts=owner.strip().split('|',1);owners.append(Owner(name=parts[0],share=parts[1] if len(parts)>1 else ''))
            r.targets.append(Target(kind=clean(row['구분']) or '기타',address=clean(row['소재지']),debtor=clean(row['채무자']),owners=owners,duplicate=clean(row['중복담보']) or '미확인',stores=clean(row['관련점포']),confirmed=checked(row['확정'])))
    with st.expander('3. 평가결과',expanded=True):
        st.info('평가금액은 담당자가 입력합니다. 산식 미확정 상태에서 공시지가×면적 계산을 적용하지 않습니다. 공시지가·적용율을 쓰지 않는 경우 산정근거에 “해당 없음”을 명시하세요.')
        cols=['유형','주소','지목','면적(m²)','공시지가(천원/m²)','적용율(%)','평가금액(천원)','산정근거','확정']
        rows=[[v.kind,v.address,v.category,*[str(x) if x is not None else '' for x in (v.area,v.public_price,v.rate,v.amount)],v.basis,v.confirmed] for v in seed.valuations]
        data=editor('평가 행',rows,cols,{'유형':['토지','건물','집합건물']},['확정'])
        r.valuations=[Valuation(kind=clean(x['유형']) or '토지',address=clean(x['주소']),category=clean(x['지목']),area=parsed(x['면적(m²)']),public_price=parsed(x['공시지가(천원/m²)']),rate=parsed(x['적용율(%)']),amount=parsed(x['평가금액(천원)']),basis=clean(x['산정근거']),confirmed=checked(x['확정'])) for x in data]
        r.empty_tables=choice('미해당 평가유형의 표 데이터 행',['유지','제거'],seed.empty_tables)
    with st.expander('4. 권리내역',expanded=True):
        st.warning('접수일자가 빠르다는 이유만으로 선순위를 확정하지 않습니다. 말소·변경 연결과 누락을 원문으로 대조하세요. 금액은 이 표에서 원 단위입니다.')
        cols=['ID','구역','순위','접수일자','권리종류','채권최고액(원)','담보권자','채무자','상태','선순위 결정','비고','확정']
        rows=[[x.id,x.section,x.rank,x.receipt_date,x.kind,str(x.amount_won) if x.amount_won is not None else '',x.creditor,x.debtor,x.status,x.decision,x.notes,x.confirmed] for x in seed.rights]
        data=editor('권리 행',rows,cols,{'상태':['유효 여부 검토','말소','변경 검토','유효 확인'],'선순위 결정':['미검토','공제','제외']},['확정'])
        old={x.id:x for x in seed.rights}
        r.rights=[]
        for i,x in enumerate(data):
            rid=clean(x['ID']) or f'manual:{i+1}'
            base=old[rid].model_copy(deep=True) if rid in old else Right(id=rid)
            for attr,key in [('section','구역'),('rank','순위'),('receipt_date','접수일자'),('kind','권리종류'),('creditor','담보권자'),('debtor','채무자'),('notes','비고')]: setattr(base,attr,clean(x[key]))
            base.amount_won=parsed(x['채권최고액(원)']);base.status=clean(x['상태']) or '유효 여부 검토';base.decision=clean(x['선순위 결정']) or '미검토';base.confirmed=checked(x['확정'])
            r.rights.append(base)
        r.rights_reviewed=check('갑구·을구 전체 대조 완료 (권리 없음도 직접 확인)',seed.rights_reviewed)
        r.rounding=choice('원→천원 변환 기준',['정밀 유지','절사','반올림'],seed.rounding)
        r.rounding_confirmed=check('위 천원 미만 금액 처리 기준을 확인했습니다',seed.rounding_confirmed)
    with st.expander('5. 공제대상 임차보증금내역',expanded=True):
        dep=seed.deposit.model_copy(deep=True)
        dep.tenancy=choice('임차 여부',['미확인','있음','없음'],dep.tenancy)
        dep.a=dec('집합건물 a) 보증금총액 (천원)',dep.a)
        dep.b=dec('비집합건물 주거용 b) 보증금총액 (천원)',dep.b)
        shops=dec('비집합건물 상업용 점포수',Decimal(dep.shops) if dep.shops is not None else None)
        if shops is not None and shops%1: raise ValueError('점포수는 정수여야 합니다.')
        dep.shops=int(shops) if shops is not None else None
        dep.c=dec('비집합건물 상업용 c) 보증금총액 (천원)',dep.c)
        dep.decision=choice('보증금 공제 결정',['미검토','공제','공제 없음'],dep.decision)
        dep.basis=text('임차보증금 공제 기준·출처',dep.basis,True)
        dep.attachments=text('첨부서류 (없으면 해당 없음)',dep.attachments)
        dep.attachment_review=choice('첨부서류 검토 상태',['미검토','확인','해당 없음'],dep.attachment_review)
        dep.reviewed=check('a·b·c 및 공제대상 검토 완료 (미해당 금액은 0 입력)',dep.reviewed)
        r.deposit=dep
    with st.expander('6. 평가결과(종합)',expanded=True):
        r.evidence_reviewed=check('추출 실패·누락·충돌 및 모든 증빙자료를 대조하고 수동 보완했습니다',seed.evidence_reviewed)
        calc=calculate(r)
        for label,key in [('a) 평가금액 합계','a'),('b) 선순위 채권최고액 합계','b'),('c) 공제대상 임차보증금 합계','c'),('d) 최종담보가치','d'),('담보여력','capacity')]:
            st.write(f'{label}: {calc[key]:,} 천원' if calc[key] is not None else f'{label}: 미확정')
        from config.field_options import NOTE
        st.caption(NOTE+' (자동 승인 규칙이 아닙니다.)')
    with st.expander('7. 의견',expanded=True):
        r.opinion=text('담당자 의견',seed.opinion,True)
        r.completion=choice('결과서 구분',['최종','임차 미반영 비최종'],seed.completion)
        r.reviewer=text('담당자',seed.reviewer)
    return r
