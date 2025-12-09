import os
import sys
import platform
import shutil
import subprocess
import time
import glob
from datetime import datetime

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
                os.path.join(home, "Library", "Application Support", "Antigravity"),
                os.path.join(home, "Library", "Caches", "Antigravity"),
                os.path.join(home, "Library", "Preferences", "com.antigravity.plist"), # Hypothetical
                os.path.join(home, "Library", "Saved Application State", "com.antigravity.savedState"),
                "/Applications/Antigravity.app"
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


# --- CLI Menu ---

def main():
    cleaner = Cleaner()
    
    # Check args
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--dry-run":
            cleaner.dry_run = True
            console.print(Panel.fit("DRY RUN MODE ENABLED", style="bold yellow"))
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
        console.print("0. Exit")

        choice = Prompt.ask("Enter choice", choices=["0", "1", "2", "3", "4", "5"], default="0")

        if choice == "0":
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
            status = "[bold red]ON[/bold red]" if cleaner.dry_run else "OFF"
            console.print(f"Dry Run is now {status}")

        if choice != "5":
            if not Confirm.ask("Run another task?"):
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Cancelled by user.[/red]")
        sys.exit(0)
