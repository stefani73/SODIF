$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual nu este inițializat."
}

Push-Location $ProjectRoot
try {
    & $Python -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff a eșuat." }

    & $Python -m mypy src tests
    if ($LASTEXITCODE -ne 0) { throw "mypy a eșuat." }

    & $Python -m pytest
    if ($LASTEXITCODE -ne 0) { throw "pytest a eșuat." }
}
finally {
    Pop-Location
}
