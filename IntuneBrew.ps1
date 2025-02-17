<#PSScriptInfo

.VERSION 0.3.6

.GUID 53ddb976-1bc1-4009-bfa0-1e2a51477e4d

.AUTHOR ugurk

.COPYRIGHT

.TAGS

.LICENSEURI https://github.com/ugurkocde/IntuneBrew/blob/main/LICENSE

.PROJECTURI https://github.com/ugurkocde/IntuneBrew

.ICONURI

.EXTERNALMODULEDEPENDENCIES

.REQUIREDSCRIPTS

.EXTERNALSCRIPTDEPENDENCIES

.RELEASENOTES


.PRIVATEDATA

#>

<#

.DESCRIPTION
 This script automates the process of deploying macOS applications to Microsoft Intune using information from Homebrew casks. It fetches app details, creates Intune policies, and manages the deployment process.

.PARAMETER Upload
 Specifies a list of app names to upload directly, bypassing the manual selection process.
 Example: IntuneBrew -Upload google_chrome, visual_studio_code

.PARAMETER UpdateAll
 Updates all applications that have a newer version available in Intune.
 Example: IntuneBrew -UpdateAll

#>
param(
    [Parameter(Mandatory = $false)]
    [string[]]$Upload,
    
    [Parameter(Mandatory = $false)]
    [switch]$UpdateAll
)

Write-Host "
___       _                    ____                    
|_ _|_ __ | |_ _   _ _ __   ___| __ ) _ __ _____      __
 | || '_ \| __| | | | '_ \ / _ \  _ \| '__/ _ \ \ /\ / /
 | || | | | |_| |_| | | | |  __/ |_) | | |  __/\ V  V / 
|___|_| |_|\__|\__,_|_| |_|\___|____/|_|  \___| \_/\_/  
" -ForegroundColor Cyan

Write-Host "IntuneBrew - Automated macOS Application Deployment via Microsoft Intune" -ForegroundColor Green
Write-Host "Made by Ugur Koc with" -NoNewline; Write-Host " ❤️  and ☕" -NoNewline
Write-Host " | Version" -NoNewline; Write-Host " 0.3.6" -ForegroundColor Yellow -NoNewline
Write-Host " | Last updated: " -NoNewline; Write-Host "2025-02-15" -ForegroundColor Magenta
Write-Host ""
Write-Host "This is a preview version. If you have any feedback, please open an issue at https://github.com/ugurkocde/IntuneBrew/issues. Thank you!" -ForegroundColor Cyan
Write-Host "You can sponsor the development of this project at https://github.com/sponsors/ugurkocde" -ForegroundColor Red
Write-Host ""


# Authentication START

# Required Graph API permissions for app functionality
$requiredPermissions = @(
    "DeviceManagementApps.ReadWrite.All"
)

# Function to validate JSON configuration file
function Test-AuthConfig {
    param (
        [string]$Path
    )
    
    if (-not (Test-Path $Path)) {
        Write-Host "Error: Configuration file not found at path: $Path" -ForegroundColor Red
        return $false
    }
    
    try {
        $config = Get-Content $Path | ConvertFrom-Json
        return $true
    }
    catch {
        Write-Host "Error: Invalid JSON format in configuration file" -ForegroundColor Red
        return $false
    }
}

# Function to authenticate using certificate
function Connect-WithCertificate {
    param (
        [string]$ConfigPath
    )
    
    $config = Get-Content $ConfigPath | ConvertFrom-Json
    
    if (-not $config.appId -or -not $config.tenantId -or -not $config.certificateThumbprint) {
        Write-Host "Error: Configuration file must contain appId, tenantId, and certificateThumbprint" -ForegroundColor Red
        return $false
    }
    
    try {
        Connect-MgGraph -ClientId $config.appId -TenantId $config.tenantId -CertificateThumbprint $config.certificateThumbprint -NoWelcome -ErrorAction Stop
        Write-Host "Successfully connected to Microsoft Graph using certificate-based authentication." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Failed to connect to Microsoft Graph using certificate. Error: $_" -ForegroundColor Red
        return $false
    }
}

# Function to authenticate using client secret
function Connect-WithClientSecret {
    param (
        [string]$ConfigPath
    )
    
    $config = Get-Content $ConfigPath | ConvertFrom-Json
    
    if (-not $config.appId -or -not $config.tenantId -or -not $config.clientSecret) {
        Write-Host "Error: Configuration file must contain appId, tenantId, and clientSecret" -ForegroundColor Red
        return $false
    }
    
    try {
        $SecureClientSecret = ConvertTo-SecureString -String $config.clientSecret -AsPlainText -Force
        $ClientSecretCredential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $config.appId, $SecureClientSecret
        Connect-MgGraph -TenantId $config.tenantId -ClientSecretCredential $ClientSecretCredential -NoWelcome -ErrorAction Stop
        Write-Host "Successfully connected to Microsoft Graph using client secret authentication." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Failed to connect to Microsoft Graph using client secret. Error: $_" -ForegroundColor Red
        return $false
    }
}

