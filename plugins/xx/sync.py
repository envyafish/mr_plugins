import os

from plugins.xx.common import get_crawler
from plugins.xx.logger import Logger
from plugins.xx.db import get_course_db


def command(path):
    videos = collect_videos(path)
    sync(videos)


def collect_videos(path):
    videos = []
    if os.path.isdir(path):
        for file in os.listdir(path):
            videos.extend(collect_videos(os.path.join(path, file)))
        return videos
    elif os.path.splitext(path)[1].lower() in [
        ".mp4",
        ".avi",
        ".rmvb",
        ".wmv",
        ".mov",
        ".mkv",
        ".webm",
        ".iso",
        ".mpg",
        ".m4v",
    ]:
        return [path]
    else:
        return []


def sync(videos):
    course_db = get_course_db()
    library, bus = get_crawler()
    for video in videos:
        filename = os.path.basename(video)
        code = filename.split('.')[-2]
        code = code.replace('-C', '')
        code = code.replace('-cd1','')
        code = code.replace('-cd2','')
        code = code.replace('-cd3','')
        code = code.replace('-cd4','')
        code = code.replace('-cd5','')
        code = code.replace('-cd6','')
        code = code.replace('-cd7','')
        code = code.replace('-cd8','')
        code = code.replace('-cd9','')
        code = code.replace('-无码流出','')
        code = code.replace('726ANKK','ANKK')
        code = code.replace('420POW','POW')
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
