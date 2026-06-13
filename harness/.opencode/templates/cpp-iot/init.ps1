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

# PlatformIO CLI disponible
try {
    $pioVersion = & pio --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "platformio -> $pioVersion"
    } else {
        fail "platformio no esta instalado o no esta en PATH"
        fail "Instala con: pip install platformio"
        exit 1
    }
} catch {
    fail "platformio no esta instalado o no esta en PATH"
    fail "Instala con: pip install platformio"
    exit 1
}

# Python (PlatformIO depende de Python)
try {
    $pyVersion = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "python -> $pyVersion"
    } else {
        fail "python no esta disponible"
        exit 1
    }
} catch {
    fail "python no esta disponible"
    exit 1
}

Write-Host ""
Write-Host "-- 2. Instalando dependencias (si es necesario) ------------"

# PlatformIO instala las libs automaticamente al compilar
if (-not (Test-Path -LiteralPath ".pio" -PathType Container)) {
    warn ".pio/ no existe. Ejecutando pio run para instalar dependencias..."
    & pio run 2>&1
    if ($LASTEXITCODE -ne 0) {
        fail "pio run fallo. Revisa platformio.ini"
        $script:exitCode = 1
    } else {
        ok "Dependencias instaladas y proyecto compilado"
    }
} else {
    ok ".pio/ existe. Dependencias ya instaladas."
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
} else {
    ok "Entorno nativo (sin Docker detectado)"
}

Write-Host ""
Write-Host "-- 5. Validando feature_list.json y specs ------------------"

& python harness/.opencode/scripts/validate_features.py
if ($LASTEXITCODE -ne 0) { $script:exitCode = 1 }

Write-Host ""
Write-Host "-- 6. Verificando documentacion de datos --------------------"

if (Test-Path -LiteralPath "harness/docs/database.md" -PathType Leaf) {
    $dbSize = (Get-Item -LiteralPath "harness/docs/database.md").Length
    if ($dbSize -lt 50) {
        warn "docs/database.md parece vacio. Documenta tus estructuras de datos."
    } else {
        ok "docs/database.md existe ($dbSize bytes)"
    }
} else {
    warn "docs/database.md no existe. Creala para documentar estructuras de datos."
}

Write-Host ""
Write-Host "-- 7. Compilando para todos los targets --------------------"

if (Test-Path -LiteralPath "platformio.ini" -PathType Leaf) {
    # Obtener los envs definidos
    $envs = & python -c "import configparser; c=configparser.ConfigParser(); c.read('platformio.ini'); print(','.join(s.split(':')[1].strip() for s in c.sections() if s.startswith('env:')))" 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $envs) {
        foreach ($env in $envs -split ',') {
            if ($env) {
                Write-Host "  Compilando para $env ..."
                & pio run -e $env 2>&1 | Select-Object -Last 5
                if ($LASTEXITCODE -eq 0) {
                    ok "Compilacion OK para $env"
                } else {
                    fail "Compilacion fallo para $env"
                    $script:exitCode = 1
                }
            }
        }
    } else {
        & pio run 2>&1 | Select-Object -Last 5
        if ($LASTEXITCODE -eq 0) {
            ok "Compilacion OK (default env)"
        } else {
            fail "Compilacion fallo"
            $script:exitCode = 1
        }
    }
} else {
    warn "platformio.ini no existe todavia"
}

Write-Host ""
Write-Host "-- 8. Ejecutando tests en host -----------------------------"

if (Test-Path -LiteralPath "test" -PathType Container) {
    # Primero tests nativos (no requieren hardware)
    & pio test -e native 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "Tests en host pasan"
    } else {
        warn "Tests en host fallaron (puede ser normal si no hay env native)"
    }
} else {
    warn "Carpeta test/ no existe todavia"
}

Write-Host ""
Write-Host "-- 7. Resumen ---------------------------------------------"

if ($script:exitCode -eq 0) {
    ok "Entorno listo. Puedes empezar a trabajar."
} else {
    fail "Entorno NO esta listo. Resuelve los errores antes de avanzar."
}

exit $script:exitCode
