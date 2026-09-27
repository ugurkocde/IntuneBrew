"""Publish a consistent catalog after collection and packaging, without network I/O."""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

REPACKAGED = {"app", "pkg_in_dmg", "pkg_in_pkg"}


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def original(path):
    result = subprocess.run(["git", "show", f"HEAD:{path.as_posix()}"], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def restore(path):
    previous = original(path)
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        path.write_bytes(previous)


def valid_package(data):
    if data.get("type") not in REPACKAGED or data.get("deprecated"):
        return True
    url = urlparse(data.get("url", ""))
    expected = data.get("fileName", "")
    return (url.scheme == "https" and url.hostname == "intunebrew.blob.core.windows.net"
            and url.path.startswith("/pkg/") and expected.endswith(".pkg")
            and unquote(url.path.rsplit("/", 1)[-1]) == expected
            and expected.endswith("_" + str(data.get("version", "")) + ".pkg")
            and bool(re.fullmatch(r"[a-fA-F0-9]{64}", data.get("sha", ""))))


def publish(scope="all"):
    report = load(Path("collection-report.json"), {"failures": [], "collisions": []})
    previous = load(Path("catalog-sync.json"), {})
    failures = {}
    failed_casks = {item["cask"] for item in report["failures"] if "cask" in item}
    for item in report["failures"]:
        if item.get("file"):
            failures[Path(item["file"]).name] = item["stage"]
    for item in report["collisions"]:
        failures[Path(item["file_path"]).name] = "identity collision"
        failed_casks.update([item["existing_cask"], item["incoming_cask"]])
    for path in Path("Apps").glob("*.json"):
        if load(path, {}).get("homebrew_cask") in failed_casks:
            failures[path.name] = "collection"
    packaging = Path("packaging-failed-apps.txt")
    if packaging.exists():
        for name in packaging.read_text().splitlines():
            if name.strip():
                failures[Path(name).name + ".json"] = "packaging"
    for name in failures:
        restore(Path("Apps") / name)

    apps = {}
    updates = []
    excluded = []
    for path in sorted(Path("Apps").glob("*.json")):
        data = load(path, {})
        if not valid_package(data):
            failures[path.name] = "package validation"
            restore(path)
            if not path.exists():
                continue
            data = load(path, {})
        if data.get("deprecated"):
            continue
        if not valid_package(data):
            excluded.append(path.stem)
            continue
        apps[path.stem] = f"https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/{path.name}"
        old_bytes = original(path)
        old = json.loads(old_bytes) if old_bytes else {}
        if old.get("version") and data.get("version") != old["version"]:
            updates.append({"appName": path.stem.replace("_", " "), "previousVersion": old["version"],
                            "newVersion": data["version"], "changelog": data.get("changelog"),
                            "logoUrl": f"https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Logos/{path.stem}.png"})
    if not apps:
        raise RuntimeError("Refusing to publish an empty catalog")
    # A failed request with no existing file must still appear in the report.
    for token in failed_casks:
        if not any(load(p, {}).get("homebrew_cask") == token for p in Path("Apps").glob("*.json")):
            failures[f"cask:{token}"] = "collection"
    if len(failures) >= len(apps):
        raise RuntimeError("Collection failed for most of the catalog; keeping the published snapshot")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    failed = [{"app": name.removesuffix(".json"), "stage": stage} for name, stage in sorted(failures.items())]
    full = scope == "all"
    # A scoped app addition must not refresh the age or health of a full sync.
    state = {
        "schemaVersion": 1,
        "lastPublishedAt": now,
        "lastFullSyncAt": now if full else previous.get("lastFullSyncAt"),
        "lastSuccessfulSyncAt": now if full and not failed else previous.get("lastSuccessfulSyncAt"),
        "status": ("degraded" if failed else "healthy") if full else previous.get("status", "unknown"),
        "failedApps": failed if full else previous.get("failedApps", []),
        "appCount": len(apps),
        "runUrl": f"https://github.com/ugurkocde/IntuneBrew/actions/runs/{os.environ['GITHUB_RUN_ID']}" if os.environ.get("GITHUB_RUN_ID") else None,
    }
    Path("supported_apps.json").write_text(json.dumps(apps, indent=4) + "\n")
    Path("catalog-sync.json").write_text(json.dumps(state, indent=2) + "\n")
    # Preserve the last change list on a quiet scan, but record a genuine check.
    old_feed = load(Path("latest-updates.json"), {"updates": []})
    feed = {"lastChecked": state["lastFullSyncAt"], "updates": updates or old_feed.get("updates", [])}
    Path("latest-updates.json").write_text(json.dumps(feed, indent=2) + "\n")
    readme = Path("README.md")
    if readme.exists():
        section = "## 🔄 Latest Updates\n\n*Last checked: " + str(feed["lastChecked"]) + "*\n\n"
        section += "| Application | Previous Version | New Version |\n|---|---|---|\n"
        for update in feed["updates"]:
            section += f"| {update['appName']} | {update['previousVersion']} | {update['newVersion']} |\n"
        if failed:
            section += f"\n{len(failed)} app updates could not be published. See [catalog sync status](catalog-sync.json).\n"
        readme.write_text(re.sub(r"## 🔄 Latest Updates.*?(?=## ✨ Features)", section + "\n", readme.read_text(), flags=re.S))
    summary = f"Catalog published: {len(apps)} apps, {len(updates)} new versions, {len(failed)} retained failures.\n"
    summary += "\n".join(f"- {item['app']}: {item['stage']} (previous entry retained or new entry omitted)" for item in failed)
    Path("catalog-sync-report.md").write_text(summary + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
            output.write(summary + "\n")
    return state, feed


if __name__ == "__main__":
    publish(os.environ.get("BUILD_SCOPE", "all"))
