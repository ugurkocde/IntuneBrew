# IntuneBrewCompanion User Guide

## Table of Contents
- [What is IntuneBrewCompanion?](#what-is-intunebrewcompanion)
- [Getting Started](#getting-started)
- [Main Features](#main-features)
- [Step-by-Step Guides](#step-by-step-guides)
- [Tips and Best Practices](#tips-and-best-practices)
- [Frequently Asked Questions](#frequently-asked-questions)

## What is IntuneBrewCompanion?

IntuneBrewCompanion is a tool that bridges the gap between your manually installed macOS applications and Homebrew package management. It helps you:

- Discover which of your apps are available through Homebrew
- Migrate existing apps to Homebrew management
- Keep all your Homebrew apps updated easily
- Search and install new apps from Homebrew's extensive catalog

### Why Use Homebrew?

Homebrew provides:
- Easy updates for all apps with a single command
- Consistent installation and removal process
- No need to manually download updates from websites
- Command-line and GUI management options

## Getting Started

### System Requirements

Before using IntuneBrewCompanion, ensure you have:

1. **macOS 15.4 or later**
2. **Homebrew installed** - If not, install it:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

### First Launch Setup

1. **Launch IntuneBrewCompanion**
   - Find it in your Applications folder
   - Or use Spotlight: Press `⌘ Space` and type "IntuneBrewCompanion"

2. **Initial Scan**
   - The app will automatically scan your Applications folder
   - This may take a few moments depending on how many apps you have

3. **Review Your Apps**
   - You'll see a list of installed apps that are available in Homebrew
   - Apps are color-coded by their status

## Main Features

### The Interface

![Main Window Overview]
```
┌─────────────────────────────────────────────────┐
│ IntuneBrewCompanion                             │
├─────────────────────────────────────────────────┤
│ [Installed Apps] [Search & Install]             │
│                                                 │
│ 🔍 Search...                    [Check Updates] │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ App Name    Version   Status    Action      │ │
│ │ Discord     0.0.1     Update    [Update]    │ │
│ │ Notion      2.0.1     Current   [Managed]   │ │
│ │ Claude      1.0.0     Migrate   [Migrate]   │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Status Indicators

- **🟢 Managed**: App is installed and managed by Homebrew
- **🟡 Migrate**: App can be migrated to Homebrew
- **🔵 Update**: An update is available
- **⚪ Current**: App is up to date

## Step-by-Step Guides

### How to Migrate an App to Homebrew

Migrating an app means IntuneBrewCompanion will:
- Move your current app to Trash (as backup)
- Install the same app through Homebrew
- Preserve all your settings and data

**Steps:**

1. **Find the app** in your Installed Apps list
2. **Check the status** - it should show "Migrate available"
3. **Click "Migrate to Homebrew"**
4. **Wait for the process** to complete (usually 30-60 seconds)
5. **Verify** the app works correctly

**Note**: Your app data and preferences are preserved during migration.

### How to Update Apps

#### Updating a Single App

1. Look for apps with the **"Update"** button
2. Click the **"Update"** button
3. The app will be updated in the background
4. You may need to restart the app to use the new version

#### Updating All Apps at Once

1. Click **"Update All"** in the toolbar
2. All available updates will be installed
3. Progress is shown for each app
4. A summary appears when complete

### How to Search and Install New Apps

1. **Switch to the "Search & Install" tab**
2. **Type the app name** in the search box
3. **Review the results** - shows app name, description, and version
4. **Click "Install"** next to the app you want
5. **Wait for installation** to complete

### How to Check for Updates

There are three ways to check for updates:

1. **Automatic**: Updates are checked when you launch the app
2. **Manual**: Click "Check for Updates" button
3. **Keyboard**: Press `⌘U`

## Tips and Best Practices

### Before Migrating

1. **Close the app** you're about to migrate
2. **Save any open work** in that application
3. **Check available disk space** - you need room for both versions temporarily

### Managing Updates

- **Regular checks**: Check for updates weekly
- **Restart apps**: Some updates require restarting the app
- **Bulk updates**: Use "Update All" to save time

### Troubleshooting Failed Migrations

If a migration fails:

1. **Check if the app is running** - close it completely
2. **Try again** - temporary issues often resolve
3. **Check Trash** - your original app is backed up there
4. **Restore if needed** - drag the app back from Trash

## Frequently Asked Questions

### Q: Will I lose my app settings when migrating?

**A:** No, your settings, preferences, and data are preserved. IntuneBrewCompanion only replaces the app bundle, not your data.

### Q: What happens to my original app?

**A:** It's moved to Trash as a backup. You can restore it if needed by dragging it back to Applications.

### Q: Can I still update apps outside of Homebrew?

**A:** Yes, but once an app is managed by Homebrew, it's best to update it through Homebrew to avoid conflicts.

### Q: What if I don't see an app in the list?

**A:** This means either:
- The app isn't available as a Homebrew cask
- The app is installed in a non-standard location
- The app name doesn't match Homebrew's naming

### Q: Is it safe to migrate system apps?

**A:** IntuneBrewCompanion only shows apps that are safe to migrate. System apps are automatically excluded.

### Q: How do I uninstall an app managed by Homebrew?

**A:** You can:
- Use Homebrew: `brew uninstall --cask app-name`
- Or simply drag the app to Trash (though this leaves Homebrew metadata)

### Q: Can I undo a migration?

**A:** Yes, your original app is in Trash. To undo:
1. Uninstall the Homebrew version: `brew uninstall --cask app-name`
2. Restore your original app from Trash

### Q: Why do some apps show as "Not available"?

**A:** These apps aren't available through Homebrew. Common reasons:
- Paid apps that require license verification
- Apps distributed only through the Mac App Store
- Custom or enterprise applications

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘R` | Refresh app list |
| `⌘F` | Focus search box |
| `⌘U` | Check for updates |
| `⌘,` | Open settings |
| `⌘Q` | Quit IntuneBrewCompanion |

## Getting Help

If you encounter issues:

1. **Check the Troubleshooting section** in the README
2. **View logs** in Settings → Activity Log
3. **Report issues** on [GitHub](https://github.com/ugurkoc/intunebrewcompanion/issues)
4. **Ask questions** in [Discussions](https://github.com/ugurkoc/intunebrewcompanion/discussions)

---

Remember: IntuneBrewCompanion is a tool to make your life easier. If something doesn't work as expected, your original apps are always safely backed up in Trash.