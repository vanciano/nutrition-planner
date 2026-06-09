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
    def phase_goals_table(self) -> str:
        return f"{self.catalog}.{self.schema}.phase_nutrient_goals"

    @property
    def meal_plans_table(self) -> str:
        return f"{self.catalog}.{self.schema}.cycle_meal_plans"


settings = Settings()
