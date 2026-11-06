import pytest
import pymupdf as fitz
from core.pdf_reader import read_pdf, safe_filename, open_pdf
from models.schemas import PageResult

class FailEngine:
    def recognize(self,*args): raise RuntimeError("private OCR content")
class StubEngine:
    def recognize(self,image,number): return PageResult(number=number,text="가상 인식 결과",words=[{"text":"가상","bbox":[10,10,20,20]}],ocr=True,confidence=92)

def test_text_skips_ocr(root):
    p=read_pdf((root/"sample_data/pdf/case_01_토지.pdf").read_bytes(),FailEngine())
    assert p[0].text and p[0].words and not p[0].ocr and not p[0].error

def test_failure_is_visible(root):
    p=read_pdf((root/"sample_data/pdf/scan_case_03.pdf").read_bytes(),FailEngine())
    assert p[0].ocr and p[0].error and "private" not in p[0].error

def test_stub_ocr(root):
    p=read_pdf((root/"sample_data/pdf/scan_case_03.pdf").read_bytes(),StubEngine())
    assert p[0].confidence==92 and p[0].words[0]["bbox"][0]<10

@pytest.mark.parametrize("data",[b"",b"not pdf",b"%PDF-broken",b"%PDF-"+b"0"*(21*1024*1024)])
def test_invalid(data):
    with pytest.raises(ValueError): open_pdf(data)

def test_page_limit():
    doc=fitz.open()
    for _ in range(51): doc.new_page()
    with pytest.raises(ValueError): open_pdf(doc.tobytes())

def test_encrypted(root):
    d=fitz.open(root/"sample_data/pdf/case_01_토지.pdf")
    data=d.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,user_pw="test")
    with pytest.raises(ValueError): open_pdf(data)

def test_filename():
    assert safe_filename("../../secret.pdf")=="secret.pdf"
    assert "/" not in safe_filename("..\\file.pdf")

@pytest.mark.ocr
@pytest.mark.parametrize("name",["scan_case_03.pdf","scan_rotated.pdf"])
def test_real_ocr(root,name):
    import shutil, pytesseract
    if not shutil.which("tesseract") or "kor" not in pytesseract.get_languages(): pytest.skip("로컬 한국어 Tesseract 미설치")
    pages=read_pdf((root/"sample_data/pdf"/name).read_bytes())
    assert pages[0].ocr and not pages[0].error
    assert "150,000,000" in pages[0].text or "150000000" in pages[0].text.replace(",","")
    assert pages[0].words
    from core.registry_parser import parse_registry
    parsed=parse_registry(pages,name)
    assert any(r.kind=="근저당권" and str(r.amount_won)=="150000000" for r in parsed.rights)
    assert any(f.field=="소유자" and f.value=="가상소유자넷 | 1/1" for f in parsed.facts)
    assert any(f.field=="면적" and f.value=="120.50" for f in parsed.facts)
    assert any(f.field=="소재지" and "3-1" in f.value for f in parsed.facts)
    assert all(not r.reviewed for r in parsed.rights)
