$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '../IntuneBrew.ps1'
& pwsh -NoProfile -NonInteractive -File $script -Upload google_chrome -NonInteractive -ConfigFile (Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString() + '.json')) *> $null
if ($LASTEXITCODE -eq 0) { throw 'Missing authentication configuration reported success.' }
Write-Host 'Unattended authentication failures return a nonzero exit code.'
