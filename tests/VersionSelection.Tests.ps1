$ErrorActionPreference = 'Stop'
foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
    $tokens = $null; $errors = $null
    $source = [IO.File]::ReadAllText((Join-Path $PSScriptRoot "../$file"), [Text.UTF8Encoding]::new($false))
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw ($errors | Out-String) }
    $updater = if ($file -eq 'IntuneBrew.ps1') { 'Test-NewerVersion' } else { 'Is-NewerVersion' }
    $required = @('ConvertTo-NumericBundleVersion', 'Compare-NumericBundleVersion', 'Convert-VersionToSortable', 'Select-LatestAppRecord', 'Compare-VersionSegments', $updater)
    foreach ($name in $required) {
        $definition = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
        if (-not $definition) { throw "Required function missing: $name" }
        foreach ($command in $definition.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
            $dependency = $command.GetCommandName()
            if ($dependency -in @('ConvertTo-NumericBundleVersion', 'Compare-NumericBundleVersion', 'Select-LatestAppRecord') -and $dependency -notin $required) { throw "Unextracted dependency: $dependency" }
        }
        Invoke-Expression $definition.Extent.Text
    }
    foreach ($bad in @($null, '', '1', '1.2+build.1', '1.2,3', '1.2-rc1', "1.2+3`n", "1.2`r`n", ' 1.2+3', ('1.2+' + [char]0x0663))) {
        if ($null -ne (ConvertTo-NumericBundleVersion $bad)) { throw "Non-numeric bundle format accepted in $file" }
    }
    $fallback = '$Apps | Sort-Object -Property @{Expression = { Convert-VersionToSortable $_.primaryBundleVersion } } -Descending | Select-Object -First 1'
    $selector = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Select-LatestAppRecord' }, $true)
    if (-not $selector.Extent.Text.Contains($fallback)) { throw 'Legacy selection pipeline changed.' }
    $lookupName = if ($file -eq 'IntuneBrew.ps1') { 'Get-IntuneApp' } else { 'Get-IntuneApps' }
    $lookup = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $lookupName }, $true)
    $calls = @($lookup.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Select-LatestAppRecord' }, $true))
    $expectedCount = if ($file -eq 'IntuneBrew.ps1') { 1 } else { 2 }
    if ($calls.Count -ne $expectedCount) { throw "Not all lookup paths use the selector in $file" }
    $sortableCalls = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Convert-VersionToSortable' }, $true))
    if ($sortableCalls.Count -ne 1 -or $sortableCalls[0].Extent.StartOffset -lt $selector.Extent.StartOffset -or $sortableCalls[0].Extent.EndOffset -gt $selector.Extent.EndOffset) { throw 'Sortable keys used outside the legacy fallback.' }

    foreach ($custom in @($false, $true)) {
        foreach ($pair in @(
            @('0.4.28.0+10', '0.4.28+2'),
            @('0.4.28+100000000000000000000', '0.4.28+99999999999999999999'),
            @('0.4.28+10', '0.4.28+2'), @('0.4.10+2', '0.4.9+2'),
            @('0.4.28+2', '0.4.28'), @('2026.10.0+123', '2026.10.0+99'),
            @('1.10', '1.2+1'), @('0.4.28.1', '0.4.28+999'),
            @('0.4.100000000000000000000000000000000000000000000000001+2', '0.4.100000000000000000000000000000000000000000000000000+99'),
            @('0.4.28+100000000000000000000000000000000000000000000000001', '0.4.28+99999999999999999999999999999999999999999999999999')
        )) {
            $winner = @{ id = 'fake-newer'; primaryBundleVersion = $pair[0] }
            $older = @{ id = 'fake-older'; primaryBundleVersion = $pair[1] }
            if ($custom) { $winner = [pscustomobject]$winner; $older = [pscustomobject]$older }
            foreach ($records in @(@($winner, $older), @($older, $winner))) {
                $actual = @(Select-LatestAppRecord $records)
                if ($actual.Count -ne 1 -or -not [object]::ReferenceEquals($actual[0], $winner)) { throw "Wrong record selected in $file`: $pair" }
            }
            $script:IgnoreAppVersion = $false
            if (-not (& $updater $pair[0] $pair[1]) -or (& $updater $pair[1] $pair[0])) { throw "Updater and selector disagree in $file`: $pair" }
        }
        foreach ($versions in @(@('0.4.28+0002', '0.4.28.0+2'), @('0.4.28', '0.4.28.0+0'))) {
            $first = @{ id = 'fake-first'; primaryBundleVersion = $versions[0] }
            $second = @{ id = 'fake-second'; primaryBundleVersion = $versions[1] }
            if ($custom) { $first = [pscustomobject]$first; $second = [pscustomobject]$second }
            if (-not [object]::ReferenceEquals((Select-LatestAppRecord @($first, $second)), $first)) { throw 'Numeric tie did not keep the first record.' }
        }
        $singleton = @{ id = 'fake-single'; primaryBundleVersion = '0.4.28+2' }
        if ($custom) { $singleton = [pscustomobject]$singleton }
        if (-not [object]::ReferenceEquals((Select-LatestAppRecord @($singleton)), $singleton)) { throw 'Singleton record identity changed.' }
    }
    if ($null -ne (Select-LatestAppRecord $null) -or $null -ne (Select-LatestAppRecord @())) { throw 'Empty input should return null.' }
    # Invalid, mixed-format and bare-only groups deliberately retain their old ordering.
    foreach ($versions in @(@('1.2,10', '1.2,2'), @('1.2-rc1', '1.3'), @('latest', '2.0'), @('1.2+2', '1.2,3'), @($null, '1.2+3'), @('1.2', '1.10'))) {
        $records = @($versions | ForEach-Object { @{ primaryBundleVersion = $_ } })
        $legacy = $records | Sort-Object -Property @{Expression = { Convert-VersionToSortable $_.primaryBundleVersion } } -Descending | Select-Object -First 1
        if (-not [object]::ReferenceEquals((Select-LatestAppRecord $records), $legacy)) { throw "Legacy fallback changed in $file" }
    }
    $older = @{ primaryBundleVersion = '0.4.28+2' }; $newer = @{ primaryBundleVersion = '0.4.28.0+10' }
    $script:IgnoreAppVersion = $true
    if (-not [object]::ReferenceEquals((Select-LatestAppRecord @($older, $newer)), $newer)) { throw 'Policy opt-out changed record selection.' }
    if ($file -eq 'IntuneBrew.ps1' -and (& $updater $newer.primaryBundleVersion $older.primaryBundleVersion)) { throw 'IgnoreAppVersion was bypassed.' }
    $script:IgnoreAppVersion = $false
    if (& $updater '0.4.28+10' 'Managed via VPP') { throw 'VPP opt-out was bypassed.' }
}
Write-Host 'Numeric record selection, identity, caller wiring and legacy fallback checks passed.'

# Exercise the Windows PowerShell runtime through the existing Windows CI job as well.
if ($env:OS -eq 'Windows_NT' -and $PSVersionTable.PSEdition -ne 'Desktop') {
    $windowsPowerShell = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
    if (-not (Test-Path -LiteralPath $windowsPowerShell)) { throw 'Windows PowerShell runtime is missing.' }
    & $windowsPowerShell -NoProfile -NonInteractive -File $PSCommandPath
    if ($LASTEXITCODE -ne 0) { throw 'Windows PowerShell numeric selection regression failed.' }
}
