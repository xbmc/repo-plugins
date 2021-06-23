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

# Advanced Emulator/MAME Launcher constants and globals.
# This module has no external dependencies.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

# Transitional code from Python 2 to Python 3 (https://github.com/benjaminp/six/blob/master/six.py)
import sys
ADDON_RUNNING_PYTHON_2 = sys.version_info[0] == 2
ADDON_RUNNING_PYTHON_3 = sys.version_info[0] == 3
if ADDON_RUNNING_PYTHON_3:
    text_type = str
    binary_type = bytes
elif ADDON_RUNNING_PYTHON_2:
    text_type = unicode
    binary_type = str
else:
    raise TypeError('Unknown Python runtime version')

# -------------------------------------------------------------------------------------------------
# Addon options and tuneables.
# -------------------------------------------------------------------------------------------------
# Compact, smaller size, non-human readable JSON. False forces human-readable JSON for development.
# In AEL speed is not as critical so False is OK.
# In AML this must be True when releasing.
OPTION_COMPACT_JSON = True

# Use less memory when writing big JSON files, but writing is slower.
# In AEL this can be False when releasing.
# In AML it must be True when releasing.
OPTION_LOWMEM_WRITE_JSON = True

# The addon name in the GUI. Title of Kodi dialogs (yesno, progress, etc.) and used also in log functions.
ADDON_LONG_NAME = 'Advanced MAME Launcher'
ADDON_SHORT_NAME = 'AML'

# These parameters are used in utils_write_JSON_file() when pprint is True or
# OPTION_COMPACT_JSON is False. Otherwise non-human readable, compact JSON is written.
# pprint = True function parameter overrides option OPTION_COMPACT_JSON.
# More compact JSON files (less blanks) load faster because file size is smaller.
JSON_INDENT = 1
JSON_SEP = (', ', ': ')

# -------------------------------------------------------------------------------------------------
# DEBUG/TEST settings
# -------------------------------------------------------------------------------------------------
# If True MAME is not launched. Useful to test the Recently Played and Most Played code.
# This setting must be False when releasing.
DISABLE_MAME_LAUNCHING = False

# -------------------------------------------------------------------------------------------------
# This is to ease printing colors in Kodi.
# -------------------------------------------------------------------------------------------------
KC_RED        = '[COLOR red]'
KC_ORANGE     = '[COLOR orange]'
KC_GREEN      = '[COLOR green]'
KC_YELLOW     = '[COLOR yellow]'
KC_VIOLET     = '[COLOR violet]'
KC_BLUEVIOLET = '[COLOR blueviolet]'
KC_END        = '[/COLOR]'

# -------------------------------------------------------------------------------------------------
# Image file constants.
# -------------------------------------------------------------------------------------------------
# Supported image files in:
# 1. misc_identify_image_id_by_contents()
# 2. misc_identify_image_id_by_ext()
IMAGE_PNG_ID     = 'PNG'
IMAGE_JPEG_ID    = 'JPEG'
IMAGE_GIF_ID     = 'GIF'
IMAGE_BMP_ID     = 'BMP'
IMAGE_TIFF_ID    = 'TIFF'
IMAGE_UKNOWN_ID  = 'Image unknown'
IMAGE_CORRUPT_ID = 'Image corrupt'

IMAGE_IDS = [
    IMAGE_PNG_ID,
    IMAGE_JPEG_ID,
    IMAGE_GIF_ID,
    IMAGE_BMP_ID,
    IMAGE_TIFF_ID,
]

IMAGE_EXTENSIONS = {
    IMAGE_PNG_ID  : ['png'],
    IMAGE_JPEG_ID : ['jpg', 'jpeg'],
    IMAGE_GIF_ID  : ['gif'],
    IMAGE_BMP_ID  : ['bmp'],
    IMAGE_TIFF_ID : ['tif', 'tiff'],
}

