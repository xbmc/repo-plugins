# -*- coding: utf-8 -*-

# Copyright (c) 2016-2021 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator/MAME Launcher utility functions.
#
# The idea if this module is to share it between AEL and AML.
#
# All functions that depends on Kodi modules are here. This includes IO functions
# and logging functions. Misc function that do not depend on Kodi modules are
# located in the misc module.
#
# Low-level filesystem and IO functions are here (FileName class).
# db module (formaer disk_IO module) contains high level IO functions.
#
# When Kodi modules are not available replacements can be provided. This is useful
# to use addon modules with CPython for testing or debugging.
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
    import xbmcaddon
    import xbmcgui
    import xbmcplugin
except:
    KODI_RUNTIME_AVAILABLE_UTILS = False
else:
    KODI_RUNTIME_AVAILABLE_UTILS = True

# --- Python standard library ---
# Check what modules are really used and remove not used ones.
import collections
import errno
import fnmatch
import io
import json
import math
import os
import re
import shutil
import string
import sys
import threading
import time
import xml.etree.ElementTree
import zlib

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
#   FileName.getPathNoExt()     Full path with no extension                   /home/Wintermute/Sonic
#   FileName.getDir()           Directory name of file. Does not end in '/'   /home/Wintermute/
#   FileName.getBase()          File name with no path                        Sonic.zip
#   FileName.getBaseNoExt()     File name with no path and no extension       Sonic
#   FileName.getExt()           File extension                                .zip
# -------------------------------------------------------------------------------------------------
class FileName:
    # pathString must be a Unicode string object
    def __init__(self, pathString):
        self.originalPath = pathString
        self.path = pathString

        # --- Path transformation ---
        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

        elif self.originalPath.lower().startswith('special:'):
            self.path = xbmc.translatePath(self.path)

    def _join_raw(self, arg):
        self.path = os.path.join(self.path, arg)
        self.originalPath = os.path.join(self.originalPath, arg)
        return self

    # Appends a string to path. Returns self FileName object
    # Instead of append() use pappend(). This will avoid using string.append() instead of FileName.append()
    def pappend(self, arg):
        self.path = self.path + arg
        self.originalPath = self.originalPath + arg
        return self

    # Behaves like os.path.join(). Returns a FileName object
    # Instead of join() use pjoin(). This will avoid using string.join() instead of FileName.join()
    def pjoin(self, *args):
        child = FileName(self.originalPath)
        for arg in args:
            child._join_raw(arg)
        return child

    # Behaves like os.path.join()
    #
    # See http://blog.teamtreehouse.com/operator-overloading-python
    # other is a FileName object. other originalPath is expected to be a subdirectory (path
    # transformation not required)
    # def __add__(self, other):
    #     current_path = self.originalPath
    #     if type(other) is FileName:      other_path = other.originalPath
    #     elif type(other) is text_type:   other_path = other
    #     elif type(other) is binary_type: other_path = other.decode('utf-8')
    #     else: raise NameError('Unknown type for overloaded + in FileName object')
    #     new_path = os.path.join(current_path, other_path)
    #     child    = FileName(new_path)
    #     return child

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

    def getPathNoExt(self):
        root, ext = os.path.splitext(self.path)
        return root

    def getDir(self):
        return os.path.dirname(self.path)

    def getBase(self):
        return os.path.basename(self.path)

    def getBaseNoExt(self):
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

# How to report errors in these IO functions? That's the eternal question.
# 1) Raise an exception and make the addon crash? Crashes are always reported in the GUI.
# 2) Use AEL approach and report status in a control dictionary? Caller code is responsible
#    to report the error in the GUI.
#
# A convention must be chosen.
# A) Low-level, basic IO functions raise KodiAddonError exception. However, any other function
#    uses st_dic to report errors.
# B) All functions use st_dic. IO functions are responsible to catch exceptions and fill st_dic.
# C) Do not use st_dic at all, only use KodiAddonError.

# -------------------------------------------------------------------------------------------------
# Low level filesystem functions.
# -------------------------------------------------------------------------------------------------
def utils_get_fs_encoding():
    fs_encoding = sys.getfilesystemencoding()
    return fs_encoding

