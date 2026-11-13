param([string]$ExtractedFunctionDirectory)
$ErrorActionPreference = 'Stop'
$root = if ($ExtractedFunctionDirectory) { $ExtractedFunctionDirectory } else { Join-Path $PSScriptRoot '..' }
$shared = @('Compare-VersionSegments', 'Get-CveComparableVersion', 'ConvertTo-CveDataset', 'Test-CveVersionAffected', 'Get-CveUpdateImpact')
$asts = @{}; $sources = @{}; $definitions = @{}
foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
    $source = [IO.File]::ReadAllText((Join-Path $root $file)); $sources[$file] = $source
    $tokens = $null; $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw ($errors | Out-String) }
    $asts[$file] = $ast
    foreach ($name in $shared) {
        $definition = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
        if (-not $definition) { throw "Missing shared security function $name in $file" }
        if ($file -eq 'IntuneBrew.ps1') { $definitions[$name] = $definition.Extent.Text }
        elseif ($definitions[$name] -cne $definition.Extent.Text) { throw "Security evaluator drift: $name" }
        Invoke-Expression $definition.Extent.Text
    }
    foreach ($case in @(@('5.8.2(095C)', '5.8.2'), @('2.5.1(2F17)', '2.5.1'), @('2.152.0-stable.4', '2.152.0'), @('0.0.0-stable.0', '0.0.0'), @('1.2.3.4.5', '1.2.3.4.5'))) {
        if ((Get-CveComparableVersion $case[0]) -cne $case[1]) { throw "Comparable release mismatch: $case" }
    }
    foreach ($bad in @('', '5.8.2(095c)', '5.8.2(0951)', '5.8.2 (095C)', '5.8.2(095CD)', '05.8.2(095C)', '5.8.2(0G5C)',
            '2.152.0-Stable.4', '2.152.0-stable.04', '2.152-stable.4', '2.152.0.1-stable.4', '2.152.0-stable', '2.152.0-beta.1',
            '2.152.0-rc1', '2.152.0 (build 4)', '2.152.0+4', '1000000000.1.1-stable.4', "2.152.0-stable.4`n")) {
        if ($null -ne (Get-CveComparableVersion $bad)) { throw "Unsupported decoration accepted: $bad" }
        if ($null -ne (Test-CveVersionAffected $bad @{ fixed_version = '99' })) { throw "Unsupported version gained an exposure result: $bad" }
        $unknownVersion = Get-CveUpdateImpact $bad '5' @(@{ fixed_version = '99'; severity = 'CRITICAL'; is_kev = $true }) -HoldLevel High
        if ($unknownVersion.Held -or $unknownVersion.Records[0].Classification -ne 'Indeterminate') { throw 'Unsupported current version became determinate.' }
    }
    foreach ($pair in @(@('5.8.1', '5.8.2(095C)', '5.8.2'), @('2.5', '2.5.1(2F17)', '2.5.1'),
            @('2.151.0-stable.1', '2.152.0-stable.4', '2.152.0'))) {
        foreach ($level in @('None', 'Medium', 'High', 'Critical')) {
            foreach ($severity in @('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')) {
                foreach ($kev in @($false, $true)) {
                    $v = @{ cve_id = 'CVE-2026-12345'; severity = $severity; is_kev = $kev; affected_version_start = $pair[2]; affected_version_start_type = 'including' }
                    $rank = @{ LOW = 1; MEDIUM = 2; HIGH = 3; CRITICAL = 4; None = 99 }
                    $expected = $level -ne 'None' -and ($kev -or $rank[$severity] -ge $rank[$level.ToUpperInvariant()])
                    $decorated = Get-CveUpdateImpact $pair[0] $pair[1] @($v) -HoldLevel $level
                    $plain = Get-CveUpdateImpact (Get-CveComparableVersion $pair[0]) $pair[2] @($v) -HoldLevel $level
                    if ($decorated.Records[0].Classification -ne 'Introduced' -or $decorated.Held -ne $expected -or $decorated.Held -ne $plain.Held) { throw 'Decorated target changed hold semantics.' }
                    if ((Get-CveUpdateImpact $pair[0] $pair[1] @($v) -HoldLevel $level -IgnoreHold).Held) { throw 'Explicit override ignored.' }
                    $reverse = Get-CveUpdateImpact $pair[1] $pair[0] @($v) -HoldLevel $level
                    if ($reverse.Held -or $reverse.Records[0].Classification -ne 'Fixed') { throw 'Decorated current version changed fixed classification.' }
                    if ((Get-CveUpdateImpact $pair[1] $pair[1] @($v) -HoldLevel $level).Held) { throw 'Persistent CVE unexpectedly held.' }
                }
            }
        }
    }
    $unknown = @{ cve_id = 'CVE-2026-12345'; severity = 'CRITICAL'; is_kev = $true; fixed_version = '2.152.0-stable.5' }
    $impact = Get-CveUpdateImpact '2.151.0' '2.152.0-stable.4' @($unknown) -HoldLevel High
    if ($impact.Held -or $impact.Records[0].Classification -ne 'Indeterminate') { throw 'Decorated CVE bounds were normalized or unknown ranges held.' }
}
if ($ExtractedFunctionDirectory) { Write-Host 'Windows PowerShell shared CVE parity and decorated-version holds passed.'; exit 0 }
function Import-RunbookFunction([string]$Name) {
    $definition = $asts['IntuneBrew_Runbook.ps1'].Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $Name }, $true)
    if (-not $definition) { throw "Missing Runbook function $Name" }
    # Install in the caller's script scope; never execute either full product script.
    . ([scriptblock]::Create($definition.Extent.Text.Replace("function $Name", "function script:$Name")))
}
foreach ($name in @('ConvertTo-RunbookSecurityConfig', 'Read-BoundedCveContent', 'Invoke-CveDataRequest', 'Get-RunbookCveAssessment', 'New-RunbookAppCandidate',
        'ConvertTo-UnraidRevisionVersion', 'ConvertTo-NumericBundleVersion', 'Compare-NumericBundleVersion', 'Is-NewerVersion', 'Get-IntuneApps', 'Get-AllMacOsApps',
        'Select-LatestAppRecord', 'Convert-VersionToSortable')) { Import-RunbookFunction $name }
