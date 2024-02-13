from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
import logging

from .event import save_json
from .event import push_message
from .event import change_banner

server = mbot_api
_LOGGER = logging.getLogger(__name__)


@plugin.command(name='echo', title='初始化追剧日历数据', desc='订阅剧集越多，执行时间越长，请耐心等待', icon='Today', run_in_background=True)
def echo(ctx: PluginCommandContext):
    """
    异步执行,签到测试
    """
    try:
        save_json()
    except Exception as e:
        _LOGGER.error(e, exc_info=True)
        return PluginCommandResponse(False, f'创建数据源失败')
    return PluginCommandResponse(True, f'创建数据源成功')


@plugin.command(name='banner', title='获取不可说头图', desc='', icon='Today', run_in_background=True)
def echo(ctx: PluginCommandContext):
    """
    异步执行,签到测试
    """
    result = change_banner()
    if result:
        return PluginCommandResponse(True, f'替换成功')
    else:
        return PluginCommandResponse(False, f'肥肠抱歉,切换头图失败,请确认已配置不可说站点')

