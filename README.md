# Tawana Antigravity Cleaner (CLI)

A Windows PowerShell command‑line tool to **fully uninstall Google Antigravity IDE** and remove leftover files/caches for a clean reinstall.

> **Maintained by TawanaNetworkLtc**

<p align="center">
  <!-- Replace with your latest screenshot if needed -->
  <img width="703" height="481" alt="Antigravity Cleaner CLI screenshot" src="https://github.com/user-attachments/assets/a1aca41e-7e8b-4ad0-972b-f0564d2f11d4" />
</p>

---

## Why this exists

Antigravity IDE sometimes leaves behind user‑level caches, temp installers, and registry entries. These leftovers can cause:

* Repeated Google/Gmail login errors
* Broken updates or corrupted profiles
* Conflicting reinstalls
* Random crashes / missing extensions

This cleaner gives you a reliable **one‑command reset** before reinstalling.

---

## Features

* ✅ Detects uninstall entries (per‑user + system)
* ✅ Runs the vendor uninstaller when available
* ✅ Deletes leftover folders in **AppData / Programs / Temp**
* ✅ Optional **Deep Clean** for extra traces
* ✅ Optional **Network Reset** for stubborn login/network issues
* ✅ Safe **Dry Run** mode first
* ✅ Creates a timestamped log on Desktop

---

## Requirements

* Windows 10 / Windows 11
* PowerShell 5.1+ (built‑in) or PowerShell 7+ (recommended)
* **Run as Administrator** for best results

> Tip: The script resolves user folders dynamically, so it works even if your profile isn’t on `C:`.

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

1. Download or clone this repo.
2. Put `Antigravity-Cleaner.ps1` somewhere like `C:\tools\`.
3. Open PowerShell **as Administrator**.
4. Run one of the commands below.

---

## How to run

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

Quick scan + extra traces (related caches, extension icons, temp artifacts).

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -ScanDeep
```

### 3) Clean Only

Runs uninstall (if found) + removes main leftovers.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -CleanOnly
```

### 4) Deep Clean (Recommended)

Full clean + deep cache/traces cleanup.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -AutoDeepClean
```

### 5) Dry Run

Shows what would be removed **without deleting anything**.

```powershell
powershell -ExecutionPolicy Bypass -File .\Antigravity-Cleaner.ps1 -DryRunOnly
```

### 6) Network Reset

Runs Windows network reset commands.
**Restart recommended afterwards.**

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

## Recommended clean‑reinstall workflow

1. **Dry Run** (preview targets):

```powershell
.\Antigravity-Cleaner.ps1 -DryRunOnly
```

2. **Deep Clean**:

```powershell
.\Antigravity-Cleaner.ps1 -AutoDeepClean
```

3. Restart Windows.

4. Reinstall Antigravity IDE normally.

5. If Gmail/login errors persist:

```powershell
.\Antigravity-Cleaner.ps1 -NetResetOnly
```

Restart again.

---

## Troubleshooting

### 1) ExecutionPolicy / script blocked

Run once per session:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

### 2) No uninstall entries found

Registry uninstall key is already gone. The script will still remove leftovers.

### 3) Login still fails after clean

Run network reset:

```powershell
.\Antigravity-Cleaner.ps1 -NetResetOnly
```

Restart afterward.

### 4) Confirming a fully clean state

Run deep scan:

```powershell
.\Antigravity-Cleaner.ps1 -ScanDeep
```

If it reports `none`, your system is clean.

---

## Safety notes

* The script only targets folders/keys that clearly match **Antigravity** patterns.
* **Dry Run** is the safest first step.
* Run as Admin for full coverage.
* Unrelated Chrome/Google data is not removed.

---

## Contributing

PRs and improvements are welcome.

* Keep changes Windows‑safe
* Avoid deleting unrelated Google/Chrome data
* Add new leftover paths only when verified
* Keep CLI flags backward compatible when possible

---

## License

MIT is recommended. Add your license text as `LICENSE`.

---

## Author

**TawanaNetworkLtc**
Ethical AI & Data Transparency Research Hub

---

If you want a GUI later, you can add a wrapper without changing the core script.
