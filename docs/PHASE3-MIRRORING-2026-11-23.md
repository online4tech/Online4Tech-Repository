# Phase 3 — Initial payload mirroring and structural checks (2026-11-23)

## Mirroring policy
This repository is an additional Online4Tech-hosted copy, not a replacement for upstream sources. Original repositories, URLs, author names, licenses, versions, and provenance are to be retained. No source repository was modified or deleted.

The user confirmed that the curated collection is authorized for copying and use. This confirmation is recorded as the collection's permission basis; it does not invent or replace each upstream author's license terms. Third-party attribution and applicable license notices must remain with each item.

## Mirrored files
| Item | Original source | New repository path | Size at source | Git blob SHA |
|---|---|---|---:|---|
| BYRomeh OpenATV channel backup | `online4tech/Chanal-List` / `channels_backup_openATV_Enigma2-Chanal-List-BYRomeh.tar.gz` | `backups/channels/BYRomeh-OpenATV/channels_backup_openATV_Enigma2-Chanal-List-BYRomeh.tar.gz` | 680,644 bytes | `11b7a72ed4c9639c631d8f1ab9349d3a61441fe7` |
| Online4Tech Plugin 7.5 | `online4tech/Online4Tech-Panel1` / `enigma2-plugin-extensions-online4tech_7.5_all.ipk` | `packages/plugins/online4tech/enigma2-plugin-extensions-online4tech_7.5_all.ipk` | 385,696 bytes | `853be7b292ad0ceacc9fd543c2a7cccf7069aa6e` |

The mirrored Git blob SHAs are identical to their original source Git blob SHAs, confirming byte-for-byte identity at the Git blob level. Each item has a `SOURCE.md` sidecar recording its original repository, path, snapshot commit, source blob SHA, mirror status and pending checks.

Original source links remain:
- https://github.com/online4tech/Chanal-List/blob/main/channels_backup_openATV_Enigma2-Chanal-List-BYRomeh.tar.gz
- https://github.com/online4tech/Online4Tech-Panel1/blob/main/enigma2-plugin-extensions-online4tech_7.5_all.ipk

## Structural checks performed
### IPK package
The mirrored IPK was read back from the target repository and its ar container structure was inspected:
- ar magic: `!<arch>\n`
- `debian-binary`: 4 bytes
- `control.tar.gz`: 538 bytes
- `data.tar.gz`: 384,965 bytes
- The parsed ar member table ends at byte 385,696; the decoder's allocated buffer includes two base64-padding bytes, not package payload.

This confirms a plausible Debian/IPK container layout only. The compressed control and data payloads have not yet been extracted or inspected. Package dependencies, architecture, bundled third-party files, maintainer scripts and install/remove behavior remain pending.

### Channel backup
The mirrored file was read back and its Git blob SHA matches the source. The gzip signature is present in the source encoding. The archive has not yet been decompressed or listed, so internal paths, contents and archive traversal safety remain pending.

## Installation status
Neither mirrored file is approved for a one-line installer yet:
1. Inspect archive members and reject absolute paths or `..` traversal.
2. Compute and publish SHA-256 checksums (Git blob SHA is not a SHA-256 file checksum).
3. Inspect the IPK control metadata, data payload, dependencies and maintainer scripts.
4. Test installation and rollback on a disposable Enigma2 image.
5. For channel installation, pin the archive SHA-256 and install only the BYRomeh channel package. Do not reference or merge any `Product-test` channel files.

## Current change boundaries
- Target repository changed: `online4tech/Online4Tech-Repository` only.
- Original source repositories changed: none.
- Original source links retained: yes.
- Payloads mirrored: 2.
- External source payloads deleted: none.
- `Product-test`: excluded from the user's channel-list selection; original repository not deleted.
- Panel/store integration: not changed.
