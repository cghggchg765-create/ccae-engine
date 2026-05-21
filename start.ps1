# CCAE Cross-Cultural Adaptation Engine
# Usage: .\start.ps1 [--port 8080] [--host 127.0.0.1] [--no-debug]

Set-Location "$PSScriptRoot"

:: Check for virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[WARN] No venv found, using system Python" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CCAE | Cross-Cultural Adaptation Engine"       -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Management UI : "  -NoNewline
Write-Host "http://127.0.0.1:5000/" -ForegroundColor Green
Write-Host "  API Base      : "  -NoNewline
Write-Host "http://127.0.0.1:5000/api" -ForegroundColor Green
Write-Host ""

python run.py @args
