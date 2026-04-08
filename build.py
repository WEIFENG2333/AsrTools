#!/usr/bin/env python3
"""
ASRTools 构建脚本
同时构建 GUI 和 CLI 版本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def run_cmd(cmd, cwd=None):
    """运行命令并返回输出"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def clean_build():
    """清理之前的构建文件"""
    print("Cleaning previous build files...")
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)


def build_gui():
    """构建 GUI 版本"""
    print("\nBuilding GUI version...")

    hidden_imports = [
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'qfluentwidgets',
        'requests',
        'urllib3',
        'chardet',
        'idna',
        'certifi',
        '_ssl',
        'ssl',
        '_hashlib',
        '_socket',
        'http.client',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        '_ctypes',
    ]

    exclude_modules = [
        'torch', 'torchvision', 'torchaudio',
        'pandas', 'scipy', 'yaml',
        'setuptools', 'pywin32', 'Pythonwin',
        'markupsafe', 'PIL', 'dateutil', 'pytz', 'google',
    ]

    cmd = [
        'pyinstaller',
        '--onedir',
        '--windowed',
        '--noconsole',
        '--strip',
        '--name', 'asr_gui',
    ]

    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])

    for mod in exclude_modules:
        cmd.extend(['--exclude-module', mod])

    cmd.append('asr_gui.py')

    return run_cmd(' '.join(cmd))


def build_cli(onefile=False):
    """构建 CLI 版本

    Args:
        onefile: 如果为 True，使用 --onefile 模式打包成单个 exe
    """
    mode = "onefile" if onefile else "onedir"
    print(f"\nBuilding CLI version ({mode})...")

    hidden_imports = [
        'requests',
        'urllib3',
        'chardet',
        'idna',
        'certifi',
        '_ssl',
        'ssl',
        '_hashlib',
        '_socket',
        'http.client',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        '_ctypes',
    ]

    exclude_modules = [
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'qfluentwidgets',
        'torch', 'torchvision', 'torchaudio',
        'pandas', 'scipy', 'yaml',
        'setuptools', 'pywin32', 'Pythonwin',
        'markupsafe', 'PIL', 'dateutil', 'pytz', 'google',
    ]

    name = 'asr_cli' if not onefile else 'asr_cli_single'

    cmd = [
        'pyinstaller',
        '--onefile' if onefile else '--onedir',
        '--console',
        '--strip',
        '--name', name,
    ]

    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])

    for mod in exclude_modules:
        cmd.extend(['--exclude-module', mod])

    cmd.append('cli.py')

    return run_cmd(' '.join(cmd))


def copy_ffmpeg():
    """复制 ffmpeg.exe 到构建目录"""
    print("\nCopying ffmpeg...")
    ffmpeg_source = Path('dist') / 'asr_gui' / 'ffmpeg.exe'

    # 如果源目录没有，尝试从项目根目录找
    if not ffmpeg_source.exists():
        ffmpeg_source = Path('ffmpeg.exe')

    if ffmpeg_source.exists():
        # 复制到 GUI 目录
        gui_dest = Path('dist') / 'asr_gui' / 'ffmpeg.exe'
        if ffmpeg_source != gui_dest:
            shutil.copy2(ffmpeg_source, gui_dest)
            print(f"Copied ffmpeg to {gui_dest}")

        # 复制到 CLI 目录
        cli_dest = Path('dist') / 'asr_cli' / 'ffmpeg.exe'
        shutil.copy2(ffmpeg_source, cli_dest)
        print(f"Copied ffmpeg to {cli_dest}")
    else:
        print("Warning: ffmpeg.exe not found")


def copy_ssl_dlls():
    """在 Windows 上复制 SSL DLLs"""
    if sys.platform != 'win32':
        return

    print("\nCopying SSL DLLs...")
    python_dir = Path(sys.executable).parent

    # 尝试从不同位置找到 DLLs
    dll_names = ['libcrypto-3.dll', 'libssl-3.dll']
    search_paths = [
        python_dir / 'DLLs',
        python_dir,
        Path(os.environ.get('SystemRoot', '')) / 'System32',
    ]

    gui_internal = Path('dist') / 'asr_gui' / '_internal'
    cli_internal = Path('dist') / 'asr_cli' / '_internal'

    for dll_name in dll_names:
        found = False
        for search_path in search_paths:
            dll_path = search_path / dll_name
            if dll_path.exists():
                # 复制到 GUI
                if gui_internal.exists():
                    shutil.copy2(dll_path, gui_internal / dll_name)
                    print(f"Copied {dll_name} to GUI _internal")
                # 复制到 CLI
                if cli_internal.exists():
                    shutil.copy2(dll_path, cli_internal / dll_name)
                    print(f"Copied {dll_name} to CLI _internal")
                found = True
                break
        if not found:
            print(f"Warning: {dll_name} not found")


def main():
    """主构建函数"""
    import argparse

    parser = argparse.ArgumentParser(description='ASRTools Build Script')
    parser.add_argument('--no-gui', action='store_true', help='Skip GUI build')
    parser.add_argument('--no-cli', action='store_true', help='Skip CLI (onedir) build')
    parser.add_argument('--cli-single', action='store_true', help='Build CLI single-file version')
    parser.add_argument('--no-clean', action='store_true', help='Skip cleaning build files')
    args = parser.parse_args()

    print("=" * 60)
    print("ASRTools Build Script")
    print("=" * 60)

    # 检查 pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        if not run_cmd('pip install pyinstaller'):
            print("Failed to install PyInstaller")
            return 1

    # 清理
    if not args.no_clean:
        clean_build()

    # 构建 GUI
    if not args.no_gui:
        if not build_gui():
            print("GUI build failed!")
            return 1

    # 构建 CLI (onedir)
    if not args.no_cli:
        if not build_cli(onefile=False):
            print("CLI build failed!")
            return 1

    # 构建 CLI (single file)
    if args.cli_single:
        if not build_cli(onefile=True):
            print("CLI single-file build failed!")
            return 1

    # 复制额外文件
    copy_ffmpeg()
    copy_ssl_dlls()

    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    if not args.no_gui:
        print(f"GUI: dist/asr_gui/")
    if not args.no_cli:
        print(f"CLI: dist/asr_cli/")
    if args.cli_single:
        print(f"CLI single-file: dist/asr_cli_single.exe")

    return 0


if __name__ == '__main__':
    sys.exit(main())
