# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Attempting to install or use fallback..." -ForegroundColor Yellow
    # This is a complex topic for a one-liner. 
    # For now, we will just download the repo and try to run the bat file which handles checks.
}

$repoUrl = "https://github.com/tawanamohammadi/tawana-antigravity-cleaner/archive/refs/heads/main.zip"
$zipPath = "$env:TEMP\antigravity-cleaner.zip"
$destPath = "$env:TEMP\antigravity-cleaner-install"

Write-Host "Downloading Antigravity Cleaner..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $repoUrl -OutFile $zipPath

if (Test-Path $destPath) { Remove-Item -Recurse -Force $destPath }
Expand-Archive -Path $zipPath -DestinationPath $destPath

$innerFolder = Get-ChildItem $destPath | Select-Object -First 1
$runBat = "$($innerFolder.FullName)\run_windows.bat"

Write-Host "Starting Cleaner..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/c $runBat" -Wait

# Cleanup
Remove-Item -Path $zipPath -Force
# We keep the extracted folder so the bat file can run, but usually we might want to clean it up after.
# Since run_windows.bat pauses, we can't easily auto-delete here without a wrapper. 
# We'll leave it in temp.
