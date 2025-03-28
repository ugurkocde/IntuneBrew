#!/usr/bin/env python3
import json
import os
import requests
import re
from pathlib import Path
import sys

# Import app_urls from collect_app_info.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.github', 'scripts'))
from collect_app_info import app_urls

# Create Uninstall Scripts directory if it doesn't exist
uninstall_dir = "Uninstall Scripts"
os.makedirs(uninstall_dir, exist_ok=True)

def get_app_info(json_url):
    """Fetch application information from brew.sh API"""
    print(f"Fetching information for {json_url}")
    response = requests.get(json_url)
    response.raise_for_status()
    return response.json()

def extract_uninstall_paths(app_data):
    """Extract paths that need to be removed during uninstallation"""
    uninstall_paths = []
    
    # Extract app bundle path
    if "artifacts" in app_data:
        for artifact in app_data["artifacts"]:
            if isinstance(artifact, str) and artifact.endswith(".app"):
                uninstall_paths.append(f"/Applications/{artifact}")
            elif isinstance(artifact, dict) and "app" in artifact:
                app_path = artifact["app"]
                if isinstance(app_path, list):
                    for app in app_path:
                        uninstall_paths.append(f"/Applications/{app}")
                else:
                    uninstall_paths.append(f"/Applications/{app_path}")
    
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
    
    # Extract zap stanza for additional paths
    if "zap" in app_data:
        zap_data = app_data["zap"]
        
        # Extract additional app bundles
        if "trash" in zap_data:
            trash_paths = zap_data["trash"]
            if isinstance(trash_paths, list):
                for path in trash_paths:
                    uninstall_paths.append(path)
            else:
                uninstall_paths.append(trash_paths)
        
        # Extract launchctl services from zap
        if "launchctl" in zap_data:
            launchctl_services = zap_data["launchctl"]
            if isinstance(launchctl_services, list):
                for service in launchctl_services:
                    uninstall_paths.append(f"LAUNCHCTL:{service}")
            else:
                uninstall_paths.append(f"LAUNCHCTL:{launchctl_services}")
        
        # Extract pkgutil IDs from zap
        if "pkgutil" in zap_data:
            pkgutil_ids = zap_data["pkgutil"]
            if isinstance(pkgutil_ids, list):
                for pkg_id in pkgutil_ids:
                    uninstall_paths.append(f"PKGUTIL:{pkg_id}")
            else:
                uninstall_paths.append(f"PKGUTIL:{pkgutil_ids}")
    
    # Common locations for application data
    app_name = app_data["name"][0]
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

def main():
    print(f"Generating uninstall scripts for {len(app_urls)} applications...")
    
    for url in app_urls:
        try:
            # Get application data from brew.sh
            app_data = get_app_info(url)
            app_name = app_data["name"][0]
            
            # Extract paths to remove during uninstallation
            uninstall_paths = extract_uninstall_paths(app_data)
            
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
            print(f"Error processing {url}: {str(e)}")
    
    print(f"Uninstall scripts generated in '{uninstall_dir}' directory")

if __name__ == "__main__":
    main()