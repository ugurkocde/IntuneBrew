$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '../IntuneBrew.ps1'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Resolve-LocalManifestPath', 'Remove-LocalAppFile', 'Get-LocalAppFile', 'Get-AppFile', 'Get-GitHubAppInfo')) {
    $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
    Invoke-Expression $definition.Extent.Text
}
function Assert-Throws([scriptblock]$Action) {
    $thrown = $false
    try { & $Action | Out-Null } catch { $thrown = $true }
    if (-not $thrown) { throw 'Expected operation to fail.' }
}
$root = Join-Path ([System.IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
[System.IO.Directory]::CreateDirectory($root) | Out-Null
try {
    $installer = Join-Path $root 'Installer with spaces.pkg'
    [System.IO.File]::WriteAllText($installer, 'fixture payload')
    $sha = (Get-FileHash -LiteralPath $installer).Hash
    $uri = ([Uri]::new($installer, [UriKind]::Absolute)).AbsoluteUri
    foreach ($location in @($uri, 'file://./Installer%20with%20spaces.pkg')) {
        $copy = Get-LocalAppFile -FileUri $location -FileName 'app.pkg' -ExpectedHash $sha -BaseDirectory $root
        if ($copy -eq $installer -or (Get-FileHash $copy).Hash -ne $sha) { throw 'Copy verification failed.' }
        [System.IO.File]::WriteAllText("$copy.bin", 'encrypted fixture')
        Remove-LocalAppFile -Path $copy
        Remove-LocalAppFile -Path $copy
        if (Test-Path (Split-Path $copy)) { throw 'Temporary directory was not cleaned.' }
        Remove-LocalAppFile -Path $installer
        if (-not (Test-Path $installer)) { throw 'Cleanup removed an unowned installer.' }
    }
    Assert-Throws { Get-LocalAppFile -FileUri $uri -FileName '../app.pkg' -ExpectedHash $sha }
    Assert-Throws { Get-LocalAppFile -FileUri $uri -FileName 'app.pkg' -ExpectedHash ('0' * 64) }
    Assert-Throws { Get-LocalAppFile -FileUri $uri -FileName 'app.pkg' -ExpectedHash '' }
    Assert-Throws { Get-LocalAppFile -FileUri 'file://./../outside.pkg' -FileName 'app.pkg' -ExpectedHash $sha -BaseDirectory $root }
    Assert-Throws { Get-LocalAppFile -FileUri 'file://server/share/app.pkg' -FileName 'app.pkg' -ExpectedHash $sha }
    Assert-Throws { Get-AppFile -url $uri -fileName 'app.pkg' -expectedHash $sha }
    if ((Get-FileHash -LiteralPath $installer).Hash -ne $sha) { throw 'The source installer was modified.' }
    $LocalJsonDirectory = $root
    $localJsonOverrides = @{ app = (Join-Path $root 'app.json') }
    if ((Resolve-LocalManifestPath -JsonUrl ('file://' + $localJsonOverrides.app)) -ne $localJsonOverrides.app) { throw 'Explicit local manifest rejected.' }
    Assert-Throws { Resolve-LocalManifestPath -JsonUrl ('file://' + (Join-Path $root 'unselected.json')) }
    Write-Host 'Local installer verification passed.'
}
finally { Remove-Item -LiteralPath $root -Recurse -Force }
