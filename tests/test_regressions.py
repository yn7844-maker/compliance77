from pathlib import Path
from decimal import Decimal
from io import BytesIO
import pytest
from docx import Document
from core.collateral_calculator import calculate
from core.validation import validate_report
from core.word_generator import generate_word
from streamlit.testing.v1 import AppTest

def test_nonmonetary_cell_has_no_missing_marker(complete):
    doc=Document(BytesIO(generate_word(complete,draft=False)))
    assert doc.tables[5].cell(1,3).text=='해당 없음'
    assert all('미입력' not in c.text and '미확정' not in c.text for t in doc.tables for row in t.rows for c in row.cells)

def test_missing_monetary_amount_requires_explicit_na(complete):
    x=complete.rights[1]
    x.amount_won=None;x.amount_thousand=None;x.deduction=False
    assert any('금액 또는' in e for e in validate_report(complete))
    x.amount_not_applicable=True
    assert not validate_report(complete)

def test_bad_share_and_date(complete):
    complete.targets[0].owners[0].share='지분 확인 필요'
    complete.rights[0].received='아직 모름'
    errors=validate_report(complete)
    assert any('지분' in e for e in errors) and any('접수일자' in e for e in errors)

def test_tenancy_conflict_blocks(complete):
    complete.deposits.tenancy='없음'
    assert calculate(complete).collateral is None

def test_final_confirmation_clears_after_edit():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
    app.button[0].click().run()
    final=next(c for c in app.checkbox if c.label.startswith('담당자 최종 확인'))
    final.check().run()
    assert app.session_state.report.confirmed
    name=next(t for t in app.text_input if t.label=='점포명')
    name.set_value('변경가상점포').run()
    assert not app.session_state.report.confirmed
    assert not app.exception
    app.run()
    final=next(c for c in app.checkbox if c.label.startswith('담당자 최종 확인'))
    assert not final.value
    final.check().run()
    assert app.session_state.report.confirmed


def test_ownership_cancellation_requires_review():
    from core.registry_parser import parse_registry
    from models.schemas import PageResult
    r=parse_registry([PageResult(number=1,text="【갑구】\n2 소유권말소 2024년 5월 10일\n소유자: 가상소유자")],"test")
    assert r.rights[0].cancellation=="검토 필요"
