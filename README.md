# 담보평가결과서 자동작성 시스템

준법지원팀 업무지원 PoC. **가상 등기 PDF → 로컬 인식 → 담당자 수정·확정 → 7개 영역의 편집 가능한 Word** 흐름을 제공한다. 외부 LLM, 유료 OCR, 외부 업무시스템 연동, DB를 사용하지 않는다. 실제 개인정보를 올리지 않는다.

## 빠른 실행

Python **3.12 권장**. 아래 명령은 이 README가 있는 `collateral-report-poc` 폴더에서 실행한다.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell은 `.venv\Scripts\Activate.ps1`로 활성화한다. 기본 접속 주소는 http://localhost:8501 이다. 패키지 버전은 Python 3.12에서 설치·통합 테스트한 조합으로 고정했다. 최신 버전을 자동 설치하지 않는다.

포함된 PDF·템플릿·완성 패키지를 그대로 사용할 수 있다. 재생성하려면:

```bash
python -m scripts.generate_samples
python -m pytest -q
python -m scripts.evaluate
```

`generate_samples`는 가상 자료와 시연 템플릿을 덮어쓴다. **실제 원본 템플릿을 설치한 뒤에는 별도 백업 후 실행**한다. 앱과 핵심 로직을 분리했으므로 CLI/API/다른 프론트엔드에서 동일한 모델·파서·계산기·Word 생성기를 사용할 수 있다.

## 화면에서 사용하기

1. **평가 유형 선택**: 토지·건물 또는 집합건물. 빠른 시연은 `package_01` 또는 `package_03` 선택 후 ‘가상 사례 불러오기’를 누른다.
2. **직접 업로드**: `sample_data/pdf`의 `case_01_토지.pdf`와 `case_01_건물.pdf`를 함께 업로드하고 ‘문서 분석 시작’을 누른다. 한 평가에 파일 최대 10개, 파일당 20MB, 총 60MB, 각 50페이지까지 허용한다. 추가 증빙은 PDF 업로드·목록·원본 조회만 지원한다.
3. **원본 대조**: 좌측에서 문서·페이지를 선택하고 우측 후보 표를 수정한다. 후보의 근거 문서 ID·페이지·PDF 좌표·원문을 보존한다. 후보 검토는 STEP 2, 최종 결과서에 쓸 필드는 STEP 3에서 각각 확정한다. 여러 후보를 임의로 한 값으로 축약하지 않는다.
4. **7개 영역 작성**: 금액을 천원 단위로 입력한다. 표의 행 추가/수정/삭제를 지원한다. 공동소유자는 `가상소유자 | 1/2`처럼 작성하고 여러 명이면 세미콜론으로 구분한다. 채무자를 별도로 입력한다. 넓은 표는 가로 스크롤 또는 전체 화면 버튼으로 편집한다.
5. **권리 검토**: 원문금액(원)은 보존한다. 금액(원)을 수정하면 천원 정규화값을 다시 계산한다. 원 단위 근거가 없으면 직접금액(천원)을 입력한다. 공제할 권리의 ‘선순위 공제’와 ‘확인’을 담당자가 선택한다. 말소·검토 필요 권리는 공제 불가다. 비금전 등기·말소 행의 금액이 업무상 해당 없으면 ‘금액 해당 없음’을 명시한다. 소유권 등기는 채권최고액 해당 없음으로 출력한다.
6. **임차 검토**: a/b/c에는 임의 추정값 대신 내부 기준에 따라 확정한 공제금액을 입력한다. 해당 없는 항목은 0, 첨부서류·근거는 ‘해당 없음’도 명시한다. 임차 미확인은 최종 결과서로 출력할 수 없다.
7. **검증 및 다운로드**: 최종 확인을 체크하고 다운로드 구분 ‘최종’을 선택한다. 내용 변경 시 최종 확인이 해제되어 재확인이 필요하다. 누락·미확정 상태에서는 ‘초안’만 다운로드된다. 파일 안에도 초안/최종 상태와 검토사항이 표시된다. 앱 미리보기는 Word 내용 미리보기이며 실제 인쇄 페이지와 동일한 렌더러가 아니다.

완성 패키지를 불러와도 담당자 최종 확인은 다시 해야 한다. 최종 확인 표시가 있는 것만으로 실제 업무 승인이나 법률적 판단이 이루어지는 것은 아니다.

## OCR 설치 및 설정

텍스트형 PDF는 OCR 없이 PyMuPDF로 처리한다. 페이지별 텍스트 양과 깨진 문자 비율을 검사해 필요한 페이지만 OCR을 수행한다. 한국어 엔진이 없으면 스캔 페이지만 실패 상태가 되고 텍스트형 PDF는 계속 동작한다.

