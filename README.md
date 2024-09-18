## ? AsrTools

**音频转字幕文本工具**  
??? AsrTools: 智能语音转文字工具 | 内置剪映、快手、必剪官方接口 | 高效批处理 | 用户友好界面 | 无需 GPU | 免费使用大厂 ASR 服务 | 支持 SRT/TXT 输出 | 让您的音频瞬间变成精确文字！
---

## ? **特色功能**

- ? **调用大厂接口**： 内置多家大厂API，包括剪映、快手、必剪，免费享受高质量服务。
- ? **无需本地运行**：轻松使用，无需 GPU 和繁琐的本地配置。
- ?? **高颜值界面**：基于 **PyQt5** 和 **qfluentwidgets**，界面美观且用户友好。
-  ? **效率超人**：多线程并发 + 批量处理，文字转换快如闪电
- ? **多格式支持**：支持生成 `.srt` 和 `.txt` 字幕文件，满足不同需求。
- ? **剪映接口**： 剪映接口逆向还原，与官方体验一致，稳定可靠。

---


## ? **截图预览**

*主界面截图示例*

![main_window](resources/main_window.png)


## ?? **安装指南**

我们为 Windows 用户提供了打包好的[Release](https://github.com/WEIFENG2333/AsrTools/releases)版本，下载后解压即可直接使用，无需配置环境。

1. **启动应用**：运行启动GUI界面。

2. **选择ASR引擎**：在下拉菜单中选择你需要使用的ASR引擎（剪映、快手、必剪）。

3. **添加文件**：点击“选择文件”按钮或将文件/文件夹拖拽到指定区域。

4. **开始处理**：点击“开始处理”按钮，程序将自动开始转换，并在完成后在原音频目录生成 `.srt` 字幕文件。（默认保持3个线程运行）


## ?? **开发者指南**
如果你想从源码运行：
```bash
git clone https://github.com/WEIFENG2333/AsrTools.git
cd AsrTools

# 1.纯代码调用示例
pip install requests
python example.py

# 2.可以选择启动GUI界面（PyQt5 + qfluentwidgets 环境）
pip install -r requirements.txt
python asr_gui.py
```


#### ? **代码示例**

如果想代码中调用 `bk_asr`，你可以下载 `bk_asr` 文件夹，以下是一个简单的调用示例：

```python
from bk_asr import BcutASR, JianYingASR, KuaiShouASR, WhisperASR

audio_file = "resources/test.mp3"
asr = BcutASR(audio_file)  # 可以选择BcutASR, JianYingASR, 或 KuaiShouASR
result = asr.run()
srt = result.to_srt()  # 生成SRT字幕文件
txt = result.to_txt()  # 生成TXT字幕文件
json_data = result.to_json()  # 返回一个字典（包含时间）
print(txt)
```

---


## ? **许可证**

本项目采用 [MIT 许可证](https://opensource.org/licenses/MIT)。详情请参阅 [LICENSE](https://github.com/WEIFENG2333/AsrTools/blob/main/LICENSE) 文件。

---

## ? **联系与支持**

如果你在使用过程中遇到任何问题或有任何建议，欢迎通过以下方式联系我们：

- **邮件**：2715673327@qq.com
- **Issues**：[提交问题](https://github.com/WEIFENG2333/AsrTools/issues)

---

感谢您使用 **AsrTools**！?  
希望这款工具能为您的工作和生活带来便利。?