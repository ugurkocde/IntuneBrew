# Catalog support and package details

## Architecture

IntuneBrew uses each Homebrew cask's published macOS download metadata. Architecture is app-specific: a package may be Apple Silicon, Intel, or universal. Do not assume every package supports both architectures. The Visual Studio Code cask currently selects the Apple Silicon download (`darwin-arm64`); it is not an Intel-specific package. Check the vendor download and bundle requirements before assigning an app to an Intel fleet.

## Downloads and versions

Use the current [catalog](https://www.intunebrew.com/apps) or [public API](https://www.intunebrew.com/api-docs) rather than saving an installer link permanently. Chrome, VLC, and Warp are supported. Vendor evergreen URLs may change their bytes without changing the URL, so the collector refreshes checksums during collection. Validate the downloaded artifact against the current manifest's `sha` before deployment. A mismatch must be investigated rather than bypassed.

DDPM (Dell Display and Peripheral Manager), Supremo, and Tableau Prep are available under catalog IDs `ddpm`, `supremo`, and `tableau_prep`. DDPM and Tableau Prep use published PKG artifacts; Supremo uses its vendor DMG. App metadata and vendor prerequisites remain the authority for device compatibility.

The PowerShell CLI and runbook compare version segments without the four-segment limit of .NET's Version type. Versions such as `6.10.0.252.3` and `21.0.8.9.1` are supported.

## Icons

Icons extracted from vendor bundles retain their transparency when resized to PNG. Palette transparency and RGB transparency keys are expanded before resizing so transparent edges remain transparent. An opaque background that is part of the vendor artwork is preserved; removing every white pixel would damage some logos.

## Retired or blocked applications

A removed Homebrew cask is excluded instead of being silently mapped to a similarly named, unrelated app. Historical JSON records remain marked deprecated. Reintroduction requires validating the actual replacement cask and installer. See [excluded applications](../EXCLUDED_APPS.md) for active exclusions, including installers requiring explicit vendor license acceptance.

FileZilla is intentionally excluded from the supported catalog and automated packaging. Re-enabling it requires an explicit decision and a maintained official macOS installer source suitable for unattended download. A time-limited signed download link is not enough for a daily synchronizer. A future source must provide stable version detection, architecture information, and a verifiable installer; license prompts must not be accepted automatically.
