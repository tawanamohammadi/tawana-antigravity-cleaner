import os
import sys
import platform
import shutil
import subprocess
import time
import glob
import logging
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Import new modules
try:
    from browser_helper import BrowserHelper
    from network_optimizer import NetworkOptimizer
    from session_manager import SessionManager
except ImportError as e:
    # Modules not yet available, will be created
    BrowserHelper = None
    NetworkOptimizer = None
    SessionManager = None

# Try imports for runtime (UI and Process handling)
try:
    import psutil
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.style import Style
    from rich import print as rprint
except ImportError:
    print("Missing dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Platform check
CURRENT_OS = platform.system()
IS_WINDOWS = CURRENT_OS == "Windows"
IS_MAC = CURRENT_OS == "Darwin"
IS_LINUX = CURRENT_OS == "Linux"

if IS_WINDOWS:
    import winreg

# Setup Console
console = Console()

# --- Configuration & Constants ---

APP_NAME = "Antigravity"
LOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "Antigravity-Cleaner.log")

class Cleaner:
    def __init__(self):
        self.dry_run = False
        self.found_items = []

    def log(self, message, style="dim"):
        """Log to file and console."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Write to file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
        # Write to console (fancy)
        console.print(f"[{style}]{message}[/{style}]")

    def get_user_confirmation(self, question):
        return Confirm.ask(question)

    # --- Scanning Logic ---

    def scan_processes(self):
        """Check if Antigravity is running."""
        self.log("Scanning for running processes...", style="cyan")
        running = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if APP_NAME.lower() in proc.info['name'].lower():
                    running.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return running

    def kill_processes(self, processes):
        if not processes:
            return
        
        self.log(f"Found {len(processes)} running Antigravity processes.", style="yellow")
        if self.dry_run:
            self.log("[Dry Run] Would terminate processes.", style="yellow")
            return

        for proc in processes:
            try:
                proc.kill()
                self.log(f"Killed process {proc.info['name']} (PID: {proc.info['pid']})", style="green")
            except Exception as e:
                self.log(f"Failed to kill {proc.info['name']}: {e}", style="red")

    def find_uninstallers_windows(self):
        """Find uninstall strings in Windows Registry."""
        self.log("Scanning Windows Registry for uninstallers...", style="cyan")
        uninstallers = []
        roots = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for hive, path in roots:
            try:
                with winreg.OpenKey(hive, path) as key:
                    for i in range(0, winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if APP_NAME.lower() in display_name.lower():
                                        uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                        uninstallers.append({
                                            "name": display_name,
                                            "key": path + "\\" + subkey_name,
                                            "cmd": uninstall_string
                                        })
                                except FileNotFoundError:
                                    pass
                        except OSError:
                            continue
            except OSError:
                continue
        return uninstallers

    def get_cleanup_paths(self, deep=False):
        """Return list of paths to check based on OS."""
        paths = []
        home = os.path.expanduser("~")

        if IS_WINDOWS:
            local_appdata = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
            appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
            temp = os.environ.get("TEMP", os.path.join(local_appdata, "Temp"))
            
            paths.extend([
                os.path.join(local_appdata, "Programs", "Antigravity"),
                os.path.join(local_appdata, "Antigravity"),
                os.path.join(appdata, "Antigravity"),
                os.path.join(appdata, "Google", "Antigravity"), # Based on legacy script
                os.path.join(local_appdata, "Google", "Antigravity"),
            ])
            
            if deep:
                paths.extend([
                    os.path.join(temp, "antigravity-stable-user-x64"),
                    os.path.join(temp, "is-*.tmp"), # Inno Setup temp files
                    # Chrome Extension Trace (Wildcard structure handled by expand_globs)
                    os.path.join(local_appdata, "Google", "Chrome", "User Data", "*", "Extensions", "*", "*", "*antigravity*"),
                    # Python Lib Trace
                    os.path.join(local_appdata, "Python", "pythoncore-*", "Lib", "antigravity.py")
                ])

        elif IS_MAC:
            paths.extend([
                # Application
                "/Applications/Antigravity.app",
                # Application Support
                os.path.join(home, "Library", "Application Support", "Antigravity"),
                # Recent Documents (shared file list)
                os.path.join(home, "Library", "Application Support", "com.apple.sharedfilelist",
                             "com.apple.LSSharedFileList.ApplicationRecentDocuments", "com.google.antigravity.sfl3"),
                # Caches
                os.path.join(home, "Library", "Caches", "Antigravity"),
                os.path.join(home, "Library", "Caches", "com.google.antigravity"),
                os.path.join(home, "Library", "Caches", "com.google.antigravity.ShipIt"),
                # HTTP Storages
                os.path.join(home, "Library", "HTTPStorages", "com.google.antigravity"),
                # Preferences
                os.path.join(home, "Library", "Preferences", "com.google.antigravity.plist"),
                os.path.join(home, "Library", "Preferences", "ByHost", "com.google.antigravity.ShipIt.*.plist"),
                # Saved Application State
                os.path.join(home, "Library", "Saved Application State", "com.antigravity.savedState"),
                os.path.join(home, "Library", "Saved Application State", "com.google.antigravity.savedState"),
            ])

        elif IS_LINUX:
            paths.extend([
                os.path.join(home, ".config", "Antigravity"),
                os.path.join(home, ".local", "share", "Antigravity"),
                os.path.join(home, ".cache", "Antigravity"),
            ])

        return paths

    def expand_globs(self, paths):
        """Expand wildcard paths."""
        expanded = []
        for p in paths:
            # Simple check if it's a glob pattern or exact path
            if "*" in p:
                expanded.extend(glob.glob(p))
            else:
                expanded.append(p)
        return list(set(expanded)) # Unique

    def clean_paths(self, paths):
        found_any = False
        for p in paths:
            if os.path.exists(p):
                found_any = True
                if self.dry_run:
                    self.log(f"[Dry Run] Would remove: {p}", style="yellow")
                else:
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p)
                        else:
                            os.remove(p)
                        self.log(f"Removed: {p}", style="green")
                    except Exception as e:
                        self.log(f"Error removing {p}: {e}", style="red")
        
        if not found_any:
            self.log("No leftover files found in standard paths.", style="dim")


    def run_windows_uninstallers(self, uninstallers):
        for item in uninstallers:
            cmd = item['cmd']
            self.log(f"Running uninstaller for: {item['name']}", style="bold white")
            if self.dry_run:
                self.log(f"[Dry Run] CMD: {cmd}", style="yellow")
                continue

            # Attempt to parse quiet flags
            # This is heuristic based on the legacy script
            final_cmd = cmd
            args = []
            
            if "msiexec" in cmd.lower():
                args = ["/qn", "/norestart"]
                # We need to restructure for subprocess
                # cmd usually: msiexec /x {GUID}
                parts = cmd.split()
                exe = parts[0]
                arguments = parts[1:] + args
                try:
                    subprocess.run([exe] + arguments, check=True)
                    self.log("MSI Uninstall complete.", style="green")
                except subprocess.CalledProcessError as e:
                    self.log(f"Uninstall failed: {e}", style="red")
            
            elif "unins" in cmd.lower() and ".exe" in cmd.lower():
                 # Ex: "C:\path\unins000.exe"
                 # We simply run it with silent flags
                 # Need to extract the exe path carefully if quoted
                 import shlex
                 parts = shlex.split(cmd)
                 exe = parts[0]
                 # Common InnoSetup/NSIS silent flags
                 silent_args = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
                 try:
                    subprocess.run([exe] + silent_args, check=True)
                    self.log("Uninstaller executed successfully.", style="green")
                 except subprocess.CalledProcessError as e:
                    self.log(f"Uninstaller failed: {e}", style="red")
            else:
                self.log(f"Unknown uninstaller type. Running manually: {cmd}", style="yellow")
                subprocess.run(cmd, shell=True)


    def network_reset(self):
        self.log("Resetting Network Settings...", style="bold magenta")
        
        commands = []
        if IS_WINDOWS:
            commands = [
                "ipconfig /flushdns",
                "netsh winsock reset",
                "netsh int ip reset"
            ]
        elif IS_MAC:
            commands = [
                "dscacheutil -flushcache",
                "killall -HUP mDNSResponder"
            ]
        elif IS_LINUX:
            # Distro dependent, try systemd-resolve or just simple flush
            commands = [
                "resolvectl flush-caches" 
            ]

        if self.dry_run:
            for cmd in commands:
                self.log(f"[Dry Run] Would run: {cmd}", style="yellow")
        else:
            for cmd in commands:
                self.log(f"Executing: {cmd}", style="cyan")
                try:
                    subprocess.run(cmd, shell=True, check=False) # Check false to ignore errors on missing cmds
                except Exception as e:
                    self.log(f"Error running {cmd}: {e}", style="red")
            self.log("Network reset complete. Restart recommended.", style="green")

    # --- Shell Config Cleanup ---

    def get_shell_config_files(self):
        """Return list of shell config files to scan for Antigravity entries."""
        home = os.path.expanduser("~")
        config_files = []

        if IS_WINDOWS:
            # Windows PowerShell profile locations
            documents = os.path.join(home, "Documents")
            config_files.extend([
                # Windows PowerShell (5.1)
                os.path.join(documents, "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
                os.path.join(documents, "WindowsPowerShell", "profile.ps1"),
                # PowerShell Core (7+)
                os.path.join(documents, "PowerShell", "Microsoft.PowerShell_profile.ps1"),
                os.path.join(documents, "PowerShell", "profile.ps1"),
                # All Users profiles (may need admin)
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"),
                            "PowerShell", "7", "profile.ps1"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"),
                            "System32", "WindowsPowerShell", "v1.0", "profile.ps1"),
                # Git Bash on Windows (if installed)
                os.path.join(home, ".bashrc"),
                os.path.join(home, ".bash_profile"),
            ])
        else:
            # Unix-like systems (macOS and Linux)
            config_files.extend([
                os.path.join(home, ".profile"),
                os.path.join(home, ".bash_profile"),
                os.path.join(home, ".bashrc"),
                os.path.join(home, ".zshrc"),
                os.path.join(home, ".zprofile"),
                os.path.join(home, ".zshenv"),
            ])

            if IS_MAC:
                # macOS-specific locations
                config_files.extend([
                    os.path.join(home, ".zlogin"),
                    os.path.join(home, ".bash_login"),
                ])
            elif IS_LINUX:
                # Linux-specific locations
                config_files.extend([
                    os.path.join(home, ".bash_login"),
                    "/etc/profile.d/antigravity.sh",  # System-wide (may need sudo)
                ])

        # Return only files that exist
        return [f for f in config_files if os.path.isfile(f)]

    def scan_shell_configs(self):
        """Scan shell config files for Antigravity-related entries."""
        config_files = self.get_shell_config_files()

        # Common patterns (work across all shells)
        patterns = [
            re.compile(r'.*antigravity.*', re.IGNORECASE),
            re.compile(r'.*ANTIGRAVITY.*'),
        ]

        # Unix shell patterns (bash/zsh)
        unix_patterns = [
            re.compile(r'export\s+PATH=.*[Aa]ntigravity.*'),
            re.compile(r'alias\s+\w*antigravity\w*=.*', re.IGNORECASE),
            re.compile(r'source.*antigravity.*', re.IGNORECASE),
            re.compile(r'\.\s+.*antigravity.*', re.IGNORECASE),  # . /path/to/antigravity
            re.compile(r'eval.*antigravity.*', re.IGNORECASE),
        ]

        # PowerShell patterns
        powershell_patterns = [
            re.compile(r'\$env:PATH.*antigravity.*', re.IGNORECASE),
            re.compile(r'Set-Alias.*antigravity.*', re.IGNORECASE),
            re.compile(r'New-Alias.*antigravity.*', re.IGNORECASE),
            re.compile(r'Import-Module.*antigravity.*', re.IGNORECASE),
            re.compile(r'\.\s+.*antigravity.*\.ps1', re.IGNORECASE),  # Dot-sourcing .ps1
            re.compile(r'Add-PathVariable.*antigravity.*', re.IGNORECASE),
            re.compile(r'\[Environment\]::SetEnvironmentVariable.*antigravity.*', re.IGNORECASE),
        ]

        found_entries = []

        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                # Determine which patterns to use based on file type
                is_powershell = config_file.endswith('.ps1')
                if is_powershell:
                    active_patterns = patterns + powershell_patterns
                    comment_char = '#'
                else:
                    active_patterns = patterns + unix_patterns
                    comment_char = '#'

                for line_num, line in enumerate(lines, 1):
                    # Skip comments that just mention antigravity
                    stripped = line.strip()
                    if stripped.startswith(comment_char):
                        # Only flag comments if they look like commented-out code
                        if not any(p.match(stripped[1:].strip()) for p in active_patterns):
                            continue

                    for pattern in active_patterns:
                        if pattern.match(line):
                            found_entries.append({
                                'file': config_file,
                                'line_num': line_num,
                                'content': line.rstrip('\n'),
                                'pattern': pattern.pattern
                            })
                            break  # Don't match same line multiple times

            except (IOError, OSError) as e:
                self.log(f"Could not read {config_file}: {e}", style="yellow")

        return found_entries

    def clean_shell_configs(self, entries_to_remove):
        """Remove Antigravity entries from shell config files after backing up."""
        if not entries_to_remove:
            self.log("No shell config entries to clean.", style="dim")
            return

        # Group entries by file
        files_to_clean = {}
        for entry in entries_to_remove:
            file_path = entry['file']
            if file_path not in files_to_clean:
                files_to_clean[file_path] = []
            files_to_clean[file_path].append(entry['line_num'])

        backup_dir = os.path.join(os.path.expanduser("~"), ".antigravity-cleaner", "backups", "shell-configs")
        os.makedirs(backup_dir, exist_ok=True)

        for file_path, line_numbers in files_to_clean.items():
            if self.dry_run:
                self.log(f"[Dry Run] Would clean {len(line_numbers)} lines from {file_path}", style="yellow")
                continue

            try:
                # Create backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = os.path.basename(file_path) + f".backup_{timestamp}"
                backup_path = os.path.join(backup_dir, backup_name)
                shutil.copy2(file_path, backup_path)
                self.log(f"Backup created: {backup_path}", style="dim")

                # Read file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                # Remove matching lines (convert to 0-indexed)
                lines_to_remove = set(ln - 1 for ln in line_numbers)
                new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]

                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)

                self.log(f"Cleaned {len(line_numbers)} lines from {file_path}", style="green")

            except (IOError, OSError) as e:
                self.log(f"Error cleaning {file_path}: {e}", style="red")

    def scan_windows_path_registry(self):
        """Scan Windows Registry for Antigravity entries in PATH."""
        if not IS_WINDOWS:
            return []

        found_entries = []

        # Registry locations for PATH
        registry_locations = [
            (winreg.HKEY_CURRENT_USER, r"Environment", "User PATH"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
             "System PATH"),
        ]

        for hive, key_path, description in registry_locations:
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                    try:
                        path_value, reg_type = winreg.QueryValueEx(key, "Path")
                        if path_value:
                            # Split PATH into components
                            path_parts = path_value.split(';')
                            for i, part in enumerate(path_parts):
                                if 'antigravity' in part.lower():
                                    found_entries.append({
                                        'hive': hive,
                                        'key_path': key_path,
                                        'description': description,
                                        'path_index': i,
                                        'path_value': part,
                                        'full_path': path_value,
                                        'reg_type': reg_type
                                    })
                    except FileNotFoundError:
                        pass  # Path variable doesn't exist
            except OSError as e:
                self.log(f"Could not read {description}: {e}", style="yellow")

        return found_entries

    def clean_windows_path_registry(self, entries_to_remove):
        """Remove Antigravity entries from Windows PATH in Registry."""
        if not IS_WINDOWS or not entries_to_remove:
            return

        # Group by registry key
        keys_to_clean = {}
        for entry in entries_to_remove:
            key_id = (entry['hive'], entry['key_path'])
            if key_id not in keys_to_clean:
                keys_to_clean[key_id] = {
                    'description': entry['description'],
                    'full_path': entry['full_path'],
                    'reg_type': entry['reg_type'],
                    'paths_to_remove': []
                }
            keys_to_clean[key_id]['paths_to_remove'].append(entry['path_value'])

        # Backup file for registry changes
        backup_dir = os.path.join(os.path.expanduser("~"), ".antigravity-cleaner", "backups", "registry")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"path_backup_{timestamp}.txt")

        for (hive, key_path), data in keys_to_clean.items():
            if self.dry_run:
                self.log(f"[Dry Run] Would remove {len(data['paths_to_remove'])} paths from {data['description']}", style="yellow")
                continue

            try:
                # Save backup
                with open(backup_file, 'a', encoding='utf-8') as f:
                    hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
                    f.write(f"{hive_name}\\{key_path}\\Path\n")
                    f.write(f"Original: {data['full_path']}\n\n")

                # Calculate new PATH
                current_parts = data['full_path'].split(';')
                new_parts = [p for p in current_parts if p.lower() not in
                            [r.lower() for r in data['paths_to_remove']]]
                new_path = ';'.join(new_parts)

                # Write to registry
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "Path", 0, data['reg_type'], new_path)

                self.log(f"Cleaned {len(data['paths_to_remove'])} paths from {data['description']}", style="green")
                self.log(f"Backup saved to: {backup_file}", style="dim")

            except OSError as e:
                self.log(f"Error cleaning {data['description']}: {e}", style="red")
                if "Access is denied" in str(e):
                    self.log("Try running as Administrator for System PATH changes.", style="yellow")

    def run_shell_config_cleanup(self):
        """Interactive shell config cleanup (cross-platform)."""
        found_anything = False

        # --- Shell/PowerShell Config Files ---
        self.log("Scanning shell configuration files...", style="cyan")

        config_files = self.get_shell_config_files()
        if config_files:
            self.log(f"Found {len(config_files)} config files to scan.", style="dim")
            shell_entries = self.scan_shell_configs()
        else:
            self.log("No shell config files found.", style="dim")
            shell_entries = []

        if shell_entries:
            found_anything = True
            self.log(f"\nFound {len(shell_entries)} Antigravity-related entries in config files:", style="yellow")

            table = Table(title="Shell/PowerShell Config Entries")
            table.add_column("File", style="cyan", no_wrap=True)
            table.add_column("Line", justify="right", style="magenta")
            table.add_column("Content", style="white")

            for entry in shell_entries:
                table.add_row(
                    os.path.basename(entry['file']),
                    str(entry['line_num']),
                    entry['content'][:60] + "..." if len(entry['content']) > 60 else entry['content']
                )

            console.print(table)

        # --- Windows Registry PATH ---
        registry_entries = []
        if IS_WINDOWS:
            self.log("\nScanning Windows Registry PATH...", style="cyan")
            registry_entries = self.scan_windows_path_registry()

            if registry_entries:
                found_anything = True
                self.log(f"\nFound {len(registry_entries)} Antigravity paths in Registry:", style="yellow")

                table = Table(title="Windows Registry PATH Entries")
                table.add_column("Location", style="cyan")
                table.add_column("Path Value", style="white")

                for entry in registry_entries:
                    table.add_row(
                        entry['description'],
                        entry['path_value'][:50] + "..." if len(entry['path_value']) > 50 else entry['path_value']
                    )

                console.print(table)
            else:
                self.log("No Antigravity paths found in Registry.", style="dim")

        # --- No entries found ---
        if not found_anything:
            self.log("\nNo Antigravity-related entries found.", style="green")
            return

        # --- Dry run mode ---
        if self.dry_run:
            self.log("\n[Dry Run] Would remove the above entries.", style="yellow")
            return

        # --- Confirm and clean ---
        if self.get_user_confirmation("\nRemove these entries? (Backups will be created)"):
            if shell_entries:
                self.clean_shell_configs(shell_entries)

            if registry_entries:
                self.clean_windows_path_registry(registry_entries)

            # Platform-specific completion message
            if IS_WINDOWS:
                self.log("\nShell config cleanup complete. Please restart your terminal or sign out/in for PATH changes.", style="bold green")
            else:
                self.log("\nShell config cleanup complete. Please restart your terminal or run 'source ~/.zshrc' (or equivalent).", style="bold green")
        else:
            self.log("Shell config cleanup cancelled.", style="dim")

    # --- Main Actions ---

    def run_clean(self, deep=False):
        # 1. Check processes
        procs = self.scan_processes()
        if procs:
            if self.dry_run or self.get_user_confirmation(f"Found {len(procs)} running instances. Kill them?"):
                self.kill_processes(procs)

        # 2. Uninstall (Windows only usually has registry uninstallers)
        if IS_WINDOWS:
            uninstallers = self.find_uninstallers_windows()
            if uninstallers:
                self.log(f"Found {len(uninstallers)} matching uninstallers.", style="bold white")
                if self.dry_run:
                    for u in uninstallers: self.log(f" - {u['name']}", style="dim")
                else:
                    if self.get_user_confirmation("Run uninstallers first?"):
                        self.run_windows_uninstallers(uninstallers)
            else:
                self.log("No uninstallers found in registry.", style="dim")

        # 3. Clean files
        self.log("Scanning for leftovers...", style="bold white")
        target_paths = self.get_cleanup_paths(deep=deep)
        target_paths = self.expand_globs(target_paths)
        
        # Filter existing
        existing = [p for p in target_paths if os.path.exists(p) or glob.glob(p)]
        
        if existing:
            self.log(f"Found {len(existing)} locations to clean.", style="yellow")
            self.clean_paths(existing)
        else:
            self.log("No leftovers found.", style="green")

        if deep:
             self.log("Deep scan complete.", style="bold green")

    def run_network_reset(self):
        self.network_reset()


# --- Agent Logging Setup ---

def setup_agent_logging():
    """Setup detailed logging for agent operations"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', '.agent', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'browser-helper-operations.log')
    
    logger = logging.getLogger('antigravity_agent')
    logger.setLevel(logging.DEBUG)
    
    # Rotating file handler (10MB max, keep 3 backups)
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    logger.addHandler(handler)
    return logger


