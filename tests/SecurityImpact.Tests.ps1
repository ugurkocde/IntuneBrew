$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../IntuneBrew.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Compare-VersionSegments', 'Test-CveVersionAffected', 'Get-CveUpdateImpact', 'Write-CveUpdateImpact')) {
    $function = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    Invoke-Expression $function.Extent.Text
}
$vuln = @{ cve_id = 'CVE-test'; severity = 'HIGH'; affected_version_start = '2.0'; affected_version_start_type = 'including'; affected_version_end = '3.0'; affected_version_end_type = 'excluding' }
foreach ($case in @(@('1.0','2.0','Introduced'),@('2.0','3.0','Fixed'),@('2.0','2.1','Persists'),@('3.0','4.0','NotRelevant'))) {
    $impact = Get-CveUpdateImpact $case[0] $case[1] @($vuln)
    if ($impact.Records[0].Classification -ne $case[2] -or $impact.Held) { throw "Incorrect default impact: $case" }
}
if (-not (Get-CveUpdateImpact '1' '2' @($vuln) -HoldLevel High).Held) { throw 'Introduced HIGH was not held.' }
if ((Get-CveUpdateImpact '2' '2.1' @($vuln) -HoldLevel Medium).Held) { throw 'Persistent CVE held an update.' }
if ((Get-CveUpdateImpact '1' '2' @($vuln) -HoldLevel High -IgnoreHold).Held) { throw 'Override did not work.' }
$vuln.is_kev = $true; $vuln.severity = 'LOW'
if (-not (Get-CveUpdateImpact '1' '2' @($vuln) -HoldLevel Critical).Held) { throw 'Introduced KEV was not held.' }
$unknown = @{ cve_id = 'unknown'; severity = 'CRITICAL'; is_kev = $true }
$impact = Get-CveUpdateImpact '1' '2' @($unknown) -HoldLevel Medium
if ($impact.Held -or $impact.Records[0].Classification -ne 'Indeterminate') { throw 'Unknown range was treated as assessable.' }
if ((Get-CveUpdateImpact '1' 'unknown' @($vuln) -HoldLevel Medium).Held) { throw 'Unknown target version triggered a hold.' }
$range = @{ affected_version_start = '1.2.3.4.5'; affected_version_start_type = 'excluding' }
if ((Test-CveVersionAffected '1.2.3.4.5' $range) -ne $false -or (Test-CveVersionAffected '1.2.3.4.6' $range) -ne $true) { throw 'Open-ended exclusive range failed.' }
$range = @{ fixed_version = '2' }
if ((Test-CveVersionAffected '1.9' $range) -ne $true -or (Test-CveVersionAffected '2' $range) -ne $false) { throw 'Fixed-version boundary failed.' }
$range = @{ affected_version_end = '2'; affected_version_end_type = 'including' }
if ((Test-CveVersionAffected '2' $range) -ne $true -or (Test-CveVersionAffected '2.0.1' $range) -ne $false) { throw 'Inclusive upper boundary failed.' }
$range = @{ affected_version_start = '3'; affected_version_start_type = 'including'; fixed_version = '2' }
if ($null -ne (Test-CveVersionAffected '1' $range)) { throw 'Contradictory range accepted.' }
Write-Host 'Version-aware CVE classification, boundary, hold, and override tests passed.'
# Exercise the actual selection block before any upload code, including its exit status.
$source = Get-Content (Join-Path $PSScriptRoot '../IntuneBrew.ps1') -Raw
$start = $source.IndexOf('$heldApps = @($appsToUpload')
$end = $source.IndexOf('# Check if there are apps to process', $start)
$selection = $source.Substring($start, $end - $start)
$fixture = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString() + '.ps1')
try {
    @'
function Disconnect-MgGraph {}
$appsToUpload = @([pscustomobject]@{ FormattedName='Held'; IntuneVersion='1'; GitHubVersion='2'; SecurityHeld=$true })
'@ + "`n$selection" | Set-Content $fixture
    & pwsh -NoProfile -File $fixture *> $null
    if ($LASTEXITCODE -ne 2) { throw 'A fully held run did not return exit code 2.' }
    @'
function Disconnect-MgGraph {}
$appsToUpload = @([pscustomobject]@{ FormattedName='Held'; SecurityHeld=$true }, [pscustomobject]@{ FormattedName='Allowed'; SecurityHeld=$false })
'@ + "`n$selection`n" + @'
if ($appsToUpload.Count -ne 1 -or $appsToUpload[0].FormattedName -ne 'Allowed') { throw 'Held app reached upload selection.' }
'@ | Set-Content $fixture
    & pwsh -NoProfile -File $fixture *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Allowed updates were blocked with the held app.' }
}
finally { Remove-Item $fixture -Force }
