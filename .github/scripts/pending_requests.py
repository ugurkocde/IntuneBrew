#!/usr/bin/env python3
"""Track approvals until publication and acknowledged notification delivery.

resolve emits repeatable notifications without removing durable request state.
acknowledge applies only successful deliveries for the same request revision.
A stale request stays tracked after its maintainer-review notice, so a later
successful build can still notify the requester that their app is live.
"""
import datetime
import hashlib
import json
import os
import sys

STATE_FILE = ".github/pending-requests.json"
NOTIFICATIONS_FILE = "pending-notifications.json"
DELIVERIES_FILE = "delivered-request-notifications.json"
APPS_FOLDER = "Apps"
MAX_AGE_DAYS = 3


def set_output(name, value):
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")
    print(f"Output: {name}={value}")


def load_state():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE) as f:
        data = json.load(f)
    if not isinstance(data, list) or any(
        not isinstance(entry, dict) or not isinstance(entry.get("issue"), int)
        or not isinstance(entry.get("casks"), list)
        or not all(isinstance(cask, str) for cask in entry["casks"])
        for entry in data
    ):
        raise ValueError(f"Invalid request state in {STATE_FILE}; refusing to overwrite it")
    return data


def save_state(entries):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")


def parse_timestamp(value):
    try:
        timestamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return timestamp.replace(tzinfo=datetime.timezone.utc) if timestamp.tzinfo is None else timestamp
    except (AttributeError, TypeError, ValueError):
        return None


def record():
    issue = int(os.environ["ISSUE_NUMBER"])
    apps = json.loads(os.environ["APPS_JSON"])
    casks = [a["cask"] for a in apps if isinstance(a, dict) and a.get("cask")]
    if not casks:
        raise ValueError("No casks in APPS_JSON")
    entries = load_state()
    existing = next((entry for entry in entries if entry["issue"] == issue), {})
    # Re-approval of another app on the same issue must preserve earlier work.
    casks = sorted(set(existing.get("casks", []) + casks))
    entries = [entry for entry in entries if entry["issue"] != issue]
    entries.append({
        "issue": issue,
        "casks": casks,
        "recorded_at": existing.get("recorded_at") or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "needs_review": os.environ.get("NEEDS_REVIEW") == "true",
    })
    save_state(entries)
    print(f"Recorded issue #{issue} waiting on: {', '.join(casks)}")


def catalog_entries():
    # The index is produced after package validation. An app file alone does
    # not prove the app was included in the published catalog.
    from publish_catalog import valid_package
    live = {}
    if not os.path.isdir(APPS_FOLDER) or not os.path.exists("supported_apps.json"):
        return live
    with open("supported_apps.json") as f:
        published = json.load(f)
    for filename in sorted(os.listdir(APPS_FOLDER)):
        if not filename.endswith(".json") or filename[:-5] not in published:
            continue
        try:
            with open(os.path.join(APPS_FOLDER, filename)) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        cask, version = data.get("homebrew_cask"), data.get("version")
        if not cask or not version or version == "0.0.0" or data.get("deprecated") or not valid_package(data):
            continue
        live[cask] = {"name": data.get("name", cask), "version": version, "file": f"{APPS_FOLDER}/{filename}"}
    return live


def notification(entry, kind, **details):
    revision = {"issue": entry["issue"], "casks": sorted(entry["casks"]),
                "recorded_at": entry.get("recorded_at"), "needs_review": bool(entry.get("needs_review"))}
    key = hashlib.sha256(json.dumps({**revision, "kind": kind}, sort_keys=True).encode()).hexdigest()
    return {**revision, "kind": kind, "marker": f"<!-- intunebrew-request:{key} -->", **details}


def resolve():
    entries = load_state()
    live = catalog_entries() if entries else {}
    now = datetime.datetime.now(datetime.timezone.utc)
    notifications = []
    for entry in entries:
        casks = entry["casks"]
        missing = [cask for cask in casks if cask not in live]
        if casks and not missing:
            notifications.append(notification(entry, "live", apps=[live[cask] for cask in casks]))
        else:
            recorded = parse_timestamp(entry.get("recorded_at"))
            if recorded and (now - recorded).days >= MAX_AGE_DAYS and not entry.get("review_notified_at"):
                notifications.append(notification(entry, "needs-review", missing=missing))
    with open(NOTIFICATIONS_FILE, "w") as f:
        json.dump(notifications, f, indent=2)
    set_output("notify_count", len(notifications))
    print(f"{len(notifications)} to notify; durable request state retained until acknowledgement")


def acknowledge():
    with open(DELIVERIES_FILE) as f:
        deliveries = json.load(f)
    entries = load_state()
    remaining = []
    for entry in entries:
        receipt = next((delivery for delivery in deliveries
                        if delivery.get("kind") in ("live", "needs-review")
                        and delivery.get("marker") == notification(entry, delivery["kind"])["marker"]), None)
        if receipt and receipt["kind"] == "live":
            continue
        if receipt:
            entry = {**entry, "review_notified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        remaining.append(entry)
    if remaining != entries:
        save_state(remaining)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    handlers = {"record": record, "resolve": resolve, "acknowledge": acknowledge}
    if command not in handlers:
        raise ValueError("Usage: pending_requests.py [record|resolve|acknowledge]")
    handlers[command]()


if __name__ == "__main__":
    main()
