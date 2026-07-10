# === UTF-8 encoding guard (added 2026-07-09) ===
try { chcp 65001 2>&1 | Out-Null } catch { }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

<#
.SYNOPSIS
  close.ps1 -- Cierre de sesion limpio para sip_edge
.DESCRIPTION
  Ejecuta los 3 pasos del cierre de sesion:
  1. Verifica documentacion pendiente (current.md, closure-*.md)
  2. Sincroniza con repositorio remoto (git pull/push) o advierte si no hay remote
  3. Ejecuta init.ps1 como verificacion final
.PARAMETER SkipDocs
  Omite la verificacion de documentacion
.PARAMETER SkipGit
  Omite la sincronizacion con repositorio remoto
.PARAMETER SkipVerify
  Omite la ejecucion de init.ps1
#>

param(
    [switch]$SkipDocs,
    [switch]$SkipGit,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
$script:exitCode = 0

function ok   { Write-Host "[OK]    $args" -ForegroundColor Green }
function warn { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function fail { Write-Host "[FAIL]  $args" -ForegroundColor Red; $script:exitCode = 1 }

Write-Host ""
Write-Host "=============================================================="
Write-Host "  CIERRE DE SESION"
Write-Host "=============================================================="
Write-Host ""

# ------------------------------------------------------------------
# 1. Documentacion
# ------------------------------------------------------------------
if (-not $SkipDocs) {
    Write-Host "-- 1. Verificando documentacion pendiente --------------------"

    $currentMd = Join-Path $PSScriptRoot "..\progress\current.md"
    if (Test-Path $currentMd) {
        $content = Get-Content $currentMd -Raw
        $nonTemplateLines = $content -split "`n" | Where-Object {
            $line = $_.Trim()
            # Skip empty/whitespace
            if ($line -notmatch '\S') { return $false }
            # Skip markdown structure: headers, blockquotes, horizontal rules
            if ($line -match '^\s*#') { return $false }
            if ($line -match '^\s*>') { return $false }
            if ($line -match '^\s*---') { return $false }
            # Skip feature index table rows (| NN | name | status |)
            if ($line -match '^\|\s*\d+\s*\|') { return $false }
            # Skip table header and separator
            if ($line -match '^\|\s*ID\s*\|') { return $false }
            if ($line -match '^\|[\s\-:]+\|') { return $false }
            # Skip template metadata with placeholder values
            if ($line -match '^\-\s+\*\*Inicio:\*\*\s*\(pendiente\)') { return $false }
            if ($line -match '^\-\s+\*\*Agente:\*\*\s*\(pendiente\)') { return $false }
            if ($line -match '^\-\s+\*\*Feature en curso:\*\*\s*\(ninguna\)') { return $false }
            if ($line -match '^\-\s+\*\*Estado:\*\*\s*\(ninguno\)') { return $false }
            # Skip section placeholders
            if ($line -eq '(pendiente)') { return $false }
            if ($line -eq '(ninguno)') { return $false }
            if ($line -eq '(none)') { return $false }
            return $true
        }
        if ($nonTemplateLines.Count -gt 0) {
            warn "harness/progress/current.md contiene trabajo sin archivar."
            Write-Host "  Mueva el resumen a harness/progress/history.md y vacie current.md"
        } else {
            ok "current.md sin trabajo pendiente"
        }
    } else {
        warn "No se encontro harness/progress/current.md"
    }

    $featureList = Join-Path $PSScriptRoot "..\feature_list.json"
    if (Test-Path $featureList) {
        $features = Get-Content $featureList -Raw | ConvertFrom-Json
        foreach ($f in $features.features) {
            if ($f.status -eq "done") {
                $closureFile = Join-Path $PSScriptRoot "..\progress\closure-$($f.name).md"
                if (-not (Test-Path $closureFile)) {
                    warn "Feature '$($f.name)' esta 'done' pero falta closure-$($f.name).md"
                }
            }
        }
    }

    ok "Verificacion de documentacion completada"
    Write-Host ""
}

# ------------------------------------------------------------------
# 2. Git sync
# ------------------------------------------------------------------
if (-not $SkipGit) {
    Write-Host "-- 2. Sincronizando con repositorio remoto ------------------"

    $remotes = git remote -v 2>$null
    if ($LASTEXITCODE -eq 0 -and $remotes) {
        Write-Host "  Remote detectado. Verificando working tree limpio..."
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $dirty = git status --porcelain 2>&1
        $ErrorActionPreference = $prevEAP
        if ($dirty) {
            fail "Working tree sucio. Haga commit de los cambios antes de cerrar la sesion."
            Write-Host "  git status para ver los archivos modificados."
            $script:exitCode = 1
        } else {
            Write-Host "  Working tree limpio. Ejecutando git pull --rebase..."
            $prevEAP = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            git pull --rebase 2>&1 | ForEach-Object { Write-Host "  $_" }
            $ErrorActionPreference = $prevEAP
            if ($LASTEXITCODE -ne 0) {
                fail "git pull --rebase fallo"
            } else {
                Write-Host "  Ejecutando git push..."
                $prevEAP = $ErrorActionPreference
                $ErrorActionPreference = "Continue"
                git push 2>&1 | ForEach-Object { Write-Host "  $_" }
                $ErrorActionPreference = $prevEAP
                if ($LASTEXITCODE -ne 0) {
                    fail "git push fallo"
                } else {
                    ok "Repositorio sincronizado con remoto"
                }
            }
        }
    } else {
        warn "No se detecto repositorio remoto (git remote -v vacio). Saltando sincronizacion."
    }
    Write-Host ""
}

# ------------------------------------------------------------------
# 3. Verificacion final
# ------------------------------------------------------------------
if (-not $SkipVerify) {
    Write-Host "-- 3. Ejecutando verificacion final (init.ps1) --------------"
    Write-Host ""

    $initScript = Join-Path $PSScriptRoot "..\init.ps1"
    if (Test-Path $initScript) {
        & $initScript
        $verifyExit = $LASTEXITCODE
        Write-Host ""
        if ($verifyExit -eq 0) {
            ok "init.ps1 paso correctamente"
        } else {
            fail "init.ps1 reporto errores (exit code $verifyExit)"
        }
    } else {
        fail "No se encontro init.ps1 en harness/"
    }
}

# ------------------------------------------------------------------
# 4. Marcar sesion como cerrada
# ------------------------------------------------------------------
$sessionFile = Join-Path $PSScriptRoot "..\.session"
Set-Content -LiteralPath $sessionFile -Value "closed"
ok "Sesion marcada como cerrada (harness/.session = closed)"

# ------------------------------------------------------------------
# Resumen
# ------------------------------------------------------------------
Write-Host ""
Write-Host "=============================================================="
if ($script:exitCode -eq 0) {
    ok "Cierre de sesion completado exitosamente"
} else {
    fail "Cierre de sesion completado con errores. Revise arriba."
}
Write-Host "=============================================================="

exit $script:exitCode