# Function to authenticate interactively
function Connect-Interactive {
    try {
        $permissionsList = $requiredPermissions -join ','
        Connect-MgGraph -Scopes $permissionsList -NoWelcome -ErrorAction Stop
        Write-Host "Successfully connected to Microsoft Graph using interactive sign-in." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Failed to connect to Microsoft Graph via interactive sign-in. Error: $_" -ForegroundColor Red
        return $false
    }
}

# Function to show file picker dialog
function Show-FilePickerDialog {
    param (
        [string]$Title = "Select JSON Configuration File",
        [string]$Filter = "JSON files (*.json)|*.json|All files (*.*)|*.*"
    )
    
    Add-Type -AssemblyName System.Windows.Forms
    
    # Create a temporary form to own the dialog
    $form = New-Object System.Windows.Forms.Form
    $form.TopMost = $true
    $form.Opacity = 0
    
    # Show the form without activating it
    $form.Show()
    $form.Location = New-Object System.Drawing.Point(-32000, -32000)
    
    # Create and configure the dialog
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $Title
    $dialog.Filter = $Filter
    $dialog.CheckFileExists = $true
    $dialog.Multiselect = $false
    
    # Show dialog with the form as owner
    try {
        if ($dialog.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) {
            return $dialog.FileName
        }
    }
    finally {
        # Clean up the temporary form
        $form.Close()
        $form.Dispose()
    }
    return $null
}

# Display authentication options
Write-Host "`nChoose authentication method:" -ForegroundColor Cyan
Write-Host "1. App Registration with Certificate"
Write-Host "2. App Registration with Secret"
Write-Host "3. Interactive Session with Admin Account"
$authChoice = Read-Host "`nEnter your choice (1-3)"

$authenticated = $false

switch ($authChoice) {
    "1" {
        Write-Host "`nPlease select the certificate configuration JSON file..." -ForegroundColor Yellow
        $configPath = Show-FilePickerDialog -Title "Select Certificate Configuration JSON File"
        if ($configPath -and (Test-AuthConfig $configPath)) {
            $authenticated = Connect-WithCertificate $configPath
        }
    }
    "2" {
        Write-Host "`nPlease select the client secret configuration JSON file..." -ForegroundColor Yellow
        $configPath = Show-FilePickerDialog -Title "Select Client Secret Configuration JSON File"
        if ($configPath -and (Test-AuthConfig $configPath)) {
            $authenticated = Connect-WithClientSecret $configPath
        }
    }
    "3" {
        $authenticated = Connect-Interactive
    }
    default {
        Write-Host "Invalid choice. Please select 1, 2, or 3." -ForegroundColor Red
        exit
    }
}

if (-not $authenticated) {
    Write-Host "Authentication failed. Exiting script." -ForegroundColor Red
    exit
}

# Check and display the current permissions
$context = Get-MgContext
$currentPermissions = $context.Scopes

# Validate required permissions
$missingPermissions = $requiredPermissions | Where-Object { $_ -notin $currentPermissions }
if ($missingPermissions.Count -gt 0) {
    Write-Host "WARNING: The following permissions are missing:" -ForegroundColor Red
    $missingPermissions | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "Please ensure these permissions are granted to the app registration for full functionality." -ForegroundColor Yellow
    exit
}

Write-Host "All required permissions are present." -ForegroundColor Green

# Authentication END

# Import required modules
Import-Module Microsoft.Graph.Authentication

# Fetch supported apps from GitHub repository
$supportedAppsUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/refs/heads/main/supported_apps.json"
$githubJsonUrls = @()

try {
    # Fetch the supported apps JSON
    $supportedApps = Invoke-RestMethod -Uri $supportedAppsUrl -Method Get

    # Process apps based on command line parameters or allow manual selection
    if ($Upload) {
        Write-Host "`nProcessing specified applications:" -ForegroundColor Cyan
        foreach ($app in $Upload) {
            $appName = $app.Trim().ToLower()
            Write-Host "  - $appName"
            if ($supportedApps.PSObject.Properties.Name -contains $appName) {
                $githubJsonUrls += $supportedApps.$appName
            }
            else {
                Write-Host "Warning: '$appName' is not a supported application" -ForegroundColor Yellow
            }
        }
    }
    elseif ($UpdateAll) {
        Write-Host "`nChecking existing Intune applications for available updates..." -ForegroundColor Cyan
        $githubJsonUrls = $supportedApps.PSObject.Properties.Value
        Write-Host "(Note: Only applications already in Intune will be checked for updates)" -ForegroundColor Yellow
    }
    else {
        # Allow user to select which apps to process
        Write-Host "`nAvailable applications:" -ForegroundColor Cyan
        # Add Sort-Object to sort the app names alphabetically
        $supportedApps.PSObject.Properties |
        Sort-Object Name |
        ForEach-Object {
            Write-Host "  - $($_.Name)"
        }
        Write-Host "`nEnter app names separated by commas (or 'all' for all apps):"
        $selectedApps = Read-Host

        if ($selectedApps.Trim().ToLower() -eq 'all') {
            $githubJsonUrls = $supportedApps.PSObject.Properties.Value
        }
        else {
            $selectedAppsList = $selectedApps.Split(',') | ForEach-Object { $_.Trim().ToLower() }
            foreach ($app in $selectedAppsList) {
                if ($supportedApps.PSObject.Properties.Name -contains $app) {
                    $githubJsonUrls += $supportedApps.$app
                }
                else {
                    Write-Host "Warning: '$app' is not a supported application" -ForegroundColor Yellow
                }
            }
        }
    }

    if ($githubJsonUrls.Count -eq 0) {
        Write-Host "No valid applications selected. Exiting..." -ForegroundColor Red
        exit
    }
}
catch {
    Write-Host "Error fetching supported apps list: $_" -ForegroundColor Red
    exit
}

