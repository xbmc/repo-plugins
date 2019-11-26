# -*- coding: utf-8 -*-

# Advanced MAME Launcher miscellaneous functions.

# Copyright (c) 2016-2019 Wintermute0110 <wintermute0110@gmail.com>
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
import sys
import os
import shutil
import time
import random
import hashlib
import urlparse
import re
import string
import fnmatch

# --- Kodi modules ---
# >> FileName class uses xbmc.translatePath()
try:
    import xbmc
    KODI_RUNTIME_AVAILABLE_UTILS = True
except:
    KODI_RUNTIME_AVAILABLE_UTILS = False

# --- AEL modules ---
# This module must only include utils_kodi.py to avoid circular dependencies.
from .utils_kodi import *

# -------------------------------------------------------------------------------------------------
# Strings and text
# -------------------------------------------------------------------------------------------------
#
# If max_length == -1 do nothing (no length limit).
#
def text_limit_string(string, max_length):
  if max_length > 5 and len(string) > max_length:
    string = string[0:max_length-3] + '...'

  return string

#
# Given a Category/Launcher name clean it so the cleaned srt can be used as a filename.
#  1) Convert any non-printable character into '_'
#  2) Convert spaces ' ' into '_'
#
def text_title_to_filename_str(title_str):
    cleaned_str_1 = ''.join([i if i in string.printable else '_' for i in title_str])
    cleaned_str_2 = cleaned_str_1.replace(' ', '_')

    return cleaned_str_2

#
# Writes a XML text tag line, indented 2 spaces by default.
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
#
def XML_text(tag_name, tag_text, num_spaces = 2):
    if tag_text:
        tag_text = text_escape_XML(tag_text)
        line = '{0}<{1}>{2}</{3}>\n'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        # >> Empty tag    
        line = '{0}<{1} />\n'.format(' ' * num_spaces, tag_name)

    return line

