import json
import os
import requests
import re
import fileinput
from pathlib import Path
import subprocess
from datetime import datetime

# Array of Homebrew cask JSON URLs
app_urls = [
    "https://formulae.brew.sh/api/cask/visual-studio-code.json",
    "https://formulae.brew.sh/api/cask/microsoft-azure-storage-explorer.json",
    "https://formulae.brew.sh/api/cask/figma.json",
    "https://formulae.brew.sh/api/cask/postman.json",
    "https://formulae.brew.sh/api/cask/fantastical.json",
    "https://formulae.brew.sh/api/cask/iterm2.json",
    "https://formulae.brew.sh/api/cask/sublime-text.json",
    "https://formulae.brew.sh/api/cask/vivaldi.json",
    "https://formulae.brew.sh/api/cask/github.json",
    "https://formulae.brew.sh/api/cask/transmit.json",
    "https://formulae.brew.sh/api/cask/1password.json",
    "https://formulae.brew.sh/api/cask/alfred.json",
    "https://formulae.brew.sh/api/cask/asana.json",
    "https://formulae.brew.sh/api/cask/deepl.json"
]

homebrew_cask_urls = [
    "https://formulae.brew.sh/api/cask/google-chrome.json",
    "https://formulae.brew.sh/api/cask/zoom.json",
    "https://formulae.brew.sh/api/cask/firefox.json",
    "https://formulae.brew.sh/api/cask/slack.json",
    "https://formulae.brew.sh/api/cask/microsoft-teams.json",
    "https://formulae.brew.sh/api/cask/spotify.json",
    "https://formulae.brew.sh/api/cask/intune-company-portal.json",
    "https://formulae.brew.sh/api/cask/adobe-acrobat-reader.json",
    "https://formulae.brew.sh/api/cask/windows-app.json",
    "https://formulae.brew.sh/api/cask/parallels.json",
    "https://formulae.brew.sh/api/cask/keepassxc.json",
    "https://formulae.brew.sh/api/cask/synology-drive.json",
    "https://formulae.brew.sh/api/cask/grammarly-desktop.json",
    "https://formulae.brew.sh/api/cask/todoist.json",
    "https://formulae.brew.sh/api/cask/xmind.json",
    "https://formulae.brew.sh/api/cask/docker.json",
    "https://formulae.brew.sh/api/cask/vlc.json",
    "https://formulae.brew.sh/api/cask/bitwarden.json",
    "https://formulae.brew.sh/api/cask/miro.json",
    "https://formulae.brew.sh/api/cask/snagit.json",
    "https://formulae.brew.sh/api/cask/canva.json",
    "https://formulae.brew.sh/api/cask/blender.json",
    "https://formulae.brew.sh/api/cask/webex.json",
    "https://formulae.brew.sh/api/cask/mongodb-compass.json",
    "https://formulae.brew.sh/api/cask/suspicious-package.json",
    "https://formulae.brew.sh/api/cask/teamviewer-quicksupport.json",
    "https://formulae.brew.sh/api/cask/notion.json",
    "https://formulae.brew.sh/api/cask/signal.json",
    "https://formulae.brew.sh/api/cask/adobe-acrobat-pro.json",
    "https://formulae.brew.sh/api/cask/adobe-creative-cloud.json",
    "https://formulae.brew.sh/api/cask/anydesk.json",
    "https://formulae.brew.sh/api/cask/android-studio.json",
    "https://formulae.brew.sh/api/cask/brave-browser.json",
    "https://formulae.brew.sh/api/cask/evernote.json",
    "https://formulae.brew.sh/api/cask/dropbox.json",
    "https://formulae.brew.sh/api/cask/krisp.json",
    "https://formulae.brew.sh/api/cask/obsidian.json",
    "https://formulae.brew.sh/api/cask/rstudio.json",
    "https://formulae.brew.sh/api/cask/utm.json",
    "https://formulae.brew.sh/api/cask/tableau.json",
    "https://formulae.brew.sh/api/cask/vnc-viewer.json",
    "https://formulae.brew.sh/api/cask/powershell.json",
    "https://formulae.brew.sh/api/cask/betterdisplay.json",
    "https://formulae.brew.sh/api/cask/orbstack.json",
    "https://formulae.brew.sh/api/cask/capcut.json",
    "https://formulae.brew.sh/api/cask/bbedit.json",
    "https://formulae.brew.sh/api/cask/termius.json",
    "https://formulae.brew.sh/api/cask/corretto@21.json",
    "https://formulae.brew.sh/api/cask/anki.json"
]

# Custom scraper scripts to run
custom_scrapers = [
    ".github/scripts/scrapers/remotehelp.sh",
]

