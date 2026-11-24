# Receiver backups

## Three upload methods

### 1. GitHub Releases website — easiest for files already on your PC
1. Open https://github.com/online4tech/Online4Tech-Repository/releases
2. Choose **Draft a new release**.
3. Use a unique tag and a descriptive title, preferably:
   `Backup | Brand | Exact Model | Image Version`
4. Attach the backup archive and optional cover/screenshots.
5. Add optional plain-text metadata in the release description (no JSON file needed):
   ```text
   Brand: Vu+
   Model: Vu+ Zero 4K
   Version: OpenATV 8.0.1
   Date: 2026-11-24
   Description: Clean image with basic setup
   Compatibility: Vu+ Zero 4K
   ID: vu-zero-4k
   ```
6. Publish the release. GitHub Actions generates the backup.json manifest and updates the website index.

Name the cover image `cover.webp`, `cover.jpg`, `thumbnail.png`, or `poster.jpg`. Other image assets are treated as screenshots. By default, the card ID is derived from brand + model, so a newer Release for the same model updates the existing card instead of adding a duplicate. Set a different `ID:` in the Release description only when you intentionally want a separate card for another backup line.

### 2. GitHub Desktop / Git
- Use this for normal backup folders and files that fit GitHub's regular repository upload limits.
- Keep the structure `backups/<brand>/<model>/<backup-id>/`; push to `main`.
- Do not commit files larger than 100 MiB. For large archives, use the Releases website method. If you already use GitHub CLI, you can upload an asset with: `gh release upload backup-vu-zero-4k-2026 "D:\Backups\fullbackup.zip" --repo online4tech/Online4Tech-Repository`. If that Release was already published, run the workflow below with only its `tag_name` to refresh the index.
- Existing folder-based backups continue to use the existing `backup.json` workflow; Release uploads do not require a manually created JSON file.

### 3. GitHub Actions cloud upload
1. Open https://github.com/online4tech/Online4Tech-Repository/actions/workflows/backup-release-publisher.yml
2. Choose **Run workflow**.
3. Enter a direct-download URL to a cloud-hosted archive, a unique tag, and the model details.
4. Run the workflow. The runner downloads the file and attaches it to a Release; it is not downloaded to your PC. To refresh a Release after adding assets to an already-published Release, leave `source_url` blank and enter only `tag_name`.

The source URL must be directly downloadable without interactive login. Files must be smaller than 2 GiB. If the URL does not end in a supported archive extension, enter the original archive name in `file_name`.

## Notes
- Actions generates `catalog/uploads/release-backups/<tag>/backup.json` automatically.
- Use a new unique tag for each new backup version. Do not reuse a tag for a different model or image.
- Existing releases and their assets are preserved; this automation does not delete old releases.
- Never upload passwords, subscription credentials, personal data, or other sensitive information.
