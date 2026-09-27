# Version-aware vulnerability reports

When the PowerShell CLI finds an update to an existing app, it compares both the installed and target versions with the CVE dataset. The report separates vulnerabilities fixed by the update, persisting after it, newly introduced by it, and indeterminate records. CVEs affecting neither version are hidden unless `-ShowAllCves` is set.

Numeric dotted versions, including more than four segments, are supported. Explicit inclusive/exclusive range boundaries are respected; `fixed_version` supplies an exclusive upper bound when no end is present. A start-only range remains assessable. Missing, malformed, contradictory, or nonnumeric ranges are indeterminate. The report does not infer ranges from vulnerability descriptions or establish exposure beyond the supplied dataset.

High/critical or KEV-listed indeterminate records are shown individually as “unable to confirm exposure.” Lower-severity indeterminate records are collapsed into a count. Missing CVE data is reported as unavailable, not as evidence of safety.

## Optional update holds

No updates are held by default. Enable an explicit policy:

```powershell
./IntuneBrew.ps1 -UpdateAll -SecurityHoldLevel High -ConfigFile ./credentials.json -NonInteractive
```

`-SecurityHoldLevel` accepts `None`, `Medium`, `High`, or `Critical`. A hold applies only if an update introduces a newly assessable vulnerability at or above that level. An introduced KEV vulnerability also triggers a hold whenever a level other than `None` is selected. A vulnerability already affecting the installed version does not hold the update. Unknown ranges never trigger a hold.

Held apps are removed from upload selection and reported by name. Other selected apps continue. Exit code 2 indicates one or more held updates, including when every selected update is held. `-IgnoreSecurityHold` explicitly overrides the policy for that run. `-ShowAllCves` changes display only and does not alter hold decisions.

This policy is implemented in the main PowerShell CLI. The separate Azure Automation runbook and the website do not enforce this hold policy. Review upstream data and pilot changes before enabling unattended holds; this is a version-based advisory, not a complete security assessment.
