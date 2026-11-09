$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../IntuneBrew.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$statements = @($ast.EndBlock.Statements)
$loops = @($statements | Where-Object {
    $_ -is [System.Management.Automation.Language.ForEachStatementAst] -and
    $_.Condition.Extent.Text -eq '$appsToUpload' -and $_.Body.Extent.Text.Contains('Get-AppFile')
})
if ($loops.Count -ne 1) { throw 'Expected one production catalog upload loop.' }
$loop = $loops[0]
$initializers = foreach ($name in @('existingAssignments', 'updateSummaries', 'uploadFailures')) {
    $statements | Where-Object {
        $_ -is [System.Management.Automation.Language.AssignmentStatementAst] -and
        $_.Left -is [System.Management.Automation.Language.VariableExpressionAst] -and
        $_.Left.VariablePath.UserPath -eq $name -and $_.Extent.StartOffset -lt $loop.Extent.StartOffset
    } | Select-Object -Last 1
}
$production = (@($initializers) + @($statements | Where-Object { $_.Extent.StartOffset -ge $loop.Extent.StartOffset }) |
    ForEach-Object { $_.Extent.Text }) -join "`n"

# The renaming logic normally normalizes unknown extensions before this branch.
# Exercise the actual defensive else block directly, without copying its logic.
$typeCheck = $loop.Find({ param($n) $n -is [System.Management.Automation.Language.IfStatementAst] -and
    $n.ElseClause -and $n.ElseClause.Extent.Text.Contains('Unsupported installer type.') }, $true)
if (-not $typeCheck) { throw 'Unsupported installer guard missing.' }
$unsupportedFailed = $false
$NonInteractive = $false; $fileExtension = '.unsupported'
foreach ($fixture in @(1)) {
    try { & ([scriptblock]::Create($typeCheck.ElseClause.Extent.Text.Trim().TrimStart('{').TrimEnd('}'))) }
    catch { $unsupportedFailed = $true }
}
if (-not $unsupportedFailed) { throw 'Unsupported installers must fail in interactive mode.' }

