$ErrorActionPreference = 'Stop'
$batch = (Resolve-Path (Join-Path $PSScriptRoot '../Invoke-IntuneBrewBatch.ps1')).Path
$root = Join-Path ([IO.Path]::GetTempPath()) ('batch test ' + [guid]::NewGuid())
[IO.Directory]::CreateDirectory($root) | Out-Null
try {
    $stub = Join-Path $root 'deployment stub.ps1'
    @'
param($ConfigFile, $Upload, [switch]$NonInteractive, [switch]$UpdateAll, [switch]$UseExistingIntuneApp, [switch]$PreserveAssignments)
if (-not $NonInteractive -or $Upload.Count -ne 2) { exit 4 }
if ((Split-Path (Get-Location) -Leaf) -notlike 'IntuneBrewBatch-*') { exit 5 }
$config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
# An exclusive marker proves tenants do not share a working directory.
[IO.File]::Open('exclusive.lock', [IO.FileMode]::CreateNew).Dispose()
Start-Sleep -Milliseconds 100
Write-Output 'sensitive child output must not be aggregated'
exit $config.testExitCode
'@ | Set-Content $stub
    $tenants = @(1..3 | ForEach-Object {
        $path = Join-Path $root "tenant $_.json"
        @{ tenantId = [guid]::NewGuid().ToString(); appId = [guid]::NewGuid().ToString(); clientSecret = 'test-only'; testExitCode = $(if ($_ -eq 2) { 7 } else { 0 }) } | ConvertTo-Json | Set-Content $path
        @{ name = "Tenant $_"; configFile = "tenant $_.json" }
    })
    $manifest = Join-Path $root 'tenants.json'
    @{ tenants = $tenants } | ConvertTo-Json -Depth 4 | Set-Content $manifest
    $summary = Join-Path $root 'summary.json'
    # Use a driver to preserve array parameters across the process boundary.
    $driver = Join-Path $root 'driver.ps1'
    @'
param($Batch, $Manifest, $Stub, $Summary, [switch]$PlanOnly)
& $Batch -TenantManifest $Manifest -IntuneBrewPath $Stub -Upload @('one', 'two') -SummaryPath $Summary -ThrottleLimit 2 -WhatIf:$PlanOnly
exit $LASTEXITCODE
'@ | Set-Content $driver
    $output = & pwsh -NoProfile -File $driver $batch $manifest $stub $summary -PlanOnly 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -or (Test-Path $summary)) { throw 'WhatIf performed a deployment.' }
    $output = & pwsh -NoProfile -File $driver $batch $manifest $stub $summary 2>&1 | Out-String
    if ($LASTEXITCODE -ne 1) { throw 'A partial batch did not fail.' }
    if ($output -match 'sensitive child|test-only') { throw 'Child output or secrets escaped.' }
    $result = Get-Content $summary -Raw | ConvertFrom-Json
    if ($result.tenants.Count -ne 3 -or @($result.tenants | Where-Object Status -eq 'Succeeded').Count -ne 2) { throw ('Incorrect per-tenant results: ' + ($result | ConvertTo-Json -Depth 5)) }
    if (($result.tenants | Where-Object Tenant -eq 'Tenant 2').ExitCode -ne 7) { throw 'Child failure code was lost.' }
    $config = Get-Content (Join-Path $root 'tenant 2.json') -Raw | ConvertFrom-Json
    $config.testExitCode = 0
    $config | ConvertTo-Json | Set-Content (Join-Path $root 'tenant 2.json')
    & pwsh -NoProfile -File $driver $batch $manifest $stub $summary *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Successful batch failed.' }
    $tenants[1].configFile = $tenants[0].configFile
    @{ tenants = $tenants } | ConvertTo-Json -Depth 4 | Set-Content $manifest
    & pwsh -NoProfile -File $driver $batch $manifest $stub $summary -PlanOnly *> $null
    if ($LASTEXITCODE -eq 0) { throw 'Duplicate tenants accepted.' }
    Write-Host 'Batch isolation, partial failure, dry run, and validation tests passed.'
}
finally { Remove-Item $root -Recurse -Force }
