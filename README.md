# Nutrition Planner (Team 7)

A cycle-phase-aware nutrition planner built as a Databricks App. It pairs a chat
assistant with per-phase nutrient goals and meal-plan data so users get nutrition
guidance tailored to where they are in their cycle.

## Stack

- **Backend:** FastAPI (`src/app`, run with `uvicorn app:app`)
- **Frontend:** React + Vite (`frontend/`), built into `src/app/static` and served by FastAPI at `/`
- **Data store:** Unity Catalog sample data (read); a Delta table in our writable `team7`
  schema for app-owned user profiles, with an in-memory fallback when no warehouse is
  configured (see [Profile persistence](#profile-persistence))
- **Hosting:** Databricks Apps (Declarative Asset Bundle)
- **LLM:** Databricks Foundation Model API (`databricks-claude-sonnet-4-6`)
- **Retrieval:** static dictionary by default; opt-in **Vector Search** (`databricks-gte-large-en` embeddings)

## Prerequisites

- **Databricks CLI** configured with the `hackathons` profile
  (workspace `https://emerging-emea-hackathons.cloud.databricks.com`)
- **Node.js** (for the Vite frontend)
- **Python 3** (for the backend and the index builder)

Auth uses the CLI profile locally and the app's service principal (OAuth) in
production. Both are out-of-the-box: no tokens are stored in this repo, and no
raw tokens are logged. See [Token hygiene](#token-hygiene).

## Local development

```bash
scripts/dev.sh
```

This starts the backend on `:8000` and the Vite dev server on `:5173`. Open
**http://localhost:5173** — the dev server proxies `/api` to the backend.

## Testing

```bash
scripts/test.sh                    # unit tests (pytest -m "not integration")
RUN_INTEGRATION=1 scripts/test.sh  # also run integration tests
```

Activates `.venv` automatically if present.

## Deploy

```bash
scripts/deploy.sh
```

Runs the pre-deploy gate and ships the app:

1. `scripts/test.sh` (aborts on failure)
2. `scripts/build.sh` (frontend → `src/app/static`)
3. `databricks bundle validate -t dev -p hackathons`
4. `databricks bundle deploy -t dev -p hackathons`
5. `databricks bundle run nutrition_planner -t dev -p hackathons`
6. **First-deploy bootstrap (safe to re-run):** grants the app's service
   principal read access to the sample schema and `CAN_QUERY` on the LLM
   endpoint. These steps are non-fatal — re-running after grants already exist
   is harmless.
7. Prints the deployed app URL.

## Project layout

```
nutrition-planner/
├── databricks.yml            # bundle definition (target: dev)
├── resources/
│   └── app.app.yml           # app resource (nutrition_planner -> nutrition-planner-dev)
├── src/app/
│   ├── app.yaml              # app command + env vars
│   ├── app.py                # FastAPI entrypoint (uvicorn app:app)
│   ├── config.py             # env-driven settings + logging
│   ├── retrieval.py          # static | vector retrieval backends
│   ├── warehouse.py          # SQL warehouse queries
│   └── static/               # built frontend (generated)
├── frontend/                 # React + Vite SPA
├── scripts/
│   ├── build.sh              # build frontend into src/app/static
│   ├── dev.sh                # local backend + frontend dev servers
│   ├── test.sh               # pytest gate
│   ├── deploy.sh             # gate + bundle deploy + bootstrap grants
│   └── index_build.py        # opt-in RAG index builder (see below)
└── README.md
```

## Environment variables

These are set in `src/app/app.yaml` (defaults mirrored in `src/app/config.py`):

| Variable                  | Value / source                | Purpose                                   |
| ------------------------- | ----------------------------- | ----------------------------------------- |
| `DATABRICKS_WAREHOUSE_ID` | from `sql-warehouse` resource | SQL warehouse for UC queries              |
| `NUTRITION_CATALOG`       | `flo_heatlh_hackathon`        | Unity Catalog catalog                     |
| `NUTRITION_SCHEMA`        | `uc5_nutrition_planner`       | Read-only sample data schema              |
| `NUTRITION_TEAM_SCHEMA`   | `team7`                       | Our writable schema                       |
| `LLM_ENDPOINT`            | `databricks-claude-sonnet-4-6`| Foundation Model API chat endpoint        |
| `RETRIEVAL_MODE`          | `static`                      | Retrieval backend: `static` or `vector`   |
| `EMBEDDING_ENDPOINT`      | `databricks-gte-large-en`     | Embedding endpoint (vector mode)          |
| `VECTOR_ENDPOINT`         | _(unset by default)_          | Vector Search endpoint name (vector mode) |
| `VECTOR_INDEX`            | _(unset by default)_          | Vector Search index name (vector mode)    |

## RAG scale-up

The app ships with `RETRIEVAL_MODE=static`: it preloads a compact per-phase
nutrient dictionary and feeds it to the model as context. This needs **zero
extra infra** and is the default.

To scale up to semantic retrieval over the meal-plan data:

1. Build the index (one-time, opt-in):

   ```bash
   DATABRICKS_CONFIG_PROFILE=hackathons python3 scripts/index_build.py
   ```

   This creates a source Delta table `flo_heatlh_hackathon.team7.meals`, ensures a
   Vector Search endpoint (`nutrition-vs`), and creates a TRIGGERED Delta Sync
   index `flo_heatlh_hackathon.team7.meals_idx` embedded via
   `databricks-gte-large-en`.

   > **Note:** provisioning the Vector Search endpoint takes several **minutes**.
   > The script is **not** part of `scripts/deploy.sh`, and it is safe to re-run.

2. Flip the app to vector mode by setting these in `src/app/app.yaml`
   (values are printed by `index_build.py`):

   ```yaml
   - name: RETRIEVAL_MODE
     value: "vector"
   - name: VECTOR_ENDPOINT
     value: "nutrition-vs"
   - name: VECTOR_INDEX
     value: "flo_heatlh_hackathon.team7.meals_idx"
   ```

3. Redeploy with `scripts/deploy.sh`.

## Profile persistence

User profiles (`/api/profile`, the Profile tab) persist in a Delta table
`flo_heatlh_hackathon.team7.user_profiles`, read/written through the SQL warehouse as the
app's service principal and keyed by the signed-in user (`X-Forwarded-Email`). Diets and
allergies are stored as JSON strings. See [src/app/db.py](src/app/db.py).

When no real warehouse is configured (tests use the `test-wh` placeholder; warehouse-less
local runs), the store falls back to a **process-local in-memory dict** — the API works
end-to-end, but values reset on restart. No setup needed for local dev or tests.

On deploy, [scripts/deploy.sh](scripts/deploy.sh) grants the app SP `USE SCHEMA` +
`CREATE TABLE` + `SELECT` + `MODIFY` on `team7`; the table is created automatically on
first use and the startup log shows `profile_persistence=True`.

## Token hygiene

No raw tokens are stored in this repo or written to logs. Local development
authenticates via the Databricks CLI `hackathons` profile; in production the
app authenticates as its **service principal via OAuth**, provisioned
out-of-the-box by Databricks Apps. The first deploy grants that service
principal the data and endpoint permissions it needs (see
[Deploy](#deploy)).
