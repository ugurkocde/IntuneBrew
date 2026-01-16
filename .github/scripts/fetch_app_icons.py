#!/usr/bin/env python3
"""
Fetch missing app icons from multiple sources:
1. iTunes/App Store API (primary - for Mac App Store apps)
2. App Bundle Extraction (secondary - download PKG/DMG/ZIP and extract .icns)
3. Google Favicon API (last resort - free, no auth)

All icons are standardized to 512x512 PNG format.
"""

import argparse
import os
import json
import requests
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO

# Import the icon extraction module
from extract_icon_from_app import extract_icon_from_url

# Calculate repository root (script is in .github/scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

APPS_DIR = os.path.join(REPO_ROOT, "Apps")
LOGOS_DIR = os.path.join(REPO_ROOT, "Logos")
TARGET_SIZE = (512, 512)


def get_apps_to_process(force=False):
    """Get list of apps to process.

    Args:
        force: If True, return all apps. If False, only return apps missing icons.

    Returns:
        List of (app_name, app_data) tuples.
    """
    apps = []
    for filename in os.listdir(APPS_DIR):
        if filename.endswith('.json'):
            app_name = filename[:-5]
            icon_path = os.path.join(LOGOS_DIR, f"{app_name}.png")

            # Include app if force mode OR icon is missing
            if force or not os.path.exists(icon_path):
                with open(os.path.join(APPS_DIR, filename)) as f:
                    app_data = json.load(f)
                apps.append((app_name, app_data))
    return apps


def fetch_from_itunes(bundle_id):
    """Fetch icon from iTunes API using bundle ID."""
    if not bundle_id or bundle_id == "null":
        return None
    try:
        url = f"https://itunes.apple.com/lookup?bundleId={bundle_id}&entity=macSoftware"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get('resultCount', 0) > 0:
            artwork_url = data['results'][0].get('artworkUrl512')
            if artwork_url:
                img_resp = requests.get(artwork_url, timeout=10)
                if img_resp.status_code == 200:
                    return Image.open(BytesIO(img_resp.content))
    except Exception as e:
        print(f"  iTunes error: {e}")
    return None


def fetch_from_app_bundle(download_url, app_name):
    """Extract icon from app bundle (PKG, DMG, or ZIP).

    Downloads the app artifact and extracts the .icns icon file,
    converting it to PNG format.

    This approach provides the highest quality icons as it uses
    the actual app icons rather than brand logos.
    """
    if not download_url:
        return None
    try:
        return extract_icon_from_url(download_url, app_name)
    except Exception as e:
        print(f"  App bundle extraction error: {e}")
    return None


def fetch_from_google_favicon(homepage):
    """Fetch favicon from Google's Favicon API (free, no auth required)."""
    if not homepage:
        return None
    try:
        domain = urlparse(homepage).netloc
        if not domain:
            return None
        domain = domain.replace('www.', '')
        # Google Favicon API - redirects to gstatic.com
        url = f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
        resp = requests.get(url, timeout=10, allow_redirects=True)
        if resp.status_code == 200 and 'image' in resp.headers.get('content-type', ''):
            img = Image.open(BytesIO(resp.content))
            # Skip if it's the default/placeholder icon (very small)
            if img.size[0] >= 64:
                return img
    except Exception as e:
        print(f"  Google Favicon error: {e}")
    return None


def save_icon(image, app_name):
    """Resize and save icon as PNG."""
    # Handle different image modes
    if image.mode == 'P':
        image = image.convert('RGBA')
    elif image.mode not in ('RGBA', 'RGB'):
        image = image.convert('RGBA')

    # Resize to target size with high quality
    image = image.resize(TARGET_SIZE, Image.LANCZOS)

    # Save as PNG
    output_path = os.path.join(LOGOS_DIR, f"{app_name}.png")
    image.save(output_path, 'PNG')
    return output_path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch missing app icons from various sources"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of apps to process (0 = all, default: 0)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-fetch icons even if they already exist (overwrites existing)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    os.makedirs(LOGOS_DIR, exist_ok=True)
    apps_to_process = get_apps_to_process(force=args.force)

    if not apps_to_process:
        print("All apps have icons!")
        return

    # Apply limit if specified
    if args.limit > 0:
        apps_to_process = apps_to_process[:args.limit]

    mode_str = "FORCE mode (overwriting existing)" if args.force else "missing icons only"
    print(f"Processing {len(apps_to_process)} apps ({mode_str})\n")

    fetched = []
    failed = []
    skipped = []

    for app_name, app_data in apps_to_process:
        print(f"Processing: {app_name}")
        bundle_id = app_data.get('bundleId')
        homepage = app_data.get('homepage')
        download_url = app_data.get('url')

        image = None
        source = None

        # Try iTunes first (best quality for Mac App Store apps)
        if bundle_id:
            print(f"  Trying iTunes API (bundleId: {bundle_id})")
            image = fetch_from_itunes(bundle_id)
            if image:
                source = "iTunes"

        # Fallback 1: Extract from app bundle (PKG/DMG/ZIP)
        if image is None and download_url:
            print(f"  Trying app bundle extraction (url: {download_url[:60]}...)")
            image = fetch_from_app_bundle(download_url, app_name)
            if image:
                source = "App Bundle"

        # Fallback 2: Google Favicon API (last resort - free, no auth)
        if image is None and homepage:
            print(f"  Trying Google Favicon API (homepage: {homepage})")
            image = fetch_from_google_favicon(homepage)
            if image:
                source = "Google Favicon"

        if image:
            save_icon(image, app_name)
            fetched.append((app_name, source))
            print(f"  [OK] Saved icon from {source}")
        else:
            failed.append(app_name)
            print(f"  [MISS] No icon found")
        print()

    # Summary
    print("=" * 50)
    print(f"SUMMARY: {len(fetched)} fetched, {len(failed)} failed")
    print("=" * 50)

    if fetched:
        print("\nFetched icons:")
        for app_name, source in fetched:
            print(f"  + {app_name} (from {source})")

    if failed:
        print("\nFailed (need manual addition):")
        for app_name in failed:
            print(f"  - {app_name}")


if __name__ == "__main__":
    main()
