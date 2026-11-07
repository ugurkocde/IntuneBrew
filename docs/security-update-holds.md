# Version-aware vulnerability reports

When the PowerShell CLI finds an update to an existing app, it compares both the installed and target versions with the CVE dataset. The report separates vulnerabilities fixed by the update, persisting after it, newly introduced by it, and indeterminate records. CVEs affecting neither version are hidden unless `-ShowAllCves` is set.

Numeric dotted versions, including more than four segments, are supported. Two proven bundle decorations also use their numeric release core for CVE evaluation: canonical `release(AB12)` with exactly four uppercase hexadecimal characters including A–F, and canonical three-component `release-stable.N`. Decorated components have at most nine digits and no leading zeros. This applies to both installed and target versions; CVE range bounds must remain numeric. Other suffixes, `(build N)` and `+N` remain indeterminate. Explicit inclusive/exclusive range boundaries are respected; `fixed_version` supplies an exclusive upper bound when no end is present. A start-only range remains assessable. Missing, malformed, contradictory, or nonnumeric ranges are indeterminate. The report does not infer ranges from vulnerability descriptions or establish exposure beyond the supplied dataset.

High/critical or KEV-listed indeterminate records are shown individually as “unable to confirm exposure.” Lower-severity indeterminate records are collapsed into a count. Missing CVE data is reported as unavailable, not as evidence of safety.

## Optional update holds

No updates are held by default. Enable an explicit policy:

```powershell
./IntuneBrew.ps1 -UpdateAll -SecurityHoldLevel High -ConfigFile ./credentials.json -NonInteractive
```

`-SecurityHoldLevel` accepts `None`, `Medium`, `High`, or `Critical`. A hold applies only if an update introduces a newly assessable vulnerability at or above that level. An introduced KEV vulnerability also triggers a hold whenever a level other than `None` is selected. A vulnerability already affecting the installed version does not hold the update. Unknown ranges never trigger a hold.

Held apps are removed from upload selection and reported by name. Other selected apps continue. Exit code 2 indicates one or more held updates, including when every selected update is held. `-IgnoreSecurityHold` explicitly overrides the policy for that run. `-ShowAllCves` changes display only and does not alter hold decisions.

The CLI and Azure Automation Runbook use identical CVE range and hold evaluators, checked by regression tests. The website does not enforce this hold policy. A malformed local CLI CVE file now holds an update when a hold level is configured, unless explicitly overridden; an absent local file retains the existing unavailable/no-hold behavior.

## Azure Automation Runbook

Set these optional Automation variables:

| Variable | Values | Default |
| --- | --- | --- |
| `SecurityHoldLevel` | `None`, `Medium`, `High`, `Critical` (case-insensitive) | `None` |
| `IgnoreSecurityHold` | Boolean, or the exact string `true`/`false` | `false` |

Invalid settings stop the run before authentication or Graph calls. No policy is enabled by default. When configured, each update candidate reads `CVE/<manifest-key>.json` from the same fixed GitHub repository/main trust root as its app manifest. Requests disallow redirects, use a 20-second cancellation budget and accept at most 16 MiB of strict UTF-8 JSON. A missing CVE file (404) is logged as unavailable and does not automatically hold, matching the CLI. Transport failures, non-200/non-404 responses, oversized bodies, invalid JSON and malformed dataset records hold that app. Neither missing data nor an indeterminate range establishes safety. The explicit override also bypasses a data-error hold, with a warning for each affected app.

Both display-name and bundle-ID matching paths assess the installed and target versions. Held updates are skipped and reported before `MaxAppsPerRun` and assignment reads; other updates continue. An all-held Runbook run exits successfully without an interactive prompt and rechecks holds on its next scheduled run. The CLI retains its existing exit code 2 for held updates.

The Runbook retains the manifest and its URL at discovery and uploads that exact assessed version, even if the catalog changes later or another manifest shares its display name. The feed and manifest still come from moving `main` at separate instants; this is not a transactional security-data snapshot. Review upstream data and pilot changes before enabling unattended holds; this is a version-based advisory, not a complete security assessment.

The complete CVE JSON feed is parsed in memory. The byte limit bounds the response, not peak process memory: parsing and vulnerability evaluation can use substantially more memory, alongside the Graph modules. Azure Automation cloud sandboxes have a [400 MB memory limit](https://learn.microsoft.com/en-us/azure/automation/automation-subscription-limits-faq). Measure the largest current feed with the modules loaded in the actual cloud sandbox or Hybrid Worker before enabling holds there; a local test does not establish that runtime's memory headroom.
