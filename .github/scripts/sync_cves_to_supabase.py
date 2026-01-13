#!/usr/bin/env python3
"""
CVE Data Sync Script for IntuneBrew

This script syncs CVE data from the CVE/ directory to Supabase.
Run automatically as part of the check-app-cves.yml workflow.

Required environment variables:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Service role key for write access

Usage:
    python sync_cves_to_supabase.py [--cve-dir ./CVE]
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py not installed. Run: pip install supabase")
    sys.exit(1)


def load_cve_files(cve_dir: str) -> Dict[str, Dict[str, Any]]:
    """Load all CVE JSON files from the specified directory."""
    cve_data = {}
    cve_path = Path(cve_dir)

    if not cve_path.exists():
        print(f"Warning: CVE directory '{cve_dir}' does not exist")
        return cve_data

    json_files = list(cve_path.glob("*.json"))
    print(f"Found {len(json_files)} CVE JSON files")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Use app_key from file if available, otherwise derive from filename
                app_key = data.get('app_key', json_file.stem)
                app_name = data.get('app_name', app_key)

                # CVEs are in 'vulnerabilities' key in the existing format
                vulnerabilities = data.get('vulnerabilities', data.get('cves', []))

                cve_data[app_key] = {
                    'app_name': app_name,
                    'app_key': app_key,
                    'summary': data.get('summary', {}),
                    'last_updated': data.get('last_updated'),
                    'cves': vulnerabilities
                }

                if vulnerabilities:
                    print(f"  Loaded {len(vulnerabilities)} CVEs for {app_name}")

        except json.JSONDecodeError as e:
            print(f"Error parsing {json_file}: {e}")
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    return cve_data


def calculate_summary(cves: List[Dict]) -> Dict[str, int]:
    """Calculate CVE summary counts."""
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


def sync_to_supabase(supabase: Client, cve_data: Dict[str, Dict[str, Any]], batch_size: int = 500) -> Dict[str, int]:
    """Sync CVE data to Supabase. Returns stats about the sync."""
    stats = {
        'apps_synced': 0,
        'cves_synced': 0,
        'errors': 0,
    }

    for app_key, app_data in cve_data.items():
        app_name = app_data['app_name']
        cves = app_data['cves']

        print(f"\nSyncing {app_name} ({len(cves)} CVEs)...")

        # Calculate summary from CVEs
        summary = calculate_summary(cves)

        # Use last_updated from file or current timestamp
        last_updated = app_data.get('last_updated')
        if last_updated:
            # Convert date string to ISO format if needed
            try:
                if 'T' not in last_updated:
                    last_updated = f"{last_updated}T00:00:00Z"
            except:
                last_updated = datetime.utcnow().isoformat()
        else:
            last_updated = datetime.utcnow().isoformat()

        # Build summary record
        summary_record = {
            'app_key': app_key,
            'app_name': app_name,
            'total_cves': len(cves),
            'critical_count': summary['critical_count'],
            'high_count': summary['high_count'],
            'medium_count': summary['medium_count'],
            'low_count': summary['low_count'],
            'kev_count': summary['kev_count'],
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


def main():
    parser = argparse.ArgumentParser(description='Sync CVE data to Supabase')
    parser.add_argument('--cve-dir', default='./CVE', help='Directory containing CVE JSON files')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size for database inserts')
    args = parser.parse_args()

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
    print("=" * 60)

    # Create Supabase client
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    # Load CVE data
    print(f"\nLoading CVE data from: {args.cve_dir}")
    cve_data = load_cve_files(args.cve_dir)

    if not cve_data:
        print("No CVE data found to sync")
        sys.exit(0)

    print(f"\nFound CVE data for {len(cve_data)} applications")

    # Sync to Supabase
    print("\nStarting sync to Supabase...")
    stats = sync_to_supabase(supabase, cve_data, args.batch_size)

    # Print summary
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Apps synced: {stats['apps_synced']}")
    print(f"CVEs synced: {stats['cves_synced']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 60)

    if stats['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
