-- Cost snapshot for the partner deck: tokens and credits per app feature, last 30 days.
-- Run with: setup\run_cost_snapshot.cmd   (output goes to setup\cost_snapshot_log.txt)
-- Needs a role that can read SNOWFLAKE.ACCOUNT_USAGE. ACCOUNT_USAGE lags (AI functions ~5 min, agents up to 1 h,
-- warehouse attribution up to 8 h). Each query runs on its own; if one view is missing, the others still run.

-- 1) Cortex AI functions (AI_COMPLETE, AI_AGG...) by app feature: calls, tokens, credits
WITH h AS (
  SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
  WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
    AND TRY_PARSE_JSON(QUERY_TAG):app::STRING = 'aa-enterprise'),
t AS (
  SELECT h.QUERY_ID, h.START_TIME, h.FUNCTION_NAME, h.MODEL_NAME,
         SUM(IFF(m.value:key:metric::STRING IN ('input', 'total'), m.value:value::NUMBER, 0)) AS IN_TOK,
         SUM(IFF(m.value:key:metric::STRING = 'output', m.value:value::NUMBER, 0)) AS OUT_TOK
  FROM h, LATERAL FLATTEN(INPUT => h.METRICS, OUTER => TRUE) m
  GROUP BY 1, 2, 3, 4)
SELECT COALESCE(TRY_PARSE_JSON(h.QUERY_TAG):feature::STRING, 'other') AS FEATURE, h.FUNCTION_NAME, h.MODEL_NAME,
       COUNT(DISTINCT h.QUERY_ID) AS CALLS,
       ROUND(SUM(t.IN_TOK) / NULLIF(COUNT(DISTINCT h.QUERY_ID), 0)) AS AVG_INPUT_TOKENS,
       ROUND(SUM(t.OUT_TOK) / NULLIF(COUNT(DISTINCT h.QUERY_ID), 0)) AS AVG_OUTPUT_TOKENS,
       ROUND(SUM(h.CREDITS), 4) AS AI_CREDITS,
       ROUND(SUM(h.CREDITS) / NULLIF(COUNT(DISTINCT h.QUERY_ID), 0), 5) AS AI_CREDITS_PER_CALL
FROM h JOIN t ON t.QUERY_ID = h.QUERY_ID AND t.START_TIME = h.START_TIME
             AND t.FUNCTION_NAME = h.FUNCTION_NAME AND COALESCE(t.MODEL_NAME, '') = COALESCE(h.MODEL_NAME, '')
GROUP BY 1, 2, 3 ORDER BY AI_CREDITS DESC;

-- 2) Cortex Agent questions (the app's agents are named AA_...): requests, tokens, credits per question
SELECT AGENT_NAME, COUNT(*) AS REQUESTS,
       ROUND(AVG(TOKENS)) AS AVG_TOKENS_PER_REQUEST,
       ROUND(SUM(TOKEN_CREDITS), 4) AS AI_CREDITS,
       ROUND(AVG(TOKEN_CREDITS), 5) AS AI_CREDITS_PER_REQUEST,
       ROUND(SUM(METADATA:sql_query_credits::FLOAT), 4) AS WAREHOUSE_CREDITS_FOR_AGENT_SQL
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP()) AND STARTSWITH(UPPER(AGENT_NAME), 'AA_')
GROUP BY 1 ORDER BY AI_CREDITS DESC;

-- 3) Agent tokens split by service and model (orchestration vs Cortex Analyst)
SELECT g.value:service_type::STRING AS SERVICE, g.value:model::STRING AS MODEL,
       COUNT(DISTINCT a.REQUEST_ID) AS REQUESTS,
       ROUND(AVG(g.value:input::NUMBER)) AS AVG_INPUT, ROUND(AVG(g.value:cache_read_input::NUMBER)) AS AVG_CACHE_READ,
       ROUND(AVG(g.value:output::NUMBER)) AS AVG_OUTPUT
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY a, LATERAL FLATTEN(INPUT => a.TOKENS_GRANULAR) g
WHERE a.START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP()) AND STARTSWITH(UPPER(a.AGENT_NAME), 'AA_')
GROUP BY 1, 2 ORDER BY 1, 2;

-- 4) Warehouse compute by app feature (SEMANTIC_VIEW queries, ML, etc.)
SELECT COALESCE(TRY_PARSE_JSON(QUERY_TAG):feature::STRING, 'other') AS FEATURE, COUNT(*) AS QUERIES,
       ROUND(SUM(CREDITS_ATTRIBUTED_COMPUTE), 4) AS WAREHOUSE_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY
WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
  AND TRY_PARSE_JSON(QUERY_TAG):app::STRING = 'aa-enterprise'
GROUP BY 1 ORDER BY WAREHOUSE_CREDITS DESC;

-- 5) Cortex Search serving cost for the retail documents
SELECT SERVICE_NAME, CONSUMPTION_TYPE, ROUND(SUM(CREDITS), 4) AS CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
WHERE USAGE_DATE >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY 1, 2 ORDER BY CREDITS DESC;

