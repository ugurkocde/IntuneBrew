#!/usr/bin/env python3
"""Track app requests from approval until the app is actually live.

An approved request is committed to collect_app_info.py within seconds, but the
app is not downloadable until the build workflow has packaged it roughly twenty
minutes later. Nothing connected those two events, so the requester had to poll
the Actions tab to find out whether their app had landed.

This script maintains .github/pending-requests.json as the hand-off between the
two workflows:

  record   auto-approve-app-request.yml writes the issue number and the casks
           it just added.
  resolve  build-app-packages.yml checks which of those casks are now in the
           catalog, emits pending-notifications.json for the workflow to
           comment with, and drops the resolved entries.

Exit code is always 0. A missing, empty or corrupt state file is treated as "no
pending requests" so that a bad file can never fail a build.
"""

import datetime
import json
import os
import sys

STATE_FILE = ".github/pending-requests.json"
NOTIFICATIONS_FILE = "pending-notifications.json"
APPS_FOLDER = "Apps"

# Entries older than this are dropped. A request that has not resolved in three
# days is not going to, usually because the build failed for that app, and we
# would rather forget it than comment on it weeks later.
MAX_AGE_DAYS = 3


def set_output(name, value):
    """Set a GitHub Actions output."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")
    print(f"Output: {name}={value}")


def load_state():
    """Read the pending request list, tolerating a missing or damaged file."""
    if not os.path.exists(STATE_FILE):
        return []
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not read {STATE_FILE} ({e}), starting empty")
        return []
    if not isinstance(data, list):
        print(f"Warning: {STATE_FILE} is not a list, starting empty")
        return []
    return [entry for entry in data if isinstance(entry, dict) and entry.get("issue")]


def save_state(entries):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")


def parse_timestamp(value):
    try:
        return datetime.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def record():
    """Store the casks an approved issue is waiting on."""
    issue = os.environ.get("ISSUE_NUMBER", "").strip()
    if not issue:
        print("No ISSUE_NUMBER given, nothing to record")
        return

    try:
        apps = json.loads(os.environ.get("APPS_JSON", "[]"))
    except json.JSONDecodeError:
        print("APPS_JSON is not valid JSON, nothing to record")
        return

    casks = [a["cask"] for a in apps if isinstance(a, dict) and a.get("cask")]
    if not casks:
        print("No casks in APPS_JSON, nothing to record")
        return

    entries = [e for e in load_state() if str(e.get("issue")) != str(issue)]
    entries.append({
        "issue": int(issue),
        "casks": casks,
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    save_state(entries)
    print(f"Recorded issue #{issue} waiting on: {', '.join(casks)}")


def catalog_entries():
    """Map homebrew cask token to the published app, for live apps only."""
    live = {}
    if not os.path.isdir(APPS_FOLDER):
        return live

    for filename in sorted(os.listdir(APPS_FOLDER)):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(APPS_FOLDER, filename)) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        cask = data.get("homebrew_cask")
        version = data.get("version", "")
        # 0.0.0 is the placeholder the build writes before it has packaged the
        # app, so it means "known about" rather than "downloadable".
        if not cask or not version or version == "0.0.0" or data.get("deprecated"):
            continue

        live[cask] = {
            "name": data.get("name", cask),
            "version": version,
            "file": f"{APPS_FOLDER}/{filename}",
        }
    return live


def resolve():
    """Emit notifications for requests whose apps are now all live."""
    entries = load_state()
    if not entries:
        set_output("notify_count", "0")
        print("No pending requests")
        return

    live = catalog_entries()
    now = datetime.datetime.now(datetime.timezone.utc)

    notifications = []
    remaining = []

    for entry in entries:
        casks = entry.get("casks", [])
        resolved = [live[c] for c in casks if c in live]

        if len(resolved) == len(casks) and casks:
            notifications.append({"issue": entry["issue"], "apps": resolved})
            print(f"Issue #{entry['issue']} is now live: {', '.join(casks)}")
            continue

        recorded_at = parse_timestamp(entry.get("recorded_at"))
        if recorded_at and (now - recorded_at).days >= MAX_AGE_DAYS:
            missing = [c for c in casks if c not in live]
            print(f"Dropping stale issue #{entry['issue']}, never resolved: {', '.join(missing)}")
            continue

        remaining.append(entry)

    save_state(remaining)
    with open(NOTIFICATIONS_FILE, "w") as f:
        json.dump(notifications, f, indent=2)

    set_output("notify_count", str(len(notifications)))
    print(f"{len(notifications)} to notify, {len(remaining)} still pending")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "record":
        record()
    elif command == "resolve":
        resolve()
    else:
        print("Usage: pending_requests.py [record|resolve]", file=sys.stderr)
        # Still exit 0: a usage slip must not fail a build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
