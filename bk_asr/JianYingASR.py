import datetime
import hashlib
import hmac
import json
import logging
import os
import subprocess
import time
from typing import Dict, Tuple, Literal

# import ffmpeg
import requests

from .ASRData import ASRDataSeg
from .BaseASR import BaseASR


class JianYingASR(BaseASR):
    def __init__(self, audio_path: [str, bytes], use_cache: bool = False, start_time: float = 0, end_time: float = 6000):
        super().__init__(audio_path, use_cache)
        self.audio_path = audio_path
        self.end_time = end_time
        self.start_time = start_time

        # AWS credentials
        self.session_token = None
        self.secret_key = None
        self.access_key = None

        # Upload details
        self.store_uri = None
        self.auth = None
        self.upload_id = None
        self.session_key = None
        self.upload_hosts = None


    def submit(self) -> str:
        """Submit the task"""
        url = "https://lv-pc-api-sinfonlinec.ulikecam.com/lv/v1/audio_subtitle/submit"
        payload = {
            "adjust_endtime": 200,
            "audio": self.store_uri,
            "caption_type": 2,
            "client_request_id": "45faf98c-160f-4fae-a649-6d89b0fe35be",
            "max_lines": 1,
            "songs_info": [{"end_time": self.end_time, "id": "", "start_time": self.start_time}],
            "words_per_line": 16
        }

        sign, device_time = self._generate_sign_parameters(url='/lv/v1/audio_subtitle/submit', pf='4', appvr='4.0.0',
                                                           tdid='3943278516897751')
        headers = self._build_headers(device_time, sign)
        response = requests.post(url, json=payload, headers=headers)
        query_id = response.json()['data']['id']
        return query_id

    def upload(self):
        """Upload the file"""
        self._upload_sign()
        self._upload_auth()
        self._upload_file()
        self._upload_check()
        uri = self._upload_commit()
        return uri

    def query(self, query_id: str):
        """Query the task"""
        url = "https://lv-pc-api-sinfonlinec.ulikecam.com/lv/v1/audio_subtitle/query"
        payload = {
            "id": query_id,
            "pack_options": {"need_attribute": True}
        }
        sign, device_time = self._generate_sign_parameters(url='/lv/v1/audio_subtitle/query', pf='4', appvr='4.0.0',
                                                           tdid='3943278516897751')
        headers = self._build_headers(device_time, sign)
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def _run(self):
        logging.info("正在上传文件...")
        self.upload()
        query_id = self.submit()
        logging.info(f"任务提交成功, 查询ID: {query_id}")
        resp_data = self.query(query_id)
        return resp_data

    def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
        return [ASRDataSeg(u['text'], u['start_time'], u['end_time']) for u in resp_data['data']['utterances']]

    @staticmethod
    def _generate_sign_parameters(url: str, pf: str = '4', appvr: str = '4.0.0', tdid: str = '3943278516897751') -> \
    Tuple[str, str]:
        """Generate signature and timestamp"""
        current_time = str(int(time.time()))
        sign_str = f"9e2c|{url[-7:]}|{pf}|{appvr}|{current_time}|{tdid}|11ac"
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        return sign.lower(), current_time

    def _build_headers(self, device_time: str, sign: str) -> Dict[str, str]:
        """Build headers for requests"""
        return {
            'User-Agent': "Cronet/TTNetVersion:01594da2 2023-03-14 QuicVersion:46688bb4 2022-11-28",
            'appvr': "4.0.0",
            'device-time': str(device_time),
            'pf': "4",
            'sign': sign,
            'sign-ver': "1",
            'tdid': "3943278516897751",
        }

    def _uplosd_headers(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 Thea/1.0.1",
            'Authorization': self.auth,
            'Content-CRC32': self.crc32_hex,
        }
        return headers

    def _upload_sign(self):
        """Get upload sign"""
        url = "https://lv-pc-api-sinfonlinec.ulikecam.com/lv/v1/upload_sign"
        payload = json.dumps({"biz": "pc-recognition"})
        sign, device_time = self._generate_sign_parameters(url='/lv/v1/upload_sign', pf='4', appvr='4.0.0',
                                                           tdid='3943278516897751')
        headers = self._build_headers(device_time, sign)
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        login_data = response.json()
        self.access_key = login_data['data']['access_key_id']
        self.secret_key = login_data['data']['secret_access_key']
        self.session_token = login_data['data']['session_token']
        return self.access_key, self.secret_key, self.session_token

    def _upload_auth(self):
        """Get upload authorization"""
        if isinstance(self.audio_path, bytes):
            file_size = len(self.audio_path)
        else:
            file_size = os.path.getsize(self.audio_path)
        request_parameters = f'Action=ApplyUploadInner&FileSize={file_size}&FileType=object&IsInner=1&SpaceName=lv-mac-recognition&Version=2020-11-19&s=5y0udbjapi'

        t = datetime.datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')
        headers = {
            "x-amz-date": amz_date,
            "x-amz-security-token": self.session_token
        }
        signature = aws_signature(self.secret_key, request_parameters, headers, region="cn", service="vod")
        authorization = f"AWS4-HMAC-SHA256 Credential={self.access_key}/{datestamp}/cn/vod/aws4_request, SignedHeaders=x-amz-date;x-amz-security-token, Signature={signature}"
        headers["authorization"] = authorization
        response = requests.get(f"https://vod.bytedanceapi.com/?{request_parameters}", headers=headers)
        store_infos = response.json()

        self.store_uri = store_infos['Result']['UploadAddress']['StoreInfos'][0]['StoreUri']
        self.auth = store_infos['Result']['UploadAddress']['StoreInfos'][0]['Auth']
        self.upload_id = store_infos['Result']['UploadAddress']['StoreInfos'][0]['UploadID']
        self.session_key = store_infos['Result']['UploadAddress']['SessionKey']
        self.upload_hosts = store_infos['Result']['UploadAddress']['UploadHosts'][0]
        self.store_uri = store_infos['Result']['UploadAddress']['StoreInfos'][0]['StoreUri']
        return store_infos

    def _upload_file(self):
        """Upload the file"""
        url = f"https://{self.upload_hosts}/{self.store_uri}?partNumber=1&uploadID={self.upload_id}"
        headers = self._uplosd_headers()
        response = requests.put(url, data=self.file_binary, headers=headers)
        resp_data = response.json()
        assert resp_data['success'] == 0, f"File upload failed: {response.text}"
        return resp_data

    def _upload_check(self):
        """Check upload result"""
        url = f"https://{self.upload_hosts}/{self.store_uri}?uploadID={self.upload_id}"
        payload = f"1:{self.crc32_hex}"
        headers = self._uplosd_headers()
        response = requests.post(url, data=payload, headers=headers)
        resp_data = response.json()
        return resp_data

    def _upload_commit(self):
        """Commit the uploaded file"""
        url = f"https://{self.upload_hosts}/{self.store_uri}?uploadID={self.upload_id}&partNumber=1&x-amz-security-token={self.session_token}"
        headers = self._uplosd_headers()
        response = requests.put(url, data=self.file_binary, headers=headers)
        return self.store_uri


def sign(key: bytes, msg: str) -> bytes:
    """使用HMAC-SHA256生成签名"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(secret_key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    """生成用于AWS签名的密钥"""
    k_date = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing


def aws_signature(secret_key: str, request_parameters: str, headers: Dict[str, str],
                  method: str = "GET", payload: str = '', region: str = "cn", service: str = "vod") -> str:
    """生成AWS签名"""
    canonical_uri = '/'
    canonical_querystring = request_parameters
    canonical_headers = '\n'.join([f"{key}:{value}" for key, value in headers.items()]) + '\n'
    signed_headers = ';'.join(headers.keys())
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    amzdate = headers["x-amz-date"]
    datestamp = amzdate.split('T')[0]

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{amzdate}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signing_key = get_signature_key(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature




if __name__ == '__main__':
    # Example usage
    audio_file = r"test.mp3"
    asr = JianYingASR(audio_file)
    asr_data = asr.run()
    print(asr_data)
