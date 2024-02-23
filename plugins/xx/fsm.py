import hashlib
import json
import time
from enum import Enum

import requests


class MediaType(int, Enum):
    """媒体类型"""
    ALL = 0
    AV = 1
    CHINA = 2
    PHOTO = 3
    GAME = 4
    ANIME = 5
    COMIC = 6
    WEST = 7
    OTHER = 8


def calculate_md5(input_string):
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    return md5_hash.hexdigest()


class FSM:
    api: str = 'https://api.fsm.name/Torrents/listTorrents'
    salt: str = ""
    url: str = "/Torrents/listTorrents"
    passkey: str = None
    token: str = None
    cookie: str = None

    def __init__(self, token, passkey, salt):
        self.token = token
        self.passkey = passkey
        self.salt = salt

    def init_cookie(self):
        current_timestamp = int(time.time())
        md5 = calculate_md5(f"{self.token}{current_timestamp}{self.salt}{self.url}")
        cookie = f"{self.token};{current_timestamp};{md5}"
        self.cookie = cookie

    def search(self, type: MediaType = 0, keyword: str = None, page: int = 1):
        self.init_cookie()
        url = f"{self.api}?keyword={keyword}&page={page}&type={type}&systematics=0&tags=[]"
        headers = {
            'Authorization': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        return None

    def download_torrent(self, tid, code):
        self.init_cookie()
        url = f"https://api.fsm.name/Torrents/download?tid={tid}&passkey={self.passkey}&source=direct"
        headers = {
            'Authorization': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        torrent_path = f'/data/xx_torrents/{code}.torrent'
        with open(torrent_path, 'wb') as torrent:
            torrent.write(response.content)
            torrent.flush()
        return torrent_path
