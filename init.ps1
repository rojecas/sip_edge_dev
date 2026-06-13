<#
.SYNOPSIS
  init.ps1 -- Wrapper de verificacion para sip_edge
.DESCRIPTION
  Delegacion hacia harness/init.ps1.
#>

$harnessInit = Join-Path $PSScriptRoot "harness\init.ps1"
if (Test-Path $harnessInit) {
    & $harnessInit
    exit $LASTEXITCODE
} else {
    Write-Host "[FAIL] harness\init.ps1 no encontrado" -ForegroundColor Red
    exit 1
}