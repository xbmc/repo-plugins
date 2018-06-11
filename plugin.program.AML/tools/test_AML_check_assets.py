#!/usr/bin/python
# -*- coding: utf-8 -*-
# Checks MAME artwork
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
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
import xml.etree.ElementTree as ET 
import re
import sys
import json
import io
import os

# --- "Constants" -------------------------------------------------------------
MAIN_DB_FILE_PATH                = 'MAME_info.json'
MAIN_PCLONE_DIC_FILE_PATH        = 'MAME_PClone_dic.json'
ASSETS_DB_FILE_PATH              = 'MAME_assets.json'

ASSETS_FILE_LIST = [
    'artpreview', 'bosses', 'cabinets', 
    'covers_SL', 'cpanel', 'devices', 
    'ends', 'flyers', 'gameover', 
    'howto', 'icons', 'logo',
    'marquees', 'pcb', 'scores', 
    'select', 'snap_SL', 'snap', 
    'titles_SL', 'titles', 'versus'
]

ASSETS_DIR = '/home/mendi/AML-assets/'

# -------------------------------------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------------------------------------
def fs_write_JSON_file(json_filename, json_data):
    # >> Write JSON data
    try:
        with io.open(json_filename, 'wt', encoding='utf-8') as file:
          file.write(unicode(json.dumps(json_data, ensure_ascii = False, sort_keys = True, indent = 2, separators = (',', ': '))))
    except OSError:
        # gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (OSError)'.format(roms_json_file))
        pass
    except IOError:
        # gui_kodi_notify('Advanced Emulator Launcher - Error', 'Cannot write {0} file (IOError)'.format(roms_json_file))
        pass

def fs_load_JSON_file(json_filename):
    # --- If file does not exist return empty dictionary ---
    data_dic = {}
    if not os.path.isfile(json_filename):
        return data_dic

    # --- Parse using json module ---
    # log_verb('fs_load_ROMs_JSON() Loading JSON file {0}'.format(json_filename))
    with open(json_filename) as file:    
        data_dic = json.load(file)

    return data_dic

# -----------------------------------------------------------------------------
# Load MAME data
# -----------------------------------------------------------------------------
print('Reading main MAME database...')
machines = fs_load_JSON_file(MAIN_DB_FILE_PATH)

# -----------------------------------------------------------------------------
# Traverse all machines and check artwork
# -----------------------------------------------------------------------------
print('Checking artwork...')
assets_stats = {
    'artpreview' : 0, 'bosses' : 0, 'cabinets' : 0, 
    'cpanel' : 0, 'devices' : 0, 
    'ends' : 0, 'flyers' : 0, 'gameover' : 0, 
    'howto' : 0, 'icons' : 0, 'logo' : 0,
    'marquees' : 0, 'pcb' : 0, 'scores' : 0, 
    'select' : 0, 'snap' : 0, 
    'titles' : 0, 'versus' : 0
}

MAME_assets_dic = {}
for machine_name in machines:
    # >> Excluded manuals_SL.zip and manuals.zip
    assets_dic = {
        'artpreview' : False, 'bosses' : False, 'cabinets' : False, 
        'cpanel' : False, 'devices' : False, 
        'ends' : False, 'flyers' : False, 'gameover' : False, 
        'howto' : False, 'icons' : False, 'logo' : False,
        'marquees' : False, 'pcb' : False, 'scores' : False, 
        'select' : False, 'snap' : False, 
        'titles' : False, 'versus' : False
    }
    
    # >> Check all artwork types
    for artwork_name in assets_dic:
        if artwork_name == 'icons':
            asset_filename = os.path.join(ASSETS_DIR, artwork_name, machine_name + '.ico')
        else:
            asset_filename = os.path.join(ASSETS_DIR, artwork_name, machine_name + '.png')
        # print('Checking {0}'.format(asset_filename))
        if os.path.exists(asset_filename): 
            assets_dic[artwork_name] = True
            assets_stats[artwork_name] += 1
    MAME_assets_dic[machine_name] = assets_dic