def utils_copy_file(source_str, dest_str):
    if ADDON_RUNNING_PYTHON_2:
        source_bytes = source_str.decode(utils_get_fs_encoding(), 'ignore')
        dest_bytes = dest_str.decode(utils_get_fs_encoding(), 'ignore')
        shutil.copy(source_bytes, dest_bytes)
    elif ADDON_RUNNING_PYTHON_3:
        shutil.copy(source_str, dest_str)
    else:
        raise TypeError('Undefined Python runtime version.')

# Always write UNIX end of lines regarding of the operating system.
def utils_write_str_to_file(filename, full_string):
    log_debug('utils_write_str_to_file() File "{}"'.format(filename))
    with io.open(filename, 'wt', encoding = 'utf-8', newline = '\n') as f:
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

# If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail.
# Returns None if error.
# Returns xml_tree = xml.etree.ElementTree.parse() if success.
def utils_load_XML_to_ET(filename):
    log_debug('utils_load_XML_to_ET() Loading {}'.format(filename))
    xml_tree = None
    try:
        xml_tree = xml.etree.ElementTree.parse(filename)
    except IOError as ex:
        log_debug('utils_load_XML_to_ET() (IOError) errno = {}'.format(ex.errno))
        # log_debug(text_type(ex.errno.errorcode))
        # No such file or directory
        if ex.errno == errno.ENOENT:
            log_error('utils_load_XML_to_ET() (IOError) ENOENT No such file or directory.')
        else:
            log_error('utils_load_XML_to_ET() (IOError) Unhandled errno value.')
    except xml.etree.ElementTree.ParseError as ex:
        log_error('utils_load_XML_to_ET() (ParseError) Exception parsing {}'.format(filename))
        log_error('utils_load_XML_to_ET() (ParseError) {}'.format(text_type(ex)))
    return xml_tree

# -------------------------------------------------------------------------------------------------
# JSON write/load
# -------------------------------------------------------------------------------------------------
# Replace fs_load_JSON_file with this.
def utils_load_JSON_file(json_filename, default_obj = {}, verbose = True):
    # If file does not exist return default object (usually empty object)
    json_data = default_obj
    if not os.path.isfile(json_filename):
        log_warning('utils_load_JSON_file() Not found "{}"'.format(json_filename))
        return json_data
    # Load and parse JSON file.
    if verbose: log_debug('utils_load_JSON_file() "{}"'.format(json_filename))
    with io.open(json_filename, 'rt', encoding = 'utf-8') as file:
        try:
            json_data = json.load(file)
        except ValueError as ex:
            log_error('utils_load_JSON_file() ValueError exception in json.load() function')

    return json_data

