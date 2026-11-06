from io import BytesIO
from hashlib import sha256
from copy import deepcopy
from decimal import Decimal
from zipfile import ZipFile
import pytest
from docx import Document
from config.document_fields import HEADERS,SECTIONS,NOTE,FINAL_LABEL,PROVISIONAL_LABEL
from core.word_generator import generate_word,TEMPLATE,TABLE_KEYS

def test_word_structure_and_values(complete):
    digest=sha256(TEMPLATE.read_bytes()).digest()
    data=generate_word(complete,draft=False)
    doc=Document(BytesIO(data))
    text="\n".join(p.text for p in doc.paragraphs)
    assert all(s in text for s in SECTIONS) and NOTE in text
    assert "☑ "+FINAL_LABEL in text and "☐ "+PROVISIONAL_LABEL in text
    assert "☐ "+FINAL_LABEL not in text
    for table,key in zip(doc.tables,TABLE_KEYS): assert [c.text for c in table.rows[0].cells]==HEADERS[key]
    assert doc.tables[0].cell(1,0).text==complete.request.repeat
    assert doc.tables[0].cell(1,3).text==complete.request.purpose
    assert doc.tables[-1].cell(1,3).text=="460,000"
    assert doc.tables[-1].cell(1,4).text=="360,000"
    assert sha256(TEMPLATE.read_bytes()).digest()==digest
    with ZipFile(BytesIO(data)) as z:
        assert b"<w:tbl>" in z.read("word/document.xml")
        assert not any(n.startswith("word/media/") for n in z.namelist())
        assert b"documentProtection" not in z.read("word/settings.xml")

def test_dynamic_rows(complete):
    complete.valuations.append(complete.valuations[0].model_copy(deep=True))
    doc=Document(BytesIO(generate_word(complete,draft=False)))
    assert len(doc.tables[2].rows)==3

def test_draft_blocks_final(complete):
    complete.deposits.tenancy="미확인"
    with pytest.raises(ValueError): generate_word(complete,draft=False)
    text="\n".join(p.text for p in Document(BytesIO(generate_word(complete,draft=True))).paragraphs)
    assert "초안" in text and "☑ "+FINAL_LABEL not in text

def test_empty_rows_option(complete):
    doc=Document(BytesIO(generate_word(complete,empty_tables="제거")))
    assert len(doc.tables[4].rows)==1

def test_template_rejects_wrong_headers(complete,tmp_path):
    doc=Document(TEMPLATE);doc.tables[0].cell(0,0).text="wrong";p=tmp_path/"bad.docx";doc.save(p)
    with pytest.raises(ValueError): generate_word(complete,template=p)
