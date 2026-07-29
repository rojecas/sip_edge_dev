<# sync.ps1 — Workstation: sincroniza sip_edge_dev -> sip_edge (solo codigo de producto) #>
param([switch]$DryRun)

$devDir  = Split-Path $PSScriptRoot -Parent
$prodDir = Join-Path (Split-Path $devDir -Parent) "sip_edge"

if (-not (Test-Path $prodDir)) {
    Write-Host "[FAIL] No se encontro sip_edge/ en $prodDir" -ForegroundColor Red
    exit 1
}

$excludeDirs = @("harness", ".opencode", ".git", "__pycache__", "node_modules", ".venv", "venv", "SIP-Edge.bk", "diagnostic_scripts")
$excludeFiles = @("sync.ps1", "sync.sh", ".env", "config.yaml", "dump_weighings.sql", "init.ps1", ".session")

$robocopyArgs = @($devDir, $prodDir, "/MIR", "/XD") + $excludeDirs + @("/XF") + $excludeFiles + @("/NP", "/NFL", "/NDL", "/NJH", "/NJS")

if ($DryRun) { $robocopyArgs += "/L" }

Write-Host "Sync: sip_edge_dev -> sip_edge $(if($DryRun){'[DRY RUN]'})" -ForegroundColor Cyan
$result = & robocopy @robocopyArgs

if ($LASTEXITCODE -ge 8) {
    Write-Host "[FAIL] Sync encontro errores" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Sync completado" -ForegroundColor Green
Write-Host "`nRevisa git diff en sip_edge/ antes de commitear." -ForegroundColor Yellow
