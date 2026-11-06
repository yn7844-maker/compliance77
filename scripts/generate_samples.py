"""개인정보 없는 가상 등기 6사례. 정답은 파서 출력이 아닌 명시적 fixture로 작성."""
from pathlib import Path
import sys,json
from decimal import Decimal as D
import fitz
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from models.schemas import Report,Target,Owner,Valuation,Right,Deposit
from core.word_generator import create_template,generate_word

CASES=[
 {'id':'case01','title':'단독소유 토지·건물','kinds':['토지','건물'],'owners':[('가상소유자A','1/1')],'rights':[]},
 {'id':'case02','title':'공동소유 토지·건물','kinds':['토지','건물'],'owners':[('가상소유자A','1/2'),('가상소유자B','1/2')],'rights':[]},
 {'id':'case03','title':'집합건물 근저당권','kinds':['집합건물'],'owners':[('가상소유자C','1/1')],'rights':[('1','근저당권설정','2024-05-10','300000000','가상금융A')]},
 {'id':'case04','title':'근저당권 다수','kinds':['토지'],'owners':[('가상소유자D','1/1')],'rights':[('1','근저당권설정','2024-05-10','100000000','가상금융A'),('2','근저당권설정','2024-06-11','200000000','가상금융B')]},
 {'id':'case05','title':'가압류 존재','kinds':['건물'],'owners':[('가상소유자E','1/1')],'rights':[('2','가압류','2024-07-12','50000000','가상채권자A')]},
 {'id':'case06','title':'말소 근저당권','kinds':['집합건물'],'owners':[('가상소유자F','1/1')],'rights':[('1','근저당권설정','2024-05-10','300000000','가상금융A'),('2','1번근저당권말소','2024-08-12','','')]},
]

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def ko_date(d):
    y,m,day=d.split('-');return f'{y}년 {int(m)}월 {int(day)}일'

