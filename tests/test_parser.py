from pathlib import Path
import json
import pytest
from core.pdf_reader import read_pdf
from core.registry_parser import parse_registry
from core.rights_parser import parse_date
from models.schemas import PageResult
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('item',json.loads((ROOT/'sample_data/manifest.json').read_text()))
def test_independent_golden(item):
    from scripts.evaluate import unique_value
    gold=json.loads((ROOT/'sample_data/expected'/item['expected']).read_text())
    ex=parse_registry(read_pdf((ROOT/'sample_data/pdf'/item['pdf']).read_bytes(),item['pdf']),item['pdf'])
    assert unique_value(ex,'address')==gold['address']
    assert unique_value(ex,'area')==gold['area']
    assert [(o.name,o.share) for o in ex.owners]==[(o['name'],o['share']) for o in gold['owners']]
    assert [{k:(str(getattr(r,k)) if getattr(r,k) is not None else None) for k in ['section','rank','kind','receipt_date','amount_won','status']} for r in ex.rights]==gold['rights']
    assert all(e.bbox and e.page>=1 for r in ex.rights for e in r.evidence)

def test_missing_conflict():
    ex=parse_registry([PageResult(number=1,text='헤더 없는 문서')],'empty.pdf')
    assert any('address 누락' in x for x in ex.issues)
    ex=parse_registry([PageResult(number=1,text='【표제부】\n소재지: 가상A\n소재지: 가상B')],'conflict.pdf')
    assert all(c.status=='충돌' for c in ex.candidates)

def test_cross_page_continuation():
    ex=parse_registry([PageResult(number=1,text='【을구】\n1 근저당권설정 2024년 5월 10일\n채권최고액 금300,000,000원'),PageResult(number=2,text='【을구】\n근저당권자 가상금융\n채무자 가상채무자')],'multi.pdf')
    assert len(ex.rights)==1 and ex.rights[0].creditor=='가상금융'

def test_amount_conflict_not_chosen():
    ex=parse_registry([PageResult(number=1,text='【을구】\n1 근저당권설정 2024년 5월 10일\n채권최고액 금100원\n채권최고액 금200원')],'x.pdf')
    assert ex.rights[0].amount_won is None

def test_invalid_date(): assert parse_date('2024년 2월 31일')==''