# This consumes a lot of memory but it is fast.
# See https://stackoverflow.com/questions/24239613/memoryerror-using-json-dumps
#
# Note that there is a bug in the json module where the ensure_ascii=False flag can produce
# a mix of unicode and str objects.
# See http://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
def utils_write_JSON_file(json_filename, json_data, verbose = True, pprint = False):
    l_start = time.time()
    if verbose: log_debug('utils_write_JSON_file() "{}"'.format(json_filename))

    # Choose JSON iterative encoder or normal encoder.
    if OPTION_LOWMEM_WRITE_JSON:
        if verbose: log_debug('utils_write_JSON_file() Using OPTION_LOWMEM_WRITE_JSON option')
        if pprint:
            jobj = json.JSONEncoder(ensure_ascii = False, sort_keys = True,
                indent = JSON_INDENT, separators = JSON_SEP)
        else:
            if OPTION_COMPACT_JSON:
                jobj = json.JSONEncoder(ensure_ascii = False, sort_keys = True)
            else:
                jobj = json.JSONEncoder(ensure_ascii = False, sort_keys = True,
                    indent = JSON_INDENT, separators = JSON_SEP)
    else:
        # Parameter pprint == True overrides option OPTION_COMPACT_JSON.
        if pprint:
            f_data = text_type(json.dumps(json_data, ensure_ascii = False, sort_keys = True,
                indent = JSON_INDENT, separators = JSON_SEP))
        else:
            if OPTION_COMPACT_JSON:
                f_data = text_type(json.dumps(json_data, ensure_ascii = False, sort_keys = True))
            else:
                f_data = text_type(json.dumps(json_data, ensure_ascii = False, sort_keys = True,
                    indent = JSON_INDENT, separators = JSON_SEP))

    # Write JSON to disk
    try:
        with io.open(json_filename, 'wt', encoding = 'utf-8') as file:
            if OPTION_LOWMEM_WRITE_JSON:
                # Chunk by chunk JSON writer, uses less memory but takes longer.
                for chunk in jobj.iterencode(json_data):
                    file.write(text_type(chunk))
            else:
                file.write(f_data)
    except OSError:
        kodi_notify(ADDON_LONG_NAME, 'Cannot write {} file (OSError)'.format(json_filename))
    except IOError:
        kodi_notify(ADDON_LONG_NAME, 'Cannot write {} file (IOError)'.format(json_filename))
    l_end = time.time()
    if verbose:
        write_time_s = l_end - l_start
        log_debug('utils_write_JSON_file() Writing time {:f} s'.format(write_time_s))

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
        self.output_dic = utils_load_JSON_file(self.json_filename)

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
        log_warning('utils_file_cache_add_dir() Empty dir_str. Exiting')
        return
    dir_FN = FileName(dir_str)
    if not dir_FN.exists():
        log_debug('utils_file_cache_add_dir() Does not exist "{}"'.format(dir_str))
        file_cache[dir_str] = set()
        return
    if not dir_FN.isdir():
        log_warning('utils_file_cache_add_dir() Not a directory "{}"'.format(dir_str))
        return
    if verbose:
        # log_debug('utils_file_cache_add_dir() Scanning OP "{}"'.format(dir_FN.getOriginalPath()))
        log_debug('utils_file_cache_add_dir() Scanning  P "{}"'.format(dir_FN.getPath()))
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
            # In the cache always store paths as '/' and not as '\'
            cache_file = cache_file.replace('\\', '/')
            # Remove '/' character at the beginning of the file. If the directory dir_str
            # is like '/example/dir/' then the slash at the beginning will be removed. However,
            # if dir_str is like '/example/dir' it will be present.
            if cache_file.startswith('/'): cache_file = cache_file[1:]
            file_list.append(cache_file)
    file_set = set(file_list)
    if verbose:
        # for file in file_set: log_debug('File "{}"'.format(file))
        log_debug('utils_file_cache_add_dir() Adding {} files to cache'.format(len(file_set)))
    file_cache[dir_str] = file_set

# See utils_look_for_file() documentation below.
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

# Given the image path, image filename with no extension and a list of file
# extensions search for a file.
#
# rootPath       -> FileName object
# filename_noext -> Unicode string
# file_exts      -> list of extensions with no dot ['zip', 'rar']
#
# Returns a FileName object if a valid filename is found.
# Returns None if no file was found.
def utils_look_for_file(rootPath, filename_noext, file_exts):
    for ext in file_exts:
        file_path = rootPath.pjoin(filename_noext + '.' + ext)
        if file_path.exists(): return file_path
    return None

# -------------------------------------------------------------------------------------------------
# Logging functions.
# AEL never uses LOG_FATAL. Fatal error in my addons use LOG_ERROR. When an ERROR message is
# printed the addon must stop execution and exit.
# Kodi Matrix has changed the log levels.
# Valid set of log levels should now be: DEBUG, INFO, WARNING, ERROR and FATAL
#
# @python_v17 Default level changed from LOGNOTICE to LOGDEBUG
# @python_v19 Removed LOGNOTICE (use LOGINFO) and LOGSEVERE (use LOGFATAL)
#
# https://forum.kodi.tv/showthread.php?tid=344263&pid=2943703#pid2943703
# https://github.com/xbmc/xbmc/pull/17730
# -------------------------------------------------------------------------------------------------
# Constants
LOG_ERROR   = 0
LOG_WARNING = 1
LOG_INFO    = 2
LOG_DEBUG   = 3

# Internal globals
current_log_level = LOG_INFO

