# Run the same security differential corpus on the deployed Automation engine version.
$ErrorActionPreference = 'Stop'
$directory = $null
try {
    $executable = $env:INTUNEBREW_PWSH74
    if ([string]::IsNullOrEmpty($executable)) {
        if ($env:GITHUB_ACTIONS -ne 'true') { throw 'Set INTUNEBREW_PWSH74 to the verified PowerShell 7.4.6 executable.' }
        $architecture = [Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
        if ($IsWindows -and $architecture -eq 'X64') {
            $asset = 'PowerShell-7.4.6-win-x64.zip'; $expected = 'ed49ce5adb2162cc4a835d740486be729ba904627cca71fcb6c2b95be11b993d'
        } elseif ($IsLinux -and $architecture -eq 'X64') {
            $asset = 'powershell-7.4.6-linux-x64.tar.gz'; $expected = '6f6015203c47806c5cc444c19d8ed019695e610fbd948154264bf9ca8e157561'
        } elseif ($IsMacOS -and $architecture -eq 'Arm64') {
            $asset = 'powershell-7.4.6-osx-arm64.tar.gz'; $expected = 'a482d668787ef98c37f0a5a7696107dffdb3dc340c5be3d1c153ec9d239072a8'
        } elseif ($IsMacOS -and $architecture -eq 'X64') {
            $asset = 'powershell-7.4.6-osx-x64.tar.gz'; $expected = '7a18daed105b7cfc80bf8cc00762fe7990105dd23f951cc32ceb744651650e3d'
        } else { throw 'No pinned PowerShell 7.4.6 archive for this test host.' }
        $directory = Join-Path ([IO.Path]::GetTempPath()) ('IntuneBrew-CvePS74-' + [guid]::NewGuid().ToString('N'))
        $null = [IO.Directory]::CreateDirectory($directory)
        if (-not $IsWindows) { & chmod 700 $directory; if ($LASTEXITCODE -ne 0) { throw 'Cannot protect test directory.' } }
        $archive = Join-Path $directory $asset
        # Immutable Microsoft release, with its published digest checked before extraction/execution.
        try {
            Invoke-WebRequest ('https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/' + $asset) -OutFile $archive -TimeoutSec 90
        } catch { throw 'Pinned PowerShell 7.4.6 download failed.' }
        if ((Get-Item -LiteralPath $archive).Length -gt 512MB -or
            (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) { throw 'PowerShell 7.4.6 archive integrity failed.' }
        $runtime = Join-Path $directory 'runtime'; $null = [IO.Directory]::CreateDirectory($runtime)
        if ($IsWindows) {
            Expand-Archive -LiteralPath $archive -DestinationPath $runtime
            $executable = Join-Path $runtime 'pwsh.exe'
        } else {
            & tar -xzf $archive -C $runtime
            if ($LASTEXITCODE -ne 0) { throw 'Pinned PowerShell archive extraction failed.' }
            $executable = Join-Path $runtime 'pwsh'; & chmod 700 $executable
            if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare verified runtime executable.' }
        }
    }
    if (-not [IO.File]::Exists($executable)) { throw 'Verified PowerShell 7.4.6 executable is missing.' }
    $version = & $executable -NoProfile -NonInteractive -Command '$PSVersionTable.PSVersion.ToString()'
    if ($LASTEXITCODE -ne 0 -or $version -cne '7.4.6') { throw 'Unexpected compatibility-test runtime version.' }
    & $executable -NoProfile -NonInteractive -File (Join-Path $PSScriptRoot 'CveCompactParity.Tests.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'PowerShell 7.4.6 full/compact CVE evaluator parity failed.' }
    Write-Host 'PowerShell 7.4.6 full/compact CVE evaluator parity passed.'
}
finally {
    if ($null -ne $directory -and (Test-Path -LiteralPath $directory)) { Remove-Item -LiteralPath $directory -Recurse -Force }
}
