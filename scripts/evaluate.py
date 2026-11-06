"""독립 정답과 추출값 비교. 실문서 정확도를 보장하지 않는다."""
import argparse
import json
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from core.pdf_reader import read_pdf
from core.registry_parser import parse_registry
from core.field_mapper import map_registries
from core.word_generator import generate_word
from models.schemas import Report
ROOT=Path(__file__).resolve().parents[1]

def evaluate() -> dict:
    cases=[];fields={k:{"correct":0,"total":0,"missing":0,"wrong_mapping":0} for k in ["소재지","면적","소유자"]}
    right_correct=right_total=cancel_correct=cancel_total=0
    for path in sorted((ROOT/"sample_data/expected").glob("case*.json")):
        expected=json.loads(path.read_text());started=perf_counter()
        actual=parse_registry(read_pdf((ROOT/"sample_data/pdf"/expected["file"]).read_bytes()),expected["file"])
        mismatches=[]
        wanted={"소재지":[expected["address"]],"면적":[expected["area"]],"소유자":expected["owners"]}
        for field,values in wanted.items():
            candidates=[f.value.split(" | ")[0] if field=="소유자" else f.value for f in actual.facts if f.field==field and f.value]
            stat=fields[field];stat["total"]+=len(values)
            stat["correct"]+=sum(v in candidates for v in values)
            stat["missing"]+=sum(v not in candidates for v in values)
            stat["wrong_mapping"]+=sum(v not in values for v in candidates)
            if sorted(candidates)!=sorted(values): mismatches.append({"field":field,"expected":values,"actual":candidates})
        lookup={(r.section,r.rank):r for r in actual.rights}
        for truth in expected["rights"]:
            right_total+=1;cancel_total+=1
            r=lookup.get((truth["section"],truth["rank"]))
            amount=Decimal(truth["amount_won"]) if truth["amount_won"] else None
            ok=bool(r and r.kind==truth["kind"] and r.received==truth["received"] and r.amount_won==amount)
            right_correct+=ok
            cancellation_ok=bool(r and r.cancellation==truth["cancellation"])
            cancel_correct+=cancellation_ok
            if not ok or not cancellation_ok: mismatches.append({"right":truth,"actual":r.model_dump(mode="json") if r else None})
        unexpected=set(lookup)-{(r["section"],r["rank"]) for r in expected["rights"]}
        if unexpected: mismatches.append({"unexpected_rights":sorted(unexpected)})
        cases.append({"file":expected["file"],"elapsed_seconds":round(perf_counter()-started,3),"mismatches":mismatches,"warnings":actual.warnings})
    generated=0;attempts=0
    for path in sorted((ROOT/"sample_data/packages").glob("*.json")):
        attempts+=1
        try:
            generate_word(Report.model_validate_json(path.read_text()),draft=False);generated+=1
        except ValueError: pass
    return {"scope":"가상 텍스트 PDF 8개. 실제 등기부 성능 보장 아님. OCR 성능은 별도 pytest -m ocr로 측정.","field_metrics":{k:{**v,"accuracy":v["correct"]/max(v["total"],1),"missing_rate":v["missing"]/max(v["total"],1)} for k,v in fields.items()},"rights":{"correct":right_correct,"expected":right_total,"accuracy":right_correct/max(right_total,1)},"cancellation":{"correct":cancel_correct,"expected":cancel_total,"accuracy":cancel_correct/max(cancel_total,1)},"word_generation":{"success":generated,"attempts":attempts,"success_rate":generated/max(attempts,1),"browser_download_success":None},"reviewer_corrections":None,"completion_seconds":None,"session_metrics_note":"실제 수정 수·작성 시간·다운로드 클릭은 UI 세션에서 측정. 실제 파일 저장 성공은 수동 확인 필요.","cases":cases}

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=ROOT/"sample_data/evaluation_results.json");args=parser.parse_args()
    results=evaluate();args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in results.items() if k!="cases"},ensure_ascii=False,indent=2))
    raise SystemExit(1 if any(c["mismatches"] for c in results["cases"]) else 0)
