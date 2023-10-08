import os
from typing import List

import requests
from pyquery import PyQuery as pq

from plugins.xx.logger import Logger
from plugins.xx.exceptions import CloudFlareError
from plugins.xx.utils import *
from plugins.xx.models import Course, Teacher


class JavLibrary:
    host: str = 'https://www.javlibrary.com'
    top20_url: str = f'{host}/cn/vl_mostwanted.php?page='
    cookie: str
    ua: str
    proxies: dict
    cookie_dict: dict
    headers: dict

    def __init__(self, cookie: str = '', ua: str = '', proxies: dict = None):
        self.cookie = cookie
        self.ua = ua
        self.proxies = proxies
        self.cookie_dict = str_cookies_to_dict(cookie)
        self.headers = {'cookie': cookie, 'Referer': self.host}
        if ua:
            self.headers['User-Agent'] = ua

    def crawling_top20(self, page):
        code_list = []
        res = requests.get(url=f'{self.top20_url}{page}', proxies=self.proxies, cookies=self.cookie_dict,
                           headers=self.headers, allow_redirects=False)
        doc = pq(res.text)
        page_title = doc('head>title').text()
        if page_title.startswith('最想要的影片'):
            videos = doc('div.video>a').items()
            if videos:
                for video in videos:
                    code = video('a div.id').text()
                    code_list.append(code)
                return code_list
        if page_title.startswith('Just a moment'):
            raise CloudFlareError
        return []


