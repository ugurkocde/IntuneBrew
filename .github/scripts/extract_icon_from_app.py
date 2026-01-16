#!/usr/bin/env python3
"""
Extract app icons from macOS app bundles (PKG, DMG, ZIP).

This module downloads app artifacts and extracts the .icns icon file,
converting it to PNG format for use as app icons.

Requires macOS for:
- hdiutil (DMG mounting)
- pkgutil (PKG expansion)
- sips (ICNS to PNG conversion)
"""

import os
import glob
import plistlib
import shutil
import subprocess
import tempfile
import zipfile
from typing import Optional
from urllib.parse import unquote, urlparse

import requests
from PIL import Image
from io import BytesIO

# Global verbose flag (set by caller)
VERBOSE = False


def set_verbose(verbose: bool):
    """Set verbose mode for extraction logging."""
    global VERBOSE
    VERBOSE = verbose


def log(message: str):
    """Print message only if verbose mode is enabled."""
    if VERBOSE:
        print(message)


def extract_icon_from_url(url: str, app_name: str) -> Optional[Image.Image]:
    """Extract icon from a PKG, DMG, or ZIP file at the given URL.

    Args:
        url: Download URL for the app artifact
        app_name: Name of the app (for logging)

    Returns:
        PIL Image if successful, None otherwise
    """
    if not url:
        return None

    # Parse URL to get the path without query parameters
    parsed = urlparse(url)
    path_lower = parsed.path.lower()

    # Also check query params for redirected downloads (e.g., ?file=something.dmg)
    query_lower = parsed.query.lower() if parsed.query else ""

    if path_lower.endswith('.pkg'):
        return extract_icon_from_pkg(url, app_name)
    elif path_lower.endswith('.dmg') or '.dmg' in query_lower:
        return extract_icon_from_dmg(url, app_name)
    elif path_lower.endswith('.zip') or '.zip' in query_lower:
        return extract_icon_from_zip(url, app_name)
    else:
        log(f"  Unknown file type for URL: {url}")
        return None


