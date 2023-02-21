import os
from mbot.openapi import mbot_api
from mbot.common.osutils import OSUtils
import logging

_LOGGER = logging.getLogger(__name__)


def clear_notify_tool(uid):
    mbot_api.notify.clear_system_message(uid)


def list_user():
    return mbot_api.user.list()


def delete_hard_link_tool(source_filepath, find_path=None, use_cache: bool = True):
    files = OSUtils.find_hardlink_files(source_filepath, find_path, use_cache)
    for file_path in files:
        if os.path.exists(file_path):
            os.remove(file_path)