$rb = $sources['IntuneBrew_Runbook.ps1']
if ($rb.IndexOf('$securityConfig = ConvertTo-RunbookSecurityConfig') -gt $rb.IndexOf('Connect-MgGraph')) { throw 'Security config validated after Graph authentication.' }
foreach ($case in @(@($null, $null, 'None', $false), @('hIgH', 'true', 'High', $true), @('Critical', 'false', 'Critical', $false), @('Medium', $true, 'Medium', $true))) {
    $actual = ConvertTo-RunbookSecurityConfig $case[0] $case[1]
    if ($actual.HoldLevel -cne $case[2] -or $actual.IgnoreHold -ne $case[3]) { throw 'Security config normalization changed.' }
}
foreach ($case in @(@('bad', $false), @('', $false), @(' High', $false), @('High', 'yes'), @('High', 'True'), @('High', 1))) {
    $threw = $false; try { $null = ConvertTo-RunbookSecurityConfig $case[0] $case[1] } catch { $threw = $true }
    if (-not $threw) { throw 'Invalid config accepted.' }
}
$dataset = '{"vulnerabilities":[{"cve_id":"CVE-2026-12345","severity":"HIGH","is_kev":false,"affected_version_start":"2","affected_version_start_type":"including"}]}'
$null = ConvertTo-CveDataset ($dataset | ConvertFrom-Json)
$null = ConvertTo-CveDataset ('{"vulnerabilities":[]}' | ConvertFrom-Json)
foreach ($bad in @('{}', '[]', '{"vulnerabilities":{}}', '{"vulnerabilities":[null]}', '{"vulnerabilities":[{"cve_id":""}]}',
        '{"vulnerabilities":[{"cve_id":"CVE-2026-12345","severity":5}]}', '{"vulnerabilities":[{"cve_id":"CVE-2026-12345","is_kev":"true"}]}')) {
    $threw = $false; try { $null = ConvertTo-CveDataset ($bad | ConvertFrom-Json) } catch { $threw = $true }
    if (-not $threw) { throw 'Malformed dataset accepted.' }
}
# Exercise the production stream reader at and beyond its cap, invalid UTF-8 and cancellation.
foreach ($length in @(0, 8191, 8192, 16MB)) {
    $stream = [IO.MemoryStream]::new([byte[]]::new($length))
    try { if ((Read-BoundedCveContent $stream ([Threading.CancellationToken]::None)).Length -ne $length) { throw 'Stream was truncated.' } }
    finally { $stream.Dispose() }
}
foreach ($bytes in @([byte[]]::new(16MB + 1), [byte[]]@(0xff))) {
    $stream = [IO.MemoryStream]::new($bytes); $threw = $false
    try { $null = Read-BoundedCveContent $stream ([Threading.CancellationToken]::None) } catch { $threw = $true }
    finally { $stream.Dispose() }
    if (-not $threw) { throw 'Oversized or invalid UTF-8 CVE stream accepted.' }
}
$stream = [IO.MemoryStream]::new([byte[]]@(1)); $cancelled = [Threading.CancellationTokenSource]::new(); $cancelled.Cancel(); $threw = $false
try { $null = Read-BoundedCveContent $stream $cancelled.Token } catch { $threw = $true }
finally { $stream.Dispose(); $cancelled.Dispose() }
if (-not $threw) { throw 'CVE stream ignored cancellation.' }

