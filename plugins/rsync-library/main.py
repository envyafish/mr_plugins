import requests
from mbot.openapi import mbot_api

api_key = ''
url = 'http://:8096/emby/Items'


def get_tmdb_by_Movie():
    params = {'api_key': api_key, 'IncludeItemTypes': 'Movie', 'Fields': 'ProviderIds', 'Recursive': 'true'}
    # 发送请求，获取所有电影信息
    response = requests.get(url, params=params)
    # print(response.content)
    # 解析响应JSON数据，提取所需信息
    movies = []
    for item in response.json()['Items']:
        movie = {
            'title': item['Name'],
            'tmdb_id': item['ProviderIds'].get('Tmdb')
            # 其他影片信息字段类似
        }
        movies.append(movie)
    # 输出结果
    return movies


def get_series_by_id(series, series_id):
    items = series.json()['Items']
    filter_list = list(filter(lambda x: x['Id'] == series_id, items))
    if filter_list:
        return filter_list[0]['ProviderIds'].get('Tmdb')
    return None


def get_tmdb_by_season():
    params = {'api_key': api_key, 'IncludeItemTypes': 'Season', 'Fields': 'ProviderIds', 'Recursive': 'true'}
    # 发送请求，获取所有电影信息
    season_res = requests.get(url, params=params)
    params = {'api_key': api_key, 'IncludeItemTypes': 'Series', 'Fields': 'ProviderIds', 'Recursive': 'true'}
    series_res = requests.get(url, params=params)
    # print(series_res.content)
    seasons = []
    for item in season_res.json()['Items']:
        season_index = item['IndexNumber']
        series_name = item['SeriesName']
        series_id = item['SeriesId']
        tmdb_id = get_series_by_id(series_res, series_id)
        season = {
            'title': series_name,
            'tmdb_id': tmdb_id,
            'season_index': season_index
        }
        seasons.append(season)
    return seasons


if __name__ == '__main__':
    seasons = get_tmdb_by_season()
    print(seasons)
    movies = get_tmdb_by_Movie()
    print(movies)
