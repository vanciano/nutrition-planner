"""Foundation Model API client (Databricks Model Serving).

Uses the OpenAI-compatible client from the Databricks SDK. Auth is the app
service principal (or local profile) via WorkspaceClient -- no infra to stand up,
no tokens handled in app code.
"""
from databricks.sdk import WorkspaceClient
from openai import OpenAI

from config import get_logger, settings

logger = get_logger(__name__)
_w: WorkspaceClient | None = None


def _ws() -> WorkspaceClient:
    # Lazy so importing this module never triggers SDK/network init.
    global _w
    if _w is None:
        _w = WorkspaceClient()
    return _w

SYSTEM_PROMPT = (
    "You are Flo's nutrition assistant. Give concise, actionable meal guidance "
    "tailored to the user's menstrual cycle phase. Ground your advice in the "
    "provided phase nutrient targets and meal context when available. "
    "Never give medical diagnoses; suggest consulting a clinician for medical concerns."
)


def client():
    """OpenAI-compatible client bound to the Databricks serving endpoints.

    Mints a fresh SP token per call via the SDK auth headers (works across
    databricks-sdk versions; the token is used transiently and never stored).
    """
    w = _ws()
    token = w.config.authenticate()["Authorization"].split(" ", 1)[1]
    return OpenAI(base_url=f"{w.config.host}/serving-endpoints", api_key=token)


def chat(messages: list[dict], phase_context: str | None = None) -> str:
    """Send a chat completion request and return the assistant reply text."""
    msgs: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if phase_context:
        msgs.append(
            {"role": "system", "content": f"Relevant nutrition context:\n{phase_context}"}
        )
    msgs.extend(messages)

    logger.info("LLM chat request endpoint=%s msgs=%d", settings.llm_endpoint, len(msgs))
    resp = client().chat.completions.create(
        model=settings.llm_endpoint,
        messages=msgs,
        max_tokens=800,
    )
    return resp.choices[0].message.content or ""
