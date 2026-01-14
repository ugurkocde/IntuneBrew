<#
.SYNOPSIS
    This is for you to schedule and run IntuneBrew via a Azure Runbook. 
    
    This will upload all available updates for all macOS applications in Intune.  
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
    Version:        0.2
    Author:         Ugur Koc
    Creation Date:  2025-02-24
    Updated:        2026-01-14
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
# Disable verbose output to avoid cluttering the Azure Automation Runbook logs
$VerbosePreference = "SilentlyContinue"

# Function to write logs that will be visible in Azure Automation
function Write-Log {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [Parameter(Mandatory = $false)]
        [string]$Type = "Info"  # Info, Warning, Error, Verbose
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Type] $Message"
    if ($Type -eq "Verbose") {
        # Enable verbose output only when we really need it
        $VerbosePreference = "Continue"
        Write-Verbose $logMessage
        $VerbosePreference = "SilentlyContinue"
    }
    else {
        Write-Output $logMessage
    }
}

Write-Log "Starting IntuneBrew Automation Runbook - Version 0.2"

# Authentication START

# Required Graph API permissions for app functionality
$requiredPermissions = @(
    "DeviceManagementApps.ReadWrite.All"
)

# Get the authentication method from Automation Account variable
$AuthenticationMethod = Get-AutomationVariable -Name 'AuthenticationMethod'
$CopyAssignments = Get-AutomationVariable -Name 'CopyAssignments' -ErrorAction SilentlyContinue

# Get UseExistingIntuneApp setting - when true, updates existing apps instead of creating new ones (Issue #141)
$UseExistingIntuneApp = Get-AutomationVariable -Name 'UseExistingIntuneApp' -ErrorAction SilentlyContinue
if ($null -eq $UseExistingIntuneApp) { $UseExistingIntuneApp = $false }

# Get MaxAppsPerRun setting - limits apps processed per run to prevent memory exhaustion (Issue #45)
$MaxAppsPerRun = Get-AutomationVariable -Name 'MaxAppsPerRun' -ErrorAction SilentlyContinue
if ($null -eq $MaxAppsPerRun -or $MaxAppsPerRun -le 0) { $MaxAppsPerRun = 10 }

if ($CopyAssignments -eq $true) {
    Write-Log "Copy Assignments is set to true"
    $requiredPermissions += "Group.Read.All"
}

# Don't copy assignments if updating existing app (assignments are preserved on existing app)
if ($UseExistingIntuneApp -eq $true) {
    Write-Log "UseExistingIntuneApp is set to true - will update existing apps instead of creating new ones"
    if ($CopyAssignments -eq $true) {
        Write-Log "Note: CopyAssignments is ignored when UseExistingIntuneApp is enabled (assignments are preserved)" -Type "Warning"
        $CopyAssignments = $false
    }
}

# Log configuration summary
Write-Log "Configuration Summary:"
Write-Log "  - Authentication Method: $AuthenticationMethod"
Write-Log "  - Copy Assignments: $CopyAssignments"
Write-Log "  - Use Existing Intune App: $UseExistingIntuneApp"
Write-Log "  - Max Apps Per Run: $MaxAppsPerRun"

# Check if the AuthenticationMethod variable is empty
if ([string]::IsNullOrWhiteSpace($AuthenticationMethod)) {
    Write-Log "Authentication method is not specified. Please set the 'AuthenticationMethod' Automation Account variable." -Type "Error"
    throw "Authentication method is required but not provided."
}