# -----------------------------------------------------------------------------
# Write assets DB
# -----------------------------------------------------------------------------
print('Writing MAME assets database...')
fs_write_JSON_file(ASSETS_DB_FILE_PATH, MAME_assets_dic)

# -----------------------------------------------------------------------------
# Assets report
# -----------------------------------------------------------------------------
print('Writing report...')
str_list = []
str_list.append(u'<Statistics>\n')
str_list.append(u'artpreview {0:5d}\n'.format(assets_stats['artpreview']))
str_list.append(u'bosses     {0:5d}\n'.format(assets_stats['bosses']))
str_list.append(u'cabinets   {0:5d}\n'.format(assets_stats['cabinets']))
str_list.append(u'cpanel     {0:5d}\n'.format(assets_stats['cpanel']))
str_list.append(u'devices    {0:5d}\n'.format(assets_stats['devices']))
str_list.append(u'ends       {0:5d}\n'.format(assets_stats['ends']))
str_list.append(u'flyers     {0:5d}\n'.format(assets_stats['flyers']))
str_list.append(u'gameover   {0:5d}\n'.format(assets_stats['gameover']))
str_list.append(u'howto      {0:5d}\n'.format(assets_stats['howto']))
str_list.append(u'icons      {0:5d}\n'.format(assets_stats['icons']))
str_list.append(u'logo       {0:5d}\n'.format(assets_stats['logo']))
str_list.append(u'marquees   {0:5d}\n'.format(assets_stats['marquees']))
str_list.append(u'pcb        {0:5d}\n'.format(assets_stats['pcb']))
str_list.append(u'scores     {0:5d}\n'.format(assets_stats['scores']))
str_list.append(u'select     {0:5d}\n'.format(assets_stats['select']))
str_list.append(u'snap       {0:5d}\n'.format(assets_stats['snap']))
str_list.append(u'titles     {0:5d}\n'.format(assets_stats['titles']))
str_list.append(u'versus     {0:5d}\n'.format(assets_stats['versus']))

str_list.append(u'\n<AML MAME assets report>\n')
str_list.append(u'Machine    | artpreview | bosses | cabinets | cpanel | devices | ends | flyers | gameover | ' +
                u'howto | icons | logo | marquees | pcb   | scores | select | snap | titles | versus |\n')
for machine_name in sorted(MAME_assets_dic):
    m = MAME_assets_dic[machine_name]
    str_list.append(u'{0} '.format(machine_name.ljust(12)))
    str_list.append(u'{0}        '.format(str(m['artpreview']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['bosses']).ljust(5)))
    str_list.append(u'{0}      '.format(str(m['cabinets']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['cpanel']).ljust(5)))
    str_list.append(u'{0}     '.format(str(m['devices']).ljust(5)))
    str_list.append(u'{0}  '.format(str(m['ends']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['flyers']).ljust(5)))
    str_list.append(u'{0}      '.format(str(m['gameover']).ljust(5)))
    str_list.append(u'{0}   '.format(str(m['howto']).ljust(5)))
    str_list.append(u'{0}   '.format(str(m['icons']).ljust(5)))
    str_list.append(u'{0}  '.format(str(m['logo']).ljust(5)))
    str_list.append(u'{0}      '.format(str(m['marquees']).ljust(5)))
    str_list.append(u'{0}   '.format(str(m['pcb']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['scores']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['select']).ljust(5)))
    str_list.append(u'{0}  '.format(str(m['snap']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['titles']).ljust(5)))
    str_list.append(u'{0}    '.format(str(m['versus']).ljust(5)))
    str_list.append(u'\n')
full_string = ''.join(str_list)
file = open('asset_report.txt', 'wt' )
file.write(full_string.encode('utf-8'))
file.close()
