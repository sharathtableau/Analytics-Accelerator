-- AI Gateway test: read-only checks. Run in a Snowsight worksheet with role WBR_OWNER (or: snow sql -c wbr -f ...).
-- Part A before the probe, Part B a few minutes after it.

-- A1. Does the account have the gateway, and what is its endpoint?
SHOW AI GATEWAYS;
DESCRIBE AI GATEWAY SNOWFLAKE;

-- A2. Who may use it? (USAGE is granted to PUBLIC by default; if not listed, an admin runs:
--     GRANT USAGE ON AI GATEWAY SNOWFLAKE TO ROLE WBR_OWNER;)
SHOW GRANTS ON AI GATEWAY SNOWFLAKE;

-- B1. Traces of the probe's calls (needs MONITOR on the gateway; an admin can run
--     GRANT MONITOR ON AI GATEWAY SNOWFLAKE TO ROLE WBR_OWNER;)
SELECT TIMESTAMP,
       RESOURCE_ATTRIBUTES:"user"::STRING                 AS GATEWAY_USER,
       RECORD_ATTRIBUTES:"gen_ai.request.model"::STRING   AS MODEL,
       RECORD_ATTRIBUTES:"gen_ai.usage.input_tokens"      AS INPUT_TOKENS,
       RECORD_ATTRIBUTES:"gen_ai.usage.output_tokens"     AS OUTPUT_TOKENS,
       RECORD_ATTRIBUTES:"http.status_code"               AS HTTP_STATUS
FROM TABLE(AGENT_TRACE_TABLE('SNOWFLAKE'))
WHERE TIMESTAMP >= DATEADD('hour', -2, CURRENT_TIMESTAMP())
ORDER BY TIMESTAMP DESC LIMIT 20;

-- B2. Gateway credits (ACCOUNT_USAGE lags; check the next day). Needs ACCOUNT_USAGE access.
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.AI_GATEWAY_USAGE_HISTORY
WHERE START_TIME >= DATEADD('day', -2, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC LIMIT 20;
