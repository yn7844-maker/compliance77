"""미확정 업무 산식은 활성화하지 않는다. 금액은 천원, 단가는 천원/m²."""
VALUATION_RULES = {'토지': None, '건물': None, '집합건물': None}
ROUNDING_POLICIES = ['정밀 유지', '절사', '반올림']
DEFAULT_ROUNDING = '정밀 유지'  # 원 금액을 1000으로 정확히 나눈 값, 절사/반올림 없음
