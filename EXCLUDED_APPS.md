# Excluded applications

The following apps are intentionally excluded from collection, packaging, and the supported catalog. Their historical metadata is retained with the existing `deprecated` flag; this does not mean the vendor discontinued them.

| Application | Reason |
|---|---|
| Murus Firewall | Disk image requires explicit vendor license acceptance. |
| Switch Audio Converter | Disk image requires explicit vendor license acceptance. |
| RawTherapee | Disk image requires explicit license acceptance. |
| Autodesk Fusion 360 | Public download is a bootstrap app, not the required deployable installer. |
| Send to Kindle | Vendor download returns HTTP 403. |
| Avast Secure Browser | Vendor installer returns HTTP 404. |
| Contexts | Vendor installer fails TLS validation. |
| jamovi | Vendor installer redirects to an HTML error page. |
| BusyContacts | Published artifact contains AppleDouble metadata instead of a macOS installer. |
| Postbox | Vendor installer host cannot be reached. |
| Real VNC Viewer, CHIRP, Dynalist, fig, Nocturnal, Yubikey Manager | Homebrew casks were removed; historical records remain deprecated. |

Re-enabling an app requires resolving its blocker, restoring its collector URL, clearing its exclusion flags, and validating its package before publication. No license agreement is accepted automatically.

