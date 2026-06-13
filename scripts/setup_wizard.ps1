<#
.SYNOPSIS
  setup_wizard.ps1 -- Wizard de configuracion para proyectos nuevos
.DESCRIPTION
  Detecta si el proyecto es nuevo (sin archivos del stack real), infiere el
  stack del template copiado, y ejecuta el wizard especifico del stack.
  Llamado automaticamente por init.ps1 al detectar un proyecto virgen.
#>

$script:exitCode = 0

function ok   { Write-Host "[OK]    $args" -ForegroundColor Green }
function warn { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function fail { Write-Host "[FAIL]  $args" -ForegroundColor Red; $script:exitCode = 1 }

Write-Host ""
Write-Host "=============================================================="
Write-Host "  SETUP WIZARD -- Configuracion inicial del proyecto"
Write-Host "=============================================================="
Write-Host ""

# ==== 1. Detectar si es un proyecto nuevo ================================

$markers = @("composer.json", "package.json", "Cargo.toml", "go.mod", "platformio.ini", ".env")
$isNew = $true
foreach ($m in $markers) {
    if (Test-Path -LiteralPath $m -PathType Leaf) {
        $isNew = $false
        break
    }
}

if ($isNew) {
    $srcFiles = @(Get-ChildItem -LiteralPath "src" -ErrorAction SilentlyContinue)
    $testFiles = @(Get-ChildItem -LiteralPath "tests" -ErrorAction SilentlyContinue)
    $onlyGitkeep = $true
    foreach ($f in $srcFiles) { if ($f.Name -ne ".gitkeep") { $onlyGitkeep = $false } }
    foreach ($f in $testFiles) { if ($f.Name -ne ".gitkeep") { $onlyGitkeep = $false } }
    if (-not $onlyGitkeep) { $isNew = $false }
}

if (-not $isNew) {
    ok "El proyecto ya esta inicializado. Saltando wizard."
    exit 0
}

ok "Proyecto nuevo detectado. Iniciando configuracion..."

# ==== 2. Inferir stack del init.ps1 ======================================

$initContent = Get-Content "init.ps1" -Raw -ErrorAction SilentlyContinue
$stack = "unknown"

if ($initContent -match "php artisan")               { $stack = "php-laravel" }
elseif ($initContent -match "python -m unittest")    { $stack = "python" }
elseif ($initContent -match "npm test|npx vitest|jest") { $stack = "typescript" }
elseif ($initContent -match "cargo test")            { $stack = "rust" }
elseif ($initContent -match "go test")               { $stack = "go" }
elseif ($initContent -match "pio run|platformio")    { $stack = "cpp-iot" }

Write-Host "  Stack inferido: $stack"

# ==== 3. Ejecutar wizard especifico del stack ============================

$wizardPaths = @(
    "harness/.opencode/templates/$stack/setup_wizard.ps1",
    ".opencode/templates/$stack/setup_wizard.ps1"
)

$wizardFound = $false
foreach ($wp in $wizardPaths) {
    if (Test-Path -LiteralPath $wp -PathType Leaf) {
        Write-Host "  Ejecutando wizard de $stack ($wp)..."
        Write-Host ""
        & $wp
        $script:exitCode = $LASTEXITCODE
        if ($script:exitCode -ne 0) {
            fail "El wizard de $stack fallo (exit code: $script:exitCode)"
        }
        $wizardFound = $true
        break
    }
}

if (-not $wizardFound) {
    fail "No se encontro wizard para el stack '$stack'"
    Write-Host "  Buscado en: $($wizardPaths -join ', ')"
    Write-Host "  Stacks conocidos: php-laravel, python, typescript, rust, go, cpp-iot"
}

exit $script:exitCode
