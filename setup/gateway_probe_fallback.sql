-- AI Gateway test, FALLBACK ONLY: use this only if probe test G5 fails and G4 (plain Cortex REST) also fails.
-- It lets the probe reach the gateway through the account's public address with a programmatic access token.
-- Needs an admin for the integration (CREATE INTEGRATION). Review before running.
--
-- The token: YOU create it in Snowsight (your profile > Programmatic access tokens), restricted to role WBR_OWNER,
-- with the shortest expiry that covers the test (e.g. 1 day). Paste it ONLY into step 3 below, in a Snowsight
-- worksheet. Never save it in a file, a chat or this script. Delete the secret and revoke the token after the test.

-- 1. The public host. Confirm it from the endpoint column of DESCRIBE AI GATEWAY SNOWFLAKE (gateway_probe_checks.sql).
USE ROLE WBR_OWNER;
CREATE OR REPLACE NETWORK RULE WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_RULE
  MODE = EGRESS TYPE = HOST_PORT
  VALUE_LIST = ('wb19670-c2gpartners.snowflakecomputing.com');          -- VERIFY against the gateway endpoint

-- 2. The secret (placeholder value first).
CREATE OR REPLACE SECRET WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PAT TYPE = GENERIC_STRING SECRET_STRING = 'placeholder';

-- 3. Put the real token in (run this line on its own, in Snowsight, then clear the worksheet):
-- ALTER SECRET WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PAT SET SECRET_STRING = '<paste token here>';

-- 4. ADMIN: the integration, and its use by WBR_OWNER.
-- USE ROLE ACCOUNTADMIN;
-- CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION AA_GATEWAY_EAI
--   ALLOWED_NETWORK_RULES = (WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_RULE)
--   ALLOWED_AUTHENTICATION_SECRETS = (WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PAT)
--   ENABLED = TRUE;
-- GRANT USAGE ON INTEGRATION AA_GATEWAY_EAI TO ROLE WBR_OWNER;

-- 5. Attach both to the probe (after deploy_gateway_probe.cmd), as WBR_OWNER:
-- USE ROLE WBR_OWNER;
-- ALTER STREAMLIT WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PROBE SET
--   EXTERNAL_ACCESS_INTEGRATIONS = (AA_GATEWAY_EAI)
--   SECRETS = ('aa_gateway_pat' = WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PAT);
-- Then reopen the probe, type the host into the G7 box and run the tests again.

-- 6. Clean-up after the test:
-- DROP STREAMLIT IF EXISTS WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PROBE;
-- DROP SECRET IF EXISTS WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PAT;
-- DROP NETWORK RULE IF EXISTS WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_RULE;
-- (admin) DROP INTEGRATION IF EXISTS AA_GATEWAY_EAI;   and revoke the token in Snowsight.
