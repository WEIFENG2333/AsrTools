from bk_asr import BcutASR, JianYingASR, KuaiShouASR


if __name__ == '__main__':
    audio_file = "resources/低视力音乐助人者.mp3"
    asr = JianYingASR(audio_file)
    result = asr.run()
    result.to_srt()
    print(result)