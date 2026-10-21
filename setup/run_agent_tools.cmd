@echo off
REM Creates the Cortex Agent action tool (stored procedure AA_CREATE_DECISION) and smoke-tests it.
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo Creating agent tools (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f 06_agent_tools.sql -c wbr 2>&1 | Tee-Object -FilePath agent_tools_log.txt"
echo.
echo Finished. Output saved to %cd%\agent_tools_log.txt
endlocal
