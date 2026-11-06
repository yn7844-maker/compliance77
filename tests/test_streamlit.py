from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_app_empty_and_complete_package():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state.report.request.store=="가상시연점포01"
    assert len(app.session_state.documents)==2

def test_full_upload_review_word_flow(root):
    from core.pdf_reader import read_pdf
    from core.registry_parser import parse_registry
    from core.field_mapper import map_registries
    from models.schemas import Report
    from core.word_generator import generate_word
    from core.validation import validate_report
    from docx import Document
    from io import BytesIO
    names=["case_01_토지.pdf","case_01_건물.pdf"]
    parsed=[parse_registry(read_pdf((root/"sample_data/pdf"/n).read_bytes()),n) for n in names]
    proposal=map_registries(parsed,"토지·건물")
    assert len(proposal.targets)==2 and len(proposal.rights)==3
    # 가상 담당자가 별도 증빙의 확인값을 입력한다.
    approved=Report.model_validate_json((root/"sample_data/packages/package_01.json").read_text())
    approved.facts=proposal.facts
    for fact in approved.facts: fact.status="사용자 확정"
    assert not validate_report(approved)
    doc=Document(BytesIO(generate_word(approved,draft=False)))
    assert doc.tables[-1].cell(1,3).text=="460,000"
