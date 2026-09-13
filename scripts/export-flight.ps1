$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$OutputDirectory = Join-Path $ProjectRoot "var\exports"
$ArchiveDirectory = Join-Path $ProjectRoot "var\archive"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual nu este inițializat."
}

Push-Location $ProjectRoot
try {
    & $Python -m sodif.reporting.cli --kind both --output-dir $OutputDirectory `
        --archive-root $ArchiveDirectory
    if ($LASTEXITCODE -ne 0) { throw "Exportul flight-ului a eșuat." }
}
finally {
    Pop-Location
}
