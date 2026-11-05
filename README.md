# Todo · 便签

一个放在 Windows 桌面上的**便笺风**小工具：左边记待办，右边随手写便签。**无边框、半透明、可拖动/缩放/置顶**，支持浅黑 / 浅白两套主题，完全离线，数据存在本机。

![暗色主题](docs/sticky-dark.png) ![浅色主题](docs/sticky-light.png)

## 功能

- 🗒 **便笺式外观**：无系统标题栏、半透明背景、圆角观感，安静地待在桌面上
- 🎨 **浅黑 / 浅白一键切换**：点标题栏「亮/暗」切换主题
- 📌 **可拖动、可缩放、可置顶**：拖动标题栏移动，右下角 ◢ 缩放，点「顶」钉在最前
- ✅ **待办三栏填写**：每条待办分开填写「时间 / 地点 / 内容」
- ↕️ **手动排序**：拖动每行右侧的 `≡` 手柄即可调整顺序；也可右键「上移 / 下移」
- 🖊 **便签区**：下方一块文本区，随手记一段话，**自动保存**
- ⚙️ **状态记忆**：自动记住窗口位置、大小、主题、是否置顶
- 🔒 **完全离线**：SQLite 本地存储，无账号、无网络请求

## 界面

| 编辑待办 | 浅色主题 |
| --- | --- |
| ![对话框](docs/dialog-dark.png) | ![浅色](docs/sticky-light.png) |

## 快速开始

### 方式一：直接运行 exe（推荐，无需 Python）

- 单文件版：双击 `dist\TodoApp.exe`
- 若单文件版在个别加固环境报 `VCRUNTIME140.dll ... Permission denied`，改用**文件夹版** `dist_onedir\TodoApp\TodoApp.exe`（需保留同目录 `_internal`）。

### 方式二：用 Python 运行

```powershell
cd "D:\Agent Project\TODO"
python app.py
```

### 方式三：无控制台双击

双击 `TodoApp.pyw`。

## 使用说明

| 操作 | 方式 |
| --- | --- |
| 添加待办 | 待办区右上「＋ 添加」或 `Ctrl+N` |
| 编辑待办 | 双击某条待办；或右键「编辑」 |
| 勾选完成 | 点左侧 ☐ / ☑ |
| 调整顺序 | 拖动右侧 `≡` 手柄；或右键「上移 / 下移」 |
| 删除待办 | 右键「删除」（会二次确认） |
| 移动窗口 | 拖动标题栏 |
| 调整大小 | 拖右下角 ◢ |
| 置顶开关 | 标题栏「顶」（高亮表示已置顶） |
| 切换主题 | 标题栏「亮 / 暗」 |
| 写便签 | 在下方「便签」文本框输入，停止输入约 0.7 秒自动保存 |

## 数据与隐私

- 数据库：`%APPDATA%\TodoApp\todo.db`（SQLite，含 `todos` 与 `note` 两张表）
- 偏好设置：`%APPDATA%\TodoApp\settings.json`（窗口位置/大小、主题、置顶）
- 备份：复制 `%APPDATA%\TodoApp` 文件夹即可；若该目录不可写会自动回退到程序目录下 `data\`。

## 项目结构

```
TODO/
├─ app.py                    # 入口（含 DPI 适配）
├─ TodoApp.pyw               # 无控制台双击入口
├─ todo/
│  ├─ models.py              # Todo / Note 数据类
│  ├─ storage.py             # SQLite 仓储（todos 排序、note）
│  ├─ service.py             # 业务逻辑（校验/排序/移动/便签）
│  └─ ui/
│     ├─ theme.py            # 浅黑/浅白两套主题
│     ├─ widgets.py          # 可滚动容器、窗口拖动等
│     ├─ main_window.py      # 便笺主窗口
│     └─ todo_dialog.py      # 添加/编辑待办浮动框
├─ tests/test_service.py     # 单元测试
├─ scripts/                  # 冒烟测试 / 演示数据 / 离线取 wheel
├─ build.ps1                 # 打包脚本
├─ requirements-build.txt    # 仅打包依赖（PyInstaller）
├─ docs/                     # 截图
├─ dist/                     # 单文件 exe
└─ dist_onedir/              # 文件夹版 exe
```

## 开发与测试

运行应用本身**不需要任何第三方库**（仅 Python 标准库 + 自带 tkinter）。

```powershell
cd "D:\Agent Project\TODO"
python -m unittest discover -s tests -v   # 单元测试（15 项）
python scripts\smoke_ui.py                # 无值守 UI 冒烟测试
```

## 打包为 exe

```powershell
cd "D:\Agent Project\TODO"
.\build.ps1                       # 单文件版 -> dist\TodoApp.exe
```

文件夹版：

```powershell
python -m PyInstaller --noconfirm --clean --onedir --windowed --name TodoApp --distpath dist_onedir app.py
```

## 常见问题

- **单文件 exe 首次启动慢 / 被杀软误报**：单文件版启动时会先解压到临时目录；加入杀软白名单，或改用文件夹版。
- **`VCRUNTIME140.dll ... Permission denied`**：说明系统临时目录不可写（多见于受限/加固环境），改用文件夹版，或把 `TEMP` 指向可写目录。
- **窗口跑到屏幕外**：删除 `%APPDATA%\TodoApp\settings.json` 后重启即可恢复默认位置。
- **高分屏模糊**：程序启动时已开启 DPI 感知；若仍异常，可在系统兼容性里调整缩放。

## 仓库

- GitHub：<https://github.com/munk-alt/todo-goal.git>

## 版本

- v2.0.0 —— 改为便笺风：无边框半透明窗口、浅黑/浅白主题、待办（时间/地点/内容）与便签分栏、拖拽排序、自动保存。
- v1.0.0 —— 初版窗口化表格应用。
