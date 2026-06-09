"""Application configuration and logging setup.

All settings come from environment variables so the same code runs locally
(profile auth) and in Databricks Apps (service-principal auth, injected env).
"""
import logging
import os

# --- logging -----------------------------------------------------------------
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# --- settings ----------------------------------------------------------------
class Settings:
    # Unity Catalog (read-only sample source)
    catalog: str = os.environ.get("NUTRITION_CATALOG", "flo_heatlh_hackathon")
    schema: str = os.environ.get("NUTRITION_SCHEMA", "uc5_nutrition_planner")
    team_schema: str = os.environ.get("NUTRITION_TEAM_SCHEMA", "team7")

    # SQL warehouse
    warehouse_id: str = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")

    # Auth identity for warehouse reads:
    #   "sp"  -> app service principal (default; needs SELECT granted to the SP)
    #   "obo" -> on-behalf-of the signed-in user (needs user authorization + sql scope)
    auth_mode: str = os.environ.get("AUTH_MODE", "sp")

    # Foundation Model API (chat)
    llm_endpoint: str = os.environ.get("LLM_ENDPOINT", "databricks-claude-sonnet-4-6")

    # Retrieval / RAG
    retrieval_mode: str = os.environ.get("RETRIEVAL_MODE", "static")  # static | vector
    embedding_endpoint: str = os.environ.get(
        "EMBEDDING_ENDPOINT", "databricks-gte-large-en"
    )
    vector_endpoint: str = os.environ.get("VECTOR_ENDPOINT", "")
    vector_index: str = os.environ.get("VECTOR_INDEX", "")

    @property
    def profile_persistence(self) -> bool:
        """True when a real warehouse backs profiles (else the in-memory fallback).

        The test suite runs with the placeholder ``test-wh`` warehouse id and must use
        the in-memory store, so that value is treated as 'no persistence'.
        """
        return bool(self.warehouse_id) and self.warehouse_id != "test-wh"

    @property
    def phase_goals_table(self) -> str:
        return f"{self.catalog}.{self.schema}.phase_nutrient_goals"

    @property
    def user_profiles_table(self) -> str:
        return f"{self.catalog}.{self.team_schema}.user_profiles"

    @property
    def meal_plans_table(self) -> str:
        return f"{self.catalog}.{self.schema}.cycle_meal_plans"

    # --- Plan tab: the synthetic meal + nutrition dictionaries live in the
    # team7 schema (not the read-only uc5 sample). All keyed by meal_id. ----
    def _team(self, name: str) -> str:
        return f"{self.catalog}.{self.team_schema}.{name}"

    @property
    def cycle_meals_table(self) -> str:
        return self._team("cycle_meal_plans")

    @property
    def meal_nutrition_table(self) -> str:
        return self._team("np_meal_nutrition")

    @property
    def meal_allergens_table(self) -> str:
        return self._team("np_meal_allergens")

    @property
    def meal_ingredients_table(self) -> str:
        return self._team("np_meal_ingredients")

    @property
    def meal_images_table(self) -> str:
        return self._team("np_meal_images")

    @property
    def meal_images_direct_table(self) -> str:
        # backfilled direct image URLs (resolved from the Flickr/Wikimedia page
        # og:image); the base table only has unembeddable page URLs.
        return self._team("np_meal_images_direct")

    @property
    def focus_nutrients_table(self) -> str:
        return self._team("focus_nutrients_by_phase")

    @property
    def daily_targets_table(self) -> str:
        return self._team("daily_nutrition_targets")


settings = Settings()


def log_startup_config() -> None:
    """Log the effective (non-secret) config so env issues are obvious in logs.

    No tokens/credentials are logged -- only resolved identifiers and flags.
    """
    log = get_logger("config")
    log.info(
        "startup config: catalog=%s schema=%s team_schema=%s warehouse_id=%s "
        "auth_mode=%s llm_endpoint=%s retrieval_mode=%s vector_index=%s "
        "profile_persistence=%s",
        settings.catalog,
        settings.schema,
        settings.team_schema,
        settings.warehouse_id or "<unset>",
        settings.auth_mode,
        settings.llm_endpoint,
        settings.retrieval_mode,
        settings.vector_index or "<unset>",
        settings.profile_persistence,
    )
    # Flag likely-misconfig early (warn, don't crash).
    if not settings.warehouse_id:
        log.warning("DATABRICKS_WAREHOUSE_ID is unset -- /api/phases and chat context will fail")
    if settings.retrieval_mode == "vector" and not settings.vector_index:
        log.warning("RETRIEVAL_MODE=vector but VECTOR_INDEX is unset -- retrieval will fail")
