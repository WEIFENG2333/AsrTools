# AsrTools

音视频转文字工具，支持多种 ASR 引擎。

## 功能

- **GUI 界面**：图形化操作，支持批量处理
- **命令行工具**：脚本化批量处理
- **多引擎支持**：必剪、剪映、快手 ASR 接口
- **多格式输出**：SRT、ASS、TXT 字幕格式
- **视频支持**：自动转换视频为音频（FFmpeg 自动下载）
- **多线程处理**：批量文件并行处理
- **目录递归扫描**：自动查找处理目录下所有音视频文件

## 快速开始

### 使用预构建版本

从 [Releases](https://github.com/ZedeX/AsrTools/releases) 下载对应系统的版本。

### 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 GUI
python asr_gui.py

# 使用命令行（默认处理当前目录）
python cli.py
```

## 命令行工具 (CLI) 使用说明

### 默认行为

不指定输入路径时，默认处理**当前目录及其子目录**下的所有音视频文件：
- 默认引擎：JianYingASR (J 接口)
- 默认输出格式：TXT
- 默认递归子目录：开启

### 用法

```
python cli.py [输入路径] [选项]
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `input` | - | 输入文件或目录路径 | 当前目录 `.` |
| `--engine` | `-e` | ASR 引擎 (BcutASR/JianYingASR/KuaiShouASR/B/J/K) | `J` |
| `--format` | `-f` | 输出格式 (srt/ass/txt) | `txt` |
| `--output` | `-o` | 输出文件路径（仅单个文件时使用） | - |
| `--recursive` | `-r` | 递归处理子目录 | 开启 |
| `--no-recursive` | - | 不递归处理子目录 | - |
| `--cache` | `-c` | 使用缓存 | 关闭 |
| `--help` | `-h` | 显示帮助信息 | - |

### 示例

```bash
# 处理当前目录及其子目录下的所有文件（最常用）
python cli.py

# 处理指定目录
python cli.py ./videos

# 处理单个文件
python cli.py video.mp4

# 指定引擎和格式
python cli.py -e B -f srt

# 使用缓存
python cli.py -c

# 只处理当前目录，不递归子目录
python cli.py --no-recursive

# 完整示例
python cli.py ./media -e K -f ass -c
```

### 支持的文件格式

**音频**: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.wma`

**视频**: `.mp4`, `.avi`, `.mov`, `.ts`, `.mkv`, `.wmv`, `.flv`, `.webm`, `.rmvb`

## 项目结构

```
AsrTools/
├── asr_gui.py          # GUI 主程序
├── cli.py              # 命令行工具
├── build.py            # 自动化构建脚本
├── ffmpeg_manager.py   # FFmpeg 自动管理
├── bk_asr/             # ASR 引擎模块
│   ├── BcutASR.py
│   ├── JianYingASR.py
│   └── KuaiShouASR.py
├── asr_gui.spec        # PyInstaller GUI 配置
├── asr_cli.spec        # PyInstaller CLI 配置
└── .github/workflows/build.yml  # GitHub Actions 自动构建
```

## 构建

### 使用构建脚本（推荐）

项目提供了自动化构建脚本 `build.py`：

```bash
# 默认构建：GUI + CLI (目录版本)
python build.py

# 构建所有版本：GUI + CLI + CLI 单文件版本
python build.py --cli-single

# 仅构建 CLI 单文件版本（独立 exe，无依赖）
python build.py --no-gui --no-cli --cli-single

# 跳过清理，增量构建
python build.py --no-clean
```

构建脚本参数说明：

| 参数 | 说明 |
|------|------|
| `--no-gui` | 跳过 GUI 版本构建 |
| `--no-cli` | 跳过 CLI 目录版本构建 |
| `--cli-single` | 构建 CLI 单文件版本 |
| `--no-clean` | 跳过清理之前的构建文件 |

### 手动使用 PyInstaller

```bash
# GUI 版本
pyinstaller asr_gui.spec

# CLI 版本（目录版）
pyinstaller asr_cli.spec

# CLI 单文件版本
pyinstaller --onefile --console --strip --name asr_cli_single cli.py
```

### 构建产物

- **GUI 版本**: `dist/asr_gui/` (目录版，包含 `asr_gui.exe` 和 `_internal/` 依赖)
- **CLI 目录版**: `dist/asr_cli/` (目录版，包含 `asr_cli.exe` 和 `_internal/` 依赖)
- **CLI 单文件版**: `dist/asr_cli_single.exe` (单文件 exe，可独立运行，推荐用于分发)

## 版本发布流程

### v1.3.x 完整更新记录

#### v1.3.0 - FFmpeg 自动下载
- 新增 `ffmpeg_manager.py` 模块
- 自动检测系统 PATH 和程序目录中的 FFmpeg
- 从 GitHub (BtbN/FFmpeg-Builds) 自动下载 FFmpeg
- GUI 集成 FFmpeg 下载对话框
- 首次使用视频转换时提示自动下载
- FFMPEG 调用不弹出控制台窗口（Windows）

#### v1.3.1 - 增强 CLI 和 Node.js 24 修复
- 增强 CLI 工具：默认处理当前目录及其子目录
- 默认引擎：JianYingASR (J)
- 默认输出格式：TXT
- 添加 `--no-recursive` 选项
- 批量处理时自动跳过已存在文件
- 修复 Node.js 20 弃用警告：使用 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`
- 使用 Python 动态查找 SSL DLL 路径

#### v1.3.2 - 自动创建 Release
- GitHub Actions 支持 `v*` 标签推送触发
- 新增 `release` job，自动下载 artifacts 并创建 ZIP
- 使用 `softprops/action-gh-release` 自动创建 Release
- 自动生成 Release Notes

### 如何发布新版本

只需以下几步即可自动构建和发布：

```bash
# 1. 创建带注释的标签
git tag -a v1.x.x -m "Release v1.x.x - 版本说明"

# 2. 推送标签到 GitHub
git push origin v1.x.x
```

### GitHub Actions 自动流程

推送 `v*` 标签后，GitHub Actions 会自动执行：

1. **检测到标签推送**
   - 触发条件：`refs/tags/v*`

2. **构建阶段 (build job)**
   - 在 Windows、Ubuntu、macOS 三个平台上并行构建
   - 每个平台构建 GUI 和 CLI 两个版本
   - 上传 artifacts（共 6 个：3 平台 × 2 版本）

3. **发布阶段 (release job)**
   - 等待所有构建完成
   - 下载所有 artifacts
   - 打包成 ZIP 文件
   - 自动创建 GitHub Release
   - 上传所有 ZIP 文件
   - 自动生成 Release Notes

### 手动创建 Release（备选方案）

如果需要手动创建 Release：

1. 访问：https://github.com/ZedeX/AsrTools/releases/new
2. **Choose a tag**：选择已推送的标签（如 `v1.3.2`）
3. **Release title**：输入版本号（如 `v1.3.2`）
4. **Describe this release**：填写更新说明
5. 点击 **Publish release**

创建后，GitHub Actions 会自动将 artifacts 上传到该 Release。

## 许可证

MIT License
