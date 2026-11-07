param([ValidateRange(0,1)][int]$ShardIndex = 0, [ValidateSet(1,2)][int]$ShardCount = 1)
$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..'
if ($ShardIndex -ge $ShardCount) { throw 'Invalid parity shard.' }
# Committed-only parity is intentional: dirty full or compact feeds must never pass unnoticed.
$dirty = @(& git -C $root status --porcelain --untracked-files=all -- CVE/ CVE-Holds/ IntuneBrew.ps1 IntuneBrew_Runbook.ps1)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'Commit or revert full/compact CVE feed edits before parity testing.' }
$allFiles = @(Get-ChildItem (Join-Path $root 'CVE/*.json') | Sort-Object Name)
if ($allFiles.Count -lt 126) { throw 'The current all-app CVE parity corpus unexpectedly shrank.' }
$selected = @(); for ($index = 0; $index -lt $allFiles.Count; $index++) {
    if (($index % $ShardCount) -eq $ShardIndex) { $selected += $allFiles[$index] }
}

# Provenance describes published Git blob bytes. A Windows text checkout can use CRLF instead.
function Get-TrackedCveBytes([string]$Path) {
    <# .SYNOPSIS
    Reads immutable published Git blob bytes without checkout newline conversion.
    .DESCRIPTION
    Streams stdout as bytes, drains stderr asynchronously, and refuses a failed Git read.
    #>
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = 'git'; $start.WorkingDirectory = $root
    $start.UseShellExecute = $false; $start.RedirectStandardOutput = $true; $start.RedirectStandardError = $true
    foreach ($argument in @('cat-file', 'blob', ('HEAD:' + $Path))) { $start.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $start
    $buffer = [IO.MemoryStream]::new()
    try {
        if (-not $process.Start()) { throw 'Cannot read tracked CVE data.' }
        $errorRead = $process.StandardError.ReadToEndAsync()
        $process.StandardOutput.BaseStream.CopyTo($buffer)
        $process.WaitForExit(); $null = $errorRead.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw 'Tracked CVE data is unavailable.' }
        return ,$buffer.ToArray()
    }
    finally { $buffer.Dispose(); $process.Dispose() }
}

$tokens = $null; $errors = $null
$evaluatorSource = [Text.UTF8Encoding]::new($false, $true).GetString((Get-TrackedCveBytes 'IntuneBrew.ps1'))
$ast = [Management.Automation.Language.Parser]::ParseInput($evaluatorSource, [ref]$tokens, [ref]$errors)
foreach ($name in 'Compare-VersionSegments','Get-CveComparableVersion','ConvertTo-CveDataset','Test-CveVersionAffected','Get-CveUpdateImpact') {
    $definitions = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true))
    if ($definitions.Count -ne 1) { throw 'Missing evaluator.' }
    . ([scriptblock]::Create($definitions[0].Extent.Text))
}
# This cache is confined to this corpus process. Other regression suites import uncached helpers.
function Assert-CveMemoPurity($Ast) {
    $pins = @{
        'Compare-VersionSegments' = '02710ef504f97fa8e50e86fa5f92e1edff3fc61d8a4bad579eb629f247b9cdf9'
        'Get-CveComparableVersion' = 'ff1a1281a38fa4255c2fdb2e1a9e8172b06cb21d82594249504204eef170a681'
        'Get-CveUpdateImpact' = 'fb301805cfe1dc76d0e567b8dabdbeab70d7fb317e9049ab6021c038e2a5a0e1'
        'Test-CveVersionAffected' = '791f49c38d644a893a29ac8513c6cde497aa67b2f807e6ff1615d31b7b061443'
    }
    foreach ($name in $pins.Keys) {
        $definitions = @($Ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true))
        if ($definitions.Count -ne 1) { throw 'Memoized helper identity changed; review purity again.' }
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($definitions[0].Extent.Text))).ToLowerInvariant()
        if ($digest -cne $pins[$name]) { throw 'Memoized helper changed; review purity again.' }
        if ($name -eq 'Test-CveVersionAffected') {
            foreach ($variable in $definitions[0].FindAll({ param($n) $n -is [Management.Automation.Language.VariableExpressionAst] }, $true)) {
                if ($variable.VariablePath.UserPath -match '^(script|global|env):') { throw 'Stateful helper cannot be memoized.' }
            }
            foreach ($command in $definitions[0].FindAll({ param($n) $n -is [Management.Automation.Language.CommandAst] }, $true)) {
                if ($command.GetCommandName() -cnotin @('Get-CveComparableVersion', 'Compare-VersionSegments')) { throw 'Unreviewed helper dependency.' }
            }
        }
    }
}
Assert-CveMemoPurity $ast
$script:originalCveAffected = ${function:Test-CveVersionAffected}
$script:originalCveImpact = ${function:Get-CveUpdateImpact}
$script:cveMemo = [Collections.Generic.Dictionary[object, object]]::new([Collections.Generic.ReferenceEqualityComparer]::Instance)
function Test-CveVersionAffected {
    param([string]$Version, $Vulnerability)
    if ($null -eq $Vulnerability) {
        $actual = @(& $script:originalCveAffected -Version $Version -Vulnerability $Vulnerability)
        if ($actual.Count -ne 1 -or ($null -ne $actual[0] -and $actual[0] -isnot [bool])) { throw 'CVE helper contract changed.' }
        return $actual[0]
    }
    $versions = $null
    if (-not $script:cveMemo.TryGetValue($Vulnerability, [ref]$versions)) {
        $versions = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
        $script:cveMemo[$Vulnerability] = $versions
    }
    $value = $null
    if ($versions.TryGetValue($Version, [ref]$value)) { return $value }
    $actual = @(& $script:originalCveAffected -Version $Version -Vulnerability $Vulnerability)
    if ($actual.Count -ne 1 -or ($null -ne $actual[0] -and $actual[0] -isnot [bool])) { throw 'CVE helper contract changed.' }
    $versions[$Version] = $actual[0]
    return $actual[0]
}
function Invoke-UncachedCveImpact {
    param($Current, $Target, $Records, $Level, $Ignore)
    function Test-CveVersionAffected {
        param([string]$Version, $Vulnerability)
        & $script:originalCveAffected -Version $Version -Vulnerability $Vulnerability
    }
    & $script:originalCveImpact -CurrentVersion $Current -TargetVersion $Target -Vulnerabilities $Records -HoldLevel $Level -IgnoreHold:$Ignore
}