# Invalid routes must fail before constructing an HTTP client; all valid requests below are mocked.
foreach ($uri in @('https://example.invalid/CVE/app.json', 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/CVE-Holds/a..b.json')) {
    $threw = $false; try { $null = Invoke-CveDataRequest $uri } catch { $threw = $true }
    if (-not $threw) { throw 'Untrusted CVE route accepted.' }
}
function New-TestCompact($Records) {
    return (@{ schema_version = 1; app_key = 'fixture'; source_sha256 = ('a' * 64); vulnerabilities = @($Records) } | ConvertTo-Json -Depth 8 -Compress)
}
$dataset = New-TestCompact (($dataset | ConvertFrom-Json).vulnerabilities)
$script:requests = 0; $script:response = @{ StatusCode = 200; Content = $dataset }; $script:requestThrows = $false
function Invoke-CveDataRequest {
    param($Uri)
    $script:requests++
    if ($Uri -cnotmatch '^https://raw\.githubusercontent\.com/ugurkocde/IntuneBrew/main/CVE-Holds/fixture[a-z0-9_]*\.json\z') { throw 'Wrong feed trust root or key.' }
    if ($script:requestThrows) { throw 'mock timeout' }
    return $script:response
}
$SecurityHoldLevel = 'None'; $IgnoreSecurityHold = $false; $url = 'https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/fixture.json'
if ((Get-RunbookCveAssessment $url '1' '2').Held -or $script:requests -ne 0) { throw 'Disabled policy fetched a feed or held an update.' }
$SecurityHoldLevel = 'High'
if (-not (Get-RunbookCveAssessment $url '1' '2').Held) { throw 'Introduced target not held.' }

# Compact envelope validation rejects boolean/string versions, extra keys, wrong identity and malformed digests.
$baseEnvelope = $dataset | ConvertFrom-Json -AsHashtable
foreach ($change in @(@{ schema_version = $true }, @{ schema_version = '1' }, @{ schema_version = 2 },
        @{ app_key = 'other' }, @{ source_sha256 = ('A' * 64) }, @{ source_sha256 = 'short' }, @{ extra = 'field' })) {
    $envelope = $baseEnvelope.Clone()
    foreach ($key in $change.Keys) { $envelope[$key] = $change[$key] }
    $script:response = @{ StatusCode = 200; Content = ($envelope | ConvertTo-Json -Depth 8 -Compress) }
    $badEnvelope = Get-RunbookCveAssessment $url '1' '2'
    if (-not $badEnvelope.Held -or $badEnvelope.Reason -ne 'data-error') { throw 'Malformed compact envelope failed open.' }
}
$script:response = @{ StatusCode = 200; Content = $dataset }
# A valid large feed must reach the evaluator rather than become a data-error hold.
$padding = 'x' * (2MB + 1)
$largeIntroduced = $padding.Replace('x', ' ') + (New-TestCompact @(@{ cve_id = 'CVE-2026-12345'; severity = 'HIGH'; affected_version_start = '2'; affected_version_start_type = 'including' }))
$script:response = @{ StatusCode = 200; Content = $largeIntroduced }
$largeResult = Get-RunbookCveAssessment $url '1' '2'
if (-not $largeResult.Held -or $largeResult.Reason -ne 'assessed' -or $largeResult.Impact.Records[0].Classification -ne 'Introduced') { throw 'Valid large introduced feed failed to reach evaluator.' }
$script:response = @{ StatusCode = 200; Content = ($padding.Replace('x', ' ') + (New-TestCompact @())) }
$largeResult = Get-RunbookCveAssessment $url '1' '2'
if ($largeResult.Held -or $largeResult.Reason -ne 'assessed') { throw 'Valid large empty feed became a data-error hold.' }
$script:response = @{ StatusCode = 200; Content = $dataset }
foreach ($name in @('Read-BoundedCveContent', 'Invoke-CveDataRequest', 'Get-RunbookCveAssessment')) {
    $cveFunction = $asts['IntuneBrew_Runbook.ps1'].Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if ($cveFunction.Extent.Text -match '(?<![0-9])2MB\b' -or $cveFunction.Extent.Text -notmatch '16MB') { throw 'Inconsistent Runbook CVE byte limit.' }
}

$script:response = @{ StatusCode = 404 }
if ((Get-RunbookCveAssessment $url '1' '2').Held) { throw '404 changed CLI missing-data semantics.' }
foreach ($response in @(@{ StatusCode = 429 }, @{ StatusCode = 500 }, @{ StatusCode = 302 }, @{ StatusCode = 200; Content = 'not json' },
        @{ StatusCode = 200; Content = '{}' }, @{ StatusCode = 200; Content = ('x' * (16MB + 1)) })) {
    $script:response = $response
    $result = Get-RunbookCveAssessment $url '1' '2'
    if (-not $result.Held -or $result.Reason -ne 'data-error') { throw 'Unavailable or malformed feed failed open.' }
}
$script:requestThrows = $true
if (-not (Get-RunbookCveAssessment $url '1' '2').Held) { throw 'Transport failure failed open.' }
$script:requestThrows = $false; $script:response = @{ StatusCode = 200; Content = $dataset }
$before = $script:requests
if (-not (Get-RunbookCveAssessment 'https://example.invalid/fixture.json' '1' '2').Held -or $script:requests -ne $before) { throw 'Invalid app key reached a request or failed open.' }
$IgnoreSecurityHold = $true
if ((Get-RunbookCveAssessment $url '1' '2').Held) { throw 'Runbook override did not work.' }
$IgnoreSecurityHold = $false
$script:messages = @()
function Write-Log { param($Message, $Type); $script:messages += [pscustomobject]@{ Message = $Message; Type = $Type } }
function Is-ValidUrl { param($Url); return $Url.StartsWith('https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/') }
$script:manifest = @{ name = 'Fixture'; version = '2'; bundleId = 'invalid.fixture'; url = 'https://example.invalid/two.pkg'; sha = ('a' * 64) }
$script:metadataReads = 0
function Get-GitHubAppInfo { param($jsonUrl); $script:metadataReads++; return $script:manifest }
function Invoke-MgGraphRequest {
    param($Uri, $Method)
    if ($Uri.Contains('displayName')) {
        if ($script:byBundle) { return @{ value = @() } }
        return @{ value = @(@{ id = 'fake-app'; primaryBundleVersion = '1' }) }
    }
    return @{ value = @(@{ id = 'fake-app'; primaryBundleVersion = '1'; primaryBundleId = 'invalid.fixture'; displayName = 'Renamed fixture' }) }
}
$githubJsonUrls = @($url)
foreach ($mode in @($false, $true)) {
    $script:byBundle = $mode; $script:allMacOsAppsCache = $null
    $apps = @(Get-IntuneApps)
    if ($apps.Count -ne 1 -or -not $apps[0].SecurityHeld) { throw "Lookup path bypassed gate: bundle=$mode" }
}
# Logged CVE IDs use canonical sequence padding; malformed IDs never alter hold evaluation.
$validIds = @('CVE-2014-0160', 'CVE-2026-10000', 'CVE-2026-1234567')
$invalidIds = @('CVE-2026-05773', 'CVE-2026-123', "CVE-2026-1234`n")
$records = @(($validIds + $invalidIds) | ForEach-Object {
    @{ cve_id = $_; severity = 'HIGH'; affected_version_start = '2'; affected_version_start_type = 'including' }
})
$script:response = @{ StatusCode = 200; Content = (New-TestCompact $records) }
$script:messages = @()
$loggedCandidate = New-RunbookAppCandidate -Manifest $script:manifest -JsonUrl $url -IntuneVersion '1' -IntuneAppId 'fake-app'
if (-not $loggedCandidate.SecurityHeld) { throw 'Logging filter changed hold evaluation.' }
$warning = @($script:messages | Where-Object Type -eq 'Warning').Message -join ' '
$loggedIds = (($warning -split '; ', 2)[1]) -split ', '
if ($loggedIds.Count -ne $validIds.Count) { throw 'Wrong number of canonical CVE IDs logged.' }
foreach ($id in $validIds) { if ($loggedIds -cnotcontains $id) { throw "Canonical CVE ID missing from warning: $id" } }
foreach ($id in $invalidIds) { if ($loggedIds -ccontains $id) { throw 'Malformed CVE ID reached the warning log.' } }
$script:response = @{ StatusCode = 200; Content = $dataset }
$SecurityHoldLevel = 'None'; $script:metadataReads = 0
$app = @(Get-IntuneApps)[0]
$script:manifest.version = '3'; $script:manifest.url = 'https://example.invalid/three.pkg'
function Get-GitHubAppInfo { throw 'Upload re-fetched the catalog.' }
$start = $rb.IndexOf('        # Upload exactly the metadata/version assessed')
$end = $rb.IndexOf('        # Check if this is an update and fetch existing assignments', $start)
Invoke-Expression $rb.Substring($start, $end - $start)
if ($appInfo.version -ne '2' -or $appInfo.url -ne 'https://example.invalid/two.pkg' -or $script:metadataReads -ne 1) { throw 'Upload failed to pin assessed metadata.' }
# Run the actual selection/limit/exit block in a child process with fake candidates only.
$start = $rb.IndexOf('$heldApps = @($intuneAppVersions')
$end = $rb.IndexOf('# Determine if assignments should be copied', $start)
$selection = $rb.Substring($start, $end - $start)
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('RunbookCve-' + [guid]::NewGuid().ToString('N') + '.ps1')
try {
    $setup = @'
function Write-Log { param($Message,$Type) }
function Disconnect-MgGraph {}
function Is-NewerVersion { return $true }
$MaxAppsPerRun = 10
$intuneAppVersions = @(1..12 | ForEach-Object { [pscustomobject]@{ Name="Fake$_"; IntuneVersion='1'; GitHubVersion='2'; SecurityHeld=($_ -le 3) } })
'@
    ($setup + "`n" + $selection + "`nif (`$appsToUpload.Count -ne 9 -or @(`$appsToUpload | Where-Object SecurityHeld).Count) { throw 'Held app consumed a slot.' }") | Set-Content $fixture
    & pwsh -NoProfile -File $fixture
    if ($LASTEXITCODE -ne 0) { throw 'Runbook selection/limit regression.' }
    ($setup + "`n`$intuneAppVersions | ForEach-Object { `$_.SecurityHeld = `$true }`n" + $selection + "`nthrow 'All-held run did not exit.'") | Set-Content $fixture
    & pwsh -NoProfile -File $fixture
    if ($LASTEXITCODE -ne 0) { throw 'All-held unattended run did not exit 0.' }
}
finally { Remove-Item $fixture -Force }
# The CLI also validates local datasets: configured malformed data is held, an absent file stays unavailable.
$cliAst = $asts['IntuneBrew.ps1']
$localReader = $cliAst.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-AppCveInfo' }, $true)
Invoke-Expression $localReader.Extent.Text
$localDirectory = Join-Path ([IO.Path]::GetTempPath()) ('LocalCve-' + [guid]::NewGuid().ToString('N'))
$null = [IO.Directory]::CreateDirectory((Join-Path $localDirectory 'CVE'))
Push-Location $localDirectory
try {
    if ($null -ne (Get-AppCveInfo 'absent')) { throw 'Missing local CVE file changed semantics.' }
    $localFile = Join-Path $localDirectory 'CVE/fixture.json'
    $dataset | Set-Content $localFile
    if ((Get-AppCveInfo 'fixture').vulnerabilities.Count -ne 1) { throw 'Valid local dataset rejected.' }
    '{}' | Set-Content $localFile
    $cveInfo = Get-AppCveInfo 'fixture'
    if ($cveInfo.DataError -ne $true) { throw 'Malformed local dataset was not marked.' }
    $source = $sources['IntuneBrew.ps1']
    $start = $source.IndexOf('                    if ($cveInfo.DataError')
    $end = $source.IndexOf('                    Write-CveUpdateImpact', $start)
    foreach ($level in @('None', 'High')) {
        foreach ($ignore in @($false, $true)) {
            $SecurityHoldLevel = $level; $IgnoreSecurityHold = $ignore
            $securityImpact = [pscustomobject]@{ Held = $false }
            Invoke-Expression $source.Substring($start, $end - $start)
            if ($securityImpact.Held -ne ($level -ne 'None' -and -not $ignore)) { throw 'Malformed local CVE hold bypassed configured policy.' }
        }
    }
}
finally { Pop-Location; Remove-Item $localDirectory -Recurse -Force }

Write-Host 'Shared CVE grammar/hold parity, strict config/feed, both lookup paths, upload pin and unattended selection checks passed.'

if ($env:OS -eq 'Windows_NT' -and $PSVersionTable.PSEdition -ne 'Desktop') {
    $windowsPowerShell = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
    if (-not (Test-Path -LiteralPath $windowsPowerShell)) { throw 'Windows PowerShell runtime is missing.' }
    $directory = Join-Path ([IO.Path]::GetTempPath()) ('CveCompatibility-' + [guid]::NewGuid().ToString('N'))
    $null = [IO.Directory]::CreateDirectory($directory)
    try {
        foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
            $code = foreach ($name in $shared) { $asts[$file].Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true).Extent.Text }
            [IO.File]::WriteAllText((Join-Path $directory $file), ($code -join "`r`n"), [Text.UTF8Encoding]::new($false))
        }
        & $windowsPowerShell -NoProfile -File $PSCommandPath -ExtractedFunctionDirectory $directory
        if ($LASTEXITCODE -ne 0) { throw 'Windows PowerShell CVE parity failed.' }
    }
    finally { Remove-Item $directory -Recurse -Force }
}
