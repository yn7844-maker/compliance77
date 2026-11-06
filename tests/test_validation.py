from decimal import Decimal as D
import pytest
from core.validation import validate_report
from models.schemas import Report

def test_complete(complete): assert validate_report(complete)==[]

def test_empty_is_draft(): assert len(validate_report(Report()))>8

def test_unchecked_tenancy(complete):
    complete.deposit.tenancy='미확인'
    assert any('임차 여부 미확인' in x for x in validate_report(complete))

def test_cancelled_deduction_rejected(complete):
    complete.rights[0].status='말소'
    assert any('말소/미확정' in x for x in validate_report(complete))

def test_invalid_option_and_amount(complete):
    complete.purpose='임의 선택';complete.requested=D('-1')
    assert any('평가목적' in x for x in validate_report(complete))
    assert any('평가의뢰금액' in x for x in validate_report(complete))

def test_missing_valuation_basis(complete):
    complete.valuations[0].basis=''
    assert any('산정근거' in x for x in validate_report(complete))
