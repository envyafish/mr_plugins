import configparser
import datetime
import logging
import os
import random
import threading
import time
from typing import List, Dict, Any

from mbot.openapi import mbot_api

from .crawler import JavLibrary, MTeam, JavBus
from .models import Course, Teacher, DownloadRecord
from .plugin_tools import PluginTools
from .db import DownloadRecordDB, CourseDB, TeacherDB
from .organize import Organize, collect_videos
from .download_client import DownloadClient

_LOGGER = logging.getLogger(__name__)


class Config:
    path: str
    proxy: str
    proxies: dict = {}
    jav_cookie: str
    jav_bus_cookie: str
    ua: str
    category: str
    uid: List
    client_name: str
    need_mdc: bool
    pic_url: str
    hard_link_dir: str
    fail_folder: str

    def __init__(self, config: Dict[str, Any]) -> None:
        self.path = config.get('path')
        self.proxy = config.get('proxy')
        if config.get('proxy'):
            self.proxies = {
                'http': config.get('proxy'),
                'https': config.get('proxy')
            }
        self.jav_cookie = config.get('jav_cookie')
        self.jav_bus_cookie = config.get('jav_bus_cookie')
        self.ua = config.get('ua')
        self.category = config.get('category')
        self.uid = config.get('uid')
        self.message_to_uid = config.get('uid')
        self.client_name = config.get('client_name')
        self.need_mdc = config.get('need_mdc')
        self.pic_url = config.get('pic_url')
        self.hard_link_dir = config.get('hard_link_dir')
        self.fail_folder = config.get('fail_folder')
        self.create_config_ini()

    def create_config_ini(self):
        conf = configparser.ConfigParser()
        conf['common'] = {'target_folder': self.hard_link_dir, 'fail_folder': self.fail_folder}
        conf['proxy'] = {'proxy': self.proxy}
        config_ini_path = f'{os.path.abspath(os.path.dirname(__file__))}/config.ini'
        if os.path.exists(config_ini_path):
            os.remove(config_ini_path)
        with open(config_ini_path, 'w') as cfg:
            conf.write(cfg)


class Message:
    uids: List
    pic_url: str

    def __init__(self, uids, pic_url):
        self.uids = uids
        self.pic_url = pic_url

    def push_msg(self, title, content):
        for uid in self.uids:
            mbot_api.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                'title': title,
                'a': content,
                'link_url': '',
                'pic_url': self.pic_url
            }, to_uid=uid)

    def push_new_code_msg(self, code_list):
        title = '有新的学习资料进入想看列表'
        content = ','.join(code_list)
        self.push_msg(title, content)

    # 想要的科目开始下载
    def push_new_download_msg(self, code_list):
        title = '有新的学习资料开始下载'
        content = ','.join(code_list)
        self.push_msg(title, content)

    def push_downloaded(self, torrent_name):
        title = '有新的学习资料下载完成'
        self.push_msg(title, torrent_name)

    def push_upgrade_success(self, old_version, new_version, update_log):
        title = '日语学习工具已更新'
        content = f'当前版本:V.{old_version}\n' \
                  f'新版本:V.{new_version}\n' \
                  f'更新内容如下:\n' \
                  f'{update_log}\n' \
                  f'备注:更新内容已下载到本地,新版本需在重启容器之后生效'
        self.push_msg(title, content)


def has_number(keyword):
    for s in keyword:
        if s.isdigit():
            return True
    else:
        return False


def get_true_code(input_code: str):
    code_list = input_code.split('-')
    code = ''.join(code_list)
    length = len(code)
    index = length - 1
    num = ''
    all_number = '0123456789'
    while index > -1:
        s = code[index]
        if s not in all_number:
            break
        num = s + num
        index = index - 1
    prefix = code[0:index + 1]
    return (prefix + '-' + num).upper()


