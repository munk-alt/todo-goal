# 在 Windows PowerShell 中运行：  .\build.ps1
# 产物： dist\TodoApp.exe （单文件、无控制台窗口）

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pyLibs = Join-Path $PSScriptRoot ".build\pylibs"
$hasPyInstaller = Test-Path (Join-Path $pyLibs "PyInstaller")

if (-not $hasPyInstaller) {
    Write-Host "正在安装 PyInstaller 到 .build\pylibs ..."
    python -m pip install --no-warn-script-location --no-cache-dir --target $pyLibs "pyinstaller==6.22.3" 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pip 安装失败，改用直接下载 wheel 的方式（scripts\_fetch_wheels.py）。"
        python (Join-Path $PSScriptRoot "scripts\_fetch_wheels.py")
        if ($LASTEXITCODE -ne 0) { throw "无法获取 PyInstaller。" }
    }
}

$env:PYTHONPATH = $pyLibs
$env:TMP = Join-Path $PSScriptRoot ".build\tmp"
$env:TEMP = $env:TMP
New-Item -ItemType Directory -Force $env:TMP, ".build\work", "dist" | Out-Null

Write-Host "开始打包 ..."
python -m PyInstaller --noconfirm --clean --onefile --windowed --name TodoApp `
    --distpath dist --workpath ".build\work" --specpath ".build" app.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 打包失败。" }

Write-Host ""
Write-Host "构建完成： $PSScriptRoot\dist\TodoApp.exe" -ForegroundColor Green
