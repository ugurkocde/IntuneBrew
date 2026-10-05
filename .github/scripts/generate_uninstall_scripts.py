#!/usr/bin/env python3
import json
import os
import requests
import re
from pathlib import Path
import sys
import argparse

# Default output directory
uninstall_dir = "Uninstall Scripts"
def get_brew_app_info(app_name, token=None):
    """Fetch application information from brew.sh API"""
    # If token is provided, use it directly
    if token:
        json_url = f"https://formulae.brew.sh/api/cask/{token}.json"
        print(f"Fetching information for {app_name} using token {token} from {json_url}")
        try:
            response = requests.get(json_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {json_url}: {str(e)}")
            return None
    
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
            f"https://formulae.brew.sh/api/cask/{brew_name.replace('-', '_')}.json",
            f"https://formulae.brew.sh/api/cask/{brew_name.replace(' ', '')}.json",
            f"https://formulae.brew.sh/api/cask/{brew_name.replace(' ', '_')}.json"
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
        return None

def extract_uninstall_paths(app_data):
    """Extract paths that need to be removed during uninstallation directly from brew.sh data"""
    uninstall_paths = []
    
    # Extract app bundle path from artifacts
    if "artifacts" in app_data:
        for artifact in app_data["artifacts"]:
            # Handle string artifacts (usually .app files)
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
                
                # Handle binary artifacts
                if "binary" in artifact:
                    binary_path = artifact["binary"]
                    if isinstance(binary_path, list):
                        for binary in binary_path:
                            # Handle variables like $APPDIR
                            if binary.startswith("$APPDIR"):
                                # We'll handle this specially in the script generation
                                uninstall_paths.append(f"BINARY:{binary}")
                            else:
                                uninstall_paths.append(f"/usr/local/bin/{binary}")
                    else:
                        if binary_path.startswith("$APPDIR"):
                            uninstall_paths.append(f"BINARY:{binary_path}")
                        else:
                            uninstall_paths.append(f"/usr/local/bin/{binary_path}")
                
                # Handle uninstall artifacts
                if "uninstall" in artifact:
                    uninstall_data = artifact["uninstall"]
                    if isinstance(uninstall_data, list):
                        for uninstall_item in uninstall_data:
                            if isinstance(uninstall_item, dict):
                                # Handle launchctl
                                if "launchctl" in uninstall_item:
                                    launchctl_services = uninstall_item["launchctl"]
                                    if isinstance(launchctl_services, list):
                                        for service in launchctl_services:
                                            uninstall_paths.append(f"LAUNCHCTL:{service}")
                                    else:
                                        uninstall_paths.append(f"LAUNCHCTL:{launchctl_services}")
                                
                                # Handle quit
                                if "quit" in uninstall_item:
                                    quit_ids = uninstall_item["quit"]
                                    if isinstance(quit_ids, list):
                                        for quit_id in quit_ids:
                                            uninstall_paths.append(f"BUNDLE:{quit_id}")
                                    else:
                                        uninstall_paths.append(f"BUNDLE:{quit_ids}")
                
                # Handle zap artifacts (most important for cleanup)
                if "zap" in artifact:
                    zap_data = artifact["zap"]
                    if isinstance(zap_data, list):
                        for zap_item in zap_data:
                            # Handle trash paths
                            if isinstance(zap_item, dict) and "trash" in zap_item:
                                trash_paths = zap_item["trash"]
                                if isinstance(trash_paths, list):
                                    for path in trash_paths:
                                        uninstall_paths.append(path)
                                else:
                                    uninstall_paths.append(trash_paths)
                            
                            # Handle delete paths
                            if isinstance(zap_item, dict) and "delete" in zap_item:
                                delete_paths = zap_item["delete"]
                                if isinstance(delete_paths, list):
                                    for path in delete_paths:
                                        uninstall_paths.append(path)
                                else:
                                    uninstall_paths.append(delete_paths)
                            
                            # Handle rmdir paths
                            if isinstance(zap_item, dict) and "rmdir" in zap_item:
                                rmdir_paths = zap_item["rmdir"]
                                if isinstance(rmdir_paths, list):
                                    for path in rmdir_paths:
                                        uninstall_paths.append(path)
                                else:
                                    uninstall_paths.append(rmdir_paths)
                            
                            # Handle signal paths
                            if isinstance(zap_item, dict) and "signal" in zap_item:
                                signal_data = zap_item["signal"]
                                if isinstance(signal_data, dict):
                                    for signal_app, _ in signal_data.items():
                                        uninstall_paths.append(f"SIGNAL:{signal_app}")
    
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
    
    return uninstall_paths

def get_local_uninstall_paths(app_name, local_app_data):
    """Use installed recipe payloads and canonical source tokens for cleanup."""
    if local_app_data.get("homebrew_formula") == "azure-cli" and local_app_data.get("packaging_recipe") == "azure-cli-universal-v1":
        return ["/usr/local/bin/az", "/usr/local/lib/intunebrew/azure_cli", "PKGUTIL:com.intunebrew.azure_cli"]
    token = local_app_data.get("homebrew_cask") or local_app_data.get("token") or local_app_data.get("brew_token")
    brew_data = get_brew_app_info(app_name, token)
    if not brew_data:
        return None
    paths = extract_uninstall_paths(brew_data)
    if token == "logi-options+" and local_app_data.get("packaging_recipe") == "logi-options-silent-v1":
        paths.extend([
            "/Applications/logioptionsplus.app",
            "/Applications/Utilities/Logi Options+ Driver Installer.bundle",
            "/Library/Application Support/Logi",
            "/Library/Application Support/Logitech.localized/LogiOptionsPlus",
            "/usr/local/lib/intunebrew/logitech_options",
            "PKGUTIL:com.intunebrew.logitech_options",
        ])
    return list(dict.fromkeys(paths))

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
            # Handle bundle IDs for killing applications
            bundle_id = path.replace("BUNDLE:", "")
            script_content += f"""
# Kill application with bundle ID {bundle_id} if running
echo "Stopping application with bundle ID {bundle_id} if running..."
killall -9 "{bundle_id}" 2>/dev/null || true
"""
        elif path.startswith("SIGNAL:"):
            # Handle signal paths (usually for killing processes)
            app_to_signal = path.replace("SIGNAL:", "")
            script_content += f"""
# Kill application {app_to_signal} if running
echo "Stopping application {app_to_signal} if running..."
killall -9 "{app_to_signal}" 2>/dev/null || true
"""
        elif path.startswith("BINARY:"):
            # Handle binary paths with variables
            binary_path = path.replace("BINARY:", "")
            if binary_path.startswith("$APPDIR"):
                # Replace $APPDIR with the actual application directory
                app_dir_path = f"/Applications/{app_name}.app"
                actual_path = binary_path.replace("$APPDIR", app_dir_path)
                script_content += f"""
# Remove binary {actual_path}
echo "Removing binary {actual_path}..."
if [ -f "{actual_path}" ]; then
    rm -f "{actual_path}" 2>/dev/null || true
fi
"""
            else:
                script_content += f"""
# Remove binary {binary_path}
echo "Removing binary {binary_path}..."
if [ -f "{binary_path}" ]; then
    rm -f "{binary_path}" 2>/dev/null || true
fi
"""
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
def parse_brew_json_data(json_data):
    """Parse brew.sh JSON data directly from a string"""
    try:
        app_data = json.loads(json_data)
        return app_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {str(e)}")
        return None

def test_with_json_string(json_string):
    """Test the script with a JSON string"""
    try:
        # Parse JSON data
        json_data = parse_brew_json_data(json_string)
        
        if not json_data:
            print("Error: Could not parse JSON data")
            return
        
        # Extract app name
        app_name = json_data["name"][0] if isinstance(json_data["name"], list) else json_data["name"]
        
        # Extract uninstall paths
        uninstall_paths = extract_uninstall_paths(json_data)
        
        if not uninstall_paths:
            print(f"Warning: No uninstall paths found for {app_name}")
            return
        
        # Generate uninstall script
        script_content = generate_uninstall_script(app_name, uninstall_paths)
        
        # Print the script content
        print("\n" + "="*80)
        print(f"Uninstall script for {app_name}:")
        print("="*80)
        print(script_content)
        print("="*80)
        
        # Save script to file
        script_filename = f"uninstall_{sanitize_filename(app_name)}.sh"
        script_path = os.path.join(uninstall_dir, script_filename)
        
        with open(script_path, "w", newline="\n") as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        print(f"Created uninstall script for {app_name}: {script_path}")
        
    except Exception as e:
        print(f"Error processing JSON string: {str(e)}")


def main():
    global uninstall_dir
    
    parser = argparse.ArgumentParser(description='Generate uninstall scripts for macOS applications using brew.sh data')
    parser.add_argument('--all', action='store_true', help='Generate uninstall scripts for all apps in the Apps directory')
    parser.add_argument('--app', type=str, help='Generate uninstall script for a specific app name')
    parser.add_argument('--apps', type=str, nargs='+', help='Generate uninstall scripts for specific app files (e.g., Apps/1password.json)')
    parser.add_argument('--json-file', type=str, help='Generate uninstall script from a JSON file')
    parser.add_argument('--json-string', type=str, help='Generate uninstall script from a JSON string')
    parser.add_argument('--output', type=str, help='Output directory for uninstall scripts', default=uninstall_dir)
    parser.add_argument('--apps-dir', type=str, help='Directory containing app JSON files', default='Apps')
    parser.add_argument('--test-json', action='store_true', help='Test with a JSON string (for development)')
    
    args = parser.parse_args()
    
    # Update output directory if specified
    uninstall_dir = args.output
    
    # Create output directory if it doesn't exist
    os.makedirs(uninstall_dir, exist_ok=True)
    
    # Process based on arguments
    if args.json_file:
        try:
            with open(args.json_file, 'r') as f:
                json_data = json.load(f)
            
            app_name = json_data["name"][0] if isinstance(json_data["name"], list) else json_data["name"]
            uninstall_paths = extract_uninstall_paths(json_data)
            
            if not uninstall_paths:
                print(f"Warning: No uninstall paths found in the JSON file")
                return
            
            generate_and_save_script(app_name, uninstall_paths)
            
        except Exception as e:
            print(f"Error processing JSON file: {str(e)}")
            
    elif args.json_string:
        try:
            json_data = parse_brew_json_data(args.json_string)
            
            if not json_data:
                print("Error: Could not parse JSON string")
                return
                
            app_name = json_data["name"][0] if isinstance(json_data["name"], list) else json_data["name"]
            uninstall_paths = extract_uninstall_paths(json_data)
            
            if not uninstall_paths:
                print(f"Warning: No uninstall paths found in the JSON string")
                return
            
            generate_and_save_script(app_name, uninstall_paths)
            
        except Exception as e:
            print(f"Error processing JSON string: {str(e)}")
            
    elif args.app:
        try:
            app_name = args.app
            brew_app_data = get_brew_app_info(app_name)
            
            if not brew_app_data:
                print(f"Warning: Could not fetch brew.sh data for {app_name}")
                return
            
            uninstall_paths = extract_uninstall_paths(brew_app_data)
            
            if not uninstall_paths:
                print(f"Warning: No uninstall paths found for {app_name}")
                return
            
            generate_and_save_script(app_name, uninstall_paths)
            
        except Exception as e:
            print(f"Error processing app {args.app}: {str(e)}")
    
    elif args.apps:
        success_count = 0
        error_count = 0
        
        for app_file_path in args.apps:
            try:
                app_file = Path(app_file_path)
                if not app_file.exists():
                    print(f"Error: App file not found: {app_file}")
                    error_count += 1
                    continue
                    
                # Read the local app.json file
                with open(app_file, 'r') as f:
                    local_app_data = json.load(f)
                
                app_name = local_app_data.get("name")
                if not app_name:
                    print(f"Warning: No name found in {app_file}")
                    error_count += 1
                    continue
                    
                # Handle case where app_name is an array
                if isinstance(app_name, list):
                    app_name = app_name[0]
                
                print(f"Processing {app_name} from {app_file}")
                
                # Get application data from brew.sh
                uninstall_paths = get_local_uninstall_paths(app_name, local_app_data)
                
                if uninstall_paths is None:
                    print(f"Warning: Could not fetch brew.sh data for {app_name}")
                    error_count += 1
                    continue
                
                # Extract paths to remove during uninstallation
                
                if not uninstall_paths:
                    print(f"Warning: No uninstall paths found for {app_name}")
                    error_count += 1
                    continue
                
                generate_and_save_script(app_name, uninstall_paths)
                success_count += 1
                
            except Exception as e:
                print(f"Error processing {app_file_path}: {str(e)}")
                error_count += 1
        
        print(f"Summary: {success_count} scripts generated successfully, {error_count} errors")
            
    elif args.test_json:
        # Test with a JSON string (for development)
        json_string = input("Enter JSON string: ")
        test_with_json_string(json_string)
        
    elif args.all:
        process_all_apps(args.apps_dir)
        
    else:
        # Default behavior: process all apps
        process_all_apps(args.apps_dir)

def generate_and_save_script(app_name, uninstall_paths):
    """Generate and save an uninstall script for the given app name and paths"""
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

def process_all_apps(apps_dir_path='Apps'):
    """Process all apps in the specified directory"""
    apps_dir = Path(apps_dir_path)
    
    if not apps_dir.exists():
        print(f"Error: Apps directory not found at {apps_dir.absolute()}")
        return
        
    app_files = list(apps_dir.glob("*.json"))
    
    if not app_files:
        print(f"Warning: No JSON files found in the Apps directory")
        return
    
    print(f"Generating uninstall scripts for {len(app_files)} applications...")
    
    success_count = 0
    error_count = 0
    
    for app_file in app_files:
        try:
            # Read the local app.json file
            with open(app_file, 'r') as f:
                local_app_data = json.load(f)
            
            app_name = local_app_data.get("name")
            if not app_name:
                print(f"Warning: No name found in {app_file}")
                error_count += 1
                continue
                
            # Handle case where app_name is an array
            if isinstance(app_name, list):
                app_name = app_name[0]
            
            print(f"Processing {app_name} from {app_file}")
            
            # Get application data from brew.sh
            uninstall_paths = get_local_uninstall_paths(app_name, local_app_data)
            
            if uninstall_paths is None:
                print(f"Warning: Could not fetch brew.sh data for {app_name}")
                error_count += 1
                continue
            
            # Extract paths to remove during uninstallation
            
            if not uninstall_paths:
                print(f"Warning: No uninstall paths found for {app_name}")
                error_count += 1
                continue
            
            generate_and_save_script(app_name, uninstall_paths)
            success_count += 1
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {app_file}: {str(e)}")
            error_count += 1
        except KeyError as e:
            print(f"Missing key in {app_file}: {str(e)}")
            error_count += 1
        except Exception as e:
            print(f"Error processing {app_file}: {str(e)}")
            error_count += 1
    
    print(f"Uninstall scripts generated in '{uninstall_dir}' directory")
    print(f"Summary: {success_count} scripts generated successfully, {error_count} errors")

if __name__ == "__main__":
    main()