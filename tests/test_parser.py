import json
from decimal import Decimal
import pytest
from core.pdf_reader import read_pdf
from core.registry_parser import parse_registry
from core.rights_parser import normalize_date, parse_amount
from core.field_mapper import map_registries
from models.schemas import PageResult

@pytest.mark.parametrize("name",["case_01_토지","case_01_건물","case_02_토지","case_02_건물","case_03_집합건물","case_04_집합건물","case_05_집합건물","case_06_집합건물"])
def test_independent_truth(root,name):
    truth=json.loads((root/"sample_data/expected"/(name+".json")).read_text())
    r=parse_registry(read_pdf((root/"sample_data/pdf"/(name+".pdf")).read_bytes()),name)
    assert [f.value for f in r.facts if f.field=="소재지"]==[truth["address"]]
    assert [f.value.split(" | ")[0] for f in r.facts if f.field=="소유자"]==truth["owners"]
    assert [f.value for f in r.facts if f.field=="면적"]==[truth["area"]]
    assert len(r.rights)==len(truth["rights"])
    for actual,expected in zip(r.rights,truth["rights"]):
        for key in ["rank","section","kind","received","cancellation"]: assert getattr(actual,key)==expected[key]
        assert actual.amount_won==(Decimal(expected["amount_won"]) if expected["amount_won"] else None)
        assert actual.evidence and actual.evidence[0].page==1 and actual.evidence[0].bbox
        assert not actual.reviewed and not actual.deduction

def test_normalizers():
    assert normalize_date("2024년 5월 10일")=="2024-05-10"
    assert normalize_date("2024년 2월 31일")==""
    assert parse_amount("채권최고액 금300,000,000원")==[Decimal("300000000")]

def test_missing_and_conflict():
    r=parse_registry([PageResult(number=1,text="【표제부】\n소재지: 가상가\n소재지: 가상나\n【을구】\n1 근저당권설정 2024년 5월 10일\n채권최고액 금1,000원\n채권최고액 금2,000원")],"x")
    assert all(f.status=="충돌" for f in r.facts if f.field=="소재지")
    assert any(f.status=="누락" and f.field=="면적" for f in r.facts)
    assert r.rights[0].amount_won is None
    mapped=map_registries([r],"토지·건물")
    assert not mapped.targets[0].address and not mapped.targets[0].debtor

def test_continuation_across_pages():
    r=parse_registry([PageResult(number=1,text="【을구】\n1 근저당권설정 2024년 5월 10일"),PageResult(number=2,text="【을구】\n채권최고액 금100,000원\n근저당권자: 가상은행")],"x")
    assert r.rights[0].amount_won==Decimal("100000")
    assert [e.page for e in r.rights[0].evidence]==[1,2,2]
