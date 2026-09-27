$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../IntuneBrew.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$function = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Set-IntuneVersionDetection' }, $true)
Invoke-Expression $function.Extent.Text
foreach ($value in @($true, $false)) {
    $payload = @{ primaryBundleVersion = '2.0'; ignoreVersionDetection = -not $value }
    Set-IntuneVersionDetection -Payload $payload -Options @{ IgnoreVersionDetection = $value }
    if ($payload.ignoreVersionDetection -ne $value -or $payload.primaryBundleVersion -ne '2.0') { throw 'Explicit detection option was not applied independently of the app version.' }
}
$payload = @{ ignoreVersionDetection = $true }
Set-IntuneVersionDetection -Payload $payload -Options @{}
if (-not $payload.ignoreVersionDetection) { throw 'Omitting the option changed existing detection behavior.' }
$payload = @{}
Set-IntuneVersionDetection -Payload $payload -Options @{ IgnoreAppVersion = $true }
if ($payload.ContainsKey('ignoreVersionDetection')) { throw 'The older comparison flag changed device detection.' }
Write-Host 'Version detection parameter tests passed.'

& {
    param([switch]$IgnoreVersionDetection)
    $payload = @{}
    Set-IntuneVersionDetection -Payload $payload -Options $PSBoundParameters
    if (-not $payload.ContainsKey('ignoreVersionDetection') -or $payload.ignoreVersionDetection -ne $false) { throw 'Explicit false switch binding was lost.' }
} -IgnoreVersionDetection:$false
