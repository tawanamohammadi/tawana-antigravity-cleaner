# Changelog

All notable changes to the "Antigravity Cleaner" project will be documented in this file.

## [2.1.0] - 2025-12-10

### Added
- **Browser Login Helper**: Safe, selective cleaning of Antigravity browser traces
  - Supports Chrome, Edge, Brave, and Firefox
  - Scans all browser profiles
  - Removes only Antigravity-related cookies, cache, and localStorage
  - Automatic backups before deletion
  - Graceful browser process management
  
- **Session Manager**: Backup and restore browser sessions
  - AES-256-GCM encryption for secure storage
  - Avoid repeated logins
  - Session validation and expiration (30 days)
  - Manage multiple saved sessions
  
- **Network Optimizer**: Comprehensive network diagnostics
  - Test connectivity to Google services
  - DNS resolution diagnostics
  - Proxy/VPN conflict detection
  - SSL certificate verification
  - Detailed diagnostic reports
  - Network stack reset (Windows)

### Changed
- Updated menu system with new options (6: Browser Login Helper, 7: Session Manager)
- Enhanced logging with detailed agent operation logs in `.agent/logs/`
- Updated dependencies (added `requests`, `pycryptodome`)
- Updated `.gitignore` to allow agent logs

### Security
- Session data encrypted at rest using AES-256-GCM
- Master key stored with restrictive permissions
- No sensitive data in user-facing logs
- Automatic backups before any browser data deletion

---

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