macOS:

```bash
brew install tesseract tesseract-lang
tesseract --list-langs
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-kor tesseract-ocr-eng
```

Windows는 승인된 Tesseract 설치본과 `kor`, `eng`, `osd` 언어 데이터를 설치하고 PATH를 설정한다. PATH에 없으면 `TESSERACT_CMD`에 실행 파일의 절대 경로를 지정한다. 언어 데이터 경로를 별도로 관리하면 `TESSDATA_PREFIX`를 설정한다. `tesseract --list-langs`에 **kor, eng, osd**가 표시되어야 한다.

Tesseract는 OSD 방향 감지, 회전 보정, 명암·선명도 전처리를 수행한다. 90/180/270도 회전을 지원하지만 OSD 실패 시 수동 회전·재업로드가 필요할 수 있다. 임의 기울기·심한 흐림·복잡한 표 OCR의 정확도를 보장하지 않는다. 시간 제한은 방향 감지 20초, 페이지 인식 90초다. 이미지 최대 약 2천만 픽셀로 제한한다. 좌표는 원본 PDF 페이지 좌표로 환산한다.

**선택 PaddleOCR 어댑터**: 기본 requirements와 분리되어 있다. Python 3.11의 별도 호환 환경에서 `requirements-ocr-paddle.txt`를 설치하고, 승인된 로컬 검출/한국어 인식/방향분류 모델 디렉터리를 UI에서 지정한다. 실행 중 자동 모델 다운로드를 의도하지 않는다. 이번 환경에서는 Paddle을 설치·실행 검증하지 않았다. 사내 배포 전 해당 플랫폼의 wheel·모델 호환성 및 네트워크 차단 상태를 반드시 확인한다. 기본 검증 엔진은 Tesseract다.

## 계산과 업무 확정

모든 금액은 Decimal로 처리한다. 브라우저 숫자 부동소수점 변환을 피하기 위해 금액 편집은 문자열 입력 후 Decimal로 검증한다.

- a = 확인된 평가금액 합계
- b = 담당자가 선순위 공제로 확정한 유효 권리 금액 합계
- c = 담당자가 확정한 임차보증금 a/b/c 합계
- 최종담보가치 = a - b - c
- 담보여력 = 최종담보가치 - 평가의뢰금액

계산에 필요한 값·권리 전체 검토·임차 검토가 미확정이면 최종 계산값을 비워 두고 ‘미확정’으로 표시한다. 선순위를 접수일자만으로 판단하지 않는다. 토지와 건물에 같은 공동담보 채권이 각각 기재되었다면 담당자가 **중복 공제 여부를 원본·공동담보목록과 대조**해야 한다. 자동 채무 병합을 하지 않는다.

천원 미만 처리 기준은 기본 ‘미정’이다. 소수 원/천원 환산이 필요한 공제금액은 담당자가 ‘정확값 유지’, ‘절사’, ‘반올림’ 중 내부 기준에 맞는 값을 선택해야 계산한다. 원문 원 금액과 정확 환산 천원값은 보존하며, 종합 공제합계에는 선택한 처리 기준을 적용한다. 평가 산식은 `config/calculation_rules.py`에 분리했으며, 현 버전은 기준 미확정으로 **평가금액 직접 입력만 지원**한다. 공시지가·적용율을 빈칸으로 둔 직접평가 행은 Word에 ‘해당 없음 (직접평가)’을 출력하므로 담당자는 산정근거와 직접 평가금액을 확인해야 한다.

음수 담보여력으로 승인 여부를 자동 판단하지 않는다. 제공된 주석 ‘담보여력이 부족한 경우에도 최종담보가치(d) 이내에서 담보 설정 가능’을 그대로 보존한다.

## Word 양식과 교체

`templates/collateral_report.docx`는 명세로 만든 시연용 **실제 Word 표**다. Word 생성 시 원본 템플릿을 읽기만 하고 덮어쓰지 않는다. 7개 영역, 8개 표(평가결과 3종 포함), 지정 열 헤더 순서, 선택값 단일 출력, 반복 헤더, 행 분할 억제, 천 단위 쉼표, 주석과 상호배타적 체크를 지원한다. 기본 A4 가로 2페이지이며 행과 긴 문장에 따라 자동으로 늘어난다. 해당 없는 평가유형의 데이터 행 유지/삭제를 선택할 수 있다.

