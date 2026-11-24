# Release asset mirror queue

These category indexes are generated from the source Release APIs. They retain original download URLs and source release attribution so no upstream download is lost.

## Current state
- Metadata inventory: complete for the five source repositories checked.
- Binary mirroring: pending a binary-capable transfer path.
- No source release, tag, or asset was modified or deleted.
- Do not treat an indexed item as validated or installable until the binary is mirrored and inspected.

## Category indexes
- [Plugins and packages](../../catalog/releases/plugins.json)
- [Skins](../../catalog/releases/skins.json)
- [Picons](../../catalog/releases/picons.json)
- [Vu+ / Dreambox receiver backups](../../catalog/releases/receiver_backups.json)
- [Scripts](../../catalog/releases/scripts.json)
- [Bridge tools](../../catalog/releases/bridge_tools.json)
- [Other assets and manifests](../../catalog/releases/other.json)

## Transfer order
1. Small metadata, scripts, picon feed files and artwork.
2. Plugins and skin archives, preserving each release/version separately.
3. Receiver backup images in model-specific batches; these account for most of the 31.76 GB.
4. Bridge utilities separately from Enigma2 packages.

For each transferred file, verify source and target byte size, compute SHA-256, preserve developer attribution/license and original URL, inspect archive paths, then set a validation status. Similar filenames are not proof of duplicate content.

## فهرس الوصول حسب موديل الرسيفر
- [نسخ الباك أب مرتبة حسب موديل الجهاز](RECEIVER-BACKUPS-BY-MODEL.md) — فهرس مباشر للتحميل من الـReleases المركزية، مع روابط المصدر الأصلي وملاحظات التصنيف.
