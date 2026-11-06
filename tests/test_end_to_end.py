from pathlib import Path
from io import BytesIO
from decimal import Decimal as D
from docx import Document
from core.pdf_reader import read_pdf
from core.registry_parser import parse_registry
from core.field_mapper import suggest
from core.word_generator import generate_word,fmt
from core.validation import validate_report
ROOT=Path(__file__).resolve().parents[1]

def test_pdf_to_review_to_word(complete):
    path=ROOT/'sample_data/pdf/case03_집합건물.pdf'
    extracted=parse_registry(read_pdf(path.read_bytes(),path.name),path.name)
    target,valuation=suggest(extracted,'집합건물')
    assert target.address==complete.targets[0].address
    assert valuation.area==D('84.5')
    # 추출 제안을 담당자가 증빙 대조 후 보완하는 업무 경로
    target.debtor='가상채무자A';target.duplicate='없음';target.stores='해당 없음';target.confirmed=True
    complete.targets=[target]
    valuation.amount=D('500000');valuation.basis='외부 가상 감정 입력; 공시지가·적용율 해당 없음';valuation.confirmed=True
    complete.valuations=[valuation]
    for right in extracted.rights:
        right.confirmed=True;right.status='유효 확인';right.notes='담당자 검토 완료'
        if right.kind=='소유권': right.decision='제외';right.creditor='해당 없음'
        else: right.decision='공제'
    complete.rights=extracted.rights
    assert not validate_report(complete)
    doc=Document(BytesIO(generate_word(complete,final=True)))
    assert '가상소유자C' in doc.tables[1].cell(1,3).text
    assert doc.tables[5].cell(2,3).text=='300,000'
    assert doc.tables[7].cell(1,3).text=='190,000'

def test_precision_preserved_in_word():
    assert fmt(D('1.0001'))=='1.0001'
