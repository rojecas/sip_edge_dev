# === UTF-8 encoding guard (added 2026-07-09) ===
# Mitiga corrupcion de caracteres en Windows: fuerza ACP 65001 (UTF-8)
# y configura el console output encoding. Requiere reboot tras el cambio de registry.
try { chcp 65001 2>&1 | Out-Null } catch { }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

<#
.SYNOPSIS
  init.ps1 -- Verificacion e inicializacion del entorno de sip_edge
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

# Python disponible
try {
    $pyVersion = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "python -> $pyVersion"
    } else {
        fail "python no esta instalado o no esta en PATH"
        exit 1
    }
} catch {
    fail "python no esta instalado o no esta en PATH"
    exit 1
}

# Version minima 3.9
& python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>&1
if ($LASTEXITCODE -eq 0) {
    ok "Version de Python compatible"
} else {
    fail "Se requiere Python >= 3.9"
    exit 1
}

Write-Host ""
Write-Host "-- 1.5. Verificando estado de sesion anterior ----------------"

$sessionFile = "harness/.session"
if (Test-Path -LiteralPath $sessionFile -PathType Leaf) {
    $sessionStatus = (Get-Content -LiteralPath $sessionFile -Raw).Trim()
    if ($sessionStatus -eq "open") {
        warn "La sesion anterior NO se cerro correctamente (harness/.session = open)"
        Write-Host "  Revisa harness/progress/current.md y git status para verificar el estado."
        Write-Host "  Ejecuta harness/scripts/close.ps1 si quieres cerrar la sesion anterior formalmente."
    } elseif ($sessionStatus -eq "closed") {
        ok "Sesion anterior cerrada correctamente (harness/.session = closed)"
    } else {
        warn "harness/.session contiene un valor desconocido: '$sessionStatus'"
    }
} else {
    warn "No se encontro harness/.session. El agente debe crearlo al iniciar trabajo."
}

Write-Host ""
Write-Host "-- 2. Verificando archivos base del harness ------------------"

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
Write-Host "-- 3. Detectando entorno de ejecucion -----------------------"

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
Write-Host "-- 4. Verificando schema de base de datos -------------------"

if (Test-Path -LiteralPath "harness/database/.schema_dump.json" -PathType Leaf) {
    ok "database/.schema_dump.json detectado"
    
    # Regenerar docs/database.md desde la BD real
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $null = & python harness/scripts/schema_dump.py 2>&1
    $ErrorActionPreference = $prevEAP
    if ($LASTEXITCODE -eq 0) {
        ok "docs/database.md regenerado desde la BD"
    } else {
        warn "schema_dump.py fallo. La BD puede no estar disponible."
    }

    # Contar migraciones (informativo)
    if (Test-Path -LiteralPath "harness/database/migrations" -PathType Container) {
        $migrationCount = (Get-ChildItem -LiteralPath "harness/database/migrations" -Filter "*.sql" -ErrorAction SilentlyContinue).Count
        if ($migrationCount -gt 0) {
            ok "database/migrations/ contiene $migrationCount archivos SQL"
        }
    }

    # Contar backups (informativo)
    if (Test-Path -LiteralPath "harness/database/backups" -PathType Container) {
        $backupCount = (Get-ChildItem -LiteralPath "harness/database/backups" -Filter "*.sql" -ErrorAction SilentlyContinue).Count
        if ($backupCount -gt 0) {
            ok "database/backups/ contiene $backupCount backups"
        }
    }
} else {
    # Sin BD SQL: verificar que docs/database.md describa la persistencia real
    if (Test-Path -LiteralPath "harness/docs/database.md" -PathType Leaf) {
        ok "docs/database.md presente (persistencia no-SQL documentada)"
    }
}

Write-Host ""
Write-Host "-- 5. Validando feature_list.json y specs ------------------"

$valid = & python harness/scripts/validate_features.py 2>&1
if ($LASTEXITCODE -ne 0) {
    $valid | Out-Host
    $script:exitCode = 1
} else {
    ok "feature_list.json es valido"
}

# Verificar que features sdd: true con status spec_ready/in_progress/done tengan su carpeta specs/
$featuresJson = Get-Content -LiteralPath "harness/feature_list.json" -Raw | ConvertFrom-Json
foreach ($feat in $featuresJson.features) {
    $featType = if ($feat.PSObject.Properties['type']) { $feat.type } else { "feature" }
    $featStatus = $feat.status
    $featName = $feat.name
    $featId = $feat.id
    $sdd = if ($feat.PSObject.Properties['sdd']) { $feat.sdd } else { $false }

    # Solo verificar specs para features SDD (no bugs)
    if ($featType -ne "bug" -and $sdd -eq $true -and $featStatus -in @("spec_ready", "in_progress", "done")) {
        $paddedId = "{0:D2}" -f $featId
        $specDir = "harness/specs/${paddedId}_$featName"
        if (Test-Path -LiteralPath $specDir -PathType Container) {
            $reqFile = Join-Path $specDir "requirements.md"
            $desFile = Join-Path $specDir "design.md"
            $tskFile = Join-Path $specDir "tasks.md"
            $allSpecFiles = $true
            foreach ($sf in @($reqFile, $desFile, $tskFile)) {
                if (-not (Test-Path -LiteralPath $sf -PathType Leaf)) {
                    warn "Falta archivo de spec: $sf (feature $featId - $featName)"
                    $allSpecFiles = $false
                }
            }
            if ($allSpecFiles) {
                ok "Spec completo para feature $featId ($featName)"
            }
        } else {
            fail "Falta carpeta de spec: $specDir (feature $featId - $featName)"
            $script:exitCode = 1
        }
    }
}

Write-Host ""
Write-Host "-- 6. Ejecutando tests -------------------------------------"

if (Test-Path -LiteralPath "tests" -PathType Container) {
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    if ($hasCompose) {
        $testResult = & docker compose exec -T backend python -m unittest discover -s tests -v 2>&1
    } else {
        $testResult = & python -m unittest discover -s tests -v 2>&1
    }
    $ErrorActionPreference = $prevEAP
    $testExit = $LASTEXITCODE
    if ($testExit -eq 0 -or $testExit -eq 5) {
        ok "Todos los tests pasan"
    } else {
        $testResult | Out-Host
        fail "Hay tests rotos"
        $script:exitCode = 1
    }
} else {
    warn "Carpeta tests/ no existe todavia"
}

Write-Host ""
Write-Host "-- 7. Resumen ---------------------------------------------"

if ($script:exitCode -eq 0) {
    ok "Entorno listo. Puedes empezar a trabajar."
} else {
    fail "Entorno NO esta listo. Resuelve los errores antes de avanzar."
}

exit $script:exitCode
