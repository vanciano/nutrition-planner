from unittest.mock import MagicMock

import pytest

import retrieval
import warehouse
from config import settings


@pytest.fixture(autouse=True)
def _reset_state():
    """Each test gets a clean static cache and the default retrieval mode."""
    retrieval._static_cache = None
    original_mode = settings.retrieval_mode
    original_index = settings.vector_index
    yield
    retrieval._static_cache = None
    settings.retrieval_mode = original_mode
    settings.vector_index = original_index


def test_static_context_for_phase(monkeypatch):
    settings.retrieval_mode = "static"
    rows = [
        {"cycle_phase": "luteal", "iron_mg": 16, "magnesium_mg": 320, "_rescued_data": "x"},
        {"cycle_phase": "menstrual", "iron_mg": 18, "_rescued_data": "x"},
    ]
    monkeypatch.setattr(warehouse, "query", lambda *a, **k: [dict(r) for r in rows])

    out = retrieval.context_for("anything", phase="luteal")
    assert isinstance(out, str)
    assert out
    assert "luteal" in out
    # nutrient text is included, _rescued_data is excluded
    assert "iron_mg=16" in out
    assert "magnesium_mg=320" in out
    assert "_rescued_data" not in out


def test_vector_context(monkeypatch):
    settings.retrieval_mode = "vector"
    settings.vector_index = "cat.sch.idx"

    fake_index = MagicMock()
    fake_index.similarity_search.return_value = {
        "result": {"data_array": [["Oatmeal", "luteal", "desc", "iron"]]}
    }
    fake_client = MagicMock()
    fake_client.get_index.return_value = fake_index

    fake_module = MagicMock()
    fake_module.VectorSearchClient.return_value = fake_client
    # retrieval imports VectorSearchClient lazily inside _vector_context
    monkeypatch.setitem(
        __import__("sys").modules, "databricks.vector_search.client", fake_module
    )

    out = retrieval.context_for("breakfast ideas", phase="luteal")
    assert "Oatmeal" in out
    assert "iron" in out
