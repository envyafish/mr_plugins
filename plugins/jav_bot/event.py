import random
import time
from typing import Dict, Any
from mbot.core.plugins import plugin, PluginMeta

from .core import Core
from .core import Config

config: Config = None
jav_bot: Core = None


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, conf: Dict[str, Any]):
    global config, jav_bot
    config = Config(conf)
    jav_bot = Core(config)
    jav_bot.course_db.create_table()
    jav_bot.teacher_db.create_table()
    jav_bot.download_record_db.create_table()
    jav_bot.after_rebot()


@plugin.config_changed
def config_changed(conf: Dict[str, Any]):
    global config, jav_bot
    config = Config(conf)
    jav_bot = Core(config)


@plugin.task('task', '定时任务', cron_expression='0 22 * * *')
def task():
    time.sleep(random.randint(1, 3600))
    jav_bot.update_top_rank()
    jav_bot.update_teacher()


@plugin.task('auto_upgrade', '自动更新', cron_expression='5 * * * *')
def upgrade_task():
    jav_bot.upgrade_plugin()


def reorganize(src):
    jav_bot.reorganize(src)


def update_top_rank():
    jav_bot.update_top_rank()


def upgrade_plugin():
    jav_bot.upgrade_plugin()


def download_by_codes(code_list):
    jav_bot.download_by_codes(code_list)


def add_actor(keyword, start_date):
    jav_bot.add_actor(keyword, start_date)