# Core Functions

# Fetches app information from GitHub JSON file
function Get-GitHubAppInfo {
    param(
        [string]$jsonUrl
    )

    if ([string]::IsNullOrEmpty($jsonUrl)) {
        Write-Host "Error: Empty or null JSON URL provided." -ForegroundColor Red
        return $null
    }

    try {
        $response = Invoke-RestMethod -Uri $jsonUrl -Method Get
        return @{
            name        = $response.name
            description = $response.description
            version     = $response.version
            url         = $response.url
            bundleId    = $response.bundleId
            homepage    = $response.homepage
            fileName    = $response.fileName
            sha         = $response.sha
        }
    }
    catch {
        Write-Host "Error fetching app info from GitHub URL: $jsonUrl" -ForegroundColor Red
        Write-Host "Error details: $_" -ForegroundColor Red
        return $null
    }
}

# Downloads app installer file with progress indication
function Download-AppFile($url, $fileName, $expectedHash) {
    $outputPath = Join-Path $PWD $fileName
    
    # Get file size before downloading
    try {
        $response = Invoke-WebRequest -Uri $url -Method Head
        $fileSize = [math]::Round(($response.Headers.'Content-Length' / 1MB), 2)
        Write-Host "Downloading the app file ($fileSize MB) to $outputPath..."
    }
    catch {
        Write-Host "Downloading the app file to $outputPath..."
    }
    
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $outputPath

    Write-Host "✅ Download complete" -ForegroundColor Green
    
    # Validate file integrity using SHA256 hash
    Write-Host "`n🔐 Validating file integrity..." -ForegroundColor Yellow
    
    # Validate expected hash format
    if ([string]::IsNullOrWhiteSpace($expectedHash)) {
        Write-Host "❌ Error: No SHA256 hash provided in the app manifest" -ForegroundColor Red
        Remove-Item $outputPath -Force
        throw "SHA256 hash validation failed - No hash provided in app manifest"
    }
    
    Write-Host "   • Verifying the downloaded file matches the expected SHA256 hash" -ForegroundColor Gray
    Write-Host "   • This ensures the file hasn't been corrupted or tampered with" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   • Expected hash: $expectedHash" -ForegroundColor Gray
    Write-Host "   • Calculating file hash..." -ForegroundColor Gray
    $fileHash = Get-FileHash -Path $outputPath -Algorithm SHA256
    Write-Host "   • Actual hash: $($fileHash.Hash)" -ForegroundColor Gray
    
    # Case-insensitive comparison of the hashes
    $expectedHashNormalized = $expectedHash.Trim().ToLower()
    $actualHashNormalized = $fileHash.Hash.Trim().ToLower()
    
    if ($actualHashNormalized -eq $expectedHashNormalized) {
        Write-Host "`n✅ Security check passed - File integrity verified" -ForegroundColor Green
        Write-Host "   • The SHA256 hash of the downloaded file matches the expected value" -ForegroundColor Gray
        Write-Host "   • This confirms the file is authentic and hasn't been modified" -ForegroundColor Gray
        return $outputPath
    } else {
        Write-Host "`n❌ Security check failed - File integrity validation error!" -ForegroundColor Red
        Remove-Item $outputPath -Force
        Write-Host "`n"
        throw "Security validation failed - SHA256 hash of the downloaded file does not match the expected value"
    }
}

# Encrypts app file using AES encryption for Intune upload
function EncryptFile($sourceFile) {
    function GenerateKey() {
        $aesSp = [System.Security.Cryptography.AesCryptoServiceProvider]::new()
        $aesSp.GenerateKey()
        return $aesSp.Key
    }

    $targetFile = "$sourceFile.bin"
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $aes = [System.Security.Cryptography.Aes]::Create()
    $aes.Key = GenerateKey
    $hmac = [System.Security.Cryptography.HMACSHA256]::new()
    $hmac.Key = GenerateKey
    $hashLength = $hmac.HashSize / 8

    $sourceStream = [System.IO.File]::OpenRead($sourceFile)
    $sourceSha256 = $sha256.ComputeHash($sourceStream)
    $sourceStream.Seek(0, "Begin") | Out-Null
    $targetStream = [System.IO.File]::Open($targetFile, "Create")

    $targetStream.Write((New-Object byte[] $hashLength), 0, $hashLength)
    $targetStream.Write($aes.IV, 0, $aes.IV.Length)
    $transform = $aes.CreateEncryptor()
    $cryptoStream = [System.Security.Cryptography.CryptoStream]::new($targetStream, $transform, "Write")
    $sourceStream.CopyTo($cryptoStream)
    $cryptoStream.FlushFinalBlock()

    $targetStream.Seek($hashLength, "Begin") | Out-Null
    $mac = $hmac.ComputeHash($targetStream)
    $targetStream.Seek(0, "Begin") | Out-Null
    $targetStream.Write($mac, 0, $mac.Length)

    $targetStream.Close()
    $cryptoStream.Close()
    $sourceStream.Close()

    return [PSCustomObject][ordered]@{
        encryptionKey        = [System.Convert]::ToBase64String($aes.Key)
        fileDigest           = [System.Convert]::ToBase64String($sourceSha256)
        fileDigestAlgorithm  = "SHA256"
        initializationVector = [System.Convert]::ToBase64String($aes.IV)
        mac                  = [System.Convert]::ToBase64String($mac)
        macKey               = [System.Convert]::ToBase64String($hmac.Key)
        profileIdentifier    = "ProfileVersion1"
    }
}

