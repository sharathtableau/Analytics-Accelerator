@echo off
REM Re-creates only the live views + RETAIL_ANALYTICS_SV and re-runs the checks (data is untouched).
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
copy /y /b 03_semantic_view.sql + 04_validate.sql retail_sv_only.sql >nul
echo Creating the semantic view (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f retail_sv_only.sql -c wbr 2>&1 | Tee-Object -FilePath retail_sv_log.txt"
echo.
echo Finished. Output saved to %cd%\retail_sv_log.txt
endlocal