$prefix = @'
param([string]$Scenario, [string]$FixtureDirectory)
$ErrorActionPreference = if ($Scenario -like 'noninteractive*') { 'Stop' } else { 'Continue' }
$script:ExpectedPreference = [string]$ErrorActionPreference
$NonInteractive = $Scenario -like 'noninteractive*'
$heldApps = if ($Scenario -in @('held', 'failure-held')) { @('Fake held app') } else { @() }
$copyAssignments = $false
$updateExistingIntuneApp = $Scenario -eq 'existing-content-error'
$ScopeTagIds = @()
$script:Calls = @(); $script:Finalized = @(); $script:LocalCleanup = @()
$script:FilesStarted = 0; $script:Committed = $false; $script:Sleeps = 0
$appsToUpload = @(foreach ($index in 1..$(if ($Scenario -eq 'noninteractive-second-failure') { 3 } elseif ($Scenario -in @('mixed', 'missing-second-id', 'noninteractive')) { 2 } else { 1 })) {
    $name = "Fake app $index"
    [pscustomobject]@{ Name=$name; FormattedName=$name; IntuneVersion='Not in Intune';
        IntuneAppId=$(if ($updateExistingIntuneApp) { 'fake-existing-app' } else { $null });
        Manifest=@{name=$name; version='1.0'; bundleId='com.example.fake'; fileName="fake-$index.dmg";
            url='https://example.invalid/fake.dmg'; sha=('f'*64); description='Fake';
            homepage='https://example.invalid'; localManifestDirectory=$FixtureDirectory} }
})
function Get-AppFile {
    param($url,$fileName,$expectedHash,$localManifestDirectory)
    $script:FilesStarted++; $script:ActiveName = "Fake app $script:FilesStarted"
    $path = Join-Path $FixtureDirectory $fileName
    [IO.File]::WriteAllText($path, 'fake installer')
    return $path
}
function Set-IntuneVersionDetection { param($Payload,$Options) }
function Invoke-MgGraphRequest {
    [CmdletBinding()] param($Method,$Uri,$Body)
    $script:Calls += [pscustomobject]@{Method=$Method; Uri=$Uri}
    if ($Uri -match 'mobileApps//|contentVersions//|files//') { throw 'Dependent request used an empty ID.' }
    if ($Method -eq 'DELETE') { return }
    if ($Uri -eq 'https://graph.microsoft.com/beta/deviceAppManagement/mobileApps') {
        if ($Scenario -in @('create-rejection','failure-held','noninteractive') -or
            ($Scenario -eq 'mixed' -and $script:FilesStarted -eq 1) -or
            ($Scenario -eq 'noninteractive-second-failure' -and $script:FilesStarted -eq 2)) { Write-Error 'FAKE creation rejected'; return }
        if ($Scenario -eq 'missing-app-id' -or ($Scenario -eq 'missing-second-id' -and $script:FilesStarted -eq 2)) { return @{} }
        $script:Committed = $false
        return @{id="fake-app-$script:FilesStarted"}
    }
    if ($Uri -match '/contentVersions$') {
        if ($Scenario -in @('content-error','existing-content-error')) { Write-Error 'FAKE content rejected'; return }
        if ($Scenario -eq 'missing-version-id') { return @{} }
        return @{id='fake-version'}
    }
    if ($Uri -match '/files$') {
        if ($Scenario -eq 'missing-file-id') { return @{} }
        return @{id='fake-file'}
    }
    if ($Uri -match '/commit$') {
        if ($Scenario -eq 'commit-error') { Write-Error 'FAKE commit rejected'; return }
        $script:Committed = $true; return
    }
    if ($Method -eq 'GET') {
        if ($Scenario -eq 'poll-error' -or ($Scenario -eq 'post-commit-poll-error' -and $script:Committed)) { Write-Error 'FAKE poll rejected'; return }
        return @{uploadState=$(if ($script:Committed -and $Scenario -eq 'commit-state-failure') { 'commitFileFailed' }
            elseif ($script:Committed) { 'commitFileSuccess' } else { 'azureStorageUriRequestSuccess' });
            azureStorageUri='https://example.invalid/fake-storage'}
    }
    if ($Method -eq 'PATCH') {
        if ($Scenario -eq 'patch-error') { Write-Error 'FAKE finalization rejected'; return }
        $script:Finalized += $script:ActiveName; return
    }
    throw 'Unexpected fake Graph request.'
}
function EncryptFile { param($sourceFile); [IO.File]::WriteAllText("$sourceFile.bin", 'fake encrypted bytes'); return @{fake='encryption'} }
function UploadFileToAzureStorage { param($sasUri,$filepath) }
function Start-Sleep { param($Seconds); $script:Sleeps++; if ($script:Sleeps -gt 25) { throw 'Fake poll bound exceeded.' } }
function Remove-LocalAppFile { param($Path); $script:LocalCleanup += $Path }
function Disconnect-MgGraph { $script:Disconnected = $true }
function Format-TimeSpanForSummary { param($TimeSpan); return '0 seconds' }
function Add-IntuneAppLogo {
    param($appId,$appName,$appType,$localLogoPath)
    if ($Scenario -eq 'optional-error') { throw 'FAKE optional logo error' }
}
try { & {
'@
$suffix = @'
} }
finally {
    @{Calls=@($script:Calls); Finalized=@($script:Finalized); LocalCleanup=@($script:LocalCleanup);
      Preference=[string]$ErrorActionPreference; ExpectedPreference=$script:ExpectedPreference;
      FilesStarted=$script:FilesStarted; Disconnected=($script:Disconnected -eq $true)} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $FixtureDirectory 'receipt.json')
}
'@
$root = Join-Path ([IO.Path]::GetTempPath()) ('intunebrew-reporting-' + [guid]::NewGuid())
[IO.Directory]::CreateDirectory($root) | Out-Null
try {
    $child = Join-Path $root 'scenario.ps1'
    Set-Content -LiteralPath $child -Value ($prefix + "`n" + $production + "`n" + $suffix)
    $executable = (Get-Process -Id $PID).Path
    foreach ($scenario in @('create-rejection','missing-app-id','missing-version-id','missing-file-id',
        'content-error','existing-content-error','commit-error','commit-state-failure','poll-error','post-commit-poll-error','patch-error','mixed',
        'missing-second-id','success','held','failure-held','noninteractive','noninteractive-second-failure','optional-error')) {
        $directory = Join-Path $root $scenario
        [IO.Directory]::CreateDirectory($directory) | Out-Null
        $output = & $executable -NoLogo -NoProfile -File $child -Scenario $scenario -FixtureDirectory $directory 2>&1 | Out-String
        $code = $LASTEXITCODE
        $receipt = Get-Content -LiteralPath (Join-Path $directory 'receipt.json') -Raw | ConvertFrom-Json
        $expected = if ($scenario -in @('success','optional-error')) { 0 } elseif ($scenario -eq 'held') { 2 } else { 1 }
        if ($code -ne $expected) { throw "$scenario exit $code instead of $expected : $output" }
        if ($receipt.Preference -ne $receipt.ExpectedPreference) { throw "$scenario changed caller error preference." }
        if ($receipt.LocalCleanup.Count -ne $receipt.FilesStarted) { throw "$scenario skipped finally cleanup." }
        if (@($receipt.Calls | Where-Object Uri -Match 'mobileApps//|contentVersions//|files//').Count) { throw "$scenario made a dependent request with an empty ID." }
        if ($expected -ne 0 -and $output.Contains('All operations completed successfully!')) { throw "$scenario printed false overall success." }
        $deletes = @($receipt.Calls | Where-Object Method -eq 'DELETE')
        if ($scenario -in @('missing-version-id','missing-file-id','content-error','poll-error')) {
            if ($deletes.Count -ne 1 -or $deletes[0].Uri -notmatch '/fake-app-1$') { throw "$scenario did not clean only the new incomplete app." }
        }
        elseif ($deletes.Count) { throw "$scenario deleted an existing/committed/uncreated app." }
        if ($scenario -in @('create-rejection','missing-app-id','failure-held','noninteractive')) {
            if ($receipt.Calls.Count -ne 1 -or $output.Contains('App created successfully')) { throw "$scenario continued after failed creation." }
        }
        if ($scenario -eq 'mixed' -and ($receipt.Finalized -join ',') -ne 'Fake app 2') { throw 'Mixed batch did not process the good app.' }
        if ($scenario -in @('commit-error','poll-error') -and @($receipt.Calls | Where-Object Method -eq 'GET').Count -ne 1) { throw "$scenario continued polling after a rejected critical request." }
        if ($scenario -eq 'commit-state-failure' -and @($receipt.Calls | Where-Object Uri -Match '/commit$').Count -ne 11) { throw 'Existing commit retry bound changed.' }
        if ($scenario -eq 'missing-second-id' -and ($receipt.Finalized -join ',') -ne 'Fake app 1') { throw 'Second app reused a stale ID.' }
        if ($scenario -eq 'success' -and ($receipt.Finalized.Count -ne 1 -or -not $output.Contains('All operations completed successfully!'))) { throw 'Successful upload reporting regressed.' }
        if ($scenario -eq 'noninteractive' -and $receipt.FilesStarted -ne 1) { throw 'Noninteractive failure did not stop immediately.' }
        if ($scenario -like 'noninteractive*' -and -not $receipt.Disconnected) { throw 'Noninteractive failure skipped disconnect.' }
        if ($scenario -eq 'noninteractive-second-failure' -and ($receipt.FilesStarted -ne 2 -or ($receipt.Finalized -join ',') -ne 'Fake app 1' -or -not $output.Contains('Fake app 1 (version 1.0) was uploaded'))) { throw 'Noninteractive failure lost the earlier successful summary or processed another app.' }
        if ($scenario -eq 'failure-held' -and $output.Contains('other selected updates completed')) { throw 'Held message masked a failed upload.' }
    }
    Write-Host 'Catalog upload failure-reporting regression tests passed (19 child scenarios plus unsupported guard).'
}
finally { Remove-Item -LiteralPath $root -Recurse -Force }
