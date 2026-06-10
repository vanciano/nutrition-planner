# team7 data dump

A point-in-time export of the `flo_heatlh_hackathon.team7` schema — the reference
data the app reads (meals, nutrition, focus nutrients, targets, images) plus the
app's `user_profiles`. Kept in-repo so the app's data can be inspected offline and
rebuilt in a fresh workspace/schema if the hackathon environment goes away.

## Contents

| file | rows | what |
|---|---|---|
| `cycle_meal_plans.csv` | 500 | meal pool per phase/slot (name, description, key_nutrients, macros/micros, dietary_tags) |
| `np_meal_nutrition.csv` | 500 | per-meal macros + micros (protein, fiber, iron, magnesium, B6, calcium, …) |
| `np_meal_allergens.csv` | 500 | per-meal allergen booleans (contains_nuts/dairy/…) |
| `np_meal_ingredients.csv` | 1694 | meal → ingredient rows (food_name, grams, role) |
| `np_meal_images.csv` | 500 | source image page URL + emoji icon |
| `np_meal_images_direct.csv` | 486 | backfilled direct image URLs (resolved from page og:image) |
| `np_nutrition_enriched.csv` | 7797 | USDA-style per-food nutrition (79 cols) |
| `nutrition_clean.csv` | 7797 | cleaned per-food nutrition (75 cols) |
| `focus_nutrients_by_phase.csv` | 12 | phase → focus nutrient, evidence level, tagline |
| `daily_nutrition_targets.csv` | 18 | constant daily macro/micro targets |
| `phase_nutrient_goals.csv` | 4 | per-phase nutrient goals (read-only sample copy) |
| `user_profiles.csv` | 5 | app per-user profiles — **contains user emails**; hackathon data only |
| `schema/<table>.sql` | — | `SHOW CREATE TABLE` DDL for each table |

> ⚠️ `user_profiles.csv` holds real user emails (the app's saved diets/allergies/energy
> target). It's included per request; treat it as throwaway hackathon data, not for
> redistribution.

## How it was produced

`scripts/export_team7.py` — runs `SELECT *` + `SHOW CREATE TABLE` via the Databricks
SQL Statement Execution REST API (profile `hackathons`, warehouse `56adb3367ffc45e8`)
and writes CSV + DDL here. Re-run it to refresh the dump.

## Restore into a fresh schema

```bash
# recreate tables + load data into a target catalog.schema (default: flo_heatlh_hackathon.team7)
.venv/bin/python scripts/restore_team7.py --target <catalog>.<schema>
```

The script creates each table from `schema/*.sql` (rewriting the FQN to the target)
and loads the CSV rows. Cells are inserted as string literals and implicitly cast by
the target column types. For very large tables this is slow; alternatively load the
CSVs with Spark (`spark.read.csv(..., header=True)` → `saveAsTable`) or `COPY INTO`
from a Unity Catalog volume.
