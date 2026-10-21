-- For an ADMIN (ACCOUNTADMIN): spend and safety controls for the Analytics Accelerator's AI.
-- Review before running; run one part at a time.
--
-- What protects what:
--   * In the app (already on): each person gets ai_daily_limit Cortex requests and agent_daily_limit agent
--     questions a day (settings.ini). Viewing dashboards is never limited. Stops runaway use by one person.
--   * PART 1, Snowflake budget: tracks the AI credits the app spends and emails people as the month's spend
--     heads past the limit. It warns; it does not stop the app.
--   * PART 2, Cortex AI Guardrails: account-wide prompt-injection screening for Cortex Agents.
-- Lines marked VERIFY follow the Snowflake docs but have not yet been run in this account.

USE ROLE ACCOUNTADMIN;

------------------------------------------------------------------------------------------------------------------
-- PART 1. Monthly AI budget
------------------------------------------------------------------------------------------------------------------
-- 1a. Let the app's role create and manage the budget in the app schema.
GRANT DATABASE ROLE SNOWFLAKE.BUDGET_CREATOR TO ROLE WBR_OWNER;
GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER TO ROLE WBR_OWNER;
GRANT CREATE SNOWFLAKE.CORE.BUDGET ON SCHEMA WBR_DB.ANALYTICS_ENTERPRISE TO ROLE WBR_OWNER;

-- 1b. AI spend is tracked per user tag. Create a tag and give it to the users whose AI use counts toward the
--     budget. In Streamlit in Snowflake the app's Cortex calls run as the app's service user, so tag that user
--     too. Find it with the query below (needs a week of app use; ACCOUNT_USAGE lags up to 45 minutes).
CREATE TAG IF NOT EXISTS WBR_DB.ANALYTICS_ENTERPRISE.AA_COST_CENTER;
GRANT APPLYBUDGET ON TAG WBR_DB.ANALYTICS_ENTERPRISE.AA_COST_CENTER TO ROLE WBR_OWNER;

SELECT USER_NAME, COUNT(*) AS QUERIES
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
  AND TRY_PARSE_JSON(QUERY_TAG):app::STRING = 'aa-enterprise'
GROUP BY 1 ORDER BY 2 DESC;

-- Replace <USER_NAME> with each name from the query above (the service user and the builders):
-- ALTER USER <USER_NAME> SET TAG WBR_DB.ANALYTICS_ENTERPRISE.AA_COST_CENTER = 'ANALYTICS_ACCELERATOR';

-- 1c. Create the budget as the app's role. Change 100 to the monthly credit limit you want and put in the
--     people to email. Every address must be verified in Snowflake (Snowsight > profile), or the call fails.
USE ROLE WBR_OWNER;
USE SCHEMA WBR_DB.ANALYTICS_ENTERPRISE;
CREATE SNOWFLAKE.CORE.BUDGET IF NOT EXISTS AA_AI_BUDGET();               -- VERIFY: IF NOT EXISTS on budgets
CALL AA_AI_BUDGET!SET_SPENDING_LIMIT(100);                               -- credits per month
CALL AA_AI_BUDGET!SET_USER_TAGS(
  [[(SELECT SYSTEM$REFERENCE('TAG', 'WBR_DB.ANALYTICS_ENTERPRISE.AA_COST_CENTER', 'SESSION', 'APPLYBUDGET')),
    'ANALYTICS_ACCELERATOR']],
  'UNION');
CALL AA_AI_BUDGET!ADD_SHARED_RESOURCE('AI FUNCTION');                    -- AI_COMPLETE, AI_AGG, ...
CALL AA_AI_BUDGET!ADD_SHARED_RESOURCE('CORTEX AGENT');                   -- VERIFY: all agents without a reference
CALL AA_AI_BUDGET!SET_NOTIFICATION_THRESHOLD(80);                        -- VERIFY: warn at 80% projected
-- CALL AA_AI_BUDGET!SET_EMAIL_NOTIFICATIONS('owner@company.com, finops@company.com');

-- Check it:
CALL AA_AI_BUDGET!GET_BUDGET_SCOPE();
CALL AA_AI_BUDGET!GET_SHARED_RESOURCES();
CALL AA_AI_BUDGET!GET_SPENDING_LIMIT();

------------------------------------------------------------------------------------------------------------------
-- PART 2. Cortex AI Guardrails (prompt-injection screening for Cortex Agents, Cortex Code and CoWork)
------------------------------------------------------------------------------------------------------------------
-- Account-wide. Needs ACCOUNTADMIN, Enterprise edition or higher, and cross-region inference enabled.
-- Screening is billed per request; see CORTEX_AI_GUARDRAILS_USAGE_HISTORY. Check the current value first:
USE ROLE ACCOUNTADMIN;
SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT;
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;

-- If AI_SETTINGS already holds other settings, merge this block into them instead of replacing them.
-- ALTER ACCOUNT SET AI_SETTINGS = $$
-- guardrails:
--   advanced_prompt_injection:
--     - enabled: true
-- $$;
