@echo off
REM Pulls tokens and credits per app feature (last 30 days) for the partner deck.
REM Output: setup\cost_snapshot_log.txt
REM Optional role that can read SNOWFLAKE.ACCOUNT_USAGE:  run_cost_snapshot.cmd ACCOUNTADMIN
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python cost_snapshot.py %1 > cost_snapshot_log.txt 2>&1
type cost_snapshot_log.txt
