"""개인정보 없는 독립 정답 기반 가상 등기 PDF/완성 패키지 생성."""
import json
from pathlib import Path
from decimal import Decimal
import pymupdf as fitz
from models.schemas import Report, Request, Target, Owner, Valuation, Right, Deposits
from core.word_generator import create_template, generate_word

ROOT=Path(__file__).resolve().parents[1]
FONT=ROOT/"fonts/NanumGothic-Regular.ttf"

def pdf_document(path: Path, address: str, kind: str, owners: list, rights: list):
    doc=fitz.open();page=doc.new_page(width=595,height=842)
    # CJK 내장 글꼴을 사용하여 OS에 별도 폰트가 없어도 샘플 생성 가능.
    font="sample" if FONT.exists() else "korea"
    if FONT.exists(): page.insert_font(fontname=font,fontfile=str(FONT))
    def text(x,y,s,size=10): page.insert_text((x,y),s,fontname=font,fontsize=size)
    def line(y): page.draw_line((35,y),(560,y),color=(.55,.6,.65),width=.6)
    text(38,30,"TEST / 가상 데이터 — 공적 증명서 아님",12)
    text(170,62,"등기사항증명서 가상 시험자료",16)
    text(38,90,"【표제부】")
    text(40,115,"표시번호    접수                  소재지번 및 건물번호                 표시사항")
    line(122)
    text(40,143,"1    2024년 1월 2일")
    text(180,143,"소재지: "+address)
    text(180,164,"지목: 대" if kind=="토지" else "구조: 철근콘크리트조 / 용도: 업무시설")
    text(180,185,"면적: 120.50 m²")
    if kind=="집합건물":
        text(180,206,"전유부분: 제3층 301호 / 대지권: 1000분의 25")
    y=235
    text(38,y,"【갑구】 소유권에 관한 사항");y+=24
    text(40,y,"순위번호      등기목적               접수                     등기원인       권리자 및 기타사항");y+=8;line(y);y+=22
    text(40,y,"1");text(110,y,"소유권보존");text(230,y,"2024년 1월 2일");text(365,y,"신축");y+=22
    for name,share in owners:
        text(180,y,("공유자: " if len(owners)>1 else "소유자: ")+name+" 지분 "+share);y+=20
    for right in [r for r in rights if r.get("section")=="갑구"]:
        text(40,y,right["rank"]);text(110,y,right["purpose"]);text(230,y,right["date"]);y+=21
        text(180,y,"권리자: "+right["creditor"]);y+=22
    line(y);y+=30
    text(38,y,"【을구】 소유권 이외의 권리에 관한 사항");y+=25
    text(40,y,"순위번호      등기목적               접수                     등기원인       권리자 및 기타사항");y+=8;line(y);y+=22
    for right in [r for r in rights if r.get("section","을구")=="을구"]:
        text(40,y,right["rank"]);text(110,y,right["purpose"]);text(260,y,right["date"]);y+=20
        if right.get("amount"):
            text(180,y,"채권최고액 금"+format(right["amount"],",")+"원");y+=20
        if right.get("creditor"):
            text(180,y,"근저당권자: "+right["creditor"]);y+=20
        if right.get("amount"):
            text(180,y,"채무자: 가상채무자");y+=20
        if right.get("related"):
            text(180,y,right["related"]+"번근저당권설정등기말소");y+=20
        line(y);y+=22
    text(40,814,"TEST / 가상 데이터 | 발급 효력 없음 | 이 문서는 파서 개발용 모형이며 실제 등기 양식은 다를 수 있습니다",8)
    doc.subset_fonts();doc.save(path);doc.close()