`fonts/NanumGothic-Regular.ttf`와 OFL 라이선스를 포함한다. Word에서 한글 레이아웃을 동일하게 보려면 **나눔고딕을 로컬 OS에 설치**한다. 글꼴 자체를 Word 파일 안에 임베드하지는 않는다. OS 기본 한글 대체 글꼴을 사용할 경우 줄바꿈·페이지 수가 달라질 수 있다.

실제 Word 원본을 받으면 원본 보관 후 `core/word_generator.py`의 템플릿 어댑터를 조정한다. 현재 어댑터는 **지정된 8개 표 순서/열 헤더와 `{{status}}`, `{{date}}`, `{{opinion}}`, `{{final_check}}`, `{{provisional_check}}`, `{{review_notes}}` 문단 토큰**을 기대한다. 이 계약을 유지한 스타일 교체는 가능하다. 임의의 표 구조·병합 셀을 가진 파일을 덮어쓰는 것만으로 자동 지원한다고 주장하지 않는다. 구조가 다르면 명확히 오류를 반환하므로 별도 매핑과 회귀 테스트가 필요하다.

## 실제 파일 구조

```text
collateral-report-poc/
├── app.py
├── requirements.txt / requirements-ocr-paddle.txt / packages.txt
├── README.md / VERIFICATION.md / pytest.ini / .gitignore
├── .streamlit/config.toml
├── app/
│   ├── state.py
│   └── components/
│       ├── upload.py
│       ├── review.py
│       ├── report_form.py
│       └── report_preview.py
├── core/
│   ├── pdf_reader.py / ocr_engine.py
│   ├── registry_parser.py / rights_parser.py / field_mapper.py
│   ├── collateral_calculator.py / validation.py / word_generator.py
├── models/schemas.py
├── config/field_options.py / document_fields.py / calculation_rules.py
├── templates/collateral_report.docx
├── fonts/NanumGothic-Regular.ttf / OFL.txt
├── sample_data/
│   ├── pdf/                       # 텍스트 8개 + 스캔 2개
│   ├── expected/                  # PDF별 독립 정답 + 완성 계산 정답
│   ├── packages/                  # 완전한 입력 JSON 2건
│   ├── completed_reports/         # 정답 Word 2건
│   └── evaluation_results.json
├── scripts/generate_samples.py / evaluate.py
└── tests/
    ├── conftest.py
    ├── test_pdf_reader.py / test_parser.py
    ├── test_calculator.py / test_validation.py
    ├── test_word_generator.py / test_streamlit.py
    └── test_regressions.py
```

각 Python 패키지에는 `__init__.py`를 포함한다. 샘플 생성 스크립트의 cases 목록 및 독립 정답을 늘려 20건 이상으로 확장할 수 있다. 실제 사례 파일을 공개 저장소에 넣지 않는다.

## 테스트와 정확도 평가

```bash
python -m pytest -q                 # 전체 테스트
python -m pytest -q -m ocr          # 로컬 한국어 Tesseract 통합 테스트
python -m scripts.evaluate         # 독립 정답과 자동 추출 결과 비교
```

6개 가상 사례는 단독소유 토지·건물, 공동소유 토지·건물, 집합건물 근저당권, 다중 근저당권, 가압류, 근저당권 말소를 포함한다. 2건의 완성 패키지에는 의뢰·평가·임차 정보, 독립 예상 계산값과 정답 Word가 있다. 시험 PDF에는 모두 `TEST / 가상 데이터`를 표시한다.

`evaluate`는 소재지·면적·소유자의 필드별 정답 일치/누락/잘못된 매핑, 권리 단위 종류·접수일·금액 일치, 말소 분류, 처리시간, Word 생성 성공률과 오류 상세를 JSON으로 기록한다. 정답은 파서의 출력을 복제해 만들지 않는다. UI는 수정 이력 수·세션 경과시간·다운로드 클릭을 메모리에서 제공한다. **브라우저 파일 저장 완료는 서버가 알 수 없으므로 다운로드 성공률이라고 표시하지 않는다.** 수정 수·업무 완료시간은 사용자 테스트로 수집해야 하며 평가 JSON에서 미측정 값은 null이다.

정답 Word는 docx 재파싱으로 7영역·헤더·다중 행·합계·선택값·체크·원본 보존·미디어 미포함·편집제한 미설정을 검증한다. 별도 렌더링으로 한글·표·페이지를 시각 검토했다. 샘플 정확도를 실제 등기부등본 정확도로 일반화할 수 없다. 세부 실행 결과는 VERIFICATION.md를 참조한다.

## 보안 및 배포