function Get-ImpactSignature($Impact) {
    <# .SYNOPSIS
    Encodes the overall hold and every record classification, hold and CVE ID without ambiguity.
    #>
    $result = [Text.StringBuilder]::new(); [void]$result.Append($Impact.Held).Append('|')
    foreach ($record in $Impact.Records) {
        foreach ($value in @($record.Classification, $record.Hold, $record.Vulnerability.cve_id)) {
            $text = [string]$value; [void]$result.Append($text.Length).Append(':').Append($text).Append('|')
        }
    }
    return $result.ToString()
}
# Small uncached differential and refusal controls run on BOTH engines, in every worker.
$fixtureRecords = @(
    @{ cve_id = 'CVE-2099-0001'; severity = 'HIGH' },
    @{ cve_id = 'CVE-2099-0002'; severity = 'CRITICAL'; fixed_version = 'invalid' },
    @{ cve_id = 'CVE-2099-0003'; severity = 'HIGH'; affected_version_start = '1'; affected_version_start_type = 'excluding'; affected_version_end = '3'; affected_version_end_type = 'excluding' },
    @{ cve_id = 'CVE-2099-0004'; severity = 'LOW'; is_kev = $true; affected_version_start = '2'; affected_version_start_type = 'including'; affected_version_end = '2'; affected_version_end_type = 'including' },
    @{ cve_id = 'CVE-2099-0005'; severity = 'HIGH'; affected_version_start = '2'; affected_version_start_type = 'excluding'; affected_version_end = '2'; affected_version_end_type = 'including' },
    @{ cve_id = 'CVE-2099-0006'; severity = 'HIGH'; affected_version_start = '1.2.3.4.5'; affected_version_start_type = 'including' }
)
foreach ($key in '1password', 'airtable', 'cursor') {
    foreach ($directory in 'CVE', 'CVE-Holds') {
        $data = [Text.Encoding]::UTF8.GetString((Get-TrackedCveBytes ($directory + '/' + $key + '.json'))) | ConvertFrom-Json -ErrorAction Stop
        $fixtureRecords += @($data.vulnerabilities | Select-Object -First 3)
    }
}
foreach ($record in $fixtureRecords) {
    foreach ($version in @('', '1', '2', '3', '1.2.3.4.5', '2.0(0A1B)', '2.0(0a1b)', 'unsupported')) {
        $expected = @(& $script:originalCveAffected -Version $version -Vulnerability $record)
        foreach ($repeat in 1,2) {
            $actual = @(Test-CveVersionAffected -Version $version -Vulnerability $record)
            if ($actual.Count -ne 1 -or $expected.Count -ne 1 -or
                (($null -eq $actual[0]) -ne ($null -eq $expected[0])) -or
                ($null -ne $actual[0] -and ($actual[0].GetType() -ne $expected[0].GetType() -or $actual[0] -cne $expected[0]))) { throw 'Memoized per-call result differs.' }
        }
    }
}
$script:cveMemo.Clear()
foreach ($pair in @(@('1','2'), @('2','1'), @('1.2.3.4.4','1.2.3.4.5'), @('unsupported','2'))) {
    foreach ($level in 'Medium','High','Critical') {
        foreach ($ignore in $false,$true) {
            $expected = Invoke-UncachedCveImpact $pair[0] $pair[1] $fixtureRecords $level $ignore
            if ($script:cveMemo.Count -ne 0) { throw 'Uncached reference unexpectedly used memoization.' }
            $actual = Get-CveUpdateImpact $pair[0] $pair[1] $fixtureRecords -HoldLevel $level -IgnoreHold:$ignore
            if ((Get-ImpactSignature $expected) -cne (Get-ImpactSignature $actual)) { throw 'Memoized impact signature differs.' }
            $script:cveMemo.Clear()
        }
    }
}
# Separate full/compact objects must always have separate entries, even with an identical CVE id.
$leftRecord = @{ cve_id = 'CVE-2099-0007'; fixed_version = '1' }
$rightRecord = @{ cve_id = 'CVE-2099-0007'; fixed_version = '3' }
if ((Test-CveVersionAffected '2' $leftRecord) -ne $false -or (Test-CveVersionAffected '2' $rightRecord) -ne $true -or $script:cveMemo.Count -ne 2) { throw 'Record reference isolation failed.' }
$beforeNull = $script:cveMemo.Count; $null = Test-CveVersionAffected '2' $null
if ($script:cveMemo.Count -ne $beforeNull) { throw 'Null records entered the cache.' }
$originalHelper = $script:originalCveAffected
try {
    foreach ($bad in @({ param($Version, $Vulnerability) 'not-bool' }, { param($Version, $Vulnerability) $true; $false }, { param($Version, $Vulnerability) throw 'TEST-ONLY original failure' })) {
        $script:cveMemo.Clear(); $script:originalCveAffected = $bad; $refused = $false
        try { $null = Test-CveVersionAffected '2' $leftRecord } catch { $refused = $true }
        if (-not $refused) { throw 'Helper contract violation passed.' }
        $versions = $null
        if ($script:cveMemo.TryGetValue($leftRecord, [ref]$versions) -and $versions.ContainsKey('2')) { throw 'A failed result entered the cache.' }
    }
}
finally { $script:originalCveAffected = $originalHelper; $script:cveMemo.Clear() }
$definition = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-CveVersionAffected' }, $true))[0]
$changed = $definition.Extent.Text.Replace('return $null', 'return $true')
$changedSource = $evaluatorSource.Replace($definition.Extent.Text, $changed)
$changedAst = [Management.Automation.Language.Parser]::ParseInput($changedSource, [ref]$tokens, [ref]$errors)
$refused = $false; try { Assert-CveMemoPurity $changedAst } catch { $refused = $_.Exception.Message -ceq 'Memoized helper changed; review purity again.' }
if (-not $refused) { throw 'Changed helper purity pin passed.' }

