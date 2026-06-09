"""Shared pytest fixtures and import-time setup.

The backend runs with cwd=src/app and imports its modules by bare name
(``import warehouse``, ``from routers import ...``). To mirror that, we prepend
src/app to sys.path BEFORE importing any backend module, set required env vars,
and stub the Databricks SDK objects that are instantiated at import time
(``Config()`` in warehouse.py, ``WorkspaceClient()`` in llm.py) so collection
never makes a network call.
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# --- import path + env (must run before importing app modules) ---------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = _REPO_ROOT / "src" / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

os.environ.setdefault("DATABRICKS_WAREHOUSE_ID", "test-wh")
os.environ.setdefault("DATABRICKS_HOST", "https://test.cloud.databricks.com")

# --- stub Databricks SDK objects created at import time ----------------------
# warehouse.py does ``from databricks.sdk.core import Config`` then ``Config()``.
# llm.py does ``from databricks.sdk import WorkspaceClient`` then ``WorkspaceClient()``.
# Patch the classes on their source modules so the instances are harmless mocks.
import databricks.sdk
import databricks.sdk.core

_FakeConfig = MagicMock(name="Config")
_FakeConfig.return_value.host = "https://test.cloud.databricks.com"
databricks.sdk.core.Config = _FakeConfig
databricks.sdk.WorkspaceClient = MagicMock(name="WorkspaceClient")

# Now it is safe to import the FastAPI app and its modules.
from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402


@pytest.fixture
def client():
    """A TestClient bound to the real FastAPI app (external calls mocked).

    ``raise_server_exceptions=False`` lets the app's registered
    ``@app.exception_handler(Exception)`` produce its 500 JSONResponse instead
    of TestClient re-raising the error -- which is what real HTTP clients see.
    """
    return TestClient(app_module.app, raise_server_exceptions=False)


def _integration_enabled() -> bool:
    wh = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    return bool(wh) and wh != "test-wh" and os.environ.get("RUN_INTEGRATION") == "1"


def pytest_collection_modifyitems(config, items):
    """Skip integration-marked tests unless a real warehouse + opt-in flag are set."""
    if _integration_enabled():
        return
    skip = pytest.mark.skip(
        reason="integration tests require RUN_INTEGRATION=1 and a real "
        "DATABRICKS_WAREHOUSE_ID"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
