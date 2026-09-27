# Local installer sources

For a private or pre-downloaded PKG/DMG, put a JSON app manifest in a directory you explicitly select with `-LocalJsonDirectory`. Set its `url` to an absolute file URI, such as `file:///C:/Packages/App.pkg` on Windows or `file:///Users/Shared/App.pkg` on macOS. Spaces can be percent-encoded as `%20`.

A relative reference such as `file://./installers/App.pkg` is resolved from the manifest's directory. Parent traversal is rejected. Network file URIs, such as `file://server/share/App.pkg`, require `-AllowNetworkPaths` and an accessible share on the host OS. On macOS/Linux, a mounted share can instead use its local absolute path.

The manifest must include a valid SHA256 `sha`, the app name, version, bundle ID, and a `.pkg` or `.dmg` `fileName`. IntuneBrew copies the installer into a temporary working directory and verifies that copy before upload. Hash failures never modify or delete the original installer. A downloaded public catalog manifest cannot enable local file access.

```powershell
IntuneBrew -LocalJsonDirectory ./manifests -Upload corporate_app -ConfigFile ./tenant.json -NonInteractive
```

Local installer support removes the need to download the installer from the internet. Authentication, catalog retrieval, and Intune upload still require connectivity.
