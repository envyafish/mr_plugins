from mbot.external.downloadclient import DownloadClientManager

from plugins.xx.base_config import get_base_config, ConfigType
from plugins.xx.exceptions import ConfigInitError
from plugins.xx.logger import Logger
from plugins.xx.models import Config


class DownloadClient:
    client: None
    config: Config
    download_manager: DownloadClientManager = DownloadClientManager()

    def __init__(self, config: Config):
        if not config:
            Logger.error("请先初始化配置")
            raise ConfigInitError
        if not config.download_path and not config.category:
            Logger.error("配置缺失:下载路径或下载分类不存在")
            raise ConfigInitError
        self.download_manager.init(client_configs=get_base_config(ConfigType.Download_Client))

        if config.download_client_name:
            self.client = self.download_manager.get(config.download_client_name)
        else:
            self.client = self.download_manager.default()

    def download_from_file(self, torrent_path, save_path, category):
        return self.client.download_from_file(torrent_filepath=torrent_path, savepath=save_path, category=category)

    def download_from_url(self, torrent_url, save_path, category):
        return self.client.download_from_url(url=torrent_url, savepath=save_path, category=category)