# Handles chunked upload of large files to Azure Storage
function UploadFileToAzureStorage($sasUri, $filepath) {
    $blockSize = 8 * 1024 * 1024  # 8 MB block size
    $fileSize = (Get-Item $filepath).Length
    $totalBlocks = [Math]::Ceiling($fileSize / $blockSize)
    
    $maxRetries = 3
    $retryCount = 0
    $uploadSuccess = $false

    while (-not $uploadSuccess -and $retryCount -lt $maxRetries) {
        try {
            $fileStream = [System.IO.File]::OpenRead($filepath)
            $blockId = 0
            # Initialize block list with proper XML structure
            $blockList = [System.Xml.Linq.XDocument]::Parse(@"
<?xml version="1.0" encoding="utf-8"?>
<BlockList></BlockList>
"@)
            
            # Ensure proper XML namespace
            $blockList.Declaration.Encoding = "utf-8"
            $blockBuffer = [byte[]]::new($blockSize)

            Write-Host "`n⬆️  Uploading to Azure Storage..." -ForegroundColor Cyan
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
            
            # Show file size with proper formatting
            $fileSizeMB = [Math]::Round($fileSize / 1MB, 2)
            Write-Host "📦 File size: " -NoNewline
            Write-Host "$fileSizeMB MB" -ForegroundColor Yellow
            
            if ($retryCount -gt 0) {
                Write-Host "🔄 Attempt $($retryCount + 1) of $maxRetries" -ForegroundColor Yellow
            }
            Write-Host ""  # Add a blank line before progress bar
            
            while ($bytesRead = $fileStream.Read($blockBuffer, 0, $blockSize)) {
                # Ensure block ID is properly padded and valid base64
                $blockIdBytes = [System.Text.Encoding]::UTF8.GetBytes($blockId.ToString("D6"))
                $id = [System.Convert]::ToBase64String($blockIdBytes)
                $blockList.Root.Add([System.Xml.Linq.XElement]::new("Latest", $id))

                $uploadBlockSuccess = $false
                $blockRetries = 3
                while (-not $uploadBlockSuccess -and $blockRetries -gt 0) {
                    try {
                        $blockUri = "$sasUri&comp=block&blockid=$id"
                        try {
                            Invoke-WebRequest -Method Put $blockUri `
                                -Headers @{"x-ms-blob-type" = "BlockBlob" } `
                                -Body ([byte[]]($blockBuffer[0..$($bytesRead - 1)])) `
                                -ErrorAction Stop | Out-Null

                            # Block upload successful
                            $uploadBlockSuccess = $true
                        }
                        catch {
                            Write-Host "`nFailed to upload block $blockId" -ForegroundColor Red
                            Write-Host "Error: $_" -ForegroundColor Red
                            throw
                        }
                        $uploadBlockSuccess = $true
                    }
                    catch {
                        $blockRetries--
                        if ($blockRetries -gt 0) {
                            Write-Host "Retrying block upload..." -ForegroundColor Yellow
                            Start-Sleep -Seconds 2
                        }
                        else {
                            Write-Host "Block upload failed: $_" -ForegroundColor Red
                            if ($_.Exception.Message -match "AuthenticationFailed.*Signed expiry time.*has to be after signed start time") {
                                Write-Host "Token timing issue detected. Adding additional delay..." -ForegroundColor Yellow
                                Start-Sleep -Seconds 5
                            }
                            throw $_
                        }
                    }
                }

                $percentComplete = [Math]::Round(($blockId + 1) / $totalBlocks * 100, 1)
                $uploadedMB = [Math]::Min(
                    [Math]::Round(($blockId + 1) * $blockSize / 1MB, 1),
                    [Math]::Round($fileSize / 1MB, 1)
                )
                $totalMB = [Math]::Round($fileSize / 1MB, 1)
                
                # Calculate basic progress
                $uploadedMB = [Math]::Min([Math]::Round(($blockId + 1) * $blockSize / 1MB, 1), [Math]::Round($fileSize / 1MB, 1))
                $totalMB = [Math]::Round($fileSize / 1MB, 1)
                $percentComplete = [Math]::Round(($blockId + 1) / $totalBlocks * 100, 1)

                # Build progress bar
                $progressWidth = 50
                $filledBlocks = [math]::Floor($percentComplete / 2)
                $emptyBlocks = $progressWidth - $filledBlocks
                $progressBar = "[" + ("▓" * $filledBlocks) + ("░" * $emptyBlocks) + "]"

                # Build progress line
                $progressText = "$progressBar $percentComplete% ($uploadedMB MB / $totalMB MB)"
                
                # Clear line and write progress
                [Console]::SetCursorPosition(0, [Console]::CursorTop)
                [Console]::Write((" " * [Console]::WindowWidth))
                [Console]::SetCursorPosition(0, [Console]::CursorTop)
                Write-Host $progressBar -NoNewline
                Write-Host " $percentComplete%" -NoNewline -ForegroundColor Cyan
                Write-Host " ($uploadedMB MB / $totalMB MB)" -NoNewline
                
                $blockId++
            }
            
            Write-Host ""
            
            $fileStream.Close()

            Invoke-RestMethod -Method Put "$sasUri&comp=blocklist" -Body $blockList | Out-Null
            $uploadSuccess = $true
        }
        catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Host "`nUpload failed. Retrying in 5 seconds..." -ForegroundColor Yellow
                Start-Sleep -Seconds 5
                
                # Request a new SAS token and wait for it to be valid
                Write-Host "Requesting new upload URL..." -ForegroundColor Yellow
                Start-Sleep -Seconds 2  # Add delay before requesting new token
                $newFileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
                if ($newFileStatus.azureStorageUri) {
                    $sasUri = $newFileStatus.azureStorageUri
                    Write-Host "Received new upload URL" -ForegroundColor Green
                    Start-Sleep -Seconds 2  # Add delay to ensure token is valid
                }
            }
            else {
                Write-Host "`nFailed to upload file after $maxRetries attempts." -ForegroundColor Red
                Write-Host "Error: $_" -ForegroundColor Red
                throw
            }
        }
        finally {
            if ($fileStream) {
                $fileStream.Close()
            }
        }
    }
}

