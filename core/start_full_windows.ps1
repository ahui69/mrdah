################################################################################
# MORDZIX AI - WINDOWS STARTUP SCRIPT (PowerShell)
# Pełna instalacja + setup + uruchomienie
################################################################################

Write-Host "" -ForegroundColor Cyan
Write-Host " MORDZIX AI - WINDOWS SETUP" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host ""

$APP_PORT = 8080

Write-Host "[1/3] Sprawdzanie Python..." -ForegroundColor Green
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host " Python nie znaleziony!" -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Instalacja zależności..." -ForegroundColor Green
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt -q
}

Write-Host "[3/3] Uruchamianie serwera..." -ForegroundColor Green
Write-Host ""
Write-Host " Serwer dostępny na:" -ForegroundColor Green
Write-Host "  http://localhost:$APP_PORT/chat_pro_clean.html" -ForegroundColor White
Write-Host ""

uvicorn app:app --host 0.0.0.0 --port $APP_PORT --reload
