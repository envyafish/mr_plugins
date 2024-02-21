from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from plugins.xx.sync import *


@plugin.command(name='sync', title='一键同步学习资料', desc='', icon='', run_in_background=True)
def sync(
        ctx: PluginCommandContext
        ):
    command()
    return PluginCommandResponse(True, '')
