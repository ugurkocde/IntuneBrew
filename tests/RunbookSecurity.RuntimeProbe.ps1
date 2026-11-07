<# Read-only Azure Automation fixture. Never runs the full Runbook or authenticates to Graph. #>
param(
    [Parameter(Mandatory = $true)][string]$Revision,
    [Parameter(Mandatory = $true)][string]$RunbookSha256
)
$ErrorActionPreference = 'Stop'

function Get-CveProbeSourceUri {
    param([string]$Revision)
    if ($Revision -cnotmatch '^[0-9a-f]{40}\z') { throw 'Invalid source revision.' }
    return 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/' + $Revision + '/IntuneBrew_Runbook.ps1'
}

function Confirm-CveProbeSource {
    param([byte[]]$Bytes, [string]$ExpectedSha256)
    if ($ExpectedSha256 -cnotmatch '^[0-9a-f]{64}\z' -or $Bytes.Length -gt 2MB) { throw 'Invalid pinned source.' }
    $hash = [Security.Cryptography.SHA256]::Create()
    try { $actual = [BitConverter]::ToString($hash.ComputeHash($Bytes)).Replace('-', '').ToLowerInvariant() }
    finally { $hash.Dispose() }
    if ($actual -cne $ExpectedSha256) { throw 'Source digest differs.' }
    return [Text.UTF8Encoding]::new($false, $true).GetString($Bytes)
}

function Read-CveProbeSource {
    param([string]$Revision, [string]$ExpectedSha256)
    $uri = Get-CveProbeSourceUri $Revision
    $handler = $null; $client = $null; $deadline = $null; $response = $null; $stream = $null; $body = $null
    try {
        $handler = [Net.Http.HttpClientHandler]::new(); $handler.AllowAutoRedirect = $false
        $client = [Net.Http.HttpClient]::new($handler)
        $deadline = [Threading.CancellationTokenSource]::new(); $deadline.CancelAfter(20000)
        $response = $client.GetAsync($uri, [Net.Http.HttpCompletionOption]::ResponseHeadersRead, $deadline.Token).GetAwaiter().GetResult()
        if ([int]$response.StatusCode -ne 200 -or $response.Content.Headers.ContentLength -gt 2MB) { throw 'Pinned source unavailable.' }
        $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult(); $body = [IO.MemoryStream]::new()
        $buffer = [byte[]]::new(8192)
        while (($count = $stream.ReadAsync($buffer, 0, $buffer.Length, $deadline.Token).GetAwaiter().GetResult()) -gt 0) {
            if ($body.Length + $count -gt 2MB) { throw 'Pinned source too large.' }
            $body.Write($buffer, 0, $count)
        }
        return Confirm-CveProbeSource $body.ToArray() $ExpectedSha256
    }
    finally {
        foreach ($resource in @($body, $stream, $response, $client, $handler, $deadline)) {
            if ($null -ne $resource) { $resource.Dispose() }
        }
    }
}

function Import-CveProbeFunctions {
    param([string]$Source)
    $tokens = $null; $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseInput($Source, [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw 'Pinned source parse failed.' }
    foreach ($name in @('Compare-VersionSegments', 'Get-CveComparableVersion', 'ConvertTo-CveDataset', 'Test-CveVersionAffected',
            'Get-CveUpdateImpact', 'Read-BoundedCveContent', 'Invoke-CveDataRequest', 'Get-RunbookCveAssessment')) {
        $definitions = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true))
        if ($definitions.Count -ne 1) { throw 'Pinned helper missing or duplicated.' }
        # Import only reviewed helpers. No top-level product code is evaluated.
        . ([scriptblock]::Create($definitions[0].Extent.Text.Replace("function $name", "function script:$name")))
    }
}