업로드 원문/파일은 서버 디스크에 저장하지 않고 Streamlit 세션 메모리에 보관한다. 공유 전역 캐시를 사용하지 않는다. 세션 초기화 버튼으로 애플리케이션 메모리 참조와 위젯을 비운다. 서버 로그에 업로드 파일명·OCR 원문·문서 내용을 출력하지 않으며 예외 메시지도 고정 문구로 처리한다. OCR 임시파일은 pytesseract 자체 정리 기능에 맡긴다. 프로세스 강제종료 시 OS 임시영역 잔재 가능성은 운영 정책으로 보완해야 한다. 디스크 스왑/메모리 덤프 삭제나 운영 보안까지 보장하는 제품은 아니다. 다운로드는 세션별 bytes로 생성한다.

확장자뿐 아니라 PDF 매직 바이트·실제 파싱·암호화·용량·페이지 수를 검증하고 파일명을 정규화한다. 개인식별번호 가상 데이터는 만들지 않는다. 앱 자체 외부 AI/OCR 호출은 없으며 Streamlit 통계 전송은 꺼져 있다. 선택 설치/배포 시의 패키지 다운로드는 별도 네트워크 작업이다. 실제 운영에서는 인터넷 차단·DLP·백신·격리·인증·인가·접근로그·백업/삭제 정책·동시 처리 제한·취약점 점검·라이선스 검토가 필요하다. PyMuPDF의 라이선스 조건도 사내 도입 시 확인한다.

### Streamlit Community Cloud 가상 시연

가상 자료만 포함한 저장소를 생성한 뒤 Python 3.12, 메인 파일 `app.py`를 지정한다. 저장소 하위 폴더를 그대로 올리면 해당 상대 경로를 메인 파일로 지정한다. `requirements.txt`, `packages.txt`, `.streamlit/config.toml`, 템플릿과 샘플을 함께 배포한다. `packages.txt`가 Tesseract 한국어 패키지를 설치한다. 실제 클라우드 계정 배포는 이번 작업에서 수행하지 않았다. 스캔 OCR은 인스턴스 자원·제한시간에 영향을 받는다. 공개 Cloud는 실제 등기 처리용 환경이 아니다.

### 사내 서버

승인된 Python 3.12 환경에 의존성과 OCR 언어 데이터를 오프라인 배포하고, 네트워크 접근을 차단한 뒤 동일 명령으로 실행할 수 있다. 접속을 넓히기 전 사내 인증 프록시·TLS·접근통제·격리·자원 한도·보안 검토를 적용한다. 기본 PoC에 사용자 DB/역할 권한·지속 저장·전자결재 제출 기능은 없다.

## 한계와 실제 업무 테스트 전 확정사항

- 실제 Word 원본·실제 등기부등본을 제공받지 않았다. 현재 파서는 가상 표 구조 중심의 규칙 기반 초기 구현이다. 실제 발급기관/버전별 열 배치·표제부 주소 표기·다중 페이지·복잡한 부기등기에서 누락·오인 가능성이 있다. 취소선만 있는 말소와 소유권 이력의 법적 유효성을 자동 판단하지 않는다.
- 현재 소유자·순위/변경/이전/공동담보·복잡한 말소를 법적으로 확정하지 않는다. OCR 실패나 인식 누락은 ‘권리 없음’의 근거가 될 수 없다.
- 평가방법과 적용률, 선순위 공제 기준, 공동담보 중복 공제 방식, 공제대상 보증금 기준, 천원 미만 처리, 해당 없음의 허용 범위를 내부에서 확정해야 한다.
- 건축물대장·토지이용계획·KB시세·임대차 증빙 자동 추출 및 외부 시스템 연동은 구현하지 않았다. 증빙은 업로드·원본 조회·수동 검토한다.
- PaddleOCR는 선택 어댑터만 제공하며 실행 검증하지 않았다. PDF 미리보기는 페이지 이미지이고 Word 미리보기는 내용 표다.
- 실제 표준양식 반영 후 20건 이상의 승인된 비식별 사례로 필드/말소/공동담보 회귀 테스트와 담당자 수정·작성시간·실제 다운로드 성공률을 측정한다.
- 최종/임차 미반영 문구의 업무적 의미, ‘추가담소’ 원문 표기, 실제 필수 항목과 서명/결재란, 승인 권한을 준법지원팀과 확정한다.

기술 참고: [Streamlit 공식 문서](https://docs.streamlit.io/), [PyMuPDF 공식 문서](https://pymupdf.readthedocs.io/), [Tesseract 공식 문서](https://tesseract-ocr.github.io/tessdoc/), [Pydantic 공식 문서](https://docs.pydantic.dev/), [python-docx 공식 문서](https://python-docx.readthedocs.io/).
