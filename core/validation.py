from config.field_options import REQUEST_TYPES, CONTRACTS, PURPOSES, PROPERTY_TYPES, DUPLICATE
from core.collateral_calculator import calculate
from models.schemas import Report

def validate_report(r: Report) -> list[str]:
    errors = list(calculate(r).blockers)
    for value, options, label in [(r.request.repeat,REQUEST_TYPES,"재의뢰 여부"),(r.request.contract,CONTRACTS,"대상계약"),(r.request.purpose,PURPOSES,"평가목적"),(r.duplicate,DUPLICATE[1:],"종합 중복담보")]:
        if value not in options: errors.append(label+" 확인 필요")
    for label, value in [("점포명",r.request.store),("평가 시 고려사항",r.request.considerations),("의견",r.opinion)]:
        if not value.strip(): errors.append(label+" 입력 필요 (해당 없으면 명시)")
    if not r.targets: errors.append("평가대상 입력 필요")
    from fractions import Fraction
    for i,t in enumerate(r.targets,1):
        for owner in t.owners:
            try:
                share=Fraction(owner.share)
                if not 0<share<=1: raise ValueError()
            except (ValueError,ZeroDivisionError): errors.append(f"평가대상 {i}: 소유자 지분을 1/1, 1/2 등으로 확인하세요")
        if t.kind not in PROPERTY_TYPES or not t.address.strip() or not t.debtor.strip() or not t.owners or any(not o.name.strip() or not o.share.strip() for o in t.owners) or not t.related_store.strip():
            errors.append(f"평가대상 {i}: 구분·소재지·채무자·소유자·지분·관련점포 확인 필요")
        if t.duplicate not in DUPLICATE[1:]: errors.append(f"평가대상 {i}: 중복담보 확인 필요")
    for i,v in enumerate(r.valuations,1):
        if not v.address.strip() or not v.category.strip() or v.area is None or not v.basis.strip():
            errors.append(f"평가행 {i}: 주소·지목(해당 없음 허용)·면적·산정근거 필요")
        if r.evaluation_type == "집합건물" and v.kind != "집합건물" or r.evaluation_type == "토지·건물" and v.kind == "집합건물":
            errors.append(f"평가행 {i}: 평가 유형 불일치")
    ids = [x.id for x in r.rights]
    if len(ids) != len(set(ids)): errors.append("권리 ID 중복")
    for x in r.rights:
        if x.kind!="소유권 관련 등기" and x.amount_won is None and x.amount_thousand is None and not x.amount_not_applicable:
            errors.append(f"권리 {x.rank}: 금액 또는 금액 해당 없음 확인 필요")
        if x.amount_not_applicable and x.deduction:
            errors.append(f"권리 {x.rank}: 금액 해당 없음과 선순위 공제 동시 선택 불가")
        if not x.rank or not x.kind or not x.received or not x.creditor or not x.note:
            errors.append(f"권리 {x.rank}: 순위·접수일·종류·권리자·비고 확인 필요")
        from datetime import date
        try: date.fromisoformat(x.received)
        except ValueError: errors.append(f"권리 {x.rank}: 접수일자는 YYYY-MM-DD로 입력하세요")
        if x.cancellation == "검토 필요": errors.append(f"권리 {x.rank}: 말소/변경 관계 확인 필요")
        if x.amount_won is not None and x.amount_thousand is not None and x.amount_won / 1000 != x.amount_thousand:
            errors.append(f"권리 {x.rank}: 원/천원 금액 불일치")
    d=r.deposits
    if d.stores is None or not d.attachments.strip() or not d.basis.strip(): errors.append("임차 점포수·첨부서류·공제 근거 필요 (해당 없음 명시)")
    if not r.attachments_reviewed: errors.append("첨부서류 검토 미완료")
    if r.completion != "최종" or d.tenancy == "미확인": errors.append("최종 결과서 상태 및 임차 여부 확인 필요")
    if not r.confirmed: errors.append("담당자 최종 확인 필요")
    if any(f.status != "사용자 확정" for f in r.facts): errors.append("자동 추출 후보 및 충돌 검토 미완료")
    return list(dict.fromkeys(errors))
