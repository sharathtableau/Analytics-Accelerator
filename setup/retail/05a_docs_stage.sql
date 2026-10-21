-- Harborline documents -> Cortex Search (A1/C5 in ENTERPRISE_TRACKER.md). Part 1: stage.
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.RETAIL_DEMO;
-- AI_PARSE_DOCUMENT needs server-side encryption and a directory table on the stage.
CREATE STAGE IF NOT EXISTS RETAIL_DOCS_STAGE
  DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Harborline (fictional) policy PDFs, WBR notes and plan memo for Cortex Search';
