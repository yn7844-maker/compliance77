# GitHub → Streamlit Community Cloud 배포

이 배포는 가상자료 시연 전용입니다. 실제 개인정보를 업로드하지 마세요.

1. https://share.streamlit.io/ 에서 GitHub 계정으로 로그인합니다.
2. Create app을 선택하고 `yn7844-maker/compliance77` 저장소에 대한 접근을 허용합니다.
3. 다음 값을 선택합니다.
   - Repository: `yn7844-maker/compliance77`
   - Branch: `main`
   - Main file path: `app.py`
   - Advanced settings → Python version: `3.12`
4. Deploy를 누릅니다. Python 패키지는 루트 `requirements.txt`, 시스템 OCR은 루트 `packages.txt`에서 설치합니다. 외부 API 키나 secrets 입력은 필요하지 않습니다.
5. 배포 후 발급된 `https://…streamlit.app` 주소로 접속합니다. 이 URL은 Streamlit이 발급하는 값이며 저장소 이름만으로 확정할 수 없습니다.
6. 가상 패키지 case03을 불러오고, 하단의 현재 입력 최종 확인을 체크한 후 Word 다운로드를 확인합니다.
7. `sample_data/pdf/case03_scan.pdf` 업로드로 OCR을 별도 확인합니다. 인식 오류는 STEP 3에서 수정하고 최종 확인합니다.

화면이 뜨지 않으면 Manage app의 로그에서 requirements/packages 설치 오류를 확인합니다. OCR 언어 오류는 `tesseract-ocr-kor` 설치 여부를 확인하세요. 저장소가 private인 경우 연결한 GitHub 계정과 Streamlit의 저장소 접근 권한이 필요합니다. 저장소 공개 전환은 필수가 아니며 자동으로 변경하지 않습니다.

배포 완료 후 `main`에 push하면 Streamlit이 변경을 반영합니다. 초기 설치·재시작 시 live 프로세스는 새로 시작됩니다. Streamlit Community Cloud 계정 로그인과 최종 Deploy는 해당 계정의 웹 화면에서 진행해야 합니다.
