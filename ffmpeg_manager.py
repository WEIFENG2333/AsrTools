#!/usr/bin/env python3
"""
FFmpeg 管理器 - 自动检测、下载和管理 ffmpeg
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path
from typing import Optional, Callable


class FFmpegManager:
    """FFmpeg 管理器"""

    # 下载源配置 - 使用 BtbN/FFmpeg-Builds
    FFMPEG_DOWNLOADS = {
        'Windows': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.1-latest-win64-gpl-6.1.zip',
            'binary': 'ffmpeg.exe',
            'inner_path': 'bin/ffmpeg.exe'
        },
        'Linux': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.1-latest-linux64-gpl-6.1.tar.xz',
            'binary': 'ffmpeg',
            'inner_path': 'bin/ffmpeg'
        },
        'Darwin': {
            'url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.1-latest-macos64-gpl-6.1.tar.xz',
            'binary': 'ffmpeg',
            'inner_path': 'bin/ffmpeg'
        }
    }

    def __init__(self):
        self._ffmpeg_path: Optional[str] = None
        self._checked = False

    def get_app_directory(self) -> Path:
        """获取程序所在目录（兼容开发和打包环境）"""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent

    def _is_executable(self, path: str) -> bool:
        """检查文件是否是可执行的 ffmpeg"""
        try:
            result = subprocess.run(
                [path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and 'ffmpeg version' in result.stdout
        except (subprocess.TimeoutExpired, Exception):
            return False

    def _find_in_path(self) -> Optional[str]:
        """在系统 PATH 中查找 ffmpeg"""
        system = platform.system()
        binary_name = 'ffmpeg.exe' if system == 'Windows' else 'ffmpeg'

        for path_dir in os.environ.get('PATH', '').split(os.pathsep):
            path_dir = path_dir.strip()
            if not path_dir:
                continue
            ffmpeg_path = os.path.join(path_dir, binary_name)
            if os.path.isfile(ffmpeg_path) and self._is_executable(ffmpeg_path):
                return ffmpeg_path
        return None

    def _find_in_app_dir(self) -> Optional[str]:
        """在程序目录中查找 ffmpeg"""
        app_dir = self.get_app_directory()
        system = platform.system()
        binary_name = 'ffmpeg.exe' if system == 'Windows' else 'ffmpeg'

        # 检查几个可能的位置
        possible_paths = [
            app_dir / binary_name,
            app_dir / '_internal' / binary_name,  # PyInstaller one-dir
        ]

        for path in possible_paths:
            if path.is_file() and self._is_executable(str(path)):
                return str(path)
        return None

    def find_ffmpeg(self) -> Optional[str]:
        """
        查找可用的 ffmpeg（按优先级）

        优先级：
        1. 程序目录（或 _internal 子目录）
        2. 系统 PATH
        """
        # 先检查程序目录
        ffmpeg_path = self._find_in_app_dir()
        if ffmpeg_path:
            self._ffmpeg_path = ffmpeg_path
            return ffmpeg_path

        # 再检查系统 PATH
        ffmpeg_path = self._find_in_path()
        if ffmpeg_path:
            self._ffmpeg_path = ffmpeg_path
            return ffmpeg_path

        return None

    def get_ffmpeg_path(self) -> Optional[str]:
        """获取 ffmpeg 路径，如果未检测过则先检测"""
        if not self._checked:
            self.find_ffmpeg()
            self._checked = True
        return self._ffmpeg_path

    def is_ffmpeg_available(self) -> bool:
        """检查 ffmpeg 是否可用"""
        return self.get_ffmpeg_path() is not None

    def download_ffmpeg(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        下载并安装 ffmpeg

        Args:
            progress_callback: 进度回调 (0-100)
            status_callback: 状态消息回调

        Returns:
            bool: 是否成功
        """
        import requests
        import tempfile
        import zipfile
        import tarfile

        system = platform.system()
        if system not in self.FFMPEG_DOWNLOADS:
            if status_callback:
                status_callback(f"不支持的操作系统: {system}")
            return False

        config = self.FFMPEG_DOWNLOADS[system]
        url = config['url']
        binary_name = config['binary']
        inner_path = config['inner_path']

        app_dir = self.get_app_directory()
        dest_path = app_dir / binary_name

        try:
            if status_callback:
                status_callback("正在连接下载服务器...")

            # 下载
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # 创建临时文件
            suffix = '.zip' if system == 'Windows' else '.tar.xz'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                temp_path = Path(f.name)

            try:
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                percent = min(100, int(downloaded * 100 / total_size))
                                progress_callback(percent)

                if status_callback:
                    status_callback("正在解压...")

                # 解压
                if system == 'Windows':
                    with zipfile.ZipFile(temp_path, 'r') as zf:
                        for info in zf.infolist():
                            if info.filename.replace('\\', '/').endswith(inner_path):
                                info.filename = binary_name
                                zf.extract(info, app_dir)
                                break
                else:
                    with tarfile.open(temp_path, 'r:*') as tf:
                        for member in tf.getmembers():
                            if member.name.endswith(inner_path) and member.isfile():
                                member.name = binary_name
                                tf.extract(member, app_dir)
                                # 设置执行权限
                                os.chmod(dest_path, 0o755)
                                break

                # 验证
                if not self._is_executable(str(dest_path)):
                    if status_callback:
                        status_callback("验证 ffmpeg 失败")
                    return False

                self._ffmpeg_path = str(dest_path)
                self._checked = True

                if status_callback:
                    status_callback("下载完成！")

                return True

            finally:
                # 清理临时文件
                try:
                    temp_path.unlink()
                except:
                    pass

        except requests.RequestException as e:
            if status_callback:
                status_callback(f"下载失败: {str(e)}")
            logging.error(f"FFmpeg download error: {e}")
            return False
        except Exception as e:
            if status_callback:
                status_callback(f"处理失败: {str(e)}")
            logging.error(f"FFmpeg extraction error: {e}")
            return False


# 全局实例
_ffmpeg_manager: Optional[FFmpegManager] = None


def get_ffmpeg_manager() -> FFmpegManager:
    """获取全局 FFmpegManager 实例"""
    global _ffmpeg_manager
    if _ffmpeg_manager is None:
        _ffmpeg_manager = FFmpegManager()
    return _ffmpeg_manager


def get_ffmpeg_path() -> Optional[str]:
    """便捷函数：获取 ffmpeg 路径"""
    return get_ffmpeg_manager().get_ffmpeg_path()


def is_ffmpeg_available() -> bool:
    """便捷函数：检查 ffmpeg 是否可用"""
    return get_ffmpeg_manager().is_ffmpeg_available()
