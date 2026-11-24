# Skins

Each skin gets its own folder: `skins/<skin-id>/`.

Expected files:
- `latest.json` — current release metadata and stable package pointer.
- `install.sh` — stable installation entry point for the skin.
- `icon.png` — card icon (recommended square PNG, 512×512).
- `screenshots/` — preview images used by the website and panel.
- `releases/<version>/` — immutable versioned ZIP, TAR, IPK, or other approved payloads.

Do not overwrite old release payloads. Publish a new version directory and update only the `latest.json` pointer after review. A skin is not marked compatible until tested on the stated image/device.