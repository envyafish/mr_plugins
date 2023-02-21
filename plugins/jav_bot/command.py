import datetime
import os

from mbot.openapi import mbot_api
import logging
from mbot.core.params import ArgSchema, ArgType
from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from .event import *

server = mbot_api
_LOGGER = logging.getLogger(__name__)
namespace = os.path.split(os.path.abspath(os.path.dirname(__file__)))[1]
file_name = os.path.split(__file__)[1]
file_name = file_name[0:len(file_name) - 3]
module_name = f"{namespace}.{file_name}"



def get_base_commands():
    commands = [
        {'name': '更新TOP20榜单', 'value': 'update_rank'},
        {'name': '插件升级,完成后需重启容器', 'value': 'upgrade_plugin'},
    ]
    return commands


@plugin.command(name='mdc', title='一键刮削', desc='刮削目录为插件中配置的目录', icon='', run_in_background=True)
def mdc(
        ctx: PluginCommandContext,
        path: ArgSchema(ArgType.String, '刮削路径', '')):
    reorganize(path)
    _LOGGER.info("一键刮削完成")
    return PluginCommandResponse(True, '')


@plugin.command(name='base_command', title='学习工具:更新', desc='', icon='', run_in_background=True)
def base_command(ctx: PluginCommandContext,
                 command: ArgSchema(ArgType.Enum, '选择操作', '', enum_values=get_base_commands, multi_value=False)):
    if command == 'update_rank':
        update_top_rank()
    if command == 'upgrade_plugin':
        upgrade_plugin()
    _LOGGER.info("更新完成")
    return PluginCommandResponse(True, '')


@plugin.command(name='subscribe_command', title='学习工具:订阅', desc='', icon='', run_in_background=True)
def subscribe_command(
        ctx: PluginCommandContext,
        codes: ArgSchema(ArgType.String, '番号订阅', '输入番号,多个番号用英文逗号隔开,若订阅教师，以下两个参数必传',
                         required=False),
        keyword: ArgSchema(ArgType.String, '教师订阅-关键字', '输入教师姓名或是单人授课科目名', required=False),
        start_date: ArgSchema(ArgType.String, '教师订阅-时间限制', '日期格式务必准确,例如:2023-01-01', required=False)
):
    if codes:
        code_list = codes.split(',')
        download_by_codes(code_list)
    if keyword and start_date:
        try:
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
        except Exception as e:
            _LOGGER.error("日期格式错误")
            return
        add_actor(keyword, start_date)

    _LOGGER.info("订阅完成")
    return PluginCommandResponse(True, '')
