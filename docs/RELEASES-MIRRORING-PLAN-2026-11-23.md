# GitHub Releases inventory — 2026-11-23

## Confirmed scope
The release inventory was queried from the five in-scope source repositories. The repositories `online4tech/Online4Tech-Panel1`, `online4tech/manus-ipk`, and `online4tech/Chanal-List` currently return zero GitHub Releases. The two repositories with releases are:

| Repository | Releases | Assets | Total asset size |
|---|---:|---:|---:|
| `online4tech/online4Tech` | 25 | 885 | 33,990,060,274 bytes (~31.65 GiB) |
| `online4tech/Smart-Manager` | 13 | 26 | 117,016,666 bytes (~111.6 MiB) |
| **Total** | **38** | **911** | **34,107,076,940 bytes (~31.76 GiB)** |

## Asset categories (filename/release-name classification; preliminary)
| Category | Assets | Total bytes |
|---|---:|---:|
| Receiver backups / images | 210 | 31,407,080,623 |
| Skins | 198 | 1,368,612,928 |
| Plugins / packages | 311 | 808,451,372 |
| Picons | 23 | 368,828,932 |
| Scripts | 125 | 431,233 |
| Bridge tools | 28 | 131,801,799 |
| Other / manifests / checksums | 16 | 21,870,053 |

Note: category labels are based on release and asset filenames; final classification must inspect each asset. A receiver-backup category can include full firmware images, not just small settings backups. The inventory includes release assets from Smart-Manager for completeness; bridge binaries should be treated separately from Enigma2 content.

## User-requested collection
The collection plan explicitly includes:
- Every release containing Enigma2 plugins and IPK/DEB packages.
- All skin releases and their archives/previews where supplied.
- Picons and picon feed metadata (the user's “البيكون” is recorded as Picons pending confirmation of exact term).
- Vu+ and Dreambox backup/firmware images, grouped by exact receiver model and image/firmware version.
- Release-attached images, logos, screenshots, bootlogos and related artwork.
- Scripts, installer commands, manifests and checksum files.
- Old releases and superseded versions, not only latest releases.

## Preservation and mirror rules
1. Preserve each original GitHub Release page URL and each asset's original download URL.
2. Keep release tag, release name, publication date, asset name, exact size, and available digest.
3. Keep developer/author attribution and license/redistribution notices alongside third-party plugins and skins.
4. Mirror as an additional Online4Tech-hosted copy; never delete or rewrite upstream Releases.
5. Keep versions separately. Do not replace older files with newer versions.
6. Detect byte-identical duplicates by SHA-256 before storage; do not collapse different files based on similar names.
7. Verify large assets with checksums and record exact source/target sizes.
8. Preserve model distinctions: Vu+ Zero 4K, Uno 4K/SE, Ultimo 4K, Solo 4K, Duo 4K/SE, Dreambox DM520/DM525 and other models must not be mixed.
9. Keep `Product-test` excluded from the user's channel-list selection and channel installer. This does not mean deleting its repository or erasing unrelated source history.
10. Do not publish install commands until package contents, dependencies, compatibility, and scripts have been reviewed.

## Current status
- Release metadata inventory: complete for the five queried repositories (38 releases, 911 assets).
- Binary Release assets downloaded into the new repository: none yet.
- Existing two mirrored files remain separate from this Release asset inventory.
- Source repositories/releases modified or deleted: none.
- Panel/store integration: not changed.

## Important technical constraint
The GitHub release listing API returns metadata and asset download URLs, not the binary bytes. This inventory phase therefore preserves the links and exact asset metadata; actual mirroring requires a binary-capable download/transfer path. Large receiver images total over 31 GB, so they should be mirrored in verified batches without losing their original links.
