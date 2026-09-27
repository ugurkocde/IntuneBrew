$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../IntuneBrew.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Test-LocalUploadArguments', 'New-LocalUploadInfo', 'Get-GitHubAppInfo', 'Test-ValidUrl')) {
    $function = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    Invoke-Expression $function.Extent.Text
}
$root = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
[IO.Directory]::CreateDirectory($root) | Out-Null
try {
    $path = Join-Path $root 'Company VPN.pkg'
    Set-Content -LiteralPath $path -Value 'fixture'
    $config = Join-Path $root 'config.json'
    @{ name = 'Company VPN'; version = '1.2.3'; bundleId = 'com.example.vpn' } | ConvertTo-Json | Set-Content $config
    $info = New-LocalUploadInfo -Path $path -MetadataPath $config -Version '1.2.4'
    if ($info.version -ne '1.2.4' -or $info.name -ne 'Company VPN' -or $info.sha -ne (Get-FileHash $path).Hash) { throw 'Metadata or checksum incorrect.' }
    if ($info.url -notmatch '^file:' -or $info.localManifestDirectory -ne $root) { throw 'Installer source incorrect.' }
    $script:ExplicitLocalAppInfo = $info
    if (-not (Test-ValidUrl 'local-upload://selected')) { throw 'Explicit upload was rejected.' }
    if ((Get-GitHubAppInfo 'local-upload://selected').bundleId -ne 'com.example.vpn') { throw 'Local upload did not enter the normal metadata flow.' }
    $threw = $false
    try { New-LocalUploadInfo -Path $path -Name 'Incomplete' | Out-Null } catch { $threw = $true }
    if (-not $threw) { throw 'Incomplete metadata accepted.' }
    @{ name = 'Company VPN'; version = '1'; bundleId = 'com.example.vpn'; sha = ('0' * 64) } | ConvertTo-Json | Set-Content $config
    $threw = $false
    try { New-LocalUploadInfo -Path $path -MetadataPath $config | Out-Null } catch { $threw = $true }
    if (-not $threw) { throw 'Incorrect checksum accepted.' }
    Write-Host 'Explicit local upload metadata tests passed.'
}
finally { Remove-Item $root -Recurse -Force }

Test-LocalUploadArguments -Options @{}
foreach ($key in @('LocalFilePath', 'LocalFileConfig', 'LocalFileAppName', 'LocalFileVersion', 'LocalFileBundleID')) {
    $threw = $false
    try { Test-LocalUploadArguments -Options @{ $key = '  ' } } catch { $threw = $true }
    if (-not $threw) { throw "Explicit blank $key was accepted." }
}