def make_pdf(case,kind,path):
    doc=fitz.open()
    fontpath=next((p for p in [ROOT/'sample_data/assets/NanumGothic.ttf', Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')] if p.exists()),None)
    fontname='sample' if fontpath else 'korea'
    def page(title):
        p=doc.new_page(width=842,height=595)
        if fontpath: p.insert_font(fontname=fontname,fontfile=str(fontpath))
        p.insert_text((35,30),'TEST / 가상 데이터 — 공적 증명서 아님',fontname=fontname,fontsize=13,color=(.6,.1,.1))
        p.insert_text((35,55),title,fontname=fontname,fontsize=16)
        return p
    def line(p,y,text): p.insert_text((45,y),text,fontname=fontname,fontsize=11)
    address=f'가상특별시 시험구 모의동 {case["id"][-2:]}-1'+(' 모의아파트 제101동 제1001호' if kind=='집합건물' else '')
    p=page(f'등기사항전부증명서 [{kind}] (시연용)')
    for y,text in [(90,'【표제부】'),(118,f'소재지: {address}'),(146,'지목: 대' if kind=='토지' else '지목: 해당없음'),(174,'면적: 84.50 m²'),(202,'구조: 철근콘크리트 / 용도: 주거용'),(230,'전유부분: 제1001호 / 대지권: 1000분의 35' if kind=='집합건물' else '대지권: 해당 없음'),(275,'【갑구】'),(306,'순위번호       등기목적                    접수                       권리자 및 기타사항')]: line(p,y,text)
    line(p,340,'1   소유권이전   2023년 3월 1일 제10001호')
    y=370
    for name,share in case['owners']:
        n,d=share.split('/');line(p,y,f'{"공유자" if len(case["owners"])>1 else "소유자"} {name} 지분 {d}분의 {n}');y+=28
    if case['id']=='case05':
        rank,purpose,dt,amt,creditor=case['rights'][0]
        line(p,y+8,f'{rank}   {purpose}   {ko_date(dt)} 제20001호');line(p,y+36,f'채권액 금{int(amt):,}원');line(p,y+64,f'채권자 {creditor}')
    p=page('【을구】 소유권 이외의 권리에 관한 사항')
    line(p,90,'순위번호       등기목적                    접수                       권리자 및 기타사항')
    y=125
    for rank,purpose,dt,amt,creditor in ([] if case['id']=='case05' else case['rights']):
        # 실제 등기와 유사하게 표의 여러 열과 후속 행에 데이터를 배치
        for x,text in [(45,rank),(105,purpose),(320,ko_date(dt)),(520,'제20001호')]: p.insert_text((x,y),text,fontname=fontname,fontsize=11)
        if amt:
            line(p,y+28,f'채권최고액 금{int(amt):,}원');line(p,y+56,'채무자 가상채무자A');line(p,y+84,f'근저당권자 {creditor}')
        else: line(p,y+28,'말소 원인: 해지 (TEST)')
        for x in [35,95,310,510,800]: p.draw_line((x,y-15),(x,y+100),color=(.6,.6,.6),width=.4)
        p.draw_line((35,y+100),(800,y+100),color=(.6,.6,.6),width=.4)
        y+=135
    if not case['rights'] or case['id']=='case05': line(p,130,'기록사항 없음 (담당자 원본 대조 필요)')
    doc.subset_fonts()
    doc.save(path,garbage=4,deflate=True);doc.close()
    return address

def completed(case,addresses):
    r=Report(evaluation_type='집합건물' if case['kinds']==['집합건물'] else '토지·건물',re_request='최초',store=f'가상점포_{case["id"]}',contract='임대차',purpose='신규담보',requested=D('100000'),considerations='가상 자료 기반 시연, 실제 법률 판단 아님',rights_reviewed=True,rounding_confirmed=True,evidence_reviewed=True,opinion='가상자료를 담당자가 대조한 시연용 결과입니다.',completion='최종',reviewer='가상담당자',reviewed=True)
    for kind,address in zip(case['kinds'],addresses):
        r.targets.append(Target(kind=kind,address=address,debtor='가상채무자A',owners=[Owner(name=n,share=s) for n,s in case['owners']],duplicate='없음',stores='해당 없음',confirmed=True))
        r.valuations.append(Valuation(kind=kind,address=address,category='대' if kind=='토지' else '해당 없음',area=D('84.5'),amount=D('500000'),basis='외부 가상 평가자료 직접 입력; 공시지가·적용율 해당 없음',confirmed=True))
    for rank,purpose,dt,amt,creditor in case['rights']:
        r.rights.append(Right(id=f'gold:{rank}',section='을구',rank=rank,receipt_date=dt,kind='근저당권',amount_won=D(amt) if amt else None,creditor=creditor or '해당 없음',status='유효 확인',decision='공제',confirmed=True,notes='가상 내부 기준에 따라 담당자가 공제 대상으로 확정한 테스트 입력'))
    for i,kind in enumerate(case['kinds']):
        r.rights.append(Right(id=f'gold:owner:{i}',section='갑구',rank='1',receipt_date='2023-03-01',kind='소유권',creditor='해당 없음',status='유효 확인',decision='제외',confirmed=True,notes=f'{kind} 소유권 이전, 원문 및 현재 소유자 대조 완료'))
    r.deposit=Deposit(a=D('10000') if case['kinds']==['집합건물'] else D('0'),b=D('0'),c=D('0'),shops=0,tenancy='있음' if case['kinds']==['집합건물'] else '없음',reviewed=True,decision='공제' if case['kinds']==['집합건물'] else '공제 없음',basis='가상 임대차현황 및 담당자 확정값',attachments='가상 임차현황서 (패키지 JSON)',attachment_review='확인')
    return r

def main():
    for folder in ['pdf','expected','completed_reports']: (ROOT/'sample_data'/folder).mkdir(parents=True,exist_ok=True)
    create_template()
    manifest=[]
    for case in CASES:
        addresses=[]
        for kind in case['kinds']:
            name=f'{case["id"]}_{kind}.pdf'
            address=make_pdf(case,kind,ROOT/'sample_data/pdf'/name);addresses.append(address)
            rights=[{'section':'갑구','rank':'1','kind':'소유권','receipt_date':'2023-03-01','amount_won':None,'status':'변경 검토'}]
            for rank,purpose,dt,amt,creditor in case['rights']:
                rights.append({'section':'갑구' if case['id']=='case05' else '을구','rank':rank,'kind':'가압류' if case['id']=='case05' else '근저당권','receipt_date':dt,'amount_won':amt or None,'status':'말소' if case['id']=='case06' and rank=='1' else ('변경 검토' if '말소' in purpose else '유효 여부 검토')})
            expected={'document':name,'address':address,'category':'대' if kind=='토지' else '해당없음','area':'84.50','owners':[{'name':n,'share':s} for n,s in case['owners']],'rights':rights}
            write_json(ROOT/'sample_data/expected'/f'{name[:-4]}.json',expected)
            manifest.append({'case':case['id'],'title':case['title'],'pdf':name,'expected':f'{name[:-4]}.json'})
        if case['id'] in ['case01','case03']:
            report=completed(case,addresses)
            write_json(ROOT/'sample_data/expected'/f'{case["id"]}_report.json',report.model_dump(mode='json'))
            (ROOT/'sample_data/completed_reports'/f'{case["id"]}_담보평가결과서.docx').write_bytes(generate_word(report,final=True))
    # 이미지형 PDF: 텍스트 레이어가 없는 실제 OCR 테스트용
    source=fitz.open(ROOT/'sample_data/pdf/case03_집합건물.pdf');scan=fitz.open()
    for p in source:
        pix=p.get_pixmap(matrix=fitz.Matrix(2,2));dest=scan.new_page(width=p.rect.width,height=p.rect.height);dest.insert_image(dest.rect,stream=pix.tobytes('png'))
    scan.save(ROOT/'sample_data/pdf/case03_scan.pdf',deflate=True);scan.close();source.close()
    write_json(ROOT/'sample_data/manifest.json',manifest)
    print(f'{len(CASES)}개 가상 사례 / {len(manifest)}개 등기 PDF / 스캔 PDF 1개 / 완성 Word 2개 생성')
if __name__=='__main__': main()
