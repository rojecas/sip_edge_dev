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

    $currentMd = Join-Path $PSScriptRoot "..\harness\progress\current.md"
    if (Test-Path $currentMd) {
        $content = Get-Content $currentMd -Raw
        $nonTemplateLines = $content -split "`n" | Where-Object {
            $_ -match '\S' -and
            $_ -notmatch '^\s*#' -and
            $_ -notmatch '^\s*>' -and
            $_ -notmatch '^\s*---' -and
            $_ -notmatch '^\s*$'
        }
        if ($nonTemplateLines.Count -gt 2) {
            warn "harness/progress/current.md contiene trabajo sin archivar."
            Write-Host "  Mueva el resumen a harness/progress/history.md y vacie current.md"
        } else {
            ok "current.md sin trabajo pendiente"
        }
    } else {
        warn "No se encontro harness/progress/current.md"
    }

    $featureList = Join-Path $PSScriptRoot "..\harness\feature_list.json"
    if (Test-Path $featureList) {
        $features = Get-Content $featureList -Raw | ConvertFrom-Json
        foreach ($f in $features.features) {
            if ($f.status -eq "done") {
                $closureFile = Join-Path $PSScriptRoot "..\harness\progress\closure-$($f.name).md"
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
        Write-Host "  Remote detectado. Ejecutando git pull --rebase..."
        git pull --rebase 2>&1 | ForEach-Object { Write-Host "  $_" }
        if ($LASTEXITCODE -ne 0) {
            fail "git pull --rebase fallo"
        } else {
            Write-Host "  Ejecutando git push..."
            git push 2>&1 | ForEach-Object { Write-Host "  $_" }
            if ($LASTEXITCODE -ne 0) {
                fail "git push fallo"
            } else {
                ok "Repositorio sincronizado con remoto"
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
        fail "No se encontro init.ps1 en la raiz del proyecto"
    }
}

# ------------------------------------------------------------------
# 4. Marcar sesion como cerrada
# ------------------------------------------------------------------
$sessionFile = Join-Path $PSScriptRoot "..\harness\.session"
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
