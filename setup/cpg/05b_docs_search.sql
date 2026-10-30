-- Part 2 (after the PUT): markdown -> chunks (+ metric glossary from the semantic view) -> Cortex Search.
-- The INFERA pack's DEMO_GUIDE (planted signals) is deliberately NOT loaded: it would give the answers away.
USE SCHEMA WBR_DB.CPG_DEMO;
ALTER STAGE CPG_DOCS_STAGE REFRESH;
SELECT RELATIVE_PATH, SIZE FROM DIRECTORY(@CPG_DOCS_STAGE) ORDER BY 1;

CREATE OR REPLACE FILE FORMAT FF_LINES TYPE = CSV FIELD_DELIMITER = NONE RECORD_DELIMITER = '\n'
  SKIP_BLANK_LINES = FALSE FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE_UNENCLOSED_FIELD = NONE;
CREATE OR REPLACE TABLE CPG_DOCS_PARSED AS
SELECT METADATA$FILENAME AS FILE_NAME,
       LISTAGG(COALESCE($1, ''), '\n') WITHIN GROUP (ORDER BY METADATA$FILE_ROW_NUMBER) AS CONTENT
FROM @CPG_DOCS_STAGE (FILE_FORMAT => 'WBR_DB.CPG_DEMO.FF_LINES', PATTERN => '.*[.]md')
GROUP BY METADATA$FILENAME;
SELECT FILE_NAME, LENGTH(CONTENT) AS CHARS FROM CPG_DOCS_PARSED ORDER BY 1;

-- Chunk with SPLIT_TEXT_RECURSIVE_CHARACTER (markdown-aware). Fallback: one chunk per section heading.
CREATE OR REPLACE TABLE CPG_DOCS (
  DOC_ID STRING, TITLE STRING, DOC_TYPE STRING, SOURCE STRING, CHUNK_NO INT, CHUNK STRING);
EXECUTE IMMEDIATE $$
BEGIN
  INSERT INTO WBR_DB.CPG_DEMO.CPG_DOCS
  SELECT 'APX-ONTOLOGY', 'Apex Athletic business ontology', 'business definitions', p.FILE_NAME, c.INDEX, c.VALUE::STRING
  FROM WBR_DB.CPG_DEMO.CPG_DOCS_PARSED p,
       LATERAL FLATTEN(SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(p.CONTENT, 'markdown', 1200, 150)) c;
  RETURN 'Chunked with SPLIT_TEXT_RECURSIVE_CHARACTER';
EXCEPTION WHEN OTHER THEN
  INSERT INTO WBR_DB.CPG_DEMO.CPG_DOCS
  SELECT 'APX-ONTOLOGY', 'Apex Athletic business ontology', 'business definitions', p.FILE_NAME, s.INDEX,
         '## ' || s.VALUE::STRING
  FROM WBR_DB.CPG_DEMO.CPG_DOCS_PARSED p, LATERAL FLATTEN(SPLIT(p.CONTENT, '\n## ')) s;
  RETURN 'SPLIT_TEXT_RECURSIVE_CHARACTER unavailable - chunked by section heading';
END;
$$;

-- Metric glossary straight from the semantic view, so definitions in search = definitions in the dashboard.
DESCRIBE SEMANTIC VIEW WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV;
INSERT INTO CPG_DOCS
SELECT 'GLOSSARY', 'Metric definition: ' || INITCAP(REPLACE("object_name", '_', ' ')), 'metric definition',
       'CPG_ANALYTICS_SV', 0,
       'Metric ' || INITCAP(REPLACE("object_name", '_', ' ')) || ' (' || "object_name" || '): ' || "property_value"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "object_kind" IN ('METRIC', 'DERIVED_METRIC') AND "property" = 'COMMENT'
  AND "object_name" NOT ILIKE 'HELPER%';
SELECT DOC_TYPE, COUNT(*) AS CHUNKS FROM CPG_DOCS GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE CORTEX SEARCH SERVICE CPG_DOCS_SEARCH
  ON CHUNK
  ATTRIBUTES DOC_TYPE, TITLE, DOC_ID
  WAREHOUSE = POWERHOUSE
  TARGET_LAG = '1 day'
  COMMENT = 'Apex Athletic (fictional): personas, metric dictionary, alert library, business rules and metric glossary'
  AS SELECT CHUNK, TITLE, DOC_TYPE, DOC_ID, SOURCE, CHUNK_NO FROM CPG_DOCS;

-- Smoke tests: the definitions the demo relies on.
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.CPG_DEMO.CPG_DOCS_SEARCH',
  '{"query": "why exclude DTC from channel inventory", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS DTC_RULE;
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.CPG_DEMO.CPG_DOCS_SEARCH',
  '{"query": "weeks of supply healthy band and inventory bloat alert", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS WOS_RULE;
