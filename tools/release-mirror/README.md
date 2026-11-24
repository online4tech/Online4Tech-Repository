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


## Unattended sequential run (Windows)

After reviewing the source permissions and attribution for the indexed assets, the operator can start the sequential runner:

    .\tools\release-mirror\Run-AllReleaseMirror.ps1

The runner uses the existing completed-assets ledger and processes these groups in order:
1. small-first (non-.sh skins, plugins and picons)
2. remaining skins, plugins and picons (including script-like files classified in those groups)
3. scripts
4. other
5. bridge_tools
6. receiver_backups

It launches the existing single-batch worker repeatedly. A batch is considered complete only when the worker has downloaded the destination assets again, verified SHA-256 and size, published the final PASS manifest, and advanced the completed ledger. It then proceeds to the next batch without asking for per-batch approval.

Safety and recovery:
- The runner does not edit/delete source repositories or source Releases.
- It does not execute any mirrored package, shell script, command or backup.
- It does not delete or overwrite an existing destination Release.
- It stops on the first failed batch or if the ledger does not advance; it does not blindly retry a possibly partial Release.
- Logs and a JSON run summary are written under _release-mirror-work/automation/.
- A register of individual assets at/above 2 GiB is written to oversize-assets.json; these are not transferred by this runner and need a separate chunked-storage plan.
- The runner requests that Windows remain awake only while the process is active. Keep the computer powered and connected to the internet.
- Do not delete _release-mirror-work; it contains the completed ledger and recovery evidence.

To resume after a cleanly completed run, start the runner again; completed assets are skipped. If a run stops on error, inspect its log and the last destination Release before resuming.


## Interrupted upload recovery

`Start-ReleaseMirror.ps1` retries failed GitHub Release uploads up to five times and checks the remote asset SHA-256 before treating an interrupted upload response as successful. Existing assets with different bytes are never overwritten.

If an older batch stopped during upload, inspect its local manifest and destination Release first, then use `Recover-PartialBatch.ps1 -BatchTag <tag>`. The recovery script validates every local file against its manifest, skips remote assets only when size and GitHub SHA-256 match, uploads only missing assets, downloads the full destination batch for SHA-256 verification, publishes the final PASS manifest/checksums, and only then advances the completed ledger. It does not modify source repositories/releases or execute package contents.
