#!/usr/bin/env python3
"""
CVE Data Sync Script for IntuneBrew

This script syncs CVE data from the CVE/ directory to Supabase.
It also calculates "recent" CVE counts based on the latest app versions.

Required environment variables:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Service role key for write access

Usage:
    python sync_cves_to_supabase.py --manifest PATH [--cve-dir ./CVE] [--apps-dir ./Apps]
"""

import os
import sys
import json
import argparse
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py not installed. Run: pip install supabase")
    sys.exit(1)


# =============================================================================
# VERSION COMPARISON UTILITIES
# =============================================================================

def normalize_version(version: str) -> Optional[Tuple[int, int, int]]:
    """
    Normalize version string to (major, minor, patch) tuple.
    Returns None if version cannot be parsed.
    """
    if not version:
        return None

    # Remove leading 'v' if present
    cleaned = version.lstrip('vV')

    # Try to extract major.minor.patch
    match = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?', cleaned)
    if not match:
        return None

    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) else 0
    patch = int(match.group(3)) if match.group(3) else 0

    return (major, minor, patch)


def is_recent_fix(fixed_version: str, latest_version: str) -> bool:
    """
    Check if a CVE fix is "recent" relative to the latest version.
    Returns True if the fix is in the SAME major version and within 3 minor versions.

    This matches the logic in the website's /api/app-cves endpoint.
    """
    fixed = normalize_version(fixed_version)
    latest = normalize_version(latest_version)

    if not fixed or not latest:
        # Fall back to exact match for non-parseable versions
        return fixed_version == latest_version

    fixed_major, fixed_minor, _ = fixed
    latest_major, latest_minor, _ = latest

    # Must be same major version
    if fixed_major != latest_major:
        return False

    # Within 3 minor versions
    return latest_minor - fixed_minor <= 3


# =============================================================================
# DATA LOADING
# =============================================================================

def load_app_versions(apps_dir: str) -> Dict[str, str]:
    """Load app versions from Apps/*.json files."""
    versions = {}
    apps_path = Path(apps_dir)

    if not apps_path.exists():
        print(f"Warning: Apps directory '{apps_dir}' does not exist")
        return versions

    for json_file in apps_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                app_key = json_file.stem
                version = data.get('version')
                if version:
                    versions[app_key] = version
        except Exception as e:
            # Silently skip files that can't be parsed
            pass

    print(f"Loaded versions for {len(versions)} apps")
    return versions


def strict_json(payload):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate JSON key')
            value[key] = item
        return value
    def invalid_number(value):
        raise ValueError('Non-finite JSON number')
    return json.loads(payload, object_pairs_hook=unique, parse_constant=invalid_number)


