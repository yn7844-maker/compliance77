from copy import deepcopy
from io import BytesIO
from pathlib import Path
from decimal import Decimal
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from config.document_fields import HEADERS, SECTIONS, NOTE, FINAL_LABEL, PROVISIONAL_LABEL
from core.collateral_calculator import calculate, fmt
from core.validation import validate_report
from core.pdf_reader import safe_filename
from models.schemas import Report

TEMPLATE = Path(__file__).resolve().parents[1]/"templates/collateral_report.docx"
TABLE_KEYS = ["request","target","valuation","valuation","valuation","rights","deposits","summary"]

def _table(doc, key):
    table=doc.add_table(rows=2,cols=len(HEADERS[key]));table.style="Table Grid"
    table.autofit=False
    for c,text in zip(table.rows[0].cells,HEADERS[key]):
        c.text=text
        shade=OxmlElement("w:shd");shade.set(qn("w:fill"),"E8EEF5");c._tc.get_or_add_tcPr().append(shade)
        for run in c.paragraphs[0].runs: run.bold=True
    repeat=OxmlElement("w:tblHeader");table.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in table.rows:
        for cell in row.cells: cell.width=Cm(26.5/len(row.cells))
    return table

def create_template(path: Path = TEMPLATE):
    doc=Document();section=doc.sections[0]
    section.orientation=WD_ORIENT.LANDSCAPE;section.page_width=Cm(29.7);section.page_height=Cm(21)
    section.top_margin=Cm(1.2);section.bottom_margin=Cm(1.2);section.left_margin=Cm(1.5);section.right_margin=Cm(1.5)
    for name in ["Normal","Title","Heading 1","Heading 2"]:
        style=doc.styles[name];style.font.name="NanumGothic";style.font.color.rgb=RGBColor(0,0,0)
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),"NanumGothic")
        style.font.size=Pt(9 if name=="Normal" else 12)
        style.paragraph_format.space_after=Pt(4)
    for style in doc.styles:
        if style.type==1:
            for border in list(style.element.iter(qn("w:pBdr"))): border.getparent().remove(border)
    doc.styles["Title"].font.size=Pt(20)
    doc.add_paragraph("담보평가결과서",style="Title")
    doc.add_paragraph("{{status}} | 작성일 {{date}} | 금액 단위 천원")
    doc.add_paragraph("TEST / 가상 데이터 전용 시연 양식")
    for i,heading in enumerate(SECTIONS):
        if i==3: doc.add_page_break()
        doc.add_paragraph(heading,style="Heading 1")
        if i==0: _table(doc,"request")
        elif i==1: _table(doc,"target")
        elif i==2:
            for label in ["(가) 토지","(나) 건물","(다) 집합건물(외부감정 포함)"]:
                doc.add_paragraph(label);_table(doc,"valuation")
        elif i==3: _table(doc,"rights")
        elif i==4: _table(doc,"deposits")
        elif i==5:
            _table(doc,"summary");doc.add_paragraph(NOTE)
        else:
            doc.add_paragraph("{{opinion}}")
            doc.add_paragraph("{{final_check}} "+FINAL_LABEL)
            doc.add_paragraph("{{provisional_check}} "+PROVISIONAL_LABEL)
            doc.add_paragraph("{{review_notes}}")
    path.parent.mkdir(parents=True,exist_ok=True);doc.save(path)

def _value(x):
    if x is None or x=="": return "미입력/검토 필요"
    return fmt(x) if isinstance(x,Decimal) else str(x)

def _fill(table, rows):
    proto=deepcopy(table.rows[1]._tr)
    for row in list(table.rows)[1:]: table._tbl.remove(row._tr)
    for values in rows:
        table._tbl.append(deepcopy(proto))
        row=table.rows[-1]
        for cell,value in zip(row.cells,values): cell.text=_value(value)
        no_split=OxmlElement("w:cantSplit");row._tr.get_or_add_trPr().append(no_split)

def generate_word(report: Report, *, draft: bool = True, template: Path = TEMPLATE, empty_tables: str = "유지") -> bytes:
    errors=validate_report(report)
    if not draft and errors: raise ValueError("최종 문서 생성 불가: "+"; ".join(errors))
    if not template.exists(): raise FileNotFoundError("템플릿 생성 스크립트를 먼저 실행하세요")
    doc=Document(template)
    if len(doc.tables)!=len(TABLE_KEYS): raise ValueError("템플릿 표 수 불일치: 교체용 양식 어댑터를 작성하세요")
    for table,key in zip(doc.tables,TABLE_KEYS):
        if [c.text for c in table.rows[0].cells]!=HEADERS[key]: raise ValueError("템플릿 열 헤더 불일치")
    t=calculate(report);d=report.deposits;q=report.request
    rows=[[[q.repeat,q.store,q.contract,q.purpose,q.amount,q.considerations]],
          [[x.kind,x.address,x.debtor,"\n".join(o.name+" ("+o.share+")" for o in x.owners),x.duplicate,x.related_store] for x in report.targets]]
    for kind in ["토지","건물","집합건물"]:
        vals=[[v.address,v.category,v.area,v.public_price if v.public_price is not None else "해당 없음 (직접평가)",v.rate if v.rate is not None else "해당 없음 (직접평가)",v.amount] for v in report.valuations if v.kind==kind]
        rows.append(vals if vals else ([["해당 없음"]*6] if empty_tables=="유지" else []))
    rows.extend([[[x.rank,x.received,x.kind,("해당 없음" if x.amount_won is None and x.amount_thousand is None and (x.kind=="소유권 관련 등기" or x.amount_not_applicable) else x.amount_thousand if x.amount_won is None else x.amount_won/1000),x.creditor,x.note+" / "+x.cancellation+" / "+("선순위 공제 확정" if x.deduction and x.reviewed else "공제 미선택")+" / 문서 "+x.document_id] for x in report.rights],
       [[d.tenancy,d.collective,d.residential,d.stores,d.commercial,t.deposits,d.attachments+" / 근거: "+d.basis]],
       [[t.valuation,t.senior,t.deposits,t.collateral,t.capacity,report.duplicate]]])
    for table,data in zip(doc.tables,rows): _fill(table,data)
    is_final=not draft
    mapping={"{{status}}":"최종 결과서" if is_final else "초안 — 검토 미완료", "{{date}}":str(report.written_on), "{{opinion}}":report.opinion or "의견 입력 필요", "{{final_check}}":"☑" if is_final else "☐", "{{provisional_check}}":"☑" if report.completion=="임차 미반영" else "☐", "{{review_notes}}":"담당자 최종 확인 완료" if is_final else "초안 검토사항: "+("; ".join(errors) if errors else "최종 다운로드 전 담당자 재확인")}
    for p in doc.paragraphs:
        for token,value in mapping.items():
            if token in p.text: p.text=p.text.replace(token,value)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(2)
                    for run in p.runs: run.font.size=Pt(8)
    out=BytesIO();doc.save(out);return out.getvalue()

def download_filename(report: Report, draft: bool) -> str:
    return safe_filename(f"담보평가결과서_{report.request.store or '미입력'}_{report.written_on}_{'초안' if draft else '최종'}.docx")
