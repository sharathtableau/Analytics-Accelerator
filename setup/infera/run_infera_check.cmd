@echo off
REM Read-only check of SANDBOX.BI.INFERA_SEMANTIC_VIEW: can the app's role see it, and what is in it.
REM Nothing is created or changed. Send infera_check_log.txt back to Claude.
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo Checking INFERA_SEMANTIC_VIEW (a browser window may open for sign-in)...
powershell -NoProfile -Command "'===== AS WBR_OWNER (the app role) =====' | Out-File infera_check_log.txt -Encoding utf8; snow sql -f 08a_check_as_app_role.sql -c wbr 2>&1 | Tee-Object -FilePath infera_check_log.txt -Append"
powershell -NoProfile -Command "'===== AS DS_BASIC (the owner) =====' | Out-File infera_check_log.txt -Append -Encoding utf8; snow sql -f 08b_check_as_owner.sql -c wbr 2>&1 | Tee-Object -FilePath infera_check_log.txt -Append"
echo.
echo Finished. Output saved to %cd%\infera_check_log.txt
endlocal
