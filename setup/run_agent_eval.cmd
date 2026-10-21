@echo off
REM D1: registers the Cortex Agent evaluation dataset + config and starts a baseline run (AI Observability).
REM Run AFTER the agent exists (ask it one question in the app first).
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set P=%~dp0
set P=%P:\=/%
> eval_put.sql echo PUT 'file://%P%eval/aa_agent_eval.yaml' @WBR_DB.ANALYTICS_ENTERPRISE.AA_EVAL_CONFIG AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
copy /y /b 07_agent_eval.sql + eval_put.sql + 07b_agent_eval_start.sql agent_eval_all.sql >nul
echo Setting up agent evaluation (a browser window opens for sign-in)...
powershell -NoProfile -Command "snow sql -f agent_eval_all.sql -c wbr 2>&1 | Tee-Object -FilePath agent_eval_log.txt"
echo.
echo Finished. Output saved to %cd%\agent_eval_log.txt  (the run itself takes 3-5 minutes)
endlocal
