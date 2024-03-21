import hashlib
import json
import time
from enum import Enum

import requests

from plugins.xx import Logger


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




class FSM:
    api: str = 'https://api.fsm.name/Torrents/listTorrents'
    url: str = "/Torrents/listTorrents"
    passkey: str = None
    token: str = None

    def __init__(self, token, passkey):
        self.token = token
        self.passkey = passkey


    def search(self, type: MediaType = 0, keyword: str = None, page: int = 1):
        url = f"{self.api}?keyword={keyword}&page={page}&type={type}&systematics=0&tags=[]"
        headers = {
            'APITOKEN': self.token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            Logger.error('飞天拉面神教API Token失效')
            return None
        if response.status_code == 200:
            data = response.json()
            return data
        return None

    def download_torrent(self, tid, code):
        url = f"https://api.fsm.name/Torrents/download?tid={tid}&passkey={self.passkey}&source=direct"
        headers = {
            'APITOKEN': self.token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        torrent_path = f'/data/xx_torrents/{code}.torrent'
        with open(torrent_path, 'wb') as torrent:
            torrent.write(response.content)
            torrent.flush()
        return torrent_path
