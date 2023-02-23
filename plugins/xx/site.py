import os.path
import random
import time
from typing import List

import requests
from moviebotapi.site import SearchQuery, SearchType, CateLevel1, Torrent

from plugins.xx import str_cookies_to_dict
from plugins.xx.db import get_config_db
from plugins.xx.exceptions import ConfigInitError
from plugins.xx.logger import Logger
from plugins.xx.models import Config
from mbot.openapi import mbot_api
from pyrate_limiter import Duration, RequestRate, Limiter

config_db = get_config_db()

# 一分钟请求一次站点
rate_limits = ([RequestRate(1, Duration.MINUTE)])

limiter = Limiter(*rate_limits)


class Site:
    config: Config
    cn_keywords: List[str] = ['中字', '中文字幕', '色花堂', '字幕']

    def __init__(self, config: Config):
        if not config:
            Logger.error("请先初始化配置")
            raise ConfigInitError
        if not config.site_id:
            Logger.error("配置缺失:缺少可搜索的站点")
            raise ConfigInitError
        self.config = config
        if not os.path.exists('/data/xx_torrents'):
            os.mkdir('/data/xx_torrents')

    def get_local_torrent(self, code):
        torrents = self.search_local_torrent(code)
        filter_torrents = self.filter_torrents(torrents)
        sort_torrents = self.sort_torrents(filter_torrents)
        if sort_torrents:
            return sort_torrents[0]
        return None

    @limiter.ratelimit('site_search', delay=True)
    def get_remote_torrent(self, code):
        time.sleep(random.randint(1, 20))
        Logger.info(f"从PT站点搜索{code}的学习资料")
        torrents = self.search_remote_torrents(code)
        filter_torrents = self.filter_torrents(torrents)
        sort_torrents = self.sort_torrents(filter_torrents)
        if sort_torrents:
            return sort_torrents[0]
        return None

    @staticmethod
    def search_local_torrent(code):
        query = SearchQuery(SearchType.Keyword, code)
        return mbot_api.site.search_local(query=query, cate_level1=[CateLevel1.AV])

    def search_remote_torrents(self, code):
        query = SearchQuery(SearchType.Keyword, code)
        return mbot_api.site.search_remote(query=query, cate_level1=[CateLevel1.AV],
                                           site_id=self.config.site_id.split(','))

    # def search_remote_torrents(self, code):
    #     params = {
    #         'keyword': code,
    #         'cates': 'AV',
    #         'cache': '',
    #         'site_id': self.config.site_id,
    #         'searchDouban': False,
    #         'searchMediaServer': False,
    #         'searchSite': True
    #     }
    #     res = mbot_api.session.get('movie.search_keyword', params=params)
    #     torrents = res['torrents']
    #     for torrent in torrents:
    #         for key in torrent:
    #             if not torrent[key]:
    #                 torrent[key] = None
    #         torrent['free_deadline'] = None
    #         torrent['publish_date'] = None
    #
    #     if torrents:
    #         return [Torrent(torrent) for torrent in torrents]
    #     return []

    def filter_torrents(self, torrents: List[Torrent]):
        Logger.info("过滤前种子列表:")
        for torrent in torrents:
            Logger.info(f"种子名:{torrent.name}{torrent.subject}|种子大小:{torrent.size_mb}MB")
        only_chinese = self.config.only_chinese
        max_size = self.config.max_size
        min_size = self.config.min_size
        Logger.info(f"过滤条件:只下中文:{only_chinese}|最大体积:{max_size}MB|最小体积:{min_size}MB")
        filter_list = []
        for torrent in torrents:
            title = f"{torrent.name}{torrent.subject}"
            has_chinese = self.has_chinese(title)
            setattr(torrent, 'chinese', has_chinese)
            size_mb = torrent.size_mb
            if not size_mb:
                continue
            if only_chinese:
                if not has_chinese:
                    continue
            if max_size:
                if size_mb > max_size:
                    continue
            if min_size:
                if size_mb < min_size:
                    continue
            filter_list.append(torrent)
        Logger.info("过滤后种子列表:")
        for torrent in filter_list:
            Logger.info(f"种子名:{torrent.name}{torrent.subject}|种子大小:{torrent.size_mb}MB")
        return filter_list

    @staticmethod
    def sort_torrents(torrents: List[Torrent]):
        for item in torrents:
            if not item.upload_count:
                item.upload_count = 0
        upload_sort_list = sorted(torrents, key=lambda torrent: torrent.upload_count, reverse=True)
        cn_sort_list = sorted(upload_sort_list, key=lambda torrent: torrent.chinese, reverse=True)
        return cn_sort_list

    def has_chinese(self, title: str):
        has_chinese = False
        for keyword in self.cn_keywords:
            if title.find(keyword) > -1:
                has_chinese = True
                break
        return has_chinese

    @staticmethod
    def get_site(site_id):
        site_list = mbot_api.site.list()
        for site in site_list:
            if site_id == site.site_id:
                return site
        return None

    def download_torrent(self, code, torrent: Torrent):
        site_id = torrent.site_id
        site = self.get_site(site_id)
        if site:
            cookie = site.cookie
            domain = site.domain
            user_agent = site.user_agent
            cookie_dict = str_cookies_to_dict(cookie)
            headers = {'cookie': cookie, 'Referer': domain}
            if user_agent:
                headers['User-Agent'] = user_agent
            res = requests.get(torrent.download_url, cookies=cookie_dict, headers=headers)
            torrent_path = f'/data/xx_torrents/{code}.torrent'
            with open(torrent_path, 'wb') as torrent:
                torrent.write(res.content)
                torrent.flush()
            return torrent_path
