# -*- coding: utf-8 -*-

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

# Advanced MAME Launcher Kodi utility functions.
#
# The idea if this module is to share it between AEL and AML.
#
# All functions that depends on Kodi modules are here. This includes IO functions
# and logging functions.
#
# Low-level filesystem and IO functions are here. disk_IO module contains high level functions.
#
# When Kodi modules are not available replaces can be provided. This is useful to use addon
# modules with CPython.
#
# This module must NOT include any other addon modules to avoid circular dependencies. The
# only exception to this rule is the module .constants. This module is virtually included
# by every other addon module.
#
# How to report errors on the low-level filesystem functions??? See the end of the file.

# --- Be prepared for the future ---
from __future__ import unicode_literals
from __future__ import division

# --- Addon modules ---
from .constants import *

# --- Kodi modules ---
try:
    import xbmc
    import xbmcgui
    KODI_RUNTIME_AVAILABLE_UTILS = True
except:
    KODI_RUNTIME_AVAILABLE_UTILS = False

# --- Python standard library ---
# Check what modules are really used and remove not used ones.
import fnmatch
import io
import json
import math
import os
import sys
import threading
import time

# --- Determine interpreter running platform ---
# Cache all possible platform values in global variables for maximum speed.
# See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform
cached_sys_platform = sys.platform
def _aux_is_android():
    if not cached_sys_platform.startswith('linux'): return False
    return 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ or 'XBMC_ANDROID_APK' in os.environ

is_windows_bool = cached_sys_platform == 'win32' or cached_sys_platform == 'win64' or cached_sys_platform == 'cygwin'
is_osx_bool = cached_sys_platform.startswith('darwin')
is_android_bool = _aux_is_android()
is_linux_bool = cached_sys_platform.startswith('linux') and not is_android_bool

def is_windows(): return is_windows_bool

def is_osx(): return is_osx_bool

def is_android(): return is_android_bool

def is_linux(): return is_linux_bool

