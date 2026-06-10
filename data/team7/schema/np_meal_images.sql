CREATE TABLE flo_heatlh_hackathon.team7.np_meal_images (
  meal_id STRING COLLATE UTF8_BINARY,
  image_url STRING COLLATE UTF8_BINARY,
  icon STRING COLLATE UTF8_BINARY,
  source STRING COLLATE UTF8_BINARY,
  license STRING COLLATE UTF8_BINARY,
  attribution_title STRING COLLATE UTF8_BINARY)
USING delta
COMMENT 'Unique per-meal images. image_url = CC-licensed photo source (Openverse aggregator; mostly Flickr) keyed per meal, distinct image per recipe variant. icon = emoji fallback. Attribution in license/attribution_title. Prototype uses downsized local copies in experiments/ui/img/.'
TBLPROPERTIES (
  'delta.checkpoint.writeStatsAsJson' = 'false',
  'delta.checkpoint.writeStatsAsStruct' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.domainMetadata' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd')