class Core:
    config: Config
    download_client: DownloadClient
    course_db: CourseDB
    teacher_db: TeacherDB
    download_record_db: DownloadRecordDB
    organize: Organize
    message: Message
    jav_library: JavLibrary
    m_team: MTeam
    jav_bus: JavBus
    jav_bot_plugin_path: str = os.path.abspath(os.path.dirname(__file__))
    plugin_utils: PluginTools

    def __init__(self, conf: Config):
        self.config = conf
        self.download_client = DownloadClient(conf.client_name)
        self.course_db = CourseDB()
        self.teacher_db = TeacherDB()
        self.download_record_db = DownloadRecordDB()
        self.organize = Organize()
        self.message = Message(conf.uid, conf.pic_url)
        self.jav_library = JavLibrary(conf.jav_cookie, conf.ua, conf.proxies)
        self.m_team = MTeam()
        self.jav_bus = JavBus(conf.jav_bus_cookie, conf.ua, conf.proxies)
        self.plugin_utils = PluginTools(conf.proxies)

    def get_core(self):
        return self

    def after_rebot(self):
        _LOGGER.info("重启服务器之后,将还在下载跟下载完成没有刮削的纳入监听")
        download_records = self.download_record_db.list(download_status=0)
        for record in download_records:
            torrent_file_hash = record.torrent_hash
            t = threading.Thread(target=self.wait_torrent_downloaded, args=(torrent_file_hash,))
            t.start()

    def wait_torrent_downloaded(self, torrent_file_hash: str):
        torrent = self.download_client.get_torrent_by_hash(torrent_file_hash=torrent_file_hash)
        if not torrent:
            _LOGGER.info(f"hash值{torrent_file_hash}的种子可能已被移出下载器,监听程序结束")
            download_record = self.download_record_db.get_by_torrent_hash(torrent_file_hash)
            if download_record:
                download_record.download_status = -1
                download_record.completed_time = datetime.datetime.now()
                self.download_record_db.update(download_record)
            return
        progress = torrent.progress
        _LOGGER.info(f"种子名:{torrent.name}当前的下载进度:{progress}%")
        if int(progress == 100):
            download_record = self.download_record_db.get_by_torrent_hash(torrent_file_hash)
            download_record.download_status = 1
            download_record.completed_time = datetime.datetime.now()
            self.download_record_db.update(download_record)
            self.message.push_downloaded(torrent.name)
            _LOGGER.info(f"种子名:{torrent.name}下载完成,开始执行MDC")
            self.organize.organize(torrent.content_path)
        else:
            time.sleep(45)
            self.wait_torrent_downloaded(torrent_file_hash)

    def update_top_rank(self):
        new_code_list = self.save_new_code()
        if new_code_list:
            self.message.push_new_code_msg(new_code_list)
        download_code_list = self.fetch_un_download_code()
        if download_code_list:
            self.message.push_new_download_msg(download_code_list)
        _LOGGER.error("更新榜单完成")

    def save_new_code(self):
        crawling_course_list = self.jav_library.crawling_top20()
        _LOGGER.info(f"当前TOP:{[crawling_course['code'] for crawling_course in crawling_course_list]}")
        if not crawling_course_list:
            _LOGGER.error('爬取jav失败')
            return
        new_course = []
        for crawling_course in crawling_course_list:
            code = crawling_course['code']
            course = self.course_db.get_by_code(code)
            code_exist = self.find_video_from_library(code)
            if not course:
                course = Course({
                    'code': code,
                    'status': 0
                })
                course = self.course_db.insert(course)
                self.fill_course_info(course)
                if not code_exist:
                    new_course.append(code)
                else:
                    _LOGGER.info(f"媒体库已存在番号{code},将标记为下载完成")
                    course.status = 1
                    self.course_db.update(course)
            else:
                if course.status == 0:
                    if code_exist:
                        _LOGGER.info(f"媒体库已存在番号{code},将标记为下载完成")
                        course.status = 1
                        self.course_db.update(course)
        return new_course

    def find_video_from_library(self, code: str):
        videos = collect_videos(self.config.hard_link_dir)
        video_name_list = [os.path.split(video)[1] for video in videos]
        for video_name in video_name_list:
            if video_name.startswith(code):
                return True
        return False

    def fill_course_info(self, course: Course):
        crawler_detail = self.jav_bus.crawling_detail(course.code)
        if not crawler_detail:
            return
        course.overview = crawler_detail.title
        course.tags = ','.join(crawler_detail.tags)
        course.casts = ','.join(crawler_detail.casts)
        course.duration = crawler_detail.length
        course.poster_url = crawler_detail.poster.replace(self.jav_bot_plugin_path, '')
        course.banner_url = crawler_detail.banner.replace(self.jav_bot_plugin_path, '')
        course.release_date = crawler_detail.release_date
        self.course_db.update(course)

    def deal_un_download_course(self, course):
        code = course.code
        torrents = self.m_team.crawling_torrents(code)
        if torrents:
            torrent = self.m_team.get_best_torrent(torrents)
            if torrent:
                torrent_path = self.m_team.download_torrent(code, torrent['download_url'])
                torrent_in_download = self.download_client.get_torrent_by_torrent_file(torrent_file=torrent_path)
                if not torrent_in_download:
                    res = self.download_client.download(torrent_path, save_path=self.config.path,
                                                        category=self.config.category)
                    if res:
                        course.status = 1
                        self.course_db.update(course)
                        self.monitor_download_progress(course.id, torrent_path, 1)
                        return code
                    else:
                        _LOGGER.error(f'{code}添加种子失败')
                        return None
                else:
                    course.status = 1
                    self.course_db.update(course)
                    self.monitor_download_progress(course.id, torrent_path, 1)
                    _LOGGER.info(f"{code}已存在下载器中,标记为已下载")
                    return code
            else:
                _LOGGER.info(f"{code}没有有效的种子")
                return None
        else:
            _LOGGER.info(f"{code}尚无资源")
            return None
        return None

    def fetch_un_download_code(self):
        courses = self.course_db.list(status=0)
        _LOGGER.info(f"尚未下载的科目:{[course.code for course in courses]}")
        download_chapter = []
        for index, course in enumerate(courses):
            code = self.deal_un_download_course(course)
            if code:
                download_chapter.append(code)
            if index < len(courses) - 1:
                _LOGGER.info("等待10-20S继续操作")
                time.sleep(random.randint(10, 20))
        return download_chapter

    def monitor_download_progress(self, course_id, torrent_path, retry_time):
        if self.config.need_mdc:
            if retry_time > 3:
                _LOGGER.info(f"重试三次没有取到种子,放弃监听{torrent_path}的种子")
                return
            torrent = self.download_client.get_torrent_by_torrent_file(torrent_file=torrent_path)
            _LOGGER.info(f"开启监控种子:{torrent.name}的下载进度")
            if torrent:
                download_record = self.download_record_db.get_by_torrent_hash(torrent.hash)
                if not download_record:
                    download_record = DownloadRecord({
                        'course_id': course_id,
                        'torrent_name': torrent.name,
                        'torrent_hash': torrent.hash,
                        'torrent_path': torrent_path,
                        'content_path': torrent.content_path,
                        'download_status': 0
                    })
                    self.download_record_db.insert(download_record)
                else:
                    download_record.course_id = course_id
                    download_record.torrent_name = torrent.name
                    download_record.torrent_path = torrent_path
                    download_record.content_path = torrent.content_path
                    download_record.download_status = 0
                    self.download_record_db.update(download_record)
                torrent_file_hash = torrent.hash
                t = threading.Thread(target=self.wait_torrent_downloaded, args=(torrent_file_hash,))
                t.start()
            else:
                _LOGGER.info(f"通过hash没取到种子,等待5S重试")
                time.sleep(5)
                self.monitor_download_progress(torrent_path, retry_time + 1)

    def download_by_codes(self, code_list: List):
        for index, code in enumerate(code_list):
            if not code:
                continue
            self.download_by_code(code)
            if index < len(code_list) - 1:
                _LOGGER.info("等待10-20S继续操作")
                time.sleep(random.randint(10, 20))

    def download_by_code(self, code: str):
        code = get_true_code(code)
        course = self.course_db.get_by_code(code)
        if not course:
            course = Course({
                'code': code,
                'status': 0
            })
            course = self.course_db.insert(course)
            self.fill_course_info(course)
            self.message.push_new_code_msg([code])
        if course.status == 1:
            _LOGGER.info(f'你已经下载过番号{code}')
            return
        if self.find_video_from_library(code):
            course.status = 1
            self.course_db.update(course)
            _LOGGER.info(f'媒体库已存在番号{code}')
            return
        self.deal_un_download_course(course)

    def upgrade_plugin(self):
        _LOGGER.info("jav_bot开始检查更新")
        new_version_download_url = self.plugin_utils.check_update()
        if new_version_download_url:
            _LOGGER.info("jav_bot检测到新的版本,开始执行更新")
            old_manifest = self.plugin_utils.get_manifest()
            old_version = old_manifest['version']
            if self.plugin_utils.download_plugin(new_version_download_url, 1):
                new_manifest = self.plugin_utils.get_manifest()
                new_version = new_manifest['version']
                update_log = new_manifest['update_log']
                _LOGGER.info(f"执行更新成功:当前版本{new_version}")
                self.message.push_upgrade_success(old_version, new_version, update_log)
            else:
                _LOGGER.info("执行更新失败")

    def reorganize(self, src):
        self.organize.organize_all(src)

    def add_actor(self, keyword: str, start_date):
        if len(keyword) == len(keyword.encode()) and has_number(keyword):
            true_code = get_true_code(keyword)
            teacher_grab = self.jav_bus.crawling_by_code(true_code)
        else:
            teacher_grab = self.jav_bus.crawling_by_name(keyword)
        flag = False
        if teacher_grab:
            teacher_code = teacher_grab['teacher_code']
            name = teacher_grab['teacher_name']
            teacher = self.teacher_db.get_by_code(teacher_code)
            start_date_str = f"{start_date} 00:00:00"
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
            if teacher:
                flag = False
                teacher.start_date = start_date
                self.teacher_db.update(teacher)
                _LOGGER.info(f"{name}已存在订阅的演员列表中")
            else:
                flag = True
                teacher = Teacher({
                    'name': name,
                    'code': teacher_code,
                    'start_date': start_date_str
                })
                self.teacher_db.insert(teacher)
                _LOGGER.info(f"{name}订阅完成")
            code_list = self.jav_bus.crawling_actor(teacher_code, start_date)
            if code_list:
                code_list = [item['code'] for item in code_list]
                self.download_by_codes(code_list)
        return flag

    def update_teacher(self):
        teacher_list = self.teacher_db.list()
        for teacher in teacher_list:
            code_list = self.jav_bus.crawling_actor(teacher.code, teacher.start_date)
            code_list = [item['code'] for item in code_list]
            self.download_by_codes(code_list)
