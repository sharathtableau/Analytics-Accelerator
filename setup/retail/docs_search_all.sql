-- Harborline documents -> Cortex Search (A1/C5 in ENTERPRISE_TRACKER.md). Part 1: stage.
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.RETAIL_DEMO;
-- AI_PARSE_DOCUMENT needs server-side encryption and a directory table on the stage.
CREATE STAGE IF NOT EXISTS RETAIL_DOCS_STAGE
  DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Harborline (fictional) policy PDFs, WBR notes and plan memo for Cortex Search';
PUT 'file://C:/Users/SharathKumarKammari/Downloads/snowflake-react-app-runtime/Analytics_Accelerator_Enterprise_Claude/setup/retail/docs/pdf/*.pdf' @WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
PUT 'file://C:/Users/SharathKumarKammari/Downloads/snowflake-react-app-runtime/Analytics_Accelerator_Enterprise_Claude/setup/retail/docs/*.md' @WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
-- Part 2 (runs after the PUT of docs\pdf\*.pdf and docs\*.md): parse -> chunk -> glossary -> Cortex Search.
ALTER STAGE RETAIL_DOCS_STAGE REFRESH;
SELECT RELATIVE_PATH, SIZE FROM DIRECTORY(@RETAIL_DOCS_STAGE) ORDER BY 1;

-- 1) AI_PARSE_DOCUMENT reads each PDF (layout mode keeps headings/lists as markdown).
--    Fallback: if AI_PARSE_DOCUMENT is not enabled, read the markdown twins of the same documents.
CREATE OR REPLACE TABLE RETAIL_DOCS_PARSED (FILE_NAME STRING, CONTENT STRING, PARSED_BY STRING);
EXECUTE IMMEDIATE $$
BEGIN
  INSERT INTO RETAIL_DOCS_PARSED
  SELECT RELATIVE_PATH,
         AI_PARSE_DOCUMENT(TO_FILE('@WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE', RELATIVE_PATH), {'mode': 'LAYOUT'}):content::STRING,
         'AI_PARSE_DOCUMENT'
  FROM DIRECTORY(@WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE) WHERE RELATIVE_PATH ILIKE '%.pdf';
  RETURN 'Parsed PDFs with AI_PARSE_DOCUMENT';
EXCEPTION WHEN OTHER THEN
  CREATE OR REPLACE FILE FORMAT WBR_DB.RETAIL_DEMO.FF_LINES TYPE = CSV FIELD_DELIMITER = NONE RECORD_DELIMITER = '\n'
    SKIP_BLANK_LINES = FALSE FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE_UNENCLOSED_FIELD = NONE;
  INSERT INTO RETAIL_DOCS_PARSED
  SELECT REPLACE(METADATA$FILENAME, '.md', '.pdf'),
         LISTAGG(COALESCE($1, ''), '\n') WITHIN GROUP (ORDER BY METADATA$FILE_ROW_NUMBER), 'markdown fallback'
  FROM @WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE (FILE_FORMAT => 'WBR_DB.RETAIL_DEMO.FF_LINES', PATTERN => '.*[.]md')
  GROUP BY METADATA$FILENAME;
  RETURN 'AI_PARSE_DOCUMENT unavailable (' || SQLERRM || ') - loaded markdown twins instead';
END;
$$;
SELECT FILE_NAME, PARSED_BY, LENGTH(CONTENT) AS CHARS FROM RETAIL_DOCS_PARSED ORDER BY 1;

-- 2) Chunk with SPLIT_TEXT_RECURSIVE_CHARACTER (markdown-aware). Fallback: one chunk per section heading.
CREATE OR REPLACE TABLE RETAIL_DOCS (
  DOC_ID STRING, TITLE STRING, DOC_TYPE STRING, SOURCE STRING, CHUNK_NO INT, CHUNK STRING);
