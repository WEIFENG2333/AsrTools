import logging
import os
from pathlib import Path
import platform
import subprocess
import sys
import webbrowser

# FIX: 修复中文路径报错 https://github.com/WEIFENG2333/AsrTools/issues/18  设置QT_QPA_PLATFORM_PLUGIN_PATH
# 仅在非 PyInstaller 打包环境中设置此路径
if not getattr(sys, 'frozen', False):
    plugin_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')
    if os.path.exists(plugin_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PyQt5.QtCore import Qt, QRunnable, QThreadPool, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QSize, QThread, \
    pyqtSignal
from PyQt5.QtGui import QCursor, QColor, QFont
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QTableWidgetItem, QHeaderView, QSizePolicy, QTextEdit, QDialog, QProgressBar, QPushButton, QLabel, QMessageBox)
from qfluentwidgets import (ComboBox, PushButton, LineEdit, TableWidget, FluentIcon as FIF,
                            Action, RoundMenu, InfoBar, InfoBarPosition,
                            FluentWindow, BodyLabel, MessageBox)

from bk_asr.BcutASR import BcutASR
from bk_asr.JianYingASR import JianYingASR
from bk_asr.KuaiShouASR import KuaiShouASR

from ffmpeg_manager import get_ffmpeg_manager, FFmpegManager, get_ffmpeg_path

# 让 PyInstaller 检测到LOG属性
from qfluentwidgets import FluentIcon
# _ = FluentIcon.LOG  # 移除，因为 FluentIcon 没有 LOG 属性

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class WorkerSignals(QObject):
    finished = Signal(str, str)
    errno = Signal(str, str)


class ASRWorker(QRunnable):
    """ASR处理工作线程"""
    def __init__(self, file_path, asr_engine, export_format):
        super().__init__()
        self.file_path = file_path
        self.asr_engine = asr_engine
        self.export_format = export_format
        self.signals = WorkerSignals()

        self.audio_path = None

    @Slot()
    def run(self):
        try:
            use_cache = True

            # 检查文件类型,如果不是音频则转换
            logging.info("[+]正在进ffmpeg转换")
            audio_exts = ['.mp3', '.wav']
            if not any(self.file_path.lower().endswith(ext) for ext in audio_exts):
                temp_audio = self.file_path.rsplit(".", 1)[0] + ".mp3"
                if not video2audio(self.file_path, temp_audio):
                    raise Exception("音频转换失败，确保安装ffmpeg")
                self.audio_path = temp_audio
            else:
                self.audio_path = self.file_path

            # 根据选择的 ASR 引擎实例化相应的类
            if self.asr_engine == 'B 接口':
                asr = BcutASR(self.audio_path, use_cache=use_cache)
            elif self.asr_engine == 'J 接口':
                asr = JianYingASR(self.audio_path, use_cache=use_cache)
            elif self.asr_engine == 'K 接口':
                asr = KuaiShouASR(self.audio_path, use_cache=use_cache)
            elif self.asr_engine == 'Whisper':
                # from bk_asr.WhisperASR import WhisperASR
                # asr = WhisperASR(self.file_path, use_cache=use_cache)
                raise NotImplementedError("WhisperASR 暂未实现")
            else:
                raise ValueError(f"未知的 ASR 引擎: {self.asr_engine}")

            logging.info(f"开始处理文件: {self.file_path} 使用引擎: {self.asr_engine}")
            result = asr.run()

            # 根据导出格式选择转换方法
            save_ext = self.export_format.lower()
            if save_ext == 'srt':
                result_text = result.to_srt()
            elif save_ext == 'ass':
                result_text = result.to_ass()
            elif save_ext == 'txt':
                result_text = result.to_txt()

            logging.info(f"完成处理文件: {self.file_path} 使用引擎: {self.asr_engine}")
            save_path = self.file_path.rsplit(".", 1)[0] + "." + save_ext
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(result_text)
            self.signals.finished.emit(self.file_path, result_text)
        except Exception as e:
            logging.error(f"处理文件 {self.file_path} 时出错: {str(e)}")
            self.signals.errno.emit(self.file_path, f"处理时出错: {str(e)}")