#
# First row            column aligment 'right' or 'left'
# Second row           column titles
# Third and next rows  table data
#
# Returns a list of strings that must be joined with '\n'.join()
#
def text_render_table_str(table_str):
    rows = len(table_str)
    cols = len(table_str[0])
    table_str_list = []
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Table header ---
    row_str = ''
    for j in range(cols):
        if j < cols - 1:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j]) + '  '
        else:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j])
    table_str_list.append(row_str)
    # >> Table -----
    total_size = sum(col_sizes) + 2*(cols-1)
    table_str_list.append('{0}'.format('-' * total_size))

    # --- Data rows ---
    for i in range(2, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

#
# First row             column aligment 'right' or 'left'
# Second and next rows  table data
#
def text_render_table_str_NO_HEADER(table_str):
    rows = len(table_str)
    cols = len(table_str[0])
    table_str_list = []
    # >> Ignore row 0 when computing sizes.
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Data rows ---
    for i in range(1, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

#
# Removed Kodi colour tags before computing size (substitute by ''):
#   A) [COLOR skyblue]
#   B) [/COLOR]
#
def text_get_table_str_col_sizes(table_str, rows, cols):
    col_sizes = [0] * cols
    for j in range(cols):
        col_max_size = 0
        for i in range(1, rows):
            cell_str = re.sub(r'\[COLOR \w+?\]', '', table_str[i][j])
            cell_str = re.sub(r'\[/COLOR\]', '', cell_str)
            str_size = len('{0}'.format(cell_str))
            if str_size > col_max_size: col_max_size = str_size
        col_sizes[j] = col_max_size

    return col_sizes

def text_str_list_size(str_list):
    max_str_size = 0
    for str_item in str_list:
        str_size = len('{0}'.format(str_item))
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_str_dic_max_size(dictionary_list, dic_key, title_str = ''):
    max_str_size = 0
    for item in dictionary_list:
        str_size = len('{0}'.format(item[dic_key]))
        if str_size > max_str_size: max_str_size = str_size
    if title_str:
        str_size = len(title_str)
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_print_padded_left(str, str_max_size):
    formatted_str = '{0}'.format(str)
    padded_str =  formatted_str + ' ' * (str_max_size - len(formatted_str))

    return padded_str

def text_print_padded_right(str, str_max_size):
    formatted_str = '{0}'.format(str)
    padded_str = ' ' * (str_max_size - len(formatted_str)) + formatted_str

    return padded_str

def text_remove_color_tags_slist(slist):
    # Iterate list of strings and remove the following tags
    # 1) [COLOR colorname]
    # 2) [/COLOR]
    #
    # Modifying list already seen is OK when iterating the list. Do not change the size of the
    # list when iterating.
    for i, s in enumerate(slist):
        modified = False
        s_temp = s

        # >> Remove [COLOR colorname]
        m = re.search('(\[COLOR \w+?\])', s_temp)
        if m:
            s_temp = s_temp.replace(m.group(1), '')
            modified = True

        # >> Remove [/COLOR]
        if s_temp.find('[/COLOR]') >= 0:
            s_temp = s_temp.replace('[/COLOR]', '')
            modified = True

        # >> Update list
        if modified:
            slist[i] = s_temp

# Some XML encoding of special characters:
#   {'\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
#
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
# See https://wiki.python.org/moin/EscapingXml
# See https://github.com/python/cpython/blob/master/Lib/xml/sax/saxutils.py
# See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
#
def text_escape_XML(data_str):
    # Ampersand MUST BE replaced FIRST
    data_str = data_str.replace('&', '&amp;')
    data_str = data_str.replace('>', '&gt;')
    data_str = data_str.replace('<', '&lt;')

    data_str = data_str.replace("'", '&apos;')
    data_str = data_str.replace('"', '&quot;')
    
    # --- Unprintable characters ---
    data_str = data_str.replace('\n', '&#10;')
    data_str = data_str.replace('\r', '&#13;')
    data_str = data_str.replace('\t', '&#9;')

    return data_str

def text_unescape_XML(data_str):
    data_str = data_str.replace('&quot;', '"')
    data_str = data_str.replace('&apos;', "'")

    data_str = data_str.replace('&lt;', '<')
    data_str = data_str.replace('&gt;', '>')
    # Ampersand MUST BE replaced LAST
    data_str = data_str.replace('&amp;', '&')
    
    # --- Unprintable characters ---
    data_str = data_str.replace('&#10;', '\n')
    data_str = data_str.replace('&#13;', '\r')
    data_str = data_str.replace('&#9;', '\t')
    
    return data_str

#
# http://www.w3schools.com/tags/ref_urlencode.asp
#
def text_decode_HTML(s):
    # >> Must be done first
    s = s.replace('%25', '%')
    
    s = s.replace('%20', ' ')
    s = s.replace('%23', '#')
    s = s.replace('%26', '&')
    s = s.replace('%28', '(')
    s = s.replace('%29', ')')
    s = s.replace('%2C', ',')
    s = s.replace('%2F', '/')
    s = s.replace('%3B', ';')
    s = s.replace('%3A', ':')
    s = s.replace('%3D', '=')
    s = s.replace('%3F', '?')

    return s

def text_unescape_HTML(s):
    # >> Replace single HTML characters by their Unicode equivalent
    s = s.replace('<br>',   '\n')
    s = s.replace('<br/>',  '\n')
    s = s.replace('<br />', '\n')
    s = s.replace('&lt;',   '<')
    s = s.replace('&gt;',   '>')
    s = s.replace('&quot;', '"')
    s = s.replace('&nbsp;', ' ')
    s = s.replace('&copy;', '©')
    s = s.replace('&amp;',  '&') # >> Must be done last

    # >> Complex HTML entities. Single HTML chars must be already replaced.
    s = s.replace('&#039;', "'")
    s = s.replace('&#149;', "•")
    s = s.replace('&#x22;', '"')
    s = s.replace('&#x26;', '&')
    s = s.replace('&#x27;', "'")

    s = s.replace('&#x101;', "ā")
    s = s.replace('&#x113;', "ē")
    s = s.replace('&#x12b;', "ī")
    s = s.replace('&#x12B;', "ī")
    s = s.replace('&#x14d;', "ō")
    s = s.replace('&#x14D;', "ō")
    s = s.replace('&#x16b;', "ū")
    s = s.replace('&#x16B;', "ū")
    
    return s

#    
# Remove HTML tags
#
def text_remove_HTML_tags(s):
    p = re.compile(r'<.*?>')
    s = p.sub('', s)

    return s

def text_unescape_and_untag_HTML(s):
    s = text_unescape_HTML(s)
    s = text_remove_HTML_tags(s)

    return s

def text_dump_str_to_file(filename, full_string):
    file_obj = open(filename, 'w')
    file_obj.write(full_string.encode('utf-8'))
    file_obj.close()

# -------------------------------------------------------------------------------------------------
# ROM name cleaning and formatting
# -------------------------------------------------------------------------------------------------
#
# This function is used to clean the ROM name to be used as search string for the scraper.
#
# 1) Cleans ROM tags: [BIOS], (Europe), (Rev A), ...
# 2) Substitutes some characters by spaces
#
def text_format_ROM_name_for_scraping(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title = re.sub('\{.*?\}', '', title)
    
    title = title.replace('_', '')
    title = title.replace('-', '')
    title = title.replace(':', '')
    title = title.replace('.', '')
    title = title.strip()

    return title

#
# Format ROM file name when scraping is disabled.
# 1) Remove No-Intro/TOSEC tags (), [], {} at the end of the file
#
# title      -> Unicode string
# clean_tags -> bool
#
# Returns a Unicode string.
#
def text_format_ROM_title(title, clean_tags):
    #
    # Regexp to decompose a string in tokens
    #
    if clean_tags:
        reg_exp = '\[.+?\]\s?|\(.+?\)\s?|\{.+?\}|[^\[\(\{]+'
        tokens = re.findall(reg_exp, title)
        str_list = []
        for token in tokens:
            stripped_token = token.strip()
            if (stripped_token[0] == '[' or stripped_token[0] == '(' or stripped_token[0] == '{') and \
               stripped_token != '[BIOS]':
                continue
            str_list.append(stripped_token)
        cleaned_title = ' '.join(str_list)
    else:
        cleaned_title = title

    # if format_title:
    #     if (title.startswith("The ")): new_title = title.replace("The ","", 1)+", The"
    #     if (title.startswith("A ")): new_title = title.replace("A ","", 1)+", A"
    #     if (title.startswith("An ")): new_title = title.replace("An ","", 1)+", An"
    # else:
    #     if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The", 1))
    #     if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A", 1))
    #     if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An", 1))

    return cleaned_title

# -------------------------------------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------------------------------------
#
# Get extension of URL. Returns '' if not found.
#
def text_get_URL_extension(url):
    path = urlparse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    
    return ext

#
# Defaults to .jpg if URL extension cannot be determined
#
def text_get_image_URL_extension(url):
    path = urlparse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    ret = '.jpg' if ext == '' else ext

    return ret

# -------------------------------------------------------------------------------------------------
# File cache
# -------------------------------------------------------------------------------------------------
file_cache = {}

def misc_clear_file_cache(verbose = True):
    global file_cache
    if verbose: log_debug('misc_clear_file_cache() Clearing file cache')
    file_cache = {}

def misc_add_file_cache(dir_str, verbose = True):
    global file_cache

    # >> Create a set with all the files in the directory
    if not dir_str:
        log_warning('misc_add_file_cache() Empty dir_str. Exiting')
        return
    dir_FN = FileName(dir_str)
    if not dir_FN.exists():
        log_debug('misc_add_file_cache() Does not exist "{0}"'.format(dir_str))
        file_cache[dir_str] = set()
        return
    if not dir_FN.isdir():
        log_warning('misc_add_file_cache() Not a directory "{0}"'.format(dir_str))
        return
    if verbose:
        # log_debug('misc_add_file_cache() Scanning OP "{0}"'.format(dir_FN.getOriginalPath()))
        log_debug('misc_add_file_cache() Scanning  P "{0}"'.format(dir_FN.getPath()))
    # >> A recursive scanning function is needed. os.listdir() is not.
    # file_list = os.listdir(dir_FN.getPath())
    # >> os.walk() is recursive
    file_list = []
    root_dir_str = dir_FN.getPath()
    # >> For unicode errors in os.walk() see
    # >> https://stackoverflow.com/questions/21772271/unicodedecodeerror-when-performing-os-walk
    for root, dirs, files in os.walk(str(root_dir_str)):
        # log_debug('----------')
        # log_debug('root = {0}'.format(root))
        # log_debug('dirs = {0}'.format(unicode(dirs)))
        # log_debug('files = {0}'.format(unicode(files)))
        # log_debug('\n')
        for f in files:
            my_file = os.path.join(root, f).decode('utf-8')
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
        # for file in file_set: log_debug('File "{0}"'.format(file))
        log_debug('misc_add_file_cache() Adding {0} files to cache'.format(len(file_set)))
    file_cache[dir_str] = file_set

#
# See misc_look_for_file() documentation below.
#
def misc_search_file_cache(dir_str, filename_noext, file_exts):
    # Check for empty, unconfigured dirs
    if not dir_str: return None
    current_cache_set = file_cache[dir_str]
    # if filename_noext == '005':
    #     log_debug('misc_search_file_cache() Searching in "{0}"'.format(dir_str))
    #     log_debug('misc_search_file_cache() current_cache_set "{0}"'.format(unicode(current_cache_set)))
    for ext in file_exts:
        file_base = filename_noext + '.' + ext
        # log_debug('misc_search_file_cache() file_Base = "{0}"'.format(file_base))
        if file_base in current_cache_set:
            # log_debug('misc_search_file_cache() Found in cache')
            return FileName(dir_str).pjoin(file_base)

    return None

# -------------------------------------------------------------------------------------------------
# Misc stuff
# -------------------------------------------------------------------------------------------------
#
# Given the image path, image filename with no extension and a list of file extensions search for 
# a file.
#
# rootPath       -> FileName object
# filename_noext -> Unicode string
# file_exts      -> list of extenstions with no dot [ 'zip', 'rar' ]
#
# Returns a FileName object if a valid filename is found.
# Returns None if no file was found.
#
def misc_look_for_file(rootPath, filename_noext, file_exts):
    for ext in file_exts:
        file_path = rootPath.join(filename_noext + '.' + ext)
        if file_path.exists():
            return file_path

    return None

#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5( str(t1 + t2) )
    sid = base.hexdigest()

    return sid

# -------------------------------------------------------------------------------------------------
# Filesystem helper class
# This class always takes and returns Unicode string paths. Decoding to UTF-8 must be done in
# caller code.
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
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
    # Decomposes a file name path or directory into its constituents
    #   FileName.getOriginalPath()  Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath()          Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath_noext()    Full path with no extension                   /home/Wintermute/Sonic
    #   FileName.getDir()           Directory name of file. Does not end in '/'   /home/Wintermute/
    #   FileName.getBase()          File name with no path                        Sonic.zip
    #   FileName.getBase_noext()    File name with no path and no extension       Sonic
    #   FileName.getExt()           File extension                                .zip
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
