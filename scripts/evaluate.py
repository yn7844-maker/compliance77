"""독립 정답 fixture와 추출값 비교. 실문서 정확도를 보장하지 않음."""
from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core.pdf_reader import read_pdf
from core.registry_parser import parse_registry
from core.field_mapper import unique_value

def evaluate():
    manifest=json.loads((ROOT/'sample_data/manifest.json').read_text())
    totals={k:[0,0] for k in ['address','area','category','owners','rights','cancellation']}
    details=[];missing=0;mapping=0;word_success=0
    for item in manifest:
        gold=json.loads((ROOT/'sample_data/expected'/item['expected']).read_text())
        start=time.perf_counter()
        ex=parse_registry(read_pdf((ROOT/'sample_data/pdf'/item['pdf']).read_bytes(),item['pdf']),item['pdf'])
        actual={k:unique_value(ex,k) for k in ['address','area','category']}
        actual['owners']=[{'name':o.name,'share':o.share} for o in ex.owners]
        actual['rights']=[{k:(str(getattr(r,k)) if getattr(r,k) is not None else None) for k in ['section','rank','kind','receipt_date','amount_won','status']} for r in ex.rights]
        comparisons={k:actual[k]==gold[k] for k in ['address','area','category','owners','rights']}
        comparisons['cancellation']=[r['status'] for r in actual['rights']]==[r['status'] for r in gold['rights']]
        for k,ok in comparisons.items(): totals[k][0]+=int(ok);totals[k][1]+=1
        missing+=sum(not actual[k] for k in ['address','area','category','owners'])
        mapping+=sum(not comparisons[k] and bool(actual[k]) for k in ['address','area','category','owners'])
        details.append({'file':item['pdf'],'seconds':round(time.perf_counter()-start,3),'checks':comparisons,'expected':gold,'actual':actual,'issues':ex.issues})
    from models.schemas import Report
    from core.word_generator import generate_word
    from docx import Document
    from io import BytesIO
    for name in ['case01','case03']:
        r=Report.model_validate_json((ROOT/'sample_data/expected'/f'{name}_report.json').read_text())
        output=Document(BytesIO(generate_word(r,final=True)))
        word_success+=int(len(output.tables)==9 and r.store in output.tables[0].cell(1,1).text)
    result={'scope':'자체 생성 가상 텍스트 PDF 8개. 스캔 OCR 및 실제 등기부 성능은 별도 검증 필요.',
            'field_exact_match':{k:{'passed':v[0],'total':v[1],'rate':v[0]/v[1]} for k,v in totals.items()},
            'required_field_missing_rate':missing/(len(manifest)*4),'wrong_mapping_count':mapping,
            'word_generation_reopen_rate':word_success/2,'browser_download_success_rate':None,
            'user_correction_count':None,'report_completion_seconds':None,
            'unmeasured_reason':'브라우저 저장 성공·담당자 수정·작성 시간은 사용자 테스트에서 별도 기록. 세션에는 수정 영역/시간/클릭 수만 표시.',
            'details':details}
    return result
if __name__=='__main__':
    result=evaluate()
    out=ROOT/'sample_data/evaluation_results.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='details'},ensure_ascii=False,indent=2))
