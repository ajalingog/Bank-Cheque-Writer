@echo off
cd /d "%~dp0"
echo Starting Philippine Cheque Writer (Windows app)...
py -3 -m app
if errorlevel 1 python -m app
if errorlevel 1 pause
