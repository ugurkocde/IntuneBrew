$ErrorActionPreference = 'Stop'
foreach ($file in @('IntuneBrew.ps1', 'IntuneBrew_Runbook.ps1')) {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot "../$file"), [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw ($errors | Out-String) }
    $function = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Compare-VersionSegments' }, $true)
    if (-not $function) { throw "Version comparator missing in $file" }
    Invoke-Expression $function.Extent.Text
    foreach ($case in @(
        @('21.0.8.9.1', '21.0.8.9', 1),
        @('6.10.0.252.3', '6.9.1.1', 1),
        @('1.2.3.4.5', '1.2.3.4.6', -1),
        @('1.2.3.4.5', '1.2.3.4.5', 0),
        @('1.2', '1.2.0.0.0', 0)
    )) {
        if ((Compare-VersionSegments $case[0] $case[1]) -ne $case[2]) { throw "Incorrect comparison in $file`: $case" }
    }
}
Write-Host 'Long version comparison tests passed for the CLI and runbook.'
