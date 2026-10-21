@echo off
setlocal
REM Deploys the AI Gateway probe: a small TEST-ONLY Streamlit app, WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PROBE.
REM It does not touch the Analytics Accelerator or the portal. See the playbook, section "AI Gateway test".
REM Remove it afterwards with:  snow sql -c wbr -q "DROP STREAMLIT WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PROBE"
set CONN=wbr
set PYTHONIOENCODING=utf-8
cd /d "%~dp0gateway_probe"
echo [1/2] Deploying AA_GATEWAY_PROBE...
snow streamlit deploy aa_gateway_probe --replace -c %CONN% || exit /b 1
echo [2/2] Probe URL:
snow streamlit get-url WBR_DB.ANALYTICS_ENTERPRISE.AA_GATEWAY_PROBE -c %CONN%
endlocal
