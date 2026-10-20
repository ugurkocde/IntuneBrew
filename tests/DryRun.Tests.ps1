$ErrorActionPreference = 'Stop'
$sourcePath = Join-Path $PSScriptRoot '../IntuneBrew.ps1'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($sourcePath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
if ('DryRun' -notin $ast.ParamBlock.Parameters.Name.VariablePath.UserPath) { throw 'DryRun parameter is missing.' }
$functions = foreach ($name in @('Compare-VersionSegments', 'Test-NewerVersion')) {
    $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true).Extent.Text
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
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $output = (& pwsh -NoProfile -NonInteractive -OutputFormat Text -EncodedCommand $encoded 2>&1 | Out-String)
    if ($LASTEXITCODE -ne $case.ExitCode) { throw "Unexpected dry-run exit code: $LASTEXITCODE`n$output" }
    foreach ($expected in @($case.Summary, $case.Expected, 'No installers downloaded', 'DISCONNECTED')) {
        if ($expected -and -not $output.Contains($expected)) { throw "Missing '$expected':`n$output" }
    }
    foreach ($excluded in @('Current:', 'Absent:', 'VPP:', 'Unexpected', 'did not exit')) {
        if ($output.Contains($excluded)) { throw "Unexpected '$excluded':`n$output" }
    }
}
Write-Host 'Dry-run selection, version filtering, security holds, and deployment isolation passed.'