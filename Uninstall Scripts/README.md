# Intune macOS Uninstall Scripts

This folder contains uninstall scripts for macOS applications that were deployed using pkg files through Intune. Since Intune does not support uninstalling applications that were deployed using pkg files, these scripts can be used to uninstall the applications.

## How to Use

1. Deploy these scripts through Intune as shell scripts
2. Assign them to the devices that have the corresponding application installed
3. The scripts will remove the application and its associated files

## Script Details

Each script follows this naming convention: `uninstall_[app_name].sh`

For example:

- `uninstall_1password.sh` - Uninstalls 1Password
- `uninstall_visual_studio_code.sh` - Uninstalls Visual Studio Code

## What the Scripts Do

Each uninstall script performs the following actions:

1. Stops the application if it's running
2. Removes the application bundle from `/Applications`
3. Removes application data from common locations:
   - `~/Library/Application Support/[App Name]`
   - `~/Library/Caches/[Bundle ID]`
   - `~/Library/Preferences/[Bundle ID].plist`
   - `~/Library/Saved Application State/[Bundle ID].savedState`
4. Unloads any launchd services associated with the application
5. Removes package receipts using `pkgutil --forget`
6. Removes any additional files and folders specific to the application

## Regenerating Scripts

These scripts are generated using the `generate_uninstall_scripts.py` script in the `.github/scripts` directory. If you need to regenerate the scripts, run:

```bash
bash .github/scripts/update_uninstall_scripts.sh
```

This will fetch the latest application information from brew.sh and generate updated uninstall scripts.

## Notes

- These scripts must be run with root privileges (sudo)
- They are designed to be deployed through Intune as shell scripts
- The scripts include error handling to prevent failures if files don't exist
