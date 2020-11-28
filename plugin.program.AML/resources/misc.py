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

# Advanced MAME Launcher miscellaneous functions.
#
# The idea if this module is to share it between AEL and AML.
# Functions in this module only depend on the Python standard library.
# This module can be loaded anywhere without creating circular dependencies.
# Optionally this module can include utils.py to use the log_*() functions but better avoid it.

# --- Addon modules ---
from .constants import *

# --- Python standard library ---
import re
import time

# -------------------------------------------------------------------------------------------------
# Strings and text functions.
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
def text_XML(tag_name, tag_text, num_spaces = 2):
    if tag_text:
        tag_text = text_escape_XML(tag_text)
        line = '{}<{}>{}</{}>\n'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        # Empty tag.
        line = '{}<{} />\n'.format(' ' * num_spaces, tag_name)

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
    table_str_list.append('{}'.format('-' * total_size))

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
            str_size = len('{}'.format(cell_str))
            if str_size > col_max_size: col_max_size = str_size
        col_sizes[j] = col_max_size

    return col_sizes

def text_str_list_size(str_list):
    max_str_size = 0
    for str_item in str_list:
        str_size = len('{}'.format(str_item))
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_str_dic_max_size(dictionary_list, dic_key, title_str = ''):
    max_str_size = 0
    for item in dictionary_list:
        str_size = len('{}'.format(item[dic_key]))
        if str_size > max_str_size: max_str_size = str_size
    if title_str:
        str_size = len(title_str)
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_print_padded_left(text_line, text_max_size):
    formatted_str = '{}'.format(text_line)
    padded_str =  formatted_str + ' ' * (text_max_size - len(formatted_str))

    return padded_str

def text_print_padded_right(text_line, text_max_size):
    formatted_str = '{}'.format(text_line)
    padded_str = ' ' * (text_max_size - len(formatted_str)) + formatted_str

    return padded_str

# --- BEGIN code in dev-misc/test_color_tag_remove.py ---------------------------------------------
def text_remove_color_tags_slist(slist):
    # Iterate list of strings and remove the following tags
    # 1) [COLOR colorname]
    # 2) [/COLOR]
    #
    # Modifying a list is OK when iterating the list. However, do not change the size of the
    # list when iterating.
    for i, s in enumerate(slist):
        s_temp, modified = s, False

        # Remove all [COLOR colorname] tags.
        fa_list = re.findall('(\[COLOR \w+?\])', s_temp)
        fa_set = set(fa_list)
        if len(fa_set) > 0:
            modified = True
            for m in fa_set:
                s_temp = s_temp.replace(m, '')

        # Remove all [/COLOR]
        if s_temp.find('[/COLOR]') >= 0:
            s_temp = s_temp.replace('[/COLOR]', '')
            modified = True

        # Update list
        if modified:
            slist[i] = s_temp
# --- END code in dev-misc/test_color_tag_remove.py -----------------------------------------------

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
    base = hashlib.md5(text_type(t1 + t2))
    sid = base.hexdigest()

    return sid

# See https://docs.python.org/3.8/library/time.html#time.gmtime
def misc_time_to_str(secs):
    return time.strftime('%a %d %b %Y %H:%M:%S', time.localtime(secs))

#
# All version numbers must be less than 100, except the major version.
# AML version is like this: aa.bb.cc[-|~][alpha[dd]|beta[dd]]
# It gets converted to: aa.bb.cc Rdd -> int aab,bcc,Rdd
# The number 2,147,483,647 is the maximum positive value for a 32-bit signed binary integer.
#
# aa.bb.cc.Xdd    formatted aab,bcc,Xdd
#  |  |  | | |--> Beta/Alpha flag 0, 1, ..., 99
#  |  |  | |----> Release kind flag 
#  |  |  |        5 for non-beta, non-alpha, non RC versions.
#  |  |  |        2 for RC versions
#  |  |  |        1 for beta versions
#  |  |  |        0 for alpha versions
#  |  |  |------> Build version 0, 1, ..., 99
#  |  |---------> Minor version 0, 1, ..., 99
#  |------------> Major version 0, ..., infinity
#
def misc_addon_version_str_to_int(AML_version_str):
    # log_debug('misc_addon_version_str_to_int() AML_version_str = "{}"'.format(AML_version_str))
    version_int = 0
    # Parse versions like "0.9.8[-|~]alpha[jj]"
    m_obj_alpha_n = re.search('^(\d+?)\.(\d+?)\.(\d+?)[\-\~](alpha|beta)(\d+?)$', AML_version_str)
    # Parse versions like "0.9.8[-|~]alpha"
    m_obj_alpha = re.search('^(\d+?)\.(\d+?)\.(\d+?)[\-\~](alpha|beta)$', AML_version_str)
    # Parse versions like "0.9.8"
    m_obj_standard = re.search('^(\d+?)\.(\d+?)\.(\d+?)$', AML_version_str)

    if m_obj_alpha_n:
        major    = int(m_obj_alpha_n.group(1))
        minor    = int(m_obj_alpha_n.group(2))
        build    = int(m_obj_alpha_n.group(3))
        kind_str = m_obj_alpha_n.group(4)
        beta     = int(m_obj_alpha_n.group(5))
        if kind_str == 'alpha':
            release_flag = 0
        elif kind_str == 'beta':
            release_flag = 1
        # log_debug('misc_addon_version_str_to_int() major        {}'.format(major))
        # log_debug('misc_addon_version_str_to_int() minor        {}'.format(minor))
        # log_debug('misc_addon_version_str_to_int() build        {}'.format(build))
        # log_debug('misc_addon_version_str_to_int() kind_str     {}'.format(kind_str))
        # log_debug('misc_addon_version_str_to_int() release_flag {}'.format(release_flag))
        # log_debug('misc_addon_version_str_to_int() beta         {}'.format(beta))
        version_int = major * 10000000 + minor * 100000 + build * 1000 + release_flag * 100 + beta
    elif m_obj_alpha:
        major    = int(m_obj_alpha.group(1))
        minor    = int(m_obj_alpha.group(2))
        build    = int(m_obj_alpha.group(3))
        kind_str = m_obj_alpha.group(4)
        if kind_str == 'alpha':
            release_flag = 0
        elif kind_str == 'beta':
            release_flag = 1
        # log_debug('misc_addon_version_str_to_int() major        {}'.format(major))
        # log_debug('misc_addon_version_str_to_int() minor        {}'.format(minor))
        # log_debug('misc_addon_version_str_to_int() build        {}'.format(build))
        # log_debug('misc_addon_version_str_to_int() kind_str     {}'.format(kind_str))
        # log_debug('misc_addon_version_str_to_int() release_flag {}'.format(release_flag))
        version_int = major * 10000000 + minor * 100000 + build * 1000 + release_flag * 100
    elif m_obj_standard:
        major = int(m_obj_standard.group(1))
        minor = int(m_obj_standard.group(2))
        build = int(m_obj_standard.group(3))
        release_flag = 5
        # log_debug('misc_addon_version_str_to_int() major {}'.format(major))
        # log_debug('misc_addon_version_str_to_int() minor {}'.format(minor))
        # log_debug('misc_addon_version_str_to_int() build {}'.format(build))
        version_int = major * 10000000 + minor * 100000 + build * 1000 + release_flag * 100
    else:
        # log_debug('AML addon version "{}" cannot be parsed.'.format(AML_version_str))
        raise TypeError('misc_addon_version_str_to_int() failure')
    # log_debug('misc_addon_version_str_to_int() version_int = {}'.format(version_int))

    return version_int
