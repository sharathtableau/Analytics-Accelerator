@echo off
REM Builds the Keystone Financial (fictional) finance workspace in WBR_DB.FINANCE_DEMO, in one Snowflake sign-in:
REM   tables -> upload CSVs -> copy -> rolling-date views -> FINANCE_ANALYTICS_SV -> checks -> document search.
REM Output is also saved to finance_setup_log.txt so Claude can read it.
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set P=%~dp0
set P=%P:\=/%
> finance_put.sql echo PUT 'file://%P%data/*.csv' @WBR_DB.FINANCE_DEMO.FINANCE_DATA_STAGE OVERWRITE = TRUE;
> finance_docs_put.sql echo PUT 'file://%P%docs/*.md' @WBR_DB.FINANCE_DEMO.FINANCE_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
copy /y /b 01a_load_tables.sql + finance_put.sql + 01b_copy.sql + 02_views.sql + 03_semantic_view.sql + 04_validate.sql + 05a_docs_stage.sql + finance_docs_put.sql + 05b_docs_search.sql finance_all.sql >nul
echo Building the Keystone Financial workspace (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f finance_all.sql -c wbr 2>&1 | Tee-Object -FilePath finance_setup_log.txt"
echo.
echo Finished. Full output saved to %cd%\finance_setup_log.txt
endlocal
