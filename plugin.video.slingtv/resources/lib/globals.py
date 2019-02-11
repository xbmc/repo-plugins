#   Copyright (C) 2018 Lunatixz, eracknaphobia, d21spike
#
#
# This file is part of Sling.TV.
#
# Sling.TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sling.TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sling.TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, pytz, calendar, random
import urlparse, urllib, urllib2, socket, json, requests, base64, inputstreamhelper
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

from hashlib import sha1
from simplecache import SimpleCache, use_cache

try:
    from multiprocessing import cpu_count 
    from multiprocessing.pool import ThreadPool 
    ENABLE_POOL = True
except: ENABLE_POOL = False

# Plugin Info
ADDON_ID      = 'plugin.video.slingtv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT       = 15
USER_EMAIL    = REAL_SETTINGS.getSetting('User_Email')
USER_PASSWORD = REAL_SETTINGS.getSetting('User_Password')
LOGIN_URL     = ''
ACCESS_TOKEN  = REAL_SETTINGS.getSetting('access_token')
SUBSCRIBER_ID = REAL_SETTINGS.getSetting('subscriber_id')
DEVICE_ID     = REAL_SETTINGS.getSetting('device_id')
USER_SUBS     = REAL_SETTINGS.getSetting('user_subs')
LEGACY_SUBS   = REAL_SETTINGS.getSetting('legacy_subs')
USER_DMA      = REAL_SETTINGS.getSetting('user_dma')
USER_OFFSET   = REAL_SETTINGS.getSetting('user_offset')
USER_ZIP      = REAL_SETTINGS.getSetting('user_zip')
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
USER_AGENT    = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
HEADERS       = {'Accept': '*/*',
                 'Origin': 'https://www.sling.com',
                 'User-Agent': USER_AGENT,
                 'Content-Type': 'application/json;charset=UTF-8',
                 'Referer': 'https://www.sling.com',
                 'Accept-Encoding': 'gzip, deflate, br',
                 'Accept-Language': 'en-US,en;q=0.9'}
                 
# This url includes more environments (beta, dev, etc.)
# https://webapp.movetv.com/config/env-list/sling.json
BASE_URL      = 'https://watch.sling.com'
BASE_API      = 'https://ums.p.sling.com'
BASE_WEB      = 'https://webapp.movetv.com'
BASE_GEO      = 'https://p-geo.movetv.com/geo?subscriber_id={}&device_id={}'
MAIN_URL      = '%s/config/android/sling/menu_tabs.json'%BASE_WEB
USER_INFO_URL = '%s/v2/user.json'%BASE_API
WEB_ENDPOINTS = '%s/config/env-list/browser-sling.json'%(BASE_WEB)
MYTV          = '%s/config/shared/pages/mytv.json'%(BASE_WEB)
CONFIG        = '%s/config/browser/sling/config.json'%(BASE_WEB)
VERIFY        = False


def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def uni(string1, encoding='utf-8'):
    if isinstance(string1, basestring):
        if not isinstance(string1, unicode):
            string1 = unicode(string1, encoding)
        elif isinstance(string1, unicode):
            string1 = string1.encode('ascii', 'replace')
    return string1

def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval

def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)

def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)

def notificationDialog(message, header=ADDON_NAME, sound=False, time=1000, icon=ICON):
    try:
        xbmcgui.Dialog().notification(header, message, icon, time, sound)
    except:
        xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))

def loadJSON(string1):
    try:
        return json.loads(string1)
    except Exception as e:
        log("loadJSON Failed! " + str(e), xbmc.LOGERROR)
        return {}

def dumpJSON(string1):
    try:
        return json.dumps(string1)
    except Exception as e:
        log("dumpJSON Failed! " + str(e), xbmc.LOGERROR)
        return ''

def stringToDate(string, date_format):
    try: return datetime.datetime.strptime(str(string), date_format)
    except TypeError: return datetime.datetime(*(time.strptime(str(string), date_format)[0:6]))
    
def poolList(method, items):
    results = []
    if ENABLE_POOL:
        pool = ThreadPool(cpu_count())
        results = pool.imap_unordered(method, items)
        pool.close()
        pool.join()
    else: results = [method(item) for item in items]
    results = filter(None, results)
    return results

def sortGroup(str):
    arr = str.split(',')
    arr = sorted(arr)
    return ','.join(arr)

def utcToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)