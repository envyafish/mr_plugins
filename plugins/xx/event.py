import os.path
import shutil
from typing import Dict, Any

from mbot.core.plugins import plugin, PluginMeta, PluginContext
from mbot.openapi import mbot_api
from plugins.xx.logger import Logger
from plugins.xx.db import get_course_db, get_teacher_db, get_config_db
from plugins.xx.download_client import DownloadClient
from plugins.xx.notify import Notify
from plugins.xx.site import Site
from plugins.xx.common import sync_new_course, check_config

course_db = get_course_db()
teacher_db = get_teacher_db()
config_db = get_config_db()


def link_resource():
    if os.path.exists('/app/frontend/static/assets/xx'):
        shutil.rmtree('/app/frontend/static/assets/xx')
    shutil.copytree('/data/plugins/xx/webui/static/assets/xx', '/app/frontend/static/assets/xx', symlinks=True)
    if os.path.exists('/app/frontend/templates/xx/index.html'):
        os.remove('/app/frontend/templates/xx/index.html')
    if not os.path.exists('/app/frontend/templates/xx'):
        os.mkdir('/app/frontend/templates/xx')
    os.symlink('/data/plugins/xx/webui/index.html', '/app/frontend/templates/xx/index.html')


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    link_resource()
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/course')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/teacher')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/rank')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/subscribe')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/options')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/index')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/sites')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/users')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/download-client')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/channel')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/media-path')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/config/get')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/config/set')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/course/list')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/course/add')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/course/download')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/course/delete')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/teacher/add')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/teacher/list')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/teacher/delete')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/rank/list')
    mbot_api.auth.add_permission([1, 2], '/api/plugins/xx/complex/search')


@plugin.on_event(bind_event=['SiteListComplete'], order=1)
def on_site_list_complete(ctx: PluginContext, event_type: str, data: Dict):
    if not check_config():
        return
    course_list = course_db.list_course(status=1)
    config = config_db.get_config()
    site = Site(config)
    client = DownloadClient(config)
    notify = Notify(config)
    if course_list:
        for course in course_list:
            torrent = site.get_local_torrent(course.code)
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


@plugin.task('sync_new_course', '同步教师的新课程', cron_expression='0 20 * * *')
def sync_new_course_task():
    if not check_config():
        return
    teachers = teacher_db.list_teacher()
    if teachers:
        for teacher in teachers:
            sync_new_course(teacher)
