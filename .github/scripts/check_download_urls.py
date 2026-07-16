#!/usr/bin/env python3
"""Check that every catalog download URL still resolves to a downloadable file.

Vendors sometimes delete versioned files and redirect to an HTML error page
that is served with a 200 status. The nightly collector only syncs version
data from Homebrew, so a rotted URL stays in the catalog silently until a
user upload fails. This script probes every non-deprecated app URL and
writes a markdown report of the broken ones, so a scheduled workflow can
open or update a GitHub issue.

Exit code is always 0. The number of broken URLs is exposed through the
GITHUB_OUTPUT variable "broken_count" and the report is written to
url-health-report.md in the working directory.
"""

import concurrent.futures
import datetime
import json
import os
import sys

import requests

APPS_FOLDER = "Apps"
REPORT_FILE = "url-health-report.md"
TIMEOUT_SECONDS = 45
MAX_WORKERS = 20
# Different CDNs block different clients: SourceForge rejects browser user
# agents from non-browser TLS stacks, Tableau's CDN only allows curl-style
# agents, others require a browser agent. Try them in order and treat the
# URL as broken only if every attempt fails.
ATTEMPTS = [
    {"method": "HEAD", "user_agent": "IntuneBrew-URL-Health-Check/1.0"},
    {"method": "GET", "user_agent": "IntuneBrew-URL-Health-Check/1.0"},
    {"method": "GET", "user_agent": "curl/8.4.0"},
    {
        "method": "GET",
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
    },
]


def check_url(url):
    """Return (verdict, detail). Verdict is 'ok' or a failure category."""
    verdict, detail = "request_failed", "no attempt succeeded"
    for attempt in ATTEMPTS:
        headers = {"User-Agent": attempt["user_agent"]}
        if attempt["method"] == "GET":
            headers["Range"] = "bytes=0-0"
        try:
            response = requests.request(
                attempt["method"],
                url,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
                allow_redirects=True,
                stream=True,
            )
            response.close()
        except requests.RequestException as e:
            verdict, detail = "request_failed", type(e).__name__
            continue

        if response.status_code >= 400:
            verdict, detail = "http_error", f"HTTP {response.status_code}"
            continue

        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            verdict, detail = "html_page", f"returns an HTML page (final URL: {response.url})"
            continue

        return "ok", content_type

    return verdict, detail


def main():
    apps = []
    for filename in sorted(os.listdir(APPS_FOLDER)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(APPS_FOLDER, filename)) as f:
            try:
                data = json.load(f)
            except ValueError:
                print(f"Skipping unparseable file: {filename}")
                continue
        if data.get("deprecated"):
            continue
        if not data.get("url"):
            continue
        apps.append({"name": filename[: -len(".json")], "version": data.get("version", ""), "url": data["url"]})

    print(f"Checking {len(apps)} download URLs...")
    broken = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(check_url, app["url"]): app for app in apps}
        for future in concurrent.futures.as_completed(futures):
            app = futures[future]
            verdict, detail = future.result()
            if verdict != "ok":
                broken.append({**app, "verdict": verdict, "detail": detail})
                print(f"BROKEN {app['name']}: {verdict} ({detail})")

    broken.sort(key=lambda a: a["name"])
    today = datetime.date.today().isoformat()

    lines = [
        f"Automated URL health check from {today}.",
        "",
        f"Checked {len(apps)} catalog download URLs, found {len(broken)} broken.",
        "",
    ]
    if broken:
        lines += [
            "These apps cannot currently be uploaded to Intune. Either the vendor "
            "moved or removed the file (wait for the Homebrew cask to catch up) or "
            "the app is discontinued and its JSON should be flagged with "
            '"deprecated": true.',
            "",
            "| App | Version | Problem | URL |",
            "| --- | --- | --- | --- |",
        ]
        for app in broken:
            lines.append(
                f"| {app['name']} | {app['version']} | {app['verdict']}: {app['detail']} | {app['url']} |"
            )
    else:
        lines.append("All download URLs are healthy.")

    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"broken_count={len(broken)}\n")

    print(f"\n{len(broken)} of {len(apps)} URLs are broken. Report written to {REPORT_FILE}.")


if __name__ == "__main__":
    main()
