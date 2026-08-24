$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual nu este inițializat."
}

Push-Location $ProjectRoot
try {
    & $Python -m sodif.demo.cli
    if ($LASTEXITCODE -ne 0) { throw "Flight-ul SODIF a eșuat." }
}
finally {
    Pop-Location
}
