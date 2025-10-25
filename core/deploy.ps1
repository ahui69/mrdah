################################################################################
# MORDZIX AI - DEPLOY DO OVH (PowerShell)
# Automatyczne przesyłanie i uruchomienie na serwerze produkcyjnym
################################################################################

param(
    [string]$Server = "162.19.220.29",
    [string]$User = "ubuntu",
    [string]$KeyPath = "C:\Users\48501\.ssh\id_ed25519_ovh"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " MORDZIX AI - DEPLOY NA SERWER OVH" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$LocalPath = "C:\Users\48501\Desktop\mrd"
$RemotePath = "/workspace/mrd"

# 1. Test połączenia
Write-Host "[1/5] Test połączenia SSH..." -ForegroundColor Green
try {
    ssh -i $KeyPath -o ConnectTimeout=5 $User@$Server "echo 'OK'" | Out-Null
    Write-Host " Połączenie OK" -ForegroundColor Green
} catch {
    Write-Host " BŁĄD: Nie można połączyć się z serwerem!" -ForegroundColor Red
    Write-Host " Sprawdź: ssh -i $KeyPath $User@$Server" -ForegroundColor Yellow
    exit 1
}

# 2. Utwórz katalog workspace
Write-Host "[2/5] Tworzenie katalogu workspace..." -ForegroundColor Green
ssh -i $KeyPath $User@$Server "sudo mkdir -p $RemotePath && sudo chown -R ubuntu:ubuntu /workspace"
Write-Host " Katalog utworzony" -ForegroundColor Green

# 3. Przesyłanie plików (TYLKO WAŻNE!)
Write-Host "[3/5] Przesyłanie plików..." -ForegroundColor Green

$FilesToUpload = @(
    "app.py",
    "index.html",
    ".env",
    "requirements.txt",
    "start_production.sh",
    "assistant_endpoint.py",
    "psyche_endpoint.py",
    "programista_endpoint.py",
    "files_endpoint.py",
    "travel_endpoint.py",
    "admin_endpoint.py",
    "captcha_endpoint.py",
    "prometheus_endpoint.py",
    "tts_endpoint.py",
    "stt_endpoint.py",
    "writing_endpoint.py",
    "suggestions_endpoint.py",
    "batch_endpoint.py",
    "research_endpoint.py"
)

foreach ($file in $FilesToUpload) {
    $fullPath = Join-Path $LocalPath $file
    if (Test-Path $fullPath) {
        Write-Host "  Przesyłanie: $file" -ForegroundColor Gray
        scp -i $KeyPath $fullPath ${User}@${Server}:${RemotePath}/
    }
}

# Prześlij folder core/
Write-Host "  Przesyłanie: core/" -ForegroundColor Gray
scp -i $KeyPath -r "$LocalPath\core" ${User}@${Server}:${RemotePath}/

Write-Host " Pliki przesłane" -ForegroundColor Green

# 4. Nadaj uprawnienia i uruchom
Write-Host "[4/5] Konfiguracja i uruchomienie..." -ForegroundColor Green
ssh -i $KeyPath $User@$Server @"
cd $RemotePath
chmod +x *.sh
sudo ./start_production.sh
"@

# 5. Sprawdź status
Write-Host "[5/5] Sprawdzanie statusu..." -ForegroundColor Green
Start-Sleep -Seconds 5
ssh -i $KeyPath $User@$Server "sudo supervisorctl status mordzix"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host " DEPLOY ZAKOŃCZONY!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Aplikacja dostępna na:" -ForegroundColor Yellow
Write-Host "  https://mordxixai.xyz/" -ForegroundColor White
Write-Host "  https://mordxixai.xyz/docs" -ForegroundColor White
Write-Host ""
Write-Host "Logi:" -ForegroundColor Yellow
Write-Host "  ssh -i $KeyPath $User@$Server 'sudo supervisorctl tail -f mordzix'" -ForegroundColor White
Write-Host ""