# Validates GitHub URL format for security
function Is-ValidUrl {
    param (
        [string]$url
    )

    if ($url -match "^https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/.*\.json$") {
        return $true
    }
    else {
        Write-Host "Invalid URL format: $url" -ForegroundColor Red
        return $false
    }
}

# Retrieves and compares app versions between Intune and GitHub
function Get-IntuneApps {
    $intuneApps = @()
    $totalApps = $githubJsonUrls.Count
    $currentApp = 0

    Write-Host "`nChecking app versions in Intune..." -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    foreach ($jsonUrl in $githubJsonUrls) {
        $currentApp++
        
        # Check if the URL is valid
        if (-not (Is-ValidUrl $jsonUrl)) {
            continue
        }

        # Fetch GitHub app info
        $appInfo = Get-GitHubAppInfo $jsonUrl
        if ($appInfo -eq $null) {
            Write-Host "[$currentApp/$totalApps] Failed to fetch app info for $jsonUrl. Skipping." -ForegroundColor Yellow
            continue
        }

        $appName = $appInfo.name
        Write-Host "[$currentApp/$totalApps] 🔍 Checking: $appName" -ForegroundColor Yellow -NoNewline

        # Fetch Intune app info
        $intuneQueryUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?`$filter=(isof('microsoft.graph.macOSDmgApp') or isof('microsoft.graph.macOSPkgApp')) and displayName eq '$appName'"

        try {
            $response = Invoke-MgGraphRequest -Uri $intuneQueryUri -Method Get
            if ($response.value.Count -gt 0) {
                $intuneVersions = $response.value | ForEach-Object { $_.primaryBundleVersion }
                $githubVersion = $appInfo.version
                $latestIntuneVersion = $intuneVersions | Sort-Object -Descending | Select-Object -First 1
                
                # Check if GitHub version is newer than ALL installed versions
                $needsUpdate = $intuneVersions | ForEach-Object { Is-NewerVersion $githubVersion $_ } | Where-Object { $_ -eq $true }
                
                if ($needsUpdate.Count -eq $intuneVersions.Count) {
                    Write-Host " → Update available ($latestIntuneVersion → $githubVersion)" -ForegroundColor Green
                } else {
                    Write-Host " → Up to date ($latestIntuneVersion)" -ForegroundColor Gray
                }
                
                $intuneApps += [PSCustomObject]@{
                    Name          = $appName
                    IntuneVersion = $latestIntuneVersion
                    GitHubVersion = $githubVersion
                }
            }
            else {
                Write-Host " → Not in Intune" -ForegroundColor Gray
                $intuneApps += [PSCustomObject]@{
                    Name          = $appName
                    IntuneVersion = 'Not in Intune'
                    GitHubVersion = $appInfo.version
                }
            }
        }
        catch {
            Write-Host "`nError fetching Intune app info for '$appName': $_" -ForegroundColor Red
        }
    }

    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    return $intuneApps
}

