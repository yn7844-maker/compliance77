# 담보평가결과서 자동작성 시스템

준법지원팀 업무지원용 **가상 데이터 PoC**. Python 3.12 / Streamlit / PyMuPDF / 로컬 Tesseract / Pydantic / python-docx.
외부 LLM, OCR API, 사내 시스템 접속, 법률 판단 자동 확정을 사용하지 않습니다.

## 빠른 실행

```bash
cd /workspace/compliance77  # 로컬에서는 저장소를 내려받은 경로
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.lock.txt
streamlit run app.py
```

`requirements.txt`는 직접 의존성 고정 버전, `requirements.lock.txt`는 이 환경에서 검증한 전체 의존성입니다.
텍스트 PDF와 Word 생성은 OCR 없이 동작합니다. 샘플 PDF, 정답 JSON, Word 템플릿은 저장소에 포함됩니다.

현재 클라우드에서 재설치: `bash scripts/setup.sh`. TLS·한국어 언어 데이터 SHA256 검증을 유지하며 재실행할 수 있습니다.
작업 환경은 이미 격리되어 있으므로 기존 체크아웃을 사용하며 추가 Git worktree를 만들 필요가 없습니다.

## 5단계 사용법

1. **평가 유형·문서 업로드**: 토지·건물/집합건물 선택. 복수 등기 PDF와 증빙 PDF를 업로드한 뒤 분석합니다. 증빙은 자동 분석하지 않습니다. `가상 패키지 불러오기`로 case01 또는 case03의 완성 입력을 불러올 수도 있습니다.
2. **문서 인식 검토**: 페이지 이미지와 원문·근거 페이지·좌표·OCR 상태를 대조합니다. 소유자 후보는 과거 소유자를 포함할 수 있습니다. 원본 추출 결과는 보존됩니다.
3. **7개 영역 작성**: 의뢰내역 → 평가대상 → 평가결과(토지/건물/집합건물) → 권리내역 → 공제대상 임차보증금내역 → 종합 → 의견. 표 마지막 행에서 추가하고 행을 선택해 삭제합니다. 소유자는 `가상A|1/2; 가상B|1/2` 형식입니다. 금액·면적은 문자열 입력 후 Decimal로 변환하며, 빈 값은 미확정입니다.
4. **검증·미리보기**: 누락/미검토를 표시하고, 생성 Word를 다시 읽은 실제 표 셀 내용을 보여줍니다(Word 인쇄 화면과 동일한 시각적 렌더링은 아닙니다). 담당자 최종 확인은 현재 입력에 묶이므로 내용 변경 시 해제됩니다.
5. **Word 다운로드**: 검토·필수 입력·임차 확인·최종 구분을 모두 만족하면 최종본, 그 외에는 **초안**만 가능합니다. 초안에도 미완료 항목을 출력합니다. DOCX는 이미지가 아닌 편집 가능한 9개 표로 7개 영역을 구성합니다.

실제 PDF 테스트: `sample_data/pdf/case01_토지.pdf`와 `case01_건물.pdf`를 함께 업로드하거나 `case03_집합건물.pdf`를 업로드합니다. PDF 제안만으로 평가가 완성되지는 않습니다. 담당자가 의뢰금액, 채무자, 평가금액, 공제 판단·근거 등 추가 정보를 입력해야 합니다. 완성 패키지는 `sample_data/expected/case01_report.json`, `case03_report.json`에 해당 입력을 포함합니다.

