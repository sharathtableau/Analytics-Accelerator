@echo off
setlocal
REM Deploys the Dashboard Portal (viewers only) as its own app. Same code and tables as the builder.
REM   Portal:  WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_PORTAL
REM   Builders keep ANALYTICS_ACCELERATOR_ENTERPRISE (deploy_enterprise.cmd). Do not run "deploy_enterprise.cmd build"
REM   unless app\frontend\src is the current UI source (the deployed UI bundle is the source of truth for now).
set CONN=wbr
set PYTHONIOENCODING=utf-8
cd /d "%~dp0app"
echo [1/3] Running tests (local, no Snowflake calls)...
python -m unittest discover -s tests -p "test_*.py" || exit /b 1
echo [2/3] Deploying ANALYTICS_ACCELERATOR_PORTAL...
cd streamlit
snow streamlit deploy analytics_accelerator_portal --replace -c %CONN% || exit /b 1
echo [3/3] Portal URL:
snow streamlit get-url WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_PORTAL -c %CONN%
REM To give a viewer role the portal (and not the builder), run once per role:
REM   snow sql -c %CONN% -q "GRANT USAGE ON STREAMLIT WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_PORTAL TO ROLE <VIEWER_ROLE>"
endlocal
