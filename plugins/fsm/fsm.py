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


class FSM:
    cookie: str = None
    api: str = 'https://api.fsm.name/Torrents/listTorrents'

    def __init__(self, cookie):
        self.cookie = cookie

    def search(self, type: MediaType = 0, keyword: str = None, page: int = 1):
        url = f"{self.api}?keyword={keyword}&page={page}&type={type}&systematics=1&tags=[]"
        headers = {
            'APITOKEN ': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        print(response.text)
        if response.status_code == 200:
            data = response.json()
            print(data)
            return data
        return None


if __name__ == '__main__':
    fsm = FSM('7a1s4RQVVsDcdNV1')
    print(fsm.cookie)
    fsm.search(MediaType.AV, 'SNIS-')