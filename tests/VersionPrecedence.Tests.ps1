$ErrorActionPreference = 'Stop'
foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot "../$file"), [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw ($errors | Out-String) }
    $comparator = if ($file -eq 'IntuneBrew_Runbook.ps1') { 'Is-NewerVersion' } else { 'Test-NewerVersion' }
    $requiredFunctions = @('Compare-VersionSegments', 'ConvertTo-NumericBundleVersion', 'Compare-NumericBundleVersion', 'Select-LatestAppRecord', $comparator, 'Convert-VersionToSortable')
    foreach ($name in $requiredFunctions) {
        $function = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
        foreach ($command in $function.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
            $dependency = $command.GetCommandName()
            if ($dependency -in @('ConvertTo-NumericBundleVersion', 'Compare-NumericBundleVersion', 'Select-LatestAppRecord') -and $dependency -notin $requiredFunctions) { throw "Unextracted dependency: $dependency" }
        }
        Invoke-Expression $function.Extent.Text
    }
    foreach ($case in @(
        @('1.2.3-rc1','1.2.3',$false), @('1.2.3','1.2.3-rc1',$true),
        @('1.2.3-rc.10','1.2.3-rc.2',$true), @('1.2','1.2.0',$false),
        @('1.2.3,100','1.2.3,100-rc1',$true), @('1.2.3,100-rc1','1.2.3,100',$false),
        @('2.0-rc1','1.9',$true), @('1.2.3,101','1.2.3,100',$true),
        @('0.4.28+10','0.4.28+2',$true), @('0.4.28+2','0.4.28+10',$false),
        @('0.4.10+2','0.4.9+2',$true), @('0.4.9+2','0.4.10+2',$false),
        @('0.4.28+2','0.4.28',$true), @('0.4.28','0.4.28+2',$false),
        @('0.4.28+2','0.4.28+2',$false), @('0.4.28+0002','0.4.28+2',$false),
        @('0.4.28+0','0.4.28',$false), @('0.4.28+0','0.4.28.0',$false),
        @('2026.10.0+123','2026.10.0+99',$true),
        @('0.4.28+9007199254740993','0.4.28+9007199254740992',$true),
        @('0.4.28+100000000000000000000','0.4.28+99999999999999999999',$true),
        @('0.4.9007199254740993+2','0.4.9007199254740992+2',$true),
        @('1.2.3+build.10','1.2.3+build.2',$true),
        @('1.2.3-rc.1+10','1.2.3-rc.1+2',$false)
    )) {
        if ((& $comparator $case[0] $case[1]) -ne $case[2]) { throw "Incorrect version precedence in $file`: $case" }
    }
    # Compatibility vectors from held artifact observations; these do not approve publication.
    foreach ($case in @(
        @('160.0','159.0b4',$true), @('159.0b4','160.0',$false), @('160.0','160.0',$false), # firefox@developer-edition
        @('5.8.2(095C)','5.8.1',$true), @('5.8.1','5.8.2(095C)',$false), @('5.8.2(095C)','5.8.2(095C)',$false), # steermouse
        @('2026.10.261408-latest','2026.10.121159',$true), @('2026.10.121159','2026.10.261408-latest',$false), @('2026.10.261408-latest','2026.10.261408-latest',$false), # lens
        @('10.0.2 (build 6590)','10.0.1',$true), @('10.0.1','10.0.2 (build 6590)',$false), @('10.0.2 (build 6590)','10.0.2 (build 6590)',$false), # tunnelblick
        @('4.2.0','4.1.15.55',$true), @('4.1.15.55','4.2.0',$false), @('4.2.0','4.2.0',$false), # wechat
        @('27.1.0','27.0.3-58680',$true), @('27.0.3-58680','27.1.0',$false), @('27.1.0','27.1.0',$false), # parallels
        @('1.207.0','1.202.0.0',$true), @('1.202.0.0','1.207.0',$false), @('1.207.0','1.207.0',$false), # grammarly-desktop
        @('27.01.05087','26.05.01107-202609082317',$true), @('26.05.01107-202609082317','27.01.05087',$false), @('27.01.05087','27.01.05087',$false), # xmind
        @('2026.2','2026.2.1.8',$false), @('2026.2.1.8','2026.2',$true), @('2026.2','2026.2',$false), # android-studio
        @('156.1.98.63','1.97.59.0',$true), @('1.97.59.0','156.1.98.63',$false), @('156.1.98.63','156.1.98.63',$false), # brave-browser
        @('9.7.1','9.5.0.4590',$true), @('9.5.0.4590','9.7.1',$false), @('9.7.1','9.7.1',$false), # capcut
        @('6.6.1-demo','6.6.0',$true), @('6.6.0','6.6.1-demo',$false), @('6.6.1-demo','6.6.1-demo',$false), # hopper-disassembler
        @('18.6.6','18.6.5',$true), @('18.6.5','18.6.6',$false), @('18.6.6','18.6.6',$false), # keeper-password-manager
        @('26.8.2.2','26.8.1',$true), @('26.8.1','26.8.2.2',$false), @('26.8.2.2','26.8.2.2',$false), # libreoffice
        @('0.4.28+2','0.4.26',$true), @('0.4.26','0.4.28+2',$false), @('0.4.28+2','0.4.28+2',$false), # lm-studio
        @('139.0','138.0.6044.24',$true), @('138.0.6044.24','139.0',$false), @('139.0','139.0',$false), # opera
        @('8.38.4','8.37.2-1',$true), @('8.37.2-1','8.38.4',$false), @('8.38.4','8.38.4',$false), # 8x8-work
        @('4.7.6','4.7.5.260831071',$true), @('4.7.5.260831071','4.7.6',$false), @('4.7.6','4.7.6',$false), # musescore
        @('2026.11.03','2026.10.02.902',$true), @('2026.10.02.902','2026.11.03',$false), @('2026.11.03','2026.11.03',$false), # expandrive
        @('26.10.1','26.9.0-0',$true), @('26.9.0-0','26.10.1',$false), @('26.10.1','26.10.1',$false), # hoppscotch
        @('139.0','137.0.6036.65',$true), @('137.0.6036.65','139.0',$false), @('139.0','139.0',$false), # opera-gx
        @('7.84.0_310d2afu','7.82',$true), @('7.82','7.84.0_310d2afu',$false), @('7.84.0_310d2afu','7.84.0_310d2afu',$false), # reaper
        @('2.5.1(2F17)','2.5',$true), @('2.5','2.5.1(2F17)',$false), @('2.5.1(2F17)','2.5.1(2F17)',$false), # cursorsense
        @('12.11.12.2','12.11.11',$true), @('12.11.11','12.11.12.2',$false), @('12.11.12.2','12.11.12.2',$false), # goodsync
        @('0.99','0.98.8.0',$true), @('0.98.8.0','0.99',$false), @('0.99','0.99',$false), # jasp
        @('6.7.0','6.6.2.0',$true), @('6.6.2.0','6.7.0',$false), @('6.7.0','6.7.0',$false), # megasync
        @('3.35','3.32.721',$true), @('3.32.721','3.35',$false), @('3.35','3.35',$false), # numi
        @('2.152.0-stable.3','2.150.0',$true), @('2.150.0','2.152.0-stable.3',$false), @('2.152.0-stable.3','2.152.0-stable.3',$false), # pitch
        @('26.202.0','26.180.0.11926',$true), @('26.180.0.11926','26.202.0',$false), @('26.202.0','26.202.0',$false), # shapr3d
        @('0.65.2','0.65.2',$false), @('0.65.2','0.65.2',$false), @('0.65.2','0.65.2',$false), # cmux
        @('4.5.102000','4.4',$true), @('4.4','4.5.102000',$false), @('4.5.102000','4.5.102000',$false) # winbox
    )) {
        if ((& $comparator $case[0] $case[1]) -ne $case[2]) { throw "Catalog format changed in $file`: $case" }
    }

}
Write-Host 'Release, prerelease, build, and normalized-version comparisons passed.'
