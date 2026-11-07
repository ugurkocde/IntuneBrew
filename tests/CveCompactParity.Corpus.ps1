param([ValidateRange(0,1)][int]$ShardIndex = 0, [ValidateSet(1,2)][int]$ShardCount = 1)
$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..'
if ($ShardIndex -ge $ShardCount) { throw 'Invalid parity shard.' }
# Committed-only parity is intentional: dirty full or compact feeds must never pass unnoticed.
$dirty = @(& git -C $root status --porcelain --untracked-files=all -- CVE/ CVE-Holds/)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'Commit or revert full/compact CVE feed edits before parity testing.' }
$allFiles = @(Get-ChildItem (Join-Path $root 'CVE/*.json') | Sort-Object Name)
if ($allFiles.Count -lt 126) { throw 'The current all-app CVE parity corpus unexpectedly shrank.' }
$selected = @(); for ($index = 0; $index -lt $allFiles.Count; $index++) {
    if (($index % $ShardCount) -eq $ShardIndex) { $selected += $allFiles[$index] }
}

$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseInput([IO.File]::ReadAllText((Join-Path $root 'IntuneBrew.ps1')), [ref]$tokens, [ref]$errors)
foreach ($name in 'Compare-VersionSegments','Get-CveComparableVersion','ConvertTo-CveDataset','Test-CveVersionAffected','Get-CveUpdateImpact') {
    $definitions = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true))
    if ($definitions.Count -ne 1) { throw 'Missing evaluator.' }
    . ([scriptblock]::Create($definitions[0].Extent.Text))
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
$count = 0; $apps = 0
foreach ($file in $selected) {
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
