[CmdletBinding()]
param(
    [string]$BatchTag = 'o4t-mirror-small-first-20261124-043416',
    [string]$TargetRepo = 'online4tech/Online4Tech-Repository',
    [string]$WorkRoot = '.\_release-mirror-work',
    [int]$MaxRetries = 5
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Invoke-CheckedGh([string[]]$Arguments, [string]$Description) {
    & gh @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Description failed (exit $LASTEXITCODE)." }
}
$batchDir = Join-Path $WorkRoot $BatchTag
$downloadDir = Join-Path $batchDir 'downloads'
$verifyDir = Join-Path $batchDir 'verify'
$manifestPath = Join-Path $batchDir 'mirror-manifest.json'
$checksumPath = Join-Path $batchDir 'SHA256SUMS.txt'
$ledgerPath = Join-Path $WorkRoot 'completed-assets.json'
if (!(Test-Path $manifestPath) -or !(Test-Path $downloadDir)) { throw "Local batch files missing: $batchDir" }
$manifest = ConvertFrom-Json -InputObject (Get-Content $manifestPath -Raw -Encoding UTF8)
if ($manifest.Count -ne 10) { throw "Expected 10 manifest entries; found $($manifest.Count)." }
$release = gh release view $BatchTag --repo $TargetRepo --json assets,isPrerelease
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect destination release.' }
$remote = ($release | ConvertFrom-Json).assets
if (-not ($release | ConvertFrom-Json).isPrerelease) { throw 'Destination is not a prerelease; stopped.' }
foreach ($entry in $manifest) {
    $localPath = Join-Path $downloadDir $entry.mirrored_asset_name
    if (!(Test-Path -LiteralPath $localPath -PathType Leaf)) { throw "Local asset missing: $($entry.mirrored_asset_name)" }
    $local = Get-Item -LiteralPath $localPath
    $sha = (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($local.Length -ne [int64]$entry.size_bytes -or $sha -ne $entry.sha256) { throw "Local source integrity mismatch: $($entry.mirrored_asset_name)" }
    $existing = @($remote | Where-Object { $_.name -eq $entry.mirrored_asset_name })
    if ($existing.Count -gt 1) { throw "Duplicate remote asset name: $($entry.mirrored_asset_name)" }
    if ($existing.Count -eq 1) {
        $digest = [string]$existing[0].digest
        if ([int64]$existing[0].size -ne [int64]$entry.size_bytes -or $digest -ne ("sha256:" + $entry.sha256)) {
            throw "Remote asset exists but does not match source: $($entry.mirrored_asset_name)"
        }
        Write-Host "Already uploaded and digest-matched: $($entry.mirrored_asset_name)"
        continue
    }
    $uploaded = $false
    for ($attempt=1; $attempt -le $MaxRetries; $attempt++) {
        Write-Host "Uploading $($entry.mirrored_asset_name) (attempt $attempt/$MaxRetries)"
        & gh release upload $BatchTag $localPath --repo $TargetRepo 2>&1 | ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -eq 0) { $uploaded = $true; break }
        Start-Sleep -Seconds ([Math]::Min(30, 3 * $attempt))
        $check = gh release view $BatchTag --repo $TargetRepo --json assets
        if ($LASTEXITCODE -eq 0) {
            $now = ($check | ConvertFrom-Json).assets | Where-Object { $_.name -eq $entry.mirrored_asset_name }
            if ($now) {
                if ([int64]$now.size -eq [int64]$entry.size_bytes -and $now.digest -eq ("sha256:" + $entry.sha256)) { $uploaded = $true; break }
                throw "Upload outcome uncertain and remote digest mismatches: $($entry.mirrored_asset_name)"
            }
        }
    }
    if (-not $uploaded) { throw "Upload retries exhausted for $($entry.mirrored_asset_name). Local files retained." }
    $check = gh release view $BatchTag --repo $TargetRepo --json assets
    if ($LASTEXITCODE -ne 0) { throw 'Could not confirm uploaded asset.' }
    $confirmed = ($check | ConvertFrom-Json).assets | Where-Object { $_.name -eq $entry.mirrored_asset_name }
    if (-not $confirmed -or [int64]$confirmed.size -ne [int64]$entry.size_bytes -or $confirmed.digest -ne ("sha256:" + $entry.sha256)) {
        throw "Remote digest check failed after upload: $($entry.mirrored_asset_name)"
    }
}
if (!(Test-Path $verifyDir)) { New-Item -ItemType Directory -Force -Path $verifyDir | Out-Null }
Invoke-CheckedGh @('release','download',$BatchTag,'--repo',$TargetRepo,'--dir',$verifyDir) 'Downloading destination assets'
foreach ($entry in $manifest) {
    $remotePath = Join-Path $verifyDir $entry.mirrored_asset_name
    if (!(Test-Path -LiteralPath $remotePath -PathType Leaf)) { throw "Downloaded target asset missing: $($entry.mirrored_asset_name)" }
    $remoteFile = Get-Item -LiteralPath $remotePath
    $remoteSha = (Get-FileHash -LiteralPath $remotePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($remoteFile.Length -ne [int64]$entry.size_bytes -or $remoteSha -ne $entry.sha256) { throw "Downloaded target SHA-256 mismatch: $($entry.mirrored_asset_name)" }
    $entry.verification = 'PASS: downloaded source bytes equal downloaded target bytes by SHA-256 and size'
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifest | ForEach-Object { "$($_.sha256)  $($_.mirrored_asset_name)" } | Set-Content -LiteralPath $checksumPath -Encoding ASCII
Invoke-CheckedGh @('release','upload',$BatchTag,$manifestPath,$checksumPath,'--repo',$TargetRepo,'--clobber') 'Publishing final PASS manifest'
$keys = @()
if (Test-Path $ledgerPath) {
    $ledger = Get-Content $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $keys = @($ledger.completed_keys)
}
foreach ($entry in $manifest) {
    $key = "$($entry.original_repository)|$($entry.original_release_tag)|$($entry.original_asset_name)"
    if ($key -notin $keys) { $keys += $key }
}
[pscustomobject]@{ schema_version=1; updated_at=(Get-Date).ToString('o'); completed_keys=@($keys | Sort-Object -Unique) } |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ledgerPath -Encoding UTF8
Write-Host "RECOVERY PASS: $($manifest.Count) assets verified. Ledger now contains $(@($keys | Sort-Object -Unique).Count) keys."
Write-Host "Release: https://github.com/$TargetRepo/releases/tag/$BatchTag"
