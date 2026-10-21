# Scenario 19: Automatic QA validation (drop 1)

**Goal:** confirm on a real Snowflake account that every tile is checked automatically against the base tables, and that a real difference would be flagged.

**Before you start:** deploy the latest build with `deploy_enterprise.cmd` and `deploy_portal.cmd`. The app role needs SELECT on the base tables behind the semantic view. Without it, QA-01 reports "Not checked" and gives the reason; it never shows a false pass.

## Steps

1. **Build an Executive dashboard** on Harborline Retail. When the tiles appear:
   - Each tile shows a grey **Checking** pill.
   - The strip under the headline says **Validating numbers against the base tables…**.
   - After a few seconds the pills change to **Verified**, **Review**, **Mismatch** or **Not checked**.
   - Expected: mostly Verified.
2. **Click View report** on the strip. Check that:
   - The page checks QA-04 (joins), QA-05 (periods), QA-06 (freshness) and QA-08 (summary figures) are listed.
   - Each tile lists QA-01 to QA-03, plus QA-06 and QA-07 where they apply.
3. **Open a tile's QA-01.** Check that:
   - The sample rows show Dashboard and Independent values side by side.
   - The independent SQL reads the base tables (`FROM DB.SCHEMA.TABLE T0 ... LEFT JOIN ...`), not `SEMANTIC_VIEW(...)`.
   - Running that SQL in a worksheet gives the same numbers.
4. **Multi-table view:** build on a view that has relationships. Check that:
   - QA-04 lists each join with its unique-key and orphan counts.
   - The independent SQL contains the LEFT JOINs.
5. **Filters:** set Region to one value. Check that:
   - The tiles go back to Checking, then show their result again.
   - QA-07 says the filter was applied, and the independent SQL contains it.
6. **Edit a tile** (for example, change its metric with ✦). Only that tile re-checks; the others keep their result.
7. **Refresh (↻):** if the numbers change, validation re-runs at most once every 10 minutes (cost guardrail). Otherwise the strip keeps its "Checked hh:mm" time.
8. **Publish, then open the dashboard in the portal.** Check that:
   - Viewers see one line: **Numbers verified against the source tables · Checked when published … · x of y page(s)**.
   - Viewers see no tile pills.
9. **Evidence trail:** run
   ```sql
   SELECT RUN_AT, PAGE_ID, STATUS, TILES, VERIFIED, REVIEW, MISMATCH, NOT_CHECKED, QUERIES
   FROM WBR_DB.ANALYTICS_ENTERPRISE.AA_VALIDATION_RUNS ORDER BY RUN_AT DESC LIMIT 20;
   ```
   Expect one row per page validation. `REPORT` holds every check, both SQLs and expected vs actual.
10. **Optional negative test.** In a dev copy only, change one metric expression in the semantic view (for example SUM to AVG) without changing the base table. Rebuild: the affected tiles show **Mismatch**, with the differing rows.

## VERIFY on the live account

- The property names used by `DESCRIBE SEMANTIC VIEW`: RELATIONSHIP rows with `TABLE`, `REF_TABLE`, `FOREIGN_KEY` and `REF_KEY`, and TABLE rows with `BASE_TABLE_*` and `PRIMARY_KEY`. If they differ, QA-01 shows "Not checked" with the reason. Send me the output of `DESCRIBE SEMANTIC VIEW <view>` and I will adjust the parser.
- How long the independent queries take on the largest page. Cap: 30 queries per run, 6 in parallel.

## Part B: Validation tab, diagnosis, resolutions (15 Oct)

1. On any dashboard, click **Validation** (next to the page tabs, or top right on single-page dashboards). Check the status card, pages checked, tiles verified, values compared and last run.
2. Click **Validate all pages**. Pages never opened are queried first, then every tile is checked in the background. The hero shows progress; you can keep working.
3. **Check matrix**: one row per tile, one column per check (Source, Math, Totals, Joins, Periods, Health, Filters). Click a row: its evidence opens below the matrix.
4. **What was checked against**: the semantic view, the base tables read, and each join with unique keys and rows with no match.
5. **Needs attention**: each mismatch shows a **Diagnosis**. "Cause found" means the cause reproduces the dashboard numbers exactly; otherwise "Cause not found" with what was ruled out.
6. **Resolve…** a finding: Accept with a reason (pick 7/30/90 days), or Raise data issue (owner + due date, appears in Decisions). The tile turns **Accepted**, never Verified, and re-opens if its numbers change.
7. **Run history** lists the stored runs. Check them in SQL:
   ```sql
   SELECT * FROM WBR_DB.ANALYTICS_ENTERPRISE.AA_VALIDATION_RESOLUTIONS ORDER BY CREATED_AT DESC;
   ```
8. **Publish**: the dialog shows pages validated, tiles verified and any open findings. Publishing is still allowed.
