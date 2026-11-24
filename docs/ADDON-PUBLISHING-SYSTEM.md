# Online4Tech Plugins & Skins Publishing System

## Canonical layout

- `plugins/<addon-id>/` — one folder per plugin.
- `skins/<addon-id>/` — one folder per skin.
- `releases/<version>/` — immutable payloads; never replace a published binary in place.
- `icon.png` — square card icon.
- `screenshots/` — screenshots and preview artwork.
- `latest.json` — current-version pointer and package metadata.
- `install.sh` — stable installation URL for the add-on.
- `catalog/addons/plugins.json` and `catalog/addons/skins.json` — public listing indexes for the website and panel.

## latest.json contract

Each add-on's `latest.json` should contain `schema_version`, `id`, `kind`, `name`, `version`, `package`, `package_format`, `sha256`, `size_bytes`, `install_method`, `compatibility_status`, `supported_models`, `supported_images`, `license_review`, `source_url`, and `release_notes`.

`package` is a path relative to the add-on folder, normally `releases/<version>/<filename>`. `sha256` must be calculated from the exact uploaded binary. Never claim compatibility from the filename alone.

## Stable install command

The public command points to the same `install.sh` URL for the lifetime of the add-on. Publishing a new version updates `latest.json` and the installer resolves the current package from that manifest; the user's command does not change. The installer must verify SHA-256 before installation.

The generic safe install path can support IPK via `opkg` after device/image compatibility is explicitly declared. ZIP, TAR, and SH files are not interchangeable install formats: each requires a reviewed, add-on-specific installation procedure. Never execute an uploaded `.sh` just because it exists in the folder. Never unpack an archive over system paths without validating its contents and target paths.

## Publishing workflow

1. Create `plugins/<id>/` or `skins/<id>/`.
2. Upload icon and screenshots to that add-on's folder.
3. Upload the package under a new immutable `releases/<version>/` directory.
4. Calculate SHA-256 and byte size from the exact package.
5. Complete metadata, source attribution, redistribution-license review, supported models/images, and compatibility evidence in `latest.json`.
6. Review the install procedure; test on a disposable receiver matching the declared target.
7. Update the relevant `catalog/addons/*.json` index only after the add-on is approved for publication.
8. The website and panel can render the index entry, icon, screenshots, download link, and stable install command.

## Status meanings

- `draft`: folder or metadata is being prepared; not listed publicly.
- `pending_review`: awaiting license, security, or compatibility review.
- `published`: approved for listing and distribution.
- `deprecated`: retained for existing users but not recommended for new installs.
- `withdrawn`: hidden from new distribution while historical files remain preserved.

SHA-256 proves file integrity, not safety, authenticity, or device compatibility. Original sources and old releases must remain preserved.