def set_log_level(level):
    global current_log_level
    current_log_level = level

def log_variable(var_name, var):
    if current_log_level < LOG_DEBUG: return
    log_text = '{} DUMP : Dumping variable "{}"\n{}'.format(ADDON_SHORT_NAME,
        var_name, pprint.pformat(var))
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

# For Unicode stuff in Kodi log see https://github.com/romanvm/kodi.six
def log_debug_KR(text_line):
    if current_log_level < LOG_DEBUG: return

    # If it is bytes we assume it's "utf-8" encoded.
    # will fail if called with other encodings (latin, etc).
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')

    # At this point we are sure text_line is a Unicode string.
    # Kodi functions (Python 3) require Unicode strings as arguments.
    # Kodi functions (Python 2) require UTF-8 encoded bytes as arguments.
    log_text = ADDON_SHORT_NAME + ' DEBUG: ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_info_KR(text_line):
    if current_log_level < LOG_INFO: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = ADDON_SHORT_NAME + ' INFO : ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGNOTICE)

def log_warning_KR(text_line):
    if current_log_level < LOG_WARNING: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = ADDON_SHORT_NAME + ' WARN : ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGWARNING)

def log_error_KR(text_line):
    if current_log_level < LOG_ERROR: return
    if isinstance(text_line, binary_type): text_line = text_line.decode('utf-8')
    log_text = ADDON_SHORT_NAME + ' ERROR: ' + text_line
    xbmc.log(log_text.encode('utf-8'), level = xbmc.LOGERROR)

# Replacement functions when running outside Kodi with the standard Python interpreter.
def log_debug_Python(text_line): print(text_line)

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
def kodi_dialog_OK(text, title = ADDON_LONG_NAME):
    xbmcgui.Dialog().ok(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno(text, title = ADDON_LONG_NAME):
    return xbmcgui.Dialog().yesno(title, text)

# Returns True is YES was pressed, returns False if NO was pressed or dialog canceled.
def kodi_dialog_yesno_custom(text, yeslabel_str, nolabel_str, title = ADDON_LONG_NAME):
    return xbmcgui.Dialog().yesno(title, text, yeslabel = yeslabel_str, nolabel = nolabel_str)

def kodi_dialog_yesno_timer(text, timer_ms = 30000, title = ADDON_LONG_NAME):
    return xbmcgui.Dialog().yesno(title, text, autoclose = timer_ms)

# Returns a directory. See https://codedocs.xyz/AlwinEsch/kodi
#
# This supports directories, files, images and writable directories.
# xbmcgui.Dialog().browse(type, heading, shares[, mask, useThumbs, treatAsFolder, defaultt, enableMultiple])
#
# This supports files and images only.
# xbmcgui.Dialog().browseMultiple(type, heading, shares[, mask, useThumbs, treatAsFolder, defaultt])
# 
# This supports directories, files, images and writable directories.
# xbmcgui.Dialog().browseSingle(type, heading, shares[, mask, useThumbs, treatAsFolder, defaultt])
#
# shares   string or unicode - from sources.xml
# "files"  list file sources (added through filemanager)
# "local"  list local drives
# ""       list local drives and network shares

# Returns a directory.
def kodi_dialog_get_directory(d_heading, d_dir = ''):
    if d_dir:
        ret = xbmcgui.Dialog().browse(0, d_heading, '', defaultt = d_dir)
    else:
        ret =  xbmcgui.Dialog().browse(0, d_heading, '')

    return ret.decode('utf-8')

# Mask is supported only for files.
# mask  [opt] string or unicode - '|' separated file mask. (i.e. '.jpg|.png')
#
# KODI BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
# Fixed in Krypton Beta 6 http://forum.kodi.tv/showthread.php?tid=298161
def kodi_dialog_get_file(d_heading, mask = '', default_file = ''):
    if mask and default_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask, defaultt = default_file)
    elif default_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', defaultt = default_file)
    elif mask:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask)
    else:
        ret = xbmcgui.Dialog().browse(1, d_heading, '')

    return ret.decode('utf-8')

