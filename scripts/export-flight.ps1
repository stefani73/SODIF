$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$OutputDirectory = Join-Path $ProjectRoot "var\exports"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual nu este inițializat."
}

Push-Location $ProjectRoot
try {
    & $Python -m sodif.reporting.cli --output-dir $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw "Exportul flight-ului a eșuat." }
}
finally {
    Pop-Location
}
