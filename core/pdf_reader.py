import re
from pathlib import PurePath
import fitz
from models.schemas import PageResult
from core.ocr_engine import OCREngine, TesseractEngine

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 40
MAX_TOTAL_BYTES = 60 * 1024 * 1024
MAX_FILES = 12

def validate_filename(name: str) -> str:
    if not name or len(name) > 150 or '/' in name or '\\' in name or any(ord(c)<32 for c in name) or name.startswith('.'):
        raise ValueError('파일명에 경로·제어문자를 사용할 수 없습니다(150자 이하).')
    if PurePath(name).suffix.lower() != '.pdf': raise ValueError('PDF 파일만 업로드하세요.')
    return name

def open_pdf(data: bytes, name: str) -> fitz.Document:
    validate_filename(name)
    if len(data) > MAX_BYTES: raise ValueError('파일당 최대 20MB입니다.')
    if not data.startswith(b'%PDF-'): raise ValueError('PDF 파일 형식이 아닙니다.')
    try: doc = fitz.open(stream=data,filetype='pdf')
    except Exception: raise ValueError('손상되었거나 읽을 수 없는 PDF입니다.') from None
    if doc.is_encrypted:
        doc.close(); raise ValueError('암호화된 PDF는 지원하지 않습니다.')
    if not 1 <= doc.page_count <= MAX_PAGES:
        doc.close(); raise ValueError('PDF는 1~40페이지여야 합니다.')
    return doc

def text_quality(text: str) -> bool:
    chars = re.sub(r'\s','',text)
    return len(chars) >= 40 and sum(c.isalnum() for c in chars)/len(chars) > .65 and chars.count('\ufffd')/len(chars) < .05

def inspect_pdf(data: bytes, name: str) -> dict:
    with open_pdf(data,name) as doc:
        return {'파일명':name,'페이지 수':len(doc),'텍스트 추출 가능 페이지':sum(text_quality(p.get_text()) for p in doc)}

def read_pdf(data: bytes, name: str, engine: OCREngine | None = None, use_ocr: bool = True) -> list[PageResult]:
    results = []
    with open_pdf(data,name) as doc:
        for page in doc:
            text = page.get_text(sort=True)
            blocks = []
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:
                        blocks.append({'text':span['text'],'bbox':list(span['bbox']),'coordinate_space':'pdf_points'})
            if text_quality(text):
                results.append(PageResult(number=page.number+1,text=text,blocks=blocks))
            elif not use_ocr:
                results.append(PageResult(number=page.number+1,text=text,blocks=blocks,error='텍스트 품질 부족: OCR 필요'))
            else:
                # 한 페이지 최대 약 12MP, 큰 도면의 메모리 과점유 방지
                scale = min(2.5, (12_000_000/max(page.rect.width*page.rect.height,1))**.5)
                result = (engine or TesseractEngine()).recognize(page.get_pixmap(matrix=fitz.Matrix(scale,scale)).tobytes('png'),page.number+1)
                results.append(result)
    return results

def page_image(data: bytes, name: str, number: int) -> bytes:
    with open_pdf(data,name) as doc:
        p = doc[number-1]
        scale = min(1.5, (4_000_000/max(p.rect.width*p.rect.height,1))**.5)
        return p.get_pixmap(matrix=fitz.Matrix(scale,scale)).tobytes('png')
