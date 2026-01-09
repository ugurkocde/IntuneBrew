#!/usr/bin/env python3
"""
Script to add a new app to IntuneBrew based on GitHub issue content.

This script:
1. Parses the issue title/body to extract the app name or Homebrew cask name
2. Searches Homebrew if no direct cask name is found
3. Fetches app info from Homebrew API to determine the app type
4. Adds the URL to the appropriate list in collect_app_info.py
5. Outputs the result for the GitHub Action
"""

import os
import re
import sys
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
    print(f"Output: {name}={value}")

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
    # Convert to lowercase
    name = name.lower()
    # Remove common suffixes
    name = re.sub(r'\s*(app|application|client|desktop|for mac|for macos|macos|mac)$', '', name, flags=re.IGNORECASE)
    # Replace special characters with spaces
    name = re.sub(r'[_\-\.]+', ' ', name)
    # Remove extra whitespace
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

        # Calculate various similarity scores
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

        if best_score >= 0.4:  # Minimum threshold
            results.append((token, cask, best_score))

    # Sort by score descending
    results.sort(key=lambda x: x[2], reverse=True)

    return results[:10]  # Return top 10 matches

def extract_app_name_from_issue(issue_title, issue_body):
    """Extract the app name from issue title and body."""

    # Try various patterns in the title
    patterns = [
        # [Feature] Add AppName to IntuneBrew
        r'\[Feature\]\s*Add\s+(.+?)\s+to\s+(?:IntuneBrew|the\s+)?(?:Application\s+)?(?:List)?',
        # Add AppName
        r'^Add\s+(.+?)(?:\s+to|\s*$)',
        # Request: AppName
        r'Request[:\s]+(.+?)(?:\s+to|\s*$)',
        # AppName request
        r'^(.+?)\s+request',
    ]

    for pattern in patterns:
        match = re.search(pattern, issue_title, re.IGNORECASE)
        if match:
            app_name = match.group(1).strip()
            # Clean up the app name
            app_name = re.sub(r'\s+to\s+IntuneBrew.*$', '', app_name, flags=re.IGNORECASE)
            app_name = re.sub(r'\s+application\s+list.*$', '', app_name, flags=re.IGNORECASE)
            if app_name and len(app_name) > 1:
                return app_name

    # Try to find app name in body if title didn't work
    # Look for patterns like "App name: xyz" or "Application: xyz"
    body_patterns = [
        r'app\s*(?:name)?[:\s]+([^\n,]+)',
        r'application[:\s]+([^\n,]+)',
        r'software[:\s]+([^\n,]+)',
        r'requesting[:\s]+([^\n,]+)',
    ]

    for pattern in body_patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE)
        if match:
            app_name = match.group(1).strip()
            if app_name and len(app_name) > 1 and len(app_name) < 50:
                return app_name

    return None

def extract_cask_name(issue_title, issue_body, comment_body):
    """
    Extract or find the Homebrew cask name from the issue or comment.

    Returns: tuple (cask_name, is_exact_match, search_results)
    - cask_name: The Homebrew cask token
    - is_exact_match: True if we found an exact URL/cask reference
    - search_results: List of alternative matches if search was used
    """

    # Check if comment has a specific cask name override (e.g., "/approve signal")
    comment_match = re.search(r'/approve\s+(\S+)', comment_body)
    if comment_match:
        cask_name = comment_match.group(1).strip()
        return cask_name, True, []

    # Try to find Homebrew API URL
    api_pattern = r'formulae\.brew\.sh/api/cask/([^/\s.]+)\.json'
    match = re.search(api_pattern, issue_body)
    if match:
        return match.group(1), True, []

    # Try to find Homebrew cask page URL
    cask_pattern = r'formulae\.brew\.sh/cask/([^/\s]+)'
    match = re.search(cask_pattern, issue_body)
    if match:
        return match.group(1), True, []

    # Try to find "brew install --cask" command
    brew_pattern = r'brew\s+install\s+(?:--cask\s+)?([^\s]+)'
    match = re.search(brew_pattern, issue_body)
    if match:
        return match.group(1), True, []

    # No direct cask reference found, extract app name and search
    app_name = extract_app_name_from_issue(issue_title, issue_body)

    if not app_name:
        return None, False, []

    print(f"No direct cask reference found. Searching Homebrew for: '{app_name}'")

    # Search Homebrew
    search_results = search_homebrew_casks(app_name)

    if not search_results:
        return None, False, []

    # Get the best match
    best_match = search_results[0]
    best_token, best_cask, best_score = best_match

    print(f"Best match: {best_token} (score: {best_score:.2f})")
    print(f"  Names: {best_cask.get('name', [])}")

    # If score is high enough, use it automatically
    if best_score >= 0.7:
        return best_token, False, search_results

    # If score is moderate, still use it but include alternatives
    if best_score >= 0.5:
        return best_token, False, search_results

    # Score too low, return results for manual review
    return None, False, search_results

