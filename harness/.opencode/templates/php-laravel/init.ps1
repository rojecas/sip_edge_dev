<#
.SYNOPSIS
  init.ps1 -- Verificacion e inicializacion del entorno de spanel
.DESCRIPTION
  Este script lo ejecuta el agente al COMENZAR una sesion y antes de
  declarar cualquier tarea como `done`. Si falla, la sesion no debe avanzar.
  La deteccion de proyecto nuevo y el wizard Docker los maneja el wrapper raiz.
  Soporta modo Docker (por defecto) y modo nativo.
#>

$exitCode = 0

function ok   { Write-Host "[OK]    $args" -ForegroundColor Green }
function warn { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function fail { Write-Host "[FAIL]  $args" -ForegroundColor Red; $script:exitCode = 1 }

# ==== 0. Estado de Laravel ================================================

Write-Host "-- 0. Verificando estado de Laravel -------------------------"

$lacksLaravel = (-not (Test-Path -LiteralPath "composer.json" -PathType Leaf))

if ($lacksLaravel) {
    warn "Laravel no instalado. El wizard del wrapper raiz lo configurara."
} elseif (-not (Test-Path -LiteralPath "vendor" -PathType Container)) {
    warn "vendor/ no existe. Se instalaran dependencias en paso 3."
} else {
    ok "vendor/ existe. Proyecto ya inicializado."
}

# ==== 1. Detectar entorno de ejecucion ====================================

Write-Host ""
Write-Host "-- 1. Detectando entorno de ejecucion -----------------------"

$isInContainer = (Test-Path "/.dockerenv") -or (Test-Path "/.containerenv")
$hasCompose = (Test-Path "compose.yml") -or (Test-Path "docker-compose.yml") -or (Test-Path "docker-compose.yaml")

$useDocker = $false
if ($isInContainer) {
    ok "Ejecutando dentro de un contenedor Docker"
    $useDocker = $true
} elseif ($hasCompose) {
    ok "Detectado compose.yml. Usando Docker para todos los comandos PHP."
    $useDocker = $true
} else {
    ok "Entorno nativo (sin Docker detectado)"
}

# ==== 2. Verificar runtime PHP ============================================

Write-Host ""
Write-Host "-- 2. Verificando PHP --------------------------------------"

if ($useDocker) {
    # Check PHP inside the Docker container
    $servicesRunning = & docker compose ps -q 2>$null
    if (-not $servicesRunning) {
        warn "Contenedores no estan corriendo. Intentando levantar..."
        & docker compose up -d
        if ($LASTEXITCODE -ne 0) {
            fail "No se pudo levantar los contenedores docker compose"
            exit 1
        }
    }
    $phpVer = & docker compose exec -T app php --version
    if ($LASTEXITCODE -eq 0) {
        ok "php (docker) -> $($phpVer -split '\n' | Select-Object -First 1)"
    } else {
        fail "php no se pudo ejecutar dentro del contenedor app"
        exit 1
    }
} else {
    try {
        $phpVer = & php --version 2>&1 | Select-Object -First 1
        if ($LASTEXITCODE -eq 0) {
            ok "php -> $phpVer"
        } else {
            fail "php no esta instalado o no esta en PATH"
            exit 1
        }
    } catch {
        fail "php no esta instalado o no esta en PATH"
        exit 1
    }
    & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>&1 > $null
}

# ==== 3. Instalar dependencias ============================================

Write-Host ""
Write-Host "-- 3. Dependencias PHP -------------------------------------"

if ($lacksLaravel) {
    if ($useDocker) {
        warn "Laravel no esta instalado todavia (sin composer.json)."
        Write-Host "       Ejecuta manualmente:"
        Write-Host "         docker compose exec app composer create-project laravel/laravel ."
        Write-Host "         docker compose exec app php artisan key:generate"
        Write-Host "       Luego vuelve a ejecutar init.ps1"
    } else {
        fail "composer.json no encontrado. Instala Laravel primero."
    }
} else {
    if (-not (Test-Path -LiteralPath "vendor" -PathType Container)) {
        warn "vendor/ no existe. Instalando dependencias..."
        if ($useDocker) {
            & docker compose exec -T app composer install --no-interaction
        } else {
            & composer install --no-interaction 2>&1
        }
        if ($LASTEXITCODE -ne 0) {
            fail "composer install fallo"
            exit 1
        }
        ok "Dependencias instaladas"
    } else {
        ok "vendor/ existe"
    }
}

# ==== 4. Archivos base del harness ========================================

Write-Host ""
Write-Host "-- 4. Verificando archivos base del harness ----------------"

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

# ==== 5. Schema de base de datos ==========================================

Write-Host ""
Write-Host "-- 5. Verificando schema de base de datos ------------------"

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
    if (Test-Path -LiteralPath "database/migrations" -PathType Container) {
        $migrationCount = (Get-ChildItem -LiteralPath "database/migrations" -Filter "*.php" -ErrorAction SilentlyContinue).Count
        if ($migrationCount -gt 0) {
            ok "database/migrations/ contiene $migrationCount migraciones PHP"
        }
    }
    if (Test-Path -LiteralPath "database/backups" -PathType Container) {
        $backupCount = (Get-ChildItem -LiteralPath "database/backups" -Filter "*.sql" -ErrorAction SilentlyContinue).Count
        if ($backupCount -gt 0) {
            ok "database/backups/ contiene $backupCount backups"
        }
    }
} else {
    if (Test-Path -LiteralPath "harness/docs/database.md" -PathType Leaf) {
        ok "docs/database.md presente (persistencia no-SQL documentada)"
    }
}

