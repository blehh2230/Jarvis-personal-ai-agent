Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      JARVIS PERSONAL AI AGENT -- COMMAND CENTER" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[INFO] Backend is already running on http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "[INFO] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
    $py = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
    Start-Process $py -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload" -WindowStyle Minimized
    Start-Sleep -Seconds 2
}

Write-Host "[INFO] Launching JARVIS Command Center in default browser..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000/app"

Write-Host ""
Write-Host "========================================================" -ForegroundColor DarkCyan
Write-Host "  HUD Frontend : http://127.0.0.1:8000/app" -ForegroundColor White
Write-Host "  API Docs     : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Health Check : http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor DarkCyan
Write-Host ""