$count = 0; $apps = 0
foreach ($file in $selected) {
    $script:cveMemo.Clear()
    $bytes = Get-TrackedCveBytes ('CVE/' + $file.Name)
    $full = ConvertTo-CveDataset ([Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json -ErrorAction Stop)
    $compact = [Text.Encoding]::UTF8.GetString((Get-TrackedCveBytes ('CVE-Holds/' + $file.Name))) | ConvertFrom-Json -ErrorAction Stop
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    if ($compact.source_sha256 -cne $digest -or $compact.app_key -cne $file.BaseName -or $compact.schema_version -ne 1) { throw 'Compact provenance drift.' }
    $small = ConvertTo-CveDataset $compact
    if ($small.vulnerabilities.Count -ne $full.vulnerabilities.Count) { throw 'Compaction dropped records.' }
    $boundary = '2.0.0'
    foreach ($record in $full.vulnerabilities) {
        foreach ($field in 'affected_version_start','affected_version_end','fixed_version') {
            $candidate = [string]$record.$field
            if ($candidate -cmatch '^(0|[1-9][0-9]{0,8})(\.(0|[1-9][0-9]{0,8})){1,4}\z') { $boundary = $candidate; break }
        }
        if ($boundary -ne '2.0.0') { break }
    }
    $pairs = @(@('0.0.0', $boundary), @($boundary, '0.0.0'), @('0.0.0(0A1B)', ($boundary + '(0A1B)')),
        @('1.0.0-stable.1','2.0.0-stable.4'), @('unsupported','2.0.0'))
    foreach ($pair in $pairs) {
        foreach ($level in 'Medium','High','Critical') {
            foreach ($ignore in $false,$true) {
                $left = Get-CveUpdateImpact $pair[0] $pair[1] @($full.vulnerabilities) -HoldLevel $level -IgnoreHold:$ignore
                $right = Get-CveUpdateImpact $pair[0] $pair[1] @($small.vulnerabilities) -HoldLevel $level -IgnoreHold:$ignore
                if ((Get-ImpactSignature $left) -cne (Get-ImpactSignature $right)) { throw ('Compact evaluator mismatch: ' + $file.Name) }
                $count++
            }
        }
    }
    $apps++
}
if ($apps -ne $selected.Count -or $count -ne (30 * $apps)) { throw 'Parity shard coverage differs.' }
[pscustomobject]@{ Runtime = $PSVersionTable.PSVersion.ToString(); ShardIndex = $ShardIndex; ShardCount = $ShardCount;
    Apps = $apps; Comparisons = $count; AppKeys = @($selected | ForEach-Object BaseName); Mismatches = 0 } | ConvertTo-Json -Compress