# Compares version strings accounting for build numbers
function Is-NewerVersion($githubVersion, $intuneVersion) {
    if ($intuneVersion -eq 'Not in Intune') {
        return $true
    }

    try {
        # Remove hyphens and everything after them for comparison
        $ghVersion = $githubVersion -replace '-.*$'
        $itVersion = $intuneVersion -replace '-.*$'

        # Handle versions with commas (e.g., "3.5.1,16101")
        $ghVersionParts = $ghVersion -split ','
        $itVersionParts = $itVersion -split ','

        # Compare main version numbers first
        $ghMainVersion = [Version]($ghVersionParts[0])
        $itMainVersion = [Version]($itVersionParts[0])

        if ($ghMainVersion -ne $itMainVersion) {
            return ($ghMainVersion -gt $itMainVersion)
        }

        # If main versions are equal and there are build numbers
        if ($ghVersionParts.Length -gt 1 -and $itVersionParts.Length -gt 1) {
            $ghBuild = [int]$ghVersionParts[1]
            $itBuild = [int]$itVersionParts[1]
            return $ghBuild -gt $itBuild
        }

        # If versions are exactly equal
        return $githubVersion -ne $intuneVersion
    }
    catch {
        Write-Host "Version comparison failed: GitHubVersion='$githubVersion', IntuneVersion='$intuneVersion'. Assuming versions are equal." -ForegroundColor Yellow
        return $false
    }
}

# Downloads and adds app logo to Intune app entry
function Add-IntuneAppLogo {
    param (
        [string]$appId,
        [string]$appName
    )

    Write-Host "`n🖼️  Adding app logo..." -ForegroundColor Yellow
    
    try {
        # Construct the logo URL - only replace spaces with underscores
        $logoFileName = $appName.ToLower().Replace(" ", "_") + ".png"
        $logoUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Logos/$logoFileName"

        # For debugging
        Write-Host "Downloading logo from: $logoUrl" -ForegroundColor Gray

        # Download the logo
        $tempLogoPath = Join-Path $PWD "temp_logo.png"
        Invoke-WebRequest -Uri $logoUrl -OutFile $tempLogoPath

        # Convert the logo to base64
        $logoContent = [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tempLogoPath))

        # Prepare the request body
        $logoBody = @{
            "@odata.type" = "#microsoft.graph.mimeContent"
            "type"        = "image/png"
            "value"       = $logoContent
        }

        # Update the app with the logo
        $logoUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$appId"
        $updateBody = @{
            "@odata.type" = "#microsoft.graph.$appType"
            "largeIcon"   = $logoBody
        }

        Invoke-MgGraphRequest -Method PATCH -Uri $logoUri -Body ($updateBody | ConvertTo-Json -Depth 10)
        Write-Host "✅ Logo added successfully" -ForegroundColor Green

        # Cleanup
        if (Test-Path $tempLogoPath) {
            Remove-Item $tempLogoPath -Force
        }
    }
    catch {
        Write-Host "⚠️ Warning: Could not add app logo. Error: $_" -ForegroundColor Yellow
    }
}

# Retrieve Intune app versions
Write-Host "Fetching current Intune app versions..."
$intuneAppVersions = Get-IntuneApps
Write-Host ""

# Only show the table if not using UpdateAll
if (-not $UpdateAll) {
    # Prepare table data
    $tableData = @()
    foreach ($app in $intuneAppVersions) {
        if ($app.IntuneVersion -eq 'Not in Intune') {
            $status = "Not in Intune"
            $statusColor = "Red"
        }
        elseif (Is-NewerVersion $app.GitHubVersion $app.IntuneVersion) {
            $status = "Update Available"
            $statusColor = "Yellow"
        }
        else {
            $status = "Up-to-date"
            $statusColor = "Green"
        }

        $tableData += [PSCustomObject]@{
            "App Name"       = $app.Name
            "Latest Version" = $app.GitHubVersion
            "Intune Version" = $app.IntuneVersion
            "Status"         = $status
            "StatusColor"    = $statusColor
        }
    }

    # Function to write colored table
    function Write-ColoredTable {
        param (
            $TableData
        )

        $lineSeparator = "+----------------------------+----------------------+----------------------+-----------------+"
        
        Write-Host $lineSeparator
        Write-Host ("| {0,-26} | {1,-20} | {2,-20} | {3,-15} |" -f "App Name", "Latest Version", "Intune Version", "Status") -ForegroundColor Cyan
        Write-Host $lineSeparator

        foreach ($row in $TableData) {
            $color = $row.StatusColor
            Write-Host ("| {0,-26} | {1,-20} | {2,-20} | {3,-15} |" -f $row.'App Name', $row.'Latest Version', $row.'Intune Version', $row.Status) -ForegroundColor $color
            Write-Host $lineSeparator
        }
    }

    # Display the colored table with lines
    Write-ColoredTable $tableData
}

# Filter apps that need to be uploaded
$appsToUpload = $intuneAppVersions | Where-Object {
    if ($UpdateAll) {
        # For UpdateAll, only include apps that are in Intune and have updates
        $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion)
    } else {
        # For normal operation, include both new and updatable apps
        $_.IntuneVersion -eq 'Not in Intune' -or (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion)
    }
}

if ($appsToUpload.Count -eq 0) {
    Write-Host "`nAll apps are up-to-date. No uploads necessary." -ForegroundColor Green
    Disconnect-MgGraph > $null 2>&1
    Write-Host "Disconnected from Microsoft Graph." -ForegroundColor Green
    exit 0
}

