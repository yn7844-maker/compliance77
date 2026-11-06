import re
from datetime import date
from decimal import Decimal
from models.schemas import Right, Evidence

KINDS=[("근저당권","근저당권"),("저당권","저당권"),("가압류","가압류"),("가처분","가처분"),("압류","압류"),("전세권","전세권"),("소유권","소유권 관련 등기")]

def normalize_date(text: str) -> str:
    m=re.search(r"(\d{4})\s*[년.\-/]\s*(\d{1,2})\s*[월.\-/]\s*(\d{1,2})",text)
    if not m: return ""
    try: return date(*map(int,m.groups())).isoformat()
    except ValueError: return ""

def parse_amount(text: str):
    text=re.sub(r"\s+","",text)
    matches=re.findall(r"(?:채권최고액|채권액|전세금)\s*금?\s*([\d,]+)\s*원",text)
    values=list(dict.fromkeys(Decimal(x.replace(",","")) for x in matches))
    return values

def normalize_labels(text: str) -> str:
    for label in ["소재지","소유자","공유자","지분","면적","지목","전유부분","대지권","구조","용도","채권최고액","근저당권자","저당권자","전세권자","권리자","채권자","채무자"]:
        text=re.sub(r"\s*".join(re.escape(c) for c in label),label,text)
    return text

def parse_right(rank: str, section: str, chunks: list[Evidence], index: int) -> Right:
    raw=normalize_labels("\n".join(e.text for e in chunks))
    compact=re.sub(r"\s+","",raw)
    kind=next((v for k,v in KINDS if k in compact),"기타 등기")
    amounts=parse_amount(raw)
    creditor=re.search(r"(?:근저당권자|저당권자|전세권자|권리자|채권자|소유자|공유자)\s*[:：]?\s*([^\n]+)",raw)
    debtor=re.search(r"채무자\s*[:：]?\s*([^\n]+)",raw)
    related=re.search(r"(\d+(?:-\d+)?)번(?:근저당권|저당권|등기|가압류|압류|전세권)?(?:설정)?(?:등기)?(?:말소|변경)",compact)
    operation=any(x in compact for x in ["말소","변경","이전","경정"])
    return Right(id=f"{chunks[0].document_id}:{section}:{rank}:{index}",document_id=chunks[0].document_id,section=section,rank=rank,received=normalize_date(raw),kind=kind,amount_raw="\n".join(e.text for e in chunks if any(label in re.sub(r"\s+","",e.text) for label in ["채권최고액","채권액","전세금"])),amount_won=amounts[0] if len(amounts)==1 else None,amount_thousand=amounts[0]/1000 if len(amounts)==1 else None,creditor=creditor[1].strip() if creditor else "",debtor=debtor[1].strip() if debtor else "",cancellation="검토 필요" if operation or "-" in rank else "유효 추정",related_rank=related[1] if related else "",note="담당자 권리·순위 확인 필요"+("; 금액 충돌" if len(amounts)>1 else "")+("; 변경·말소 연결 확인 필요" if operation else ""),evidence=chunks)

def link_cancellations(rights: list[Right]):
    for r in rights:
        raw=re.sub(r"\s+","","".join(e.text for e in r.evidence))
        if r.related_rank:
            candidates=[x for x in rights if x.document_id==r.document_id and x.section==r.section and x.rank==r.related_rank and x.id!=r.id]
            if len(candidates)==1 and "말소" in raw:
                candidates[0].cancellation="말소"
                candidates[0].note+="; 말소 연결: "+r.rank+" (담당자 확인 필요)"
            else:
                for x in candidates: x.cancellation="검토 필요"