def kodi_dialog_get_image(d_heading, mask = '', default_file = ''):
    if mask and default_file:
        ret = xbmcgui.Dialog().browse(2, d_heading, '', mask = mask, defaultt = default_file)
    elif default_file:
        ret = xbmcgui.Dialog().browse(2, d_heading, '', defaultt = default_file)
    elif mask:
        ret = xbmcgui.Dialog().browse(2, d_heading, '', mask = mask)
    else:
        ret = xbmcgui.Dialog().browse(2, d_heading, '')

    return ret.decode('utf-8')

def kodi_dialog_get_wdirectory(d_heading):
    return xbmcgui.Dialog().browse(3, d_heading, '').decode('utf-8')

# Select multiple versions of the avobe functions.
def kodi_dialog_get_file_multiple(d_heading, mask = '', d_file = ''):
    if mask and d_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask, defaultt = d_file, enableMultiple = True)
    elif d_file:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', defaultt = d_file, enableMultiple = True)
    elif mask:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', mask = mask, enableMultiple = True)
    else:
        ret = xbmcgui.Dialog().browse(1, d_heading, '', enableMultiple = True)

    # ret is a list
    for i in range(len(ret)):
        ret[i] = ret[i].decode('utf-8')

    return ret

# Displays a small box in the bottom right corner
def kodi_notify(text, title = ADDON_LONG_NAME, time = 5000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_INFO, time)

def kodi_notify_warn(text, title = ADDON_LONG_NAME, time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_WARNING, time)

# Do not use this function much because it is the same icon displayed when Python fails
# with an exception and that may confuse the user.
def kodi_notify_error(text, title = ADDON_LONG_NAME, time = 7000):
    xbmcgui.Dialog().notification(title, text, xbmcgui.NOTIFICATION_ERROR, time)

def kodi_refresh_container():
    log_debug('kodi_refresh_container()')
    xbmc.executebuiltin('Container.Refresh')

# Progress dialog that can be closed and reopened.
# Messages and progress in the dialog are always remembered, even if closed and reopened.
# If the dialog is canceled this class remembers it forever.
#
# Kodi Matrix change: Renamed option line1 to message. Removed option line2. Removed option line3.
# See https://forum.kodi.tv/showthread.php?tid=344263&pid=2933596#pid2933596
#
# --- Example 1 ---
# pDialog = KodiProgressDialog()
# pDialog.startProgress('Doing something...', step_total)
# for i in range():
#     pDialog.updateProgressInc()
#     # Do stuff...
# pDialog.endProgress()
class KodiProgressDialog(object):
    def __init__(self):
        self.heading = ADDON_LONG_NAME
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
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        except ZeroDivisionError:
            # Fix case when step_total is 0.
            self.step_total = 0.001
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        self.dialog_active = True
        self.message = message
        # In Leia and lower xbmcgui.DialogProgress().update() requires an int.
        if kodi_running_version >= KODI_VERSION_MATRIX:
            self.progressDialog.create(self.heading, self.message)
            self.progressDialog.update(self.progress)
        else:
            self.progressDialog.create(self.heading, self.message, ' ', ' ')
            self.progressDialog.update(int(self.progress))

    # Changes message and resets progress.
    def resetProgress(self, message, step_total = 100, step_counter = 0):
        if not self.dialog_active: raise TypeError
        self.step_total = step_total
        self.step_counter = step_counter
        try:
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        except ZeroDivisionError:
            # Fix case when step_total is 0.
            self.step_total = 0.001
            self.progress = math.floor((self.step_counter * 100) / self.step_total)
        self.message = message
        if kodi_running_version >= KODI_VERSION_MATRIX:
            self.progressDialog.update(self.progress, self.message)
        else:
            self.progressDialog.update(int(self.progress), self.message, ' ', ' ')

    # Update progress and optionally update message as well.
    def updateProgress(self, step_counter, message = None):
        if not self.dialog_active: raise TypeError
        self.step_counter = step_counter
        self.progress = math.floor((self.step_counter * 100) / self.step_total)
        if message is None:
            if kodi_running_version >= KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress)
            else:
                self.progressDialog.update(int(self.progress))
        else:
            if type(message) is not text_type: raise TypeError
            self.message = message
            if kodi_running_version >= KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress, self.message)
            else:
                self.progressDialog.update(int(self.progress), self.message, ' ', ' ')
        # DEBUG code
        # time.sleep(1)

    # Update progress, optionally update message as well, and autoincrements.
    # Progress is incremented AFTER dialog is updated.
    def updateProgressInc(self, message = None):
        if not self.dialog_active: raise TypeError
        self.progress = math.floor((self.step_counter * 100) / self.step_total)
        self.step_counter += 1
        if message is None:
            if kodi_running_version >= KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress)
            else:
                self.progressDialog.update(int(self.progress))
        else:
            if type(message) is not text_type: raise TypeError
            self.message = message
            if kodi_running_version >= KODI_VERSION_MATRIX:
                self.progressDialog.update(self.progress, self.message)
            else:
                self.progressDialog.update(int(self.progress), self.message, ' ', ' ')

    # Update dialog message but keep same progress.
    def updateMessage(self, message):
        if not self.dialog_active: raise TypeError
        if type(message) is not text_type: raise TypeError
        self.message = message
        if kodi_running_version >= KODI_VERSION_MATRIX:
            self.progressDialog.update(self.progress, self.message)
        else:
            self.progressDialog.update(int(self.progress), self.message, ' ', ' ')

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

    # Like endProgress() but do not completely fills the progress bar.
    def close(self):
        if not self.dialog_active: raise TypeError
        if self.progressDialog.iscanceled(): self.flag_dialog_canceled = True
        self.progressDialog.close()
        self.dialog_active = False

    # Reopens a previously closed dialog with close(), remembering the messages
    # and the progress it had when it was closed.
    def reopen(self):
        if self.dialog_active: raise TypeError
        if kodi_running_version >= KODI_VERSION_MATRIX:
            self.progressDialog.create(self.heading, self.message)
            self.progressDialog.update(self.progress)
        else:
            self.progressDialog.create(self.heading, self.message, ' ', ' ')
            self.progressDialog.update(int(self.progress))
        self.dialog_active = True

