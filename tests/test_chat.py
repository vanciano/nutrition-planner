import llm
import retrieval


def test_chat_ok(client, monkeypatch):
    calls = {}

    def fake_context_for(query, phase=None, user_token=None):
        calls["context_for"] = {"query": query, "phase": phase, "user_token": user_token}
        return "CTX"

    def fake_chat(messages, phase_context=None):
        calls["chat"] = {"messages": messages, "phase_context": phase_context}
        return "PLAN"

    monkeypatch.setattr(retrieval, "context_for", fake_context_for)
    monkeypatch.setattr(llm, "chat", fake_chat)

    resp = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "what should I eat?"}]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"reply": "PLAN"}

    # both collaborators were invoked, and the retrieval context flowed into the LLM
    assert "context_for" in calls
    assert calls["context_for"]["query"] == "what should I eat?"
    assert "chat" in calls
    assert calls["chat"]["phase_context"] == "CTX"


def test_chat_llm_error_returns_500(client, monkeypatch):
    monkeypatch.setattr(retrieval, "context_for", lambda *a, **k: "CTX")

    def boom(*a, **k):
        raise RuntimeError("llm exploded")

    monkeypatch.setattr(llm, "chat", boom)

    resp = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}
