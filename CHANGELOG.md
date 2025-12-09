# Changelog

All notable changes to the "Antigravity Cleaner" project will be documented in this file.

## [2.0.0] - 2025-12-09
### Added
- **Cross-Platform Core**: Replaced PowerShell-only core with a robust Python engine (`src/main.py`).
- **New UI**: Implemented `rich` library for a beautiful, colorful CLI experience.
- **Process Management**: Added `psutil` integration to auto-detect and kill stuck Antigravity processes.
- **One-Liner Installers**: Added `install.ps1` (Windows) and `install.sh` (Linux/Mac) for instant deployment.
- **Launchers**: Added `run_windows.bat` and `run_mac_linux.sh` for easy double-click execution.
- **Bilingual Documentation**: Updated README with full English and Persian (Farsi) guides.

### Changed
- **Directory Structure**: Moved legacy scripts to `legacy/` folder.
- **Logic**: Improved cleanup logic to be safer and more comprehensive (Deep Scan).

### Removed
- **Dependency on PowerShell**: Core logic no longer relies solely on PowerShell, allowing Mac/Linux support.

---

## [1.0.0] - 2024-05-20
### Initial Release
- Basic PowerShell script for Windows.
- Registry cleaning.
- Temp file removal.
