-- =====================================================================================================
-- Analytics Accelerator: data alerts by email — ONE-TIME SETUP
-- On the WB19670-C2GPARTNERS account WBR_OWNER can create the email integration itself (done 21 Oct 2026:
-- AA_EMAIL_INT). Only step 3 (EXECUTE TASK) may need an account admin. Review before running.
-- =====================================================================================================
USE ROLE WBR_OWNER;

-- 1. The email channel (no recipient list: any VERIFIED email of a user in this account can be emailed).
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS AA_EMAIL_INT
  TYPE = EMAIL
  ENABLED = TRUE
  COMMENT = 'Analytics Accelerator data alerts';
-- Optional, to restrict who can be emailed (every address must already be verified, or this fails):
-- ALTER NOTIFICATION INTEGRATION AA_EMAIL_INT SET ALLOWED_RECIPIENTS = ('sharath.kammari@blend360.com');

-- 2. Each recipient verifies their email ONCE in Snowsight: your name (bottom left) → Settings → Profile →
--    Email → Verify, then click the link in the email from Snowflake. Check:
-- DESC USER "SHARATH.KAMMARI@BLEND360.COM";   -- IS_EMAIL_VERIFIED must be true
-- CALL SYSTEM$SEND_EMAIL('AA_EMAIL_INT', 'sharath.kammari@blend360.com', 'Test', 'Email works.');

-- 3. Hourly checks: the app's "Turn on hourly schedule" button creates task AA_ALERTS_TASK. Resuming it
--    needs EXECUTE TASK on the account. Check:  SHOW GRANTS TO ROLE WBR_OWNER;  (privilege EXECUTE TASK,
--    granted_on ACCOUNT). If missing, an ACCOUNTADMIN runs:
-- USE ROLE ACCOUNTADMIN;
-- GRANT EXECUTE TASK ON ACCOUNT TO ROLE WBR_OWNER;

-- Undo (if ever needed):
-- ALTER TASK WBR_DB.ANALYTICS_ENTERPRISE.AA_ALERTS_TASK SUSPEND;
-- DROP NOTIFICATION INTEGRATION IF EXISTS AA_EMAIL_INT;
