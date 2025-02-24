<#PSScriptInfo
.VERSION 0.3.8
.GUID 53ddb976-1bc1-4009-bfa0-1e2a51477e4d
.AUTHOR ugurk
.COMPANYNAME
.COPYRIGHT
.TAGS Intune macOS Homebrew
.LICENSEURI https://github.com/ugurkocde/IntuneBrew/blob/main/LICENSE
.PROJECTURI https://github.com/ugurkocde/IntuneBrew
.ICONURI
.EXTERNALMODULEDEPENDENCIES Microsoft.Graph.Authentication
.REQUIREDSCRIPTS
.EXTERNALSCRIPTDEPENDENCIES
.RELEASENOTES
Version 0.3.8: Modified for Azure Automation Runbook with client secret auth
.PRIVATEDATA
#>

<#
.DESCRIPTION
 This script automates the process of deploying macOS applications to Microsoft Intune using information from Homebrew casks. It fetches app details, creates Intune policies, and manages the deployment process.

.PARAMETER UpdateAll
 Updates all applications that have a newer version available in Intune.
 Example: -UpdateAll $true
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [switch]$UpdateAll = $true  # Default to true for automation
)

# Enable verbose output
$VerbosePreference = "Continue"

Write-Output "Starting IntuneBrew Runbook execution"
Write-Output "----------------------------------------"
Write-Output "IntuneBrew - Automated macOS Application Deployment via Microsoft Intune"
Write-Output "Version: 0.3.8"
Write-Output "----------------------------------------"

# Required Graph API permissions
$requiredPermissions = @(
    "DeviceManagementApps.ReadWrite.All"
)

# Get authentication details from Automation Account
try {
    $tenantId = Get-AutomationVariable -Name 'TenantId'
    $appId = Get-AutomationVariable -Name 'AppId'
    $clientSecret = Get-AutomationVariable -Name 'ClientSecret'

    Write-Output "Retrieved authentication variables from Automation Account"
}
catch {
    Write-Output "Failed to retrieve authentication variables: $_"
    throw
}

# Connect to Microsoft Graph using client secret
try {
    $secureClientSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
    $clientSecretCredential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $appId, $secureClientSecret
    
    Connect-MgGraph -TenantId $tenantId -ClientSecretCredential $clientSecretCredential -NoWelcome
    Write-Output "Successfully connected to Microsoft Graph using client secret"
}
catch {
    Write-Output "Failed to connect to Microsoft Graph: $_"
    throw
}

# Validate permissions
$context = Get-MgContext
$currentPermissions = $context.Scopes
$missingPermissions = $requiredPermissions | Where-Object { $_ -notin $currentPermissions }

if ($missingPermissions.Count -gt 0) {
    Write-Output "Missing required permissions: $($missingPermissions -join ', ')"
    throw "Required permissions are missing"
}

Write-Output "All required permissions are present"

# Import required modules
Import-Module Microsoft.Graph.Authentication

