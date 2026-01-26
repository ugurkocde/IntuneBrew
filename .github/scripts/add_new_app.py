#!/usr/bin/env python3
"""
Script to add new apps to IntuneBrew based on GitHub issue content.

This script:
1. Parses the comment for specific cask names (/approve cask1, cask2)
2. Or extracts app names from issue title/body
3. Searches Homebrew for each app
4. Adds all found apps to the appropriate lists in collect_app_info.py
5. Outputs the results for the GitHub Action
"""

import os
import re
import sys
import json
import requests
from difflib import SequenceMatcher

# Cache for the Homebrew cask list
_cask_list_cache = None

def set_output(name, value):
    """Set GitHub Actions output."""
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            # Handle multi-line values
            if '\n' in str(value):
                import uuid
                delimiter = uuid.uuid4().hex
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")
    print(f"Output: {name}={value[:100]}..." if len(str(value)) > 100 else f"Output: {name}={value}")

def set_failed(message):
    """Set the action as failed with an error message."""
    set_output('app_added', 'false')
    set_output('error_message', message)
    print(f"Error: {message}", file=sys.stderr)

def get_homebrew_cask_list():
    """Fetch the full list of Homebrew casks."""
    global _cask_list_cache

    if _cask_list_cache is not None:
        return _cask_list_cache

    print("Fetching Homebrew cask list...")
    url = "https://formulae.brew.sh/api/cask.json"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        _cask_list_cache = response.json()
        print(f"Loaded {len(_cask_list_cache)} casks from Homebrew")
        return _cask_list_cache
    except Exception as e:
        print(f"Error fetching cask list: {e}")
        return []

def normalize_name(name):
    """Normalize an app name for comparison."""
    name = name.lower()
    name = re.sub(r'\s*(app|application|client|desktop|for mac|for macos|macos|mac)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[_\-\.]+', ' ', name)
    name = ' '.join(name.split())
    return name

def similarity_score(s1, s2):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def search_homebrew_casks(search_term):
    """
    Search Homebrew casks for a matching app.
    Returns a list of (cask_token, cask_data, score) tuples sorted by relevance.
    """
    casks = get_homebrew_cask_list()
    if not casks:
        return []

    search_normalized = normalize_name(search_term)
    search_words = set(search_normalized.split())

    results = []

    for cask in casks:
        token = cask.get('token', '')
        names = cask.get('name', [])
        if isinstance(names, str):
            names = [names]

        scores = []

        # Exact token match (highest priority)
        if token.lower() == search_term.lower():
            scores.append(1.0)
        elif token.lower() == search_term.lower().replace(' ', '-'):
            scores.append(0.98)

        # Token similarity
        token_normalized = normalize_name(token)
        scores.append(similarity_score(search_normalized, token_normalized) * 0.9)

        # Check each name
        for name in names:
            name_normalized = normalize_name(name)

            # Exact name match
            if name_normalized == search_normalized:
                scores.append(0.95)

            # Name similarity
            scores.append(similarity_score(search_normalized, name_normalized) * 0.85)

            # Word overlap
            name_words = set(name_normalized.split())
            if search_words and name_words:
                overlap = len(search_words & name_words) / max(len(search_words), len(name_words))
                scores.append(overlap * 0.8)

        # Token contains search term or vice versa
        if search_normalized.replace(' ', '') in token.replace('-', ''):
            scores.append(0.7)
        if token.replace('-', '') in search_normalized.replace(' ', ''):
            scores.append(0.7)

        best_score = max(scores) if scores else 0

        if best_score >= 0.5:  # Minimum threshold
            results.append((token, cask, best_score))

    # Sort by score descending
    results.sort(key=lambda x: x[2], reverse=True)

    return results[:5]  # Return top 5 matches

def extract_casks_from_comment(comment_body):
    """Extract specific cask names from /approve command."""
    # Match /approve followed by cask names (comma or space separated)
    match = re.search(r'/approve\s+([^\n]+)', comment_body, re.IGNORECASE)
    if match:
        casks_str = match.group(1).strip()
        # Split by comma, space, or both
        casks = re.split(r'[,\s]+', casks_str)
        # Filter out empty strings and common words
        casks = [c.strip() for c in casks if c.strip() and c.strip().lower() not in ['and', 'the', 'to']]
        return casks
    return []

def extract_casks_from_urls(issue_body):
    """Extract all cask names from Homebrew URLs in the issue body."""
    casks = []
    # Homebrew API URLs
    for match in re.finditer(r'formulae\.brew\.sh/api/cask/([^/\s.]+)\.json', issue_body):
        if match.group(1) not in casks:
            casks.append(match.group(1))
    # Homebrew cask page URLs
    for match in re.finditer(r'formulae\.brew\.sh/cask/([^/\s\)]+)', issue_body):
        if match.group(1) not in casks:
            casks.append(match.group(1))
    # brew install commands
    for match in re.finditer(r'brew\s+install\s+(?:--cask\s+)?([^\s\n]+)', issue_body):
        if match.group(1) not in casks:
            casks.append(match.group(1))
    return casks

