# -*- coding: utf-8 -*-

# Advanced MAME Launcher constants and globals.

# Copyright (c) 2018-2020 Wintermute0110 <wintermute0110@gmail.com>
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

# -------------------------------------------------------------------------------------------------
# Addon configuration options
# -------------------------------------------------------------------------------------------------
# Compat, smaller size, non-human readable JSON.
# This setting must be True when releasing.
OPTION_COMPACT_JSON = True

# Use less memory when writing big JSON files, but writing is slower.
# This setting must be True when releasing.
OPTION_LOWMEM_WRITE_JSON = True

# -------------------------------------------------------------------------------------------------
# DEBUG/TEST settings
# -------------------------------------------------------------------------------------------------
# If True MAME is not launched. Useful to test the Recently Played and Most Played code.
# This setting must be False when releasing.
DISABLE_MAME_LAUNCHING = False

# -------------------------------------------------------------------------------------------------
# A universal Addon error reporting exception
# This exception is raised to report errors in the GUI.
# Unhandled exceptions must not raise Addon_Error() so the addon crashes and the traceback 
# is printed in the Kodi log file.
# -------------------------------------------------------------------------------------------------
# Top-level GUI code looks like this:
#
# try:
#     autoconfig_export_category(category, export_FN)
# except Addon_Error as ex:
#     kodi_notify_warn('{0}'.format(ex))
# else:
#     kodi_notify('Exported Category "{0}" XML config'.format(category['m_name']))
#
# Low-level code looks like this:
#
# def autoconfig_export_category(category, export_FN):
#     try:
#         do_something_that_may_fail()
#     except OSError:
#         log_error('(OSError) Cannot write {0} file'.format(export_FN.getBase()))
#         # >> Message to be printed in the GUI
#         raise Addon_Error('Error writing file (OSError)')
#
class Addon_Error(Exception):
    def __init__(self, err_str):
        self.err_str = err_str

    def __str__(self):
        return self.err_str

# -------------------------------------------------------------------------------------------------
# Advanced MAME Launcher settings
# -------------------------------------------------------------------------------------------------
# Operational modes
# This must match setting op_mode_raw in settings.xml or bad things will happen.
OP_MODE_EXTERNAL           = 'External MAME'
OP_MODE_RETRO_MAME2003PLUS = 'Retroarch MAME 2003 Plus'
OP_MODE_RETRO_MAME2010     = 'Retroarch MAME 2010'
OP_MODE_RETRO_MAME2014     = 'Retroarch MAME 2014'
OP_MODE_LIST = [
    OP_MODE_EXTERNAL,
    OP_MODE_RETRO_MAME2003PLUS,
    OP_MODE_RETRO_MAME2010,
    OP_MODE_RETRO_MAME2014,
]

# Make sure these strings are equal to the ones in settings.xml or bad things will happen.
VIEW_MODE_FLAT             = 0 # 'Flat'
VIEW_MODE_PCLONE           = 1 # 'Parent/Clone'
ROMSET_MAME_MERGED         = 0 # 'Merged'
ROMSET_MAME_SPLIT          = 1 # 'Split'
ROMSET_MAME_NONMERGED      = 2 # 'Non-merged'
ROMSET_MAME_FULLYNONMERGED = 3 # 'Non-merged'
ROMSET_SL_MERGED           = 0 # 'Merged'
ROMSET_SL_SPLIT            = 1 # 'Split'

# -------------------------------------------------------------------------------------------------
# Advanced MAME Launcher constants
# -------------------------------------------------------------------------------------------------
# Database status. Status it determined with timestamps in control_dic
MAME_XML_EXTRACTED    = 100
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
