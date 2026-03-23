@echo off
setlocal
cd /d %~dp0

echo Starte Google Ads Analyzer Wizard...
echo.
python wizard.py

echo.
echo Fertig. Taste druecken zum Schliessen...
pause >nul
