# Phase 2 — Candidate review (2026-11-23)

## Scope and safety
- Target repository: `online4tech/Online4Tech-Repository` only.
- Read-only review of source repositories; no source repository was changed.
- `Product-test` is excluded from this phase and from the candidate manifest. This is an exclusion from the new repository's workflow, not deletion of the original GitHub repository.
- No binaries, scripts, packages, skins, backups, or images were imported in this phase.
- Candidate classification is preliminary. A source being hosted in an Online4Tech repository does not by itself prove copyright ownership or redistribution permission.

## Sources inspected
| Source | Snapshot / evidence | Review result |
|---|---|---|
| `online4tech/Chanal-List` | tree `e98398518c4500cd0cac7c6511b75181f41b74b2`; README blob `ed10c3832dd20edf311abf824dbbf44ad36763c4` | README identifies BYRomeh channel list and its OpenATV archive. Primary channel candidate source. |
| `online4tech/Online4Tech-Panel1` | tree `f0b1a9f879f85472b9364f981c2a77dc25dae2b8`; `SOURCES.md` blob `de7da62e8f8ec642829b1a015226089e9a1d7556` | Contains first-party wrappers mixed with third-party payloads. External redistribution is explicitly not approved without rights verification. |
| `online4tech/online4Tech` | tree `5d31c60cf815618d308a610f7f106fa24e312918`; monitored sources blob `cd9c9080a03efa395140cc8590a2533c78673620` | Large mixed catalogue: community packages, upstream mirrors, site assets and metadata. Monitoring is not approval; scripts require manual review. |
| `online4tech/Smart-Manager` | README blob `211ca12a3c07eec75f30268cc8c61e45392cf571` | Plugin and command catalogues are data indexes; the project itself says installation is not enabled and commands must not be automatically executed. |
| `online4tech/manus-ipk` | README blob `047c0a02e4946fd04a5288808526f5084fa8278c` | Public catalogue contains 841 plugin records and 807 command records; metadata/catalogue only until item-level provenance and commands are reviewed. |
| `Product-test` | deliberately excluded | Not considered a source for channels, installer commands, imports, or candidate matching. |

## Confirmed channel-list candidate
The `Chanal-List` README names the BYRomeh OpenATV backup archive and warns that it is a backup, not a standalone XML file. The repository's `install-channels.sh` fetches the archive from the canonical `online4tech/Chanal-List` repository (the legacy URL redirects to this repository).

| File | Path | Size | Git blob SHA | Preliminary status |
|---|---|---:|---|---|
| OpenATV channel backup | `channels_backup_openATV_Enigma2-Chanal-List-BYRomeh.tar.gz` | 680,644 bytes | `11b7a72ed4c9639c631d8f1ab9349d3a61441fe7` | `first_party_candidate` — preserve as the only channel-list package candidate |
| Installer | `install-channels.sh` | 1,879 bytes | `41834dadbe18ccd2bf2c3edcb54d38ccd0e47702` | `first_party_candidate` — review required before approving installation |
| Satellite data | `satellites.xml` | 529,521 bytes | `6a1364d04398235ae329dfb73ea92868b35b277a` | `first_party_candidate` |
| Cable data | `cables.xml` | 811,770 bytes | `ee8829d83c7d2d843438a951e308b15ced7b76cd` | `first_party_candidate` |

### Channel installer review
Positive: the script downloads only the named BYRomeh archive, extracts to a temporary directory, selects channel bouquet and satellite/cable/terrestrial data filenames, backs up matching target files, and copies the selected files into `/etc/enigma2`.

Still required before approving a public one-line install command:
1. Validate archive member paths before extraction (path traversal protection).
2. Verify a pinned SHA-256 before extraction and installation.
3. Confirm the archive's internal layout and exact set of files.
4. Keep the target limited to channel files; never use a second channel repository or generic multi-author channel catalogue.
5. Make the backup and failure behavior explicit and test on a disposable Enigma2 image.

The current script is not yet certified as safe for automatic execution. Its source is the right candidate, but the final installer command should not be published from this review alone.

## Other preliminary candidates
- Branding assets in `Chanal-List`: `assets/byromeh-logo.png` (266,555 bytes; blob `cd58af7ccde2fc5487e4057f8ebceec39317b96c`), `assets/icon_online4tech.png` (6,014 bytes; blob `615a15c862ed7dcfd6eeb9008596308d054b2123`), and `assets/bootlogo_online4tech.jpg` (88,154 bytes; blob `35f34af7569622053a39b3e8011e74a956cfa580`) are brand-asset candidates pending visual and rights review.
- `Online4Tech-Panel1/enigma2-plugin-extensions-online4tech_7.5_all.ipk` (385,696 bytes; blob `853be7b292ad0ceacc9fd543c2a7cccf7069aa6e`) is a first-party package candidate, but must be unpacked and reviewed for metadata, bundled third-party files, architecture, dependencies, and scripts before import.
- Panel1's `SOURCES.md` states third-party payloads are not copied until original author/license or redistribution permission is verified. Its static command audit covers 824 entries: 320 third-party, 498 first-party-labelled, 818 URLs, 663 unique URLs, 136 TLS-verification bypasses, 816 pipe-to-shell commands, 59 quarantined entries, and 5 wildcard-removal findings. These are audit counts, not approvals.
- Website plugin catalogue: 82 curated records and 278 package entries; keep as `metadata_only` until each package's origin and license is verified.
- Manus catalogue: 841 plugin metadata records and 807 command records; keep as `metadata_only` pending item-level provenance and command review.
- Smart Manager: 836 plugin/tool records and 1,276 commands are catalogues, not approved install payloads.

## Decision
1. The only channel package candidate in scope is the BYRomeh OpenATV backup in `online4tech/Chanal-List`.
2. Do not use or import `Product-test` content. Do not include its installer or channel URLs.
3. Do not import community IPKs, skins, backups, or third-party scripts until rights, integrity, and compatibility are verified.
4. Do not activate panel integration or change any existing download/install command in this phase.
5. Next technical gate: inspect the channel archive contents and review the Online4Tech 7.5 IPK metadata/payload before deciding what may be imported.

## Change log
- New repository documentation only.
- Source repositories modified: none.
- Payload imports: none.
- Panel connection or configuration changes: none.
