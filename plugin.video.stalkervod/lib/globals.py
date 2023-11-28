"""Module to initializes global setting for the plugin"""

from __future__ import absolute_import, division, unicode_literals
import os
import sys
from urllib.parse import urlencode, urlsplit
import dataclasses
import xbmcaddon

ADDON = xbmcaddon.Addon()


@dataclasses.dataclass
class PortalConfig:
    """Portal config"""
    mac_cookie: str = None
    portal_url: str = None
    device_id: str = None
    device_id_2: str = None
    signature: str = None
    serial_number: str = None
    portal_base_url: str = None
    context_path: str = None


@dataclasses.dataclass
class AddOnConfig:
    """Addon config"""
    url: str = None
    addon_id: str = None
    handle: str = None
    addon_data_path: str = None
    max_page_limit: int = 2
    max_retries: int = 2
    token_path: str = None


class GlobalVariables:
    """Class initializes global settings used by the plugin"""

    def __init__(self):
        """Init class"""
        self.is_addd_on_first_run = None
        self.addon_config = AddOnConfig()
        self.portal_config = PortalConfig()

    def init_globals(self):
        """Init global settings"""
        self.is_addd_on_first_run = self.is_addd_on_first_run is None
        self.addon_config.url = sys.argv[0]
        if self.is_addd_on_first_run:
            self.addon_config.addon_id = ADDON.getAddonInfo('id')
            self.addon_config.addon_data_path = ADDON.getAddonInfo('path')
            self.addon_config.token_path = os.path.join(self.addon_config.addon_data_path, 'resources', 'tokens')
            self.addon_config.handle = int(sys.argv[1])
            self.portal_config.mac_cookie = 'mac=' + ADDON.getSetting('mac_address')
            self.portal_config.portal_url = ADDON.getSetting('server_address')
            self.portal_config.device_id = ADDON.getSetting('device_id')
            self.portal_config.device_id_2 = ADDON.getSetting('device_id_2')
            self.portal_config.signature = ADDON.getSetting('signature')
            self.portal_config.serial_number = ADDON.getSetting('serial_number')
            self.portal_config.portal_base_url = self.get_portal_base_url(self.portal_config.portal_url)
            self.portal_config.context_path = '/stalker_portal/server/load.php'

    @staticmethod
    def get_portal_base_url(url):
        """Get portal base url"""
        split_url = urlsplit(url)
        return split_url.scheme + '://' + split_url.netloc

    def get_handle(self):
        """Get addon handle"""
        return self.addon_config.handle

    def get_custom_thumb_path(self, thumb_file_name):
        """Get thumb file path"""
        return os.path.join(self.addon_config.addon_data_path, 'resources', 'media', thumb_file_name)

    def get_plugin_url(self, params):
        """Get plugin url"""
        return '{}?{}'.format(self.addon_config.url, urlencode(params))


G = GlobalVariables()