def extract_icon_from_pkg(pkg_url: str, app_name: str) -> Optional[Image.Image]:
    """Extract icon from a PKG file.

    PKG extraction process:
    1. Download the PKG file
    2. Expand using pkgutil --expand-full
    3. Find .app bundle in the payload
    4. Extract icon from the app bundle
    """
    temp_dir = tempfile.mkdtemp(prefix="intunebrew_pkg_")
    try:
        # Download PKG
        pkg_path = os.path.join(temp_dir, "app.pkg")
        log(f"  Downloading PKG...")

        if not download_file(pkg_url, pkg_path):
            return None

        # Expand PKG
        expanded_dir = os.path.join(temp_dir, "expanded")
        log(f"  Expanding PKG...")

        result = subprocess.run(
            ["pkgutil", "--expand-full", pkg_path, expanded_dir],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            log(f"  pkgutil error: {result.stderr}")
            return None

        # Find .app bundle in expanded payload
        app_path = find_app_bundle(expanded_dir)
        if not app_path:
            log(f"  No .app bundle found in PKG")
            return None

        return extract_icon_from_app_bundle(app_path, temp_dir)

    except Exception as e:
        log(f"  PKG extraction error: {e}")
        return None
    finally:
        cleanup_temp_dir(temp_dir)


def extract_icon_from_dmg(dmg_url: str, app_name: str) -> Optional[Image.Image]:
    """Extract icon from a DMG file.

    DMG extraction process:
    1. Download the DMG file
    2. Mount using hdiutil attach
    3. Find .app bundle in mounted volume
    4. Extract icon from the app bundle
    5. Unmount the DMG
    """
    temp_dir = tempfile.mkdtemp(prefix="intunebrew_dmg_")
    mount_point = None

    try:
        # Download DMG
        dmg_path = os.path.join(temp_dir, "app.dmg")
        log(f"  Downloading DMG...")

        if not download_file(dmg_url, dmg_path):
            return None

        # Mount DMG (use yes to auto-accept any EULA prompts)
        log(f"  Mounting DMG...")

        # First attempt: standard mount with EULA auto-accept via stdin
        result = subprocess.run(
            ["hdiutil", "attach", "-nobrowse", "-noverify", "-noautoopen", "-plist", dmg_path],
            capture_output=True,
            input=b"y\n" * 10,  # Send multiple 'y' responses for EULA prompts
            timeout=120
        )

        if result.returncode != 0:
            stderr_msg = result.stderr.decode().strip() if result.stderr else "Unknown error"
            log(f"  hdiutil attach error (code {result.returncode}): {stderr_msg}")
            return None

        # Parse plist output to get mount point
        if not result.stdout:
            # Some DMGs with EULAs may need a different approach
            log(f"  hdiutil returned no output (possibly EULA-protected DMG)")
            return None

        try:
            plist_data = plistlib.loads(result.stdout)
        except Exception as plist_err:
            log(f"  Failed to parse hdiutil output: {plist_err}")
            return None
        for entity in plist_data.get("system-entities", []):
            if "mount-point" in entity:
                mount_point = entity["mount-point"]
                break

        if not mount_point:
            log(f"  Could not find mount point")
            return None

        log(f"  Mounted at: {mount_point}")

        # Find .app bundle
        app_path = find_app_bundle(mount_point)
        if not app_path:
            log(f"  No .app bundle found in DMG")
            return None

        return extract_icon_from_app_bundle(app_path, temp_dir)

    except Exception as e:
        log(f"  DMG extraction error: {e}")
        return None
    finally:
        # Always try to unmount
        if mount_point:
            subprocess.run(
                ["hdiutil", "detach", mount_point, "-quiet"],
                capture_output=True
            )
        cleanup_temp_dir(temp_dir)


def extract_icon_from_zip(zip_url: str, app_name: str) -> Optional[Image.Image]:
    """Extract icon from a ZIP file containing an app bundle.

    ZIP extraction process:
    1. Download the ZIP file
    2. Extract using Python's zipfile module
    3. Find .app bundle in extracted contents
    4. Extract icon from the app bundle
    """
    temp_dir = tempfile.mkdtemp(prefix="intunebrew_zip_")
    try:
        # Download ZIP
        zip_path = os.path.join(temp_dir, "app.zip")
        log(f"  Downloading ZIP...")

        if not download_file(zip_url, zip_path):
            return None

        # Extract ZIP
        extract_dir = os.path.join(temp_dir, "extracted")
        log(f"  Extracting ZIP...")

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            log(f"  Invalid ZIP file")
            return None

        # Find .app bundle
        app_path = find_app_bundle(extract_dir)
        if not app_path:
            log(f"  No .app bundle found in ZIP")
            return None

        return extract_icon_from_app_bundle(app_path, temp_dir)

    except Exception as e:
        log(f"  ZIP extraction error: {e}")
        return None
    finally:
        cleanup_temp_dir(temp_dir)


def find_app_bundle(search_dir: str) -> Optional[str]:
    """Find the first .app bundle in a directory tree.

    Searches recursively but prioritizes top-level .app bundles.
    """
    # First check top level
    for item in os.listdir(search_dir):
        if item.endswith('.app'):
            return os.path.join(search_dir, item)

    # Then search recursively (limited depth to avoid going too deep)
    for root, dirs, files in os.walk(search_dir):
        # Limit search depth
        depth = root[len(search_dir):].count(os.sep)
        if depth > 5:
            continue

        for d in dirs:
            if d.endswith('.app'):
                return os.path.join(root, d)

    return None


def extract_icon_from_app_bundle(app_path: str, temp_dir: str) -> Optional[Image.Image]:
    """Extract and convert icon from a .app bundle.

    Reads Info.plist to find CFBundleIconFile, then converts
    the .icns file to PNG using sips.
    """
    # Read Info.plist
    info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
    if not os.path.exists(info_plist_path):
        log(f"  No Info.plist found")
        return None

    try:
        with open(info_plist_path, 'rb') as f:
            info = plistlib.load(f)
    except Exception as e:
        log(f"  Error reading Info.plist: {e}")
        return None

    # Get icon file name from plist
    icon_name = info.get('CFBundleIconFile', '')
    if not icon_name:
        # Try alternate key
        icon_name = info.get('CFBundleIconName', '')

    if not icon_name:
        log(f"  No icon file specified in Info.plist")
        # Try to find any .icns file
        resources_dir = os.path.join(app_path, "Contents", "Resources")
        if os.path.exists(resources_dir):
            icns_files = glob.glob(os.path.join(resources_dir, "*.icns"))
            if icns_files:
                icon_name = os.path.basename(icns_files[0])
                log(f"  Found fallback icon: {icon_name}")

    if not icon_name:
        return None

    # Add .icns extension if not present
    if not icon_name.endswith('.icns'):
        icon_name += '.icns'

    # Find the icon file
    icns_path = os.path.join(app_path, "Contents", "Resources", icon_name)
    if not os.path.exists(icns_path):
        log(f"  Icon file not found: {icns_path}")
        return None

    log(f"  Found icon: {icon_name}")

    # Convert to PNG using sips
    return convert_icns_to_png(icns_path, temp_dir)


def convert_icns_to_png(icns_path: str, temp_dir: str) -> Optional[Image.Image]:
    """Convert .icns file to PNG using macOS sips command.

    sips (Scriptable Image Processing System) is a native macOS tool
    that can convert between image formats including ICNS.
    """
    png_path = os.path.join(temp_dir, "icon.png")

    log(f"  Converting ICNS to PNG...")
    result = subprocess.run(
        ["sips", "-s", "format", "png", icns_path, "--out", png_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log(f"  sips conversion error: {result.stderr}")
        return None

    if not os.path.exists(png_path):
        log(f"  PNG conversion failed - no output file")
        return None

    try:
        img = Image.open(png_path)
        # Load image data into memory so we can delete the temp file
        img.load()
        # Create a copy in memory
        return img.copy()
    except Exception as e:
        log(f"  Error loading converted PNG: {e}")
        return None


def download_file(url: str, dest_path: str, timeout: int = 300) -> bool:
    """Download a file from URL to destination path.

    Uses streaming download to handle large files efficiently.
    Verifies downloaded size matches expected size.
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        if total_size > 0:
            log(f"  File size: {total_size / (1024*1024):.1f} MB")

        downloaded_size = 0
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)

        # Verify download completed
        if total_size > 0 and downloaded_size != total_size:
            log(f"  Download incomplete: got {downloaded_size} bytes, expected {total_size}")
            return False

        # Verify file exists and has content
        actual_size = os.path.getsize(dest_path)
        if actual_size < 1000:  # Less than 1KB is suspicious
            log(f"  Downloaded file too small: {actual_size} bytes")
            return False

        return True
    except requests.RequestException as e:
        log(f"  Download error: {e}")
        return False


def cleanup_temp_dir(temp_dir: str) -> None:
    """Safely remove a temporary directory."""
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        log(f"  Warning: Could not clean up temp dir: {e}")


if __name__ == "__main__":
    # Quick test
    print("Icon extraction module loaded successfully")
    print("This module requires macOS for PKG/DMG extraction")
