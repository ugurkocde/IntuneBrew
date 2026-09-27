# Local installer sources

For a private or pre-downloaded PKG/DMG, put a JSON app manifest in a directory you explicitly select with `-LocalJsonDirectory`. Set its `url` to an absolute file URI, such as `file:///C:/Packages/App.pkg` on Windows or `file:///Users/Shared/App.pkg` on macOS. Spaces can be percent-encoded as `%20`.

A relative reference such as `file://./installers/App.pkg` is resolved from the manifest's directory. Parent traversal is rejected. Network file URIs, such as `file://server/share/App.pkg`, require `-AllowNetworkPaths` and an accessible share on the host OS. On macOS/Linux, a mounted share can instead use its local absolute path.

The manifest must include a valid SHA256 `sha`, the app name, version, bundle ID, and a `.pkg` or `.dmg` `fileName`. IntuneBrew copies the installer into a temporary working directory and verifies that copy before upload. Hash failures never modify or delete the original installer. A downloaded public catalog manifest cannot enable local file access.

```powershell
IntuneBrew -LocalJsonDirectory ./manifests -Upload corporate_app -ConfigFile ./tenant.json -NonInteractive
```

Local installer support removes the need to download the installer from the internet. Authentication, catalog retrieval, and Intune upload still require connectivity.

## Non-interactive local uploads

Use `-LocalFilePath` to select an installer without opening a dialog. This preserves the existing interactive `-LocalFile` switch and supports `-UseExistingIntuneApp` through the normal catalog deployment flow:

```powershell
./IntuneBrew.ps1 -LocalFilePath './Company VPN.pkg' `
  -LocalFileAppName 'Company VPN' -LocalFileVersion '1.2.3' `
  -LocalFileBundleID 'com.example.vpn' -UseExistingIntuneApp `
  -ConfigFile ./credentials.json -NonInteractive
```

Alternatively, pass `-LocalFileConfig ./app.json` with the metadata:

```json
{
  "name": "Company VPN",
  "version": "1.2.3",
  "bundleId": "com.example.vpn",
  "description": "Company VPN client"
}
```

Explicit metadata parameters override the JSON values. An optional `sha` in that JSON is checked against the selected file. Otherwise, the script calculates SHA256 from the explicitly selected source, then checks the temporary upload copy against it. Only that temporary copy is cleaned up; the original installer is retained.

The existing app is matched by its formatted display name, including any prefix/suffix, and is updated only when the supplied version is newer. Use the same name as the existing Intune entry. Metadata must describe the actual bundle inside the installer. This flow still requires catalog and Graph connectivity and does not assign a newly created app automatically.
