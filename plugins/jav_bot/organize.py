import configparser
import datetime
import logging
import os
import stat
import sys

_LOGGER = logging.getLogger(__name__)


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


def get_highest_quality_videos(videos):
    max_size = 0
    max_size_video = None
    for path in videos:
        size = os.path.getsize(path)
        if size > max_size:
            max_size = size
            max_size_video = path
    return max_size_video


def is_hardlink(src, dst):
    s1 = os.stat(src)
    s2 = os.stat(dst)
    return (s1[stat.ST_INO], s1[stat.ST_DEV]) == (s2[stat.ST_INO], s2[stat.ST_DEV])


def find_hard_link(src, videos):
    for video in videos:
        if is_hardlink(src, video):
            return True
    return False


def get_organize_tool():
    if 'plugins.mdc_mbot_plugin' not in sys.modules:
        _LOGGER.error("mdc模块尚未安装，无法进行刮削整理")
        return None
    from plugins.mdc_mbot_plugin import mdc_main
    _LOGGER.error("mdc模块已安装")
    return mdc_main


class Organize:
    config_path: str = f'{os.path.abspath(os.path.dirname(__file__))}/config.ini'
    organize_success: str
    organize_fail: str
    organize_tool: None

    def __init__(self):
        conf = configparser.ConfigParser()
        conf.read(self.config_path)
        self.organize_success = conf.get('common', 'target_folder')
        self.organize_fail = conf.get('common', 'fail_folder')
        self.organize_tool = get_organize_tool()

    def organize(self, course_path: str):
        if self.organize_tool:
            _LOGGER.info(f"开始整理学习资料{course_path}")
            courses = collect_videos(course_path)
            course = get_highest_quality_videos(courses)
            try:
                self.organize_tool(course, self.config_path)
            except Exception as e:
                self.write_fail_log(fail_courses=[course])

    def organize_all(self, src: str):
        if not os.path.isdir(src):
            self.organize(src)
        else:
            if self.organize_tool:
                _LOGGER.info(f"开始整理目录{src}下的学习资料")
                courses = collect_videos(src)
                hard_link_courses = collect_videos(self.organize_success)
                fail_courses = []
                for course in courses:
                    if find_hard_link(course, hard_link_courses):
                        _LOGGER.info(f"科目{course}已经整理,跳过整理")
                        continue
                    if os.path.getsize(course) < 200 * 1024 * 1000:
                        _LOGGER.info(f"科目{course}文件体积小于200M,跳过整理")
                        continue
                    try:
                        self.organize_tool(course, self.config_path)
                        _LOGGER.info(f"科目{course}整理完成")
                    except Exception as e:
                        _LOGGER.error(f"科目{course}整理失败")
                        fail_courses.append(course)
                        continue
                self.write_fail_log(fail_courses)

    def write_fail_log(self, fail_courses):
        if self.organize_fail:
            _LOGGER.info("开始写入整理失败的科目")
            if not os.path.exists(self.organize_fail):
                os.makedirs(self.organize_fail)
            now_str = datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分%S秒')
            note = open(f'{self.organize_fail}/{now_str}.txt', mode='a')
            for course in fail_courses:
                note.writelines(f"{course}\n")
            note.close()
