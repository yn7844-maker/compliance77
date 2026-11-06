"""입력 자료에서 초안을 준비한다. 미확인 업무값은 확정하지 않는다."""
import re
from decimal import InvalidOperation
from models.schemas import Report, PageResult, Extraction
from core.registry_parser import parse_registry
from core.field_mapper import suggest

MAX_TEXT_CHARS = 200_000

def parse_text(text: str, name: str = '붙여넣은 등기 텍스트') -> Extraction:
    if not text.strip(): raise ValueError('등기 내용을 붙여넣어 주세요.')
    if any(ord(c)<32 and c not in '\n\r\t\f' for c in text):
        raise ValueError('읽을 수 없는 텍스트입니다. 암호화 여부를 확인하거나 정상 텍스트를 붙여넣어 주세요.')
    if len(text)>MAX_TEXT_CHARS: raise ValueError('텍스트는 최대 200,000자입니다.')
    pages=text.split('\f')
    if len(pages)>40: raise ValueError('텍스트는 최대 40페이지입니다.')
    return parse_registry([PageResult(number=i+1,text=p) for i,p in enumerate(pages)],name)

def prepare_report(extractions: list[Extraction], evaluation_type: str, attachments: list[str] | None = None) -> Report:
    report=Report(evaluation_type=evaluation_type,attachments=attachments or [])
    for ex in extractions:
        text=re.sub(r'\s','', ''.join(p.text for p in ex.pages[:2]))
        kind='집합건물' if '[집합건물]' in text or '【집합건물】' in text else ('건물' if '[건물]' in text or '【건물】' in text else ('집합건물' if evaluation_type=='집합건물' else '토지'))
        try:
            target,valuation=suggest(ex,kind)
        except (InvalidOperation,ValueError):
            # OCR에서 인식한 면적이 숫자가 아니면 확정하지 않고 누락으로 남긴다.
            safe=ex.model_copy(deep=True)
            safe.candidates=[c for c in safe.candidates if c.field!='area']
            target,valuation=suggest(safe,kind)
            report.extraction_issues.append(f'{ex.document}: 면적 숫자 확인 필요')
        report.targets.append(target);report.valuations.append(valuation)
        report.rights.extend(ex.rights);report.extraction_issues.extend(ex.issues)
    return report
