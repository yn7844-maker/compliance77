"""좌표 기반 행 복원 → 섹션 상태기계 → 등기 단위 다중 행 묶음.
실제 원본의 레이아웃 차이는 반드시 사용자 대조 대상이다.
"""
import re
from models.schemas import Extraction, Candidate, Evidence, Owner, PageResult
from core.rights_parser import parse_right, link_cancellations

def page_lines(page: PageResult):
    rows = []
    for block in page.blocks:
        box = block['bbox']
        # 동일 행의 여러 셀을 x 순서로 연결. OCR 픽셀에는 더 큰 허용값 사용.
        tol = 12 if block.get('coordinate_space')=='ocr_pixels' else 4
        row = next((r for r in rows if abs(r[0]-box[1]) <= tol),None)
        if row is None:
            row = [box[1],[]]; rows.append(row)
        row[1].append(block)
    if not rows:
        return [(line,None) for line in page.text.splitlines()]
    return [(' '.join(b['text'] for b in sorted(row,key=lambda b:b['bbox'][0])),
             [min(b['bbox'][0] for b in row),min(b['bbox'][1] for b in row),max(b['bbox'][2] for b in row),max(b['bbox'][3] for b in row)])
            for _,row in sorted(rows,key=lambda r:r[0])]

def parse_registry(pages: list[PageResult], document: str) -> Extraction:
    result = Extraction(document=document,pages=pages)
    section = ''
    rank = ''
    buffer = []
    current_section = ''
    def flush():
        nonlocal buffer
        if buffer and rank:
            result.rights.append(parse_right(current_section,rank,buffer,f'{document}:{current_section}:{len(result.rights)+1}'))
        buffer=[]
    for page in pages:
        if page.error: result.issues.append(f'{document} p.{page.number}: {page.error}')
        for line,box in page_lines(page):
            compact = re.sub(r'\s','',line)
            ev = Evidence(document=document,page=page.number,text=line,bbox=box)
            newsec = next((s for s in ['표제부','갑구','을구'] if s in compact and ('【' in compact or '[' in compact or compact==s)),None)
            if newsec:
                if newsec!=section: flush();rank=''
                section=newsec
                continue
            if not line.strip() or '순위번호' in compact or 'TEST' in line or '가상데이터' in compact: continue
            if section=='표제부':
                patterns = [('address',r'(?:소재지|소재지번)\s*[:：]?\s*(.+)'),('category',r'지\s*목\s*[:：]?\s*([가-힣\s]+)'),('area',r'면\s*적\s*[:：]?\s*([\d,.\s]+)\s*(?:m²|㎡|m2)'),('structure',r'(?:구조및용도|구조)\s*[:：]?\s*(.+)'),('exclusive',r'전유부분\s*[:：]?\s*(.+)'),('land_right',r'대지권\s*[:：]?\s*(.+)')]
                for field,pat in patterns:
                    for m in re.finditer(pat,line):
                        raw=m.group(1).strip()
                        result.candidates.append(Candidate(field=field,raw=raw,value=re.sub(r'[,\s]','',raw) if field in ['area','category'] else raw,evidence=ev))
            elif section in ['갑구','을구']:
                start = re.match(r'^\s*(\d+(?:-\d+)?)\s+(.+)',line)
                if start and any(w in re.sub(r'\s','',start.group(2)) for w in ['권','압류','처분','말소','변경','설정','이전']):
                    flush();rank=start.group(1);current_section=section
                if rank: buffer.append((line,ev))
                # 과거 소유자도 후보로 남기며 현재 소유자라고 확정하지 않는다.
                own = re.search(r'(?:공유자|소유자)\s*[:：]?\s*([가-힣A-Za-z가-힣㈜()]+)(?:\s+지분\s*([\d]+)분의\s*([\d]+))?',line)
                if own:
                    share=f'{own.group(3)}/{own.group(2)}' if own.group(2) else ''
                    result.owners.append(Owner(name=own.group(1),share=share,evidence=ev))
    flush()
    result.issues.extend(link_cancellations(result.rights))
    for field in ['address','category','area']:
        values=[c for c in result.candidates if c.field==field]
        if not values: result.issues.append(f'{document}: {field} 누락, 수동 입력 필요')
        elif len({c.value for c in values})>1:
            for c in values: c.status='충돌'
            result.issues.append(f'{document}: {field} 후보 충돌, 임의 선택 안 함')
    if not result.owners: result.issues.append(f'{document}: 소유자 누락')
    else: result.issues.append(f'{document}: 소유자는 과거 등기 포함 후보입니다. 현재 소유자·지분 대조 필요')
    result.issues.append(f'{document}: 말소선·변경·부기·누락 및 등기 완전성 수동 검토 필요')
    return result