# Use Client Secret for authentication (Issues #108, #103)
if ($AuthenticationMethod -eq "ClientSecret") {
    Write-Log "Using Client Secret for authentication"

    # Get authentication details from Automation Account variables
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

    # Clear any existing connections to prevent token cache issues
    try {
        Disconnect-MgGraph -ErrorAction SilentlyContinue
    }
    catch {
        # Ignore disconnect errors - there may not be an existing connection
    }

    # Authenticate using client secret from Automation Account
    $authSuccess = $false

    # Primary method: PSCredential approach
    try {
        Write-Log "Attempting primary authentication method (PSCredential)..."
        $SecureClientSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
        $ClientSecretCredential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $appId, $SecureClientSecret
        Connect-MgGraph -TenantId $tenantId -ClientSecretCredential $ClientSecretCredential -NoWelcome -ErrorAction Stop
        Write-Log "Successfully connected to Microsoft Graph using client secret authentication"
        $authSuccess = $true
    }
    catch {
        Write-Log "Primary authentication method failed: $_" -Type "Warning"
        Write-Log "Attempting fallback authentication method (direct token acquisition)..." -Type "Warning"

        # Fallback method: Direct OAuth2 token acquisition via REST API
        try {
            $tokenBody = @{
                Grant_Type    = "client_credentials"
                Scope         = "https://graph.microsoft.com/.default"
                Client_Id     = $appId
                Client_Secret = $clientSecret
            }
            $tokenResponse = Invoke-RestMethod -Uri "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token" -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
            $accessToken = $tokenResponse.access_token

            # Connect with acquired token
            $secureToken = ConvertTo-SecureString -String $accessToken -AsPlainText -Force
            Connect-MgGraph -AccessToken $secureToken -NoWelcome -ErrorAction Stop
            Write-Log "Successfully connected using fallback token acquisition method"
            $authSuccess = $true
        }
        catch {
            Write-Log "Fallback authentication also failed: $_" -Type "Error"
        }
    }

    if (-not $authSuccess) {
        Write-Log "Failed to authenticate with Microsoft Graph using client secret" -Type "Error"
        Write-Log "Troubleshooting steps:" -Type "Error"
        Write-Log "  1. Verify TenantId, AppId, and ClientSecret are correct" -Type "Error"
        Write-Log "  2. Ensure ClientSecret has not expired" -Type "Error"
        Write-Log "  3. Verify the app registration has required Graph API permissions" -Type "Error"
        Write-Log "  4. Check if the ClientSecret value (not ID) is stored in automation variable" -Type "Error"
        throw "Failed to authenticate with Microsoft Graph using client secret"
    }

    # Log module version for troubleshooting
    $graphModule = Get-Module Microsoft.Graph.Authentication -ErrorAction SilentlyContinue
    if ($graphModule) {
        Write-Log "Microsoft.Graph.Authentication version: $($graphModule.Version)"
    }
}
# Use System Managed Identity for authentication (Issue #43 - improved error handling)
elseif ($AuthenticationMethod -eq "SystemManagedIdentity") {
    Write-Log "Using System Managed Identity for authentication"

    # Authenticate using System Managed Identity from Automation Account
    try {
        Connect-MgGraph -Identity -NoWelcome -ErrorAction Stop
        Write-Log "Successfully connected to Microsoft Graph using System Managed Identity"

        # Log module version for troubleshooting
        $graphModule = Get-Module Microsoft.Graph.Authentication -ErrorAction SilentlyContinue
        if ($graphModule) {
            Write-Log "Microsoft.Graph.Authentication version: $($graphModule.Version)"
        }
    }
    catch {
        Write-Log "Failed to connect to Microsoft Graph using System Managed Identity. Error: $_" -Type "Error"
        Write-Log " " -Type "Error"
        Write-Log "Troubleshooting steps for System Managed Identity:" -Type "Error"
        Write-Log "  1. Go to Azure Portal > Automation Account > Identity" -Type "Error"
        Write-Log "  2. Ensure 'System assigned' tab shows Status: On" -Type "Error"
        Write-Log "  3. Click 'Azure role assignments' and verify Graph API permissions:" -Type "Error"
        Write-Log "     - DeviceManagementApps.ReadWrite.All" -Type "Error"
        Write-Log "     - Group.Read.All (if using CopyAssignments)" -Type "Error"
        Write-Log "  4. If permissions were recently added, wait 5-10 minutes for propagation" -Type "Error"
        Write-Log " " -Type "Error"
        Write-Log "To assign permissions via PowerShell:" -Type "Error"
        Write-Log "  Connect-AzAccount" -Type "Error"
        Write-Log "  \$MI = Get-AzADServicePrincipal -DisplayName '<AutomationAccountName>'" -Type "Error"
        Write-Log "  \$GraphApp = Get-AzADServicePrincipal -Filter \"appId eq '00000003-0000-0000-c000-000000000000'\"" -Type "Error"
        Write-Log "  \$Permission = \$GraphApp.AppRole | Where-Object {{\$_.Value -eq 'DeviceManagementApps.ReadWrite.All'}}" -Type "Error"
        Write-Log "  New-AzADServicePrincipalAppRoleAssignment -ServicePrincipalId \$MI.Id -ResourceId \$GraphApp.Id -AppRoleId \$Permission.Id" -Type "Error"
        throw
    }
}
# Use User Assigned Managed Identity for authentication (Issue #43 - improved error handling)
elseif ($AuthenticationMethod -eq "UserAssignedManagedIdentity") {
    Write-Log "Using User Assigned Managed Identity for authentication"

    # Authenticate using User Assigned Managed Identity from Automation Account
    try {
        $appId = Get-AutomationVariable -Name 'AppId'
        if ([string]::IsNullOrWhiteSpace($appId)) {
            throw "AppId automation variable is not set. Required for User Assigned Managed Identity."
        }
        Write-Log "Using Client ID: $appId"

        Connect-MgGraph -Identity -ClientId $appId -NoWelcome -ErrorAction Stop
        Write-Log "Successfully connected to Microsoft Graph using User Assigned Managed Identity"

        # Log module version for troubleshooting
        $graphModule = Get-Module Microsoft.Graph.Authentication -ErrorAction SilentlyContinue
        if ($graphModule) {
            Write-Log "Microsoft.Graph.Authentication version: $($graphModule.Version)"
        }
    }
    catch {
        Write-Log "Failed to connect to Microsoft Graph using User Assigned Managed Identity. Error: $_" -Type "Error"
        Write-Log " " -Type "Error"
        Write-Log "Troubleshooting steps for User Assigned Managed Identity:" -Type "Error"
        Write-Log "  1. Go to Azure Portal > Automation Account > Identity" -Type "Error"
        Write-Log "  2. Switch to 'User assigned' tab" -Type "Error"
        Write-Log "  3. Click 'Add' and select your User Assigned Managed Identity" -Type "Error"
        Write-Log "  4. Ensure the 'AppId' automation variable contains the Client ID of your User Assigned Identity" -Type "Error"
        Write-Log "  5. Verify the User Assigned Identity has Graph API permissions:" -Type "Error"
        Write-Log "     - DeviceManagementApps.ReadWrite.All" -Type "Error"
        Write-Log "     - Group.Read.All (if using CopyAssignments)" -Type "Error"
        Write-Log " " -Type "Error"
        Write-Log "To find the Client ID of your User Assigned Identity:" -Type "Error"
        Write-Log "  Go to Azure Portal > Managed Identities > Select your identity > Overview > Client ID" -Type "Error"
        throw
    }
}

