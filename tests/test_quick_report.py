import pytest
from core.quick_report import parse_text,prepare_report,MAX_TEXT_CHARS

def test_no_invented_financial_inputs():
    ex=parse_text('[집합건물]\n【표제부】\n소재지: 가상구 1\n면적: 15.5 m²\n【을구】\n1 근저당권설정 2024년 5월 10일\n채권최고액 금300,000,000원')
    r=prepare_report([ex],'토지·건물')
    assert r.targets[0].kind=='집합건물'
    assert r.valuations[0].amount is None and not r.rights[0].confirmed
    assert r.requested is None and r.deposit.tenancy=='미확인'

@pytest.mark.parametrize('text',[' ','a'*(MAX_TEXT_CHARS+1),'\f'*41])
def test_input_limits(text):
    with pytest.raises(ValueError): parse_text(text)
