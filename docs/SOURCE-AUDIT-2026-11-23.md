# Source Audit — 2026-11-23

## Scope and safety

This is a read-only inventory of source repositories. No files were changed, moved, deleted, or replaced in any source repository. No payloads have been imported into this repository. All source snapshots below are identified by their observed commit SHA.

## Snapshot inventory

| Source repository | Snapshot commit | Files | Notes |
|---|---|---:|---|
| online4tech/online4Tech | 5d31c60cf815618d308a610f7f106fa24e312918 | 1,184 | Website/download source; 95 IPK, 173 GZ, 253 SH, 97 WEBP, 32 PNG, 32 JPG in the tree inventory. |
| online4tech/Online4Tech-Panel1 | f0b1a9f879f85472b9364f981c2a77dc25dae2b8 | 835 | Package/command panel; includes 23 IPK, 27 DEB, 114 GZ, 544 SH. |
| online4tech/Smart-Manager | 3140fae3b7e199f57b2551c5de8435dc845a1314 | 36 | App, bridge, tests, and data catalogs. |
| online4tech/manus-ipk | 2b626e0fd8d84912fcf42d9d375bfbe940c84b44 | 23 | Catalog website and source JSON data. |
| online4tech/Chanal-List | e98398518c4500cd0cac7c6511b75181f41b74b2 | 218 | Channel lists, backups, scripts, and control-center source. |
| online4tech/Product-test | ec9b28d41f0b1b3f480d5d42e443f6f3fda6251d | 179 | Related product/test tree; substantial path overlap with Chanal-List. |

## Catalog counts observed

- manus-ipk `public/catalog-data.json`: 841 items, 37 categories.
- manus-ipk `public/commands-data.json`: 807 commands, 36 categories.
- Smart-Manager `src/data/plugins.json`: 836 items, 37 categories.
- Smart-Manager `src/data/commands.json`: 1,276 items, 35 categories.
- Online4Tech website `data/plugins.json`: 82 curated plugin records, 19 categories.
- Online4Tech website `data/plugins-inventory.json`: 278 package entries and 16 plugin-page records.
- Online4Tech-Panel1 `o4t_database.json`: 39 top-level sections; the `plugins` section contains 151 records. This is a sectioned database, not a flat count of unique downloadable files.

These counts describe source records, not verified unique or redistributable payloads. Do not add them together.

## Chanal-List vs Product-test comparison

Comparison used exact repository paths and Git blob SHAs from the observed trees:

- Chanal-List: 218 files.
- Product-test: 179 files.
- Shared paths: 177.
- Identical content at the same path: 168.
- Same path but different content: 9.
- Chanal-List-only paths: 41.
- Product-test-only paths: 2.

The nine differing paths are:
- `control-center-app/index.html`
- `control-center/index.html`
- `data/enigma2/commands.json`
- `enigma2-center.html`
- `enigma2-control-center.html`
- `index.html`
- `products.html`
- `src/components/DeviceConnection.jsx`
- `src/pages/ControlCenter.jsx`

Do not merge these paths by filename. Preserve both variants and compare their content and purpose before selecting any candidate.

## Important provenance and safety findings

- Panel1's `SOURCES.md` states that third-party payloads are not copied until the original license or explicit redistribution permission is verified. It also notes that its command audit is static and does not execute scripts, download every nested payload, verify all signatures/checksums, or certify receiver compatibility.
- The website's monitored-source configuration explicitly says monitoring is not approval; imports require classification, compatibility checks, deduplication, and review. It specifies manual review for scripts/Telnet commands and disables auto-publishing.
- The Online4Tech website tree contains a large mixture of first-party assets, community packages, upstream mirrors, generated catalogs, backups, and site code. Each class requires separate provenance handling.
- A matching Git blob SHA at a path is evidence of identical Git object content. Similar names or matching display labels are not.

## Next review queue

1. Compare catalog records by stable IDs and normalized source URLs; identify duplicates and conflicting metadata without changing source files.
2. Build a file-level candidate index for first-party-owned assets and packages, with original path, commit SHA, size, and SHA-256 where the binary bytes can be safely retrieved.
3. Separate first-party Online4Tech files from third-party/community payloads and upstream mirrors.
4. Review license/redistribution permission and script safety before any payload copy.
5. Keep unresolved, unlicensed, or untested items as metadata-only records with direct source references.

## Current import status

**No source payloads imported. No source repositories modified. No download panel connected.**
