CREATE TABLE flo_heatlh_hackathon.team7.focus_nutrients_by_phase (
  phase STRING COLLATE UTF8_BINARY,
  nutrient STRING COLLATE UTF8_BINARY,
  evidence_level STRING COLLATE UTF8_BINARY,
  tagline STRING COLLATE UTF8_BINARY)
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
