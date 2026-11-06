from pathlib import Path
from io import BytesIO
from hashlib import sha256
from decimal import Decimal as D
from docx import Document
import pytest
from config.document_fields import SECTIONS,HEADERS
from config.field_options import NOTE,FINAL_TEXT,NONFINAL_TEXT
from core.word_generator import generate_word,DEFAULT_TEMPLATE,TABLE_HEADERS
from models.schemas import Report

def test_word_structure_and_cells(complete):
    before=sha256(DEFAULT_TEMPLATE.read_bytes()).hexdigest()
    doc=Document(BytesIO(generate_word(complete,final=True)))
    paragraphs=[p.text for p in doc.paragraphs]
    assert [p for p in paragraphs if p[:1].isdigit()]==[f'{i+1}. {s}' for i,s in enumerate(SECTIONS)]
    assert [[c.text for c in t.rows[0].cells] for t in doc.tables]==TABLE_HEADERS
    assert doc.tables[0].cell(1,0).text=='최초'
    assert doc.tables[0].cell(1,3).text=='신규담보'
    assert doc.tables[7].cell(1,3).text=='190,000'
    assert doc.tables[7].cell(1,4).text=='90,000'
    assert '☑ '+FINAL_TEXT in paragraphs and '☐ '+NONFINAL_TEXT in paragraphs
    assert NOTE in paragraphs
    assert sha256(DEFAULT_TEMPLATE.read_bytes()).hexdigest()==before
    assert not doc.inline_shapes
    # 실제 w:tbl / w:tc 편집 가능 요소 확인
    assert '<w:tbl>' in doc._element.xml and '가상점포_case03' in doc._element.xml

def test_multiple_rows_and_empty_modes(complete):
    complete.valuations.append(complete.valuations[0].model_copy())
    complete.rights.append(complete.rights[0].model_copy(update={'id':'second','rank':'2'}))
    doc=Document(BytesIO(generate_word(complete,final=True)))
    assert len(doc.tables[4].rows)==3 and len(doc.tables[5].rows)==len(complete.rights)+1
    complete.empty_tables='제거'
    doc=Document(BytesIO(generate_word(complete)))
    assert len(doc.tables[2].rows)==1

def test_draft_and_final_gate():
    data=generate_word(Report())
    doc=Document(BytesIO(data))
    assert any('초안' in p.text for p in doc.paragraphs)
    assert any('미완료' in p.text for p in doc.paragraphs)
    with pytest.raises(ValueError): generate_word(Report(),final=True)

def test_template_contract_rejects_missing_table(tmp_path,complete):
    path=tmp_path/'bad.docx';Document().save(path)
    with pytest.raises(ValueError): generate_word(complete,template=path)
