import os

from openai import OpenAI

from .ASRData import ASRDataSeg
from .BaseASR import BaseASR
from dotenv import load_dotenv
import logging
import json

load_dotenv()

class WhisperASR(BaseASR):
    def __init__(self, audio_path: [str, bytes], model: str = "gpt-4o-mini-transcribe", use_cache: bool = False):
        super().__init__(audio_path, use_cache)
        # self.base_url = os.getenv('OPENAI_BASE_URL')
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("环境变量 OPENAI_BASE_URL 和 OPENAI_API_KEY 必须设置")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def _run(self) -> StopIteration:
        response = self._submit()
        return response.text
    
    def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
        return [ASRDataSeg(u['text'], u['start'], u['end']) for u in resp_data['segments']]

    def _get_key(self) -> str:
        return f"{self.__class__.__name__}-{self.model}-{self.crc32_hex}-{self.model}"

    def _submit(self) -> dict:
        audio_file = open(self.audio_path, "rb")
        completion = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file,  
            prompt="請將語音轉換成文字，並添加標點符號。如果有偵測錯誤，請自行修正。這段語音是關於 CoscI 物理模擬器網站的使用介紹與說明，演化式是對時間的一階微分(dt)。",
            language="zh"
        )
        return completion


