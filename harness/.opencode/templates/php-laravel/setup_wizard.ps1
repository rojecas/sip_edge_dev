<#
.SYNOPSIS
  setup_wizard.ps1 -- Wizard de configuracion para PHP/Laravel
.DESCRIPTION
  Guia interactiva para configurar un proyecto Laravel nuevo:
  - Pregunta version de PHP, version de Laravel, configuracion MySQL
  - Genera Dockerfile, compose.yml, .env
  - Levanta contenedores e instala Laravel dentro de Docker
  Llamado por scripts/setup_wizard.ps1 (dispatcher generico).
#>

$script:exitCode = 0

function ok   { Write-Host "[OK]    $args" -ForegroundColor Green }
function warn { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function fail { Write-Host "[FAIL]  $args" -ForegroundColor Red; $script:exitCode = 1 }

function Read-Choice {
    param([string]$Prompt, [string[]]$Options, [string]$Default)
    Write-Host ""
    Write-Host $Prompt
    for ($i = 0; $i -lt $Options.Length; $i++) {
        $marker = if ($Options[$i] -eq $Default) { " [*]" } else { " [ ]" }
        Write-Host "  $($i + 1). $($Options[$i])$marker"
    }
    while ($true) {
        $answer = Read-Host "  Elige (1-$($Options.Length)) [Enter para default]"
        if ([string]::IsNullOrWhiteSpace($answer)) { return $Default }
        $num = 0
        if ([int]::TryParse($answer, [ref]$num) -and $num -ge 1 -and $num -le $Options.Length) {
            return $Options[$num - 1]
        }
        Write-Host "  Opcion invalida. Intenta de nuevo." -ForegroundColor Yellow
    }
}

function Read-WithDefault {
    param([string]$Prompt, [string]$Default)
    $answer = Read-Host "  $Prompt [Enter = '$Default']"
    if ([string]::IsNullOrWhiteSpace($answer)) { return $Default }
    return $answer
}

function Read-Password {
    param([string]$Prompt, [string]$Default)
    $answer = Read-Host "  $Prompt [Enter = $Default]" -AsSecureString
    if ($answer.Length -eq 0) { return $Default }
    $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($answer)
    try { return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

# ==== 1. Leer nombre del proyecto ========================================

$projectName = "proyecto"
if (Test-Path -LiteralPath "feature_list.json" -PathType Leaf) {
    try {
        $fl = Get-Content "feature_list.json" -Raw | ConvertFrom-Json
        if ($fl.project) { $projectName = $fl.project }
    } catch { }
}
$projectName = $projectName -replace '[^a-zA-Z0-9_-]', '_'

Write-Host ""
Write-Host "=============================================================="
Write-Host "  PHP / Laravel -- Configuracion del proyecto"
Write-Host "=============================================================="
Write-Host ""
Write-Host "  Proyecto detectado: $projectName"
Write-Host ""

# ==== 2. Elegir version de PHP ===========================================

$phpVersion = Read-Choice `
    -Prompt "Version de PHP:" `
    -Options @("8.2", "8.3", "8.4") `
    -Default "8.3"

ok "PHP version: $phpVersion"

# ==== 3. Elegir version de Laravel =======================================

$laravelVersion = Read-Choice `
    -Prompt "Version de Laravel:" `
    -Options @("12 (latest)", "11 (LTS)") `
    -Default "12 (latest)"

$laravelMajor = if ($laravelVersion -match "12") { "12" } else { "11" }
ok "Laravel version: $laravelMajor"

# ==== 4. Elegir motor de BD ==============================================

$dbEngine = Read-Choice `
    -Prompt "Motor de base de datos:" `
    -Options @("MySQL 8.4 (LTS)", "MySQL 8.0", "MariaDB 11.4 (LTS)", "MariaDB 10.11 (LTS)", "SQLite (archivo local)", "PostgreSQL 16") `
    -Default "MySQL 8.4 (LTS)"

ok "Base de datos: $dbEngine"

$useSqlite = $dbEngine -match "SQLite"
$usePgsql = $dbEngine -match "PostgreSQL"

$dbImage = switch -Wildcard ($dbEngine) {
    "MySQL 8.4*"    { "mysql:8.4" }
    "MySQL 8.0*"    { "mysql:8.0" }
    "MariaDB 11.4*" { "mariadb:11.4" }
    "MariaDB 10.11*" { "mariadb:10.11" }
    "PostgreSQL*"   { "postgres:16" }
    default         { "" }
}

$dbConnection = if ($usePgsql) { "pgsql" } elseif ($useSqlite) { "sqlite" } else { "mysql" }
$dbHost = if ($usePgsql) { "pgsql" } else { "mysql" }

# ==== 5. Configurar puerto externo =======================================

$dbPortExternal = "3306"
$dbInternalPort = "3306"
if (-not $useSqlite) {
    if ($usePgsql) {
        $dbPortExternal = "5432"
        $dbInternalPort = "5432"
    }
    $dbPortExternal = Read-WithDefault `
        -Prompt "Puerto externo para la base de datos:" `
        -Default $dbPortExternal
}

# ==== 6. Credenciales de BD ==============================================

if (-not $useSqlite) {
    $dbName = Read-WithDefault `
        -Prompt "Nombre de la base de datos:" `
        -Default $projectName

    $dbUser = Read-WithDefault `
        -Prompt "Usuario de la base de datos:" `
        -Default $projectName

    $dbPass = Read-Password `
        -Prompt "Password de la base de datos:" `
        -Default "$($projectName)_secret"

    Write-Host ""
    $rootPass = Read-Password `
        -Prompt "Password root de la base de datos:" `
        -Default "root_secret"
}

# ==== 7. Confirmacion =====================================================

Write-Host ""
Write-Host "--------------------------------------------------------------"
Write-Host "  RESUMEN DE CONFIGURACION"
Write-Host "--------------------------------------------------------------"
Write-Host "  Proyecto:        $projectName"
Write-Host "  PHP:             $phpVersion"
Write-Host "  Laravel:         $laravelMajor"
Write-Host "  Base de datos:   $dbEngine"
if (-not $useSqlite) {
    Write-Host "  Puerto externo:  $dbPortExternal"
    Write-Host "  DB name:         $dbName"
    Write-Host "  DB user:         $dbUser"
}
Write-Host ""

$confirm = Read-Host "  Continuar con la instalacion? [S/n]"
if ($confirm -match "^(n|N|no|NO|No)$") {
    warn "Instalacion cancelada por el usuario."
    exit 0
}

# ==== 8. Generar Dockerfile ==============================================

Write-Host ""
Write-Host "-- Generando Dockerfile -----------------------------------------"

$dockerExtPgsql = " libpq-dev"
$dockerExtInstall = " && docker-php-ext-install pdo_pgsql"
if ($usePgsql) {
    # pgsql extras already in defaults
} elseif ($useSqlite) {
    $dockerExtPgsql = ""
    $dockerExtInstall = ""
} else {
    # mysql is default
    $dockerExtPgsql = ""
    $dockerExtInstall = " && docker-php-ext-install pdo_mysql"
}

$dockerfile = @"
FROM php:$phpVersion-cli

RUN apt-get update && apt-get install -y \
    git unzip libzip-dev libonig-dev libcurl4-openssl-dev libxml2-dev$dockerExtPgsql \
    && docker-php-ext-install pdo mbstring zip opcache bcmath curl dom xml$dockerExtInstall

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www
"@

Set-Content -Path "Dockerfile" -Value $dockerfile
ok "Dockerfile generado (PHP $phpVersion-cli)"

# ==== 9. Generar compose.yml =============================================

Write-Host "-- Generando compose.yml -----------------------------------------"

$composeYml = ""
$composeYml += "services:`n"
$composeYml += "  app:`n"
$composeYml += "    build:`n"
$composeYml += "      context: .`n"
$composeYml += "      dockerfile: Dockerfile`n"
$composeYml += "    volumes:`n"
$composeYml += "      - .:/var/www`n"
$composeYml += "    working_dir: /var/www`n"
$composeYml += "    command: tail -f /dev/null`n"
$composeYml += "    networks:`n"
$composeYml += "      - ${projectName}_net`n"

if (-not $useSqlite) {
    $dbService = if ($usePgsql) { "pgsql" } else { "mysql" }
    $composeYml += "`n"
    $composeYml += "    depends_on:`n"
    $composeYml += "      - ${dbService}`n"
    $composeYml += "`n"
    $composeYml += "  ${dbService}:`n"
    $composeYml += "    image: $dbImage`n"
    $composeYml += "    restart: unless-stopped`n"
    $composeYml += "    environment:`n"
    if ($usePgsql) {
        $composeYml += "      POSTGRES_DB: $dbName`n"
        $composeYml += "      POSTGRES_USER: $dbUser`n"
        $composeYml += "      POSTGRES_PASSWORD: $dbPass`n"
    } else {
        $composeYml += "      MYSQL_DATABASE: $dbName`n"
        $composeYml += "      MYSQL_USER: $dbUser`n"
        $composeYml += "      MYSQL_PASSWORD: $dbPass`n"
        $composeYml += "      MYSQL_ROOT_PASSWORD: $rootPass`n"
    }
    $composeYml += "    ports:`n"
    $composeYml += "      - `"${dbPortExternal}:${dbInternalPort}`"`n"
    $composeYml += "    volumes:`n"
    $composeYml += "      - ${projectName}_dbdata:/var/lib/$dbService`n"
    $composeYml += "    networks:`n"
    $composeYml += "      - ${projectName}_net`n"
}

$composeYml += "`n"
$composeYml += "volumes:`n"
if (-not $useSqlite) {
    $composeYml += "  ${projectName}_dbdata:`n"
}
$composeYml += "`n"
$composeYml += "networks:`n"
$composeYml += "  ${projectName}_net:`n"
$composeYml += "    driver: bridge`n"

Set-Content -Path "compose.yml" -Value $composeYml
ok "compose.yml generado"

# ==== 10. Generar .env ==================================================

Write-Host "-- Generando .env ------------------------------------------------"

$randomBytes = New-Object byte[] 16
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($randomBytes)
$appKeyPlaceholder = "base64:" + [Convert]::ToBase64String($randomBytes) + "="

$envContent = @"
APP_NAME=$projectName
APP_ENV=local
APP_KEY=$appKeyPlaceholder
APP_DEBUG=true
APP_URL=http://localhost

LOG_CHANNEL=stack
LOG_LEVEL=debug

DB_CONNECTION=$dbConnection
"@

if (-not $useSqlite) {
    $envContent += @"
DB_HOST=$dbHost
DB_PORT=$dbInternalPort
DB_DATABASE=$dbName
DB_USERNAME=$dbUser
DB_PASSWORD=$dbPass
"@
} else {
    $sqlitePath = Join-Path (Get-Location) "database/database.sqlite"
    $envContent += @"
DB_DATABASE=$sqlitePath
"@
}

Set-Content -Path ".env" -Value $envContent
ok ".env generado"

# ==== 11. Construir y levantar contenedores ==============================

Write-Host ""
Write-Host "-- Construyendo imagen Docker ------------------------------------"

& docker compose build app
if ($LASTEXITCODE -ne 0) {
    fail "docker compose build fallo. Verifica que Docker este instalado y corriendo."
    exit 1
}
ok "Imagen Docker construida"

if (-not $useSqlite) {
    Write-Host "-- Levantando servicio de base de datos -------------------------"
    & docker compose up -d $dbHost
    if ($LASTEXITCODE -ne 0) {
        fail "docker compose up fallo para $dbHost"
        exit 1
    }
    ok "Servicio $dbHost levantado"

    Write-Host "-- Esperando a que $dbHost termine de inicializar --------------"
    $maxWait = 60
    $waited = 0
    $ready = $false
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 5
        $waited += 5
        Write-Host "  Esperando... (${waited}s)"
        try {
            $client = New-Object System.Net.Sockets.TcpClient('127.0.0.1', $dbPortExternal)
            $client.Close()
            $ready = $true
            break
        } catch { }
    }
    if ($ready) {
        ok "$dbHost acepta conexiones (espera: ${waited}s)"
        Start-Sleep -Seconds 5
    } else {
        warn "$dbHost no acepta conexiones tras ${waited}s. Continuando..."
        Start-Sleep -Seconds 15
    }
}

Write-Host ""
Write-Host "-- Levantando contenedor de la aplicacion ----------------------"

& docker compose up -d app
if ($LASTEXITCODE -ne 0) {
    fail "docker compose up fallo para app"
    exit 1
}
ok "Contenedor app listo"

# ==== 12. Actualizar environment.md =====================================

Write-Host "-- Actualizando docs/environment.md ------------------------------"

if ($usePgsql) {
    $dbDisplayName = "PostgreSQL"
} elseif ($useSqlite) {
    $dbDisplayName = "SQLite (archivo local)"
} else {
    $dbDisplayName = "MySQL"
}

# Build envMd using single-quoted here-strings (safe for backticks) + string interpolation for variables
$envMd = "# Environment -- $projectName`n`n"
$envMd += @'
> El agente DEBE leer este archivo **antes de ejecutar cualquier comando bash**.
> Describe DONDE y COMO se ejecutan los comandos, y que servicios estan disponibles.
> Generado automaticamente por el setup wizard.

## Execution mode

**Mode:** docker

**Compose file:** compose.yml

**Service:** app

> Todos los comandos PHP se ejecutan dentro del contenedor `app`.

## Shell

Prefix ALL commands with: `docker compose exec app`

Ejemplo: `docker compose exec app php artisan test`

## Runtime

'@
$envMd += "- PHP $phpVersion (dentro del contenedor ``app``)`n"
$envMd += "- Composer (dentro del contenedor ``app``)`n"
$envMd += "- Laravel $laravelMajor (instalar manualmente tras el wizard)`n`n"

$envMd += @'
## Services

| Service       | Host access            | Container access      |
|--------------|-----------------------|----------------------|
| app (PHP)    | --                     | --                    |
'@

if (-not $useSqlite) {
    $envMd += "| $dbDisplayName | 127.0.0.1:${dbPortExternal}   | ${dbHost}:${dbInternalPort}        |`n"
}

$envMd += @'

> Edita esta tabla segun tu compose.yml si anades mas servicios.

## Primeros pasos (crear proyecto Laravel)

```bash
# Crear proyecto Laravel dentro del contenedor
docker compose exec app composer create-project laravel/laravel .

# Generar APP_KEY
docker compose exec app php artisan key:generate

# Ejecutar migraciones iniciales
docker compose exec app php artisan migrate
```

## Init / Lifecycle

```bash
# Arrancar servicios (primera vez o despues de apagar)
docker compose up -d

# Instalar dependencias PHP
docker compose exec app composer install

# Ejecutar migraciones
docker compose exec app php artisan migrate

# Ejecutar tests
docker compose exec app php artisan test

# Verificar formato
docker compose exec app ./vendor/bin/pint --test
```
'@

Set-Content -Path "docs/environment.md" -Value $envMd
ok "docs/environment.md actualizado"

# ==== 13. Instrucciones finales ==========================================

Write-Host ""
Write-Host "=============================================================="
Write-Host "  ENTORNO CONFIGURADO"
Write-Host "=============================================================="
Write-Host ""
Write-Host "  Stack:       PHP $phpVersion"
Write-Host "  Framework:   Laravel $laravelMajor (pendiente de instalar)"
if (-not $useSqlite) {
    Write-Host "  Base datos:  $dbEngine (puerto ${dbPortExternal})"
    Write-Host "  DB name:     $dbName"
    Write-Host "  DB user:     $dbUser"
} else {
    Write-Host "  Base datos:  SQLite (archivo local)"
}
Write-Host ""
Write-Host "  Contenedores activos:"
Write-Host "    - app  (PHP $phpVersion + Composer, idle)"
if (-not $useSqlite) {
    Write-Host "    - $dbHost ($dbImage)"
}
Write-Host ""
Write-Host "  === PARA CREAR EL PROYECTO LARAVEL, EJECUTA: ==="
Write-Host ""
Write-Host "    docker compose exec app composer create-project laravel/laravel ."
Write-Host "    docker compose exec app php artisan key:generate"
Write-Host ""
if (-not $useSqlite) {
    Write-Host "  (la base de datos '$dbName' ya existe y esta lista)"
}
Write-Host "  === COMANDOS UTILES ==="
Write-Host "    docker compose up -d                # Arrancar servicios"
Write-Host "    docker compose down                 # Detener servicios"
Write-Host "    docker compose exec app composer    # Gestionar dependencias"
Write-Host "    docker compose exec app php artisan # CLI de Laravel"
Write-Host ""

exit 0