def extract_app_names_from_title(issue_title):
    """Extract multiple app names from issue title."""
    app_names = []

    patterns = [
        r'\[Feature\]\s*Add\s+(.+?)\s+to\s+(?:IntuneBrew|the\s+)?(?:app(?:lication)?\s+)?(?:list)?',
        r'^Add\s+(.+?)\s+to\s+',
        r'^Add\s+(.+?)$',
        r'Request[:\s]+(.+?)(?:\s+to|\s*$)',
    ]

    apps_string = None
    for pattern in patterns:
        match = re.search(pattern, issue_title, re.IGNORECASE)
        if match:
            apps_string = match.group(1).strip()
            break

    if apps_string:
        # Split by comma, "and", or "&"
        parts = re.split(r'\s*[,&]\s*|\s+and\s+', apps_string)
        for part in parts:
            part = part.strip()
            part = re.sub(r'\s+to\s+IntuneBrew.*$', '', part, flags=re.IGNORECASE)
            part = re.sub(r'\s+application\s+list.*$', '', part, flags=re.IGNORECASE)
            if part and len(part) > 1:
                app_names.append(part)

    return app_names

def fetch_homebrew_info(cask_name):
    """Fetch app information from Homebrew API."""
    url = f"https://formulae.brew.sh/api/cask/{cask_name}.json"
    print(f"Fetching Homebrew info for: {cask_name}")

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        return None
    except Exception as e:
        print(f"Error fetching {cask_name}: {e}")
        return None

def determine_app_type(homebrew_data):
    """
    Determine which list the app should be added to based on the download URL
    and artifact information.

    Returns: tuple (list_name, type_value)
    """
    url = homebrew_data.get('url', '').lower()
    artifacts = homebrew_data.get('artifacts', [])

    def get_url_extension(url):
        file_match = re.search(r'[?&]file=([^&]+)', url)
        if file_match:
            return file_match.group(1).lower()
        path = url.split('?')[0].split('/')[-1].lower()
        return path

    url_file = get_url_extension(url)

    has_pkg_artifact = any(isinstance(a, dict) and 'pkg' in a for a in artifacts)
    has_app_artifact = any(isinstance(a, dict) and 'app' in a for a in artifacts)

    is_pkg_url = url_file.endswith('.pkg')
    is_dmg_url = url_file.endswith('.dmg')
    is_archive_url = any(url_file.endswith(ext) for ext in ['.zip', '.tar.gz', '.tar.xz', '.tar.bz2', '.tbz', '.tgz'])

    if is_pkg_url:
        return 'pkg_urls', 'pkg'

    if is_dmg_url:
        if has_pkg_artifact:
            return 'pkg_in_dmg_urls', 'pkg_in_dmg'
        return 'homebrew_cask_urls', 'dmg'

    if is_archive_url:
        return 'app_urls', 'app'

    # URL doesn't have a clear extension - use artifacts to decide
    if has_pkg_artifact:
        return 'pkg_urls', 'pkg'

    if has_app_artifact:
        return 'app_urls', 'app'

    # Default to DMG list
    print(f"Warning: Could not determine app type for URL: {url}")
    return 'homebrew_cask_urls', 'dmg'

def check_app_exists(cask_name, script_content):
    """Check if the app already exists in any of the lists."""
    pattern = rf'formulae\.brew\.sh/api/cask/{re.escape(cask_name)}\.json'
    return bool(re.search(pattern, script_content))

def add_url_to_list(script_path, list_name, cask_name, lines):
    """Add the Homebrew URL to the appropriate list. Modifies lines in place."""
    url_to_add = f'    "https://formulae.brew.sh/api/cask/{cask_name}.json",\n'

    list_start_pattern = rf'^{re.escape(list_name)}\s*=\s*\['
    list_start_line = -1
    in_target_list = False
    last_url_line = -1
    bracket_count = 0

    for i, line in enumerate(lines):
        if re.match(list_start_pattern, line):
            list_start_line = i
            in_target_list = True
            bracket_count = line.count('[') - line.count(']')
            if 'formulae.brew.sh' in line:
                last_url_line = i
            continue

        if in_target_list:
            bracket_count += line.count('[') - line.count(']')
            if 'formulae.brew.sh' in line:
                last_url_line = i
            if bracket_count <= 0:
                break

    if list_start_line == -1:
        return False, f"Could not find list '{list_name}' in collect_app_info.py"

    if last_url_line == -1:
        insert_line = list_start_line + 1
    else:
        # Ensure the previous line has a trailing comma to avoid string concatenation
        prev_line = lines[last_url_line].rstrip('\n')
        if prev_line.rstrip().endswith('"') and not prev_line.rstrip().endswith('",'):
            # Add comma to the previous line
            lines[last_url_line] = prev_line.rstrip() + ',\n'
        insert_line = last_url_line + 1

    lines.insert(insert_line, url_to_add)
    return True, None