# ==== 6. Validar feature_list.json ========================================

Write-Host ""
Write-Host "-- 6. Validando feature_list.json y specs -----------------"

$valid = & python harness/.opencode/scripts/validate_features.py 2>&1
if ($LASTEXITCODE -ne 0) {
    $valid | Out-Host
    $script:exitCode = 1
} else {
    ok "feature_list.json es valido"
}

# ==== 7. Ejecutar tests ===================================================

Write-Host ""
Write-Host "-- 7. Ejecutando tests ------------------------------------"

if ($lacksLaravel) {
    ok "Laravel no instalado aun -- saltando tests"
} elseif (Test-Path -LiteralPath "tests" -PathType Container) {
    $testOk = $false
    if ($useDocker) {
        & docker compose exec -T app php artisan test --env=testing
        $testOk = ($LASTEXITCODE -eq 0)
    } else {
        & php artisan test --env=testing 2>&1
        $testOk = ($LASTEXITCODE -eq 0)
    }
    if ($testOk) {
        ok "Todos los tests pasan"
    } else {
        fail "Hay tests rotos"
        $script:exitCode = 1
    }
} else {
    warn "Carpeta tests/ no existe todavia"
}

# ==== 8. Verificar formato ================================================

Write-Host ""
Write-Host "-- 8. Verificando formato ---------------------------------"

if ($lacksLaravel) {
    ok "Laravel no instalado aun -- saltando formato"
} elseif ($useDocker) {
    if (Test-Path -LiteralPath "vendor/bin/pint" -PathType Leaf) {
        & docker compose exec -T app php vendor/bin/pint --test
        if ($LASTEXITCODE -eq 0) {
            ok "Formato PSR-12 correcto"
        } else {
            warn "Hay problemas de formato. Ejecuta: docker compose exec app composer pint"
        }
    }
} else {
    if (Test-Path -LiteralPath "vendor/bin/pint" -PathType Leaf) {
        & php vendor/bin/pint --test 2>&1
        if ($LASTEXITCODE -eq 0) {
            ok "Formato PSR-12 correcto"
        } else {
            warn "Hay problemas de formato. Ejecuta: composer pint"
        }
    }
}

# ==== 9. Resumen ==========================================================

Write-Host ""
Write-Host "-- 9. Resumen ---------------------------------------------"

if ($script:exitCode -eq 0) {
    if ($lacksLaravel -and $useDocker) {
        ok "Entorno Docker listo. Instala Laravel con:"
        Write-Host "         docker compose exec app composer create-project laravel/laravel ."
        Write-Host "         docker compose exec app php artisan key:generate"
    } else {
        ok "Entorno listo. Puedes empezar a trabajar."
    }
} else {
    fail "Entorno NO esta listo. Resuelve los errores antes de avanzar."
}

exit $script:exitCode

