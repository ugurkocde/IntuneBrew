# Close an app before a PKG update

Use [close-app-before-install.sh](../scripts/close-app-before-install.sh) as a starting point for IntuneBrew's `-PreInstallScriptPath`. It applies to PKG apps; IntuneBrew does not attach pre-install scripts to DMG apps.

Set `APP_BUNDLE_ID` and `PROCESS_NAME` in your copy to the app's actual values. Outlook commonly uses `com.microsoft.Outlook` and `Microsoft Outlook`. Teams releases differ, so inspect the installed application's Info.plist and main process before configuring it.

```powershell
./IntuneBrew.ps1 -Upload microsoft_outlook -PreInstallScriptPath ./close-outlook.sh
```

The script runs as root, requests a normal quit in the console user's session, and checks whether the exact main process remains. It does not unload launch agents or force-kill the app. Unsaved work, macOS automation permissions, another logged-in user, or an app that relaunches can prevent shutdown. In those cases it returns a nonzero exit code so installation is deferred rather than proceeding while the app is open.

Test the configured script on a pilot device, including an unsaved document. Ask users to save and quit before the maintenance window. The quit request and subsequent wait each have a bounded timeout (30 seconds by default). Returning a failure cannot guarantee the next device sync will succeed; the blocking app must actually close. The included automated tests use mocked processes and never close a user's applications.