# Check if there are apps to process
if (($appsToUpload.Count) -eq 0) {
    Write-Host "`nNo new or updatable apps found. Exiting..." -ForegroundColor Yellow
    Disconnect-MgGraph > $null 2>&1
    Write-Host "Disconnected from Microsoft Graph." -ForegroundColor Green
    exit 0
}

# Skip confirmation if using -Upload or -UpdateAll parameter
if (-not $Upload -and -not $UpdateAll) {
    # Create custom message based on app statuses
    $newApps = @($appsToUpload | Where-Object { $_.IntuneVersion -eq 'Not in Intune' })
    $updatableApps = @($appsToUpload | Where-Object { $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion) })

    # Construct the message
    if (($newApps.Length + $updatableApps.Length) -eq 1) {
        # Check if it's a new app or an update
        if ($newApps.Length -eq 1) {
            $message = "`nDo you want to upload this new app ($($newApps[0].Name)) to Intune? (y/n)"
        }
        elseif ($updatableApps.Length -eq 1) {
            $message = "`nDo you want to update this app ($($updatableApps[0].Name)) in Intune? (y/n)"
        }
        else {
            $message = "`nDo you want to process this app? (y/n)"
        }
    }
    else {
        $statusParts = @()
        if ($newApps.Length -gt 0) {
            $statusParts += "$($newApps.Length) new app$(if($newApps.Length -gt 1){'s'}) to upload"
        }
        if ($updatableApps.Length -gt 0) {
            $statusParts += "$($updatableApps.Length) app$(if($updatableApps.Length -gt 1){'s'}) to update"
        }
        $message = "`nFound $($statusParts -join ' and '). Do you want to continue? (y/n)"
    }

    # Prompt user to continue
    $continue = Read-Host -Prompt $message
    if ($continue -ne "y") {
        Write-Host "Operation cancelled by user." -ForegroundColor Yellow
        Disconnect-MgGraph > $null 2>&1
        Write-Host "Disconnected from Microsoft Graph." -ForegroundColor Green
        exit 0
    }
}

