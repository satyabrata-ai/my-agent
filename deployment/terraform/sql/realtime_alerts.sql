-- BigQuery DDL to create the `realtime_alerts` table
-- This file is used by the project migration script and Terraform/CI to create the alerts table.
-- Replace `${project_id}` and `${dataset_id}` with runtime values when executing via scripts.

CREATE TABLE IF NOT EXISTS `${project_id}.${dataset_id}.realtime_alerts` (
  id STRING NOT NULL,
  timestamp TIMESTAMP,
  ticker STRING,
  alert_type STRING,
  severity STRING,
  metric STRING,
  metric_value FLOAT64,
  description STRING,
  details JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY ticker;

-- Recommended indices: partitioning + clustering help with recent lookups by ticker and time
