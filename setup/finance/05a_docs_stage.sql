-- Keystone Financial documents -> Cortex Search. Part 1: stage (the PUT of docs\*.md follows).
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.FINANCE_DEMO;
CREATE STAGE IF NOT EXISTS FINANCE_DOCS_STAGE
  DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Keystone Financial (fictional) business ontology: personas, metric dictionary, alert library, business rules';
