from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from config.calculation_rules import VALUATION_RULES
from models.schemas import Report, Valuation

D = Decimal

def won_to_thousand(value: Decimal, policy: str = '정밀 유지') -> Decimal:
    value = D(value) / D(1000)
    if policy == '절사': return value.quantize(D('1'), rounding=ROUND_DOWN)
    if policy == '반올림': return value.quantize(D('1'), rounding=ROUND_HALF_UP)
    if policy != '정밀 유지': raise ValueError('알 수 없는 금액 처리 기준')
    return value

def valuation_amount(row: Valuation) -> Decimal | None:
    rule = VALUATION_RULES[row.kind]
    if rule is None: return row.amount
    if rule == 'area_price_rate':
        if any(v is None for v in [row.area, row.public_price, row.rate]): return None
        return row.area * row.public_price * row.rate / D(100)
    raise ValueError('지원되지 않는 산식')

def calculate(report: Report) -> dict[str, Decimal | None]:
    """검토가 끝난 입력에만 합계 및 최종값을 제공한다. 미검토를 0으로 바꾸지 않는다."""
    a = b = c = None
    if report.valuations and all(v.confirmed and valuation_amount(v) is not None for v in report.valuations):
        a = sum((valuation_amount(v) for v in report.valuations), D(0))
    if report.rights_reviewed and report.rounding_confirmed and all(r.confirmed and r.decision != '미검토' and r.status in ['유효 확인','말소'] for r in report.rights):
        included = [r for r in report.rights if r.decision == '공제']
        if all(r.amount_won is not None and r.status == '유효 확인' for r in included):
            b = sum((won_to_thousand(r.amount_won, report.rounding) for r in included), D(0))
    dep = report.deposit
    deposit_total = None
    if dep.reviewed and all(v is not None for v in (dep.a, dep.b, dep.c)):
        deposit_total = dep.a + dep.b + dep.c
    if dep.reviewed and dep.tenancy != '미확인' and dep.decision != '미검토' and deposit_total is not None and dep.attachment_review != '미검토' and dep.basis.strip():
        c = deposit_total if dep.decision == '공제' else D(0)
    ready = all(v is not None for v in (a, b, c)) and report.evidence_reviewed and all(t.confirmed for t in report.targets) and bool(report.targets)
    d = a - b - c if ready else None
    return {'a': a, 'b': b, 'c': c, 'deposit_total': deposit_total, 'd': d,
            'capacity': d - report.requested if d is not None and report.requested is not None else None}
