"""Retrieval / grounding for the chat assistant.

Two backends, switched by ``RETRIEVAL_MODE``:

- ``static`` (default, zero infra): preload the compact reference dictionary
  (per-phase nutrient goals + a short meal-plan digest) and return it as context.
  This is the "fit the dictionary into the model before queries" path.
- ``vector`` (opt-in): query a Databricks Vector Search Delta Sync index whose
  vectors are produced by the embedding endpoint. Requires the index built via
  ``scripts/index_build.py`` and ``VECTOR_ENDPOINT`` / ``VECTOR_INDEX`` set.
"""
from config import get_logger, settings
import warehouse

logger = get_logger(__name__)

# cache of the static dictionary, loaded lazily once
_static_cache: dict[str, str] | None = None


def _load_static(user_token: str | None = None) -> dict[str, str]:
    """Build a per-phase context string from phase_nutrient_goals (read-only UC).

    Cache only the service-principal/local result. Under OBO (a per-user token)
    we query fresh every time so each user's UC permissions are honored and one
    user's authorized result is never served to another.
    """
    global _static_cache
    if user_token is None and _static_cache is not None:
        return _static_cache

    rows = warehouse.query(
        f"SELECT * FROM {settings.phase_goals_table}", user_token=user_token
    )
    cache: dict[str, str] = {}
    for r in rows:
        phase = (r.get("cycle_phase") or "").lower()
        targets = ", ".join(
            f"{k}={v}" for k, v in r.items() if k not in ("cycle_phase", "_rescued_data") and v is not None
        )
        cache[phase] = f"Phase '{phase}' daily targets: {targets}"
    if user_token is None:
        _static_cache = cache
    logger.info("Loaded static retrieval dictionary for %d phases", len(cache))
    return cache


def _static_context(query: str, phase: str | None, user_token: str | None) -> str:
    cache = _load_static(user_token=user_token)
    if phase and phase.lower() in cache:
        return cache[phase.lower()]
    # no phase given -> return the whole compact dictionary
    return "\n".join(cache.values())


def _vector_context(query: str, phase: str | None, k: int = 5) -> str:
    from databricks.vector_search.client import VectorSearchClient

    vsc = VectorSearchClient(disable_notice=True)
    index = vsc.get_index(
        endpoint_name=settings.vector_endpoint, index_name=settings.vector_index
    )
    res = index.similarity_search(
        query_text=query,
        columns=["meal_name", "cycle_phase", "description", "key_nutrients"],
        num_results=k,
    )
    rows = res.get("result", {}).get("data_array", []) if isinstance(res, dict) else []
    return "\n".join(" | ".join(str(c) for c in row) for row in rows)


def context_for(query: str, phase: str | None = None, user_token: str | None = None) -> str:
    """Return grounding context for a user query under the active retrieval mode."""
    if settings.retrieval_mode == "vector" and settings.vector_index:
        logger.info("Retrieval mode=vector")
        return _vector_context(query, phase)
    logger.info("Retrieval mode=static")
    return _static_context(query, phase, user_token)