# -------------------------------------------------------------------------------------------------
# Filesystem helper class.
# The addon must not use any Python IO functions, only this class. This class can be changed
# to use Kodi IO functions or Python IO functions.
#
# This class always takes and returns Unicode string paths. Decoding to UTF-8 must be done in
# caller code.
#
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
#
# Decomposes a file name path or directory into its constituents
#   FileName.getOriginalPath()  Full path                                     /home/Wintermute/Sonic.zip
#   FileName.getPath()          Full path                                     /home/Wintermute/Sonic.zip
#   FileName.getPath_noext()    Full path with no extension                   /home/Wintermute/Sonic
#   FileName.getDir()           Directory name of file. Does not end in '/'   /home/Wintermute/
#   FileName.getBase()          File name with no path                        Sonic.zip
#   FileName.getBase_noext()    File name with no path and no extension       Sonic
#   FileName.getExt()           File extension                                .zip
# -------------------------------------------------------------------------------------------------
class FileName:
    # pathString must be a Unicode string object
    def __init__(self, pathString):
        self.originalPath = pathString
        self.path         = pathString
        
        # --- Path transformation ---
        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

        elif self.originalPath.lower().startswith('special:'):
            self.path = xbmc.translatePath(self.path)

    def _join_raw(self, arg):
        self.path         = os.path.join(self.path, arg)
        self.originalPath = os.path.join(self.originalPath, arg)

        return self

    # Appends a string to path. Returns self FileName object
    # Instead of append() use pappend(). This will avoid using string.append() instead of FileName.append()
    def pappend(self, arg):
        self.path         = self.path + arg
        self.originalPath = self.originalPath + arg

        return self

    # Behaves like os.path.join(). Returns a FileName object
    # Instead of join() use pjoin(). This will avoid using string.join() instead of FileName.join()
    def pjoin(self, *args):
        child = FileName(self.originalPath)
        for arg in args:
            child._join_raw(arg)

        return child

    def escapeQuotes(self):
        self.path = self.path.replace("'", "\\'")
        self.path = self.path.replace('"', '\\"')

    # ---------------------------------------------------------------------------------------------
    # Filename decomposition.
    # ---------------------------------------------------------------------------------------------
    def getOriginalPath(self):
        return self.originalPath

    def getPath(self):
        return self.path

    def getPath_noext(self):
        root, ext = os.path.splitext(self.path)

        return root

    def getDir(self):
        return os.path.dirname(self.path)

    def getBase(self):
        return os.path.basename(self.path)

    def getBase_noext(self):
        basename  = os.path.basename(self.path)
        root, ext = os.path.splitext(basename)
        
        return root

    def getExt(self):
        root, ext = os.path.splitext(self.path)
        
        return ext

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(self.path, filename))

        return files

    def scanFilesInPathAsPaths(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(FileName(os.path.join(self.path, filename)))

        return files

    def recursiveScanFilesInPath(self, mask):
        files = []
        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                files.append(os.path.join(root, filename))

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    #
    # mtime (Modification time) is a floating point number giving the number of seconds since
    # the epoch (see the time module).
    #
    def getmtime(self):
        return os.path.getmtime(self.path)

    def stat(self):
        return os.stat(self.path)

    def fileSize(self):
        stat_output = os.stat(self.path)
        return stat_output.st_size

    def exists(self):
        return os.path.exists(self.path)

    def isdir(self):
        return os.path.isdir(self.path)

    def isfile(self):
        return os.path.isfile(self.path)

    def makedirs(self):
        if not os.path.exists(self.path): 
            os.makedirs(self.path)

    # os.remove() and os.unlink() are exactly the same.
    def unlink(self):
        os.unlink(self.path)

    def rename(self, to):
        os.rename(self.path, to.getPath())

#
# How to report errors in these IO functions? That's the eternal question.
# 1) Raise an exception and make the addon crash? Crashes are always reported in the GUI.
# 2) Use AEL approach and report status in a control dictionary? Caller code is responsible
#    to report the error in the GUI.
#
# -------------------------------------------------------------------------------------------------
# Low level filesystem functions.
# -------------------------------------------------------------------------------------------------
def utils_write_str_to_file(filename, full_string):
    log_debug('utils_write_str_to_file() File "{}"'.format(filename))
    with io.open(filename, 'wt', encoding = 'utf-8') as f:
        f.write(full_string)

def utils_load_file_to_str(filename):
    log_debug('utils_load_file_to_str() File "{}"'.format(filename))
    with io.open(filename, 'rt', encoding = 'utf-8') as f:
        string = f.read()
    return string

# -------------------------------------------------------------------------------------------------
# Generic text file writer.
# slist is a list of Unicode strings that will be joined and written to a file encoded in UTF-8.
# Joining command is '\n'.join()
# -------------------------------------------------------------------------------------------------
def utils_write_slist_to_file(filename, slist):
    log_debug('utils_write_slist_to_file() File "{}"'.format(filename))
    try:
        file_obj = io.open(filename, 'wt', encoding = 'utf-8')
        file_obj.write('\n'.join(slist))
        file_obj.close()
    except OSError:
        log_error('(OSError) exception in utils_write_slist_to_file()')
        log_error('Cannot write {} file'.format(filename))
        raise AEL_Error('(OSError) Cannot write {} file'.format(filename))
    except IOError:
        log_error('(IOError) exception in utils_write_slist_to_file()')
        log_error('Cannot write {} file'.format(filename))
        raise AEL_Error('(IOError) Cannot write {} file'.format(filename))

def utils_load_file_to_slist(filename):
    log_debug('utils_load_file_to_slist() File "{}"'.format(filename))
    with io.open(filename, 'rt', encoding = 'utf-8') as f:
        slist = f.readlines()
    return slist

# -------------------------------------------------------------------------------------------------
# JSON write/load
# -------------------------------------------------------------------------------------------------
def utils_load_JSON_file_dic(json_filename, verbose = True):
    # --- If file does not exist return empty dictionary ---
    data_dic = {}
    if not os.path.isfile(json_filename):
        log_warning('utils_load_JSON_file_dic() Not found "{}"'.format(json_filename))
        return data_dic
    if verbose:
        log_debug('utils_load_JSON_file_dic() "{}"'.format(json_filename))
    with io.open(json_filename, 'rt', encoding = 'utf-8') as file:
        data_dic = json.load(file)

    return data_dic

def utils_load_JSON_file_list(json_filename, verbose = True):
    # --- If file does not exist return empty dictionary ---
    data_list = []
    if not os.path.isfile(json_filename):
        log_warning('utils_load_JSON_file_list() Not found "{}"'.format(json_filename))
        return data_list
    if verbose:
        log_debug('utils_load_JSON_file_list() "{}"'.format(json_filename))
    with io.open(json_filename, 'rt', encoding = 'utf-8') as file:
        data_list = json.load(file)

    return data_list

# This consumes a lot of memory but it is fast.
# See https://stackoverflow.com/questions/24239613/memoryerror-using-json-dumps
def utils_write_JSON_file(json_filename, json_data, verbose = True):
    l_start = time.time()
    if verbose:
        log_debug('utils_write_JSON_file() "{}"'.format(json_filename))
    try:
        with io.open(json_filename, 'wt', encoding = 'utf-8') as file:
            if OPTION_COMPACT_JSON:
                file.write(text_type(json.dumps(json_data, ensure_ascii = False, sort_keys = True)))
            else:
                file.write(text_type(json.dumps(json_data, ensure_ascii = False, sort_keys = True,
                    indent = 1, separators = (',', ':'))))
    except OSError:
        kodi_notify('Advanced MAME Launcher',
                    'Cannot write {} file (OSError)'.format(json_filename))
    except IOError:
        kodi_notify('Advanced MAME Launcher',
                    'Cannot write {} file (IOError)'.format(json_filename))
    l_end = time.time()
    if verbose:
        write_time_s = l_end - l_start
        log_debug('utils_write_JSON_file() Writing time {:f} s'.format(write_time_s))

def utils_write_JSON_file_pprint(json_filename, json_data, verbose = True):
    l_start = time.time()
    if verbose:
        log_debug('utils_write_JSON_file_pprint() "{}"'.format(json_filename))
    try:
        with io.open(json_filename, 'wt', encoding = 'utf-8') as file:
            file.write(text_type(json.dumps(json_data, ensure_ascii = False, sort_keys = True,
                indent = 1, separators = (', ', ' : '))))
    except OSError:
        kodi_notify('Advanced MAME Launcher',
                    'Cannot write {} file (OSError)'.format(json_filename))
    except IOError:
        kodi_notify('Advanced MAME Launcher',
                    'Cannot write {} file (IOError)'.format(json_filename))
    l_end = time.time()
    if verbose:
        write_time_s = l_end - l_start
        log_debug('utils_write_JSON_file_pprint() Writing time {:f} s'.format(write_time_s))

def utils_write_JSON_file_lowmem(json_filename, json_data, verbose = True):
    l_start = time.time()
    if verbose:
        log_debug('utils_write_JSON_file_lowmem() "{}"'.format(json_filename))
    try:
        if OPTION_COMPACT_JSON:
            jobj = json.JSONEncoder(ensure_ascii = False, sort_keys = True)
        else:
            jobj = json.JSONEncoder(ensure_ascii = False, sort_keys = True,
                indent = 1, separators = (',', ':'))
        # --- Chunk by chunk JSON writer ---
        with io.open(json_filename, 'wt', encoding = 'utf-8') as file:
            for chunk in jobj.iterencode(json_data):
                file.write(text_type(chunk))
    except OSError:
        kodi_notify('Advanced MAME Launcher',
                    'Cannot write {} file (OSError)'.format(json_filename))
    except IOError:
        kodi_notify('Advanced MAME Launcher',
                    'Cannot write {} file (IOError)'.format(json_filename))
    l_end = time.time()
    if verbose:
        write_time_s = l_end - l_start
        log_debug('utils_write_JSON_file_lowmem() Writing time {:f} s'.format(write_time_s))

# -------------------------------------------------------------------------------------------------
# Threaded JSON loader
# -------------------------------------------------------------------------------------------------
# How to use this code:
#     render_thread = Threaded_Load_JSON(cfg.RENDER_DB_PATH.getPath())
#     assets_thread = Threaded_Load_JSON(cfg.MAIN_ASSETS_DB_PATH.getPath())
#     render_thread.start()
#     assets_thread.start()
#     render_thread.join()
#     assets_thread.join()
#     MAME_db_dic = render_thread.output_dic
#     MAME_assets_dic = assets_thread.output_dic
class Threaded_Load_JSON(threading.Thread):
    def __init__(self, json_filename): 
        threading.Thread.__init__(self) 
        self.json_filename = json_filename
 
    def run(self): 
        self.output_dic = utils_load_JSON_file_dic(self.json_filename)

# -------------------------------------------------------------------------------------------------
# File cache functions.
# Depends on the FileName class.
# -------------------------------------------------------------------------------------------------
file_cache = {}

def utils_file_cache_clear(verbose = True):
    global file_cache
    if verbose: log_debug('utils_file_cache_clear() Clearing file cache')
    file_cache = {}

def utils_file_cache_add_dir(dir_str, verbose = True):
    global file_cache

    # Create a set with all the files in the directory
    if not dir_str:
        log_warning('file_cache_add_dir() Empty dir_str. Exiting')
        return
    dir_FN = FileName(dir_str)
    if not dir_FN.exists():
        log_debug('file_cache_add_dir() Does not exist "{}"'.format(dir_str))
        file_cache[dir_str] = set()
        return
    if not dir_FN.isdir():
        log_warning('file_cache_add_dir() Not a directory "{}"'.format(dir_str))
        return
    if verbose:
        # log_debug('file_cache_add_dir() Scanning OP "{}"'.format(dir_FN.getOriginalPath()))
        log_debug('file_cache_add_dir() Scanning  P "{}"'.format(dir_FN.getPath()))
    # A recursive scanning function is needed. os.listdir() is not. os.walk() is recursive
    # file_list = os.listdir(dir_FN.getPath())
    file_list = []
    root_dir_str = dir_FN.getPath()
    # For Unicode errors in os.walk() see
    # https://stackoverflow.com/questions/21772271/unicodedecodeerror-when-performing-os-walk
    for root, dirs, files in os.walk(text_type(root_dir_str)):
        # log_debug('----------')
        # log_debug('root = {}'.format(root))
        # log_debug('dirs = {}'.format(text_type(dirs)))
        # log_debug('files = {}'.format(text_type(files)))
        # log_debug('\n')
        for f in files:
            my_file = os.path.join(root, f)
            cache_file = my_file.replace(root_dir_str, '')
            # >> In the cache always store paths as '/' and not as '\'
            cache_file = cache_file.replace('\\', '/')
            # >> Remove '/' character at the beginning of the file. If the directory dir_str
            # >> is like '/example/dir/' then the slash at the beginning will be removed. However,
            # >> if dir_str is like '/example/dir' it will be present.
            if cache_file.startswith('/'): cache_file = cache_file[1:]
            file_list.append(cache_file)
    file_set = set(file_list)
    if verbose:
        # for file in file_set: log_debug('File "{}"'.format(file))
        log_debug('file_cache_add_dir() Adding {} files to cache'.format(len(file_set)))
    file_cache[dir_str] = file_set

#
# See misc_look_for_file() documentation below.
#
def utils_file_cache_search(dir_str, filename_noext, file_exts):
    # Check for empty, unconfigured dirs
    if not dir_str: return None
    current_cache_set = file_cache[dir_str]
    # if filename_noext == '005':
    #     log_debug('utils_file_cache_search() Searching in "{}"'.format(dir_str))
    #     log_debug('utils_file_cache_search() current_cache_set "{}"'.format(text_type(current_cache_set)))
    for ext in file_exts:
        file_base = filename_noext + '.' + ext
        # log_debug('utils_file_cache_search() file_Base = "{}"'.format(file_base))
        if file_base in current_cache_set:
            # log_debug('utils_file_cache_search() Found in cache')
            return FileName(dir_str).pjoin(file_base)

    return None

# -------------------------------------------------------------------------------------------------
# Logging functions
# Kodi Matrix has changed the log levels. See
# https://forum.kodi.tv/showthread.php?tid=344263&pid=2943703#pid2943703
# -------------------------------------------------------------------------------------------------
# Constants
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_VERB    = 3
LOG_DEBUG   = 4

# Internal globals
current_log_level = LOG_INFO

def set_log_level(level):
    global current_log_level

    current_log_level = level

def log_variable(var_name, var):
    if current_log_level < LOG_DEBUG: return
    log_text = 'AML DUMP : Dumping variable "{}"\n{}'.format(var_name, pprint.pformat(var))
    xbmc.log(log_text, level = xbmc.LOGERROR)

# For Unicode stuff in Kodi log see https://github.com/romanvm/kodi.six
def log_debug_KR(text_line):
    if current_log_level < LOG_DEBUG: return

    # If it is bytes we assume it's "utf-8" encoded.
    # will fail if called with other encodings (latin, etc).
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')

    # At this point we are sure text_line is a Unicode string.
    # Kodi functions (Python 3) require Unicode strings as arguments.
    # Kodi functions (Python 2) require UTF-8 encoded bytes as arguments.
    log_text = 'AML DEBUG: ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_verb_KR(text_line):
    if current_log_level < LOG_VERB: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = 'AML VERB : ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_info_KR(text_line):
    if current_log_level < LOG_INFO: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = 'AML INFO : ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_warning_KR(text_line):
    if current_log_level < LOG_WARNING: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = 'AML WARN : ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGWARNING)

def log_error_KR(text_line):
    if current_log_level < LOG_ERROR: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = 'AML ERROR: ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

#
# Replacement functions when running outside Kodi with the standard Python interpreter.
#
def log_debug_Python(text_line): print(text_line)

def log_verb_Python(text_line): print(text_line)

def log_info_Python(text_line): print(text_line)

def log_warning_Python(text_line): print(text_line)

def log_error_Python(text_line): print(text_line)

# -------------------------------------------------------------------------------------------------
# Kodi notifications and dialogs
# -------------------------------------------------------------------------------------------------
# Displays a modal dialog with an OK button. Dialog can have up to 3 rows of text, however first
# row is multiline.
# Call examples:
#  1) ret = kodi_dialog_OK('Launch ROM?')
#  2) ret = kodi_dialog_OK('Launch ROM?', title = 'AML - Launcher')
def kodi_dialog_OK(text, title = 'Advanced MAME Launcher'):
    xbmcgui.Dialog().ok(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(text, title = 'Advanced MAME Launcher'):
    return xbmcgui.Dialog().yesno(title, text)

# Returns a directory.
def kodi_dialog_get_directory(dialog_heading):
    return xbmcgui.Dialog().browse(0, dialog_heading, '').decode('utf-8')

def kodi_dialog_get_file(dialog_heading):
    return xbmcgui.Dialog().browse(1, dialog_heading, '').decode('utf-8')

def kodi_dialog_get_image(dialog_heading):
    return xbmcgui.Dialog().browse(2, dialog_heading, '').decode('utf-8')

# Returns a writable directory.
# Arg 1: type 3 ShowAndGetWriteableDirectory
# Arg 2: heading
# Arg 3: shares
#     shares  'files'  list file sources (added through filemanager)
#     shares  'local'  list local drives
#     shares  ''       list local drives and network shares
def kodi_dialog_get_wdirectory(dialog_heading):
    return xbmcgui.Dialog().browse(3, dialog_heading, '').decode('utf-8')

# Displays a small box in the bottom right corner
def kodi_notify(text, title = 'Advanced MAME Launcher', time = 5000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def kodi_notify_warn(text, title = 'Advanced MAME Launcher warning', time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

# Do not use this function much because it is the same icon displayed when Python fails
# with an exception and that may confuse the user.
def kodi_notify_error(text, title = 'Advanced MAME Launcher error', time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

# Progress dialog that can be closed and reopened.
# Messages and progress in the dialog are always remembered, even if closed and reopened.
# If the dialog is canceled this class remembers it forever.
# Kodi Matrix change: Renamed option line1 to message. Removed option line2. Removed option line3.
#
# --- Example 1 ---
# pDialog = KodiProgressDialog()
# pDialog.startProgress('Doing something...', step_total)
# for ...
#     pDialog.updateProgressInc()
#     # Do stuff...
# pDialog.endProgress()
class KodiProgressDialog(object):
    def __init__(self):
        self.heading = 'Advanced MAME Launcher'
        self.progress = 0
        self.flag_dialog_canceled = False
        self.dialog_active = False
        self.progressDialog = xbmcgui.DialogProgress()

    # Creates a new progress dialog.
    def startProgress(self, message, step_total = 100, step_counter = 0):
        if self.dialog_active: raise TypeError
        self.step_total = step_total
        self.step_counter = step_counter
        try:
            self.progress = int(math.floor((self.step_counter * 100) / self.step_total))
        except ZeroDivisionError:
            # Fix case when step_total is 0.
            self.step_total = 0.001
            self.progress = int(math.floor((self.step_counter * 100) / self.step_total))
        self.dialog_active = True
        self.message = message
        self.progressDialog.create(self.heading, self.message, ' ', ' ') # Workaround for Kodi Leia
        # self.progressDialog.create(self.heading, self.message) # Code for Krypton and up.
        self.progressDialog.update(self.progress)

    # Changes message and resets progress.
    def resetProgress(self, message, step_total = 100, step_counter = 0):
        if not self.dialog_active: raise TypeError
        self.step_total = step_total
        self.step_counter = step_counter
        try:
            self.progress = int(math.floor((self.step_counter * 100) / self.step_total))
        except ZeroDivisionError:
            # Fix case when step_total is 0.
            self.step_total = 0.001
            self.progress = int(math.floor((self.step_counter * 100) / self.step_total))
        self.message = message
        self.progressDialog.update(self.progress, self.message, ' ', ' ') # Workaround for Kodi Leia
        # self.progressDialog.update(self.progress, self.message) # Code for Krypton and up.

    # Update progress and optionally update message as well.
    def updateProgress(self, step_counter, message = None):
        if not self.dialog_active: raise TypeError
        self.step_counter = step_counter
        self.progress = int(math.floor((self.step_counter * 100) / self.step_total))
        if message is None:
            self.progressDialog.update(self.progress)
        else:
            if type(message) is not text_type: raise TypeError
            self.message = message
            self.progressDialog.update(self.progress, self.message, ' ', ' ') # Workaround for Kodi Leia
            # self.progressDialog.update(self.progress, self.message) # Code for Krypton and up.

    # Update progress, optionally update message as well, and autoincrements.
    # Progress is incremented AFTER dialog is updated.
    def updateProgressInc(self, message = None):
        if not self.dialog_active: raise TypeError
        self.progress = int(math.floor((self.step_counter * 100) / self.step_total))
        self.step_counter += 1
        if message is None:
            self.progressDialog.update(self.progress)
        else:
            if type(message) is not text_type: raise TypeError
            self.message = message
            self.progressDialog.update(self.progress, self.message, ' ', ' ') # Workaround for Kodi Leia
            # self.progressDialog.update(self.progress, self.message) # Code for Matrix and up.

    # Update dialog message but keep same progress.
    def updateMessage(self, message):
        if not self.dialog_active: raise TypeError
        if type(message) is not text_type: raise TypeError
        self.message = message
        self.progressDialog.update(self.progress, self.message, ' ', ' ') # Workaround for Kodi Leia
        # self.progressDialog.update(self.progress, self.message) # Code for Matrix and up.

    def isCanceled(self):
        # If the user pressed the cancel button before then return it now.
        if self.flag_dialog_canceled: return True
        # If not check and set the flag.
        if not self.dialog_active: raise TypeError
        self.flag_dialog_canceled = self.progressDialog.iscanceled()
        return self.flag_dialog_canceled

    # Before closing the dialog check if the user pressed the Cancel button and remember
    # the user decision.
    def endProgress(self):
        if not self.dialog_active: raise TypeError
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.update(100)
        self.progressDialog.close()
        self.dialog_active = False

    # Reopens a previously closed dialog with endProgress(), remembering the messages
    # and the progress it had when it was closed.
    def reopen(self):
        if self.dialog_active: raise TypeError
        self.progressDialog.create(self.heading, self.message, ' ', ' ') # Workaround for Kodi Leia
        # self.progressDialog.create(self.heading, self.message) # Code for Matrix and up.
        self.progressDialog.update(self.progress)
        self.dialog_active = True

def kodi_toogle_fullscreen():
    kodi_jsonrpc_dict('Input.ExecuteAction', {'action' : 'togglefullscreen'})

def kodi_get_screensaver_mode():
    r_dic = kodi_jsonrpc_dict('Settings.getSettingValue', {'setting' : 'screensaver.mode'})
    screensaver_mode = r_dic['value']
    return screensaver_mode

g_screensaver_mode = None # Global variable to store screensaver status.
def kodi_disable_screensaver():
    global g_screensaver_mode
    g_screensaver_mode = kodi_get_screensaver_mode()
    log_debug('kodi_disable_screensaver() g_screensaver_mode "{}"'.format(g_screensaver_mode))
    p_dic = {
        'setting' : 'screensaver.mode',
        'value' : '',
    }
    kodi_jsonrpc_dict('Settings.setSettingValue', p_dic)
    log_debug('kodi_disable_screensaver() Screensaver disabled.')

# kodi_disable_screensaver() must be called before this function or bad things will happen.
def kodi_restore_screensaver():
    if g_screensaver_mode is None:
        log_error('kodi_disable_screensaver() must be called before kodi_restore_screensaver()')
        raise RuntimeError
    log_debug('kodi_restore_screensaver() Screensaver mode "{}"'.format(g_screensaver_mode))
    p_dic = {
        'setting' : 'screensaver.mode',
        'value' : g_screensaver_mode,
    }
    kodi_jsonrpc_dict('Settings.setSettingValue', p_dic)
    log_debug('kodi_restore_screensaver() Restored previous screensaver status.')

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
def kodi_jsonrpc_dict(method_str, params_dic, verbose = False):
    params_str = json.dumps(params_dic)
    if verbose:
        log_debug('kodi_jsonrpc_dict() method_str "{}"'.format(method_str))
        log_debug('kodi_jsonrpc_dict() params_dic = \n{}'.format(pprint.pformat(params_dic)))
        log_debug('kodi_jsonrpc_dict() params_str "{}"'.format(params_str))

    # --- Do query ---
    header = '"id" : 1, "jsonrpc" : "2.0"'
    query_str = '{{{}, "method" : "{}", "params" : {} }}'.format(header, method_str, params_str)
    response_json_str = xbmc.executeJSONRPC(query_str)

    # --- Parse JSON response ---
    response_dic = json.loads(response_json_str)
    if 'error' in response_dic:
        result_dic = response_dic['error']
        log_warning('kodi_jsonrpc_dict() JSONRPC ERROR {}'.format(result_dic['message']))
    else:
        result_dic = response_dic['result']
    if verbose:
        log_debug('kodi_jsonrpc_dict() result_dic = \n{}'.format(pprint.pformat(result_dic)))

    return result_dic

# Displays a text window and requests a monospaced font.
# v18 Leia change: New optional param added usemono.
def kodi_display_text_window_mono(window_title, info_text):
    xbmcgui.Dialog().textviewer(window_title, info_text, True)

# Displays a text window with a proportional font (default).
def kodi_display_text_window(window_title, info_text):
    xbmcgui.Dialog().textviewer(window_title, info_text)

# -------------------------------------------------------------------------------------------------
# Astraction layer for settings to easy the Leia-Matrix transition.
# Settings are only read once on every execution and they are not performance critical.
# -------------------------------------------------------------------------------------------------
def kodi_get_int_setting(cfg, setting_str):
    return int(cfg.__addon__.getSetting(setting_str))

def kodi_get_float_setting_as_int(cfg, setting_str):
    return int(round(float(cfg.__addon__.getSetting(setting_str))))

def kodi_get_bool_setting(cfg, setting_str):
    return True if cfg.__addon__.getSetting(setting_str) == 'true' else False

def kodi_get_str_setting(cfg, setting_str):
    return cfg.__addon__.getSetting(setting_str).decode('utf-8')

# -------------------------------------------------------------------------------------------------
# Determine Kodi version and create some constants to allow version-dependent code.
# This if useful to work around bugs in Kodi core.
# -------------------------------------------------------------------------------------------------
# Version constants. Minimum required version is Kodi Krypton.
KODI_VERSION_ISENGARD = 15
KODI_VERSION_JARVIS = 16
KODI_VERSION_KRYPTON = 17
KODI_VERSION_LEIA = 18
KODI_VERSION_MATRIX = 19

def kodi_get_Kodi_major_version():
    r_dic = kodi_jsonrpc_dict('Application.GetProperties', {'properties' : ['version']})
    return int(r_dic['version']['major'])

# Execute the Kodi version query when module is loaded and store results in global variable.
kodi_running_version = kodi_get_Kodi_major_version()

# -------------------------------------------------------------------------------------------------
# If running with Kodi Python interpreter use Kodi proper functions.
# If running with the standard Python interpreter use replacement functions.
# 
# Functions here in the same order as in the Function List browser.
# -------------------------------------------------------------------------------------------------
if KODI_RUNTIME_AVAILABLE_UTILS:
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

# -------------------------------------------------------------------------------------------------
# Kodi GUI error reporting.
# * Errors can be reported up in the function backtrace with `if not st_dic['status']: return` after
#   every function call.
# * Warnings and non-fatal messages are printed in the callee function.
# * If st_dic['status'] is True but st_dic['dialog'] is not KODI_MESSAGE_NONE then display
#   the message but do not abort execution (success information message).
# * When kodi_display_status_message() is used to display the last message on a chaing of
#   function calls it is irrelevant its return value because addon always finishes.
#
# How to use:
# def high_level_function():
#     st_dic = kodi_new_status_dic()
#     function_that_does_something_that_may_fail(..., st_dic)
#     if kodi_display_status_message(st_dic): return # Display error message and abort addon execution.
#     if not st_dic['status']: return # Alternative code to return to caller function.
#
# def function_that_does_something_that_may_fail(..., st_dic):
#     code_that_fails
#     kodi_set_error_status(st_dic, 'Message') # Or change st_dic manually.
#     return
# -------------------------------------------------------------------------------------------------
KODI_MESSAGE_NONE        = 100
# Kodi notifications must be short.
KODI_MESSAGE_NOTIFY      = 200
KODI_MESSAGE_NOTIFY_WARN = 300
# Kodi OK dialog to display a message.
KODI_MESSAGE_DIALOG      = 400

# If st_dic['abort'] is False then everything is OK.
# If st_dic['abort'] is True then execution must be aborted and error displayed.
# Success message can also be displayed (st_dic['abort'] False and 
# st_dic['dialog'] is different from KODI_MESSAGE_NONE).
def kodi_new_status_dic():
    return {
        'abort' : False,
        'dialog' : KODI_MESSAGE_NONE,
        'msg' : '',
    }

# Display an error message in the GUI.
# Returns True in case of error and addon must abort immediately.
# Returns False if no error.
def kodi_display_status_message(st_dic):
    # Display (error) message and return status.
    if st_dic['dialog'] == KODI_MESSAGE_NONE:
        pass
    elif st_dic['dialog'] == KODI_MESSAGE_NOTIFY:
        kodi_notify(st_dic['msg'])
    elif st_dic['dialog'] == KODI_MESSAGE_NOTIFY_WARN:
        kodi_notify(st_dic['msg'])
    elif st_dic['dialog'] == KODI_MESSAGE_DIALOG:
        kodi_dialog_OK(st_dic['msg'])
    else:
        raise TypeError('st_dic["dialog"] = {}'.format(st_dic['dialog']))

    return st_dic['abort']

def kodi_is_error_status(st_dic): return st_dic['abort']

# Utility function to write more compact code.
# By default error messages are shown in modal OK dialogs.
def kodi_set_error_status(st_dic, msg, dialog = KODI_MESSAGE_DIALOG):
    st_dic['abort'] = True
    st_dic['msg'] = msg
    st_dic['dialog'] = dialog

def kodi_reset_status(st_dic):
    st_dic['abort'] = False
    st_dic['msg'] = ''
    st_dic['dialog'] = KODI_MESSAGE_NONE

# -------------------------------------------------------------------------------------------------
# Alternative Kodi GUI error reporting.
# This is a more phytonic way of reporting errors than using st_dic.
# -------------------------------------------------------------------------------------------------
# Create a Exception-derived class and use that for reporting.
#
# Example code:
# try:
#     function_that_may_fail()
# except KodiAddonError as ex:
#     kodi_display_status_message(ex)
# else:
#     kodi_notify('Operation completed')
#
# def function_that_may_fail():
#     raise KodiAddonError(msg, dialog)
class KodiAddonError(Exception):
    def __init__(self, msg, dialog = KODI_MESSAGE_DIALOG):
        self.dialog = dialog
        self.msg = msg

    def __str__(self):
        return self.msg

def kodi_display_exception(ex):
    st_dic = kodi_new_status_dic()
    st_dic['abort'] = True
    st_dic['dialog'] = ex.dialog
    st_dic['msg'] = ex.msg
    kodi_display_status_message(st_dic)
