@echo off
REM Re-creates the rolling views and FINANCE_ANALYTICS_SV, then re-runs the checks (data and document search are untouched).
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
copy /y /b 02_views.sql + 03_semantic_view.sql + 04_validate.sql finance_sv_only.sql >nul
echo Re-creating the views and the semantic view (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f finance_sv_only.sql -c wbr 2>&1 | Out-File -Encoding utf8 finance_sv_log.txt; Get-Content finance_sv_log.txt"
echo.
echo Finished. Output saved to %cd%\finance_sv_log.txt
endlocal
