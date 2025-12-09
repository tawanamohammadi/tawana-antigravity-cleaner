# Tawana Antigravity Cleaner (CLI)

A Windows PowerShell command‑line tool to **fully uninstall Google Antigravity IDE** and remove leftover files/caches for a clean reinstall.

> **Maintained by TawanaNetworkLtc**

---

## What this tool does

* Detects Antigravity uninstall entries (per‑user + system)
* Runs the vendor uninstaller when available
* Deletes leftover folders in AppData/Programs/Temp
* Optional **Deep Clean** to remove extra related caches
* Optional **Network Reset** (useful if login/network errors persist)
* Creates a timestamped log file on your Desktop

---

## Requirements

* Windows 10 / Windows 11
* PowerShell 5.1+ (built‑in) or PowerShell 7+ (recommended)
* **Run as Administrator** for best results

---

## Files in this repo

```text
/antigravity-cleaner
  Antigravity-Cleaner.ps1        # Core CLI cleaner (run this)
  Antigravity-Cleaner-GUI.ps1    # Optional GUI wrapper (future)
  README.md
  LICENSE
```

CLI‑only users just need:

* `Antigravity-Cleaner.ps1`

---

## Quick start

### Option A — One‑liner (download & run latest)

No manual download needed. This runs the latest core script directly from GitHub:

```powershell
iwr -useb https://raw.githubusercontent.com/tawanamohammadi/tawana-antigravity-cleaner/main/Antigravity-Cleaner.ps1 | iex
```

After that, run any command (examples below), or just follow on‑screen prompts if your core script shows a menu.

---

### Option B — Download ZIP / clone

1. Download or clone this repo.
2. Put `Antigravity-Cleaner.ps1` somewhere like `C:\tools\`.
3. Open PowerShell **as Administrator**.
4. Run one of the commands below.

---

## How to run (local)

### Step 1 — Open Admin PowerShell

Start Menu → search **PowerShell** → **Run as Administrator**

### Step 2 — Go to the folder

```powershell
cd C:\tools
```

### Step 3 — (Optional) allow running for this session

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

---

## Commands

> All commands below assume you are in the folder containing the script.

### 1) Scan (Quick)

Checks uninstall registry entries and common leftover locations.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -ScanQuick
```

### 2) Scan (Deep)

Quick scan + extra traces (related caches, extension icons, etc.).

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -ScanDeep
```

### 3) Clean Only

Runs uninstall (if found) + removes main leftovers.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -CleanOnly
```

### 4) Deep Clean (Recommended)

Full clean + extra caches/traces.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -AutoDeepClean
```

### 5) Dry Run

Shows what would be removed **without deleting anything**.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -DryRunOnly
```

### 6) Network Reset

Runs Windows network reset commands. **Restart recommended afterwards.**

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -NetResetOnly
```

### 7) One‑shot full repair

Deep Clean + Network Reset (run sequentially).

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -AutoDeepClean
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -NetResetOnly
```

---

## Output & logs

* The tool prints progress to the console.
* A log file is created on your Desktop:

```text
Desktop\Antigravity-Cleaner.log
```

If you want a different path, edit the `$LogFile` value in the core script.

---

## Typical workflow (clean reinstall)

1. Run Dry Run (optional, safe preview):

```powershell
.\Antigravity-Cleaner.ps1 -DryRunOnly
```

2. Run Deep Clean:

```powershell
.\Antigravity-Cleaner.ps1 -AutoDeepClean
```

3. Restart Windows.

4. Reinstall Antigravity IDE normally.

5. If login is still broken, run Network Reset:

```powershell
.\Antigravity-Cleaner.ps1 -NetResetOnly
```

Restart again.

---

## Troubleshooting

### 1) “ExecutionPolicy” / script blocked

Run:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

Then retry.

### 2) “No uninstall entries found”

This usually means Antigravity is already removed from registry. The script will still cleanup leftovers.

### 3) Login still fails after clean

Run network reset:

```powershell
.\Antigravity-Cleaner.ps1 -NetResetOnly
```

Restart afterward.

### 4) I want to confirm nothing is left

Run deep scan:

```powershell
.\Antigravity-Cleaner.ps1 -ScanDeep
```

If it reports `none`, you are clean.

---

## Safety notes

* The script only targets folders/keys that clearly match **Antigravity** patterns.
* Dry Run is provided for verification.
* Run as Admin for full coverage.

---

## Contributing

PRs and improvements are welcome.

* Keep changes Windows‑safe
* Avoid deleting unrelated Google/Chrome data
* Add new leftover paths only when verified

---

## License

Choose your license (MIT recommended) and add a `LICENSE` file.

---

## Author

**TawanaNetworkLtc**

Ethical AI & Data Transparency Research Hub

---

If you want a GUI later, you can add a wrapper without changing the core script.
