# Repository Structure

- plugins/<plugin-id>/<version>/: plugin packages and supporting files.
- scripts/<script-id>/<version>/: scripts and command definitions.
- packages/<package-id>/<version>/: IPK and installable packages.
- assets/plugins/, assets/logos/, assets/skins/: artwork and previews.
- backups/<source>/<date-or-version>/: preserved backup snapshots.
- releases/<tag>/: release notes and curated manifests.
- catalog/: machine-readable indexes.
- checksums/: SHA-256 manifests.

Use stable IDs, keep each version in its own directory, and never silently overwrite a published version.
