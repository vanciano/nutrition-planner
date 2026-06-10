CREATE TABLE flo_heatlh_hackathon.team7.daily_nutrition_targets (
  nutrient_category STRING COLLATE UTF8_BINARY,
  nutrient_name STRING COLLATE UTF8_BINARY,
  daily_target_value BIGINT,
  unit STRING COLLATE UTF8_BINARY,
  target_type STRING COLLATE UTF8_BINARY,
  applies_to_phase STRING COLLATE UTF8_BINARY,
  basis STRING COLLATE UTF8_BINARY,
  notes STRING COLLATE UTF8_BINARY)
USING delta
COMMENT 'Created by the file upload UI'
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