class UpdateCheckerThread(QThread):
    msg = pyqtSignal(str, str, str)  # 用于发送消息的信号

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            from check_update import check_update, check_internet_connection
            # 检查互联网连接
            if not check_internet_connection():
                self.msg.emit("错误", "无法连接到互联网，请检查网络连接。", "")
                return
            # 检查更新
            config = check_update(self)
            if config:
                if config['fource']:
                    self.msg.emit("更新", "检测到新版本，请下载最新版本。", config['update_download_url'])
                else:
                    self.msg.emit("可更新", "检测到新版本，请下载最新版本。", config['update_download_url'])
        except Exception as e:
            pass


class FFmpegDownloadThread(QThread):
    """FFmpeg 下载线程"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, ffmpeg_manager: FFmpegManager, parent=None):
        super().__init__(parent)
        self.ffmpeg_manager = ffmpeg_manager

    def run(self):
        try:
            success = self.ffmpeg_manager.download_ffmpeg(
                progress_callback=self.progress_updated.emit,
                status_callback=self.status_updated.emit
            )
            self.finished.emit(success, "下载完成" if success else "下载失败")
        except Exception as e:
            self.finished.emit(False, str(e))


class FFmpegDownloadDialog(QDialog):
    """FFmpeg 下载对话框"""

    def __init__(self, ffmpeg_manager: FFmpegManager, parent=None):
        super().__init__(parent)
        self.ffmpeg_manager = ffmpeg_manager
        self.success = False
        self._init_ui()
        self._start_download()

    def _init_ui(self):
        self.setWindowTitle("正在下载 FFmpeg")
        self.setFixedSize(450, 180)
        layout = QVBoxLayout(self)

        self.info_label = QLabel(
            "视频转换需要 FFmpeg，正在自动下载...\n"
            "下载源：GitHub (BtbN/FFmpeg-Builds)",
            self
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.status_label = QLabel("准备中...", self)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

    def _start_download(self):
        self.download_thread = FFmpegDownloadThread(self.ffmpeg_manager, self)
        self.download_thread.progress_updated.connect(self.progress_bar.setValue)
        self.download_thread.status_updated.connect(self.status_label.setText)
        self.download_thread.finished.connect(self._on_finished)
        self.download_thread.start()

    def _on_finished(self, success: bool, message: str):
        self.success = success
        if success:
            InfoBar.success(
                title='下载完成',
                content='FFmpeg 已准备就绪',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent() if self.parent() else self
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "下载失败",
                f"FFmpeg 下载失败：{message}\n\n"
                "请手动下载 ffmpeg.exe 并放置到程序目录，\n"
                "或从 https://github.com/BtbN/FFmpeg-Builds/releases 下载。"
            )
            self.reject()


class ASRWidget(QWidget):
    """ASR处理界面"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.max_threads = 3  # 设置最大线程数
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(self.max_threads)
        self.processing_queue = []
        self.workers = {}  # 维护文件路径到worker的映射
        self.all_done_shown = False


    def init_ui(self):
        layout = QVBoxLayout(self)

        # ASR引擎选择区域
        engine_layout = QHBoxLayout()
        engine_label = BodyLabel("选择接口:", self)
        engine_label.setFixedWidth(70)
        self.combo_box = ComboBox(self)
        self.combo_box.addItems(['B 接口', 'J 接口', 'K 接口', 'Whisper'])
        engine_layout.addWidget(engine_label)
        engine_layout.addWidget(self.combo_box)
        layout.addLayout(engine_layout)

        # 导出格式选择区域
        format_layout = QHBoxLayout()
        format_label = BodyLabel("导出格式:", self)
        format_label.setFixedWidth(70)
        self.format_combo = ComboBox(self)
        self.format_combo.addItems(['SRT', 'TXT', 'ASS'])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_input = LineEdit(self)
        self.file_input.setPlaceholderText("拖拽文件或文件夹到这里")
        self.file_input.setReadOnly(True)
        self.file_button = PushButton("选择文件", self)
        self.file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.file_button)
        layout.addLayout(file_layout)

        # 文件列表表格
        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['文件名', '状态'])
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)

        # 设置表格列的拉伸模式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 处理按钮
        button_layout = QHBoxLayout()
        self.process_button = PushButton("开始处理", self)
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setEnabled(False)  # 初始禁用
        button_layout.addWidget(self.process_button)
        self.clear_btn = PushButton("清理已完成", self)
        self.clear_btn.clicked.connect(self.clear_success_tasks)
        button_layout.addWidget(self.clear_btn)
        layout.addLayout(button_layout)

        self.setAcceptDrops(True)

    def select_file(self):
        """选择文件对话框"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择音频或视频文件", "",
                                                "Media Files (*.mp3 *.wav *.ogg *.mp4 *.avi *.mov *.ts)")
        for file in files:
            self.add_file_to_table(file)
        self.all_done_shown = False
        self.update_start_button_state()

    def add_file_to_table(self, file_path):
        """将文件添加到表格中"""
        if self.find_row_by_file_path(file_path) != -1:
            InfoBar.warning(
                title='文件已存在',
                content=f"文件 {os.path.basename(file_path)} 已经添加到列表中。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        item_filename = self.create_non_editable_item(os.path.basename(file_path))
        item_status = self.create_non_editable_item("未处理")
        item_status.setForeground(QColor("gray"))
        self.table.setItem(row_count, 0, item_filename)
        self.table.setItem(row_count, 1, item_status)
        item_filename.setData(Qt.UserRole, file_path)

    def create_non_editable_item(self, text):
        """创建不可编辑的表格项"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def show_context_menu(self, pos):
        """显示右键菜单"""
        current_row = self.table.rowAt(pos.y())
        if current_row < 0:
            return

        self.table.selectRow(current_row)

        menu = RoundMenu(parent=self)
        reprocess_action = Action(FIF.SYNC, "重新处理")
        delete_action = Action(FIF.DELETE, "删除任务")
        open_dir_action = Action(FIF.FOLDER, "打开文件目录")
        menu.addActions([reprocess_action, delete_action, open_dir_action])

        delete_action.triggered.connect(self.delete_selected_row)
        open_dir_action.triggered.connect(self.open_file_directory)
        reprocess_action.triggered.connect(self.reprocess_selected_file)

        menu.exec(QCursor.pos())

    def delete_selected_row(self):
        """删除选中的行"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            file_path = self.table.item(current_row, 0).data(Qt.UserRole)
            if file_path in self.workers:
                worker = self.workers[file_path]
                worker.signals.finished.disconnect(self.update_table)
                worker.signals.errno.disconnect(self.handle_error)
                # QThreadPool 不支持直接终止线程，通常需要设计任务可中断
                # 这里仅移除引用
                self.workers.pop(file_path, None)
            self.table.removeRow(current_row)
            self.update_start_button_state()

    def open_file_directory(self):
        """打开文件所在目录"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            current_item = self.table.item(current_row, 0)
            if current_item:
                file_path = current_item.data(Qt.UserRole)
                directory = os.path.dirname(file_path)
                try:
                    if platform.system() == "Windows":
                        os.startfile(directory)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", directory])
                    else:
                        subprocess.Popen(["xdg-open", directory])
                except Exception as e:
                    InfoBar.error(
                        title='无法打开目录',
                        content=str(e),
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )

    def reprocess_selected_file(self):
        """重新处理选中的文件"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            file_path = self.table.item(current_row, 0).data(Qt.UserRole)
            status = self.table.item(current_row, 1).text()
            if status == "处理中":
                InfoBar.warning(
                    title='当前文件正在处理中',
                    content="请等待当前文件处理完成后再重新处理。",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return
            self.add_to_queue(file_path)

    def add_to_queue(self, file_path):
        """将文件添加到处理队列并更新状态"""
        self.processing_queue.append(file_path)
        self.process_next_in_queue()

    def process_files(self):
        """处理所有未处理或出错的文件"""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 1).text() in ["未处理", "错误"]:
                file_path = self.table.item(row, 0).data(Qt.UserRole)
                self.processing_queue.append(file_path)
        self.process_next_in_queue()

    def process_next_in_queue(self):
        """处理队列中的下一个文件"""
        while self.thread_pool.activeThreadCount() < self.max_threads and self.processing_queue:
            file_path = self.processing_queue.pop(0)
            if file_path not in self.workers:
                self.process_file(file_path)

    def process_file(self, file_path):
        """处理单个文件"""
        # 检查是否需要转换视频，如果需要则先确保 FFmpeg 可用
        audio_exts = ['.mp3', '.wav']
        needs_ffmpeg = not any(file_path.lower().endswith(ext) for ext in audio_exts)

        if needs_ffmpeg:
            # 获取主窗口
            main_window = self.window()
            if hasattr(main_window, 'ensure_ffmpeg'):
                if not main_window.ensure_ffmpeg():
                    # 用户取消或下载失败
                    row = self.find_row_by_file_path(file_path)
                    if row != -1:
                        item_status = self.create_non_editable_item("需要 FFmpeg")
                        item_status.setForeground(QColor("orange"))
                        self.table.setItem(row, 1, item_status)
                    return

        selected_engine = self.combo_box.currentText()
        selected_format = self.format_combo.currentText()
        # 检查输出文件是否存在 (根据选择的格式)
        save_ext = selected_format.lower()
        base_name = os.path.splitext(file_path)[0]
        output_path = base_name + "." + save_ext
        if os.path.exists(output_path):
            row = self.find_row_by_file_path(file_path)
            if row != -1:
                status_item = self.create_non_editable_item("已存在")
                status_item.setForeground(QColor("blue"))
                self.table.setItem(row, 1, status_item)
            self.update_start_button_state()
            return

        worker = ASRWorker(file_path, selected_engine, selected_format)
        worker.signals.finished.connect(self.update_table)
        worker.signals.errno.connect(self.handle_error)
        self.thread_pool.start(worker)
        self.workers[file_path] = worker

        row = self.find_row_by_file_path(file_path)
        if row != -1:
            status_item = self.create_non_editable_item("处理中")
            status_item.setForeground(QColor("orange"))
            self.table.setItem(row, 1, status_item)
            self.update_start_button_state()

    def update_table(self, file_path, result):
        """更新表格中文件的处理状态"""
        row = self.find_row_by_file_path(file_path)
        if row != -1:
            item_status = self.create_non_editable_item("已处理")
            item_status.setForeground(QColor("green"))
            self.table.setItem(row, 1, item_status)

            InfoBar.success(
                title='处理完成',
                content=f"文件 {self.table.item(row, 0).text()} 已处理完成",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self
            )

        self.workers.pop(file_path, None)
        self.process_next_in_queue()
        self.update_start_button_state()

    def handle_error(self, file_path, error_message):
        """处理错误信息"""
        row = self.find_row_by_file_path(file_path)
        if row != -1:
            item_status = self.create_non_editable_item("错误")
            item_status.setForeground(QColor("red"))
            self.table.setItem(row, 1, item_status)

            InfoBar.error(
                title='处理出错',
                content=error_message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

        self.workers.pop(file_path, None)
        self.process_next_in_queue()
        self.update_start_button_state()

    def find_row_by_file_path(self, file_path):
        """根据文件路径查找表格中的行号"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item.data(Qt.UserRole) == file_path:
                return row
        return -1

    def update_start_button_state(self):
        """根据文件列表更新开始处理按钮的状态"""
        has_pending = any(
            self.table.item(row, 1).text() in ["未处理", "错误"]
            for row in range(self.table.rowCount())
        )
        self.process_button.setEnabled(has_pending)

        # 如果没有待处理的任务，且表格不为空，且未显示过完成通知，则显示
        if not has_pending and self.table.rowCount() > 0 and not self.all_done_shown:
            InfoBar.success(
                title='处理完毕',
                content="全部任务处理完毕",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=0,  # 不自动消失
                parent=self
            )
            self.all_done_shown = True

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽释放事件"""
        supported_formats = ('.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma',  # 音频格式
                           '.mp4', '.avi', '.mov', '.ts', '.mkv', '.wmv', '.flv', '.webm', '.rmvb')  # 视频格式
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            if os.path.isdir(file):
                for root, dirs, files_in_dir in os.walk(file):
                    for f in files_in_dir:
                        if f.lower().endswith(supported_formats):
                            self.add_file_to_table(os.path.join(root, f))
            elif file.lower().endswith(supported_formats):
                self.add_file_to_table(file)
        self.all_done_shown = False
        self.update_start_button_state()

    def clear_success_tasks(self):
        """倒序遍历列表，删除包含'成功'或'完成'状态的条目"""
        # 注意：这里假设您的列表控件名为 self.table，请根据实际代码调整变量名
        # 如果源码中使用的是 TableWidget:
        row_count = self.table.rowCount()
        removed_count = 0
        for i in range(row_count - 1, -1, -1):  # 倒序删除防止索引错位
            status_item = self.table.item(i, 1)
            if status_item and status_item.text() in ["已处理", "已存在"]:
                self.table.removeRow(i)
                removed_count += 1

        if removed_count > 0:
            InfoBar.success(
                title='清理完成',
                content=f"已清理 {removed_count} 个已完成/跳过任务",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            InfoBar.info(
                title='无任务可清理',
                content="没有找到已完成的成功任务",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        self.update_start_button_state()


class InfoWidget(QWidget):
    """个人信息界面"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # GitHub URL 和仓库描述
        GITHUB_URL = "https://github.com/WEIFENG2333/AsrTools"
        REPO_DESCRIPTION = """
    🚀 无需复杂配置：无需 GPU 和繁琐的本地配置，小白也能轻松使用。
    🖥️ 高颜值界面：基于 PyQt5 和 qfluentwidgets，界面美观且用户友好。
    ⚡ 效率超人：多线程并发 + 批量处理，文字转换快如闪电。
    📄 多格式支持：支持生成 .srt 和 .txt 字幕文件，满足不同需求。
        """

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        # main_layout.setSpacing(50)

        # 标题
        title_label = BodyLabel("  ASRTools v1.3.0", self)
        title_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 仓库描述区域
        desc_label = BodyLabel(REPO_DESCRIPTION, self)
        desc_label.setFont(QFont("Segoe UI", 12))
        main_layout.addWidget(desc_label)

        github_button = PushButton("GitHub 仓库", self)
        github_button.setIcon(FIF.GITHUB)
        github_button.setIconSize(QSize(20, 20))
        github_button.setMinimumHeight(42)
        github_button.clicked.connect(lambda _: webbrowser.open(GITHUB_URL))
        main_layout.addWidget(github_button)


