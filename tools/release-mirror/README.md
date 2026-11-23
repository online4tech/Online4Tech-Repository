# Online4Tech Release Mirror Transfer Tool

This tool runs locally on Windows and mirrors selected GitHub Release assets into online4tech/Online4Tech-Repository. It does not modify, delete, retag, or replace any source repository or source release.

## Why destination Releases?

The current inventory is about 31.76 GiB. GitHub blocks regular Git files above 100 MiB and enforces a 2 GiB push limit. GitHub Releases allow up to 1,000 assets per release, each under 2 GiB, with no total release-size or bandwidth cap. Binary payloads therefore belong in new destination Releases, not Git commits. Catalog JSON and documentation remain in Git.

Official limits:
- https://docs.github.com/en/repositories/releasing-projects/about-releases
- https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits

## Requirements

- Windows PowerShell 5.1 or PowerShell 7
- GitHub CLI (gh)
- A local clone of online4tech/Online4Tech-Repository
- gh auth login completed locally with permission to create Releases in the target repository

Never paste a Personal Access Token into ChatGPT or save one in this repository.

## First run: preview only

Open PowerShell in the repository folder and run:

    gh auth status
    .\tools\release-mirror\Start-ReleaseMirror.ps1 -Category small-first -MaxFiles 10 -MaxBatchGB 0.5

This is a dry run. It only reads the inventory and prints the exact candidate list. It downloads or uploads nothing.

## Execute a reviewed batch

After reviewing the exact list and confirming redistribution rights/attribution for every selected asset:

    .\tools\release-mirror\Start-ReleaseMirror.ps1 -Category skins -MaxFiles 10 -MaxBatchGB 0.5 -Execute -IConfirmRightsAndAttribution

For the first skin/plugin/Picons pass, use `small-first`. After a batch passes remote SHA-256 verification, the tool records its completed asset keys in `_release-mirror-work/completed-assets.json`; the next run skips those completed assets and selects the next batch. Keep the work folder so this progress ledger is preserved.

The script:
1. Downloads from the original URL recorded in the inventory.
2. Checks downloaded size.
3. Calculates SHA-256 and compares it with GitHub's published digest when available.
4. Creates a new prerelease in the target repository.
5. Uploads assets with collision-safe names while retaining original filenames in the manifest.
6. Downloads destination assets back and compares SHA-256 and size.
7. Writes a local manifest and SHA256SUMS.txt under _release-mirror-work.

The manifest preserves source repository, release tag/page, original filename, original download URL, original digest, category, content type, size, computed SHA-256 and target release details.

## Recommended order

1. skins
2. plugins
3. picons
4. scripts
5. other
6. bridge_tools (separate from Enigma2 plugins)
7. receiver_backups (last)

The small-first category selects non-`.sh` binary assets in skins, plugins and picons, in that priority order and then by size. Shell scripts are deliberately excluded from this first package batch.

## Safety rules

- No source repository or source Release is changed.
- No existing destination Release is overwritten; each execution creates a uniquely tagged new prerelease.
- Files of 2 GiB or larger are skipped.
- A batch stops on size/hash mismatch or upload/verification failure.
- Never treat Git blob SHA as a file SHA-256.
- Preserve original author attribution and any license/copyright notices. The operator confirms redistribution permission before execution; do not remove original notices from the packages.
- Product-test is not in the current release inventory and remains excluded from channel-list content and installation commands.
- The tool does not unpack/install packages or approve installation commands.
- Keep the local work folder until all batches are reviewed and the target releases are verified; it contains the completed-assets ledger used to avoid repeating successful transfers.

## Final verification record

The script uploads an initial manifest/checksum set, downloads the target assets and verifies every binary, then replaces the manifest/checksum assets in the same destination Release with the final PASS state. Inspect the destination release after success; never rerun a completed batch blindly.
