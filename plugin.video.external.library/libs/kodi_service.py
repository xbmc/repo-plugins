# (c) Roman Miroshnychenko <roman1972@gmail.com> 2020
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Classes and functions to interact with Kodi API"""
import hashlib
import json
import logging
import re
from pathlib import Path
from urllib.parse import urlencode

import xbmc
from xbmcaddon import Addon
from xbmcvfs import translatePath

from libs.exception_logger import format_trace, format_exception

ADDON = Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')

ADDON_DIR = Path(translatePath(ADDON.getAddonInfo('path')))
ADDON_ICON = Path(translatePath(ADDON.getAddonInfo('icon')))
ADDON_PROFILE_DIR = Path(translatePath(ADDON.getAddonInfo('profile')))

PLUGIN_URL = f'plugin://{ADDON_ID}/'

LOG_FORMAT = '[{addon_id} v.{addon_version}] {filename}:{lineno} - {message}'


class KodiLogHandler(logging.Handler):
    """
    Logging handler that writes to the Kodi log with correct levels

    It also adds {addon_id} and {addon_version} variables available to log format.
    """
    LEVEL_MAP = {
        logging.NOTSET: xbmc.LOGNONE,
        logging.DEBUG: xbmc.LOGDEBUG,
        logging.INFO: xbmc.LOGINFO,
        logging.WARN: xbmc.LOGWARNING,
        logging.WARNING: xbmc.LOGWARNING,
        logging.ERROR: xbmc.LOGERROR,
        logging.CRITICAL: xbmc.LOGFATAL,
    }

    def emit(self, record):
        record.addon_id = ADDON_ID
        record.addon_version = ADDON_VERSION
        extended_trace_info = getattr(self, 'extended_trace_info', False)
        if extended_trace_info:
            if record.exc_info is not None:
                record.exc_text = format_exception(record.exc_info[1])
            if record.stack_info is not None:
                record.stack_info = format_trace(7)
        message = self.format(record)
        kodi_log_level = self.LEVEL_MAP.get(record.levelno, xbmc.LOGDEBUG)
        xbmc.log(message, level=kodi_log_level)


class GettextEmulator:
    """
    Emulate GNU Gettext by mapping resource.language.en_gb UI strings to their numeric string IDs
    """
    _instance = None

    class LocalizationError(Exception):  # pylint: disable=missing-docstring
        pass

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._en_gb_string_po_path = (ADDON_DIR / 'resources' / 'language' /
                                      'resource.language.en_gb' / 'strings.po')
        if not self._en_gb_string_po_path.exists():
            raise self.LocalizationError(
                'Missing resource.language.en_gb strings.po localization file')
        if not ADDON_PROFILE_DIR.exists():
            ADDON_PROFILE_DIR.mkdir()
        self._string_mapping_path = ADDON_PROFILE_DIR / 'strings-map.json'
        self.strings_mapping = self._load_strings_mapping()

    def _load_strings_po(self):  # pylint: disable=missing-docstring
        with self._en_gb_string_po_path.open('r', encoding='utf-8') as fo:
            return fo.read()

    def _load_strings_mapping(self):
        """
        Load mapping of resource.language.en_gb UI strings to their IDs

        If a mapping file is missing or resource.language.en_gb strins.po file has been updated,
        a new mapping file is created.

        :return: UI strings mapping
        """
        strings_po = self._load_strings_po()
        strings_po_md5 = hashlib.md5(strings_po.encode('utf-8')).hexdigest()
        try:
            with self._string_mapping_path.open('r', encoding='utf-8') as fo:
                mapping = json.load(fo)
            if mapping['md5'] != strings_po_md5:
                raise IOError('resource.language.en_gb strings.po has been updated')
        except (IOError, ValueError):
            strings_mapping = self._parse_strings_po(strings_po)
            mapping = {
                'strings': strings_mapping,
                'md5': strings_po_md5,
            }
            with self._string_mapping_path.open('w', encoding='utf-8') as fo:
                json.dump(mapping, fo)
        return mapping['strings']

    @staticmethod
    def _parse_strings_po(strings_po):
        """
        Parse resource.language.en_gb strings.po file contents into a mapping of UI strings
        to their numeric IDs.

        :param strings_po: the content of strings.po file as a text string
        :return: UI strings mapping
        """
        id_string_pairs = re.findall(r'^msgctxt "#(\d+?)"\r?\nmsgid "(.*)"\r?$', strings_po, re.M)
        return {string: int(string_id) for string_id, string in id_string_pairs if string}

    @classmethod
    def gettext(cls, en_string: str) -> str:
        """
        Return a localized UI string by a resource.language.en_gb source string

        :param en_string: resource.language.en_gb UI string
        :return: localized UI string
        """
        emulator = cls()
        try:
            string_id = emulator.strings_mapping[en_string]
        except KeyError as exc:
            raise cls.LocalizationError(
                f'Unable to find "{en_string}" string in resource.language.en_gb/strings.po'
            ) from exc
        return ADDON.getLocalizedString(string_id)


def initialize_logging(extended_trace_info=True):
    """
    Initialize the root logger that writes to the Kodi log

    After initialization, you can use Python logging facilities as usual.

    :param extended_trace_info: write extended trace info when exc_info=True
        or stack_info=True parameters are passed to logging methods.
    """
    handler = KodiLogHandler()
    # pylint: disable=attribute-defined-outside-init
    handler.extended_trace_info = extended_trace_info
    logging.basicConfig(
        format=LOG_FORMAT,
        style='{',
        level=logging.DEBUG,
        handlers=[handler],
        force=True
    )


def get_plugin_url(**kwargs):
    return f'{PLUGIN_URL}?{urlencode(kwargs)}'


def get_remote_kodi_url(with_credentials=False):
    host = ADDON.getSetting('kodi_host')
    port = ADDON.getSetting('kodi_port')
    login = ADDON.getSetting('kodi_login')
    password = ADDON.getSetting('kodi_password')
    use_https = ADDON.getSettingBool('use_https')
    protocol = 'https' if use_https else 'http'
    if not with_credentials or not login:
        return f'{protocol}://{host}:{port}'
    return f'{protocol}://{login}:{password}@{host}:{port}'