# Image file magic numbers. All at file offset 0.
# See https://en.wikipedia.org/wiki/List_of_file_signatures
# b prefix is a byte string in both Python 2 and 3.
IMAGE_MAGIC_DIC = {
    IMAGE_PNG_ID  : [ b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' ],
    IMAGE_JPEG_ID : [
        b'\xFF\xD8\xFF\xDB',
        b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01',
        b'\xFF\xD8\xFF\xEE',
        b'\xFF\xD8\xFF\xE1',
    ],
    IMAGE_GIF_ID  : [
        b'\x47\x49\x46\x38\x37\x61',
        b'\x47\x49\x46\x38\x39\x61',
    ],
    IMAGE_BMP_ID  : [ b'\x42\x4D' ],
    IMAGE_TIFF_ID : [
        b'\x49\x49\x2A\x00',
        b'\x4D\x4D\x00\x2A',
    ]
}

# -------------------------------------------------------------------------------------------------
# Addon constants
# -------------------------------------------------------------------------------------------------
# Operational modes
# This must match setting op_mode_raw in settings.xml or bad things will happen.
OP_MODE_VANILLA            = 'Vanilla MAME'
OP_MODE_RETRO_MAME2003PLUS = 'Retroarch MAME 2003 Plus'
OP_MODE_RETRO_MAME2010     = 'Retroarch MAME 2010'
OP_MODE_RETRO_MAME2014     = 'Retroarch MAME 2014'
OP_MODE_LIST = [
    OP_MODE_VANILLA,
    OP_MODE_RETRO_MAME2003PLUS,
    OP_MODE_RETRO_MAME2010,
    OP_MODE_RETRO_MAME2014,
]

# In MAME 2003 Plus the MAME version is not found on the XML file.
MAME2003PLUS_VERSION_RAW = '0.78 (RA2003Plus)'

# Make sure these strings are equal to the ones in settings.xml or bad things will happen.
VIEW_MODE_FLAT             = 0 # 'Flat'
VIEW_MODE_PCLONE           = 1 # 'Parent/Clone'
ROMSET_MAME_MERGED         = 0 # 'Merged'
ROMSET_MAME_SPLIT          = 1 # 'Split'
ROMSET_MAME_NONMERGED      = 2 # 'Non-merged'
ROMSET_MAME_FULLYNONMERGED = 3 # 'Fully non-merged'
ROMSET_SL_MERGED           = 0 # 'Merged'
ROMSET_SL_SPLIT            = 1 # 'Split'

ROMSET_NAME_LIST = ['Merged', 'Split', 'Non-merged', 'Fully non-merged']
CHDSET_NAME_LIST = ['Merged', 'Split', 'Non-merged']

# -------------------------------------------------------------------------------------------------
# Advanced MAME Launcher constants
# -------------------------------------------------------------------------------------------------
# Database status. Status it determined with timestamps in control_dic
MAME_MAIN_DB_BUILT    = 200
MAME_AUDIT_DB_BUILT   = 300
MAME_CATALOG_BUILT    = 400
MAME_MACHINES_SCANNED = 500
MAME_ASSETS_SCANNED   = 600
SL_MAIN_DB_BUILT      = 700
SL_ITEMS_SCANNED      = 800
SL_ASSETS_SCANNED     = 900

# INI and DAT files default names.
ALLTIME_INI   = 'Alltime.ini'
ARTWORK_INI   = 'Artwork.ini'
BESTGAMES_INI = 'bestgames.ini'
CATEGORY_INI  = 'Category.ini'
CATLIST_INI   = 'catlist.ini'
CATVER_INI    = 'catver.ini'
GENRE_INI     = 'genre.ini'
MATURE_INI    = 'mature.ini'
NPLAYERS_INI  = 'nplayers.ini'
SERIES_INI    = 'series.ini'
COMMAND_DAT   = 'command.dat'
GAMEINIT_DAT  = 'gameinit.dat'
HISTORY_XML   = 'history.xml'
HISTORY_DAT   = 'history.dat'
MAMEINFO_DAT  = 'mameinfo.dat'

# --- Used in the addon URLs so mark the location of machines/ROMs ---
LOCATION_STANDARD           = 'STANDARD'
LOCATION_MAME_FAVS          = 'MAME_FAVS'
LOCATION_MAME_MOST_PLAYED   = 'MAME_MOST_PLAYED'
LOCATION_MAME_RECENT_PLAYED = 'MAME_RECENT_PLAYED'
LOCATION_SL_FAVS            = 'SL_FAVS'
LOCATION_SL_MOST_PLAYED     = 'SL_MOST_PLAYED'
LOCATION_SL_RECENT_PLAYED   = 'SL_RECENT_PLAYED'

# --- ROM flags used by skins to display status icons ---
AEL_INFAV_BOOL_LABEL  = 'AEL_InFav'
AEL_PCLONE_STAT_LABEL = 'AEL_PClone_stat'

AEL_INFAV_BOOL_VALUE_TRUE    = 'InFav_True'
AEL_INFAV_BOOL_VALUE_FALSE   = 'InFav_False'
AEL_PCLONE_STAT_VALUE_PARENT = 'PClone_Parent'
AEL_PCLONE_STAT_VALUE_CLONE  = 'PClone_Clone'
AEL_PCLONE_STAT_VALUE_NONE   = 'PClone_None'

# --- SL ROM launching cases ---
SL_LAUNCH_CASE_A     = 'Case A'
SL_LAUNCH_CASE_B     = 'Case B'
SL_LAUNCH_CASE_C     = 'Case C'
SL_LAUNCH_CASE_D     = 'Case D'
SL_LAUNCH_CASE_ERROR = 'Case ERROR!'

# --- ROM types ---
ROM_TYPE_ROM    = 'ROM'  # Normal ROM (no merged, no BIOS)
ROM_TYPE_BROM   = 'BROM' # BIOS merged ROM
ROM_TYPE_XROM   = 'XROM' # BIOS non-merged ROM
ROM_TYPE_MROM   = 'MROM' # non-BIOS merged ROM
ROM_TYPE_DROM   = 'DROM' # Device ROM
ROM_TYPE_DISK   = 'DISK'
ROM_TYPE_SAMPLE = 'SAM'
ROM_TYPE_ERROR  = 'ERR'

# --- ROM audit status ---
AUDIT_STATUS_OK                = 'OK'
AUDIT_STATUS_OK_INVALID_ROM    = 'OK (invalid ROM)'
AUDIT_STATUS_OK_INVALID_CHD    = 'OK (invalid CHD)'
AUDIT_STATUS_OK_WRONG_NAME_ROM = 'OK (wrong named ROM)'
AUDIT_STATUS_ZIP_NO_FOUND      = 'ZIP not found'
AUDIT_STATUS_CHD_NO_FOUND      = 'CHD not found'
AUDIT_STATUS_BAD_ZIP_FILE      = 'Bad ZIP file'
AUDIT_STATUS_BAD_CHD_FILE      = 'Bad CHD file'
AUDIT_STATUS_ROM_NOT_IN_ZIP    = 'ROM not in ZIP'
AUDIT_STATUS_ROM_BAD_CRC       = 'ROM bad CRC'
AUDIT_STATUS_ROM_BAD_SIZE      = 'ROM bad size'
AUDIT_STATUS_CHD_BAD_VERSION   = 'CHD bad version'
AUDIT_STATUS_CHD_BAD_SHA1      = 'CHD bad SHA1'
AUDIT_STATUS_SAMPLE_NOT_IN_ZIP = 'SAMPLE not in ZIP'

# --- File name extensions ---
MAME_ROM_EXTS      = ['zip']
MAME_CHD_EXTS      = ['chd']
MAME_SAMPLE_EXTS   = ['zip']
SL_ROM_EXTS        = ['zip']
SL_CHD_EXTS        = ['chd']
ASSET_ARTWORK_EXTS = ['zip']
ASSET_MANUAL_EXTS  = ['pdf', 'cbz', 'cbr']
ASSET_TRAILER_EXTS = ['mp4']
ASSET_IMAGE_EXTS   = ['png']

# Colors for filters and items in the root main menu.
COLOR_FILTER_MAIN = '[COLOR thistle]'
COLOR_FILTER_BINARY = '[COLOR lightblue]'
COLOR_FILTER_CATALOG_DAT = '[COLOR violet]'
COLOR_FILTER_CATALOG_NODAT = '[COLOR sandybrown]'
COLOR_MAME_DAT_BROWSER = '[COLOR lightgreen]'
COLOR_SOFTWARE_LISTS = '[COLOR goldenrod]'
COLOR_MAME_CUSTOM_FILTERS = '[COLOR darkgray]'
COLOR_AEL_ROLS = '[COLOR blue]'
COLOR_MAME_SPECIAL = '[COLOR silver]'
COLOR_SL_SPECIAL = '[COLOR gold]'
COLOR_UTILITIES = '[COLOR limegreen]'
COLOR_GLOBAL_REPORTS = '[COLOR darkorange]'
COLOR_DEFAULT = '[COLOR white]'
COLOR_END = '[/COLOR]'
