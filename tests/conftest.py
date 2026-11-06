import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.schemas import Report
@pytest.fixture
def complete():
    return Report.model_validate_json((ROOT/'sample_data/expected/case03_report.json').read_text())