# Wrapper class for xbmcgui.Dialog().select(). Takes care of Kodi bugs.
# v17 (Krypton) Python API changes:
#   Preselect option added.
#   Added new option useDetails.
#   Allow listitems for parameter list
class KodiSelectDialog(object):
    def __init__(self, heading = ADDON_LONG_NAME, rows = [], preselect = -1, useDetails = False):
        self.heading = heading
        self.rows = rows
        self.preselect = preselect
        self.useDetails = useDetails
        self.dialog = xbmcgui.Dialog()

    def setHeading(self, heading): self.heading = heading

    def setRows(self, row_list): self.rows = row_list

    def setPreselect(self, preselect): self.preselect = preselect

    def setUseDetails(self, useDetails): self.useDetails = useDetails

    def executeDialog(self):
        # Kodi Krypton bug: if preselect is used then dialog never returns < 0 even if cancel
        # button is pressed. This bug has been solved in Leia.
        # See https://forum.kodi.tv/showthread.php?tid=337011
        if self.preselect >= 0 and kodi_running_version >= KODI_VERSION_LEIA:
            selection = self.dialog.select(self.heading, self.rows, useDetails = self.useDetails,
                preselect = self.preselect)
        else:
            selection = self.dialog.select(self.heading, self.rows, useDetails = self.useDetails)
        selection = None if selection < 0 else selection
        return selection

# Wrapper class for xbmc.Keyboard()
class KodiKeyboardDialog(object):
    def __init__(self, heading = 'Kodi keyboard', default_text = ''):
        self.heading = heading
        self.default_text = default_text
        self.keyboard = xbmc.Keyboard()

    def setHeading(self, heading): self.heading = heading

    def setDefaultText(self, default_text): self.default_text = default_text

    def executeDialog(self):
        self.keyboard.setHeading(self.heading)
        self.keyboard.setDefault(self.default_text)
        self.keyboard.doModal()

    def isConfirmed(self): return self.keyboard.isConfirmed()

    # Use a different name from getText() to avoid coding errors.
    def getData(self): return self.keyboard.getText().decode('utf-8')

