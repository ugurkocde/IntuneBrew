$ErrorActionPreference = 'Stop'

function Invoke-GeneratedScript {
    param([Parameter(Mandatory)][string]$Command)
    $path = Join-Path ([IO.Path]::GetTempPath()) "IntuneBrew-DryRunTest-$([guid]::NewGuid().ToString('N')).ps1"
    $created = $false
    try {
        $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $created = $true
        $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
        try { $writer.Write($Command) } finally { $writer.Dispose() }
        $output = (& pwsh -NoProfile -NonInteractive -OutputFormat Text -File $path 2>&1 | Out-String)
        [pscustomobject]@{ Output = $output; ExitCode = $LASTEXITCODE }
    }
    finally {
        if ($created) { Remove-Item -LiteralPath $path -Force }
    }
}

$sourcePath = Join-Path $PSScriptRoot '../IntuneBrew.ps1'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($sourcePath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
if ('DryRun' -notin $ast.ParamBlock.Parameters.Name.VariablePath.UserPath) { throw 'DryRun parameter is missing.' }
$functions = foreach ($name in @('Compare-VersionSegments', 'Test-NewerVersion')) {
    $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
    if (-not $definition) { throw "Required function not found: $name" }
    $definition.Extent.Text
}
$guard = $ast.EndBlock.Statements | Where-Object { $_.Extent.Text.StartsWith('if ($DryRun -and') } | Select-Object -First 1
if (-not $guard) { throw 'DryRun selection validation is missing.' }
foreach ($options in @(@{ UpdateAll = $false }, @{ UpdateAll = $true; Upload = 'example' }, @{ UpdateAll = $true; LocalFile = $true })) {
    $rejected = $false
    try {
        & {
            $DryRun = $true; $UpdateAll = $options.UpdateAll; $Upload = $options.Upload; $LocalFile = $options.LocalFile
            Invoke-Expression $guard.Extent.Text
        }
    }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'Unsafe DryRun selection was accepted.' }
}
$source = $ast.Extent.Text
$tail = $source.Substring($source.IndexOf('Write-Host "Fetching current Intune app versions..."'))
$fixture = @(
    @{ FormattedName = 'Update Me'; IntuneVersion = '1.0'; GitHubVersion = '2.0'; SecurityHeld = $false },
    @{ FormattedName = 'Current'; IntuneVersion = '2.0'; GitHubVersion = '2.0'; SecurityHeld = $false },
    @{ FormattedName = 'Absent'; IntuneVersion = 'Not in Intune'; GitHubVersion = '2.0'; SecurityHeld = $false },
    @{ FormattedName = 'VPP'; IntuneVersion = 'Managed via VPP'; GitHubVersion = '2.0'; SecurityHeld = $false },
    @{ FormattedName = 'Held'; IntuneVersion = '1.0'; GitHubVersion = '2.0'; SecurityHeld = $true }
)
foreach ($case in @(
    @{ Apps = $fixture; ExitCode = 2; Summary = '1 available update(s), 1 held'; Expected = 'Update Me: 1.0 -> 2.0' },
    @{ Apps = @($fixture[0]); ExitCode = 0; Summary = '1 available update(s), 0 held'; Expected = 'Update Me: 1.0 -> 2.0' },
    @{ Apps = @($fixture[1]); ExitCode = 0; Summary = '0 available update(s), 0 held'; Expected = '' },
    @{ Apps = @($fixture[4]); ExitCode = 2; Summary = '0 available update(s), 1 held'; Expected = 'HELD: Held' }
)) {
    $json = ConvertTo-Json -InputObject @($case.Apps) -Compress
    $command = @"
`$ErrorActionPreference = 'Stop'
`$UpdateAll = `$true; `$DryRun = `$true; `$PreserveAssignments = [switch]`$true
function Get-IntuneApp { ConvertFrom-Json '$json' }
function Disconnect-MgGraph { Write-Host 'DISCONNECTED' }
function Invoke-MgGraphRequest { throw 'Unexpected Graph request' }
function Invoke-WebRequest { throw 'Unexpected download' }
function Get-IntuneAppAssignment { throw 'Unexpected assignment processing' }
$($functions -join "`n")
$tail
throw 'DryRun did not exit before deployment'
"@
    $result = Invoke-GeneratedScript -Command $command
    $output = $result.Output
    if ($result.ExitCode -ne $case.ExitCode) { throw "Unexpected dry-run exit code: $($result.ExitCode)`n$output" }
    foreach ($expected in @($case.Summary, $case.Expected, 'No installers downloaded', 'DISCONNECTED')) {
        if ($expected -and -not $output.Contains($expected)) { throw "Missing '$expected':`n$output" }
    }
    foreach ($excluded in @('  Current:', '  Absent:', '  VPP:', 'Unexpected', 'did not exit')) {
        if ($output.Contains($excluded)) { throw "Unexpected '$excluded':`n$output" }
    }
}
$lookup = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Get-IntuneApp' }, $true)
if (-not $lookup) { throw 'Required function not found: Get-IntuneApp' }
$failurePolicy = $ast.EndBlock.Statements | Where-Object {
    $_ -is [System.Management.Automation.Language.IfStatementAst] -and $_.Extent.Text.Contains('$ErrorActionPreference = "Stop"')
} | Select-Object -First 1
if (-not $failurePolicy) { throw 'Error handling policy not found.' }
foreach ($scenario in @('invalid-url', 'metadata', 'graph', 'vpp', 'graph-nonterminating')) {
    $command = @"
`$ErrorActionPreference = 'Continue'
`$UpdateAll = `$true; `$DryRun = `$true; `$NonInteractive = `$false
$($failurePolicy.Extent.Text)
`$githubJsonUrls = @('https://example.test/fixture.json')
function Test-ValidUrl { '$scenario' -ne 'invalid-url' }
function Get-GitHubAppInfo {
    if ('$scenario' -eq 'metadata') { return `$null }
    return @{ name = 'Fixture'; version = '2.0' }
}
function Get-FormattedAppName { param(`$BaseName) `$BaseName }
function Get-IntuneAppCollection {
    param(`$Filter)
    if ('$scenario' -eq 'vpp' -and `$Filter -notmatch 'macOsVppApp') { return @{ value = @() } }
    if ('$scenario' -eq 'graph-nonterminating') {
        Write-Error 'Simulated Graph lookup failure'
        return @{ value = @() }
    }
    throw 'Simulated Graph lookup failure'
}
function Disconnect-MgGraph { }
$($lookup.Extent.Text)
$tail
"@
    $result = Invoke-GeneratedScript -Command $command
    $output = $result.Output
    if ($result.ExitCode -eq 0) { throw "DryRun reported success after $scenario lookup failure:`n$output" }
    if ($output.Contains('0 available update(s)')) { throw "DryRun reported a clean scan after $scenario failure." }
    $expected = if ($scenario -in @('invalid-url', 'metadata')) { 'https://example.test/fixture.json' } else { 'Simulated Graph lookup failure' }
    if (-not $output.Contains($expected)) { throw "Lookup error context missing for ${scenario}:`n$output" }
}
$authStart = $source.IndexOf('$authenticated = $false')
$authEnd = $source.IndexOf('# Authentication END', $authStart)
if ($authStart -lt 0 -or $authEnd -lt 0) { throw 'Authentication test boundary not found.' }
$authSetup = $source.Substring($authStart, $authEnd - $authStart)
$catalogSetup = $ast.EndBlock.Statements | Where-Object {
    $_ -is [System.Management.Automation.Language.TryStatementAst] -and $_.Extent.Text.Contains('$supportedApps = Invoke-RestMethod')
} | Select-Object -First 1
if (-not $catalogSetup) { throw 'Catalog setup test boundary not found.' }
foreach ($scenario in @('invalid-config', 'config-read', 'auth-method', 'auth-failure', 'invalid-choice', 'file-picker', 'app-permissions', 'interactive-permissions', 'catalog-fetch', 'empty-catalog')) {
    foreach ($dryRunMode in @($true, $false)) {
        $setup = if ($scenario -in @('catalog-fetch', 'empty-catalog')) { $catalogSetup.Extent.Text } else { $authSetup }
        $modeLiteral = if ($dryRunMode) { '$true' } else { '$false' }
        $command = @"
`$ErrorActionPreference = 'Continue'
`$DryRun = $modeLiteral; `$NonInteractive = `$false; `$UpdateAll = `$true
`$ConfigFile = if ('$scenario' -in @('invalid-choice', 'file-picker', 'interactive-permissions')) { `$null } else { 'mock-config.json' }
`$requiredPermissions = @('DeviceManagementApps.ReadWrite.All')
`$githubJsonUrls = @(); `$localJsonOverrides = @{}
function Test-AuthConfig { '$scenario' -ne 'invalid-config' }
function Get-Content {
    if ('$scenario' -eq 'config-read') { throw 'Simulated configuration read failure' }
    if ('$scenario' -eq 'auth-method') { return '{"authMethod":"Unsupported"}' }
    return '{"authMethod":"Certificate","tenantId":"11111111-1111-1111-1111-111111111111"}'
}
function Connect-WithCertificate { '$scenario' -ne 'auth-failure' }
function Connect-Interactive { `$true }
function Show-FilePickerDialog { `$null }
function Read-Host {
    param(`$Prompt)
    if ('$scenario' -eq 'file-picker') { return '1' }
    if ('$scenario' -eq 'interactive-permissions' -and `$Prompt -like '*choice*') { return '3' }
    return 'n'
}
function Get-MgContext { [pscustomobject]@{ TenantId = '11111111-1111-1111-1111-111111111111'; Scopes = @() } }
function Invoke-RestMethod {
    if ('$scenario' -eq 'catalog-fetch') { throw 'Simulated catalog fetch failure' }
    return [pscustomobject]@{}
}
$setup
Write-Host 'SETUP_COMPLETED'
"@
        $result = Invoke-GeneratedScript -Command $command
        $output = $result.Output
        $expectedCode = if ($dryRunMode) { 1 } else { 0 }
        if ($result.ExitCode -ne $expectedCode -or $output.Contains('SETUP_COMPLETED')) {
            throw "Incorrect setup failure exit for $scenario (DryRun=$dryRunMode): $($result.ExitCode), expected $expectedCode`n$output"
        }
    }
}
Write-Host 'Dry-run selection, filtering, holds, deployment isolation, lookup failures, and setup failure exits passed.'
