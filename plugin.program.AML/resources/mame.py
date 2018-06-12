# -*- coding: utf-8 -*-
# Advanced MAME Launcher MAME specific stuff
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

# --- Python standard library ---
from __future__ import unicode_literals
import zipfile as z
import struct
import binascii
import xml.etree.ElementTree as ET
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except:
    PILLOW_AVAILABLE = False

# --- AEL packages ---
from constants import *
from utils import *
try:
    from utils_kodi import *
except:
    from utils_kodi_standalone import *
from disk_IO import *

# -------------------------------------------------------------------------------------------------
# Data structures
# -------------------------------------------------------------------------------------------------
# >> Substitute notable drivers with a proper name
# >> Drivers are located in https://github.com/mamedev/mame/blob/master/src/mame/drivers/<driver_name>.cpp
mame_driver_name_dic = {
    # --- Atari ---
    'atari_s1.cpp' : 'Atari Generation/System 1',
    'atari_s2.cpp' : 'Atari Generation/System 2 and 3',
    'atarifb.cpp'  : 'Atari Football hardware',
    'atarittl.cpp' : 'Atari / Kee Games Driver',
    'asteroid.cpp' : 'Atari Asteroids hardware',
    'atetris.cpp'  : 'Atari Tetris hardware',
    # 'avalnche.cpp' : 'Atari XXXXX',
    # 'bzone.cpp'    : 'Atari XXXXX',
    # 'bwidow.cpp'   : 'Atari XXXXX',
    # 'boxer.cpp'    : 'Atari XXXXX',
    # 'canyon.cpp'   : 'Atari XXXXX',
    # 'cball.cpp'    : 'Atari XXXXX',
    # 'ccastles.cpp' : 'Atari XXXXX',
    'centiped.cpp' : 'Atari Centipede hardware',
    # 'cloak.cpp'    : 'Atari XXXXX',
    # 'destroyr.cpp' : 'Atari XXXXX',
    # 'mhavoc.cpp'   : 'Atari XXXXX',
    # 'mgolf.cpp'    : 'Atari XXXXX',
    'pong.cpp'     : 'Atari Pong hardware',

    # --- Capcom ---
    '1942.cpp'   : 'Capcom 1942',
    '1943.cpp'   : 'Capcom 1943: The Battle of Midway',
    'capcom.cpp' : 'Capcom A0015405',
    'gng.cpp'    : "Capcom Ghosts'n Goblins",
    'cps1.cpp'   : 'Capcom Play System 1',
    'cps2.cpp'   : 'Capcom Play System 2',
    'cps3.cpp'   : 'Capcom Play System 3',

    # --- Konami ---
    '88games.cpp'   : 'Konami 88 Games',
    'ajax.cpp'      : 'Konami GX770',
    'aliens.cpp'    : 'Konami Aliens',
    'asterix.cpp'   : 'Konami Asterix',
    'konamigv.cpp'  : 'Konami GV System (PSX Hardware)',
    'konblands.cpp' : 'Konami GX455 - Konami Badlands',
    'konamigx.cpp'  : 'Konami System GX',
    'konamim2.cpp'  : 'Konami M2 Hardware',

    # --- Midway ---
    'midtunit.cpp' : 'Midway T-unit system',
    'midvunit.cpp' : 'Midway V-Unit games',
    'midwunit.cpp' : 'Midway Wolf-unit system',
    'midxunit.cpp' : 'Midway X-unit system',
    'midyunit.cpp' : 'Williams/Midway Y/Z-unit system',
    'midzeus.cpp'  : 'Midway Zeus games',

    # --- Namco ---
    'galaxian.cpp' : 'Namco Galaxian-derived hardware',
    'namcops2.cpp' : 'Namco System 246 / System 256 (Sony PS2 based)',

    # --- SNK ---
    'neodriv.hxx' : 'SNK NeoGeo AES',
    'neogeo.cpp'  : 'SNK NeoGeo MVS',

    # --- Misc important drivers (important enough to have a fancy name!) ---
    'seta.cpp' : 'Seta Hardware',

    # --- SEGA ---
    # Less known boards
    'segajw.cpp'    : 'SEGA GOLDEN POKER SERIES',
    'segam1.cpp'    : 'SEGA M1 hardware',
    'segaufo.cpp'   : 'SEGA UFO Catcher, Z80 type hardware',
    # Boards listed in wikipedia
    # Sega Z80 board is included in galaxian.cpp
    'vicdual.cpp'   : 'SEGA VIC Dual Game board',
    'segag80r.cpp'  : 'SEGA G-80 raster hardware',
    'segag80v.cpp'  : 'SEGA G-80 vector hardware',
    'zaxxon.cpp'    : 'SEGA Zaxxon hardware',
    'segald.cpp'    : 'SEGA LaserDisc Hardware',
    'system1.cpp'   : 'SEGA System1 / System 2',
    'segac2.cpp'    : 'SEGA System C (System 14)',
    'segae.cpp'     : 'SEGA System E',
    'segas16a.cpp'  : 'SEGA System 16A',
    'segas16b.cpp'  : 'SEGA System 16B',
    'system16.cpp'  : 'SEGA System 16 / 18 bootlegs',
    'segas24.cpp'   : 'SEGA System 24',
    'segas18.cpp'   : 'SEGA System 18',
    'kyugo.cpp'     : 'SEGA Kyugo Hardware',
    'segahang.cpp'  : 'SEGA Hang On hardware', # AKA Sega Space Harrier
    'segaorun.cpp'  : 'SEGA Out Run hardware',
    'segaxbd.cpp'   : 'SEGA X-board',
    'segaybd.cpp'   : 'SEGA Y-board',
    'segas32.cpp'   : 'SEGA System 32',
    'model1.cpp'    : 'SEGA Model 1',
    'model2.cpp'    : 'SEGA Model 2',
    'model3.cpp'    : 'SEGA Model 3',
    'stv.cpp'       : 'SEGA ST-V hardware',
    'naomi.cpp'     : 'SEGA Naomi / Naomi 2 / Atomiswave',
    'segasp.cpp'    : 'SEGA System SP (Spider)', # Naomi derived
    'chihiro.cpp'   : 'SEGA Chihiro (Xbox-based)',
    'triforce.cpp'  : 'SEGA Triforce Hardware',
    'lindbergh.cpp' : 'SEGA Lindbergh',

    # --- Taito ---
    # Ordered alphabetically
    'taito_b.cpp'  : 'Taito B System',
    'taito_f2.cpp' : 'Taito F2 System',
    'taito_f3.cpp' : 'Taito F3 System',
    'taito_h.cpp'  : 'Taito H system',
    'taito_l.cpp'  : 'Taito L System',
    'taito_o.cpp'  : 'Taito O system (Gambling)',
    'taito_x.cpp'  : 'Taito X system',
    'taito_z.cpp'  : 'Taito Z System (twin 68K with optional Z80)',
    'taitoair.cpp' : 'Taito Air System',
    'taitogn.cpp'  : 'Taito GNET Motherboard',
    'taitojc.cpp'  : 'Taito JC System',
    'taitopjc.cpp' : 'Taito Power-JC System',
    'taitosj.cpp'  : 'Taito SJ system',
    'taitottl.cpp' : 'Taito Discrete Hardware Games',
    'taitotz.cpp'  : 'Taito Type-Zero hardware',
    'taitowlf.cpp' : 'Taito Wolf System',

    # --- SONY ---
    'zn.cpp' : 'Sony ZN1/ZN2 (Arcade PSX)',
}

# >> Some Software Lists don't follow the convention of adding the company name at the beginning.
# >> I will try to create pull requests to fix theses and if the PRs are not accepted then
# >> SL names will be changed using the data here.
SL_better_name_dic = {

    # --- SEGA ---
    'megacd'  : 'Sega Mega CD (Euro) CD-ROMs', # Mega CD (Euro) CD-ROMs
    'megacdj' : 'Sega Mega CD (Jpn) CD-ROMs',  # Mega CD (Jpn) CD-ROMs
}

#
# Numerical MAME version. Allows for comparisons like ver_mame >= MAME_VERSION_0190
# Support MAME versions higher than 0.53 August 12th 2001.
# See header of MAMEINFO.dat for a list of all MAME versions.
# a.bbb.ccc gets transformed into an uint a,bbb,ccc
# Examples:
#   '0.53'   ->  53000
#   '0.70'   ->  70000
#   '0.70u1' ->  70001
#   '0.150'  -> 150000
#   '0.190'  -> 190000
#
# mame_version_raw examples:
#   a) '0.194 (mame0194)' from '<mame build="0.194 (mame0194)" debug="no" mameconfig="10">'
#
# re.search() returns a MatchObject https://docs.python.org/2/library/re.html#re.MatchObject
def mame_get_numerical_version(mame_version_str):
    log_verb('mame_get_numerical_version() mame_version_str = "{0}"'.format(mame_version_str))
    version_int = 0
    m_obj = re.search('^(\d+?)\.(\d+?) \(', mame_version_str)
    if m_obj:
        major = int(m_obj.group(1))
        minor = int(m_obj.group(2))
        log_verb('mame_get_numerical_version() major = {0}'.format(major))
        log_verb('mame_get_numerical_version() minor = {0}'.format(minor))
        version_int = major * 100000 + minor * 1000
    log_verb('mame_get_numerical_version() version_int = {0}'.format(version_int))

    return version_int

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
def mame_get_control_str(control_type_list):
    control_set = set()
    improved_c_type_list = mame_improve_control_type_list(control_type_list)
    for control in improved_c_type_list: control_set.add(control)
    control_str = ', '.join(list(sorted(control_set)))

    return control_str

def mame_get_screen_rotation_str(display_rotate):
    if display_rotate == '0' or display_rotate == '180':
        screen_str = 'horizontal'
    elif display_rotate == '90' or display_rotate == '270':
        screen_str = 'vertical'
    else:
        raise TypeError

    return screen_str

def mame_get_screen_str(machine_name, machine):
    d_list = machine['display_type']
    if d_list:
        if len(d_list) == 1:
            rotation_str = mame_get_screen_rotation_str(machine['display_rotate'][0])
            screen_str = 'One {0} {1} screen'.format(d_list[0], rotation_str)
        elif len(d_list) == 2:
            if d_list[0] == 'lcd' and d_list[1] == 'raster':
                r_str_1 = mame_get_screen_rotation_str(machine['display_rotate'][0])
                r_str_2 = mame_get_screen_rotation_str(machine['display_rotate'][1])
                screen_str = 'One LCD {0} screen and one raster {1} screen'.format(r_str_1, r_str_2)
            elif d_list[0] == 'raster' and d_list[1] == 'raster':
                r_str = mame_get_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Two raster {0} screens'.format(r_str)
            elif d_list[0] == 'svg' and d_list[1] == 'svg':
                r_str = mame_get_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Two SVG {0} screens'.format(r_str)
            elif d_list[0] == 'unknown' and d_list[1] == 'unknown':
                screen_str = 'Two unknown screens'
            else:
                screen_str = 'Two unrecognised screens'
        elif len(d_list) == 3:
            if d_list[0] == 'raster' and d_list[1] == 'raster' and d_list[2] == 'raster':
                r_str = mame_get_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Three raster {0} screens'.format(r_str)
            elif d_list[0] == 'raster' and d_list[1] == 'lcd' and d_list[2] == 'lcd':
                screen_str = 'Three screens special case'
            else:
                screen_str = 'Three unrecognised screens'
        elif len(d_list) == 4:
            if d_list[0] == 'raster' and d_list[1] == 'raster' and d_list[2] == 'raster' and d_list[3] == 'raster':
                r_str = mame_get_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Four raster {0} screens'.format(r_str)
            else:
                screen_str = 'Four unrecognised screens'
        elif len(d_list) == 5:
            screen_str = 'Five unrecognised screens'
        elif len(d_list) == 6:
            screen_str = 'Six unrecognised screens'
        else:
            log_error('mame_get_screen_str() d_list = {0}'.format(unicode(d_list)))
            raise TypeError
    else:
        screen_str = 'No screen'

    return screen_str

#
# A) Capitalise every list item
# B) Substitute Only_buttons -> Only buttons
#
def mame_improve_control_type_list(control_type_list):
    out_list = []
    for control_str in control_type_list:
        capital_str = control_str.title()
        if capital_str == 'Only_Buttons': capital_str = 'Only Buttons'
        out_list.append(capital_str)

    return out_list

#
# A) Capitalise every list item
#
def mame_improve_device_list(control_type_list):
    out_list = []
    for control_str in control_type_list: out_list.append(control_str.title())

    return out_list

#
# See tools/test_compress_item_list.py for reference
# Input/Output examples:
# 1) ['dial']                 ->  ['dial']
# 2) ['dial', 'dial']         ->  ['2 x dial']
# 3) ['dial', 'dial', 'joy']  ->  ['2 x dial', 'joy']
# 4) ['joy', 'dial', 'dial']  ->  ['joy', '2 x dial']
#
def mame_compress_item_list(item_list):
    reduced_list = []
    num_items = len(item_list)
    if num_items == 0 or num_items == 1: return item_list
    previous_item = item_list[0]
    item_count = 1
    for i in range(1, num_items):
        current_item = item_list[i]
        # print('{0} | item_count {1} | previous_item "{2:>8}" | current_item "{3:>8}"'.format(i, item_count, previous_item, current_item))
        if current_item == previous_item:
            item_count += 1
        else:
            if item_count == 1: reduced_list.append('{0}'.format(previous_item))
            else:               reduced_list.append('{0} {1}'.format(item_count, previous_item))
            item_count = 1
            previous_item = current_item
        # >> Last elemnt of the list
        if i == num_items - 1:
            if current_item == previous_item:
                if item_count == 1: reduced_list.append('{0}'.format(current_item))
                else:               reduced_list.append('{0} {1}'.format(item_count, current_item))
            else:
               reduced_list.append('{0}'.format(current_item))

    return reduced_list

#
# See tools/test_compress_item_list.py for reference
# Output is sorted alphabetically
# Input/Output examples:
# 1) ['dial']                 ->  ['dial']
# 2) ['dial', 'dial']         ->  ['dial']
# 3) ['dial', 'dial', 'joy']  ->  ['dial', 'joy']
# 4) ['joy', 'dial', 'dial']  ->  ['dial', 'joy']
#
def mame_compress_item_list_compact(item_list):
    num_items = len(item_list)
    if num_items == 0 or num_items == 1: return item_list
    item_set = set(item_list)
    reduced_list = list(item_set)
    reduced_list_sorted = sorted(reduced_list)

    return reduced_list_sorted

# -------------------------------------------------------------------------------------------------
# Loading of data files
# -------------------------------------------------------------------------------------------------
def mame_load_Catver_ini(filename):
    log_info('mame_load_Catver_ini() Parsing "{0}"'.format(filename))
    catver_version = 'Not found'
    categories_dic = {}
    categories_set = set()
    __debug_do_list_categories = False
    read_status = 0
    # read_status FSM values
    # 0 -> Looking for '[Category]' tag
    # 1 -> Reading categories
    # 2 -> Categories finished. STOP
    try:
        f = open(filename, 'rt')
    except IOError:
        log_error('mame_load_Catver_ini() (IOError) opening "{0}"'.format(filename))
        return (categories_dic, catver_version)
    for cat_line in f:
        stripped_line = cat_line.strip()
        if __debug_do_list_categories: print('Line "' + stripped_line + '"')
        if read_status == 0:
            # >> Look for Catver version
            m = re.search(r'^;; CatVer ([0-9\.]+) / ', stripped_line)
            if m: catver_version = m.group(1)
            m = re.search(r'^;; CATVER.ini ([0-9\.]+) / ', stripped_line)
            if m: catver_version = m.group(1)
            if stripped_line == '[Category]':
                if __debug_do_list_categories: print('Found [Category]')
                read_status = 1
        elif read_status == 1:
            line_list = stripped_line.split("=")
            if len(line_list) == 1:
                read_status = 2
                continue
            else:
                if __debug_do_list_categories: print(line_list)
                machine_name = line_list[0]
                category = line_list[1]
                if machine_name not in categories_dic:
                    categories_dic[machine_name] = category
                categories_set.add(category)
        elif read_status == 2:
            log_debug('mame_load_Catver_ini() Reached end of categories parsing.')
            break
        else:
            raise CriticalError('Unknown read_status FSM value')
    f.close()
    log_info('mame_load_Catver_ini() Version "{0}"'.format(catver_version))
    log_info('mame_load_Catver_ini() Number of machines {0:6d}'.format(len(categories_dic)))
    log_info('mame_load_Catver_ini() Number of categories {0:6d}'.format(len(categories_set)))

    return (categories_dic, catver_version)

# -------------------------------------------------------------------------------------------------
# Load nplayers.ini. Structure similar to catver.ini
# -------------------------------------------------------------------------------------------------
def mame_load_nplayers_ini(filename):
    log_info('mame_load_nplayers_ini() Parsing "{0}"'.format(filename))
    nplayers_version = 'Not found'
    categories_dic = {}
    categories_set = set()
    __debug_do_list_categories = False
    # --- read_status FSM values ---
    # 0 -> Looking for '[NPlayers]' tag
    # 1 -> Reading categories
    # 2 -> Categories finished. STOP
    read_status = 0
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_nplayers_ini() (IOError) opening "{0}"'.format(filename))
        return (categories_dic, nplayers_version)
    for cat_line in f:
        stripped_line = cat_line.strip()
        if __debug_do_list_categories: print('Line "' + stripped_line + '"')
        if read_status == 0:
            m = re.search(r'NPlayers ([0-9\.]+) / ', stripped_line)
            if m: nplayers_version = m.group(1)
            if stripped_line == '[NPlayers]':
                if __debug_do_list_categories: print('Found [NPlayers]')
                read_status = 1
        elif read_status == 1:
            line_list = stripped_line.split("=")
            if len(line_list) == 1:
                read_status = 2
                continue
            else:
                if __debug_do_list_categories: print(line_list)
                machine_name = line_list[0]
                category = line_list[1]
                if machine_name not in categories_dic:
                    categories_dic[machine_name] = category
                categories_set.add(category)
        elif read_status == 2:
            log_info('mame_load_nplayers_ini() Reached end of nplayers parsing.')
            break
        else:
            raise CriticalError('Unknown read_status FSM value')
    f.close()
    log_info('mame_load_nplayers_ini() Version "{0}"'.format(nplayers_version))
    log_info('mame_load_nplayers_ini() Number of machines {0:6d}'.format(len(categories_dic)))
    log_info('mame_load_nplayers_ini() Number of categories {0:6d}'.format(len(categories_set)))

    return (categories_dic, nplayers_version)

#
# Load mature.ini file.
# Returns a tuple consisting of:
# 1) ini_set = {machine1, machine2, ...}
# 2) ini_version
#
def mame_load_Mature_ini(filename):
    log_info('mame_load_Mature_ini() Parsing "{0}"'.format(filename))
    ini_version = 'Not found'
    ini_set = set()
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_Mature_ini() (IOError) opening "{0}"'.format(filename))
        return (ini_set, ini_version)
    # FSM statuses
    # 0 -> Reading the file header
    # 1 -> '[ROOT_FOLDER]' found. Read machines (one per line).
    fsm_status = 0
    for file_line in f:
        stripped_line = file_line.strip()
        if fsm_status == 0:
            # >> Skip comments: lines starting with ';;'
            # >> Look for version string in comments
            if re.search(r'^;;', stripped_line):
                m = re.search(r';; (\w+)\.ini ([0-9\.]+) / ', stripped_line)
                if m: ini_version = m.group(2)
                continue
            if stripped_line == '[ROOT_FOLDER]':
                fsm_status = 1
                continue
        elif fsm_status == 1:
            if stripped_line == '': continue
            machine_name = stripped_line
            ini_set.add(machine_name)
    f.close()
    log_info('mame_load_Mature_ini() Version "{0}"'.format(ini_version))
    log_info('mame_load_Mature_ini() Number of machines {0:6d}'.format(len(ini_set)))

    return (ini_set, ini_version)

#
# Generic MAME INI file loader.
# Supports Catlist.ini, Genre.ini, Bestgames.ini and Series.ini
#
def mame_load_INI_datfile(filename):
    log_info('mame_load_INI_datfile() Parsing "{0}"'.format(filename))
    ini_version = 'Not found'
    ini_dic = {}
    ini_set = set()
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_INI_datfile() (IOError) opening "{0}"'.format(filename))
        return (ini_dic, ini_version)
    for file_line in f:
        stripped_line = file_line.strip()
        # >> Skip comments: lines starting with ';;'
        # >> Look for version string in comments
        if re.search(r'^;;', stripped_line):
            m = re.search(r';; (\w+)\.ini ([0-9\.]+) / ', stripped_line)
            if m: ini_version = m.group(2)
            continue
        # >> Skip blanks
        if stripped_line == '': continue
        # >> New category
        searchObj = re.search(r'^\[(.*)\]', stripped_line)
        if searchObj:
            current_category = searchObj.group(1)
            ini_set.add(current_category)
        else:
            machine_name = stripped_line
            ini_dic[machine_name] = current_category
    f.close()
    log_info('mame_load_INI_datfile() Version "{0}"'.format(ini_version))
    log_info('mame_load_INI_datfile() Number of machines {0:6d}'.format(len(ini_dic)))
    log_info('mame_load_INI_datfile() Number of categories {0:6d}'.format(len(ini_set)))

    return (ini_dic, ini_version)

#
# Loads History.dat
#
# history_idx_dic = {
#    'nes' : {
#        'name': string,
#        'machines' : [['100mandk', 'beautiful_name'], ['89denku', 'beautiful_name'], ...],
#    }
#    'mame' : {
#        'name' : string,
#        'machines': [['88games', 'beautiful_name'], ['flagrall', 'beautiful_name'], ...],
#    }
# }
#
# history_dic = {
#    'nes' : {'100mandk' : string, '89denku' : string, ...},
#    'mame' : {'88games' : string, 'flagrall' : string, ...},
# }
def mame_load_History_DAT(filename):
    log_info('mame_load_History_DAT() Parsing "{0}"'.format(filename))
    version_str = 'Not found'
    history_idx_dic = {}
    history_dic = {}
    __debug_function = False

    # --- read_status FSM values ---
    # 0 -> Looking for '$(xxxx)=(machine_name),'
    # 1 -> Looking for $bio
    # 2 -> Reading information. If '$end' found go to 0.
    read_status = 0

    # >> Open file
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_History_DAT() (IOError) opening "{0}"'.format(filename))
        return (history_idx_dic, history_dic, version_str)

    # >> Parse file
    for file_line in f:
        stripped_line = file_line.strip()
        line_uni = stripped_line.decode('utf-8', 'replace')
        if __debug_function: log_debug('Line "{0}"'.format(line_uni))
        if read_status == 0:
            # >> Skip comments: lines starting with '##'
            # >> Look for version string in comments
            if re.search(r'^##', line_uni):
                m = re.search(r'## REVISION\: ([0-9\.]+)', line_uni)
                if m: version_str = m.group(1)
                continue
            if line_uni == '': continue
            # >> New machine history
            m = re.search(r'^\$(.+?)=(.+?),', line_uni)
            if m:
                list_name = m.group(1)
                machine_name = m.group(2)
                # >> Transform some special list names
                if   list_name == 'info':          list_name = 'mame'
                elif list_name == 'info,megatech': list_name = 'mame'
                elif list_name == 'info,stv':      list_name = 'mame'
                if __debug_function: log_debug('List "{0}" / Machine "{1}"'.format(list_name, machine_name))
                if list_name in history_idx_dic:
                    history_idx_dic[list_name]['machines'].append([machine_name, machine_name])
                else:
                    history_idx_dic[list_name] = {'name' : list_name, 'machines' : []}
                    history_idx_dic[list_name]['machines'].append([machine_name, machine_name])
            read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{0}"'.format(line_uni))
            if line_uni == '$bio':
                read_status = 2
                info_str_list = []
            else:
                raise TypeError('Wrong second line = "{0}"'.format(line_uni))
        elif read_status == 2:
            if line_uni == '$end':
                if list_name in history_dic:
                    history_dic[list_name][machine_name] = '\n'.join(info_str_list)
                else:
                    history_dic[list_name] = {}
                    history_dic[list_name][machine_name] = '\n'.join(info_str_list)
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {0}'.format(read_status))
    f.close()
    log_info('mame_load_History_DAT() Version "{0}"'.format(version_str))
    log_info('mame_load_History_DAT() Number of rows in history_idx_dic {0:6d}'.format(len(history_idx_dic)))
    log_info('mame_load_History_DAT() Number of rows in history_dic {0:6d}'.format(len(history_dic)))

    return (history_idx_dic, history_dic, version_str)

#
# Looks that mameinfo.dat has information for both machines and drivers.
#
# idx_dic  = { 
#     'mame' : [['88games', 'beautiful_name'], ['flagrall', 'beautiful_name'], ...],
#     'drv' : [['88games.cpp', 'beautiful_name'], ['flagrall.cpp', 'beautiful_name'], ...],
# }
# data_dic = {
#    'mame' : {'88games' : string, 'flagrall' : string, ...},
#    'drv' : {'1942.cpp' : string, '1943.cpp' : string, ...},
# }
#
def mame_load_MameInfo_DAT(filename):
    log_info('mame_load_MameInfo_DAT() Parsing "{0}"'.format(filename))
    version_str = 'Not found'
    idx_dic = {}
    data_dic = {}
    __debug_function = False

    # --- read_status FSM values ---
    # 0 -> Looking for '$(xxxx)=(machine_name)'
    # 1 -> Looking for $bio
    # 2 -> Reading information. If '$end' found go to 0.
    # 3 -> Ignoring information. If '$end' found go to 0.
    read_status = 0

    # >> Open file
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_MameInfo_DAT() (IOError) opening "{0}"'.format(filename))
        return (idx_dic, data_dic, version_str)

    # >> Parse file
    for file_line in f:
        stripped_line = file_line.strip()
        line_uni = stripped_line.decode('utf-8', 'replace')
        # if __debug_function: log_debug('Line "{0}"'.format(line_uni))
        if read_status == 0:
            # >> Skip comments: lines starting with '#'
            # >> Look for version string in comments
            if re.search(r'^#', line_uni):
                m = re.search(r'# MAMEINFO.DAT v([0-9\.]+)', line_uni)
                if m: version_str = m.group(1)
                continue
            if line_uni == '': continue
            # >> New machine or driver information
            m = re.search(r'^\$info=(.+?)$', line_uni)
            if m:
                machine_name = m.group(1)
                if __debug_function: log_debug('Machine "{1}"'.format(machine_name))
                read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{0}"'.format(line_uni))
            if line_uni == '$mame':
                read_status = 2
                info_str_list = []
                list_name = 'mame'
                if 'mame' in idx_dic:
                    idx_dic['mame'].append([machine_name, machine_name])
                else:
                    idx_dic['mame'] = []
                    idx_dic['mame'].append([machine_name, machine_name])
            elif line_uni == '$drv':
                read_status = 2
                info_str_list = []
                list_name = 'drv'
                if 'drv' in idx_dic:
                    idx_dic['drv'].append([machine_name, machine_name])
                else:
                    idx_dic['drv'] = []
                    idx_dic['drv'].append([machine_name, machine_name])
            else:
                raise TypeError('Wrong second line = "{0}"'.format(line_uni))
        elif read_status == 2:
            if line_uni == '$end':
                if list_name in data_dic:
                    data_dic[list_name][machine_name] = '\n'.join(info_str_list)
                else:
                    data_dic[list_name] = {}
                    data_dic[list_name][machine_name] = '\n'.join(info_str_list)
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {0}'.format(read_status))
    f.close()
    log_info('mame_load_MameInfo_DAT() Version "{0}"'.format(version_str))
    log_info('mame_load_MameInfo_DAT() Number of rows in idx_dic {0:6d}'.format(len(idx_dic)))
    log_info('mame_load_MameInfo_DAT() Number of rows in data_dic {0:6d}'.format(len(data_dic)))

    return (idx_dic, data_dic, version_str)

#
# NOTE set objects are not JSON-serializable. Use lists and transform lists to sets if
#      necessary after loading the JSON file.
#
# idx_list  = [['88games', 'beautiful_name'], ['flagrall', 'beautiful_name'], ...],
# data_dic = { '88games' : 'string', 'flagrall' : 'string', ... }
#
def mame_load_GameInit_DAT(filename):
    log_info('mame_load_GameInit_DAT() Parsing "{0}"'.format(filename))
    version_str = 'Not found'
    idx_list = []
    data_dic = {}
    __debug_function = False

    # --- read_status FSM values ---
    # 0 -> Looking for '$info=(machine_name)'
    # 1 -> Looking for $mame
    # 2 -> Reading information. If '$end' found go to 0.
    # 3 -> Ignoring information. If '$end' found go to 0.
    read_status = 0

    # >> Open file
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_GameInit_DAT() (IOError) opening "{0}"'.format(filename))
        return (idx_list, data_dic, version_str)

    # >> Parse file
    for file_line in f:
        stripped_line = file_line.strip()
        line_uni = stripped_line.decode('utf-8', 'replace')
        if __debug_function: log_debug('read_status {0} | Line "{1}"'.format(read_status, line_uni))
        # >> Note that Gameinit.dat may have a BOM 0xEF,0xBB,0xBF
        # >> See https://en.wikipedia.org/wiki/Byte_order_mark
        # >> Remove BOM if present.
        if line_uni and line_uni[0] == '\ufeff': line_uni = line_uni[1:]
        if read_status == 0:
            # >> Skip comments: lines starting with '#'
            # >> Look for version string in comments
            if re.search(r'^#', line_uni):
                if __debug_function: log_debug('Comment | "{0}"'.format(line_uni))
                m = re.search(r'# MAME GAMEINIT\.DAT v([0-9\.]+) ', line_uni)
                if m: version_str = m.group(1)
                continue
            if line_uni == '': continue
            # >> New machine or driver information
            m = re.search(r'^\$info=(.+?)$', line_uni)
            if m:
                machine_name = m.group(1)
                if __debug_function: log_debug('Machine "{0}"'.format(machine_name))
                idx_list.append([machine_name, machine_name])
                read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{0}"'.format(line_uni))
            if line_uni == '$mame':
                read_status = 2
                info_str_list = []
            else:
                raise TypeError('Wrong second line = "{0}"'.format(line_uni))
        elif read_status == 2:
            if line_uni == '$end':
                data_dic[machine_name] = '\n'.join(info_str_list)
                info_str_list = []
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {0}'.format(read_status))
    f.close()
    log_info('mame_load_GameInit_DAT() Version "{0}"'.format(version_str))
    log_info('mame_load_GameInit_DAT() Number of rows in idx_list {0:6d}'.format(len(idx_list)))
    log_info('mame_load_GameInit_DAT() Number of rows in data_dic {0:6d}'.format(len(data_dic)))

    return (idx_list, data_dic, version_str)

#
# NOTE set objects are not JSON-serializable. Use lists and transform lists to sets if
#      necessary after loading the JSON file.
#
# idx_list = [['88games', 'beautiful_name'], ['flagrall', 'beautiful_name'], ...],
# data_dic = { '88games' : 'string', 'flagrall' : 'string', ... }
#
def mame_load_Command_DAT(filename):
    log_info('mame_load_Command_DAT() Parsing "{0}"'.format(filename))
    version_str = 'Not found'
    idx_list = []
    data_dic = {}
    proper_idx_list = []
    proper_data_dic = {}
    __debug_function = False

    # --- read_status FSM values ---
    # 0 -> Looking for '$info=(machine_name)'
    # 1 -> Looking for $cmd
    # 2 -> Reading information. If '$end' found go to 0.
    read_status = 0

    # >> Open file
    try:
        f = open(filename, 'rt')
    except IOError:
        log_info('mame_load_Command_DAT() (IOError) opening "{0}"'.format(filename))
        return (proper_idx_list, proper_data_dic, version_str)

    # >> Parse file
    for file_line in f:
        stripped_line = file_line.strip()
        line_uni = stripped_line.decode('utf-8', 'replace')
        # if __debug_function: log_debug('Line "{0}"'.format(line_uni))
        if read_status == 0:
            # >> Skip comments: lines starting with '#'
            # >> Look for version string in comments
            if re.search(r'^#', line_uni):
                m = re.search(r'# Command List-[\w]+[\s]+([0-9\.]+) #', line_uni)
                if m: version_str = m.group(1)
                continue
            if line_uni == '': continue
            # >> New machine or driver information
            m = re.search(r'^\$info=(.+?)$', line_uni)
            if m:
                machine_name = m.group(1)
                if __debug_function: log_debug('Machine "{0}"'.format(machine_name))
                idx_list.append(machine_name)
                read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{0}"'.format(line_uni))
            if line_uni == '$cmd':
                read_status = 2
                info_str_list = []
            else:
                raise TypeError('Wrong second line = "{0}"'.format(line_uni))
        elif read_status == 2:
            if line_uni == '$end':
                data_dic[machine_name] = '\n'.join(info_str_list)
                info_str_list = []
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {0}'.format(read_status))
    f.close()
    log_info('mame_load_Command_DAT() Version "{0}"'.format(version_str))
    log_info('mame_load_Command_DAT() Number of rows in idx_list {0:6d}'.format(len(idx_list)))
    log_info('mame_load_Command_DAT() Number of rows in data_dic {0:6d}'.format(len(data_dic)))

    # >> Expand database. Many machines share the same entry. Expand the database.
    for original_name in idx_list:
        original_name_list = original_name.split(',')
        for expanded_name in original_name_list:
            # Skip empty strings
            if not expanded_name: continue
            expanded_name = expanded_name.strip()
            proper_idx_list.append([expanded_name, expanded_name])
            proper_data_dic[expanded_name] = data_dic[original_name]
    log_info('mame_load_Command_DAT() Number of entries on proper_idx_list {0:6d}'.format(len(proper_idx_list)))
    log_info('mame_load_Command_DAT() Number of entries on proper_data_dic {0:6d}'.format(len(proper_data_dic)))

    return (proper_idx_list, proper_data_dic, version_str)

# -------------------------------------------------------------------------------------------------
# CHD manipulation functions
# -------------------------------------------------------------------------------------------------
# Reference in https://github.com/rtissera/libchdr/blob/master/src/chd.h
# Reference in https://github.com/mamedev/mame/blob/master/src/lib/util/chd.h
#
# Open CHD and return stat information.
#
# chd_info = {
#     'status'  : CHD_OK or CHD_BAD,
#     'version' : int,
#     'sha1'    : string,
# }
#
CHD_OK          = 0
CHD_BAD_CHD     = 1
CHD_BAD_VERSION = 2
def _mame_stat_chd(chd_path):
    __debug_this_function = False
    chd_info = {
        'status'  : CHD_OK,
        'version' : 0,
        'sha1'    : '',
    }

    # --- Open CHD file and read first 124 bytes ---
    if __debug_this_function: log_debug('_mame_stat_chd() Opening "{0}"'.format(chd_path))
    try:
        f = open(chd_path, 'rb')
        chd_data_str = f.read(124)
        f.close()
    except IOError as E:
        chd_info['status'] = CHD_BAD_CHD
        return chd_info

    # --- Check CHD magic string to skip fake files ---
    if chd_data_str[0:8] != 'MComprHD':
        if __debug_this_function: log_debug('_mame_stat_chd() Magic string not found!')
        chd_info['status'] = CHD_BAD_CHD
        return chd_info

    # --- Parse CHD header ---
    # >> All values in the CHD header are stored in big endian!
    h_tuple = struct.unpack('>8sII', chd_data_str[0:16])
    tag     = h_tuple[0]
    length  = h_tuple[1]
    version = h_tuple[2]
    if __debug_this_function:
        log_debug('_mame_stat_chd() Tag     "{0}"'.format(tag))
        log_debug('_mame_stat_chd() Length  {0}'.format(length))
        log_debug('_mame_stat_chd() Version {0}'.format(version))

    # >> Discard very old CHD that don't have SHA1 hash. Older version used MD5.
    if version == 1 or version == 2 or version == 3:
        chd_info['status'] = CHD_BAD_VERSION
        chd_info['version'] = version
        return chd_info

    # >> Read the whole header (must consider V3, V4 and V5)
    # >> NOTE In MAME 0.196 some CHDs have version 4, most have version 5, version 3 is obsolete
    if version == 4:
        if __debug_this_function: log_debug('Reading V4 CHD header')
        chd_header_v4_str = '>8sIIIIIQQI20s20s20s'
        header_size = struct.calcsize(chd_header_v4_str)
        t = struct.unpack(chd_header_v4_str, chd_data_str[0:108])
        tag          = t[0]
        length       = t[1]
        version      = t[2]
        flags        = t[3]
        compression  = t[4]
        totalhunks   = t[5]
        logicalbytes = t[6]
        metaoffset   = t[7]
        hunkbytes    = t[8]
        rawsha1      = binascii.b2a_hex(t[9])
        sha1         = binascii.b2a_hex(t[10])
        parentsha1   = binascii.b2a_hex(t[11])

        if __debug_this_function:
            log_debug('V4 header size = {0}'.format(header_size))
            log_debug('tag           "{0}"'.format(tag))
            log_debug('length        {0}'.format(length))
            log_debug('version       {0}'.format(version))
            log_debug('flags         {0}'.format(flags))
            log_debug('compression   {0}'.format(compression))
            log_debug('totalhunks    {0}'.format(totalhunks))
            log_debug('logicalbytes  {0}'.format(logicalbytes))
            log_debug('metaoffset    {0}'.format(metaoffset))
            log_debug('hunkbytes     {0}'.format(hunkbytes))
            log_debug('rawsha1       "{0}"'.format(rawsha1))
            log_debug('sha1          "{0}"'.format(sha1))
            log_debug('parentsha1    "{0}"'.format(parentsha1))

        # >> The CHD SHA1 string storet in MAME -listxml is the rawsha1 field in V4 CHDs.
        chd_info['status']  = CHD_OK
        chd_info['version'] = version
        chd_info['sha1']    = rawsha1
    elif version == 5:
        if __debug_this_function: log_debug('Reading V5 CHD header')
        chd_header_v5_str = '>8sII16sQQQII20s20s20s'
        header_size = struct.calcsize(chd_header_v5_str)
        t = struct.unpack(chd_header_v5_str, chd_data_str)
        tag           = t[0]
        length        = t[1]
        version       = t[2]
        compressors   = t[3]
        logicalbytes  = t[4]
        mapoffset     = t[5]
        metaoffset    = t[6]
        hunkbytes     = t[7]
        unitbytes     = t[8]
        rawsha1       = binascii.b2a_hex(t[9])
        sha1          = binascii.b2a_hex(t[10])
        parentsha1    = binascii.b2a_hex(t[11])

        if __debug_this_function:
            log_debug('V5 header size = {0}'.format(header_size))
            log_debug('tag           "{0}"'.format(tag))
            log_debug('length        {0}'.format(length))
            log_debug('version       {0}'.format(version))
            log_debug('compressors   "{0}"'.format(compressors))
            log_debug('logicalbytes  {0}'.format(logicalbytes))
            log_debug('mapoffset     {0}'.format(mapoffset))
            log_debug('metaoffset    {0}'.format(metaoffset))
            log_debug('hunkbytes     {0}'.format(hunkbytes))
            log_debug('unitbytes     {0}'.format(unitbytes))
            log_debug('rawsha1       "{0}"'.format(rawsha1))
            log_debug('sha1          "{0}"'.format(sha1))
            log_debug('parentsha1    "{0}"'.format(parentsha1))

        # >> The CHD SHA1 string storet in MAME -listxml is the sha1 field (combined raw+meta SHA1).
        chd_info['status']  = CHD_OK
        chd_info['version'] = version
        chd_info['sha1']    = sha1
    else:
        raise TypeError('Unsuported version = {0}'.format(version))

    return chd_info

