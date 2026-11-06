import re
from datetime import date
from decimal import Decimal
from models.schemas import Right, Evidence

DATE = r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일'
AMOUNT = r'(?:채권최고액|채권액|전세금)\s*(?:금)?\s*([\d,]+)\s*원'
KINDS = ['근저당권','저당권','가압류','압류','가처분','전세권','소유권']

def parse_date(text: str) -> str:
    m = re.search(DATE,text)
    if not m: return ''
    try: return date(*map(int,m.groups())).isoformat()
    except ValueError: return ''

def parse_right(section: str, rank: str, lines: list[tuple[str,Evidence]], uid: str) -> Right:
    text = '\n'.join(t for t,_ in lines)
    purpose_text = re.sub(r'^\s*' + re.escape(rank) + r'\s+', '', text, count=1)
    compact = re.sub(r'[ \t]','',purpose_text)
    kind = next((k for k in KINDS if k in compact),'기타 등기')
    amounts = re.findall(AMOUNT,compact)
    creditor = re.search(r'(?:근저당권자|저당권자|전세권자|권리자|채권자)\s*[:：]?\s*([^\n]+)',text)
    debtor = re.search(r'채무자\s*[:：]?\s*([^\n]+)',text)
    status = '유효 여부 검토'
    target = ''
    notes = ['선순위 및 현재 유효 여부는 담당자 확인 필요']
    if '말소' in compact:
        status = '변경 검토'
        m = re.search(r'(\d+(?:-\d+)?)번(?:근저당권|저당권|전세권|등기|가압류|압류|가처분|소유권)?(?:설정)?말소',compact)
        target = m.group(1) if m else ''
        notes.append('말소 등기: 연결 대상 및 원문 대조 필요')
    elif any(w in compact for w in ['변경','이전','부기']):
        status = '변경 검토'
        notes.append('변경·이전·부기 연결 검토')
    if len(set(amounts)) > 1: notes.append('채권금액 후보 충돌')
    amt = Decimal(amounts[0].replace(',','')) if len(set(amounts)) == 1 else None
    return Right(id=uid,section=section,rank=rank,receipt_date=parse_date(text),kind=kind,
                 amount_raw=' / '.join(amounts),amount_won=amt,creditor=creditor.group(1).strip() if creditor else '',
                 debtor=debtor.group(1).strip() if debtor else '',status=status,target_rank=target,
                 notes='; '.join(notes),evidence=[e for _,e in lines])

def link_cancellations(rights: list[Right]) -> list[str]:
    issues = []
    for r in rights:
        if r.target_rank:
            matches = [x for x in rights if x.section==r.section and x.rank==r.target_rank and x.id!=r.id]
            if len(matches)==1:
                matches[0].status='말소'
                matches[0].notes += f'; {r.rank}번 말소기재 연결(사용자 확인 필요)'
            else: issues.append(f'{r.section} {r.rank}: 말소 대상 연결 불명확')
    return issues
