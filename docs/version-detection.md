# Ignore app version detection

Use `-IgnoreVersionDetection` to set Intune's **Ignore app version** setting when creating or updating a PKG/DMG application. Catalog versions are still compared normally, so the uploaded installer can remain current for future installs while an existing device installation is detected by its bundle ID.

```powershell
IntuneBrew -Upload google_chrome -UseExistingIntuneApp -IgnoreVersionDetection
```

Omitting the flag preserves an existing application's setting. To explicitly restore version-based detection, pass `-IgnoreVersionDetection:$false`.

The older `-IgnoreAppVersion` flag has a different purpose: it suppresses update comparisons for apps already present in Intune. Do not combine it with this option when the goal is to keep the uploaded installer current.
