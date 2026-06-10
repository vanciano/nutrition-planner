CREATE TABLE flo_heatlh_hackathon.team7.phase_nutrient_goals (
  cycle_phase STRING COLLATE UTF8_BINARY,
  iron_mg DOUBLE,
  vitamin_c_mg DOUBLE,
  magnesium_mg DOUBLE,
  omega3_g DOUBLE,
  vitamin_b6_mg DOUBLE,
  calcium_mg DOUBLE,
  zinc_mg DOUBLE,
  fiber_g DOUBLE,
  protein_g DOUBLE,
  calories INT)
USING delta
COMMENT 'Per-cycle-phase daily nutrient targets (4 rows) cleaned + copied from uc5_nutrition_planner. Removed _rescued_data. No missing values.'
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
