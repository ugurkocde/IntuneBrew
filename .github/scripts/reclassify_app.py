#!/usr/bin/env python3
"""Move an app between packaging lists from a maintainer comment.

Whether a PKG needs unwrapping cannot be decided from the package itself:
ordinary distribution packages contain component packages exactly like the
apps in pkg_in_pkg_urls do, and expanding them does not tell the two apart.
It also cannot be inferred from a failed build, because plain pkg apps are
served straight from the vendor URL and never packaged here. In practice the
answer arrives as a deployment report from someone using the app.

So the classification stays a human decision, and this script makes acting on
it a one liner. Given a cask and a target list it moves the entry in
collect_app_info.py and corrects the type in the app's JSON, which matters
because the collector preserves an existing type and would otherwise keep
serving the old one forever.

Reads CASK_NAME and TARGET_LIST from the environment. Sets moved=true on
success, and on failure sets moved=false with a reason rather than raising,
so the workflow can answer the maintainer in the issue.
"""

import glob
import json
import os
import re
import sys

SCRIPT_FILE = ".github/scripts/collect_app_info.py"
APPS_FOLDER = "Apps"

# The type each list gives an app, mirroring get_homebrew_app_info().
LIST_TYPES = {
    "app_urls": "app",
    "homebrew_cask_urls": "dmg",
    "pkg_in_dmg_urls": "pkg_in_dmg",
    "pkg_in_pkg_urls": "pkg_in_pkg",
    "pkg_urls": "pkg",
}


def set_output(name, value):
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")
    print(f"Output: {name}={value}")


def fail(reason):
    set_output("moved", "false")
    set_output("reason", reason)
    print(f"Not moved: {reason}")
    return 0


def list_bounds(lines, list_name):
    """Return (start, end) line indices of a list literal, or None."""
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(list_name)}\s*=\s*\[", line):
            start = i
            break
    if start is None:
        return None

    depth = lines[start].count("[") - lines[start].count("]")
    for i in range(start + 1, len(lines)):
        depth += lines[i].count("[") - lines[i].count("]")
        if depth <= 0:
            return start, i
    return None


def owning_list(lines, cask):
    """Which list currently holds this cask, and on which line."""
    entry = None
    for i, line in enumerate(lines):
        if re.search(rf"cask/{re.escape(cask)}\.json", line):
            entry = i
            break
    if entry is None:
        return None, None

    owner = None
    for name in LIST_TYPES:
        bounds = list_bounds(lines, name)
        if bounds and bounds[0] < entry <= bounds[1]:
            owner = name
    return owner, entry


def update_app_type(cask, new_type):
    """Correct the type on the catalog entry backed by this cask."""
    for path in sorted(glob.glob(os.path.join(APPS_FOLDER, "*.json"))):
        try:
            with open(path) as f:
                data = json.load(f)
        except (ValueError, OSError):
            continue
        if data.get("homebrew_cask") != cask:
            continue

        old_type = data.get("type")
        if old_type == new_type:
            return path, False

        data["type"] = new_type
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"  {path}: type {old_type} -> {new_type}")
        return path, True
    return None, False


def main():
    cask = os.environ.get("CASK_NAME", "").strip()
    target = os.environ.get("TARGET_LIST", "").strip()

    if not cask:
        return fail("no cask given, use /reclassify <cask> <list>")
    if target not in LIST_TYPES:
        return fail(
            f"unknown list `{target}`, expected one of: {', '.join(LIST_TYPES)}"
        )

    with open(SCRIPT_FILE) as f:
        lines = f.readlines()

    current, entry_index = owning_list(lines, cask)
    if entry_index is None:
        return fail(f"`{cask}` is not in {SCRIPT_FILE}")
    if current is None:
        return fail(f"`{cask}` is not inside a recognised list")
    if current == target:
        return fail(f"`{cask}` is already in `{target}`")

    entry = lines.pop(entry_index)
    bounds = list_bounds(lines, target)
    if bounds is None:
        return fail(f"could not find `{target}` in {SCRIPT_FILE}")
    lines.insert(bounds[1], entry if entry.endswith("\n") else entry + "\n")

    with open(SCRIPT_FILE, "w") as f:
        f.writelines(lines)
    print(f"Moved {cask}: {current} -> {target}")

    app_file, type_changed = update_app_type(cask, LIST_TYPES[target])

    set_output("moved", "true")
    set_output("cask", cask)
    set_output("from_list", current)
    set_output("to_list", target)
    set_output("new_type", LIST_TYPES[target])
    set_output("app_file", app_file or "")
    set_output("type_changed", "true" if type_changed else "false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
