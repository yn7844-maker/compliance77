from pathlib import Path
from zipfile import BadZipFile
from docx.opc.exceptions import PackageNotFoundError
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from config.document_fields import SECTIONS, HEADERS
from config.field_options import NOTE, FINAL_TEXT, NONFINAL_TEXT
from core.collateral_calculator import calculate, won_to_thousand, valuation_amount
from core.validation import validate_report
from models.schemas import Report
from core.blank_document import blank_document

DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1]/'templates/collateral_report.docx'
TABLE_KEYS = ['request','targets','land','building','unit','rights','deposit','summary','opinion']
TABLE_HEADERS = [HEADERS[0],HEADERS[1],HEADERS[2],HEADERS[2],HEADERS[2],HEADERS[3],HEADERS[4],HEADERS[5],HEADERS[6]]

def fmt(value) -> str:
    if value is None: return '미확정'
    if isinstance(value,Decimal):
        if not value.is_finite(): return '입력 오류'
        return f'{value:,f}'.rstrip('0').rstrip('.') if value%1 else f'{value:,.0f}'
    return str(value)

def _table_id(table):
    item=table._tbl.tblPr.find(qn('w:tblCaption'))
    return item.get(qn('w:val')) if item is not None else ''

def _header_style(table):
    trPr=table.rows[0]._tr.get_or_add_trPr()
    repeat=OxmlElement('w:tblHeader');trPr.append(repeat)
    for cell in table.rows[0].cells:
        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E7EDF5');cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs: run.bold=True

def build_template():
    """디스크의 DOCX를 읽지 않고 기본 시연 양식을 메모리에서 만든다."""
    doc=blank_document()
    sec=doc.sections[0]
    sec.page_width=Cm(29.7);sec.page_height=Cm(21)
    sec.top_margin=sec.bottom_margin=Cm(1.4);sec.left_margin=sec.right_margin=Cm(1.3)
    style=doc.styles['Normal'];style.font.name='맑은 고딕';style.font.size=Pt(9)
    style.element.rPr.rFonts.set(qn('w:eastAsia'),'맑은 고딕')
    doc.add_heading('담보평가결과서',0)
    doc.add_paragraph('{{STATUS}}')
    doc.add_paragraph('금액 단위: 천원 (권리내역 원문금액은 검토 화면에서 원 단위로 관리)')
    idx=0
    for n,title in enumerate(SECTIONS):
        doc.add_heading(f'{n+1}. {title}',1)
        keys = ['land','building','unit'] if n==2 else [[ 'request'],['targets'],[],['rights'],['deposit'],['summary'],['opinion']][n]
        for key in keys:
            if n==2: doc.add_paragraph({'land':'(가) 토지','building':'(나) 건물','unit':'(다) 집합건물(외부감정 포함)'}[key])
            headers=TABLE_HEADERS[TABLE_KEYS.index(key)]
            t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid'
            cap=OxmlElement('w:tblCaption');cap.set(qn('w:val'),key);t._tbl.tblPr.append(cap)
            for c,h in zip(t.rows[0].cells,headers): c.text=h
            _header_style(t)
            t.add_row()
        if n==5: doc.add_paragraph(NOTE)
    doc.add_paragraph('{{FINAL_CHECK}}')
    doc.add_paragraph('{{NONFINAL_CHECK}}')
    doc.add_paragraph('담당자: {{REVIEWER}} / 작성일: {{DATE}}')
    doc.add_paragraph('준법지원팀 업무지원 PoC · TEST / 가상 데이터 전용')
    return doc

def create_template(path: Path = DEFAULT_TEMPLATE):
    path.parent.mkdir(parents=True,exist_ok=True)
    build_template().save(path)

def _populate(table, rows):
    for row in list(table.rows)[1:]: table._tbl.remove(row._tr)
    for values in rows:
        cells=table.add_row().cells
        for cell,value in zip(cells,values): cell.text=fmt(value)

