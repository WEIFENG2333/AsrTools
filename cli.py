#!/usr/bin/env python3
"""
ASRTools 命令行工具 v1.3.0

使用方法:
    python cli.py [输入路径] [选项]

如果不指定输入路径，默认处理当前目录及其子目录下的所有音视频文件。

选项:
    -e, --engine ENGINE    ASR 引擎 (BcutASR, JianYingASR, KuaiShouASR, B, J, K)
                           默认: JianYingASR (J)
    -f, --format FORMAT    输出格式 (srt, ass, txt)
                           默认: txt
    -o, --output FILE      输出文件路径 (仅处理单个文件时使用)
    -r, --recursive        递归处理子目录 (默认开启)
    --no-recursive         不递归处理子目录
    -c, --cache            使用缓存 (可选)
    -h, --help             显示帮助信息

示例:
    # 处理当前目录及其子目录下的所有文件（默认）
    python cli.py

    # 处理指定目录
    python cli.py ./videos

    # 处理单个文件
    python cli.py video.mp4

    # 指定引擎和格式
    python cli.py -e BcutASR -f srt

    # 使用缓存
    python cli.py -c
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 导入 ASR 引擎
from bk_asr import BcutASR, JianYingASR, KuaiShouASR

# 导入 FFmpeg 管理器
from ffmpeg_manager import get_ffmpeg_manager, get_ffmpeg_path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 支持的音视频格式
SUPPORTED_FORMATS = [
    '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma',  # 音频
    '.mp4', '.avi', '.mov', '.ts', '.mkv', '.wmv', '.flv', '.webm', '.rmvb'  # 视频
]


def video2audio(input_file: str, output: str = "") -> bool:
    """使用ffmpeg将视频转换为音频"""
    import platform
    import subprocess

    ffmpeg_mgr = get_ffmpeg_manager()

    # 检查 ffmpeg
    if not ffmpeg_mgr.is_ffmpeg_available():
        logging.info("未找到 FFmpeg，尝试自动下载...")
        print("\n" + "=" * 60)
        print("FFmpeg 未找到")
        print("正在从 GitHub (BtbN/FFmpeg-Builds) 自动下载...")
        print("=" * 60 + "\n")

        def show_progress(p):
            print(f"\r下载进度: [{'#' * (p // 5)}{' ' * (20 - p // 5)}] {p:3d}%", end='', flush=True)

        def show_status(msg):
            print(f"\n{msg}")

        success = ffmpeg_mgr.download_ffmpeg(
            progress_callback=show_progress,
            status_callback=show_status
        )

        if not success:
            print("\n\n错误：FFmpeg 下载失败！")
            print("\n请手动下载 FFmpeg：")
            print("1. 访问 https://github.com/BtbN/FFmpeg-Builds/releases")
            print("2. 下载对应系统的 ffmpeg")
            print("3. 将 ffmpeg (或 ffmpeg.exe) 放置在程序目录或添加到 PATH\n")
            return False

        print("\nFFmpeg 下载成功！\n")

    # 创建output目录
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output = str(output)

    # 获取 ffmpeg 路径
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return False

    cmd = [
        ffmpeg_path,
        '-i', input_file,
        '-ac', '1',
        '-f', 'mp3',
        '-af', 'aresample=async=1',
        '-y',
        output
    ]

    # 构建 subprocess.run 的参数字典
    kwargs = {
        'capture_output': True,
        'check': True,
        'encoding': 'utf-8',
        'errors': 'replace'
    }

    # 在 Windows 上添加隐藏窗口的配置
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(cmd, **kwargs)

    if result.returncode == 0 and Path(output).is_file():
        return True
    else:
        return False


def get_engine_class(engine_name):
    """根据引擎名称获取引擎类"""
    engines = {
        'BcutASR': BcutASR,
        'JianYingASR': JianYingASR,
        'KuaiShouASR': KuaiShouASR,
        'bcut': BcutASR,
        'jianying': JianYingASR,
        'kuaishou': KuaiShouASR,
        'B': BcutASR,
        'J': JianYingASR,
        'K': KuaiShouASR,
    }
    return engines.get(engine_name, JianYingASR)


def find_media_files(directory: Path, recursive: bool = True):
    """递归查找目录下的所有音视频文件"""
    files = []
    if recursive:
        for ext in SUPPORTED_FORMATS:
            files.extend(directory.rglob(f"*{ext}"))
            files.extend(directory.rglob(f"*{ext.upper()}"))
    else:
        for ext in SUPPORTED_FORMATS:
            files.extend(directory.glob(f"*{ext}"))
            files.extend(directory.glob(f"*{ext.upper()}"))
    return sorted(set(files))


def process_single_file(
    input_path: Path,
    engine_name: str,
    output_format: str,
    output_path: Path = None,
    use_cache: bool = False
) -> bool:
    """处理单个音视频文件"""
    temp_audio = None
    try:
        # 确定输出路径
        if output_path:
            final_output_path = output_path
        else:
            final_output_path = input_path.with_suffix(f'.{output_format.lower()}')

        # 检查输出文件是否已存在
        if final_output_path.exists():
            logging.info(f"跳过已存在: {final_output_path}")
            return True

        # 检查文件类型，如果不是音频则转换
        audio_path = str(input_path)
        audio_exts = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma']

        if not any(input_path.suffix.lower() == ext for ext in audio_exts):
            logging.info(f"正在转换视频: {input_path.name}")
            temp_audio = str(input_path.with_suffix('.mp3'))
            if not video2audio(str(input_path), temp_audio):
                logging.error(f"音频转换失败: {input_path}")
                return False
            audio_path = temp_audio

        # 获取引擎类
        engine_class = get_engine_class(engine_name)
        logging.info(f"使用引擎: {engine_class.__name__} - 文件: {input_path.name}")

        # 初始化 ASR
        asr = engine_class(audio_path, use_cache=use_cache)

        # 运行识别
        result = asr.run()

        # 导出结果
        save_ext = output_format.lower()
        if save_ext == 'srt':
            result_text = result.to_srt()
        elif save_ext == 'ass':
            result_text = result.to_ass()
        elif save_ext == 'txt':
            result_text = result.to_txt()
        else:
            result_text = result.to_txt()

        # 保存文件
        with open(final_output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)

        logging.info(f"处理完成: {final_output_path}")
        return True

    except Exception as e:
        logging.error(f"处理出错 {input_path}: {str(e)}")
        return False
    finally:
        # 清理临时音频文件
        if temp_audio and Path(temp_audio).exists():
            try:
                Path(temp_audio).unlink()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description='ASRTools 命令行工具 v1.3.0 - 音视频转文字',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理当前目录及其子目录下的所有文件（默认）
  %(prog)s

  # 处理指定目录
  %(prog)s ./videos

  # 处理单个文件
  %(prog)s video.mp4

  # 指定引擎和格式
  %(prog)s -e B -f srt

  # 使用缓存
  %(prog)s -c
        """
    )

    parser.add_argument(
        'input',
        nargs='?',
        default='.',
        help='输入文件或目录路径 (默认: 当前目录)'
    )
    parser.add_argument(
        '-e', '--engine',
        default='J',
        help='ASR 引擎 (BcutASR, JianYingASR, KuaiShouASR, B, J, K) 默认: J (JianYingASR)'
    )
    parser.add_argument(
        '-f', '--format',
        default='txt',
        choices=['srt', 'ass', 'txt'],
        help='输出格式 (srt, ass, txt) 默认: txt'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径 (仅处理单个文件时使用)'
    )

    # 递归选项
    recursive_group = parser.add_mutually_exclusive_group()
    recursive_group.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=True,
        help='递归处理子目录 (默认开启)'
    )
    recursive_group.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='不递归处理子目录'
    )

    parser.add_argument(
        '-c', '--cache',
        action='store_true',
        help='使用缓存 (可选)'
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    # 检查输入是否存在
    if not input_path.exists():
        logging.error(f"错误: 路径不存在: {args.input}")
        sys.exit(1)

    # 处理单个文件
    if input_path.is_file():
        success = process_single_file(
            input_path=input_path,
            engine_name=args.engine,
            output_format=args.format,
            output_path=Path(args.output) if args.output else None,
            use_cache=args.cache
        )
        sys.exit(0 if success else 1)

    # 处理目录
    elif input_path.is_dir():
        logging.info(f"扫描目录: {input_path}")
        if args.recursive:
            logging.info("(包含子目录)")

        media_files = find_media_files(input_path, recursive=args.recursive)

        if not media_files:
            logging.warning("未找到音视频文件")
            sys.exit(0)

        logging.info(f"找到 {len(media_files)} 个文件")

        # 处理所有文件
        success_count = 0
        for file_path in media_files:
            if process_single_file(
                input_path=file_path,
                engine_name=args.engine,
                output_format=args.format,
                use_cache=args.cache
            ):
                success_count += 1

        logging.info(f"完成: {success_count}/{len(media_files)} 成功")
        sys.exit(0 if success_count == len(media_files) else 1)

    else:
        logging.error(f"错误: 不是文件或目录: {args.input}")
        sys.exit(1)


if __name__ == '__main__':
    main()