class JavBus:
    hosts: []
    rotate_index = 0
    cookie: str
    ua: str
    proxies: dict
    cookie_dict: dict
    headers: dict

    def __init__(self, cookie: str = '', ua: str = '', proxies: dict = None):
        with open(os.path.join(os.path.dirname(__file__), 'mirror_sites.txt'), 'r') as f:
            self.hosts = f.read().splitlines()
        self.cookie = cookie
        self.ua = ua
        self.proxies = proxies
        if 'existmag' not in self.cookie:
            self.cookie = f"existmag=all; {self.cookie}"
        self.cookie = self.cookie.replace('existmag=mag', 'existmag=all')
        self.cookie_dict = str_cookies_to_dict(self.cookie)
        self.headers = {'cookie': self.cookie, 'Referer': self.hosts[0]}
        if ua:
            self.headers['User-Agent'] = ua

    # def rotate_host(self) -> str:
    #     current_index = self.rotate_index
    #     if self.rotate_index == len(self.hosts) - 1:
    #         self.rotate_index = 0
    #     else:
    #         self.rotate_index = self.rotate_index + 1
    #     return self.hosts[current_index]

    def search_code(self, code):
        for host in self.hosts:
            try:
                url = f"{host}/{code}"
                res = requests.get(url=url, proxies=self.proxies, headers=self.headers, cookies=self.cookie_dict,
                                   allow_redirects=False)
                doc = pq(res.text)
                page_title = doc('head>title').text()
                if page_title.startswith(code):
                    sample_img_elements = doc('a.sample-box')
                    sample_img_list = []
                    for img in sample_img_elements.items():
                        sample_img_list.append(img.attr('href'))
                    still_photo = ','.join(sample_img_list)
                    info = doc('div.info')
                    if info:
                        release_date = ''
                        duration = ''
                        producer = ''
                        publisher = ''
                        series = ''
                        genre_list = ''
                        cast_list = ''
                        title = doc('h3').text()
                        release_date_element = info('span:Contains("發行日期:")')
                        duration_element = info('span:Contains("長度:")')
                        producer_element = info('span:Contains("製作商:")')
                        publisher_element = info('span:Contains("發行商:")')
                        series_element = info('span:Contains("系列:")')
                        genre_elements = info('span.genre>label>a')
                        cast_elements = info('div.star-box>li>div.star-name>a')
                        banner = doc('a.bigImage>img').attr('src')
                        poster = banner.replace('cover', 'thumb').replace('_b', '')
                        if release_date_element:
                            release_date = release_date_element.parent().contents()[1].strip()
                        if duration_element:
                            duration = duration_element.parent().contents()[1].strip().replace('分鐘', '')
                        if producer_element:
                            producer = producer_element.parent()('a').text().strip()
                        if publisher_element:
                            publisher = publisher_element.parent()('a').text().strip()
                        if series_element:
                            series = series_element.parent()('a').text().strip()
                        if genre_elements:
                            genre_list = [item.text() for item in genre_elements.items()]
                        if cast_elements:
                            cast_list = [item.attr('title') for item in cast_elements.items()]
                        course = Course(
                            {'code': code, 'title': title, 'release_date': release_date, 'duration': duration,
                             'producer': producer, 'publisher': publisher,
                             'series': series, 'genres': ','.join(genre_list), 'casts': ','.join(cast_list),
                             'poster': poster, 'banner': banner, 'still_photo': still_photo})
                        return course
                return None
            except:
                Logger.error(f"访问{host}失败")
                continue
        return None

    # def search_teacher(self, keyword):
    #     if len(keyword) == len(keyword.encode()) and has_number(keyword):
    #         true_code = get_true_code(keyword)
    #         teacher_code_list = self.get_teachers(true_code)
    #         teacher_num = len(teacher_code_list)
    #         if teacher_num != 1:
    #             return None
    #         teacher_code = teacher_code_list[0]
    #     else:
    #         teacher_code = self.search_by_name(keyword)
    #     if teacher_code:
    #         teacher = self.crawling_teacher(teacher_code)
    #         return teacher
    #     return None

    def crawling_teacher(self, teacher_code):
        for host in self.hosts:
            try:
                url = f"{host}/star/{teacher_code}"
                res = requests.get(url=url, proxies=self.proxies, headers=self.headers, cookies=self.cookie_dict,
                                   allow_redirects=False)
                doc = pq(res.text)
                page_title = doc('head>title').text()
                if page_title.endswith('女優 - 影片'):
                    photo_info = doc('div.photo-info')
                    if photo_info:
                        photo = ''
                        name = ''
                        birth = ''
                        height = ''
                        cup = ''
                        bust = ''
                        waist = ''
                        hip = ''
                        photo_element = doc('div.photo-frame>img')
                        name_element = photo_info('span.pb10')
                        birth_element = photo_info('p:Contains("生日")')
                        height_element = photo_info('p:Contains("身高")')
                        cup_element = photo_info('p:Contains("罩杯")')
                        bust_element = photo_info('p:Contains("胸圍")')
                        waist_element = photo_info('p:Contains("腰圍")')
                        hip_element = photo_info('p:Contains("臀圍")')
                        if photo_element:
                            photo = photo_element.attr('src')
                        if name_element:
                            name = name_element.text()
                        if birth_element:
                            birth = birth_element.text().replace('生日:', '').strip()
                        if height_element:
                            height = height_element.text().replace('身高:', '').strip()
                        if cup_element:
                            cup = cup_element.text().replace('罩杯:', '').strip()
                        if bust_element:
                            bust = bust_element.text().replace('胸圍:', '').strip()
                        if waist_element:
                            waist = waist_element.text().replace('腰圍:', '').strip()
                        if hip_element:
                            hip = hip_element.text().replace('臀圍:', '').strip()
                        teacher = Teacher(
                            {'code': teacher_code, 'photo': photo, 'name': name, 'birth': birth, 'height': height,
                             'cup': cup,
                             'bust': bust, 'waist': waist, 'hip': hip})
                        return teacher
                return None
            except:
                Logger.error(f"访问{host}失败")
                continue
        return None

    def crawling_teacher_courses(self, teacher_code, limit_date):
        for host in self.hosts:
            try:
                start_date_timestamp = date_str_to_timestamp(limit_date)
                if not start_date_timestamp:
                    return None
                url = f"{host}/star/{teacher_code}"
                res = requests.get(url=url, proxies=self.proxies, headers=self.headers, cookies=self.cookie_dict,
                                   allow_redirects=False)
                doc = pq(res.text)
                page_title = doc('head>title').text()
                if page_title.endswith('女優 - 影片'):
                    movie_list = doc('a.movie-box')
                    code_list = []
                    for item in movie_list.items():
                        date_list = item('date')
                        info_list = [d.text() for d in date_list.items()]
                        code_list.append({'date': info_list[1], 'code': info_list[0]})
                    filter_list = list(
                        filter(
                            lambda x: date_str_to_timestamp(x['date']) >= start_date_timestamp and
                                      'VR' not in x['code'],
                            code_list))
                    return [item['code'] for item in filter_list]
                return []
            except:
                Logger.error(f"访问{host}失败")
                continue
        return []

    def get_teachers(self, code: str):
        for host in self.hosts:
            try:
                url = f"{host}/{code}"
                res = requests.get(url=url, proxies=self.proxies, headers=self.headers, cookies=self.cookie_dict,
                                   allow_redirects=False)
                doc = pq(res.text)
                page_title = doc('head>title').text()
                if page_title.startswith(code):
                    casts_list = doc('div.info>ul>div.star-box>li>div.star-name>a')
                    teacher_code_list = []
                    if casts_list:
                        for cast in casts_list.items():
                            url = cast.attr('href')
                            code_split_list = url.split('/')
                            code = code_split_list[len(code_split_list) - 1]
                            teacher_code_list.append(code)
                    return teacher_code_list
                return []
            except:
                Logger.error(f"访问{host}失败")
                continue
        return []

    def search_by_name(self, teacher_name):
        for host in self.hosts:
            try:
                url = f"{host}/searchstar/{teacher_name}"
                res = requests.get(url=url, proxies=self.proxies, headers=self.headers, cookies=self.cookie_dict,
                                   allow_redirects=False)
                doc = pq(res.text)
                page_title = doc('head>title').text()
                if page_title == '搜尋 - 女優列表 - JavBus - JavBus':
                    actors = doc('a.avatar-box')
                    teachers = [teacher for teacher in actors.items()]
                    if len(teachers) != 1:
                        return None
                    teacher_url = teachers[0].attr('href')
                    code_split_list = teacher_url.split('/')
                    code = code_split_list[len(code_split_list) - 1]
                    return code
                return None
            except:
                Logger.error(f"访问{host}失败")
                continue
        return None

    def search_all_by_name(self, teacher_name):
        for host in self.hosts:
            try:
                url = f"{host}/searchstar/{teacher_name}"
                res = requests.get(url=url, proxies=self.proxies, headers=self.headers, cookies=self.cookie_dict,
                                   allow_redirects=False)
                doc = pq(res.text)
                page_title = doc('head>title').text()
                teacher_code_list = []
                if page_title == '搜尋 - 女優列表 - JavBus - JavBus':
                    actors = doc('a.avatar-box')
                    for actor in actors.items():
                        teacher_url = actor.attr('href')
                        code_split_list = teacher_url.split('/')
                        code = code_split_list[len(code_split_list) - 1]
                        teacher_code_list.append(code)
                    return teacher_code_list
                return []
            except:
                Logger.error(f"访问{host}失败")
                continue
        return []
