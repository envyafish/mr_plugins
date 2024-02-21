import datetime
import json
import re

import requests
from pyquery import PyQuery as pq


# 获取文章列表
def get_article_list():
    url = 'https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum&__biz=Mzk0OTM5NDM2OQ==&album_id=2514923508611760129&count=10&is_reverse=1&uin=&key=&pass_ticket=&wxtoken=&devicetype=&clientversion=&__biz=Mzk0OTM5NDM2OQ%3D%3D&enterid=1707872626&appmsg_token=&x5=0&f=json'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }
    # 爬取文章列表
    response = requests.get(url, headers=headers)
    article_list = response.json()['getalbum_resp']['article_list']
    return article_list


def get_latest_article(article_list: list):
    # 获取最新一篇文章
    latest_article = article_list[0]
    return latest_article


def get_stream_media_list(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }
    # 爬取文章列表
    response = requests.get(url, headers=headers)

    doc = pq(response.text)
    content = doc('#js_content')
    p_list = content.children()
    p_list = list(p_list.items())
    sub_head(p_list)
    p_list = sub_foot(p_list)
    stream_media_list = []
    # 将文章内容进行分组
    while p_list:
        article = get_article_content(p_list)
        if article:
            stream_media_list.append(article)
    return stream_media_list


def sub_head(p_list: list):
    while p_list:
        p = p_list[0]
        if p.text() and p.text()[0].isdigit():
            break
        if p.text():
            if not p.text()[0].isdigit():
                p_list.remove(p)
                continue
        else:
            p_list.remove(p)
            continue


def sub_foot(p_list: list):
    index = 0
    for p in p_list:
        #         判断p的子元素为section,返回index
        if p.text() and p.text()=='END':
            break
        index = index + 1
    #     删除p_list中index之后的元素
    p_list = p_list[:index]
    return p_list


def get_article_content(p_list: list):
    article = {}
    index = 0
    while p_list:
        p = p_list[0]
        if index == 0:
            title = p.text()
            info = extract_info(title)
            article['title'] = info[0]
            article['platform'] = info[1]
            article['rate'] = info[2]
            article['genre'] = info[3]
        else:
            if p('img'):
                article['img'] = p('img').attr('data-src')
            else:
                if p.text() and p.text()[0].isdigit():
                    break
                article['content'] = p.text()
        p_list.remove(p)
        index = index + 1
    return article


def extract_info(text):
    # 定义正则表达式模式
    title_pattern = r'：([^（]+)'
    platform_pattern = r'上线平台：([^）]+)'
    imdb_pattern = r'IMDB 评分：([\d.]+)'
    genre_pattern = r'([^、：]+)：'

    # 使用正则表达式进行匹配
    title_match = re.search(title_pattern, text)
    platform_match = re.search(platform_pattern, text)
    imdb_match = re.search(imdb_pattern, text)
    genre_match = re.search(genre_pattern, text)

    # 提取标题
    title = title_match.group(1).strip() if title_match else None
    # 提取上线平台
    platform = platform_match.group(1).strip() if platform_match else None
    # 提取IMDB评分
    imdb_rating = imdb_match.group(1).strip() if imdb_match else None
    # 提取影片类型
    genre = genre_match.group(1).strip() if genre_match else None

    return title, platform, imdb_rating, genre


def get_stream_media():
    article_list = get_article_list()
    latest_article = get_latest_article(article_list)
    url = latest_article['url']
    # 时间戳转日期
    date_time = datetime.datetime.fromtimestamp(int(latest_article['create_time']))
    # 使用 strftime() 格式化日期
    date = date_time.strftime('%Y-%m-%d')
    stream_media_list = get_stream_media_list(url)
    return stream_media_list, date


# if __name__ == '__main__':
#     stream_media_list, date = get_stream_media()
#     for stream_media in stream_media_list:
#         print(stream_media)
