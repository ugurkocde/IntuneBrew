$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../IntuneBrew.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$definition = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-IntuneAppCollection' }, $true)
Invoke-Expression $definition.Extent.Text
$script:calls = 0
function Invoke-MgGraphRequest {
    param($Uri, $Method)
    $script:calls++
    if ($script:calls -eq 1) {
        if ($Uri -notmatch '%26') { throw 'Filter was not URL-encoded.' }
        return @{ value = @(); '@odata.nextLink' = 'https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?$skiptoken=fixture' }
    }
    return @{ value = @(@{ id = 'fixture' }) }
}
$result = Get-IntuneAppCollection -Filter "displayName eq 'App & Co'"
if ($script:calls -ne 2 -or $result.value.Count -ne 1 -or $result.value[0].id -ne 'fixture') { throw 'Empty-page pagination failed.' }
Write-Host 'Graph paging tests passed.'
