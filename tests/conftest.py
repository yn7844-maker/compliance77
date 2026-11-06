from pathlib import Path
import pytest
from models.schemas import Report
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def root(): return ROOT
@pytest.fixture
def complete(root): return Report.model_validate_json((root/"sample_data/packages/package_01.json").read_text())
