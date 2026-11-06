from pathlib import Path
import fitz,pytest
from core.pdf_reader import read_pdf,open_pdf,validate_filename,MAX_BYTES
from models.schemas import PageResult
ROOT=Path(__file__).resolve().parents[1]

def test_text_skips_ocr():
    class MustNotRun:
        def recognize(self,*args): raise AssertionError('텍스트 PDF OCR 호출 금지')
    pages=read_pdf((ROOT/'sample_data/pdf/case03_집합건물.pdf').read_bytes(),'x.pdf',MustNotRun())
    assert len(pages)==2 and all(not p.used_ocr for p in pages)

def test_ocr_failure_preserved():
    class Failed:
        def recognize(self,image,page): return PageResult(number=page,used_ocr=True,error='엔진 없음')
    pages=read_pdf((ROOT/'sample_data/pdf/case03_scan.pdf').read_bytes(),'scan.pdf',Failed())
    assert all(p.error=='엔진 없음' and p.used_ocr for p in pages)

@pytest.mark.parametrize('name',['../x.pdf','a\\b.pdf','.secret.pdf','bad\n.pdf','x.docx'])
def test_filename(name):
    with pytest.raises(ValueError): validate_filename(name)

def test_pdf_limits():
    with pytest.raises(ValueError): open_pdf(b'notpdf','x.pdf')
    with pytest.raises(ValueError): open_pdf(b'%PDF-'+b'0'*MAX_BYTES,'x.pdf')
    doc=fitz.open()
    for _ in range(41): doc.new_page()
    with pytest.raises(ValueError): open_pdf(doc.tobytes(),'x.pdf')

def test_encrypted():
    doc=fitz.open();doc.new_page()
    with pytest.raises(ValueError): open_pdf(doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,user_pw='fake'),'x.pdf')

@pytest.mark.ocr
def test_real_korean_ocr():
    pages=read_pdf((ROOT/'sample_data/pdf/case03_scan.pdf').read_bytes(),'scan.pdf')
    assert all(p.used_ocr and p.text and p.blocks for p in pages)
    assert '채권최고액' in pages[1].text.replace(' ','')
    from core.registry_parser import parse_registry
    from decimal import Decimal
    ex=parse_registry(pages,'scan.pdf')
    assert any(r.amount_won==Decimal('300000000') for r in ex.rights)

@pytest.mark.ocr
def test_rotated_scan_orientation():
    with fitz.open(ROOT/'sample_data/pdf/case03_scan.pdf') as doc:
        for p in doc: p.set_rotation(90)
        data=doc.tobytes()
    pages=read_pdf(data,'rotated.pdf')
    assert all(p.rotation==270 for p in pages)
    assert '채권최고액' in pages[1].text.replace(' ','')
