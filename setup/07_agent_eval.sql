-- D1 in ENTERPRISE_TRACKER.md: Snowflake-native Cortex Agent evaluation (AI Observability).
-- Dataset + config live in the agent's schema (Snowflake requires the agent and dataset to be co-located).
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE DATABASE WBR_DB;
USE SCHEMA ANALYTICS_ENTERPRISE;

-- 1) Evaluation questions with ground truth (expected answer + expected tool calls).
CREATE OR REPLACE TABLE AA_RETAIL_AGENT_EVAL_DATA (INPUT_QUERY VARCHAR, GROUND_TRUTH VARIANT);
INSERT INTO AA_RETAIL_AGENT_EVAL_DATA
SELECT column1, PARSE_JSON(column2) FROM VALUES
('Why is stockout rate for Boots high in the West?',
 '{"ground_truth_output": "Boots stockout rate in the West (Reno DC) rose well above normal in Aug-Sep 2026. Cause (HLO-INV-008): supplier Pacific Stride Footwear cut allocation to Reno DC to about 20-35% of normal from the cycle starting 25 Jul 2026; a 15,000-pair transfer from Columbus and Dallas DCs was approved 2 Sep and first arrived 21 Sep.",
   "ground_truth_invocations": [{"tool_name": "analyst", "tool_input": "Boots stockout rate by month for West region"}, {"tool_name": "documents", "tool_input": "West footwear stockouts Reno DC cause"}]}'),
('When is West footwear availability expected to recover?',
 '{"ground_truth_output": "Normal allocation to Reno DC is expected to resume from the replenishment cycle starting 20 October 2026 (HLO-INV-008; WBR 28 Sep 2026).",
   "ground_truth_invocations": [{"tool_name": "documents", "tool_input": "West footwear recovery date"}]}'),
('Why did free shipping % drop this year?',
 '{"ground_truth_output": "Free shipping % is about 9 points below last year because the free-shipping threshold was raised from 99 USD to 119 USD on 1 March 2026 (HLO-POL-014). The drop is intended; average order value rose.",
   "ground_truth_invocations": [{"tool_name": "analyst", "tool_input": "free shipping order pct by month this year vs last year"}, {"tool_name": "documents", "tool_input": "free shipping threshold change"}]}'),
('Why are Southeast deliveries late?',
 '{"ground_truth_output": "USPS on-time delivery in the Southeast fell from August 2026 after USPS consolidated its Atlanta sort facility on 27 July 2026, adding about 1.5 days of transit (HLO-OPS-022, incident TR-2026-031). Light parcels are re-routed to UPS from 5 October 2026.",
   "ground_truth_invocations": [{"tool_name": "analyst", "tool_input": "on-time rate by carrier for Southeast by month"}, {"tool_name": "documents", "tool_input": "Southeast USPS delivery delays"}]}'),
('Which region is furthest behind plan and why?',
 '{"ground_truth_output": "Southwest, with plan attainment around 87-88% year to date. Its +10% target assumed three new stores but only Austin opened, and online demand in TX and AZ has been softer (HLO-FIN-003; WBR 14 Sep 2026).",
   "ground_truth_invocations": [{"tool_name": "analyst", "tool_input": "plan attainment by region year to date"}, {"tool_name": "documents", "tool_input": "Southwest plan miss reason"}]}'),
('What is the free shipping threshold?',
 '{"ground_truth_output": "119 USD since 1 March 2026 (99 USD before). Gold and Platinum members and free-shipping promotion days are always free; Expedited and Next-day are never free (HLO-POL-014).",
   "ground_truth_invocations": [{"tool_name": "documents", "tool_input": "free shipping threshold policy"}]}'),
('What does in-stock rate mean?',
 '{"ground_truth_output": "In-stock rate is the share of SKU x DC x day records ending with stock available, i.e. 1 minus stockout rate. Target is 95% per DC (HLO-INV-008).",
   "ground_truth_invocations": [{"tool_name": "documents", "tool_input": "in-stock rate definition"}]}'),
('What were net sales by region last month?',
 '{"ground_truth_output": "A table of net sales for each of the five US regions (Northeast, Southeast, Midwest, Southwest, West) for the latest complete month, computed from the semantic view.",
   "ground_truth_invocations": [{"tool_name": "analyst", "tool_input": "net sales by region for last month"}]}');

-- 2) Register the dataset with Snowflake AI Observability.
--    Safe to re-run: if the dataset already exists, the existing registration is kept.
EXECUTE IMMEDIATE $$
BEGIN
  CALL SYSTEM$CREATE_EVALUATION_DATASET(
    'Cortex Agent',
    'WBR_DB.ANALYTICS_ENTERPRISE.AA_RETAIL_AGENT_EVAL_DATA',
    'WBR_DB.ANALYTICS_ENTERPRISE.AA_RETAIL_AGENT_EVALSET',
    OBJECT_CONSTRUCT('query_text', 'INPUT_QUERY', 'expected_tools', 'GROUND_TRUTH'));
  RETURN 'Evaluation dataset AA_RETAIL_AGENT_EVALSET registered';
EXCEPTION WHEN OTHER THEN
  RETURN 'Dataset not (re)registered: ' || SQLERRM;
END;
$$;

-- 3) Stage for the YAML config (uploaded by the PUT the .cmd adds).
CREATE FILE FORMAT IF NOT EXISTS AA_YAML_FORMAT TYPE = 'CSV' FIELD_DELIMITER = NONE RECORD_DELIMITER = '\n' SKIP_HEADER = 0;
CREATE STAGE IF NOT EXISTS AA_EVAL_CONFIG FILE_FORMAT = AA_YAML_FORMAT
  COMMENT = 'Cortex Agent evaluation configs for Analytics Accelerator';

-- 4) Run registry the app reads (Governance -> Agent evaluations).
CREATE TABLE IF NOT EXISTS AA_EVAL_RUNS (RUN_NAME VARCHAR, AGENT VARCHAR, CONFIG VARCHAR, STARTED_BY VARCHAR,
  STARTED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP());
