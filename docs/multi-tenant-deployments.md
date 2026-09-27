# Deploy to multiple tenants

Use PowerShell 7 and `Invoke-IntuneBrewBatch.ps1` from a checkout of this repository. Install the Microsoft.Graph.Authentication module first. Each tenant needs its own app registration and an existing IntuneBrew certificate or client-secret configuration with an explicit tenant GUID. Protect those files with filesystem permissions and keep them out of source control.

Create a manifest containing friendly names and configuration paths (relative to the manifest):

```json
{
  "tenants": [
    { "name": "Customer One", "configFile": "credentials/customer-one.json" },
    { "name": "Customer Two", "configFile": "credentials/customer-two.json" }
  ]
}
```

Validate the complete plan without authenticating or deploying:

```powershell
./Invoke-IntuneBrewBatch.ps1 -TenantManifest ./tenants.json -Upload google_chrome,slack -WhatIf
```

Run the same command without `-WhatIf` to deploy. Use `-UpdateAll` instead of `-Upload` to update existing catalog apps. `-UseExistingIntuneApp` and `-PreserveAssignments` are forwarded to each deployment. Existing IntuneBrew assignment behavior still applies; uploading an app does not automatically assign it to devices.

Each tenant runs in a separate PowerShell process with a separate working directory and process-scoped Graph authentication. The authenticated tenant must match its configuration. The default concurrency is three tenants; `-ThrottleLimit` accepts 1–10. Duplicate tenants are rejected before any deployment starts.

The command writes `intunebrew-batch-summary.json` (or `-SummaryPath`) containing friendly tenant names, success/failure, exit codes, and duration. Exit code 1 means at least one tenant failed; other tenants still finish. No automatic retries occur because deployment may have partially completed. Check the affected tenant before retrying. Child output is suppressed to keep credentials and tenant details out of aggregate logs; run IntuneBrew directly with the affected configuration for diagnostics. A failed batch is not rolled back across tenants.

This first release provides batch automation, not website tenant switching. Automated tests exercise isolated child processes and failure handling. Graph reads were verified against the lab tenant; no live cross-tenant deployments were performed as part of validation.
