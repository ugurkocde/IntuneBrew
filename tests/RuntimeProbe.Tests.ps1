$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'RunbookSecurity.RuntimeProbe.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Runtime probe parse failure.' }
foreach ($name in @('Get-CveProbeSourceUri', 'Confirm-CveProbeSource', 'Import-CveProbeFunctions',
        'Get-CveProbeMemorySnapshot', 'Assert-CveProbeMemoryMetrics', 'Get-CveProbeReport')) {
    $fn = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    Invoke-Expression $fn.Extent.Text
}
function Assert-Refused([scriptblock]$Action) {
    $threw = $false; try { $null = & $Action } catch { $threw = $true }
    if (-not $threw) { throw 'Unsafe probe input was accepted.' }
}
$revision = 'a' * 40
if ((Get-CveProbeSourceUri $revision) -cne ('https://raw.githubusercontent.com/ugurkocde/IntuneBrew/' + $revision + '/IntuneBrew_Runbook.ps1')) { throw 'Wrong immutable source route.' }
foreach ($bad in @('main', '../main', ('A' * 40), ($revision + "`n"), ($revision + '?token=test'))) { Assert-Refused { Get-CveProbeSourceUri $bad } }
$bytes = [Text.Encoding]::UTF8.GetBytes('fixture-only')
$hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
if ((Confirm-CveProbeSource $bytes $hash) -cne 'fixture-only') { throw 'Pinned bytes rejected.' }
Assert-Refused { Confirm-CveProbeSource $bytes ('0' * 64) }
Assert-Refused { Confirm-CveProbeSource ([byte[]]::new(2MB + 1)) $hash }
Assert-Refused { Confirm-CveProbeSource $bytes ($hash + "`n") }
$invalid = [byte[]]@(0xff); $invalidHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($invalid)).ToLowerInvariant()
Assert-Refused { Confirm-CveProbeSource $invalid $invalidHash }
$product = [IO.File]::ReadAllText((Join-Path $root 'IntuneBrew_Runbook.ps1'))
# A top-level product action must never execute while helpers are imported.
Import-CveProbeFunctions ($product + "`nthrow 'Product top-level code executed'`n")
$fixture = @{ cve_id = 'CVE-2026-12345'; severity = 'HIGH'; affected_version_start = '5.8.2'; affected_version_start_type = 'including' }
$impact = Get-CveUpdateImpact '5.8.1' '5.8.2(095C)' @($fixture) -HoldLevel High
if (-not $impact.Held -or $impact.Records[0].Classification -ne 'Introduced') { throw 'Imported actual helper failed.' }
Assert-Refused { Import-CveProbeFunctions ($product + "`nfunction Get-CveComparableVersion {}") }
Assert-Refused { Import-CveProbeFunctions 'function Get-CveComparableVersion {}' }
# Run the real report code with fake process/module/feed inputs; no network or Graph.
function Import-Module {
    param($Name, $RequiredVersion, $ErrorAction)
    if ($Name -cne 'Microsoft.Graph.Authentication' -or $RequiredVersion -ne '2.26.0') { throw 'Unexpected module import.' }
}
function Get-Module { param($Name) return [pscustomobject]@{ Version = [version]'2.26.0' } }
$validBaseline = @{ IsWindows = $true; OSDescription = 'Windows TEST-ONLY'; WorkingSetBytes = 200MB; PeakWorkingSetBytes = 220MB; PrivateMemoryBytes = 210MB; PeakCommitBytes = 230MB }
$validFinal = @{ IsWindows = $true; OSDescription = 'Windows TEST-ONLY'; WorkingSetBytes = 210MB; PeakWorkingSetBytes = 250MB; PrivateMemoryBytes = 220MB; PeakCommitBytes = 270MB }
Assert-CveProbeMemoryMetrics $validBaseline $validFinal
foreach ($case in @(@('WorkingSetBytes', 0), @('PeakWorkingSetBytes', 0), @('PrivateMemoryBytes', 0), @('PeakCommitBytes', 0),
        @('PeakWorkingSetBytes', 205MB), @('PeakCommitBytes', 225MB), @('PeakCommitBytes', 215MB), @('IsWindows', $false), @('OSDescription', ''))) {
    $bad = $validFinal.Clone(); $bad[$case[0]] = $case[1]
    Assert-Refused { Assert-CveProbeMemoryMetrics $validBaseline $bad }
}
foreach ($case in @(@('WorkingSetBytes', 0), @('PeakWorkingSetBytes', 190MB), @('PeakCommitBytes', 0), @('IsWindows', $false))) {
    $bad = $validBaseline.Clone(); $bad[$case[0]] = $case[1]
    Assert-Refused { Assert-CveProbeMemoryMetrics $bad $validFinal }
}
$actualHost = Get-CveProbeMemorySnapshot
if (-not $actualHost.IsWindows) { Assert-Refused { Assert-CveProbeMemoryMetrics $actualHost $actualHost } }
$script:sampleOrdinal = 0; $script:reportedPeakCommit = 270MB; $script:badBaseline = $false
function Get-CveProbeMemorySnapshot {
    $script:sampleOrdinal++
    if ($script:sampleOrdinal % 2 -eq 1) {
        $sample = $validBaseline.Clone()
        if ($script:badBaseline) { $sample.WorkingSetBytes = 0 }
        return $sample
    }
    $sample = $validFinal.Clone(); $sample.PeakCommitBytes = $script:reportedPeakCommit
    return $sample
}
function Invoke-CveDataRequest {
    param($Uri)
    if ($Uri -cne 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/CVE-Holds/google_chrome.json') { throw 'Unexpected transport route.' }
    return @{ StatusCode = 200; Content = '{"test":"fixture-only"}' }
}
$script:feedReason = 'assessed'; $script:feedRecords = 2; $script:feedCalls = 0
function Get-RunbookCveAssessment {
    param($JsonUrl, $CurrentVersion, $TargetVersion)
    if ($JsonUrl -cne 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/google_chrome.json' -or $CurrentVersion -ne '0.0.0' -or $TargetVersion -ne '1.0.0') { throw 'Unexpected feed request.' }
    $null = Invoke-CveDataRequest 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/CVE-Holds/google_chrome.json'
    $script:feedCalls++
    $records = @(); for ($i = 0; $i -lt $script:feedRecords; $i++) { $records += 'fake' }
    return [pscustomobject]@{ Reason = $script:feedReason; SourceDigest = ('a' * 64); Impact = [pscustomobject]@{ Records = $records } }
}
$report = Get-CveProbeReport $revision $hash
if ($report.Revision -cne $revision -or $report.RunbookSha256 -cne $hash -or $report.DecoratedIntroducedHoldsPassed -ne 3 -or
    $report.PeakWorkingSetMiB -ne 250 -or $report.PrivateMemoryMiB -ne 220 -or $report.PeakCommitMiB -ne 270 -or
    $report.FeedWorkingSetGrowthMiB -ne 50 -or $report.FeedPeakCommitGrowthMiB -ne 40 -or $report.FeedBytes -ne 23 -or
    -not $report.MeetsMemoryThreshold -or $report.AcceptancePeakLimitMiB -ne 300 -or $report.OSDescription -ne 'Windows TEST-ONLY' -or
    $report.VulnerabilityRecords -ne 2 -or $report.GraphModuleVersion -ne '2.26.0' -or $script:feedCalls -ne 1) { throw 'Runtime measurement report lost its source/runtime/hold binding.' }
$script:reportedPeakCommit = 301MB
$over = Get-CveProbeReport $revision $hash
if ($over.MeetsMemoryThreshold -or $over.MaximumPeakMiB -ne 301) { throw 'Over-threshold peak commit became a pass.' }
$script:reportedPeakCommit = 270MB
$script:sampleOrdinal = 0; $script:badBaseline = $true; $before = $script:feedCalls
Assert-Refused { Get-CveProbeReport $revision $hash }
if ($script:feedCalls -ne $before -or $script:CveProbeStage -ne 'metrics') { throw 'Bad baseline reached the feed or lost its stage.' }
$script:sampleOrdinal = 0; $script:badBaseline = $false
$script:feedReason = 'data-error'
Assert-Refused { Get-CveProbeReport $revision $hash }
if ($script:CveProbeStage -ne 'feed') { throw 'Data-error feed did not fail at the feed stage.' }
$script:sampleOrdinal = 0
$script:feedReason = 'assessed'; $script:feedRecords = 0
Assert-Refused { Get-CveProbeReport $revision $hash }
if ($script:CveProbeStage -ne 'feed') { throw 'Empty-record feed did not fail at the feed stage.' }
# Exercise the actual imported assessment -> instrumented transport -> schema -> evaluator chain.
Import-CveProbeFunctions $product
function Invoke-CveDataRequest {
    param($Uri)
    if ($Uri -cne 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/CVE-Holds/google_chrome.json') { throw 'Unexpected real-chain route.' }
    return @{ StatusCode = 200; Content = ('{"schema_version":1,"app_key":"google_chrome","source_sha256":"' + ('a' * 64) + '","vulnerabilities":[{"cve_id":"CVE-2026-12345","severity":"HIGH","affected_version_start":"1","affected_version_start_type":"including"}]}') }
}
$script:sampleOrdinal = 0
$chain = Get-CveProbeReport $revision $hash
if (-not $chain.LiveFeedAssessed -or $chain.SourceDigest -cne ('a' * 64) -or $chain.FeedFormat -cne 'compact-v1' -or $chain.VulnerabilityRecords -ne 1 -or $chain.FeedBytes -le 0 -or
    -not $chain.MeetsMemoryThreshold -or $chain.DecoratedIntroducedHoldsPassed -ne 3) { throw 'Actual assessment chain or byte instrumentation failed.' }
Write-Host 'Runtime probe immutable-source, digest, strict UTF-8, helper isolation and actual report controls passed.'