class QTextEditHandler(logging.Handler):
    """自定义日志处理器，将日志输出到 QTextEdit"""
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


class LogWidget(QWidget):
    """日志显示界面"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # 添加日志处理器
        handler = QTextEditHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)


class MainWindow(FluentWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ASR Processing Tool v1.3.0')

        # ASR 处理界面
        self.asr_widget = ASRWidget()
        self.asr_widget.setObjectName("main")
        self.addSubInterface(self.asr_widget, FIF.ALBUM, 'ASR Processing')

        # 个人信息界面
        self.info_widget = InfoWidget()
        self.info_widget.setObjectName("info")  # 设置对象名称
        self.addSubInterface(self.info_widget, FIF.GITHUB, 'About')

        # 日志界面
        self.log_widget = LogWidget()
        self.log_widget.setObjectName("log")
        self.addSubInterface(self.log_widget, FIF.INFO, 'LOG')

        self.navigationInterface.setExpandWidth(200)
        self.resize(800, 600)

        self.update_checker = UpdateCheckerThread(self)
        self.update_checker.msg.connect(self.show_msg)
        self.update_checker.start()

        # 检查 FFmpeg
        self._check_ffmpeg_on_startup()

    def _check_ffmpeg_on_startup(self):
        """启动时检查 FFmpeg"""
        ffmpeg_mgr = get_ffmpeg_manager()
        if not ffmpeg_mgr.is_ffmpeg_available():
            InfoBar.info(
                title='提示',
                content='首次使用视频转换功能时将自动下载 FFmpeg',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )

    def ensure_ffmpeg(self) -> bool:
        """
        确保 FFmpeg 可用，需要时下载

        Returns:
            bool: FFmpeg 是否可用
        """
        ffmpeg_mgr = get_ffmpeg_manager()
        if ffmpeg_mgr.is_ffmpeg_available():
            return True

        reply = QMessageBox.question(
            self,
            "需要 FFmpeg",
            "视频转换需要 FFmpeg，是否现在自动下载？\n\n"
            "下载大小约 80-100MB，可能需要几分钟。\n\n"
            "或者您可以手动下载 ffmpeg.exe 并放置到程序目录。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            dialog = FFmpegDownloadDialog(ffmpeg_mgr, self)
            return dialog.exec_() == QDialog.Accepted

        return False

    def show_msg(self, title, content, update_download_url):
        w = MessageBox(title, content, self)
        if w.exec() and update_download_url:
            webbrowser.open(update_download_url)
        if title == "更新":
            sys.exit(0)


def video2audio(input_file: str, output: str = "") -> bool:
    """使用ffmpeg将视频转换为音频"""
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


def start():
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    # setTheme(Theme.DARK)  # 如果需要深色主题，取消注释此行
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    start()