function Get-CveProbeMemorySnapshot {
    $process = [Diagnostics.Process]::GetCurrentProcess()
    try {
        $process.Refresh()
        return [pscustomobject]@{
            IsWindows = [Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([Runtime.InteropServices.OSPlatform]::Windows)
            OSDescription = [Runtime.InteropServices.RuntimeInformation]::OSDescription
            WorkingSetBytes = $process.WorkingSet64; PeakWorkingSetBytes = $process.PeakWorkingSet64
            PrivateMemoryBytes = $process.PrivateMemorySize64; PeakCommitBytes = $process.PeakPagedMemorySize64
        }
    }
    finally { $process.Dispose() }
}

function Assert-CveProbeMemoryMetrics {
    param($Baseline, $Final)
    if (-not $Baseline.IsWindows -or -not $Final.IsWindows -or [string]::IsNullOrWhiteSpace($Final.OSDescription) -or
        $Baseline.WorkingSetBytes -le 0 -or $Baseline.PeakWorkingSetBytes -lt $Baseline.WorkingSetBytes -or
        $Baseline.PeakCommitBytes -le 0 -or $Final.WorkingSetBytes -le 0 -or $Final.PrivateMemoryBytes -le 0 -or
        $Final.PeakWorkingSetBytes -lt $Final.WorkingSetBytes -or $Final.PeakWorkingSetBytes -lt $Baseline.PeakWorkingSetBytes -or
        $Final.PeakCommitBytes -lt $Baseline.PeakCommitBytes -or $Final.PeakCommitBytes -lt $Final.PrivateMemoryBytes) {
        throw 'Memory metrics unavailable or inconsistent.'
    }
}

function Get-CveProbeReport {
    param([string]$Revision, [string]$SourceSha256)
    $script:CveProbeStage = 'module'
    Import-Module Microsoft.Graph.Authentication -RequiredVersion 2.26.0 -ErrorAction Stop
    $script:CveProbeStage = 'metrics'
    $baseline = Get-CveProbeMemorySnapshot
    Assert-CveProbeMemoryMetrics $baseline $baseline
    if ([math]::Max($baseline.PeakWorkingSetBytes, $baseline.PeakCommitBytes) -gt 300MB) { throw 'Insufficient baseline memory headroom.' }
    $SecurityHoldLevel = 'High'; $IgnoreSecurityHold = $false
    $script:CveProbeFeedBytes = 0
    $originalTransport = (Get-Command Invoke-CveDataRequest -CommandType Function).ScriptBlock
    function Invoke-CveDataRequest {
        param([string]$Uri)
        $response = & $originalTransport $Uri
        if ($response.StatusCode -eq 200 -and $response.Content -is [string]) {
            $script:CveProbeFeedBytes = [Text.Encoding]::UTF8.GetByteCount($response.Content)
        }
        return $response
    }
    $script:CveProbeStage = 'feed'
    # Exercise the actual network, schema and evaluator path on the largest current feed.
    # Versions are fake: no tenant app or assignment is read or changed.
    $assessment = Get-RunbookCveAssessment 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/google_chrome.json' '0.0.0' '1.0.0'
    if ($assessment.Reason -ne 'assessed' -or $assessment.Impact.Records.Count -le 0 -or $script:CveProbeFeedBytes -le 0) { throw 'Live feed assessment failed.' }
    $script:CveProbeStage = 'holds'
    $decorated = @(@('5.8.1', '5.8.2(095C)', '5.8.2'), @('2.5', '2.5.1(2F17)', '2.5.1'), @('2.151.0-stable.1', '2.152.0-stable.4', '2.152.0'))
    foreach ($pair in $decorated) {
        $fixture = @{ cve_id = 'CVE-2026-12345'; severity = 'HIGH'; affected_version_start = $pair[2]; affected_version_start_type = 'including' }
        $impact = Get-CveUpdateImpact $pair[0] $pair[1] @($fixture) -HoldLevel High
        if (-not $impact.Held -or $impact.Records[0].Classification -ne 'Introduced') { throw 'Decorated hold failed.' }
    }
    $script:CveProbeStage = 'metrics'
    $final = Get-CveProbeMemorySnapshot
    Assert-CveProbeMemoryMetrics $baseline $final
    $growth = ($final.PeakWorkingSetBytes - $baseline.WorkingSetBytes) / 1MB
    $feedMiB = $script:CveProbeFeedBytes / 1MB
    $maximumPeak = [math]::Max($final.PeakWorkingSetBytes, $final.PeakCommitBytes)
    return [pscustomobject]@{
        Kind = 'IntuneBrew381ReadOnlyRuntimeProbe'; Revision = $Revision; RunbookSha256 = $SourceSha256
        PowerShellVersion = $PSVersionTable.PSVersion.ToString(); GraphModuleVersion = (Get-Module Microsoft.Graph.Authentication).Version.ToString()
        OSDescription = $final.OSDescription; IsWindows = $final.IsWindows
        BaselineWorkingSetMiB = [math]::Round($baseline.WorkingSetBytes / 1MB, 2); WorkingSetMiB = [math]::Round($final.WorkingSetBytes / 1MB, 2)
        PeakWorkingSetMiB = [math]::Round($final.PeakWorkingSetBytes / 1MB, 2); PrivateMemoryMiB = [math]::Round($final.PrivateMemoryBytes / 1MB, 2)
        PeakCommitMiB = [math]::Round($final.PeakCommitBytes / 1MB, 2); MaximumPeakMiB = [math]::Round($maximumPeak / 1MB, 2)
        FeedBytes = $script:CveProbeFeedBytes; FeedWorkingSetGrowthMiB = [math]::Round($growth, 2)
        WorkingSetGrowthMiBPerFeedMiB = [math]::Round($growth / $feedMiB, 2)
        FeedPeakCommitGrowthMiB = [math]::Round(($final.PeakCommitBytes - $baseline.PeakCommitBytes) / 1MB, 2)
        DocumentedCloudLimitMB = 400; AcceptancePeakLimitMiB = 300; MeetsMemoryThreshold = ($maximumPeak -le 300MB)
        LiveFeedAssessed = $true; VulnerabilityRecords = $assessment.Impact.Records.Count
        DecoratedIntroducedHoldsPassed = 3; GraphAuthenticationCalls = 0; TenantWrites = 0
    }
}

try {
    $script:CveProbeStage = 'source'
    $source = Read-CveProbeSource $Revision $RunbookSha256
    $script:CveProbeStage = 'import'
    Import-CveProbeFunctions $source
    Get-CveProbeReport $Revision $RunbookSha256 | ConvertTo-Json -Compress
}
catch {
    [pscustomobject]@{ Kind = 'IntuneBrew381ReadOnlyRuntimeProbe'; Passed = $false; Stage = $script:CveProbeStage; TenantWrites = 0 } | ConvertTo-Json -Compress
    throw ('Read-only runtime probe failed at stage ' + $script:CveProbeStage + '; no tenant operation was attempted.')
}