def main():
    issue_title = os.environ.get('ISSUE_TITLE', '')
    issue_body = os.environ.get('ISSUE_BODY', '')
    comment_body = os.environ.get('COMMENT_BODY', '')

    print(f"Issue title: {issue_title}")
    print(f"Comment body: {comment_body}")

    script_path = '.github/scripts/collect_app_info.py'

    # Read the script content
    with open(script_path, 'r') as f:
        lines = f.readlines()
    content = ''.join(lines)

    # Determine which casks to add
    casks_to_process = []

    # First, check if specific casks are mentioned in the /approve command
    specific_casks = extract_casks_from_comment(comment_body)
    if specific_casks:
        print(f"Specific casks from command: {specific_casks}")
        casks_to_process = specific_casks
    else:
        # Try to extract from URLs in issue body
        casks_from_urls = extract_casks_from_urls(issue_body)
        if casks_from_urls:
            print(f"Casks from URLs: {casks_from_urls}")
            casks_to_process = casks_from_urls
        else:
            # Search by app names from title
            app_names = extract_app_names_from_title(issue_title)
            print(f"App names from title: {app_names}")
            for app_name in app_names:
                results = search_homebrew_casks(app_name)
                if results:
                    best_token, _, best_score = results[0]
                    if best_score >= 0.5:
                        print(f"  Found: {best_token} (score: {best_score:.2f})")
                        if best_token not in casks_to_process:
                            casks_to_process.append(best_token)
                    else:
                        print(f"  Low score for {app_name}: {best_token} ({best_score:.2f})")

    if not casks_to_process:
        set_failed("Could not find any apps to add. Please specify cask names: /approve cask1, cask2")
        sys.exit(1)

    # Process each cask
    added_apps = []
    skipped_apps = []
    failed_apps = []

    for cask_name in casks_to_process:
        # Check if already exists
        if check_app_exists(cask_name, content):
            print(f"Skipping {cask_name}: already exists")
            skipped_apps.append({'cask': cask_name, 'reason': 'already exists'})
            continue

        # Fetch Homebrew info
        homebrew_data = fetch_homebrew_info(cask_name)
        if not homebrew_data:
            print(f"Failed {cask_name}: not found on Homebrew")
            failed_apps.append({'cask': cask_name, 'reason': 'not found on Homebrew'})
            continue

        # Get app name
        app_name = homebrew_data.get('name', [cask_name])
        if isinstance(app_name, list):
            app_name = app_name[0] if app_name else cask_name

        # Determine app type
        list_name, app_type = determine_app_type(homebrew_data)
        print(f"Adding {cask_name} ({app_name}) to {list_name} as {app_type}")

        # Add to list
        success, error = add_url_to_list(script_path, list_name, cask_name, lines)
        if success:
            # Update content for subsequent checks
            content = ''.join(lines)
            added_apps.append({
                'cask': cask_name,
                'name': app_name,
                'type': app_type,
                'list': list_name
            })
        else:
            print(f"Failed to add {cask_name}: {error}")
            failed_apps.append({'cask': cask_name, 'reason': error})

    # Write the updated file if any apps were added
    if added_apps:
        with open(script_path, 'w') as f:
            f.writelines(lines)

        # Generate commit message
        if len(added_apps) == 1:
            commit_msg = f"{added_apps[0]['name']} to supported apps list"
        else:
            app_names = [a['name'] for a in added_apps]
            if len(app_names) <= 3:
                commit_msg = f"{', '.join(app_names)} to supported apps list"
            else:
                commit_msg = f"{len(added_apps)} apps to supported apps list"

        set_output('app_added', 'true')
        set_output('apps_json', json.dumps(added_apps))
        set_output('commit_message', commit_msg)
        set_output('added_count', str(len(added_apps)))

        # For single app compatibility
        if len(added_apps) == 1:
            set_output('app_name', added_apps[0]['name'])
            set_output('cask_name', added_apps[0]['cask'])
            set_output('app_type', added_apps[0]['type'])

        print(f"\nSuccessfully added {len(added_apps)} app(s)")
    else:
        if skipped_apps:
            skipped_list = ', '.join(a['cask'] for a in skipped_apps)
            set_failed(f"All apps already exist: {skipped_list}")
        elif failed_apps:
            failed_list = ', '.join(f"{a['cask']} ({a['reason']})" for a in failed_apps)
            set_failed(f"Failed to add apps: {failed_list}")
        else:
            set_failed("No apps were added")
        sys.exit(1)

    # Output summary
    if skipped_apps:
        set_output('skipped', json.dumps(skipped_apps))
        print(f"Skipped {len(skipped_apps)} app(s): {', '.join(a['cask'] for a in skipped_apps)}")
    if failed_apps:
        set_output('failed', json.dumps(failed_apps))
        print(f"Failed {len(failed_apps)} app(s): {', '.join(a['cask'] for a in failed_apps)}")

if __name__ == '__main__':
    main()
