<#
.SYNOPSIS
  init.ps1 -- Delega en harness/init.ps1
.DESCRIPTION
  Wrapper que ejecuta el script de verificacion real ubicado en harness/init.ps1.
  Mantenido en raiz por compatibilidad con opencode y scaffold.
  NOTA: Cambia CWD a $PSScriptRoot para que harness/init.ps1 resuelva
  correctamente sus rutas relativas desde la raiz del proyecto.
#>

Push-Location $PSScriptRoot
try {
    & "harness\init.ps1" @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
