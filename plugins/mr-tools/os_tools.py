import os
import shutil
import logging

_LOGGER = logging.getLogger(__name__)


def os_tool(src, dst, rename, copy_type):
    if not os.path.exists(src):
        _LOGGER.error("源目录/文件不存在")
        return
    dst = dst.strip()
    dst = dst.rstrip("/")
    basename = os.path.basename(src)
    if rename.strip():
        basename = rename
    dst = f"{dst}/{basename}"
    if os.path.exists(dst):
        _LOGGER.error("目标目录已存在该目录或文件")
        return
    if copy_type == 'link':
        hard_link(src, dst)
    if copy_type == 'copy':
        copy(src, dst)
    if copy_type == 'move':
        move(src, dst)


def hard_link(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, copy_function=os.link)
    if os.path.isfile(src):
        os.link(src, dst)


def copy(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    if os.path.isfile(src):
        shutil.copy(src, dst)


def move(src, dst):
    shutil.move(src, dst)

# 通过文件路径找到对应的硬链接文件，返回文件路径
def find_hard_link_file(file_path):
    if not os.path.exists(file_path):
        return None
    if os.path.islink(file_path):
        return os.path.realpath(file_path)
    return file_path

