from decimal import Decimal
from datetime import date
import re
from config.field_options import RE_REQUEST, CONTRACTS, PURPOSES, PROPERTY_TYPES
from core.collateral_calculator import calculate
from models.schemas import Report

def validate_report(r: Report) -> list[str]:
    errors = []
    for label, value, options in [('재의뢰 여부',r.re_request,RE_REQUEST),('대상계약',r.contract,CONTRACTS),('평가목적',r.purpose,PURPOSES)]:
        if value not in options: errors.append(f'의뢰내역: {label} 선택 필요')
    for label, value in [('점포명',r.store),('평가 시 고려사항',r.considerations),('의견',r.opinion),('담당자',r.reviewer)]:
        if not value.strip(): errors.append(f'{label}: 입력 또는 해당 없음 명시 필요')
    def amount(label, value):
        if value is None or not value.is_finite() or value < 0: errors.append(f'{label}: 0 이상의 유한 금액/수치 필요')
    amount('평가의뢰금액',r.requested)
    if not r.targets: errors.append('평가대상: 최소 1건 필요')
    for i,t in enumerate(r.targets,1):
        if t.kind not in PROPERTY_TYPES or not t.address.strip() or not t.debtor.strip() or not t.owners or any(not o.name.strip() or not o.share.strip() for o in t.owners): errors.append(f'평가대상 {i}: 구분·소재지·채무자·소유자·지분 필요')
        for owner in t.owners:
            match=re.fullmatch(r'(\d+)/(\d+)',owner.share.strip())
            if not match or not (0 < int(match[1]) <= int(match[2])): errors.append(f'평가대상 {i}: 지분은 양수 분수(예: 1/2)로 입력 필요')
        if t.duplicate == '미확인' or not t.stores.strip() or not t.confirmed: errors.append(f'평가대상 {i}: 중복담보·관련점포·담당자 확정 필요')
    if not r.valuations: errors.append('평가금액: 최소 1개 행 필요')
    for i,v in enumerate(r.valuations,1):
        for label,val in [('면적',v.area),('평가금액',v.amount)]: amount(f'평가 {i} {label}',val)
        for label,val in [('공시지가',v.public_price),('적용율',v.rate)]:
            if val is not None: amount(f'평가 {i} {label}',val)
        if not v.address.strip() or not v.category.strip() or not v.basis.strip() or not v.confirmed: errors.append(f'평가 {i}: 주소·지목(해당 없음 허용)·산정근거·확정 필요')
        if (v.public_price is None or v.rate is None) and '해당 없음' not in v.basis: errors.append(f'평가 {i}: 공시지가/적용율 미사용 시 근거에 해당 없음 명시 필요')
    if not r.rights_reviewed: errors.append('권리내역: 전체 검토(권리 없음 포함) 필요')
    for i,x in enumerate(r.rights,1):
        if not x.rank.strip() or not x.receipt_date.strip() or not x.kind.strip() or not x.creditor.strip() or not x.notes.strip(): errors.append(f'권리 {i}: 필수 셀 입력(해당 없음 허용) 필요')
        if x.receipt_date and x.receipt_date != '해당 없음':
            try: date.fromisoformat(x.receipt_date)
            except ValueError: errors.append(f'권리 {i}: 접수일자는 YYYY-MM-DD로 입력 필요')
        if x.kind in ['근저당권','저당권','전세권'] and x.amount_won is None and x.status!='말소': errors.append(f'권리 {i}: 채권금액 또는 전세금 확인 필요')
        if not x.confirmed or x.decision == '미검토' or x.status in ['유효 여부 검토','변경 검토']: errors.append(f'권리 {i}: 유효/말소 여부 및 선순위 공제·제외 확인 필요')
        if x.decision == '공제' and (x.status != '유효 확인' or x.amount_won is None): errors.append(f'권리 {i}: 말소/미확정 권리 공제 불가')
    d = r.deposit
    for label,v in [('a',d.a),('b',d.b),('c',d.c)]: amount(f'보증금 {label}',v)
    if d.shops is None or d.shops < 0: errors.append('상업용 점포수: 0 이상 정수 필요')
    if not d.reviewed or d.decision == '미검토' or not d.basis.strip() or not d.attachments.strip() or d.attachment_review == '미검토': errors.append('임차보증금: 공제 기준·첨부서류·검토 확정 필요')
    if d.tenancy == '없음' and any(v is not None and v != 0 for v in (d.a,d.b,d.c)): errors.append('임차 없음과 보증금 금액 충돌')
    if r.completion == '최종' and d.tenancy == '미확인': errors.append('임차 여부 미확인: 최종 결과서 불가')
    if not r.rounding_confirmed: errors.append('천원 미만 금액 처리 기준 확인 필요')
    if not r.evidence_reviewed: errors.append('문서 추출 누락·충돌 및 모든 증빙 대조 확인 필요')
    if not r.reviewed: errors.append('담당자 최종 확인 필요')
    if r.completion == '최종' and calculate(r)['d'] is None: errors.append('최종담보가치 미확정')
    return errors
