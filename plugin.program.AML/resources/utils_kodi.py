# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher miscellaneous functions
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

#
# Utility functions which DEPEND on Kodi modules
#
import sys, os, shutil, time, random, hashlib, urlparse

try:
    import xbmc, xbmcgui
    KODI_RUNTIME_AVAILABLE = True
except:
    KODI_RUNTIME_AVAILABLE = False

# Addon custom modules/packages
# import utils
# import disk_IO

# --- Constants -----------------------------------------------------------------------------------
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# --- Internal globals ----------------------------------------------------------------------------
current_log_level = LOG_INFO

# -------------------------------------------------------------------------------------------------
# Logging functions
# -------------------------------------------------------------------------------------------------
def set_log_level(level):
    global current_log_level

    current_log_level = level

# For Unicode stuff in Kodi log see http://forum.kodi.tv/showthread.php?tid=144677
#
def log_debug_KR(str_text):
    if current_log_level >= LOG_DEBUG:
        # if it is str we assume it's "utf-8" encoded.
        # will fail if called with other encodings (latin, etc).
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
                                  
        # At this point we are sure str_text is a unicode string.
        log_text = u'AML DEBUG: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_verb_KR(str_text):
    if current_log_level >= LOG_VERB:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML VERB : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_info_KR(str_text):
    if current_log_level >= LOG_INFO:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML INFO : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_warning_KR(str_text):
    if current_log_level >= LOG_WARNING:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML WARN : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGWARNING)

def log_error_KR(str_text):
    if current_log_level >= LOG_ERROR:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = u'AML ERROR: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

#
# Replacement functions when running outside Kodi with the standard Python interpreter.
#
def log_debug_Python(str):
    print(str)

def log_verb_Python(str):
    print(str)

def log_info_Python(str):
    print(str)

def log_warning_Python(str):
    print(str)

def log_error_Python(str):
    print(str)

# -------------------------------------------------------------------------------------------------
# Kodi notifications and dialogs
# -------------------------------------------------------------------------------------------------
#
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi_dialog_OK('Launch ROM?')
#  2) ret = kodi_dialog_OK('Launch ROM?', title = 'AML - Launcher')
#
def kodi_dialog_OK(row1, row2='', row3='', title = 'Advanced MAME Launcher'):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, row1, row2, row3)

#
# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(row1, row2='', row3='', title = 'Advanced MAME Launcher'):
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno(title, row1, row2, row3)

    return ret

#
# Displays a small box in the bottom right corner
#
def kodi_notify(text, title = 'Advanced MAME Launcher', time = 5000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def kodi_notify_warn(text, title = 'Advanced MAME Launcher warning', time = 7000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

#
# Do not use this function much because it is the same icon as when Python fails,
# and that may confuse the user.
#
def kodi_notify_error(text, title = 'Advanced MAME Launcher error', time = 7000):
    dialog = xbmcgui.Dialog()
    dialog.notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

def kodi_toogle_fullscreen():
    # >> Frodo and up compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')

# -------------------------------------------------------------------------------------------------
# If runnining with Kodi Python interpreter use Kodi proper functions.
# If running with the standard Python interpreter use replacement functions.
# -------------------------------------------------------------------------------------------------
if KODI_RUNTIME_AVAILABLE:
    log_debug   = log_debug_KR
    log_verb    = log_verb_KR
    log_info    = log_info_KR
    log_warning = log_warning_KR
    log_error   = log_error_KR
else:
    log_debug   = log_debug_Python
    log_verb    = log_verb_Python
    log_info    = log_info_Python
    log_warning = log_warning_Python
    log_error   = log_error_Python
