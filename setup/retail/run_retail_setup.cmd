@echo off
REM Builds the Harborline Outfitters (fictional) retail demo in WBR_DB.RETAIL_DEMO.
REM One Snowflake login; output is also saved to retail_setup_log.txt so Claude can read it.
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
copy /y /b 01_reference_data.sql + 02_facts.sql + 03_semantic_view.sql + 04_validate.sql retail_demo_all.sql >nul
echo Building retail demo data (this takes a few minutes; a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f retail_demo_all.sql -c wbr 2>&1 | Tee-Object -FilePath retail_setup_log.txt"
echo.
echo Finished. Full output saved to %cd%\retail_setup_log.txt
endlocal
