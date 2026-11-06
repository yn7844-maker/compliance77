#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
# 시스템 Tesseract 엔진과 eng/osd는 OS 패키지로 설치해야 합니다.
if ! command -v tesseract >/dev/null; then
  echo 'Tesseract 없음: 텍스트 PDF는 사용 가능. OCR은 README의 OS 설치 절차를 따르세요.' >&2
else
  mkdir -p .local/tessdata
  for lang in eng osd; do
    if [ -f "/usr/share/tesseract-ocr/5/tessdata/$lang.traineddata" ]; then
      cp "/usr/share/tesseract-ocr/5/tessdata/$lang.traineddata" .local/tessdata/
    fi
  done
  if [ ! -f .local/tessdata/kor.traineddata ]; then
    curl --fail --location https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/kor.traineddata -o .local/tessdata/kor.traineddata.download
    echo '6b85e11d9bbf07863b97b3523b1b112844c43e713df8b66418a081fd1060b3b2  .local/tessdata/kor.traineddata.download' | sha256sum --check -
    mv .local/tessdata/kor.traineddata.download .local/tessdata/kor.traineddata
  fi
  echo '6b85e11d9bbf07863b97b3523b1b112844c43e713df8b66418a081fd1060b3b2  .local/tessdata/kor.traineddata' | sha256sum --check -
fi
# 기존 템플릿/가상 출력물을 덮어쓰지 않습니다. 명시적 갱신은 generate_samples.py 사용.
.venv/bin/python -c 'from core.word_generator import DEFAULT_TEMPLATE; assert DEFAULT_TEMPLATE.exists(), "배포 템플릿이 없습니다. scripts/generate_samples.py 실행 필요"'
.venv/bin/python -m pip check
