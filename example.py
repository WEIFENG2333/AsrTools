from bk_asr import BcutASR, JianYingASR, KuaiShouASR


if __name__ == '__main__':
    audio_file = "resources/test.mp3"
    asr = JianYingASR(audio_file)
    result = asr.run()
    result.to_srt()
    print(result.to_srt())