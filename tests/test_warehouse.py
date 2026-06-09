from unittest.mock import MagicMock

from databricks import sql

import warehouse


def _make_fake_connect(captured):
    """Return a fake sql.connect that records kwargs and yields a fake cursor."""
    cursor = MagicMock()
    cursor.description = [("a",)]
    cursor.fetchall.return_value = [(1,)]
    # cursor is used as a context manager: ``with conn.cursor() as cur``
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    cursor_cm.__exit__.return_value = False

    conn = MagicMock()
    conn.cursor.return_value = cursor_cm

    conn_cm = MagicMock()
    conn_cm.__enter__.return_value = conn
    conn_cm.__exit__.return_value = False

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return conn_cm

    return fake_connect


def test_query_with_user_token(monkeypatch):
    captured = {}
    monkeypatch.setattr(sql, "connect", _make_fake_connect(captured))

    result = warehouse.query("SELECT 1", user_token="tok")

    assert captured.get("access_token") == "tok"
    assert "credentials_provider" not in captured
    assert result == [{"a": 1}]


def test_query_without_token(monkeypatch):
    captured = {}
    monkeypatch.setattr(sql, "connect", _make_fake_connect(captured))

    result = warehouse.query("SELECT 1")

    assert "credentials_provider" in captured
    assert "access_token" not in captured
    assert result == [{"a": 1}]
