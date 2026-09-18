param(
    [System.IO.FileInfo]$OutputPath
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LockPath = Join-Path $ProjectRoot "repro\toolchain.lock.json"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual .venv nu este inițializat."
}
if (-not (Test-Path -LiteralPath $LockPath)) {
    throw "Lipsește repro/toolchain.lock.json."
}

$Lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
$Tesseract = if ($env:SODIF_TESSERACT_CMD) {
    $env:SODIF_TESSERACT_CMD
} elseif (Test-Path -LiteralPath "C:\Program Files\Tesseract-OCR\tesseract.exe") {
    "C:\Program Files\Tesseract-OCR\tesseract.exe"
} else {
    (Get-Command tesseract -ErrorAction Stop).Source
}
$PdfToPpm = if ($env:SODIF_PDFTOPPM_CMD) {
    $env:SODIF_PDFTOPPM_CMD
} else {
    (Get-Command pdftoppm -ErrorAction Stop).Source
}

$PythonVersion = (& $Python -c "import sys; print(sys.version.split()[0])").Trim()
$PackageJson = & $Python -c "import importlib.metadata as m, json; print(json.dumps({n:m.version(n) for n in ('PyMuPDF','streamlit','streamlit-pdf')}, sort_keys=True))"
$Packages = $PackageJson | ConvertFrom-Json
$TesseractLine = (& $Tesseract --version 2>&1 | Select-Object -First 1).ToString()
$TesseractVersion = [regex]::Match($TesseractLine, 'v([0-9.]+)').Groups[1].Value
$Languages = @(& $Tesseract --list-langs 2>&1 | Select-Object -Skip 1) | ForEach-Object {
    $_.ToString().Trim()
} | Where-Object { $_ }
$PopplerLine = (& $PdfToPpm -v 2>&1 | Select-Object -First 1).ToString()
$PopplerVersion = [regex]::Match($PopplerLine, 'version\s+([0-9.]+)').Groups[1].Value

$Actual = [ordered]@{
    schema = "sodif.toolchain-observation/v1"
    verified_at = [DateTime]::UtcNow.ToString("o")
    python = $PythonVersion
    packages = [ordered]@{
        PyMuPDF = $Packages.PyMuPDF
        streamlit = $Packages.streamlit
        "streamlit-pdf" = $Packages.'streamlit-pdf'
    }
    tesseract = [ordered]@{
        executable = $Tesseract
        version = $TesseractVersion
        languages = @($Languages)
        oem = 1
        preserve_interword_spaces = $true
    }
    poppler = [ordered]@{
        executable = $PdfToPpm
        pdftoppm_version = $PopplerVersion
    }
}

$Differences = [System.Collections.Generic.List[string]]::new()
if ($Actual.python -ne $Lock.python) {
    $Differences.Add("Python: așteptat $($Lock.python), detectat $($Actual.python)")
}
foreach ($Name in $Lock.packages.PSObject.Properties.Name) {
    if ($Actual.packages[$Name] -ne $Lock.packages.$Name) {
        $Differences.Add("$Name`: așteptat $($Lock.packages.$Name), detectat $($Actual.packages[$Name])")
    }
}
if ($Actual.tesseract.version -ne $Lock.tesseract.version) {
    $Differences.Add("Tesseract: așteptat $($Lock.tesseract.version), detectat $($Actual.tesseract.version)")
}
foreach ($Language in $Lock.tesseract.languages) {
    if ($Language -notin $Actual.tesseract.languages) {
        $Differences.Add("Tesseract: lipsește limba $Language")
    }
}
if ($Actual.poppler.pdftoppm_version -ne $Lock.poppler.pdftoppm_version) {
    $Differences.Add("Poppler: așteptat $($Lock.poppler.pdftoppm_version), detectat $($Actual.poppler.pdftoppm_version)")
}

$Result = [ordered]@{
    status = if ($Differences.Count -eq 0) { "conform" } else { "neconform" }
    lock = $Lock
    actual = $Actual
    differences = @($Differences)
}
$Json = $Result | ConvertTo-Json -Depth 10
if ($OutputPath) {
    $Directory = Split-Path -Parent $OutputPath.FullName
    if ($Directory) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }
    Set-Content -LiteralPath $OutputPath.FullName -Value $Json -Encoding utf8
}
$Json
if ($Differences.Count -gt 0) {
    throw "Toolchain-ul nu corespunde versiunilor fixate."
}
