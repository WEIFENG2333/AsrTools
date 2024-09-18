# 🎤 AsrTools

**音频转字幕文本工具**

🎙️✨ **AsrTools**：智能语音转文字工具 | 内置剪映、快手、必剪官方接口 | 高效批处理 | 用户友好界面 | 无需 GPU | 免费使用大厂 ASR 服务 | 支持 SRT/TXT 输出 | 让您的音频瞬间变成精确文字！



## 🌟 **特色功能**

- 💸 **调用大厂接口**：内置多家大厂 API，包括剪映、快手、必剪，免费享受高质量服务。
- 🚀 **无需本地运行**：轻松使用，无需 GPU 和繁琐的本地配置。
- 🖥️ **高颜值界面**：基于 **PyQt5** 和 **qfluentwidgets**，界面美观且用户友好。
- ⚡ **效率超人**：多线程并发 + 批量处理，文字转换快如闪电。
- 📄 **多格式支持**：支持生成 `.srt` 和 `.txt` 字幕文件，满足不同需求。
- 🔍 **剪映接口**：剪映接口逆向还原，与官方体验一致，稳定可靠。



*主界面截图示例*

<img src="resources/main_window.png" width="80%" alt="主界面">


### 🖥️ **快速上手**

1. **启动应用**：运行下载的可执行文件或通过命令行启动 GUI 界面。
2. **选择 ASR 引擎**：在下拉菜单中选择你需要使用的 ASR 引擎（剪映、快手、必剪）。
3. **添加文件**：点击“选择文件”按钮或将文件/文件夹拖拽到指定区域。
4. **开始处理**：点击“开始处理”按钮，程序将自动开始转换，并在完成后在原音频目录生成 `.srt` 或 `.txt` 字幕文件。（默认保持 3 个线程运行）

## 🛠️ **安装指南**

我们为 Windows 用户提供了打包好的[Release](https://github.com/WEIFENG2333/AsrTools/releases)版本，下载后解压即可直接使用，无需配置环境。

###  **1. 从发布版本安装**

1. **下载 Release**：访问 [Release 页面](https://github.com/WEIFENG2333/AsrTools/releases) 并下载最新的可执行文件压缩包。
2. **解压文件**：将下载的压缩包解压到您的目标目录。
3. **启动应用**：运行解压后的可执行文件，即可启动 GUI 界面。


###  **2. 从源码安装（开发者）**

如果您想从源码运行，请按照以下步骤操作：

1. **克隆仓库并进入项目目录**

    ```bash
    git clone https://github.com/WEIFENG2333/AsrTools.git
    cd AsrTools
    ```

2. **安装依赖并运行**

    - **启动 GUI 界面**

        ```bash
        pip install -r requirements.txt
        python asr_gui.py
        ```

    - **纯代码调用示例**

        ```bash
        pip install requests
        python example.py
        ```

---

## 📝 **开发者指南**

如果您想在代码中调用 `bk_asr`，可以下载 `bk_asr` 文件夹，以下是一个简单的调用示例：

```python
from bk_asr import BcutASR, JianYingASR, KuaiShouASR, WhisperASR

audio_file = "resources/test.mp3"

# 使用必剪 ASR 引擎
asr = BcutASR(audio_file, use_cache=True)
result = asr.run()
srt = result.to_srt()      # 生成 SRT 字幕文件
txt = result.to_txt()      # 生成 TXT 字幕文件
json_data = result.to_json()  # 返回一个字典（包含时间）
print(txt)
```

---

## 📬 **联系与支持**

如果您在使用过程中遇到任何问题或有任何建议，欢迎通过以下方式联系我们：

- **邮件**：2715673327@qq.com
- **Issues**：[提交问题](https://github.com/WEIFENG2333/AsrTools/issues)

感谢您使用 **AsrTools**！🎉  
希望这款工具能为您的工作和生活带来便利。😊

---

 ## 📄 **许可证**

本项目采用 [GNU 通用公共许可证第3版（GPL-3.0）](https://www.gnu.org/licenses/gpl-3.0.en.html)。详情请参阅 [LICENSE](https://github.com/WEIFENG2333/AsrTools/blob/main/LICENSE) 文件。



