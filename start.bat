@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

:: Check for virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARN] No venv found, using system Python
)

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
