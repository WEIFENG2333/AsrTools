from bk_asr import BcutASR, JianYingASR, KuaiShouASR, WhisperASR


if __name__ == '__main__':
    audio_file = "resources/低视力音乐助人者.mp3"
    asr = JianYingASR(audio_file, use_cache=True)
    result = asr.run()
    result.to_srt()
    print(result)

    # 使用PySide6 + qfluentwidgets 制作页面，
    # 垂直布局，
    # - 含有下拉框，选择 BcutASR, JianYingASR, KuaiShouASR, WhisperASR
    # - 文件选择输入，支持输入音频文件和文件夹，可以退拽进来, 输入框和按钮在一行，每次选择以后再列表增加文件
    # - 文件列表展示，展示音频文件列表，并显示是否完成处理，可以右键菜单，删除文件，打开文件目录功能
    # - 按钮，点击后调用 ASR.transcribe(platform, audio_file)，对未处理文件的进行处理
    # -