import hashlib
import json
import time
import streamlit as st
from models.schemas import Report

def initialize():
    for key,value in {'seed':Report().model_dump(mode='json'),'revision':0,'documents':{},'extractions':[], 'started':time.monotonic(),'downloads':0,'audit':[]}.items():
        if key not in st.session_state: st.session_state[key]=value

def load_report(report: Report):
    st.session_state.seed=report.model_dump(mode='json')
    st.session_state.revision+=1

def fingerprint(report: Report) -> str:
    payload=report.model_dump(mode='json');payload['reviewed']=False
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
