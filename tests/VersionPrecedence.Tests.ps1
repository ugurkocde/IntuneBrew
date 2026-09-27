$ErrorActionPreference = 'Stop'
foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot "../$file"), [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw ($errors | Out-String) }
    $comparator = if ($file -eq 'IntuneBrew_Runbook.ps1') { 'Is-NewerVersion' } else { 'Test-NewerVersion' }
    foreach ($name in @('Compare-VersionSegments', $comparator)) {
        $function = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
        Invoke-Expression $function.Extent.Text
    }
    foreach ($case in @(
        @('1.2.3-rc1','1.2.3',$false), @('1.2.3','1.2.3-rc1',$true),
        @('1.2.3-rc.10','1.2.3-rc.2',$true), @('1.2','1.2.0',$false),
        @('2.0-rc1','1.9',$true), @('1.2.3,101','1.2.3,100',$true)
    )) {
        if ((& $comparator $case[0] $case[1]) -ne $case[2]) { throw "Incorrect version precedence in $file`: $case" }
    }
}
Write-Host 'Release, prerelease, build, and normalized-version comparisons passed.'
