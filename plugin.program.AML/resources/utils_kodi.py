# -*- coding: utf-8 -*-

# Advanced Emulator Launcher miscellaneous functions.

# Copyright (c) 2016-2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import hashlib
import json
import os
import pprint
import random
import shutil
import sys
import time
import urlparse

# --- Kodi modules ---
try:
    import xbmc, xbmcgui
    KODI_RUNTIME_AVAILABLE_UTILS_KODI = True
except:
    KODI_RUNTIME_AVAILABLE_UTILS_KODI = False

# --- AEL modules ---
# This module must not include any other AML/AEL modules to avoid circular dependencies.

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

def log_variable(var_name, var):
    if current_log_level < LOG_DEBUG: return
    log_text = 'AML DUMP : Dumping variable "{}"\n{}'.format(var_name, pprint.pformat(var))
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

# For Unicode stuff in Kodi log see http://forum.kodi.tv/showthread.php?tid=144677
#
def log_debug_KR(str_text):
    if current_log_level >= LOG_DEBUG:
        # if it is str we assume it's "utf-8" encoded.
        # will fail if called with other encodings (latin, etc).
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
                                  
        # At this point we are sure str_text is a unicode string.
        log_text = 'AML DEBUG: ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_verb_KR(str_text):
    if current_log_level >= LOG_VERB:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = 'AML VERB : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_info_KR(str_text):
    if current_log_level >= LOG_INFO:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = 'AML INFO : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_warning_KR(str_text):
    if current_log_level >= LOG_WARNING:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = 'AML WARN : ' + str_text
        xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGWARNING)

def log_error_KR(str_text):
    if current_log_level >= LOG_ERROR:
        if isinstance(str_text, str): str_text = str_text.decode('utf-8')
        log_text = 'AML ERROR: ' + str_text
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

# type 3 ShowAndGetWriteableDirectory
# shares  'files'  list file sources (added through filemanager)
# shares  'local'  list local drives
# shares  ''       list local drives and network shares
def kodi_dialog_get_wdirectory(dialog_heading):
    return xbmcgui.Dialog().browse(3, dialog_heading, '').decode('utf-8')

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
    # Frodo and up compatible
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"}}')

#
# Access Kodi JSON-RPC interface in an easy way.
# Returns a dictionary with the parsed response 'result' field.
#
# Query input:
#
# {
#     "id" : 1,
#     "jsonrpc" : "2.0",
#     "method" : "Application.GetProperties",
#     "params" : { "properties" : ["name", "version"] }
# }
#
# Query response:
#
# {
#     "id" : 1,
#     "jsonrpc" : "2.0",
#     "result" : {
#         "name" : "Kodi",
#         "version" : {"major":17,"minor":6,"revision":"20171114-a9a7a20","tag":"stable"}
#     }
# }
#
# Query response ERROR:
# {
#     "id" : null,
#     "jsonrpc" : "2.0",
#     "error" : { "code":-32700, "message" : "Parse error."}
# }
#
def kodi_jsonrpc_query(method_str, params_str, verbose = False):
    if verbose:
        log_debug('kodi_jsonrpc_query() method_str "{0}"'.format(method_str))
        log_debug('kodi_jsonrpc_query() params_str "{0}"'.format(params_str))
        params_dic = json.loads(params_str)
        log_debug('kodi_jsonrpc_query() params_dic = \n{0}'.format(pprint.pformat(params_dic)))

    # --- Do query ---
    query_str = '{{"id" : 1, "jsonrpc" : "2.0", "method" : "{0}", "params" : {1} }}'.format(method_str, params_str)
    # if verbose: log_debug('kodi_jsonrpc_query() query_str "{0}"'.format(query_str))
    response_json_str = xbmc.executeJSONRPC(query_str)
    # if verbose: log_debug('kodi_jsonrpc_query() response "{0}"'.format(response_json_str))

    # --- Parse JSON response ---
    response_dic = json.loads(response_json_str)
    # if verbose: log_debug('kodi_jsonrpc_query() response_dic = \n{0}'.format(pprint.pformat(response_dic)))
    if 'error' in response_dic:
        result_dic = response_dic['error']
        log_warning('kodi_jsonrpc_query() JSONRPC ERROR {0}'.format(result_dic['message']))
    else:
        result_dic = response_dic['result']
    if verbose:
        log_debug('kodi_jsonrpc_query() result_dic = \n{0}'.format(pprint.pformat(result_dic)))

    return result_dic

# -------------------------------------------------------------------------------------------------
# Determine Kodi version and create some constants to allow version-dependent code.
# This if useful to work around bugs in Kodi core.
# -------------------------------------------------------------------------------------------------
def kodi_get_Kodi_major_version():
    try:
        rpc_dic = kodi_jsonrpc_query('Application.GetProperties', '{ "properties" : ["version"] }')
        return int(rpc_dic['version']['major'])
    except:
        # Default fallback
        return KODI_VERSION_KRYPTON

# Execute the Kodi version query when module is loaded and store results in global variable.
kodi_running_version = kodi_get_Kodi_major_version()

# --- Version constants. Minimum required version is Kodi Krypton ---
KODI_VERSION_KRYPTON = 17
KODI_VERSION_LEIA    = 18

# -------------------------------------------------------------------------------------------------
# If runnining with Kodi Python interpreter use Kodi proper functions.
# If running with the standard Python interpreter use replacement functions.
# -------------------------------------------------------------------------------------------------
if KODI_RUNTIME_AVAILABLE_UTILS_KODI:
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
