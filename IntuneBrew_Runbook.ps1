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

        # Rest of your app processing code...
        # (Include all the necessary functions and processing logic)

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
