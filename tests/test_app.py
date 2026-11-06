from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

def test_manual_draft_screen():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not app.exception
    assert any('담보평가결과서 자동작성 시스템' in t.value for t in app.title)
    assert len(app.get('download_button'))==1
    assert '초안' in app.get('download_button')[0].label

def test_sample_to_final_download():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.selectbox[0].select('case03').run()
    next(b for b in app.button if b.label=='가상 패키지 불러오기').click().run()
    assert not app.exception
    next(c for c in app.checkbox if c.label=='현재 입력과 원본 대조를 완료했으며 담당자로서 최종 확인합니다').check().run()
    assert not app.exception
    assert app.get('download_button')[0].label=='담보평가결과서 다운로드'
    # 금액 변경 후 이전 최종 확인이 재사용되지 않아야 함
    next(t for t in app.text_input if t.label=='평가의뢰금액 (천원)').set_value('200000').run()
    assert '초안' in app.get('download_button')[0].label