# Check and display the current permissions
$context = Get-MgContext
if ($null -eq $context) {
    Write-Log "Failed to get Graph context - authentication may have failed silently" -Type "Error"
    throw "No active Graph connection. Please verify authentication succeeded."
}
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
# Fixed with proper resource disposal to prevent memory leaks (Issue #45)
function EncryptFile($sourceFile) {
    function GenerateKey() {
        $aesSp = [System.Security.Cryptography.AesCryptoServiceProvider]::new()
        try {
            $aesSp.GenerateKey()
            return $aesSp.Key
        }
        finally {
            $aesSp.Dispose()
        }
    }

    $targetFile = "$sourceFile.bin"

    # Initialize all disposable objects to $null for proper cleanup in finally block
    $sha256 = $null
    $aes = $null
    $hmac = $null
    $sourceStream = $null
    $targetStream = $null
    $cryptoStream = $null
    $transform = $null

    # Store values needed for return object before cleanup
    $encryptionKey = $null
    $fileDigest = $null
    $initializationVector = $null
    $macValue = $null
    $macKey = $null

    try {
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

        # Store values before cleanup
        $encryptionKey = [System.Convert]::ToBase64String($aes.Key)
        $fileDigest = [System.Convert]::ToBase64String($sourceSha256)
        $initializationVector = [System.Convert]::ToBase64String($aes.IV)
        $macValue = [System.Convert]::ToBase64String($mac)
        $macKey = [System.Convert]::ToBase64String($hmac.Key)
    }
    finally {
        # Dispose all resources in reverse order of creation
        if ($cryptoStream) { $cryptoStream.Dispose() }
        if ($targetStream) { $targetStream.Dispose() }
        if ($sourceStream) { $sourceStream.Dispose() }
        if ($transform) { $transform.Dispose() }
        if ($hmac) { $hmac.Dispose() }
        if ($aes) { $aes.Dispose() }
        if ($sha256) { $sha256.Dispose() }
    }

    return [PSCustomObject][ordered]@{
        encryptionKey        = $encryptionKey
        fileDigest           = $fileDigest
        fileDigestAlgorithm  = "SHA256"
        initializationVector = $initializationVector
        mac                  = $macValue
        macKey               = $macKey
        profileIdentifier    = "ProfileVersion1"
    }
}

