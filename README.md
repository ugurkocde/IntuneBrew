<h1 align="center">🍺 IntuneBrew</h1>

<div align="center">
  <p>
    <a href="https://twitter.com/UgurKocDe">
      <img src="https://img.shields.io/badge/Follow-@UgurKocDe-1DA1F2?style=flat&logo=x&logoColor=white" alt="Twitter Follow"/>
    </a>
    <a href="https://www.linkedin.com/in/ugurkocde/">
      <img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin" alt="LinkedIn"/>
    </a>
    <img src="https://img.shields.io/github/license/ugurkocde/IntuneAssignmentChecker?style=flat" alt="License"/>
  </p>
  <p>
  <p>
    <a href="https://www.powershellgallery.com/packages/IntuneBrew">
      <img src="https://img.shields.io/powershellgallery/v/IntuneBrew?style=flat&label=PSGallery%20Version" alt="PowerShell Gallery Version"/>
    </a>
    <a href="https://www.powershellgallery.com/packages/IntuneBrew">
      <img src="https://img.shields.io/powershellgallery/dt/IntuneBrew?style=flat&label=PSGallery%20Downloads&color=brightgreen" alt="PowerShell Gallery Downloads"/>
    </a>
                                                                                                                                                                                                                                                                                                                                                                          <p>
    <a href="#-supported-applications">
      <img src="https://img.shields.io/badge/Apps_Available-507-2ea44f?style=flat" alt="TotalApps"/>
    </a>
  </p>
</div>

IntuneBrew is a PowerShell-based tool that simplifies the process of uploading and managing macOS applications in Microsoft Intune. It automates the entire workflow—from downloading apps to uploading them to Intune with proper metadata and icons.

This project uses publicly available metadata from Homebrew’s JSON API. Homebrew is a registered trademark of its respective owners and is not affiliated with or endorsing this project.

## Watch the full walkthrough of the tool:

<div align="center">
      <a href="https://www.youtube.com/watch?v=7NEs-EnvmII">
     <img 
      src="https://img.youtube.com/vi/7NEs-EnvmII/maxresdefault.jpg" 
      alt="IntuneBrew" 
      style="width:100%;">
      </a>
</div>

## Table of Contents

