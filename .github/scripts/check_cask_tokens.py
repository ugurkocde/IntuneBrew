#!/usr/bin/env python3
"""Check that every Homebrew cask referenced by the catalog still exists.

Homebrew renames and retires casks. When that happens the token in
collect_app_info.py stops resolving, the collector can no longer refresh that
app, and its version silently freezes at whatever was last recorded. This is
distinct from check_download_urls.py, which checks the vendor download URL of
an app that was collected successfully.

The full cask index is fetched once rather than probing each token, so the
check costs a single request regardless of catalog size. For every missing
token the closest surviving cask is suggested, since the usual cause is a
rename such as tailscale -> tailscale-app.

Exit code is always 0. The number of missing tokens is exposed through the
GITHUB_OUTPUT variable "missing_count" and the report is written to
cask-token-report.md in the working directory.
"""

import datetime
import json
import os
import re
import sys
from difflib import SequenceMatcher

import requests

SCRIPT_FILE = ".github/scripts/collect_app_info.py"
APPS_FOLDER = "Apps"
REPORT_FILE = "cask-token-report.md"
CASK_INDEX_URL = "https://formulae.brew.sh/api/cask.json"
TIMEOUT_SECONDS = 60

# Only offer a rename suggestion when it is close enough to be plausible.
SUGGESTION_THRESHOLD = 0.6


def referenced_tokens(path):
    """Every cask token referenced by the catalog source, in file order."""
    with open(path) as f:
        content = f.read()
    # Preserve first-seen order so the report is stable between runs.
    seen = {}
    for match in re.finditer(r"formulae\.brew\.sh/api/cask/([^\"']+)\.json", content):
        seen.setdefault(match.group(1), None)
    return list(seen)


def fetch_cask_index():
    """Fetch the full Homebrew cask list. Returns None on failure."""
    try:
        response = requests.get(CASK_INDEX_URL, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Could not fetch the Homebrew cask index: {e}", file=sys.stderr)
        return None


def suggest_rename(token, available):
    """Find the most plausible surviving cask for a token that disappeared."""
    best, best_score = None, 0.0
    for candidate in available:
        ratio = SequenceMatcher(None, token, candidate).ratio()
        # A rename usually keeps the old token as a prefix (tailscale-app) or
        # drops a suffix, so rank those above plain similarity. Several casks
        # can share a prefix (wireshark-app, wireshark-chmodbpf), so keep the
        # ratio in the score to break the tie toward the closest name.
        if candidate.startswith(token + "-") or token.startswith(candidate + "-"):
            score = 0.9 + 0.1 * ratio
        else:
            score = ratio
        if score > best_score:
            best, best_score = candidate, score
    if best_score >= SUGGESTION_THRESHOLD:
        return best, best_score
    return None, 0.0


def affected_app(token):
    """Find the catalog entry that depends on a token, if one exists."""
    if not os.path.isdir(APPS_FOLDER):
        return None
    for filename in sorted(os.listdir(APPS_FOLDER)):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(APPS_FOLDER, filename)) as f:
                data = json.load(f)
        except (ValueError, OSError):
            continue
        if data.get("homebrew_cask") == token:
            return {
                "name": data.get("name", filename[: -len(".json")]),
                "version": data.get("version", ""),
                "deprecated": bool(data.get("deprecated")),
            }
    return None


def write_report(lines):
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")


def set_output(name, value):
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    tokens = referenced_tokens(SCRIPT_FILE)
    print(f"Catalog references {len(tokens)} Homebrew casks")

    index = fetch_cask_index()
    if index is None:
        # Treat an unreachable index as "nothing to report" rather than
        # flagging every token as missing and opening an alarming issue.
        write_report(["Could not reach the Homebrew cask index, check skipped."])
        set_output("missing_count", "0")
        return 0

    available = {cask.get("token", "") for cask in index}
    available.discard("")
    print(f"Homebrew currently publishes {len(available)} casks")

    missing = []
    for token in tokens:
        if token in available:
            continue
        suggestion, score = suggest_rename(token, available)
        app = affected_app(token)
        missing.append({
            "token": token,
            "suggestion": suggestion,
            "score": score,
            "app": app,
        })
        print(f"MISSING {token}" + (f" -> suggest {suggestion}" if suggestion else ""))

    # A cask that is already flagged deprecated is a known loss. An app still
    # serving users from a frozen version is the one that needs attention, so
    # list those first.
    missing.sort(key=lambda item: (
        bool(item["app"] and item["app"]["deprecated"]),
        item["app"] is None,
        item["token"],
    ))

    live_count = sum(
        1 for item in missing if item["app"] and not item["app"]["deprecated"]
    )

    today = datetime.date.today().isoformat()
    lines = [
        f"Automated Homebrew cask token check from {today}.",
        "",
        f"Checked {len(tokens)} cask tokens, found {len(missing)} that no longer exist, "
        f"{live_count} of which back an app that is still live in the catalog.",
        "",
    ]

    if missing:
        lines += [
            "These casks were renamed or retired by Homebrew. The collector cannot "
            "refresh them, so their version is frozen at whatever was last recorded. "
            "Update the token in `collect_app_info.py`, or mark the app deprecated "
            "if it is genuinely gone. Rows are ordered with still-live apps first, "
            "since those are the ones silently serving a stale version.",
            "",
            "| Cask | Catalog app | Frozen at | Likely replacement |",
            "| --- | --- | --- | --- |",
        ]
        for item in missing:
            app = item["app"]
            app_name = app["name"] if app else "not in catalog"
            if app and app["deprecated"]:
                app_name += " (deprecated)"
            version = app["version"] if app else ""
            replacement = (
                f"`{item['suggestion']}` ({int(item['score'] * 100)}%)"
                if item["suggestion"] else "none found"
            )
            lines.append(f"| `{item['token']}` | {app_name} | {version} | {replacement} |")
    else:
        lines.append("Every referenced cask still exists.")

    write_report(lines)
    set_output("missing_count", str(len(missing)))
    print(f"\n{len(missing)} of {len(tokens)} tokens are missing. Report written to {REPORT_FILE}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
