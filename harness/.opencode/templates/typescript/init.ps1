<#
.SYNOPSIS
  init.ps1 -- Verificacion e inicializacion del entorno de {{PROJECT_NAME}}
.DESCRIPTION
  Este script lo ejecuta el agente al COMENZAR una sesion y antes de
  declarar cualquier tarea como `done`. Si falla, la sesion no debe avanzar.
  En la primera ejecucion, instala dependencias automaticamente.
#>

$exitCode = 0

function ok   { Write-Host "[OK]    $args" -ForegroundColor Green }
function warn { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function fail { Write-Host "[FAIL]  $args" -ForegroundColor Red; $script:exitCode = 1 }

Write-Host "-- 1. Verificando entorno ----------------------------------"

# Node.js disponible
try {
    $nodeVersion = & node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "node -> $nodeVersion"
    } else {
        fail "node no esta instalado o no esta en PATH"
        exit 1
    }
} catch {
    fail "node no esta instalado o no esta en PATH"
    exit 1
}

# npm disponible
try {
    $npmVersion = & npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "npm -> v$npmVersion"
    } else {
        fail "npm no esta disponible"
        exit 1
    }
} catch {
    fail "npm no esta disponible"
    exit 1
}

Write-Host ""
Write-Host "-- 2. Instalando dependencias (si es necesario) ------------"

if (-not (Test-Path -LiteralPath "node_modules" -PathType Container)) {
    warn "node_modules/ no existe. Ejecutando npm install..."
    & npm install 2>&1
    if ($LASTEXITCODE -ne 0) {
        fail "npm install fallo"
        exit 1
    }
    ok "Dependencias instaladas"
} else {
    ok "node_modules/ existe"
}

Write-Host ""
Write-Host "-- 3. Verificando archivos base del harness ------------------"

$baseFiles = @(
    "harness/AGENTS.md",
    "harness/VERSION",
    "harness/feature_list.json",
    "harness/progress/current.md",
    "harness/docs/architecture.md",
    "harness/docs/conventions.md",
    "harness/docs/verification.md",
    "harness/docs/specs.md",
    "harness/docs/environment.md",
    "harness/docs/sessions.md",
    "harness/CHECKPOINTS.md"
)

foreach ($f in $baseFiles) {
    if (Test-Path -LiteralPath $f -PathType Leaf) {
        ok "Existe $f"
    } else {
        fail "Falta archivo base: $f"
        $script:exitCode = 1
    }
}

Write-Host ""
Write-Host "-- 4. Detectando entorno de ejecucion -----------------------"

$isInContainer = (Test-Path "/.dockerenv") -or (Test-Path "/.containerenv")
$hasCompose = (Test-Path "compose.yml") -or (Test-Path "docker-compose.yml") -or (Test-Path "docker-compose.yaml")

if ($isInContainer) {
    ok "Ejecutando dentro de un contenedor Docker"
} elseif ($hasCompose) {
    ok "Detectado compose.yml. El proyecto usa Docker."
    if ((Get-Content "harness/docs/environment.md" -Raw) -notmatch "docker") {
        warn "environment.md no refleja el uso de Docker. Revisa la seccion 'Template Docker' en el archivo y actualizalo."
    }
} else {
    ok "Entorno nativo (sin Docker detectado)"
}

Write-Host ""
Write-Host "-- 5. Verificando schema de base de datos -------------------"

if (Test-Path -LiteralPath "harness/database/.schema_dump.json" -PathType Leaf) {
    ok "database/.schema_dump.json detectado"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $null = & python harness/.opencode/scripts/schema_dump.py 2>&1
    $ErrorActionPreference = $prevEAP
    if ($LASTEXITCODE -eq 0) {
        ok "docs/database.md regenerado desde la BD"
    } else {
        warn "schema_dump.py fallo. La BD puede no estar disponible."
    }
    if (Test-Path -LiteralPath "harness/database/migrations" -PathType Container) {
        $migrationCount = (Get-ChildItem -LiteralPath "harness/database/migrations" -Filter "*.sql" -ErrorAction SilentlyContinue).Count
        if ($migrationCount -gt 0) {
            ok "database/migrations/ contiene $migrationCount archivos SQL"
        }
    }
    if (Test-Path -LiteralPath "harness/database/backups" -PathType Container) {
        $backupCount = (Get-ChildItem -LiteralPath "harness/database/backups" -Filter "*.sql" -ErrorAction SilentlyContinue).Count
        if ($backupCount -gt 0) {
            ok "database/backups/ contiene $backupCount backups"
        }
    }
} else {
    if (Test-Path -LiteralPath "harness/docs/database.md" -PathType Leaf) {
        ok "docs/database.md presente (persistencia no-SQL documentada)"
    }
}

Write-Host ""
Write-Host "-- 6. Validando feature_list.json y specs ------------------"

$valid = & python harness/.opencode/scripts/validate_features.py 2>&1
if ($LASTEXITCODE -ne 0) {
    $valid | Out-Host
    $script:exitCode = 1
} else {
    ok "feature_list.json es valido"
}

Write-Host ""
Write-Host "-- 7. Ejecutando tests -------------------------------------"

if (Test-Path -LiteralPath "tests" -PathType Container) {
    & npx vitest run 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "Todos los tests pasan"
    } else {
        fail "Hay tests rotos"
        $script:exitCode = 1
    }
} else {
    warn "Carpeta tests/ no existe todavia"
}

Write-Host ""
Write-Host "-- 8. Resumen ---------------------------------------------"

if ($script:exitCode -eq 0) {
    ok "Entorno listo. Puedes empezar a trabajar."
} else {
    fail "Entorno NO esta listo. Resuelve los errores antes de avanzar."
}

exit $script:exitCode