def main():
    for folder in ["pdf","expected","packages","completed_reports"]: (ROOT/"sample_data"/folder).mkdir(parents=True,exist_ok=True)
    create_template()
    cases=[
      ("01","단독소유 토지·건물",[("가상소유자하나","1분의 1")],[{"rank":"1","purpose":"근저당권설정","date":"2024년 5월 10일","amount":300000000,"creditor":"가상한빛은행"}]),
      ("02","공동소유 토지·건물",[("가상소유자둘","2분의 1"),("가상소유자셋","2분의 1")],[]),
      ("03","근저당권 집합건물",[("가상소유자넷","1분의 1")],[{"rank":"1","purpose":"근저당권설정","date":"2024년 5월 10일","amount":150000000,"creditor":"가상푸른은행"}]),
      ("04","다중 근저당권",[("가상소유자다섯","1분의 1")],[{"rank":"1","purpose":"근저당권설정","date":"2024년 5월 10일","amount":100000000,"creditor":"가상새봄은행"},{"rank":"2","purpose":"근저당권설정","date":"2024년 6월 11일","amount":200000000,"creditor":"가상누리은행"}]),
      ("05","가압류",[("가상소유자여섯","1분의 1")],[{"section":"갑구","rank":"2","purpose":"가압류","date":"2024년 7월 12일","creditor":"가상채권기관"}]),
      ("06","근저당권 말소",[("가상소유자일곱","1분의 1")],[{"rank":"1","purpose":"근저당권설정","date":"2024년 5월 10일","amount":100000000,"creditor":"가상으뜸은행"},{"rank":"2","purpose":"근저당권말소","date":"2024년 8월 13일","creditor":"","related":"1"}]),
    ]
    packages={}
    for cid,label,owners,rights in cases:
        files=[];addresses=[]
        kinds=["토지","건물"] if cid in ["01","02"] else ["집합건물"]
        for kind in kinds:
            address=f"가상특별시 시험구 모형동 {int(cid)}-1"+(" 제3층 301호" if kind=="집합건물" else "")
            filename=f"case_{cid}_{kind}.pdf";files.append(filename);addresses.append(address)
            pdf_document(ROOT/"sample_data/pdf"/filename,address,kind,owners,rights if kind!="건물" else [])
            truth={"case":cid,"label":label,"file":filename,"address":address,"area":"120.50","owners":[n for n,s in owners],"rights":[{"rank":"1","section":"갑구","kind":"소유권 관련 등기","received":"2024-01-02","amount_won":None,"cancellation":"유효 추정"}]+[{"rank":r["rank"],"section":r.get("section","을구"),"kind":"가압류" if r["purpose"]=="가압류" else "근저당권","received":r["date"].replace("년 ","-").replace("월 ","-").replace("일", ""),"amount_won":str(r["amount"]) if r.get("amount") else None,"cancellation":"검토 필요" if r.get("related") else ("말소" if cid=="06" and r["rank"]=="1" else "유효 추정")} for r in (rights if kind!="건물" else [])]}
            from core.rights_parser import normalize_date
            for expected in truth["rights"][1:]:
                source=next(r for r in rights if r["rank"]==expected["rank"] and r.get("section","을구")==expected["section"])
                expected["received"]=normalize_date(source["date"])
            (ROOT/"sample_data/expected"/(Path(filename).stem+".json")).write_text(json.dumps(truth,ensure_ascii=False,indent=2))
        if cid in ["01","03"]:
            report=Report(evaluation_type="토지·건물" if cid=="01" else "집합건물",request=Request(store="가상시연점포"+cid,amount="100000",considerations="가상자료 기준 담당자 검토 완료"),duplicate="없음",opinion="가상자료에 기초한 시연용 결과입니다. 실제 업무 판단에 사용할 수 없습니다.",completion="최종",rounding="정확값 유지",registry_reviewed=True,attachments_reviewed=True,confirmed=True,attachments=files)
            for kind,address,filename in zip(kinds,addresses,files):
                report.targets.append(Target(kind=kind,address=address,debtor="가상채무자",owners=[Owner(name=n,share="1/1") for n,s in owners],duplicate="없음",related_store="가상시연점포"+cid))
                report.valuations.append(Valuation(kind=kind,address=address,category="대" if kind=="토지" else "해당 없음",area="120.50",amount="600000" if kind!="건물" else "200000",basis="가상 평가증빙에 따른 담당자 직접 확정",reviewed=True))
            # 완성 패키지의 권리는 파서 결과와 독립적으로 작성한다.
            for i,(kind,filename) in enumerate(zip(kinds,files)):
                report.rights.append(Right(id=filename+":owner",document_id=filename,section="갑구",rank="1",received="2024-01-02",kind="소유권 관련 등기",creditor=owners[0][0],cancellation="유효 추정",reviewed=True,note="소유권 보존 원본 대조 완료; 공제대상 아님"))
                if i==0:
                    value=Decimal(rights[0]["amount"])
                    report.rights.append(Right(id=filename+":mortgage",document_id=filename,section="을구",rank="1",received="2024-05-10",kind="근저당권",amount_raw=str(value),amount_won=value,amount_thousand=value/1000,creditor=rights[0]["creditor"],debtor="가상채무자",cancellation="유효 추정",deduction=True,reviewed=True,note="가상 내부 검토로 선순위 공제 확정"))
            report.deposits=Deposits(collective="20000" if cid=="03" else "0",residential="10000" if cid=="01" else "0",commercial="30000" if cid=="01" else "0",stores=1 if cid=="01" else 0,tenancy="있음",attachments="가상 임대차확인서 검토 완료",basis="가상 내부 공제 확인표에서 확정한 금액",reviewed=True)
            (ROOT/"sample_data/packages"/f"package_{cid}.json").write_text(report.model_dump_json(indent=2))
            (ROOT/"sample_data/completed_reports"/f"정답_담보평가결과서_{cid}.docx").write_bytes(generate_word(report,draft=False))
            packages[cid]={"valuation":"800000" if cid=="01" else "600000","senior":"300000" if cid=="01" else "150000","deposits":"40000" if cid=="01" else "20000","collateral":"460000" if cid=="01" else "430000","capacity":"360000" if cid=="01" else "330000"}
    (ROOT/"sample_data/expected/completed_totals.json").write_text(json.dumps(packages,indent=2))
    # 스캔 및 회전된 스캔 PDF: 텍스트 레이어가 없다.
    with fitz.open(ROOT/"sample_data/pdf/case_03_집합건물.pdf") as original:
        pix=original[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        for rotated in [False,True]:
            scan=fitz.open();page=scan.new_page(width=595,height=842)
            page.insert_image(page.rect,stream=pix.tobytes("png"),rotate=90 if rotated else 0)
            scan.save(ROOT/"sample_data/pdf"/("scan_rotated.pdf" if rotated else "scan_case_03.pdf"));scan.close()
    print("생성 완료: 6개 사례 / 등기 PDF 8개 / 스캔 PDF 2개 / 완성 패키지 및 Word 2개")

if __name__=="__main__": main()
