import requests

from .ASRData import ASRDataSeg
from .BaseASR import BaseASR


class KuaiShouASR(BaseASR):
    def __init__(self, audio_path: [str, bytes], use_cache: bool = False):
        super().__init__(audio_path, use_cache)

    def _run(self) -> dict:
        return self._submit()

    def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
        return [ASRDataSeg(u['text'], u['start_time'], u['end_time']) for u in resp_data['data']['text']]

    def _submit(self) -> dict:
        payload = {
            "typeId": "1"
        }
        files = [('file', ('test.mp3', self.file_binary, 'audio/mpeg'))]
        result = requests.post("https://ai.kuaishou.com/api/effects/subtitle_generate", data=payload, files=files)
        return result.json()


if __name__ == '__main__':
    # Example usage
    # Example usage
    audio_file = r"test.mp3"
    asr = KuaiShouASR(audio_file)
    asr_data = asr.run()
    print(asr_data)
