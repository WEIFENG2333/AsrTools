import os

from openai import OpenAI

from .ASRData import ASRDataSeg
from .BaseASR import BaseASR



class WhisperASR(BaseASR):
    def __init__(self, audio_path: [str, bytes], model: str = MODEL, use_cache: bool = False):
        super().__init__(audio_path, use_cache)
        self.base_url = os.getenv('OPENAI_BASE_URL')
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.base_url or not self.api_key:
            raise ValueError("环境变量 OPENAI_BASE_URL 和 OPENAI_API_KEY 必须设置")
        self.model = model
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def _run(self) -> dict:
        return self._submit()

    def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
        return [ASRDataSeg(u['text'], u['start'], u['end']) for u in resp_data['segments']]

    def _get_key(self) -> str:
        return f"{self.__class__.__name__}-{self.model}-{self.crc32_hex}-{self.model}"

    def _submit(self) -> dict:
        completion = self.client.audio.transcriptions.create(
            model=self.model,
            temperature=0,
            response_format="verbose_json",
            file=("test.mp3", self.file_binary, "audio/mp3"),
            prompt="",
            language="zh"
        )
        return completion.to_dict()

if __name__ == '__main__':
    # Example usage
    audio_file = r"test.mp3"
    asr = WhisperASR(audio_file)
    asr_data = asr.run()
    print(asr_data)