def fetch_homebrew_info(cask_name):
    """Fetch app information from Homebrew API."""
    url = f"https://formulae.brew.sh/api/cask/{cask_name}.json"
    print(f"Fetching Homebrew info from: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise

def determine_app_type(homebrew_data):
    """
    Determine which list the app should be added to based on the download URL
    and artifact information.

    Returns: tuple (list_name, type_value)
    - list_name: The Python variable name in collect_app_info.py
    - type_value: The type to be stored in the JSON (or None for DMG)
    """
    url = homebrew_data.get('url', '').lower()
    artifacts = homebrew_data.get('artifacts', [])

    # Extract actual file extension from URL (handles redirects like ?file=app.dmg)
    def get_url_extension(url):
        # Check for file parameter in URL (e.g., rotation.php?file=HandBrake.dmg)
        import re
        file_match = re.search(r'[?&]file=([^&]+)', url)
        if file_match:
            return file_match.group(1).lower()
        # Get the last path segment
        path = url.split('?')[0].split('/')[-1].lower()
        return path

    url_file = get_url_extension(url)

    # Check artifacts first - they're more reliable than URL
    has_pkg_artifact = False
    has_app_artifact = False

    for artifact in artifacts:
        if isinstance(artifact, dict):
            if 'pkg' in artifact:
                has_pkg_artifact = True
            if 'app' in artifact:
                has_app_artifact = True

    # Determine file type from URL
    is_pkg_url = url_file.endswith('.pkg')
    is_dmg_url = url_file.endswith('.dmg')
    is_archive_url = any(url_file.endswith(ext) for ext in ['.zip', '.tar.gz', '.tar.xz', '.tar.bz2', '.tbz', '.tgz'])

    # Decision logic:
    # 1. If URL is PKG and has pkg artifact -> direct PKG
    # 2. If URL is DMG and has pkg artifact -> PKG in DMG
    # 3. If URL is DMG and has app artifact -> regular DMG
    # 4. If URL is archive (zip/tar) -> needs repackaging (app type)
    # 5. If URL has no extension but has pkg artifact -> direct PKG
    # 6. If URL has no extension but has app artifact -> needs repackaging (ZIP download)

    if is_pkg_url:
        if has_pkg_artifact:
            # Check if it might be pkg-in-pkg (nested package)
            # This is harder to detect, usually these are special cases
            return 'pkg_urls', 'pkg'
        return 'pkg_urls', 'pkg'

    if is_dmg_url:
        if has_pkg_artifact:
            return 'pkg_in_dmg_urls', 'pkg_in_dmg'
        return 'homebrew_cask_urls', None

    if is_archive_url:
        return 'app_urls', 'app'

    # URL doesn't have a clear extension - use artifacts to decide
    if has_pkg_artifact:
        # It's a PKG download (like cloudflare-warp)
        return 'pkg_urls', 'pkg'

    if has_app_artifact:
        # It's likely a ZIP or archive that extracts to .app (like VS Code)
        return 'app_urls', 'app'

    # Default to DMG list if we can't determine
    print(f"Warning: Could not determine app type for URL: {url}")
    return 'homebrew_cask_urls', None

def check_app_exists(cask_name, script_content):
    """Check if the app already exists in any of the lists."""
    pattern = rf'formulae\.brew\.sh/api/cask/{re.escape(cask_name)}\.json'
    return bool(re.search(pattern, script_content))

def add_url_to_list(script_path, list_name, cask_name):
    """Add the Homebrew URL to the appropriate list in collect_app_info.py."""

    with open(script_path, 'r') as f:
        lines = f.readlines()

    content = ''.join(lines)

    # Check if app already exists
    if check_app_exists(cask_name, content):
        return False, "App already exists in the supported apps list"

    # Find the list and the position to insert
    url_to_add = f'    "https://formulae.brew.sh/api/cask/{cask_name}.json",\n'

    # Find the line where the list starts
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
                # Found the closing bracket
                break

    if list_start_line == -1:
        return False, f"Could not find list '{list_name}' in collect_app_info.py"

    # Insert after the last URL line
    if last_url_line == -1:
        # Empty list, insert after the opening bracket
        insert_line = list_start_line + 1
    else:
        insert_line = last_url_line + 1

    # Insert the new URL
    lines.insert(insert_line, url_to_add)

    with open(script_path, 'w') as f:
        f.writelines(lines)

    return True, None

def main():
    # Get environment variables
    issue_title = os.environ.get('ISSUE_TITLE', '')
    issue_body = os.environ.get('ISSUE_BODY', '')
    comment_body = os.environ.get('COMMENT_BODY', '')

    print(f"Issue title: {issue_title}")
    print(f"Issue body length: {len(issue_body)}")
    print(f"Comment body: {comment_body}")

    # Extract cask name (with search if needed)
    cask_name, is_exact, search_results = extract_cask_name(issue_title, issue_body, comment_body)

    if not cask_name:
        if search_results:
            # We found some matches but none were confident enough
            suggestions = "\n".join([
                f"  - `{token}` ({cask.get('name', ['Unknown'])[0]}) - score: {score:.0%}"
                for token, cask, score in search_results[:5]
            ])
            set_failed(
                f"Could not confidently match the app name. Possible matches:\n{suggestions}\n\n"
                f"To approve one of these, comment: /approve <cask-name>"
            )
        else:
            set_failed(
                "Could not find the app on Homebrew. Please ensure:\n"
                "1. The app is available as a Homebrew cask\n"
                "2. The issue title clearly states the app name\n"
                "3. Or include a Homebrew URL in the issue body"
            )
        sys.exit(1)

    print(f"Using cask name: {cask_name}")
    set_output('cask_name', cask_name)

    # If we used search, output the alternatives
    if not is_exact and search_results:
        alternatives = ", ".join([f"`{t}`" for t, _, _ in search_results[1:4]])
        if alternatives:
            set_output('alternatives', alternatives)

    # Fetch Homebrew info to verify and get details
    homebrew_data = fetch_homebrew_info(cask_name)

    if not homebrew_data:
        if search_results and len(search_results) > 1:
            # Try the next best match
            next_best = search_results[1]
            set_failed(
                f"Could not find '{cask_name}' on Homebrew. "
                f"Did you mean `{next_best[0]}`? Try: /approve {next_best[0]}"
            )
        else:
            set_failed(f"Could not find '{cask_name}' on Homebrew. Please verify the cask name is correct.")
        sys.exit(1)

    # Get app name
    app_name = homebrew_data.get('name', [cask_name])
    if isinstance(app_name, list):
        app_name = app_name[0] if app_name else cask_name
    print(f"App name: {app_name}")
    set_output('app_name', app_name)

    # Determine app type
    list_name, app_type = determine_app_type(homebrew_data)
    print(f"Determined list: {list_name}, type: {app_type}")
    set_output('app_type', app_type or 'dmg')

    # Add to collect_app_info.py
    script_path = '.github/scripts/collect_app_info.py'

    success, error = add_url_to_list(script_path, list_name, cask_name)

    if not success:
        set_failed(error)
        sys.exit(1)

    print(f"Successfully added {cask_name} to {list_name}")
    set_output('app_added', 'true')

    # If search was used, mention it
    if not is_exact:
        set_output('search_used', 'true')
        print(f"Note: App was found via search, not direct URL reference")

if __name__ == '__main__':
    main()