EXECUTE IMMEDIATE $$
BEGIN
  INSERT INTO RETAIL_DOCS
  SELECT SPLIT_PART(p.FILE_NAME, '_', 1),
         REPLACE(REPLACE(SUBSTR(p.FILE_NAME, POSITION('_' IN p.FILE_NAME) + 1), '.pdf', ''), '_', ' '),
         CASE WHEN p.FILE_NAME ILIKE 'HLO-POL%' THEN 'policy' WHEN p.FILE_NAME ILIKE 'HLO-OPS%' THEN 'operations standard'
              WHEN p.FILE_NAME ILIKE 'HLO-INV%' THEN 'supply chain standard' WHEN p.FILE_NAME ILIKE 'HLO-FIN%' THEN 'finance memo'
              ELSE 'WBR notes' END,
         p.FILE_NAME || ' (' || p.PARSED_BY || ')', c.INDEX, c.VALUE::STRING
  FROM RETAIL_DOCS_PARSED p,
       LATERAL FLATTEN(SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(p.CONTENT, 'markdown', 1200, 150)) c;
  RETURN 'Chunked with SPLIT_TEXT_RECURSIVE_CHARACTER';
EXCEPTION WHEN OTHER THEN
  INSERT INTO RETAIL_DOCS
  SELECT SPLIT_PART(p.FILE_NAME, '_', 1),
         REPLACE(REPLACE(SUBSTR(p.FILE_NAME, POSITION('_' IN p.FILE_NAME) + 1), '.pdf', ''), '_', ' '),
         'document', p.FILE_NAME || ' (' || p.PARSED_BY || ')', s.INDEX, '## ' || s.VALUE::STRING
  FROM RETAIL_DOCS_PARSED p, LATERAL FLATTEN(SPLIT(p.CONTENT, '\n## ')) s;
  RETURN 'SPLIT_TEXT_RECURSIVE_CHARACTER unavailable - chunked by section heading';
END;
$$;

-- 3) Metric glossary straight from the semantic view, so definitions in search = definitions in the dashboard.
DESCRIBE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV;
INSERT INTO RETAIL_DOCS
SELECT 'GLOSSARY', 'Metric definition: ' || INITCAP(REPLACE("object_name", '_', ' ')), 'metric definition',
       'RETAIL_ANALYTICS_SV', 0,
       'Metric ' || INITCAP(REPLACE("object_name", '_', ' ')) || ' (' || "object_name" || '): ' || "property_value"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "object_kind" IN ('METRIC', 'DERIVED_METRIC') AND "property" = 'COMMENT'
  AND "object_name" NOT ILIKE 'HELPER%';
SELECT DOC_TYPE, COUNT(*) AS CHUNKS FROM RETAIL_DOCS GROUP BY 1 ORDER BY 1;

-- 4) Cortex Search service (hybrid vector + keyword) over the chunks.
CREATE OR REPLACE CORTEX SEARCH SERVICE RETAIL_DOCS_SEARCH
  ON CHUNK
  ATTRIBUTES DOC_TYPE, TITLE, DOC_ID
  WAREHOUSE = POWERHOUSE
  TARGET_LAG = '1 day'
  COMMENT = 'Harborline policies, standards, plan memo, WBR notes and metric glossary (fictional)'
  AS SELECT CHUNK, TITLE, DOC_TYPE, DOC_ID, SOURCE, CHUNK_NO FROM RETAIL_DOCS;

-- 5) Smoke tests: the answers the demo relies on.
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.RETAIL_DEMO.RETAIL_DOCS_SEARCH',
  '{"query": "why did free shipping percent drop this year", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS FREE_SHIP;
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.RETAIL_DEMO.RETAIL_DOCS_SEARCH',
  '{"query": "West footwear stockouts Reno cause", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS WEST_FOOTWEAR;
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.RETAIL_DEMO.RETAIL_DOCS_SEARCH',
  '{"query": "Southeast USPS late deliveries", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS SOUTHEAST_USPS;