## OCR 설치

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-kor fonts-noto-cjk
source .venv/bin/activate
tesseract --list-langs  # kor, eng, osd 확인
```

macOS: `brew install tesseract tesseract-lang`. Windows는 신뢰할 수 있는 Tesseract 배포판에 kor/eng/osd를 설치하고 실행 파일을 PATH에 추가하세요. `TesseractEngine(tessdata='...')`로 언어 데이터 경로를 지정할 수 있습니다.
이 클라우드에서는 시스템 엔진과 `.local/tessdata`의 공식 kor 데이터를 사용합니다. `scripts/setup.sh`가 해당 데이터를 검증하여 설치합니다. 시스템 한국어 데이터만 있어도 작동합니다.

텍스트가 충분한 페이지에는 OCR을 호출하지 않습니다. 나머지 페이지만 이미지로 변환해 회전(OSD), 명암 보정, 선명화 후 인식합니다. OSD가 판단하지 못하는 짧은/복잡한 문서는 자동 회전이 보장되지 않습니다. 엔진·언어 데이터가 없거나 처리 실패하면 페이지 오류를 남깁니다. OCR 임시 파일은 pytesseract의 임시 컨텍스트에서 정리됩니다. OCR 좌표는 보정된 이미지의 픽셀, 텍스트 PDF 좌표는 PDF point입니다.

`PaddleEngine`은 별도 어댑터입니다. PaddleOCR 3.x와 호환 PaddlePaddle, 사전에 준비한 로컬 한국어 모델 경로를 생성자에 전달하는 방식이며 기본 설치·UI에는 포함하지 않습니다. 이 환경에서는 Paddle 엔진을 설치하거나 검증하지 않았습니다. 추가 엔진 사용 시 네트워크 다운로드 없는 로컬 모델 설정을 별도로 검증해야 합니다.

## 계산·검토 원칙

- 결과서 금액은 **천원**, 권리 편집 표와 원문 금액은 **원**입니다.
- `a = 확정한 평가금액 합계`, `b = 담당자가 공제로 확정한 유효 권리만 합산`, `c = 담당자 검토를 마친 임차보증금 공제액`, `d = a-b-c`, `담보여력 = d-의뢰금액`입니다.
- 보증금 총액 `a+b+c`와 실제 공제 반영액을 구분합니다. `공제 없음`은 담당자의 별도 결정과 근거가 필요합니다. 미해당 보증금은 0, 첨부가 없으면 해당 없음을 직접 명시합니다.
- 접수일자로 선순위를 자동 판정하지 않습니다. 말소 연결은 후보로만 제시하며, 변경·이전·부기·말소선·현재 소유자 여부는 원본 대조가 필요합니다.
- `config/calculation_rules.py`에서 부동산 유형별 산식을 분리했습니다. 기본은 모두 **미확정(None)**이므로 평가금액을 직접 입력합니다. 예시 산식을 활성화하려면 내부 승인과 단위 검증이 선행돼야 합니다.
- 원→천원 처리 기준은 담당자가 정밀 유지/절사/반올림 중 확인합니다. 정밀 유지는 정확한 나눗셈이고, 절사·반올림은 **권리 행별** 천원 변환에 적용합니다. 이 적용 범위도 사내 기준과 대조해야 합니다. 원 단위 원문은 수정 후에도 추출 근거에 남습니다.
- 미검토를 0으로 대체하지 않으며 최종 계산은 필요한 검토가 완료된 경우에만 표시합니다. 음수 담보여력은 자동 거절/승인으로 해석하지 않습니다.
- “추가담소” 원문 옵션은 `config/field_options.py`에 보존했습니다.

## 구조와 확장 지점

```text
app.py                         Streamlit 진입점
app/components/                upload, review, report_form, report_preview
app/state.py                   세션 초기화·입력 fingerprint
models/schemas.py              검증 가능한 데이터 모델·원문/근거/상태
core/pdf_reader.py             형식·용량·페이지 검증, 선택적 OCR
core/ocr_engine.py             Tesseract / 선택적 Paddle 어댑터
core/registry_parser.py        좌표 기반 행 복원·섹션 상태·등기 행 묶음
core/rights_parser.py          날짜·금액·변경/말소 참조 연결
core/field_mapper.py           충돌 없는 제안값 매핑
core/collateral_calculator.py  Decimal 계산
core/validation.py             결과서 완결성·검토 검사
core/word_generator.py         편집 가능한 표 생성·템플릿 인터페이스
config/                        선택지·열 순서·계산 기준
templates/collateral_report.docx
sample_data/pdf/               가상 6사례 8개 등기 PDF + 스캔 PDF
sample_data/expected/          독립 정답 JSON + 완성 입력 2건
sample_data/completed_reports/ 정답 Word 2건
sample_data/*evaluation_results.json
scripts/                       샘플 생성·평가·환경 설치
tests/                         파서·PDF·OCR·계산·검증·Word·화면·E2E
docs/TEMPLATE_CONTRACT.md       실제 원본 양식 교체 계약
```

## 테스트·재생성

```bash
source .venv/bin/activate
python -m pytest -q                   # 실제 한국어 OCR 통합 테스트 포함
python -m pytest -q -m 'not ocr'      # OCR 미설치 환경 (OCR 검증 제외)
python scripts/evaluate.py           # 텍스트 fixture 정답 비교, 상세 JSON 기록
python scripts/evaluate_ocr.py       # 스캔 OCR의 실제 오인식·누락도 기록
python scripts/generate_samples.py   # 가상 PDF/정답/Word/템플릿 덮어쓰기, 명시적 재생성 전용
```

가상자료 생성기에서는 테스트 전용 소유자·주소·금융기관만 사용하고 주민등록번호는 생성하지 않습니다. 실제 문서와 유사한 표제부·갑구·을구 및 복수 행/열을 사용하지만 실제 공적 양식이나 모든 발급 버전을 재현하지 않습니다. 동봉한 NanumGothic 글꼴(라이선스: docs/FONT_LICENSE.txt)을 우선 사용하며 없으면 시스템 Nanum 또는 PyMuPDF 내장 한글 폰트로 대체합니다.
정답은 파서가 만든 출력물을 재사용하지 않고 명시적 가상 fixture에서 생성합니다. `manifest.json`에 사례를 추가하는 대신 생성기 `CASES`를 확장해 20건 이상으로 늘릴 수 있습니다.

평가 결과는 필드별 **문서 단위 완전 일치율**, 필수 필드 누락률, 매핑 오류 수, 권리 목록/말소 상태 완전 일치율 및 처리시간을 남깁니다. Word 생성·재열기 성공률과 브라우저 저장 성공률을 구분합니다. 화면에서는 수정된 최상위 영역 수·경과시간·다운로드 클릭 수를 세션에 표시하며, 브라우저 실제 저장 성공과 업무 종료 시간/필드별 수정 횟수는 아직 별도 사용자 테스트 기록이 필요합니다. 높은 합성 텍스트 PDF 정확도는 실제 문서 정확도를 보장하지 않습니다.

## 배포와 보안 범위

GitHub를 통한 배포의 정확한 입력값과 확인 절차: [Streamlit 배포 가이드](docs/DEPLOY_STREAMLIT.md).

- Community Cloud: 저장소와 `app.py` 지정, Python 3.12, `requirements.txt`·`packages.txt` 사용. **가상자료 시연 전용**이며 이 작업에서 Community Cloud 배포는 수행하지 않았습니다.
- 사내 서버: 승인된 Python/Tesseract 환경에 설치하고 Streamlit을 내부 reverse proxy 뒤에 실행합니다. 실제 운영에는 SSO·접근권한·TLS·보관정책·접속/감사로그·리소스 제한·보안 검토가 추가로 필요합니다.
- 세션 상태를 사용하며 전역 캐시/사용자 DB/원문 파일 영구 저장을 사용하지 않습니다. 좌측 `현재 세션 자료 지우기`로 메모리 자료를 지웁니다. 세션은 서버 메모리에 머무르며, 운영체제 메모리 삭제까지 보장하는 보안 삭제 기능은 아닙니다.
- 파일당 20MB/40페이지, 건당 12개/60MB 제한, 파일 경로/제어문자/중복 이름/PDF magic/암호화를 검사합니다. 렌더링 픽셀 수도 제한합니다. 악성 PDF 격리 샌드박스나 바이러스 검사는 이 PoC 범위에 없습니다.
- 사용자 파일·OCR 원문은 코드에서 로그에 기록하지 않습니다. 파일은 세션별로 관리하고 생성 Word도 요청마다 새 바이트 버퍼에서 만듭니다. Python 오류/인프라 로그의 개인정보 방지는 실제 운영 전 별도 검토해야 합니다.

## 실제 준법지원팀 검증 전 확인

1. 실제 Word 원본의 열·병합·폭·페이지 배치와 템플릿 계약을 대조합니다.
2. 공제대상, 선순위, 권리 변경·말소/소유권의 유효성, 평가 산식·단위·천원 처리 범위를 확정합니다.
3. 익명화·승인된 실제 발급 양식으로 좌표/표 경계, OCR 숫자·한글, 누락·충돌 및 소유자 이력의 오류를 측정합니다.
4. Word 인쇄·페이지 나눔을 Microsoft Word에서 확인하고 담당자 서명/승인 절차를 정합니다.
5. 실제 개인정보 반입 전 사내 보안 승인을 받습니다. 이 PoC를 운영 수준의 보안·법률 판단 도구로 간주하지 마세요.

현재 외부시스템 연동, 법률 자동 확정, 실제 문서 전 유형 범용 인식, 취소선 기반 자동 유효성 확정, PDF 좌표 하이라이트, Word 인쇄 렌더링, 브라우저 파일 저장 완료 추적, 영구 감사로그/인증은 지원하지 않습니다.
