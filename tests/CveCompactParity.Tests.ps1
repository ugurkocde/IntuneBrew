# Run the same security differential corpus on the deployed Automation engine version.
$ErrorActionPreference = 'Stop'
$directory = $null
$workers = @()
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
    $current = [Environment]::ProcessPath
    $expectedKeys = @(Get-ChildItem (Join-Path $PSScriptRoot '../CVE/*.json') | Sort-Object Name | ForEach-Object BaseName)
    $engines = @(@{ Label = 'current'; Path = $current; Version = $PSVersionTable.PSVersion.ToString() },
                 @{ Label = '7.4.6'; Path = $executable; Version = '7.4.6' })
    foreach ($engine in $engines) {
        foreach ($shard in 0,1) {
            $start = [Diagnostics.ProcessStartInfo]::new()
            $start.FileName = $engine.Path; $start.UseShellExecute = $false
            $start.RedirectStandardOutput = $true; $start.RedirectStandardError = $true
            foreach ($argument in @('-NoProfile', '-NonInteractive', '-File', (Join-Path $PSScriptRoot 'CveCompactParity.Corpus.ps1'),
                    '-ShardIndex', [string]$shard, '-ShardCount', '2')) { $start.ArgumentList.Add($argument) }
            $process = [Diagnostics.Process]::new(); $process.StartInfo = $start
            if (-not $process.Start()) { $process.Dispose(); throw 'Cannot start parity worker.' }
            $workers += @{ Process = $process; Output = $process.StandardOutput.ReadToEndAsync();
                Error = $process.StandardError.ReadToEndAsync(); Engine = $engine; Shard = $shard }
        }
    }
    $results = @()
    foreach ($worker in $workers) {
        $worker.Process.WaitForExit()
        $output = $worker.Output.GetAwaiter().GetResult(); $errorText = $worker.Error.GetAwaiter().GetResult()
        if ($worker.Process.ExitCode -ne 0) { throw ('Parity worker failed: ' + $worker.Engine.Label + '/' + $worker.Shard + ': ' + $errorText) }
        $result = $output | ConvertFrom-Json -ErrorAction Stop
        if ($result.Runtime -cne $worker.Engine.Version -or $result.ShardIndex -ne $worker.Shard -or $result.ShardCount -ne 2 -or
            $result.Mismatches -ne 0 -or $result.Comparisons -ne (30 * $result.Apps)) { throw 'Parity worker identity or coverage differs.' }
        $results += @{ Engine = $worker.Engine.Label; Result = $result }
    }
    foreach ($engine in $engines) {
        $selected = @($results | Where-Object { $_.Engine -ceq $engine.Label })
        $keys = @($selected | ForEach-Object { $_.Result.AppKeys } | Sort-Object)
        if ($selected.Count -ne 2 -or $keys.Count -ne $expectedKeys.Count -or
            @($keys | Select-Object -Unique).Count -ne $expectedKeys.Count -or
            (Compare-Object -CaseSensitive $expectedKeys $keys)) { throw 'An app was omitted or duplicated across parity shards.' }
        $comparisons = ($selected | ForEach-Object { $_.Result.Comparisons } | Measure-Object -Sum).Sum
        if ($comparisons -ne (30 * $expectedKeys.Count)) { throw 'Full parity matrix did not run.' }
        Write-Host ("Full/compact evaluator parity ($($engine.Version)): $($keys.Count) apps, $comparisons comparisons, zero mismatches.")
    }
}
finally {
    foreach ($worker in $workers) {
        if (-not $worker.Process.HasExited) { $worker.Process.Kill($true); $worker.Process.WaitForExit() }
        $worker.Process.Dispose()
    }
    if ($null -ne $directory -and (Test-Path -LiteralPath $directory)) { Remove-Item -LiteralPath $directory -Recurse -Force }
}
