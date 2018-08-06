# -*- coding: utf-8 -*-
import os
import time
from resources.lib.utils import *
from kodiswift import Plugin, xbmcgui, xbmc

plugin = Plugin()
last_category = None

_lang = plugin.get_string

os_name = get_os_name()
os_is_android = None

NATIVE_PATH = xbmc.translatePath(plugin.addon.getAddonInfo('path'))
DEFAULT_API_URL = plugin.get_setting('api_url', str)

# try:
#     import hashlib
#     CACHE_ID_SUFFIX = '-' + hashlib.md5(CUSTOM_API_URL.encode('utf-8')).hexdigest()
# except Exception as ex:
#     log("SiTo.tv hashlib error: %s" % ex, level=xbmc.LOGERROR)
#     CACHE_ID_SUFFIX = '-' + CUSTOM_API_URL.replace(':', '_').replace('/', '-').replace('\\', '-')


# sito.log = log
# sito.notice = notice
# sito.image_resource_url = image_resource_url
# sito.url_for = plugin.url_for
# sito.store = plugin.get_storage('basic_cache' + CACHE_ID_SUFFIX)
# sito.requests_cache = plugin.get_storage('requests_cache', ttl=60*4)
#
# sito.SITO_FANART_IMAGE = plugin.addon.getAddonInfo('fanart') or image_resource_url(sito.SITO_FANART_IMAGE)
#
# NONE = sito.NONE


def notice(message, heading='', time=4000):
    plugin.notify(msg=heading, title=message, delay=time, image='')


def image_resource_url(image_resource):
    return os.path.join(NATIVE_PATH, image_resource)






