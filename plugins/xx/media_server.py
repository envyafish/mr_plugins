import re


from mbot.external.mediaserver import EmbyMediaServer
from mbot.models.mediamodels import MediaType
from plexapi.server import PlexServer

from plugins.xx.base_config import get_base_config, ConfigType
from plugins.xx.db import get_config_db

config_db = get_config_db()




class MediaServer:
    emby: EmbyMediaServer = None
    plex: PlexServer = None

    def __init__(self):
        emby_info, plex_info = self.get_config()
        if emby_info:
            self.emby = EmbyMediaServer(api_key=emby_info['api_key'], host=emby_info['host'], port=emby_info['port'],
                                        https=False)
        if plex_info:
            self.plex = PlexServer(plex_info['url'], plex_info['token'])

    def read_yaml_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            yaml_data = file.read()
        return yaml_data

    def get_config(self):
        servers = get_base_config(ConfigType.Media_Server)
        emby_info = {}
        plex_info = {}
        for server in servers:
            if server['name'] == 'emby':
                emby_info['host'] = server['host']
                emby_info['port'] = server['port']
                emby_info['api_key'] = server['api_key']
            elif server['name'] == 'plex':
                plex_info['url'] = server['url']
                plex_info['token'] = server['token']
        return emby_info, plex_info

    def list_emby_all(self, path_list: list):
        data = self.emby.list_all(MediaType.Movie.name)
        movies = data['Items']
        #         返回path的父目录在path_list中的所有电影
        return [movie['Name'] for movie in movies if self.match_path(movie['MediaSources'][0]['Path'], path_list)]

    def match_path(self, path, folders):
        #     判断path是否在folders中
        for folder in folders:
            if path.startswith(folder):
                return True
        return False

    def list_plex_all(self, title_list: list):
        movies = []
        for section in self.plex.library.sections():
            if section.title in title_list:
                for video in section.all():
                    movies.append(video.title)
        return movies

    def get_codes(self):
        videos = []
        codes = []
        config = config_db.get_config()
        emby_folders = config.emby_folders
        plex_titles = config.plex_titles
        if self.emby and emby_folders:
            folder_list = emby_folders.split(',')
            movies = self.list_emby_all(folder_list)
            videos.extend(movies)
        if self.plex and plex_titles:
            title_list = plex_titles.split(',')
            movies = self.list_plex_all(title_list)
            videos.extend(movies)
        for movie in videos:
            match = re.match(r'^([A-Z0-9-]+)', movie)
            if match:
                code = match.group(1)
                codes.append(code)
        # 为codes去重
        codes = list(set(codes))
        return codes

if __name__ == '__main__':
    media_server = MediaServer()
    codes = media_server.get_codes()
    for code in codes:
        print(code)