def find_bundle_id(json_string):
    regex_patterns = {
        'pkgutil': r'(?s)"pkgutil"\s*:\s*(?:\[\s*"([^"]+)"(?:,\s*"([^"]+)")?\s*\]|\s*"([^"]+)")',
        'quit': r'(?s)"quit"\s*:\s*(?:\[\s*"([^"]+)"(?:,\s*"([^"]+)")?\s*\]|\s*"([^"]+)")',
        'launchctl': r'(?s)"launchctl"\s*:\s*(?:\[\s*"([^"]+)"(?:,\s*"([^"]+)")?\s*\]|\s*"([^"]+)")'
    }

    for key, pattern in regex_patterns.items():
        match = re.search(pattern, json_string)
        if match:
            if match.group(1):
                return match.group(1)
            elif match.group(3):
                return match.group(3)

    return None

def get_homebrew_app_info(json_url, needs_packaging=False):
    response = requests.get(json_url)
    response.raise_for_status()
    data = response.json()
    json_string = json.dumps(data)

    bundle_id = find_bundle_id(json_string)

    app_info = {
        "name": data["name"][0],
        "description": data["desc"],
        "version": data["version"],
        "url": data["url"],
        "bundleId": bundle_id,
        "homepage": data["homepage"],
        "fileName": os.path.basename(data["url"])
    }
    
    if needs_packaging:
        app_info["type"] = "app"
    
    return app_info

def sanitize_filename(name):
    sanitized = name.replace(' ', '_')
    sanitized = re.sub(r'[^\w_]', '', sanitized)
    return sanitized.lower()

def update_readme_apps(apps_list):
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    logos_path = Path(__file__).parent.parent.parent / "Logos"
    if not readme_path.exists():
        print("README.md not found")
        return

    print(f"\n📋 Checking logos for all apps...")
    print(f"Looking in: {logos_path}\n")

    # Read all app JSON files to get versions
    apps_folder = Path(__file__).parent.parent.parent / "Apps"
    apps_info = []
    missing_logos = []
    
    for app_json in apps_folder.glob("*.json"):
        # Read the JSON file to get the display name
        with open(app_json, 'r') as f:
            try:
                data = json.load(f)
                display_name = data['name']
                # Convert display name to filename format
                logo_name = sanitize_filename(display_name)
                
                # Look for matching logo file (trying both .png and .ico)
                logo_file = None
                for ext in ['.png', '.ico']:
                    # Case-insensitive search for logo files
                    potential_logos = [f for f in os.listdir(logos_path) 
                                     if f.lower() == f"{logo_name}{ext}".lower()]
                    if potential_logos:
                        logo_file = f"Logos/{potential_logos[0]}"
                        break
                
                if not logo_file:
                    missing_logos.append(display_name)

                apps_info.append({
                    'name': display_name,
                    'version': data['version'],
                    'logo': logo_file
                })
            except Exception as e:
                print(f"Error reading {app_json}: {e}")

    # Print missing logos summary
    if missing_logos:
        print("❌ Missing logos for the following apps:")
        for app in missing_logos:
            print(f"   - {app}")
        print("\nExpected logo files (case-insensitive):")
        for app in missing_logos:
            logo_name = sanitize_filename(app)
            print(f"   - {logo_name}.png or {logo_name}.ico")
        print("\n")
    else:
        print("✅ All apps have logos!\n")

    # Sort apps by name
    apps_info.sort(key=lambda x: x['name'].lower())

    # Create the new table content
    table_content = """### 📱 Supported Applications

| Application | Latest Version |
|-------------|----------------|
"""
    
    for app in apps_info:
        logo_cell = f"<img src='{app['logo']}' width='32' height='32'>" if app['logo'] else "❌"
        table_content += f"| {logo_cell} {app['name']} | {app['version']} |\n"

    # Add note about requesting new apps
    table_content += "\n> [!NOTE]\n"
    table_content += "> Missing an app? Feel free to [request additional app support]"
    table_content += "(https://github.com/ugurkocde/IntuneBrew/issues/new?labels=app-request) by creating an issue!\n"

    # Read the entire README
    with open(readme_path, 'r') as f:
        content = f.read()

    # Find the supported applications section using the correct marker
    start_marker = "### 📱 Supported Applications"
    end_marker = "## 🔧 Configuration"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("Couldn't find the markers in README.md")
        print(f"Start marker found: {start_idx != -1}")
        print(f"End marker found: {end_idx != -1}")
        return

    # Construct the new content
    new_content = (
        content[:start_idx] +
        table_content +
        "\n" +
        content[end_idx:]
    )

    # Write the updated content back to README.md
    with open(readme_path, 'w') as f:
        f.write(new_content)
    print("README.md has been updated with the new table format including logos")