# --- Browser Login Helper Submenu ---

def browser_login_helper_menu(browser_helper, network_optimizer, logger):
    """Browser Login Helper submenu"""
    while True:
        console.print("\n" + "="*70)
        console.print("[bold cyan]BROWSER LOGIN HELPER | کمک‌کننده ورود[/bold cyan]")
        console.print("="*70)
        console.print("\n1. [green]Clean Antigravity Browser Traces (Safe)[/green]")
        console.print("   [dim]پاک‌سازی ردهای Antigravity در مرورگر (ایمن)[/dim]")
        console.print("\n2. [yellow]Optimize Network for Login[/yellow]")
        console.print("   [dim]بهینه‌سازی شبکه برای ورود[/dim]")
        console.print("\n3. [magenta]Network Diagnostic Report[/magenta]")
        console.print("   [dim]گزارش تشخیصی شبکه[/dim]")
        console.print("\n4. [cyan]Run Full Login Repair (1+2)[/cyan]")
        console.print("   [dim]اجرای تعمیر کامل ورود[/dim]")
        console.print("\n0. [dim]Back to Main Menu[/dim]")
        
        choice = Prompt.ask("\nEnter choice", choices=["0", "1", "2", "3", "4"], default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            # Clean browser traces
            browsers = browser_helper.detect_installed_browsers()
            if not browsers:
                console.print("[red]No supported browsers found.[/red]")
                continue
            
            console.print(f"\n[cyan]Found browsers: {', '.join(browsers)}[/cyan]")
            browser = Prompt.ask("Select browser to clean", choices=browsers + ["all"], default="all")
            
            if browser == "all":
                for b in browsers:
                    stats = browser_helper.clean_browser_completely(b)
                    console.print(f"\n[green]✓ {b}: {stats['cookies']} cookies, {stats['cache']} cache items cleaned[/green]")
            else:
                stats = browser_helper.clean_browser_completely(browser)
                console.print(f"\n[green]✓ Cleaned {stats['cookies']} cookies, {stats['cache']} cache items[/green]")
        
        elif choice == "2":
            # Optimize network
            console.print("\n[cyan]Optimizing network settings...[/cyan]")
            network_optimizer.clear_dns_cache()
            if IS_WINDOWS:
                if Confirm.ask("Reset network stack? (Requires restart)"):
                    network_optimizer.reset_network_stack()
            console.print("[green]✓ Network optimization complete[/green]")
        
        elif choice == "3":
            # Diagnostic report
            console.print("\n[cyan]Generating diagnostic report...[/cyan]")
            report = network_optimizer.generate_diagnostic_report()
            console.print("\n" + report)
            
            # Save to file
            report_file = os.path.join(os.path.expanduser("~"), "Desktop", "Antigravity-Network-Diagnostic.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            console.print(f"\n[green]✓ Report saved to: {report_file}[/green]")
        
        elif choice == "4":
            # Full repair
            console.print("\n[cyan]Running full login repair...[/cyan]")
            
            # Clean browsers
            browsers = browser_helper.detect_installed_browsers()
            for b in browsers:
                stats = browser_helper.clean_browser_completely(b)
                console.print(f"[green]✓ {b}: {stats['cookies']} cookies cleaned[/green]")
            
            # Optimize network
            network_optimizer.clear_dns_cache()
            console.print("[green]✓ DNS cache cleared[/green]")
            
            # Diagnostic
            console.print("\n[cyan]Running diagnostics...[/cyan]")
            connectivity = network_optimizer.test_google_connectivity()
            console.print(f"[green]✓ Google connectivity: {connectivity['overall_status']}[/green]")
            
            console.print("\n[bold green]✓ Full login repair complete![/bold green]")
        
        if choice != "0":
            if not Confirm.ask("\nContinue in Browser Helper?"):
                break


# --- Session Manager Submenu ---

def session_manager_menu(session_manager, browser_helper, logger):
    """Session Manager submenu"""
    while True:
        console.print("\n" + "="*70)
        console.print("[bold green]SESSION MANAGER | مدیریت نشست‌ها[/bold green]")
        console.print("="*70)
        console.print("\n1. [cyan]Backup Current Session[/cyan]")
        console.print("   [dim]پشتیبان‌گیری از Session فعلی[/dim]")
        console.print("\n2. [yellow]Restore Saved Session[/yellow]")
        console.print("   [dim]بازیابی Session ذخیره‌شده[/dim]")
        console.print("\n3. [magenta]List All Saved Sessions[/magenta]")
        console.print("   [dim]لیست تمام Session های ذخیره‌شده[/dim]")
        console.print("\n4. [red]Delete Old Sessions[/red]")
        console.print("   [dim]حذف Session های قدیمی[/dim]")
        console.print("\n0. [dim]Back to Main Menu[/dim]")
        
        choice = Prompt.ask("\nEnter choice", choices=["0", "1", "2", "3", "4"], default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            # Backup session
            browsers = browser_helper.detect_installed_browsers()
            if not browsers:
                console.print("[red]No supported browsers found.[/red]")
                continue
            
            console.print(f"\n[cyan]Found browsers: {', '.join(browsers)}[/cyan]")
            browser = Prompt.ask("Select browser", choices=browsers)
            
            profiles = browser_helper.get_browser_profiles(browser)
            if not profiles:
                console.print("[red]No profiles found.[/red]")
                continue
            
            profile_names = [p[0] for p in profiles]
            profile_name = Prompt.ask("Select profile", choices=profile_names, default=profile_names[0])
            profile_path = next(p[1] for p in profiles if p[0] == profile_name)
            
            session_name = Prompt.ask("Session name (optional)", default="")
            if not session_name:
                session_name = None
            
            if session_manager.backup_session(browser, profile_path, session_name):
                console.print("[green]✓ Session backed up successfully![/green]")
            else:
                console.print("[red]✗ Session backup failed.[/red]")
        
        elif choice == "2":
            # Restore session
            sessions = session_manager.list_saved_sessions()
            if not sessions:
                console.print("[red]No saved sessions found.[/red]")
                continue
            
            console.print("\n[cyan]Saved sessions:[/cyan]")
            for i, s in enumerate(sessions, 1):
                status = "[red](expired)[/red]" if s.get('expired') else "[green](valid)[/green]"
                console.print(f"{i}. {s['name']} - {s['browser']} - {s['cookie_count']} cookies {status}")
            
            session_idx = int(Prompt.ask("Select session number", choices=[str(i) for i in range(1, len(sessions)+1)]))
            selected_session = sessions[session_idx - 1]
            
            # Get browser and profile
            browsers = browser_helper.detect_installed_browsers()
            browser = Prompt.ask("Select browser", choices=browsers, default=selected_session['browser'])
            
            profiles = browser_helper.get_browser_profiles(browser)
            profile_names = [p[0] for p in profiles]
            profile_name = Prompt.ask("Select profile", choices=profile_names, default=profile_names[0])
            profile_path = next(p[1] for p in profiles if p[0] == profile_name)
            
            if session_manager.restore_session(selected_session['name'], browser, profile_path):
                console.print("[green]✓ Session restored successfully![/green]")
            else:
                console.print("[red]✗ Session restore failed.[/red]")
        
        elif choice == "3":
            # List sessions
            sessions = session_manager.list_saved_sessions()
            if not sessions:
                console.print("[yellow]No saved sessions found.[/yellow]")
                continue
            
            table = Table(title="Saved Sessions")
            table.add_column("Name", style="cyan")
            table.add_column("Browser", style="magenta")
            table.add_column("Backup Time", style="yellow")
            table.add_column("Cookies", justify="right", style="green")
            table.add_column("Status", style="white")
            
            for s in sessions:
                status = "[red]Expired[/red]" if s.get('expired') else "[green]Valid[/green]"
                table.add_row(
                    s['name'],
                    s['browser'],
                    s['backup_time'],
                    str(s['cookie_count']),
                    status
                )
            
            console.print(table)
        
        elif choice == "4":
            # Delete old sessions
            if Confirm.ask("Delete all expired sessions?"):
                count = session_manager.delete_expired_sessions()
                console.print(f"[green]✓ Deleted {count} expired sessions[/green]")
        
        if choice != "0":
            if not Confirm.ask("\nContinue in Session Manager?"):
                break


# --- CLI Menu ---

def main():
    # Setup logging
    agent_logger = setup_agent_logging()
    agent_logger.info("=== Antigravity Cleaner Started ===")
    
    cleaner = Cleaner()
    
    # Initialize new helpers (if modules available)
    browser_helper = None
    network_optimizer = None
    session_manager = None
    
    if BrowserHelper and NetworkOptimizer and SessionManager:
        try:
            browser_helper = BrowserHelper(agent_logger, dry_run=cleaner.dry_run)
            network_optimizer = NetworkOptimizer(agent_logger, dry_run=cleaner.dry_run)
            session_storage = os.path.join(os.path.expanduser('~'), '.antigravity-cleaner', 'sessions')
            session_manager = SessionManager(session_storage, agent_logger, dry_run=cleaner.dry_run)
            agent_logger.info("Browser helper modules initialized successfully")
        except Exception as e:
            agent_logger.error(f"Failed to initialize browser helper modules: {e}")
            console.print(f"[yellow]Warning: Browser helper features unavailable: {e}[/yellow]")
    
    # Check args
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--dry-run":
            cleaner.dry_run = True
            console.print(Panel.fit("DRY RUN MODE ENABLED", style="bold yellow"))
            # Update helpers dry_run mode
            if browser_helper:
                browser_helper.dry_run = True
            if network_optimizer:
                network_optimizer.dry_run = True
            if session_manager:
                session_manager.dry_run = True
        elif arg == "--auto":
            cleaner.run_clean(deep=True)
            cleaner.run_network_reset()
            sys.exit(0)

    # Header
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(f"[bold cyan]ANTIGRAVITY CLEANER[/bold cyan] v{platform.python_version()}")
    grid.add_row(f"[dim]Running on {CURRENT_OS}[/dim]")
    grid.add_row(f"[dim]Log: {LOG_FILE}[/dim]")
    console.print(Panel(grid, style="blue", border_style="blue"))

    while True:
        console.print("\n[bold white]Select an Option:[/bold white]")
        console.print("1. [green]Quick Clean[/green] (Standard paths)")
        console.print("2. [yellow]Deep Clean[/yellow] (Aggressive scan + Temp)")
        console.print("3. [magenta]Network Reset[/magenta] (Fix connection issues)")
        console.print("4. [cyan]Full Repair[/cyan] (Deep Clean + Network Reset)")
        console.print("5. [dim]Toggle Dry Run[/dim] " + (f"(Currently: [bold red]ON[/bold red])" if cleaner.dry_run else "(Currently: OFF)"))
        
        # New options (if modules available)
        if browser_helper and network_optimizer:
            console.print("6. [blue]Browser Login Helper[/blue] (Clean browser traces)")
        if session_manager:
            console.print("7. [green]Session Manager[/green] (Backup/Restore sessions)")

        # Shell config cleanup (available on all platforms)
        if IS_WINDOWS:
            console.print("8. [yellow]Shell Config Cleanup[/yellow] (PowerShell profiles + Registry PATH)")
        else:
            console.print("8. [yellow]Shell Config Cleanup[/yellow] (Clean .zshrc, .bashrc, etc.)")

        console.print("0. Exit")

        choices = ["0", "1", "2", "3", "4", "5"]
        if browser_helper and network_optimizer:
            choices.append("6")
        if session_manager:
            choices.append("7")
        choices.append("8")  # Shell config cleanup available on all platforms
        
        choice = Prompt.ask("Enter choice", choices=choices, default="0")

        if choice == "0":
            agent_logger.info("=== Antigravity Cleaner Exited ===")
            sys.exit(0)
        elif choice == "1":
            cleaner.run_clean(deep=False)
        elif choice == "2":
            cleaner.run_clean(deep=True)
        elif choice == "3":
            cleaner.run_network_reset()
        elif choice == "4":
            cleaner.run_clean(deep=True)
            cleaner.run_network_reset()
        elif choice == "5":
            cleaner.dry_run = not cleaner.dry_run
            # Update helpers dry_run mode
            if browser_helper:
                browser_helper.dry_run = cleaner.dry_run
            if network_optimizer:
                network_optimizer.dry_run = cleaner.dry_run
            if session_manager:
                session_manager.dry_run = cleaner.dry_run
            status = "[bold red]ON[/bold red]" if cleaner.dry_run else "OFF"
            console.print(f"Dry Run is now {status}")
        elif choice == "6" and browser_helper and network_optimizer:
            browser_login_helper_menu(browser_helper, network_optimizer, agent_logger)
        elif choice == "7" and session_manager:
            session_manager_menu(session_manager, browser_helper, agent_logger)
        elif choice == "8":
            cleaner.run_shell_config_cleanup()

        if choice != "5":
            if not Confirm.ask("Run another task?"):
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Cancelled by user.[/red]")
        sys.exit(0)
