"""좌표 기반 행 병합 + 섹션/순위 기반 등기 단위 파싱. 알 수 없는 구조는 검토 요청."""
import re
from models.schemas import Evidence, Fact, Registry, PageResult
from core.rights_parser import parse_right, link_cancellations, normalize_labels

def lines_from_page(page: PageResult):
    if page.ocr and page.words and all("line" in w for w in page.words):
        groups={}
        for word in page.words: groups.setdefault(tuple(word["line"]),[]).append(word)
        out=[]
        for words in groups.values():
            words=sorted(words,key=lambda w:w.get("layout_bbox",w["bbox"])[0])
            bbox=[min(w["bbox"][0] for w in words),min(w["bbox"][1] for w in words),max(w["bbox"][2] for w in words),max(w["bbox"][3] for w in words)]
            out.append((" ".join(w["text"] for w in words),bbox,min(w.get("layout_bbox",w["bbox"])[0] for w in words)))
        return out
    lines=[]
    # 같은 y의 셀 조각을 하나의 행으로 연결. 열 경계는 bbox로 보존.
    for word in sorted(page.words,key=lambda w:(round((w.get("layout_bbox",w["bbox"])[1]+w.get("layout_bbox",w["bbox"])[3])/8),w.get("layout_bbox",w["bbox"])[0])):
        x0,y0,x1,y1=word.get("layout_bbox",word["bbox"])
        hit=next((line for line in reversed(lines[-4:]) if abs(line["y"]-(y0+y1)/2)<5.5),None)
        if hit is None: lines.append({"y":(y0+y1)/2,"words":[word]})
        else: hit["words"].append(word)
    out=[]
    for line in sorted(lines,key=lambda l:l["y"]):
        words=sorted(line["words"],key=lambda w:w.get("layout_bbox",w["bbox"])[0])
        out.append((" ".join(w["text"] for w in words),[min(w["bbox"][0] for w in words),min(w["bbox"][1] for w in words),max(w["bbox"][2] for w in words),max(w["bbox"][3] for w in words)],min(w.get("layout_bbox",w["bbox"])[0] for w in words)))
    return out or [(s,[],0) for s in page.text.splitlines()]

def parse_registry(pages: list[PageResult], doc_id: str) -> Registry:
    result=Registry(document_id=doc_id)
    section=""; rank=""; chunks=[]; counter=0
    def flush():
        nonlocal chunks,counter
        if rank and chunks:
            counter+=1;result.rights.append(parse_right(rank,section,chunks,counter))
        chunks=[]
    patterns={"소재지":r"소재지(?:\s*[:：]\s*|\s+)(.+)","지목":r"지목\s*[:：]?\s*([가-힣]+)","면적":r"면적\s*[:：]?\s*([\d,.]+)\s*(?:㎡|m²|m2)?", "구조용도":r"(?:구조|용도)\s*[:：]?\s*(.+)","전유부분":r"전유부분\s*[:：]?\s*(.+)","대지권":r"대지권\s*[:：]?\s*(.+)"}
    for page in pages:
        if page.error: result.warnings.append(f"{page.number}페이지: 인식 실패, 수동 대조 필요")
        page_lines=lines_from_page(page)
        left_edge=min((x for text,bbox,x in page_lines if bbox),default=0)
        for source_text,bbox,layout_x in page_lines:
            text=normalize_labels(source_text)
            compact=re.sub(r"\s+","",text)
            ev=Evidence(document_id=doc_id,page=page.number,text=source_text,bbox=bbox,ocr=page.ocr,confidence=page.confidence)
            heading=next((s for s in ["표제부","갑구","을구"] if f"【{s}】" in compact or f"[{s}]" in compact or compact.startswith(s+"(")),None)
            if heading:
                if heading != section:
                    flush();rank="";section=heading
                continue
            if "TEST" in text or "순위번호" in compact or "표시번호" in compact or "등기목적" in compact and "접수" in compact: continue
            if section=="표제부":
                for field,pattern in patterns.items():
                    match=re.search(pattern,text)
                    if match: result.facts.append(Fact(field=field,value=match[1].replace(",","") if field=="면적" else match[1].strip(),raw=match[0],status="사용자 확인 필요",evidence=ev))
            elif section in ["갑구","을구"]:
                # 순위는 첫 열에서 시작한 경우만 사용한다. 접수번호/금액을 순위로 오인하지 않는다.
                m=re.match(r"^(\d+(?:-\d+)?)\s+(?=[가-힣])",text)
                at_first_column=not bbox or layout_x<left_edge+65
                if m and at_first_column:
                    flush();rank=m[1]
                if rank: chunks.append(ev)
                elif any(x in compact for x in ["근저당권","소유자","가압류","전세권"]):
                    result.warnings.append(f"{page.number}페이지: 순위 열 식별 실패")
                for match in re.finditer(r"(?:소유자|공유자)\s*[:：]?\s*([가-힣A-Za-z\s]+?)(?:\s*지분\s*(\d+)\s*분\s*의\s*(\d+)|$)",text):
                    share=f"{match[3]}/{match[2]}" if match[2] else "지분 확인 필요"
                    result.facts.append(Fact(field="소유자",value=re.sub(r"\s+","",match[1])+" | "+share,raw=match[0],status="사용자 확인 필요",evidence=ev))
    flush();link_cancellations(result.rights)
    for field in patterns:
        values={f.value for f in result.facts if f.field==field}
        if len(values)>1:
            for f in result.facts:
                if f.field==field: f.status="충돌"
        if not values and field in ["소재지","면적"]:
            result.facts.append(Fact(field=field,status="누락"))
    if not result.rights: result.warnings.append("등기 단위를 인식하지 못했습니다. 권리 없음으로 간주하지 말고 원본을 확인하세요")
    result.warnings.append("소유권 이력·순위·변경·말소 및 시각적 취소선은 담당자 원본 대조가 필요합니다")
    return result
