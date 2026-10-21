-- A2 in ENTERPRISE_TRACKER.md: custom Cortex Agent tool that ACTS — logs a decision in Snowflake.
-- The app adds it to the shared domain agent as tool "log_decision" (agent spec aa-spec-3).
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.ANALYTICS_ENTERPRISE;

-- Same table the app writes from the "Log decision" button (created here too in case the app hasn't run yet).
CREATE TABLE IF NOT EXISTS AA_DECISIONS (
  DECISION_ID VARCHAR, SEMANTIC_VIEW VARCHAR, TEMPLATE_ID VARCHAR, TITLE VARCHAR,
  DETAIL VARCHAR, OWNER VARCHAR, DUE_DATE DATE, STATUS VARCHAR, EVIDENCE VARIANT,
  CREATED_BY VARCHAR, CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
  UPDATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP());

-- Narrow, validated write: the agent can only insert one well-formed decision, nothing else.
-- Parameters are p_-prefixed (Snowflake guidance for agent custom tools).
CREATE OR REPLACE PROCEDURE AA_CREATE_DECISION(
    P_TITLE VARCHAR, P_DETAIL VARCHAR, P_OWNER VARCHAR, P_DUE_DATE VARCHAR,
    P_EVIDENCE VARCHAR, P_SEMANTIC_VIEW VARCHAR)
  RETURNS VARCHAR
  LANGUAGE SQL
  COMMENT = 'Cortex Agent tool log_decision: records a decision with owner, due date and evidence in AA_DECISIONS'
  EXECUTE AS CALLER
AS
$$
DECLARE
  did VARCHAR;
  due DATE;
BEGIN
  IF (P_TITLE IS NULL OR LENGTH(TRIM(P_TITLE)) < 5) THEN
    RETURN 'NOT LOGGED: a decision needs a short title (at least 5 characters).';
  END IF;
  IF (P_OWNER IS NULL OR LENGTH(TRIM(P_OWNER)) < 2) THEN
    RETURN 'NOT LOGGED: ask the user who owns this decision, then call again with p_owner.';
  END IF;
  due := TRY_TO_DATE(P_DUE_DATE);
  IF (P_DUE_DATE IS NOT NULL AND TRIM(P_DUE_DATE) <> '' AND due IS NULL) THEN
    RETURN 'NOT LOGGED: p_due_date must be a date in YYYY-MM-DD format.';
  END IF;
  IF (due < CURRENT_DATE()) THEN
    RETURN 'NOT LOGGED: the due date is in the past.';
  END IF;
  IF (P_SEMANTIC_VIEW IS NULL OR NOT REGEXP_LIKE(P_SEMANTIC_VIEW, '[A-Za-z0-9_$]+[.][A-Za-z0-9_$]+[.][A-Za-z0-9_$]+')) THEN
    RETURN 'NOT LOGGED: p_semantic_view must be the fully qualified semantic view name given in your instructions.';
  END IF;
  did := LOWER(LEFT(REPLACE(UUID_STRING(), '-', ''), 12));
  INSERT INTO WBR_DB.ANALYTICS_ENTERPRISE.AA_DECISIONS
    (DECISION_ID, SEMANTIC_VIEW, TEMPLATE_ID, TITLE, DETAIL, OWNER, DUE_DATE, STATUS, EVIDENCE, CREATED_BY)
  SELECT :did, UPPER(:P_SEMANTIC_VIEW), 'cortex_agent', LEFT(TRIM(:P_TITLE), 300), LEFT(COALESCE(:P_DETAIL, ''), 4000),
         LEFT(TRIM(:P_OWNER), 120), :due, 'Open',
         OBJECT_CONSTRUCT('source', 'Cortex Agent tool log_decision', 'evidence', LEFT(COALESCE(:P_EVIDENCE, ''), 4000)),
         CURRENT_USER() || ' via Cortex Agent';
  RETURN 'Logged decision ' || did || ': "' || LEFT(TRIM(P_TITLE), 120) || '" owner ' || TRIM(P_OWNER) ||
         COALESCE(', due ' || TO_VARCHAR(due, 'YYYY-MM-DD'), '') || '. Status Open.';
END;
$$;

-- Smoke test, then remove the test row.
CALL AA_CREATE_DECISION('SMOKE TEST decision tool', 'created by 06_agent_tools.sql', 'Setup script',
     TO_VARCHAR(DATEADD(day, 7, CURRENT_DATE()), 'YYYY-MM-DD'), 'none', 'WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV');
CALL AA_CREATE_DECISION('x', '', '', '', '', '');
DELETE FROM AA_DECISIONS WHERE TITLE = 'SMOKE TEST decision tool';
SHOW PROCEDURES LIKE 'AA_CREATE_DECISION' IN SCHEMA WBR_DB.ANALYTICS_ENTERPRISE;