def generate_word(report: Report, template: Path | str | None = None, final: bool = False) -> bytes:
    errors=validate_report(report)
    if final and (errors or report.completion!='최종'):
        raise ValueError('최종본 생성 불가: ' + '; '.join(errors or ['최종 결과서 선택 필요']))
    if template is None:
        doc=build_template()
    else:
        try:
            doc=Document(template)
        except (BadZipFile, PackageNotFoundError, OSError, KeyError) as exc:
            raise ValueError('선택한 Word 양식을 읽을 수 없습니다. 회사 암호화 또는 파일 손상 여부를 확인하고, 기본 시연 양식을 사용하거나 승인된 정상 DOCX를 선택하세요.') from exc
    text='\n'.join(p.text for p in doc.paragraphs)
    if any(token not in text for token in ['{{STATUS}}','{{FINAL_CHECK}}','{{NONFINAL_CHECK}}','{{REVIEWER}}','{{DATE}}']):
        raise ValueError('템플릿의 상태·확인·담당자 토큰이 누락됐습니다.')
    tables={_table_id(t):t for t in doc.tables}
    if any(k not in tables for k in TABLE_KEYS): raise ValueError('템플릿 표 식별자(tblCaption)가 누락됐습니다.')
    for key,headers in zip(TABLE_KEYS,TABLE_HEADERS):
        if [c.text for c in tables[key].rows[0].cells]!=headers: raise ValueError(f'템플릿 헤더 불일치: {key}')
    calc=calculate(report)
    missing=lambda s:s if str(s).strip() else '미입력'
    data={
     'request':[[missing(report.re_request),missing(report.store),missing(report.contract),missing(report.purpose),report.requested,missing(report.considerations)]],
     'targets':[[t.kind,missing(t.address),missing(t.debtor),'\n'.join(f'{o.name} (지분 {o.share or "미확인"})' for o in t.owners) or '미입력',t.duplicate,missing(t.stores)] for t in report.targets],
     'rights':[[f'{r.section} {r.rank}',r.receipt_date or '미확인',r.kind,won_to_thousand(r.amount_won,report.rounding) if r.amount_won is not None else ('해당 없음' if r.confirmed and (r.kind not in ['근저당권','저당권','전세권'] or r.status=='말소') else '금액 미확인'),r.creditor or '미입력',f'{r.status} / 선순위 {r.decision}\n{r.notes}'] for r in report.rights],
     'deposit':[[report.deposit.tenancy,report.deposit.a,report.deposit.b,report.deposit.shops,report.deposit.c,calc['deposit_total'],f'{report.deposit.attachments or "미입력"}\n검토: {report.deposit.attachment_review}\n공제: {report.deposit.decision}\n근거: {report.deposit.basis or "미입력"}']],
     'summary':[[calc['a'],calc['b'],calc['c'],calc['d'],calc['capacity'],' / '.join(sorted({t.duplicate for t in report.targets})) or '미확인']],
     'opinion':[[missing(report.opinion)]],
    }
    for key,kind in [('land','토지'),('building','건물'),('unit','집합건물')]:
        data[key]=[[v.address or '미입력',v.category or '미입력',v.area,v.public_price if v.public_price is not None else ('해당 없음' if '해당 없음' in v.basis else '미입력/미사용 확인 필요'),v.rate if v.rate is not None else ('해당 없음' if '해당 없음' in v.basis else '미입력/미사용 확인 필요'),valuation_amount(v)] for v in report.valuations if v.kind==kind]
    for key,rows in data.items():
        if not rows: rows=[['해당 없음' if report.evidence_reviewed else '미입력']*len(tables[key].columns)] if key not in ['land','building','unit'] else ([['해당 없음']*6] if report.empty_tables=='유지' else [])
        _populate(tables[key],rows)
    status='최종 결과서' if final else '초안 — 업무 사용 전 담당자 검토 필요'
    replacements={'{{STATUS}}':status,'{{FINAL_CHECK}}':('☑ ' if final else '☐ ')+FINAL_TEXT,
                  '{{NONFINAL_CHECK}}':('☑ ' if report.completion=='임차 미반영 비최종' else '☐ ')+NONFINAL_TEXT,
                  '{{REVIEWER}}':report.reviewer or '미확인','{{DATE}}':datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d')}
    for p in doc.paragraphs:
        for key,value in replacements.items():
            if key in p.text: p.text=p.text.replace(key,value)
    if errors:
        doc.add_heading('미완료 검토 항목 (초안)',1)
        for error in errors: doc.add_paragraph(error,style='List Bullet')
    doc.add_paragraph(f'금액 처리 기준: {report.rounding} / 담당자 확인: {report.rounding_confirmed}')
    output=BytesIO();doc.save(output);return output.getvalue()