- [Watch the full walkthrough of the tool:](#watch-the-full-walkthrough-of-the-tool)
- [Table of Contents](#table-of-contents)
- [🔄 Latest Updates](#-latest-updates)
- [✨ Features](#-features)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
- [📝 Usage](#-usage)
  - [Basic Usage](#basic-usage)
  - [Advanced Parameters](#advanced-parameters)
    - [Upload Specific Apps](#upload-specific-apps)
    - [Update All Apps](#update-all-apps)
    - [Upload Local Files](#upload-local-files)
    - [Copy Assignments](#copy-assignments)
    - [Use Existing Intune Apps](#use-existing-intune-apps)
    - [Non-Interactive Authentication](#non-interactive-authentication)
    - [Customize App Names](#customize-app-names)
    - [Pre/Post Install Scripts (PKG only)](#prepost-install-scripts-pkg-only)
  - [📱 Supported Applications](#-supported-applications)
- [🔧 Configuration](#-configuration)
  - [Using System Managed Identity](#using-system-managed-identity)
  - [Using User Assigned Managed Identity](#using-user-assigned-managed-identity)
  - [Using ClientSecret from Entra ID App Registration](#using-clientsecret-from-entra-id-app-registration)
  - [Certificate-Based Authentication](#certificate-based-authentication)
  - [Using Configuration File](#using-configuration-file)
  - [Copy Assignments](#copy-assignments-1)
  - [App JSON Structure](#app-json-structure)
- [🔄 Version Management](#-version-management)
- [🛠️ Error Handling](#️-error-handling)
- [🤔 Troubleshooting](#-troubleshooting)
  - [Common Issues](#common-issues)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [📞 Support](#-support)


































## 🔄 Latest Updates

*Last checked: 2025-06-11 00:32 UTC*

| Application | Previous Version | New Version |
|-------------|-----------------|-------------|
| Advanced Renamer | 4.11 | 4.12 |
| Highlight | 1.2.60 | 1.2.65 |
| Rive | 0.8.3088 | 0.8.3105 |
| Mozilla Thunderbird | 139.0.1 | 139.0.2 |
| Yaak | 2025.3.1 | 2025.4.0 |
| ChatWise | 0.8.62 | 0.8.63 |
| WeChat for Mac | 4.0.3.93 | 4.0.5.25 |
| Mozilla Firefox | 139.0.1 | 139.0.4 |
| Windows App | 11.1.7 | 11.1.8 |
| Canva | 1.109.0 | 1.110.0 |
| Dropbox | 225.4.4896 | 226.4.5094 |
| Audacity | 3.7.3 | 3.7.4 |
| ChatGPT | 1.2025.147 | 1.2025.154 |
| Microsoft Office | 16.97.25051114 | 16.98.25060824 |
| Windsurf | 1.9.4 | 1.10.1 |
| Adobe Acrobat Reader | 25.001.20467 | 25.001.20529 |
## ✨ Features

- 🚀 Automated app uploads to Microsoft Intune
- 📦 Supports both .dmg and .pkg files
- 🔄 Automatic version checking and updates
- 🖼️ Automatic app icon integration
- 📊 Progress tracking for large file uploads
- 🔐 Secure authentication with Microsoft Graph API
- 🎯 Smart duplicate detection
- 💫 Bulk upload support
- 🔁 Automatic retry mechanism for failed uploads
- 🔒 Secure file encryption for uploads
- 📈 Real-time progress monitoring

## 🚀 Getting Started

### Prerequisites

- PowerShell 7.0 or higher
- Administrator rights (script must be installed as administrator, specially if you use "Install-Script IntuneBrew -Force")
- Microsoft.Graph.Authentication Module must be installed
- Azure App Registration with appropriate permissions OR Manual Connection via Interactive Sign-In
- Windows or macOS operating system

## 📝 Usage

### Basic Usage

Download the script: IntuneBrew.ps1

Run the script:

```powershell
.\IntuneBrew.ps1
```

Follow the interactive prompts to:

1. Select which apps to upload
2. Authenticate with Microsoft Graph
3. Monitor the upload progress
4. View the results in Intune

### Advanced Parameters

#### Upload Specific Apps
```powershell
.\IntuneBrew.ps1 -Upload "google_chrome", "slack", "zoom"
```
Uploads the specified apps directly without interactive selection.

#### Update All Apps
```powershell
.\IntuneBrew.ps1 -UpdateAll
```
Updates all applications that have newer versions available.

#### Upload Local Files
```powershell
.\IntuneBrew.ps1 -LocalFile
```
Upload local PKG or DMG files to Intune with interactive prompts.

#### Copy Assignments
```powershell
.\IntuneBrew.ps1 -UpdateAll -CopyAssignments
```
When updating apps, copy assignments from existing versions to new versions.

#### Use Existing Intune Apps
```powershell
.\IntuneBrew.ps1 -UpdateAll -UseExistingIntuneApp
```
Updates existing Intune app entries instead of creating new ones. This prevents duplicate app entries in Intune.

#### Non-Interactive Authentication
```powershell
.\IntuneBrew.ps1 -UpdateAll -ConfigFile "clientSecret.json"
```
Use a configuration file for non-interactive authentication. This enables automation. See the Configuration section for setup details.

#### Customize App Names
```powershell
# Add prefix to app names
.\IntuneBrew.ps1 -Upload "slack" -AppNamePrefix "Corporate "

# Add suffix to app names  
.\IntuneBrew.ps1 -Upload "zoom" -AppNameSuffix " - Mac"

# Use both prefix and suffix
.\IntuneBrew.ps1 -Upload "chrome" -AppNamePrefix "Company " -AppNameSuffix " (Managed)"
```
Customize how app names appear in Intune by adding prefixes and/or suffixes.

#### Pre/Post Install Scripts (PKG only)
```powershell
.\IntuneBrew.ps1 -Upload "example_app" -PreInstallScriptPath "./scripts/pre-install.sh" -PostInstallScriptPath "./scripts/post-install.sh"
```
Execute custom scripts before or after PKG installations.

### 📱 Supported Applications

| Application | Latest Version |
|-------------|----------------|
| <img src='Logos/1password.png' width='32' height='32'> 1Password | 8.10.80 |
| <img src='Logos/a_better_finder_rename.png' width='32' height='32'> A Better Finder Rename | 12.12 |
| <img src='Logos/abstract.png' width='32' height='32'> Abstract | 98.6.1 |
| <img src='Logos/acorn.png' width='32' height='32'> Acorn | 8.1.1 |
| <img src='Logos/acronis_true_image.png' width='32' height='32'> Acronis True Image | 29.2 |
| <img src='Logos/adguard.png' width='32' height='32'> AdGuard | 2.16.4.1870 |
| <img src='Logos/adobe_acrobat_pro_dc.png' width='32' height='32'> Adobe Acrobat Pro DC | 25.001.20529 |
| <img src='Logos/adobe_acrobat_reader.png' width='32' height='32'> Adobe Acrobat Reader | 25.001.20529 |
| <img src='Logos/adobe_creative_cloud.png' width='32' height='32'> Adobe Creative Cloud | 6.6.0.611 |
| <img src='Logos/advanced_renamer.png' width='32' height='32'> Advanced Renamer | 4.12 |
| <img src='Logos/airbuddy.png' width='32' height='32'> AirBuddy | 2.7.3 |
| <img src='Logos/aircall.png' width='32' height='32'> Aircall | 3.1.66 |
| <img src='Logos/airfoil.png' width='32' height='32'> Airfoil | 5.12.4 |
| <img src='Logos/airparrot.png' width='32' height='32'> AirParrot | 3.1.7 |
| <img src='Logos/airtable.png' width='32' height='32'> Airtable | 1.6.6 |
| <img src='Logos/airy.png' width='32' height='32'> Airy | 3.29.2 |
| <img src='Logos/alacritty.png' width='32' height='32'> Alacritty | 0.15.1 |
| <img src='Logos/alcove.png' width='32' height='32'> Alcove | 1.2.5 |
| <img src='Logos/alfred.png' width='32' height='32'> Alfred | 5.6.2 |
| <img src='Logos/alttab.png' width='32' height='32'> AltTab | 7.24.0 |
| <img src='Logos/amadine.png' width='32' height='32'> Amadine | 1.6.7 |
| <img src='Logos/amazon_chime.png' width='32' height='32'> Amazon Chime | 5.23.22356 |
| <img src='Logos/amazon_q.png' width='32' height='32'> Amazon Q | 1.11.0 |
| <img src='Logos/android_studio.png' width='32' height='32'> Android Studio | 2024.3.2.15 |
| <img src='Logos/angry_ip_scanner.png' width='32' height='32'> Angry IP Scanner | 3.9.1 |
| <img src='Logos/anki.png' width='32' height='32'> Anki | 25.02.6 |
| <img src='Logos/antinote.png' width='32' height='32'> Antinote | 1.1.7 |
| <img src='Logos/anydo.png' width='32' height='32'> Any.do | 5.0.68 |
| <img src='Logos/anydesk.png' width='32' height='32'> AnyDesk | 9.0.2 |
| <img src='Logos/apidog.png' width='32' height='32'> Apidog | 2.7.15 |
| <img src='Logos/apifox.png' width='32' height='32'> Apifox | 2.7.15 |
| <img src='Logos/apparency.png' width='32' height='32'> Apparency | 2.2 |
| <img src='Logos/arc.png' width='32' height='32'> Arc | 1.97.1 |
| <img src='Logos/archaeology.png' width='32' height='32'> Archaeology | 1.2 |
| <img src='Logos/arduino_ide.png' width='32' height='32'> Arduino IDE | 2.3.6 |
| <img src='Logos/asana.png' width='32' height='32'> Asana | 2.4.1 |
| <img src='Logos/asset_catalog_tinkerer.png' width='32' height='32'> Asset Catalog Tinkerer | 2.9 |
| <img src='Logos/atlassian_sourcetree.png' width='32' height='32'> Atlassian SourceTree | 4.2.12 |
| <img src='Logos/audacity.png' width='32' height='32'> Audacity | 3.7.4 |
| <img src='Logos/audio_hijack.png' width='32' height='32'> Audio Hijack | 4.5.1 |
| <img src='Logos/autodesk_fusion_360.png' width='32' height='32'> Autodesk Fusion 360 | latest |
| <img src='Logos/aws_client_vpn.png' width='32' height='32'> AWS Client VPN | 5.2.0 |
| <img src='Logos/aws_corretto_jdk.png' width='32' height='32'> AWS Corretto JDK | 21.0.7.6.1 |
| <img src='Logos/azul_zulu_java_standard_edition_development_kit.png' width='32' height='32'> Azul Zulu Java Standard Edition Development Kit | 24.0.1 |
| <img src='Logos/azure_data_studio.png' width='32' height='32'> Azure Data Studio | 1.51.1 |
| <img src='Logos/background_music.png' width='32' height='32'> Background Music | 0.4.3 |
| <img src='Logos/badgeify.png' width='32' height='32'> Badgeify | 1.7.0 |
| <img src='Logos/bambu_studio.png' width='32' height='32'> Bambu Studio | 02.01.00.59 |
| <img src='Logos/bartender.png' width='32' height='32'> Bartender | 5.3.7 |
| <img src='Logos/basecamp.png' width='32' height='32'> Basecamp | 3 |
| <img src='Logos/batfi.png' width='32' height='32'> BatFi | 2.4.2 |
| <img src='Logos/bbedit.png' width='32' height='32'> BBEdit | 15.5 |
| <img src='Logos/beeper.png' width='32' height='32'> Beeper | 4.0.747 |
| <img src='Logos/betterdisplay.png' width='32' height='32'> BetterDisplay | 3.5.6 |
| <img src='Logos/bettermouse.png' width='32' height='32'> BetterMouse | 1.6 |
| <img src='Logos/bettertouchtool.png' width='32' height='32'> BetterTouchTool | 5.450 |
| <img src='Logos/betterzip.png' width='32' height='32'> BetterZip | 5.3.4 |
| <img src='Logos/beyond_compare.png' width='32' height='32'> Beyond Compare | 5.1.0.31016 |
| <img src='Logos/binary_ninja.png' width='32' height='32'> Binary Ninja | 5.0.7486 |
| <img src='Logos/bitwarden.png' width='32' height='32'> Bitwarden | 2025.5.1 |
| <img src='Logos/bitwig_studio.png' width='32' height='32'> Bitwig Studio | 5.3.8 |
| <img src='Logos/blender.png' width='32' height='32'> Blender | 4.4.3 |
| <img src='Logos/bleunlock.png' width='32' height='32'> BLEUnlock | 1.12.2 |
| <img src='Logos/blip.png' width='32' height='32'> blip | 1.1.8 |
| <img src='Logos/blizzard_battlenet.png' width='32' height='32'> Blizzard Battle.net | 1.18.10.3141 |
| <img src='Logos/blurscreen.png' width='32' height='32'> BlurScreen | 1.0 |
| <img src='Logos/boltai.png' width='32' height='32'> BoltAI | 1.35.3 |
| <img src='Logos/bome_network.png' width='32' height='32'> Bome Network | 1.6.0 |
| <img src='Logos/boop.png' width='32' height='32'> Boop | 1.4.0 |
| <img src='Logos/boxcryptor.png' width='32' height='32'> Boxcryptor | 3.13.680 |
| <img src='Logos/brave.png' width='32' height='32'> Brave | 1.79.119.0 |
| <img src='Logos/breaktimer.png' width='32' height='32'> BreakTimer | 1.3.2 |
| <img src='Logos/bruno.png' width='32' height='32'> Bruno | 2.4.0 |
| <img src='Logos/busycal.png' width='32' height='32'> BusyCal | 2025.2.2 |
| <img src='Logos/busycontacts.png' width='32' height='32'> BusyContacts | 2025.2.2 |
| <img src='Logos/caffeine.png' width='32' height='32'> Caffeine | 1.5.2 |
| <img src='Logos/calibre.png' width='32' height='32'> calibre | 8.4.0 |
| <img src='Logos/calmly_writer.png' width='32' height='32'> Calmly Writer | 2.0.59 |
| <img src='Logos/camtasia.png' width='32' height='32'> Camtasia | 25.1.2 |
| <img src='Logos/canva.png' width='32' height='32'> Canva | 1.110.0 |
| <img src='Logos/capcut.png' width='32' height='32'> CapCut | 3.3.0.1159 |
| <img src='Logos/chatgpt.png' width='32' height='32'> ChatGPT | 1.2025.154 |
| <img src='Logos/chatwise.png' width='32' height='32'> ChatWise | 0.8.63 |
| <img src='Logos/chrome_remote_desktop.png' width='32' height='32'> Chrome Remote Desktop | 137.0.7151.18 |
| <img src='Logos/cisco_jabber.png' width='32' height='32'> Cisco Jabber | 20250430033337 |
| <img src='Logos/citrix_workspace.png' width='32' height='32'> Citrix Workspace | 25.03.10.24 |
| <img src='Logos/claude.png' width='32' height='32'> Claude | 0.10.14 |
| <img src='Logos/cleanmymac.png' width='32' height='32'> CleanMyMac | 5.0.9 |
| <img src='Logos/cleanshot.png' width='32' height='32'> CleanShot | 4.8 |
| <img src='Logos/clion.png' width='32' height='32'> CLion | 2025.1.2 |
| <img src='Logos/clipy.png' width='32' height='32'> Clipy | 1.2.1 |
| <img src='Logos/clop.png' width='32' height='32'> Clop | 2.10.0 |
| <img src='Logos/cloudflare_warp.png' width='32' height='32'> Cloudflare WARP | 2025.4.943.0 |
| <img src='Logos/codeedit.png' width='32' height='32'> CodeEdit | 0.3.4 |
| <img src='Logos/coderunner.png' width='32' height='32'> CodeRunner | 4.4.1 |
| <img src='Logos/company_portal.png' width='32' height='32'> Company Portal | 5.2504.1 |
| <img src='Logos/copilot_for_xcode.png' width='32' height='32'> Copilot for Xcode | 0.35.8 |
| <img src='Logos/copyclip.png' width='32' height='32'> CopyClip | 2.9.99.2 |
| <img src='Logos/coteditor.png' width='32' height='32'> CotEditor | 5.1.7 |
| <img src='Logos/cryptomator.png' width='32' height='32'> Cryptomator | 1.16.2 |
| <img src='Logos/crystalfetch.png' width='32' height='32'> Crystalfetch | 2.2.0 |
| <img src='Logos/cursor.png' width='32' height='32'> Cursor | 1.0.1 |
| <img src='Logos/cyberduck.png' width='32' height='32'> Cyberduck | 9.1.4 |
| <img src='Logos/daisydisk.png' width='32' height='32'> DaisyDisk | 4.31 |
| <img src='Logos/dangerzone.png' width='32' height='32'> Dangerzone | 0.9.0 |
| <img src='Logos/dataflare.png' width='32' height='32'> Dataflare | 2.0.2 |
| <img src='Logos/datagrip.png' width='32' height='32'> DataGrip | 2025.1.3 |
| <img src='Logos/dataspell.png' width='32' height='32'> DataSpell | 2025.1.1 |
| <img src='Logos/db_browser_for_sqlite.png' width='32' height='32'> DB Browser for SQLite | 3.13.1 |
| <img src='Logos/dbeaver_community_edition.png' width='32' height='32'> DBeaver Community Edition | 25.1.0 |
| <img src='Logos/dbgate.png' width='32' height='32'> DbGate | 6.4.2 |
| <img src='Logos/deepl.png' width='32' height='32'> DeepL | 25.5.42089655 |
| <img src='Logos/deskpad.png' width='32' height='32'> DeskPad | 1.3.2 |
| <img src='Logos/devtoys.png' width='32' height='32'> DevToys | 2.0.8.0 |
| <img src='Logos/devutils.png' width='32' height='32'> DevUtils | 1.17.0 |
| <img src='Logos/discord.png' width='32' height='32'> Discord | 0.0.349 |
| <img src='Logos/displaylink_usb_graphics_software.png' width='32' height='32'> DisplayLink USB Graphics Software | 1.12.3 |
| <img src='Logos/dockdoor.png' width='32' height='32'> DockDoor | 1.13.1 |
| <img src='Logos/docker_desktop.png' width='32' height='32'> Docker Desktop | 4.42.0 |
| <img src='Logos/dockside.png' width='32' height='32'> Dockside | 1.9.54 |
| <img src='Logos/dosbox.png' width='32' height='32'> DOSBox | 0.74-3 |
| <img src='Logos/doughnut.png' width='32' height='32'> Doughnut | 2.0.1 |
| <img src='Logos/downie.png' width='32' height='32'> Downie | 4.9.17 |
| <img src='Logos/drawio_desktop.png' width='32' height='32'> draw.io Desktop | 27.0.9 |
| <img src='Logos/drawbot.png' width='32' height='32'> DrawBot | 3.132 |
| <img src='Logos/drivedx.png' width='32' height='32'> DriveDX | 1.12.1 |
| <img src='Logos/dropbox.png' width='32' height='32'> Dropbox | 226.4.5094 |
| <img src='Logos/dropdmg.png' width='32' height='32'> DropDMG | 3.6.9 |
| <img src='Logos/dropshare.png' width='32' height='32'> Dropshare | 6.3 |
| <img src='Logos/duckduckgo.png' width='32' height='32'> DuckDuckGo | 1.142.0 |
| <img src='Logos/easydict.png' width='32' height='32'> Easydict | 2.14.1 |
| <img src='Logos/easyfind.png' width='32' height='32'> EasyFind | 5.0.2 |
| <img src='Logos/eclipse_temurin_java_development_kit.png' width='32' height='32'> Eclipse Temurin Java Development Kit | 24.0.1 |
| <img src='Logos/edrawmax.png' width='32' height='32'> EdrawMax | 12.6.1 |
| <img src='Logos/elephas.png' width='32' height='32'> Elephas | 11.1087 |
| <img src='Logos/elgato_camera_hub.png' width='32' height='32'> Elgato Camera Hub | 2.0.0.5750 |
| <img src='Logos/elgato_capture_device_utility.png' width='32' height='32'> Elgato Capture Device Utility | 1.3.1 |
| <img src='Logos/elgato_stream_deck.png' width='32' height='32'> Elgato Stream Deck | 6.9.1.21711 |
| <img src='Logos/elgato_wave_link.png' width='32' height='32'> Elgato Wave Link | 2.0.6.3780 |
| <img src='Logos/ente.png' width='32' height='32'> Ente | 1.7.13 |
| <img src='Logos/ente_auth.png' width='32' height='32'> Ente Auth | 4.4.0 |
| <img src='Logos/epic_games_launcher.png' width='32' height='32'> Epic Games Launcher | 18.5.0 |
| <img src='Logos/espanso.png' width='32' height='32'> Espanso | 2.2.1 |
| <img src='Logos/etcher.png' width='32' height='32'> Etcher | 2.1.2 |
| <img src='Logos/evernote.png' width='32' height='32'> Evernote | 10.105.4 |
| <img src='Logos/flux.png' width='32' height='32'> f.lux | 42.2 |
| <img src='Logos/facebook_messenger.png' width='32' height='32'> Facebook Messenger | 510.0.0.1.116 |
| <img src='Logos/fantastical.png' width='32' height='32'> Fantastical | 4.0.14 |
| <img src='Logos/fathom.png' width='32' height='32'> Fathom | 1.40.0 |
| <img src='Logos/figma.png' width='32' height='32'> Figma | 125.4.9 |
| <img src='Logos/fission.png' width='32' height='32'> Fission | 2.8.8 |
| <img src='Logos/flameshot.png' width='32' height='32'> Flameshot | 12.1.0 |
| <img src='Logos/flowvision.png' width='32' height='32'> FlowVision | 1.6.4 |
| <img src='Logos/flycut.png' width='32' height='32'> Flycut | 1.9.6 |
| <img src='Logos/forecast.png' width='32' height='32'> Forecast | 0.9.6 |
| <img src='Logos/foxit_pdf_editor.png' width='32' height='32'> Foxit PDF Editor | 13.1.7.63027 |
| <img src='Logos/free_ruler.png' width='32' height='32'> Free Ruler | 2.0.8 |
| <img src='Logos/freecad.png' width='32' height='32'> FreeCAD | 1.0.1 |
| <img src='Logos/freelens.png' width='32' height='32'> Freelens | 1.3.2 |
| <img src='Logos/freemacsoft_appcleaner.png' width='32' height='32'> FreeMacSoft AppCleaner | 3.6.8 |
| <img src='Logos/freetube.png' width='32' height='32'> FreeTube | 0.23.5 |
| <img src='Logos/fsmonitor.png' width='32' height='32'> FSMonitor | 1.2 |
| <img src='Logos/gather_town.png' width='32' height='32'> Gather Town | 1.32.0 |
| <img src='Logos/geany.png' width='32' height='32'> Geany | 2.0 |
| <img src='Logos/geekbench.png' width='32' height='32'> Geekbench | 6.4.0 |
| <img src='Logos/geekbench_ai.png' width='32' height='32'> Geekbench AI | 1.3.0 |
| <img src='Logos/gemini.png' width='32' height='32'> Gemini | 2.9.11 |
| <img src='Logos/gephi.png' width='32' height='32'> Gephi | 0.10.1 |
| <img src='Logos/ghostty.png' width='32' height='32'> Ghostty | 1.1.3 |
| <img src='Logos/gifox.png' width='32' height='32'> gifox | 2.7.0+0 |
| <img src='Logos/gimp.png' width='32' height='32'> GIMP | 3.0.4 |
| <img src='Logos/git_credential_manager.png' width='32' height='32'> Git Credential Manager | 2.6.1 |
| <img src='Logos/gitfinder.png' width='32' height='32'> GitFinder | 1.7.11 |
| <img src='Logos/github_desktop.png' width='32' height='32'> GitHub Desktop | 3.4.20-d2e01c60 |
| <img src='Logos/gitkraken.png' width='32' height='32'> GitKraken | 11.1.1 |
| <img src='Logos/godot_engine.png' width='32' height='32'> Godot Engine | 4.4.1 |
| <img src='Logos/godspeed.png' width='32' height='32'> Godspeed | 1.9.1 |
| <img src='Logos/goland.png' width='32' height='32'> Goland | 2025.1.2 |
| <img src='Logos/google_ads_editor.png' width='32' height='32'> Google Ads Editor | 2.9 |
| <img src='Logos/google_chrome.png' width='32' height='32'> Google Chrome | 137.0.7151.69 |
| <img src='Logos/google_drive.png' width='32' height='32'> Google Drive | 109.0.3 |
| <img src='Logos/goose.png' width='32' height='32'> Goose | 1.0.27 |
| <img src='Logos/gpt_fdisk.png' width='32' height='32'> GPT fdisk | 1.0.10 |
| <img src='Logos/grammarly_desktop.png' width='32' height='32'> Grammarly Desktop | 1.121.1.0 |
| <img src='Logos/grandperspective.png' width='32' height='32'> GrandPerspective | 3.5.3 |
| <img src='Logos/hammerspoon.png' width='32' height='32'> Hammerspoon | 1.0.0 |
| <img src='Logos/hazel.png' width='32' height='32'> Hazel | 6.0.4 |
| <img src='Logos/hazeover.png' width='32' height='32'> HazeOver | 1.9.4 |
| <img src='Logos/headlamp.png' width='32' height='32'> Headlamp | 0.31.1 |
| <img src='Logos/hey.png' width='32' height='32'> HEY | 1.2.17 |
| <img src='Logos/hidden_bar.png' width='32' height='32'> Hidden Bar | 1.9 |
| <img src='Logos/highlight.png' width='32' height='32'> Highlight | 1.2.65 |
| <img src='Logos/home_assistant.png' width='32' height='32'> Home Assistant | 2025.5 |
| <img src='Logos/homerow.png' width='32' height='32'> Homerow | 1.4.0 |
| <img src='Logos/hp_easy_admin.png' width='32' height='32'> HP Easy Admin | 2.15.0 |
| <img src='Logos/huggingchat.png' width='32' height='32'> HuggingChat | 0.7.0 |
| <img src='Logos/huly.png' width='32' height='32'> Huly | 0.6.502 |
| <img src='Logos/hyper.png' width='32' height='32'> Hyper | 3.4.1 |
| <img src='Logos/hyperkey.png' width='32' height='32'> Hyperkey | 0.47 |
| <img src='Logos/ice.png' width='32' height='32'> Ice | 0.11.12 |
| <img src='Logos/iina.png' width='32' height='32'> IINA | 1.3.5 |
| <img src='Logos/imazing.png' width='32' height='32'> iMazing | 3.2.1 |
| <img src='Logos/imazing_profile_editor.png' width='32' height='32'> iMazing Profile Editor | 2.0.0 |
| <img src='Logos/inkscape.png' width='32' height='32'> Inkscape | 1.4.230579 |
| <img src='Logos/insomnia.png' width='32' height='32'> Insomnia | 11.2.0 |
| <img src='Logos/insta360_studio.png' width='32' height='32'> Insta360 Studio | 5.6.1 |
| <img src='Logos/intellij_idea_community_edition.png' width='32' height='32'> IntelliJ IDEA Community Edition | 2025.1.2 |
| <img src='Logos/istherenet.png' width='32' height='32'> IsThereNet | 1.7.1 |
| <img src='Logos/iterm2.png' width='32' height='32'> iTerm2 | 3.5.14 |
| <img src='Logos/itsycal.png' width='32' height='32'> Itsycal | 0.15.6 |
| <img src='Logos/jabra_direct.png' width='32' height='32'> Jabra Direct | 6.22.11401 |
| <img src='Logos/jamie.png' width='32' height='32'> Jamie | 4.2.5 |
| <img src='Logos/jellyfin.png' width='32' height='32'> Jellyfin | 10.10.7 |
| <img src='Logos/jetbrains_phpstorm.png' width='32' height='32'> JetBrains PhpStorm | 2025.1.2 |
| <img src='Logos/jetbrains_pycharm_community_edition.png' width='32' height='32'> Jetbrains PyCharm Community Edition | 2025.1.1.1 |
| <img src='Logos/jetbrains_rider.png' width='32' height='32'> JetBrains Rider | 2025.1.2 |
| <img src='Logos/jetbrains_toolbox.png' width='32' height='32'> JetBrains Toolbox | 2.6.3 |
| <img src='Logos/joplin.png' width='32' height='32'> Joplin | 3.3.13 |
| <img src='Logos/jumpcut.png' width='32' height='32'> Jumpcut | 0.84 |
| <img src='Logos/jumpshare.png' width='32' height='32'> Jumpshare | 3.3.18 |
| <img src='Logos/kap.png' width='32' height='32'> Kap | 3.6.0 |
| <img src='Logos/karabiner_elements.png' width='32' height='32'> Karabiner Elements | 15.3.0 |
| <img src='Logos/keepassxc.png' width='32' height='32'> KeePassXC | 2.7.10 |
| <img src='Logos/keeper_password_manager.png' width='32' height='32'> Keeper Password Manager | 17.2 |
| <img src='Logos/keka.png' width='32' height='32'> Keka | 1.5.1 |
| <img src='Logos/keybase.png' width='32' height='32'> Keybase | 6.5.1 |
| <img src='Logos/keycastr.png' width='32' height='32'> KeyCastr | 0.10.3 |
| <img src='Logos/keyclu.png' width='32' height='32'> KeyClu | 0.30.1 |
| <img src='Logos/kitty.png' width='32' height='32'> kitty | 0.42.1 |
| <img src='Logos/klokki.png' width='32' height='32'> Klokki | 1.3.7 |
| <img src='Logos/krisp.png' width='32' height='32'> Krisp | 3.2.6 |
| <img src='Logos/krita.png' width='32' height='32'> Krita | 5.2.9 |
| <img src='Logos/langgraph_studio.png' width='32' height='32'> LangGraph Studio | 0.0.37 |
| <img src='Logos/last_window_quits.png' width='32' height='32'> Last Window Quits | 1.1.4 |
| <img src='Logos/lens.png' width='32' height='32'> Lens | 2025.6.21515 |
| <img src='Logos/libreoffice.png' width='32' height='32'> LibreOffice | 25.2.4 |
| <img src='Logos/librewolf.png' width='32' height='32'> LibreWolf | 139.0.1 |
| <img src='Logos/little_snitch.png' width='32' height='32'> Little Snitch | 6.2.3 |
| <img src='Logos/lm_studio.png' width='32' height='32'> LM Studio | 0.3.16 |
| <img src='Logos/LocalSend.png' width='32' height='32'> LocalSend | 1.17.0 |
| <img src='Logos/logitech_g_hub.png' width='32' height='32'> Logitech G HUB | 2025.4.719084 |
| <img src='Logos/logitech_options.png' width='32' height='32'> Logitech Options+ | 1.91.722586 |
| <img src='Logos/lookaway.png' width='32' height='32'> LookAway | 1.13.1 |
| <img src='Logos/loop.png' width='32' height='32'> Loop | 1.2.0 |
| <img src='Logos/lulu.png' width='32' height='32'> LuLu | 3.1.5 |
| <img src='Logos/lunatask.png' width='32' height='32'> Lunatask | 2.0.22 |
| <img src='Logos/löve.png' width='32' height='32'> LÖVE | 11.5 |
| <img src='Logos/maccy.png' width='32' height='32'> Maccy | 2.3.0 |
| <img src='Logos/macdown.png' width='32' height='32'> MacDown | 0.7.2 |
| <img src='Logos/macfuse.png' width='32' height='32'> macFUSE | 4.10.2 |
| <img src='Logos/macpass.png' width='32' height='32'> MacPass | 0.8.1 |
| <img src='Logos/macs_fan_control.png' width='32' height='32'> Macs Fan Control | 1.5.17 |
| <img src='Logos/mactex.png' width='32' height='32'> MacTeX | 2025.0308 |
| <img src='Logos/macwhisper.png' width='32' height='32'> MacWhisper | 12.11 |
| <img src='Logos/maestral.png' width='32' height='32'> Maestral | 1.9.4 |
| <img src='Logos/magicquit.png' width='32' height='32'> MagicQuit | 1.4 |
| <img src='Logos/malwarebytes_for_mac.png' width='32' height='32'> Malwarebytes for Mac | 5.15.1.3151 |
| <img src='Logos/markedit.png' width='32' height='32'> MarkEdit | 1.24.0 |
| <img src='Logos/marsedit.png' width='32' height='32'> MarsEdit | 5.3.4 |
| <img src='Logos/marta_file_manager.png' width='32' height='32'> Marta File Manager | 0.8.2 |
| <img src='Logos/mattermost.png' width='32' height='32'> Mattermost | 5.12.1 |
| <img src='Logos/medis.png' width='32' height='32'> Medis | 2.15.1 |
| <img src='Logos/meetingbar.png' width='32' height='32'> MeetingBar | 4.11.5 |
| <img src='Logos/meld_for_macos.png' width='32' height='32'> Meld for macOS | 3.22.3+105 |
| <img src='Logos/menubar_stats.png' width='32' height='32'> MenuBar Stats | 3.9 |
| <img src='Logos/micro_snitch.png' width='32' height='32'> Micro Snitch | 1.6.1 |
| <img src='Logos/microsoft_auto_update.png' width='32' height='32'> Microsoft Auto Update | 4.79.25033028 |
| <img src='Logos/microsoft_azure_storage_explorer.png' width='32' height='32'> Microsoft Azure Storage Explorer | 1.38.0 |
| <img src='Logos/microsoft_edge.png' width='32' height='32'> Microsoft Edge | 137.0.3296.68 |
| <img src='Logos/microsoft_office.png' width='32' height='32'> Microsoft Office | 16.98.25060824 |
| <img src='Logos/microsoft_teams.png' width='32' height='32'> Microsoft Teams | 25122.1207.3700.1444 |
| <img src='Logos/microsoft_visual_studio_code.png' width='32' height='32'> Microsoft Visual Studio Code | 1.100.3 |
| <img src='Logos/middle.png' width='32' height='32'> Middle | 1.9 |
| <img src='Logos/middleclick.png' width='32' height='32'> MiddleClick | 3.1.0 |
| <img src='Logos/mindmanager.png' width='32' height='32'> Mindmanager | 24.1.155 |
| <img src='Logos/miro.png' width='32' height='32'> Miro | 0.11.99 |
| <img src='Logos/mist.png' width='32' height='32'> Mist | 0.20.1 |
| <img src='Logos/mitmproxy.png' width='32' height='32'> mitmproxy | 12.1.1 |
| <img src='Logos/mixxx.png' width='32' height='32'> Mixxx | 2.5.1 |
| <img src='Logos/mobirise.png' width='32' height='32'> Mobirise | 6.0.6 |
| <img src='Logos/mockoon.png' width='32' height='32'> Mockoon | 9.2.0 |
| <img src='Logos/mongodb_compass.png' width='32' height='32'> MongoDB Compass | 1.46.3 |
| <img src='Logos/monitorcontrol.png' width='32' height='32'> MonitorControl | 4.3.3 |
| <img src='Logos/moonlight.png' width='32' height='32'> Moonlight | 6.1.0 |
| <img src='Logos/mos.png' width='32' height='32'> Mos | 3.5.0 |
| <img src='Logos/motrix.png' width='32' height='32'> Motrix | 1.8.19 |
| <img src='Logos/mountain_duck.png' width='32' height='32'> Mountain Duck | 4.17.4 |
| <img src='Logos/mounty_for_ntfs.png' width='32' height='32'> Mounty for NTFS | 2.4 |
| <img src='Logos/mouseless.png' width='32' height='32'> mouseless | 0.3.1 |
| <img src='Logos/mozilla_firefox.png' width='32' height='32'> Mozilla Firefox | 139.0.4 |
| <img src='Logos/mozilla_firefox_developer_edition.png' width='32' height='32'> Mozilla Firefox Developer Edition | 140.0b7 |
| <img src='Logos/mozilla_firefox_esr.png' width='32' height='32'> Mozilla Firefox ESR | 128.11.0 |
| <img src='Logos/mozilla_thunderbird.png' width='32' height='32'> Mozilla Thunderbird | 139.0.2 |
| <img src='Logos/multi.png' width='32' height='32'> Multi | 0.538.2 |
| <img src='Logos/multiviewer_for_f1.png' width='32' height='32'> MultiViewer for F1 | 1.43.2 |
| <img src='Logos/mural.png' width='32' height='32'> MURAL | 3.0.4 |
| <img src='Logos/mysql_workbench.png' width='32' height='32'> MySQL Workbench | 8.0.42 |
| <img src='Logos/name_mangler.png' width='32' height='32'> Name Mangler | 3.9.3 |
| <img src='Logos/neofinder.png' width='32' height='32'> NeoFinder | 8.9 |
| <img src='Logos/netbeans_ide.png' width='32' height='32'> NetBeans IDE | 26 |
| <img src='Logos/netiquette.png' width='32' height='32'> Netiquette | 2.3.0 |
| <img src='Logos/netnewswire.png' width='32' height='32'> NetNewsWire | 6.1.9 |
| <img src='Logos/nextcloud.png' width='32' height='32'> Nextcloud | 3.16.5 |
| <img src='Logos/nitro_pdf_pro.png' width='32' height='32'> Nitro PDF Pro | 14.7 |
| <img src='Logos/nomachine.png' width='32' height='32'> NoMachine | 8.16.1 |
| <img src='Logos/nordlayer.png' width='32' height='32'> NordLayer | 3.6.0 |
| <img src='Logos/nordlocker.png' width='32' height='32'> NordLocker | 4.26.1 |
| <img src='Logos/nordpass.png' width='32' height='32'> NordPass | 6.2.13 |
| <img src='Logos/nordvpn.png' width='32' height='32'> NordVPN | 8.39.0 |
| <img src='Logos/nosql_workbench.png' width='32' height='32'> NoSQL Workbench | 3.13.6 |
| <img src='Logos/nota_gyazo_gif.png' width='32' height='32'> Nota Gyazo GIF | 9.10.0 |
| <img src='Logos/notesollama.png' width='32' height='32'> NotesOllama | 0.2.6 |
| <img src='Logos/notion.png' width='32' height='32'> Notion | 4.12.3 |
| <img src='Logos/notion_calendar.png' width='32' height='32'> Notion Calendar | 1.130.0 |
| <img src='Logos/notunes.png' width='32' height='32'> noTunes | 3.5 |
| <img src='Logos/noun_project.png' width='32' height='32'> Noun Project | 2.3 |
| <img src='Logos/novabench.png' width='32' height='32'> Novabench | 5.5.4 |
| <img src='Logos/nucleo.png' width='32' height='32'> Nucleo | 4.1.6 |
| <img src='Logos/nudge.png' width='32' height='32'> Nudge | 2.0.12.81807 |
| <img src='Logos/nvidia_geforce_now.png' width='32' height='32'> NVIDIA GeForce NOW | 2.0.74.169 |
| <img src='Logos/obs.png' width='32' height='32'> OBS | 31.0.3 |
| <img src='Logos/obsidian.png' width='32' height='32'> Obsidian | 1.8.10 |
| <img src='Logos/okta_advanced_server_access.png' width='32' height='32'> Okta Advanced Server Access | 1.90.0 |
| <img src='Logos/ollama.png' width='32' height='32'> Ollama | 0.9.0 |
| <img src='Logos/omnifocus.png' width='32' height='32'> OmniFocus | 4.6 |
| <img src='Logos/omnioutliner.png' width='32' height='32'> OmniOutliner | 5.14.3 |
| <img src='Logos/omnissa_horizon_client.png' width='32' height='32'> Omnissa Horizon Client | 2503-8.15.0-14236092062 |
| <img src='Logos/onedrive.png' width='32' height='32'> OneDrive | 25.075.0420.0002 |
| <img src='Logos/onyx.png' width='32' height='32'> OnyX | 4.7.9 |
| <img src='Logos/openmtp.png' width='32' height='32'> OpenMTP | 3.2.25 |
| <img src='Logos/openvpn_connect_client.png' width='32' height='32'> OpenVPN Connect client | 3.7.1 |
| <img src='Logos/opera.png' width='32' height='32'> Opera | 119.0.5497.70 |
| <img src='Logos/oracle_virtualbox.png' width='32' height='32'> Oracle VirtualBox | 7.1.10 |
| <img src='Logos/orbstack.png' width='32' height='32'> OrbStack | 1.11.3 |
| <img src='Logos/orca_slicer.png' width='32' height='32'> Orca Slicer | 2.3.0 |
| <img src='Logos/orka_cli.png' width='32' height='32'> Orka CLI | 2.4.0 |
| <img src='Logos/orka_desktop.png' width='32' height='32'> Orka Desktop | 3.0.0 |
| <img src='Logos/overflow.png' width='32' height='32'> Overflow | 3.2.1 |
| <img src='Logos/oversight.png' width='32' height='32'> OverSight | 2.4.0 |
| <img src='Logos/Packages.png' width='32' height='32'> Packages | 1.2.10 |
| <img src='Logos/paintbrush.png' width='32' height='32'> Paintbrush | 2.6.0 |
| <img src='Logos/paletro.png' width='32' height='32'> Paletro | 1.11.0 |
| <img src='Logos/panic_nova.png' width='32' height='32'> Panic Nova | 12.4 |
| <img src='Logos/parallels_client.png' width='32' height='32'> Parallels Client | 19.4.3 |
| <img src='Logos/parallels_desktop.png' width='32' height='32'> Parallels Desktop | 20.3.2-55975 |
| <img src='Logos/parsec.png' width='32' height='32'> Parsec | 150-99 |
| <img src='Logos/pastebot.png' width='32' height='32'> Pastebot | 2.4.6 |
| <img src='Logos/pdf_expert.png' width='32' height='32'> PDF Expert | 3.10.15 |
| <img src='Logos/pdf_pals.png' width='32' height='32'> PDF Pals | 1.9.0 |
| <img src='Logos/pearcleaner.png' width='32' height='32'> Pearcleaner | 4.4.5 |
| <img src='Logos/pgadmin4.png' width='32' height='32'> pgAdmin4 | 9.4 |
| <img src='Logos/philips_hue_sync.png' width='32' height='32'> Philips Hue Sync | 1.12.2.70 |
| <img src='Logos/phoenix_slides.png' width='32' height='32'> Phoenix Slides | 1.5.9 |
| <img src='Logos/pika.png' width='32' height='32'> Pika | 1.0.2 |
| <img src='Logos/piphero.png' width='32' height='32'> PiPHero | 1.2.0 |
| <img src='Logos/pixelsnap.png' width='32' height='32'> PixelSnap | 2.6.1 |
| <img src='Logos/platypus.png' width='32' height='32'> Platypus | 5.4.1 |
| <img src='Logos/plex.png' width='32' height='32'> Plex | 1.109.0.329 |
| <img src='Logos/plistedit_pro.png' width='32' height='32'> PlistEdit Pro | 1.9.7 |
| <img src='Logos/podman_desktop.png' width='32' height='32'> Podman Desktop | 1.19.1 |
| <img src='Logos/popchar_x.png' width='32' height='32'> PopChar X | 10.4 |
| <img src='Logos/portx.png' width='32' height='32'> portx | 2.2.12 |
| <img src='Logos/postico.png' width='32' height='32'> Postico | 2.1.2 |
| <img src='Logos/postman.png' width='32' height='32'> Postman | 11.49.0 |
| <img src='Logos/powershell.png' width='32' height='32'> PowerShell | 7.5.1 |
| <img src='Logos/principle.png' width='32' height='32'> Principle | 6.39 |
| <img src='Logos/privileges.png' width='32' height='32'> Privileges | 2.3.0 |
| <img src='Logos/processspy.png' width='32' height='32'> ProcessSpy | 1.7.6 |
| <img src='Logos/pronotes.png' width='32' height='32'> ProNotes | 0.7.7 |
| <img src='Logos/proton_drive.png' width='32' height='32'> Proton Drive | 2.5.0 |
| <img src='Logos/proton_mail.png' width='32' height='32'> Proton Mail | 1.8.0 |
| <img src='Logos/proton_pass.png' width='32' height='32'> Proton Pass | 1.31.5 |
| <img src='Logos/protonvpn.png' width='32' height='32'> ProtonVPN | 4.8.0 |
| <img src='Logos/proxyman.png' width='32' height='32'> Proxyman | 5.21.0 |
| <img src='Logos/ps_remote_play.png' width='32' height='32'> PS Remote Play | 8.0.0 |
| <img src='Logos/pulsar.png' width='32' height='32'> Pulsar | 1.128.0 |
| <img src='Logos/qBittorrent.png' width='32' height='32'> qBittorrent | 5.0.5 |
| <img src='Logos/qlab.png' width='32' height='32'> QLab | 5.4.11 |
| <img src='Logos/qq.png' width='32' height='32'> QQ | 6.9.73 |
| <img src='Logos/qspace_pro.png' width='32' height='32'> QSpace Pro | 5.3.4 |
| <img src='Logos/quarto.png' width='32' height='32'> quarto | 1.7.31 |
| <img src='Logos/quicklook_video.png' width='32' height='32'> QuickLook Video | 2.21 |
| <img src='Logos/qview.png' width='32' height='32'> qView | 6.1 |
| <img src='Logos/raindropio.png' width='32' height='32'> Raindrop.io | 5.6.76 |
| <img src='Logos/rancher_desktop.png' width='32' height='32'> Rancher Desktop | 1.19.1 |
| <img src='Logos/raycast.png' width='32' height='32'> Raycast | 1.99.4 |
| <img src='Logos/reactotron.png' width='32' height='32'> Reactotron | 3.7.7 |
| <img src='Logos/readest.png' width='32' height='32'> Readest | 0.9.55 |
| <img src='Logos/real_vnc_viewer.png' width='32' height='32'> Real VNC Viewer | 7.13.1 |
| <img src='Logos/rectangle.png' width='32' height='32'> Rectangle | 0.87 |
| <img src='Logos/rectangle_pro.png' width='32' height='32'> Rectangle Pro | 3.53 |
| <img src='Logos/recut.png' width='32' height='32'> Recut | 2.1.7 |
| <img src='Logos/redis_insight.png' width='32' height='32'> Redis Insight | 2.70.0 |
| <img src='Logos/reflector.png' width='32' height='32'> Reflector | 4.1.2 |
| <img src='Logos/remote_desktop_manager.png' width='32' height='32'> Remote Desktop Manager | 2025.2.6.8 |
| <img src='Logos/remote_help.png' width='32' height='32'> Remote Help | 1.0.2404171 |
| <img src='Logos/reqable.png' width='32' height='32'> Reqable | 2.33.12 |
| <img src='Logos/requestly.png' width='32' height='32'> Requestly | 25.6.5 |
| <img src='Logos/retcon.png' width='32' height='32'> Retcon | 1.3.0 |
| <img src='Logos/rhinoceros.png' width='32' height='32'> Rhinoceros | 8.19.25132.01002 |
| <img src='Logos/rive.png' width='32' height='32'> Rive | 0.8.3105 |
| <img src='Logos/rocket.png' width='32' height='32'> Rocket | 1.9.4 |
| <img src='Logos/rocket_typist.png' width='32' height='32'> Rocket Typist | 3.2.2 |
| <img src='Logos/rocketchat.png' width='32' height='32'> Rocket.Chat | 4.5.0 |
| <img src='Logos/rode_central.png' width='32' height='32'> Rode Central | 2.0.99 |
| <img src='Logos/rode_connect.png' width='32' height='32'> Rode Connect | 1.3.43 |
| <img src='Logos/rotato.png' width='32' height='32'> Rotato | 151 |
| <img src='Logos/rstudio.png' width='32' height='32'> RStudio | 2025.05.1 |
| <img src='Logos/rsyncui.png' width='32' height='32'> RsyncUI | 2.5.8 |
| <img src='Logos/rustdesk.png' width='32' height='32'> RustDesk | 1.4.0 |
| <img src='Logos/sabnzbd.png' width='32' height='32'> SABnzbd | 4.5.1 |
| <img src='Logos/santa.png' width='32' height='32'> Santa | 2025.5 |
| <img src='Logos/screenfocus.png' width='32' height='32'> ScreenFocus | 1.1.1 |
| <img src='Logos/sequel_ace.png' width='32' height='32'> Sequel Ace | 5.0.8 |
| <img src='Logos/shottr.png' width='32' height='32'> Shottr | 1.8.1 |
| <img src='Logos/signal.png' width='32' height='32'> Signal | 7.56.1 |
| <img src='Logos/silentknight.png' width='32' height='32'> SilentKnight | 2.11 |
| <img src='Logos/sketch.png' width='32' height='32'> Sketch | 2025.1.2 |
| <img src='Logos/sketchup.png' width='32' height='32'> SketchUp | 2025.0.659.288 |
| <img src='Logos/skim.png' width='32' height='32'> Skim | 1.7.10 |
| <img src='Logos/slack.png' width='32' height='32'> Slack | 4.44.65 |
| <img src='Logos/snagit.png' width='32' height='32'> Snagit | 2025.2.0 |
| <img src='Logos/splashtop_business.png' width='32' height='32'> Splashtop Business | 3.7.4.2 |
| <img src='Logos/splice.png' width='32' height='32'> Splice | 5.3.2 |
| <img src='Logos/spline.png' width='32' height='32'> Spline | 0.12.5 |
| <img src='Logos/spotify.png' width='32' height='32'> Spotify | 1.2.65.255 |
| <img src='Logos/sproutcube_shortcat.png' width='32' height='32'> Sproutcube Shortcat | 0.12.0 |
| <img src='Logos/sqlpro_for_mssql.png' width='32' height='32'> SQLPro for MSSQL | 2025.10 |
| <img src='Logos/sqlpro_for_mysql.png' width='32' height='32'> SQLPro for MySQL | 2025.10 |
| <img src='Logos/sqlpro_for_postgres.png' width='32' height='32'> SQLPro for Postgres | 2025.06 |
| <img src='Logos/sqlpro_for_sqlite.png' width='32' height='32'> SQLPro for SQLite | 2025.07 |
| <img src='Logos/sqlpro_studio.png' width='32' height='32'> SQLPro Studio | 2025.10 |
| <img src='Logos/squirrel.png' width='32' height='32'> Squirrel | 1.0.3 |
| <img src='Logos/starface.png' width='32' height='32'> Starface | 9.1.0 |
| <img src='Logos/stats.png' width='32' height='32'> Stats | 2.11.45 |
| <img src='Logos/steam.png' width='32' height='32'> Steam | 4.0 |
| <img src='Logos/steermouse.png' width='32' height='32'> SteerMouse | 5.7.4 |
| <img src='Logos/stretchly.png' width='32' height='32'> Stretchly | 1.17.2 |
| <img src='Logos/studio_3t.png' width='32' height='32'> Studio 3T | 2025.10.1 |
| <img src='Logos/sublime_merge.png' width='32' height='32'> Sublime Merge | 2102 |
| <img src='Logos/sublime_text.png' width='32' height='32'> Sublime Text | 4200 |
| <img src='Logos/superlist.png' width='32' height='32'> Superlist | 1.33.1 |
| <img src='Logos/superwhisper.png' width='32' height='32'> superwhisper | 1.46.4 |
| <img src='Logos/suspicious_package.png' width='32' height='32'> Suspicious Package | 4.5 |
| <img src='Logos/swift_shift.png' width='32' height='32'> Swift Shift | 0.27.1 |
| <img src='Logos/sync.png' width='32' height='32'> Sync | 2.2.50 |
| <img src='Logos/syncovery.png' width='32' height='32'> Syncovery | 11.4.2 |
| <img src='Logos/synology_drive.png' width='32' height='32'> Synology Drive | 3.5.2 |
| <img src='Logos/tableau_desktop.png' width='32' height='32'> Tableau Desktop | 2025.1.2 |
| <img src='Logos/tabtab.png' width='32' height='32'> TabTab | 1.3.4 |
| <img src='Logos/tailscale.png' width='32' height='32'> Tailscale | 1.84.1 |
| <img src='Logos/taskbar.png' width='32' height='32'> Taskbar | 1.4.5 |
| <img src='Logos/teacode.png' width='32' height='32'> TeaCode | 1.1.3 |
| <img src='Logos/teamviewer_host.png' width='32' height='32'> TeamViewer Host | 15 |
| <img src='Logos/teamviewer_quicksupport.png' width='32' height='32'> TeamViewer QuickSupport | 15 |
| <img src='Logos/telegram_for_macos.png' width='32' height='32'> Telegram for macOS | 11.12.1 |
| <img src='Logos/tenable_nessus_agent.png' width='32' height='32'> Tenable Nessus Agent | 10.8.4 |
| <img src='Logos/termius.png' width='32' height='32'> Termius | 9.21.2 |
| <img src='Logos/tex_live_utility.png' width='32' height='32'> TeX Live Utility | 1.54 |
| <img src='Logos/textmate.png' width='32' height='32'> TextMate | 2.0.23 |
| <img src='Logos/thonny.png' width='32' height='32'> Thonny | 4.1.7 |
| <img src='Logos/threema.png' width='32' height='32'> Threema | 1.2.48 |
| <img src='Logos/tigervnc.png' width='32' height='32'> TigerVNC | 1.15.0 |
| <img src='Logos/todoist.png' width='32' height='32'> Todoist | 9.16.1 |
| <img src='Logos/tofu.png' width='32' height='32'> Tofu | 3.0.1 |
| <img src='Logos/topaz_gigapixel_ai.png' width='32' height='32'> Topaz Gigapixel AI | 8.4.1 |
| <img src='Logos/trae.png' width='32' height='32'> Trae | 1.0.13858 |
| <img src='Logos/transmission.png' width='32' height='32'> Transmission | 4.0.6 |
| <img src='Logos/transmit.png' width='32' height='32'> Transmit | 5.10.9 |
| <img src='Logos/transnomino.png' width='32' height='32'> Transnomino | 9.3 |
| <img src='Logos/tunnelblick.png' width='32' height='32'> Tunnelblick | 8.0 |
| <img src='Logos/twingate.png' width='32' height='32'> Twingate | 2025.138.13830 |
| <img src='Logos/typora.png' width='32' height='32'> Typora | 1.10.10 |
| <img src='Logos/unnaturalscrollwheels.png' width='32' height='32'> UnnaturalScrollWheels | 1.3.0 |
| <img src='Logos/updf.png' width='32' height='32'> UPDF | 2.0.0 |
| <img src='Logos/upscayl.png' width='32' height='32'> Upscayl | 2.15.0 |
| <img src='Logos/utm.png' width='32' height='32'> UTM | 4.6.5 |
| <img src='Logos/veracrypt.png' width='32' height='32'> VeraCrypt | 1.26.24 |
| <img src='Logos/vimcal.png' width='32' height='32'> Vimcal | 1.0.35 |
| <img src='Logos/vimr.png' width='32' height='32'> VimR | 0.54.0 |
| <img src='Logos/visualvm.png' width='32' height='32'> VisualVM | 2.2 |
| <img src='Logos/vivaldi.png' width='32' height='32'> Vivaldi | 7.4.3684.46 |
| <img src='Logos/viz.png' width='32' height='32'> Viz | 2.2.1 |
| <img src='Logos/vlc_media_player.png' width='32' height='32'> VLC media player | 3.0.21 |
| <img src='Logos/vscodium.png' width='32' height='32'> VSCodium | 1.100.33714 |
| <img src='Logos/wave_terminal.png' width='32' height='32'> Wave Terminal | 0.11.3 |
| <img src='Logos/webex_teams.png' width='32' height='32'> Webex Teams | 45.6.0.32551 |
| <img src='Logos/webstorm.png' width='32' height='32'> WebStorm | 2025.1.2 |
| <img src='Logos/wechat_for_mac.png' width='32' height='32'> WeChat for Mac | 4.0.5.25 |
| <img src='Logos/whatsapp.png' width='32' height='32'> WhatsApp | 2.25.16.81 |
| <img src='Logos/windowkeys.png' width='32' height='32'> WindowKeys | 3.0 |
| <img src='Logos/windows_app.png' width='32' height='32'> Windows App | 11.1.8 |
| <img src='Logos/windsurf.png' width='32' height='32'> Windsurf | 1.10.1 |
| <img src='Logos/winehqstable.png' width='32' height='32'> WineHQ-stable | 10.0 |
| <img src='Logos/wire.png' width='32' height='32'> Wire | 3.40.5285 |
| <img src='Logos/wireshark.png' width='32' height='32'> Wireshark | 4.4.7 |
| <img src='Logos/witch.png' width='32' height='32'> Witch | 4.6.2 |
| <img src='Logos/wondershare_filmora.png' width='32' height='32'> Wondershare Filmora | 13.0.25 |
| <img src='Logos/xca.png' width='32' height='32'> XCA | 2.9.0 |
| <img src='Logos/xmind.png' width='32' height='32'> XMind | 25.04.03523-202505292348 |
| <img src='Logos/xnapper.png' width='32' height='32'> Xnapper | 1.17.1 |
| <img src='Logos/yaak.png' width='32' height='32'> Yaak | 2025.4.0 |
| <img src='Logos/yubikey_manager.png' width='32' height='32'> Yubikey Manager | 1.2.5 |
| <img src='Logos/zed.png' width='32' height='32'> Zed | 0.189.5 |
| <img src='Logos/zed_attack_proxy.png' width='32' height='32'> Zed Attack Proxy | 2.16.1 |
| <img src='Logos/zen_browser.png' width='32' height='32'> Zen Browser | 1.12.3b |
| <img src='Logos/zoom.png' width='32' height='32'> Zoom | 6.4.12.56699 |

> [!NOTE]
> Missing an app? Feel free to [request additional app support](https://github.com/ugurkocde/IntuneBrew/issues/new?labels=app-request) by creating an issue!

## 🔧 Configuration

First decide which authentication method you would like to use. There are currently the following methods implemented:

- System Managed Identity
- User Managed Identity  
- ClientSecret & ClientID using App Registration
- Certificate based authentication
- Configuration File (for non-interactive/automated scenarios)

### Using System Managed Identity

1. Open your Automation Account and select Account Settings -> Identity.
2. Turn Status on tab "System assigned" to "On".
3. Add the following API permissions to your System Managed Identity using this PowerShell script: [Microsoft Tech Community](https://techcommunity.microsoft.com/blog/integrationsonazureblog/grant-graph-api-permission-to-azure-automation-system-assigned-managed-identity/4278846)
   - DeviceManagementApps.ReadWrite.All
4. Open [Entra admin center](https://entra.microsoft.com/#view/Microsoft_AAD_IAM/StartboardApplicationsMenuBlade/~/AppAppsPreview) -> Applications -> Enterprise Applications. Change Filter "Application type" to "Managed Identities" and search for your Automation Account name. Open the entity.
5. Verify that the right permissions are set to the Managed Identity in the Security -> Permissions tab.
6. Create a new Variable in your Automation Account with the name "AuthenticationMethod" and value "SystemManagedIdentity" to use the System Managed Identity.

### Using User Assigned Managed Identity

1. Open [Azure Portal](https://portal.azure.com) and search for "Managed Identities".
2. Click "Create" and select your Azure Subscription & Resource group. Choose your region and set a name for the identity.
3. Open your Automation Account and select Account Settings -> Identity.
4. Switch to tab "User assigned" and click "Add". Choose the previously created Managed Identity.
5. Add the following API permissions to your System Managed Identity using this PowerShell script: [Microsoft Tech Community](https://techcommunity.microsoft.com/blog/integrationsonazureblog/grant-graph-api-permission-to-azure-automation-system-assigned-managed-identity/4278846)
   - DeviceManagementApps.ReadWrite.All
6. Open [Entra admin center](https://entra.microsoft.com/#view/Microsoft_AAD_IAM/StartboardApplicationsMenuBlade/~/AppAppsPreview) -> Applications -> Enterprise Applications. Change Filter "Application type" to "Managed Identities" and search for your Automation Account name. Open the entity.
7. Verify that the right permissions are set to the Managed Identity in the Security -> Permissions tab.
8. Create a new Variable in your Automation Account with the name "AuthenticationMethod" and value "UserAssignedManagedIdentity" to use the User Assigned Managed Identity.

### Using ClientSecret from Entra ID App Registration

1. Create a new App Registration in Azure
2. Add the following API permissions:
   - DeviceManagementApps.ReadWrite.All
3. Update the parameters in the script with your Azure details.
   - $appid = '<YourAppIdHere>' # App ID of the App Registration
   - $tenantid = '<YourTenantIdHere>' # Tenant ID of your EntraID
   - $certThumbprint = '<YourCertificateThumbprintHere>' # Thumbprint of the certificate associated with the App Registration

### Certificate-Based Authentication

1. Generate a self-signed certificate:

```powershell
$cert = New-SelfSignedCertificate -Subject "CN=IntuneBrew" -CertStoreLocation "Cert:\CurrentUser\My" -KeyExportPolicy Exportable -KeySpec Signature -KeyLength 2048 -KeyAlgorithm RSA -HashAlgorithm SHA256 -NotAfter (Get-Date).AddYears(2)
```

2. Export the certificate:

```powershell
$pwd = ConvertTo-SecureString -String "YourPassword" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "IntuneBrew.pfx" -Password $pwd
```

3. Upload to Azure App Registration:
   - Go to your App Registration in Azure Portal
   - Navigate to "Certificates & secrets"
   - Upload the public key portion of your certificate

### Using Configuration File

The `-ConfigFile` parameter enables non-interactive authentication, which is perfect for automation scenarios and macOS support. This method uses a JSON configuration file containing your authentication credentials.

1. Create a configuration file based on one of these templates:

**For Client Secret Authentication** (clientSecret.json):
```json
{
  "authMethod": "ClientSecret",
  "tenantId": "your-tenant-id",
  "clientId": "your-app-registration-client-id",
  "clientSecret": "your-client-secret"
}
```

**Example clientSecret.json with actual values:**
```json
{
  "authMethod": "ClientSecret",
  "tenantId": "12345678-1234-1234-1234-123456789012",
  "clientId": "87654321-4321-4321-4321-210987654321",
  "clientSecret": "xyx8Q~1234567890abcdefghijklmnopqrstuvwx"
}
```

**Important notes for clientSecret.json:**
- `authMethod`: Must be exactly "ClientSecret" (case-sensitive)
- `tenantId`: Your Azure AD tenant ID (GUID format)
- `clientId`: The Application (client) ID from your App Registration
- `clientSecret`: The secret value (not the secret ID) from your App Registration

> [!WARNING]
> - Store the clientSecret.json file securely and never commit it to version control
> - Add `clientSecret.json` to your `.gitignore` file
> - Consider using environment variables or Azure Key Vault for production scenarios
> - Client secrets expire - remember to rotate them before expiration

**For Certificate Authentication** (certificateThumbprint.json):
```json
{
  "authMethod": "Certificate",
  "tenantId": "your-tenant-id",
  "clientId": "your-app-registration-client-id",
  "certificateThumbprint": "your-certificate-thumbprint"
}
```

**Example certificateThumbprint.json with actual values:**
```json
{
  "authMethod": "Certificate",
  "tenantId": "12345678-1234-1234-1234-123456789012",
  "clientId": "87654321-4321-4321-4321-210987654321",
  "certificateThumbprint": "1234567890ABCDEF1234567890ABCDEF12345678"
}
```

**Important notes for certificateThumbprint.json:**
- `authMethod`: Must be exactly "Certificate" (case-sensitive)
- `tenantId`: Your Azure AD tenant ID (GUID format)
- `clientId`: The Application (client) ID from your App Registration
- `certificateThumbprint`: The thumbprint of the certificate uploaded to your App Registration (40 character hex string, no spaces or colons)
- The certificate must be installed in the current user or local machine certificate store

2. Ensure your App Registration has the required permissions:
   - DeviceManagementApps.ReadWrite.All

3. Use the configuration file with any IntuneBrew command:
```powershell
# Update all apps non-interactively
.\IntuneBrew.ps1 -UpdateAll -ConfigFile "clientSecret.json"

# Upload specific apps with automation
.\IntuneBrew.ps1 -Upload "slack", "zoom" -ConfigFile "certificateThumbprint.json"
```

> [!TIP]
> The ConfigFile parameter is especially useful for:
> - Automated deployments in CI/CD pipelines
> - Scheduled tasks without user interaction
> - Avoiding interactive authentication prompts

### Copy Assignments

Using the `-CopyAssignments` switch with `IntuneBrew.ps1` or creating a `CopyAssignments` Variable with Boolean Value `true` in your Azure Automation indicates that assignments from the existing app version should be copied to the new version.

### App JSON Structure

Apps are defined in JSON files with the following structure:

```json
{
  "name": "Application Name",
  "description": "Application Description",
  "version": "1.0.0",
  "url": "https://download.url/app.dmg",
  "bundleId": "com.example.app",
  "homepage": "https://app.homepage.com",
  "fileName": "app.dmg"
}
```

## 🔄 Version Management

IntuneBrew implements sophisticated version comparison logic:

- Handles various version formats (semantic versioning, build numbers)
- Supports complex version strings (e.g., "1.2.3,45678")
- Manages version-specific updates and rollbacks
- Provides clear version difference visualization

Version comparison rules:

1. Main version numbers are compared first (1.2.3 vs 1.2.4)
2. Build numbers are compared if main versions match
3. Special handling for complex version strings with build identifiers

## 🛠️ Error Handling

IntuneBrew includes robust error handling mechanisms:

1. **Upload Retry Logic**

   - Automatic retry for failed uploads (up to 3 attempts)
   - Exponential backoff between retries
   - New SAS token generation for expired URLs

2. **File Processing**

   - Temporary file cleanup
   - Handle locked files
   - Memory management for large files

3. **Network Issues**

   - Connection timeout handling
   - Bandwidth throttling
   - Resume interrupted uploads

4. **Authentication**
   - Token refresh handling
   - Certificate expiration checks
   - Fallback to interactive login

## 🤔 Troubleshooting

### Common Issues

1. **File Access Errors**

   - Ensure no other process is using the file
   - Try deleting temporary files manually
   - Restart the script

2. **Upload Failures**

   - Check your internet connection
   - Verify Azure AD permissions
   - Ensure file sizes don't exceed Intune limits

3. **Authentication Issues**
   - Verify your Azure AD credentials
   - Check tenant ID configuration
   - Ensure required permissions are granted

4. **PowerShell 7 Command Not Found**

   If you're getting "IntuneBrew is not recognized as a name of a cmdlet, function, script file, or executable program" in PowerShell 7:

   **Step 1: Check your PATH environment variable**
   ```powershell
   "Current PATH:"
   $env:PATH -split ';'
   ```

   **Step 2: Verify IntuneBrew installation location**
   ```powershell
   $intuneBrewInfo = Get-InstalledScript -Name IntuneBrew -ErrorAction SilentlyContinue

   if ($intuneBrewInfo) {
       "Installed Location for IntuneBrew:"
       $intuneBrewInfo | Select-Object Name, Version, InstalledLocation
   } else {
       Write-Warning "IntuneBrew is not installed. Run: Install-Script IntuneBrew -Force"
       return
   }
   ```

   **Step 3: Add IntuneBrew to your PATH if needed**
   ```powershell
   $scriptPath = $intuneBrewInfo.InstalledLocation
   if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $scriptPath })) {
       Write-Host "`n📌 Adding IntuneBrew script folder to PATH..." -ForegroundColor Yellow
       [Environment]::SetEnvironmentVariable("PATH", "$env:PATH;$scriptPath", [EnvironmentVariableTarget]::User)
       Write-Host "✅ Done. Restart PowerShell to use 'IntuneBrew' as a command." -ForegroundColor Green
   } else {
       Write-Host "✅ Script path is already in PATH." -ForegroundColor Green
   }
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape IntuneBrew
- Microsoft Graph API documentation and community
- The PowerShell community for their invaluable resources

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/ugurkocde/IntuneBrew/issues) page
2. Review the troubleshooting guide
3. Open a new issue if needed

---

Made with ❤️ by [Ugur Koc](https://github.com/ugurkocde)
