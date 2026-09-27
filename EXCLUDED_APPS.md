# Excluded applications

The following apps are intentionally excluded from collection, packaging, and the supported catalog. Their historical metadata is retained with the existing `deprecated` flag; this does not mean the vendor discontinued them.

| Application | Reason |
|---|---|
| Murus Firewall | Disk image requires explicit vendor license acceptance. |
| Switch Audio Converter | Disk image requires explicit vendor license acceptance. |
| RawTherapee | Disk image requires explicit license acceptance. |
| Autodesk Fusion 360 | Public download is a bootstrap app, not the required deployable installer. |
| Send to Kindle | Vendor download returns HTTP 403. |

Re-enabling an app requires resolving its blocker, restoring its collector URL, clearing its exclusion flags, and validating its package before publication. No license agreement is accepted automatically.

