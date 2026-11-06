"""실제 로컬 OCR 결과와 정답 비교. 실패도 보고하며 텍스트 정답으로 대체하지 않는다."""
from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core.pdf_reader import read_pdf
from core.registry_parser import parse_registry
from core.field_mapper import unique_value

def main():
    started=time.perf_counter()
    path=ROOT/'sample_data/pdf/case03_scan.pdf'
    ex=parse_registry(read_pdf(path.read_bytes(),path.name),path.name)
    gold=json.loads((ROOT/'sample_data/expected/case03_집합건물.json').read_text())
    result={'scope':'자체 생성 스캔 PDF 1개, 실제 등기 성능 아님','seconds':round(time.perf_counter()-started,3),
            'fields':{k:{'expected':gold[k],'actual':unique_value(ex,k),'match':gold[k]==unique_value(ex,k)} for k in ['address','area','category']},
            'owners':{'expected':gold['owners'],'actual':[{'name':o.name,'share':o.share} for o in ex.owners]},
            'rights':{'expected':gold['rights'],'actual':[r.model_dump(mode='json') for r in ex.rights]},
            'pages':[{'page':p.number,'ocr':p.used_ocr,'confidence':p.confidence,'rotation':p.rotation,'error':p.error} for p in ex.pages],
            'issues':ex.issues}
    (ROOT/'sample_data/ocr_evaluation_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'seconds':result['seconds'],'fields':result['fields'],'pages':result['pages']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
