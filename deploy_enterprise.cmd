@echo off
setlocal
REM Deploys the Enterprise edition as its own app. Does not touch ANALYTICS_ACCELERATOR_UI.
REM   App:  WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_ENTERPRISE
REM   First time only:   snow sql -c wbr -f setup\00_create_schema.sql
REM   Rebuild the React UI after editing app\frontend\src:   deploy_enterprise.cmd build
set CONN=wbr
set PYTHONIOENCODING=utf-8
cd /d "%~dp0app"
if /I "%1"=="build" (
  where node >nul 2>nul || (echo [ERROR] Node.js is required to rebuild the UI. & exit /b 1)
  pushd frontend
  if not exist node_modules call npm ci --no-audit --no-fund || exit /b 1
  call npm run build || exit /b 1
  popd
)
echo [1/3] Running tests (local, no Snowflake calls)...
python -m unittest discover -s tests -p "test_*.py" || exit /b 1
echo [2/3] Deploying ANALYTICS_ACCELERATOR_ENTERPRISE...
cd streamlit
snow streamlit deploy analytics_accelerator_enterprise --replace -c %CONN% || exit /b 1
echo [3/3] Checking the deployed main file...
snow sql -c %CONN% -q "DESCRIBE STREAMLIT WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_ENTERPRISE" | findstr /i "app.py" >nul || (echo [WARN] main_file is not app.py. Run: snow sql -c %CONN% -q "DROP STREAMLIT WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_ENTERPRISE" and re-run.)
snow streamlit get-url WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_ENTERPRISE -c %CONN%
endlocal
