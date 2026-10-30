@echo off
REM Re-creates only CPG_ANALYTICS_SV and re-runs the checks (data, views and document search are untouched).
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
copy /y /b 03_semantic_view.sql + 04_validate.sql cpg_sv_only.sql >nul
echo Re-creating the semantic view (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f cpg_sv_only.sql -c wbr 2>&1 | Out-File -Encoding utf8 cpg_sv_log.txt; Get-Content cpg_sv_log.txt"
echo.
echo Finished. Output saved to %cd%\cpg_sv_log.txt
endlocal
