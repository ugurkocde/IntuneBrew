<#
.SYNOPSIS
    IntuneBrew - Automated macOS Application and Update Management for Microsoft Intune

    This version of IntuneBrew is for automating patching of existing applications in Intune via a Azure Runbook.

.DESCRIPTION
    IntuneBrew is an automation script that streamlines the process of uploading and updating macOS applications
    in Microsoft Intune. It leverages a curated repository of popular applications to ensure your organization's
    apps are always up to date.

    Key Features:
    - Automated version checking against current Intune deployments
    - Secure file downloads with SHA256 verification
    - Automatic app encryption for Intune compatibility
    - Built-in error handling and retry mechanisms
    - Detailed logging for troubleshooting
    - Support for both .pkg and .dmg file formats
    - Automatic logo management for deployed applications

.NOTES
    Version:        0.1
    Author:         Ugur Koc
    Creation Date:  2025-02-24
    Repository:     https://github.com/ugurkocde/IntuneBrew
    License:        MIT

.LINK
    Project Homepage: https://github.com/ugurkocde/IntuneBrew
    Issue Tracker:    https://github.com/ugurkocde/IntuneBrew/issues
    Sponsor:          https://github.com/sponsors/ugurkocde

.REQUIREMENTS
    - Azure Automation Account with Managed Identity
    - Required Graph API Permissions:
        * DeviceManagementApps.ReadWrite.All
    - PowerShell 7.0 or later
    - Microsoft.Graph.Authentication module
#>

# Function to write logs that will be visible in Azure Automation
function Write-Log {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [Parameter(Mandatory = $false)]
        [string]$Type = "Info"  # Info, Warning, Error
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Type] $Message"
    Write-Output $logMessage
}

Write-Log "Starting IntuneBrew Automation Script - Version 0.4.0"
Write-Log "Automated macOS Application Deployment via Microsoft Intune"

# Authentication START

# Required Graph API permissions for app functionality
$requiredPermissions = @(
    "DeviceManagementApps.ReadWrite.All"
)

# Get authentication details from Automation Account
try {
    $tenantId = Get-AutomationVariable -Name 'TenantId'
    $appId = Get-AutomationVariable -Name 'AppId'
    $clientSecret = Get-AutomationVariable -Name 'ClientSecret'

    Write-Log "Successfully retrieved authentication variables from Automation Account"
}
catch {
    Write-Log "Failed to retrieve authentication variables: $_" -Type "Error"
    throw
}

# Authenticate using client secret from Automation Account
try {
    $SecureClientSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
    $ClientSecretCredential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $appId, $SecureClientSecret
    Connect-MgGraph -TenantId $tenantId -ClientSecretCredential $ClientSecretCredential -NoWelcome -ErrorAction Stop
    Write-Log "Successfully connected to Microsoft Graph using client secret authentication"
}
catch {
    Write-Log "Failed to connect to Microsoft Graph using client secret. Error: $_" -Type "Error"
    throw
}

# Check and display the current permissions
$context = Get-MgContext
$currentPermissions = $context.Scopes

# Validate required permissions
$missingPermissions = $requiredPermissions | Where-Object { $_ -notin $currentPermissions }
if ($missingPermissions.Count -gt 0) {
    Write-Log "WARNING: Missing required permissions:" -Type "Warning"
    foreach ($permission in $missingPermissions) {
        Write-Log "  - $permission" -Type "Warning"
    }
    Write-Log "Please ensure these permissions are granted to the app registration" -Type "Warning"
    throw "Missing required permissions"
}

Write-Log "All required permissions are present"

# Authentication END

