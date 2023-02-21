import os
import shutil
import zipfile
from datetime import datetime
import logging
from json import load
from typing import Dict, Optional

import requests

_LOGGER = logging.getLogger(__name__)


class PluginTools:
    release_url: str
    proxies: Dict[str, str]
    plugins_folder_path: str = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    plugin_path: str = os.path.abspath(os.path.dirname(__file__))
    plugin_folder_name: str = os.path.split(plugin_path)[1]
    zip_path: str = f"{plugins_folder_path}/{plugin_folder_name}.zip"
    extract_path: str = f"{plugins_folder_path}/{plugin_folder_name}_new_"
    manifest_path: str = f"{plugin_path}/manifest.json"

    def __init__(self, proxies: Optional[Dict] = None):
        manifest = self.get_manifest()
        self.release_url = manifest['release_url']
        self.proxies = proxies

    def download_plugin(self, download_url: str, retry_time: int = 1):
        if retry_time > 3:
            _LOGGER.error("尝试拉取项目3次失败,在线更新插件失败")
            return False
        try:
            res = requests.get(download_url, proxies=self.proxies)
        except Exception as e:
            self.download_plugin(retry_time + 1)

        with open(self.zip_path, "wb") as code:
            code.write(res.content)
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            self.extract_path = f"{self.extract_path}{str(round(datetime.now().timestamp()))}"
            zip_ref.extractall(self.extract_path)
        manifest_path = self.find_manifest_path()
        manifest_parent_path = os.path.split(manifest_path)[0]
        if os.path.exists(self.plugin_path):
            shutil.rmtree(self.plugin_path)
        shutil.move(manifest_parent_path, self.plugin_path)
        os.remove(self.zip_path)
        shutil.rmtree(self.extract_path)
        return True

    def find_manifest_path(self):
        for p, dir_list, file_list in os.walk(self.extract_path):
            for f in file_list:
                fp = os.path.join(p, f)
                if f.lower() == 'manifest.json':
                    return fp
        return None

    def check_update(self):
        with open(self.manifest_path, 'r', encoding='utf-8') as fp:
            json_data = load(fp)
            local_version = json_data['version']
        res = requests.get(self.release_url, proxies=self.proxies)
        json = res.json()
        latest_version = json['tag_name']
        if f"v{local_version}" != latest_version:
            return json['zipball_url']
        return None

    def get_manifest(self):
        with open(self.manifest_path, 'r', encoding='utf-8') as fp:
            json_data = load(fp)
            return json_data
