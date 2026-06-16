<#
.SYNOPSIS
  close.ps1 -- Delegates to harness/scripts/close.ps1
.DESCRIPTION
  Wrapper for backward compatibility. Invokes the canonical close script
  at harness/scripts/close.ps1.
#>

$canonical = Join-Path $PSScriptRoot "..\harness\scripts\close.ps1"
if (Test-Path $canonical) {
    & $canonical @args
    exit $LASTEXITCODE
} else {
    Write-Host "[FAIL] Canonical close script not found at $canonical" -ForegroundColor Red
    exit 1
}