# Wrapper function to get a text from the keyboard or None if the keyboard
# modal dialog was canceled.
def kodi_get_keyboard_text(heading = 'Kodi keyboard', default_text = ''):
    keyboard = KodiKeyboardDialog(heading, default_text)
    keyboard.executeDialog()
    if not keyboard.isConfirmed(): return None
    new_value_str = keyboard.getData().strip().decode('utf-8')
    return new_value_str

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
    xbmcgui.Dialog().textviewer(window_title, info_text.encode('utf-8'), True)

# Displays a text window with a proportional font (default).
def kodi_display_text_window(window_title, info_text):
    xbmcgui.Dialog().textviewer(window_title, info_text.encode('utf-8'))

# Displays a text window and requests a monospaced font.
# def kodi_display_text_window_mono(window_title, info_text):
#     log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
#     xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
#     xbmcgui.Dialog().textviewer(window_title, info_text)
#     log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
#     xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

# Displays a text window with a proportional font (default).
# def kodi_display_text_window(window_title, info_text):
#     xbmcgui.Dialog().textviewer(window_title, info_text)

# -------------------------------------------------------------------------------------------------
# Kodi addon functions
# -------------------------------------------------------------------------------------------------
class KodiAddon: pass

def kodi_addon_obj():
    addon = KodiAddon()

    # Get an instance of the Addon object and keep it.
    addon.addon = xbmcaddon.Addon()

    # Cache useful addon information.
    addon.info_id      = addon.addon.getAddonInfo('id').decode('utf-8')
    addon.info_name    = addon.addon.getAddonInfo('name').decode('utf-8')
    addon.info_version = addon.addon.getAddonInfo('version').decode('utf-8')
    addon.info_author  = addon.addon.getAddonInfo('author').decode('utf-8')
    addon.info_profile = addon.addon.getAddonInfo('profile').decode('utf-8')
    addon.info_type    = addon.addon.getAddonInfo('type').decode('utf-8')

    return addon

# -------------------------------------------------------------------------------------------------
# Abstraction layer for settings to easy the Leia-Matrix transition.
# Settings are only read once on every execution and they are not performance critical.
# -------------------------------------------------------------------------------------------------
def kodi_get_int_setting(cfg, setting_str):
    return int(cfg.addon.addon.getSetting(setting_str))

def kodi_get_float_setting_as_int(cfg, setting_str):
    return int(round(float(cfg.addon.addon.getSetting(setting_str))))

def kodi_get_bool_setting(cfg, setting_str):
    return True if cfg.addon.addon.getSetting(setting_str) == 'true' else False

def kodi_get_str_setting(cfg, setting_str):
    return cfg.addon.addon.getSetting(setting_str).decode('utf-8')

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

# -------------------------------------------------------------------------------------------------
# If running with Kodi Python interpreter use Kodi proper functions.
# If running with the standard Python interpreter use replacement functions.
# 
# Functions here in the same order as in the Function List browser.
# -------------------------------------------------------------------------------------------------
if KODI_RUNTIME_AVAILABLE_UTILS:
    log_debug   = log_debug_KR
    log_info    = log_info_KR
    log_warning = log_warning_KR
    log_error   = log_error_KR

    # Execute the Kodi version query when module is loaded and store results in global variable.
    kodi_running_version = kodi_get_Kodi_major_version()
else:
    log_debug   = log_debug_Python
    log_info    = log_info_Python
    log_warning = log_warning_Python
    log_error   = log_error_Python

    # We are using this module with the Python interpreter outside Kodi.
    # Simulate we are running a recent Kodi version.
    kodi_running_version = KODI_VERSION_MATRIX

# -------------------------------------------------------------------------------------------------
# Kodi useful definition
# -------------------------------------------------------------------------------------------------
# https://codedocs.xyz/AlwinEsch/kodi/group__kodi__guilib__listitem__iconoverlay.html
KODI_ICON_OVERLAY_NONE = 0
KODI_ICON_OVERLAY_RAR = 1
KODI_ICON_OVERLAY_ZIP = 2
KODI_ICON_OVERLAY_LOCKED = 3
KODI_ICON_OVERLAY_UNWATCHED = 4
KODI_ICON_OVERLAY_WATCHED = 5
KODI_ICON_OVERLAY_HD = 6

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

