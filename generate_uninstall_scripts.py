#!/usr/bin/env python3
import json
import os
import requests
import re
from pathlib import Path
import sys

# Create Uninstall Scripts directory if it doesn't exist
uninstall_dir = "Uninstall Scripts"
os.makedirs(uninstall_dir, exist_ok=True)

def get_brew_app_info(app_name):
    """Fetch application information from brew.sh API"""
    # Convert app name to brew.sh format (lowercase, hyphens instead of spaces)
    brew_name = app_name.lower().replace(' ', '-')
    json_url = f"https://formulae.brew.sh/api/cask/{brew_name}.json"
    
    print(f"Fetching information for {app_name} from {json_url}")
    try:
        response = requests.get(json_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {json_url}: {str(e)}")
        # Try alternative URL formats
        alternative_formats = [
            f"https://formulae.brew.sh/api/cask/{brew_name.replace('-', '')}.json",
            f"https://formulae.brew.sh/api/cask/{brew_name.replace('-', '_')}.json"
        ]
        
        for alt_url in alternative_formats:
            try:
                print(f"Trying alternative URL: {alt_url}")
                response = requests.get(alt_url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                continue
        
        print(f"Could not find brew.sh data for {app_name}")
        return None

def extract_uninstall_paths(app_data):
    """Extract paths that need to be removed during uninstallation"""
    uninstall_paths = []
    
    # Extract app bundle path
    if "artifacts" in app_data:
        for artifact in app_data["artifacts"]:
            # Handle string artifacts (usually app bundles)
            if isinstance(artifact, str) and artifact.endswith(".app"):
                uninstall_paths.append(f"/Applications/{artifact}")
            
            # Handle dictionary artifacts
            elif isinstance(artifact, dict):
                # Handle app artifacts
                if "app" in artifact:
                    app_path = artifact["app"]
                    if isinstance(app_path, list):
                        for app in app_path:
                            uninstall_paths.append(f"/Applications/{app}")
                    else:
                        uninstall_paths.append(f"/Applications/{app_path}")
                
                # Handle zap artifacts
                if "zap" in artifact:
                    zap_data = artifact["zap"]
                    if isinstance(zap_data, list):
                        for zap_item in zap_data:
                            if isinstance(zap_item, dict) and "trash" in zap_item:
                                trash_paths = zap_item["trash"]
                                if isinstance(trash_paths, list):
                                    for path in trash_paths:
                                        uninstall_paths.append(path)
                                else:
                                    uninstall_paths.append(trash_paths)
    
    # Extract pkgutil IDs
    if "pkgutil" in app_data:
        pkgutil_ids = app_data["pkgutil"]
        if isinstance(pkgutil_ids, list):
            for pkg_id in pkgutil_ids:
                uninstall_paths.append(f"PKGUTIL:{pkg_id}")
        else:
            uninstall_paths.append(f"PKGUTIL:{pkgutil_ids}")
    
    # Extract launchctl services
    if "launchctl" in app_data:
        launchctl_services = app_data["launchctl"]
        if isinstance(launchctl_services, list):
            for service in launchctl_services:
                uninstall_paths.append(f"LAUNCHCTL:{service}")
        else:
            uninstall_paths.append(f"LAUNCHCTL:{launchctl_services}")
    
    # Extract quit IDs (bundle IDs)
    if "quit" in app_data:
        quit_ids = app_data["quit"]
        if isinstance(quit_ids, list):
            for quit_id in quit_ids:
                uninstall_paths.append(f"BUNDLE:{quit_id}")
        else:
            uninstall_paths.append(f"BUNDLE:{quit_ids}")
    
    # Common locations for application data
    app_name = app_data["name"][0] if isinstance(app_data["name"], list) else app_data["name"]
    bundle_id = None
    
    # Try to extract bundle ID
    if "bundle_id" in app_data:
        bundle_id = app_data["bundle_id"]
    elif "quit" in app_data and isinstance(app_data["quit"], str):
        bundle_id = app_data["quit"]
    elif "quit" in app_data and isinstance(app_data["quit"], list) and len(app_data["quit"]) > 0:
        bundle_id = app_data["quit"][0]
    
    if bundle_id:
        # Add common paths for application data
        uninstall_paths.append(f"~/Library/Application Support/{app_name}")
        uninstall_paths.append(f"~/Library/Caches/{bundle_id}")
        uninstall_paths.append(f"~/Library/Preferences/{bundle_id}.plist")
        uninstall_paths.append(f"~/Library/Saved Application State/{bundle_id}.savedState")
    
    return uninstall_paths

def generate_uninstall_script(app_name, uninstall_paths):
    """Generate a shell script to uninstall the application"""
    script_content = f"""#!/bin/bash
# Uninstall script for {app_name}
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling {app_name}..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping {app_name} if running..."
pkill -f "{app_name}" 2>/dev/null || true
"""

    # Add commands to remove files and directories
    for path in uninstall_paths:
        if path.startswith("PKGUTIL:"):
            pkg_id = path.replace("PKGUTIL:", "")
            script_content += f"""
# Remove package {pkg_id}
echo "Removing package {pkg_id}..."
pkgutil --forget {pkg_id} 2>/dev/null || true
"""
        elif path.startswith("LAUNCHCTL:"):
            service = path.replace("LAUNCHCTL:", "")
            script_content += f"""
# Unload service {service}
echo "Unloading service {service}..."
launchctl unload -w /Library/LaunchAgents/{service}.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/{service}.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/{service}.plist 2>/dev/null || true
"""
        elif path.startswith("BUNDLE:"):
            # Bundle IDs are just for reference, no action needed
            pass
        else:
            # Expand ~ to $HOME
            if path.startswith("~"):
                path = "$HOME" + path[1:]
            
            script_content += f"""
# Remove {path}
echo "Removing {path}..."
if [ -d "{path}" ]; then
    rm -rf "{path}" 2>/dev/null || true
elif [ -f "{path}" ]; then
    rm -f "{path}" 2>/dev/null || true
fi
"""

    script_content += """
echo "Uninstallation complete!"
exit 0
"""
    return script_content

def sanitize_filename(name):
    """Sanitize the application name for use as a filename"""
    sanitized = name.replace(' ', '_')
    sanitized = re.sub(r'[^\w_]', '', sanitized)
    return sanitized.lower()

def process_brew_json_directly(json_data, app_name=None):
    """Process a brew.sh JSON data directly and generate an uninstall script"""
    if not app_name and "name" in json_data:
        app_name = json_data["name"][0] if isinstance(json_data["name"], list) else json_data["name"]
    
    # Extract paths to remove during uninstallation
    uninstall_paths = []
    
    # Process app artifacts
    if "artifacts" in json_data:
        for artifact in json_data["artifacts"]:
            # Handle app bundles
            if isinstance(artifact, dict) and "app" in artifact:
                app_paths = artifact["app"]
                if isinstance(app_paths, list):
                    for app in app_paths:
                        uninstall_paths.append(f"/Applications/{app}")
                else:
                    uninstall_paths.append(f"/Applications/{app_paths}")
    
    # Process zap artifacts
    zap_trash_paths = []
    for artifact in json_data["artifacts"]:
        if isinstance(artifact, dict) and "zap" in artifact:
            for zap_item in artifact["zap"]:
                if isinstance(zap_item, dict) and "trash" in zap_item:
                    trash_items = zap_item["trash"]
                    if isinstance(trash_items, list):
                        zap_trash_paths.extend(trash_items)
                    else:
                        zap_trash_paths.append(trash_items)
    
    # Add zap trash paths to uninstall paths
    uninstall_paths.extend(zap_trash_paths)
    
    # Generate uninstall script
    if uninstall_paths:
        script_content = generate_uninstall_script(app_name, uninstall_paths)
        
        # Save script to file
        script_filename = f"uninstall_{sanitize_filename(app_name)}.sh"
        script_path = os.path.join(uninstall_dir, script_filename)
        
        with open(script_path, "w", newline="\n") as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        print(f"Created uninstall script for {app_name}: {script_path}")
        return True
    else:
        print(f"Warning: No uninstall paths found for {app_name}")
        return False

def main():
    # Check if a JSON string is provided as an argument
    if len(sys.argv) > 1 and sys.argv[1] == "--json-string":
        if len(sys.argv) > 2:
            json_string = sys.argv[2]
            try:
                json_data = json.loads(json_string)
                app_name = json_data["name"][0] if isinstance(json_data["name"], list) else json_data["name"]
                print(f"Processing JSON data for {app_name}...")
                process_brew_json_directly(json_data, app_name)
                return
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON string: {str(e)}")
                return
            except Exception as e:
                print(f"Error processing JSON string: {str(e)}")
                return
    
    # Get all app.json files from the Apps directory
    apps_dir = Path("Apps")
    app_files = list(apps_dir.glob("*.json"))
    
    print(f"Generating uninstall scripts for {len(app_files)} applications...")
    
    for app_file in app_files:
        try:
            # Read the local app.json file
            with open(app_file, 'r') as f:
                local_app_data = json.load(f)
            
            app_name = local_app_data["name"]
            
            # Get application data from brew.sh
            brew_app_data = get_brew_app_info(app_name)
            
            if not brew_app_data:
                print(f"Warning: Could not fetch brew.sh data for {app_name}")
                continue
            
            # Extract paths to remove during uninstallation
            uninstall_paths = extract_uninstall_paths(brew_app_data)
            
            if not uninstall_paths:
                print(f"Warning: No uninstall paths found for {app_name}")
                continue
            
            # Generate uninstall script
            script_content = generate_uninstall_script(app_name, uninstall_paths)
            
            # Save script to file
            script_filename = f"uninstall_{sanitize_filename(app_name)}.sh"
            script_path = os.path.join(uninstall_dir, script_filename)
            
            with open(script_path, "w", newline="\n") as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            print(f"Created uninstall script for {app_name}: {script_path}")
            
        except Exception as e:
            print(f"Error processing {app_file}: {str(e)}")
    
    print(f"Uninstall scripts generated in '{uninstall_dir}' directory")

if __name__ == "__main__":
    main()