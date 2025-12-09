param(
    [switch]$AutoDeepClean,
    [switch]$ScanQuick,
    [switch]$ScanDeep,
    [switch]$CleanOnly,
    [switch]$DryRunOnly,
    [switch]$NetResetOnly
)

$ErrorActionPreference = "SilentlyContinue"
$logFile = Join-Path ([Environment]::GetFolderPath("Desktop")) "Antigravity-Cleaner.log"

function Log($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] $msg"
    Write-Output $line
    Add-Content -Path $logFile -Value $line
}

function Find-AntigravityUninstallEntries {
    $roots = @(
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    )
    $entries = @()
    foreach ($root in $roots) {
        if (Test-Path $root) {
            Get-ChildItem $root | ForEach-Object {
                $p = $_.PsPath
                $props = Get-ItemProperty $p
                $dn = $props.DisplayName
                if ($dn -and $dn -match "Antigravity") {
                    $entries += [pscustomobject]@{
                        DisplayName     = $dn
                        KeyPath         = $p
                        UninstallString = $props.UninstallString
                    }
                }
            }
        }
    }
    return $entries
}

function Find-LeftoverPatterns {
    @(
        "$env:LOCALAPPDATA\Programs\Antigravity*",
        "$env:LOCALAPPDATA\Antigravity*",
        "$env:APPDATA\Antigravity*",
        "$env:LOCALAPPDATA\Google\Antigravity*",
        "$env:APPDATA\Google\Antigravity*",
        "$env:LOCALAPPDATA\Temp\antigravity-stable-user-x64",
        "$env:LOCALAPPDATA\Temp\is-*.tmp"
    )
}

function Run-UninstallString($uninstallString, $dryRun=$false) {
    if (-not $uninstallString) { return }

    $u = $uninstallString.Trim()
    if ($dryRun) { Log "DRY-RUN uninstall: $u"; return }

    if ($u -match "unins\d+\.exe") {
        $exe = if ($u -match '\"(.+?unins\d+\.exe)\"') { $matches[1] } else { $u.Split(" ")[0].Trim('"') }
        if (Test-Path $exe) {
            Log "Running uninstaller: $exe"
            Start-Process -FilePath $exe -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" -Wait
        } else {
            Log "Uninstaller not found: $exe"
        }
        return
    }

    if ($u -match "msiexec") {
        Log "Running MSI uninstall: $u"
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c $u /qn /norestart" -Wait
        return
    }

    Log "Running generic uninstall: $u"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c $u" -Wait
}

function Remove-Paths($patterns, $dryRun=$false) {
    $found = 0; $removed = 0
    foreach ($pattern in $patterns) {
        $items = Get-ChildItem $pattern -ErrorAction SilentlyContinue
        foreach ($it in $items) {
            $found++
            if ($dryRun) {
                Log "DRY-RUN remove: $($it.FullName)"
            } else {
                Log "Removing: $($it.FullName)"
                Remove-Item -Recurse -Force $it.FullName
                $removed++
            }
        }
    }
    Log "Summary: found=$found, removed=$removed, dryRun=$dryRun"
    [pscustomobject]@{ Found=$found; Removed=$removed; DryRun=$dryRun }
}

function Scan($deep=$false) {
    Log "=== SCAN started (deep=$deep) ==="
    $entries = Find-AntigravityUninstallEntries

    if ($entries.Count -eq 0) {
        Log "No uninstall entries found."
    } else {
        Log "Uninstall entries:"
        $entries | ForEach-Object { Log " - $($_.DisplayName) :: $($_.KeyPath)" }
    }

    $patterns = Find-LeftoverPatterns
    Log "Checking leftover patterns:"
    $patterns | ForEach-Object { Log " - $_" }

    $existing = 0
    foreach ($pat in $patterns) {
        Get-ChildItem $pat -ErrorAction SilentlyContinue | ForEach-Object {
            $existing++; Log " - FOUND: $($_.FullName)"
        }
    }
    if ($existing -eq 0) { Log "Existing leftovers found: none" }

    if ($deep) {
        Log "Deep scan (related traces):"
        $deepTargets = @(
            "$env:LOCALAPPDATA\Google\Chrome\User Data\*\Extensions\*\*\*antigravity*",
            "$env:LOCALAPPDATA\Python\pythoncore-*\Lib\antigravity.py"
        )
        $deepFound = 0
        foreach ($dt in $deepTargets) {
            Get-ChildItem $dt -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
                $deepFound++; Log " - FOUND deep trace: $($_.FullName)"
            }
        }
        if ($deepFound -eq 0) { Log "Deep scan found: none" }
    }

    Log "=== SCAN finished ==="
}

