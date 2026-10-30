@echo off
REM Builds the Apex Athletic (fictional) CPG workspace in WBR_DB.CPG_DEMO, in one Snowflake sign-in:
REM   tables -> upload CSVs -> copy -> rolling-date views -> CPG_ANALYTICS_SV -> checks -> document search.
REM Output is also saved to cpg_setup_log.txt so Claude can read it.
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set P=%~dp0
set P=%P:\=/%
> cpg_put.sql echo PUT 'file://%P%data/*.csv' @WBR_DB.CPG_DEMO.CPG_DATA_STAGE OVERWRITE = TRUE;
> cpg_docs_put.sql echo PUT 'file://%P%docs/*.md' @WBR_DB.CPG_DEMO.CPG_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
copy /y /b 01a_load_tables.sql + cpg_put.sql + 01b_copy.sql + 02_views.sql + 03_semantic_view.sql + 04_validate.sql + 05a_docs_stage.sql + cpg_docs_put.sql + 05b_docs_search.sql cpg_all.sql >nul
echo Building the Apex Athletic workspace (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f cpg_all.sql -c wbr 2>&1 | Tee-Object -FilePath cpg_setup_log.txt"
echo.
echo Finished. Full output saved to %cd%\cpg_setup_log.txt
endlocal
