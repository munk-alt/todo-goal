# Run in Windows PowerShell:  .\build.ps1
# Default output: release\TodoApp\TodoApp.exe (folder build, recommended)
# Optional single file: .\build.ps1 -OneFile -> release\TodoApp.exe
# NOTE: this file is ASCII-only on purpose, so Windows PowerShell 5.1 parses it correctly.

param(
    [switch]$OneFile,
    [string]$Out = "release"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pyLibs = Join-Path $PSScriptRoot ".build\pylibs"
$hasPyInstaller = Test-Path (Join-Path $pyLibs "PyInstaller")
$iconPath = Join-Path $PSScriptRoot "assets\app.ico"

if (-not $hasPyInstaller) {
    Write-Host "Fetching PyInstaller into .build\pylibs ..."
    python -m pip install --no-warn-script-location --no-cache-dir --target $pyLibs "pyinstaller==6.22.3" 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pip failed; falling back to scripts\_fetch_wheels.py"
        python (Join-Path $PSScriptRoot "scripts\_fetch_wheels.py")
        if ($LASTEXITCODE -ne 0) { throw "Cannot obtain PyInstaller." }
    }
}

$env:PYTHONPATH = $pyLibs
$env:TMP = Join-Path $PSScriptRoot ".build\tmp"
$env:TEMP = $env:TMP
New-Item -ItemType Directory -Force $env:TMP, ".build\work", $Out | Out-Null

if ($OneFile) {
    Write-Host "Building single-file ..."
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name TodoApp `
        --icon "$iconPath" --distpath "$Out" --workpath ".build\work" --specpath ".build" app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
    Write-Host "`nDone: $PSScriptRoot\$Out\TodoApp.exe" -ForegroundColor Green
} else {
    Write-Host "Building folder version ..."
    python -m PyInstaller --noconfirm --clean --onedir --windowed --name TodoApp `
        --icon "$iconPath" --distpath "$Out" --workpath ".build\work" --specpath ".build" app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
    Write-Host "`nDone: $PSScriptRoot\$Out\TodoApp\TodoApp.exe" -ForegroundColor Green
    Write-Host "Keep the _internal folder next to the exe when distributing." -ForegroundColor Yellow
}
