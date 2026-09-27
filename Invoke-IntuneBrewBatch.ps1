#requires -Version 7.0
<#
.SYNOPSIS
Deploy catalog apps to multiple tenants using isolated PowerShell processes.
.DESCRIPTION
The manifest contains names and paths to existing IntuneBrew authentication configurations.
Use -WhatIf to validate the plan without authenticating or deploying.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$TenantManifest,
    [string[]]$Upload,
    [switch]$UpdateAll,
    [ValidateRange(1, 10)][int]$ThrottleLimit = 3,
    [string]$SummaryPath = './intunebrew-batch-summary.json',
    [string]$IntuneBrewPath = (Join-Path $PSScriptRoot 'IntuneBrew.ps1'),
    [switch]$UseExistingIntuneApp,
    [switch]$PreserveAssignments
)
$ErrorActionPreference = 'Stop'
if ([bool]$Upload -eq [bool]$UpdateAll) { throw 'Specify either -Upload or -UpdateAll.' }
$manifestPath = (Resolve-Path -LiteralPath $TenantManifest).Path
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$scriptPath = (Resolve-Path -LiteralPath $IntuneBrewPath).Path
$summaryFile = [IO.Path]::GetFullPath($SummaryPath)
$seenNames = @{}
$seenTenants = @{}
$plan = @($manifest.tenants | ForEach-Object {
    $name = [string]$_.name
    if ($name -notmatch '^[A-Za-z0-9][A-Za-z0-9 _.-]{0,79}$' -or $seenNames.ContainsKey($name)) {
        throw 'Each tenant needs a unique name (1-80 letters, numbers, spaces, dots, underscores or hyphens).'
    }
    $seenNames[$name] = $true
    if (-not $_.configFile) { throw "Missing configFile for $name." }
    $configPath = [string]$_.configFile
    if (-not [IO.Path]::IsPathRooted($configPath)) { $configPath = Join-Path (Split-Path $manifestPath) $configPath }
    $configPath = (Resolve-Path -LiteralPath $configPath).Path
    $auth = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $tenantId = [guid]::Empty
    if (-not [guid]::TryParse([string]$auth.tenantId, [ref]$tenantId) -or $tenantId -eq [guid]::Empty) {
        throw "A tenant GUID is required in the authentication configuration for $name."
    }
    if ($seenTenants.ContainsKey($tenantId.ToString())) { throw "Duplicate tenant configuration for $name." }
    $seenTenants[$tenantId.ToString()] = $true
    if (-not ($auth.appId -or $auth.clientId)) { throw "An appId or clientId is required for $name." }
    if (-not ($auth.clientSecret -or $auth.certificateThumbprint)) { throw "App-only authentication is required for $name." }
    [PSCustomObject]@{ Name = $name; ConfigFile = $configPath }
})
if (-not $plan.Count) { throw 'The manifest must contain at least one tenant.' }
$approved = @($plan | Where-Object { $PSCmdlet.ShouldProcess($_.Name, 'Deploy the selected IntuneBrew apps') })
if (-not $approved.Count) { return }
$runner = Join-Path $PSScriptRoot 'scripts/Invoke-IntuneBrewTenant.ps1'
$executable = (Get-Process -Id $PID).Path
$options = @{ NonInteractive = $true; UseExistingIntuneApp = [bool]$UseExistingIntuneApp; PreserveAssignments = [bool]$PreserveAssignments }
if ($UpdateAll) { $options.UpdateAll = $true } else { $options.Upload = @($Upload) }
$results = @($approved | ForEach-Object -Parallel {
    $tenant = $_
    $directory = Join-Path ([IO.Path]::GetTempPath()) ('IntuneBrewBatch-' + [guid]::NewGuid())
    $started = [DateTime]::UtcNow
    $exitCode = 1
    try {
        [IO.Directory]::CreateDirectory($directory) | Out-Null
        $invocation = Join-Path $directory 'invocation.json'
        $parameters = @{} + $using:options
        $parameters.ConfigFile = $tenant.ConfigFile
        @{ ScriptPath = $using:scriptPath; Parameters = $parameters; WorkingDirectory = $directory } |
            ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $invocation
        # Do not aggregate child output, which may contain tenant or credential details.
        & $using:executable -NoProfile -NonInteractive -File $using:runner -InvocationPath $invocation *> $null
        $exitCode = $LASTEXITCODE
    }
    catch { $exitCode = 1 }
    finally {
        if (Test-Path -LiteralPath $directory) { Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue }
    }
    [PSCustomObject]@{
        Tenant = $tenant.Name
        Status = $(if ($exitCode -eq 0) { 'Succeeded' } else { 'Failed' })
        ExitCode = $exitCode
        DurationSeconds = [math]::Round(([DateTime]::UtcNow - $started).TotalSeconds, 1)
    }
} -ThrottleLimit $ThrottleLimit)
$results = @($results | Sort-Object Tenant)
@{ schemaVersion = 1; completedAt = [DateTime]::UtcNow.ToString('o'); tenants = $results } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryFile
$results | Format-Table Tenant, Status, ExitCode, DurationSeconds
if ($results.Status -contains 'Failed') {
    Write-Warning 'Some tenants failed. Re-run IntuneBrew with the affected configuration to inspect its diagnostics.'
    exit 1
}
