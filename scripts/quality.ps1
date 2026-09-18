$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$QualityRunRoot = Join-Path $ProjectRoot ("var\quality\" + [Guid]::NewGuid().ToString("N"))

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual nu este inițializat."
}

Push-Location $ProjectRoot
try {
    & (Join-Path $PSScriptRoot "verify-toolchain.ps1") | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Verificarea toolchain-ului a eșuat." }

    & $Python -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff a eșuat." }

    & $Python -m mypy src tests
    if ($LASTEXITCODE -ne 0) { throw "mypy a eșuat." }

    New-Item -ItemType Directory -Path $QualityRunRoot -Force | Out-Null
    $env:SODIF_ARCHIVE_ROOT = Join-Path $QualityRunRoot "archive"
    $env:SODIF_EXPORT_ROOT = Join-Path $QualityRunRoot "exports"
    & $Python -m pytest --basetemp (Join-Path $QualityRunRoot "pytest")
    if ($LASTEXITCODE -ne 0) { throw "pytest a eșuat." }
}
finally {
    Pop-Location
}
