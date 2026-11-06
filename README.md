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

## 버튼 한 번으로 초안 만들기

1. **파일 업로드**(PDF 또는 TXT, 복수 가능) 또는 **텍스트 붙여넣기**를 선택합니다.
2. **결과서 초안 자동작성**을 누르면 인식 가능한 값을 7개 영역에 넣고 초안 다운로드를 바로 제공합니다. 입력 전에는 빈 Word를 생성하지 않습니다.
3. 필요한 경우에만 **결과서 내용 수정 · 미확인 항목 보완**을 펼쳐 담당자가 누락된 의뢰·평가·공제 정보를 입력합니다. **인식 원문·근거 확인**에서 자료를 대조합니다.
4. 필수 항목과 검토가 모두 완료되면 현재 입력의 최종 확인 후 최종본을 다운로드합니다. 입력을 수정하면 최종 확인은 해제됩니다. 자동작성은 법률 판단이나 평가금액을 임의 확정하지 않습니다.

PDF의 텍스트 추출·OCR은 기존 규칙을 사용합니다. TXT는 UTF-8/CP949를 지원하며 최대 200,000자입니다. 붙여넣기에는 PDF 좌표가 없고 페이지 구분 문자가 없으면 1페이지로 기록합니다. 소유자는 `가상A|1/2; 가상B|1/2` 형식으로 보완할 수 있습니다. 금액·면적은 문자열 입력 후 Decimal로 변환하며, 빈 값은 미확정입니다.

**기본 Word는 외부 DOCX 파일을 읽지 않고 메모리에서 생성합니다.** 회사 정책으로 프로젝트의 `templates/collateral_report.docx` 또는 python-docx 내부 `default.docx`가 읽히지 않아도 기본 시연 양식은 생성할 수 있습니다. 사용자 지정 양식을 명시적으로 전달하면 해당 양식만 사용하며 암호화/손상 시 안내 오류를 냅니다. 회사 DRM을 복호화하거나 우회하는 기능은 아닙니다. 내려받은 Word에도 회사 보안 정책이 적용될 수 있습니다.

가상 체험은 **가상 데이터로 바로 체험 / 직접 작성**에서 case01/case03을 선택합니다. 회사 암호화로 동봉 PDF/JSON을 읽을 수 없는 경우에는 승인된 가상 텍스트를 붙여넣어 시연하세요. 실제 PDF 테스트는 `sample_data/pdf/case01_토지.pdf`와 `case01_건물.pdf` 또는 `case03_집합건물.pdf`를 사용합니다. 완성 입력 JSON은 `sample_data/expected/case01_report.json`, `case03_report.json`입니다.

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
core/blank_document.py         파일 없이 만드는 기본 Word 패키지
core/quick_report.py           텍스트 입력·초안 자동 매핑
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