# Core Functions

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
            $blockList = [System.Xml.Linq.XDocument]::Parse(@"
<?xml version="1.0" encoding="utf-8"?>
<BlockList></BlockList>
"@)
            
            $blockList.Declaration.Encoding = "utf-8"
            $blockBuffer = [byte[]]::new($blockSize)

            Write-Output "Uploading to Azure Storage..."
            Write-Output "File size: $([Math]::Round($fileSize / 1MB, 2)) MB"
            
            if ($retryCount -gt 0) {
                Write-Output "Attempt $($retryCount + 1) of $maxRetries"
            }
            
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
                            Write-Output "Retrying block upload..."
                            Start-Sleep -Seconds 2
                        }
                        else {
                            Write-Output "Block upload failed: $_"
                            throw $_
                        }
                    }
                }

                $percentComplete = [Math]::Round(($blockId + 1) / $totalBlocks * 100, 1)
                Write-Output "Upload progress: $percentComplete%"
                $blockId++
            }
            
            $fileStream.Close()
            Invoke-RestMethod -Method Put "$sasUri&comp=blocklist" -Body $blockList | Out-Null
            $uploadSuccess = $true
        }
        catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Output "Upload failed. Retrying in 5 seconds..."
                Start-Sleep -Seconds 5
                
                Write-Output "Requesting new upload URL..."
                Start-Sleep -Seconds 2
                $newFileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
                if ($newFileStatus.azureStorageUri) {
                    $sasUri = $newFileStatus.azureStorageUri
                    Write-Output "Received new upload URL"
                    Start-Sleep -Seconds 2
                }
            }
            else {
                Write-Output "Failed to upload file after $maxRetries attempts."
                Write-Output "Error: $_"
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

# Downloads and adds app logo to Intune app entry
function Add-IntuneAppLogo {
    param (
        [string]$appId,
        [string]$appName,
        [string]$appType
    )

    Write-Output "Adding app logo..."
    
    try {
        # Try to download from repository
        $logoFileName = $appName.ToLower().Replace(" ", "_") + ".png"
        $logoUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Logos/$logoFileName"
        
        # Download the logo
        $tempLogoPath = Join-Path $env:TEMP "temp_logo.png"
        try {
            Invoke-WebRequest -Uri $logoUrl -OutFile $tempLogoPath
        }
        catch {
            Write-Output "Could not download logo from repository. Error: $_"
            return
        }

        if (-not (Test-Path $tempLogoPath)) {
            Write-Output "No valid logo file available"
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
        Write-Output "Logo added successfully"

        # Cleanup
        if (Test-Path $tempLogoPath) {
            Remove-Item $tempLogoPath -Force
        }
    }
    catch {
        Write-Output "Warning: Could not add app logo. Error: $_"
    }
}

# Fetches app information from GitHub JSON file
function Get-GitHubAppInfo {
    param(
        [string]$jsonUrl
    )

    if ([string]::IsNullOrEmpty($jsonUrl)) {
        Write-Output "Error: Empty or null JSON URL provided."
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
        Write-Output "Error fetching app info from GitHub URL: $jsonUrl"
        Write-Output "Error details: $_"
        return $null
    }
}

# Downloads app installer file with progress indication
function Download-AppFile($url, $fileName, $expectedHash) {
    $outputPath = Join-Path $env:TEMP $fileName
    
    Write-Output "Downloading the app file to $outputPath..."
    
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $outputPath

    Write-Output "Download complete"
    
    # Validate file integrity using SHA256 hash
    Write-Output "Validating file integrity..."
    
    if ([string]::IsNullOrWhiteSpace($expectedHash)) {
        Write-Output "Error: No SHA256 hash provided in the app manifest"
        Remove-Item $outputPath -Force
        throw "SHA256 hash validation failed - No hash provided in app manifest"
    }
    
    $fileHash = Get-FileHash -Path $outputPath -Algorithm SHA256
    
    # Case-insensitive comparison of the hashes
    $expectedHashNormalized = $expectedHash.Trim().ToLower()
    $actualHashNormalized = $fileHash.Hash.Trim().ToLower()
    
    if ($actualHashNormalized -eq $expectedHashNormalized) {
        Write-Output "Security check passed - File integrity verified"
        return $outputPath
    }
    else {
        Write-Output "Security check failed - File integrity validation error!"
        Remove-Item $outputPath -Force
        throw "Security validation failed - SHA256 hash of the downloaded file does not match the expected value"
    }
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
            try {
                $ghBuild = [int]$ghVersionParts[1]
                $itBuild = [int]$itVersionParts[1]
                return $ghBuild -gt $itBuild
            }
            catch {
                Write-Output "Warning: Failed to compare build numbers. Comparing version strings directly."
                return $githubVersion -ne $intuneVersion
            }
        }

        # If versions are exactly equal or can't be compared
        return $githubVersion -ne $intuneVersion
    }
    catch {
        Write-Output "Version comparison failed: GitHubVersion='$githubVersion', IntuneVersion='$intuneVersion'. Assuming versions are equal."
        return $false
    }
}

