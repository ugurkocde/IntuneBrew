![IntuneBrew_Header](https://github.com/user-attachments/assets/c036ff17-ecad-4615-a7b5-6ffbd3d4ebf1)

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
      <img src="https://img.shields.io/badge/Apps_Available-161-2ea44f?style=flat" alt="TotalApps"/>
    </a>
  </p>
</div>

IntuneBrew is a PowerShell-based tool that simplifies the process of uploading and managing macOS applications in Microsoft Intune. It automates the entire workflow from downloading apps to uploading them to Intune, complete with proper metadata and logos.

#

- [](#)
  - [🚨 Public Preview Notice](#-public-preview-notice)
  - [🔄 Latest Updates](#-latest-updates)
  - [✨ Features](#-features)
  - [🎬 Demo (New one is recorded ASAP because a lot has changed since this demo)](#-demo-new-one-is-recorded-asap-because-a-lot-has-changed-since-this-demo)
  - [🚀 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
  - [📝 Usage](#-usage)
    - [Basic Usage](#basic-usage)
    - [📱 Supported Applications](#-supported-applications)
  - [🔧 Configuration](#-configuration)
    - [Azure App Registration](#azure-app-registration)
    - [Certificate-Based Authentication](#certificate-based-authentication)
    - [App JSON Structure](#app-json-structure)
  - [🔄 Version Management](#-version-management)
  - [🛠️ Error Handling](#️-error-handling)
  - [🤔 Troubleshooting](#-troubleshooting)
    - [Common Issues](#common-issues)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)
  - [🙏 Acknowledgments](#-acknowledgments)
  - [📞 Support](#-support)

## 🚨 Public Preview Notice

> [!IMPORTANT]
> 🚧 **Public Preview Notice**
>
> IntuneBrew is currently in Public Preview. While it's fully functional, you might encounter some rough edges. Your feedback and contributions are crucial in making this tool better!
>
> - 📝 [Submit Feedback](https://github.com/ugurkocde/IntuneBrew/issues/new?labels=feedback)
> - 🐛 [Report Bugs](https://github.com/ugurkocde/IntuneBrew/issues/new?labels=bug)
> - 💡 [Request Features](https://github.com/ugurkocde/IntuneBrew/issues/new?labels=enhancement)
>
> Thank you for being an early adopter! 🙏


## 🔄 Latest Updates

*Last checked: 2025-02-05 10:04 UTC*

> All applications are up to date! 🎉
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

## 🎬 Demo (New one is recorded ASAP because a lot has changed since this demo)

![IntuneBrew Demo](IntuneBrew_Demo.gif)

## 🚀 Getting Started

### Prerequisites

- PowerShell 7.0 or higher
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

### 📱 Supported Applications

| Application | Latest Version |
|-------------|----------------|
| <img src='Logos/1password.png' width='32' height='32'> 1Password | 8.10.60 |
| <img src='Logos/acorn.png' width='32' height='32'> Acorn | 8.0.1 |
| <img src='Logos/adobe_acrobat_pro_dc.png' width='32' height='32'> Adobe Acrobat Pro DC | 24.005.20400 |
| <img src='Logos/adobe_acrobat_reader.png' width='32' height='32'> Adobe Acrobat Reader | 24.005.20400 |
| <img src='Logos/adobe_creative_cloud.png' width='32' height='32'> Adobe Creative Cloud | 6.5.0.348 |
| <img src='Logos/alacritty.png' width='32' height='32'> Alacritty | 0.15.0 |
| <img src='Logos/alfred.png' width='32' height='32'> Alfred | 5.5.1,2273 |
| <img src='Logos/alttab.png' width='32' height='32'> AltTab | 7.19.1 |
| <img src='Logos/android_studio.png' width='32' height='32'> Android Studio | 2024.2.2.13 |
| <img src='Logos/anki.png' width='32' height='32'> Anki | 24.11 |
| <img src='Logos/anydesk.png' width='32' height='32'> AnyDesk | 8.1.4 |
| <img src='Logos/arc.png' width='32' height='32'> Arc | 1.79.1,58230 |
| <img src='Logos/asana.png' width='32' height='32'> Asana | 2.3.0 |
| <img src='Logos/audacity.png' width='32' height='32'> Audacity | 3.7.1 |
| <img src='Logos/aws_corretto_jdk.png' width='32' height='32'> AWS Corretto JDK | 21.0.6.7.1 |
| <img src='Logos/azul_zulu_java_standard_edition_development_kit.png' width='32' height='32'> Azul Zulu Java Standard Edition Development Kit | 23.0.2,23.32.11 |
| <img src='Logos/azure_data_studio.png' width='32' height='32'> Azure Data Studio | 1.51.0 |
| <img src='Logos/bartender.png' width='32' height='32'> Bartender | 5.2.7 |
| <img src='Logos/basecamp.png' width='32' height='32'> Basecamp | 3,2.4.1 |
| <img src='Logos/bbedit.png' width='32' height='32'> BBEdit | 15.1.3 |
| <img src='Logos/betterdisplay.png' width='32' height='32'> BetterDisplay | 3.3.4 |
| <img src='Logos/bitwarden.png' width='32' height='32'> Bitwarden | 2025.1.3 |
| <img src='Logos/blender.png' width='32' height='32'> Blender | 4.3.2 |
| <img src='Logos/brave.png' width='32' height='32'> Brave | 1.74.51.0 |
| <img src='Logos/bruno.png' width='32' height='32'> Bruno | 1.38.1 |
| <img src='Logos/caffeine.png' width='32' height='32'> Caffeine | 1.5 |
| <img src='Logos/calibre.png' width='32' height='32'> calibre | 7.24.0 |
| <img src='Logos/canva.png' width='32' height='32'> Canva | 1.103.0 |
| <img src='Logos/capcut.png' width='32' height='32'> CapCut | 3.3.0.1159 |
| <img src='Logos/chatgpt.png' width='32' height='32'> ChatGPT | 1.2025.031,1738605767 |
| <img src='Logos/citrix_workspace.png' width='32' height='32'> Citrix Workspace | 24.11.0.55 |
| <img src='Logos/claude.png' width='32' height='32'> Claude | 0.7.8,323bb7701662920a3dd34e453243cce6baff27c0 |
| <img src='Logos/clipy.png' width='32' height='32'> Clipy | 1.2.1 |
| <img src='Logos/company_portal.png' width='32' height='32'> Company Portal | 5.2412.0 |
| <img src='Logos/cursor.png' width='32' height='32'> Cursor | 0.45.9,250202tgstl42dt |
| <img src='Logos/cyberduck.png' width='32' height='32'> Cyberduck | 9.1.2,42722 |
| <img src='Logos/datagrip.png' width='32' height='32'> DataGrip | 2024.3.4,243.23654.183 |
| <img src='Logos/db_browser_for_sqlite.png' width='32' height='32'> DB Browser for SQLite | 3.13.1 |
| <img src='Logos/deepl.png' width='32' height='32'> DeepL | 25.1.11615133 |
| <img src='Logos/discord.png' width='32' height='32'> Discord | 0.0.335 |
| <img src='Logos/docker_desktop.png' width='32' height='32'> Docker Desktop | 4.38.0,181591 |
| <img src='Logos/drawio_desktop.png' width='32' height='32'> draw.io Desktop | 26.0.9 |
| <img src='Logos/dropbox.png' width='32' height='32'> Dropbox | 217.4.4417 |
| <img src='Logos/duckduckgo.png' width='32' height='32'> DuckDuckGo | 1.124.1,355 |
| <img src='Logos/eclipse_temurin_java_development_kit.png' width='32' height='32'> Eclipse Temurin Java Development Kit | 23.0.2,7 |
| <img src='Logos/elgato_camera_hub.png' width='32' height='32'> Elgato Camera Hub | 1.11.0.4022 |
| <img src='Logos/elgato_stream_deck.png' width='32' height='32'> Elgato Stream Deck | 6.8.1.21263 |
| <img src='Logos/elgato_wave_link.png' width='32' height='32'> Elgato Wave Link | 1.10.1.2293 |
| <img src='Logos/etcher.png' width='32' height='32'> Etcher | 1.19.25 |
| <img src='Logos/evernote.png' width='32' height='32'> Evernote | 10.105.4,20240910164757,a2e60a8d876a07eded5d212fa56ba45214114ad0 |
| <img src='Logos/flux.png' width='32' height='32'> f.lux | 42.2 |
| <img src='Logos/fantastical.png' width='32' height='32'> Fantastical | 4.0.4 |
| <img src='Logos/figma.png' width='32' height='32'> Figma | 124.7.4 |
| <img src='Logos/flameshot.png' width='32' height='32'> Flameshot | 12.1.0 |
| <img src='Logos/foxit_pdf_editor.png' width='32' height='32'> Foxit PDF Editor | 13.1.6 |
| <img src='Logos/freecad.png' width='32' height='32'> FreeCAD | 1.0.0 |
| <img src='Logos/freemacsoft_appcleaner.png' width='32' height='32'> FreeMacSoft AppCleaner | 3.6.8 |
| <img src='Logos/geany.png' width='32' height='32'> Geany | 2.0 |
| <img src='Logos/ghostty.png' width='32' height='32'> Ghostty | 1.1.0 |
| <img src='Logos/gimp.png' width='32' height='32'> GIMP | 2.10.38,1 |
| <img src='Logos/git_credential_manager.png' width='32' height='32'> Git Credential Manager | 2.6.1 |
| <img src='Logos/github_desktop.png' width='32' height='32'> GitHub Desktop | 3.4.16-ba997388 |
| <img src='Logos/gitkraken.png' width='32' height='32'> GitKraken | 10.6.3 |
| <img src='Logos/godot_engine.png' width='32' height='32'> Godot Engine | 4.3 |
| <img src='Logos/goland.png' width='32' height='32'> Goland | 2024.3.2.1,243.23654.166 |
| <img src='Logos/google_chrome.png' width='32' height='32'> Google Chrome | 133.0.6943.54 |
| <img src='Logos/google_drive.png' width='32' height='32'> Google Drive | 103.0.3 |
| <img src='Logos/grammarly_desktop.png' width='32' height='32'> Grammarly Desktop | 1.105.0.0 |
| <img src='Logos/hp_easy_admin.png' width='32' height='32'> HP Easy Admin | 2.15.0,240916 |
| <img src='Logos/ice.png' width='32' height='32'> Ice | 0.11.12 |
| <img src='Logos/iina.png' width='32' height='32'> IINA | 1.3.5,141 |
| <img src='Logos/imazing.png' width='32' height='32'> iMazing | 3.0.6,21166 |
| <img src='Logos/imazing_profile_editor.png' width='32' height='32'> iMazing Profile Editor | 1.9.2,304501 |
| <img src='Logos/insomnia.png' width='32' height='32'> Insomnia | 10.3.0 |
| <img src='Logos/intellij_idea_community_edition.png' width='32' height='32'> IntelliJ IDEA Community Edition | 2024.3.2.2,243.23654.189 |
| <img src='Logos/iterm2.png' width='32' height='32'> iTerm2 | 3.5.11 |
| ❌ Jabra Direct | 6.21.01701 |
| <img src='Logos/jetbrains_pycharm_community_edition.png' width='32' height='32'> Jetbrains PyCharm Community Edition | 2024.3.2,243.23654.177 |
| <img src='Logos/karabiner_elements.png' width='32' height='32'> Karabiner Elements | 15.3.0 |
| <img src='Logos/keepassxc.png' width='32' height='32'> KeePassXC | 2.7.9 |
| <img src='Logos/keeper_password_manager.png' width='32' height='32'> Keeper Password Manager | 17.0.0 |
| <img src='Logos/keka.png' width='32' height='32'> Keka | 1.4.7 |
| <img src='Logos/kitty.png' width='32' height='32'> kitty | 0.39.1 |
| <img src='Logos/krisp.png' width='32' height='32'> Krisp | 2.54.6 |
| <img src='Logos/libreoffice.png' width='32' height='32'> LibreOffice | 24.8.4 |
| <img src='Logos/lm_studio.png' width='32' height='32'> LM Studio | 0.3.9,5 |
| <img src='Logos/logitech_options.png' width='32' height='32'> Logitech Options+ | 1.85.655119 |
| <img src='Logos/maccy.png' width='32' height='32'> Maccy | 2.3.0 |
| <img src='Logos/macfuse.png' width='32' height='32'> macFUSE | 4.8.3 |
| <img src='Logos/mactex.png' width='32' height='32'> MacTeX | 2024.0312 |
| <img src='Logos/menubar_stats.png' width='32' height='32'> MenuBar Stats | 3.9 |
| <img src='Logos/microsoft_auto_update.png' width='32' height='32'> Microsoft Auto Update | 4.77.24121924 |
| <img src='Logos/microsoft_azure_storage_explorer.png' width='32' height='32'> Microsoft Azure Storage Explorer | 1.37.0 |
| <img src='Logos/microsoft_edge.png' width='32' height='32'> Microsoft Edge | 132.0.2957.140,ee31fad8-29f2-4106-8a9b-9d59d949dbe3 |
| <img src='Logos/microsoft_office.png' width='32' height='32'> Microsoft Office | 16.93.25011212 |
| <img src='Logos/microsoft_teams.png' width='32' height='32'> Microsoft Teams | 25007.203.3361.6689 |
| <img src='Logos/microsoft_visual_studio_code.png' width='32' height='32'> Microsoft Visual Studio Code | 1.96.4 |
| <img src='Logos/miro.png' width='32' height='32'> Miro | 0.10.80 |
| <img src='Logos/mitmproxy.png' width='32' height='32'> mitmproxy | 11.1.0 |
| <img src='Logos/mongodb_compass.png' width='32' height='32'> MongoDB Compass | 1.45.2 |
| <img src='Logos/mountain_duck.png' width='32' height='32'> Mountain Duck | 4.17.2,22563 |
| <img src='Logos/mounty_for_ntfs.png' width='32' height='32'> Mounty for NTFS | 2.4 |
| <img src='Logos/mozilla_firefox.png' width='32' height='32'> Mozilla Firefox | 135.0 |
| <img src='Logos/netbeans_ide.png' width='32' height='32'> NetBeans IDE | 24 |
| <img src='Logos/notion.png' width='32' height='32'> Notion | 4.4.0 |
| <img src='Logos/notion_calendar.png' width='32' height='32'> Notion Calendar | 1.127.0,250121ji52u08fs |
| <img src='Logos/obs.png' width='32' height='32'> OBS | 31.0.1 |
| <img src='Logos/obsidian.png' width='32' height='32'> Obsidian | 1.8.4 |
| <img src='Logos/ollama.png' width='32' height='32'> Ollama | 0.5.7 |
| <img src='Logos/onedrive.png' width='32' height='32'> OneDrive | 24.244.1204.0003 |
| <img src='Logos/oracle_virtualbox.png' width='32' height='32'> Oracle VirtualBox | 7.1.6,167084 |
| <img src='Logos/orbstack.png' width='32' height='32'> OrbStack | 1.9.5_18849 |
| <img src='Logos/parallels_desktop.png' width='32' height='32'> Parallels Desktop | 20.2.0-55872 |
| <img src='Logos/pdf_expert.png' width='32' height='32'> PDF Expert | 3.10.10,1086 |
| <img src='Logos/pgadmin4.png' width='32' height='32'> pgAdmin4 | 8.14 |
| <img src='Logos/podman_desktop.png' width='32' height='32'> Podman Desktop | 1.16.1 |
| <img src='Logos/postman.png' width='32' height='32'> Postman | 11.31.0 |
| <img src='Logos/powershell.png' width='32' height='32'> PowerShell | 7.5.0 |
| <img src='Logos/privileges.png' width='32' height='32'> Privileges | 2.1.0 |
| <img src='Logos/rancher_desktop.png' width='32' height='32'> Rancher Desktop | 1.17.1 |
| <img src='Logos/raycast.png' width='32' height='32'> Raycast | 1.90.0 |
| <img src='Logos/real_vnc_viewer.png' width='32' height='32'> Real VNC Viewer | 7.13.1 |
| <img src='Logos/rectangle.png' width='32' height='32'> Rectangle | 0.86 |
| <img src='Logos/remote_help.png' width='32' height='32'> Remote Help | 1.0.2404171 |
| <img src='Logos/rstudio.png' width='32' height='32'> RStudio | 2024.12.0,467 |
| <img src='Logos/santa.png' width='32' height='32'> Santa | 2024.9 |
| <img src='Logos/shottr.png' width='32' height='32'> Shottr | 1.8.1 |
| <img src='Logos/signal.png' width='32' height='32'> Signal | 7.40.1 |
| <img src='Logos/slack.png' width='32' height='32'> Slack | 4.42.117 |
| <img src='Logos/snagit.png' width='32' height='32'> Snagit | 2024.4.0 |
| <img src='Logos/splashtop_business.png' width='32' height='32'> Splashtop Business | 3.7.2.4 |
| <img src='Logos/spotify.png' width='32' height='32'> Spotify | 1.2.56.502 |
| <img src='Logos/stats.png' width='32' height='32'> Stats | 2.11.29 |
| <img src='Logos/sublime_text.png' width='32' height='32'> Sublime Text | 4192 |
| <img src='Logos/suspicious_package.png' width='32' height='32'> Suspicious Package | 4.5,1213 |
| <img src='Logos/sync.png' width='32' height='32'> Sync | 2.2.48 |
| <img src='Logos/synology_drive.png' width='32' height='32'> Synology Drive | 3.5.1,16102 |
| <img src='Logos/tableau_desktop.png' width='32' height='32'> Tableau Desktop | 2024.3.3 |
| <img src='Logos/tailscale.png' width='32' height='32'> Tailscale | 1.80.0 |
| <img src='Logos/teamviewer_quicksupport.png' width='32' height='32'> TeamViewer QuickSupport | 15 |
| <img src='Logos/telegram_for_macos.png' width='32' height='32'> Telegram for macOS | 11.7,270736 |
| <img src='Logos/termius.png' width='32' height='32'> Termius | 9.13.1 |
| <img src='Logos/todoist.png' width='32' height='32'> Todoist | 9.10.0 |
| <img src='Logos/transmission.png' width='32' height='32'> Transmission | 4.0.6 |
| <img src='Logos/transmit.png' width='32' height='32'> Transmit | 5.10.6 |
| <img src='Logos/utm.png' width='32' height='32'> UTM | 4.6.4 |
| <img src='Logos/vivaldi.png' width='32' height='32'> Vivaldi | 7.1.3570.42 |
| <img src='Logos/vlc_media_player.png' width='32' height='32'> VLC media player | 3.0.21 |
| <img src='Logos/vscodium.png' width='32' height='32'> VSCodium | 1.96.4.25026 |
| <img src='Logos/webex_teams.png' width='32' height='32'> Webex Teams | 45.1.0.31549 |
| <img src='Logos/webstorm.png' width='32' height='32'> WebStorm | 2024.3.2.1,243.23654.157 |
| <img src='Logos/whatsapp.png' width='32' height='32'> WhatsApp | 2.24.25.94 |
| <img src='Logos/windows_app.png' width='32' height='32'> Windows App | 11.0.9 |
| <img src='Logos/windsurf.png' width='32' height='32'> Windsurf | 1.2.5,b195fa8f6708b2d32692f64ba2809ad303f79173 |
| <img src='Logos/winehqstable.png' width='32' height='32'> WineHQ-stable | 10.0 |
| <img src='Logos/wireshark.png' width='32' height='32'> Wireshark | 4.4.3 |
| <img src='Logos/xmind.png' width='32' height='32'> XMind | 25.01.01061-202501070704 |
| <img src='Logos/yubikey_manager.png' width='32' height='32'> Yubikey Manager | 1.2.5 |
| <img src='Logos/zed.png' width='32' height='32'> Zed | 0.171.6 |
| <img src='Logos/zen_browser.png' width='32' height='32'> Zen Browser | 1.7.4b |
| <img src='Logos/zoom.png' width='32' height='32'> Zoom | 6.3.6.47101 |

> [!NOTE]
> Missing an app? Feel free to [request additional app support](https://github.com/ugurkocde/IntuneBrew/issues/new?labels=app-request) by creating an issue!

## 🔧 Configuration

### Azure App Registration

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
