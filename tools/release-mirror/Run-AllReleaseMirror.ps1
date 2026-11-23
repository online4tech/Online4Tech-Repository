[CmdletBinding()]
param(
    [int]$MaxFiles = 10,
    [double]$MaxBatchGB = 1.999,
    [string]$TargetRepo = 'online4tech/Online4Tech-Repository'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
$worker = Join-Path $PSScriptRoot 'Start-ReleaseMirror.ps1'
$inventoryPath = Join-Path $repoRoot 'catalog\release-assets-inventory.json'
$workRoot = Join-Path $repoRoot '_release-mirror-work'
$logDir = Join-Path $workRoot 'automation'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$runStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logPath = Join-Path $logDir "run-all-$runStamp.log"
$summaryPath = Join-Path $logDir "run-all-$runStamp-summary.json"
$oversizePath = Join-Path $logDir 'oversize-assets.json'
$transcriptStarted = $false
$exitReason = 'completed'
$completedAtStart = 0
$completedAtEnd = 0

function Get-CompletedKeys {
    $ledgerPath = Join-Path $workRoot 'completed-assets.json'
    $keys = @{}
    if (Test-Path -LiteralPath $ledgerPath -PathType Leaf) {
        $ledger = Get-Content -LiteralPath $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($key in @($ledger.completed_keys)) { $keys[[string]$key] = $true }
    }
    return ,$keys
}
function Get-PendingAssets([string]$Category) {
    $inventory = Get-Content -LiteralPath $inventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $done = Get-CompletedKeys
    $items = @()
    foreach ($release in $inventory.releases) {
        foreach ($asset in $release.assets) {
            $key = "$($release.repo)|$($release.tag)|$($asset.name)"
            if ($done.ContainsKey($key)) { continue }
            $categoryMatch = $false
            if ($Category -eq 'small-first') {
                $categoryMatch = ([string]$asset.category -in @('skins','plugins','picons')) -and ([IO.Path]::GetExtension([string]$asset.name).ToLowerInvariant() -ne '.sh')
            } else {
                $categoryMatch = ([string]$asset.category -eq $Category)
            }
            if (-not $categoryMatch) { continue }
            $size = [int64]$asset.size_bytes
            if ($size -le 0 -or $size -ge 2GB) { continue }
            $items += [pscustomobject]@{ key=$key; name=[string]$asset.name; size_bytes=$size; category=[string]$asset.category; repo=[string]$release.repo; tag=[string]$release.tag }
        }
    }
    return $items
}
function Get-CompletedCount {
    $done = Get-CompletedKeys
    return $done.Count
}

try {
    $signature = @'
using System;
using System.Runtime.InteropServices;
public static class O4TAwake {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
}
'@
    Add-Type -TypeDefinition $signature -ErrorAction SilentlyContinue
    [void][O4TAwake]::SetThreadExecutionState([uint32]2147483649)
    Start-Transcript -LiteralPath $logPath -Force | Out-Null
    $transcriptStarted = $true

    Write-Host '=== Online4Tech unattended Release mirror ==='
    Write-Host "Started: $(Get-Date -Format o)"
    Write-Host "Target: $TargetRepo"
    Write-Host 'The computer will be kept awake while this process runs.'
    Write-Host 'No source repository/release will be modified; no package/script will be executed.'
    if (-not (Test-Path -LiteralPath $worker -PathType Leaf)) { throw "Worker script missing: $worker" }
    if (-not (Test-Path -LiteralPath $inventoryPath -PathType Leaf)) { throw "Inventory missing: $inventoryPath" }
    if ($MaxFiles -lt 1 -or $MaxBatchGB -le 0 -or $MaxBatchGB -ge 2) { throw 'Use MaxFiles >= 1 and MaxBatchGB between 0 and 2.' }

    $completedAtStart = Get-CompletedCount
    $categories = @('small-first','skins','plugins','picons','scripts','other','bridge_tools','receiver_backups')
    $inventory = Get-Content -LiteralPath $inventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $oversize = @()
    foreach ($release in $inventory.releases) {
        foreach ($asset in $release.assets) {
            if ([int64]$asset.size_bytes -ge 2GB) {
                $oversize += [pscustomobject]@{ repository=[string]$release.repo; release_tag=[string]$release.tag; asset_name=[string]$asset.name; size_bytes=[int64]$asset.size_bytes; original_download_url=[string]$asset.download_url; status='not_transferred_individual_asset_at_or_above_2GiB' }
            }
        }
    }
    $oversize | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $oversizePath -Encoding UTF8
    Write-Host "Starting completed keys: $completedAtStart"
    Write-Host "Assets at/above 2 GiB excluded from this runner: $($oversize.Count)"

    foreach ($category in $categories) {
        while ($true) {
            $pending = @(Get-PendingAssets $category)
            if ($pending.Count -eq 0) {
                Write-Host "[$category] No remaining eligible assets."
                break
            }
            $before = Get-CompletedCount
            Write-Host ''
            Write-Host "[$category] Pending eligible: $($pending.Count). Starting next verified batch..."
            & $worker -Category $category -MaxFiles $MaxFiles -MaxBatchGB $MaxBatchGB -TargetRepo $TargetRepo -WorkRoot $workRoot -InventoryPath $inventoryPath -Execute -IConfirmRightsAndAttribution
            $after = Get-CompletedCount
            if ($after -le $before) { throw "Worker did not advance the completed ledger for category '$category'. Stopping to avoid duplicate/unsafe retries." }
            Write-Host "[$category] Batch verified and ledger advanced: $before -> $after"
        }
    }

    $completedAtEnd = Get-CompletedCount
    Write-Host ''
    Write-Host '=== AUTOMATION FINISHED ==='
    Write-Host "Completed keys: $completedAtEnd (started at $completedAtStart)"
    Write-Host "Oversize assets excluded: $($oversize.Count)"
    Write-Host "Oversize register: $oversizePath"
}
catch {
    $exitReason = 'stopped_on_error'
    Write-Host ("ERROR: " + $_.Exception.Message)
    Write-Host 'AUTOMATION STOPPED. Do not rerun blindly; inspect the last destination release and log first.'
}
finally {
    try { $completedAtEnd = Get-CompletedCount } catch {}
    $summary = [pscustomobject]@{
        schema_version=1
        started_at=$runStamp
        finished_at=(Get-Date).ToString('o')
        status=$exitReason
        completed_keys_at_start=$completedAtStart
        completed_keys_at_end=$completedAtEnd
        max_files_per_batch=$MaxFiles
        max_batch_gb=$MaxBatchGB
        target_repository=$TargetRepo
        log_file=$logPath
        oversize_register=$oversizePath
        note='Only verified assets enter the completed ledger. Original source releases are not modified. Assets >=2 GiB are listed separately and require a different transfer method.'
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    if ($transcriptStarted) { Stop-Transcript | Out-Null }
    try { [void][O4TAwake]::SetThreadExecutionState([uint32]2147483648) } catch {}
}
if ($exitReason -ne 'completed') { exit 1 }
exit 0


