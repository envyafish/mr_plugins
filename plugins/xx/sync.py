import os
import re

from plugins.xx.common import get_crawler
from plugins.xx.logger import Logger
from plugins.xx.db import get_course_db
from plugins.xx.media_server import MediaServer


def command():
    videos = collect_videos()
    sync(videos)


def collect_videos():
    media_server = MediaServer()
    codes = media_server.get_codes()
    return codes


def sync(codes):
    course_db = get_course_db()
    library, bus = get_crawler()
    for code in codes:
        Logger.info(f"开始处理番号{code}")
        row = course_db.get_course_by_code(code)
        if row:
            row.status = 2
            course_db.update_course(row)
            Logger.info(f"数据库已存在番号{code},跳过")
            continue
        Logger.info(f"开始爬取番号{code}的信息")
        course = bus.search_code(code)
        if course:
            course.status = 2
            course.sub_type = 1
            Logger.info(f"保存番号{code}到数据库")
            course_db.add_course(course)
