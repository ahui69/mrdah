################################################################################
# MORDZIX AI - ANGULAR DEPLOY (PowerShell)
# Automatyczny build i upload frontendu Angular na serwer OVH
################################################################################

param(
    [string]$Server = "162.19.220.29",
    [string]$User = "ubuntu",
    [string]$KeyPath = "C:\Users\48501\.ssh\id_ed25519_ovh",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " MORDZIX AI - ANGULAR FRONTEND DEPLOY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$LocalPath = "C:\Users\48501\Desktop\mrd\frontend"
$DistPath = "$LocalPath\dist\mordzix-ai"
$RemotePath = "/workspace/mrd/frontend/dist"

# 1. Check Node.js
Write-Host "[1/5] Sprawdzanie Node.js..." -ForegroundColor Green
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Gray
    Write-Host "  npm: $npmVersion" -ForegroundColor Gray
} catch {
    Write-Host "  BŁĄD: Node.js nie zainstalowany!" -ForegroundColor Red
    Write-Host "  Pobierz z: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# 2. Install dependencies (jeśli node_modules nie istnieje)
if (-not (Test-Path "$LocalPath\node_modules")) {
    Write-Host "[2/5] Instalacja zależności..." -ForegroundColor Green
    Push-Location $LocalPath
    npm install
    Pop-Location
} else {
    Write-Host "[2/5] Zależności już zainstalowane (skip)" -ForegroundColor Gray
}

# 3. Build Angular
if (-not $SkipBuild) {
    Write-Host "[3/5] Build Angular production..." -ForegroundColor Green
    Push-Location $LocalPath
    
    # Usuń stary build
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force dist
    }
    
    # Build
    npm run build:prod
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  BŁĄD: Build failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host "  Build success!" -ForegroundColor Green
} else {
    Write-Host "[3/5] Build skip (--SkipBuild)" -ForegroundColor Gray
}

# 4. Sprawdź czy build istnieje
if (-not (Test-Path "$DistPath\index.html")) {
    Write-Host "  BŁĄD: Build nie istnieje! ($DistPath)" -ForegroundColor Red
    exit 1
}

$buildSize = (Get-ChildItem -Recurse $DistPath | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "  Build size: $([math]::Round($buildSize, 2)) MB" -ForegroundColor Gray

# 5. Upload do serwera
Write-Host "[4/5] Upload do serwera..." -ForegroundColor Green

# Test połączenia
try {
    ssh -i $KeyPath -o ConnectTimeout=5 $User@$Server "echo OK" | Out-Null
} catch {
    Write-Host "  BŁĄD: Nie można połączyć się z serwerem!" -ForegroundColor Red
    exit 1
}

# Utwórz katalog na serwerze
ssh -i $KeyPath $User@$Server "mkdir -p $RemotePath"

# Upload plików
Write-Host "  Przesyłanie plików..." -ForegroundColor Gray
scp -i $KeyPath -r $DistPath ${User}@${Server}:${RemotePath}/

if ($LASTEXITCODE -ne 0) {
    Write-Host "  BŁĄD: Upload failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  Upload complete!" -ForegroundColor Green

# 6. Restart backendu
Write-Host "[5/5] Restart serwera..." -ForegroundColor Green
ssh -i $KeyPath $User@$Server "sudo supervisorctl restart mordzix"

Start-Sleep -Seconds 2

# Sprawdź status
$status = ssh -i $KeyPath $User@$Server "sudo supervisorctl status mordzix"
Write-Host "  Status: $status" -ForegroundColor Gray

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host " DEPLOY ZAKOŃCZONY!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Aplikacja dostępna na:" -ForegroundColor Yellow
Write-Host "  https://mordxixai.xyz/" -ForegroundColor White
Write-Host ""
Write-Host "Sprawdź logi:" -ForegroundColor Yellow
Write-Host "  ssh -i $KeyPath $User@$Server 'sudo supervisorctl tail -f mordzix'" -ForegroundColor White
Write-Host ""
