# 🧹 BEZPIECZNE CZYSZCZENIE PROJEKTU MORDZIX AI
# Usuwa TYLKO zweryfikowane nieużywane pliki

Write-Host "🧹 MORDZIX AI - Czyszczenie projektu" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "c:\Users\48501\Desktop\mrd"
Set-Location $projectRoot

# Liczniki
$deletedFiles = 0
$deletedFolders = 0
$freedSpace = 0

# Funkcja do bezpiecznego usuwania
function Remove-SafeItem {
    param($Path, $Type = "File")
    
    if (Test-Path $Path) {
        try {
            $size = 0
            if ($Type -eq "File") {
                $size = (Get-Item $Path).Length
            } else {
                $size = (Get-ChildItem $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum
            }
            
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
            
            if ($Type -eq "File") {
                $script:deletedFiles++
                Write-Host "✅ Usunięto plik: $(Split-Path $Path -Leaf)" -ForegroundColor Green
            } else {
                $script:deletedFolders++
                Write-Host "✅ Usunięto folder: $(Split-Path $Path -Leaf)" -ForegroundColor Green
            }
            
            $script:freedSpace += $size
            return $true
        }
        catch {
            Write-Host "❌ Błąd usuwania: $Path - $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "⚠️  Nie znaleziono: $(Split-Path $Path -Leaf)" -ForegroundColor Yellow
        return $false
    }
}

Write-Host "🔍 Rozpoczynam czyszczenie..." -ForegroundColor Yellow
Write-Host ""

# ============================================
# KROK 1: NIEUŻYWANE MODUŁY PYTHON
# ============================================
Write-Host "📦 KROK 1: Nieużywane moduły Python" -ForegroundColor Magenta

Remove-SafeItem "$projectRoot\advanced_llm.py"
Remove-SafeItem "$projectRoot\enhanced_prompts.py"
Remove-SafeItem "$projectRoot\proactive_suggestions.py"
Remove-SafeItem "$projectRoot\monolit.py"

Write-Host ""

# ============================================
# KROK 2: DUPLIKATY I ARCHIWA
# ============================================
Write-Host "📁 KROK 2: Duplikaty i archiwa" -ForegroundColor Magenta

Remove-SafeItem "$projectRoot\mordzix-ai" "Folder"
Remove-SafeItem "$projectRoot\mordzix-ai.zip"
Remove-SafeItem "$projectRoot\chat.html"

Write-Host ""

# ============================================
# KROK 3: CACHE I TYMCZASOWE
# ============================================
Write-Host "🗑️  KROK 3: Cache i pliki tymczasowe" -ForegroundColor Magenta

# Python cache
Get-ChildItem $projectRoot -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-SafeItem $_.FullName "Folder"
}

Remove-SafeItem "$projectRoot\.mypy_cache" "Folder"
Remove-SafeItem "$projectRoot\.pytest_cache" "Folder"
Remove-SafeItem "$projectRoot\env.tmp"

Write-Host ""

# ============================================
# KROK 4: ZBĘDNE DOKUMENTY
# ============================================
Write-Host "📄 KROK 4: Zbędne dokumenty" -ForegroundColor Magenta

$docsToRemove = @(
    "CLEANUP_REPORT.md",
    "DASHBOARD_INFO.md",
    "ENDPOINTS_STATUS.md",
    "PERSONALITIES.md",
    "README_AUTO.md",
    "INSTALL_OVH.md",
    "INSTALL_OVH_CORRECTED.txt",
    "QUICK_START_OVH.txt",
    "QUICK_START_WEB_ENABLED.md",
    "START_OVH.sh"
)

foreach ($doc in $docsToRemove) {
    Remove-SafeItem "$projectRoot\$doc"
}

Write-Host ""

# ============================================
# KROK 5: ZBĘDNE SKRYPTY
# ============================================
Write-Host "⚙️  KROK 5: Zbędne skrypty" -ForegroundColor Magenta

Remove-SafeItem "$projectRoot\start_full.ps1"
Remove-SafeItem "$projectRoot\start_full.sh"
Remove-SafeItem "$projectRoot\personality_switcher.js"
Remove-SafeItem "$projectRoot\stress_test_system.py"
Remove-SafeItem "$projectRoot\ultra_destruction_test.py"

Write-Host ""

# ============================================
# KROK 6: LOGI I WYNIKI TESTÓW
# ============================================
Write-Host "📊 KROK 6: Logi i wyniki testów" -ForegroundColor Magenta

Remove-SafeItem "$projectRoot\server_error.txt"
Remove-SafeItem "$projectRoot\server_output.txt"
Remove-SafeItem "$projectRoot\stress_test_results.json"
Remove-SafeItem "$projectRoot\endpoints.json"

Write-Host ""

# ============================================
# KROK 7: DUPLIKATY REQUIREMENTS
# ============================================
Write-Host "📦 KROK 7: Duplikaty requirements" -ForegroundColor Magenta

Remove-SafeItem "$projectRoot\requirements_versioned.txt"

Write-Host ""

# ============================================
# PODSUMOWANIE
# ============================================
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "✅ CZYSZCZENIE ZAKOŃCZONE!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Statystyki:" -ForegroundColor Yellow
Write-Host "   - Usuniętych plików: $deletedFiles" -ForegroundColor White
Write-Host "   - Usuniętych folderów: $deletedFolders" -ForegroundColor White
Write-Host "   - Odzyskana przestrzeń: $([math]::Round($freedSpace / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "🛡️  Zachowano:" -ForegroundColor Green
Write-Host "   ✅ mem.db - baza danych" -ForegroundColor White
Write-Host "   ✅ .env - zmienne środowiskowe" -ForegroundColor White
Write-Host "   ✅ core/ - cała logika biznesowa" -ForegroundColor White
Write-Host "   ✅ requirements.txt - zależności" -ForegroundColor White
Write-Host "   ✅ Wszystkie aktywne endpointy" -ForegroundColor White
Write-Host "   ✅ chat_pro.html - interfejs użytkownika" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Projekt gotowy do działania!" -ForegroundColor Cyan
