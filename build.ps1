# 在 Windows PowerShell 中运行：  .\build.ps1
# 默认产物： release\TodoApp\TodoApp.exe （文件夹版，推荐，启动不依赖临时目录）
# 可选单文件：.\build.ps1 -OneFile  ->  release\TodoApp.exe （注意：受限环境可能因临时目录不可写而报错）

param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pyLibs = Join-Path $PSScriptRoot ".build\pylibs"
$hasPyInstaller = Test-Path (Join-Path $pyLibs "PyInstaller")
$iconPath = Join-Path $PSScriptRoot "assets\app.ico"

if (-not $hasPyInstaller) {
    Write-Host "正在获取 PyInstaller 到 .build\pylibs ..."
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
New-Item -ItemType Directory -Force $env:TMP, ".build\work", "release" | Out-Null

if ($OneFile) {
    Write-Host "开始打包（单文件）..."
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name TodoApp `
        --icon "$iconPath" --distpath release --workpath ".build\work" --specpath ".build" app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller 打包失败。" }
    Write-Host "`n构建完成： $PSScriptRoot\release\TodoApp.exe" -ForegroundColor Green
} else {
    Write-Host "开始打包（文件夹版）..."
    python -m PyInstaller --noconfirm --clean --onedir --windowed --name TodoApp `
        --icon "$iconPath" --distpath release --workpath ".build\work" --specpath ".build" app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller 打包失败。" }
    Write-Host "`n构建完成： $PSScriptRoot\release\TodoApp\TodoApp.exe" -ForegroundColor Green
    Write-Host "提示：分发时请连同同目录的 _internal 文件夹一起复制/压缩。" -ForegroundColor Yellow
}
