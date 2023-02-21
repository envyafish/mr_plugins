import gc
import os
import sys

from mbot.core.plugins.pluginloader import PluginLoader
from mbot.core import MovieBot
import logging

_LOGGER = logging.getLogger(__name__)


def get_movie_bot():
    object_list = gc.get_objects()
    for item in object_list:
        if isinstance(item, MovieBot):
            return item


movie_bot = get_movie_bot()
namespace = 'plugins'
plugin_folder = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
plugin_loader = PluginLoader(plugin_folder=plugin_folder, namespace=namespace, mbot=movie_bot)
mr_tools_path = os.path.abspath(os.path.dirname(__file__))


def install(download_url):
    # 安装
    plugin_path = plugin_loader.install(download_url=download_url)
    # 加载
    load(plugin_path)
    load(mr_tools_path)


def upgrade(plugin_name, download_url):
    plugin_loader.uninstall(plugin_name, delete_config=False)
    _LOGGER.info("卸载完成")
    plugin_path = plugin_loader.install(download_url=download_url)
    _LOGGER.info(f"插件路径:{plugin_path}")
    _LOGGER.info(f"开始加载插件")
    load(plugin_path)


def load(plugin_path):
    mod_name = os.path.split(plugin_path)[-1]
    full_mod_name = f'{namespace}.{mod_name}'
    for module in list(sys.modules.keys()):
        if module.startswith(full_mod_name):
            sys.modules.pop(module)
    plugin_loader.setup(plugin_path)


def list_plugins():
    plugins = movie_bot.plugins
    plugin_list = [plugins[plugin_name] for plugin_name in plugins]
    plugin_enum = [
        {'name': plugin.manifest.title, 'value': {'plugin_path': plugin.plugin_folder, 'plugin_name': plugin.name}} for
        plugin in plugin_list]
    return plugin_enum


def list_task():
    tasks = movie_bot.task_manager.get_tasks()
    task_enum = [{'name': task.desc, 'value': task.cron_expression} for task in tasks]
    return task_enum