# -------------------------------------------------------------------------------------------------
# Statistic printing
# -------------------------------------------------------------------------------------------------
# >> See https://docs.python.org/2/library/time.html
def _str_time(secs):
    return time.strftime('%a  %d %b %Y  %H:%M:%S', time.localtime(secs))

def mame_info_MAME_print(slist, location, machine_name, machine, assets):
    slist.append('[COLOR orange]Machine {0} / Render data[/COLOR]'.format(machine_name))
    # >> Print MAME Favourites special fields
    if 'ver_mame' in machine:
        slist.append("[COLOR slateblue]name[/COLOR]: {0}".format(machine['name']))
    if 'ver_mame' in machine:
        slist.append("[COLOR slateblue]ver_mame[/COLOR]: {0}".format(machine['ver_mame']))
    if 'ver_mame_str' in machine:
        slist.append("[COLOR slateblue]ver_mame_str[/COLOR]: {0}".format(machine['ver_mame_str']))
    # >> Most Played Favourites special fields
    if 'launch_count' in machine:
        slist.append("[COLOR slateblue]launch_count[/COLOR]: {0}".format(unicode(machine['launch_count'])))

    # >> Standard fields in Render database
    slist.append("[COLOR violet]cloneof[/COLOR]: '{0}'".format(machine['cloneof']))
    slist.append("[COLOR violet]description[/COLOR]: '{0}'".format(machine['description']))
    slist.append("[COLOR violet]driver_status[/COLOR]: '{0}'".format(machine['driver_status']))
    slist.append("[COLOR violet]genre[/COLOR]: '{0}'".format(machine['genre']))
    slist.append("[COLOR skyblue]isBIOS[/COLOR]: {0}".format(machine['isBIOS']))
    slist.append("[COLOR skyblue]isDevice[/COLOR]: {0}".format(machine['isDevice']))
    slist.append("[COLOR skyblue]isMature[/COLOR]: {0}".format(machine['isMature']))
    slist.append("[COLOR violet]manufacturer[/COLOR]: '{0}'".format(machine['manufacturer']))
    slist.append("[COLOR violet]nplayers[/COLOR]: '{0}'".format(machine['nplayers']))
    slist.append("[COLOR violet]year[/COLOR]: '{0}'".format(machine['year']))

    # >> Standard fields in Main database
    slist.append('\n[COLOR orange]Machine Main data[/COLOR]')
    slist.append("[COLOR violet]bestgames[/COLOR]: '{0}'".format(machine['bestgames']))
    slist.append("[COLOR violet]catlist[/COLOR]: '{0}'".format(machine['catlist']))
    slist.append("[COLOR violet]catver[/COLOR]: '{0}'".format(machine['catver']))
    # >> Deprecated
    slist.append("[COLOR skyblue]coins[/COLOR]: {0}".format(machine['coins']))
    # >> Deprecated
    slist.append("[COLOR skyblue]control_type[/COLOR]: {0}".format(unicode(machine['control_type'])))
    # --- Devices list is a special case ---
    if machine['devices']:
        for i, device in enumerate(machine['devices']):
            slist.append("[COLOR lime]devices[/COLOR][{0}]:".format(i))
            slist.append("  [COLOR violet]att_type[/COLOR]: {0}".format(device['att_type']))
            slist.append("  [COLOR violet]att_tag[/COLOR]: {0}".format(device['att_tag']))
            slist.append("  [COLOR skyblue]att_mandatory[/COLOR]: {0}".format(unicode(device['att_mandatory'])))
            slist.append("  [COLOR violet]att_interface[/COLOR]: {0}".format(device['att_interface']))
            slist.append("  [COLOR skyblue]instance[/COLOR]: {0}".format(unicode(device['instance'])))
            slist.append("  [COLOR skyblue]ext_names[/COLOR]: {0}".format(unicode(device['ext_names'])))
    else:
        slist.append("[COLOR lime]devices[/COLOR]: []")
    slist.append("[COLOR skyblue]display_rotate[/COLOR]: {0}".format(unicode(machine['display_rotate'])))
    slist.append("[COLOR skyblue]display_type[/COLOR]: {0}".format(unicode(machine['display_type'])))
    slist.append("[COLOR violet]genre[/COLOR]: '{0}'".format(machine['genre']))
    # --- input is a special case ---
    if machine['input']:
        # >> Print attributes
        slist.append("[COLOR lime]input[/COLOR]:")
        slist.append("  [COLOR skyblue]att_coins[/COLOR]: {0}".format(unicode(machine['input']['att_coins'])))
        slist.append("  [COLOR skyblue]att_players[/COLOR]: {0}".format(unicode(machine['input']['att_players'])))
        slist.append("  [COLOR skyblue]att_service[/COLOR]: {0}".format(unicode(machine['input']['att_service'])))
        slist.append("  [COLOR skyblue]att_tilt[/COLOR]: {0}".format(unicode(machine['input']['att_tilt'])))
        # >> Print control tag list
        for i, control in enumerate(machine['input']['control_list']):
            slist.append("[COLOR lime]control[/COLOR][{0}]:".format(i))
            slist.append("  [COLOR violet]type[/COLOR]: {0}".format(control['type']))
            slist.append("  [COLOR skyblue]player[/COLOR]: {0}".format(unicode(control['player'])))
            slist.append("  [COLOR skyblue]buttons[/COLOR]: {0}".format(unicode(control['buttons'])))
            slist.append("  [COLOR skyblue]ways[/COLOR]: {0}".format(unicode(control['ways'])))
    else:
        slist.append("[COLOR lime]input[/COLOR]: []")
    slist.append("[COLOR skyblue]isDead[/COLOR]: {0}".format(unicode(machine['isDead'])))
    slist.append("[COLOR skyblue]isMechanical[/COLOR]: {0}".format(unicode(machine['isMechanical'])))
    slist.append("[COLOR violet]romof[/COLOR]: '{0}'".format(machine['romof']))
    slist.append("[COLOR violet]sampleof[/COLOR]: '{0}'".format(machine['sampleof']))
    slist.append("[COLOR violet]series[/COLOR]: '{0}'".format(machine['series']))
    slist.append("[COLOR skyblue]softwarelists[/COLOR]: {0}".format(unicode(machine['softwarelists'])))
    slist.append("[COLOR violet]sourcefile[/COLOR]: '{0}'".format(machine['sourcefile']))

    slist.append('\n[COLOR orange]Machine assets/artwork[/COLOR]')
    slist.append("[COLOR violet]PCB[/COLOR]: '{0}'".format(assets['PCB']))
    slist.append("[COLOR violet]artpreview[/COLOR]: '{0}'".format(assets['artpreview']))
    slist.append("[COLOR violet]artwork[/COLOR]: '{0}'".format(assets['artwork']))
    slist.append("[COLOR violet]cabinet[/COLOR]: '{0}'".format(assets['cabinet']))
    slist.append("[COLOR violet]clearlogo[/COLOR]: '{0}'".format(assets['clearlogo']))
    slist.append("[COLOR violet]cpanel[/COLOR]: '{0}'".format(assets['cpanel']))
    slist.append("[COLOR violet]fanart[/COLOR]: '{0}'".format(assets['fanart']))
    slist.append("[COLOR violet]flags[/COLOR]: '{0}'".format(assets['flags']))
    slist.append("[COLOR violet]flyer[/COLOR]: '{0}'".format(assets['flyer']))
    slist.append("[COLOR violet]manual[/COLOR]: '{0}'".format(assets['manual']))
    slist.append("[COLOR violet]marquee[/COLOR]: '{0}'".format(assets['marquee']))
    slist.append("[COLOR violet]plot[/COLOR]: '{0}'".format(assets['plot']))
    slist.append("[COLOR violet]snap[/COLOR]: '{0}'".format(assets['snap']))
    slist.append("[COLOR violet]title[/COLOR]: '{0}'".format(assets['title']))
    slist.append("[COLOR violet]trailer[/COLOR]: '{0}'".format(assets['trailer']))

def mame_info_SL_print(slist, location, SL_name, SL_ROM, rom, assets, SL_dic, SL_machine_list):
    # --- ROM stuff ---
    slist.append('[COLOR orange]Software List {0} Item {1}[/COLOR]'.format(SL_name, SL_ROM))
    if 'SL_DB_key' in rom:
        slist.append("[COLOR slateblue]SL_DB_key[/COLOR]: '{0}'".format(rom['SL_DB_key']))
    if 'SL_ROM_name' in rom:
        slist.append("[COLOR slateblue]SL_ROM_name[/COLOR]: '{0}'".format(rom['SL_ROM_name']))
    if 'SL_name' in rom:
        slist.append("[COLOR slateblue]SL_name[/COLOR]: '{0}'".format(rom['SL_name']))
    slist.append("[COLOR violet]cloneof[/COLOR]: '{0}'".format(rom['cloneof']))
    slist.append("[COLOR violet]description[/COLOR]: '{0}'".format(rom['description']))
    slist.append("[COLOR skyblue]hasCHDs[/COLOR]: {0}".format(unicode(rom['hasCHDs'])))
    slist.append("[COLOR skyblue]hasROMs[/COLOR]: {0}".format(unicode(rom['hasROMs'])))
    if 'launch_count' in rom:
        slist.append("[COLOR slateblue]launch_count[/COLOR]: '{0}'".format(unicode(rom['launch_count'])))
    if 'launch_machine' in rom:
        slist.append("[COLOR slateblue]launch_machine[/COLOR]: '{0}'".format(rom['launch_machine']))
    if rom['parts']:
        for i, part in enumerate(rom['parts']):
            slist.append("[COLOR lime]parts[/COLOR][{0}]:".format(i))
            slist.append("  [COLOR violet]interface[/COLOR]: '{0}'".format(part['interface']))
            slist.append("  [COLOR violet]name[/COLOR]: '{0}'".format(part['name']))
    else:
        slist.append('[COLOR lime]parts[/COLOR]: []')
    slist.append("[COLOR violet]plot[/COLOR]: '{0}'".format(rom['plot']))
    slist.append("[COLOR violet]publisher[/COLOR]: '{0}'".format(rom['publisher']))
    slist.append("[COLOR violet]status_CHD[/COLOR]: '{0}'".format(rom['status_CHD']))
    slist.append("[COLOR violet]status_ROM[/COLOR]: '{0}'".format(rom['status_ROM']))
    if 'ver_mame' in rom:
        slist.append("[COLOR slateblue]ver_mame[/COLOR]: {0}".format(rom['ver_mame']))
    if 'ver_mame_str' in rom:
        slist.append("[COLOR slateblue]ver_mame_str[/COLOR]: {0}".format(rom['ver_mame_str']))
    slist.append("[COLOR violet]year[/COLOR]: '{0}'".format(rom['year']))

    slist.append('\n[COLOR orange]Software List assets[/COLOR]')
    slist.append("[COLOR violet]title[/COLOR]: '{0}'".format(assets['title']))
    slist.append("[COLOR violet]snap[/COLOR]: '{0}'".format(assets['snap']))
    slist.append("[COLOR violet]boxfront[/COLOR]: '{0}'".format(assets['boxfront']))
    slist.append("[COLOR violet]fanart[/COLOR]: '{0}'".format(assets['fanart']))
    slist.append("[COLOR violet]trailer[/COLOR]: '{0}'".format(assets['trailer']))
    slist.append("[COLOR violet]manual[/COLOR]: '{0}'".format(assets['manual']))

    slist.append('\n[COLOR orange]Software List {0}[/COLOR]'.format(SL_name))
    slist.append("[COLOR violet]display_name[/COLOR]: '{0}'".format(SL_dic['display_name']))
    slist.append("[COLOR skyblue]num_with_CHDs[/COLOR]: {0}".format(unicode(SL_dic['num_with_CHDs'])))
    slist.append("[COLOR skyblue]num_with_ROMs[/COLOR]: {0}".format(unicode(SL_dic['num_with_ROMs'])))
    slist.append("[COLOR violet]rom_DB_noext[/COLOR]: '{0}'".format(SL_dic['rom_DB_noext']))

    slist.append('\n[COLOR orange]Runnable by[/COLOR]')
    for machine_dic in sorted(SL_machine_list):
        t = "[COLOR violet]machine[/COLOR]: '{0}' [COLOR slateblue]({1})[/COLOR]"
        slist.append(t.format(machine_dic['description'], machine_dic['machine']))

#
# slist is a list of strings that will be joined like '\n'.join(slist)
# slist is a list, so it is mutable and can be changed by reference.
#
def mame_stats_main_print_slist(slist, control_dic, AML_version_str):
    slist.append('[COLOR orange]Main information[/COLOR]')
    slist.append("AML version            {0}".format(AML_version_str))
    slist.append("MAME version string    {0}".format(control_dic['ver_mame_str']))
    slist.append("MAME version numerical {0}".format(control_dic['ver_mame']))
    slist.append("bestgames.ini version  {0}".format(control_dic['ver_bestgames']))
    slist.append("catlist.ini version    {0}".format(control_dic['ver_catlist']))
    slist.append("catver.ini version     {0}".format(control_dic['ver_catver']))
    slist.append("command.dat version    {0}".format(control_dic['ver_command']))
    slist.append("gameinit.dat version   {0}".format(control_dic['ver_gameinit']))
    slist.append("genre.ini version      {0}".format(control_dic['ver_genre']))
    slist.append("history.dat version    {0}".format(control_dic['ver_history']))
    slist.append("mameinfo.dat version   {0}".format(control_dic['ver_mameinfo']))
    slist.append("mature.ini version     {0}".format(control_dic['ver_mature']))
    slist.append("nplayers.ini version   {0}".format(control_dic['ver_nplayers']))
    slist.append("series.ini version     {0}".format(control_dic['ver_series']))

    slist.append('')
    slist.append('[COLOR orange]Timestamps[/COLOR]')
    if control_dic['t_XML_extraction']:
        slist.append("MAME XML extracted on   {0}".format(_str_time(control_dic['t_XML_extraction'])))
    else:
        slist.append("MAME XML never extracted")
    if control_dic['t_MAME_DB_build']:
        slist.append("MAME DB built on        {0}".format(_str_time(control_dic['t_MAME_DB_build'])))
    else:
        slist.append("MAME DB never built")
    if control_dic['t_MAME_Audit_DB_build']:
        slist.append("MAME Audit DB built on  {0}".format(_str_time(control_dic['t_MAME_Audit_DB_build'])))
    else:
        slist.append("MAME Audit DB never built")
    if control_dic['t_MAME_Catalog_build']:
        slist.append("MAME Catalog built on   {0}".format(_str_time(control_dic['t_MAME_Catalog_build'])))
    else:
        slist.append("MAME Catalog never built")
    if control_dic['t_MAME_ROMs_scan']:
        slist.append("MAME ROMs scaned on     {0}".format(_str_time(control_dic['t_MAME_ROMs_scan'])))
    else:
        slist.append("MAME ROMs never scaned")
    if control_dic['t_MAME_assets_scan']:
        slist.append("MAME assets scaned on   {0}".format(_str_time(control_dic['t_MAME_assets_scan'])))
    else:
        slist.append("MAME assets never scaned")
    if control_dic['t_Custom_Filter_build']:
        slist.append("Custom filters built on {0}".format(_str_time(control_dic['t_Custom_Filter_build'])))
    else:
        slist.append("Custom filters never built")

    # >> Software Lists stuff
    if control_dic['t_SL_DB_build']:
        slist.append("SL DB built on          {0}".format(_str_time(control_dic['t_SL_DB_build'])))
    else:
        slist.append("SL DB never built")
    if control_dic['t_SL_ROMs_scan']:
        slist.append("SL ROMs scaned on       {0}".format(_str_time(control_dic['t_SL_ROMs_scan'])))
    else:
        slist.append("SL ROMs never scaned")
    if control_dic['t_SL_assets_scan']:
        slist.append("SL assets scaned on     {0}".format(_str_time(control_dic['t_SL_assets_scan'])))
    else:
        slist.append("SL assets never scaned")

    # >> Audit stuff
    if control_dic['t_MAME_audit']:
        slist.append("MAME ROMs audited on    {0}".format(_str_time(control_dic['t_MAME_audit'])))
    else:
        slist.append("MAME ROMs never audited")
    if control_dic['t_SL_audit']:
        slist.append("SL ROMs audited on      {0}".format(_str_time(control_dic['t_SL_audit'])))
    else:
        slist.append("SL ROMs never audited")

    # >> 5,d prints the comma separator but does not pad to 5 spaces.
    slist.append('')
    slist.append('[COLOR orange]MAME machine count[/COLOR]')
    t = "Machines   {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_processed_machines'],
                          control_dic['stats_parents'], 
                          control_dic['stats_clones']))
    t = "Runnable   {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_runnable'],
                          control_dic['stats_runnable_parents'], 
                          control_dic['stats_runnable_clones']))
    t = "Coin       {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_coin'],
                          control_dic['stats_coin_parents'], 
                          control_dic['stats_coin_clones']))
    t = "Nocoin     {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_nocoin'],
                          control_dic['stats_nocoin_parents'],
                          control_dic['stats_nocoin_clones']))
    t = "Mechanical {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_mechanical'],
                          control_dic['stats_mechanical_parents'],
                          control_dic['stats_mechanical_clones']))
    t = "Dead       {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_dead'],
                          control_dic['stats_dead_parents'], 
                          control_dic['stats_dead_clones']))
    t = "Devices    {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_devices'],
                          control_dic['stats_devices_parents'], 
                          control_dic['stats_devices_clones']))
    # >> Binary filters
    t = "BIOS       {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_BIOS'],
                          control_dic['stats_BIOS_parents'], 
                          control_dic['stats_BIOS_clones']))
    t = "Samples    {0:5d}, parents {1:5d}, clones {2:5d}"
    slist.append(t.format(control_dic['stats_samples'],
                          control_dic['stats_samples_parents'], 
                          control_dic['stats_samples_clones']))

    slist.append('')
    slist.append('[COLOR orange]Software Lists item count[/COLOR]')
    slist.append("SL files           {0:6d}".format(control_dic['stats_SL_XML_files']))
    slist.append("SL software items  {0:6d}".format(control_dic['stats_SL_software_items']))
    slist.append("SL items with ROMs {0:6d}".format(control_dic['stats_SL_items_with_ROMs']))
    slist.append("SL items with CHDs {0:6d}".format(control_dic['stats_SL_items_with_CHDs']))

def mame_stats_scanner_print_slist(slist, control_dic):
    # >> MAME statistics
    slist.append('[COLOR orange]MAME scanner information[/COLOR]')
    ta = "You have {0:5d} ROM ZIP files out of {1:5d}, missing    {2:5d}"
    tb = "You have {0:5d} CHDs out of          {1:5d}, missing    {2:5d}"
    tc = "You have {0:5d} Samples out of       {1:5d}, missing    {2:5d}"
    slist.append(ta.format(control_dic['scan_ROM_ZIP_files_have'],
                           control_dic['scan_ROM_ZIP_files_total'],
                           control_dic['scan_ROM_ZIP_files_missing']))
    slist.append(tb.format(control_dic['scan_CHD_files_have'],
                           control_dic['scan_CHD_files_total'],
                           control_dic['scan_CHD_files_missing']))
    slist.append(tc.format(control_dic['scan_Samples_have'],
                           control_dic['scan_Samples_total'],
                           control_dic['scan_Samples_missing']))

    ta = "Can run  {0:5d} ROM machines out of  {1:5d}, unrunnable {2:5d}"
    tb = "Can run  {0:5d} CHD machines out of  {1:5d}, unrunnable {2:5d}"
    slist.append(ta.format(control_dic['scan_machine_archives_ROM_have'],
                           control_dic['scan_machine_archives_ROM_total'],
                           control_dic['scan_machine_archives_ROM_missing']))
    slist.append(tb.format(control_dic['scan_machine_archives_CHD_have'],
                           control_dic['scan_machine_archives_CHD_total'],
                           control_dic['scan_machine_archives_CHD_missing']))

    # >> SL statistics
    slist.append('')
    slist.append('[COLOR orange]Software List scanner information[/COLOR]')
    ta = "You have {0:5d} SL ROMs out of {1:5d}, missing {2:5d}"
    tb = "You have {0:5d} SL CHDs out of {1:5d}, missing {2:5d}"
    slist.append(ta.format(control_dic['scan_SL_archives_ROM_have'],
                           control_dic['scan_SL_archives_ROM_total'],
                           control_dic['scan_SL_archives_ROM_missing']))
    slist.append(tb.format(control_dic['scan_SL_archives_CHD_have'],
                           control_dic['scan_SL_archives_CHD_total'],
                           control_dic['scan_SL_archives_CHD_missing']))

    # >> MAME asset scanner.
    slist.append('')
    slist.append('[COLOR orange]MAME asset scanner information[/COLOR]')
    # slist.append('Total number of MAME machines {0:,d}'.format(control_dic['assets_num_MAME_machines']))
    t = "You have {0:6d} MAME PCBs       , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_PCBs_have'],
                          control_dic['assets_PCBs_missing'],
                          control_dic['assets_PCBs_alternate']))
    t = "You have {0:6d} MAME Artpreviews, missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_artpreview_have'],
                          control_dic['assets_artpreview_missing'],
                          control_dic['assets_artpreview_alternate']))
    t = "You have {0:6d} MAME Artwork    , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_artwork_have'],
                          control_dic['assets_artwork_missing'],
                          control_dic['assets_artwork_alternate']))
    t = "You have {0:6d} MAME Cabinets   , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_cabinets_have'],
                          control_dic['assets_cabinets_missing'],
                          control_dic['assets_cabinets_alternate']))
    t = "You have {0:6d} MAME Clearlogos , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_clearlogos_have'],
                          control_dic['assets_clearlogos_missing'],
                          control_dic['assets_clearlogos_alternate']))
    t = "You have {0:6d} MAME CPanels    , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_cpanels_have'],
                          control_dic['assets_cpanels_missing'],
                          control_dic['assets_cpanels_alternate']))
    t = "You have {0:6d} MAME Fanart     , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_fanarts_have'],
                          control_dic['assets_fanarts_missing'],
                          control_dic['assets_fanarts_alternate']))
    t = "You have {0:6d} MAME Flyers     , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_flyers_have'],
                          control_dic['assets_flyers_missing'],
                          control_dic['assets_flyers_alternate']))
    t = "You have {0:6d} MAME Manuals    , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_manuals_have'],
                          control_dic['assets_manuals_missing'],
                          control_dic['assets_manuals_alternate']))
    t = "You have {0:6d} MAME Marquees   , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_marquees_have'],
                          control_dic['assets_marquees_missing'],
                          control_dic['assets_marquees_alternate']))
    t = "You have {0:6d} MAME Snaps      , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_snaps_have'],
                          control_dic['assets_snaps_missing'],
                          control_dic['assets_snaps_alternate']))
    t = "You have {0:6d} MAME Titles     , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_titles_have'],
                          control_dic['assets_titles_missing'],
                          control_dic['assets_titles_alternate']))
    t = "You have {0:6d} MAME Trailers   , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_trailers_have'],
                          control_dic['assets_trailers_missing'],
                          control_dic['assets_trailers_alternate']))

    # >> Software List scanner
    slist.append('')
    slist.append('[COLOR orange]Software List asset scanner information[/COLOR]')
    # slist.append('Total number of SL items {0:,d}'.format(control_dic['assets_SL_num_items']))
    t = "You have {0:6d} SL Titles   , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_SL_titles_have'],
                          control_dic['assets_SL_titles_missing'],
                          control_dic['assets_SL_titles_alternate']))
    t = "You have {0:6d} SL Snaps    , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_SL_snaps_have'],
                          control_dic['assets_SL_snaps_missing'],
                          control_dic['assets_SL_snaps_alternate']))
    t = "You have {0:6d} SL Boxfronts, missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_SL_boxfronts_have'],
                          control_dic['assets_SL_boxfronts_missing'],
                          control_dic['assets_SL_boxfronts_alternate']))
    t = "You have {0:6d} SL Fanarts  , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_SL_fanarts_have'],
                          control_dic['assets_SL_fanarts_missing'],
                          control_dic['assets_SL_fanarts_alternate']))
    t = "You have {0:6d} SL Trailers , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_SL_trailers_have'],
                          control_dic['assets_SL_trailers_missing'],
                          control_dic['assets_SL_trailers_alternate']))
    t = "You have {0:6d} SL Manuals  , missing {1:6d}, alternate {2:6d}"
    slist.append(t.format(control_dic['assets_SL_manuals_have'],
                          control_dic['assets_SL_manuals_missing'],
                          control_dic['assets_SL_manuals_alternate']))

def mame_stats_audit_print_slist(slist, control_dic, settings_dic):
    rom_set = ['Merged', 'Split', 'Non-merged'][settings_dic['mame_rom_set']]
    chd_set = ['Merged', 'Split', 'Non-merged'][settings_dic['mame_chd_set']]

    slist.append('[COLOR orange]MAME ROM audit database statistics[/COLOR]')
    t = "{0:6d} runnable MAME machines"
    slist.append(t.format(control_dic['audit_MAME_machines_runnable']))
    t = "{0:6d} machines require ROM ZIPs, {1:5d} parents and {2:5d} clones"
    slist.append(t.format(control_dic['stats_audit_machine_archives_ROM'],
                          control_dic['stats_audit_machine_archives_ROM_parents'],
                          control_dic['stats_audit_machine_archives_ROM_clones']))
    t = "{0:6d} machines require CHDs    , {1:5d} parents and {2:5d} clones"
    slist.append(t.format(control_dic['stats_audit_machine_archives_CHD'],
                          control_dic['stats_audit_machine_archives_CHD_parents'],
                          control_dic['stats_audit_machine_archives_CHD_clones']))
    t = "{0:6d} machines require Samples , {1:5d} parents and {2:5d} clones"
    slist.append(t.format(control_dic['stats_audit_machine_archives_Samples'],
                          control_dic['stats_audit_machine_archives_Samples_parents'],
                          control_dic['stats_audit_machine_archives_Samples_clones']))
    t = "{0:6d} machines require nothing , {1:5d} parents and {2:5d} clones"
    slist.append(t.format(control_dic['stats_audit_archive_less'],
                          control_dic['stats_audit_archive_less_parents'],
                          control_dic['stats_audit_archive_less_clones']))

    t = "{0:6d} ROM ZIPs    in the {1} set"
    slist.append(t.format(control_dic['stats_audit_MAME_ROM_ZIP_files'], rom_set))
    t = "{0:6d} CHDs        in the {1} set"
    slist.append(t.format(control_dic['stats_audit_MAME_CHD_files'], chd_set))
    t = "{0:6d} Sample ZIPs in the {1} set"
    slist.append(t.format(control_dic['stats_audit_MAME_Sample_ZIP_files'], rom_set))

    t = "{0:6d} total ROMs, {1:6d} valid and {2:6d} invalid"
    slist.append(t.format(
        control_dic['stats_audit_ROMs_total'],
        control_dic['stats_audit_ROMs_valid'],
        control_dic['stats_audit_ROMs_invalid'],
    ))
    t = "{0:6d} total CHDs, {1:6d} valid and {2:6d} invalid"
    slist.append(t.format(
        control_dic['stats_audit_CHDs_total'],
        control_dic['stats_audit_CHDs_valid'],
        control_dic['stats_audit_CHDs_invalid'],
    ))

    # --- SL item audit database statistics ---
    slist.append('')
    slist.append('[COLOR orange]SL audit database statistics[/COLOR]')
    t = "{0:6d} runnable Software List items"
    slist.append(t.format(control_dic['stats_audit_SL_items_runnable']))
    t = "{0:6d} SL items require ROM ZIPs and/or CHDs"
    slist.append(t.format(control_dic['stats_audit_SL_items_with_arch']))
    t = "{0:6d} SL items require ROM ZIPs"
    slist.append(t.format(control_dic['stats_audit_SL_items_with_arch_ROM']))
    t = "{0:6d} SL items require CHDs"
    slist.append(t.format(control_dic['stats_audit_SL_items_with_CHD']))

    # --- MAME audit info ---
    slist.append('\n[COLOR orange]MAME ROM audit information[/COLOR]\n')
    table_str = []
    table_str.append(['left', 'right', 'right',  'right'])
    table_str.append(['Type', 'Total', 'Good',   'Bad'])
    table_row = [
        'Machines with ROMs and/or CHDs',
        str(control_dic['audit_MAME_machines_with_arch']),
        str(control_dic['audit_MAME_machines_with_arch_OK']),
        str(control_dic['audit_MAME_machines_with_arch_BAD']),
    ]
    table_str.append(table_row)
    table_row = [
        'Machines with ROMs',
        str(control_dic['audit_MAME_machines_with_ROMs']),
        str(control_dic['audit_MAME_machines_with_ROMs_OK']),
        str(control_dic['audit_MAME_machines_with_ROMs_BAD']),
    ]
    table_str.append(table_row)
    table_row = [
        'Machines with CHDs',
        str(control_dic['audit_MAME_machines_with_CHDs']),
        str(control_dic['audit_MAME_machines_with_CHDs_OK']),
        str(control_dic['audit_MAME_machines_with_CHDs_BAD']),
    ]
    table_str.append(table_row)
    table_row = [
        'Machines with Samples',
        str(control_dic['audit_MAME_machines_with_SAMPLES']),
        str(control_dic['audit_MAME_machines_with_SAMPLES_OK']),
        str(control_dic['audit_MAME_machines_with_SAMPLES_BAD']),
    ]
    table_str.append(table_row)
    slist.extend(text_render_table_str(table_str))

    # --- SL audit info ---
    slist.append('\n[COLOR orange]SL audit information[/COLOR]\n')
    table_str = []
    table_str.append(['left', 'right', 'right',  'right'])
    table_str.append(['Type', 'Total', 'Good',   'Bad'])
    table_row = [
        'SL items with ROMs and/or CHDs',
        str(control_dic['audit_SL_items_with_arch']),
        str(control_dic['audit_SL_items_with_arch_OK']),
        str(control_dic['audit_SL_items_with_arch_BAD']),
    ]
    table_str.append(table_row)
    table_row = [
        'SL items with ROMs',
        str(control_dic['audit_SL_items_with_arch_ROM']),
        str(control_dic['audit_SL_items_with_arch_ROM_OK']),
        str(control_dic['audit_SL_items_with_arch_ROM_BAD']),
    ]
    table_str.append(table_row)
    table_row = [
        'SL items with CHDs',
        str(control_dic['audit_SL_items_with_CHD']),
        str(control_dic['audit_SL_items_with_CHD_OK']),
        str(control_dic['audit_SL_items_with_CHD_BAD']),
    ]
    table_str.append(table_row)
    slist.extend(text_render_table_str(table_str))