def update_readme_with_latest_changes(apps_info):
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    
    # Read current README content
    with open(readme_path, 'r') as f:
        content = f.read()

    # Prepare the updates section
    updates_section = "\n## 🔄 Latest Updates\n\n"
    updates_section += f"*Last checked: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*\n\n"

    # Get version changes
    version_changes = []
    for app in apps_info:
        try:
            with open(f"Apps/{sanitize_filename(app['name'])}.json", 'r') as f:
                current_data = json.load(f)
                if 'previous_version' in current_data and current_data['version'] != current_data['previous_version']:
                    version_changes.append({
                        'name': app['name'],
                        'old_version': current_data['previous_version'],
                        'new_version': current_data['version']
                    })
        except Exception as e:
            print(f"Error checking version history for {app['name']}: {e}")

    if version_changes:
        updates_section += "| Application | Previous Version | New Version |\n"
        updates_section += "|-------------|-----------------|-------------|\n"
        for change in version_changes:
            updates_section += f"| {change['name']} | {change['old_version']} | {change['new_version']} |\n"
    else:
        updates_section += "> All applications are up to date! 🎉\n"

    # Find where to insert the updates section (after the Public Preview notice)
    preview_notice_end = "Thank you for being an early adopter! 🙏"
    features_section = "## ✨ Features"
    
    if preview_notice_end in content and features_section in content:
        parts = content.split(preview_notice_end, 1)
        if len(parts) == 2:
            second_parts = parts[1].split(features_section, 1)
            if len(second_parts) == 2:
                # Remove existing updates section if it exists
                if "## 🔄 Latest Updates" in second_parts[0]:
                    second_parts[0] = "\n\n"
                
                # Construct new content with updates section in the new location
                new_content = (
                    parts[0] + 
                    preview_notice_end + 
                    "\n\n" +
                    updates_section +
                    features_section +
                    second_parts[1]
                )
                
                # Write the updated content back to README.md
                with open(readme_path, 'w') as f:
                    f.write(new_content)
                return
    
    print("Could not find the correct location to insert the updates section")

def main():
    apps_folder = "Apps"
    os.makedirs(apps_folder, exist_ok=True)
    print(f"\n📁 Apps folder absolute path: {os.path.abspath(apps_folder)}")
    print(f"📁 Apps folder exists: {os.path.exists(apps_folder)}")
    print(f"📁 Apps folder is writable: {os.access(apps_folder, os.W_OK)}\n")
    
    supported_apps = []
    apps_info = []

    # Process apps that need special packaging
    for url in app_urls:
        try:
            print(f"\nProcessing special app URL: {url}")
            app_info = get_homebrew_app_info(url, needs_packaging=True)
            display_name = app_info['name']
            print(f"Got app info for: {display_name}")
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            print(f"🔍 Sanitized filename: {file_name}")
            file_path = os.path.join(apps_folder, file_name)
            print(f"📝 Attempting to write to: {os.path.abspath(file_path)}")

            # Store previous version and preserve existing bundle ID if file exists
            if os.path.exists(file_path):
                print(f"Found existing file for {display_name}")
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    app_info["previous_version"] = existing_data.get("version")
                    # Preserve existing bundle ID if it exists
                    if existing_data.get("bundleId"):
                        app_info["bundleId"] = existing_data["bundleId"]

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)
                print(f"Successfully wrote {file_path} with type 'app' flag")

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing special app {url}: {str(e)}")
            print(f"Full error details: ", e)

    # Process regular Homebrew cask URLs
    for url in homebrew_cask_urls:
        try:
            app_info = get_homebrew_app_info(url)
            display_name = app_info['name']
            supported_apps.append(display_name)
            file_name = f"{sanitize_filename(display_name)}.json"
            file_path = os.path.join(apps_folder, file_name)

            # Store previous version if file exists
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    app_info["previous_version"] = existing_data.get("version")
                    if existing_data.get("bundleId") and app_info["bundleId"] is None:
                        app_info["bundleId"] = existing_data["bundleId"]

            with open(file_path, "w") as f:
                json.dump(app_info, f, indent=2)

            apps_info.append(app_info)
            print(f"Saved app information for {display_name} to {file_path}")
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")

    # Run custom scrapers and update apps_info accordingly
    for scraper in custom_scrapers:
        try:
            subprocess.run([scraper], check=True)
            # Get the app name from the JSON file created by the scraper
            json_file = os.path.join(apps_folder, os.path.basename(scraper).replace('.sh', '.json'))
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    app_data = json.load(f)
                    supported_apps.append(app_data['name'])
        except Exception as e:
            print(f"Error running scraper {scraper}: {str(e)}")

    # Update the README with both the apps table and latest changes
    update_readme_apps(supported_apps)
    update_readme_with_latest_changes(apps_info)

if __name__ == "__main__":
    main()