def load_manifest_cves(cve_dir, manifest_path):
    """Authorize exact complete files before creating a database client; no broad fallback."""
    path = Path(manifest_path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Publication manifest must be a regular file')
    manifest = strict_json(path.read_bytes())
    fields = {'schema', 'run_id', 'run_attempt', 'selected_count', 'selected_apps',
              'failure_limit_percent', 'kev_entries', 'validated', 'stale'}
    if not isinstance(manifest, dict) or set(manifest) != fields:
        raise ValueError('Publication manifest shape differs')
    for key in ['schema', 'run_id', 'run_attempt', 'selected_count', 'failure_limit_percent', 'kev_entries']:
        if type(manifest[key]) is not int or manifest[key] <= 0:
            raise ValueError('Publication manifest counts differ')
    if manifest['schema'] != 1 or manifest['failure_limit_percent'] != 10:
        raise ValueError('Publication policy differs')
    if str(manifest['run_id']) != os.environ.get('GITHUB_RUN_ID') or str(manifest['run_attempt']) != os.environ.get('GITHUB_RUN_ATTEMPT'):
        raise ValueError('Publication run identity differs')
    validated, stale, selected = (manifest[key] for key in ['validated', 'stale', 'selected_apps'])
    if not all(isinstance(rows, list) for rows in [validated, stale, selected]) or not validated:
        raise ValueError('Publication app lists are missing or empty')
    def valid_key(value):
        return isinstance(value, str) and re.fullmatch(r'[a-z0-9_]+', value) is not None
    if not all(valid_key(key) for key in selected) or len(selected) != len(set(selected)) or len(selected) != manifest['selected_count']:
        raise ValueError('Selected app identities differ')
    authorized = {}
    for row in validated:
        if not isinstance(row, dict) or set(row) != {'app_key', 'sha256', 'total_cves'} or not valid_key(row['app_key']):
            raise ValueError('Validated app identity differs')
        if row['app_key'] in authorized or not isinstance(row['sha256'], str) or re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is None or type(row['total_cves']) is not int or row['total_cves'] < 0:
            raise ValueError('Validated app binding differs')
        authorized[row['app_key']] = row
    stale_keys = []
    for row in stale:
        if not isinstance(row, dict) or set(row) != {'app_key', 'reason'} or not valid_key(row['app_key']) or not isinstance(row['reason'], str):
            raise ValueError('Stale app identity differs')
        stale_keys.append(row['app_key'])
    if len(stale_keys) != len(set(stale_keys)) or set(authorized).intersection(stale_keys) or set(authorized).union(stale_keys) != set(selected) or 10 * len(stale_keys) > len(selected):
        raise ValueError('Publication coverage or failure threshold differs')
    directory = Path(cve_dir)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('CVE directory must be regular')
    result = {}
    for key, row in authorized.items():
        file = directory / (key + '.json')
        if file.is_symlink() or not file.is_file():
            raise ValueError('Validated CVE file is missing or not regular')
        payload = file.read_bytes()
        if hashlib.sha256(payload).hexdigest() != row['sha256']:
            raise ValueError('Validated CVE file hash differs')
        data = strict_json(payload)
        if not isinstance(data, dict) or data.get('app_key') != key or not isinstance(data.get('vulnerabilities'), list) or type(data.get('total_cves')) is not int or data['total_cves'] != row['total_cves'] or data['total_cves'] != len(data['vulnerabilities']) or not all(isinstance(cve, dict) for cve in data['vulnerabilities']):
            raise ValueError('Validated CVE file contents differ')
        result[key] = {'app_name':data.get('app_name', key), 'app_key':key, 'summary':data.get('summary', {}),
                       'last_updated':data.get('last_updated'), 'cves':data['vulnerabilities']}
    print(f"Found {len(result)} CVE JSON files")
    print('Manifest validated apps: ' + ', '.join(result))
    print('Manifest stale apps preserved: ' + ', '.join(stale_keys))
    return result


# =============================================================================
# SUMMARY CALCULATION
# =============================================================================

def calculate_summary(cves: List[Dict]) -> Dict[str, int]:
    """Calculate CVE summary counts for all CVEs."""
    summary = {
        'critical_count': 0,
        'high_count': 0,
        'medium_count': 0,
        'low_count': 0,
        'kev_count': 0,
    }

    for cve in cves:
        severity = (cve.get('severity') or '').upper()
        if severity == 'CRITICAL':
            summary['critical_count'] += 1
        elif severity == 'HIGH':
            summary['high_count'] += 1
        elif severity == 'MEDIUM':
            summary['medium_count'] += 1
        elif severity == 'LOW':
            summary['low_count'] += 1

        if cve.get('is_kev'):
            summary['kev_count'] += 1

    return summary


def calculate_recent_summary(cves: List[Dict], latest_version: Optional[str]) -> Dict[str, int]:
    """Calculate CVE summary counts for CVEs fixed in recent versions."""
    summary = {
        'recent_total_cves': 0,
        'recent_critical_count': 0,
        'recent_high_count': 0,
        'recent_medium_count': 0,
        'recent_low_count': 0,
        'recent_kev_count': 0,
    }

    if not latest_version:
        return summary

    for cve in cves:
        fixed_version = cve.get('fixed_version')
        if not fixed_version:
            continue

        if not is_recent_fix(fixed_version, latest_version):
            continue

        # This CVE was fixed in a recent version
        summary['recent_total_cves'] += 1

        severity = (cve.get('severity') or '').upper()
        if severity == 'CRITICAL':
            summary['recent_critical_count'] += 1
        elif severity == 'HIGH':
            summary['recent_high_count'] += 1
        elif severity == 'MEDIUM':
            summary['recent_medium_count'] += 1
        elif severity == 'LOW':
            summary['recent_low_count'] += 1

        if cve.get('is_kev'):
            summary['recent_kev_count'] += 1

    return summary


# =============================================================================
# SUPABASE SYNC
# =============================================================================

def sync_to_supabase(
    supabase: Client,
    cve_data: Dict[str, Dict[str, Any]],
    app_versions: Dict[str, str],
    batch_size: int = 500
) -> Dict[str, int]:
    """Sync CVE data to Supabase. Returns stats about the sync."""
    stats = {
        'apps_synced': 0,
        'cves_synced': 0,
        'apps_with_recent_cves': 0,
        'errors': 0,
    }

    for app_key, app_data in cve_data.items():
        print('SYNC_APP ' + app_key)
        app_name = app_data['app_name']
        cves = app_data['cves']

        # Get latest version for this app
        latest_version = app_versions.get(app_key)

        print(f"\nSyncing {app_name} ({len(cves)} CVEs, latest: {latest_version or 'unknown'})...")

        # Calculate total summary
        total_summary = calculate_summary(cves)

        # Calculate recent summary (CVEs fixed in recent versions)
        recent_summary = calculate_recent_summary(cves, latest_version)

        if recent_summary['recent_total_cves'] > 0:
            stats['apps_with_recent_cves'] += 1
            print(f"  Recent CVEs: {recent_summary['recent_total_cves']} (Critical: {recent_summary['recent_critical_count']}, KEV: {recent_summary['recent_kev_count']})")

        # Use last_updated from file or current timestamp
        last_updated = app_data.get('last_updated')
        if last_updated:
            try:
                if 'T' not in last_updated:
                    last_updated = f"{last_updated}T00:00:00Z"
            except:
                last_updated = datetime.utcnow().isoformat()
        else:
            last_updated = datetime.utcnow().isoformat()

        # Build summary record with both total and recent counts
        summary_record = {
            'app_key': app_key,
            'app_name': app_name,
            'total_cves': len(cves),
            'critical_count': total_summary['critical_count'],
            'high_count': total_summary['high_count'],
            'medium_count': total_summary['medium_count'],
            'low_count': total_summary['low_count'],
            'kev_count': total_summary['kev_count'],
            'recent_total_cves': recent_summary['recent_total_cves'],
            'recent_critical_count': recent_summary['recent_critical_count'],
            'recent_high_count': recent_summary['recent_high_count'],
            'recent_medium_count': recent_summary['recent_medium_count'],
            'recent_low_count': recent_summary['recent_low_count'],
            'recent_kev_count': recent_summary['recent_kev_count'],
            'latest_version': latest_version,
            'last_updated': last_updated,
        }

        try:
            # Upsert summary
            supabase.table('app_cve_summaries').upsert(
                summary_record,
                on_conflict='app_key'
            ).execute()
            print(f"  Summary updated")
        except Exception as e:
            print(f"  Error upserting summary: {e}")
            stats['errors'] += 1
            continue

        # Delete existing CVE entries for this app
        try:
            supabase.table('cve_entries').delete().eq('app_key', app_key).execute()
        except Exception as e:
            print(f"  Error deleting old CVE entries: {e}")
            stats['errors'] += 1
            continue

        # Insert new CVE entries in batches
        if cves:
            cve_records = []
            for cve in cves:
                # Convert date strings to ISO format
                published_date = cve.get('published_date')
                if published_date and 'T' not in published_date:
                    published_date = f"{published_date}T00:00:00Z"

                last_modified = cve.get('last_modified_date')
                if last_modified and 'T' not in last_modified:
                    last_modified = f"{last_modified}T00:00:00Z"

                record = {
                    'app_key': app_key,
                    'cve_id': cve.get('cve_id'),
                    'published_date': published_date,
                    'last_modified_date': last_modified,
                    'description': cve.get('description'),
                    'base_score': cve.get('base_score'),
                    'severity': cve.get('severity'),
                    'cvss_version': cve.get('cvss_version'),
                    'cvss_vector': cve.get('cvss_vector'),
                    'affected_version_start': cve.get('affected_version_start'),
                    'affected_version_start_type': cve.get('affected_version_start_type'),
                    'affected_version_end': cve.get('affected_version_end'),
                    'affected_version_end_type': cve.get('affected_version_end_type'),
                    'fixed_version': cve.get('fixed_version'),
                    'is_kev': cve.get('is_kev', False),
                    'kev_date_added': cve.get('kev_date_added'),
                    'kev_due_date': cve.get('kev_due_date'),
                    'kev_ransomware_use': cve.get('kev_ransomware_use'),
                    'vendor': cve.get('vendor'),
                    'product': cve.get('product'),
                }
                cve_records.append(record)

            # Insert in batches
            for i in range(0, len(cve_records), batch_size):
                batch = cve_records[i:i + batch_size]
                try:
                    supabase.table('cve_entries').insert(batch).execute()
                    stats['cves_synced'] += len(batch)
                except Exception as e:
                    print(f"  Error inserting batch: {e}")
                    stats['errors'] += 1

        stats['apps_synced'] += 1
        print(f"  Done ({len(cves)} CVEs synced)")

    return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Sync CVE data to Supabase')
    parser.add_argument('--cve-dir', default='./CVE', help='Directory containing CVE JSON files')
    parser.add_argument('--apps-dir', default='./Apps', help='Directory containing app JSON files with versions')
    parser.add_argument('--manifest', required=True, help='Exact validated publication manifest from this run')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size for database inserts')
    args = parser.parse_args()

    # Fail closed before any database client or mutation, including after a commit rebase.
    try:
        cve_data = load_manifest_cves(args.cve_dir, args.manifest)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print('Error: publication manifest validation failed (' + type(exc).__name__ + ')')
        raise SystemExit(1)

    # Get Supabase credentials from environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")
        sys.exit(1)

    print("=" * 60)
    print("IntuneBrew CVE Sync to Supabase")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Supabase URL: {supabase_url}")
    print(f"CVE Directory: {args.cve_dir}")
    print(f"Apps Directory: {args.apps_dir}")
    print("=" * 60)

    # Create Supabase client
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    # Load app versions
    print(f"\nLoading app versions from: {args.apps_dir}")
    app_versions = load_app_versions(args.apps_dir)

    print(f"\nFound CVE data for {len(cve_data)} applications")

    # Sync to Supabase
    print("\nStarting sync to Supabase...")
    stats = sync_to_supabase(supabase, cve_data, app_versions, args.batch_size)

    # Print summary
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Apps synced: {stats['apps_synced']}")
    print(f"Apps with recent CVEs: {stats['apps_with_recent_cves']}")
    print(f"CVEs synced: {stats['cves_synced']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 60)

    if stats['errors'] > 0 or stats['apps_synced'] != len(cve_data):
        sys.exit(1)


if __name__ == '__main__':
    main()
