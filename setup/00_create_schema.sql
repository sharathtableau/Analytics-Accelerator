-- One-time setup for the Enterprise edition. Isolated schema: nothing in
-- WBR_DB.DECISION_STUDIO_REACT_POC (the current app) is touched.
USE ROLE WBR_OWNER;
CREATE SCHEMA IF NOT EXISTS WBR_DB.ANALYTICS_ENTERPRISE
  COMMENT = 'Analytics Accelerator - Enterprise edition (demo build)';
CREATE STAGE IF NOT EXISTS WBR_DB.ANALYTICS_ENTERPRISE.EVAL_STAGE
  DIRECTORY = (ENABLE = TRUE) COMMENT = 'AI Quality evaluation datasets';
SHOW SCHEMAS LIKE 'ANALYTICS_ENTERPRISE' IN DATABASE WBR_DB;
