from decimal import Decimal as D
import pytest
from core.collateral_calculator import calculate, won_to_thousand

def test_exact_totals(complete):
    t=calculate(complete)
    assert (t.valuation,t.senior,t.deposits,t.collateral,t.capacity)==tuple(map(D,["800000","300000","40000","460000","360000"]))

def test_negative_capacity(complete):
    complete.request.amount=D("900000")
    assert calculate(complete).capacity==D("-440000")

def test_not_all_rights_summed(complete):
    complete.rights[1].deduction=False
    assert calculate(complete).senior==0

@pytest.mark.parametrize("field",["registry","valuation","deposit","amount","right"])
def test_unconfirmed_blocks(complete,field):
    if field=="registry": complete.registry_reviewed=False
    if field=="valuation": complete.valuations[0].reviewed=False
    if field=="deposit": complete.deposits.reviewed=False
    if field=="amount": complete.request.amount=None
    if field=="right": complete.rights[0].reviewed=False
    assert calculate(complete).collateral is None

def test_cancelled_deduction_blocked(complete):
    complete.rights[1].cancellation="말소"
    assert calculate(complete).collateral is None

def test_won_policy():
    assert won_to_thousand(D("300000000"))==D("300000")
    with pytest.raises(ValueError): won_to_thousand(D("1555"))
    assert won_to_thousand(D("1555"),"정확값 유지")==D("1.555")
    assert won_to_thousand(D("1555"),"절사")==D("1")
    assert won_to_thousand(D("1555"),"반올림")==D("2")

def test_decimal_fraction(complete):
    complete.valuations[0].amount=D("0.1");complete.valuations[1].amount=D("0.2")
    assert calculate(complete).valuation==D("0.3")
