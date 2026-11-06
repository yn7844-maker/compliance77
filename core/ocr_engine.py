"""로컬 OCR 전용 어댑터. 엔진/모델 미설치 시 페이지 오류로 반환한다."""
import os
import re
from typing import Protocol
from PIL import Image, ImageOps, ImageFilter
from models.schemas import PageResult

class OCREngine(Protocol):
    def recognize(self, image: Image.Image, number: int) -> PageResult: ...

class TesseractEngine:
    def recognize(self, image: Image.Image, number: int) -> PageResult:
        import pytesseract
        from pytesseract import Output
        if os.getenv("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
        if "kor" not in pytesseract.get_languages():
            raise RuntimeError("Tesseract 한국어 언어 데이터(kor)가 없습니다")
        rotation = 0
        try:
            osd = pytesseract.image_to_osd(image, timeout=20)
            match = re.search(r"Rotate: (\d+)", osd)
            rotation = int(match[1]) if match else 0
        except pytesseract.TesseractError:
            pass
        image = image.rotate(-rotation, expand=True)
        image = ImageOps.autocontrast(ImageOps.grayscale(image)).filter(ImageFilter.SHARPEN)
        data = pytesseract.image_to_data(image, lang="kor+eng", config="--psm 6", output_type=Output.DICT, timeout=90)
        words, lines = [], {}
        for i, text in enumerate(data["text"]):
            if not text.strip(): continue
            x,y,w,h = (data[k][i] for k in ["left","top","width","height"])
            confidence = float(data["conf"][i])
            words.append({"text":text,"bbox":[x,y,x+w,y+h],"confidence":confidence})
            key=tuple(data[k][i] for k in ["block_num","par_num","line_num"])
            words[-1]["line"]=list(key)
            lines.setdefault(key,[]).append(text)
        return PageResult(number=number, text="\n".join(" ".join(x) for x in lines.values()), words=words, ocr=True, confidence=sum(w["confidence"] for w in words)/len(words) if words else None, rotation=rotation)

class PaddleEngine:
    def __init__(self, detection_dir: str, recognition_dir: str, classifier_dir: str):
        # 로컬 모델만 허용하여 실행 중 자동 다운로드를 방지한다.
        if not all(os.path.isdir(p) for p in [detection_dir,recognition_dir,classifier_dir]):
            raise ValueError("승인된 로컬 Paddle 모델 폴더 3개를 지정하세요")
        from paddleocr import PaddleOCR
        self.engine = PaddleOCR(lang="korean", use_angle_cls=True, det_model_dir=detection_dir, rec_model_dir=recognition_dir, cls_model_dir=classifier_dir, show_log=False)
    def recognize(self, image: Image.Image, number: int) -> PageResult:
        import numpy as np
        words=[]
        for group in self.engine.ocr(np.array(image), cls=True) or []:
            for box, (text, conf) in group or []:
                words.append({"text":text,"bbox":[min(p[0] for p in box),min(p[1] for p in box),max(p[0] for p in box),max(p[1] for p in box)],"confidence":float(conf)*100})
        return PageResult(number=number,text="\n".join(w["text"] for w in words),words=words,ocr=True,confidence=sum(w["confidence"] for w in words)/len(words) if words else None)