function Clean($dryRun=$false) {
    Log "=== CLEAN started (dryRun=$dryRun) ==="
    $entries = Find-AntigravityUninstallEntries
    $uninstallAttempted = 0

    foreach ($e in $entries) {
        $uninstallAttempted++
        Log "Attempting uninstall for: $($e.DisplayName)"
        Run-UninstallString $e.UninstallString $dryRun
    }

    $patterns = Find-LeftoverPatterns
    $result = Remove-Paths $patterns $dryRun

    Log "=== CLEAN finished ==="
    Log ""

    if ($dryRun) {
        Log "DRY RUN COMPLETE. Would remove: $($result.Found) item(s)."
    } else {
        if ($uninstallAttempted -eq 0 -and $result.Found -eq 0) {
            Log "SUCCESS: No Antigravity installation or leftovers found."
            Log "System is clean. Next install will be a clean install."
        } elseif ($result.Removed -gt 0) {
            Log "SUCCESS: Cleanup finished. Removed: $($result.Removed) item(s)."
            Log "Clean install ready."
        } else {
            Log "NOTICE: Uninstall attempted ($uninstallAttempted) but no leftovers detected."
            Log "System should already be clean."
        }
    }
    Log ""
}

function Deep-Clean($dryRun=$false) {
    Log "=== DEEP CLEAN started (dryRun=$dryRun) ==="
    Clean $dryRun

    $extraTemp = @("$env:LOCALAPPDATA\Temp\*Antigravity*")
    $extraResult = Remove-Paths $extraTemp $dryRun

    Log "=== DEEP CLEAN finished ==="
    Log ""
    if ($dryRun) {
        Log "DEEP DRY RUN COMPLETE. Extra temp items would be removed: $($extraResult.Found)"
    } else {
        if ($extraResult.Removed -gt 0) {
            Log "DEEP CLEAN SUCCESS: Extra temp artifacts removed: $($extraResult.Removed)"
        } else {
            Log "DEEP CLEAN COMPLETE: No extra temp artifacts found."
        }
    }
    Log ""
}

function Network-Reset {
    Log "=== NETWORK RESET started ==="
    ipconfig /flushdns | Out-Null
    netsh winsock reset | Out-Null
    netsh int ip reset | Out-Null
    Log "Network reset commands executed. Restart recommended."
    Log "=== NETWORK RESET finished ==="
    Log "NETWORK RESET COMPLETE. Please restart Windows if needed."
}

# One-shot modes for GUI
if ($ScanQuick)    { Scan $false; exit }
if ($ScanDeep)     { Scan $true;  exit }
if ($CleanOnly)    { Clean $false; exit }
if ($DryRunOnly)   { Clean $true;  exit }
if ($NetResetOnly) { Network-Reset; exit }
if ($AutoDeepClean){ Deep-Clean $false; exit }

# Optional CLI menu
while ($true) {
    Clear-Host
    Write-Host "==============================="
    Write-Host "   Antigravity Cleaner v8"
    Write-Host "==============================="
    Write-Host "1) Scan (quick)"
    Write-Host "2) Scan (deep)"
    Write-Host "3) Clean (uninstall + leftovers)"
    Write-Host "4) Deep Clean"
    Write-Host "5) Dry Run"
    Write-Host "6) Network Reset"
    Write-Host "0) Exit"
    Write-Host ""

    $choice = Read-Host "Select an option"
    switch ($choice) {
        "1" { Scan $false; Read-Host "Press Enter" }
        "2" { Scan $true;  Read-Host "Press Enter" }
        "3" { Clean $false; Read-Host "Press Enter" }
        "4" { Deep-Clean $false; Read-Host "Press Enter" }
        "5" { Clean $true; Read-Host "Press Enter" }
        "6" { Network-Reset; Read-Host "Press Enter" }
        "0" { break }
        default { Write-Host "Invalid option."; Start-Sleep 1 }
    }
}
