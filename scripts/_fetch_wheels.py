"""开发辅助：绕过 pip，直接从 PyPI 下载 PyInstaller 及其依赖的 wheel。

用法： python scripts/_fetch_wheels.py
下载到 .build/wheels，并用 zipfile 解压到 .build/pylibs。
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHEEL_DIR = ROOT / ".build" / "wheels"
LIB_DIR = ROOT / ".build" / "pylibs"

PYINSTALLER_VERSION = "6.22.3"

_WHEEL_PRIORITY = [
    "py3-none-any.whl",
    "py3-none-win_amd64.whl",
    "cp313-cp313-win_amd64.whl",
    "cp313-abi3-win_amd64.whl",
    "cp313-none-win_amd64.whl",
]


def _context():
    try:
        import certifi  # noqa: F401
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def get_json(name: str) -> dict:
    url = f"https://pypi.org/pypi/{name}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "todo-build-fetch"})
    with urllib.request.urlopen(req, timeout=60, context=_context()) as resp:
        return json.load(resp)


def pick_wheel(files: list) -> dict | None:
    wheels = [f for f in files if f.get("packagetype") == "bdist_wheel"]
    for suffix in _WHEEL_PRIORITY:
        for f in wheels:
            if f["filename"].endswith(suffix):
                return f
    win = [f for f in wheels if "win_amd64" in f["filename"]]
    if win:
        return win[0]
    return wheels[0] if wheels else None


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "todo-build-fetch"})
    with urllib.request.urlopen(req, timeout=120, context=_context()) as resp:
        dest.write_bytes(resp.read())


def resolve_name(requirement: str) -> str | None:
    """从 requires_dist 条目里取出包名；若环境标记明显不适用则返回 None。"""
    req = requirement.strip()
    if ";" in req:
        _, marker = req.split(";", 1)
        marker = marker.strip().lower()
        # 跳过明显非 Windows 的标记
        if "sys_platform" in marker and "win32" not in marker:
            if "==" in marker and "linux" in marker or "darwin" in marker or "!= 'win32'" in marker:
                return None
        if "platform_system" in marker and "windows" not in marker:
            return None
    name = re.split(r"[\s<>=!~\[\(;]", req, maxsplit=1)[0]
    return name.strip() or None


def main() -> int:
    WHEEL_DIR.mkdir(parents=True, exist_ok=True)
    LIB_DIR.mkdir(parents=True, exist_ok=True)

    meta = get_json("pyinstaller")
    files = meta["releases"].get(PYINSTALLER_VERSION, [])
    chosen = pick_wheel(files)
    if not chosen:
        print(f"ERROR: 找不到 pyinstaller {PYINSTALLER_VERSION} 的 wheel")
        return 1
    to_download = [chosen]

    requires = meta["info"].get("requires_dist") or []
    print("requires_dist:", requires)
    for req in requires:
        name = resolve_name(req)
        if not name:
            continue
        try:
            dep_meta = get_json(name)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN 无法获取 {name}: {exc}")
            continue
        dep_files = dep_meta["releases"].get(dep_meta["info"]["version"], [])
        dep_wheel = pick_wheel(dep_files)
        if dep_wheel:
            to_download.append(dep_wheel)
        else:
            print(f"WARN {name} 无可用 wheel")

    for f in to_download:
        dest = WHEEL_DIR / f["filename"]
        if dest.exists():
            print("skip existing", dest.name)
            continue
        print("download", f["filename"])
        download(f["url"], dest)

    for whl in sorted(WHEEL_DIR.glob("*.whl")):
        print("extract", whl.name)
        with zipfile.ZipFile(whl) as zf:
            zf.extractall(LIB_DIR)

    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