# Aggressively clears memory to prevent Azure Automation sandbox suspension (Issue #45)
function Clear-MemoryAggressively {
    # Force garbage collection multiple times for thorough cleanup
    for ($i = 0; $i -lt 3; $i++) {
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }

    # Force full blocking collection
    [System.GC]::Collect([System.GC]::MaxGeneration, [System.GCCollectionMode]::Forced, $true, $true)

    # Log memory usage for monitoring
    try {
        $process = Get-Process -Id $PID -ErrorAction SilentlyContinue
        if ($process) {
            $memoryMB = [Math]::Round($process.WorkingSet64 / 1MB, 2)
            Write-Log "Current memory usage: $memoryMB MB"
        }
    }
    catch {
        # Ignore errors when getting process info in Azure Automation
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

# Function to get assignments for a specific Intune app
function Get-IntuneAppAssignments {
    param (
        [string]$AppId
    )

    if ([string]::IsNullOrEmpty($AppId)) {
        Write-Log "Error: App ID is required to fetch assignments." -Type "Verbose"
        return $null
    }

    Write-Log "`n🔍 Fetching assignments for existing app (ID: $AppId)..." -Type "Verbose"
    $assignmentsUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$AppId/assignments"
    
    try {
        # Use Invoke-MgGraphRequest for consistency and authentication handling
        $response = Invoke-MgGraphRequest -Method GET -Uri $assignmentsUri
        
        # The response directly contains the assignments array in the 'value' property
        if ($response.value -ne $null -and $response.value.Count -gt 0) {
            Write-Log "✅ Found $($response.value.Count) assignment(s)." -Type "Verbose"
            return $response.value
        }
        else {
            Write-Log "ℹ️ No assignments found for the existing app." -Type "Verbose"
            return @() # Return an empty array if no assignments
        }
    }
    catch {
        Write-Log "❌ Error fetching assignments for App ID ${AppId}: $($_.Exception.Message)" -Type "Verbose"
        # Consider returning specific error info or re-throwing if needed
        return $null # Indicate error
    }
}

# Function to apply assignments to a specific Intune app
function Set-IntuneAppAssignments {
    param (
        [string]$NewAppId,
        [array]$Assignments
    )

    if ([string]::IsNullOrEmpty($NewAppId)) {
        Write-Log "Error: New App ID is required to set assignments." -Type "Error"
        return
    }

    # Check if $Assignments is null or empty before proceeding
    if ($Assignments -eq $null -or $Assignments.Count -eq 0) {
        Write-Log "ℹ️ No assignments to apply." -Type "Info"
        return
    }

    Write-Log "Applying assignments to new app (ID: $NewAppId)..." -Type "Info"
    $assignmentsUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$NewAppId/assignments"
    $appliedCount = 0
    $failedCount = 0

    foreach ($assignment in $Assignments) {
        # Construct the body for the new assignment
        $targetObject = $null
        $originalTargetType = $assignment.target.'@odata.type'

        # Determine the target type and construct the target object accordingly
        if ($assignment.target.groupId) {
            $targetObject = @{
                "@odata.type" = "#microsoft.graph.groupAssignmentTarget"
                groupId       = $assignment.target.groupId
            }
        }
        elseif ($originalTargetType -match 'allLicensedUsersAssignmentTarget') {
            $targetObject = @{
                "@odata.type" = "#microsoft.graph.allLicensedUsersAssignmentTarget"
            }
        }
        elseif ($originalTargetType -match 'allDevicesAssignmentTarget') {
            $targetObject = @{
                "@odata.type" = "#microsoft.graph.allDevicesAssignmentTarget"
            }
        }
        else {
            Write-Log "⚠️ Warning: Unsupported assignment target type '$originalTargetType' found. Skipping this assignment." -Type "Warning"
            continue # Skip to the next assignment
        }

        # Build the main assignment body
        $assignmentBody = @{
            "@odata.type" = "#microsoft.graph.mobileAppAssignment" # Explicitly set the assignment type
            target        = $targetObject # Use the constructed target object
        }

        # Add intent (mandatory)
        $assignmentBody.intent = $assignment.intent

        # Conditionally add optional settings if they exist in the source assignment
        if ($assignment.PSObject.Properties.Name -contains 'settings' -and $assignment.settings -ne $null) {
            $assignmentBody.settings = $assignment.settings
        }
        # 'source' is usually determined by Intune and not needed for POST
        # 'sourceId' is read-only and should not be included

        $assignmentJson = $assignmentBody | ConvertTo-Json -Depth 5 -Compress

        try {
            $targetDescription = if ($assignment.target.groupId) { "group ID: $($assignment.target.groupId)" } elseif ($assignment.target.'@odata.type') { $assignment.target.'@odata.type' } else { "unknown target" }
            Write-Log "   • Applying assignment for target $targetDescription" -Type "Info"
            # Use Invoke-MgGraphRequest for consistency
            Invoke-MgGraphRequest -Method POST -Uri $assignmentsUri -Body $assignmentJson -ErrorAction Stop | Out-Null
            $appliedCount++
        }
        catch {
            $failedCount++
            Write-Log "❌ Error applying assignment for target $targetDescription : $_" -Type "Error"
            # Log the failed assignment body for debugging if needed
            # Write-Host "Failed assignment body: $assignmentJson" -ForegroundColor DarkGray
        }
    }
    
    Write-Log "---------------------------------------------------" -Type "Info"
    if ($appliedCount -gt 0) {
        Write-Log "✅ Successfully applied $appliedCount assignment(s)." -Type "Info"
    }
    if ($failedCount -gt 0) {
        Write-Log "❌ Failed to apply $failedCount assignment(s)." -Type "Error"
    }
    # (Function definition removed from here)


    if ($appliedCount -eq 0 -and $failedCount -eq 0) {
        Write-Log "ℹ️ No assignments were processed." -Type "Info" # Should not happen if $Assignments was not empty initially
    }
    Write-Log "---------------------------------------------------" -Type "Info"
}

# Function to remove assignments from a specific Intune app
function Remove-IntuneAppAssignments {
    param (
        [string]$OldAppId,
        [array]$AssignmentsToRemove
    )

    if ([string]::IsNullOrEmpty($OldAppId)) {
        Write-Log "Error: Old App ID is required to remove assignments." -Type "Error"
        return
    }

    if ($AssignmentsToRemove -eq $null -or $AssignmentsToRemove.Count -eq 0) {
        Write-Log "ℹ️ No assignments specified for removal." -Type "Info"
        return
    }

    Write-Log "Removing assignments from old app (ID: $OldAppId)..." -Type "Info"
    $removedCount = 0
    $failedCount = 0

    foreach ($assignment in $AssignmentsToRemove) {
        # Each assignment fetched earlier has its own ID
        $assignmentId = $assignment.id
        if ([string]::IsNullOrEmpty($assignmentId)) {
            Write-Log "⚠️ Warning: Assignment found without an ID. Cannot remove." -Type "Warning"
            continue
        }

        $removeUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$OldAppId/assignments/$assignmentId"
    
        # Determine target description for logging
        $targetDescription = "assignment ID: $assignmentId"
        if ($assignment.target.groupId) { $targetDescription = "group ID: $($assignment.target.groupId)" }
        elseif ($assignment.target.'@odata.type' -match 'allLicensedUsersAssignmentTarget') { $targetDescription = "All Users" }
        elseif ($assignment.target.'@odata.type' -match 'allDevicesAssignmentTarget') { $targetDescription = "All Devices" }

        try {
            Write-Log "   • Removing assignment for target $targetDescription" -Type "Info"
            Invoke-MgGraphRequest -Method DELETE -Uri $removeUri -ErrorAction Stop | Out-Null
            $removedCount++
        }
        catch {
            $failedCount++
            Write-Log "❌ Error removing assignment for target $targetDescription : $_" -Type "Error"
        }
    }

    Write-Log "---------------------------------------------------" -Type "Info"
    if ($removedCount -gt 0) {
        Write-Log "✅ Successfully removed $removedCount assignment(s) from old app." -Type "Info"
    }
    if ($failedCount -gt 0) {
        Write-Log "❌ Failed to remove $failedCount assignment(s) from old app." -Type "Error"
    }
    if ($removedCount -eq 0 -and $failedCount -eq 0) {
        Write-Log "ℹ️ No assignments were processed for removal." -Type "Info"
    }
    Write-Log "---------------------------------------------------" -Type "Info"
}

function Add-IntuneAppLogo {
    param (
        [string]$appId,
        [string]$appName,
        [string]$appType,
        [string]$localLogoPath = $null
    )

    Write-Log "Adding app logo..." -Type "Info"
    
    try {
        $tempLogoPath = $null

        if ($localLogoPath -and (Test-Path $localLogoPath)) {
            # Use the provided local logo file
            $tempLogoPath = $localLogoPath
            Write-Log "Using local logo file: $localLogoPath" -Type "Info"
        }
        else {
            # Try to download from repository
            $logoFileName = $appName.ToLower().Replace(" ", "_") + ".png"
            $logoUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Logos/$logoFileName"
            Write-Log "Downloading logo from: $logoUrl" -Type "Info"
            
            # Download the logo
            $tempLogoPath = Join-Path $PWD "temp_logo.png"
            try {
                Invoke-WebRequest -Uri $logoUrl -OutFile $tempLogoPath
            }
            catch {
                Write-Log "⚠️ Could not download logo from repository. Error: $_" -Type "Warning"
                return
            }
        }

        if (-not $tempLogoPath -or -not (Test-Path $tempLogoPath)) {
            Write-Log "⚠️ No valid logo file available" -Type "Warning"
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
        Write-Log "✅ Logo added successfully" -Type "Info"

        # Cleanup
        if (Test-Path $tempLogoPath) {
            Remove-Item $tempLogoPath -Force
        }
    }
    catch {
        Write-Log "⚠️ Warning: Could not add app logo. Error: $_" -Type "Warning"
    }
}

# Fetch supported apps from GitHub repository
$supportedAppsUrl = "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/refs/heads/main/supported_apps.json"
$githubJsonUrls = @()

try {
    # Fetch the supported apps JSON
    $supportedApps = Invoke-RestMethod -Uri $supportedAppsUrl -Method Get
    
    # Get all apps for checking updates
    Write-Log "Checking existing Intune applications for available updates..." -Type "Info"
    $githubJsonUrls = $supportedApps.PSObject.Properties.Value
    
    if ($githubJsonUrls.Count -eq 0) {
        Write-Log "No applications found to check. Exiting..." -Type "Error"
        exit
    }
}
catch {
    Write-Log "Error fetching supported apps list: $_" -Type "Error"
    exit
}

# Core Functions

# Fetches app information from GitHub JSON file
function Get-GitHubAppInfo {
    param(
        [string]$jsonUrl
    )

    if ([string]::IsNullOrEmpty($jsonUrl)) {
        Write-Log "Error: Empty or null JSON URL provided." -Type "Verbose"
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
        Write-Log "Error fetching app info from GitHub URL: $jsonUrl" -Type "Verbose"
        Write-Log "Error details: $_" -Type "Verbose"
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
        Write-Log "Downloading the app file ($fileSize MB) to $outputPath..." -Type "Verbose"
    }
    catch {
        Write-Log "Downloading the app file to $outputPath..." -Type "Verbose"
    }
    
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $outputPath

    Write-Log "✅ Download complete" -Type "Verbose"
    
    # Validate file integrity using SHA256 hash
    Write-Log "`n🔐 Validating file integrity..." -Type "Verbose"
    
    # Validate expected hash format
    if ([string]::IsNullOrWhiteSpace($expectedHash)) {
        Write-Log "❌ Error: No SHA256 hash provided in the app manifest" -Type "Verbose"
        Remove-Item $outputPath -Force
        throw "SHA256 hash validation failed - No hash provided in app manifest"
    }
    
    Write-Log "   • Verifying the downloaded file matches the expected SHA256 hash" -Type "Verbose"
    Write-Log "   • This ensures the file hasn't been corrupted or tampered with" -Type "Verbose"
    Write-Log "   " -Type "Verbose"
    Write-Log "   • Expected hash: $expectedHash" -Type "Verbose"
    Write-Log "   • Calculating file hash..." -Type "Verbose"
    $fileHash = Get-FileHash -Path $outputPath -Algorithm SHA256
    Write-Log "   • Actual hash: $($fileHash.Hash)" -Type "Verbose"
    
    # Case-insensitive comparison of the hashes
    $expectedHashNormalized = $expectedHash.Trim().ToLower()
    $actualHashNormalized = $fileHash.Hash.Trim().ToLower()
    
    if ($actualHashNormalized -eq $expectedHashNormalized) {
        Write-Log "`n✅ Security check passed - File integrity verified" -Type "Verbose"
        Write-Log "   • The SHA256 hash of the downloaded file matches the expected value" -Type "Verbose"
        Write-Log "   • This confirms the file is authentic and hasn't been modified" -Type "Verbose"
        return $outputPath
    }
    else {
        Write-Log "`n❌ Security check failed - File integrity validation error!" -Type "Verbose"
        Remove-Item $outputPath -Force
        Write-Log "`n" -Type "Verbose"
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
        Write-Log "Invalid URL format: $url" -Type "Verbose"
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
                # Find the latest version among potentially multiple entries
                $latestAppEntry = $response.value | Sort-Object -Property @{Expression = { [Version]($_.primaryBundleVersion -replace '-.*$') } } -Descending | Select-Object -First 1

                $intuneVersion = $latestAppEntry.primaryBundleVersion
                $intuneAppId = $latestAppEntry.id # Get the ID of the latest version
                $githubVersion = $appInfo.version
                
                # Check if GitHub version is newer
                $needsUpdate = Is-NewerVersion $githubVersion $intuneVersion
                
                if ($needsUpdate) {
                    Write-Log "Update available for $appName ($intuneVersion → $githubVersion)"
                }
                else {
                    Write-Log "$appName is up to date (Version: $intuneVersion)"
                }
                
                $intuneApps += [PSCustomObject]@{
                    Name          = $appName
                    IntuneVersion = $intuneVersion
                    IntuneAppId   = $intuneAppId # Add the ID here
                    GitHubVersion = $githubVersion
                }
            }
            else {
                Write-Log "$appName not found in Intune"
                $intuneApps += [PSCustomObject]@{
                    Name          = $appName
                    IntuneVersion = 'Not in Intune'
                    IntuneAppId   = $null
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
        # silence spammy log message for not installed apps
        if ($githubVersion -eq $intuneVersion -and -not [string]::IsNullOrEmpty($githubVersion)) {
            Write-Log "Version comparison failed: GitHubVersion='$githubVersion', IntuneVersion='$intuneVersion'. Assuming versions are equal." -Type "Verbose"
        }
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
    
    Write-Log "Found $($updatesAvailable.Count) update$(if($updatesAvailable.Count -ne 1){'s'}) available."
    Write-Log "Starting update process in 10 seconds..."
    Start-Sleep -Seconds 10
}

# Filter apps that need to be uploaded (only updates, no new apps)
$appsToUpload = $intuneAppVersions | Where-Object {
    $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion)
}

if ($appsToUpload.Count -eq 0) {
    Write-Log "`nAll apps are up-to-date. No uploads necessary." -Type "Info"
    Disconnect-MgGraph > $null 2>&1
    Write-Log "Disconnected from Microsoft Graph." -Type "Info"
    exit 0
}

# Limit apps per run to prevent memory exhaustion in Azure Automation sandbox (Issue #45)
if ($appsToUpload.Count -gt $MaxAppsPerRun) {
    Write-Log "Limiting to $MaxAppsPerRun apps per run (out of $($appsToUpload.Count) available) to prevent memory issues." -Type "Warning"
    Write-Log "Remaining apps will be processed in next scheduled run." -Type "Warning"
    $appsToUpload = $appsToUpload | Select-Object -First $MaxAppsPerRun
}

# Check if there are apps to process
if (($appsToUpload.Count) -eq 0) {
    Write-Log "`nNo new or updatable apps found. Exiting..." -Type "Info"
    Disconnect-MgGraph > $null 2>&1
    Write-Log "Disconnected from Microsoft Graph." -Type "Info"
    exit 0
}

# Determine if assignments should be copied based on the -CopyAssignments switch
$copyAssignments = $CopyAssignments -eq $true

# Define variables needed for assignment checking/copying regardless of mode
$updatableApps = @($appsToUpload | Where-Object { $_.IntuneVersion -ne 'Not in Intune' -and (Is-NewerVersion $_.GitHubVersion $_.IntuneVersion) })
$fetchedAssignments = @{} # Hashtable to store fetched assignments [AppID -> AssignmentsArray]
$assignmentsFound = $false # Flag to track if any assignments were found

# --- Non-Interactive Assignment Check/Display ---
# Pre-fetch and display assignments if running non-interactively (-Upload or -UpdateAll) AND copying is requested (-CopyAssignments) AND updates exist
if ($copyAssignments -and $updatableApps.Length -gt 0) {
    Write-Log "`nChecking assignments for apps to be updated..." -Type "Info"
    foreach ($updApp in $updatableApps) {
        $assignments = Get-IntuneAppAssignments -AppId $updApp.IntuneAppId
        if ($assignments -ne $null -and $assignments.Count -gt 0) {
            $fetchedAssignments[$updApp.IntuneAppId] = $assignments
            # $assignmentsFound = $true # Not needed for non-interactive prompt logic
            # Display summary for this app
            $assignmentSummaries = @()
            foreach ($assignment in $assignments) {
                $rawTargetType = $assignment.target.'@odata.type'.Replace("#microsoft.graph.", "")
                $groupId = $assignment.target.groupId
                $displayType = ""
                $targetDetail = ""
                switch ($rawTargetType) {
                    "groupAssignmentTarget" {
                        $displayType = "Group"
                        if ($groupId) {
                            try {
                                $groupUri = "https://graph.microsoft.com/v1.0/groups/$groupId`?`$select=displayName"
                                $groupInfo = Invoke-MgGraphRequest -Method GET -Uri $groupUri
                                if ($groupInfo.displayName) { $targetDetail = "('$($groupInfo.displayName)')" }
                                else { $targetDetail = "(ID: $groupId)" }
                            }
                            catch {
                                Write-Log "⚠️ Warning: Could not fetch display name for Group ID $groupId. Error: $($_.Exception.Message)" -Type "Warning"
                                $targetDetail = "(ID: $groupId)"
                            }
                        }
                        else { $targetDetail = "(Unknown Group ID)" }
                    }
                    "allLicensedUsersAssignmentTarget" { $displayType = "All Users" }
                    "allDevicesAssignmentTarget" { $displayType = "All Devices" }
                    default { $displayType = $rawTargetType }
                }
                $summaryPart = "$($assignment.intent): $displayType"
                if (-not [string]::IsNullOrWhiteSpace($targetDetail)) { $summaryPart += " $targetDetail" }
                $assignmentSummaries += $summaryPart
            }
            Write-Log "  - $($updApp.Name): Found $($assignments.Count) assignment(s): $($assignmentSummaries -join ', ')" -Type "Info"
        }
        else {
            Write-Log "  - $($updApp.Name): No assignments found." -Type "Info"
        }
    }
    Write-Log "   " -Type "Info"
}

$existingAssignments = $null # Initialize variable to store assignments for updates

# Main script for uploading only newer apps
foreach ($app in $appsToUpload) {
    try {
        # Clear memory before processing each app to prevent Azure sandbox suspension (Issue #45)
        Clear-MemoryAggressively

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

        # Check if this is an update and fetch existing assignments
        $existingAssignments = $null # Reset for each app
        # Fetch assignments only if the flag is set and it's an update
        # Retrieve pre-fetched assignments if the flag is set and it's an update
        if ($copyAssignments -and $app.IntuneAppId -and $fetchedAssignments.ContainsKey($app.IntuneAppId)) {
            $existingAssignments = $fetchedAssignments[$app.IntuneAppId]
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

        # Initialize the Intune app ID variable (Issue #141 - UseExistingIntuneApp support)
        $intuneAppId = $null

        # Check if we should update existing app or create new one
        if ($UseExistingIntuneApp -and $app.IntuneAppId) {
            # Use existing app ID - preserves assignments and other settings
            $intuneAppId = $app.IntuneAppId
            Write-Log "🔄 Updating Existing Intune App (ID: $intuneAppId)"
            Write-Log "Note: Existing app settings (assignments, logo, etc.) will be preserved"
        }
        else {
            # Create new app in Intune
            Write-Log "🔄 Creating new app in Intune..."

            $newAppPayload = @{
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
                $newAppPayload["primaryBundleId"] = $appBundleId
                $newAppPayload["primaryBundleVersion"] = $appBundleVersion
                $newAppPayload["includedApps"] = @(
                    @{
                        "@odata.type" = "#microsoft.graph.macOSIncludedApp"
                        bundleId      = $appBundleId
                        bundleVersion = $appBundleVersion
                    }
                )
            }

            $createAppUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps"
            $newApp = Invoke-MgGraphRequest -Method POST -Uri $createAppUri -Body ($newAppPayload | ConvertTo-Json -Depth 10)
            $intuneAppId = $newApp.id
            Write-Log "App created successfully (ID: $intuneAppId)"
        }

        Write-Log "🔒 Processing content version..."
        $contentVersionUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($intuneAppId)/microsoft.graph.$appType/contentVersions"
        $contentVersion = Invoke-MgGraphRequest -Method POST -Uri $contentVersionUri -Body "{}"
        Write-Log "Content version created (ID: $($contentVersion.id))"

        Write-Log "🔐 Encrypting application file..."
        $encryptedFilePath = "$appFilePath.bin"
        if (Test-Path $encryptedFilePath) {
            Remove-Item $encryptedFilePath -Force
        }

        # Store original file size before encryption (needed later for content file entry)
        $originalFileSize = (Get-Item $appFilePath).Length
        $originalFileName = [System.IO.Path]::GetFileName($appFilePath)

        $fileEncryptionInfo = EncryptFile $appFilePath
        Write-Log "File encryption complete"

        # Store encrypted file size
        $encryptedFileSize = (Get-Item "$appFilePath.bin").Length

        # Delete original file immediately after encryption to free disk space and memory (Issue #45)
        # The encrypted .bin file is all we need for upload
        if (Test-Path $appFilePath) {
            try {
                Remove-Item $appFilePath -Force -ErrorAction Stop
                Write-Log "Original file removed to free resources"
            }
            catch {
                Write-Log "Warning: Could not remove original file immediately: $_" -Type "Warning"
            }
        }
        Clear-MemoryAggressively

        try {
            Write-Log "⬆️ Uploading to Azure Storage..."
            $fileContent = @{
                "@odata.type" = "#microsoft.graph.mobileAppContentFile"
                name          = $originalFileName
                size          = $originalFileSize
                sizeEncrypted = $encryptedFileSize
                isDependency  = $false
            }

            Write-Log "Creating content file entry in Intune..."
            $contentFileUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($intuneAppId)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files"  
            $contentFile = Invoke-MgGraphRequest -Method POST -Uri $contentFileUri -Body ($fileContent | ConvertTo-Json)
            Write-Log "Content file entry created successfully"

            Write-Log "Waiting for Azure Storage URI..."
            $maxWaitAttempts = 12  # 1 minute total (5 seconds * 12)
            $waitAttempt = 0
            do {
                Start-Sleep -Seconds 5
                $waitAttempt++
                Write-Log "Checking upload state (attempt $waitAttempt of $maxWaitAttempts)..."
                
                $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($intuneAppId)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
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
        $commitUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($intuneAppId)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)/commit"
        Invoke-MgGraphRequest -Method POST -Uri $commitUri -Body ($commitData | ConvertTo-Json)

        $retryCount = 0
        $maxRetries = 10
        do {
            Start-Sleep -Seconds 10
            $fileStatusUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($intuneAppId)/microsoft.graph.$appType/contentVersions/$($contentVersion.id)/files/$($contentFile.id)"
            $fileStatus = Invoke-MgGraphRequest -Method GET -Uri $fileStatusUri
            if ($fileStatus.uploadState -eq "commitFileFailed") {
                $commitResponse = Invoke-MgGraphRequest -Method POST -Uri $commitUri -Body ($commitData | ConvertTo-Json)
                $retryCount++
            }
        } while ($fileStatus.uploadState -ne "commitFileSuccess" -and $retryCount -lt $maxRetries)

        if ($fileStatus.uploadState -eq "commitFileSuccess") {
            Write-Log "✅ File committed successfully" -Type "Info"
        }
        else {
            Write-Log "Failed to commit file after $maxRetries attempts." -Type "Error"
            throw "Failed to commit file after $maxRetries attempts for $($app.Name)"
        }

        $updateAppUri = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/$($intuneAppId)"
        $updateData = @{
            "@odata.type"           = "#microsoft.graph.$appType"
            committedContentVersion = $contentVersion.id
        }
        Invoke-MgGraphRequest -Method PATCH -Uri $updateAppUri -Body ($updateData | ConvertTo-Json)

            # Apply assignments if the flag is set and assignments were successfully fetched
        if ($copyAssignments -and $existingAssignments -ne $null) {
            Set-IntuneAppAssignments -NewAppId $intuneAppId -Assignments $existingAssignments
            # Now remove assignments from the old app version
            Remove-IntuneAppAssignments -OldAppId $app.IntuneAppId -AssignmentsToRemove $existingAssignments
        }

        Add-IntuneAppLogo -appId $intuneAppId -appName $appDisplayName -appType $appType

        Write-Log "🧹 Cleaning up temporary files..."
        if (Test-Path $appFilePath) {
            try {
                [System.GC]::Collect()
                [System.GC]::WaitForPendingFinalizers()
                Remove-Item $appFilePath -Force -ErrorAction Stop
            }
            catch {
                Write-Log "Warning: Could not remove $appFilePath. Error: $_" -Type "Warning"
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
                        Write-Log "Retry $attempt of $maxAttempts to remove encrypted file..." -Type "Warning"
                        Start-Sleep -Seconds 2
                    }
                    else {
                        Write-Log "Warning: Could not remove encrypted file. Error: $_" -Type "Warning"
                    }
                }
            }
        }
        Write-Log "✅ Cleanup complete" -Type "Info"

        Write-Log "Successfully processed $($appInfo.name)"
        Write-Log "App is now available in Intune Portal: https://intune.microsoft.com/#view/Microsoft_Intune_Apps/SettingsMenu/~/0/appId/$($intuneAppId)"
        Write-Log " " -Type "Info"
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