# Import required modules
Import-Module Microsoft.Graph.Authentication

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
    try {
        Write-Log "Starting file upload to Azure Storage"
        $fileSize = [Math]::Round((Get-Item $filepath).Length / 1MB, 2)
        Write-Log "File size: $fileSize MB"
        
        $blockSize = 8 * 1024 * 1024  # 8 MB block size
        $fileSize = (Get-Item $filepath).Length
        $totalBlocks = [Math]::Ceiling($fileSize / $blockSize)
        
        $maxRetries = 3
        $retryCount = 0
        $uploadSuccess = $false
        $lastProgressReport = 0

        while (-not $uploadSuccess -and $retryCount -lt $maxRetries) {
            try {
                if ($retryCount -gt 0) {
                    Write-Log "Retry attempt $($retryCount + 1) of $maxRetries" -Type "Warning"
                }
                
                $fileStream = [System.IO.File]::OpenRead($filepath)
                $blockId = 0
                $blockList = [System.Xml.Linq.XDocument]::Parse(@"
<?xml version="1.0" encoding="utf-8"?>
<BlockList></BlockList>
"@)
                
                $blockList.Declaration.Encoding = "utf-8"
                $blockBuffer = [byte[]]::new($blockSize)
                
                while ($bytesRead = $fileStream.Read($blockBuffer, 0, $blockSize)) {
                    $blockIdBytes = [System.Text.Encoding]::UTF8.GetBytes($blockId.ToString("D6"))
                    $id = [System.Convert]::ToBase64String($blockIdBytes)
                    $blockList.Root.Add([System.Xml.Linq.XElement]::new("Latest", $id))

                    $uploadBlockSuccess = $false
                    $blockRetries = 3
                    while (-not $uploadBlockSuccess -and $blockRetries -gt 0) {
                        try {
                            $blockUri = "$sasUri&comp=block&blockid=$id"
                            Invoke-WebRequest -Method Put $blockUri `
                                -Headers @{"x-ms-blob-type" = "BlockBlob" } `
                                -Body ([byte[]]($blockBuffer[0..$($bytesRead - 1)])) `
                                -ErrorAction Stop | Out-Null

                            $uploadBlockSuccess = $true
                        }
                        catch {
                            $blockRetries--
                            if ($blockRetries -gt 0) {
                                Start-Sleep -Seconds 2
                            }
                            else {
                                Write-Log "Failed to upload block. Error: $_" -Type "Error"
                            }
                        }
                    }

                    if (-not $uploadBlockSuccess) {
                        throw "Failed to upload block after multiple retries"
                    }

                    $percentComplete = [Math]::Round(($blockId + 1) / $totalBlocks * 100, 1)
                    # Only log progress at 10% intervals
                    if ($percentComplete - $lastProgressReport -ge 10) {
                        Write-Log "Upload progress: $percentComplete%"
                        $lastProgressReport = [Math]::Floor($percentComplete / 10) * 10
                    }
                    
                    $blockId++
                }
                
                $fileStream.Close()

                Write-Log "Finalizing upload..."
                Invoke-RestMethod -Method Put "$sasUri&comp=blocklist" -Body $blockList | Out-Null
                Write-Log "Upload completed successfully"
                
                $uploadSuccess = $true
            }
            catch {
                $retryCount++
                Write-Log "Upload attempt failed: $_" -Type "Error"
                if ($retryCount -lt $maxRetries) {
                    Write-Log "Retrying upload..." -Type "Warning"
                    Start-Sleep -Seconds 5
                }
                else {
                    Write-Log "Failed all upload attempts" -Type "Error"
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
    catch {
        Write-Log "Critical error during upload: $_" -Type "Error"
        throw
    }
}

function Add-IntuneAppLogo {
    param (
        [string]$appId,
        [string]$appName,
        [string]$appType,
        [string]$localLogoPath = $null
    )

    Write-Host "`n🖼️  Adding app logo..." -ForegroundColor Yellow
    
    try {
        $tempLogoPath = $null

        if ($localLogoPath -and (Test-Path $localLogoPath)) {
            # Use the provided local logo file
            $tempLogoPath = $localLogoPath
            Write-Host "Using local logo file: $localLogoPath" -ForegroundColor Gray
        }
        else {
            # Try to download from repository
            $logoFileName = $appName.ToLower().Replace(" ", "_") + ".png"
            $logoUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Logos/$logoFileName"
            Write-Host "Downloading logo from: $logoUrl" -ForegroundColor Gray
            
            # Download the logo
            $tempLogoPath = Join-Path $PWD "temp_logo.png"
            try {
                Invoke-WebRequest -Uri $logoUrl -OutFile $tempLogoPath
            }
            catch {
                Write-Host "⚠️ Could not download logo from repository. Error: $_" -ForegroundColor Yellow
                return
            }
        }

        if (-not $tempLogoPath -or -not (Test-Path $tempLogoPath)) {
            Write-Host "⚠️ No valid logo file available" -ForegroundColor Yellow
            return
        }

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

# Fetch supported apps from GitHub repository
$supportedAppsUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/refs/heads/main/supported_apps.json"
$githubJsonUrls = @()

try {
    # Fetch the supported apps JSON
    $supportedApps = Invoke-RestMethod -Uri $supportedAppsUrl -Method Get
    
    # Get all apps for checking updates
    Write-Host "`nChecking existing Intune applications for available updates..." -ForegroundColor Cyan
    $githubJsonUrls = $supportedApps.PSObject.Properties.Value
    
    if ($githubJsonUrls.Count -eq 0) {
        Write-Host "No applications found to check. Exiting..." -ForegroundColor Red
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
    }
    else {
        Write-Host "`n❌ Security check failed - File integrity validation error!" -ForegroundColor Red
        Remove-Item $outputPath -Force
        Write-Host "`n"
        throw "Security validation failed - SHA256 hash of the downloaded file does not match the expected value"
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

    Write-Log "Checking app versions in Intune..."

    foreach ($jsonUrl in $githubJsonUrls) {
        $currentApp++
        
        # Check if the URL is valid
        if (-not (Is-ValidUrl $jsonUrl)) {
            Write-Log "Invalid URL format: $jsonUrl" -Type "Error"
            continue
        }

        # Fetch GitHub app info
        $appInfo = Get-GitHubAppInfo $jsonUrl
        if ($appInfo -eq $null) {
            Write-Log "[$currentApp/$totalApps] Failed to fetch app info for $jsonUrl. Skipping." -Type "Warning"
            continue
        }

        $appName = $appInfo.name
        Write-Log "[$currentApp/$totalApps] Checking: $appName"

        # Fetch Intune app info
        $intuneQueryUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?`$filter=(isof('microsoft.graph.macOSDmgApp') or isof('microsoft.graph.macOSPkgApp')) and displayName eq '$appName'&`$orderby=createdDateTime desc"

        try {
            $response = Invoke-MgGraphRequest -Uri $intuneQueryUri -Method Get
            if ($response.value.Count -gt 0) {
                # Get only the latest version from Intune (first item due to orderby desc)
                $latestIntuneVersion = $response.value[0].primaryBundleVersion
                $githubVersion = $appInfo.version
                
                # Compare only with the latest version
                $needsUpdate = Is-NewerVersion $githubVersion $latestIntuneVersion
                
                if ($needsUpdate) {
                    Write-Log "Update available for $appName ($latestIntuneVersion → $githubVersion)"
                }
                else {
                    Write-Log "$appName is up to date (Version: $latestIntuneVersion)"
                }
                
                $intuneApps += [PSCustomObject]@{
                    Name          = $appName
                    IntuneVersion = $latestIntuneVersion
                    GitHubVersion = $githubVersion
                }
            }
            else {
                Write-Log "$appName not found in Intune"
                $intuneApps += [PSCustomObject]@{
                    Name          = $appName
                    IntuneVersion = 'Not in Intune'
                    GitHubVersion = $appInfo.version
                }
            }
        }
        catch {
            Write-Log "Error fetching Intune app info for '$appName': $_" -Type "Error"
        }
    }

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

# Retrieve Intune app versions
Write-Log "Fetching current Intune app versions..."
$intuneAppVersions = Get-IntuneApps

# Show the overview table using Write-Log
Write-Log "----------------------------------------"
Write-Log "Available Updates Overview:"
Write-Log "----------------------------------------"

$updatesAvailable = $intuneAppVersions | Where-Object {
    $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion)
}

if ($updatesAvailable.Count -eq 0) {
    Write-Log "No updates available for any installed applications."
    Write-Log "Exiting..."
    Disconnect-MgGraph > $null 2>&1
    exit 0
}
else {
    # Create table header
    Write-Log "+--------------------------+--------------------+--------------------+"
    Write-Log "| App Name                | Current Version    | Available Version  |"
    Write-Log "+--------------------------+--------------------+--------------------+"
    
    # Add table rows
    foreach ($app in $updatesAvailable) {
        $appName = $app.Name.PadRight(24)[0..23] -join ''
        $currentVersion = $app.IntuneVersion.PadRight(18)[0..17] -join ''
        $availableVersion = $app.GitHubVersion.PadRight(18)[0..17] -join ''
        Write-Log "| $appName | $currentVersion | $availableVersion |"
        Write-Log "+--------------------------+--------------------+--------------------+"
    }
    
    Write-Log ""
    Write-Log "Found $($updatesAvailable.Count) update$(if($updatesAvailable.Count -ne 1){'s'}) available."
    Write-Log "Starting update process in 10 seconds..."
    Start-Sleep -Seconds 10
}

# Filter apps that need to be uploaded (only updates, no new apps)
$appsToUpload = $intuneAppVersions | Where-Object {
    $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion)
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

# Main script for uploading only newer apps
foreach ($app in $appsToUpload) {
    try {
        Write-Log "Processing application: $($app.Name)"
        Write-Log "Current version in Intune: $($app.IntuneVersion)"
        Write-Log "Available version: $($app.GitHubVersion)"
        
        # Find the corresponding JSON URL for this app
        $jsonUrl = $githubJsonUrls | Where-Object {
            $appInfo = Get-GitHubAppInfo -jsonUrl $_
            $appInfo -and $appInfo.name -eq $app.Name
        } | Select-Object -First 1

        if (-not $jsonUrl) {
            Write-Log "Could not find JSON URL for $($app.Name). Skipping." -Type "Error"
            continue
        }

        $appInfo = Get-GitHubAppInfo -jsonUrl $jsonUrl
        if ($appInfo -eq $null) {
            Write-Log "Failed to fetch app info for $jsonUrl. Skipping." -Type "Error"
            continue
        }

        # Clean up any existing temporary files before starting new download
        Get-ChildItem -Path $PWD -File | Where-Object { $_.Name -match '\.dmg$|\.pkg$|\.bin$' } | ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -ErrorAction Stop
                Write-Log "Cleaned up temporary file: $($_.Name)"
            }
            catch {
                Write-Log "Warning: Could not remove temporary file $($_.Name): $_" -Type "Warning"
            }
        }

        # Force garbage collection before starting new app
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()

        Write-Log "Starting upload process for: $($appInfo.name)"
        Write-Log "Downloading application from: $($appInfo.url)"
        
        # Check available space before downloading
        $drive = Get-PSDrive -Name $PWD.Drive.Name
        $availableSpace = $drive.Free
        $requiredSpace = 0
        
        try {
            $response = Invoke-WebRequest -Uri $appInfo.url -Method Head
            $fileSize = [long]$response.Headers.'Content-Length'
            # We need space for both the original and encrypted file, plus some buffer
            $requiredSpace = $fileSize * 2.5
        }
        catch {
            Write-Log "Warning: Could not determine file size before download" -Type "Warning"
            $requiredSpace = 1GB  # Assume 1GB as safety measure
        }

        if ($availableSpace -lt $requiredSpace) {
            Write-Log "Error: Not enough space to process $($appInfo.name). Required: $([math]::Round($requiredSpace/1GB, 2))GB, Available: $([math]::Round($availableSpace/1GB, 2))GB" -Type "Error"
            continue
        }

        $appFilePath = Download-AppFile $appInfo.url $appInfo.fileName $appInfo.sha

        Write-Log "Application Details:"
        Write-Log "• Display Name: $($appInfo.name)"
        Write-Log "• Version: $($appInfo.version)"
        Write-Log "• Bundle ID: $($appInfo.bundleId)"
        Write-Log "• File: $(Split-Path $appFilePath -Leaf)"

        $appDisplayName = $appInfo.name
        $appDescription = $appInfo.description
        $appPublisher = $appInfo.name
        $appHomepage = $appInfo.homepage
        $appBundleId = $appInfo.bundleId
        $appBundleVersion = $appInfo.version

        Write-Log "🔄 Creating app in Intune..."

        # Determine app type based on file extension
        $appType = if ($appInfo.fileName -match '\.dmg$') {
            "macOSDmgApp"
        }
        elseif ($appInfo.fileName -match '\.pkg$') {
            "macOSPkgApp"
        }
        else {
            Write-Log "Unsupported file type. Only .dmg and .pkg files are supported." -Type "Error"
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
        Write-Log "App created successfully (ID: $($newApp.id))"

        Write-Log "🔒 Processing content version..."
        $contentVersionUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions"
        $contentVersion = Invoke-MgGraphRequest -Method POST -Uri $contentVersionUri -Body "{}"
        Write-Log "Content version created (ID: $($contentVersion.id))"

        Write-Log "🔐 Encrypting application file..."
        $encryptedFilePath = "$appFilePath.bin"
        if (Test-Path $encryptedFilePath) {
            Remove-Item $encryptedFilePath -Force
        }
        $fileEncryptionInfo = EncryptFile $appFilePath
        Write-Log "File encryption complete"

        try {
            Write-Log "⬆️ Uploading to Azure Storage..."
            $fileContent = @{
                "@odata.type" = "#microsoft.graph.mobileAppContentFile"
                name          = [System.IO.Path]::GetFileName($appFilePath)
                size          = (Get-Item $appFilePath).Length
                sizeEncrypted = (Get-Item "$appFilePath.bin").Length
                isDependency  = $false
            }

            Write-Log "Creating content file entry in Intune..."
            $contentFileUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files"  
            $contentFile = Invoke-MgGraphRequest -Method POST -Uri $contentFileUri -Body ($fileContent | ConvertTo-Json)
            Write-Log "Content file entry created successfully"

            Write-Log "Waiting for Azure Storage URI..."
            $maxWaitAttempts = 12  # 1 minute total (5 seconds * 12)
            $waitAttempt = 0
            do {
                Start-Sleep -Seconds 5
                $waitAttempt++
                Write-Log "Checking upload state (attempt $waitAttempt of $maxWaitAttempts)..."
                
                $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($newApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
                $fileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
                
                if ($waitAttempt -eq $maxWaitAttempts -and $fileStatus.uploadState -ne "azureStorageUriRequestSuccess") {
                    throw "Timed out waiting for Azure Storage URI"
                }
            } while ($fileStatus.uploadState -ne "azureStorageUriRequestSuccess")

            Write-Log "Received Azure Storage URI, starting upload..."
            UploadFileToAzureStorage $fileStatus.azureStorageUri "$appFilePath.bin"
            Write-Log "Upload to Azure Storage complete"
        }
        catch {
            Write-Log "Failed during upload process: $_" -Type "Error"
            throw
        }

        Write-Log "🔄 Committing file to Intune..."
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

        Add-IntuneAppLogo -appId $newApp.id -appName $appDisplayName -appType $appType -localLogoPath $logoPath

        Write-Log "🧹 Cleaning up temporary files..."
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

        Write-Log "Successfully processed $($appInfo.name)"
        Write-Log "App is now available in Intune Portal: https://intune.microsoft.com/#view/Microsoft_Intune_Apps/SettingsMenu/~/0/appId/$($newApp.id)"
        Write-Host "" -ForegroundColor Cyan
    }
    catch {
        Write-Log "Critical error processing $($app.Name): $_" -Type "Error"
        Write-Log "Moving to next application..." -Type "Info"
        continue
    }
}

Write-Log "All operations completed successfully!"
Write-Log "Disconnecting from Microsoft Graph"
Disconnect-MgGraph > $null 2>&1


