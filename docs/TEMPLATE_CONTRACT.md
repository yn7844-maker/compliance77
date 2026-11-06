# 실제 Word 원본으로 교체하기

기본 실행은 `build_template()`과 `blank_document()`에서 파일을 읽지 않고 양식을 생성합니다. `templates/collateral_report.docx`는 교체 계약 확인용 예시이며 기본 실행의 필수 파일이 아닙니다.

원본 파일은 제공되지 않았으므로 `templates/collateral_report.docx`는 명세로 만든 **시연용 양식**입니다. `generate_word(report, template=Path(...), final=True)`로 다른 템플릿을 주입할 수 있으며 원본은 수정하지 않습니다.

실제 원본을 복사한 뒤 각 표의 `w:tblCaption/@w:val`에 아래 ID를 지정하세요. ID와 첫 행 헤더는 `core.word_generator.TABLE_KEYS/TABLE_HEADERS`와 일치해야 합니다. 미일치 시 빈 문서를 완성본으로 내보내지 않고 오류를 냅니다.

| ID | 표 |
|---|---|
| request | 의뢰내역 |
| targets | 평가대상 |
| land | 토지 평가 |
| building | 건물 평가 |
| unit | 집합건물 평가 |
| rights | 권리내역 |
| deposit | 임차보증금 |
| summary | 종합 |
| opinion | 의견 |

표 첫 행은 헤더이고 나머지는 데이터 행입니다. 렌더러가 데이터 행을 대체합니다. 병합된 여러 헤더 행을 쓰는 실제 원본은 해당 레이아웃을 위한 별도 렌더링 어댑터를 구현하고 테스트해야 합니다. 원본을 바꾼다는 이유로 코드가 이를 자동 추정하지 않습니다.

문단 토큰은 `{{STATUS}}`, `{{FINAL_CHECK}}`, `{{NONFINAL_CHECK}}`, `{{REVIEWER}}`, `{{DATE}}`입니다. 7개 제목·금액 단위·기존 주석은 템플릿에 유지합니다. 표 ID·열 검증 외에도 템플릿 교체 시 Word 출력 테스트와 수동 인쇄 검증이 필요합니다.

기본 양식은 가로 A4, 맑은 고딕 9pt, 헤더 반복, 편집 가능한 표로 생성합니다. 현재 자동 미리보기는 DOCX 내용을 재파싱한 표 미리보기이며 인쇄 미리보기가 아닙니다.
