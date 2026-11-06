import pytest
from core.validation import validate_report
from models.schemas import Report

def test_complete(complete): assert validate_report(complete)==[]
def test_empty(): assert len(validate_report(Report()))>=8

def test_unknown_tenancy(complete):
    complete.deposits.tenancy="미확인"
    assert any("임차" in x for x in validate_report(complete))

def test_missing_debtor(complete):
    complete.targets[0].debtor=""
    assert any("채무자" in x for x in validate_report(complete))

def test_invalid_selection(complete):
    complete.request.purpose="자동승인"
    assert any("평가목적" in x for x in validate_report(complete))

@pytest.mark.parametrize("amount",["-1","NaN","Infinity"])
def test_model_rejects_money(complete,amount):
    with pytest.raises(ValueError): complete.request.amount=amount
