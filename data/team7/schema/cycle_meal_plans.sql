CREATE TABLE flo_heatlh_hackathon.team7.cycle_meal_plans (
  meal_id STRING COLLATE UTF8_BINARY,
  cycle_phase STRING COLLATE UTF8_BINARY,
  meal_type STRING COLLATE UTF8_BINARY,
  meal_name STRING COLLATE UTF8_BINARY,
  description STRING COLLATE UTF8_BINARY,
  key_nutrients STRING COLLATE UTF8_BINARY,
  calories INT,
  iron_mg DOUBLE,
  magnesium_mg DOUBLE,
  omega3_g DOUBLE,
  vitamin_c_mg DOUBLE,
  prep_time_min INT,
  dietary_tags STRING COLLATE UTF8_BINARY)
USING delta
COMMENT 'Cycle-phase meal plans (500 meals) cleaned + copied from uc5_nutrition_planner. Removed _rescued_data; trimmed text; 14 missing dietary_tags filled with synthetic value "omnivore" (all were meat-based dishes with no special diet).'
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
