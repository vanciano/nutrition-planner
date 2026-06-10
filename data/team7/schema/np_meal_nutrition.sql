CREATE TABLE flo_heatlh_hackathon.team7.np_meal_nutrition (
  meal_id STRING COLLATE UTF8_BINARY,
  cycle_phase STRING COLLATE UTF8_BINARY,
  meal_type STRING COLLATE UTF8_BINARY,
  meal_name STRING COLLATE UTF8_BINARY,
  dietary_tags STRING COLLATE UTF8_BINARY,
  prep_time_min INT,
  n_ingredients BIGINT,
  scale_factor DOUBLE,
  calories_kcal DOUBLE,
  protein_g DOUBLE,
  iron_mg DOUBLE,
  magnesium_mg DOUBLE,
  vitamin_c_mg DOUBLE,
  vitamin_b6_mg DOUBLE,
  calcium_mg DOUBLE,
  zinc_mg DOUBLE,
  fiber_g DOUBLE,
  omega3_g DOUBLE,
  nutrition_is_computed BOOLEAN)
USING delta
COMMENT 'Step 3 / Gap A. Full 10-nutrient profile per meal. Composition COMPUTED from np_meal_ingredients x np_nutrition_enriched (per-100g * grams/100), then CALORIE-ANCHORED: every nutrient scaled by scale_factor = original_meal_calories / raw_computed_calories so absolute amounts are realistic (a meal != half a day). Nutrient ratios are real/food-derived; omega3 carries the estimated flag. Adds the 5 nutrients meals lacked: vitamin_b6, calcium, zinc, fiber, protein.'
TBLPROPERTIES (
  'delta.checkpoint.writeStatsAsJson' = 'false',
  'delta.checkpoint.writeStatsAsStruct' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')
