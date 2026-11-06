from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4
import streamlit as st
from models.schemas import Report, Audit

def initialize():
    for key in ["word_success","word_failures"]:
        st.session_state.setdefault(key,0)
    if "report" not in st.session_state:
        st.session_state.report=Report()
        st.session_state.documents={}
        st.session_state.revision=uuid4().hex
        st.session_state.started=monotonic()
        st.session_state.downloads=0
        st.session_state.word_success=0
        st.session_state.word_failures=0

def replace_report(report, documents=None):
    st.session_state.report=report
    if documents is not None: st.session_state.documents=documents
    st.session_state.revision=uuid4().hex
    st.session_state.started=monotonic()

def record_changes(before: Report, after: Report):
    # 세션 메모리에만 수정 이력을 저장한다. 서버 로그/DB에는 기록하지 않는다.
    a=before.model_dump(mode="json",exclude={"audit"})
    b=after.model_dump(mode="json",exclude={"audit"})
    def walk(x,y,path):
        if isinstance(x,dict) and isinstance(y,dict):
            for key in x.keys() | y.keys(): walk(x.get(key),y.get(key),path+"."+key)
        elif x!=y:
            after.audit.append(Audit(field=path,before=str(x),after=str(y),at=datetime.now(timezone.utc).isoformat()))
    walk(a,b,"report")

def widget_key(name): return st.session_state.revision+name
