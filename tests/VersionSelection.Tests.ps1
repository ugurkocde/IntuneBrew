param([string]$ExtractedFunctionDirectory)

$ErrorActionPreference = 'Stop'
foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
    $tokens = $null; $errors = $null
    $sourcePath = if ($ExtractedFunctionDirectory) { Join-Path $ExtractedFunctionDirectory $file } else { Join-Path $PSScriptRoot "../$file" }
    $source = [IO.File]::ReadAllText($sourcePath, [Text.UTF8Encoding]::new($false))
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
    if (-not $ExtractedFunctionDirectory) {
        $lookupName = if ($file -eq 'IntuneBrew.ps1') { 'Get-IntuneApp' } else { 'Get-IntuneApps' }
        $lookup = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $lookupName }, $true)
        $calls = @($lookup.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Select-LatestAppRecord' }, $true))
        $expectedCount = if ($file -eq 'IntuneBrew.ps1') { 1 } else { 2 }
        if ($calls.Count -ne $expectedCount) { throw "Not all lookup paths use the selector in $file" }
        $sortableCalls = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Convert-VersionToSortable' }, $true))
        if ($sortableCalls.Count -lt 1 -or @($sortableCalls | Where-Object { $_.Extent.StartOffset -lt $selector.Extent.StartOffset -or $_.Extent.EndOffset -gt $selector.Extent.EndOffset }).Count -ne 0) { throw 'Sortable keys used outside the selector.' }
    }

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
    # Same-core stable ordinals must select the same original app ID in every input order.
    foreach ($custom in @($false, $true)) {
        foreach ($versions in @(@('2.152.0-stable.3', '2.152.0-stable.4'), @('2.152.0-stable.9', '2.152.0-stable.10'), @('2.152.0-stable.0', '2.152.0-stable.999999999'))) {
            $older = @{ id = 'fixture-older'; primaryBundleVersion = $versions[0] }
            $newer = @{ id = 'fixture-newer'; primaryBundleVersion = $versions[1] }
            if ($custom) { $older = [pscustomobject]$older; $newer = [pscustomobject]$newer }
            foreach ($records in @(@($older, $newer), @($newer, $older))) {
                if (-not [object]::ReferenceEquals((Select-LatestAppRecord $records), $newer)) { throw 'Stable ordinal selected the wrong app identity.' }
            }
            if (-not (& $updater $versions[1] $versions[0]) -or (& $updater $versions[0] $versions[1])) { throw 'Stable selector and updater disagree.' }
        }
        $records = @('2.152.0-stable.3','2.152.0-stable.10','2.152.0-stable.4' | ForEach-Object { @{ id = ('fixture-' + $_); primaryBundleVersion = $_ } })
        if ($custom) { $records = @($records | ForEach-Object { [pscustomobject]$_ }) }
        foreach ($indices in @(@(0,1,2),@(0,2,1),@(1,0,2),@(1,2,0),@(2,0,1),@(2,1,0))) {
            if (-not [object]::ReferenceEquals((Select-LatestAppRecord @($records[$indices[0]],$records[$indices[1]],$records[$indices[2]])), $records[1])) { throw 'Stable ordinal depends on input order.' }
        }
        $lowerUnproven = @{ id = 'fixture-lower-core'; primaryBundleVersion = '2.151.0-Stable.999' }
        if (-not [object]::ReferenceEquals((Select-LatestAppRecord (@($lowerUnproven) + $records)), $records[1])) { throw 'Lower non-tied group changed the winner.' }
    }
    # Any unsupported item in the winning tie keeps the exact legacy result, in either order.
    foreach ($bad in @('2.152.0', '2.152.0-Stable.99','2.152.0-beta.99','2.152.0-stable.04','02.152.0-stable.99','2.152.0-stable.1000000000',"2.152.0-stable.99`n",('2.152.0-stable.'+[char]0x0664),'2.152.0-stable.99+1','2.152.0-stable.99(ABCD)','2.152.0.0-stable.99','2.152-stable.99')) {
        $good = @{ id = 'fixture-canonical'; primaryBundleVersion = '2.152.0-stable.4' }; $other = @{ id = 'fixture-unsupported'; primaryBundleVersion = $bad }
        foreach ($records in @(@($good,$other),@($other,$good))) {
            $legacy = $records | Sort-Object -Property @{Expression = { Convert-VersionToSortable $_.primaryBundleVersion } } -Descending | Select-Object -First 1
            if (-not [object]::ReferenceEquals((Select-LatestAppRecord $records), $legacy)) { throw ('Unsupported tie changed legacy identity: '+$bad) }
        }
    }
    $duplicateA=@{id='fixture-a';primaryBundleVersion='2.152.0-stable.4'};$duplicateB=@{id='fixture-b';primaryBundleVersion='2.152.0-stable.4'}
    foreach($records in @(@($duplicateA,$duplicateB),@($duplicateB,$duplicateA))){
        $legacy=$records | Sort-Object -Property @{Expression={Convert-VersionToSortable $_.primaryBundleVersion}} -Descending | Select-Object -First 1
        if(-not [object]::ReferenceEquals((Select-LatestAppRecord $records),$legacy)){throw 'Equal ordinal changed legacy identity.'}
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

# Windows PowerShell receives only extracted helpers, never the PowerShell 7 product scripts.
if (-not $ExtractedFunctionDirectory -and $env:OS -eq 'Windows_NT' -and $PSVersionTable.PSEdition -ne 'Desktop') {
    $windowsPowerShell = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
    if (-not (Test-Path -LiteralPath $windowsPowerShell)) { throw 'Windows PowerShell runtime is missing.' }
    $fixtureDirectory = Join-Path ([IO.Path]::GetTempPath()) ('IntuneBrew-NumericCompatibility-' + [guid]::NewGuid().ToString('N'))
    if (Test-Path -LiteralPath $fixtureDirectory) { throw 'Compatibility fixture already exists.' }
    $null = [IO.Directory]::CreateDirectory($fixtureDirectory)
    try {
        foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
            $source = [IO.File]::ReadAllText((Join-Path $PSScriptRoot "../$file"), [Text.UTF8Encoding]::new($false))
            $tokens = $null; $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
            if ($errors.Count) { throw ($errors | Out-String) }
            $updater = if ($file -eq 'IntuneBrew.ps1') { 'Test-NewerVersion' } else { 'Is-NewerVersion' }
            $functions = foreach ($name in @('ConvertTo-NumericBundleVersion', 'Compare-NumericBundleVersion', 'Convert-VersionToSortable', 'Select-LatestAppRecord', 'Compare-VersionSegments', $updater)) {
                $definition = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
                if (-not $definition) { throw "Required function missing: $name" }
                $definition.Extent.Text
            }
            [IO.File]::WriteAllText((Join-Path $fixtureDirectory $file), ($functions -join "`n"), [Text.UTF8Encoding]::new($false))
        }
        & $windowsPowerShell -NoProfile -NonInteractive -File $PSCommandPath -ExtractedFunctionDirectory $fixtureDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Windows PowerShell numeric selection regression failed.' }
    }
    finally { Remove-Item -LiteralPath $fixtureDirectory -Recurse -Force }
}
