@echo off
REM Loads the Harborline documents into Snowflake and builds the Cortex Search service (one sign-in).
REM   stage -> PUT PDFs (+ markdown twins) -> AI_PARSE_DOCUMENT -> SPLIT_TEXT_RECURSIVE_CHARACTER -> CORTEX SEARCH SERVICE
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set P=%~dp0
set P=%P:\=/%
> docs_put.sql echo PUT 'file://%P%docs/pdf/*.pdf' @WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
>> docs_put.sql echo PUT 'file://%P%docs/*.md' @WBR_DB.RETAIL_DEMO.RETAIL_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
copy /y /b 05a_docs_stage.sql + docs_put.sql + 05b_docs_search.sql docs_search_all.sql >nul
echo Building document search (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f docs_search_all.sql -c wbr 2>&1 | Tee-Object -FilePath docs_search_log.txt"
echo.
echo Finished. Output saved to %cd%\docs_search_log.txt
endlocal
