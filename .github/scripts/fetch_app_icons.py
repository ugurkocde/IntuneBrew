#!/usr/bin/env python3
"""
Fetch app icons by extracting them directly from app bundles (PKG/DMG/ZIP).

Downloads the app artifact and extracts the .icns icon file,
converting it to 512x512 PNG format.
"""

import argparse
import os
import sys
import json

# Force unbuffered output for real-time progress display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
os.environ['PYTHONUNBUFFERED'] = '1'
from PIL import Image

# Import the icon extraction module
from extract_icon_from_app import extract_icon_from_url, set_verbose

# Calculate repository root (script is in .github/scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

APPS_DIR = os.path.join(REPO_ROOT, "Apps")
LOGOS_DIR = os.path.join(REPO_ROOT, "Logos")
TARGET_SIZE = (512, 512)


class ProgressBar:
    """Terminal progress bar with real-time stats."""

    def __init__(self, total, bar_width=30):
        self.total = total
        self.bar_width = bar_width
        self.processed = 0
        self.success = 0
        self.failed = 0
        self.current_app = ""

    def set_current(self, app_name):
        """Set current app being processed (before result is known)."""
        self.current_app = app_name
        self._render()

    def update(self, app_name, success):
        """Update progress bar with result."""
        self.current_app = app_name
        self.processed += 1
        if success:
            self.success += 1
        else:
            self.failed += 1
        self._render()

    def _render(self):
        """Render the progress bar to terminal."""
        # Calculate progress
        progress = self.processed / self.total if self.total > 0 else 0
        filled = int(self.bar_width * progress)
        bar = "=" * filled + "-" * (self.bar_width - filled)

        # Build status line with current app (truncated)
        percent = progress * 100
        app_display = self.current_app[:20].ljust(20) if self.current_app else " " * 20

        stats = f"\r[{bar}] {percent:5.1f}% | {self.processed}/{self.total} | OK:{self.success} FAIL:{self.failed} | {app_display}"

        # Clear line and print
        sys.stdout.write(f"\033[K{stats}")  # \033[K clears to end of line
        sys.stdout.flush()

    def finish(self):
        """Complete the progress bar."""
        self.current_app = "Done!"
        self._render()
        print()  # New line after progress bar


def get_apps_to_process(force=False):
    """Get list of apps to process.

    Args:
        force: If True, return all apps. If False, only return apps missing icons.

    Returns:
        List of (app_name, app_data) tuples, sorted by app name for consistent ordering.
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

    # Sort by app name for consistent ordering across runs
    apps.sort(key=lambda x: x[0])
    return apps


def fetch_from_app_bundle(download_url, app_name):
    """Extract icon from app bundle (PKG, DMG, or ZIP)."""
    if not download_url:
        return None
    try:
        return extract_icon_from_url(download_url, app_name)
    except Exception as e:
        print(f"\n  App bundle extraction error: {e}")
    return None


def save_icon(image, app_name):
    """Resize and save icon as PNG."""
    if image.mode == 'P':
        image = image.convert('RGBA')
    elif image.mode not in ('RGBA', 'RGB'):
        image = image.convert('RGBA')

    image = image.resize(TARGET_SIZE, Image.LANCZOS)

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
        "--offset",
        type=int,
        default=0,
        help="Number of apps to skip (for batch processing, default: 0)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-fetch icons even if they already exist (overwrites existing)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output for each app (disables progress bar)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Set verbose mode for extraction module
    set_verbose(args.verbose)

    os.makedirs(LOGOS_DIR, exist_ok=True)
    all_apps = get_apps_to_process(force=args.force)

    if not all_apps:
        print("All apps have icons!")
        return

    # Apply offset
    if args.offset > 0:
        all_apps = all_apps[args.offset:]

    # Apply limit
    if args.limit > 0:
        all_apps = all_apps[:args.limit]

    if not all_apps:
        print("No apps to process after applying offset/limit")
        return

    total_apps = len(all_apps)
    mode_str = "FORCE mode" if args.force else "missing only"
    offset_str = f", offset={args.offset}" if args.offset > 0 else ""
    limit_str = f", limit={args.limit}" if args.limit > 0 else ""

    print(f"Processing {total_apps} apps ({mode_str}{offset_str}{limit_str})")
    print()

    # Initialize progress bar and show initial state
    progress = ProgressBar(total_apps)
    progress._render()  # Show empty progress bar immediately
    fetched = []
    failed = []

    for app_name, app_data in all_apps:
        # Show which app is being processed
        progress.set_current(app_name)

        bundle_id = app_data.get('bundleId')
        homepage = app_data.get('homepage')
        download_url = app_data.get('url')

        image = None
        source = None

        # Extract from app bundle (PKG/DMG/ZIP)
        if download_url:
            if args.verbose:
                print(f"\n  [{app_name}] Extracting from app bundle")
            image = fetch_from_app_bundle(download_url, app_name)

        if image:
            save_icon(image, app_name)
            fetched.append(app_name)
            progress.update(app_name, success=True)
        else:
            failed.append(app_name)
            progress.update(app_name, success=False)

    progress.finish()

    # Summary
    print()
    print("=" * 60)
    print(f"SUMMARY")
    print("=" * 60)
    print(f"  Total processed: {len(fetched) + len(failed)}")
    print(f"  Successfully extracted: {len(fetched)}")
    print(f"  Failed (need manual): {len(failed)}")
    print()

    if failed and len(failed) <= 50:
        print("Failed apps (need manual addition):")
        for app_name in failed:
            print(f"  - {app_name}")
    elif failed:
        print(f"Failed apps: {len(failed)} (too many to list, check logs)")


if __name__ == "__main__":
    main()
