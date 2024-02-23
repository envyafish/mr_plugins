import threading

from plugins.xx.db import get_course_db, get_teacher_db, get_config_db
from plugins.xx.crawler import JavLibrary, JavBus
from plugins.xx.download_client import DownloadClient
from plugins.xx.fsm import FSM, MediaType
from plugins.xx.models import Teacher, Course
from plugins.xx.notify import Notify
from plugins.xx.site import Site
from plugins.xx.logger import Logger

course_db = get_course_db()
teacher_db = get_teacher_db()
config_db = get_config_db()


def check_config():
    config = config_db.get_config()
    if not config:
        Logger.error("配置没有初始化")
        return False
    if not config.site_id:
        Logger.error("搜索站点没有配置")
        return False
    if not config.download_path and not config.category:
        Logger.error("下载路径没有配置")
        return False
    return True


def sync_new_course(teacher: Teacher):
    t = threading.Thread(target=sync_new_course_thread, args=(teacher,))
    t.start()


def sync_new_course_thread(teacher: Teacher):
    config = config_db.get_config()
    library, bus = get_crawler()
    notify = Notify(config)
    course_code_list = bus.crawling_teacher_courses(teacher.code, teacher.limit_date)
    Logger.error(f"{teacher.name}在{teacher.limit_date}之后教授的课程有如下:\n{','.join(course_code_list)}")
    if course_code_list:
        for code in course_code_list:
            row = course_db.get_course_by_code(code)
            if row and row.status > 0:
                continue
            #     手动取消订阅的课程,在更新老师课程的时候 不会再次订阅
            if row and row.status == -1:
                continue
            if row and row.status == 0:
                row.status = 1
                row.sub_type = 2
                row = course_db.update_course(row)
                download_once(row)
                notify.push_new_course(teacher=teacher, course=row)
                continue
            course = bus.search_code(code)
            if course:
                casts = course.casts
                cast_list = casts.split(',')
                if len(cast_list) > 4:
                    Logger.info(f"课程{course.code}同时存在超过4名老师,小明无法承受,所以跳过订阅此课程")
                    continue
                course.status = 1
                course.sub_type = 2
                course = course_db.add_course(course)
                download_once(course)
                notify.push_new_course(teacher=teacher, course=course)


def get_crawler():
    proxies = {}
    library: JavLibrary = JavLibrary(ua='', cookie='', proxies=proxies)
    bus = JavBus(ua='', cookie='', proxies=proxies)
    config = config_db.get_config()
    if config:
        if config.proxy:
            proxies = {
                'https': config.proxy,
                'http': config.proxy
            }
        library = JavLibrary(ua=config.user_agent, cookie=config.library_cookie, proxies=proxies)
        bus = JavBus(ua=config.user_agent, cookie=config.bus_cookie, proxies=proxies)
    return library, bus


# 避免批量操作
def download_once(course):
    t = threading.Thread(target=download_thread, args=(course,))
    t.start()


def download_thread(course):
    row = course_db.get_course_by_primary(course.id)
    if row:
        config = config_db.get_config()
        site = Site(config)
        client = DownloadClient(config)
        notify = Notify(config)
        torrent = site.get_remote_torrent(course.code)
        if torrent:
            torrent_path = site.download_torrent(course.code, torrent)
            if torrent_path:
                download_status = client.download_from_file(torrent_path, config.download_path, config.category)
                if download_status:
                    course.status = 2
                    course_db.update_course(course)
                    notify.push_downloading(course, torrent)
                else:
                    Logger.error(f"下载课程:添加番号{course.code}下载失败")
        else:
            if config.fsm_token:
                Logger.error("开始从飞天拉面神教搜索可下载的课程")
                fsm = FSM(config.fsm_token, config.fsm_passkey, config.fsm_salt)
                data = fsm.search(type=MediaType.AV, keyword=course.code, page=1)
                list = data['data']['list']
                if list:
                    tid = list[0]['tid']
                    Logger.error(f"飞天拉面神教搜索到番号{course.code}的课程,开始下载")
                    torrent_path = fsm.download_torrent(tid, course.code)
                    if torrent_path:
                        download_status = client.download_from_file(torrent_path, config.download_path, config.category)
                        if download_status:
                            course.status = 2
                            course_db.update_course(course)
                            notify.push_downloading(course, torrent)
                        else:
                            Logger.error(f"下载课程:添加番号{course.code}下载失败")

    else:
        Logger.error(f"下载课程:番号{course.code}不存在数据库")


def sub_top20():
    library, bus = get_crawler()
    top20_codes = library.crawling_top20(1)
    for code in top20_codes:
        course = course_db.get_course_by_code(code)
        if course:
            if course.status == 0:
                course.status = 1
                course.sub_type = 3
                course_db.update_course(course)
        else:
            course = bus.search_code(code)
            if course:
                course.status = 1
                course.sub_type = 3
                course_db.add_course(course)
