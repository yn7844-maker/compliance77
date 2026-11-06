"""로컬 OCR 어댑터. PaddleOCR는 선택 의존성으로 별도 설치한다."""
from pathlib import Path
from typing import Protocol
import io
from PIL import Image, ImageOps, ImageFilter
from models.schemas import PageResult

class OCREngine(Protocol):
    def recognize(self, image: bytes, page: int) -> PageResult: ...

class TesseractEngine:
    def __init__(self, language: str = 'kor+eng', tessdata: str | None = None):
        self.language = language
        local = Path(__file__).resolve().parents[1] / '.local/tessdata'
        self.tessdata = tessdata or (str(local) if (local / 'kor.traineddata').exists() else None)

    def recognize(self, image: bytes, page: int) -> PageResult:
        import pytesseract
        from pytesseract import Output
        result = PageResult(number=page, used_ocr=True)
        try:
            im = Image.open(io.BytesIO(image)).convert('RGB')
            cfg = f'--tessdata-dir "{self.tessdata}"' if self.tessdata else ''
            available = pytesseract.get_languages(config=cfg)
            if 'kor' not in available: raise RuntimeError('한국어 OCR 언어 데이터(kor)가 없습니다.')
            try:
                osd = pytesseract.image_to_osd(im, config=cfg, output_type=Output.DICT)
                result.rotation = int(osd.get('rotate', 0))
                if result.rotation: im = im.rotate(-result.rotation, expand=True)
            except pytesseract.TesseractError:
                pass  # 짧은 페이지의 OSD 실패는 아래 OCR에서 별도로 검토한다.
            im = ImageOps.autocontrast(ImageOps.grayscale(im)).filter(ImageFilter.SHARPEN)
            data = pytesseract.image_to_data(im, lang=self.language, config=cfg + ' --psm 6', output_type=Output.DICT, timeout=90)
            lines = {}
            scores = []
            for i, word in enumerate(data['text']):
                if not word.strip(): continue
                x,y,w,h = [data[k][i] for k in ('left','top','width','height')]
                conf = float(data['conf'][i])
                block = {'text': word, 'bbox': [x,y,x+w,y+h], 'confidence': conf, 'coordinate_space': 'ocr_pixels'}
                result.blocks.append(block)
                key = (data['block_num'][i],data['par_num'][i],data['line_num'][i])
                lines.setdefault(key, []).append(word)
                if conf >= 0: scores.append(conf)
            result.text = '\n'.join(' '.join(words) for words in lines.values())
            result.confidence = sum(scores)/len(scores) if scores else 0
            if not result.text.strip(): result.error = 'OCR에서 텍스트를 찾지 못했습니다.'
            elif result.confidence < 65: result.error = 'OCR 신뢰도가 낮습니다. 원본 대조 필요'
        except Exception as exc:
            result.error = f'OCR 처리 실패 ({type(exc).__name__}). 한국어 데이터·엔진 및 원본을 확인하세요.'
        return result

class PaddleEngine:
    """PaddleOCR 3.x 어댑터. 모델은 사전에 사내 승인 경로에 설치할 것."""
    def __init__(self, detector_dir: str, recognizer_dir: str):
        if not Path(detector_dir).is_dir() or not Path(recognizer_dir).is_dir():
            raise ValueError('사전에 준비한 로컬 Paddle 모델 폴더가 필요합니다.')
        from paddleocr import PaddleOCR
        self.engine = PaddleOCR(text_detection_model_dir=detector_dir, text_recognition_model_dir=recognizer_dir,
                                use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)

    def recognize(self, image: bytes, page: int) -> PageResult:
        import numpy as np
        result = PageResult(number=page,used_ocr=True)
        try:
            preds = list(self.engine.predict(np.array(Image.open(io.BytesIO(image)).convert('RGB'))))
            for pred in preds:
                for text,score,box in zip(pred['rec_texts'],pred['rec_scores'],pred['rec_polys']):
                    pts = box.tolist()
                    result.blocks.append({'text':text,'bbox':[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)],'confidence':float(score)*100,'coordinate_space':'ocr_pixels'})
            result.text = '\n'.join(b['text'] for b in result.blocks)
            result.confidence = sum(b['confidence'] for b in result.blocks)/len(result.blocks) if result.blocks else 0
            if not result.text: result.error = 'OCR 결과 없음'
        except Exception as exc:
            result.error = f'PaddleOCR 처리 실패 ({type(exc).__name__})'
        return result