# Display an status/error message in the GUI.
# Note that it is perfectly OK to display an error message and not abort execution.
# Returns True in case of error and addon must abort/exit immediately.
# Returns False if no error.
#
# Example of use: if kodi_display_user_message(st_dic): return
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

# -------------------------------------------------------------------------------------------------
# Kodi specific stuff
# -------------------------------------------------------------------------------------------------
# About Kodi image cache
#
# See http://kodi.wiki/view/Caches_explained
# See http://kodi.wiki/view/Artwork
# See http://kodi.wiki/view/HOW-TO:Reduce_disk_space_usage
# See http://forum.kodi.tv/showthread.php?tid=139568 (What are .tbn files for?)
#
# Whenever Kodi downloads images from the internet, or even loads local images saved along
# side your media, it caches these images inside of ~/.kodi/userdata/Thumbnails/. By default,
# large images are scaled down to the default values shown below, but they can be sized
# even smaller to save additional space.

# Gets where in Kodi image cache an image is located.
# image_path is a Unicode string.
# cache_file_path is a Unicode string.
def kodi_get_cached_image_FN(image_path):
    THUMBS_CACHE_PATH = os.path.join(xbmc.translatePath('special://profile/' ), 'Thumbnails')

    # --- Get the Kodi cached image ---
    # This function return the cache file base name
    base_name = xbmc.getCacheThumbName(image_path)
    cache_file_path = os.path.join(THUMBS_CACHE_PATH, base_name[0], base_name)

    return cache_file_path

# Updates Kodi image cache for the image provided in img_path.
# In other words, copies the image img_path into Kodi cache entry.
# Needles to say, only update image cache if image already was on the cache.
# img_path is a Unicode string
def kodi_update_image_cache(img_path):
    # What if image is not cached?
    cached_thumb = kodi_get_cached_image_FN(img_path)
    log_debug('kodi_update_image_cache()       img_path {}'.format(img_path))
    log_debug('kodi_update_image_cache()   cached_thumb {}'.format(cached_thumb))

    # For some reason Kodi xbmc.getCacheThumbName() returns a filename ending in TBN.
    # However, images in the cache have the original extension. Replace TBN extension
    # with that of the original image.
    cached_thumb_root, cached_thumb_ext = os.path.splitext(cached_thumb)
    if cached_thumb_ext == '.tbn':
        img_path_root, img_path_ext = os.path.splitext(img_path)
        cached_thumb = cached_thumb.replace('.tbn', img_path_ext)
        log_debug('kodi_update_image_cache() U cached_thumb {}'.format(cached_thumb))

    # --- Check if file exists in the cache ---
    # xbmc.getCacheThumbName() seems to return a filename even if the local file does not exist!
    if not os.path.isfile(cached_thumb):
        log_debug('kodi_update_image_cache() Cached image not found. Doing nothing')
        return

    # --- Copy local image into Kodi image cache ---
    # See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
    log_debug('kodi_update_image_cache() Image found in cache. Updating Kodi image cache')
    log_debug('kodi_update_image_cache() copying {}'.format(img_path))
    log_debug('kodi_update_image_cache() into    {}'.format(cached_thumb))
    fs_encoding = sys.getfilesystemencoding()
    log_debug('kodi_update_image_cache() fs_encoding = "{}"'.format(fs_encoding))
    encoded_img_path = img_path.encode(fs_encoding, 'ignore')
    encoded_cached_thumb = cached_thumb.encode(fs_encoding, 'ignore')
    try:
        shutil.copy2(encoded_img_path, encoded_cached_thumb)
    except OSError:
        log_kodi_notify_warn('AEL warning', 'Cannot update cached image (OSError)')
        lod_error('Exception in kodi_update_image_cache()')
        lod_error('(OSError) Cannot update cached image')

    # Is this really needed?
    # xbmc.executebuiltin('XBMC.ReloadSkin()')
