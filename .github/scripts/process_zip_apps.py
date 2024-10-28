import os
import zipfile
import subprocess
import shutil
from pathlib import Path

def create_dmg_from_app(app_path, dmg_name):
    """
    Create a DMG file from an app folder using genisoimage
    """
    dmg_path = f"{dmg_name}.dmg"
    
    # Create a temporary directory for DMG contents
    staging_dir = Path("temp_dmg")
    staging_dir.mkdir(exist_ok=True)
    
    # Copy .app to staging directory
    shutil.copytree(app_path, staging_dir / app_path.name)
    
    # Create symbolic link to /Applications
    os.symlink("/Applications", staging_dir / "Applications")
    
    # Create DMG using genisoimage
    subprocess.run([
        'genisoimage',
        '-V', dmg_name,           # Volume name
        '-D',                     # Deep directory relocation
        '-R',                     # Rock Ridge protocol
        '-apple',                 # Generate Apple ISO9660 extensions
        '-no-pad',               # Don't pad to nearest 2048 bytes
        '-o', dmg_path,          # Output file
        staging_dir              # Source directory
    ], check=True)
    
    # Clean up
    shutil.rmtree(staging_dir)
    
    return dmg_path

def process_zip_app(zip_path, app_name):
    """
    Process a zip file containing a .app folder:
    1. Extract the zip
    2. Find the .app folder
    3. Convert to DMG
    4. Clean up temporary files
    """
    temp_dir = Path("temp_extract")
    temp_dir.mkdir(exist_ok=True)
    
    # Extract zip
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find .app directory
    app_path = None
    for root, dirs, files in os.walk(temp_dir):
        for dir in dirs:
            if dir.endswith('.app'):
                app_path = Path(root) / dir
                break
        if app_path:
            break
    
    if not app_path:
        raise Exception(f"No .app folder found in {zip_path}")
    
    try:
        # Create DMG
        dmg_path = create_dmg_from_app(app_path, app_name)
        final_path = f"Apps/dmg/{app_name}.dmg"
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        shutil.move(dmg_path, final_path)
        return final_path
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
