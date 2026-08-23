$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Streamlit = Join-Path $ProjectRoot ".venv\Scripts\streamlit.exe"
$Application = Join-Path $ProjectRoot "src\sodif\app.py"

if (-not (Test-Path -LiteralPath $Streamlit)) {
    throw "Mediul virtual nu este inițializat. Rulați mai întâi instalarea Pasului 1."
}

& $Streamlit run $Application

