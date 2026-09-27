# Internal child-process entry point. The invocation file contains paths and options, not credentials.
param([Parameter(Mandatory)][string]$InvocationPath)
$ErrorActionPreference = 'Stop'
try {
    $invocation = Get-Content -LiteralPath $InvocationPath -Raw | ConvertFrom-Json -AsHashtable
    Set-Location -LiteralPath $invocation.WorkingDirectory
    [Environment]::CurrentDirectory = $invocation.WorkingDirectory
    $parameters = $invocation.Parameters
    $global:LASTEXITCODE = 0
    & $invocation.ScriptPath @parameters
    exit $LASTEXITCODE
}
catch { exit 1 }
