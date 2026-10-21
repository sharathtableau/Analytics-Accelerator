-- Checks which Cortex / AI features work in this account for WBR_OWNER.
-- Run:  snow sql -c wbr -f setup\01_feature_check.sql > setup\feature_check_result.txt 2>&1
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
EXECUTE IMMEDIATE $$
DECLARE
  out STRING DEFAULT '';
  v STRING;
BEGIN
  BEGIN SELECT AI_COMPLETE('claude-sonnet-4-5', 'Reply with OK')::STRING INTO :v; out := out || 'AI_COMPLETE claude-sonnet-4-5: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_COMPLETE claude-sonnet-4-5: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT AI_COMPLETE('llama3.3-70b', 'Reply with OK')::STRING INTO :v; out := out || 'AI_COMPLETE llama3.3-70b: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_COMPLETE llama3.3-70b: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT AI_AGG(t, 'Summarize in one line') INTO :v FROM (SELECT 'Sales rose 5% in West' t UNION ALL SELECT 'Profit fell in East'); out := out || 'AI_AGG: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_AGG: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT AI_SUMMARIZE_AGG(t) INTO :v FROM (SELECT 'Sales rose 5% in West' t UNION ALL SELECT 'Profit fell in East'); out := out || 'AI_SUMMARIZE_AGG: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_SUMMARIZE_AGG: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT AI_CLASSIFY('Late delivery again', ['shipping','pricing','quality'])::STRING INTO :v; out := out || 'AI_CLASSIFY: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_CLASSIFY: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT AI_SENTIMENT('Great service')::STRING INTO :v; out := out || 'AI_SENTIMENT: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_SENTIMENT: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT AI_EXTRACT(text => 'Order 42 shipped to Denver', responseFormat => ['city'])::STRING INTO :v; out := out || 'AI_EXTRACT: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'AI_EXTRACT: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SHOW CORTEX SEARCH SERVICES IN ACCOUNT; out := out || 'CORTEX SEARCH (list): OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'CORTEX SEARCH (list): FAIL ' || SQLERRM || '\n'; END;
  BEGIN SHOW SNOWFLAKE.ML.ANOMALY_DETECTION IN ACCOUNT; out := out || 'ML ANOMALY_DETECTION: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'ML ANOMALY_DETECTION: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SHOW SNOWFLAKE.ML.FORECAST IN ACCOUNT; out := out || 'ML FORECAST: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'ML FORECAST: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SHOW SNOWFLAKE.ML.TOP_INSIGHTS IN ACCOUNT; out := out || 'ML TOP_INSIGHTS: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'ML TOP_INSIGHTS: FAIL ' || SQLERRM || '\n'; END;
  BEGIN SELECT COUNT(*)::STRING INTO :v FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY; out := out || 'Cortex usage history (cost panel): OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'Cortex usage history (cost panel): FAIL ' || SQLERRM || '\n'; END;
  BEGIN SHOW COMPUTE POOLS LIKE 'SYSTEM_COMPUTE_POOL_CPU'; out := out || 'Compute pool visible: OK\n';
  EXCEPTION WHEN OTHER THEN out := out || 'Compute pool visible: FAIL ' || SQLERRM || '\n'; END;
  RETURN out;
END;
$$;
