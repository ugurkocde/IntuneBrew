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
      <img src="https://img.shields.io/badge/Apps_Available-1236-2ea44f?style=flat" alt="TotalApps"/>
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
- [Automated Workflows](#automated-workflows)
- [📜 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [📞 Support](#-support)

















































































































































































































































































## 🔄 Latest Updates

*Last checked: 2026-02-08 00:50 UTC*

| Application | Previous Version | New Version |
|-------------|-----------------|-------------|
| Caffeine | 1.6.3 | 1.1.4 |
| Multi | 0.538.2 | 3.0.2 |
| BoltAI 2 | 2.6.3 | 2.7.0 |
| FontBase | 2.25.6 | 2.25.10 |
| Caffeine | 1.6.3 | 1.1.4 |
| Multi | 0.538.2 | 3.0.2 |
| Zotero | 8.0.2 | 8.0.3 |
| Claude Code | 2.1.34 | 2.1.37 |
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

### Supported Applications

| Application | Latest Version |
|-------------|----------------|
| <img src='Logos/010_editor.png' width='32' height='32'> 010 Editor | 16.0.3 |
| <img src='Logos/1password.png' width='32' height='32'> 1Password | 8.12.0 |
| <img src='Logos/1password_cli.png' width='32' height='32'> 1Password CLI | 2.32.0 |
| <img src='Logos/4k_slideshow_maker.png' width='32' height='32'> 4K Slideshow Maker | 2.0.1 |
| <img src='Logos/4k_stogram.png' width='32' height='32'> 4K Stogram | 4.9.0 |
| <img src='Logos/4k_video_downloader.png' width='32' height='32'> 4K Video Downloader | 4.33.5 |
| <img src='Logos/4k_video_to_mp3.png' width='32' height='32'> 4K Video to MP3 | 3.0.1 |
| <img src='Logos/4k_youtube_to_mp3.png' width='32' height='32'> 4K YouTube to MP3 | 26.0.1 |
| <img src='Logos/8x8_work.png' width='32' height='32'> 8x8_work | 8.30.2-10 |
| <img src='Logos/a_better_finder_rename.png' width='32' height='32'> A Better Finder Rename | 12.23 |
| <img src='Logos/abbyy_finereader_pdf.png' width='32' height='32'> ABBYY FineReader PDF | 1402.19 |
| <img src='Logos/ableton_live_lite.png' width='32' height='32'> Ableton Live Lite | 12.3.5 |
| <img src='Logos/ableton_live_suite.png' width='32' height='32'> Ableton Live Suite | 12.3.5 |
| <img src='Logos/abstract.png' width='32' height='32'> Abstract | 98.6.3 |
| <img src='Logos/acorn.png' width='32' height='32'> Acorn | 8.4.1 |
| <img src='Logos/acronis_true_image.png' width='32' height='32'> Acronis True Image | 29.2 |
| <img src='Logos/activedock.png' width='32' height='32'> ActiveDock | 2.850 |
| <img src='Logos/activitywatch.png' width='32' height='32'> ActivityWatch | 0.13.2 |
| <img src='Logos/actual.png' width='32' height='32'> Actual | 26.2.0 |
| <img src='Logos/adguard.png' width='32' height='32'> AdGuard | 2.18.0.2089 |
| <img src='Logos/adium.png' width='32' height='32'> Adium | 1.5.10.4 |
| <img src='Logos/adlock.png' width='32' height='32'> AdLock | 2.1.7.3 |
| <img src='Logos/adobe_acrobat_pro_dc.png' width='32' height='32'> Adobe Acrobat Pro DC | 25.001.21145 |
| <img src='Logos/adobe_acrobat_reader.png' width='32' height='32'> Adobe Acrobat Reader | 25.001.21111 |
| <img src='Logos/adobe_creative_cloud.png' width='32' height='32'> Adobe Creative Cloud | 6.8.1.865 |
| <img src='Logos/adobe_digital_editions.png' width='32' height='32'> Adobe Digital Editions | 4.5.12 |
| <img src='Logos/adobe_dng_converter.png' width='32' height='32'> Adobe DNG Converter | 18.1.1 |
| <img src='Logos/advanced_renamer.png' width='32' height='32'> Advanced Renamer | 4.20 |
| <img src='Logos/affinity_designer_2.png' width='32' height='32'> Affinity Designer 2 | 2.6.5 |
| <img src='Logos/affinity_photo_2.png' width='32' height='32'> Affinity Photo 2 | 2.6.5 |
| <img src='Logos/affinity_publisher_2.png' width='32' height='32'> Affinity Publisher 2 | 2.6.5 |
| <img src='Logos/airbuddy.png' width='32' height='32'> AirBuddy | 2.7.4 |
| <img src='Logos/aircall.png' width='32' height='32'> Aircall | 3.1.66 |
| <img src='Logos/airdroid.png' width='32' height='32'> AirDroid | 3.7.3.1 |
| <img src='Logos/airfoil.png' width='32' height='32'> Airfoil | 5.12.6 |
| <img src='Logos/airparrot.png' width='32' height='32'> AirParrot | 3.1.7 |
| <img src='Logos/airserver.png' width='32' height='32'> AirServer | 7.2.7 |
| <img src='Logos/airtable.png' width='32' height='32'> Airtable | 1.6.6 |
| <img src='Logos/airtame.png' width='32' height='32'> Airtame | 4.15.0 |
| <img src='Logos/airy.png' width='32' height='32'> Airy | 3.29.2 |
| <img src='Logos/akiflow.png' width='32' height='32'> Akiflow | 2.66.3 |
| <img src='Logos/alacritty.png' width='32' height='32'> Alacritty | 0.16.1 |
| <img src='Logos/alcove.png' width='32' height='32'> Alcove | 1.5.1 |
| <img src='Logos/aldente.png' width='32' height='32'> AlDente | 1.36.3 |
| <img src='Logos/alfred.png' width='32' height='32'> Alfred | 5.7.2 |
| <img src='Logos/alloy.png' width='32' height='32'> Alloy | 6.2.0 |
| <img src='Logos/altair_graphql_client.png' width='32' height='32'> Altair GraphQL Client | 8.5.0 |
| <img src='Logos/altserver.png' width='32' height='32'> AltServer | 1.7.2 |
| <img src='Logos/alttab.png' width='32' height='32'> AltTab | 8.3.4 |
| <img src='Logos/amadeus_pro.png' width='32' height='32'> Amadeus Pro | 2.8.14 |
| <img src='Logos/amadine.png' width='32' height='32'> Amadine | 1.7.2 |
| <img src='Logos/amazon_chime.png' width='32' height='32'> Amazon Chime | 5.23.22475 |
| <img src='Logos/amazon_music.png' width='32' height='32'> Amazon Music | 9.5.2.2478 |
| <img src='Logos/amazon_q.png' width='32' height='32'> Amazon Q | 1.19.6 |
| <img src='Logos/amazon_workspaces.png' width='32' height='32'> Amazon Workspaces | 5.31.0.6030 |
| <img src='Logos/amethyst.png' width='32' height='32'> Amethyst | 0.24.1 |
| <img src='Logos/amie.png' width='32' height='32'> Amie | 251228.0.0 |
| <img src='Logos/android_file_transfer.png' width='32' height='32'> Android File Transfer | 5071136 |
| <img src='Logos/android_ndk.png' width='32' height='32'> Android NDK | 29 |
| <img src='Logos/android_sdk_commandline_tools.png' width='32' height='32'> Android SDK Command-line Tools | 14742923 |
| <img src='Logos/android_sdk_platformtools.png' width='32' height='32'> Android SDK Platform-Tools | 36.0.2 |
| <img src='Logos/android_studio.png' width='32' height='32'> Android Studio | 2025.2.3.9 |
| <img src='Logos/angry_ip_scanner.png' width='32' height='32'> Angry IP Scanner | 3.9.3 |
| <img src='Logos/anki.png' width='32' height='32'> Anki | 25.09 |
| <img src='Logos/another_redis_desktop_manager.png' width='32' height='32'> Another Redis Desktop Manager | 1.7.1 |
| <img src='Logos/antinote.png' width='32' height='32'> Antinote | 1.1.7 |
| <img src='Logos/anydo.png' width='32' height='32'> Any.do | 5.0.68 |
| <img src='Logos/anydesk.png' width='32' height='32'> AnyDesk | 9.6.1 |
| <img src='Logos/anytype.png' width='32' height='32'> Anytype | 0.53.1 |
| <img src='Logos/apidog.png' width='32' height='32'> Apidog | 2.8.5 |
| <img src='Logos/apifox.png' width='32' height='32'> Apifox | 2.8.5 |
| <img src='Logos/apparency.png' width='32' height='32'> Apparency | 3.1 |
| <img src='Logos/appflowy.png' width='32' height='32'> AppFlowy | 0.11.1 |
| <img src='Logos/appgate_sdp_client_for_macos.png' width='32' height='32'> AppGate SDP Client for macOS | 6.6.0 |
| <img src='Logos/appgrid.png' width='32' height='32'> AppGrid | 1.0.4 |
| <img src='Logos/appium_inspector_gui.png' width='32' height='32'> Appium Inspector GUI | 2026.1.3 |
| <img src='Logos/applite.png' width='32' height='32'> Applite | 1.3.1 |
| <img src='Logos/apptivate.png' width='32' height='32'> Apptivate | 2.2.1 |
| <img src='Logos/aptible_toolbelt.png' width='32' height='32'> Aptible Toolbelt | 0.26.1 |
| <img src='Logos/arc.png' width='32' height='32'> Arc | 1.132.1 |
| <img src='Logos/archaeology.png' width='32' height='32'> Archaeology | 1.5 |
| <img src='Logos/archi.png' width='32' height='32'> Archi | 5.7.0 |
| <img src='Logos/arduino_ide.png' width='32' height='32'> Arduino IDE | 2.3.7 |
| <img src='Logos/arq.png' width='32' height='32'> Arq | 7.37 |
| <img src='Logos/asana.png' width='32' height='32'> Asana | 2.5.1 |
| <img src='Logos/asset_catalog_tinkerer.png' width='32' height='32'> Asset Catalog Tinkerer | 2.9 |
| <img src='Logos/atext.png' width='32' height='32'> aText | 3.21 |
| <img src='Logos/atlassian_sourcetree.png' width='32' height='32'> Atlassian SourceTree | 4.2.16 |
| <img src='Logos/audacity.png' width='32' height='32'> Audacity | 3.7.7 |
| <img src='Logos/audio_hijack.png' width='32' height='32'> Audio Hijack | 4.5.6 |
| <img src='Logos/audirvana.png' width='32' height='32'> Audirvana | 3.5.50 |
| <img src='Logos/aurora_hdr.png' width='32' height='32'> Aurora HDR | 1.0.2 |
| <img src='Logos/autodesk_fusion_360.png' width='32' height='32'> Autodesk Fusion 360 | latest |
| <img src='Logos/avast_secure_browser.png' width='32' height='32'> Avast Secure Browser | 139.0.6697.68 |
| <img src='Logos/avidemux.png' width='32' height='32'> Avidemux | 2.8.1 |
| <img src='Logos/aws_client_vpn.png' width='32' height='32'> AWS Client VPN | 5.3.3 |
| <img src='Logos/aws_corretto_jdk.png' width='32' height='32'> AWS Corretto JDK | 21.0.10.7.1 |
| <img src='Logos/axure_rp.png' width='32' height='32'> Axure RP | 11.0.0.4134 |
| <img src='Logos/azul_zulu_java_standard_edition_development_kit.png' width='32' height='32'> Azul Zulu Java Standard Edition Development Kit | 25.0.2 |
| <img src='Logos/azure_data_studio.png' width='32' height='32'> Azure Data Studio | 1.52.0 |
| <img src='Logos/backblaze.png' width='32' height='32'> Backblaze | 9.2.2.898 |
| <img src='Logos/background_music.png' width='32' height='32'> Background Music | 0.4.3 |
| <img src='Logos/backlog.png' width='32' height='32'> Backlog | 1.8.0 |
| <img src='Logos/backuploupe.png' width='32' height='32'> BackupLoupe | 3.14.7 |
| <img src='Logos/badgeify.png' width='32' height='32'> Badgeify | 1.12.3 |
| <img src='Logos/balsamiq_wireframes.png' width='32' height='32'> Balsamiq Wireframes | 4.8.6 |
| <img src='Logos/bambu_studio.png' width='32' height='32'> Bambu Studio | 02.05.00.66 |
| <img src='Logos/bankid_security_application_sweden.png' width='32' height='32'> BankID Security Application (Sweden) | 7.16.0 |
| <img src='Logos/bartender.png' width='32' height='32'> Bartender | 6.3.1 |
| <img src='Logos/basecamp.png' width='32' height='32'> Basecamp | 3 |
| <img src='Logos/basictex.png' width='32' height='32'> BasicTeX | 2025.0308 |
| <img src='Logos/batfi.png' width='32' height='32'> BatFi | 3.0.1 |
| <img src='Logos/battery_buddy.png' width='32' height='32'> Battery Buddy | 1.0.3 |
| <img src='Logos/bbedit.png' width='32' height='32'> BBEdit | 15.5.4 |
| <img src='Logos/bdash.png' width='32' height='32'> Bdash | 1.31.0 |
| <img src='Logos/beardedspice.png' width='32' height='32'> BeardedSpice | 2.2.3 |
| <img src='Logos/beaver_notes.png' width='32' height='32'> Beaver Notes | 4.2.0 |
| <img src='Logos/beekeeper_studio.png' width='32' height='32'> Beekeeper Studio | 5.5.6 |
| <img src='Logos/beeper.png' width='32' height='32'> Beeper | 4.2.518 |
| <img src='Logos/berkeley_open_infrastructure_for_network_computing.png' width='32' height='32'> Berkeley Open Infrastructure for Network Computing | 8.2.5 |
| <img src='Logos/betaflightconfigurator.png' width='32' height='32'> Betaflight-Configurator | 10.10.0 |
| <img src='Logos/betterdisplay.png' width='32' height='32'> BetterDisplay | 4.1.1 |
| <img src='Logos/bettermouse.png' width='32' height='32'> BetterMouse | 1.6 |
| <img src='Logos/bettertouchtool.png' width='32' height='32'> BetterTouchTool | 6.135 |
| <img src='Logos/betterzip.png' width='32' height='32'> BetterZip | 5.4 |
| <img src='Logos/beyond_compare.png' width='32' height='32'> Beyond Compare | 5.1.7.31736 |
| <img src='Logos/bezel.png' width='32' height='32'> Bezel | 3.5.1 |
| <img src='Logos/bibdesk.png' width='32' height='32'> BibDesk | 1.9.10 |
| <img src='Logos/bilibili.png' width='32' height='32'> Bilibili | 1.17.5 |
| <img src='Logos/binance.png' width='32' height='32'> Binance | 2.2.1 |
| <img src='Logos/binary_ninja.png' width='32' height='32'> Binary Ninja | 5.2.8722 |
| <img src='Logos/birdfont.png' width='32' height='32'> BirdFont | 6.15.1 |
| <img src='Logos/biscuit.png' width='32' height='32'> Biscuit | 1.2.33 |
| <img src='Logos/bitbar.png' width='32' height='32'> BitBar | 1.10.1 |
| <img src='Logos/bitbox.png' width='32' height='32'> BitBox | 4.50.1 |
| <img src='Logos/bitfocus_companion.png' width='32' height='32'> Bitfocus Companion | 4.2.3 |
| <img src='Logos/bitrix24.png' width='32' height='32'> Bitrix24 | 20.0.28.90 |
| <img src='Logos/bitwarden.png' width='32' height='32'> Bitwarden | 2025.12.1 |
| <img src='Logos/bitwig_studio.png' width='32' height='32'> Bitwig Studio | 5.3.13 |
| <img src='Logos/blackhole_16ch.png' width='32' height='32'> BlackHole 16ch | 0.6.1 |
| <img src='Logos/blackhole_2ch.png' width='32' height='32'> BlackHole 2ch | 0.6.1 |
| <img src='Logos/blackhole_64ch.png' width='32' height='32'> BlackHole 64ch | 0.6.1 |
| <img src='Logos/blender.png' width='32' height='32'> Blender | 5.0.1 |
| <img src='Logos/bleunlock.png' width='32' height='32'> BLEUnlock | 1.12.2 |
| <img src='Logos/blip.png' width='32' height='32'> blip | 1.1.15 |
| <img src='Logos/blizzard_battlenet.png' width='32' height='32'> Blizzard Battle.net | 1.19.0.3190 |
| <img src='Logos/blockblock.png' width='32' height='32'> BlockBlock | 2.2.5 |
| <img src='Logos/bluebubbles.png' width='32' height='32'> BlueBubbles | 1.9.9 |
| <img src='Logos/bluefish.png' width='32' height='32'> Bluefish | 2.4.0 |
| <img src='Logos/bluej.png' width='32' height='32'> BlueJ | 5.5.0 |
| <img src='Logos/bluewallet.png' width='32' height='32'> BlueWallet | 7.2.0 |
| <img src='Logos/blurscreen.png' width='32' height='32'> BlurScreen | 1.0 |
| <img src='Logos/boltai.png' width='32' height='32'> BoltAI | 1.36.5 |
| <img src='Logos/boltai_2.png' width='32' height='32'> BoltAI 2 | 2.6.3 |
| <img src='Logos/bome_network.png' width='32' height='32'> Bome Network | 1.6.0 |
| <img src='Logos/boom_3d.png' width='32' height='32'> Boom 3D | 2.2 |
| <img src='Logos/boop.png' width='32' height='32'> Boop | 1.4.0 |
| <img src='Logos/boostnotenext.png' width='32' height='32'> Boostnote.Next | 0.23.1 |
| <img src='Logos/box_drive.png' width='32' height='32'> Box Drive | 2.49.255 |
| <img src='Logos/box_tools.png' width='32' height='32'> Box Tools | 4.31 |
| <img src='Logos/boxcryptor.png' width='32' height='32'> Boxcryptor | 3.13.680 |
| <img src='Logos/brackets.png' width='32' height='32'> Brackets | 2.2.0 |
| <img src='Logos/brave.png' width='32' height='32'> Brave | 1.86.146.0 |
| <img src='Logos/breaktimer.png' width='32' height='32'> BreakTimer | 2.0.3 |
| <img src='Logos/bria.png' width='32' height='32'> Bria | 6.8.5 |
| <img src='Logos/browserstack_local_testing.png' width='32' height='32'> BrowserStack Local Testing | 3.7.1 |
| <img src='Logos/bruno.png' width='32' height='32'> Bruno | 3.0.2 |
| <img src='Logos/bunch.png' width='32' height='32'> Bunch | 1.4.17 |
| <img src='Logos/busycal.png' width='32' height='32'> BusyCal | 2026.1.1 |
| <img src='Logos/busycontacts.png' width='32' height='32'> BusyContacts | 2026.1.1 |
| <img src='Logos/butler.png' width='32' height='32'> Butler | 4.4.8 |
| <img src='Logos/buttercup.png' width='32' height='32'> Buttercup | 2.28.1 |
| <img src='Logos/buzz.png' width='32' height='32'> Buzz | 1.2.0 |
| <img src='Logos/cacher.png' width='32' height='32'> Cacher | 2.47.9 |
| <img src='Logos/caffeine.png' width='32' height='32'> Caffeine | 1.1.4 |
| <img src='Logos/calhash.png' width='32' height='32'> CalHash | 1.5.2 |
| <img src='Logos/calibre.png' width='32' height='32'> calibre | 9.1.0 |
| <img src='Logos/calibrite_profiler.png' width='32' height='32'> calibrite PROFILER | 3.0.4 |
| <img src='Logos/calmly_writer.png' width='32' height='32'> Calmly Writer | 2.0.61 |
| <img src='Logos/camtasia.png' width='32' height='32'> Camtasia | 26.0.5 |
| <img src='Logos/camunda_modeler.png' width='32' height='32'> Camunda Modeler | 5.43.1 |
| <img src='Logos/canva.png' width='32' height='32'> Canva | 1.120.0 |
| <img src='Logos/capacities.png' width='32' height='32'> Capacities | 1.58.27 |
| <img src='Logos/capcut.png' width='32' height='32'> CapCut | 3.3.0.1159 |
| <img src='Logos/captain.png' width='32' height='32'> Captain | 10.5.0 |
| <img src='Logos/captin.png' width='32' height='32'> Captin | 1.3.1 |
| <img src='Logos/caption.png' width='32' height='32'> Caption | 2.0.1 |
| <img src='Logos/capto.png' width='32' height='32'> Capto | 2.1.4 |
| <img src='Logos/carbon_copy_cloner.png' width='32' height='32'> Carbon Copy Cloner | 7.1.4 |
| <img src='Logos/cardhop.png' width='32' height='32'> Cardhop | 2.4.3 |
| <img src='Logos/castr.png' width='32' height='32'> castr | 3.1.0 |
| <img src='Logos/catch.png' width='32' height='32'> Catch | 2.3 |
| <img src='Logos/cellprofiler.png' width='32' height='32'> CellProfiler | 4.2.8 |
| <img src='Logos/cerebro.png' width='32' height='32'> Cerebro | 0.11.0 |
| <img src='Logos/chalk.png' width='32' height='32'> Chalk | 1.7.5 |
| <img src='Logos/charles.png' width='32' height='32'> Charles | 5.0.3 |
| <img src='Logos/charmstone.png' width='32' height='32'> Charmstone | 1.43 |
| <img src='Logos/chatgpt.png' width='32' height='32'> ChatGPT | 1.2026.014 |
| <img src='Logos/chatgpt_atlas.png' width='32' height='32'> ChatGPT Atlas | 1.2026.21.3 |
| <img src='Logos/chatwise.png' width='32' height='32'> ChatWise | 0.9.79 |
| <img src='Logos/chatwork.png' width='32' height='32'> ChatWork | 2.20.0 |
| <img src='Logos/cheatsheet.png' width='32' height='32'> CheatSheet | 1.6.4 |
| <img src='Logos/cheetah3d.png' width='32' height='32'> Cheetah3D | 8.1.3 |
| <img src='Logos/chime.png' width='32' height='32'> Chime | 2.2.5 |
| <img src='Logos/chipmunk_log_analyzer__viewer.png' width='32' height='32'> Chipmunk Log Analyzer & Viewer | 3.19.4 |
| <img src='Logos/chirp.png' width='32' height='32'> CHIRP | 20250801 |
| <img src='Logos/choosy.png' width='32' height='32'> Choosy | 2.5.2 |
| <img src='Logos/chrome_remote_desktop.png' width='32' height='32'> Chrome Remote Desktop | 144.0.7559.13 |
| <img src='Logos/chromium.png' width='32' height='32'> Chromium | latest |
| <img src='Logos/chronosync.png' width='32' height='32'> ChronoSync | 12.0.0 |
| <img src='Logos/cisco_jabber.png' width='32' height='32'> Cisco Jabber | 20260122074039 |
| <img src='Logos/cisco_proximity.png' width='32' height='32'> Cisco Proximity | 4.0.0 |
| <img src='Logos/citrix_workspace.png' width='32' height='32'> Citrix Workspace | 25.11.1.42 |
| <img src='Logos/clamxav.png' width='32' height='32'> ClamXAV | 3.9.2 |
| <img src='Logos/claude.png' width='32' height='32'> Claude | 1.1.1520 |
| ❌ Claude Code | 2.1.29 |
| <img src='Logos/cleanclip.png' width='32' height='32'> CleanClip | 2.4.6 |
| <img src='Logos/cleanmymac.png' width='32' height='32'> CleanMyMac | 5.3.1 |
| <img src='Logos/cleanmymac_x_chinese.png' width='32' height='32'> CleanMyMac X Chinese | 4.15.14 |
| <img src='Logos/cleanshot.png' width='32' height='32'> CleanShot | 4.8.7 |
| <img src='Logos/cleartext.png' width='32' height='32'> Cleartext | 2.45 |
| <img src='Logos/clickup.png' width='32' height='32'> ClickUp | 3.5.163 |
| <img src='Logos/clion.png' width='32' height='32'> CLion | 2025.3.2 |
| <img src='Logos/clipbook.png' width='32' height='32'> ClipBook | 1.33.0 |
| <img src='Logos/clipgrab.png' width='32' height='32'> ClipGrab | 3.9.16 |
| <img src='Logos/clipy.png' width='32' height='32'> Clipy | 1.2.1 |
| <img src='Logos/clocker.png' width='32' height='32'> Clocker | 23.01 |
| <img src='Logos/clockify.png' width='32' height='32'> Clockify | 2.12.0 |
| <img src='Logos/clop.png' width='32' height='32'> Clop | 2.11.2 |
| <img src='Logos/cloudcompare.png' width='32' height='32'> CloudCompare | 2.13.2 |
| <img src='Logos/cloudflare_warp.png' width='32' height='32'> Cloudflare WARP | 2025.10.186.0 |
| <img src='Logos/cloudytabs.png' width='32' height='32'> CloudyTabs | 2.0 |
| <img src='Logos/cncnet_classic_command__conquer.png' width='32' height='32'> CnCNet: Classic Command & Conquer | 2.1 |
| <img src='Logos/coconutbattery.png' width='32' height='32'> coconutBattery | 4.2.0 |
| <img src='Logos/codeedit.png' width='32' height='32'> CodeEdit | 0.3.6 |
| <img src='Logos/coderunner.png' width='32' height='32'> CodeRunner | 4.5 |
| <img src='Logos/coherence_x.png' width='32' height='32'> Coherence X | 5.1.1 |
| <img src='Logos/colorsnapper_2.png' width='32' height='32'> ColorSnapper 2 | 1.6.4 |
| <img src='Logos/colorwell.png' width='32' height='32'> ColorWell | 8.1.4 |
| <img src='Logos/colour_contrast_analyser.png' width='32' height='32'> Colour Contrast Analyser | 3.5.5 |
| <img src='Logos/combine_pdfs.png' width='32' height='32'> Combine PDFs | 5.6.1 |
| <img src='Logos/comfyui.png' width='32' height='32'> ComfyUI | 0.8.0 |
| <img src='Logos/commander_one.png' width='32' height='32'> Commander One | 3.17.1 |
| <img src='Logos/company_portal.png' width='32' height='32'> Company Portal | 5.2511.0 |
| <img src='Logos/compositor.png' width='32' height='32'> Compositor | 1.28.0 |
| <img src='Logos/connect_fonts.png' width='32' height='32'> Connect Fonts | 28.0.2 |
| <img src='Logos/connectmenow.png' width='32' height='32'> ConnectMeNow | 4.0.18 |
| <img src='Logos/contexts.png' width='32' height='32'> Contexts | 3.9.0 |
| <img src='Logos/cool_retro_term.png' width='32' height='32'> Cool Retro Term | 1.2.0 |
| <img src='Logos/coolterm.png' width='32' height='32'> CoolTerm | 2.4.0.3.0.1425 |
| <img src='Logos/copilot_for_xcode.png' width='32' height='32'> Copilot for Xcode | 0.37.5 |
| <img src='Logos/copyclip.png' width='32' height='32'> CopyClip | 2.9.99.2 |
| <img src='Logos/copyq.png' width='32' height='32'> CopyQ | 13.0.0 |
| <img src='Logos/cork.png' width='32' height='32'> Cork | 1.7.3.1 |
| <img src='Logos/coteditor.png' width='32' height='32'> CotEditor | 6.2.2 |
| <img src='Logos/craft.png' width='32' height='32'> Craft | 3.3.7 |
| <img src='Logos/crashplan.png' width='32' height='32'> CrashPlan | 11.8.0 |
| <img src='Logos/crossover.png' width='32' height='32'> CrossOver | 25.1.1 |
| <img src='Logos/crypter.png' width='32' height='32'> Crypter | 5.0.0 |
| <img src='Logos/cryptomator.png' width='32' height='32'> Cryptomator | 1.18.0 |
| <img src='Logos/crystalfetch.png' width='32' height='32'> Crystalfetch | 2.2.0 |
| <img src='Logos/curio.png' width='32' height='32'> Curio | 32.0.4 |
| <img src='Logos/cursor.png' width='32' height='32'> Cursor | 2.4.22 |
| <img src='Logos/cursorsense.png' width='32' height='32'> CursorSense | 2.4.3 |
| <img src='Logos/cursr.png' width='32' height='32'> Cursr | 1.7.3 |
| <img src='Logos/customshortcuts.png' width='32' height='32'> CustomShortcuts | 1.3 |
| <img src='Logos/cyberduck.png' width='32' height='32'> Cyberduck | 9.3.1 |
| <img src='Logos/daisydisk.png' width='32' height='32'> DaisyDisk | 4.33.2 |
| <img src='Logos/dangerzone.png' width='32' height='32'> Dangerzone | 0.10.0 |
| <img src='Logos/darkmodebuddy.png' width='32' height='32'> DarkModeBuddy | 1.2 |
| <img src='Logos/darktable.png' width='32' height='32'> darktable | 5.4.0 |
| <img src='Logos/dash.png' width='32' height='32'> Dash | 23.0.2 |
| <img src='Logos/dataflare.png' width='32' height='32'> Dataflare | 2.8.5 |
| <img src='Logos/datagraph.png' width='32' height='32'> DataGraph | 5.5 |
| <img src='Logos/datagrip.png' width='32' height='32'> DataGrip | 2025.3.4 |
| <img src='Logos/dataspell.png' width='32' height='32'> DataSpell | 2025.3.2 |
| <img src='Logos/db_browser_for_sqlite.png' width='32' height='32'> DB Browser for SQLite | 3.13.1 |
| <img src='Logos/dbeaver_community_edition.png' width='32' height='32'> DBeaver Community Edition | 25.3.4 |
| <img src='Logos/dbgate.png' width='32' height='32'> DbGate | 7.0.1 |
| <img src='Logos/debookee.png' width='32' height='32'> Debookee | 8.2.0 |
| <img src='Logos/deckset.png' width='32' height='32'> Deckset | 2.0.47 |
| <img src='Logos/deepgit.png' width='32' height='32'> DeepGit | 4.4 |
| <img src='Logos/deepl.png' width='32' height='32'> DeepL | 26.1.33715377 |
| <img src='Logos/deepnest.png' width='32' height='32'> Deepnest | 1.0.5 |
| <img src='Logos/deezer.png' width='32' height='32'> Deezer | 7.1.60 |
| <img src='Logos/default_folder_x.png' width='32' height='32'> Default Folder X | 6.2.5 |
| <img src='Logos/defold.png' width='32' height='32'> Defold | 1.12.0 |
| <img src='Logos/descript.png' width='32' height='32'> Descript | 114.0.4-release.20250509.32955 |
| <img src='Logos/deskpad.png' width='32' height='32'> DeskPad | 1.3.2 |
| <img src='Logos/desktime.png' width='32' height='32'> DeskTime | 6.1.3 |
| <img src='Logos/devkinsta.png' width='32' height='32'> DevKinsta | 2.13.6 |
| <img src='Logos/devknife.png' width='32' height='32'> DevKnife | 1.9.1 |
| <img src='Logos/devonagent_pro.png' width='32' height='32'> DEVONagent Pro | 3.11.10 |
| <img src='Logos/devonsphere_express.png' width='32' height='32'> DEVONsphere Express | 1.9.8 |
| <img src='Logos/devonthink.png' width='32' height='32'> DEVONthink | 4.2 |
| <img src='Logos/devtoys.png' width='32' height='32'> DevToys | 2.0.9.0 |
| <img src='Logos/devutils.png' width='32' height='32'> DevUtils | 1.17.0 |
| <img src='Logos/dialpad.png' width='32' height='32'> Dialpad | 2512.1.0 |
| <img src='Logos/dictionaries.png' width='32' height='32'> Dictionaries | 2.8 |
| <img src='Logos/diffmerge.png' width='32' height='32'> DiffMerge | 4.2.1.1013 |
| <img src='Logos/diffusion_bee.png' width='32' height='32'> Diffusion Bee | 2.5.3 |
| <img src='Logos/digiexam.png' width='32' height='32'> digiexam | 25.4.6 |
| <img src='Logos/digikam.png' width='32' height='32'> digiKam | 8.8.0 |
| <img src='Logos/dingtalk.png' width='32' height='32'> DingTalk | 8.0.2 |
| <img src='Logos/discord.png' width='32' height='32'> Discord | 0.0.375 |
| <img src='Logos/disk_drill.png' width='32' height='32'> Disk Drill | 6.1.2111 |
| <img src='Logos/disk_inventory_x.png' width='32' height='32'> Disk Inventory X | 1.3 |
| <img src='Logos/displaperture.png' width='32' height='32'> Displaperture | 2.3 |
| <img src='Logos/displaycal.png' width='32' height='32'> DisplayCAL | 3.8.9.3 |
| <img src='Logos/displaylink_usb_graphics_software.png' width='32' height='32'> DisplayLink USB Graphics Software | 15.0 |
| <img src='Logos/ditto.png' width='32' height='32'> Ditto | 1.11.8 |
| <img src='Logos/djview.png' width='32' height='32'> DjView | 4.12 |
| <img src='Logos/dockdoor.png' width='32' height='32'> DockDoor | 1.31.2 |
| <img src='Logos/docker_desktop.png' width='32' height='32'> Docker Desktop | 4.42.1 |
| <img src='Logos/dockfix.png' width='32' height='32'> DockFix | 4.1.6 |
| <img src='Logos/dockside.png' width='32' height='32'> Dockside | 1.9.54 |
| <img src='Logos/dockstation.png' width='32' height='32'> DockStation | 1.5.1 |
| <img src='Logos/dockview.png' width='32' height='32'> DockView | 1.7.3 |
| <img src='Logos/dorico.png' width='32' height='32'> Dorico | 6.1.10 |
| <img src='Logos/dosbox.png' width='32' height='32'> DOSBox | 0.74-3 |
| <img src='Logos/double_commander.png' width='32' height='32'> Double Commander | 1.1.32 |
| <img src='Logos/doughnut.png' width='32' height='32'> Doughnut | 2.0.1 |
| <img src='Logos/douyin.png' width='32' height='32'> Douyin | 7.2.0 |
| <img src='Logos/downie.png' width='32' height='32'> Downie | 4.11.10 |
| <img src='Logos/drawio_desktop.png' width='32' height='32'> draw.io Desktop | 29.3.6 |
| <img src='Logos/drawbot.png' width='32' height='32'> DrawBot | 3.132 |
| <img src='Logos/drivedx.png' width='32' height='32'> DriveDX | 1.12.1 |
| <img src='Logos/dropbox.png' width='32' height='32'> Dropbox | 240.4.8609 |
| <img src='Logos/dropdmg.png' width='32' height='32'> DropDMG | 3.7.1 |
| <img src='Logos/droplr.png' width='32' height='32'> Droplr | 5.9.19 |
| <img src='Logos/dropshare.png' width='32' height='32'> Dropshare | 6.9.1 |
| <img src='Logos/dropzone.png' width='32' height='32'> Dropzone | 4.80.75 |
| <img src='Logos/duckduckgo.png' width='32' height='32'> DuckDuckGo | 1.175.0 |
| <img src='Logos/duet.png' width='32' height='32'> Duet | 3.20.3.0 |
| <img src='Logos/duoconnect.png' width='32' height='32'> DuoConnect | 2.0.9 |
| <img src='Logos/dupeguru.png' width='32' height='32'> dupeGuru | 4.3.1 |
| <img src='Logos/dust3d.png' width='32' height='32'> Dust3D | 1.0.0-rc.9 |
| <img src='Logos/dymo_connect.png' width='32' height='32'> Dymo Connect | 1.5.1.15 |
| <img src='Logos/dynalist.png' width='32' height='32'> Dynalist | 1.0.6 |
| <img src='Logos/eaglefiler.png' width='32' height='32'> EagleFiler | 1.9.19 |
| <img src='Logos/easydict.png' width='32' height='32'> Easydict | 2.17.0 |
| <img src='Logos/easyfind.png' width='32' height='32'> EasyFind | 5.0.2 |
| <img src='Logos/ecamm_live.png' width='32' height='32'> Ecamm Live | 4.4.14 |
| <img src='Logos/eclipse_for_rcp_and_rap_developers.png' width='32' height='32'> Eclipse for RCP and RAP Developers | 4.38 |
| <img src='Logos/eclipse_ide_for_cc_developers.png' width='32' height='32'> Eclipse IDE for C/C++ Developers | 4.38 |
| <img src='Logos/eclipse_ide_for_eclipse_committers.png' width='32' height='32'> Eclipse IDE for Eclipse Committers | 4.38 |
| <img src='Logos/eclipse_ide_for_java_and_dsl_developers.png' width='32' height='32'> Eclipse IDE for Java and DSL Developers | 4.38 |
| <img src='Logos/eclipse_ide_for_java_developers.png' width='32' height='32'> Eclipse IDE for Java Developers | 4.38 |
| <img src='Logos/eclipse_ide_for_java_ee_developers.png' width='32' height='32'> Eclipse IDE for Java EE Developers | 4.38 |
| <img src='Logos/eclipse_ide_for_php_developers.png' width='32' height='32'> Eclipse IDE for PHP Developers | 4.38 |
| <img src='Logos/eclipse_installer.png' width='32' height='32'> Eclipse Installer | 4.38 |
| <img src='Logos/eclipse_modeling_tools.png' width='32' height='32'> Eclipse Modeling Tools | 4.38 |
| <img src='Logos/eclipse_temurin_java_development_kit.png' width='32' height='32'> Eclipse Temurin Java Development Kit | 25.0.2 |
| <img src='Logos/edrawmax.png' width='32' height='32'> EdrawMax | 14.5.2 |
| <img src='Logos/egnyte.png' width='32' height='32'> Egnyte | 1.13.0 |
| <img src='Logos/elan.png' width='32' height='32'> ELAN | 7.0 |
| <img src='Logos/electric_sheep.png' width='32' height='32'> Electric Sheep | 3.0.2 |
| <img src='Logos/electron.png' width='32' height='32'> Electron | 40.1.0 |
| <img src='Logos/electron_cash.png' width='32' height='32'> Electron Cash | 4.4.2 |
| <img src='Logos/electron_fiddle.png' width='32' height='32'> Electron Fiddle | 0.37.3 |
| <img src='Logos/electronmail.png' width='32' height='32'> ElectronMail | 5.3.5 |
| <img src='Logos/electrum.png' width='32' height='32'> Electrum | 4.7.0 |
| <img src='Logos/element.png' width='32' height='32'> Element | 1.12.9 |
| <img src='Logos/elephas.png' width='32' height='32'> Elephas | 11.4010 |
| <img src='Logos/elgato_camera_hub.png' width='32' height='32'> Elgato Camera Hub | 2.2.1.6945 |
| <img src='Logos/elgato_capture_device_utility.png' width='32' height='32'> Elgato Capture Device Utility | 1.3.1 |
| <img src='Logos/elgato_control_center.png' width='32' height='32'> Elgato Control Center | 1.8.2 |
| <img src='Logos/elgato_stream_deck.png' width='32' height='32'> Elgato Stream Deck | 7.2.1.22472 |
| <img src='Logos/elgato_wave_link.png' width='32' height='32'> Elgato Wave Link | 2.0.7.3795 |
| <img src='Logos/elmedia_player.png' width='32' height='32'> Elmedia Player | 8.24 |
| <img src='Logos/eltima_cloudmounter.png' width='32' height='32'> Eltima CloudMounter | 4.16 |
| <img src='Logos/em_client.png' width='32' height='32'> eM Client | 10.4.4293 |
| <img src='Logos/enclave.png' width='32' height='32'> Enclave | 2025.6.2 |
| <img src='Logos/enpass.png' width='32' height='32'> Enpass | 6.11.17.2135 |
| <img src='Logos/ente.png' width='32' height='32'> Ente | 1.7.18 |
| <img src='Logos/ente_auth.png' width='32' height='32'> Ente Auth | 4.4.15 |
| <img src='Logos/envkey.png' width='32' height='32'> EnvKey | 1.5.10 |
| <img src='Logos/epic_games_launcher.png' width='32' height='32'> Epic Games Launcher | 19.1.5 |
| <img src='Logos/equinox.png' width='32' height='32'> Equinox | 5.0 |
| <img src='Logos/espanso.png' width='32' height='32'> Espanso | 2.3.0 |
| <img src='Logos/etcher.png' width='32' height='32'> Etcher | 2.1.4 |
| <img src='Logos/etrecheck.png' width='32' height='32'> EtreCheck | 6.8.13 |
| <img src='Logos/eudic.png' width='32' height='32'> Eudic | latest |
| <img src='Logos/evernote.png' width='32' height='32'> Evernote | 10.105.4 |
| <img src='Logos/evkey.png' width='32' height='32'> EVKey | 3.3.8 |
| <img src='Logos/exifcleaner.png' width='32' height='32'> ExifCleaner | 3.6.0 |
| <img src='Logos/exifrenamer.png' width='32' height='32'> ExifRenamer | 2.4.0 |
| <img src='Logos/expandrive.png' width='32' height='32'> ExpanDrive | 2026.01.22.812 |
| <img src='Logos/expressvpn.png' width='32' height='32'> ExpressVPN | 12.1.0.12128 |
| <img src='Logos/extraterm.png' width='32' height='32'> Extraterm | 0.81.4 |
| <img src='Logos/flux.png' width='32' height='32'> f.lux | 42.2 |
| <img src='Logos/facebook_messenger.png' width='32' height='32'> Facebook Messenger | 525.0.0.34.106 |
| <img src='Logos/fantastical.png' width='32' height='32'> Fantastical | 4.1.7 |
| <img src='Logos/far2l.png' width='32' height='32'> far2l | 2.7.0 |
| <img src='Logos/farrago.png' width='32' height='32'> Farrago | 2.1.4 |
| <img src='Logos/fastmail.png' width='32' height='32'> Fastmail | 1.0.8 |
| <img src='Logos/fastscripts.png' width='32' height='32'> FastScripts | 3.3.8 |
| <img src='Logos/fathom.png' width='32' height='32'> Fathom | 1.42.2 |
| <img src='Logos/fellow.png' width='32' height='32'> Fellow | 5.0.1 |
| <img src='Logos/ferdium.png' width='32' height='32'> Ferdium | 7.1.1 |
| <img src='Logos/fig.png' width='32' height='32'> fig | 2.19.0 |
| <img src='Logos/figma.png' width='32' height='32'> Figma | 126.0.4 |
| <img src='Logos/file_juicer.png' width='32' height='32'> File Juicer | 4.114 |
| <img src='Logos/filebot.png' width='32' height='32'> FileBot | 5.2.0 |
| <img src='Logos/filemaker_pro.png' width='32' height='32'> FileMaker Pro | 22.0.4.406 |
| <img src='Logos/filen.png' width='32' height='32'> Filen | 3.0.47 |
| <img src='Logos/fing_desktop.png' width='32' height='32'> Fing Desktop | 3.9.3 |
| <img src='Logos/firecamp.png' width='32' height='32'> Firecamp | 2.6.1 |
| <img src='Logos/fission.png' width='32' height='32'> Fission | 2.9.3 |
| <img src='Logos/flameshot.png' width='32' height='32'> Flameshot | 13.3.0 |
| <img src='Logos/fleet.png' width='32' height='32'> Fleet | 1.48.261 |
| <img src='Logos/flexoptix_app.png' width='32' height='32'> FLEXOPTIX App | 5.58.0-latest |
| <img src='Logos/floorp_browser.png' width='32' height='32'> Floorp browser | 12.10.3 |
| <img src='Logos/flowvision.png' width='32' height='32'> FlowVision | 1.6.8 |
| <img src='Logos/fluid.png' width='32' height='32'> Fluid | 2.1.2 |
| <img src='Logos/flycut.png' width='32' height='32'> Flycut | 1.9.6 |
| <img src='Logos/folx.png' width='32' height='32'> Folx | 5.32 |
| <img src='Logos/fontbase.png' width='32' height='32'> FontBase | 2.25.1 |
| <img src='Logos/fontlab.png' width='32' height='32'> Fontlab | 8.4.2.8950 |
| <img src='Logos/forecast.png' width='32' height='32'> Forecast | 0.9.6 |
| <img src='Logos/fork.png' width='32' height='32'> Fork | 2.62.1 |
| <img src='Logos/forklift.png' width='32' height='32'> ForkLift | 4.4.5 |
| <img src='Logos/foxit_pdf_editor.png' width='32' height='32'> Foxit PDF Editor | 14.0.2.69164 |
| <img src='Logos/framer.png' width='32' height='32'> Framer | 2025.48.2 |
| <img src='Logos/franz.png' width='32' height='32'> Franz | 5.11.0 |
| <img src='Logos/free_download_manager.png' width='32' height='32'> Free Download Manager | 6.33 |
| <img src='Logos/free_ruler.png' width='32' height='32'> Free Ruler | 2.0.8 |
| <img src='Logos/freecad.png' width='32' height='32'> FreeCAD | 1.0.2 |
| <img src='Logos/freefilesync.png' width='32' height='32'> FreeFileSync | 14.7 |
| <img src='Logos/freelens.png' width='32' height='32'> Freelens | 1.8.0 |
| <img src='Logos/freemacsoft_appcleaner.png' width='32' height='32'> FreeMacSoft AppCleaner | 3.6.8 |
| <img src='Logos/freetube.png' width='32' height='32'> FreeTube | 0.23.13 |
| <img src='Logos/front.png' width='32' height='32'> Front | 3.68.0 |
| <img src='Logos/fsmonitor.png' width='32' height='32'> FSMonitor | 1.2 |
| <img src='Logos/fsnotes.png' width='32' height='32'> FSNotes | 7.1.0 |
| <img src='Logos/funter.png' width='32' height='32'> Funter | 7.1 |
| <img src='Logos/fuset.png' width='32' height='32'> FUSE-T | 1.0.49 |
| <img src='Logos/garmin_express.png' width='32' height='32'> Garmin Express | 7.28.0 |
| <img src='Logos/gather_town.png' width='32' height='32'> Gather Town | 1.35.1 |
| <img src='Logos/gdevelop.png' width='32' height='32'> GDevelop | 5.6.254 |
| <img src='Logos/geany.png' width='32' height='32'> Geany | 2.1 |
| <img src='Logos/geekbench.png' width='32' height='32'> Geekbench | 6.5.0 |
| <img src='Logos/geekbench_ai.png' width='32' height='32'> Geekbench AI | 1.5.0 |
| <img src='Logos/gemini.png' width='32' height='32'> Gemini | 2.9.11 |
| <img src='Logos/gephi.png' width='32' height='32'> Gephi | 0.10.1 |
| <img src='Logos/ghost_browser.png' width='32' height='32'> Ghost Browser | 2.4.1.2 |
| <img src='Logos/ghostty.png' width='32' height='32'> Ghostty | 1.2.3 |
| <img src='Logos/gifox.png' width='32' height='32'> gifox | 2.8.0+2 |
| <img src='Logos/gimp.png' width='32' height='32'> GIMP | 3.0.8 |
| <img src='Logos/git_credential_manager.png' width='32' height='32'> Git Credential Manager | 2.7.0 |
| <img src='Logos/gitbutler.png' width='32' height='32'> GitButler | 0.18.7 |
| <img src='Logos/gitfinder.png' width='32' height='32'> GitFinder | 1.7.11 |
| <img src='Logos/gitfox.png' width='32' height='32'> Gitfox | 4.1.0 |
| <img src='Logos/github_copilot_for_xcode.png' width='32' height='32'> GitHub Copilot for Xcode | 0.46.0 |
| <img src='Logos/github_desktop.png' width='32' height='32'> GitHub Desktop | 3.5.4-9dfb8d8d |
| <img src='Logos/gitify.png' width='32' height='32'> Gitify | 6.17.0 |
| <img src='Logos/gitkraken.png' width='32' height='32'> GitKraken | 11.8.0 |
| <img src='Logos/glyphs.png' width='32' height='32'> Glyphs | 3.5 |
| <img src='Logos/go2shell.png' width='32' height='32'> Go2Shell | 2.5 |
| <img src='Logos/godot_engine.png' width='32' height='32'> Godot Engine | 4.6 |
| <img src='Logos/godspeed.png' width='32' height='32'> Godspeed | 1.9.19 |
| <img src='Logos/gog_galaxy.png' width='32' height='32'> GOG Galaxy | 2.0.94.27 |
| <img src='Logos/goland.png' width='32' height='32'> Goland | 2025.3.1.1 |
| <img src='Logos/goodsync.png' width='32' height='32'> GoodSync | 12.9.26 |
| <img src='Logos/google_ads_editor.png' width='32' height='32'> Google Ads Editor | 2.11 |
| <img src='Logos/google_antigravity.png' width='32' height='32'> Google Antigravity | 1.15.8 |
| <img src='Logos/google_chrome.png' width='32' height='32'> Google Chrome | 144.0.7559.110 |
| <img src='Logos/google_drive.png' width='32' height='32'> Google Drive | 120.0.1 |
| <img src='Logos/google_earth_pro.png' width='32' height='32'> Google Earth Pro | 7.3.6.10441 |
| <img src='Logos/google_web_designer.png' width='32' height='32'> Google Web Designer | 14.0.1.0 |
| <img src='Logos/goose.png' width='32' height='32'> Goose | 1.22.2 |
| <img src='Logos/gpg_suite.png' width='32' height='32'> GPG Suite | 2023.3 |
| <img src='Logos/gpodder.png' width='32' height='32'> gPodder | 3.11.5 |
| <img src='Logos/gpt_fdisk.png' width='32' height='32'> GPT fdisk | 1.0.10 |
| <img src='Logos/grammarly_desktop.png' width='32' height='32'> Grammarly Desktop | 1.150.0.0 |
| <img src='Logos/grandperspective.png' width='32' height='32'> GrandPerspective | 3.6.3 |
| <img src='Logos/granola.png' width='32' height='32'> Granola | 7.1.0 |
| <img src='Logos/graphicconverter.png' width='32' height='32'> GraphicConverter | 12.5 |
| <img src='Logos/graphiql_app.png' width='32' height='32'> GraphiQL App | 0.7.2 |
| <img src='Logos/graphpad_prism.png' width='32' height='32'> GraphPad Prism | 10.6.1 |
| <img src='Logos/graphql_playground.png' width='32' height='32'> GraphQL Playground | 1.8.10 |
| <img src='Logos/grids.png' width='32' height='32'> Grids | 8.5.8 |
| <img src='Logos/guilded.png' width='32' height='32'> Guilded | 1.0.9329126 |
| <img src='Logos/guitar_pro.png' width='32' height='32'> Guitar Pro | 8.1.4-43 |
| <img src='Logos/hammerspoon.png' width='32' height='32'> Hammerspoon | 1.1.0 |
| <img src='Logos/handbrake.png' width='32' height='32'> HandBrake | 1.10.2 |
| <img src='Logos/hazel.png' width='32' height='32'> Hazel | 6.1.1 |
| <img src='Logos/hazeover.png' width='32' height='32'> HazeOver | 1.9.6 |
| <img src='Logos/headlamp.png' width='32' height='32'> Headlamp | 0.39.0 |
| <img src='Logos/helium.png' width='32' height='32'> Helium | 1.0.0 |
| <img src='Logos/hepta.png' width='32' height='32'> Hepta | 1.83.5 |
| <img src='Logos/hex_fiend.png' width='32' height='32'> Hex Fiend | 2.18.1 |
| <img src='Logos/hey.png' width='32' height='32'> HEY | 1.2.17 |
| <img src='Logos/hidden_bar.png' width='32' height='32'> Hidden Bar | 1.9 |
| <img src='Logos/hides.png' width='32' height='32'> Hides | 7.2.2 |
| <img src='Logos/hidock.png' width='32' height='32'> HiDock | 1.4 |
| <img src='Logos/highlight.png' width='32' height='32'> Highlight | 1.2.131 |
| <img src='Logos/hma_vpn.png' width='32' height='32'> HMA! VPN | latest |
| <img src='Logos/home_assistant.png' width='32' height='32'> Home Assistant | 2025.11.2 |
| <img src='Logos/homerow.png' width='32' height='32'> Homerow | 1.4.1 |
| <img src='Logos/hoppscotch.png' width='32' height='32'> Hoppscotch | 26.1.0-0 |
| <img src='Logos/hot.png' width='32' height='32'> Hot | 1.9.4 |
| <img src='Logos/houdahspot.png' width='32' height='32'> HoudahSpot | 6.7.2 |
| <img src='Logos/hp_easy_admin.png' width='32' height='32'> HP Easy Admin | 2.16.0 |
| <img src='Logos/http_toolkit.png' width='32' height='32'> HTTP Toolkit | 1.24.4 |
| <img src='Logos/huggingchat.png' width='32' height='32'> HuggingChat | 0.7.0 |
| <img src='Logos/huly.png' width='32' height='32'> Huly | 0.7.353 |
| <img src='Logos/hyper.png' width='32' height='32'> Hyper | 3.4.1 |
| <img src='Logos/hyperkey.png' width='32' height='32'> Hyperkey | 1.56 |
| <img src='Logos/ibm_aspera_connect.png' width='32' height='32'> IBM Aspera Connect | 4.2.13.820 |
| <img src='Logos/ice.png' width='32' height='32'> Ice | 0.11.12 |
| <img src='Logos/icon_composer.png' width='32' height='32'> Icon Composer | 1.2 |
| <img src='Logos/iconjar.png' width='32' height='32'> IconJar | 2.11.4 |
| <img src='Logos/iconset.png' width='32' height='32'> Iconset | 2.5.0 |
| <img src='Logos/idagio.png' width='32' height='32'> IDAGIO | 1.14.0 |
| <img src='Logos/iexplorer.png' width='32' height='32'> iExplorer | 4.6.0 |
| <img src='Logos/iina.png' width='32' height='32'> IINA | 1.4.1 |
| <img src='Logos/imagej.png' width='32' height='32'> ImageJ | 1.54 |
| <img src='Logos/imageoptim.png' width='32' height='32'> ImageOptim | 1.9.3 |
| <img src='Logos/imazing.png' width='32' height='32'> iMazing | 3.4.0 |
| <img src='Logos/imazing_converter.png' width='32' height='32'> iMazing Converter | 2.0.9 |
| <img src='Logos/imazing_profile_editor.png' width='32' height='32'> iMazing Profile Editor | 2.1.2 |
| <img src='Logos/imhex.png' width='32' height='32'> ImHex | 1.38.1 |
| <img src='Logos/inkscape.png' width='32' height='32'> Inkscape | 1.4.3 |
| <img src='Logos/input_source_pro.png' width='32' height='32'> Input Source Pro | 2.9.0 |
| <img src='Logos/insomnia.png' width='32' height='32'> Insomnia | 12.3.0 |
| <img src='Logos/insta360_link_controller.png' width='32' height='32'> Insta360 Link Controller | 2.2.1 |
| <img src='Logos/insta360_studio.png' width='32' height='32'> Insta360 Studio | 5.8.8 |
| <img src='Logos/integrity.png' width='32' height='32'> Integrity | 12.11.3 |
| <img src='Logos/intellidock.png' width='32' height='32'> IntelliDock | 1.0 |
| <img src='Logos/intellij_idea_community_edition.png' width='32' height='32'> IntelliJ IDEA Community Edition | 2025.2.5 |
| <img src='Logos/intellij_idea_ultimate.png' width='32' height='32'> IntelliJ IDEA Ultimate | 2025.3.2 |
| <img src='Logos/invesalius.png' width='32' height='32'> InVesalius | 3.1.99998 |
| <img src='Logos/iris.png' width='32' height='32'> Iris | 1.2.2 |
| <img src='Logos/istats_menus.png' width='32' height='32'> iStats Menus | 7.20.7 |
| <img src='Logos/istherenet.png' width='32' height='32'> IsThereNet | 1.7.1 |
| <img src='Logos/iterm2.png' width='32' height='32'> iTerm2 | 3.6.6 |
| <img src='Logos/itsycal.png' width='32' height='32'> Itsycal | 0.15.10 |
| <img src='Logos/jabra_direct.png' width='32' height='32'> Jabra Direct | 6.26.32801 |
| <img src='Logos/jami.png' width='32' height='32'> Jami | 2.38 |
| <img src='Logos/jamie.png' width='32' height='32'> Jamie | 4.5.0 |
| <img src='Logos/jamovi.png' width='32' height='32'> jamovi | 2.7.17.0 |
| <img src='Logos/jasp.png' width='32' height='32'> JASP | 0.95.4.0 |
| <img src='Logos/jellyfin.png' width='32' height='32'> Jellyfin | 10.11.6 |
| <img src='Logos/jetbrains_phpstorm.png' width='32' height='32'> JetBrains PhpStorm | 2025.3.2 |
| <img src='Logos/jetbrains_pycharm_community_edition.png' width='32' height='32'> Jetbrains PyCharm Community Edition | 2025.2.5 |
| <img src='Logos/jetbrains_rider.png' width='32' height='32'> JetBrains Rider | 2025.3.2 |
| <img src='Logos/jetbrains_toolbox.png' width='32' height='32'> JetBrains Toolbox | 3.2 |
| <img src='Logos/jiggler.png' width='32' height='32'> Jiggler | 1.10 |
| <img src='Logos/jitsi_meet.png' width='32' height='32'> Jitsi Meet | 2025.10.0 |
| <img src='Logos/joplin.png' width='32' height='32'> Joplin | 3.5.12 |
| <img src='Logos/jump_desktop.png' width='32' height='32'> Jump Desktop | 9.1.9 |
| <img src='Logos/jumpcut.png' width='32' height='32'> Jumpcut | 0.84 |
| <img src='Logos/jumpshare.png' width='32' height='32'> Jumpshare | 3.4.22 |
| <img src='Logos/kaleidoscope.png' width='32' height='32'> Kaleidoscope | 6.5 |
| <img src='Logos/kap.png' width='32' height='32'> Kap | 3.6.0 |
| <img src='Logos/karabiner_elements.png' width='32' height='32'> Karabiner Elements | 15.9.0 |
| <img src='Logos/kdenlive.png' width='32' height='32'> Kdenlive | 25.12.1 |
| <img src='Logos/keepassxc.png' width='32' height='32'> KeePassXC | 2.7.11 |
| <img src='Logos/keeper_password_manager.png' width='32' height='32'> Keeper Password Manager | 17.5.1 |
| <img src='Logos/keepingyouawake.png' width='32' height='32'> KeepingYouAwake | 1.6.8 |
| <img src='Logos/keeweb.png' width='32' height='32'> KeeWeb | 1.18.7 |
| <img src='Logos/keka.png' width='32' height='32'> Keka | 1.6.0 |
| <img src='Logos/keybase.png' width='32' height='32'> Keybase | 6.5.4 |
| <img src='Logos/keyboard_cowboy.png' width='32' height='32'> Keyboard Cowboy | 3.28.4 |
| <img src='Logos/keyboard_maestro.png' width='32' height='32'> Keyboard Maestro | 11.0.4 |
| <img src='Logos/keyboardcleantool.png' width='32' height='32'> KeyboardCleanTool | 7 |
| <img src='Logos/keycastr.png' width='32' height='32'> KeyCastr | 0.10.5 |
| <img src='Logos/keyclu.png' width='32' height='32'> KeyClu | 0.31 |
| <img src='Logos/keystore_explorer.png' width='32' height='32'> KeyStore Explorer | 5.6.1 |
| <img src='Logos/kicad.png' width='32' height='32'> KiCad | 9.0.7 |
| <img src='Logos/kitty.png' width='32' height='32'> kitty | 0.45.0 |
| <img src='Logos/klokki.png' width='32' height='32'> Klokki | 1.3.7 |
| <img src='Logos/knockknock.png' width='32' height='32'> KnockKnock | 4.0.3 |
| <img src='Logos/kobo.png' width='32' height='32'> Kobo | latest |
| <img src='Logos/kodi.png' width='32' height='32'> Kodi | 21.3-Omega |
| <img src='Logos/krisp.png' width='32' height='32'> Krisp | 3.9.4 |
| <img src='Logos/krita.png' width='32' height='32'> Krita | 5.2.15 |
| <img src='Logos/langgraph_studio.png' width='32' height='32'> LangGraph Studio | 0.0.37 |
| <img src='Logos/lapce.png' width='32' height='32'> Lapce | 0.4.6 |
| <img src='Logos/lark.png' width='32' height='32'> Lark | 7.60.9 |
| <img src='Logos/last_window_quits.png' width='32' height='32'> Last Window Quits | 1.1.4 |
| <img src='Logos/latest.png' width='32' height='32'> Latest | 0.11 |
| <img src='Logos/launchbar.png' width='32' height='32'> LaunchBar | 6.22.2 |
| <img src='Logos/launchcontrol.png' width='32' height='32'> LaunchControl | 2.10.1 |
| <img src='Logos/launchos.png' width='32' height='32'> LaunchOS | 1.5.1 |
| <img src='Logos/lens.png' width='32' height='32'> Lens | 2026.1.161237 |
| <img src='Logos/librecad.png' width='32' height='32'> LibreCAD | 2.2.1.3 |
| <img src='Logos/libreoffice.png' width='32' height='32'> LibreOffice | 25.8.4 |
| <img src='Logos/librewolf.png' width='32' height='32'> LibreWolf | 147.0.2 |
| <img src='Logos/lifesize.png' width='32' height='32'> lifesize | 3.0.18 |
| <img src='Logos/lightburn.png' width='32' height='32'> LightBurn | 2.0.05 |
| <img src='Logos/limitless.png' width='32' height='32'> Limitless | 2.961.1 |
| <img src='Logos/linear.png' width='32' height='32'> Linear | 1.28.10 |
| <img src='Logos/linearmouse.png' width='32' height='32'> LinearMouse | 0.10.2 |
| <img src='Logos/lingon_x.png' width='32' height='32'> Lingon X | 9.6.6 |
| <img src='Logos/little_snitch.png' width='32' height='32'> Little Snitch | 6.3.3 |
| <img src='Logos/lm_studio.png' width='32' height='32'> LM Studio | 0.4.1 |
| <img src='Logos/lorain.png' width='32' height='32'> lo-rain | 1.5.2 |
| <img src='Logos/local.png' width='32' height='32'> Local | 9.2.9 |
| <img src='Logos/localsend.png' width='32' height='32'> LocalSend | 1.17.0 |
| <img src='Logos/locationsimulator.png' width='32' height='32'> LocationSimulator | 0.2.2 |
| <img src='Logos/logitech_g_hub.png' width='32' height='32'> Logitech G HUB | 2025.9.824733 |
| <img src='Logos/logitech_options.png' width='32' height='32'> Logitech Options+ | 1.98.824948 |
| <img src='Logos/logseq.png' width='32' height='32'> Logseq | 0.10.15 |
| <img src='Logos/lookaway.png' width='32' height='32'> LookAway | 1.14.10 |
| <img src='Logos/loom.png' width='32' height='32'> Loom | 0.330.1 |
| <img src='Logos/loop.png' width='32' height='32'> Loop | 1.4.2 |
| <img src='Logos/loopback.png' width='32' height='32'> Loopback | 2.4.8 |
| <img src='Logos/losslesscut.png' width='32' height='32'> LosslessCut | 3.68.0 |
| <img src='Logos/loupdeck.png' width='32' height='32'> Loupdeck | 6.2.4.228 |
| <img src='Logos/low_profile.png' width='32' height='32'> Low Profile | 5.0.0 |
| <img src='Logos/ltspice.png' width='32' height='32'> LTspice | 17.2.4 |
| <img src='Logos/lulu.png' width='32' height='32'> LuLu | 4.2.1 |
| <img src='Logos/lunacy.png' width='32' height='32'> Lunacy | 11.6 |
| <img src='Logos/lunar.png' width='32' height='32'> Lunar | 6.9.6 |
| <img src='Logos/lunasea.png' width='32' height='32'> LunaSea | 11.0.0 |
| <img src='Logos/lunatask.png' width='32' height='32'> Lunatask | 2.1.20 |
| <img src='Logos/lyx.png' width='32' height='32'> LyX | 2.4.4 |
| <img src='Logos/löve.png' width='32' height='32'> LÖVE | 11.5 |
| <img src='Logos/mac_mouse_fix.png' width='32' height='32'> Mac Mouse Fix | 3.0.8 |
| <img src='Logos/maccy.png' width='32' height='32'> Maccy | 2.6.1 |
| <img src='Logos/macdown.png' width='32' height='32'> MacDown | 0.7.2 |
| <img src='Logos/macfuse.png' width='32' height='32'> macFUSE | 5.1.3 |
| <img src='Logos/macjournal.png' width='32' height='32'> MacJournal | 7.4 |
| <img src='Logos/macpacker.png' width='32' height='32'> MacPacker | 0.13 |
| <img src='Logos/macpass.png' width='32' height='32'> MacPass | 0.8.1 |
| <img src='Logos/macpilot.png' width='32' height='32'> MacPilot | 17.5 |
| <img src='Logos/macs_fan_control.png' width='32' height='32'> Macs Fan Control | 1.5.20 |
| <img src='Logos/macsyzones.png' width='32' height='32'> MacsyZones | 2.0.2 |
| <img src='Logos/mactex.png' width='32' height='32'> MacTeX | 2025.0308 |
| <img src='Logos/mactracker.png' width='32' height='32'> Mactracker | 8.1.1 |
| <img src='Logos/macwhisper.png' width='32' height='32'> MacWhisper | 13.12.2 |
| <img src='Logos/maestral.png' width='32' height='32'> Maestral | 1.9.5 |
| <img src='Logos/magicquit.png' width='32' height='32'> MagicQuit | 1.4 |
| <img src='Logos/mailmate.png' width='32' height='32'> MailMate | 5673 |
| <img src='Logos/mailspring.png' width='32' height='32'> Mailspring | 1.17.3 |
| <img src='Logos/makemkv.png' width='32' height='32'> MakeMKV | 1.18.3 |
| <img src='Logos/malwarebytes_for_mac.png' width='32' height='32'> Malwarebytes for Mac | 5.20.0.3620 |
| <img src='Logos/marginnote.png' width='32' height='32'> MarginNote | 4.2.4 |
| <img src='Logos/markedit.png' width='32' height='32'> MarkEdit | 1.29.1 |
| <img src='Logos/marsedit.png' width='32' height='32'> MarsEdit | 5.3.12 |
| <img src='Logos/marta_file_manager.png' width='32' height='32'> Marta File Manager | 0.8.2 |
| <img src='Logos/masscode.png' width='32' height='32'> massCode | 4.4.0 |
| <img src='Logos/mattermost.png' width='32' height='32'> Mattermost | 6.0.4 |
| <img src='Logos/medis.png' width='32' height='32'> Medis | 2.16.1 |
| <img src='Logos/meetingbar.png' width='32' height='32'> MeetingBar | 4.11.6 |
| <img src='Logos/mega.png' width='32' height='32'> MEGA | 12.1.2 |
| <img src='Logos/megasync.png' width='32' height='32'> MEGAsync | 6.1.1.0 |
| <img src='Logos/meld_for_macos.png' width='32' height='32'> Meld for macOS | 3.22.3+105 |
| <img src='Logos/mellel.png' width='32' height='32'> Mellel | 6.6.0 |
| <img src='Logos/melodics.png' width='32' height='32'> Melodics | 4.1.2953 |
| <img src='Logos/mem.png' width='32' height='32'> Mem | 0.43.0 |
| <img src='Logos/memory_cleaner.png' width='32' height='32'> Memory Cleaner | 5.5.1 |
| <img src='Logos/memory_tracker_by_timely.png' width='32' height='32'> Memory Tracker by Timely | 2023.11 |
| <img src='Logos/mendeley_reference_manager.png' width='32' height='32'> Mendeley Reference Manager | 2.142.0 |
| <img src='Logos/menubar_stats.png' width='32' height='32'> MenuBar Stats | 3.9 |
| <img src='Logos/menubarx.png' width='32' height='32'> MenubarX | 1.7.6 |
| <img src='Logos/merlin_project.png' width='32' height='32'> Merlin Project | 9.1.2 |
| <img src='Logos/micro_snitch.png' width='32' height='32'> Micro Snitch | 1.6.1 |
| <img src='Logos/microsoft_auto_update.png' width='32' height='32'> Microsoft Auto Update | 4.81.25121042 |
| <img src='Logos/microsoft_azure_storage_explorer.png' width='32' height='32'> Microsoft Azure Storage Explorer | 1.41.0 |
| <img src='Logos/microsoft_build_of_openjdk.png' width='32' height='32'> Microsoft Build of OpenJDK | 25.0.2 |
| <img src='Logos/microsoft_edge.png' width='32' height='32'> Microsoft Edge | 144.0.3719.104 |
| <img src='Logos/microsoft_excel.png' width='32' height='32'> Microsoft Excel | 16.105.26012530 |
| <img src='Logos/microsoft_office.png' width='32' height='32'> Microsoft Office | 16.105.26011018 |
| <img src='Logos/microsoft_office_businesspro.png' width='32' height='32'> Microsoft Office BusinessPro | 16.105.26011018 |
| <img src='Logos/microsoft_onenote.png' width='32' height='32'> Microsoft OneNote | 16.105.26011018 |
| <img src='Logos/microsoft_outlook.png' width='32' height='32'> Microsoft Outlook | 16.105.26012530 |
| <img src='Logos/microsoft_powerpoint.png' width='32' height='32'> Microsoft PowerPoint | 16.105.26012530 |
| <img src='Logos/microsoft_teams.png' width='32' height='32'> Microsoft Teams | 25290.302.4044.3989 |
| <img src='Logos/microsoft_visual_studio_code.png' width='32' height='32'> Microsoft Visual Studio Code | 1.108.2 |
| <img src='Logos/microsoft_word.png' width='32' height='32'> Microsoft Word | 16.105.26012530 |
| <img src='Logos/middle.png' width='32' height='32'> Middle | 1.14 |
| <img src='Logos/middleclick.png' width='32' height='32'> MiddleClick | 3.1.3 |
| <img src='Logos/milanote.png' width='32' height='32'> Milanote | 3.18.75 |
| <img src='Logos/mimestream.png' width='32' height='32'> Mimestream | 1.9.10 |
| <img src='Logos/min.png' width='32' height='32'> Min | 1.35.2 |
| <img src='Logos/mindmac.png' width='32' height='32'> MindMac | 1.9.28 |
| <img src='Logos/mindmanager.png' width='32' height='32'> Mindmanager | 25.1.105 |
| <img src='Logos/minecraft.png' width='32' height='32'> Minecraft | 2.1.3 |
| <img src='Logos/minisim.png' width='32' height='32'> MiniSim | 0.9.1 |
| <img src='Logos/minstaller.png' width='32' height='32'> mInstaller | 3.2.2 |
| <img src='Logos/miro.png' width='32' height='32'> Miro | 0.11.125 |
| <img src='Logos/mission_control_plus.png' width='32' height='32'> Mission Control Plus | 1.24 |
| <img src='Logos/missive.png' width='32' height='32'> Missive | 11.12.4 |
| <img src='Logos/mist.png' width='32' height='32'> Mist | 0.30 |
| <img src='Logos/mitmproxy.png' width='32' height='32'> mitmproxy | 12.2.1 |
| <img src='Logos/mixxx.png' width='32' height='32'> Mixxx | 2.5.4 |
| <img src='Logos/mobirise.png' width='32' height='32'> Mobirise | 6.1.12 |
| <img src='Logos/mockoon.png' width='32' height='32'> Mockoon | 9.5.0 |
| <img src='Logos/modern_csv.png' width='32' height='32'> Modern CSV | 2.3 |
| <img src='Logos/mongodb_compass.png' width='32' height='32'> MongoDB Compass | 1.49.1 |
| <img src='Logos/monitorcontrol.png' width='32' height='32'> MonitorControl | 4.3.3 |
| <img src='Logos/monodraw.png' width='32' height='32'> Monodraw | 1.7.1 |
| <img src='Logos/moom.png' width='32' height='32'> Moom | 4.4.1 |
| <img src='Logos/moonlight.png' width='32' height='32'> Moonlight | 6.1.0 |
| <img src='Logos/mos.png' width='32' height='32'> Mos | 3.5.0 |
| <img src='Logos/motrix.png' width='32' height='32'> Motrix | 1.8.19 |
| <img src='Logos/mountain_duck.png' width='32' height='32'> Mountain Duck | 5.1.1 |
| <img src='Logos/mounty_for_ntfs.png' width='32' height='32'> Mounty for NTFS | 2.4 |
| <img src='Logos/mouseless.png' width='32' height='32'> mouseless | 0.4.3 |
| <img src='Logos/movist_pro.png' width='32' height='32'> Movist Pro | 2.13.1 |
| <img src='Logos/mozilla_firefox.png' width='32' height='32'> Mozilla Firefox | 147.0.2 |
| <img src='Logos/mozilla_firefox_developer_edition.png' width='32' height='32'> Mozilla Firefox Developer Edition | 148.0b10 |
| <img src='Logos/mozilla_firefox_esr.png' width='32' height='32'> Mozilla Firefox ESR | 140.7.0 |
| <img src='Logos/mozilla_thunderbird.png' width='32' height='32'> Mozilla Thunderbird | 147.0.1 |
| <img src='Logos/mqttx.png' width='32' height='32'> MQTTX | 1.13.0 |
| <img src='Logos/mucommander.png' width='32' height='32'> muCommander | 1.5.2-1 |
| <img src='Logos/mullvad_browser.png' width='32' height='32'> Mullvad Browser | 15.0.4 |
| <img src='Logos/mullvad_vpn.png' width='32' height='32'> Mullvad VPN | 2025.14 |
| <img src='Logos/multi.png' width='32' height='32'> Multi | 3.0.1 |
| <img src='Logos/multipass.png' width='32' height='32'> Multipass | 1.16.1 |
| <img src='Logos/multitouch.png' width='32' height='32'> Multitouch | 1.41 |
| <img src='Logos/multiviewer_for_f1.png' width='32' height='32'> MultiViewer for F1 | 1.43.2 |
| <img src='Logos/mural.png' width='32' height='32'> MURAL | 3.0.4 |
| <img src='Logos/murus_firewall.png' width='32' height='32'> Murus Firewall | 2.7 |
| <img src='Logos/museeks.png' width='32' height='32'> Museeks | 0.23.1 |
| <img src='Logos/musescore.png' width='32' height='32'> MuseScore | 4.6.5.253511702 |
| <img src='Logos/mx_power_gadget.png' width='32' height='32'> Mx Power Gadget | 1.5.2 |
| <img src='Logos/mysql_workbench.png' width='32' height='32'> MySQL Workbench | 8.0.46 |
| <img src='Logos/nagstamon.png' width='32' height='32'> Nagstamon | 3.16.2 |
| <img src='Logos/name_mangler.png' width='32' height='32'> Name Mangler | 3.9.3 |
| <img src='Logos/namechanger.png' width='32' height='32'> NameChanger | 3.4.4 |
| <img src='Logos/naps2.png' width='32' height='32'> NAPS2 | 8.2.1 |
| <img src='Logos/native_access.png' width='32' height='32'> Native Access | 3.22.0 |
| <img src='Logos/nektony_app_cleaner__uninstaller.png' width='32' height='32'> Nektony App Cleaner & Uninstaller | 9.0.4 |
| <img src='Logos/nektony_maccleaner_pro.png' width='32' height='32'> Nektony MacCleaner Pro | 4.0.2 |
| <img src='Logos/neo_network_utility.png' width='32' height='32'> Neo Network Utility | 2.0 |
| <img src='Logos/neofinder.png' width='32' height='32'> NeoFinder | 9.1 |
| <img src='Logos/netbeans_ide.png' width='32' height='32'> NetBeans IDE | 27 |
| <img src='Logos/netiquette.png' width='32' height='32'> Netiquette | 2.3.0 |
| <img src='Logos/netnewswire.png' width='32' height='32'> NetNewsWire | 7.0 |
| <img src='Logos/netron.png' width='32' height='32'> Netron | 8.8.8 |
| <img src='Logos/netspot.png' width='32' height='32'> NetSpot | 5.1.4971 |
| <img src='Logos/nextcloud.png' width='32' height='32'> Nextcloud | 4.0.6 |
| <img src='Logos/nextcloud_talk_desktop.png' width='32' height='32'> Nextcloud Talk Desktop | 2.0.6 |
| <img src='Logos/nightfall.png' width='32' height='32'> Nightfall | 3.1.0 |
| <img src='Logos/nitro_pdf_pro.png' width='32' height='32'> Nitro PDF Pro | 14.10.4 |
| <img src='Logos/nocturnal.png' width='32' height='32'> Nocturnal | 0.3 |
| <img src='Logos/nomachine.png' width='32' height='32'> NoMachine | 9.3.7 |
| <img src='Logos/nordlayer.png' width='32' height='32'> NordLayer | 3.9.1 |
| <img src='Logos/nordlocker.png' width='32' height='32'> NordLocker | 4.26.1 |
| <img src='Logos/nordpass.png' width='32' height='32'> NordPass | 7.3.14 |
| <img src='Logos/nordvpn.png' width='32' height='32'> NordVPN | 9.12.0 |
| <img src='Logos/nosql_workbench.png' width='32' height='32'> NoSQL Workbench | 3.13.7 |
| <img src='Logos/nota_gyazo_gif.png' width='32' height='32'> Nota Gyazo GIF | 10.5.0 |
| <img src='Logos/notchnook.png' width='32' height='32'> NotchNook | 1.5.5 |
| <img src='Logos/notesnook.png' width='32' height='32'> Notesnook | 3.3.8 |
| <img src='Logos/notesollama.png' width='32' height='32'> NotesOllama | 0.2.6 |
| <img src='Logos/notion.png' width='32' height='32'> Notion | 7.2.1 |
| <img src='Logos/notion_calendar.png' width='32' height='32'> Notion Calendar | 1.132.0 |
| <img src='Logos/notion_enhanced.png' width='32' height='32'> Notion Enhanced | 2.0.18-1 |
| <img src='Logos/notion_mail.png' width='32' height='32'> Notion Mail | 0.0.44 |
| <img src='Logos/notunes.png' width='32' height='32'> noTunes | 3.5 |
| <img src='Logos/noun_project.png' width='32' height='32'> Noun Project | 2.3 |
| <img src='Logos/novabench.png' width='32' height='32'> Novabench | 5.6.1 |
| <img src='Logos/nucleo.png' width='32' height='32'> Nucleo | 4.1.9 |
| <img src='Logos/nudge.png' width='32' height='32'> Nudge | 2.0.12.81807 |
| <img src='Logos/numi.png' width='32' height='32'> Numi | 3.32.721 |
| <img src='Logos/nvidia_geforce_now.png' width='32' height='32'> NVIDIA GeForce NOW | 2.0.81.178 |
| <img src='Logos/obs.png' width='32' height='32'> OBS | 32.0.4 |
| <img src='Logos/obsidian.png' width='32' height='32'> Obsidian | 1.11.5 |
| <img src='Logos/ocenaudio.png' width='32' height='32'> ocenaudio | 3.17.1 |
| <img src='Logos/ok_json.png' width='32' height='32'> OK JSON | 2.10.1 |
| <img src='Logos/oka_unarchiver.png' width='32' height='32'> Oka Unarchiver | 2.1.6 |
| <img src='Logos/okta_advanced_server_access.png' width='32' height='32'> Okta Advanced Server Access | 1.99.7 |
| <img src='Logos/okta_verify.png' width='32' height='32'> Okta Verify | 9.55.0 |
| <img src='Logos/ollama.png' width='32' height='32'> Ollama | 0.9.2 |
| <img src='Logos/omnidisksweeper.png' width='32' height='32'> OmniDiskSweeper | 1.16 |
| <img src='Logos/omnifocus.png' width='32' height='32'> OmniFocus | 4.8.6 |
| <img src='Logos/omnigraffle.png' width='32' height='32'> OmniGraffle | 7.25.1 |
| <img src='Logos/omnioutliner.png' width='32' height='32'> OmniOutliner | 6.0.2 |
| <img src='Logos/omniplan.png' width='32' height='32'> OmniPlan | 4.10.1 |
| <img src='Logos/omnissa_horizon_client.png' width='32' height='32'> Omnissa Horizon Client | 2506-8.16.0-16536825094 |
| <img src='Logos/one_switch.png' width='32' height='32'> One Switch | 1.35.2 |
| <img src='Logos/onedrive.png' width='32' height='32'> OneDrive | 25.243.1211.0001 |
| <img src='Logos/onionshare.png' width='32' height='32'> OnionShare | 2.6.3 |
| <img src='Logos/onlyoffice.png' width='32' height='32'> ONLYOFFICE | 9.2.1 |
| <img src='Logos/onlyswitch.png' width='32' height='32'> OnlySwitch | 2.6.5 |
| <img src='Logos/onyx.png' width='32' height='32'> OnyX | 4.9.4 |
| <img src='Logos/opal_composer.png' width='32' height='32'> Opal Composer | 2.0.0 |
| <img src='Logos/openaudible.png' width='32' height='32'> OpenAudible | 4.7.1 |
| <img src='Logos/openboard.png' width='32' height='32'> OpenBoard | 1.7.5 |
| <img src='Logos/opencloud_desktop.png' width='32' height='32'> OpenCloud Desktop | 3.0.3 |
| <img src='Logos/openinterminal.png' width='32' height='32'> OpenInTerminal | 2.3.8 |
| <img src='Logos/openlens.png' width='32' height='32'> OpenLens | 6.5.2-366 |
| <img src='Logos/openmtp.png' width='32' height='32'> OpenMTP | 3.2.25 |
| <img src='Logos/openrct2.png' width='32' height='32'> OpenRCT2 | 0.4.31 |
| <img src='Logos/openrefine.png' width='32' height='32'> OpenRefine | 3.9.5 |
| <img src='Logos/openshot_video_editor.png' width='32' height='32'> OpenShot Video Editor | 3.4.0 |
| <img src='Logos/opentoonz.png' width='32' height='32'> OpenToonz | 1.7.1 |
| <img src='Logos/openvpn_connect_client.png' width='32' height='32'> OpenVPN Connect client | 3.8.1 |
| <img src='Logos/opera.png' width='32' height='32'> Opera | 127.0.5778.14 |
| <img src='Logos/opera_gx.png' width='32' height='32'> Opera GX | 126.0.5750.88 |
| <img src='Logos/optimus_player.png' width='32' height='32'> Optimus Player | 1.5 |
| <img src='Logos/oracle_virtualbox.png' width='32' height='32'> Oracle VirtualBox | 7.2.6 |
| <img src='Logos/orbstack.png' width='32' height='32'> OrbStack | 2.0.5 |
| <img src='Logos/orca_slicer.png' width='32' height='32'> Orca Slicer | 2.3.1 |
| <img src='Logos/orion_browser.png' width='32' height='32'> Orion Browser | 1.0.3 |
| <img src='Logos/orka_cli.png' width='32' height='32'> Orka CLI | 2.4.0 |
| <img src='Logos/orka_desktop.png' width='32' height='32'> Orka Desktop | 3.1.0 |
| <img src='Logos/osquery.png' width='32' height='32'> osquery | 5.21.0 |
| <img src='Logos/outset.png' width='32' height='32'> outset | 4.2.0.21973 |
| <img src='Logos/overflow.png' width='32' height='32'> Overflow | 3.2.1 |
| <img src='Logos/oversight.png' width='32' height='32'> OverSight | 2.4.0 |
| <img src='Logos/owncloud.png' width='32' height='32'> ownCloud | 6.0.3.18040 |
| <img src='Logos/pacifist.png' width='32' height='32'> Pacifist | 4.1.4 |
| <img src='Logos/packages.png' width='32' height='32'> Packages | 1.2.10 |
| <img src='Logos/paintbrush.png' width='32' height='32'> Paintbrush | 2.6.0 |
| <img src='Logos/pale_moon.png' width='32' height='32'> Pale Moon | 34.0.1 |
| <img src='Logos/paletro.png' width='32' height='32'> Paletro | 1.11.0 |
| <img src='Logos/panic_nova.png' width='32' height='32'> Panic Nova | 13.3 |
| <img src='Logos/parallels_client.png' width='32' height='32'> Parallels Client | 19.4.3 |
| <img src='Logos/parallels_desktop.png' width='32' height='32'> Parallels Desktop | 26.2.1-57371 |
| <img src='Logos/parsec.png' width='32' height='32'> Parsec | 150-101a |
| <img src='Logos/paste.png' width='32' height='32'> Paste | 6.3.5 |
| <img src='Logos/pastebot.png' width='32' height='32'> Pastebot | 2.4.6 |
| <img src='Logos/path_finder.png' width='32' height='32'> Path Finder | 2211 |
| <img src='Logos/pdf_expert.png' width='32' height='32'> PDF Expert | 3.11 |
| <img src='Logos/pdf_pals.png' width='32' height='32'> PDF Pals | 1.9.0 |
| <img src='Logos/pdfsam_basic.png' width='32' height='32'> PDFsam Basic | 5.4.5 |
| <img src='Logos/pearcleaner.png' width='32' height='32'> Pearcleaner | 5.4.3 |
| <img src='Logos/pencil.png' width='32' height='32'> Pencil | 3.1.1 |
| <img src='Logos/permute.png' width='32' height='32'> Permute | 3.14.6 |
| <img src='Logos/pgadmin4.png' width='32' height='32'> pgAdmin4 | 9.11 |
| <img src='Logos/philips_hue_sync.png' width='32' height='32'> Philips Hue Sync | 1.13.1.83 |
| <img src='Logos/phoenix.png' width='32' height='32'> Phoenix | 4.0.1 |
| <img src='Logos/phoenix_slides.png' width='32' height='32'> Phoenix Slides | 1.5.9 |
| <img src='Logos/photostickies.png' width='32' height='32'> PhotoStickies | 6.0.1 |
| <img src='Logos/pibar.png' width='32' height='32'> PiBar | 1.1.2 |
| <img src='Logos/picview.png' width='32' height='32'> PicView | 4.1.1 |
| <img src='Logos/piezo.png' width='32' height='32'> Piezo | 1.9.8 |
| <img src='Logos/pika.png' width='32' height='32'> Pika | 1.3.0 |
| <img src='Logos/pingplotter.png' width='32' height='32'> PingPlotter | 5.25.20 |
| <img src='Logos/piphero.png' width='32' height='32'> PiPHero | 1.2.0 |
| <img src='Logos/piriform_ccleaner.png' width='32' height='32'> Piriform CCleaner | 2.09.187 |
| <img src='Logos/pitch.png' width='32' height='32'> Pitch | 2.112.0 |
| <img src='Logos/pixelsnap.png' width='32' height='32'> PixelSnap | 2.6.1 |
| <img src='Logos/platypus.png' width='32' height='32'> Platypus | 5.5.0 |
| <img src='Logos/plex.png' width='32' height='32'> Plex | 1.112.0.359 |
| <img src='Logos/plex_htpc.png' width='32' height='32'> Plex HTPC | 1.71.1.346 |
| <img src='Logos/plex_media_server.png' width='32' height='32'> Plex Media Server | 1.43.0.10467 |
| <img src='Logos/plexamp.png' width='32' height='32'> Plexamp | 4.12.4 |
| <img src='Logos/plistedit_pro.png' width='32' height='32'> PlistEdit Pro | 1.10.0 |
| <img src='Logos/podman_desktop.png' width='32' height='32'> Podman Desktop | 1.25.1 |
| <img src='Logos/polymail.png' width='32' height='32'> Polymail | 2.4.3002 |
| <img src='Logos/popchar_x.png' width='32' height='32'> PopChar X | 10.5 |
| <img src='Logos/popclip.png' width='32' height='32'> PopClip | 2025.9.2 |
| <img src='Logos/popsql.png' width='32' height='32'> PopSQL | 1.0.135 |
| <img src='Logos/portx.png' width='32' height='32'> portx | 2.2.15 |
| <img src='Logos/positron.png' width='32' height='32'> Positron | 2026.02.0-139 |
| <img src='Logos/postbox.png' width='32' height='32'> Postbox | 7.0.65 |
| <img src='Logos/postico.png' width='32' height='32'> Postico | 2.3.1 |
| <img src='Logos/postman.png' width='32' height='32'> Postman | 11.83.2 |
| <img src='Logos/powerphotos.png' width='32' height='32'> PowerPhotos | 3.2.4 |
| <img src='Logos/powershell.png' width='32' height='32'> PowerShell | 7.5.4 |
| <img src='Logos/preform.png' width='32' height='32'> PreForm | 3.48.0 |
| <img src='Logos/principle.png' width='32' height='32'> Principle | 6.42 |
| <img src='Logos/pritunl.png' width='32' height='32'> Pritunl | 1.3.4466.51 |
| <img src='Logos/private_internet_access.png' width='32' height='32'> Private Internet Access | 3.7-08412 |
| <img src='Logos/privileges.png' width='32' height='32'> Privileges | 2.5.0 |
| <img src='Logos/prizmo.png' width='32' height='32'> Prizmo | 4.7.1 |
| <img src='Logos/processing.png' width='32' height='32'> Processing | 4.5.2 |
| <img src='Logos/processspy.png' width='32' height='32'> ProcessSpy | 1.10.3 |
| <img src='Logos/pronotes.png' width='32' height='32'> ProNotes | 0.7.8.2 |
| <img src='Logos/propresenter.png' width='32' height='32'> ProPresenter | 21.1 |
| <img src='Logos/proton_drive.png' width='32' height='32'> Proton Drive | 2.10.2 |
| <img src='Logos/proton_mail.png' width='32' height='32'> Proton Mail | 1.11.0 |
| <img src='Logos/proton_mail_bridge.png' width='32' height='32'> Proton Mail Bridge | 3.21.2 |
| <img src='Logos/proton_pass.png' width='32' height='32'> Proton Pass | 1.34.1 |
| <img src='Logos/protonvpn.png' width='32' height='32'> ProtonVPN | 6.3.0 |
| <img src='Logos/protopie.png' width='32' height='32'> ProtoPie | 9.0.0 |
| <img src='Logos/proxyman.png' width='32' height='32'> Proxyman | 6.5.0 |
| <img src='Logos/ps_remote_play.png' width='32' height='32'> PS Remote Play | 8.5.2 |
| <img src='Logos/pulsar.png' width='32' height='32'> Pulsar | 1.130.1 |
| <img src='Logos/purevpn.png' width='32' height='32'> PureVPN | 9.38.1 |
| <img src='Logos/pycharm.png' width='32' height='32'> PyCharm | 2025.3.2.1 |
| <img src='Logos/qbittorrent.png' width='32' height='32'> qBittorrent | 5.0.5 |
| <img src='Logos/qgis.png' width='32' height='32'> QGIS | 3.44.7 |
| <img src='Logos/qlab.png' width='32' height='32'> QLab | 5.5.9 |
| <img src='Logos/qobuz.png' width='32' height='32'> Qobuz | 8.1.0 |
| <img src='Logos/qq.png' width='32' height='32'> QQ | 6.9.88 |
| <img src='Logos/qspace_pro.png' width='32' height='32'> QSpace Pro | 6.1.2 |
| <img src='Logos/quarto.png' width='32' height='32'> quarto | 1.8.27 |
| <img src='Logos/quicklook_video.png' width='32' height='32'> QuickLook Video | 2.21 |
| <img src='Logos/quicksilver.png' width='32' height='32'> Quicksilver | 2.5.4 |
| <img src='Logos/qview.png' width='32' height='32'> qView | 7.1 |
| <img src='Logos/radio_silence.png' width='32' height='32'> Radio Silence | 3.3 |
| <img src='Logos/raindropio.png' width='32' height='32'> Raindrop.io | 5.6.95 |
| <img src='Logos/rambox.png' width='32' height='32'> Rambox | 2.5.2 |
| <img src='Logos/rancher_desktop.png' width='32' height='32'> Rancher Desktop | 1.22.0 |
| <img src='Logos/rapidapi.png' width='32' height='32'> RapidAPI | 4.5.4 |
| <img src='Logos/rapidweaver.png' width='32' height='32'> RapidWeaver | 9.6.8 |
| <img src='Logos/raspberry_pi_imager.png' width='32' height='32'> Raspberry Pi Imager | 2.0.6 |
| <img src='Logos/rawtherapee.png' width='32' height='32'> RawTherapee | 5.12 |
| <img src='Logos/raycast.png' width='32' height='32'> Raycast | 1.104.4 |
| <img src='Logos/reactotron.png' width='32' height='32'> Reactotron | 3.8.2 |
| <img src='Logos/readest.png' width='32' height='32'> Readest | 0.9.98 |
| <img src='Logos/real_vnc_viewer.png' width='32' height='32'> Real VNC Viewer | 7.15.1 |
| <img src='Logos/reaper.png' width='32' height='32'> REAPER | 7.60 |
| <img src='Logos/recents.png' width='32' height='32'> Recents | 2.5.0 |
| <img src='Logos/rectangle.png' width='32' height='32'> Rectangle | 0.93 |
| <img src='Logos/rectangle_pro.png' width='32' height='32'> Rectangle Pro | 3.68 |
| <img src='Logos/recut.png' width='32' height='32'> Recut | 4.3.4 |
| <img src='Logos/redis_insight.png' width='32' height='32'> Redis Insight | 2.70.1 |
| <img src='Logos/redispro.png' width='32' height='32'> redis-pro | 3.1.0 |
| <img src='Logos/reflect_notes.png' width='32' height='32'> Reflect Notes | 3.1.7 |
| <img src='Logos/reflector.png' width='32' height='32'> Reflector | 4.1.2 |
| <img src='Logos/reminders_menubar.png' width='32' height='32'> Reminders MenuBar | 1.25.0 |
| <img src='Logos/remnote.png' width='32' height='32'> RemNote | 1.22.77 |
| <img src='Logos/remote_buddy.png' width='32' height='32'> Remote Buddy | 2.7.2 |
| <img src='Logos/remote_desktop_manager.png' width='32' height='32'> Remote Desktop Manager | 2025.3.9.2 |
| <img src='Logos/remote_help.png' width='32' height='32'> Remote Help | 1.0.2509231 |
| <img src='Logos/reqable.png' width='32' height='32'> Reqable | 3.0.38 |
| <img src='Logos/requestly.png' width='32' height='32'> Requestly | 26.1.28 |
| <img src='Logos/resilio_sync.png' width='32' height='32'> Resilio Sync | 3.1.2.1076 |
| <img src='Logos/responsively.png' width='32' height='32'> Responsively | 1.17.1 |
| <img src='Logos/retcon.png' width='32' height='32'> Retcon | 1.5.3 |
| <img src='Logos/retroarch.png' width='32' height='32'> RetroArch | 1.22.2 |
| <img src='Logos/retrobatch.png' width='32' height='32'> Retrobatch | 2.3.1 |
| <img src='Logos/rewind.png' width='32' height='32'> Rewind | 1.5310 |
| <img src='Logos/rewritebar.png' width='32' height='32'> RewriteBar | 2.25.0 |
| <img src='Logos/rhinoceros.png' width='32' height='32'> Rhinoceros | 8.20.25157.13002 |
| <img src='Logos/rightfont.png' width='32' height='32'> RightFont | 9.8 |
| <img src='Logos/ringcentral.png' width='32' height='32'> RingCentral | 25.2.30 |
| <img src='Logos/rive.png' width='32' height='32'> Rive | 0.8.4187 |
| <img src='Logos/riverside_studio.png' width='32' height='32'> Riverside Studio | 1.19.1 |
| <img src='Logos/rize.png' width='32' height='32'> Rize | 2.3.7 |
| <img src='Logos/roam_research.png' width='32' height='32'> Roam Research | 0.0.33 |
| <img src='Logos/roboform.png' width='32' height='32'> RoboForm | 9.9.2 |
| <img src='Logos/rocket.png' width='32' height='32'> Rocket | 1.9.4 |
| <img src='Logos/rocket_typist.png' width='32' height='32'> Rocket Typist | 3.3 |
| <img src='Logos/rocketchat.png' width='32' height='32'> Rocket.Chat | 4.11.2 |
| <img src='Logos/rocketman_choices_packager.png' width='32' height='32'> Rocketman Choices Packager | 1.0.0 |
| <img src='Logos/rode_central.png' width='32' height='32'> Rode Central | 2.0.108 |
| <img src='Logos/rode_connect.png' width='32' height='32'> Rode Connect | 1.3.47 |
| <img src='Logos/roon.png' width='32' height='32'> Roon | 2.58 |
| <img src='Logos/rotato.png' width='32' height='32'> Rotato | 154 |
| <img src='Logos/royal_tsx.png' width='32' height='32'> Royal TSX | 6.3.0.1000 |
| <img src='Logos/rstudio.png' width='32' height='32'> RStudio | 2026.01.0 |
| <img src='Logos/rsyncui.png' width='32' height='32'> RsyncUI | 2.9.0 |
| <img src='Logos/rubymine.png' width='32' height='32'> RubyMine | 2025.3.2 |
| <img src='Logos/runjs.png' width='32' height='32'> RunJS | 3.2.2 |
| <img src='Logos/rustdesk.png' width='32' height='32'> RustDesk | 1.4.5 |
| <img src='Logos/rustrover.png' width='32' height='32'> RustRover | 2025.3.3 |
| <img src='Logos/sabnzbd.png' width='32' height='32'> SABnzbd | 4.5.5 |
| <img src='Logos/safe_exam_browser.png' width='32' height='32'> Safe Exam Browser | 3.6.1 |
| <img src='Logos/salesforce_cli.png' width='32' height='32'> Salesforce CLI | 2.120.3 |
| <img src='Logos/sanesidebuttons.png' width='32' height='32'> SaneSideButtons | 1.4.1 |
| <img src='Logos/santa.png' width='32' height='32'> Santa | 2026.1 |
| <img src='Logos/sbarex_qlmarkdown.png' width='32' height='32'> sbarex QLMarkdown | 1.0.24 |
| <img src='Logos/sc_menu.png' width='32' height='32'> SC Menu | 2.0 |
| <img src='Logos/scratch.png' width='32' height='32'> Scratch | 3.31.1 |
| <img src='Logos/screaming_frog_seo_spider.png' width='32' height='32'> Screaming Frog SEO Spider | 23.2 |
| <img src='Logos/screen_studio.png' width='32' height='32'> Screen Studio | 3.5.2-4162 |
| <img src='Logos/screenflick.png' width='32' height='32'> Screenflick | 3.3.2 |
| <img src='Logos/screenflow.png' width='32' height='32'> ScreenFlow | 10.5.1 |
| <img src='Logos/screenfocus.png' width='32' height='32'> ScreenFocus | 1.1.1 |
| <img src='Logos/screens.png' width='32' height='32'> Screens | 4.12.16 |
| <img src='Logos/scribus.png' width='32' height='32'> Scribus | 1.6.5 |
| <img src='Logos/scrivener.png' width='32' height='32'> Scrivener | 3.5.2 |
| <img src='Logos/scroll_reverser.png' width='32' height='32'> Scroll Reverser | 1.9 |
| <img src='Logos/secretive.png' width='32' height='32'> Secretive | 3.0.4 |
| <img src='Logos/securesafe.png' width='32' height='32'> SecureSafe | 2.25.0 |
| <img src='Logos/selfcontrol.png' width='32' height='32'> SelfControl | 4.0.2 |
| <img src='Logos/sempliva_tiles.png' width='32' height='32'> Sempliva Tiles | 1.3.2 |
| <img src='Logos/send_to_kindle.png' width='32' height='32'> Send to Kindle | 1.1.1.259 |
| <img src='Logos/sensei.png' width='32' height='32'> Sensei | 2.0 |
| <img src='Logos/sentinel.png' width='32' height='32'> Sentinel | 0.40.0 |
| <img src='Logos/sequel_ace.png' width='32' height='32'> Sequel Ace | 5.1.0 |
| <img src='Logos/session.png' width='32' height='32'> Session | 1.17.8 |
| <img src='Logos/session_manager_plugin_for_the_aws_cli.png' width='32' height='32'> Session Manager Plugin for the AWS CLI | 1.2.764.0 |
| <img src='Logos/setapp.png' width='32' height='32'> Setapp | 3.49.7 |
| <img src='Logos/sf_symbols.png' width='32' height='32'> SF Symbols | 7.1 |
| <img src='Logos/shapr3d.png' width='32' height='32'> Shapr3D | 26.0.0.10296 |
| <img src='Logos/shift.png' width='32' height='32'> Shift | 9.6.4.1231 |
| <img src='Logos/shifty.png' width='32' height='32'> Shifty | 1.2 |
| <img src='Logos/shotcut.png' width='32' height='32'> Shotcut | 26.1.30 |
| <img src='Logos/shottr.png' width='32' height='32'> Shottr | 1.9.1 |
| <img src='Logos/shureplus_motiv.png' width='32' height='32'> ShurePlus MOTIV | 1.5.4 |
| <img src='Logos/shutter_encoder.png' width='32' height='32'> Shutter Encoder | 19.8 |
| <img src='Logos/sidenotes.png' width='32' height='32'> SideNotes | 1.5.2 |
| <img src='Logos/sigmaos.png' width='32' height='32'> SigmaOS | 1.19.0.4 |
| <img src='Logos/signal.png' width='32' height='32'> Signal | 7.87.0 |
| <img src='Logos/silentknight.png' width='32' height='32'> SilentKnight | 2.12 |
| <img src='Logos/silhouette_studio.png' width='32' height='32'> Silhouette Studio | 5.0.414.001 |
| <img src='Logos/simple_comic.png' width='32' height='32'> Simple Comic | 1.9.9 |
| <img src='Logos/simpledemviewer.png' width='32' height='32'> SimpleDEMViewer | 8.5.2 |
| <img src='Logos/simplenote.png' width='32' height='32'> Simplenote | 2.24.0 |
| <img src='Logos/sirimote.png' width='32' height='32'> SiriMote | 1.4.5 |
| <img src='Logos/sketch.png' width='32' height='32'> Sketch | 2025.3.4 |
| <img src='Logos/sketchup.png' width='32' height='32'> SketchUp | 2026.0.428.164 |
| <img src='Logos/skim.png' width='32' height='32'> Skim | 1.7.12 |
| <img src='Logos/skype.png' width='32' height='32'> Skype | 8.150.0.125 |
| <img src='Logos/slab.png' width='32' height='32'> Slab | 1.7.2 |
| <img src='Logos/slack.png' width='32' height='32'> Slack | 4.48.86 |
| <img src='Logos/slidepad.png' width='32' height='32'> Slidepad | 1.5.9 |
| <img src='Logos/sloth.png' width='32' height='32'> Sloth | 3.5 |
| <img src='Logos/smartbear_soapui.png' width='32' height='32'> SmartBear SoapUI | 5.9.1 |
| <img src='Logos/smartsheet.png' width='32' height='32'> Smartsheet | 1.0.53 |
| <img src='Logos/smartsvn.png' width='32' height='32'> SmartSVN | 14.5.1 |
| <img src='Logos/smoothscroll.png' width='32' height='32'> SmoothScroll | 1.7.6 |
| <img src='Logos/smultron.png' width='32' height='32'> Smultron | 14.4.5 |
| <img src='Logos/snagit.png' width='32' height='32'> Snagit | 2026.0.0 |
| <img src='Logos/sococo.png' width='32' height='32'> Sococo | 6.12.2 |
| <img src='Logos/sonic_visualiser.png' width='32' height='32'> Sonic Visualiser | 5.2.1 |
| <img src='Logos/sonobus.png' width='32' height='32'> SonoBus | 1.7.2 |
| <img src='Logos/sonos_s2.png' width='32' height='32'> Sonos S2 | 90.0-67171 |
| <img src='Logos/soulver.png' width='32' height='32'> Soulver | 3.15.2 |
| <img src='Logos/sound_control.png' width='32' height='32'> Sound Control | 3.3.3 |
| <img src='Logos/soundanchor.png' width='32' height='32'> SoundAnchor | 1.6.0 |
| <img src='Logos/soundsource.png' width='32' height='32'> SoundSource | 6.0.3 |
| <img src='Logos/spamsieve.png' width='32' height='32'> SpamSieve | 3.2.2 |
| <img src='Logos/sparkle.png' width='32' height='32'> Sparkle | 2.8.1 |
| <img src='Logos/spitfire_audio.png' width='32' height='32'> Spitfire Audio | 3.4.13 |
| <img src='Logos/splashtop_business.png' width='32' height='32'> Splashtop Business | 3.8.0.4 |
| <img src='Logos/splashtop_streamer.png' width='32' height='32'> Splashtop Streamer | 3.8.0.4 |
| <img src='Logos/splice.png' width='32' height='32'> Splice | 5.4.5 |
| <img src='Logos/spline.png' width='32' height='32'> Spline | 0.12.11 |
| <img src='Logos/spotify.png' width='32' height='32'> Spotify | 1.2.82.428 |
| <img src='Logos/sproutcube_shortcat.png' width='32' height='32'> Sproutcube Shortcat | 0.12.2 |
| <img src='Logos/spyder.png' width='32' height='32'> Spyder | 6.1.2 |
| <img src='Logos/sqlectron.png' width='32' height='32'> Sqlectron | 1.39.0 |
| <img src='Logos/sqlpro_for_mssql.png' width='32' height='32'> SQLPro for MSSQL | 2025.10 |
| <img src='Logos/sqlpro_for_mysql.png' width='32' height='32'> SQLPro for MySQL | 2025.10 |
| <img src='Logos/sqlpro_for_postgres.png' width='32' height='32'> SQLPro for Postgres | 2025.06 |
| <img src='Logos/sqlpro_for_sqlite.png' width='32' height='32'> SQLPro for SQLite | 2025.59 |
| <img src='Logos/sqlpro_studio.png' width='32' height='32'> SQLPro Studio | 2025.78 |
| <img src='Logos/squash.png' width='32' height='32'> squash | 3.3.0 |
| <img src='Logos/squirrel.png' width='32' height='32'> Squirrel | 1.0.3 |
| <img src='Logos/ssh_config_editor.png' width='32' height='32'> SSH Config Editor | 2.6.11 |
| <img src='Logos/standard_notes.png' width='32' height='32'> Standard Notes | 3.198.5 |
| <img src='Logos/starface.png' width='32' height='32'> Starface | 9.2.3 |
| <img src='Logos/staruml.png' width='32' height='32'> StarUML | 6.3.4 |
| <img src='Logos/stats.png' width='32' height='32'> Stats | 2.11.66 |
| <img src='Logos/steam.png' width='32' height='32'> Steam | 4.0 |
| <img src='Logos/steermouse.png' width='32' height='32'> SteerMouse | 5.7.7 |
| <img src='Logos/stellarium.png' width='32' height='32'> Stellarium | 25.4 |
| <img src='Logos/stillcolor.png' width='32' height='32'> Stillcolor | 1.1 |
| <img src='Logos/stoplight_studio.png' width='32' height='32'> Stoplight Studio | 2.10.0 |
| <img src='Logos/streamlabs_desktop.png' width='32' height='32'> Streamlabs Desktop | 1.20.6 |
| <img src='Logos/stremio.png' width='32' height='32'> Stremio | 4.4.171 |
| <img src='Logos/stretchly.png' width='32' height='32'> Stretchly | 1.20.0 |
| <img src='Logos/studio.png' width='32' height='32'> Studio | 2.26.1 |
| <img src='Logos/studio_3t.png' width='32' height='32'> Studio 3T | 2026.2.0 |
| <img src='Logos/subethaedit.png' width='32' height='32'> SubEthaEdit | 5.2.4 |
| <img src='Logos/sublime_merge.png' width='32' height='32'> Sublime Merge | 2121 |
| <img src='Logos/sublime_text.png' width='32' height='32'> Sublime Text | 4200 |
| <img src='Logos/sunsama.png' width='32' height='32'> Sunsama | 3.2.6 |
| <img src='Logos/supercollider.png' width='32' height='32'> SuperCollider | 3.14.1 |
| <img src='Logos/superduper.png' width='32' height='32'> SuperDuper! | 3.11 |
| <img src='Logos/superhuman.png' width='32' height='32'> Superhuman | 1038.0.19 |
| <img src='Logos/superkey.png' width='32' height='32'> Superkey | 1.59 |
| <img src='Logos/superlist.png' width='32' height='32'> Superlist | 1.47.2 |
| <img src='Logos/superwhisper.png' width='32' height='32'> superwhisper | 2.9.0 |
| <img src='Logos/support_companion.png' width='32' height='32'> Support Companion | 2.3.1.81039 |
| <img src='Logos/surfshark.png' width='32' height='32'> Surfshark | 4.25.1 |
| <img src='Logos/surge.png' width='32' height='32'> Surge | 6.4.3 |
| <img src='Logos/suspicious_package.png' width='32' height='32'> Suspicious Package | 4.6 |
| <img src='Logos/swift_quit.png' width='32' height='32'> Swift Quit | 1.5 |
| <img src='Logos/swift_shift.png' width='32' height='32'> Swift Shift | 0.27.1 |
| <img src='Logos/swiftbar.png' width='32' height='32'> SwiftBar | 2.0.1 |
| <img src='Logos/swiftdialog.png' width='32' height='32'> swiftDialog | 2.5.6 |
| <img src='Logos/swifty.png' width='32' height='32'> Swifty | 0.6.13 |
| <img src='Logos/swinsian.png' width='32' height='32'> Swinsian | 3.0.5 |
| <img src='Logos/swish.png' width='32' height='32'> Swish | 1.13.2 |
| <img src='Logos/switch_audio_converter.png' width='32' height='32'> Switch Audio Converter | 13.07 |
| <img src='Logos/sync.png' width='32' height='32'> Sync | 2.2.55 |
| <img src='Logos/syncmate.png' width='32' height='32'> SyncMate | 8.10.575 |
| <img src='Logos/syncovery.png' width='32' height='32'> Syncovery | 11.12.2 |
| <img src='Logos/synology_drive.png' width='32' height='32'> Synology Drive | 4.0.2 |
| <img src='Logos/syntax_highlight.png' width='32' height='32'> Syntax Highlight | 2.1.27 |
| <img src='Logos/systhist.png' width='32' height='32'> SystHist | 1.21 |
| <img src='Logos/tabby.png' width='32' height='32'> Tabby | 1.0.230 |
| <img src='Logos/tableau_desktop.png' width='32' height='32'> Tableau Desktop | 2025.3.2 |
| <img src='Logos/tableau_public.png' width='32' height='32'> Tableau Public | 2025.3.2 |
| <img src='Logos/tableau_reader.png' width='32' height='32'> Tableau Reader | 2025.3.2 |
| <img src='Logos/tableplus.png' width='32' height='32'> TablePlus | 6.8.0 |
| <img src='Logos/tabtab.png' width='32' height='32'> TabTab | 2.0.4 |
| <img src='Logos/tabula.png' width='32' height='32'> Tabula | 1.2.1 |
| <img src='Logos/taccy.png' width='32' height='32'> Taccy | 1.15 |
| <img src='Logos/tailscale.png' width='32' height='32'> Tailscale | 1.84.1 |
| <img src='Logos/taskade.png' width='32' height='32'> Taskade | 4.6.13 |
| <img src='Logos/taskbar.png' width='32' height='32'> Taskbar | 1.5.2.1 |
| <img src='Logos/teacode.png' width='32' height='32'> TeaCode | 1.1.3 |
| <img src='Logos/teamviewer.png' width='32' height='32'> TeamViewer | 15.74.3 |
| <img src='Logos/teamviewer_host.png' width='32' height='32'> TeamViewer Host | 15 |
| <img src='Logos/teamviewer_quicksupport.png' width='32' height='32'> TeamViewer QuickSupport | 15 |
| <img src='Logos/techsmith_capture.png' width='32' height='32'> TechSmith Capture | 1.3.31 |
| <img src='Logos/telegram_for_macos.png' width='32' height='32'> Telegram for macOS | 12.4.1 |
| <img src='Logos/tenable_nessus_agent.png' width='32' height='32'> Tenable Nessus Agent | 11.1.1 |
| <img src='Logos/termius.png' width='32' height='32'> Termius | 9.36.2 |
| <img src='Logos/tex_live_utility.png' width='32' height='32'> TeX Live Utility | 1.54 |
| <img src='Logos/texshop.png' width='32' height='32'> TeXShop | 5.57 |
| <img src='Logos/textexpander.png' width='32' height='32'> TextExpander | 8.4.1 |
| <img src='Logos/textmate.png' width='32' height='32'> TextMate | 2.0.23 |
| <img src='Logos/the_unarchiver.png' width='32' height='32'> The Unarchiver | 4.3.9 |
| <img src='Logos/thonny.png' width='32' height='32'> Thonny | 4.1.7 |
| <img src='Logos/threema.png' width='32' height='32'> Threema | 1.2.49 |
| <img src='Logos/thumbsup.png' width='32' height='32'> ThumbsUp | 4.5.3 |
| <img src='Logos/ticktick.png' width='32' height='32'> TickTick | 8.0.10 |
| <img src='Logos/tidal.png' width='32' height='32'> TIDAL | 2.39.5 |
| <img src='Logos/tigervnc.png' width='32' height='32'> TigerVNC | 1.15.0 |
| <img src='Logos/timer.png' width='32' height='32'> Timer | 9.0.3 |
| <img src='Logos/timescribe.png' width='32' height='32'> TimeScribe | 1.9.0 |
| <img src='Logos/timing.png' width='32' height='32'> Timing | 2026.1 |
| <img src='Logos/todoist.png' width='32' height='32'> Todoist | 9.17.0 |
| <img src='Logos/tofu.png' width='32' height='32'> Tofu | 3.0.1 |
| <img src='Logos/tomatobar.png' width='32' height='32'> TomatoBar | 3.5.0 |
| <img src='Logos/topaz_gigapixel_ai.png' width='32' height='32'> Topaz Gigapixel AI | 8.4.4 |
| <img src='Logos/topaz_photo_ai.png' width='32' height='32'> Topaz Photo AI | 4.0.4 |
| <img src='Logos/topaz_video_ai.png' width='32' height='32'> Topaz Video AI | 7.1.5 |
| <img src='Logos/topnotch.png' width='32' height='32'> TopNotch | 1.3.2 |
| <img src='Logos/tor_browser.png' width='32' height='32'> Tor Browser | 15.0.5 |
| ❌ Toshiba ColorMFP Drivers | 7.119.4.0 |
| <img src='Logos/tower.png' width='32' height='32'> Tower | 15.0.3 |
| <img src='Logos/tradingview_desktop.png' width='32' height='32'> TradingView Desktop | 2.14.0 |
| <img src='Logos/trae.png' width='32' height='32'> Trae | 2.3.8290 |
| <img src='Logos/transcribe.png' width='32' height='32'> Transcribe! | 9.50.1 |
| <img src='Logos/transfer.png' width='32' height='32'> Transfer | 2.4.1 |
| <img src='Logos/transmission.png' width='32' height='32'> Transmission | 4.1.0 |
| <img src='Logos/transmit.png' width='32' height='32'> Transmit | 5.11.3 |
| <img src='Logos/transnomino.png' width='32' height='32'> Transnomino | 10.0.0 |
| <img src='Logos/tresorit.png' width='32' height='32'> Tresorit | 3.5.3376.4650 |
| <img src='Logos/trex.png' width='32' height='32'> TRex | 1.9.1 |
| <img src='Logos/trezor_suite.png' width='32' height='32'> TREZOR Suite | 26.1.2 |
| <img src='Logos/tribler.png' width='32' height='32'> Tribler | 8.3.1 |
| <img src='Logos/tripmode.png' width='32' height='32'> TripMode | 3.2.4 |
| <img src='Logos/tumult_hype.png' width='32' height='32'> Tumult Hype | 4.1.20 |
| <img src='Logos/tunnelbear.png' width='32' height='32'> TunnelBear | 5.8.1 |
| <img src='Logos/tunnelblick.png' width='32' height='32'> Tunnelblick | 8.0 |
| <img src='Logos/tuple.png' width='32' height='32'> Tuple | 2.3.0 |
| <img src='Logos/tuta_mail.png' width='32' height='32'> Tuta Mail | 325.260127.0 |
| <img src='Logos/twingate.png' width='32' height='32'> Twingate | 2025.363.22082 |
| <img src='Logos/twitch_studio.png' width='32' height='32'> Twitch Studio | 0.114.8 |
| <img src='Logos/typeface.png' width='32' height='32'> Typeface | 4.2.3 |
| <img src='Logos/typinator.png' width='32' height='32'> Typinator | 9.2 |
| <img src='Logos/typora.png' width='32' height='32'> Typora | 1.12.6 |
| <img src='Logos/ubar.png' width='32' height='32'> uBar | 4.2.3 |
| <img src='Logos/ukelele.png' width='32' height='32'> Ukelele | 3.6.0 |
| <img src='Logos/ultimaker_cura.png' width='32' height='32'> UltiMaker Cura | 5.11.0 |
| <img src='Logos/unclutter.png' width='32' height='32'> Unclutter | 2.1.25d |
| <img src='Logos/ungoogled_chromium.png' width='32' height='32'> Ungoogled Chromium | 144.0.7559.96-1.1 |
| <img src='Logos/unicodechecker.png' width='32' height='32'> UnicodeChecker | 1.25.1 |
| <img src='Logos/unite.png' width='32' height='32'> Unite | 6.5 |
| <img src='Logos/unity_hub.png' width='32' height='32'> Unity Hub | 3.16.1 |
| <img src='Logos/unnaturalscrollwheels.png' width='32' height='32'> UnnaturalScrollWheels | 1.3.0 |
| <img src='Logos/updf.png' width='32' height='32'> UPDF | 2.1.2 |
| <img src='Logos/upscayl.png' width='32' height='32'> Upscayl | 2.15.0 |
| <img src='Logos/utm.png' width='32' height='32'> UTM | 4.7.5 |
| <img src='Logos/vanilla.png' width='32' height='32'> Vanilla | 2.2 |
| <img src='Logos/vellum.png' width='32' height='32'> Vellum | 4.0.2 |
| <img src='Logos/veracrypt.png' width='32' height='32'> VeraCrypt | 1.26.24 |
| <img src='Logos/versions.png' width='32' height='32'> Versions | 2.4.4 |
| <img src='Logos/via.png' width='32' height='32'> VIA | 3.0.0 |
| <img src='Logos/vimcal.png' width='32' height='32'> Vimcal | 1.0.42 |
| <img src='Logos/vimr.png' width='32' height='32'> VimR | 0.60.0 |
| <img src='Logos/virtualbuddy.png' width='32' height='32'> VirtualBuddy | 2.1 |
| <img src='Logos/viscosity.png' width='32' height='32'> Viscosity | 1.12 |
| <img src='Logos/visual_paradigm.png' width='32' height='32'> Visual Paradigm | 18.0 |
| <img src='Logos/visualvm.png' width='32' height='32'> VisualVM | 2.2 |
| <img src='Logos/vivaldi.png' width='32' height='32'> Vivaldi | 7.8.3925.56 |
| <img src='Logos/viz.png' width='32' height='32'> Viz | 2.3.3 |
| <img src='Logos/vlc_media_player.png' width='32' height='32'> VLC media player | 3.0.23 |
| <img src='Logos/vmware_fusion.png' width='32' height='32'> VMware Fusion | 13.6.3 |
| <img src='Logos/vnote.png' width='32' height='32'> VNote | 3.20.1 |
| <img src='Logos/vox.png' width='32' height='32'> VOX | 3.7.7 |
| <img src='Logos/vpn_tracker_365.png' width='32' height='32'> VPN Tracker 365 | 26.1 |
| <img src='Logos/vscodium.png' width='32' height='32'> VSCodium | 1.108.20787 |
| <img src='Logos/vuescan.png' width='32' height='32'> VueScan | 9.8.50 |
| <img src='Logos/vyprvpn.png' width='32' height='32'> VyprVPN | 6.0.4.11438 |
| <img src='Logos/vysor.png' width='32' height='32'> Vysor | 5.0.7 |
| ❌ Wacom Tablet | 6.4.12-3 |
| <img src='Logos/warp.png' width='32' height='32'> Warp | 0.2026.01.28.08.14.stable |
| <img src='Logos/waterfox.png' width='32' height='32'> Waterfox | 6.6.8 |
| <img src='Logos/wave_terminal.png' width='32' height='32'> Wave Terminal | 0.13.1 |
| <img src='Logos/wavebox.png' width='32' height='32'> Wavebox | 10.144.72.2 |
| <img src='Logos/wealthfolio.png' width='32' height='32'> Wealthfolio | 2.1.0 |
| <img src='Logos/weasis.png' width='32' height='32'> Weasis | 4.6.6 |
| <img src='Logos/webcatalog.png' width='32' height='32'> WebCatalog | 73.4.0 |
| <img src='Logos/webex.png' width='32' height='32'> Webex | 46.1.0.33913 |
| <img src='Logos/webex_teams.png' width='32' height='32'> Webex Teams | 45.6.1.32593 |
| <img src='Logos/webstorm.png' width='32' height='32'> WebStorm | 2025.3.2 |
| <img src='Logos/wechat_for_mac.png' width='32' height='32'> WeChat for Mac | 4.1.7.31 |
| <img src='Logos/weektodo.png' width='32' height='32'> WeekToDo | 2.2.0 |
| <img src='Logos/wezterm.png' width='32' height='32'> WezTerm | 20240203-110809 |
| <img src='Logos/whatroute.png' width='32' height='32'> WhatRoute | 2.7.2 |
| <img src='Logos/whatsapp.png' width='32' height='32'> WhatsApp | 2.26.5.17 |
| <img src='Logos/whatsize.png' width='32' height='32'> WhatSize | 8.2.4 |
| <img src='Logos/whimsical.png' width='32' height='32'> Whimsical | 0.4.3 |
| <img src='Logos/whisky.png' width='32' height='32'> Whisky | 2.3.5 |
| <img src='Logos/whispering.png' width='32' height='32'> Whispering | 7.11.0 |
| <img src='Logos/windowkeys.png' width='32' height='32'> WindowKeys | 3.0.1 |
| <img src='Logos/windows_app.png' width='32' height='32'> Windows App | 11.3.2 |
| <img src='Logos/windsurf.png' width='32' height='32'> Windsurf | 1.9544.26 |
| <img src='Logos/winehqstable.png' width='32' height='32'> WineHQ-stable | 11.0 |
| <img src='Logos/wins.png' width='32' height='32'> Wins | 3.1.1 |
| <img src='Logos/wire.png' width='32' height='32'> Wire | 3.40.5442 |
| <img src='Logos/wirecast.png' width='32' height='32'> Wirecast | 16.5.0 |
| <img src='Logos/wireshark.png' width='32' height='32'> Wireshark | 4.4.7 |
| <img src='Logos/witch.png' width='32' height='32'> Witch | 4.7.0 |
| <img src='Logos/wondershare_filmora.png' width='32' height='32'> Wondershare Filmora | 13.0.25 |
| <img src='Logos/wordservice.png' width='32' height='32'> WordService | 2.8.3 |
| <img src='Logos/workflowy.png' width='32' height='32'> WorkFlowy | 4.3.2602020824 |
| <img src='Logos/workspaces.png' width='32' height='32'> Workspaces | 2.1.5 |
| <img src='Logos/x_lossless_decoder.png' width='32' height='32'> X Lossless Decoder | 20250302 |
| <img src='Logos/xattred.png' width='32' height='32'> xattred | 1.7 |
| <img src='Logos/xca.png' width='32' height='32'> XCA | 2.9.0 |
| <img src='Logos/xmenu.png' width='32' height='32'> XMenu | 1.9.11 |
| <img src='Logos/xmind.png' width='32' height='32'> XMind | 26.02.02052-202601211723 |
| <img src='Logos/xmplify.png' width='32' height='32'> Xmplify | 1.11.10 |
| <img src='Logos/xnapper.png' width='32' height='32'> Xnapper | 1.17.1 |
| <img src='Logos/xnsoft_xnconvert.png' width='32' height='32'> XnSoft XnConvert | 1.106.0 |
| <img src='Logos/xnviewmp.png' width='32' height='32'> XnViewMP | 1.9.10 |
| <img src='Logos/xquartz.png' width='32' height='32'> XQuartz | 2.8.5 |
| <img src='Logos/yaak.png' width='32' height='32'> Yaak | 2026.1.2 |
| <img src='Logos/yacreader.png' width='32' height='32'> YACReader | 9.16.3.26010361 |
| <img src='Logos/yattee.png' width='32' height='32'> Yattee | 1.5.1 |
| <img src='Logos/yippy.png' width='32' height='32'> Yippy | 2.8.1 |
| <img src='Logos/yoink.png' width='32' height='32'> Yoink | 3.6.109 |
| <img src='Logos/yubico_authenticator.png' width='32' height='32'> Yubico Authenticator | 7.3.0 |
| <img src='Logos/yubikey_manager.png' width='32' height='32'> Yubikey Manager | 1.2.5 |
| <img src='Logos/yworks_yed.png' width='32' height='32'> yWorks yEd | 3.25.1 |
| <img src='Logos/zappy.png' width='32' height='32'> Zappy | 4.9.3 |
| <img src='Logos/zed.png' width='32' height='32'> Zed | 0.221.5 |
| <img src='Logos/zed_attack_proxy.png' width='32' height='32'> Zed Attack Proxy | 2.17.0 |
| <img src='Logos/zen_browser.png' width='32' height='32'> Zen Browser | 1.12.3b |
| <img src='Logos/zeplin.png' width='32' height='32'> Zeplin | 10.30.0 |
| <img src='Logos/zettlr.png' width='32' height='32'> Zettlr | 4.1.1 |
| <img src='Logos/zight.png' width='32' height='32'> Zight | 8.6.0 |
| <img src='Logos/zoom.png' width='32' height='32'> Zoom | 6.7.2.72191 |
| <img src='Logos/zotero.png' width='32' height='32'> Zotero | 8.0.1 |
| <img src='Logos/zulip.png' width='32' height='32'> Zulip | 5.12.3 |
| <img src='Logos/zwift.png' width='32' height='32'> Zwift | 1.1.14 |

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

### Azure Automation Variables

The following automation variables can be configured in your Azure Automation Account:

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `AuthenticationMethod` | String | Yes | - | Authentication method: `SystemManagedIdentity`, `UserAssignedManagedIdentity`, or `ClientSecret` |
| `TenantId` | String | For ClientSecret | - | Azure AD Tenant ID |
| `AppId` | String | For ClientSecret/UserAssigned | - | Application/Client ID |
| `ClientSecret` | String | For ClientSecret | - | Client Secret value (not the ID) |
| `CopyAssignments` | Boolean | No | false | Copy assignments from old app version to new version |
| `UseExistingIntuneApp` | Boolean | No | false | Update existing apps instead of creating new ones (preserves assignments) |
| `MaxAppsPerRun` | Integer | No | 10 | Maximum apps to process per run (prevents memory issues in Azure sandbox) |

**Notes:**
- When `UseExistingIntuneApp` is `true`, `CopyAssignments` is automatically ignored (assignments are preserved on the existing app)
- `MaxAppsPerRun` helps prevent the Azure Automation sandbox from suspending due to the 1GB memory limit

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

## Automated Workflows

IntuneBrew uses a chain of GitHub Actions workflows to automate app management. Here's how the pipeline works:

### Workflow Chain

```
App Request Approved
        |
        v
[1] Auto-Approve App Request
    - Validates the app from Homebrew
    - Adds app URL to collect_app_info.py
    - Commits and pushes changes
        |
        v
[2] Build App Packages
    - Collects app information from Homebrew
    - Downloads and repackages apps (DMG/ZIP to PKG)
    - Uploads packages to Azure Blob Storage
    - Updates Apps/*.json with version info
    - Generates supported_apps.json
    - Updates README app count badge
        |
        +------------------+
        |                  |
        v                  v
[3a] Fetch App Icons   [3b] Update Version Database
    - Downloads missing      - Syncs versions to Supabase
      app icons from         - Sends notifications to
      Brandfetch API           subscribed users
    - Commits to Logos/          |
                                 v
                        [4] Generate Uninstall Scripts
                            - Creates PowerShell uninstall
                              scripts for each app
                            - Commits to Uninstall Scripts/
```

### Workflow Details

| Workflow | Trigger | What It Does |
|----------|---------|--------------|
| **Auto-Approve App Request** | `/.approve` comment or `auto-approved` label | Validates and adds new apps to the supported list |
| **Build App Packages** | Push to `collect_app_info.py`, daily schedule, or manual | Downloads apps, creates PKG files, uploads to Azure |
| **Fetch App Icons** | After Build App Packages completes | Downloads missing app logos from Brandfetch |
| **Update Version Database** | After Build App Packages completes | Updates Supabase with version info, sends notifications |
| **Generate Uninstall Scripts** | After Update Version Database completes | Creates PowerShell uninstall scripts for Intune |

### Other Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| **Categorize Apps** | Daily or on app changes | Uses AI to categorize apps |
| **Check App CVEs** | Daily at 6 AM UTC | Scans for security vulnerabilities |
| **QA App Installation** | Manual only | Tests app installations on macOS |
| **PSScriptAnalyzer** | On IntuneBrew.ps1 changes | Lints PowerShell code |
| **Send Weekly Reports** | Mondays at 8 AM UTC | Sends fleet summary reports |

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