# Main script for uploading only newer apps
foreach ($app in $appsToUpload) {
    # Find the corresponding JSON URL for this app
    $jsonUrl = $githubJsonUrls | Where-Object {
        $appInfo = Get-GitHubAppInfo -jsonUrl $_
        $appInfo -and $appInfo.name -eq $app.Name
    } | Select-Object -First 1

    if (-not $jsonUrl) {
        Write-Host "`n❌ Could not find JSON URL for $($app.Name). Skipping." -ForegroundColor Red
        continue
    }

    $appInfo = Get-GitHubAppInfo -jsonUrl $jsonUrl
    if ($appInfo -eq $null) {
        Write-Host "`n❌ Failed to fetch app info for $jsonUrl. Skipping." -ForegroundColor Red
        continue
    }

    Write-Host "`n📦 Processing: $($appInfo.name)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    Write-Host "⬇️  Downloading application..." -ForegroundColor Yellow
    $appFilePath = Download-AppFile $appInfo.url $appInfo.fileName $appInfo.sha

    Write-Host "`n📋 Application Details:" -ForegroundColor Cyan
    Write-Host "   • Display Name: $($appInfo.name)"
    Write-Host "   • Version: $($appInfo.version)"
    Write-Host "   • Bundle ID: $($appInfo.bundleId)"
    Write-Host "   • File: $(Split-Path $appFilePath -Leaf)"

    $appDisplayName = $appInfo.name
    $appDescription = $appInfo.description
    $appPublisher = $appInfo.name
    $appHomepage = $appInfo.homepage
    $appBundleId = $appInfo.bundleId
    $appBundleVersion = $appInfo.version

    Write-Host "`n🔄 Creating app in Intune..." -ForegroundColor Yellow

    # Determine app type based on file extension
    $appType = if ($appInfo.fileName -match '\.dmg$') {
        "macOSDmgApp"
    }
    elseif ($appInfo.fileName -match '\.pkg$') {
        "macOSPkgApp"
    }
    else {
        Write-Host "❌ Unsupported file type. Only .dmg and .pkg files are supported." -ForegroundColor Red
        continue
    }

    $app = @{
        "@odata.type"                   = "#microsoft.graph.$appType"
        displayName                     = $appDisplayName
        description                     = $appDescription
        publisher                       = $appPublisher
        fileName                        = (Split-Path $appFilePath -Leaf)
        informationUrl                  = $appHomepage
        packageIdentifier               = $appBundleId
        bundleId                        = $appBundleId
        versionNumber                   = $appBundleVersion
        minimumSupportedOperatingSystem = @{
            "@odata.type" = "#microsoft.graph.macOSMinimumOperatingSystem"
            v11_0         = $true
        }
    }

    if ($appType -eq "macOSDmgApp" -or $appType -eq "macOSPkgApp") {
        $app["primaryBundleId"] = $appBundleId
        $app["primaryBundleVersion"] = $appBundleVersion
        $app["includedApps"] = @(
            @{
                "@odata.type" = "#microsoft.graph.macOSIncludedApp"
                bundleId      = $appBundleId
                bundleVersion = $appBundleVersion
            }
        )
    }

    $createAppUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps"
    $newApp = Invoke-MgGraphRequest -Method POST -Uri $createAppUri -Body ($app | ConvertTo-Json -Depth 10)
    Write-Host "✅ App created successfully (ID: $($newApp.id))" -ForegroundColor Green

    Write-Host "`n🔒 Processing content version..." -ForegroundColor Yellow
    $contentVersionUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions"
    $contentVersion = Invoke-MgGraphRequest -Method POST -Uri $contentVersionUri -Body "{}"
    Write-Host "✅ Content version created (ID: $($contentVersion.id))" -ForegroundColor Green

    Write-Host "`n🔐 Encrypting application file..." -ForegroundColor Yellow
    $encryptedFilePath = "$appFilePath.bin"
    if (Test-Path $encryptedFilePath) {
        Remove-Item $encryptedFilePath -Force
    }
    $fileEncryptionInfo = EncryptFile $appFilePath
    Write-Host "✅ Encryption complete" -ForegroundColor Green

    Write-Host "`n⬆️  Uploading to Azure Storage..." -ForegroundColor Yellow
    $fileContent = @{
        "@odata.type" = "#microsoft.graph.mobileAppContentFile"
        name          = [System.IO.Path]::GetFileName($appFilePath)
        size          = (Get-Item $appFilePath).Length
        sizeEncrypted = (Get-Item "$appFilePath.bin").Length
        isDependency  = $false
    }

    $contentFileUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files"  
    $contentFile = Invoke-MgGraphRequest -Method POST -Uri $contentFileUri -Body ($fileContent | ConvertTo-Json)

    do {
        Start-Sleep -Seconds 5
        $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
        $fileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
    } while ($fileStatus.uploadState -ne "azureStorageUriRequestSuccess")

    UploadFileToAzureStorage $fileStatus.azureStorageUri "$appFilePath.bin"
    Write-Host "✅ Upload completed successfully" -ForegroundColor Green

    Write-Host "`n🔄 Committing file..." -ForegroundColor Yellow
    $commitData = @{
        fileEncryptionInfo = $fileEncryptionInfo
    }
    $commitUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)/commit"
    Invoke-MgGraphRequest -Method POST -Uri $commitUri -Body ($commitData | ConvertTo-Json)

    $retryCount = 0
    $maxRetries = 10
    do {
        Start-Sleep -Seconds 10
        $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
        $fileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
        if ($fileStatus.uploadState -eq "commitFileFailed") {
            $commitResponse = Invoke-MgGraphRequest -Method POST -Uri $commitUri -Body ($commitData | ConvertTo-Json)
            $retryCount++
        }
    } while ($fileStatus.uploadState -ne "commitFileSuccess" -and $retryCount -lt $maxRetries)

    if ($fileStatus.uploadState -eq "commitFileSuccess") {
        Write-Host "✅ File committed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "Failed to commit file after $maxRetries attempts."
        exit 1
    }

    $updateAppUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)"
    $updateData = @{
        "@odata.type"           = "#microsoft.graph.$appType"
        committedContentVersion = $contentVersion.id
    }
    Invoke-MgGraphRequest -Method PATCH -Uri $updateAppUri -Body ($updateData | ConvertTo-Json)

    Add-IntuneAppLogo -appId $newApp.id -appName $appInfo.name

    Write-Host "`n🧹 Cleaning up temporary files..." -ForegroundColor Yellow
    if (Test-Path $appFilePath) {
        try {
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            Remove-Item $appFilePath -Force -ErrorAction Stop
        }
        catch {
            Write-Host "Warning: Could not remove $appFilePath. Error: $_" -ForegroundColor Yellow
        }
    }
    if (Test-Path "$appFilePath.bin") {
        $maxAttempts = 3
        $attempt = 0
        $success = $false
        
        while (-not $success -and $attempt -lt $maxAttempts) {
            try {
                [System.GC]::Collect()
                [System.GC]::WaitForPendingFinalizers()
                Start-Sleep -Seconds 2  # Give processes time to release handles
                Remove-Item "$appFilePath.bin" -Force -ErrorAction Stop
                $success = $true
            }
            catch {
                $attempt++
                if ($attempt -lt $maxAttempts) {
                    Write-Host "Retry $attempt of $maxAttempts to remove encrypted file..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 2
                }
                else {
                    Write-Host "Warning: Could not remove $appFilePath.bin. Error: $_" -ForegroundColor Yellow
                }
            }
        }
    }
    Write-Host "✅ Cleanup complete" -ForegroundColor Green

    Write-Host "`n✨ Successfully processed $($appInfo.name)" -ForegroundColor Cyan
    Write-Host "🔗 Intune Portal URL: https://intune.microsoft.com/#view/Microsoft_Intune_Apps/SettingsMenu/~/0/appId/$($newApp.id)" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
}

Write-Host "`n🎉 All operations completed successfully!" -ForegroundColor Green
Disconnect-MgGraph > $null 2>&1
Write-Host "Disconnected from Microsoft Graph." -ForegroundColor Green

