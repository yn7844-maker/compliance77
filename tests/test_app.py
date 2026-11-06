from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

def test_manual_draft_screen():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not app.exception
    assert any('담보평가결과서 자동작성 시스템' in t.value for t in app.title)
    assert len(app.get('download_button'))==0
    next(b for b in app.button if b.label=='빈 결과서 직접 작성').click().run()
    assert not app.exception
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


def test_one_click_text_to_word_draft():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    next(r for r in app.radio if r.label=='자료 입력 방법').set_value('텍스트 붙여넣기').run()
    next(t for t in app.text_area if t.label=='등기부등본 텍스트').set_value('등기사항증명서 [토지]\n【표제부】\n소재지: 가상시 시험동 1-1\n지목: 대\n면적: 84.5 m²\n【갑구】\n1 소유권이전 2024년 5월 10일\n소유자 가상소유자 지분 1분의 1').run()
    next(b for b in app.button if b.label=='결과서 초안 자동작성').click().run()
    assert not app.exception
    assert app.session_state['seed']['targets'][0]['address']=='가상시 시험동 1-1'
    assert app.get('download_button')[0].label=='담보평가결과서 초안 다운로드'
    assert all('STEP' not in h.value for h in app.subheader)
