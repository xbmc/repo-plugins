# -*- coding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
"""
Initialization module

This module handles initializing all package-wide content

This file is part of Special Features.

Special Features is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

Special Features is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Special Features. If not, see <http://www.gnu.org/licenses/>.

@author: smitchell6879
@author: evertiro
@license: GPL-3.0
"""

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
from lib.parse import *
from pymysql import *
from hashlib import md5
import xml.etree.ElementTree as ET
import json
import os
import re
import sys
import sqlite3
import time
import datetime
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin
import urllib
import urllib2


'''Settings'''
addon = xbmcaddon.Addon()
playall = addon.getSetting('playall')
showalldir = addon.getSetting('showalldir')
moviedir = addon.getSetting('moviedir')
tvshowdir = addon.getSetting('tvshowdir')
aclndb = addon.getSetting('aclndb')
aupdb = addon.getSetting('aupdb')
folder = addon.getSetting('folder')
sfmenu = addon.getSetting('sfmenu')
exclude = addon.getSetting('excludetypes')
sfnfo = addon.getSetting('sfnfo')
mysql = addon.getSetting('mysql')
dbName = addon.getSetting('dbName')
user = addon.getSetting('sqluser')
pword = addon.getSetting('sqlpass')
ipadd = addon.getSetting('sqlip')
ipport = int(addon.getSetting('sqlport'))

''' Addon Setup'''
addonid = addon.getAddonInfo("id")
addonpath = addon.getAddonInfo("path")
addir = xbmc.translatePath(addon.getAddonInfo("profile"))
adset = xbmc.translatePath(os.path.join(addir, "settings.xml"))
adtest = xbmc.translatePath(os.path.join(addir, "testing.sfnfo"))
adtes = xbmc.translatePath(os.path.join(addir, "movie.sfnfo"))
dbdir = xbmc.translatePath(os.path.join(addir, "{}.db".format(dbName)))
libdir = xbmc.translatePath(os.path.join(addonpath, 'lib'))
resdir = xbmc.translatePath(os.path.join(addonpath, 'resources'))
sqldir = xbmc.translatePath(os.path.join(libdir, 'pymysql'))
flag = xbmc.translatePath(os.path.join(resdir, os.path.join('media_flag', 'specialfeatures_flag.png')))

sys.path.append(libdir)
sys.path.append(resdir)
sys.path.append(sqldir)

'''GUI'''
home = xbmcgui.Window(10000)
dialpro = xbmcgui.DialogProgress()
dialbg = xbmcgui.DialogProgressBG()
dialog = xbmcgui.Dialog()

''' Plugin'''
urlhandle = "plugin://plugin.video.specialfeatures/?"
althandle = "plugin://plugin.video.specialfeatures/"

'''XBMC'''
monitor = xbmc.Monitor()
playL = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
playr = xbmc.Player()

'''General'''
winid = {'window': "{}".format(xbmc.getInfoLabel('System.CurrentWindow'))}
time1 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:")
charSet = "utf8mb4"
cuType = cursors.DictCursor

# url        = urlhandle + urlencode(winid)
carList = list()
fliList = list()
trAsh = list()


def info(txt):
    '''Something has happed, basic action tracker'''
    txt = "{}".format(txt)
    message = u'%s: %s' % ("", txt)
    xbmc.log(msg=message, level=xbmc.LOGINFO)


def notice(txt):
    '''Something has happed, basic action tracker'''
    txt = "{}".format(txt)
    message = u'%s: %s' % (addonid, txt)
    xbmc.log(msg=message, level=xbmc.LOGNOTICE)


def warning(txt):
    '''Something bad happen may cause errors'''
    txt = "{}".format(txt)
    message = u'%s: %s' % (addonid, txt)
    xbmc.log(msg=message, level=xbmc.LOGWARNING)


def error(txt):
    '''addon is about to or has crashed this may be why'''
    txt = "{}".format(txt)
    message = u'%s: %s' % (addonid, txt)
    xbmc.log(msg=message, level=xbmc.LOGERROR)


def debug(txt):
    '''In depth infomation about the status of addon'''
    txt = "{}".format(txt)
    message = u'%s: %s' % (addonid, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def encoding():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    return


def lang(txt):
    return addon.getLocalizedString(txt)


def ok(txt="", top=lang(30000)):
    dialog.ok("{}".format(top), "{}".format(txt))


def text(txt="", top=lang(30000)):
    dialog.textviewer("{}".format(top), "{}".format(txt))


def note(top=lang(30000), txt="", _time=1500, sound=False):
    dialog.notification(top, txt, time=_time, sound=sound)


def bgdc(top=lang(30000), txt=""):
    dialbg.create(top, txt)


def bgdu(pct=0, top=lang(30000), txt=""):
    dialbg.update(pct, top, txt)


def bgdcc():
    dialbg.close()


def exist():
    sys.exit(1)


# def testing(_list):
#     testing = open("{}".format(adtest), 'w')
#     for item in _list:
#         testing.write("{}".format(item))
#         testing.write("\n")
#     testing.close()
