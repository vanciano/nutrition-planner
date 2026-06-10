CREATE TABLE flo_heatlh_hackathon.team7.np_meal_allergens (
  meal_id STRING COLLATE UTF8_BINARY,
  meal_name STRING COLLATE UTF8_BINARY,
  cycle_phase STRING COLLATE UTF8_BINARY,
  meal_type STRING COLLATE UTF8_BINARY,
  dietary_tags STRING COLLATE UTF8_BINARY,
  contains_nuts BOOLEAN,
  contains_dairy BOOLEAN,
  contains_gluten BOOLEAN,
  contains_shellfish BOOLEAN,
  contains_eggs BOOLEAN,
  contains_soy BOOLEAN,
  contains_sesame BOOLEAN,
  allergens STRING COLLATE UTF8_BINARY)
USING delta
COMMENT 'Precomputed allergen flags per meal (all 500), derived from np_meal_ingredients x np_nutrition_enriched. Covers app Allergies UI: nuts, dairy, gluten, shellfish, eggs, soy, sesame. Ingredient-name + food_group based. Gluten uses word-boundary wheat match (excludes buckwheat). allergens = semicolon list ("" if none).'
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