# Get Intune apps
function Get-IntuneApps {
    $intuneApps = @()
    $totalApps = $githubJsonUrls.Count
    $currentApp = 0

    Write-Output "Checking app versions in Intune..."
    Write-Output "Total apps to check: $totalApps"

    foreach ($jsonUrl in $githubJsonUrls) {
        $currentApp++
        
        # Check if the URL is valid
        if (-not ($jsonUrl -match "^https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/.*\.json$")) {
            Write-Output "Invalid URL format: $jsonUrl"
            continue
        }

        # Fetch GitHub app info
        $appInfo = Get-GitHubAppInfo $jsonUrl
        if ($null -eq $appInfo) {
            Write-Output "Failed to fetch app info for $jsonUrl. Skipping."
            continue
        }

        $appName = $appInfo.name
        Write-Output "[$currentApp/$totalApps] Checking: $appName"

        # Fetch Intune app info
        $intuneQueryUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?`$filter=(isof('microsoft.graph.macOSDmgApp') or isof('microsoft.graph.macOSPkgApp')) and displayName eq '$appName'"

        try {
            $response = Invoke-MgGraphRequest -Uri $intuneQueryUri -Method Get
            if ($response.value.Count -gt 0) {
                $intuneVersions = $response.value | ForEach-Object { $_.primaryBundleVersion }
                $githubVersion = $appInfo.version
                $latestIntuneVersion = $intuneVersions | Sort-Object -Descending | Select-Object -First 1
                
                if (Is-NewerVersion $githubVersion $latestIntuneVersion) {
                    Write-Output "  • Update available: $appName ($latestIntuneVersion → $githubVersion)"
                    $intuneApps += [PSCustomObject]@{
                        Name          = $appName
                        IntuneVersion = $latestIntuneVersion
                        GitHubVersion = $githubVersion
                        JsonUrl       = $jsonUrl
                    }
                }
                else {
                    Write-Output "  • Up to date: $appName ($latestIntuneVersion)"
                }
            }
            else {
                Write-Output "  • Not in Intune: $appName"
            }
        }
        catch {
            Write-Output "Error fetching Intune app info for '$appName': $_"
        }
    }

    return $intuneApps
}

# Fetch supported apps from GitHub
$supportedAppsUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/refs/heads/main/supported_apps.json"
$githubJsonUrls = @()

try {
    $supportedApps = Invoke-RestMethod -Uri $supportedAppsUrl -Method Get
    Write-Output "Successfully fetched supported apps list"
    $githubJsonUrls = $supportedApps.PSObject.Properties.Value
}
catch {
    Write-Output "Error fetching supported apps list: $_"
    throw
}

# Process apps
Write-Output "Retrieving current Intune app versions..."
$intuneAppVersions = Get-IntuneApps

$appsToUpload = $intuneAppVersions | Where-Object {
    # Only include apps that are in Intune and have updates
    $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion)
}

if ($appsToUpload.Count -eq 0) {
    Write-Output "All apps are up-to-date. No uploads necessary."
    Disconnect-MgGraph > $null 2>&1
    Write-Output "Disconnected from Microsoft Graph"
    exit 0
}

Write-Output "Found $($appsToUpload.Count) apps that need updating"

# Process each app
foreach ($app in $appsToUpload) {
    try {
        Write-Output "Processing app: $($app.Name)"
        Write-Output "Current version: $($app.IntuneVersion)"
        Write-Output "Available version: $($app.GitHubVersion)"
        Write-Output "----------------------------------------"

        # Get app info directly from stored JsonUrl
        $appInfo = Get-GitHubAppInfo -jsonUrl $app.JsonUrl
        if ($appInfo -eq $null) {
            Write-Output "Failed to fetch app info. Skipping."
            continue
        }

        # Download and process the app
        Write-Output "Downloading application..."
        $appFilePath = Download-AppFile $appInfo.url $appInfo.fileName $appInfo.sha

        Write-Output "Creating app in Intune..."
        $appType = if ($appInfo.fileName -match '\.dmg$') {
            "macOSDmgApp"
        }
        else {
            "macOSPkgApp"
        }

        $newApp = @{
            "@odata.type"                   = "#microsoft.graph.$appType"
            displayName                     = $appInfo.name
            description                     = $appInfo.description
            publisher                       = $appInfo.name
            fileName                        = $appInfo.fileName
            informationUrl                  = $appInfo.homepage
            packageIdentifier               = $appInfo.bundleId
            bundleId                        = $appInfo.bundleId
            versionNumber                   = $appInfo.version
            minimumSupportedOperatingSystem = @{
                "@odata.type" = "#microsoft.graph.macOSMinimumOperatingSystem"
                v11_0         = $true
            }
        }

        if ($appType -eq "macOSDmgApp" -or $appType -eq "macOSPkgApp") {
            $newApp["primaryBundleId"] = $appInfo.bundleId
            $newApp["primaryBundleVersion"] = $appInfo.version
            $newApp["includedApps"] = @(
                @{
                    "@odata.type" = "#microsoft.graph.macOSIncludedApp"
                    bundleId      = $appInfo.bundleId
                    bundleVersion = $appInfo.version
                }
            )
        }

        $createAppUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps"
        $createdApp = Invoke-MgGraphRequest -Method POST -Uri $createAppUri -Body ($newApp | ConvertTo-Json -Depth 10)
        Write-Output "App created successfully (ID: $($createdApp.id))"

        Write-Output "Processing content version..."
        $contentVersionUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($createdApp.id)/microsoft.graph.$appType/contentVersions"
        $contentVersion = Invoke-MgGraphRequest -Method POST -Uri $contentVersionUri -Body "{}"
        Write-Output "Content version created (ID: $($contentVersion.id))"

        Write-Output "Encrypting application file..."
        $encryptedFilePath = "$appFilePath.bin"
        if (Test-Path $encryptedFilePath) {
            Remove-Item $encryptedFilePath -Force
        }
        $fileEncryptionInfo = EncryptFile $appFilePath

        Write-Output "Preparing for upload..."
        $fileContent = @{
            "@odata.type" = "#microsoft.graph.mobileAppContentFile"
            name          = $appInfo.fileName
            size          = (Get-Item $appFilePath).Length
            sizeEncrypted = (Get-Item "$appFilePath.bin").Length
            isDependency  = $false
        }

        $contentFileUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($createdApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files"
        $contentFile = Invoke-MgGraphRequest -Method POST -Uri $contentFileUri -Body ($fileContent | ConvertTo-Json)

        do {
            Start-Sleep -Seconds 5
            $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($createdApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
            $fileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
        } while ($fileStatus.uploadState -ne "azureStorageUriRequestSuccess")

        UploadFileToAzureStorage $fileStatus.azureStorageUri "$appFilePath.bin"
        Write-Output "Upload completed successfully"

        Write-Output "Committing file..."
        $commitData = @{
            fileEncryptionInfo = $fileEncryptionInfo
        }
        $commitUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($createdApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)/commit"
        Invoke-MgGraphRequest -Method POST -Uri $commitUri -Body ($commitData | ConvertTo-Json)

        $retryCount = 0
        $maxRetries = 10
        do {
            Start-Sleep -Seconds 10
            $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($createdApp.id)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
            $fileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
            if ($fileStatus.uploadState -eq "commitFileFailed") {
                $commitResponse = Invoke-MgGraphRequest -Method POST -Uri $commitUri -Body ($commitData | ConvertTo-Json)
                $retryCount++
            }
        } while ($fileStatus.uploadState -ne "commitFileSuccess" -and $retryCount -lt $maxRetries)

        if ($fileStatus.uploadState -eq "commitFileSuccess") {
            Write-Output "File committed successfully"
        }
        else {
            Write-Output "Failed to commit file after $maxRetries attempts."
            exit 1
        }

        $updateAppUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($createdApp.id)"
        $updateData = @{
            "@odata.type"           = "#microsoft.graph.$appType"
            committedContentVersion = $contentVersion.id
        }
        Invoke-MgGraphRequest -Method PATCH -Uri $updateAppUri -Body ($updateData | ConvertTo-Json)

        Add-IntuneAppLogo -appId $createdApp.id -appName $appInfo.name -appType $appType

        Write-Output "Successfully processed $($appInfo.name)"
        Write-Output "Intune Portal URL: https://intune.microsoft.com/#view/Microsoft_Intune_Apps/SettingsMenu/~/0/appId/$($createdApp.id)"
    }
    catch {
        Write-Output "Error processing app $($app.Name): $_"
        Write-Output "----------------------------------------"
        continue
    }
    finally {
        # Cleanup
        Get-ChildItem -Path $env:TEMP -Filter "*.bin" | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $env:TEMP -Filter "*.pkg" | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $env:TEMP -Filter "*.dmg" | Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

Write-Output "All operations completed successfully!"
Write-Output "Disconnecting from Microsoft Graph..."
Disconnect-MgGraph > $null 2>&1
Write-Output "Disconnected from Microsoft Graph"
