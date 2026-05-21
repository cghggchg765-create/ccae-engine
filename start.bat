@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo.
echo ================================================
echo   CCAE ^| Cross-Cultural Adaptation Engine
echo ================================================
echo.
echo   http://127.0.0.1:5000/
echo.

python run.py %*

if errorlevel 1 pause
endlocal