# -------------------------------------------------------------------------------------------------
# Check/Update/Repair Favourite ROM objects
# -------------------------------------------------------------------------------------------------
def mame_update_MAME_Fav_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog):
    line1_str = 'Checking/Updating MAME Favourites ...'
    pDialog.create('Advanced MAME Launcher', line1_str)
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    if len(fav_machines) > 1:
        num_iteration = len(fav_machines)
        iteration = 0
        for fav_key in sorted(fav_machines):
            pDialog.update((iteration*100) // num_iteration, line1_str)
            log_debug('Checking Favourite "{0}"'.format(fav_key))
            if fav_key in machines:
                machine = machines[fav_key]
                m_render = machines_render[fav_key]
                assets = assets_dic[fav_key]
                new_fav = fs_get_MAME_Favourite_full(fav_key, machine, m_render, assets, control_dic)
                fav_machines[fav_key] = new_fav
                log_debug('Updated machine    "{0}"'.format(fav_key))
            else:
                log_debug('Machine "{0}" not found in MAME main DB'.format(fav_key))
                t = 'Favourite machine "{0}" not found in database'.format(fav_key)
                kodi_dialog_OK(t)
            iteration += 1
        fs_write_JSON_file(PATHS.FAV_MACHINES_PATH.getPath(), fav_machines)
        pDialog.update((iteration*100) // num_iteration, line1_str)
    else:
        fs_write_JSON_file(PATHS.FAV_MACHINES_PATH.getPath(), fav_machines)
        pDialog.update(100, line1_str)
    pDialog.close()

def mame_update_MAME_MostPlay_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog):
    line1_str = 'Checking/Updating MAME Most Played machines ...'
    pDialog.create('Advanced MAME Launcher', line1_str)
    most_played_roms_dic = fs_load_JSON_file_dic(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if len(most_played_roms_dic) > 1:
        num_iteration = len(most_played_roms_dic)
        iteration = 0
        for fav_key in sorted(most_played_roms_dic):
            pDialog.update((iteration*100) // num_iteration, line1_str)
            log_debug('Checking Most Played machine "{0}"'.format(fav_key))
            if fav_key in machines:
                if 'launch_count' in most_played_roms_dic[fav_key]:
                    launch_count = most_played_roms_dic[fav_key]['launch_count']
                else:
                    launch_count = 1
                machine = machines[fav_key]
                m_render = machines_render[fav_key]
                assets = assets_dic[fav_key]
                new_fav = fs_get_MAME_Favourite_full(fav_key, machine, m_render, assets, control_dic)
                new_fav['launch_count'] = launch_count
                most_played_roms_dic[fav_key] = new_fav
                log_debug('Updated machine              "{0}"'.format(fav_key))
            else:
                log_debug('Machine "{0}" not found in MAME main DB'.format(fav_key))
                t = 'Favourite machine "{0}" not found in database'.format(fav_key)
                kodi_dialog_OK(t)
            iteration += 1
        fs_write_JSON_file(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
        pDialog.update((iteration*100) // num_iteration, line1_str)
    else:
        fs_write_JSON_file(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
        pDialog.update(100, line1_str)
    pDialog.close()

def mame_update_MAME_RecentPlay_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog):
    line1_str = 'Checking/Updating MAME Recently Played machines ...'
    pDialog.create('Advanced MAME Launcher', line1_str)
    recent_roms_list = fs_load_JSON_file_list(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    if len(recent_roms_list) > 1:
        num_iteration = len(recent_roms_list)
        iteration = 0
        for i, recent_rom in enumerate(recent_roms_list):
            pDialog.update((iteration*100) // num_iteration, line1_str)
            fav_key = recent_rom['name']
            log_debug('Checking Recently Played "{0}"'.format(fav_key))
            if fav_key in machines:
                machine = machines[fav_key]
                m_render = machines_render[fav_key]
                assets = assets_dic[fav_key]
                new_fav = fs_get_MAME_Favourite_full(fav_key, machine, m_render, assets, control_dic)
                recent_roms_list[i] = new_fav
                log_debug('Updated machine          "{0}"'.format(fav_key))
            else:
                log_debug('Machine "{0}" not found in MAME main DB'.format(fav_key))
                t = 'Favourite machine "{0}" not found in database'.format(fav_key)
                kodi_dialog_OK(t)
            iteration += 1
        fs_write_JSON_file(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        pDialog.update((iteration*100) // num_iteration, line1_str)
    else:
        fs_write_JSON_file(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        pDialog.update(100, line1_str)
    pDialog.close()

def mame_update_SL_Fav_objects(PATHS, control_dic, SL_catalog_dic, pDialog):
    fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
    num_SL_favs = len(fav_SL_roms)
    num_iteration = 0
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher')
    for fav_SL_key in sorted(fav_SL_roms):
        if 'ROM_name' in fav_SL_roms[fav_SL_key]:
            fav_ROM_name = fav_SL_roms[fav_SL_key]['ROM_name']
        elif 'SL_ROM_name' in fav_SL_roms[fav_SL_key]:
            fav_ROM_name = fav_SL_roms[fav_SL_key]['SL_ROM_name']
        else:
            raise TypeError('Cannot find SL ROM name')
        fav_SL_name = fav_SL_roms[fav_SL_key]['SL_name']
        log_debug('Checking SL Favourite "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))

        # >> Update progress dialog (BEGIN)
        update_number = (num_iteration * 100) // num_SL_favs
        pDialog.update(update_number, 'Checking SL Favourites (ROM "{0}") ...'.format(fav_ROM_name))
        num_iteration += 1

        # >> Load SL ROMs DB and assets
        file_name =  SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '.json'
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
        assets_file_name =  SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)
        SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath(), verbose = False)

        # >> Check
        if fav_ROM_name in SL_roms:
            SL_ROM = SL_roms[fav_ROM_name]
            SL_assets = SL_assets_dic[fav_ROM_name]
            new_fav_ROM = fs_get_SL_Favourite(fav_SL_name, fav_ROM_name, SL_ROM, SL_assets, control_dic)
            fav_SL_roms[fav_SL_key] = new_fav_ROM
            log_debug('Updated SL Favourite  "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))
        else:
            # >> Delete not found Favourites???
            log_debug('Machine "{0}" / "{1}" not found in SL main DB'.format(fav_ROM_name, fav_SL_name))
            t = 'Favourite machine "{0}" in SL "{1}" not found in database'.format(fav_ROM_name, fav_SL_name)
            kodi_dialog_OK(t)
    fs_write_JSON_file(PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
    pDialog.update(100)
    pDialog.close()

def mame_update_SL_MostPlay_objects(PATHS, control_dic, SL_catalog_dic, pDialog):
    most_played_roms_dic = fs_load_JSON_file_dic(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
    num_SL_favs = len(most_played_roms_dic)
    num_iteration = 0
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher')
    for fav_SL_key in sorted(most_played_roms_dic):
        if 'ROM_name' in most_played_roms_dic[fav_SL_key]:
            fav_ROM_name = most_played_roms_dic[fav_SL_key]['ROM_name']
        elif 'SL_ROM_name' in most_played_roms_dic[fav_SL_key]:
            fav_ROM_name = most_played_roms_dic[fav_SL_key]['SL_ROM_name']
        else:
            raise TypeError('Cannot find SL ROM name')
        if 'launch_count' in most_played_roms_dic[fav_SL_key]:
            launch_count = most_played_roms_dic[fav_SL_key]['launch_count']
        else:
            launch_count = 1
        fav_SL_name = most_played_roms_dic[fav_SL_key]['SL_name']
        log_debug('Checking SL Most Played "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))

        # >> Update progress dialog (BEGIN)
        update_number = (num_iteration * 100) // num_SL_favs
        pDialog.update(update_number, 'Checking SL Most Played (ROM "{0}") ...'.format(fav_ROM_name))
        num_iteration += 1

        # >> Load SL ROMs DB and assets
        file_name =  SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '.json'
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
        assets_file_name =  SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)
        SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath(), verbose = False)

        if fav_ROM_name in SL_roms:
            SL_ROM = SL_roms[fav_ROM_name]
            SL_assets = SL_assets_dic[fav_ROM_name]
            new_fav_ROM = fs_get_SL_Favourite(fav_SL_name, fav_ROM_name, SL_ROM, SL_assets, control_dic)
            new_fav_ROM['launch_count'] = launch_count
            most_played_roms_dic[fav_SL_key] = new_fav_ROM
            log_debug('Updated SL Most Played  "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))
        else:
            # >> Delete Favourite ROM from Favourite DB
            log_debug('Machine "{0}" / "{1}" not found in SL main DB'.format(fav_SL_name, fav_ROM_name))
            t = 'Favourite machine "{0}" in SL "{1}" not found in SL database'.format(fav_SL_name, fav_ROM_name)
            kodi_dialog_OK(t)
    fs_write_JSON_file(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
    pDialog.update(100)
    pDialog.close()

def mame_update_SL_RecentPlay_objects(PATHS, control_dic, SL_catalog_dic, pDialog):
    recent_roms_list = fs_load_JSON_file_list(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
    num_SL_favs = len(recent_roms_list)
    num_iteration = 0
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher')
    for i, recent_rom in enumerate(recent_roms_list):
        if 'ROM_name' in recent_rom:
            fav_ROM_name = recent_rom['ROM_name']
        elif 'SL_ROM_name' in recent_rom:
            fav_ROM_name = recent_rom['SL_ROM_name']
        else:
            raise TypeError('Cannot find SL ROM name')
        fav_SL_name = recent_rom['SL_name']
        log_debug('Checking SL Recently Played "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))

        # >> Update progress dialog (BEGIN)
        update_number = (num_iteration * 100) // num_SL_favs
        pDialog.update(update_number, 'Checking SL Recently Played (ROM "{0}") ...'.format(fav_ROM_name))
        num_iteration += 1

        # >> Load SL ROMs DB and assets
        file_name =  SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '.json'
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
        assets_file_name =  SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)
        SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath(), verbose = False)

        if fav_ROM_name in SL_roms:
            SL_ROM = SL_roms[fav_ROM_name]
            SL_assets = SL_assets_dic[fav_ROM_name]
            new_fav_ROM = fs_get_SL_Favourite(fav_SL_name, fav_ROM_name, SL_ROM, SL_assets, control_dic)
            recent_roms_list[i] = new_fav_ROM
            log_debug('Updated SL Recently Played  "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))
        else:
            # >> Delete Favourite ROM from Favourite DB
            log_debug('Machine "{0}" / "{1}" not found in SL main DB'.format(fav_SL_name, fav_ROM_name))
            t = 'Favourite machine "{0}" in SL "{1}" not found in SL database'.format(fav_SL_name, fav_ROM_name)
            kodi_dialog_OK(t)
    fs_write_JSON_file(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
    pDialog.update(100)
    pDialog.close()

# -------------------------------------------------------------------------------------------------
# Build MAME and SL plots
# -------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# Generate plot for MAME machines.
# Line 1) Controls are {Joystick}
# Line 2) {One Vertical Raster screen}
# Line 3) Machine [is|is not] mechanical and driver is neogeo.hpp
# Line 4) Machine has [no coin slots| N coin slots]
# Line 5) Artwork, Manual, History, Info, Gameinit, Command
# Line 6) Machine [supports|does not support] a Software List.
# ---------------------------------------------------------------------------------------------
def mame_build_MAME_plots(machines, machines_render, assets_dic, pDialog,
                          history_idx_dic, mameinfo_idx_dic, gameinit_idx_dic, command_idx_dic):
    log_info('mame_build_plots() Building machine plots/descriptions ...')
    # >> Do not crash if DAT files are not configured.
    if history_idx_dic:
        history_info_set  = {machine[0] for machine in history_idx_dic['mame']['machines']}
    else:
        history_info_set  = set()
    if mameinfo_idx_dic:
        mameinfo_info_set = {machine[0] for machine in mameinfo_idx_dic['mame']}
    else:
        mameinfo_info_set = set()
    gameinit_info_set = {machine[0] for machine in gameinit_idx_dic}
    command_info_set  = {machine[0] for machine in command_idx_dic}

    # >> Built machine plots
    pDialog.create('Advanced MAME Launcher')
    pDialog.update(0, 'Generating MAME machine plots ...')
    total_machines = len(machines)
    num_machines = 0
    for machine_name, m in machines.iteritems():
        Flag_list = []
        if assets_dic[machine_name]['artwork']: Flag_list.append('Artwork')
        if assets_dic[machine_name]['manual']: Flag_list.append('Manual')
        if machine_name in history_info_set: Flag_list.append('History')
        if machine_name in mameinfo_info_set: Flag_list.append('Info')
        if machine_name in gameinit_info_set: Flag_list.append('Gameinit')
        if machine_name in command_info_set: Flag_list.append('Command')
        Flag_str = ', '.join(Flag_list)
        if m['control_type']:
            controls_str = 'Controls {0}'.format(mame_get_control_str(m['control_type']))
        else:
            controls_str = 'No controls'
        mecha_str = 'Mechanical' if m['isMechanical'] else 'Non-mechanical'
        coin_str  = 'Machine has {0} coin slots'.format(m['coins']) if m['coins'] > 0 else 'Machine has no coin slots'
        SL_str    = ', '.join(m['softwarelists']) if m['softwarelists'] else ''

        plot_str_list = []
        plot_str_list.append('{0}'.format(controls_str))
        plot_str_list.append('{0}'.format(mame_get_screen_str(machine_name, m)))
        plot_str_list.append('{0} / Driver is {1}'.format(mecha_str, m['sourcefile']))
        plot_str_list.append('{0}'.format(coin_str))
        if Flag_str: plot_str_list.append('{0}'.format(Flag_str))
        if SL_str: plot_str_list.append('SL {0}'.format(SL_str))
        assets_dic[machine_name]['plot'] = '\n'.join(plot_str_list)

        # >> Update progress
        num_machines += 1
        pDialog.update((num_machines*100)//total_machines)
    pDialog.close()

# ---------------------------------------------------------------------------------------------
# Generate plot for Software Lists
# Line 1) SL item has {0} parts
# Line 2) {0} ROMs and {1} disks
# Line 3) Manual, History
# Line 4) Machines: machine list ...
# ---------------------------------------------------------------------------------------------
def mame_build_SL_plots(PATHS, SL_index_dic, SL_machines_dic, History_idx_dic, pDialog):
    pdialog_line1 = 'Scanning Sofware Lists assets/artwork ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(0)
    total_files = len(SL_index_dic)
    processed_files = 0
    for SL_name in sorted(SL_index_dic):
        # >> Update progress
        update_number = (processed_files*100) // total_files
        pDialog.update(update_number, pdialog_line1, 'Software List {0}'.format(SL_name))

        # >> Open database
        SL_DB_prefix = SL_index_dic[SL_name]['rom_DB_noext']
        SL_ROMs_FN      = PATHS.SL_DB_DIR.pjoin(SL_DB_prefix + '.json')
        SL_assets_FN    = PATHS.SL_DB_DIR.pjoin(SL_DB_prefix + '_assets.json')
        SL_ROM_audit_FN = PATHS.SL_DB_DIR.pjoin(SL_DB_prefix + '_ROM_audit.json')
        SL_roms          = fs_load_JSON_file_dic(SL_ROMs_FN.getPath(), verbose = False)
        SL_assets_dic    = fs_load_JSON_file_dic(SL_assets_FN.getPath(), verbose = False)
        SL_ROM_audit_dic = fs_load_JSON_file_dic(SL_ROM_audit_FN.getPath(), verbose = False)
        # >> Python Set Comprehension
        if SL_name in History_idx_dic:
            History_SL_set = { machine[0] for machine in History_idx_dic[SL_name]['machines'] }
        else:
            History_SL_set = set()
        # Machine_list = [ m['machine'] for m in SL_machines_dic[SL_name] ]
        # Machines_str = 'Machines: {0}'.format(', '.join(sorted(Machine_list)))

        # >> Traverse SL ROMs and make plot
        for rom_key in sorted(SL_roms):
            SL_rom = SL_roms[rom_key]
            num_parts = len(SL_rom['parts'])
            if num_parts == 0:   parts_str = 'SL item has no parts'
            elif num_parts == 1: parts_str = 'SL item has {0} part'.format(num_parts)
            elif num_parts > 1:  parts_str = 'SL item has {0} parts'.format(num_parts)
            num_ROMs = 0
            num_disks = 0
            for SL_rom in SL_ROM_audit_dic[rom_key]:
                if SL_rom['type'] == 'ROM': num_ROMs += 1
                elif SL_rom['type'] == 'DISK': num_disks += 1
            if num_ROMs == 0:   ROM_str = 'ROMs'
            elif num_ROMs == 1: ROM_str = 'ROM'
            elif num_ROMs > 1:  ROM_str = 'ROMs'
            if num_disks == 0:   disk_str = 'disks'
            elif num_disks == 1: disk_str = 'disk'
            elif num_disks > 1:  disk_str = 'disks'
            roms_str = '{0} {1} and {2} {3}'.format(num_ROMs, ROM_str, num_disks, disk_str)
            Flag_list = []
            if SL_assets_dic[rom_key]['manual']: Flag_list.append('Manual')
            if rom_key in History_SL_set: Flag_list.append('History')
            Flag_str = ', '.join(Flag_list)
            # >> Build plot
            # SL_roms[rom_key]['plot'] = '\n'.join([parts_str, roms_str, Flag_str, Machines_str])
            SL_roms[rom_key]['plot'] = '\n'.join([parts_str, roms_str, Flag_str])

        # >> Write SL ROMs JSON
        fs_write_JSON_file(SL_ROMs_FN.getPath(), SL_roms, verbose = False)
        # >> Update progress
        processed_files += 1
    update_number = (processed_files*100) // total_files
    pDialog.close()

# -------------------------------------------------------------------------------------------------
# MAME ROM/CHD audit code
# -------------------------------------------------------------------------------------------------
# This code is very un-optimised! But it is better to get something that works
# and then optimise. "Premature optimization is the root of all evil" -- Donald Knuth
#
# MAME loads ROMs by hash, not by filename. This is the reason MAME is able to load ROMs even
# if they have a wrong name and providing they are in the correct ZIP file (parent or clone set).
#
# Adds new field 'status': ROMS  'OK', 'OK (invalid ROM)', 'ZIP not found', 'Bad ZIP file', 
#                                'ROM not in ZIP', 'ROM bad size', 'ROM bad CRC'.
#                          DISKS 'OK', 'OK (invalid CHD)', 'CHD not found', 'CHD bad SHA1'
# Adds fields 'status_colour'.
#
# rom_list = [
#     {'type' : several types, 'name' : 'avph.03d', 'crc' : '01234567', 'location' : 'avsp/avph.03d'}, ...
#     {'type' : 'ROM_TYPE_DISK', 'name' : 'avph.03d', 'sha1' : '012...', 'location' : 'avsp/avph.03d'}, ...
# ]
#
# I'm not sure if the CHD sha1 value in MAME XML is the sha1 of the uncompressed data OR
# the sha1 of the CHD file. If the former, then AML can open the CHD file, get the sha1 from the
# header and verify it. See:
# http://www.mameworld.info/ubbthreads/showflat.php?Cat=&Number=342940&page=0&view=expanded&sb=5&o=&vc=1
#
ZIP_NOT_FOUND = 0
BAD_ZIP_FILE  = 1
ZIP_FILE_OK   = 2
def mame_audit_MAME_machine(settings, rom_list, audit_dic):
    # --- Cache the ROM set ZIP files and detect wrong named files by CRC ---
    # 1) Traverse ROMs, determine the set ZIP files, open ZIP files and put ZIPs in the cache.
    # 2) If a ZIP file is not in the cache is because the ZIP file was not found 
    # 3) z_cache_exists is used to check if the ZIP file has been found the first time or not.
    #
    # z_cache = {
    #     'zip_filename' : {
    #         'fname' : {'size' : int, 'crc' : str},
    #         'fname' : {'size' : int, 'crc' : str}, ...
    #     }
    # }
    #
    # z_cache_status = {
    #      'zip_filename' : ZIP_NOT_FOUND, BAD_ZIP_FILE, ZIP_FILE_OK
    # }
    #
    z_cache = {}
    z_cache_status = {}
    for m_rom in rom_list:
        # >> Skip CHDs
        if m_rom['type'] == ROM_TYPE_DISK: continue

        # >> Process ROM ZIP files
        set_name = m_rom['location'].split('/')[0]
        if m_rom['type'] == ROM_TYPE_SAMPLE:
            zip_FN = FileName(settings['samples_path']).pjoin(set_name + '.zip')
        else:
            zip_FN = FileName(settings['rom_path']).pjoin(set_name + '.zip')
        zip_path = zip_FN.getPath()

        # >> ZIP file encountered for the first time. Skip ZIP files already in the cache.
        if zip_path not in z_cache_status:
            if zip_FN.exists():
                # >> Scan files in ZIP file and put them in the cache
                # log_debug('Caching ZIP file {0}'.format(zip_path))
                try:
                    zip_f = z.ZipFile(zip_path, 'r')
                except z.BadZipfile as e:
                    z_cache_status[zip_path] = BAD_ZIP_FILE
                    continue
                # log_debug('ZIP {0} files {1}'.format(m_rom['location'], z_file_list))
                zip_file_dic = {}
                for zfile in zip_f.namelist():
                    # >> NOTE CRC32 in Python is a decimal number: CRC32 4225815809
                    # >> However, MAME encodes it as an hexadecimal number: CRC32 0123abcd
                    z_info = zip_f.getinfo(zfile)
                    z_info_file_size = z_info.file_size
                    z_info_crc_hex_str = '{0:08x}'.format(z_info.CRC)
                    zip_file_dic[zfile] = {'size' : z_info_file_size, 'crc' : z_info_crc_hex_str}
                    # log_debug('ZIP CRC32 {0} | CRC hex {1} | size {2}'.format(z_info.CRC, z_crc_hex, z_info.file_size))
                    # log_debug('ROM CRC hex {0} | size {1}'.format(m_rom['crc'], 0))
                zip_f.close()
                z_cache[zip_path] = zip_file_dic
                z_cache_status[zip_path] = ZIP_FILE_OK
            else:
                # >> Mark ZIP file as not found
                z_cache_status[zip_path] = ZIP_NOT_FOUND

    # --- Audit ROM by ROM ---
    for m_rom in rom_list:
        if m_rom['type'] == ROM_TYPE_DISK:
            split_list = m_rom['location'].split('/')
            set_name  = split_list[0]
            disk_name = split_list[1]
            # log_debug('Testing CHD {0}'.format(m_rom['name']))
            # log_debug('location {0}'.format(m_rom['location']))
            # log_debug('set_name  "{0}"'.format(set_name))
            # log_debug('disk_name "{0}"'.format(disk_name))

            # >> Invalid CHDs
            if not m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_CHD
                m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if DISK file exists
            chd_FN = FileName(settings['chd_path']).pjoin(set_name).pjoin(disk_name + '.chd')
            # log_debug('chd_FN P {0}'.format(chd_FN.getPath()))
            if not chd_FN.exists():
                m_rom['status'] = AUDIT_STATUS_CHD_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Open CHD file and check SHA1 hash.
            chd_info = _mame_stat_chd(chd_FN.getPath())
            if chd_info['status'] == CHD_BAD_CHD:
                m_rom['status'] = AUDIT_STATUS_BAD_CHD_FILE
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['status'] == CHD_BAD_VERSION:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_VERSION
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['sha1'] != m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_SHA1
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> DISK is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
        elif m_rom['type'] == ROM_TYPE_SAMPLE:
            split_list = m_rom['location'].split('/')
            set_name = split_list[0]
            sample_name = split_list[1] + '.wav'
            # log_debug('Testing SAMPLE {0}'.format(m_rom['name']))
            # log_debug('location       {0}'.format(m_rom['location']))
            # log_debug('set_name       {0}'.format(set_name))
            # log_debug('sample_name    {0}'.format(sample_name))

            # >> Test if ZIP file exists (use cached data). ZIP file must be in the cache always
            # >> at this point.
            zip_FN = FileName(settings['samples_path']).pjoin(set_name + '.zip')
            zip_path = zip_FN.getPath()
            # log_debug('ZIP {0}'.format(zip_FN.getPath()))
            if z_cache_status[zip_path] == ZIP_NOT_FOUND:
                m_rom['status'] = AUDIT_STATUS_ZIP_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            elif z_cache_status[zip_path] == BAD_ZIP_FILE:
                m_rom['status'] = AUDIT_STATUS_BAD_ZIP_FILE
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            # >> ZIP file is good and data was cached.
            zip_file_dic = z_cache[zip_path]

            # >> At this point the ZIP file is in the cache (if it was open)
            if sample_name not in zip_file_dic:
                # >> File not found by filename. Check if it has renamed by looking at CRC.
                # >> ROM not in ZIP (not even under other filename)
                m_rom['status'] = AUDIT_STATUS_SAMPLE_NOT_IN_ZIP
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> SAMPLE is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])

        else:
            split_list = m_rom['location'].split('/')
            set_name = split_list[0]
            rom_name = split_list[1]
            # log_debug('Testing ROM {0}'.format(m_rom['name']))
            # log_debug('location    {0}'.format(m_rom['location']))
            # log_debug('set_name    {0}'.format(set_name))
            # log_debug('rom_name    {0}'.format(rom_name))

            # >> Invalid ROMs are not in the ZIP file
            if not m_rom['crc']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_ROM
                m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if ZIP file exists (use cached data). ZIP file must be in the cache always
            # >> at this point.
            zip_FN = FileName(settings['rom_path']).pjoin(set_name + '.zip')
            zip_path = zip_FN.getPath()
            # log_debug('ZIP {0}'.format(zip_FN.getPath()))
            if z_cache_status[zip_path] == ZIP_NOT_FOUND:
                m_rom['status'] = AUDIT_STATUS_ZIP_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            elif z_cache_status[zip_path] == BAD_ZIP_FILE:
                m_rom['status'] = AUDIT_STATUS_BAD_ZIP_FILE
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            # >> ZIP file is good and data was cached.
            zip_file_dic = z_cache[zip_path]

            # >> At this point the ZIP file is in the cache (if it was open)
            if rom_name in zip_file_dic:
                # >> File has correct name
                if zip_file_dic[rom_name]['size'] != m_rom['size']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_SIZE
                    m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                    continue
                if zip_file_dic[rom_name]['crc'] != m_rom['crc']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_CRC
                    m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                    continue
            else:
                # >> File not found by filename. Check if it has renamed by looking at CRC.
                rom_OK_name = ''
                for fn in zip_file_dic:
                    if m_rom['crc'] == zip_file_dic[fn]['crc']:
                        rom_OK_name = fn
                        break
                if rom_OK_name:
                    # >> File found by CRC
                    m_rom['status'] = AUDIT_STATUS_OK_WRONG_NAME_ROM
                    m_rom['status_colour'] = '[COLOR orange]OK (named {0})[/COLOR]'.format(rom_OK_name)
                    continue
                else:
                    # >> ROM not in ZIP (not even under other filename)
                    m_rom['status'] = AUDIT_STATUS_ROM_NOT_IN_ZIP
                    m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                    continue

            # >> ROM is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])

    # >> Audit results
    # >> Naive and slow code, but better safe than sorry.
    ROM_OK_status_list = []
    SAM_OK_status_list = []
    CHD_OK_status_list = []
    audit_dic['machine_has_ROMs_or_CHDs'] = False
    audit_dic['machine_has_ROMs']         = False
    audit_dic['machine_has_SAMPLES']      = False
    audit_dic['machine_has_CHDs']         = False
    for m_rom in rom_list:
        audit_dic['machine_has_ROMs_or_CHDs'] = True
        if m_rom['type'] == ROM_TYPE_DISK:
            audit_dic['machine_has_CHDs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
               m_rom['status'] == AUDIT_STATUS_OK_INVALID_CHD:
                CHD_OK_status_list.append(True)
            else:
                CHD_OK_status_list.append(False)
        elif m_rom['type'] == ROM_TYPE_SAMPLE:
            audit_dic['machine_has_SAMPLES'] = True
            if m_rom['status'] == AUDIT_STATUS_OK:
                SAM_OK_status_list.append(True)
            else:
                SAM_OK_status_list.append(False)
        else:
            audit_dic['machine_has_ROMs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
               m_rom['status'] == AUDIT_STATUS_OK_INVALID_ROM or \
               m_rom['status'] == AUDIT_STATUS_OK_WRONG_NAME_ROM:
                ROM_OK_status_list.append(True)
            else:
                ROM_OK_status_list.append(False)
    audit_dic['machine_ROMs_are_OK']    = all(ROM_OK_status_list) if audit_dic['machine_has_ROMs'] else True
    audit_dic['machine_SAMPLES_are_OK'] = all(SAM_OK_status_list) if audit_dic['machine_has_SAMPLES'] else True
    audit_dic['machine_CHDs_are_OK']    = all(CHD_OK_status_list) if audit_dic['machine_has_CHDs'] else True
    audit_dic['machine_is_OK'] = audit_dic['machine_ROMs_are_OK'] and \
                                 audit_dic['machine_SAMPLES_are_OK'] and \
                                 audit_dic['machine_CHDs_are_OK'] 

# -------------------------------------------------------------------------------------------------
# SL ROM/CHD audit code
# -------------------------------------------------------------------------------------------------
def mame_audit_SL_machine(settings, rom_list, audit_dic):
    # --- Cache the ROM set ZIP files and detect wrong named files by CRC ---
    # >> Look at mame_audit_MAME_machine() for comments.
    z_cache = {}
    z_cache_status = {}
    for m_rom in rom_list:
        # >> Skip CHDs
        if m_rom['type'] == ROM_TYPE_DISK: continue

        # >> Process ROM ZIP files
        split_list = m_rom['location'].split('/')
        SL_name  = split_list[0]
        zip_name = split_list[1] + '.zip'
        zip_FN = FileName(settings['SL_rom_path']).pjoin(SL_name).pjoin(zip_name)
        zip_path = zip_FN.getPath()

        # >> ZIP file encountered for the first time. Skip ZIP files already in the cache.
        if zip_path not in z_cache_status:
            if zip_FN.exists():
                # >> Scan files in ZIP file and put them in the cache
                # log_debug('Caching ZIP file {0}'.format(zip_path))
                try:
                    zip_f = z.ZipFile(zip_path, 'r')
                except z.BadZipfile as e:
                    z_cache_status[zip_path] = BAD_ZIP_FILE
                    continue
                # log_debug('ZIP {0} files {1}'.format(m_rom['location'], z_file_list))
                zip_file_dic = {}
                for zfile in zip_f.namelist():
                    # >> NOTE CRC32 in Python is a decimal number: CRC32 4225815809
                    # >> However, MAME encodes it as an hexadecimal number: CRC32 0123abcd
                    z_info = zip_f.getinfo(zfile)
                    z_info_file_size = z_info.file_size
                    z_info_crc_hex_str = '{0:08x}'.format(z_info.CRC)
                    zip_file_dic[zfile] = {'size' : z_info_file_size, 'crc' : z_info_crc_hex_str}
                    # log_debug('ZIP CRC32 {0} | CRC hex {1} | size {2}'.format(z_info.CRC, z_crc_hex, z_info.file_size))
                    # log_debug('ROM CRC hex {0} | size {1}'.format(m_rom['crc'], 0))
                zip_f.close()
                z_cache[zip_path] = zip_file_dic
                z_cache_status[zip_path] = ZIP_FILE_OK
            else:
                # >> Mark ZIP file as not found
                z_cache_status[zip_path] = ZIP_NOT_FOUND

    # >> Audit ROM by ROM
    for m_rom in rom_list:
        if m_rom['type'] == ROM_TYPE_DISK:
            split_list = m_rom['location'].split('/')
            SL_name   = split_list[0]
            item_name = split_list[1]
            disk_name = split_list[2]
            # log_debug('Testing CHD "{0}"'.format(m_rom['name']))
            # log_debug('location "{0}"'.format(m_rom['location']))
            # log_debug('SL_name   "{0}"'.format(SL_name))
            # log_debug('item_name "{0}"'.format(item_name))
            # log_debug('disk_name "{0}"'.format(disk_name))

            # >> Invalid CHDs
            if not m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_CHD
                m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if DISK file exists
            chd_FN = FileName(settings['SL_chd_path']).pjoin(SL_name).pjoin(item_name).pjoin(disk_name + '.chd')
            # log_debug('chd_FN P {0}'.format(chd_FN.getPath()))
            if not chd_FN.exists():
                m_rom['status'] = AUDIT_STATUS_CHD_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Open CHD file and check SHA1 hash.
            chd_info = _mame_stat_chd(chd_FN.getPath())
            if chd_info['status'] == CHD_BAD_CHD:
                m_rom['status'] = AUDIT_STATUS_BAD_CHD_FILE
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['status'] == CHD_BAD_VERSION:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_VERSION
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['sha1'] != m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_SHA1
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> DISK is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
        else:
            split_list = m_rom['location'].split('/')
            SL_name   = split_list[0]
            item_name = split_list[1]
            rom_name  = split_list[2]
            # log_debug('Testing ROM "{0}"'.format(m_rom['name']))
            # log_debug('location "{0}"'.format(m_rom['location']))
            # log_debug('SL_name   "{0}"'.format(SL_name))
            # log_debug('item_name "{0}"'.format(item_name))
            # log_debug('rom_name  "{0}"'.format(rom_name))

            # >> Invalid ROMs are not in the ZIP file
            if not m_rom['crc']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_ROM
                m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if ZIP file exists
            zip_FN = FileName(settings['SL_rom_path']).pjoin(SL_name).pjoin(item_name + '.zip')
            zip_path = zip_FN.getPath()
            # log_debug('zip_FN P {0}'.format(zip_FN.getPath()))
            if z_cache_status[zip_path] == ZIP_NOT_FOUND:
                m_rom['status'] = AUDIT_STATUS_ZIP_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            elif z_cache_status[zip_path] == BAD_ZIP_FILE:
                m_rom['status'] = AUDIT_STATUS_BAD_ZIP_FILE
                m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                continue
            # >> ZIP file is good and data was cached.
            zip_file_dic = z_cache[zip_path]

            # >> At this point the ZIP file is in the cache (if it was open)
            if rom_name in zip_file_dic:
                # >> File has correct name
                if zip_file_dic[rom_name]['size'] != m_rom['size']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_SIZE
                    m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                    continue
                if zip_file_dic[rom_name]['crc'] != m_rom['crc']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_CRC
                    m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                    continue
            else:
                # >> File not found by filename. Check if it has renamed by looking at CRC.
                rom_OK_name = ''
                for fn in zip_file_dic:
                    if m_rom['crc'] == zip_file_dic[fn]['crc']:
                        rom_OK_name = fn
                        break
                if rom_OK_name:
                    # >> File found by CRC
                    m_rom['status'] = AUDIT_STATUS_OK_WRONG_NAME_ROM
                    m_rom['status_colour'] = '[COLOR orange]OK (named {0})[/COLOR]'.format(rom_OK_name)
                    continue
                else:
                    # >> ROM not in ZIP (not even under other filename)
                    m_rom['status'] = AUDIT_STATUS_ROM_NOT_IN_ZIP
                    m_rom['status_colour'] = '[COLOR red]{0}[/COLOR]'.format(m_rom['status'])
                    continue

            # >> ROM is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{0}[/COLOR]'.format(m_rom['status'])
            # log_debug('{0}'.format(AUDIT_STATUS_OK))

    # >> Currently exactly same code as in mame_audit_MAME_machine()
    # >> Audit results
    # >> Naive and slow code, but better safe than sorry.
    ROM_OK_status_list = []
    CHD_OK_status_list = []
    audit_dic['machine_has_ROMs_or_CHDs'] = False
    audit_dic['machine_has_ROMs']         = False
    audit_dic['machine_has_CHDs']         = False
    for m_rom in rom_list:
        audit_dic['machine_has_ROMs_or_CHDs'] = True
        if m_rom['type'] == ROM_TYPE_DISK:
            audit_dic['machine_has_CHDs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
               m_rom['status'] == AUDIT_STATUS_OK_INVALID_CHD:
                CHD_OK_status_list.append(True)
            else:
                CHD_OK_status_list.append(False)
        else:
            audit_dic['machine_has_ROMs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
               m_rom['status'] == AUDIT_STATUS_OK_INVALID_ROM or \
               m_rom['status'] == AUDIT_STATUS_OK_WRONG_NAME_ROM:
                ROM_OK_status_list.append(True)
            else:
                ROM_OK_status_list.append(False)
    audit_dic['machine_ROMs_are_OK'] = all(ROM_OK_status_list) if audit_dic['machine_has_ROMs'] else True
    audit_dic['machine_CHDs_are_OK'] = all(CHD_OK_status_list) if audit_dic['machine_has_CHDs'] else True
    audit_dic['machine_is_OK'] = audit_dic['machine_ROMs_are_OK'] and audit_dic['machine_CHDs_are_OK']

def mame_audit_MAME_all(PATHS, pDialog, settings, control_dic, machines, machines_render, audit_roms_dic):
    log_debug('mame_audit_MAME_all() Initialising ...')

    # >> Go machine by machine and audit ZIPs and CHDs.
    # >> Adds new column 'status' to each ROM.
    pDialog.create('Advanced MAME Launcher', 'Auditing MAME ROMs and CHDs ... ')
    total_machines = len(machines_render)
    processed_machines = 0
    machine_audit_dic = {}
    for m_name in sorted(machines_render):
        pDialog.update((processed_machines * 100) // total_machines)
        # >> Machine has ROMs
        audit_dic = fs_new_audit_dic()
        if m_name in audit_roms_dic:
            # >> roms_dic is mutable and edited inside the function
            rom_list = audit_roms_dic[m_name]
            mame_audit_MAME_machine(settings, rom_list, audit_dic)
        machine_audit_dic[m_name] = audit_dic
        processed_machines += 1
        if pDialog.iscanceled(): break
    pDialog.close()

    # >> Audit statistics.
    audit_MAME_machines_runnable         = 0
    audit_MAME_machines_with_arch        = 0
    audit_MAME_machines_with_arch_OK     = 0
    audit_MAME_machines_with_arch_BAD    = 0
    audit_MAME_machines_without          = 0
    audit_MAME_machines_with_ROMs        = 0
    audit_MAME_machines_with_ROMs_OK     = 0
    audit_MAME_machines_with_ROMs_BAD    = 0
    audit_MAME_machines_without_ROMs     = 0
    audit_MAME_machines_with_SAMPLES     = 0
    audit_MAME_machines_with_SAMPLES_OK  = 0
    audit_MAME_machines_with_SAMPLES_BAD = 0
    audit_MAME_machines_without_SAMPLES  = 0
    audit_MAME_machines_with_CHDs        = 0
    audit_MAME_machines_with_CHDs_OK     = 0
    audit_MAME_machines_with_CHDs_BAD    = 0
    audit_MAME_machines_without_CHDs     = 0
    for m_name in machines_render:
        render_dic = machines_render[m_name]
        audit_dic = machine_audit_dic[m_name]
        # >> Skip unrunnable (device) machines
        if render_dic['isDevice']: continue
        audit_MAME_machines_runnable += 1
        if audit_dic['machine_has_ROMs_or_CHDs']:
            audit_MAME_machines_with_arch += 1
            if audit_dic['machine_is_OK']: audit_MAME_machines_with_arch_OK += 1
            else:                          audit_MAME_machines_with_arch_BAD += 1
        else:
            audit_MAME_machines_without += 1

        if audit_dic['machine_has_ROMs']:
            audit_MAME_machines_with_ROMs += 1
            if audit_dic['machine_ROMs_are_OK']: audit_MAME_machines_with_ROMs_OK += 1
            else:                                audit_MAME_machines_with_ROMs_BAD += 1
        else:
            audit_MAME_machines_without_ROMs += 1

        if audit_dic['machine_has_SAMPLES']:
            audit_MAME_machines_with_SAMPLES += 1
            if audit_dic['machine_SAMPLES_are_OK']: audit_MAME_machines_with_SAMPLES_OK += 1
            else:                                   audit_MAME_machines_with_SAMPLES_BAD += 1
        else:
            audit_MAME_machines_without_SAMPLES += 1

        if audit_dic['machine_has_CHDs']:
            audit_MAME_machines_with_CHDs += 1
            if audit_dic['machine_CHDs_are_OK']: audit_MAME_machines_with_CHDs_OK += 1
            else:                                audit_MAME_machines_with_CHDs_BAD += 1
        else:
            audit_MAME_machines_without_CHDs += 1

    # --- Report header and statistics ---
    report_full_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows full audit report',
    ]
    report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good ROMs and/or CHDs',
    ]
    report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing ROMs and/or CHDs',
    ]
    ROM_report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good ROMs',
    ]
    ROM_report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing ROMs',
    ]
    SAMPLES_report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good Samples',
    ]
    SAMPLES_report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing Samples',
    ]
    CHD_report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good CHDs',
    ]
    CHD_report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing CHDs',
    ]
    h_list = [
        'There are {0} machines in total'.format(total_machines),
        'Of those, {0} are runnable machines'.format(audit_MAME_machines_runnable),
    ]
    report_full_list.extend(h_list)
    report_good_list.extend(h_list)
    report_error_list.extend(h_list)
    ROM_report_good_list.extend(h_list)
    ROM_report_error_list.extend(h_list)
    SAMPLES_report_good_list.extend(h_list)
    SAMPLES_report_error_list.extend(h_list)
    CHD_report_good_list.extend(h_list)
    CHD_report_error_list.extend(h_list)

    h_list = [
        'Of those, {0} require ROMs and or CHDSs'.format(audit_MAME_machines_with_arch),
        'Of those, {0} are OK and {1} have bad/missing ROMs and/or CHDs'.format(
            audit_MAME_machines_with_arch_OK, audit_MAME_machines_with_arch_BAD ),
    ]
    report_good_list.extend(h_list)
    report_error_list.extend(h_list)
    h_list = [
        'Of those, {0} require ROMs'.format(audit_MAME_machines_with_ROMs),
        'Of those, {0} are OK and {1} have bad/missing ROMs and/or CHDs'.format(
            audit_MAME_machines_with_ROMs_OK, audit_MAME_machines_with_ROMs_BAD ),
    ]
    ROM_report_good_list.extend(h_list)
    ROM_report_error_list.extend(h_list)
    h_list = [
        'Of those, {0} require ROMs and or CHDSs'.format(audit_MAME_machines_with_CHDs),
        'Of those, {0} are OK and {1} have bad/missing ROMs and/or CHDs'.format(
            audit_MAME_machines_with_CHDs_OK, audit_MAME_machines_with_CHDs_BAD ),
    ]
    CHD_report_good_list.extend(h_list)
    CHD_report_error_list.extend(h_list)

    report_full_list.append('')
    report_good_list.append('')
    report_error_list.append('')
    ROM_report_good_list.append('')
    ROM_report_error_list.append('')
    SAMPLES_report_good_list.append('')
    SAMPLES_report_error_list.append('')
    CHD_report_good_list.append('')
    CHD_report_error_list.append('')

    # >> Generate report.
    pDialog.create('Advanced MAME Launcher', 'Generating audit reports ... ')
    total_machines = len(machines_render)
    processed_machines = 0
    for m_name in sorted(machines_render):
        # >> Update progress dialog
        pDialog.update((processed_machines * 100) // total_machines)

        # >> Skip ROMless and/or CHDless machines from reports, except the full report
        description = machines_render[m_name]['description']
        cloneof = machines_render[m_name]['cloneof']
        if m_name not in audit_roms_dic:
            head_list = []
            head_list.append('Machine {0} "{1}"'.format(m_name, description))
            if cloneof:
                clone_desc = machines_render[cloneof]['description']
                head_list.append('Cloneof {0} "{1}"'.format(cloneof, clone_desc))
            head_list.append('This machine has no ROMs and/or CHDs')
            report_full_list.extend(head_list)
            continue
        rom_list = audit_roms_dic[m_name]
        if not rom_list: continue

        # >> Check if audit was canceled.
        # log_debug(unicode(rom_list))
        if 'status' not in rom_list[0]:
            report_list.append('Audit was canceled at machine {0}'.format(m_name))
            break

        # >> Machine header (in all reports).
        head_list = []
        head_list.append('Machine {0} "{1}"'.format(m_name, description))
        if cloneof:
            clone_desc = machines_render[cloneof]['description']
            head_list.append('Cloneof {0} "{1}"'.format(cloneof, clone_desc))

        # >> ROM/CHD report.
        table_str = [ ['right', 'left', 'right', 'left', 'left', 'left'] ]
        for m_rom in rom_list:
            if m_rom['type'] == ROM_TYPE_DISK:
                table_row = [m_rom['type'], m_rom['name'], '', m_rom['sha1'][0:8],
                             m_rom['location'], m_rom['status']]
            elif m_rom['type'] == ROM_TYPE_SAMPLE:
                table_row = [m_rom['type'], m_rom['name'], '', '',
                             m_rom['location'], m_rom['status']]
            else:
                table_row = [m_rom['type'], m_rom['name'],
                             str(m_rom['size']), m_rom['crc'],
                             m_rom['location'], m_rom['status']]
            table_str.append(table_row)
        local_str_list = text_render_table_str_NO_HEADER(table_str)
        local_str_list.append('')

        # --- At this point all machines have ROMs and/or CHDs ---
        # >> Full, ROMs and/or CHDs report.
        audit_dic = machine_audit_dic[m_name]
        report_full_list.extend(head_list + local_str_list)
        if audit_dic['machine_is_OK']:
            report_good_list.extend(head_list + local_str_list)
        else:
            report_error_list.extend(head_list + local_str_list)

        # >> ROM report
        if audit_dic['machine_has_ROMs']:
            if audit_dic['machine_ROMs_are_OK']:
                ROM_report_good_list.extend(head_list + local_str_list)
            else:
                ROM_report_error_list.extend(head_list + local_str_list)

        # >> Samples report
        if audit_dic['machine_has_SAMPLES']:
            if audit_dic['machine_SAMPLES_are_OK']:
                SAMPLES_report_good_list.extend(head_list + local_str_list)
            else:
                SAMPLES_report_error_list.extend(head_list + local_str_list)

        # >> CHD report.
        if audit_dic['machine_has_CHDs']:
            if audit_dic['machine_CHDs_are_OK']:
                CHD_report_good_list.extend(head_list + local_str_list)
            else:
                CHD_report_error_list.extend(head_list + local_str_list)

        # >> Update progress dialog. Check if user run out of patience.
        processed_machines += 1
    else:
        a = '*** MAME audit finished ***'
        report_full_list.append(a)
        report_good_list.append(a)
        report_error_list.append(a)
        ROM_report_good_list.append(a)
        ROM_report_error_list.append(a)
        SAMPLES_report_good_list.append(a)
        SAMPLES_report_error_list.append(a)
        CHD_report_good_list.append(a)
        CHD_report_error_list.append(a)
    pDialog.close()

    # --- Write reports ---
    pDialog.create('Advanced MAME Launcher', 'Writing report files ... ')
    num_items = 9
    pDialog.update(int((0*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_FULL_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_full_list).encode('utf-8'))
    pDialog.update(int((1*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_good_list).encode('utf-8'))
    pDialog.update(int((2*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_error_list).encode('utf-8'))
    pDialog.update(int((3*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_ROM_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(ROM_report_good_list).encode('utf-8'))
    pDialog.update(int((4*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(ROM_report_error_list).encode('utf-8'))
    pDialog.update(int((5*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(SAMPLES_report_good_list).encode('utf-8'))
    pDialog.update(int((6*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(SAMPLES_report_error_list).encode('utf-8'))
    pDialog.update(int((7*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_CHD_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(CHD_report_good_list).encode('utf-8'))
    pDialog.update(int((8*100) / num_items))
    with open(PATHS.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(CHD_report_error_list).encode('utf-8'))
    pDialog.update(int((9*100) / num_items))
    pDialog.close()

    # >> Update MAME audit statistics.
    change_control_dic(control_dic, 'audit_MAME_machines_runnable', audit_MAME_machines_runnable)
    change_control_dic(control_dic, 'audit_MAME_machines_with_arch', audit_MAME_machines_with_arch)
    change_control_dic(control_dic, 'audit_MAME_machines_with_arch_OK', audit_MAME_machines_with_arch_OK)
    change_control_dic(control_dic, 'audit_MAME_machines_with_arch_BAD', audit_MAME_machines_with_arch_BAD)
    change_control_dic(control_dic, 'audit_MAME_machines_without', audit_MAME_machines_without)
    change_control_dic(control_dic, 'audit_MAME_machines_with_ROMs', audit_MAME_machines_with_ROMs)
    change_control_dic(control_dic, 'audit_MAME_machines_with_ROMs_OK', audit_MAME_machines_with_ROMs_OK)
    change_control_dic(control_dic, 'audit_MAME_machines_with_ROMs_BAD', audit_MAME_machines_with_ROMs_BAD)
    change_control_dic(control_dic, 'audit_MAME_machines_without_ROMs', audit_MAME_machines_without_ROMs)
    change_control_dic(control_dic, 'audit_MAME_machines_with_SAMPLES', audit_MAME_machines_with_SAMPLES)
    change_control_dic(control_dic, 'audit_MAME_machines_with_SAMPLES_OK', audit_MAME_machines_with_SAMPLES_OK)
    change_control_dic(control_dic, 'audit_MAME_machines_with_SAMPLES_BAD', audit_MAME_machines_with_SAMPLES_BAD)
    change_control_dic(control_dic, 'audit_MAME_machines_without_SAMPLES', audit_MAME_machines_without_SAMPLES)
    change_control_dic(control_dic, 'audit_MAME_machines_with_CHDs', audit_MAME_machines_with_CHDs)
    change_control_dic(control_dic, 'audit_MAME_machines_with_CHDs_OK', audit_MAME_machines_with_CHDs_OK)
    change_control_dic(control_dic, 'audit_MAME_machines_with_CHDs_BAD', audit_MAME_machines_with_CHDs_BAD)
    change_control_dic(control_dic, 'audit_MAME_machines_without_CHDs', audit_MAME_machines_without_CHDs)

    # >> Update timestamp
    change_control_dic(control_dic, 't_MAME_audit', time.time())

def mame_audit_SL_all(PATHS, settings, control_dic):
    log_debug('mame_audit_SL_all() Initialising ...')

    # >> Load SL catalog.
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

    # >> Report header and statistics
    report_full_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows full Software Lists audit report',
    ]
    report_good_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with good ROMs and/or CHDs',
    ]
    report_error_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with errors in ROMs and/or CHDs',
    ]
    ROM_report_good_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with good ROMs',
    ]
    ROM_report_error_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with errors in ROMs',
    ]
    CHD_report_good_list  = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with good CHDs',
    ]
    CHD_report_error_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with errors in CHDs',
    ]
    h_list = [
        'There are {0} software lists'.format(len(SL_catalog_dic)),
        '',
    ]
    report_full_list.extend(h_list)
    report_good_list.extend(h_list)
    report_error_list.extend(h_list)
    ROM_report_good_list.extend(h_list)
    ROM_report_error_list.extend(h_list)
    CHD_report_good_list.extend(h_list)
    CHD_report_error_list.extend(h_list)

    # >> DEBUG code
    # SL_catalog_dic = {
    #     "32x" : {
    #         "display_name" : "Sega 32X cartridges",
    #         "num_with_CHDs" : 0,
    #         "num_with_ROMs" : 203,
    #         "rom_DB_noext" : "32x"
    #     }
    # }

    # >> SL audit statistics.
    audit_SL_items_runnable          = 0
    audit_SL_items_with_arch         = 0
    audit_SL_items_with_arch_OK      = 0
    audit_SL_items_with_arch_BAD     = 0
    audit_SL_items_without_arch      = 0
    audit_SL_items_with_arch_ROM     = 0
    audit_SL_items_with_arch_ROM_OK  = 0
    audit_SL_items_with_arch_ROM_BAD = 0
    audit_SL_items_without_arch_ROM  = 0
    audit_SL_items_with_CHD          = 0
    audit_SL_items_with_CHD_OK       = 0
    audit_SL_items_with_CHD_BAD      = 0
    audit_SL_items_without_CHD       = 0

    # >> Iterate all SL databases and audit ROMs.
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False
    pdialog_line1 = 'Auditing Sofware Lists ROMs and CHDs ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    total_files = len(SL_catalog_dic)
    processed_files = 0
    for SL_name in sorted(SL_catalog_dic):
        pDialog.update((processed_files*100) // total_files, pdialog_line1, 'Software List {0}'.format(SL_name))
        SL_dic = SL_catalog_dic[SL_name]
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_dic['rom_DB_noext'] + '.json')
        SL_AUDIT_ROMs_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_dic['rom_DB_noext'] + '_ROM_audit.json')
        roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)
        audit_roms = fs_load_JSON_file_dic(SL_AUDIT_ROMs_DB_FN.getPath(), verbose = False)

        # >> Iterate SL ROMs
        for rom_key in sorted(roms):
            # >> audit_roms_list and audit_dic are mutable and edited inside the function()
            audit_rom_list = audit_roms[rom_key]
            audit_dic = fs_new_audit_dic()
            mame_audit_SL_machine(settings, audit_rom_list, audit_dic)

            # >> Audit statistics
            audit_SL_items_runnable += 1
            if audit_dic['machine_has_ROMs_or_CHDs']:
                audit_SL_items_with_arch += 1
                if audit_dic['machine_is_OK']: audit_SL_items_with_arch_OK += 1
                else:                          audit_SL_items_with_arch_BAD += 1
            else:
                audit_SL_items_without_arch += 1

            if audit_dic['machine_has_ROMs']:
                audit_SL_items_with_arch_ROM += 1
                if audit_dic['machine_ROMs_are_OK']: audit_SL_items_with_arch_ROM_OK += 1
                else:                                audit_SL_items_with_arch_ROM_BAD += 1
            else:
                audit_SL_items_without_arch_ROM += 1

            if audit_dic['machine_has_CHDs']:
                audit_SL_items_with_CHD += 1
                if audit_dic['machine_CHDs_are_OK']: audit_SL_items_with_CHD_OK += 1
                else:                                audit_SL_items_with_CHD_BAD += 1
            else:
                audit_SL_items_without_CHD += 1

            # >> Software/machine header.
            # WARNING: Kodi crashes with a 22 MB text file with colours. No problem
            # if TXT file has not colours.
            rom = roms[rom_key]
            cloneof = rom['cloneof']
            head_list = []
            if cloneof:
                head_list.append('SL {0} ROM {1} (cloneof {2})'.format(SL_name, rom_key, cloneof))
            else:
                head_list.append('SL {0} ROM {1}'.format(SL_name, rom_key))

            # >> ROM/CHD report.
            table_str = [ ['right', 'left', 'left', 'left', 'left'] ]
            for m_rom in audit_rom_list:
                if m_rom['type'] == ROM_TYPE_DISK:
                    table_row = [m_rom['type'], '',
                                 m_rom['sha1'][0:8], m_rom['location'], m_rom['status']]
                else:
                    table_row = [m_rom['type'], str(m_rom['size']),
                                 m_rom['crc'], m_rom['location'], m_rom['status']]
                table_str.append(table_row)
            local_str_list = text_render_table_str_NO_HEADER(table_str)
            local_str_list.append('')

            # >> Full, ROMs and CHDs report.
            report_full_list.extend(head_list + local_str_list)
            if audit_dic['machine_is_OK']:
                report_good_list.extend(head_list + local_str_list)
            else:
                report_error_list.extend(head_list + local_str_list)

            # >> ROM report
            if audit_dic['machine_has_ROMs']:
                if audit_dic['machine_ROMs_are_OK']:
                    ROM_report_good_list.extend(head_list + local_str_list)
                else:
                    ROM_report_error_list.extend(head_list + local_str_list)

            # >> CHD report.
            if audit_dic['machine_has_CHDs']:
                if audit_dic['machine_CHDs_are_OK']:
                    CHD_report_good_list.extend(head_list + local_str_list)
                else:
                    CHD_report_error_list.extend(head_list + local_str_list)

        # >> Update progress
        processed_files += 1
    else:
        a = '*** Software Lists audit finished ***'
        report_full_list.append(a)
        report_good_list.append(a)
        report_error_list.append(a)
        ROM_report_good_list.append(a)
        ROM_report_error_list.append(a)
        CHD_report_good_list.append(a)
        CHD_report_error_list.append(a)
    pDialog.close()

    # >> Write report.
    pdialog_line1 = 'Writing SL audit reports ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    num_items = 7
    pDialog.update(int((0*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_FULL_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_full_list).encode('utf-8'))
    pDialog.update(int((1*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_good_list).encode('utf-8'))
    pDialog.update(int((2*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_error_list).encode('utf-8'))
    pDialog.update(int((3*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_ROMS_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(ROM_report_good_list).encode('utf-8'))
    pDialog.update(int((4*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(ROM_report_error_list).encode('utf-8'))
    pDialog.update(int((5*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_CHDS_GOOD_PATH.getPath(), 'w') as file:
        file.write('\n'.join(CHD_report_good_list).encode('utf-8'))
    pDialog.update(int((6*100) / num_items))
    with open(PATHS.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(CHD_report_error_list).encode('utf-8'))
    pDialog.update(int((7*100) / num_items))
    pDialog.close()

    # >> Update SL audit statistics.
    change_control_dic(control_dic, 'audit_SL_items_runnable', audit_SL_items_runnable)
    
    change_control_dic(control_dic, 'audit_SL_items_with_arch', audit_SL_items_with_arch)
    change_control_dic(control_dic, 'audit_SL_items_with_arch_OK', audit_SL_items_with_arch_OK)
    change_control_dic(control_dic, 'audit_SL_items_with_arch_BAD', audit_SL_items_with_arch_BAD)
    change_control_dic(control_dic, 'audit_SL_items_without_arch', audit_SL_items_without_arch)
    change_control_dic(control_dic, 'audit_SL_items_with_arch_ROM', audit_SL_items_with_arch_ROM)
    change_control_dic(control_dic, 'audit_SL_items_with_arch_ROM_OK', audit_SL_items_with_arch_ROM_OK)
    change_control_dic(control_dic, 'audit_SL_items_with_arch_ROM_BAD', audit_SL_items_with_arch_ROM_BAD)
    change_control_dic(control_dic, 'audit_SL_items_without_arch_ROM', audit_SL_items_without_arch_ROM)
    change_control_dic(control_dic, 'audit_SL_items_with_CHD', audit_SL_items_with_CHD)
    change_control_dic(control_dic, 'audit_SL_items_with_CHD_OK', audit_SL_items_with_CHD_OK)
    change_control_dic(control_dic, 'audit_SL_items_with_CHD_BAD', audit_SL_items_with_CHD_BAD)
    change_control_dic(control_dic, 'audit_SL_items_without_CHD', audit_SL_items_without_CHD)

    # >> Update timestamp
    change_control_dic(control_dic, 't_SL_audit', time.time())

# -------------------------------------------------------------------------------------------------
# Fanart generation
# -------------------------------------------------------------------------------------------------
#
# Scales and centers img into a box of size (box_x_size, box_y_size).
# Scaling keeps original img aspect ratio.
# Returns an image of size (box_x_size, box_y_size)
#
def PIL_resize_proportional(img, layout, dic_key, CANVAS_COLOR = (0, 0, 0)):
    box_x_size = layout[dic_key]['width']
    box_y_size = layout[dic_key]['height']
    # print('PIL_resize_proportional() Initialising ...')
    # print('img X_size = {0} | Y_size = {1}'.format(img.size[0], img.size[1]))
    # print('box X_size = {0} | Y_size = {1}'.format(box_x_size, box_y_size))

    # --- First try to fit X dimension ---
    # print('PIL_resize_proportional() Fitting X dimension')
    wpercent = (box_x_size / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    r_x_size = box_x_size
    r_y_size = hsize
    x_offset = 0
    y_offset = (box_y_size - r_y_size) / 2
    # print('resize X_size = {0} | Y_size = {1}'.format(r_x_size, r_y_size))
    # print('resize x_offset = {0} | y_offset = {1}'.format(x_offset, y_offset))

    # --- Second try to fit Y dimension ---
    if y_offset < 0:
        # print('Fitting Y dimension')
        hpercent = (box_y_size / float(img.size[1]))
        wsize = int((float(img.size[0]) * float(hpercent)))
        r_x_size = wsize
        r_y_size = box_y_size
        x_offset = (box_x_size - r_x_size) / 2
        y_offset = 0
        # print('resize X_size = {0} | Y_size = {1}'.format(r_x_size, r_y_size))
        # print('resize x_offset = {0} | y_offset = {1}'.format(x_offset, y_offset))

    # >> Create a new image and paste original image centered.
    canvas_img = Image.new('RGB', (box_x_size, box_y_size), CANVAS_COLOR)
    # >> Resize and paste
    img = img.resize((r_x_size, r_y_size), Image.ANTIALIAS)
    canvas_img.paste(img, (x_offset, y_offset, x_offset + r_x_size, y_offset + r_y_size))

    return canvas_img

def PIL_paste_image(img, img_title, layout, dic_key):
    box = (
        layout[dic_key]['left'],
        layout[dic_key]['top'], 
        layout[dic_key]['left'] + layout[dic_key]['width'],
        layout[dic_key]['top']  + layout[dic_key]['height']
    )
    img.paste(img_title, box)

    return img

# --- Fanart layout ---
MAME_layout_example = {
    'Title'       : {'width' : 450, 'height' : 450, 'left' : 50,   'top' : 50},
    'Snap'        : {'width' : 450, 'height' : 450, 'left' : 50,   'top' : 550},
    'Flyer'       : {'width' : 450, 'height' : 450, 'left' : 1420, 'top' : 50},
    'Cabinet'     : {'width' : 300, 'height' : 425, 'left' : 1050, 'top' : 625},
    'Artpreview'  : {'width' : 450, 'height' : 550, 'left' : 550,  'top' : 500},
    'PCB'         : {'width' : 300, 'height' : 300, 'left' : 1500, 'top' : 525},
    'Clearlogo'   : {'width' : 450, 'height' : 200, 'left' : 1400, 'top' : 850},
    'CPanel'      : {'width' : 300, 'height' : 100, 'left' : 1050, 'top' : 500},
    'Marquee'     : {'width' : 800, 'height' : 275, 'left' : 550,  'top' : 200},
    'MachineName' : {'left' : 550, 'top' : 50, 'fontsize' : 72},
}

MAME_layout_assets = {
    'Title'       : 'title',
    'Snap'        : 'snap',
    'Flyer'       : 'flyer',
    'Cabinet'     : 'cabinet',
    'Artpreview'  : 'artpreview',
    'PCB'         : 'PCB',
    'Clearlogo'   : 'clearlogo',
    'CPanel'      : 'cpanel',
    'Marquee'     : 'marquee',
}

def mame_load_MAME_Fanart_template(Template_FN):
    # >> Load XML file
    layout = {}
    if not os.path.isfile(Template_FN.getPath()): return None
    log_debug('mame_load_MAME_Fanart_template() Loading XML "{0}"'.format(Template_FN.getPath()))
    try:
        xml_tree = ET.parse(Template_FN.getPath())
    except IOError as E:
        return None
    xml_root = xml_tree.getroot()

    # >> Parse file
    art_list = ['Title', 'Snap', 'Flyer', 'Cabinet', 'Artpreview', 'PCB', 'Clearlogo', 'CPanel', 'Marquee']
    art_tag_list = ['width', 'height', 'left', 'top']
    text_list = ['MachineName']
    test_tag_list = ['left', 'top', 'fontsize']
    for root_element in xml_root:
        # log_debug('Root child {0}'.format(root_element.tag))
        if root_element.tag in art_list:
            art_dic = d = {key : 0 for key in art_tag_list}
            for art_child in root_element:
                if art_child.tag in art_tag_list:
                    art_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = art_dic
        elif root_element.tag in text_list:
            text_dic = d = {key : 0 for key in test_tag_list}
            for art_child in root_element:
                if art_child.tag in test_tag_list:
                    text_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = text_dic
        else:
            log_error('Unknown tag <{0}>'.format(root_element.tag))
            return None

    return layout

#
# Rebuild Fanart for a given MAME machine
#
def mame_build_fanart(PATHS, layout, m_name, assets_dic, Fanart_FN, CANVAS_COLOR = (0, 0, 0)):
    global font_mono

    # >> Quickly check if machine has valid assets, and skip fanart generation if not.
    # log_debug('mame_build_fanart() Building fanart for machine {0}'.format(m_name))
    machine_has_valid_assets = False
    for asset_key, asset_db_name in MAME_layout_assets.iteritems():
        m_assets = assets_dic[m_name]
        if m_assets[asset_db_name]:
            machine_has_valid_assets = True
            break
    if not machine_has_valid_assets: return

    # >> If font object does not exists open font an cache it.
    if not font_mono:
        log_debug('mame_build_fanart() Creating font_mono object')
        log_debug('mame_build_fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), layout['MachineName']['fontsize'])

    # >> Create fanart canvas
    fanart_img = Image.new('RGB', (1920, 1080), (0, 0, 0))
    draw = ImageDraw.Draw(fanart_img)

    # >> Draw assets according to layout
    for asset_key in layout:
        # log_debug('{0:<10} initialising'.format(asset_key))
        m_assets = assets_dic[m_name]
        if asset_key == 'MachineName':
            t_left = layout['MachineName']['left']
            t_top = layout['MachineName']['top']
            draw.text((t_left, t_top), m_name, (255, 255, 255), font = font_mono)
        else:
            asset_db_name = MAME_layout_assets[asset_key]
            if not m_assets[asset_db_name]:
                # log_debug('{0:<10} DB empty'.format(asset_db_name))
                continue
            Asset_FN = FileName(m_assets[asset_db_name])
            if not Asset_FN.exists():
                # log_debug('{0:<10} file not found'.format(asset_db_name))
                continue
            # log_debug('{0:<10} found'.format(asset_db_name))
            img_asset = Image.open(Asset_FN.getPath())
            img_asset = PIL_resize_proportional(img_asset, layout, asset_key, CANVAS_COLOR)
            fanart_img = PIL_paste_image(fanart_img, img_asset, layout, asset_key)

    # >> Save fanart and update database
    # log_debug('mame_build_fanart() Saving Fanart "{0}"'.format(Fanart_FN.getPath()))
    fanart_img.save(Fanart_FN.getPath())
    assets_dic[m_name]['fanart'] = Fanart_FN.getPath()

SL_layout_example = {
    'Title'    : {'width' : 600, 'height' : 600, 'left' : 690,  'top' : 430},
    'Snap'     : {'width' : 600, 'height' : 600, 'left' : 1300, 'top' : 430},
    'BoxFront' : {'width' : 650, 'height' : 980, 'left' : 30,   'top' : 50},
    'SLName'   : {'left' : 730, 'top' : 90,  'fontsize' : 76},
    'ItemName' : {'left' : 730, 'top' : 180, 'fontsize' : 76},
}

SL_layout_assets = {
    'Title'    : 'title',
    'Snap'     : 'snap',
    'BoxFront' : 'boxfront',
}

def mame_load_SL_Fanart_template(Template_FN):
    # >> Load XML file
    layout = {}
    if not os.path.isfile(Template_FN.getPath()): return None
    log_debug('mame_load_SL_Fanart_template() Loading XML "{0}"'.format(Template_FN.getPath()))
    try:
        xml_tree = ET.parse(Template_FN.getPath())
    except IOError as E:
        return None
    xml_root = xml_tree.getroot()

    # >> Parse file
    art_list = ['Title', 'Snap', 'BoxFront']
    art_tag_list = ['width', 'height', 'left', 'top']
    text_list = ['SLName', 'ItemName']
    test_tag_list = ['left', 'top', 'fontsize']
    for root_element in xml_root:
        # log_debug('Root child {0}'.format(root_element.tag))
        if root_element.tag in art_list:
            art_dic = d = {key : 0 for key in art_tag_list}
            for art_child in root_element:
                if art_child.tag in art_tag_list:
                    art_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = art_dic
        elif root_element.tag in text_list:
            text_dic = d = {key : 0 for key in test_tag_list}
            for art_child in root_element:
                if art_child.tag in test_tag_list:
                    text_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = text_dic
        else:
            log_error('Unknown tag <{0}>'.format(root_element.tag))
            return None

    return layout

#
# Rebuild Fanart for a given SL item
#
def mame_build_SL_fanart(PATHS, layout_SL, SL_name, m_name, assets_dic, Fanart_FN, CANVAS_COLOR = (0, 0, 0)):
    global font_mono_SL
    global font_mono_item

    # >> Quickly check if machine has valid assets, and skip fanart generation if not.
    # log_debug('mame_build_SL_fanart() Building fanart for SL {0} item {1}'.format(SL_name, m_name))
    machine_has_valid_assets = False
    for asset_key, asset_db_name in SL_layout_assets.iteritems():
        m_assets = assets_dic[m_name]
        if m_assets[asset_db_name]:
            machine_has_valid_assets = True
            break
    if not machine_has_valid_assets: return

    # >> If font object does not exists open font an cache it.
    if not font_mono_SL:
        log_debug('mame_build_SL_fanart() Creating font_mono_SL object')
        log_debug('mame_build_SL_fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_SL = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), layout_SL['SLName']['fontsize'])
    if not font_mono_item:
        log_debug('mame_build_SL_fanart() Creating font_mono_item object')
        log_debug('mame_build_SL_fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_item = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), layout_SL['ItemName']['fontsize'])

    # >> Create fanart canvas
    fanart_img = Image.new('RGB', (1920, 1080), (0, 0, 0))
    draw = ImageDraw.Draw(fanart_img)

    # >> Draw assets according to layout_SL
    for asset_key in layout_SL:
        # log_debug('{0:<10} initialising'.format(asset_key))
        m_assets = assets_dic[m_name]
        if asset_key == 'SLName':
            t_left = layout_SL['SLName']['left']
            t_top = layout_SL['SLName']['top']
            draw.text((t_left, t_top), SL_name, (255, 255, 255), font = font_mono_SL)
        elif asset_key == 'ItemName':
            t_left = layout_SL['ItemName']['left']
            t_top = layout_SL['ItemName']['top']
            draw.text((t_left, t_top), m_name, (255, 255, 255), font = font_mono_item)
        else:
            asset_db_name = SL_layout_assets[asset_key]
            if not m_assets[asset_db_name]:
                # log_debug('{0:<10} DB empty'.format(asset_db_name))
                continue
            Asset_FN = FileName(m_assets[asset_db_name])
            if not Asset_FN.exists():
                # log_debug('{0:<10} file not found'.format(asset_db_name))
                continue
            # log_debug('{0:<10} found'.format(asset_db_name))
            img_asset = Image.open(Asset_FN.getPath())
            img_asset = PIL_resize_proportional(img_asset, layout_SL, asset_key, CANVAS_COLOR)
            fanart_img = PIL_paste_image(fanart_img, img_asset, layout_SL, asset_key)

    # >> Save fanart and update database
    # log_debug('mame_build_SL_fanart() Saving Fanart "{0}"'.format(Fanart_FN.getPath()))
    fanart_img.save(Fanart_FN.getPath())
    assets_dic[m_name]['fanart'] = Fanart_FN.getPath()

#
# 1) Scan MAME hash dir for XML files.
# 2) For each XML file, read the first XML_READ_LINES lines.
# 3) Search for the line <softwarelist name="32x" description="Sega 32X cartridges">
# 4) Create the file SL_NAMES_PATH with a dictionary sl_name : description
#
# <softwarelist name="32x" description="Sega 32X cartridges">
# <softwarelist name="vsmile_cart" description="VTech V.Smile cartridges">
# <softwarelist name="vsmileb_cart" description="VTech V.Smile Baby cartridges">
#
XML_READ_LINES = 600
def mame_build_SL_names(PATHS, settings):
    log_debug('mame_build_SL_names() Starting ...')

    # >> If MAME hash path is not configured then create and empty file
    SL_names_dic = {}
    hash_dir_FN = FileName(settings['SL_hash_path'])
    if not hash_dir_FN.exists():
        log_info('mame_build_SL_names() MAME hash path does not exists.')
        log_info('mame_build_SL_names() Creating empty SL_NAMES_PATH')
        fs_write_JSON_file(PATHS.SL_NAMES_PATH.getPath(), SL_names_dic)
        return

    # >> MAME hash path exists. Carry on.
    file_list = os.listdir(hash_dir_FN.getPath())
    log_debug('mame_build_SL_names() Found {0} files'.format(len(file_list)))
    xml_files = []
    for file in file_list:
        if file.endswith('.xml'): xml_files.append(file)
    log_debug('mame_build_SL_names() Found {0} XML files'.format(len(xml_files)))
    for f_name in xml_files:
        XML_FN = hash_dir_FN.pjoin(f_name)
        # log_debug('Inspecting file "{0}"'.format(XML_FN.getPath()))
        # >> Read first XML_READ_LINES lines
        try:
            f = open(XML_FN.getPath(), 'r')
        except IOError:
            log_error('(IOError) Exception opening {0}'.format(XML_FN.getPath()))
            continue
        else:
            # >> f.readlines(XML_READ_LINES) does not work well for some files
            # content_list = f.readlines(XML_READ_LINES)
            line_count = 0
            content_list = []
            for line in f:
                content_list.append(line)
                line_count += 1
                if line_count > XML_READ_LINES: break
            content_list = [x.strip() for x in content_list]
            content_list = [x.decode('utf-8') for x in content_list]
            for line in content_list:
                # >> DEBUG
                # if f_name == 'vsmileb_cart.xml': log_debug('Line "{0}"'.format(line))
                # >> Search for SL name
                if line.startswith('<softwarelist'):
                    m = re.search(r'<softwarelist name="([^"]+?)" description="([^"]+?)"', line)
                    if m:
                        sl_name = m.group(1)
                        sl_desc = m.group(2)
                        # log_debug('mame_build_SL_names() SL "{0}" -> "{1}"'.format(sl_name, sl_desc))
                        SL_names_dic[sl_name] = sl_desc
    # >> Save database
    log_debug('mame_build_SL_names() Extracted {0} Software List names'.format(len(SL_names_dic)))
    fs_write_JSON_file(PATHS.SL_NAMES_PATH.getPath(), SL_names_dic)

# -------------------------------------------------------------------------------------------------
# MAME database building
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# Reads and processes MAME.xml
#
# The ROM location in the non-merged set is unique and can be used as a unique dictionary key.
# Include only ROMs and not CHDs.
#
# roms_sha1_dic = {
#     rom_nonmerged_location_1 : sha1_hash,
#     rom_nonmerged_location_2 : sha1_hash,
#     ...
#
# }
#
# Saves:
#   MAIN_DB_PATH
#   RENDER_DB_PATH
#   ROMS_DB_PATH
#   MAIN_ASSETS_DB_PATH  (empty JSON file)
#   MAIN_PCLONE_DIC_PATH
#   MAIN_CONTROL_PATH    (updated and then JSON file saved)
#   ROM_SHA1_HASH_DB_PATH
#
STOP_AFTER_MACHINES = 100000
class DB_obj:
    def __init__(self, machines, machines_render, devices_db_dic,
                 machine_roms, main_pclone_dic, assets_dic):
        self.machines        = machines
        self.machines_render = machines_render
        self.devices_db_dic  = devices_db_dic
        self.machine_roms    = machine_roms
        self.main_pclone_dic = main_pclone_dic
        self.assets_dic      = assets_dic

def mame_build_MAME_main_database(PATHS, settings, control_dic):
    # --- Print user configuration for debug ---
    log_info('mame_build_MAME_main_database() Starting ...')
    log_info('--- Paths ---')
    log_info('mame_prog      = "{0}"'.format(settings['mame_prog']))
    log_info('rom_path       = "{0}"'.format(settings['rom_path']))
    log_info('assets_path    = "{0}"'.format(settings['assets_path']))
    log_info('chd_path       = "{0}"'.format(settings['chd_path']))
    log_info('samples_path   = "{0}"'.format(settings['samples_path']))
    log_info('SL_hash_path   = "{0}"'.format(settings['SL_hash_path']))    
    log_info('SL_rom_path    = "{0}"'.format(settings['SL_rom_path']))
    log_info('SL_chd_path    = "{0}"'.format(settings['SL_chd_path']))
    log_info('--- INI paths ---')   
    log_info('catver_path    = "{0}"'.format(settings['catver_path']))
    log_info('catlist_path   = "{0}"'.format(settings['catlist_path']))
    log_info('genre_path     = "{0}"'.format(settings['genre_path']))
    log_info('nplayers_path  = "{0}"'.format(settings['nplayers_path']))
    log_info('bestgames_path = "{0}"'.format(settings['bestgames_path']))
    log_info('series_path    = "{0}"'.format(settings['series_path']))
    log_info('mature_path    = "{0}"'.format(settings['mature_path']))
    log_info('--- DAT paths ---')
    log_info('history_path   = "{0}"'.format(settings['history_path']))
    log_info('mameinfo_path  = "{0}"'.format(settings['mameinfo_path']))
    log_info('gameinit_path  = "{0}"'.format(settings['gameinit_path']))
    log_info('command_path   = "{0}"'.format(settings['command_path']))

    # --- Progress dialog ---
    pDialog_canceled = False
    pDialog = xbmcgui.DialogProgress()

    # --- Build SL_NAMES_PATH if available, to be used later in the catalog building ---
    pDialog.create('Advanced MAME Launcher', 'Creating list of Software List names ...')
    pDialog.update(0)
    mame_build_SL_names(PATHS, settings)
    pDialog.update(100)
    pDialog.close()

    # --- Load INI files to include category information ---
    pdialog_line1 = 'Processing INI files ...'
    num_items = 7
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(int((0*100) / num_items), pdialog_line1, 'catver.ini')
    (categories_dic, catver_version) = mame_load_Catver_ini(settings['catver_path'])
    pDialog.update(int((1*100) / num_items), pdialog_line1, 'catlist.ini')
    (catlist_dic, catlist_version) = mame_load_INI_datfile(settings['catlist_path'])
    pDialog.update(int((2*100) / num_items), pdialog_line1, 'genre.ini')
    (genre_dic, genre_version) = mame_load_INI_datfile(settings['genre_path'])
    pDialog.update(int((3*100) / num_items), pdialog_line1, 'nplayers.ini')
    (nplayers_dic, nplayers_version) = mame_load_nplayers_ini(settings['nplayers_path'])
    pDialog.update(int((4*100) / num_items), pdialog_line1, 'bestgames.ini')
    (bestgames_dic, bestgames_version) = mame_load_INI_datfile(settings['bestgames_path'])
    pDialog.update(int((5*100) / num_items), pdialog_line1, 'series.ini')
    (series_dic, series_version) = mame_load_INI_datfile(settings['series_path'])
    pDialog.update(int((6*100) / num_items), pdialog_line1, 'mature.ini')
    (mature_set, mature_version) = mame_load_Mature_ini(settings['mature_path'])
    pDialog.update(int((7*100) / num_items), ' ', ' ')
    pDialog.close()

    # --- Load DAT files to include category information ---
    pdialog_line1 = 'Processing DAT files ...'
    num_items = 4
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(int((0*100) / num_items), pdialog_line1, 'history.dat')
    (history_idx_dic, history_dic, history_version) = mame_load_History_DAT(settings['history_path'])
    pDialog.update(int((1*100) / num_items), pdialog_line1, 'mameinfo.dat')
    (mameinfo_idx_dic, mameinfo_dic, mameinfo_version) = mame_load_MameInfo_DAT(settings['mameinfo_path'])
    pDialog.update(int((2*100) / num_items), pdialog_line1, 'gameinit.dat')
    (gameinit_idx_dic, gameinit_dic, gameinit_version) = mame_load_GameInit_DAT(settings['gameinit_path'])
    pDialog.update(int((3*100) / num_items), pdialog_line1, 'command.dat')
    (command_idx_dic, command_dic, command_version) = mame_load_Command_DAT(settings['command_path'])
    pDialog.update(int((4*100) / num_items), ' ', ' ')
    pDialog.close()

    # ---------------------------------------------------------------------------------------------
    # Incremental Parsing approach B (from [1])
    # ---------------------------------------------------------------------------------------------
    # Do not load whole MAME XML into memory! Use an iterative parser to
    # grab only the information we want and discard the rest.
    # See http://effbot.org/zone/element-iterparse.htm [1]
    #
    pDialog.create('Advanced MAME Launcher')
    pDialog.update(0, 'Building main MAME database ...')
    log_info('mame_build_MAME_main_database() Loading "{0}"'.format(PATHS.MAME_XML_PATH.getPath()))
    context = ET.iterparse(PATHS.MAME_XML_PATH.getPath(), events=("start", "end"))
    context = iter(context)
    event, root = context.next()
    mame_version_raw = root.attrib['build']
    mame_version_int = mame_get_numerical_version(mame_version_raw)
    log_info('mame_build_MAME_main_database() MAME str version "{0}"'.format(mame_version_raw))
    log_info('mame_build_MAME_main_database() MAME numerical version {0}'.format(mame_version_int))

    # --- Process MAME XML ---
    total_machines = control_dic['stats_total_machines']
    log_info('mame_build_MAME_main_database() total_machines {0}'.format(total_machines))
    machines = {}
    machines_render = {}
    machines_roms = {}
    machines_devices = {}
    roms_sha1_dic = {}
    stats_processed_machines = 0
    stats_parents            = 0
    stats_clones             = 0
    stats_devices            = 0
    stats_devices_parents    = 0
    stats_devices_clones     = 0
    stats_runnable           = 0
    stats_runnable_parents   = 0
    stats_runnable_clones    = 0
    stats_samples            = 0
    stats_samples_parents    = 0
    stats_samples_clones     = 0
    stats_BIOS               = 0
    stats_BIOS_parents       = 0
    stats_BIOS_clones        = 0
    stats_coin               = 0
    stats_coin_parents       = 0
    stats_coin_clones        = 0
    stats_nocoin             = 0
    stats_nocoin_parents     = 0
    stats_nocoin_clones      = 0
    stats_mechanical         = 0
    stats_mechanical_parents = 0
    stats_mechanical_clones  = 0
    stats_dead               = 0
    stats_dead_parents       = 0
    stats_dead_clones        = 0

    log_info('mame_build_MAME_main_database() Parsing MAME XML file ...')
    num_iteration = 0
    for event, elem in context:
        # --- Debug the elements we are iterating from the XML file ---
        # print('Event     {0:6s} | Elem.tag    "{1}"'.format(event, elem.tag))
        # print('                   Elem.text   "{0}"'.format(elem.text))
        # print('                   Elem.attrib "{0}"'.format(elem.attrib))

        # <machine> tag start event includes <machine> attributes
        if event == 'start' and elem.tag == 'machine':
            machine  = fs_new_machine_dic()
            m_render = fs_new_machine_render_dic()
            m_roms   = fs_new_roms_object()
            device_list = []
            runnable = False
            num_displays = 0

            # --- Process <machine> attributes ----------------------------------------------------
            # name is #REQUIRED attribute
            if 'name' not in elem.attrib:
                log_error('name attribute not found in <machine> tag.')
                raise CriticalError('name attribute not found in <machine> tag')
            else:
                m_name = elem.attrib['name']

            # sourcefile #IMPLIED attribute
            if 'sourcefile' not in elem.attrib:
                log_error('sourcefile attribute not found in <machine> tag.')
                raise CriticalError('sourcefile attribute not found in <machine> tag.')
            else:
                # >> Remove trailing '.cpp' from driver name
                raw_driver_name = elem.attrib['sourcefile']

                # >> In MAME 0.174 some driver end with .cpp and others with .hxx
                # if raw_driver_name[-4:] == '.cpp':
                #     driver_name = raw_driver_name[0:-4]
                # else:
                #     print('Unrecognised driver name "{0}"'.format(raw_driver_name))

                # >> Assign driver name
                machine['sourcefile'] = raw_driver_name

            # Optional, default no
            if 'isbios' not in elem.attrib:
                m_render['isBIOS'] = False
            else:
                m_render['isBIOS'] = True if elem.attrib['isbios'] == 'yes' else False
            if 'isdevice' not in elem.attrib:
                m_render['isDevice'] = False
            else:
                m_render['isDevice'] = True if elem.attrib['isdevice'] == 'yes' else False
            if 'ismechanical' not in elem.attrib:
                machine['isMechanical'] = False
            else:
                machine['isMechanical'] = True if elem.attrib['ismechanical'] == 'yes' else False
            # Optional, default yes
            if 'runnable' not in elem.attrib:
                runnable = True
            else:
                runnable = False if elem.attrib['runnable'] == 'no' else True

            # cloneof is #IMPLIED attribute
            if 'cloneof' in elem.attrib: m_render['cloneof'] = elem.attrib['cloneof']

            # romof is #IMPLIED attribute
            if 'romof' in elem.attrib: machine['romof'] = elem.attrib['romof']

            # sampleof is #IMPLIED attribute
            if 'sampleof' in elem.attrib: machine['sampleof'] = elem.attrib['sampleof']

            # >> Add catver/catlist/genre
            if m_name in categories_dic: machine['catver']    = categories_dic[m_name]
            else:                        machine['catver']    = '[ Not set ]'
            if m_name in catlist_dic:    machine['catlist']   = catlist_dic[m_name]
            else:                        machine['catlist']   = '[ Not set ]'
            if m_name in genre_dic:      machine['genre']     = genre_dic[m_name]
            else:                        machine['genre']     = '[ Not set ]'
            if m_name in bestgames_dic:  machine['bestgames'] = bestgames_dic[m_name]
            else:                        machine['bestgames'] = '[ Not set ]'
            if m_name in series_dic:     machine['series']    = series_dic[m_name]
            else:                        machine['series']    = '[ Not set ]'
            if m_name in nplayers_dic:   m_render['nplayers'] = nplayers_dic[m_name]
            else:                        m_render['nplayers'] = '[ Not set ]'

            # >> Increment number of machines
            stats_processed_machines += 1

        elif event == 'start' and elem.tag == 'description':
            m_render['description'] = unicode(elem.text)

        elif event == 'start' and elem.tag == 'year':
            m_render['year'] = unicode(elem.text)

        elif event == 'start' and elem.tag == 'manufacturer':
            m_render['manufacturer'] = unicode(elem.text)

        # >> Check in machine has BIOS
        # <biosset> name and description attributes are mandatory
        elif event == 'start' and elem.tag == 'biosset':
            # --- Add BIOS to ROMS_DB_PATH ---
            bios = fs_new_bios_dic()
            bios['name'] = unicode(elem.attrib['name'])
            bios['description'] = unicode(elem.attrib['description'])
            m_roms['bios'].append(bios)

        # >> Check in machine has ROMs
        # A) ROM is considered to be valid if SHA1 has exists. 
        #    Are there ROMs with no sha1? There are a lot, for example 
        #    machine 1941j <rom name="yi22b.1a" size="279" status="nodump" region="bboardplds" />
        #
        # B) A ROM is unique to that machine if the <rom> tag does not have the 'merge' attribute.
        #    For example, snes and snespal both have <rom> tags that point to exactly the same
        #    BIOS. However, in a split set only snes.zip ROM set exists.
        #    snes    -> <rom name="spc700.rom" size="64" crc="44bb3a40" ... >
        #    snespal -> <rom name="spc700.rom" merge="spc700.rom" size="64" crc="44bb3a40" ... >
        #
        # C) In AML, hasROM actually means "machine has it own ROMs not found somewhere else".
        #
        elif event == 'start' and elem.tag == 'rom':
            # --- Research ---
            # if not 'sha1' in elem.attrib:
            #     raise GeneralError('ROM with no sha1 (machine {0})'.format(machine_name))

            # --- Add BIOS to ROMS_DB_PATH ---
            rom = fs_new_rom_dic()
            rom['name']  = unicode(elem.attrib['name'])
            rom['merge'] = unicode(elem.attrib['merge']) if 'merge' in elem.attrib else ''
            rom['bios']  = unicode(elem.attrib['bios']) if 'bios' in elem.attrib else ''
            rom['size']  = int(elem.attrib['size']) if 'size' in elem.attrib else 0
            rom['crc']   = unicode(elem.attrib['crc']) if 'crc' in elem.attrib else ''
            m_roms['roms'].append(rom)

            # --- ROMs SHA1 database ---
            sha1 = unicode(elem.attrib['sha1']) if 'sha1' in elem.attrib else ''
            # >> Only add valid ROMs, ignore invalid.
            if sha1:
                rom_nonmerged_location = m_name + '/' + rom['name']
                roms_sha1_dic[rom_nonmerged_location] = sha1

        # >> Check in machine has CHDs
        # A) CHD is considered valid if and only if SHA1 hash exists.
        #    Keep in mind that there can be multiple disks per machine, some valid, some invalid.
        #    Just one valid CHD is OK.
        # B) A CHD is unique to a machine if the <disk> tag does not have the 'merge' attribute.
        #    See comments for ROMs avobe.
        #
        elif event == 'start' and elem.tag == 'disk':
            # <!ATTLIST disk name CDATA #REQUIRED>
            # if 'sha1' in elem.attrib and 'merge' in elem.attrib:     machine['CHDs_merged'].append(elem.attrib['name'])
            # if 'sha1' in elem.attrib and 'merge' not in elem.attrib: machine['CHDs'].append(elem.attrib['name'])

            # --- Add BIOS to ROMS_DB_PATH ---
            disk = fs_new_disk_dic()
            disk['name']  = unicode(elem.attrib['name'])
            disk['merge'] = unicode(elem.attrib['merge']) if 'merge' in elem.attrib else ''
            disk['sha1']  = unicode(elem.attrib['sha1']) if 'sha1' in elem.attrib else ''
            m_roms['disks'].append(disk)

        # >> Machine devices
        elif event == 'start' and elem.tag == 'device_ref':
            device_list.append(unicode(elem.attrib['name']))

        # >> Machine samples
        elif event == 'start' and elem.tag == 'sample':
            sample = { 'name' : unicode(elem.attrib['name']) }
            m_roms['samples'].append(sample)

        # Some machines have more than one display tag (for example aquastge has 2).
        # Other machines have no display tag (18w)
        elif event == 'start' and elem.tag == 'display':
            rotate_str = elem.attrib['rotate'] if 'rotate' in elem.attrib else '0'
            # machine['display_tag'].append(elem.attrib['tag'])
            machine['display_type'].append(elem.attrib['type'])
            machine['display_rotate'].append(rotate_str)
            num_displays += 1

        # Some machines have no controls at all.
        # 1) <control> reqbuttons attribute, pang uses it (has 2 buttons but only 1 is required
        # 2) <control> reqbuttons ways2, bcclimbr uses it. Sometimes ways attribute is a string!
        #
        # machine['input'] = {
        #     'att_players' CDATA #REQUIRED
        #     'att_coins'   CDATA #IMPLIED
        #     'att_service' (yes|no) "no"
        #     'att_tilt'    (yes|no) "no"
        #     'control_list' : [
        #         {
        #         'type'       : string, CDATA #REQUIRED
        #         'player'     : int, CDATA #IMPLIED
        #         'buttons'    : int, CDATA #IMPLIED
        #         'ways'       : [ ways string, ways2 string, ways3 string ] CDATA #IMPLIED
        #         }, ...
        #     ]
        # }
        elif event == 'start' and elem.tag == 'input':
            # --- Keep this as is it now for compatibility ---
            if 'coins' in elem.attrib:
                machine['coins'] = int(elem.attrib['coins'])

            # --- Keep this as it is now for compatibility ---
            # >> Iterate children of <input> and search for <control> tags
            for control_child in elem:
                if control_child.tag == 'control':
                    machine['control_type'].append(control_child.attrib['type'])

            # --- New 'input' field in 0.9.6 ---
            # --- <input> attributes ---
            att_players = int(elem.attrib['players']) if 'players' in elem.attrib else 0
            att_coins = int(elem.attrib['coins']) if 'coins' in elem.attrib else 0
            if 'service' in elem.attrib: att_service = True if elem.attrib['service'] == 'yes' else False
            else:                        att_service = False
            if 'tilt' in elem.attrib: att_tilt = True if elem.attrib['tilt'] == 'yes' else False
            else:                     att_tilt = False

            # --- <input> child tags ---
            control_list = []
            for control_child in elem:
                attrib = control_child.attrib
                # >> Skip non <control> tags
                if control_child.tag != 'control': continue
                # >> Process <control> tags
                t_ctrl_dic = {}
                if 'type' in attrib:
                    t_ctrl_dic['type'] = attrib['type']
                else:
                    t_ctrl_dic['type'] = ''
                    raise TypeError('<input> -> <control> has not type attribute')
                t_ctrl_dic['player'] = int(attrib['player']) if 'player' in attrib else -1
                t_ctrl_dic['buttons'] = int(attrib['buttons']) if 'buttons' in attrib else -1
                ways_list = []
                if 'ways'  in attrib: ways_list.append(attrib['ways'])
                if 'ways2' in attrib: ways_list.append(attrib['ways2'])
                if 'ways3' in attrib: ways_list.append(attrib['ways3'])
                t_ctrl_dic['ways'] = ways_list
                control_list.append(t_ctrl_dic)
            # >> Fix player field when implied
            if att_players == 1:
                for control in control_list:
                    control['player'] = 1
            input_dic = {
                'att_players'  : att_players,
                'att_coins'    : att_coins,
                'att_service'  : att_service,
                'att_tilt'     : att_tilt,
                'control_list' : control_list,
            }
            machine['input'] = input_dic

        elif event == 'start' and elem.tag == 'driver':
            # status is #REQUIRED attribute
            m_render['driver_status'] = unicode(elem.attrib['status'])

        elif event == 'start' and elem.tag == 'softwarelist':
            # name is #REQUIRED attribute
            machine['softwarelists'].append(elem.attrib['name'])

        # >> Device tag for machines that support loading external files
        elif event == 'start' and elem.tag == 'device':
            att_type      = elem.attrib['type'] # The only mandatory attribute
            att_tag       = elem.attrib['tag']       if 'tag'       in elem.attrib else ''
            att_mandatory = elem.attrib['mandatory'] if 'mandatory' in elem.attrib else ''
            att_interface = elem.attrib['interface'] if 'interface' in elem.attrib else ''
            # >> Transform device_mandatory into bool
            if att_mandatory and att_mandatory == '1': att_mandatory = True
            else:                                      att_mandatory = False

            # >> Iterate children of <device> and search for <instance> tags
            instance_tag_found = False
            inst_name = ''
            inst_briefname = ''
            ext_names = []
            for device_child in elem:
                if device_child.tag == 'instance':
                    # >> Stop if <device> tag has more than one <instance> tag. In MAME 0.190 no
                    # >> machines trigger this.
                    if instance_tag_found:
                        raise GeneralError('Machine {0} has more than one <instance> inside <device>')
                    inst_name      = device_child.attrib['name']
                    inst_briefname = device_child.attrib['briefname']
                    instance_tag_found = True
                elif device_child.tag == 'extension':
                    ext_names.append(device_child.attrib['name'])

            # >> NOTE Some machines have no instance inside <device>, for example 2020bb
            # >>      I don't know how to launch those machines
            # if not instance_tag_found:
                # log_warning('<instance> tag not found inside <device> tag (machine {0})'.format(m_name))
                # device_type = '{0} (NI)'.format(device_type)

            # >> Add device to database
            device_dic = {'att_type'      : att_type,      'att_tag'        : att_tag,
                          'att_mandatory' : att_mandatory, 'att_interface'  : att_interface,
                          'instance'      : { 'name' : inst_name, 'briefname' : inst_briefname},
                          'ext_names'     : ext_names}
            machine['devices'].append(device_dic)

        # --- <machine> tag closing. Add new machine to database ---
        elif event == 'end' and elem.tag == 'machine':
            # >> Assumption 1: isdevice = True if and only if runnable = False
            if m_render['isDevice'] == runnable:
                print("Machine {0}: machine['isDevice'] == runnable".format(m_name))
                raise GeneralError

            # >> Are there machines with more than 1 <display> tag. Answer: YES
            # if num_displays > 1:
            #     print("Machine {0}: num_displays = {1}".format(m_name, num_displays))
            #     raise GeneralError

            # >> All machines with 0 displays are mechanical? NO, 24cdjuke has no screen and is not mechanical. However
            # >> 24cdjuke is a preliminary driver.
            # if num_displays == 0 and not machine['ismechanical']:
            #     print("Machine {0}: num_displays == 0 and not machine['ismechanical']".format(m_name))
            #     raise GeneralError

            # >> Mark dead machines. A machine is dead if Status is preliminary AND have no controls
            if m_render['driver_status'] == 'preliminary' and not machine['control_type']:
                machine['isDead'] = True

            # >> Delete XML element once it has been processed
            elem.clear()

            # --- Compute statistics ---
            if m_render['cloneof']: stats_clones += 1
            else:                   stats_parents += 1
            if m_render['isDevice']:
                stats_devices += 1
                if m_render['cloneof']: stats_devices_clones += 1
                else:                   stats_devices_parents += 1
            if runnable:
                stats_runnable += 1
                if m_render['cloneof']: stats_runnable_clones += 1
                else:                   stats_runnable_parents += 1
            if machine['sampleof']:
                stats_samples += 1
                if m_render['cloneof']: stats_samples_clones += 1
                else:                   stats_samples_parents += 1
            if m_render['isBIOS']:
                stats_BIOS += 1
                if m_render['cloneof']: stats_BIOS_clones += 1
                else:                   stats_BIOS_parents += 1
            if runnable:
                if machine['coins'] > 0:
                    stats_coin += 1
                    if m_render['cloneof']: stats_coin_clones += 1
                    else:                   stats_coin_parents += 1
                else:
                    stats_nocoin += 1
                    if m_render['cloneof']: stats_nocoin_clones += 1
                    else:                   stats_nocoin_parents += 1
                if machine['isMechanical']:
                    stats_mechanical += 1
                    if m_render['cloneof']: stats_mechanical_clones += 1
                    else:                   stats_mechanical_parents += 1
                if machine['isDead']:
                    stats_dead += 1
                    if m_render['cloneof']: stats_dead_clones += 1
                    else:                   stats_dead_parents += 1

            # >> Add new machine
            machines[m_name] = machine
            machines_render[m_name] = m_render
            machines_roms[m_name] = m_roms
            machines_devices[m_name] = device_list

        # --- Print something to prove we are doing stuff ---
        num_iteration += 1
        if num_iteration % 1000 == 0:
            pDialog.update((stats_processed_machines * 100) // total_machines)
            # log_debug('Processed {0:10d} events ({1:6d} machines so far) ...'.format(num_iteration, stats_processed_machines))
            # log_debug('stats_processed_machines   = {0}'.format(stats_processed_machines))
            # log_debug('total_machines = {0}'.format(total_machines))
            # log_debug('Update number  = {0}'.format(update_number))

        # --- Stop after STOP_AFTER_MACHINES machines have been processed for debug ---
        if stats_processed_machines >= STOP_AFTER_MACHINES: break
    pDialog.update(100)
    pDialog.close()
    log_info('Processed {0} MAME XML events'.format(num_iteration))
    log_info('Processed machines {0}'.format(stats_processed_machines))
    log_info('Parents            {0}'.format(stats_parents))
    log_info('Clones             {0}'.format(stats_clones))
    log_info('Dead machines      {0}'.format(stats_dead))
    log_info('Dead parents       {0}'.format(stats_dead_parents))
    log_info('Dead clones        {0}'.format(stats_dead_clones))

    # ---------------------------------------------------------------------------------------------
    # Main parent-clone list
    # ---------------------------------------------------------------------------------------------
    # Create a couple of data struct for quickly know the parent of a clone game and
    # all clones of a parent.
    # main_pclone_dic          = { 'parent_name' : ['clone_name', 'clone_name', ... ] , ... }
    # main_clone_to_parent_dic = { 'clone_name' : 'parent_name', ... }
    log_info('Making PClone list...')
    main_pclone_dic = {}
    main_clone_to_parent_dic = {}
    for machine_name, m_render in machines_render.iteritems():
        if m_render['cloneof']:
            # >> Machine is a clone
            parent_name = m_render['cloneof']
            # >> If parent already in main_pclone_dic then add clone to parent list.
            # >> If parent not there, then add parent first and then add clone.
            if parent_name not in main_pclone_dic: main_pclone_dic[parent_name] = []
            main_pclone_dic[parent_name].append(machine_name)
            # >> Add clone machine to main_clone_to_parent_dic
            main_clone_to_parent_dic[machine_name] = parent_name            
        else:
            # >> Machine is a parent. Add to main_pclone_dic if not already there.
            if machine_name not in main_pclone_dic: main_pclone_dic[machine_name] = []

    # ---------------------------------------------------------------------------------------------
    # Make empty asset list
    # ---------------------------------------------------------------------------------------------
    assets_dic = {key : fs_new_MAME_asset() for key in machines}
    for m_name, asset in assets_dic.iteritems():
        asset['flags'] = fs_initial_flags(machines[m_name], machines_render[m_name], machines_roms[m_name])

    # ---------------------------------------------------------------------------------------------
    # Improve information fields in Main Render database
    # ---------------------------------------------------------------------------------------------
    if mature_set:
        for machine_name in machines_render:
            machines_render[machine_name]['isMature'] = True if machine_name in mature_set else False

    # >> Add genre infolabel into render database
    if genre_dic:
        for machine_name in machines_render:
            machines_render[machine_name]['genre'] = machines[machine_name]['genre']
    elif categories_dic:
        for machine_name in machines_render:
            machines_render[machine_name]['genre'] = machines[machine_name]['catver']
    elif catlist_dic:
        for machine_name in machines_render:
            machines_render[machine_name]['genre'] = machines[machine_name]['catlist']

    # ---------------------------------------------------------------------------------------------
    # Improve name in DAT indices and machine names
    # ---------------------------------------------------------------------------------------------
    # >> History DAT categories are Software List names.
    if history_idx_dic:
        log_debug('Updating History DAT cateogories and machine names ...')
        # >> Open Software List index if it exists.
        SL_main_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
        # >> Update category names.
        for cat_name in history_idx_dic:
            if cat_name == 'mame':
                history_idx_dic[cat_name]['name'] = 'MAME'
                # >> Improve MAME machine names
                for machine_list in history_idx_dic[cat_name]['machines']:
                    if machine_list[0] in machines_render:
                        machine_list[1] = machines_render[machine_list[0]]['description']
            elif cat_name in SL_main_catalog_dic:
                history_idx_dic[cat_name]['name'] = SL_main_catalog_dic[cat_name]['display_name']
                # >> Improve SL machine names
                

    # >> MameInfo DAT machine names.
    if mameinfo_idx_dic:
        log_debug('Updating Mameinfo DAT machine names ...')
        for cat_name in mameinfo_idx_dic:
            for machine_list in mameinfo_idx_dic[cat_name]:
                if machine_list[0] in machines_render:
                    machine_list[1] = machines_render[machine_list[0]]['description']

    # >> GameInit DAT machine names.
    if gameinit_idx_dic:
        log_debug('Updating GameInit DAT machine names ...')
        for machine_list in gameinit_idx_dic:
            if machine_list[0] in machines_render:
                machine_list[1] = machines_render[machine_list[0]]['description']

    # >> Command DAT machine names.
    if command_idx_dic:
        log_debug('Updating Command DAT machine names ...')
        for machine_list in command_idx_dic:
            if machine_list[0] in machines_render:
                machine_list[1] = machines_render[machine_list[0]]['description']

    # ---------------------------------------------------------------------------------------------
    # Build main distributed hashed database
    # ---------------------------------------------------------------------------------------------
    # >> This saves the hashs files in the database directory.
    fs_build_main_hashed_db(PATHS, machines, machines_render, pDialog)
    fs_build_asset_hashed_db(PATHS, assets_dic, pDialog)

    # ---------------------------------------------------------------------------------------------
    # Update MAME control dictionary
    # ---------------------------------------------------------------------------------------------
    # >> Versions
    change_control_dic(control_dic, 'ver_mame', mame_version_int)
    change_control_dic(control_dic, 'ver_mame_str', mame_version_raw)
    change_control_dic(control_dic, 'ver_bestgames', bestgames_version)
    change_control_dic(control_dic, 'ver_catlist', catlist_version)
    change_control_dic(control_dic, 'ver_catver', catver_version)
    change_control_dic(control_dic, 'ver_command', command_version)
    change_control_dic(control_dic, 'ver_gameinit', gameinit_version)
    change_control_dic(control_dic, 'ver_genre', genre_version)
    change_control_dic(control_dic, 'ver_history', history_version)
    change_control_dic(control_dic, 'ver_mameinfo', mameinfo_version)
    change_control_dic(control_dic, 'ver_mature', mature_version)
    change_control_dic(control_dic, 'ver_nplayers', nplayers_version)
    change_control_dic(control_dic, 'ver_series', series_version)

    # >> Statistics
    change_control_dic(control_dic, 'stats_processed_machines', stats_processed_machines)
    change_control_dic(control_dic, 'stats_parents', stats_parents)
    change_control_dic(control_dic, 'stats_clones', stats_clones)
    change_control_dic(control_dic, 'stats_runnable', stats_runnable)
    change_control_dic(control_dic, 'stats_runnable_parents', stats_runnable_parents)
    change_control_dic(control_dic, 'stats_runnable_clones', stats_runnable_clones)

    # >> Main filters
    change_control_dic(control_dic, 'stats_coin', stats_coin)
    change_control_dic(control_dic, 'stats_coin_parents', stats_coin_parents)
    change_control_dic(control_dic, 'stats_coin_clones', stats_coin_clones)
    change_control_dic(control_dic, 'stats_nocoin', stats_nocoin)
    change_control_dic(control_dic, 'stats_nocoin_parents', stats_nocoin_parents)
    change_control_dic(control_dic, 'stats_nocoin_clones', stats_nocoin_clones)
    change_control_dic(control_dic, 'stats_mechanical', stats_mechanical)
    change_control_dic(control_dic, 'stats_mechanical_parents', stats_mechanical_parents)
    change_control_dic(control_dic, 'stats_mechanical_clones', stats_mechanical_clones)
    change_control_dic(control_dic, 'stats_dead', stats_dead)
    change_control_dic(control_dic, 'stats_dead_parents', stats_dead_parents)
    change_control_dic(control_dic, 'stats_dead_clones', stats_dead_clones)
    change_control_dic(control_dic, 'stats_devices', stats_devices)
    change_control_dic(control_dic, 'stats_devices_parents', stats_devices_parents)
    change_control_dic(control_dic, 'stats_devices_clones', stats_devices_clones)

    # >> Binary filters
    change_control_dic(control_dic, 'stats_BIOS', stats_BIOS)
    change_control_dic(control_dic, 'stats_BIOS_parents', stats_BIOS_parents)
    change_control_dic(control_dic, 'stats_BIOS_clones', stats_BIOS_clones)
    change_control_dic(control_dic, 'stats_samples', stats_samples)
    change_control_dic(control_dic, 'stats_samples_parents', stats_samples_parents)
    change_control_dic(control_dic, 'stats_samples_clones', stats_samples_clones)

    # >> Timestamp
    change_control_dic(control_dic, 't_MAME_DB_build', time.time())

    # -----------------------------------------------------------------------------
    # Write JSON databases
    # -----------------------------------------------------------------------------
    log_info('Saving database JSON files ...')
    if OPTION_LOWMEM_WRITE_JSON:
        json_write_func = fs_write_JSON_file_lowmem
        log_debug('Using fs_write_JSON_file_lowmem() JSON writer')
    else:
        json_write_func = fs_write_JSON_file
        log_debug('Using fs_write_JSON_file() JSON writer')
    pdialog_line1 = 'Saving databases ...'
    num_items = 15

    # --- Databases ---
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machines Main')
    json_write_func(PATHS.MAIN_DB_PATH.getPath(), machines)
    pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Render')
    json_write_func(PATHS.RENDER_DB_PATH.getPath(), machines_render)
    pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machine ROMs')
    json_write_func(PATHS.ROMS_DB_PATH.getPath(), machines_roms)
    pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME machine Devices')
    json_write_func(PATHS.DEVICES_DB_PATH.getPath(), machines_devices)
    pDialog.update(int((4*100) / num_items), pdialog_line1, 'MAME machine Assets')
    json_write_func(PATHS.MAIN_ASSETS_DB_PATH.getPath(), assets_dic)
    pDialog.update(int((5*100) / num_items), pdialog_line1, 'MAME PClone dictionary')
    json_write_func(PATHS.MAIN_PCLONE_DIC_PATH.getPath(), main_pclone_dic)
    pDialog.update(int((6*100) / num_items), pdialog_line1, 'MAME ROMs SHA1 dictionary')
    json_write_func(PATHS.ROM_SHA1_HASH_DB_PATH.getPath(), roms_sha1_dic)
    # --- DAT files ---
    pDialog.update(int((7*100) / num_items), pdialog_line1, 'History DAT index')
    json_write_func(PATHS.HISTORY_IDX_PATH.getPath(), history_idx_dic)
    pDialog.update(int((8*100) / num_items), pdialog_line1, 'History DAT database')
    json_write_func(PATHS.HISTORY_DB_PATH.getPath(), history_dic)
    pDialog.update(int((9*100) / num_items), pdialog_line1, 'MAMEInfo DAT index')
    json_write_func(PATHS.MAMEINFO_IDX_PATH.getPath(), mameinfo_idx_dic)
    pDialog.update(int((10*100) / num_items), pdialog_line1, 'MAMEInfo DAT database')
    json_write_func(PATHS.MAMEINFO_DB_PATH.getPath(), mameinfo_dic)
    pDialog.update(int((11*100) / num_items), pdialog_line1, 'Gameinit DAT index')
    json_write_func(PATHS.GAMEINIT_IDX_PATH.getPath(), gameinit_idx_dic)
    pDialog.update(int((12*100) / num_items), pdialog_line1, 'Gameinit DAT database')
    json_write_func(PATHS.GAMEINIT_DB_PATH.getPath(), gameinit_dic)
    pDialog.update(int((13*100) / num_items), pdialog_line1, 'Command DAT index')
    json_write_func(PATHS.COMMAND_IDX_PATH.getPath(), command_idx_dic)
    pDialog.update(int((14*100) / num_items), pdialog_line1, 'Command DAT database')
    json_write_func(PATHS.COMMAND_DB_PATH.getPath(), command_dic)
    pDialog.update(int((15*100) / num_items), ' ', ' ')
    pDialog.close()

    # Return an object with reference to the objects just in case they are needed after
    # this function (in "Build everything", for example. This saves time (databases do not
    # need to be reloaded) and apparently memory as well.
    DB = DB_obj(machines, machines_render, machines_devices,
                machines_roms, main_pclone_dic, assets_dic)

    return DB

# -------------------------------------------------------------------------------------------------
# Generates the ROM audit database. This database contains invalid ROMs also to display information
# in "View / Audit", "View MAME machine ROMs" context menu. This database also includes
# device ROMs (<device_ref> ROMs).
#
def _get_ROM_type(rom):
    if       rom['bios'] and     rom['merge']: r_type = ROM_TYPE_BROM
    elif     rom['bios'] and not rom['merge']: r_type = ROM_TYPE_XROM
    elif not rom['bios'] and     rom['merge']: r_type = ROM_TYPE_MROM
    elif not rom['bios'] and not rom['merge']: r_type = ROM_TYPE_ROM
    else:
        r_type = ROM_TYPE_ERROR

    return r_type

def _get_merged_rom(roms, merged_name):
    merged_rom_list = filter(lambda r: r['name'] == merged_name, roms)

    return merged_rom_list[0]

def _get_ROM_location(rom_set, rom, m_name, machines, machines_render, machine_roms):
    if rom_set == 'MERGED':
        cloneof = machines_render[m_name]['cloneof']

        # In the Merged set all Parent and Clone ROMs are in the parent archive.
        # However, according to the Pleasuredome DATs, ROMs are organised like
        # this:
        #   clone_name_a/clone_rom_1
        #   clone_name_b/clone_rom_1
        #   parent_rom_1
        #   parent_rom_2
        if cloneof:
            location = cloneof + '/' + m_name + '/' + rom['name']
        else:
            location = m_name + '/' + rom['name']

    elif rom_set == 'SPLIT':
        machine = machines[m_name]
        cloneof = machines_render[m_name]['cloneof']
        if not cloneof:
            # --- Parent machine ---
            # 1. In the Split set non-merged ROMs are in the machine archive and merged ROMs
            #    are in the parent archive.
            if rom['merge']:
                romof = machine['romof']
                bios_name = romof
                bios_roms = machine_roms[bios_name]['roms']
                bios_rom_merged_name = rom['merge']
                bios_merged_rom = _get_merged_rom(bios_roms, bios_rom_merged_name)
                if bios_merged_rom['merge']:
                    bios_romof = machines[bios_name]['romof']
                    parent_bios_name = bios_romof
                    parent_bios_roms = machine_roms[parent_bios_name]['roms']
                    parent_bios_rom_merged_name = bios_merged_rom['merge']
                    parent_bios_merged_rom = _get_merged_rom(parent_bios_roms, parent_bios_rom_merged_name)
                    location = parent_bios_name + '/' + parent_bios_merged_rom['name']
                else:
                    location = bios_name + '/' + bios_merged_rom['name']
            else:
                location = m_name + '/' + rom['name']
        else:
            # --- Clone machine ---
            # 1. In the Split set, non-merged ROMs are in the machine ZIP archive and
            #    merged ROMs are in the parent archive. 
            # 2. If ROM is a BIOS it is located in the romof of the parent. BIOS ROMs 
            #    always have the merge attribute. 
            # 3. Some machines (notably mslugN) also have non-BIOS common ROMs merged in 
            #    neogeo.zip BIOS archive.
            # 4. Some machines (notably XXXXX) have all ROMs merged. In other words, do not
            #    have their own ROMs.
            # 5. Special case: there could be duplicate ROMs with different regions.
            #    For example, in neogeo.zip
            #    <rom name="sm1.sm1" size="131072" crc="94416d67" sha1="42f..." />
            #    <rom name="sm1.sm1" size="131072" crc="94416d67" sha1="42f..." />
            #
            #    Furthermore, some machines may have more than 2 identical ROMs:
            #    <machine name="aa3000" sourcefile="aa310.cpp" cloneof="aa310" romof="aa310">
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="300" size="256" crc="0da2d31d" />
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="310" size="256" crc="0da2d31d" />
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="311" size="256" crc="0da2d31d" />
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="319" size="256" crc="0da2d31d" />
            #
            if rom['merge']:
                # >> Get merged ROM from parent
                parent_name = cloneof
                parent_roms = machine_roms[parent_name]['roms']
                clone_rom_merged_name = rom['merge']
                parent_merged_rom = _get_merged_rom(parent_roms, clone_rom_merged_name)
                # >> Check if clone merged ROM is also merged in parent (BIOS ROM)
                if parent_merged_rom['merge']:
                    parent_romof = machines[parent_name]['romof']
                    bios_name = parent_romof
                    bios_roms = machine_roms[bios_name]['roms']
                    bios_rom_merged_name = parent_merged_rom['merge']
                    bios_merged_rom = _get_merged_rom(bios_roms, bios_rom_merged_name)
                    # >> At least in one machine (0.196) BIOS roms can be merged in another BIOS.
                    if bios_merged_rom['merge']:
                        bios_romof = machines[bios_name]['romof']
                        parent_bios_name = bios_romof
                        parent_bios_roms = machine_roms[parent_bios_name]['roms']
                        parent_bios_rom_merged_name = bios_merged_rom['merge']
                        parent_bios_merged_rom = _get_merged_rom(parent_bios_roms, parent_bios_rom_merged_name)
                        location = parent_bios_name + '/' + parent_bios_merged_rom['name']
                    else:
                        location = bios_name + '/' + bios_merged_rom['name']
                else:
                    location = parent_name + '/' + parent_merged_rom['name']
            else:
                location = m_name + '/' + rom['name']

    elif rom_set == 'NONMERGED':
        # >> In the Non-Merged set all ROMs are in the machine archive, including BIOSes and
        # >> device ROMs.
        location = m_name + '/' + rom['name']

    else:
        raise TypeError

    return location

def _get_CHD_location(chd_set, disk, m_name, machines, machines_render, machine_roms):
    if chd_set == 'MERGED':
        machine = machines[m_name]
        cloneof = machines_render[m_name]['cloneof']
        romof   = machine['romof']
        if not cloneof:
            # --- Parent machine ---
            if disk['merge']:
                location = romof + '/' + disk['merge']
            else:
                location = m_name + '/' + disk['name']
        else:
            # --- Clone machine ---
            if disk['merge']:
                # >> Get merged ROM from parent
                parent_name = cloneof
                parent_romof = machines[parent_name]['romof']
                parent_disks =  machine_roms[parent_name]['disks']
                clone_disk_merged_name = disk['merge']
                # >> Pick ROMs with same name and choose the first one.
                parent_merged_disk_l = filter(lambda r: r['name'] == clone_disk_merged_name, parent_disks)
                parent_merged_disk = parent_merged_disk_l[0]
                # >> Check if clone merged ROM is also merged in parent
                if parent_merged_disk['merge']:
                    # >> ROM is in the 'romof' archive of the parent ROM
                    super_parent_name = parent_romof
                    super_parent_disks =  machine_roms[super_parent_name]['disks']
                    parent_disk_merged_name = parent_merged_disk['merge']
                    # >> Pick ROMs with same name and choose the first one.
                    super_parent_merged_disk_l = filter(lambda r: r['name'] == parent_disk_merged_name, super_parent_disks)
                    super_parent_merged_disk = super_parent_merged_disk_l[0]
                    location = super_parent_name + '/' + super_parent_merged_disk['name']
                else:
                    location = parent_name + '/' + parent_merged_disk['name']
            else:
                location = cloneof + '/' + disk['name']

    elif chd_set == 'SPLIT':
        if not cloneof:
            # --- Parent machine ---
            if disk['merge']:
                location = romof + '/' + disk['name']
            else:
                location = m_name + '/' + disk['name']
        else:
            # --- Clone machine ---
            parent_romof = machines[cloneof]['romof']
            if disk['merge']:
                location = romof + '/' + disk['name']
            else:
                location = m_name + '/' + disk['name']

    elif chd_set == 'NONMERGED':
        location = m_name + '/' + disk['name']

    else:
        raise TypeError

    return location

# Audit database build main function.
#
# audit_roms_dic = {
#     'machine_name ' : [
#         {
#             'crc'      : string,
#             'location' : 'zip_name/rom_name.rom'
#             'name'     : string,
#             'size'     : int,
#             'type'     : 'ROM' or 'BROM' or 'MROM' or 'XROM'
#         },
#         {
#             'location' : 'machine_name/chd_name.chd'
#             'name'     : string,
#             'sha1'     : string,
#             'type'     : 'DISK'
#         }, ...
#     ],
#     ...
# }
#
# A) Used by the ROM scanner to check how many machines may be run or not depending of the
#    ZIPs/CHDs you have. Note that depeding of the ROM set (Merged, Split, Non-merged) the number
#    of machines you can run changes.
# B) For every machine stores the ZIP/CHD required files to run the machine.
# C) A ZIP/CHD exists if and only if it is valid (CRC/SHA1 exists). Invalid ROMs are excluded.
#
# machine_archives_dic = {
#     'machine_name ' : { 'ROMs' : [name1, name2, ...], 'CHDs' : [dir/name1, dir/name2, ...] }, ...
# }
#
# A) Used by the ROM scanner to determine how many ZIPs/CHDs files you have or not.
# B) Both lists have unique elements (instead of lists there should be sets but sets are 
#    not JSON serializable).
# C) A ZIP/CHD exists if and only if it is valid (CRC/SHA1 exists). Invalid ROMs are excluded.
#
# ROM_archive_list = [ name1, name2, ..., nameN ]
# CHD_archive_list = [ dir1/name1, dir2/name2, ..., dirN/nameN ]
#
# Saves:
#   ROM_AUDIT_DB_PATH
#   ROM_SET_MACHINE_ARCHIVES_DB_PATH
#   ROM_SET_ROM_ARCHIVES_DB_PATH
#   ROM_SET_CHD_ARCHIVES_DB_PATH
#
def mame_build_ROM_audit_databases(PATHS, settings, control_dic,
                                   machines, machines_render, devices_db_dic, machine_roms):
    log_info('mame_build_ROM_audit_databases() Initialising ...')

    # --- Initialise ---
    rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][settings['mame_rom_set']]
    chd_set = ['MERGED', 'SPLIT', 'NONMERGED'][settings['mame_chd_set']]
    rom_set_str = ['Merged', 'Split', 'Non-merged'][settings['mame_rom_set']]
    chd_set_str = ['Merged', 'Split', 'Non-merged'][settings['mame_chd_set']]
    log_info('mame_build_ROM_audit_databases() ROM set is {0}'.format(rom_set))
    log_info('mame_build_ROM_audit_databases() CHD set is {0}'.format(chd_set))
    audit_roms_dic = {}
    pDialog = xbmcgui.DialogProgress()

    # --- ROM set (refactored code) ---------------------------------------------------------------
    pDialog.create('Advanced MAME Launcher')
    log_info('mame_build_ROM_audit_databases() Building {0} ROM set ...'.format(rom_set_str))
    pDialog.update(0, 'Building {0} ROM set ...'.format(rom_set_str))
    num_items = len(machines)
    item_count = 0
    for m_name in sorted(machines):
        # --- Update dialog ---
        pDialog.update((item_count*100)//num_items)
        
        # --- ROMs ---
        # >> Skip Devices
        if machines_render[m_name]['isDevice']: continue
        m_roms = machine_roms[m_name]['roms']
        machine_rom_set = []
        for rom in m_roms:
            rom['type'] = _get_ROM_type(rom)
            rom['location'] = _get_ROM_location(rom_set, rom, m_name, machines, machines_render, machine_roms)
            machine_rom_set.append(rom)

        # --- Device ROMs ---
        device_roms_list = []
        for device in devices_db_dic[m_name]:
            device_roms_dic = machine_roms[device]
            for rom in device_roms_dic['roms']:
                rom['type'] = ROM_TYPE_DROM
                rom['location'] = device + '/' + rom['name']
                device_roms_list.append(rom)
        if device_roms_list: machine_rom_set.extend(device_roms_list)

        # --- Samples ---
        sampleof = machines[m_name]['sampleof']
        m_samples = machine_roms[m_name]['samples']
        samples_list = []
        for sample in m_samples:
            sample['type'] = ROM_TYPE_SAMPLE
            sample['location'] = sampleof + '/' + sample['name']
            samples_list.append(sample)
        if samples_list: machine_rom_set.extend(samples_list)

        # >> Add ROMs to main DB
        audit_roms_dic[m_name] = machine_rom_set

        # --- Update dialog ---
        item_count += 1
    pDialog.close()

    # --- CHD set (refactored code) ---------------------------------------------------------------
    pDialog.create('Advanced MAME Launcher')
    log_info('mame_build_ROM_audit_databases() Building {0} CHD set ...'.format(chd_set_str))
    pDialog.update(0, 'Building {0} CHD set ...'.format(chd_set_str))
    num_items = len(machines)
    item_count = 0
    for m_name in sorted(machines):
        # --- Update dialog ---
        pDialog.update((item_count*100)//num_items)

        # --- CHDs ---
        # >> Skip Devices
        if machines_render[m_name]['isDevice']: continue
        m_disks = machine_roms[m_name]['disks']
        machine_chd_set = []
        for disk in m_disks:
            disk['type'] = ROM_TYPE_DISK
            disk['location'] = _get_CHD_location(chd_set, disk, m_name, machines, machines_render, machine_roms)
            machine_chd_set.append(disk)
        if m_name in audit_roms_dic:
            audit_roms_dic[m_name].extend(machine_chd_set)
        else:
            audit_roms_dic[m_name] = machine_chd_set

        # --- Update dialog ---
        item_count += 1
    pDialog.close()

    # --- Machine archives and ROM/Sample/CHD sets ---
    # NOTE roms_dic and chds_dic may have invalid ROMs/CHDs. However, machine_archives_dic must
    #      have only valid ROM archives (ZIP/7Z).
    # For every machine, it goes ROM by ROM and makes a list of ZIP archive locations. Then, it
    # transforms the list into a set to have a list with unique elements.
    # roms_dic/chds_dic have invalid ROMs. Skip invalid ROMs.
    machine_archives_dic = {}
    full_ROM_archive_set = set()
    full_Sample_archive_set = set()
    full_CHD_archive_set = set()
    pDialog.create('Advanced MAME Launcher')
    pDialog.update(0, 'Building ROM and CHD archive lists ...')
    num_items = len(machines)
    item_count = 0
    machine_archives_ROM = 0
    machine_archives_ROM_parents = 0
    machine_archives_ROM_clones = 0
    machine_archives_Samples = 0
    machine_archives_Samples_parents = 0
    machine_archives_Samples_clones = 0
    machine_archives_CHD = 0
    machine_archives_CHD_parents = 0
    machine_archives_CHD_clones = 0
    archive_less = 0
    archive_less_parents = 0
    archive_less_clones = 0
    ROMs_total = 0
    ROMs_valid = 0
    ROMs_invalid = 0
    CHDs_total = 0
    CHDs_valid = 0
    CHDs_invalid = 0
    for m_name in audit_roms_dic:
        # --- Update dialog ---
        pDialog.update((item_count*100)//num_items)

        isClone = True if machines_render[m_name]['cloneof'] else False
        rom_list = audit_roms_dic[m_name]
        machine_rom_archive_set = set()
        machine_sample_archive_set = set()
        machine_chd_archive_set = set()
        # --- Iterate ROMs/CHDs ---
        for rom in rom_list:
            if rom['type'] == ROM_TYPE_DISK:
                CHDs_total += 1
                # >> Skip invalid CHDs
                if not rom['sha1']:
                    CHDs_invalid += 1
                    continue
                CHDs_valid += 1
                chd_name = rom['location']
                machine_chd_archive_set.add(chd_name)
                full_CHD_archive_set.add(rom['location'])
            elif rom['type'] == ROM_TYPE_SAMPLE:
                sample_str_list = rom['location'].split('/')
                zip_name = sample_str_list[0]
                machine_sample_archive_set.add(zip_name)
                archive_str = rom['location'].split('/')[0]
                full_Sample_archive_set.add(archive_str)
            else:
                ROMs_total += 1
                # >> Skip invalid ROMs
                if not rom['crc']:
                    ROMs_invalid += 1
                    continue
                ROMs_valid += 1
                rom_str_list = rom['location'].split('/')
                zip_name = rom_str_list[0]
                machine_rom_archive_set.add(zip_name)
                archive_str = rom['location'].split('/')[0]
                # if not archive_str: continue
                full_ROM_archive_set.add(archive_str)
        machine_archives_dic[m_name] = {
            'ROMs'    : list(machine_rom_archive_set),
            'Samples' : list(machine_sample_archive_set),
            'CHDs'    : list(machine_chd_archive_set),
        }

        # --- Statistics ---
        if machine_rom_archive_set:
            machine_archives_ROM += 1
            if isClone:
                machine_archives_ROM_clones += 1
            else:
                machine_archives_ROM_parents += 1
        if machine_sample_archive_set:
            machine_archives_Samples += 1
            if isClone:
                machine_archives_Samples_clones += 1
            else:
                machine_archives_Samples_parents += 1
        if machine_chd_archive_set:
            machine_archives_CHD += 1
            if isClone:
                machine_archives_CHD_clones += 1
            else:
                machine_archives_CHD_parents += 1
        if not (machine_rom_archive_set or machine_sample_archive_set or machine_chd_archive_set):
            archive_less += 1
            if isClone:
                archive_less_clones += 1
            else:
                archive_less_parents += 1

        # --- Update dialog ---
        item_count += 1
    pDialog.close()
    ROM_archive_list = list(sorted(full_ROM_archive_set))
    Sample_archive_list = list(sorted(full_Sample_archive_set))
    CHD_archive_list = list(sorted(full_CHD_archive_set))

    # ---------------------------------------------------------------------------------------------
    # Remove unused fiels to save memory before saving the JSON file.
    # Do not remove earlier because 'merge' is used in the _get_XXX_location() functions.
    # ---------------------------------------------------------------------------------------------
    pDialog.create('Advanced MAME Launcher')
    log_info('mame_build_ROM_audit_databases() Building {0} ROM set ...'.format(rom_set_str))
    pDialog.update(0, 'Building {0} ROM set ...'.format(rom_set_str))
    num_items = len(machines)
    item_count = 0
    for m_name in sorted(machines):
        # --- Update dialog ---
        pDialog.update((item_count*100)//num_items)

        # --- Skip devices and process ROMs and CHDs ---
        if machines_render[m_name]['isDevice']: continue
        for rom in machine_roms[m_name]['roms']:
            # >> Remove unused fields to save space in JSON database, but remove from the copy!
            rom.pop('merge')
            rom.pop('bios')
        for disk in machine_roms[m_name]['disks']:
            disk.pop('merge')

        # --- Update dialog ---
        item_count += 1
    pDialog.close()


    # ---------------------------------------------------------------------------------------------
    # Update MAME control dictionary
    # ---------------------------------------------------------------------------------------------
    change_control_dic(control_dic, 'stats_audit_MAME_ROM_ZIP_files', len(ROM_archive_list))
    change_control_dic(control_dic, 'stats_audit_MAME_Sample_ZIP_files', len(Sample_archive_list))
    change_control_dic(control_dic, 'stats_audit_MAME_CHD_files', len(CHD_archive_list))
    change_control_dic(control_dic, 'stats_audit_machine_archives_ROM', machine_archives_ROM)
    change_control_dic(control_dic, 'stats_audit_machine_archives_ROM_parents', machine_archives_ROM_parents)
    change_control_dic(control_dic, 'stats_audit_machine_archives_ROM_clones', machine_archives_ROM_clones)
    change_control_dic(control_dic, 'stats_audit_machine_archives_CHD', machine_archives_CHD)
    change_control_dic(control_dic, 'stats_audit_machine_archives_CHD_parents', machine_archives_CHD_parents)
    change_control_dic(control_dic, 'stats_audit_machine_archives_CHD_clones', machine_archives_CHD_clones)
    change_control_dic(control_dic, 'stats_audit_machine_archives_Samples', machine_archives_Samples)
    change_control_dic(control_dic, 'stats_audit_machine_archives_Samples_parents', machine_archives_Samples_parents)
    change_control_dic(control_dic, 'stats_audit_machine_archives_Samples_clones', machine_archives_Samples_clones)
    change_control_dic(control_dic, 'stats_audit_archive_less', archive_less)
    change_control_dic(control_dic, 'stats_audit_archive_less_parents', archive_less_parents)
    change_control_dic(control_dic, 'stats_audit_archive_less_clones', archive_less_clones)
    change_control_dic(control_dic, 'stats_audit_ROMs_total', ROMs_total)
    change_control_dic(control_dic, 'stats_audit_ROMs_valid', ROMs_valid)
    change_control_dic(control_dic, 'stats_audit_ROMs_invalid', ROMs_invalid)
    change_control_dic(control_dic, 'stats_audit_CHDs_total', CHDs_total)
    change_control_dic(control_dic, 'stats_audit_CHDs_valid', CHDs_valid)
    change_control_dic(control_dic, 'stats_audit_CHDs_invalid', CHDs_invalid)
    change_control_dic(control_dic, 't_MAME_Audit_DB_build', time.time())

    # --- Save databases ---
    if OPTION_LOWMEM_WRITE_JSON:
        json_write_func = fs_write_JSON_file_lowmem
        log_debug('Using fs_write_JSON_file_lowmem() JSON writer')
    else:
        json_write_func = fs_write_JSON_file
        log_debug('Using fs_write_JSON_file() JSON writer')
    line1_str = 'Saving audit/scanner databases ...'
    pDialog.create('Advanced MAME Launcher')
    num_items = 4
    pDialog.update(int((0*100) / num_items), line1_str, 'MAME ROM Audit')
    json_write_func(PATHS.ROM_AUDIT_DB_PATH.getPath(), audit_roms_dic)
    pDialog.update(int((1*100) / num_items), line1_str, 'Machine archives list')
    json_write_func(PATHS.ROM_SET_MACHINE_ARCHIVES_DB_PATH.getPath(), machine_archives_dic)
    pDialog.update(int((2*100) / num_items), line1_str, 'ROM List index')
    json_write_func(PATHS.ROM_SET_ROM_ARCHIVES_DB_PATH.getPath(), ROM_archive_list)
    pDialog.update(int((3*100) / num_items), line1_str, 'CHD list index')
    json_write_func(PATHS.ROM_SET_CHD_ARCHIVES_DB_PATH.getPath(), CHD_archive_list)
    pDialog.update(int((4*100) / num_items), ' ', ' ')
    pDialog.close()

# -------------------------------------------------------------------------------------------------
#
# Add clones to the all catalog dictionary catalog_all_dic.
# catalog_all_dic is modified by refence.
#
def _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all_dic):
    for clone_name in main_pclone_dic[parent_name]:
        catalog_all_dic[clone_name] = machines_render[clone_name]['description']

#
# Do not store the number if categories in a catalog. If necessary, calculate it on the fly.
# I think Python len() on dictionaries is very fast
#
def _cache_index_builder(cat_name, cache_index_dic, catalog_all, catalog_parents):
    for cat_key in catalog_all:
        cache_index_dic[cat_name][cat_key] = {
            'num_parents'  : len(catalog_parents[cat_key]),
            'num_machines' : len(catalog_all[cat_key]),
            'hash'         : fs_rom_cache_get_hash(cat_name, cat_key)
        }

def _build_catalog_helper(catalog_parents, catalog_all, machines, machines_render, main_pclone_dic, db_field):
    for parent_name in main_pclone_dic:
        # >> Skip device machines in catalogs.
        if machines_render[parent_name]['isDevice']: continue
        catalog_key = machines[parent_name][db_field]
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machines_render[parent_name]['description']
            catalog_all[catalog_key][parent_name] = machines_render[parent_name]['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machines_render[parent_name]['description'] }
            catalog_all[catalog_key] = { parent_name : machines_render[parent_name]['description'] }
        for clone_name in main_pclone_dic[parent_name]:
            catalog_all[catalog_key][clone_name] = machines_render[clone_name]['description']

#
# A) Builds the following catalog files
#    CATALOG_MAIN_PARENT_PATH
#    CATALOG_MAIN_ALL_PATH
#    CATALOG_CATVER_PARENT_PATH
#    CATALOG_CATVER_ALL_PATH
#    ...
#
#    main_catalog_parents = {
#        'cat_key' : [ parent1, parent2, ... ]
#    }
#
#    main_catalog_all = {
#        'cat_key' : [ machine1, machine2, ... ]
#    }
#
# B) Cache index:
#    CACHE_INDEX_PATH
#
#    cache_index_dic = {
#        'catalog_name' : { --> 'Main', 'Binary', ...
#            'cat_key' : {
#                'num_machines' : int,
#                'num_parents' : int,
#                'hash' : str
#            }, ...
#        }, ...
#    }
#
def mame_build_MAME_catalogs(PATHS, settings, control_dic,
                             machines, machines_render, machine_roms, main_pclone_dic, assets_dic):
    # >> Progress dialog
    pDialog_line1 = 'Building catalogs ...'
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher', pDialog_line1)
    processed_filters = 0
    update_number = 0

    # --- Machine count ---
    cache_index_dic = {
        'Main'              : {},
        'Binary'            : {},
        'Catver'            : {},
        'Catlist'           : {},
        'Genre'             : {},
        'NPlayers'          : {},
        'Bestgames'         : {},
        'Series'            : {},
        'Manufacturer'      : {},
        'Year'              : {},
        'Driver'            : {},
        'Controls_Expanded' : {},
        'Controls_Compact'  : {},
        'Display_Type'      : {},
        'Display_Rotate'    : {},
        'Devices_Expanded'  : {},
        'Devices_Compact'   : {},
        'BySL'              : {},
        'ShortName'         : {},
        'LongName'          : {},
    }
    NUM_CATALOGS = len(cache_index_dic)

    # ---------------------------------------------------------------------------------------------
    # Main filters (None catalog) -----------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    pDialog.update(update_number, pDialog_line1, 'Main Catalog')
    main_catalog_parents = {}
    main_catalog_all = {}

    # --- Normal and Unusual machine list ---
    # Machines with Coin Slot and Non Mechanical and not Dead and not Device
    log_info('Making None catalog - Coin index ...')
    normal_parent_dic = {}
    normal_all_dic = {}
    unusual_parent_dic = {}
    unusual_all_dic = {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_main['isMechanical']: continue
        if machine_main['coins'] == 0: continue
        if machine_main['isDead']: continue
        if machine_render['isDevice']: continue

        # --- Determinte if machine is Normal or Unusual ----
        # Add parent to parent list and parents and clonse to all list
        # Unusual machine: no controls or control_type has "only_buttons" or "gambling"
        # or "hanafuda" or "mahjong"
        #
        # Unusual machine driver exceptions (must be Normal and not Unusual):
        #
        ctrl_list = machine_main['control_type']
        if ('only_buttons' in ctrl_list and len(ctrl_list) > 1) or \
           machine_main['sourcefile'] == '88games.cpp' or \
           machine_main['sourcefile'] == 'cball.cpp' or \
           machine_main['sourcefile'] == 'asteroid.cpp':
            normal_parent_dic[parent_name] = machine_render['description']
            normal_all_dic[parent_name] = machine_render['description']
            _catalog_add_clones(parent_name, main_pclone_dic, machines_render, normal_all_dic)
        #
        # Unusual machines. Most of them you don't wanna play.
        #
        elif not ctrl_list or 'only_buttons' in ctrl_list or 'gambling' in ctrl_list or \
             'hanafuda' in ctrl_list or 'mahjong' in ctrl_list or \
             machine_main['sourcefile'] == 'aristmk5.cpp' or \
             machine_main['sourcefile'] == 'adp.cpp' or \
             machine_main['sourcefile'] == 'mpu4vid.cpp' or \
             machine_main['sourcefile'] == 'cubo.cpp' or \
             machine_main['sourcefile'] == 'sfbonus.cpp' or \
             machine_main['sourcefile'] == 'peplus.cpp':
            unusual_parent_dic[parent_name] = machine_render['description']
            unusual_all_dic[parent_name] = machine_render['description']
            _catalog_add_clones(parent_name, main_pclone_dic, machines_render, unusual_all_dic)
        #
        # What remains go to the Normal/Standard list.
        #
        else:
            normal_parent_dic[parent_name] = machine_render['description']
            normal_all_dic[parent_name] = machine_render['description']
            _catalog_add_clones(parent_name, main_pclone_dic, machines_render, normal_all_dic)
    main_catalog_parents['Normal']  = normal_parent_dic
    main_catalog_all['Normal']      = normal_all_dic
    main_catalog_parents['Unusual'] = unusual_parent_dic
    main_catalog_all['Unusual']     = unusual_all_dic

    # --- NoCoin list ---
    # A) Machines with No Coin Slot and Non Mechanical and not Dead and not Device
    log_info('Making NoCoin index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_main['isMechanical']: continue
        if machine_main['coins'] > 0: continue
        if machine_main['isDead']: continue
        if machine_render['isDevice']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    main_catalog_parents['NoCoin'] = parent_dic
    main_catalog_all['NoCoin'] = all_dic

    # --- Mechanical machines ---
    # >> Mechanical machines and not Dead and not Device
    log_info('Making Mechanical index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = machines_render[parent_name]
        if not machine_main['isMechanical']: continue
        if machine_main['isDead']: continue
        if machine_render['isDevice']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    main_catalog_parents['Mechanical'] = parent_dic
    main_catalog_all['Mechanical'] = all_dic

    # --- Dead machines ---
    # >> Dead machines
    log_info('Making Dead Machines index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = machines_render[parent_name]
        if not machine_main['isDead']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    main_catalog_parents['Dead'] = parent_dic
    main_catalog_all['Dead'] = all_dic

    # --- Device machines ---
    # >> Device machines
    log_info('Making Device Machines index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine_render = machines_render[parent_name]
        if not machine_render['isDevice']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    main_catalog_parents['Devices'] = parent_dic
    main_catalog_all['Devices'] = all_dic

    # >> Build ROM cache index and save Main catalog JSON file
    _cache_index_builder('Main', cache_index_dic, main_catalog_all, main_catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_MAIN_ALL_PATH.getPath(), main_catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_MAIN_PARENT_PATH.getPath(), main_catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # ---------------------------------------------------------------------------------------------
    # Binary filters ------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    pDialog.update(update_number, pDialog_line1, 'Binary Catalog')
    binary_catalog_parents = {}
    binary_catalog_all = {}

    # --- CHD machines ---
    log_info('Making CHD Machines index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine_roms[parent_name]['disks']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    binary_catalog_parents['CHD'] = parent_dic
    binary_catalog_all['CHD'] = all_dic

    # --- Machines with samples ---
    log_info('Making Samples Machines index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine['sampleof']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    binary_catalog_parents['Samples'] = parent_dic
    binary_catalog_all['Samples'] = all_dic

    # --- Software List machines ---
    log_info('Making Software List Machines index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine['softwarelists']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    binary_catalog_parents['SoftwareLists'] = parent_dic
    binary_catalog_all['SoftwareLists'] = all_dic

    # --- BIOS ---
    log_info('Making BIOS Machines index ...')
    parent_dic = {}
    all_dic = {}
    for parent_name in main_pclone_dic:
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine_render['isBIOS']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, all_dic)
    binary_catalog_parents['BIOS'] = parent_dic
    binary_catalog_all['BIOS'] = all_dic

    # >> Build cache index and save Binary catalog JSON file
    _cache_index_builder('Binary', cache_index_dic, binary_catalog_all, binary_catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_BINARY_ALL_PATH.getPath(), binary_catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_BINARY_PARENT_PATH.getPath(), binary_catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # ---------------------------------------------------------------------------------------------
    # Cataloged machine lists ---------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # --- Catver catalog ---
    log_info('Making Catver catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Catver catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines, machines_render, main_pclone_dic, 'catver')
    _cache_index_builder('Catver', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_CATVER_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_CATVER_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Catlist catalog ---
    log_info('Making Catlist catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Catlist catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines, machines_render, main_pclone_dic, 'catlist')
    _cache_index_builder('Catlist', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_CATLIST_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_CATLIST_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Genre catalog ---
    log_info('Making Genre catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Genre catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines, machines_render, main_pclone_dic, 'genre')
    _cache_index_builder('Genre', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_GENRE_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_GENRE_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Nplayers catalog ---
    log_info('Making Nplayers catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Nplayers catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines_render, machines_render, main_pclone_dic, 'nplayers')
    _cache_index_builder('NPlayers', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_NPLAYERS_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_NPLAYERS_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Bestgames catalog ---
    log_info('Making Bestgames catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Bestgames catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines, machines_render, main_pclone_dic, 'bestgames')
    _cache_index_builder('Bestgames', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_BESTGAMES_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_BESTGAMES_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Series catalog ---
    log_info('Making Series catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Series catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines, machines_render, main_pclone_dic, 'series')
    _cache_index_builder('Series', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_SERIES_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_SERIES_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Manufacturer catalog ---
    log_info('Making Manufacturer catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Manufacturer catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines_render, machines_render, main_pclone_dic, 'manufacturer')
    _cache_index_builder('Manufacturer', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_MANUFACTURER_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_MANUFACTURER_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Year catalog ---
    log_info('Making Year catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Year catalog')
    catalog_parents = {}
    catalog_all = {}
    _build_catalog_helper(catalog_parents, catalog_all, machines_render, machines_render, main_pclone_dic, 'year')
    _cache_index_builder('Year', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_YEAR_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_YEAR_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Driver catalog ---
    log_info('Making Driver catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Driver catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        catalog_key = machine['sourcefile']
        if catalog_key in mame_driver_name_dic: catalog_key = mame_driver_name_dic[catalog_key]
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machine_render['description']
            catalog_all[catalog_key][parent_name] = machine_render['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
            catalog_all[catalog_key] = { parent_name : machine_render['description'] }
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Driver', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_DRIVER_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_DRIVER_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Control catalog (Expanded) ---
    log_info('Making Control Expanded catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Control Expanded catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        # >> Order alphabetically the list
        pretty_control_type_list = mame_improve_control_type_list(machine['control_type'])
        sorted_control_type_list = sorted(pretty_control_type_list)
        # >> Maybe a setting should be added for compact or non-compact control list
        # sorted_control_type_list = mame_compress_item_list(sorted_control_type_list)
        sorted_control_type_list = mame_compress_item_list_compact(sorted_control_type_list)
        catalog_key = " / ".join(sorted_control_type_list)
        # >> Change category name for machines with no controls
        if catalog_key == '': catalog_key = '[ No controls ]'
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machine_render['description']
            catalog_all[catalog_key][parent_name] = machine_render['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
            catalog_all[catalog_key] = { parent_name : machine_render['description'] }
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Controls_Expanded', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_CONTROL_EXPANDED_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_CONTROL_EXPANDED_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Control catalog (Compact) ---
    # >> In this catalog one machine may be in several categories if the machine has more than
    # >> one control.
    log_info('Making Control Compact catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Control Compact catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        # >> Order alphabetically the list
        pretty_control_type_list = mame_improve_control_type_list(machine['control_type'])
        sorted_control_type_list = sorted(pretty_control_type_list)
        compressed_control_type_list = mame_compress_item_list_compact(sorted_control_type_list)
        if not compressed_control_type_list: compressed_control_type_list = [ '[ No controls ]' ]
        for catalog_key in compressed_control_type_list:
            if catalog_key in catalog_parents:
                catalog_parents[catalog_key][parent_name] = machine_render['description']
                catalog_all[catalog_key][parent_name] = machine_render['description']
            else:
                catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
                catalog_all[catalog_key] = { parent_name : machine_render['description'] }
            _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Controls_Compact', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_CONTROL_COMPACT_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_CONTROL_COMPACT_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Display type catalog ---
    log_info('Making Display Type catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Display type catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        catalog_key = " / ".join(machine['display_type'])
        # >> Change category name for machines with no display
        if catalog_key == '': catalog_key = '[ No display ]'
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machine_render['description']
            catalog_all[catalog_key][parent_name] = machine_render['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
            catalog_all[catalog_key] = { parent_name : machine_render['description'] }
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Display_Type', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_DISPLAY_TYPE_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_DISPLAY_TYPE_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Display rotate catalog ---
    log_info('Making Display Rotate catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Display rotate catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        # >> machine['display_rotate'] is a list of strings
        fixed_d_rotate_list = []
        for d_str in machine['display_rotate']:
            if d_str == '0' or d_str == '180':
                fixed_d_rotate_list.append('Horizontal')
            elif d_str == '90' or d_str == '270':
                fixed_d_rotate_list.append('Vertical')
            else:
                raise TypeError('Machine {0} wrong display rotate "{1}"'.format(parent_name, d_str))
        catalog_key = " / ".join(fixed_d_rotate_list)
        # >> Change category name for machines with no display
        if catalog_key == '': catalog_key = '[ No display ]'
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machine_render['description']
            catalog_all[catalog_key][parent_name] = machine_render['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
            catalog_all[catalog_key] = { parent_name : machine_render['description'] }
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Display_Rotate', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_DISPLAY_ROTATE_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_DISPLAY_ROTATE_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- <device> / Device Expanded catalog ---
    log_info('Making <device> tag Expanded catalog ...')
    pDialog.update(update_number, pDialog_line1, '<device> Expanded catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        # >> Order alphabetically the list
        device_list = [device['att_type'] for device in machine['devices']]
        pretty_device_list = mame_improve_device_list(device_list)
        sorted_device_list = sorted(pretty_device_list)
        # >> Maybe a setting should be added for compact or non-compact control list
        # sorted_device_list = mame_compress_item_list(sorted_device_list)
        sorted_device_list = mame_compress_item_list_compact(sorted_device_list)
        catalog_key = " / ".join(sorted_device_list)
        # >> Change category name for machines with no devices
        if catalog_key == '': catalog_key = '[ No devices ]'
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machine_render['description']
            catalog_all[catalog_key][parent_name] = machine_render['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
            catalog_all[catalog_key] = { parent_name : machine_render['description'] }
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Devices_Expanded', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_DEVICE_EXPANDED_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_DEVICE_EXPANDED_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- <device> / Device Compact catalog ---
    log_info('Making <device> tag Compact catalog ...')
    pDialog.update(update_number, pDialog_line1, '<device> Compact catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        # >> Order alphabetically the list
        device_list = [ device['att_type'] for device in machine['devices'] ]
        pretty_device_list = mame_improve_device_list(device_list)
        sorted_device_list = sorted(pretty_device_list)
        compressed_device_list = mame_compress_item_list_compact(sorted_device_list)
        if not compressed_device_list: compressed_device_list = [ '[ No devices ]' ]
        for catalog_key in compressed_device_list:
            if catalog_key in catalog_parents:
                catalog_parents[catalog_key][parent_name] = machine_render['description']
                catalog_all[catalog_key][parent_name] = machine_render['description']
            else:
                catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
                catalog_all[catalog_key] = { parent_name : machine_render['description'] }
            _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('Devices_Compact', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_DEVICE_COMPACT_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_DEVICE_COMPACT_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- Software List catalog ---
    log_info('Making Software List catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Software List catalog')
    # >> Load proper Software List proper names, if available
    SL_names_dic = fs_load_JSON_file_dic(PATHS.SL_NAMES_PATH.getPath())
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        # >> A machine may have more than 1 software lists
        for sl_name in machine['softwarelists']:
            catalog_key = sl_name
            if catalog_key in SL_names_dic:
                catalog_key = SL_names_dic[catalog_key]
            if catalog_key in catalog_parents:
                catalog_parents[catalog_key][parent_name] = machine_render['description']
                catalog_all[catalog_key][parent_name] = machine_render['description']
            else:
                catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
                catalog_all[catalog_key] = { parent_name : machine_render['description'] }
            _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('BySL', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_SL_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_SL_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- MAME short name catalog ---
    log_info('Making MAME short name catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Short name catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        catalog_key = parent_name[0]
        t = '{0} "{1}"'.format(parent_name, machine_render['description'])
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = t
            catalog_all[catalog_key][parent_name] = t
        else:
            catalog_parents[catalog_key] = { parent_name : t }
            catalog_all[catalog_key] = { parent_name : t }
        for clone_name in main_pclone_dic[parent_name]:
            t = '{0} "{1}"'.format(clone_name, machines_render[clone_name]['description'])
            catalog_all[catalog_key][clone_name] = t
    _cache_index_builder('ShortName', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_SHORTNAME_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_SHORTNAME_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)

    # --- MAME long name catalog ---
    log_info('Making MAME long name catalog ...')
    pDialog.update(update_number, pDialog_line1, 'Long name catalog')
    catalog_parents = {}
    catalog_all = {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = machines_render[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        catalog_key = machine_render['description'][0]
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = machine_render['description']
            catalog_all[catalog_key][parent_name] = machine_render['description']
        else:
            catalog_parents[catalog_key] = { parent_name : machine_render['description'] }
            catalog_all[catalog_key] = { parent_name : machine_render['description'] }
        _catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all[catalog_key])
    _cache_index_builder('LongName', cache_index_dic, catalog_all, catalog_parents)
    fs_write_JSON_file(PATHS.CATALOG_LONGNAME_ALL_PATH.getPath(), catalog_all)
    fs_write_JSON_file(PATHS.CATALOG_LONGNAME_PARENT_PATH.getPath(), catalog_parents)
    processed_filters += 1
    update_number = int((float(processed_filters) / float(NUM_CATALOGS)) * 100)
    pDialog.update(update_number)
    pDialog.close()

    # --- Create properties database with default values ------------------------------------------
    # >> Now overwrites all properties when the catalog is rebuilt.
    #    New versions must kept user set properties!
    # >> Disabled
    # mame_properties_dic = {}
    # for catalog_name in CATALOG_NAME_LIST:
    #     catalog_dic = fs_get_cataloged_dic_parents(PATHS, catalog_name)
    #     for category_name in sorted(catalog_dic):
    #         prop_key = '{0} - {1}'.format(catalog_name, category_name)
    #         mame_properties_dic[prop_key] = {'vm' : VIEW_MODE_PCLONE}
    # fs_write_JSON_file(PATHS.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    # log_info('mame_properties_dic has {0} entries'.format(len(mame_properties_dic)))

    # --- Save Catalog index ----------------------------------------------------------------------
    fs_write_JSON_file(PATHS.CACHE_INDEX_PATH.getPath(), cache_index_dic)

    # --- Update timestamp ---
    change_control_dic(control_dic, 't_MAME_Catalog_build', time.time())

# -------------------------------------------------------------------------------------------------
# Software Lists and ROM audit database building function
# -------------------------------------------------------------------------------------------------
#
# https://www.mess.org/mess/swlist_format
# The basic idea (which leads basically the whole format) is that each <software> entry should 
# correspond to a game box you could have bought in a shop, and that each <part> entry should 
# correspond to a piece (i.e. a cart, a disk or a tape) that you would have found in such a box. 
#
# --- Example 1: 32x.xml-chaotix ---
# Stored as: SL_ROMS/32x/chaotix.zip
#
# <part name="cart" interface="_32x_cart">
#   <dataarea name="rom" size="3145728">
#     <rom name="knuckles' chaotix (europe).bin" size="3145728" crc="41d63572" sha1="5c1...922" offset="000000" />
#   </dataarea>
# </part>
#
# --- Example 2: 32x.xml-doom ---
# Stored as: SL_ROMS/32x/doom.zip
#
# <part name="cart" interface="_32x_cart">
#   <feature name="pcb" value="171-6885A" />
#   <dataarea name="rom" size="3145728">
#     <rom name="mpr-17351-f.ic1" size="2097152" crc="e0ef6ebc" sha1="302...79d" offset="000000" />
#     <rom name="mpr-17352-f.ic2" size="1048576" crc="c7079709" sha1="0f2...33b" offset="0x200000" />
#   </dataarea>
# </part>
#
# --- Example 3: a800.xml-diamond3 ---
# Stored as: SL_ROMS/a800/diamond3.zip (all ROMs from all parts)
#
# <part name="cart" interface="a8bit_cart">
#   <feature name="slot" value="a800_diamond" />
#   <dataarea name="rom" size="65536">
#     <rom name="diamond gos v3.0.rom" size="65536" crc="0ead07f8" sha1="e92...730" offset="0" />
#   </dataarea>
# </part>
# <part name="flop1" interface="floppy_5_25">
#   <dataarea name="flop" size="92176">
#     <rom name="diamond paint.atr" size="92176" crc="d2994282" sha1="be8...287" offset="0" />
#   </dataarea>
# </part>
# <part name="flop2" interface="floppy_5_25">
#   <dataarea name="flop" size="92176">
#     <rom name="diamond write.atr" size="92176" crc="e1e5b235" sha1="c3c...db5" offset="0" />
#   </dataarea>
# </part>
# <part name="flop3" interface="floppy_5_25">
#   <dataarea name="flop" size="92176">
#     <rom name="diamond utilities.atr" size="92176" crc="bb48082d" sha1="eb7...4e4" offset="0" />
#   </dataarea>
# </part>
#
# --- Example 4: a2600.xml-harmbios ---
# Stored as: SL_ROMS/a2600/harmbios.zip (all ROMs from all dataareas)
#
# <part name="cart" interface="a2600_cart">
#   <feature name="slot" value="a26_harmony" />
#   <dataarea name="rom" size="0x8000">
#     <rom name="bios_updater_NTSC.cu" size="0x8000" crc="03153eb2" sha1="cd9...009" offset="0" />
#   </dataarea>
#   <dataarea name="bios" size="0x21400">
#     <rom name="hbios_106_NTSC_official_beta.bin" size="0x21400" crc="1e1d237b" sha1="8fd...1da" offset="0" />
#     <rom name="hbios_106_NTSC_beta_2.bin"        size="0x21400" crc="807b86bd" sha1="633...e9d" offset="0" />
#     <rom name="eeloader_104e_PAL60.bin"          size="0x36f8" crc="58845532" sha1="255...71c" offset="0" />
#   </dataarea>
# </part>
#
# --- Example 5: psx.xml-traid ---
# Stored as: SL_CHDS/psx/traid/tomb raider (usa) (v1.6).chd
#
# <part name="cdrom" interface="psx_cdrom">
#   <diskarea name="cdrom">
#     <disk name="tomb raider (usa) (v1.6)" sha1="697...3ac"/>
#   </diskarea>
# </part>
#
# --- Example 6: psx.xml-traida cloneof=traid ---
# Stored as: SL_CHDS/psx/traid/tomb raider (usa) (v1.5).chd
#
# <part name="cdrom" interface="psx_cdrom">
#   <diskarea name="cdrom">
#     <disk name="tomb raider (usa) (v1.5)" sha1="d48...0a9"/>
#   </diskarea>
# </part>
#
# --- Example 7: pico.xml-sanouk5 ---
# Stored as: SL_ROMS/pico/sanouk5.zip (mpr-18458-t.ic1 ROM)
# Stored as: SL_CHDS/pico/sanouk5/imgpico-001.chd
#
# <part name="cart" interface="pico_cart">
#   <dataarea name="rom" size="524288">
#     <rom name="mpr-18458-t.ic1" size="524288" crc="6340c18a" sha1="101..." offset="000000" loadflag="load16_word_swap" />
#   </dataarea>
#   <diskarea name="cdrom">
#     <disk name="imgpico-001" sha1="c93...10d" />
#   </diskarea>
# </part>
#
# -------------------------------------------------------------------------------------------------
# A) One part may have a dataarea, a diskarea, or both.
#
# B) One part may have more than one dataarea with different names.
#
# SL_roms = {
#   'sl_rom_name' : [
#     {
#       'part_name' : string,
#       'part_interface' : string,
#       'dataarea' : [
#         {
#           'name' : string,
#           'roms' : [
#             {
#               'name' : string, 'size' : int, 'crc' : string
#             },
#           ]
#         }
#       ]
#       'diskarea' : [
#         {
#           'name' : string,
#           'disks' : [
#             {
#               'name' : string, 'sha1' : string
#             },
#           ]
#         }
#       ]
#     }, ...
#   ], ...
# }
#
# -------------------------------------------------------------------------------------------------
# --- SL List ROM Audit database ---
#
# A) For each SL ROM entry, create a list of the ROM files and CHD files, names, sizes, crc/sha1
#    and location.
# SL_roms = {
#   'sl_rom_name' : [
#     {
#       'type'     : string,
#       'name'     : string,
#       'size      : int,
#       'crc'      : sting,
#       'location' : string
#     }, ...
#   ], ...
# }

#
# SL_disks = {
#   'sl_rom_name' : [
#     {
#       'type' : string,
#       'name' : string,
#       'sha1' : sting,
#       'location' : string
#     }, ...
#   ], ...
# }
#
class SLDataObj:
    def __init__(self):
        self.roms = {}
        self.SL_roms = {}
        self.display_name = ''
        self.num_with_ROMs = 0
        self.num_with_CHDs = 0

def _get_SL_dataarea_ROMs(SL_name, item_name, part_child, dataarea_dic):
    # >> Get ROMs in dataarea
    dataarea_num_roms = 0
    for dataarea_child in part_child:
        rom_dic = { 'name' : '', 'size' : '', 'crc'  : '', 'sha1' : '' }
        # >> Force Python to guess the base of the conversion looking at
        # >> 0x prefixes.
        size_int = 0
        if 'size' in dataarea_child.attrib:
            size_int = int(dataarea_child.attrib['size'], 0)
        rom_dic['size'] = size_int
        rom_dic['name'] = dataarea_child.attrib['name'] if 'name' in dataarea_child.attrib else ''
        rom_dic['crc']  = dataarea_child.attrib['crc'] if 'crc' in dataarea_child.attrib else ''
        rom_dic['sha1'] = dataarea_child.attrib['sha1'] if 'sha1' in dataarea_child.attrib else ''

        # In the nes.xml SL some ROM names have a trailing dot '.'. For example (MAME 0.196):
        #
        # ROM  131072  028bfc44  nes/kingey/0.prg              OK            
        # ROM  131072  1aca7960  nes/kingey/king ver 1.3 vid.  ROM not in ZIP
        #
        # PD torrents do not have the trailing dot because this files cause trouble in Windows.
        # To correctly audit PD torrents, remove the trailing dot from filenames.
        # Have a look here http://forum.pleasuredome.org.uk/index.php?showtopic=32701&p=284925
        # I will create a PR to MAME repo to fix these names (and then next couple of lines must
        # be commented).
        if len(rom_dic['name']) > 2 and rom_dic['name'][-1] == '.':
            rom_dic['name'] = rom_dic['name'][:-1]

        # >> Some CRCs are in upper case. Store always lower case in AML DB.
        if rom_dic['crc']: rom_dic['crc'] = rom_dic['crc'].lower()

        # >> Just in case there are SHA1 hashes in upper case (not verified).
        if rom_dic['sha1']: rom_dic['sha1'] = rom_dic['sha1'].lower()

        # >> If ROM has attribute status="nodump" then ignore this ROM.
        if 'status' in dataarea_child.attrib:
            status = dataarea_child.attrib['status']
            if status == 'nodump':
                log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                          'status="nodump". Skipping ROM.')
                continue
            elif status == 'baddump':
                pass
            else:
                log_error('SL {0} / Item {1} / Unknown status = {2}'.format(SL_name, item_name, status))
                raise CriticalError('DEBUG')

        # >> Fix "fake" SL ROMs with loadflag="continue".
        # >> For example, SL neogeo, SL item aof
        if 'loadflag' in dataarea_child.attrib:
            loadflag = dataarea_child.attrib['loadflag']
            if loadflag == 'continue':
                # This ROM is not valid (not a valid ROM file).
                # Size must be added to previous ROM.
                log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                          'loadflag="continue" case. Adding size {0} to previous ROM.'.format(rom_dic['size']))
                previous_rom = dataarea_dic['roms'][-1]
                previous_rom['size'] += rom_dic['size']
                continue
            elif loadflag == 'ignore':
                if rom_dic['size'] > 0:
                    log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                            'loadflag="ignore" case. Adding size {0} to previous ROM.'.format(rom_dic['size']))
                    previous_rom = dataarea_dic['roms'][-1]
                    previous_rom['size'] += rom_dic['size']
                else:
                    log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                              'loadflag="ignore" case and size = 0. Skipping ROM.')
                continue
            elif loadflag == 'reload':
                log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                          'loadflag="reload" case. Skipping ROM.')
                continue
            elif loadflag == 'reload_plain':
                log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                          'loadflag="reload_plain" case. Skipping ROM.')
                continue
            elif loadflag == 'fill':
                log_debug('SL {0} / Item {1} / '.format(SL_name, item_name) +
                          'loadflag="fill" case. Skipping ROM.')
                continue
            elif loadflag == 'load16_word_swap':
                pass
            elif loadflag == 'load16_byte':
                pass
            elif loadflag == 'load32_word':
                pass
            elif loadflag == 'load32_byte':
                pass
            elif loadflag == 'load32_word_swap':
                pass
            else:
                log_error('SL {0} / Item {1} / Unknown loadflag = "{2}"'.format(SL_name, item_name, loadflag))
                raise CriticalError('DEBUG')

        # --- Add ROM to DB ---
        dataarea_dic['roms'].append(rom_dic)
        dataarea_num_roms += 1

        # --- DEBUG: Error if rom has merge attribute ---
        if 'merge' in dataarea_child.attrib:
            log_error('SL {0} / Item {1} / '.format(SL_name, item_name))
            log_error('ROM {0} has merge attribute'.format(dataarea_child.attrib['name']))
            raise CriticalError('DEBUG')

    return dataarea_num_roms

def _get_SL_dataarea_CHDs(SL_name, item_name, part_child, diskarea_dic):
    # >> Get CHDs in diskarea
    da_num_disks = 0
    for diskarea_child in part_child:
        disk_dic = { 'name' : '', 'sha1' : '' }
        disk_dic['name'] = diskarea_child.attrib['name'] if 'name' in diskarea_child.attrib else ''
        disk_dic['sha1'] = diskarea_child.attrib['sha1'] if 'sha1' in diskarea_child.attrib else ''
        diskarea_dic['disks'].append(disk_dic)
        da_num_disks += 1

    return da_num_disks

def _mame_load_SL_XML(xml_filename):
    __debug_xml_parser = False
    SLData = SLDataObj()

    # --- If file does not exist return empty dictionary ---
    if not os.path.isfile(xml_filename): return SLData
    (head, SL_name) = os.path.split(xml_filename)

    # --- Parse using cElementTree ---
    # If XML has errors (invalid characters, etc.) this will rais exception 'err'
    # log_debug('fs_load_SL_XML() Loading XML file "{0}"'.format(xml_filename))
    try:
        xml_tree = ET.parse(xml_filename)
    except:
        return SLData
    xml_root = xml_tree.getroot()
    SLData.display_name = xml_root.attrib['description']
    for root_element in xml_root:
        if __debug_xml_parser: print('Root child {0}'.format(root_element.tag))

        # >> Only process 'software' elements
        if root_element.tag != 'software': continue
        SL_item = fs_new_SL_ROM()
        SL_rom_list = []
        num_roms = 0
        num_disks = 0
        item_name = root_element.attrib['name']
        if 'cloneof' in root_element.attrib: SL_item['cloneof'] = root_element.attrib['cloneof']
        if 'romof' in root_element.attrib:
            log_error('{0} -> "romof" in root_element.attrib'.format(item_name))
            raise CriticalError('DEBUG')

        for rom_child in root_element:
            # >> By default read strings
            xml_text = rom_child.text if rom_child.text is not None else ''
            xml_tag  = rom_child.tag
            if __debug_xml_parser: print('{0} --> {1}'.format(xml_tag, xml_text))

            # --- Only pick tags we want ---
            if xml_tag == 'description' or xml_tag == 'year' or xml_tag == 'publisher':
                SL_item[xml_tag] = xml_text

            elif xml_tag == 'part':
                # <part name="cart" interface="_32x_cart">
                part_dic = fs_new_SL_ROM_part()
                part_dic['name'] = rom_child.attrib['name']
                part_dic['interface'] = rom_child.attrib['interface']
                SL_item['parts'].append(part_dic)
                SL_roms_dic = {
                    'part_name'      : rom_child.attrib['name'],
                    'part_interface' : rom_child.attrib['interface']
                }

                # --- Count number of <dataarea> and <diskarea> tags inside this <part tag> ---
                num_dataarea = 0
                num_diskarea = 0
                for part_child in rom_child:
                    if part_child.tag == 'dataarea':
                        dataarea_dic = { 'name' : part_child.attrib['name'], 'roms' : [] }
                        da_num_roms = _get_SL_dataarea_ROMs(SL_name, item_name, part_child, dataarea_dic)
                        if da_num_roms > 0:
                            # >> dataarea is valid ONLY if it contains valid ROMs
                            num_dataarea += 1
                            num_roms += da_num_roms
                        if 'dataarea' not in SL_roms_dic: SL_roms_dic['dataarea'] = []
                        SL_roms_dic['dataarea'].append(dataarea_dic)
                    elif part_child.tag == 'diskarea':
                        diskarea_dic = { 'name' : part_child.attrib['name'], 'disks' : [] }
                        da_num_disks = _get_SL_dataarea_CHDs(SL_name, item_name, part_child, diskarea_dic)
                        if da_num_disks > 0:
                            # >> diskarea is valid ONLY if it contains valid CHDs
                            num_diskarea += 1
                            num_disks += da_num_disks
                        if 'diskarea' not in SL_roms_dic: SL_roms_dic['diskarea'] = []
                        SL_roms_dic['diskarea'].append(diskarea_dic)
                    elif part_child.tag == 'feature':
                        pass
                    elif part_child.tag == 'dipswitch':
                        pass
                    else:
                        log_error('{0} -> Inside <part>, unrecognised tag <{1}>'.format(item_name, part_child.tag))
                        raise CriticalError('DEBUG')
                # --- Add ROMs/disks ---
                SL_rom_list.append(SL_roms_dic)

                # --- DEBUG/Research code ---
                # if num_dataarea > 1:
                #     log_error('{0} -> num_dataarea = {1}'.format(item_name, num_dataarea))
                #     raise CriticalError('DEBUG')
                # if num_diskarea > 1:
                #     log_error('{0} -> num_diskarea = {1}'.format(item_name, num_diskarea))
                #     raise CriticalError('DEBUG')
                # if num_dataarea and num_diskarea:
                #     log_error('{0} -> num_dataarea = {1}'.format(item_name, num_dataarea))
                #     log_error('{0} -> num_diskarea = {1}'.format(item_name, num_diskarea))
                #     raise CriticalError('DEBUG')

        # --- Finished processing of <software> element ---
        if num_roms:
            SL_item['hasROMs'] = True
            SL_item['status_ROM'] = '?'
            SLData.num_with_ROMs += 1
        else:
            SL_item['hasROMs'] = False
            SL_item['status_ROM'] = '-'
        if num_disks:
            SL_item['hasCHDs'] = True
            SL_item['status_CHD'] = '?'
            SLData.num_with_CHDs += 1
        else:
            SL_item['hasCHDs'] = False
            SL_item['status_CHD'] = '-'

        # >> Add <software> item (SL_item) to database and software ROM/CHDs to database
        SLData.roms[item_name] = SL_item
        SLData.SL_roms[item_name] = SL_rom_list

    return SLData

def _get_SL_parent_ROM_dic(parent_name, SL_ROMs):
    parent_rom_dic = {}
    for part_dic in SL_ROMs[parent_name]:
        if not 'dataarea' in part_dic: continue
        for dataarea_dic in part_dic['dataarea']:
            for rom_dic in dataarea_dic['roms']:
                parent_rom_dic[rom_dic['crc']] = rom_dic['name']

    return parent_rom_dic

def _get_SL_ROM_location(rom_set, SL_name, SL_item_name, rom_dic, SL_Items, parent_rom_dic):
    # Some SL invalid ROMs do not have name attribute (and not CRC and SHA1).
    # For those, set the location to empty.
    if not rom_dic['name']: return ''

    # In the SL ROM MERGED set all ROMs are stored in the parent ZIP file:
    #
    # PATH/32x/chaotix.zip/knuckles' chaotix (europe).bin
    # PATH/32x/chaotix.zip/chaotixju/chaotix ~ knuckles' chaotix (japan, usa).bin
    # PATH/32x/chaotix.zip/chaotixjup/knuckles' chaotix (prototype 214 - feb 14, 1995, 06.46).bin
    #
    if rom_set == 'MERGED':
        cloneof = SL_Items[SL_item_name]['cloneof']
        if cloneof:
            location = SL_name + '/' + cloneof + '/' + SL_item_name + '/' + rom_dic['name']
        else:
            location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']

    # In the SL ROM SPLIT set each item ROMs are in their own file:
    #
    # PATH/32x/chaotix.zip/knuckles' chaotix (europe).bin
    # PATH/32x/chaotixju.zip/chaotix ~ knuckles' chaotix (japan, usa).bin
    # PATH/32x/chaotixjup.zip/knuckles' chaotix (prototype 214 - feb 14, 1995, 06.46).bin
    #
    # NOTE that ClrMAME Pro (and hence PD torrents) do implicit ROM merging. SL XMLs do not have
    #      the merge attribute. However, an implicit ROM merge is done if a ROM with the same
    #      CRC is found in the parent. Implicit merging only affects clones. A dictionary
    #      of the parent ROMs with key the CRC hash and value the ROM name is required.
    #
    elif rom_set == 'SPLIT':
        cloneof = SL_Items[SL_item_name]['cloneof']
        if cloneof:
            if rom_dic['crc'] in parent_rom_dic:
                location = SL_name + '/' + cloneof + '/' + parent_rom_dic[rom_dic['crc']]
            else:
                location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']
        else:
            location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']

    elif rom_set == 'NONMERGED':
        location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']

    else:
        raise TypeError

    return location

def _get_SL_CHD_location(chd_set, SL_name, SL_item_name, disk_dic, SL_Items):
    # In the SL CHD MERGED set all CHDs are in the directory of the parent:
    #
    # ffant9  --> parent with 4 DISKS (v1.1)
    # ffant9a --> parent with 4 DISKS (v1.0)
    #
    # [parent traid]   PATH/psx/traid/tomb raider (usa) (v1.6).chd
    # [clone  traida]  PATH/psx/traid/tomb raider (usa) (v1.5).chd
    # [clone  traiddm] PATH/psx/traid/tr1.chd
    #
    if chd_set == 'MERGED':
        cloneof = SL_Items[SL_item_name]['cloneof']
        archive_name = cloneof if cloneof else SL_item_name
        location = SL_name + '/' + archive_name + '/' + disk_dic['name']

    # In the SL CHD SPLIT set CHD of each machine are in their own directory.
    # This is not confirmed since I do not have the PD DAT file for the SL CHD SPLIT set.
    #
    # [parent traid]   PATH/psx/traid/tomb raider (usa) (v1.6).chd
    # [clone  traida]  PATH/psx/traida/tomb raider (usa) (v1.5).chd
    # [clone  traiddm] PATH/psx/traiddm/tr1.chd
    #
    elif chd_set == 'SPLIT':
        location = SL_name + '/' + SL_rom + '/' + disk_dic['name']

    else:
        raise TypeError

    return location

# -------------------------------------------------------------------------------------------------
# SL_catalog = { 'name' : {
#     'display_name': u'', 'num_with_CHDs' : int, 'num_with_ROMs' : int, 'rom_DB_noext' : u'' }, ...
# }
#
# Saves:
# SL_INDEX_PATH,
# SL_MACHINES_PATH,
# SL_PCLONE_DIC_PATH,
# per-SL database                       (32x.json)
# per-SL database                       (32x_ROMs.json)
# per-SL ROM audit database             (32x_ROM_audit.json)
# per-SL item archives (ROMs and CHDs)  (32x_ROM_archives.json)
#
def mame_build_SoftwareLists_databases(PATHS, settings, control_dic, machines, machines_render):
    SL_dir_FN = FileName(settings['SL_hash_path'])
    log_debug('mame_build_SoftwareLists_databases() SL_dir_FN "{0}"'.format(SL_dir_FN.getPath()))

    # --- Scan all XML files in Software Lists directory and save SL and SL ROMs databases ---
    log_info('Processing Software List XML files ...')
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False
    pdialog_line1 = 'Building Sofware Lists ROM databases ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    SL_file_list = SL_dir_FN.scanFilesInPath('*.xml')
    # >> DEBUG code for development, only process first SL file (32x).
    # SL_file_list = [ sorted(SL_file_list)[0] ]
    total_SL_files = len(SL_file_list)
    num_SL_with_ROMs = 0
    num_SL_with_CHDs = 0
    SL_catalog_dic = {}
    processed_files = 0
    for file in sorted(SL_file_list):
        # >> Progress dialog
        FN = FileName(file)
        pDialog.update((processed_files*100) // total_SL_files, pdialog_line1, 'File {0}'.format(FN.getBase()))

        # >> Open software list XML and parse it. Then, save data fields we want in JSON.
        # log_debug('mame_build_SoftwareLists_databases() Processing "{0}"'.format(file))
        SL_path_FN = FileName(file)
        SLData = _mame_load_SL_XML(SL_path_FN.getPath())
        fs_write_JSON_file(PATHS.SL_DB_DIR.pjoin(FN.getBase_noext() + '.json').getPath(),
                           SLData.roms, verbose = False)
        fs_write_JSON_file(PATHS.SL_DB_DIR.pjoin(FN.getBase_noext() + '_ROMs.json').getPath(),
                           SLData.SL_roms, verbose = False)

        # >> Add software list to catalog
        num_SL_with_ROMs += SLData.num_with_ROMs
        num_SL_with_CHDs += SLData.num_with_CHDs
        SL = {'display_name'  : SLData.display_name, 
              'num_with_ROMs' : SLData.num_with_ROMs,
              'num_with_CHDs' : SLData.num_with_CHDs,
              'rom_DB_noext'  : FN.getBase_noext()
        }
        SL_catalog_dic[FN.getBase_noext()] = SL

        # >> Update progress
        processed_files += 1
    fs_write_JSON_file(PATHS.SL_INDEX_PATH.getPath(), SL_catalog_dic)
    pDialog.update((processed_files*100) // total_SL_files, pdialog_line1, ' ')

    # --- Make the SL ROM/CHD unified Audit databases ---
    log_info('Building Software List ROM Audit database ...')
    rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][settings['SL_rom_set']]
    chd_set = ['MERGED', 'SPLIT', 'NONMERGED'][settings['SL_chd_set']]
    log_info('mame_build_SoftwareLists_databases() SL ROM set is {0}'.format(rom_set))
    log_info('mame_build_SoftwareLists_databases() SL CHD set is {0}'.format(chd_set))
    pdialog_line1 = 'Building Software List ROM Audit database ...'
    pDialog.update(0, pdialog_line1)
    total_files = len(SL_file_list)
    processed_files = 0
    stats_audit_SL_items_runnable = 0
    stats_audit_SL_items_with_arch = 0
    stats_audit_SL_items_with_arch_ROM = 0
    stats_audit_SL_items_with_CHD = 0
    for file in sorted(SL_file_list):
        # >> Update progress
        FN = FileName(file)
        SL_name = FN.getBase_noext()
        pDialog.update((processed_files*100) // total_files, pdialog_line1, 'File {0}'.format(FN.getBase()))

        # >> Filenames of the databases
        # log_debug('mame_build_SoftwareLists_databases() Processing "{0}"'.format(file))
        SL_Items_DB_FN = PATHS.SL_DB_DIR.pjoin(FN.getBase_noext() + '.json')        
        SL_ROMs_DB_FN = PATHS.SL_DB_DIR.pjoin(FN.getBase_noext() + '_ROMs.json')
        SL_ROM_Audit_DB_FN = PATHS.SL_DB_DIR.pjoin(FN.getBase_noext() + '_ROM_audit.json')
        SL_Soft_Archives_DB_FN = PATHS.SL_DB_DIR.pjoin(FN.getBase_noext() + '_ROM_archives.json')
        SL_Items = fs_load_JSON_file_dic(SL_Items_DB_FN.getPath(), verbose = False)
        SL_ROMs = fs_load_JSON_file_dic(SL_ROMs_DB_FN.getPath(), verbose = False)

        # --- First add the SL item ROMs to the audit database ---
        SL_Audit_ROMs_dic = {}        
        for SL_item_name in SL_ROMs:
            # >> If SL item is a clone then create parent_rom_dic. This is only needed in the
            # >> SPLIT set, so current code is a bit inefficient for other sets.
            # >> key : CRC -> value : rom name
            cloneof = SL_Items[SL_item_name]['cloneof']
            if cloneof:
                parent_rom_dic = _get_SL_parent_ROM_dic(cloneof, SL_ROMs)
            else:
                parent_rom_dic = {}

            # >> Iterate Parts in a SL Software item. Then iterate dataareas on each part.
            # >> Finally, iterate ROM on each dataarea.
            set_roms = []
            for part_dic in SL_ROMs[SL_item_name]:
                if not 'dataarea' in part_dic: continue
                for dataarea_dic in part_dic['dataarea']:
                    for rom_dic in dataarea_dic['roms']:
                        location = _get_SL_ROM_location(rom_set, SL_name, SL_item_name, rom_dic, SL_Items, parent_rom_dic)
                        rom_audit_dic = fs_new_SL_ROM_audit_dic()
                        rom_audit_dic['type']     = ROM_TYPE_ROM
                        rom_audit_dic['name']     = rom_dic['name']
                        rom_audit_dic['size']     = rom_dic['size']
                        rom_audit_dic['crc']      = rom_dic['crc']
                        rom_audit_dic['location'] = location
                        set_roms.append(rom_audit_dic)
            SL_Audit_ROMs_dic[SL_item_name] = set_roms

        # --- Second add the SL item CHDs to the audit database ---
        for SL_item_name in SL_ROMs:
            set_chds = []
            for part_dic in SL_ROMs[SL_item_name]:
                if not 'diskarea' in part_dic: continue
                for diskarea_dic in part_dic['diskarea']:
                    for disk_dic in diskarea_dic['disks']:
                        location = _get_SL_CHD_location(chd_set, SL_name, SL_item_name, disk_dic, SL_Items)
                        disk_audit_dic = fs_new_SL_DISK_audit_dic()
                        disk_audit_dic['type']     = ROM_TYPE_DISK
                        disk_audit_dic['name']     = disk_dic['name']
                        disk_audit_dic['sha1']     = disk_dic['sha1']
                        disk_audit_dic['location'] = location
                        set_chds.append(disk_audit_dic)
            # >> Extend ROM list with CHDs.
            if SL_item_name in SL_Audit_ROMs_dic:
                SL_Audit_ROMs_dic[SL_item_name].extend(set_chds)
            else:
                SL_Audit_ROMs_dic[SL_item_name] =  set_chds

        # --- Machine archives ---
        # >> There is not ROMs and CHDs sets for Software List Items (not necessary).
        SL_Item_Archives_dic = {}
        for SL_item_name in SL_Audit_ROMs_dic:
            rom_list = SL_Audit_ROMs_dic[SL_item_name]
            machine_rom_archive_set = set()
            machine_chd_archive_set = set()
            # --- Iterate ROMs/CHDs ---
            for rom in rom_list:
                if rom['type'] == ROM_TYPE_DISK:
                    # >> Skip invalid CHDs
                    if not rom['sha1']: continue
                    chd_name = rom['location']
                    machine_chd_archive_set.add(chd_name)
                else:
                    # >> Skip invalid ROMs
                    if not rom['crc']: continue
                    rom_str_list = rom['location'].split('/')
                    zip_name = rom_str_list[0] + '/' + rom_str_list[1]
                    machine_rom_archive_set.add(zip_name)
            SL_Item_Archives_dic[SL_item_name] = {
                'ROMs' : list(machine_rom_archive_set),
                'CHDs' : list(machine_chd_archive_set)
            }
            # --- SL Audit database statistics ---
            stats_audit_SL_items_runnable += 1
            if SL_Item_Archives_dic[SL_item_name]['ROMs'] or SL_Item_Archives_dic[SL_item_name]['CHDs']:
                stats_audit_SL_items_with_arch += 1
            if SL_Item_Archives_dic[SL_item_name]['ROMs']: stats_audit_SL_items_with_arch_ROM += 1
            if SL_Item_Archives_dic[SL_item_name]['CHDs']: stats_audit_SL_items_with_CHD += 1

        # --- Save databases ---
        fs_write_JSON_file(SL_ROM_Audit_DB_FN.getPath(), SL_Audit_ROMs_dic, verbose = False)
        fs_write_JSON_file(SL_Soft_Archives_DB_FN.getPath(), SL_Item_Archives_dic, verbose = False)
        # >> Update progress
        processed_files += 1
    pDialog.update((processed_files*100) // total_files, pdialog_line1, ' ')

    # --- Make SL Parent/Clone databases ---
    log_info('Building Software List PClone list ...')
    pdialog_line1 = 'Building Software List PClone list ...'
    pDialog.update(0, pdialog_line1)
    total_files = len(SL_catalog_dic)
    processed_files = 0
    SL_PClone_dic = {}
    total_SL_XML_files = 0
    total_SL_software_items = 0
    for sl_name in sorted(SL_catalog_dic):
        pDialog.update((processed_files*100) // total_files, pdialog_line1, 'Software List {0}'.format(sl_name))
        total_SL_XML_files += 1
        pclone_dic = {}
        SL_database_FN = PATHS.SL_DB_DIR.pjoin(sl_name + '.json')
        ROMs = fs_load_JSON_file_dic(SL_database_FN.getPath(), verbose = False)
        for rom_name in ROMs:
            total_SL_software_items += 1
            ROM = ROMs[rom_name]
            if ROM['cloneof']:
                parent_name = ROM['cloneof']
                if parent_name not in pclone_dic: pclone_dic[parent_name] = []
                pclone_dic[parent_name].append(rom_name)
            else:
                if rom_name not in pclone_dic: pclone_dic[rom_name] = []
        SL_PClone_dic[sl_name] = pclone_dic
        # >> Update progress
        processed_files += 1
    fs_write_JSON_file(PATHS.SL_PCLONE_DIC_PATH.getPath(), SL_PClone_dic)
    pDialog.update((processed_files*100) // total_files, pdialog_line1, ' ')

    # --- Make a list of machines that can launch each SL ---
    log_info('Making Software List machine list ...')
    pdialog_line1 = 'Building Software List machine list ...'
    pDialog.update(0, pdialog_line1)
    total_SL = len(SL_catalog_dic)
    processed_SL = 0
    SL_machines_dic = {}
    for SL_name in sorted(SL_catalog_dic):
        pDialog.update((processed_SL*100) // total_SL, pdialog_line1, 'Software List {0}'.format(SL_name))
        SL_machine_list = []
        for machine_name in machines:
            # if not machines[machine_name]['softwarelists']: continue
            for machine_SL_name in machines[machine_name]['softwarelists']:
                if machine_SL_name == SL_name:
                    SL_machine_dic = {'machine'     : machine_name,
                                      'description' : machines_render[machine_name]['description'],
                                      'devices'     : machines[machine_name]['devices']}
                    SL_machine_list.append(SL_machine_dic)
        SL_machines_dic[SL_name] = SL_machine_list

        # >> Update progress
        processed_SL += 1
    fs_write_JSON_file(PATHS.SL_MACHINES_PATH.getPath(), SL_machines_dic)
    pDialog.update((processed_SL*100) // total_SL, pdialog_line1, ' ')

    # --- Empty SL asset DB ---
    log_info('Making Software List (empty) asset databases ...')
    pdialog_line1 = 'Building Software List (empty) asset databases ...'
    pDialog.update(0, pdialog_line1)
    total_SL = len(SL_catalog_dic)
    processed_SL = 0
    SL_machines_dic = {}
    for SL_name in sorted(SL_catalog_dic):
        # --- Update progress ---
        pDialog.update((processed_SL*100) // total_SL, pdialog_line1, 'Software List {0}'.format(SL_name))

        # --- Load SL databases ---
        file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '.json'
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
        SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)
        assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)

        # --- Second pass: substitute artwork ---
        SL_assets_dic = {}
        for rom_key in sorted(SL_roms):
            SL_assets_dic[rom_key] = fs_new_SL_asset()

        # --- Write SL asset JSON ---
        fs_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic, verbose = False)

        # >> Update progress
        processed_SL += 1
    pDialog.update((processed_SL*100) // total_SL, pdialog_line1, ' ')
    pDialog.close()

    # --- Create properties database with default values ---
    # --- Make SL properties DB ---
    # >> Allows customisation of every SL list window
    # >> Not used at the moment -> Global properties
    # SL_properties_dic = {}
    # for sl_name in SL_catalog_dic:
    #     # 'vm' : VIEW_MODE_NORMAL or VIEW_MODE_ALL
    #     prop_dic = {'vm' : VIEW_MODE_NORMAL}
    #     SL_properties_dic[sl_name] = prop_dic
    # fs_write_JSON_file(PATHS.SL_MACHINES_PROP_PATH.getPath(), SL_properties_dic)
    # log_info('SL_properties_dic has {0} items'.format(len(SL_properties_dic)))

    # >> One of the MAME catalogs has changed, and so the property names.
    # >> Not used at the moment -> Global properties
    # mame_properties_dic = {}
    # for catalog_name in CATALOG_NAME_LIST:
    #     catalog_dic = fs_get_cataloged_dic_parents(PATHS, catalog_name)
    #     for category_name in sorted(catalog_dic):
    #         prop_key = '{0} - {1}'.format(catalog_name, category_name)
    #         mame_properties_dic[prop_key] = {'vm' : VIEW_MODE_NORMAL}
    # fs_write_JSON_file(PATHS.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    # log_info('mame_properties_dic has {0} items'.format(len(mame_properties_dic)))

    # -----------------------------------------------------------------------------
    # Update MAME control dictionary
    # -----------------------------------------------------------------------------
    # --- SL item database ---
    change_control_dic(control_dic, 'stats_SL_XML_files', total_SL_XML_files)
    change_control_dic(control_dic, 'stats_SL_software_items', total_SL_software_items)
    change_control_dic(control_dic, 'stats_SL_items_with_ROMs', num_SL_with_ROMs)
    change_control_dic(control_dic, 'stats_SL_items_with_CHDs', num_SL_with_CHDs)

    # --- SL audit database statistics ---
    change_control_dic(control_dic, 'stats_audit_SL_items_runnable', stats_audit_SL_items_runnable)
    change_control_dic(control_dic, 'stats_audit_SL_items_with_arch', stats_audit_SL_items_with_arch)
    change_control_dic(control_dic, 'stats_audit_SL_items_with_arch_ROM', stats_audit_SL_items_with_arch_ROM)
    change_control_dic(control_dic, 'stats_audit_SL_items_with_CHD', stats_audit_SL_items_with_CHD)

    # --- SL build timestamp ---
    change_control_dic(control_dic, 't_SL_DB_build', time.time())

# -------------------------------------------------------------------------------------------------
# ROM/CHD and asset scanner
# -------------------------------------------------------------------------------------------------
# Does not save any file. assets_dic and control_dic mutated by assigment.
def mame_scan_MAME_ROMs(PATHS, settings, control_dic,
                        machines, machines_render, assets_dic,
                        machine_archives_dic, ROM_archive_list, CHD_archive_list,
                        ROM_path_FN, CHD_path_FN, Samples_path_FN,
                        scan_CHDs, scan_Samples):

    # --- Create a cache of assets ---
    # >> misc_add_file_cache() creates a set with all files in a given directory.
    # >> That set is stored in a function internal cache associated with the path.
    # >> Files in the cache can be searched with misc_search_file_cache()
    ROM_path_str = ROM_path_FN.getPath()
    CHD_path_str = CHD_path_FN.getPath()
    Samples_path_str = Samples_path_FN.getPath()
    STUFF_PATH_LIST = [ROM_path_str, CHD_path_str, Samples_path_str]
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False
    pDialog.create('Advanced MAME Launcher', 'Scanning files in ROM/CHD/Samples directories ...')
    pDialog.update(0)
    for i, asset_dir in enumerate(STUFF_PATH_LIST):
        misc_add_file_cache(asset_dir)
        pDialog.update((100*(i+1))/len(STUFF_PATH_LIST))
    pDialog.close()

    # --- Scan ROMs ---
    pDialog.create('Advanced MAME Launcher', 'Scanning MAME machine archives (ROMs and CHDs) ...')
    total_machines = len(machines_render)
    processed_machines = 0
    scan_ROM_machines_total = 0
    scan_ROM_machines_have = 0
    scan_ROM_machines_missing = 0
    scan_CHD_machines_total = 0
    scan_CHD_machines_have = 0
    scan_CHD_machines_missing = 0
    r_full_list = []
    r_have_list = []
    r_miss_list = []
    for key in sorted(machines_render):
        pDialog.update((processed_machines*100) // total_machines)

        # --- Initialise machine ---
        # log_info('_command_setup_plugin() Checking machine {0}'.format(key))
        if machines_render[key]['isDevice']: continue # Skip Devices
        m_have_str_list = []
        m_miss_str_list = []

        # --- ROMs ---
        rom_list = machine_archives_dic[key]['ROMs']
        if rom_list:
            have_rom_list = [False] * len(rom_list)
            for i, rom in enumerate(rom_list):
                # --- Old code ---
                # archive_name = rom + '.zip'
                # ROM_FN = ROM_path_FN.pjoin(archive_name)
                # if ROM_FN.exists():
                # --- New code using file cache ---
                ROM_FN = misc_search_file_cache(ROM_path_str, rom, MAME_ROM_EXTS)
                if ROM_FN:
                    have_rom_list[i] = True
                    m_have_str_list.append('HAVE ROM {0}'.format(rom))
                else:
                    m_miss_str_list.append('MISS ROM {0}'.format(rom))
            scan_ROM_machines_total += 1
            if all(have_rom_list):
                # --- All ZIP files required to run this machine exist ---
                ROM_flag = 'R'
                scan_ROM_machines_have += 1
            else:
                ROM_flag = 'r'
                scan_ROM_machines_missing += 1
        else:
            ROM_flag = '-'
        fs_set_ROM_flag(assets_dic[key], ROM_flag)

        # --- Disks ---
        # >> Machines with CHDs: 2spicy, sfiii2
        chd_list = machine_archives_dic[key]['CHDs']
        if chd_list and scan_CHDs:
            scan_CHD_machines_total += 1
            has_chd_list = [False] * len(chd_list)
            for idx, chd_name in enumerate(chd_list):
                # --- Old code ---
                # CHD_FN = CHD_path_FN.pjoin(chd_name)
                # if CHD_FN.exists():
                # --- New code using file cache ---
                # log_debug('Testing CHD "{0}"'.format(chd_name))
                CHD_FN = misc_search_file_cache(CHD_path_str, chd_name, MAME_CHD_EXTS)
                if CHD_FN:
                    has_chd_list[idx] = True
                    m_have_str_list.append('HAVE CHD {0}'.format(chd_name))
                else:
                    m_miss_str_list.append('MISS CHD {0}'.format(chd_name))
            if all(has_chd_list):
                CHD_flag = 'C'
                scan_CHD_machines_have += 1
            else:
                CHD_flag = 'c'
                scan_CHD_machines_missing += 1
        elif chd_list and not scan_CHDs:
            scan_CHD_machines_total += 1
            CHD_flag = 'c'
            scan_CHD_machines_missing += 1
        else:
            CHD_flag = '-'
        fs_set_CHD_flag(assets_dic[key], CHD_flag)

        # >> Build FULL, HAVE and MISSING reports.
        r_full_list.append('Machine {0} -- "{1}"'.format(key, machines_render[key]['description']))
        if machines_render[key]['cloneof']:
            cloneof = machines_render[key]['cloneof']
            r_full_list.append('cloneof {0} ({1})'.format(cloneof, machines_render[cloneof]['description']))
        if not rom_list and not chd_list:
            r_full_list.append('Machine has no ROMs and/or CHDs')
        else:
            r_full_list.extend(m_have_str_list)
            r_full_list.extend(m_miss_str_list)
        r_full_list.append('')

        # >> Also including missing ROMs/CHDs if any.
        if m_have_str_list:
            r_have_list.append('Machine {0} -- "{1}"'.format(key, machines_render[key]['description']))
            if machines_render[key]['cloneof']:
                cloneof = machines_render[key]['cloneof']
                r_have_list.append('cloneof {0} ({1})'.format(cloneof, machines_render[cloneof]['description']))
            r_have_list.extend(m_have_str_list)
            # if m_miss_str_list: r_have_list.extend(m_miss_str_list)
            r_have_list.extend(m_miss_str_list)
            r_have_list.append('')

        # >> Also including have ROMs/CHDs if any.
        if m_miss_str_list:
            r_miss_list.append('Machine {0} -- "{1}"'.format(key, machines_render[key]['description']))
            if machines_render[key]['cloneof']:
                cloneof = machines_render[key]['cloneof']
                r_miss_list.append('cloneof {0} ({1})'.format(cloneof, machines_render[cloneof]['description']))
            # if m_have_str_list: r_miss_list.extend(m_have_str_list)
            r_miss_list.extend(m_have_str_list)
            r_miss_list.extend(m_miss_str_list)
            r_miss_list.append('')

        # >> Progress dialog
        processed_machines += 1
    pDialog.close()

    # >> Write MAME scanner reports
    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), 'w') as file:
        report_slist = [
            '*** Advanced MAME Launcher MAME machines scanner report ***',
            'This report shows all the scanned MAME machines.\n',
            'MAME ROM path = "{0}"'.format(ROM_path_str),
            'MAME CHD path = "{0}"'.format(CHD_path_str),
            '',
        ]
        report_slist.extend(r_full_list)
        file.write('\n'.join(report_slist).encode('utf-8'))

    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), 'w') as file:
        report_slist = [
            '*** Advanced MAME Launcher MAME machines scanner report ***',
            'This reports shows HAVE MAME machines with ROM ZIPs and/or CHDs.\n',
            'MAME ROM path = "{0}"'.format(ROM_path_str),
            'MAME CHD path = "{0}"'.format(CHD_path_str),
            '',
        ]
        if not r_have_list:
            r_have_list.append('Ouch!!! You do not have any ROM ZIP files and/or CHDs.')
        report_slist.extend(r_have_list)
        file.write('\n'.join(report_slist).encode('utf-8'))

    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), 'w') as file:
        report_slist = [
            '*** Advanced MAME Launcher MAME machines scanner report ***',
            'This reports shows MISSING MAME machines with ROM ZIPs and/or CHDs.\n',
            'MAME ROM path = "{0}"'.format(ROM_path_str),
            'MAME CHD path = "{0}"'.format(CHD_path_str),
            '',
        ]
        if not r_miss_list:
            r_miss_list.append('Congratulations!!! You have no missing ROM ZIP and/or CHDs files.')
        report_slist.extend(r_miss_list)
        file.write('\n'.join(report_slist).encode('utf-8'))

    # --- ROM ZIP file list ---
    pDialog = xbmcgui.DialogProgress()
    pDialog_canceled = False
    pDialog.create('Advanced MAME Launcher', 'Scanning MAME archive ROMs ...')
    total_machines = len(machines_render)
    processed_machines = 0
    scan_ZIP_files_total = 0
    scan_ZIP_files_have = 0
    scan_ZIP_files_missing = 0
    r_list = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This report shows all missing MAME machine ROM ZIPs',
        'Each missing ROM ZIP appears only once, but more than one machine may be unrunnable.\n',
        'MAME ROM path = "{0}"'.format(ROM_path_str),
        'MAME CHD path = "{0}"'.format(CHD_path_str),
        '',
    ]
    for rom_name in ROM_archive_list:
        scan_ZIP_files_total += 1
        ROM_FN = misc_search_file_cache(ROM_path_str, rom_name, MAME_ROM_EXTS)
        if ROM_FN:
            scan_ZIP_files_have += 1
        else:
            scan_ZIP_files_missing += 1
            r_list.append('Missing ROM {0}'.format(rom_name))
        # >> Progress dialog
        processed_machines += 1
        pDialog.update((processed_machines*100) // total_machines)
    pDialog.close()
    # >> Write report
    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath(), 'w') as file:
        if scan_ZIP_files_missing == 0:
            r_list.append('Congratulations!!! You have no missing ROM ZIP files.')
        file.write('\n'.join(r_list).encode('utf-8'))

    # --- CHD file list ---
    pDialog.create('Advanced MAME Launcher', 'Scanning MAME CHDs ...')
    total_machines = len(machines_render)
    processed_machines = 0
    scan_CHD_files_total = 0
    scan_CHD_files_have = 0
    scan_CHD_files_missing = 0
    r_list = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This report shows all missing MAME machine CHDs',
        'Each missing CHD appears only once, but more than one machine may be unrunnable.\n',
        'MAME ROM path = "{0}"'.format(ROM_path_str),
        'MAME CHD path = "{0}"'.format(CHD_path_str),
        '',
    ]
    for chd_name in CHD_archive_list:
        scan_CHD_files_total += 1
        CHD_FN = misc_search_file_cache(CHD_path_str, chd_name, MAME_CHD_EXTS)
        if CHD_FN:
            scan_CHD_files_have += 1
        else:
            scan_CHD_files_missing += 1
            r_list.append('Missing CHD {0}'.format(chd_name))
        # >> Progress dialog
        processed_machines += 1
        pDialog.update((processed_machines*100) // total_machines)
    pDialog.close()
    # >> Write report
    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath(), 'w') as file:
        if scan_CHD_files_missing == 0:
            r_list.append('Congratulations!!! You have no missing CHDs.')
        file.write('\n'.join(r_list).encode('utf-8'))

    # --- Scan Samples ---
    pDialog.create('Advanced MAME Launcher', 'Scanning MAME Samples ...')
    total_machines = len(machines_render)
    processed_machines = 0
    scan_Samples_have = 0
    scan_Samples_missing = 0
    scan_Samples_total = 0
    r_have_list = []
    r_miss_list = []
    for key in sorted(machines):
        m_have_str_list = []
        m_miss_str_list = []
        if machines[key]['sampleof']:
            scan_Samples_total += 1
            if scan_Samples:
                sample = machines[key]['sampleof']
                Sample_FN = misc_search_file_cache(Samples_path_str, sample, MAME_SAMPLE_EXTS)
                if Sample_FN:
                    Sample_flag = 'S'
                    scan_Samples_have += 1
                    m_have_str_list.append('Have sample {0}'.format(sample))
                else:
                    Sample_flag = 's'
                    scan_Samples_missing += 1
                    m_miss_str_list.append('Missing sample {0}'.format(sample))
            else:
                Sample_flag = 's'
                scan_Samples_missing += 1
        else:
            Sample_flag = '-'
        fs_set_Sample_flag(assets_dic[key], Sample_flag)
        # >> Build HAVE and MISSING reports.
        if m_have_str_list:
            r_have_list.append('Machine {0} -- "{1}"'.format(key, machines_render[key]['description']))
            if machines_render[key]['cloneof']:
                cloneof = machines_render[key]['cloneof']
                r_have_list.append('cloneof {0} ({1})'.format(cloneof, machines_render[cloneof]['description']))
            r_have_list.extend(m_have_str_list)
            if m_miss_str_list: r_have_list.extend(m_miss_str_list)
            r_have_list.append('')
        if m_miss_str_list:
            r_miss_list.append('Machine {0} -- "{1}"'.format(key, machines_render[key]['description']))
            if machines_render[key]['cloneof']:
                cloneof = machines_render[key]['cloneof']
                r_miss_list.append('cloneof {0} ({1})'.format(cloneof, machines_render[cloneof]['description']))
            if m_have_str_list: r_miss_list.extend(m_have_str_list)
            r_miss_list.extend(m_miss_str_list)
            r_miss_list.append('')
        # >> Progress dialog
        processed_machines += 1
        pDialog.update((processed_machines*100) // total_machines)
    pDialog.close()
    # >> Write reports
    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_SAMP_HAVE_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_SAMP_HAVE_PATH.getPath(), 'w') as file:
        file.write('\n'.join(r_have_list).encode('utf-8'))
    log_info('Writing report "{0}"'.format(PATHS.REPORT_MAME_SCAN_SAMP_MISS_PATH.getPath()))
    with open(PATHS.REPORT_MAME_SCAN_SAMP_MISS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(r_miss_list).encode('utf-8'))

    # --- Update statistics ---
    change_control_dic(control_dic, 'scan_ROM_ZIP_files_total', scan_ZIP_files_total)
    change_control_dic(control_dic, 'scan_ROM_ZIP_files_have', scan_ZIP_files_have)
    change_control_dic(control_dic, 'scan_ROM_ZIP_files_missing', scan_ZIP_files_missing)
    change_control_dic(control_dic, 'scan_CHD_files_total', scan_CHD_files_total)
    change_control_dic(control_dic, 'scan_CHD_files_have', scan_CHD_files_have)
    change_control_dic(control_dic, 'scan_CHD_files_missing', scan_CHD_files_missing)
    change_control_dic(control_dic, 'scan_machine_archives_ROM_total', scan_ROM_machines_total)
    change_control_dic(control_dic, 'scan_machine_archives_ROM_have', scan_ROM_machines_have)
    change_control_dic(control_dic, 'scan_machine_archives_ROM_missing', scan_ROM_machines_missing)
    change_control_dic(control_dic, 'scan_machine_archives_CHD_total', scan_CHD_machines_total)
    change_control_dic(control_dic, 'scan_machine_archives_CHD_have', scan_CHD_machines_have)
    change_control_dic(control_dic, 'scan_machine_archives_CHD_missing', scan_CHD_machines_missing)
    change_control_dic(control_dic, 'scan_Samples_total', scan_Samples_total)
    change_control_dic(control_dic, 'scan_Samples_have', scan_Samples_have)
    change_control_dic(control_dic, 'scan_Samples_missing', scan_Samples_missing)
    change_control_dic(control_dic, 't_MAME_ROMs_scan', time.time())

# -------------------------------------------------------------------------------------------------
# Saves SL JSON databases, MAIN_CONTROL_PATH.
def mame_scan_SL_ROMs(PATHS, control_dic, SL_catalog_dic, SL_hash_dir_FN, SL_ROM_dir_FN, scan_SL_CHDs, SL_CHD_path_FN):

    # --- Add files to cache ---
    SL_ROM_path_str = SL_ROM_dir_FN.getPath()
    SL_CHD_path_str = SL_CHD_path_FN.getPath()
    pDialog = xbmcgui.DialogProgress()
    pdialog_line1 = 'Caching Sofware Lists ROMs/CHDs ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(0, pdialog_line1, 'Scanning SL ROM path')
    misc_add_file_cache(SL_ROM_path_str, verbose = True)
    pDialog.update(75, pdialog_line1, 'Scanning SL CHD path')
    misc_add_file_cache(SL_CHD_path_str, verbose = True)
    pDialog.update(100, pdialog_line1, ' ')
    pDialog.close()

    # --- SL ROM ZIP archives and CHDs ---
    # Traverse the Software Lists, check if ROMs ZIPs and CHDs exists for every SL item, 
    # update and save database.
    pdialog_line1 = 'Scanning Sofware Lists ROMs/CHDs ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(0)
    total_files = len(SL_catalog_dic)
    processed_files = 0
    SL_ROMs_have = 0
    SL_ROMs_missing = 0
    SL_ROMs_total = 0
    SL_CHDs_have = 0
    SL_CHDs_missing = 0
    SL_CHDs_total = 0
    r_all_list = []
    r_have_list = []
    r_miss_list = []
    for SL_name in sorted(SL_catalog_dic):
        # >> Progress dialog
        update_number = (processed_files*100) // total_files
        pDialog.update(update_number, pdialog_line1, 'Software List {0} ...'.format(SL_name))

        # >> Load SL databases
        SL_DB_FN = SL_hash_dir_FN.pjoin(SL_name + '.json')
        SL_SOFT_ARCHIVES_DB_FN = SL_hash_dir_FN.pjoin(SL_name + '_ROM_archives.json')
        sl_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)
        soft_archives = fs_load_JSON_file_dic(SL_SOFT_ARCHIVES_DB_FN.getPath(), verbose = False)

        # >> Scan
        for rom_key in sorted(sl_roms):
            m_have_str_list = []
            m_miss_str_list = []
            rom = sl_roms[rom_key]

            # --- ROMs ---
            rom_list = soft_archives[rom_key]['ROMs']
            if rom_list:
                have_rom_list = [False] * len(rom_list)
                for i, rom_file in enumerate(rom_list):
                    SL_ROMs_total += 1
                    SL_ROM_FN = misc_search_file_cache(SL_ROM_path_str, rom_file, SL_ROM_EXTS)
                    ROM_path = SL_ROM_path_str + '/' + rom_file
                    if SL_ROM_FN:
                        have_rom_list[i] = True
                        m_have_str_list.append('Have SL ROM {0}'.format(ROM_path))
                    else:
                        m_miss_str_list.append('Missing SL ROM {0}'.format(ROM_path))
                if all(have_rom_list):
                    rom['status_ROM'] = 'R'
                    SL_ROMs_have += 1
                else:
                    rom['status_ROM'] = 'r'
                    SL_ROMs_missing += 1
            else:
                rom['status_ROM'] = '-'

            # --- Disks ---
            chd_list = soft_archives[rom_key]['CHDs']
            if chd_list:
                if scan_SL_CHDs:
                    SL_CHDs_total += 1
                    has_chd_list = [False] * len(chd_list)
                    for idx, chd_file in enumerate(chd_list):
                        SL_CHD_FN = misc_search_file_cache(SL_CHD_path_str, chd_file, SL_CHD_EXTS)
                        CHD_path = SL_CHD_path_str + '/' + chd_file
                        if SL_CHD_FN:
                            has_chd_list[idx] = True
                            m_have_str_list.append('Have SL CHD {0}'.format(CHD_path))
                        else:
                            m_miss_str_list.append('Missing SL CHD {0}'.format(CHD_path))
                    if all(has_chd_list):
                        rom['status_CHD'] = 'C'
                        SL_CHDs_have += 1
                    else:
                        rom['status_CHD'] = 'c'
                        SL_CHDs_missing += 1
                else:
                    rom['status_CHD'] = 'c'
                    SL_CHDs_missing += 1
            else:
                rom['status_CHD'] = '-'

            # --- Build report ---
            description = sl_roms[rom_key]['description']
            clone_name = sl_roms[rom_key]['cloneof']
            r_all_list.append('SL {0} Software item {1} "{2}"'.format(SL_name, rom_key, description))
            if clone_name:
                clone_description = sl_roms[clone_name]['description']
                r_all_list.append('cloneof {0} "{1}"'.format(clone_name, clone_description))
            if m_have_str_list:
                r_all_list.extend(m_have_str_list)
            if m_miss_str_list:
                r_all_list.extend(m_miss_str_list)
            r_all_list.append('')

            if m_have_str_list:
                r_have_list.append('SL {0} Software item {1} "{2}"'.format(SL_name, rom_key, description))
                if clone_name:
                    r_have_list.append('cloneof {0} "{1}"'.format(clone_name, clone_description))
                r_have_list.extend(m_have_str_list)
                if m_miss_str_list: r_have_list.extend(m_miss_str_list)
                r_have_list.append('')

            if m_miss_str_list:
                r_miss_list.append('SL {0} Software item {1} "{2}"'.format(SL_name, rom_key, description))
                if clone_name:
                    r_miss_list.append('cloneof {0} "{1}"'.format(clone_name, clone_description))
                r_miss_list.extend(m_miss_str_list)
                if m_have_str_list: r_miss_list.extend(m_have_str_list)
                r_miss_list.append('')

        # >> Save SL database to update flags.
        fs_write_JSON_file(SL_DB_FN.getPath(), sl_roms, verbose = False)
        # >> Increment file count
        processed_files += 1
    pDialog.update(update_number, pdialog_line1, ' ')
    pDialog.close()

    # >> Write SL scanner reports
    log_info('Writing SL ROM ZIPs/CHDs FULL report')
    log_info('Report file "{0}"'.format(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath()))
    with open(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), 'w') as file:
        file.write('*** Advanced MAME Launcher Software Lists scanner report ***\n'.encode('utf-8'))
        file.write('This report shows all the scanned SL items\n'.encode('utf-8'))
        file.write('\n'.encode('utf-8'))
        if r_all_list:
            file.write('\n'.join(r_all_list).encode('utf-8'))
        else:
            raise TypeError

    log_info('Writing SL ROM ZIPs and/or CHDs HAVE report')
    log_info('Report file "{0}"'.format(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath()))
    with open(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), 'w') as file:
        file.write('*** Advanced MAME Launcher Software Lists scanner report ***\n'.encode('utf-8'))
        file.write('This reports shows the SL items with ROM ZIPs and/or CHDs with HAVE status\n'.encode('utf-8'))
        file.write('\n'.encode('utf-8'))
        if r_have_list:
            file.write('\n'.join(r_have_list).encode('utf-8'))
        else:
            file.write('You do not have any ROM ZIP or CHD files!\n'.encode('utf-8'))

    log_info('Writing SL ROM ZIPs/CHDs MISS report')
    log_info('Report file "{0}"'.format(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath()))
    with open(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), 'w') as file:
        file.write('*** Advanced MAME Launcher Software Lists scanner report ***\n'.encode('utf-8'))
        file.write('This reports shows the SL items with ROM ZIPs and/or CHDs with MISSING status\n'.encode('utf-8'))
        file.write('\n'.encode('utf-8'))
        if r_miss_list:
            file.write('\n'.join(r_miss_list).encode('utf-8'))
        else:
            file.write('Congratulations! No missing SL ROM ZIP or CHD files.')

    # --- SL ROM ZIP and CHD file list ---
    # >> Not coded yet
    log_info('Opening SL ROM list missing report')
    log_info('Report file "{0}"'.format(PATHS.REPORT_SL_SCAN_ROM_LIST_MISS_PATH.getPath()))
    with open(PATHS.REPORT_SL_SCAN_ROM_LIST_MISS_PATH.getPath(), 'w') as file:
        file.write('*** Advanced MAME Launcher Software Lists scanner report ***\n'.encode('utf-8'))
        file.write('This report shows all missing SL item ROM ZIPs\n'.encode('utf-8'))
        file.write('\nSL ROM list missing report not coded yet. Sorry.\n'.encode('utf-8'))
        # file.write('\n'.join(report_list).encode('utf-8'))

    # >> Not coded yet
    log_info('Opening SL CHD list missing report')
    log_info('Report file "{0}"'.format(PATHS.REPORT_SL_SCAN_CHD_LIST_MISS_PATH.getPath()))
    with open(PATHS.REPORT_SL_SCAN_CHD_LIST_MISS_PATH.getPath(), 'w') as file:
        file.write('*** Advanced MAME Launcher Software Lists scanner report ***\n'.encode('utf-8'))
        file.write('This report shows all missing SL item CHDs\n'.encode('utf-8'))
        file.write('\nSL CHD list missing report not coded yet. Sorry.\n'.encode('utf-8'))
        # file.write('\n'.join(report_list).encode('utf-8'))

    # >> Update statistics
    change_control_dic(control_dic, 'scan_SL_archives_ROM_total', SL_ROMs_total)
    change_control_dic(control_dic, 'scan_SL_archives_ROM_have', SL_ROMs_have)
    change_control_dic(control_dic, 'scan_SL_archives_ROM_missing', SL_ROMs_missing)
    change_control_dic(control_dic, 'scan_SL_archives_CHD_total', SL_CHDs_total)
    change_control_dic(control_dic, 'scan_SL_archives_CHD_have', SL_CHDs_have)
    change_control_dic(control_dic, 'scan_SL_archives_CHD_missing', SL_CHDs_missing)
    change_control_dic(control_dic, 't_SL_ROMs_scan', time.time())

#
# Note that MAME is able to use clone artwork from parent machines. Mr. Do's Artwork ZIP files
# are provided only for parents.
# First pass: search for on-disk assets.
# Second pass: do artwork substitution
#   A) A clone may use assets from parent.
#   B) A parent may use assets from a clone.
#
def mame_scan_MAME_assets(PATHS, assets_dic, control_dic, pDialog,
                          machines_render, main_pclone_dic, Asset_path_FN):
    # >> Iterate machines, check if assets/artwork exist.
    table_str = []
    table_str.append(['left', 'left', 'left',  'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'])
    table_str.append(['Name', 'PCB',  'Artp',  'Art',  'Cab',  'Clr',  'CPan', 'Fan',  'Fly',  'Man',  'Mar',  'Snap', 'Tit',  'Tra'])

    # --- Create a cache of assets ---
    pDialog.create('Advanced MAME Launcher', 'Scanning files in asset directories ...')
    pDialog.update(0)
    num_assets = len(ASSET_MAME_T_LIST)
    asset_dirs = [''] * num_assets
    for i, asset_tuple in enumerate(ASSET_MAME_T_LIST):
        asset_dir = asset_tuple[1]
        full_asset_dir_FN = Asset_path_FN.pjoin(asset_dir)
        asset_dir_str = full_asset_dir_FN.getPath()
        asset_dirs[i] = asset_dir_str
        misc_add_file_cache(asset_dir_str)
        pDialog.update((100*(i+1))/num_assets)
    pDialog.update(100)
    pDialog.close()

    # --- First pass: search for on-disk assets ---
    pDialog.create('Advanced MAME Launcher', 'Scanning MAME assets/artwork (first pass) ...')
    total_machines = len(machines_render)
    processed_machines = 0
    ondisk_assets_dic = {}
    for m_name in sorted(machines_render):
        machine_assets = fs_new_MAME_asset()
        for idx, asset_tuple in enumerate(ASSET_MAME_T_LIST):
            asset_key = asset_tuple[0]
            asset_dir = asset_tuple[1]
            if asset_key == 'artwork':
                asset_FN = misc_search_file_cache(asset_dirs[idx], m_name, ASSET_ARTWORK_EXTS)
            elif asset_key == 'manual':
                asset_FN = misc_search_file_cache(asset_dirs[idx], m_name, ASSET_MANUAL_EXTS)
            elif asset_key == 'trailer':
                asset_FN = misc_search_file_cache(asset_dirs[idx], m_name, ASSET_TRAILER_EXTS)
            else:
                asset_FN = misc_search_file_cache(asset_dirs[idx], m_name, ASSET_IMAGE_EXTS)
            # if m_name == '005':
            #     log_debug('asset_key       "{0}"'.format(asset_key))
            #     log_debug('asset_dir       "{0}"'.format(asset_dir))
            #     log_debug('asset_dirs[idx] "{0}"'.format(asset_dirs[idx]))
            #     log_debug('asset_FN        "{0}"'.format(asset_FN))
            machine_assets[asset_key] = asset_FN.getOriginalPath() if asset_FN else ''
        ondisk_assets_dic[m_name] = machine_assets
        # >> Update progress
        processed_machines += 1
        pDialog.update((processed_machines*100) // total_machines)
    pDialog.close()

    # --- Second pass: substitute artwork ---
    pDialog.create('Advanced MAME Launcher', 'Scanning MAME assets/artwork (second pass) ...')
    have_count_list = [0] * len(ASSET_MAME_T_LIST)
    alternate_count_list = [0] * len(ASSET_MAME_T_LIST)
    total_machines = len(machines_render)
    processed_machines = 0
    for m_name in sorted(machines_render):
        asset_row = ['---'] * len(ASSET_MAME_T_LIST)
        for idx, asset_tuple in enumerate(ASSET_MAME_T_LIST):
            asset_key = asset_tuple[0]
            asset_dir = asset_tuple[1]
            # >> Reset asset
            assets_dic[m_name][asset_key] = ''
            # >> If artwork exists on disk set it on database
            if ondisk_assets_dic[m_name][asset_key]:
                assets_dic[m_name][asset_key] = ondisk_assets_dic[m_name][asset_key]
                have_count_list[idx] += 1
                asset_row[idx] = 'YES'
            # >> If artwork does not exist on disk ...
            else:
                # >> if machine is a parent search in the clone list
                if m_name in main_pclone_dic:
                    for clone_key in main_pclone_dic[m_name]:
                        if ondisk_assets_dic[clone_key][asset_key]:
                            assets_dic[m_name][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                            have_count_list[idx] += 1
                            alternate_count_list[idx] += 1
                            asset_row[idx] = 'CLO'
                            break
                # >> if machine is a clone search in the parent first, then search in the clones
                else:
                    # >> Search parent
                    parent_name = machines_render[m_name]['cloneof']
                    if ondisk_assets_dic[parent_name][asset_key]:
                        assets_dic[m_name][asset_key] = ondisk_assets_dic[parent_name][asset_key]
                        have_count_list[idx] += 1
                        alternate_count_list[idx] += 1
                        asset_row[idx] = 'PAR'
                    # >> Search clones
                    else:
                        for clone_key in main_pclone_dic[parent_name]:
                            if clone_key == m_name: continue
                            if ondisk_assets_dic[clone_key][asset_key]:
                                assets_dic[m_name][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                                have_count_list[idx] += 1
                                alternate_count_list[idx] += 1
                                asset_row[idx] = 'CLX'
                                break
        table_row = [m_name] + asset_row
        table_str.append(table_row)
        # >> Update progress
        processed_machines += 1
        pDialog.update((processed_machines*100) // total_machines)
    pDialog.close()

    # --- Asset statistics and report ---
    PCB  = (have_count_list[0],  total_machines - have_count_list[0],  alternate_count_list[0])
    Artp = (have_count_list[1],  total_machines - have_count_list[1],  alternate_count_list[1])
    Art  = (have_count_list[2],  total_machines - have_count_list[2],  alternate_count_list[2])
    Cab  = (have_count_list[3],  total_machines - have_count_list[3],  alternate_count_list[3])
    Clr  = (have_count_list[4],  total_machines - have_count_list[4],  alternate_count_list[4])
    CPan = (have_count_list[5],  total_machines - have_count_list[5],  alternate_count_list[5])
    Fan  = (have_count_list[6],  total_machines - have_count_list[6],  alternate_count_list[6])
    Fly  = (have_count_list[7],  total_machines - have_count_list[7],  alternate_count_list[7])
    Man  = (have_count_list[8],  total_machines - have_count_list[8],  alternate_count_list[8])
    Mar  = (have_count_list[9],  total_machines - have_count_list[9],  alternate_count_list[9])
    Snap = (have_count_list[10], total_machines - have_count_list[10], alternate_count_list[10])
    Tit  = (have_count_list[11], total_machines - have_count_list[11], alternate_count_list[11])
    Tra  = (have_count_list[12], total_machines - have_count_list[12], alternate_count_list[12])
    pDialog.create('Advanced MAME Launcher')
    pDialog.update(0, 'Creating MAME asset report ...')
    report_slist = []
    report_slist.append('*** Advanced MAME Launcher MAME machines asset scanner report ***')
    report_slist.append('Total MAME machines {0}'.format(total_machines))
    report_slist.append('Have PCBs       {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*PCB))
    report_slist.append('Have Artpreview {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Artp))
    report_slist.append('Have Artwork    {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Art))
    report_slist.append('Have Cabinets   {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Cab))
    report_slist.append('Have Clearlogos {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Clr))
    report_slist.append('Have CPanels    {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*CPan))
    report_slist.append('Have Fanarts    {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Fan))
    report_slist.append('Have Flyers     {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Fly))
    report_slist.append('Have Manuals    {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Man))
    report_slist.append('Have Marquees   {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Mar))
    report_slist.append('Have Snaps      {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Snap))
    report_slist.append('Have Titles     {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Tit))
    report_slist.append('Have Trailers   {0:5d} (Missing {1:5d}, Alternate {2:5d})'.format(*Tra))
    report_slist.append('')
    table_str_list = text_render_table_str(table_str)
    report_slist.extend(table_str_list)
    log_info('Opening MAME asset report file "{0}"'.format(PATHS.REPORT_MAME_ASSETS_PATH.getPath()))
    with open(PATHS.REPORT_MAME_ASSETS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_slist).encode('utf-8'))
    pDialog.update(100)

    # >> Update control_dic by assigment (will be saved in caller)
    change_control_dic(control_dic, 'assets_num_MAME_machines', total_machines)
    change_control_dic(control_dic, 'assets_PCBs_have', PCB[0])
    change_control_dic(control_dic, 'assets_PCBs_missing', PCB[1])
    change_control_dic(control_dic, 'assets_PCBs_alternate', PCB[2])
    change_control_dic(control_dic, 'assets_artpreview_have', Artp[0])
    change_control_dic(control_dic, 'assets_artpreview_missing', Artp[1])
    change_control_dic(control_dic, 'assets_artpreview_alternate', Artp[2])
    change_control_dic(control_dic, 'assets_artwork_have', Art[0])
    change_control_dic(control_dic, 'assets_artwork_missing', Art[1])
    change_control_dic(control_dic, 'assets_artwork_alternate', Art[2])
    change_control_dic(control_dic, 'assets_cabinets_have', Cab[0])
    change_control_dic(control_dic, 'assets_cabinets_missing', Cab[1])
    change_control_dic(control_dic, 'assets_cabinets_alternate', Cab[2])
    change_control_dic(control_dic, 'assets_clearlogos_have', Clr[0])
    change_control_dic(control_dic, 'assets_clearlogos_missing', Clr[1])
    change_control_dic(control_dic, 'assets_clearlogos_alternate', Clr[2])
    change_control_dic(control_dic, 'assets_cpanels_have', CPan[0])
    change_control_dic(control_dic, 'assets_cpanels_missing', CPan[1])
    change_control_dic(control_dic, 'assets_cpanels_alternate', CPan[2])
    change_control_dic(control_dic, 'assets_fanarts_have', Fan[0])
    change_control_dic(control_dic, 'assets_fanarts_missing', Fan[1])
    change_control_dic(control_dic, 'assets_fanarts_alternate', Fan[2])
    change_control_dic(control_dic, 'assets_flyers_have', Fly[0])
    change_control_dic(control_dic, 'assets_flyers_missing', Fly[1])
    change_control_dic(control_dic, 'assets_flyers_alternate', Fly[2])
    change_control_dic(control_dic, 'assets_manuals_have', Man[0])
    change_control_dic(control_dic, 'assets_manuals_missing', Man[1])
    change_control_dic(control_dic, 'assets_manuals_alternate', Man[2])
    change_control_dic(control_dic, 'assets_marquees_have', Mar[0])
    change_control_dic(control_dic, 'assets_marquees_missing', Mar[1])
    change_control_dic(control_dic, 'assets_marquees_alternate', Mar[2])
    change_control_dic(control_dic, 'assets_snaps_have', Snap[0])
    change_control_dic(control_dic, 'assets_snaps_missing', Snap[1])
    change_control_dic(control_dic, 'assets_snaps_alternate', Snap[2])
    change_control_dic(control_dic, 'assets_titles_have', Tit[0])
    change_control_dic(control_dic, 'assets_titles_missing', Tit[1])
    change_control_dic(control_dic, 'assets_titles_alternate', Tit[2])
    change_control_dic(control_dic, 'assets_trailers_have', Tra[0])
    change_control_dic(control_dic, 'assets_trailers_missing', Tra[1])
    change_control_dic(control_dic, 'assets_trailers_alternate', Tra[2])
    change_control_dic(control_dic, 't_MAME_assets_scan', time.time())

def mame_scan_SL_assets(PATHS, control_dic, SL_index_dic, SL_pclone_dic, Asset_path_FN):
    log_debug('mame_scan_SL_assets() Starting ...')

    # --- Traverse Software List, check if ROM exists, update and save database ---
    pDialog = xbmcgui.DialogProgress()
    pdialog_line1 = 'Scanning Sofware Lists assets/artwork ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    pDialog.update(0)
    total_files = len(SL_index_dic)
    processed_files = 0
    table_str = []
    table_str.append(['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'])
    table_str.append(['Soft', 'Name', 'Tit',  'Snap', 'Bft',  'Fan',  'Tra',  'Man'])
    have_count_list = [0] * len(ASSET_SL_T_LIST)
    alternate_count_list = [0] * len(ASSET_SL_T_LIST)
    SL_item_count = 0
    # >> DEBUG code
    # SL_index_dic = {
    #     "32x" :
    #     { "display_name" : "Sega 32X cartridges", "num_with_CHDs" : 0, "num_with_ROMs" : 203, "rom_DB_noext" : "32x" }
    # }
    for SL_name in sorted(SL_index_dic):
        # --- Update progress ---
        update_number = (processed_files*100) // total_files
        pDialog.update(update_number, pdialog_line1, 'Software List {0}'.format(SL_name))

        # --- Load SL databases ---
        file_name = SL_index_dic[SL_name]['rom_DB_noext'] + '.json'
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
        SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

        # --- Cache files ---
        misc_clear_file_cache(verbose = False)
        num_assets = len(ASSET_SL_T_LIST)
        asset_dirs = [''] * num_assets
        for i, asset_tuple in enumerate(ASSET_SL_T_LIST):
            asset_dir = asset_tuple[1]
            full_asset_dir_FN = Asset_path_FN.pjoin(asset_dir).pjoin(SL_name)
            asset_dir_str = full_asset_dir_FN.getPath()
            asset_dirs[i] = asset_dir_str
            misc_add_file_cache(asset_dir_str, verbose = False)

        # --- First pass: scan for on-disk assets ---
        assets_file_name = SL_index_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        # log_info('Assets JSON "{0}"'.format(SL_asset_DB_FN.getPath()))
        ondisk_assets_dic = {}
        for rom_key in sorted(SL_roms):
            SL_assets = fs_new_SL_asset()
            for idx, asset_tuple in enumerate(ASSET_SL_T_LIST):
                asset_key = asset_tuple[0]
                asset_dir = asset_tuple[1]
                full_asset_dir_FN = Asset_path_FN.pjoin(asset_dir).pjoin(SL_name)
                if asset_key == 'manual':
                    asset_FN = misc_search_file_cache(asset_dirs[idx], rom_key, ASSET_MANUAL_EXTS)
                elif asset_key == 'trailer':
                    asset_FN = misc_search_file_cache(asset_dirs[idx], rom_key, ASSET_TRAILER_EXTS)
                else:
                    asset_FN = misc_search_file_cache(asset_dirs[idx], rom_key, ASSET_IMAGE_EXTS)
                # log_info('Testing P "{0}"'.format(asset_FN.getPath()))
                SL_assets[asset_key] = asset_FN.getOriginalPath() if asset_FN else ''
            ondisk_assets_dic[rom_key] = SL_assets

        # --- Second pass: substitute artwork ---
        main_pclone_dic = SL_pclone_dic[SL_name]
        SL_assets_dic = {}
        for rom_key in sorted(SL_roms):
            SL_item_count += 1
            SL_assets_dic[rom_key] = fs_new_SL_asset()
            asset_row = ['---'] * len(ASSET_SL_T_LIST)
            for idx, asset_tuple in enumerate(ASSET_SL_T_LIST):
                asset_key = asset_tuple[0]
                asset_dir = asset_tuple[1]
                # >> Reset asset
                SL_assets_dic[rom_key][asset_key] = ''
                # >> If artwork exists on disk set it on database
                if ondisk_assets_dic[rom_key][asset_key]:
                    SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[rom_key][asset_key]
                    have_count_list[idx] += 1
                    asset_row[idx] = 'YES'
                # >> If artwork does not exist on disk ...
                else:
                    # >> if machine is a parent search in the clone list
                    if rom_key in main_pclone_dic:
                        for clone_key in main_pclone_dic[rom_key]:
                            if ondisk_assets_dic[clone_key][asset_key]:
                                SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                                have_count_list[idx] += 1
                                alternate_count_list[idx] += 1
                                asset_row[idx] = 'CLO'
                                break
                    # >> if machine is a clone search in the parent first, then search in the clones
                    else:
                        # >> Search parent
                        parent_name = SL_roms[rom_key]['cloneof']
                        if ondisk_assets_dic[parent_name][asset_key]:
                            SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[parent_name][asset_key]
                            have_count_list[idx] += 1
                            alternate_count_list[idx] += 1
                            asset_row[idx] = 'PAR'
                        # >> Search clones
                        else:
                            for clone_key in main_pclone_dic[parent_name]:
                                if clone_key == rom_key: continue
                                if ondisk_assets_dic[clone_key][asset_key]:
                                    SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                                    have_count_list[idx] += 1
                                    alternate_count_list[idx] += 1
                                    asset_row[idx] = 'CLX'
                                    break
            table_row = [SL_name, rom_key] + asset_row
            table_str.append(table_row)
        # --- Write SL asset JSON ---
        fs_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic, verbose = False)
        # --- Update progress ---
        processed_files += 1
    update_number = (processed_files*100) // total_files
    pDialog.update(update_number, ' ', ' ')
    pDialog.close()

    # >> Asset statistics and report.
    Tit  = (have_count_list[0], SL_item_count - have_count_list[0], alternate_count_list[0])
    Snap = (have_count_list[1], SL_item_count - have_count_list[1], alternate_count_list[1])
    Boxf = (have_count_list[2], SL_item_count - have_count_list[2], alternate_count_list[2])
    Fan  = (have_count_list[3], SL_item_count - have_count_list[3], alternate_count_list[3])
    Tra  = (have_count_list[4], SL_item_count - have_count_list[4], alternate_count_list[4])
    Man  = (have_count_list[5], SL_item_count - have_count_list[5], alternate_count_list[5])
    pDialog.create('Advanced MAME Launcher')
    pDialog.update(0, 'Creating SL asset report ...')
    report_slist = []
    report_slist.append('*** Advanced MAME Launcher Software List asset scanner report ***')
    report_slist.append('Total SL items {0}'.format(SL_item_count))
    report_slist.append('Have Titles    {0:6d} (Missing {1:6d}, Alternate {2:6d})'.format(*Tit))
    report_slist.append('Have Snaps     {0:6d} (Missing {1:6d}, Alternate {2:6d})'.format(*Snap))
    report_slist.append('Have Boxfronts {0:6d} (Missing {1:6d}, Alternate {2:6d})'.format(*Boxf))
    report_slist.append('Have Fanarts   {0:6d} (Missing {1:6d}, Alternate {2:6d})'.format(*Fan))
    report_slist.append('Have Trailers  {0:6d} (Missing {1:6d}, Alternate {2:6d})'.format(*Tra))
    report_slist.append('Have Manuals   {0:6d} (Missing {1:6d}, Alternate {2:6d})'.format(*Man))
    report_slist.append('')
    table_str_list = text_render_table_str(table_str)
    report_slist.extend(table_str_list)
    log_info('Opening SL asset report file "{0}"'.format(PATHS.REPORT_SL_ASSETS_PATH.getPath()))
    with open(PATHS.REPORT_SL_ASSETS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(report_slist).encode('utf-8'))
    pDialog.update(100)
    pDialog.close()

    # >> Update control_dic by assigment (will be saved in caller)
    change_control_dic(control_dic, 'assets_SL_num_items', SL_item_count)
    change_control_dic(control_dic, 'assets_SL_titles_have', Tit[0])
    change_control_dic(control_dic, 'assets_SL_titles_missing', Tit[1])
    change_control_dic(control_dic, 'assets_SL_titles_alternate', Tit[2])
    change_control_dic(control_dic, 'assets_SL_snaps_have', Snap[0])
    change_control_dic(control_dic, 'assets_SL_snaps_missing', Snap[1])
    change_control_dic(control_dic, 'assets_SL_snaps_alternate', Snap[2])
    change_control_dic(control_dic, 'assets_SL_boxfronts_have', Boxf[0])
    change_control_dic(control_dic, 'assets_SL_boxfronts_missing', Boxf[1])
    change_control_dic(control_dic, 'assets_SL_boxfronts_alternate', Boxf[2])
    change_control_dic(control_dic, 'assets_SL_fanarts_have', Fan[0])
    change_control_dic(control_dic, 'assets_SL_fanarts_missing', Fan[1])
    change_control_dic(control_dic, 'assets_SL_fanarts_alternate', Fan[2])
    change_control_dic(control_dic, 'assets_SL_trailers_have', Tra[0])
    change_control_dic(control_dic, 'assets_SL_trailers_missing', Tra[1])
    change_control_dic(control_dic, 'assets_SL_trailers_alternate', Tra[2])
    change_control_dic(control_dic, 'assets_SL_manuals_have', Man[0])
    change_control_dic(control_dic, 'assets_SL_manuals_missing', Man[1])
    change_control_dic(control_dic, 'assets_SL_manuals_alternate', Man[2])
    change_control_dic(control_dic, 't_SL_assets_scan', time.time())
