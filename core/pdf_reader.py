import hashlib
import re
import unicodedata
import pymupdf as fitz
from PIL import Image
from config.calculation_rules import MAX_FILE_BYTES, MAX_PAGES
from core.ocr_engine import OCREngine, TesseractEngine
from models.schemas import PageResult

def safe_filename(name: str) -> str:
    name = unicodedata.normalize("NFKC", name.replace("\\", "/").split("/")[-1])
    name = re.sub(r"[^가-힣a-zA-Z0-9_. -]", "_", name).strip(". ")[:100]
    return name or "document.pdf"

def document_id(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]

def open_pdf(data: bytes):
    if not data or len(data)>MAX_FILE_BYTES: raise ValueError("PDF는 20MB 이하만 허용합니다")
    if not data.startswith(b"%PDF-"): raise ValueError("PDF 파일 형식이 아닙니다")
    try: doc=fitz.open(stream=data,filetype="pdf")
    except Exception: raise ValueError("손상되었거나 지원하지 않는 PDF입니다") from None
    if doc.needs_pass or not 0<doc.page_count<=MAX_PAGES:
        doc.close(); raise ValueError("암호화 PDF 또는 허용 페이지 수(1~50) 초과")
    return doc

def read_pdf(data: bytes, engine: OCREngine | None = None) -> list[PageResult]:
    results=[]
    with open_pdf(data) as doc:
        for i,page in enumerate(doc):
            words=[{"text":w[4],"bbox":list(w[:4]),"confidence":None} for w in page.get_text("words",sort=True)]
            text=page.get_text(sort=True)
            meaningful=sum(c.isalnum() for c in text)
            broken=text.count("�")/max(1,len(text))
            if meaningful>=25 and broken<0.02:
                results.append(PageResult(number=i+1,text=text,words=words))
                continue
            try:
                # 픽셀 수 상한을 두어 비정상 대형 페이지로 인한 메모리 폭증 방지.
                scale=min(2.5,(20_000_000/max(1,page.rect.width*page.rect.height))**0.5)
                pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
                image=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
                result=(engine or TesseractEngine()).recognize(image,i+1)
                if not result.text.strip(): result.error="OCR 인식 텍스트 없음"
                # 원본 PDF 좌표로 복원. 회전 보정된 좌표의 역변환도 적용.
                for w in result.words:
                    x0,y0,x1,y1=w["bbox"]
                    w["layout_bbox"]=[x0/scale,y0/scale,x1/scale,y1/scale]
                    corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
                    def inv(x,y):
                        if result.rotation==90: return y,pix.height-x
                        if result.rotation==180: return pix.width-x,pix.height-y
                        if result.rotation==270: return pix.width-y,x
                        return x,y
                    points=[inv(x,y) for x,y in corners]
                    w["bbox"]=[min(x for x,y in points)/scale,min(y for x,y in points)/scale,max(x for x,y in points)/scale,max(y for x,y in points)/scale]
                results.append(result)
            except Exception:
                # 엔진 예외 원문은 개인정보를 포함할 수 있으므로 출력하지 않는다.
                results.append(PageResult(number=i+1,text=text,words=words,ocr=True,error="OCR 실패: 로컬 엔진·한국어 데이터 설치 상태를 확인하고 수동 검토하세요"))
    return results

def render_page(data: bytes, number: int) -> bytes:
    with open_pdf(data) as doc:
        page=doc[max(0,min(number-1,doc.page_count-1))]
        scale=min(1.5,(4_000_000/max(1,page.rect.width*page.rect.height))**0.5)
        return page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).tobytes("png")
