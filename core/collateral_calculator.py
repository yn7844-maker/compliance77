from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from models.schemas import Report, Totals

ZERO = Decimal("0")

def won_to_thousand(won: Decimal, policy: str = "미정") -> Decimal:
    value = Decimal(won) / Decimal("1000")
    if value == value.to_integral_value():
        return value
    if policy == "정확값 유지":
        return value
    if policy == "절사":
        return value.quantize(Decimal("1"), rounding=ROUND_DOWN)
    if policy == "반올림":
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    raise ValueError("천원 미만 처리 기준을 확정하세요")

def calculate(report: Report) -> Totals:
    t = Totals()
    if report.valuations and all(v.reviewed and v.amount is not None for v in report.valuations):
        t.valuation = sum((v.amount for v in report.valuations), ZERO)
    else:
        t.blockers.append("평가금액 및 산정 근거 확인 필요")
    if not report.registry_reviewed or any(not r.reviewed for r in report.rights):
        t.blockers.append("권리 전체의 선순위 공제 여부 확인 필요")
    else:
        selected = [r for r in report.rights if r.deduction]
        if any(r.cancellation != "유효 추정" or r.amount_won is None and r.amount_thousand is None for r in selected):
            t.blockers.append("말소·불확실 권리 또는 공제금액 확인 필요")
        else:
            try:
                t.senior = sum((won_to_thousand(r.amount_won, report.rounding) if r.amount_won is not None else r.amount_thousand for r in selected), ZERO)
            except ValueError as exc:
                t.blockers.append(str(exc))
    d = report.deposits
    if d.reviewed and d.tenancy != "미확인" and all(x is not None for x in [d.collective,d.residential,d.commercial]):
        if d.tenancy=="없음" and d.collective+d.residential+d.commercial!=0:
            t.blockers.append("임차 없음과 공제보증금 금액이 충돌합니다")
        else:
            t.deposits = d.collective + d.residential + d.commercial
    else:
        t.blockers.append("임차 여부 및 공제대상 보증금 확인 필요")
    if report.request.amount is None:
        t.blockers.append("평가의뢰금액 미입력")
    if all(x is not None for x in [t.valuation,t.senior,t.deposits,report.request.amount]) and not t.blockers:
        t.collateral = t.valuation - t.senior - t.deposits
        t.capacity = t.collateral - report.request.amount
    return t

def fmt(value: Decimal | None) -> str:
    if value is None:
        return "미확정"
    return format(value, ",f").rstrip("0").rstrip(".") if "." in format(value, ",f") else format(value, ",f")
