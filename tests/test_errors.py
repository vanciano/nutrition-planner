"""The global exception handler must never leak internals to the client."""
import warehouse


def test_global_handler_does_not_leak_secrets(client, monkeypatch):
    def boom(*a, **k):
        # an exception whose message contains token-like material
        raise RuntimeError("auth failed: Bearer SECRET123")

    monkeypatch.setattr(warehouse, "query", boom)

    resp = client.get("/api/phases")
    assert resp.status_code == 500

    body = resp.text
    assert "SECRET123" not in body
    assert "Bearer" not in body
    assert resp.json() == {"detail": "Internal server error"}
