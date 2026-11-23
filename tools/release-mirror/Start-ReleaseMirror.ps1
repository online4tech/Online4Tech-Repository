[CmdletBinding()]
param(
    [ValidateSet('plugins','skins','picons','scripts','other','bridge_tools','receiver_backups','small-first')]
    [string]$Category = 'small-first',
    [int]$MaxFiles = 20,
    [double]$MaxBatchGB = 0.75,
    [string]$InventoryPath = '.\catalog\release-assets-inventory.json',
    [string]$TargetRepo = 'online4tech/Online4Tech-Repository',
    [string]$WorkRoot = '.\_release-mirror-work',
    [switch]$Execute,
    [switch]$IConfirmRightsAndAttribution
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Stop-Check([string]$Message) { throw $Message }
function Get-SafeAssetName([int]$Index, [string]$Name) {
    $clean = [IO.Path]::GetFileName($Name) -replace '[^\w.\-()+ ]','_'
    if ([string]::IsNullOrWhiteSpace($clean)) { $clean = 'asset.bin' }
    return ('{0:D4}--{1}' -f $Index, $clean)
}
if (-not (Test-Path -LiteralPath $InventoryPath -PathType Leaf)) { Stop-Check "Inventory not found: $InventoryPath. Run from the repository clone." }
if ($MaxFiles -lt 1 -or $MaxBatchGB -le 0) { Stop-Check 'MaxFiles and MaxBatchGB must be positive.' }
$inventory = Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$all = @()
foreach ($release in $inventory.releases) {
    foreach ($asset in $release.assets) {
        $all += [pscustomobject]@{
            repo=[string]$release.repo; tag=[string]$release.tag; release_name=[string]$release.name
            release_url=[string]$release.html_url; asset_name=[string]$asset.name
            size_bytes=[int64]$asset.size_bytes; content_type=[string]$asset.content_type
            download_url=[string]$asset.download_url; digest=[string]$asset.digest
            category=[string]$asset.category; updated_at=[string]$asset.updated_at
        }
    }
}
$selected = switch ($Category) {
    'small-first' {
        $priority = @{ skins=0; plugins=1; picons=2; scripts=3; other=4 }
        @($all | Where-Object { $_.category -in @('skins','plugins','picons','scripts','other') } |
            Sort-Object @{Expression={ $priority[$_.category] }},size_bytes,repo,tag,asset_name)
    }
    default { @($all | Where-Object { $_.category -eq $Category } | Sort-Object size_bytes,repo,tag,asset_name) }
}
$maxBytes = [int64]($MaxBatchGB * 1GB)
$batch = @(); $totalBytes = [int64]0
foreach ($item in $selected) {
    if ($batch.Count -ge $MaxFiles) { break }
    if ($item.size_bytes -le 0) { continue }
    if ($item.size_bytes -ge 2GB) { Write-Warning "Skipped asset at/above 2 GiB: $($item.asset_name)"; continue }
    if (($totalBytes + $item.size_bytes) -gt $maxBytes) {
        if ($batch.Count -eq 0) { Write-Warning "First candidate exceeds MaxBatchGB: $($item.asset_name)" }
        continue
    }
    $batch += $item; $totalBytes += $item.size_bytes
}
if ($batch.Count -eq 0) { Stop-Check "No eligible assets found for category $Category under current batch limits." }
Write-Host ''; Write-Host "Category: $Category"
Write-Host ("Selected: {0} files / {1:N2} GB" -f $batch.Count,($totalBytes/1GB))
$batch | Select-Object repo,tag,asset_name,size_bytes,category | Format-Table -AutoSize
if (-not $Execute) {
    Write-Host 'DRY RUN ONLY. Nothing was downloaded or uploaded.'
    Write-Host 'Review the list, then rerun with -Execute -IConfirmRightsAndAttribution.'
    exit 0
}
if (-not $IConfirmRightsAndAttribution) { Stop-Check 'Confirm redistribution rights and attribution for every selected item before execution.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { Stop-Check 'GitHub CLI gh is not installed or not on PATH.' }
gh auth status
if ($LASTEXITCODE -ne 0) { Stop-Check 'GitHub CLI is not authenticated. Run gh auth login locally; never paste a token into chat.' }
gh repo view $TargetRepo --json nameWithOwner,url | Out-Null
if ($LASTEXITCODE -ne 0) { Stop-Check "Cannot access target repository $TargetRepo." }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$batchTag = "o4t-mirror-$Category-$stamp"
$batchDir = Join-Path $WorkRoot $batchTag
$downloadDir = Join-Path $batchDir 'downloads'
$verifyDir = Join-Path $batchDir 'verify'
New-Item -ItemType Directory -Force -Path $downloadDir,$verifyDir | Out-Null
$manifest = [System.Collections.Generic.List[object]]::new()
$index = 0
foreach ($item in $batch) {
    $index++; $uploadName = Get-SafeAssetName $index $item.asset_name
    $localPath = Join-Path $downloadDir $uploadName
    Write-Host ("[{0}/{1}] Downloading {2}" -f $index,$batch.Count,$item.asset_name)
    Invoke-WebRequest -Uri $item.download_url -OutFile $localPath -UseBasicParsing
    $actualSize = (Get-Item -LiteralPath $localPath).Length
    if ($actualSize -ne $item.size_bytes) { Stop-Check "Size mismatch for $($item.asset_name). Stopped before upload." }
    $sha = (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.digest -match '^sha256:([0-9a-fA-F]{64})$') {
        if ($sha -ne $Matches[1].ToLowerInvariant()) { Stop-Check "Source SHA-256 mismatch for $($item.asset_name). Stopped before upload." }
    }
    $manifest.Add([pscustomobject]@{
        original_repository=$item.repo; original_release_tag=$item.tag; original_release_name=$item.release_name
        original_release_url=$item.release_url; original_asset_name=$item.asset_name
        original_download_url=$item.download_url; original_digest=$item.digest
        category=$item.category; content_type=$item.content_type; size_bytes=$actualSize; sha256=$sha
        mirrored_asset_name=$uploadName; target_repository=$TargetRepo; target_release_tag=$batchTag
        verification='source_download_sha256_passed; target_verification_pending'
        attribution_note='Original source, release, filename and URL retained; source license/permission must be reviewed.'
    })
}
$manifestPath = Join-Path $batchDir 'mirror-manifest.json'
$checksumPath = Join-Path $batchDir 'SHA256SUMS.txt'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifest | ForEach-Object { "$($_.sha256)  $($_.mirrored_asset_name)" } | Set-Content -LiteralPath $checksumPath -Encoding ASCII
Write-Host "Creating destination prerelease $batchTag"
gh release create $batchTag --repo $TargetRepo --title "Online4Tech mirror batch - $Category - $stamp" --notes "Mirrored assets. Original source URLs and SHA-256 values are recorded in mirror-manifest.json. No source release was modified." --prerelease
if ($LASTEXITCODE -ne 0) { Stop-Check 'Could not create destination release. Local downloads were retained.' }
foreach ($file in (Get-ChildItem -LiteralPath $downloadDir -File)) {
    gh release upload $batchTag $file.FullName --repo $TargetRepo
    if ($LASTEXITCODE -ne 0) { Stop-Check "Upload failed for $($file.Name). Local files remain in $batchDir." }
}
gh release upload $batchTag $manifestPath $checksumPath --repo $TargetRepo
if ($LASTEXITCODE -ne 0) { Stop-Check 'Manifest/checksum upload failed. Inspect destination release before retrying.' }
Write-Host 'Downloading target release assets back for independent verification...'
gh release download $batchTag --repo $TargetRepo --dir $verifyDir
if ($LASTEXITCODE -ne 0) { Stop-Check 'Target download failed; do not mark this batch complete.' }
foreach ($entry in $manifest) {
    $remotePath = Join-Path $verifyDir $entry.mirrored_asset_name
    if (-not (Test-Path -LiteralPath $remotePath -PathType Leaf)) { Stop-Check "Target asset missing: $($entry.mirrored_asset_name)" }
    $remoteSize = (Get-Item -LiteralPath $remotePath).Length
    $remoteSha = (Get-FileHash -LiteralPath $remotePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($remoteSize -ne $entry.size_bytes -or $remoteSha -ne $entry.sha256) { Stop-Check "Target SHA-256/size verification failed: $($entry.mirrored_asset_name)" }
    $entry.verification='PASS: downloaded source bytes equal downloaded target bytes by SHA-256 and size'
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifest | ForEach-Object { "$($_.sha256)  $($_.mirrored_asset_name)" } | Set-Content -LiteralPath $checksumPath -Encoding ASCII
gh release upload $batchTag $manifestPath $checksumPath --repo $TargetRepo --clobber
if ($LASTEXITCODE -ne 0) { Stop-Check 'Binary checks passed, but publishing the final PASS manifest/checksums failed. Final files remain local.' }
Write-Host ''
Write-Host 'ALL BINARY ASSETS IN THIS BATCH PASSED REMOTE SHA-256 VERIFICATION.'
Write-Host "Destination: https://github.com/$TargetRepo/releases/tag/$batchTag"
Write-Host "Final PASS manifest and checksums are local: $batchDir"
