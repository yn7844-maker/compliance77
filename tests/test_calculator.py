from decimal import Decimal as D
import pytest
from core.collateral_calculator import calculate,won_to_thousand,valuation_amount
from config.calculation_rules import VALUATION_RULES

@pytest.mark.parametrize('policy,expected',[('정밀 유지','1.999'),('절사','1'),('반올림','2')])
def test_units(policy,expected): assert won_to_thousand(D('1999'),policy)==D(expected)

def test_totals(complete):
    c=calculate(complete)
    assert c=={'a':D('500000'),'b':D('300000'),'c':D('10000'),'deposit_total':D('10000'),'d':D('190000'),'capacity':D('90000')}

def test_negative_capacity_is_not_rejection(complete):
    complete.requested=D('300000')
    assert calculate(complete)['capacity']==D('-110000')

def test_unconfirmed_not_zero(complete):
    complete.rights[0].confirmed=False
    assert calculate(complete)['b'] is None and calculate(complete)['d'] is None
    complete.rights[0].confirmed=True;complete.deposit.reviewed=False
    assert calculate(complete)['c'] is None

def test_no_inferred_priority(complete):
    complete.rights[0].decision='제외'
    assert calculate(complete)['b']==0
    complete.rights[0].decision='공제';complete.rights[0].status='말소'
    assert calculate(complete)['b'] is None

def test_no_automatic_valuation_rule(complete):
    row=complete.valuations[0];row.amount=None;row.area=D(100);row.public_price=D(10);row.rate=D(80)
    assert VALUATION_RULES[row.kind] is None
    assert valuation_amount(row) is None