-- 6) What the app recorded itself (no lag): AI runs per feature and average time
SELECT FEATURE, COUNT(*) AS RUNS, ROUND(AVG(LATENCY_S), 1) AS AVG_SECONDS, ROUND(AVG(LENGTH(OUTPUT))) AS AVG_OUTPUT_CHARS
FROM WBR_DB.ANALYTICS_ENTERPRISE.AA_AI_RUNS
WHERE CREATED_AT >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY RUNS DESC;

-- 7) Agent tokens per question from AI Observability (no ACCOUNT_USAGE needed: owner of the agent + CORTEX_USER)
SELECT f.key AS TOKEN_FIELD, COUNT(DISTINCT e.TRACE:trace_id::STRING) AS TRACES, COUNT(*) AS SPANS,
       SUM(TRY_TO_NUMBER(f.value::STRING)) AS TOTAL_TOKENS,
       ROUND(SUM(TRY_TO_NUMBER(f.value::STRING)) / NULLIF(COUNT(DISTINCT e.TRACE:trace_id::STRING), 0)) AS TOKENS_PER_QUESTION
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS('WBR_DB', 'ANALYTICS_ENTERPRISE', 'AA_RETAIL_ANALYTICS_SV_AGENT', 'CORTEX AGENT')) e,
     LATERAL FLATTEN(INPUT => e.RECORD_ATTRIBUTES) f
WHERE f.key ILIKE '%token%'
GROUP BY 1 ORDER BY 1;

-- 8) Output tokens per AI feature, counted with AI_COUNT_TOKENS on what the app logged (compute only, not billed per token)
SELECT FEATURE, COUNT(*) AS RUNS,
       ROUND(AVG(AI_COUNT_TOKENS('ai_complete', 'claude-sonnet-4-5', OUTPUT))) AS AVG_OUTPUT_TOKENS,
       SUM(IFF(LENGTH(OUTPUT) >= 3990, 1, 0)) AS RUNS_WITH_LOG_CUT_AT_4000_CHARS
FROM WBR_DB.ANALYTICS_ENTERPRISE.AA_AI_RUNS
WHERE CREATED_AT >= DATEADD('day', -30, CURRENT_TIMESTAMP()) AND OUTPUT IS NOT NULL AND LENGTH(OUTPUT) > 0
GROUP BY 1 ORDER BY RUNS DESC;

-- 9) MEASURED tokens per feature, as reported by Snowflake to the app (AI_COMPLETE show_details and the agent
--    response usage), priced at list rates: AI_COMPLETE claude-sonnet-4-5 1.80 in / 9.00 out AI credits per 1M tokens,
--    Cortex Agents claude-sonnet-4-5 1.95 in / 0.20 cache read / 2.44 cache write / 9.76 out; AI credit = 2.00 USD (global routing).
--    Only runs made after the token-logging build was deployed have tokens.
WITH r AS (
  SELECT FEATURE, CREATED_AT,
         TRY_TO_NUMBER(REGEXP_SUBSTR(PROVENANCE, 'tokens ([0-9]+) in', 1, 1, 'e', 1)) AS IN_TOK,
         TRY_TO_NUMBER(REGEXP_SUBSTR(PROVENANCE, 'tokens [0-9]+ in / ([0-9]+) out', 1, 1, 'e', 1)) AS OUT_TOK,
         COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(PROVENANCE, 'out / ([0-9]+) cache_read', 1, 1, 'e', 1)), 0) AS CACHE_TOK,
         COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(PROVENANCE, '/ ([0-9]+) cache_write', 1, 1, 'e', 1)), 0) AS CW_TOK
  FROM WBR_DB.ANALYTICS_ENTERPRISE.AA_AI_RUNS
  WHERE CREATED_AT >= DATEADD('day', -30, CURRENT_TIMESTAMP()) AND REGEXP_LIKE(PROVENANCE, '.*tokens [0-9]+ in / [0-9]+ out.*')),
p AS (
  SELECT FEATURE, IN_TOK, OUT_TOK, CACHE_TOK, CW_TOK,
         IFF(FEATURE IN ('agent_question', 'tile_question'),
             (GREATEST(IN_TOK - CACHE_TOK - CW_TOK, 0) * 1.95 + CACHE_TOK * 0.20 + CW_TOK * 2.44 + OUT_TOK * 9.76) / 1e6,
             (IN_TOK * 1.80 + OUT_TOK * 9.00) / 1e6) AS CREDITS
  FROM r)
SELECT FEATURE, COUNT(*) AS RUNS, ROUND(AVG(IN_TOK)) AS AVG_IN_TOKENS, ROUND(AVG(CACHE_TOK)) AS AVG_CACHE_READ, ROUND(AVG(CW_TOK)) AS AVG_CACHE_WRITE,
       ROUND(AVG(OUT_TOK)) AS AVG_OUT_TOKENS, ROUND(AVG(CREDITS), 5) AS AI_CREDITS_PER_RUN,
       ROUND(AVG(CREDITS) * 2.00, 4) AS USD_PER_RUN_LIST
FROM p GROUP BY 1 ORDER BY USD_PER_RUN_LIST DESC;
