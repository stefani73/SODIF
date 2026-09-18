param(
    [System.IO.DirectoryInfo]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Mediul virtual .venv nu este inițializat."
}

Push-Location $ProjectRoot
try {
    $Version = (& $Python -c "import sodif; print(sodif.__version__)").Trim()
    $ExpectedTag = "v$Version-trl4"
    $Revision = (& git rev-parse HEAD).Trim()
    $CurrentTag = (& git describe --tags --exact-match HEAD 2>$null).Trim()
    if ($CurrentTag -ne $ExpectedTag) {
        throw "Checkout-ul trebuie să fie etichetat exact $ExpectedTag."
    }
    if (& git status --porcelain) {
        throw "Arborele Git trebuie să fie curat înaintea construirii pachetului."
    }

    if (-not $OutputDirectory) {
        $OutputDirectory = [System.IO.DirectoryInfo](Join-Path $ProjectRoot "var\releases")
    }
    New-Item -ItemType Directory -Path $OutputDirectory.FullName -Force | Out-Null
    $ReleaseRoot = Join-Path $OutputDirectory.FullName $ExpectedTag
    if (Test-Path -LiteralPath $ReleaseRoot) {
        throw "Directorul release-ului există deja: $ReleaseRoot"
    }
    New-Item -ItemType Directory -Path $ReleaseRoot | Out-Null
    $EvidenceRoot = Join-Path $ReleaseRoot "evidence"
    $ArchiveRoot = Join-Path $ReleaseRoot "laboratory-archive"
    New-Item -ItemType Directory -Path $EvidenceRoot | Out-Null

    & (Join-Path $PSScriptRoot "verify-toolchain.ps1") -OutputPath (Join-Path $ReleaseRoot "toolchain.actual.json") | Out-Null

    $RuffOutput = @(& $Python -m ruff check . 2>&1)
    $RuffCode = $LASTEXITCODE
    Set-Content -LiteralPath (Join-Path $ReleaseRoot "ruff.log") -Value $RuffOutput -Encoding utf8
    if ($RuffCode -ne 0) { throw "Ruff a eșuat." }

    $MypyOutput = @(& $Python -m mypy src tests 2>&1)
    $MypyCode = $LASTEXITCODE
    Set-Content -LiteralPath (Join-Path $ReleaseRoot "mypy.log") -Value $MypyOutput -Encoding utf8
    if ($MypyCode -ne 0) { throw "mypy a eșuat." }

    $CoveragePath = Join-Path $ReleaseRoot "coverage.json"
    $JunitPath = Join-Path $ReleaseRoot "pytest-results.xml"
    $env:SODIF_ARCHIVE_ROOT = Join-Path $ReleaseRoot "quality-archive"
    $env:SODIF_EXPORT_ROOT = Join-Path $ReleaseRoot "quality-exports"
    $PytestRoot = Join-Path $ReleaseRoot "pytest-temp"
    $PytestOutput = @(& $Python -m pytest --basetemp $PytestRoot --junitxml=$JunitPath --cov-report=json:$CoveragePath 2>&1)
    $PytestCode = $LASTEXITCODE
    Set-Content -LiteralPath (Join-Path $ReleaseRoot "pytest.log") -Value $PytestOutput -Encoding utf8
    if ($PytestCode -ne 0) { throw "pytest a eșuat." }

    $env:SODIF_SOURCE_TAG = $ExpectedTag
    $env:SODIF_SOURCE_REVISION = $Revision
    $ExportJson = & $Python -m sodif.reporting.cli --kind all --output-dir $EvidenceRoot --archive-root $ArchiveRoot
    if ($LASTEXITCODE -ne 0) { throw "Generarea rapoartelor operaționale a eșuat." }
    Set-Content -LiteralPath (Join-Path $ReleaseRoot "flight-export-summary.json") -Value $ExportJson -Encoding utf8

    Copy-Item -LiteralPath "requirements.lock" -Destination (Join-Path $ReleaseRoot "requirements.lock")
    Copy-Item -LiteralPath "pyproject.toml" -Destination (Join-Path $ReleaseRoot "pyproject.toml")
    Copy-Item -LiteralPath "repro\toolchain.lock.json" -Destination (Join-Path $ReleaseRoot "toolchain.lock.json")
    Copy-Item -LiteralPath "repro\README.md" -Destination (Join-Path $ReleaseRoot "REPRODUCERE.md")
    $SourceZip = Join-Path $ReleaseRoot "source.zip"
    & git archive --format=zip "--output=$SourceZip" $ExpectedTag
    if ($LASTEXITCODE -ne 0) { throw "Arhivarea sursei Git a eșuat." }

    $Coverage = Get-Content -LiteralPath $CoveragePath -Raw | ConvertFrom-Json
    [xml]$Junit = Get-Content -LiteralPath $JunitPath -Raw
    $Suite = $Junit.testsuites.testsuite
    $FileRecords = Get-ChildItem -LiteralPath $ReleaseRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
        [ordered]@{
            path = [System.IO.Path]::GetRelativePath($ReleaseRoot, $_.FullName).Replace('\', '/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    $Manifest = [ordered]@{
        schema = "sodif.trl4-release-manifest/v1"
        release = $Version
        tag = $ExpectedTag
        revision = $Revision
        generated_at = [DateTime]::UtcNow.ToString("o")
        quality = [ordered]@{
            tests = [int]$Suite.tests
            failures = [int]$Suite.failures
            errors = [int]$Suite.errors
            skipped = [int]$Suite.skipped
            branch_coverage_percent = [decimal]$Coverage.totals.percent_covered
            required_percent = 85
            ruff = "passed"
            mypy = "passed"
        }
        evidence_set = (Get-Content -LiteralPath (Join-Path $ReleaseRoot "flight-export-summary.json") -Raw | ConvertFrom-Json).evidence_set_id
        files = @($FileRecords)
    }
    $ManifestPath = Join-Path $ReleaseRoot "release-manifest.json"
    Set-Content -LiteralPath $ManifestPath -Value ($Manifest | ConvertTo-Json -Depth 10) -Encoding utf8
    $ManifestHash = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $ReleaseRoot "release-manifest.sha256") -Value "$ManifestHash  release-manifest.json" -Encoding ascii

    $PackagePath = Join-Path $OutputDirectory.FullName "SODIF_$ExpectedTag`_reproduction.zip"
    Compress-Archive -Path (Join-Path $ReleaseRoot "*") -DestinationPath $PackagePath -CompressionLevel Optimal
    $PackageHash = (Get-FileHash -LiteralPath $PackagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath "$PackagePath.sha256" -Value "$PackageHash  $([System.IO.Path]::GetFileName($PackagePath))" -Encoding ascii

    [ordered]@{
        status = "conform"
        tag = $ExpectedTag
        revision = $Revision
        manifest = $ManifestPath
        manifest_sha256 = $ManifestHash
        package = $PackagePath
        package_sha256 = $PackageHash
    } | ConvertTo-Json -Depth 4
}
finally {
    Pop-Location
}
