# -*- coding: utf-8 -*-

# Advanced MAME Launcher main script file.

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
# Division operator: https://www.python.org/dev/peps/pep-0238/
from __future__ import unicode_literals
from __future__ import division
import copy
import datetime
import os
import subprocess
import urlparse

# --- Kodi stuff ---
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# --- Modules/packages in this plugin ---
# Addon module dependencies:
#   main <-- mame <-- disk_IO <-- assets, misc, utils, utils_kodi, constants
#   mame <-- filters <-- misc, utils, utils_kodi, constants
#   manuals <- misc, utils, utils_kodi, constants
#   graphics <- misc, utils, utils_kodi, constants
from .constants import *
from .assets import *
from .utils import *
from .utils_kodi import *
from .disk_IO import *
from .filters import *
from .mame import *
from .manuals import *
from .graphics import *

# --- Addon object (used to access settings) ---
__addon__         = xbmcaddon.Addon()
__addon_id__      = __addon__.getAddonInfo('id').decode('utf-8')
__addon_name__    = __addon__.getAddonInfo('name').decode('utf-8')
__addon_version__ = __addon__.getAddonInfo('version').decode('utf-8')
__addon_author__  = __addon__.getAddonInfo('author').decode('utf-8')
__addon_profile__ = __addon__.getAddonInfo('profile').decode('utf-8')
__addon_type__    = __addon__.getAddonInfo('type').decode('utf-8')

# --- Plugin database indices ---
# _PATH is a filename | _DIR is a directory
class AML_Paths:
    def __init__(self):
        self.HOME_DIR         = FileName('special://home')
        self.PROFILE_DIR      = FileName('special://profile')
        self.ADDON_CODE_DIR   = self.HOME_DIR.pjoin('addons/' + __addon_id__)
        self.ADDON_DATA_DIR   = self.PROFILE_DIR.pjoin('addon_data/' + __addon_id__)
        self.ICON_FILE_PATH   = self.ADDON_CODE_DIR.pjoin('media/icon.png')
        self.FANART_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/fanart.jpg')

        # >> MAME stdout/strderr files
        self.MAME_STDOUT_PATH     = self.ADDON_DATA_DIR.pjoin('log_stdout.log')
        self.MAME_STDERR_PATH     = self.ADDON_DATA_DIR.pjoin('log_stderr.log')
        self.MAME_STDOUT_VER_PATH = self.ADDON_DATA_DIR.pjoin('log_version_stdout.log')
        self.MAME_STDERR_VER_PATH = self.ADDON_DATA_DIR.pjoin('log_version_stderr.log')
        self.MAME_OUTPUT_PATH     = self.ADDON_DATA_DIR.pjoin('log_output.log')
        self.MONO_FONT_PATH       = self.ADDON_CODE_DIR.pjoin('fonts/Inconsolata.otf')
        self.CUSTOM_FILTER_PATH   = self.ADDON_CODE_DIR.pjoin('filters/AML-MAME-filters.xml')

        # --- MAME XML, main database and main PClone list ---
        self.MAME_XML_PATH        = self.ADDON_DATA_DIR.pjoin('MAME.xml')
        self.MAIN_ASSETS_DB_PATH  = self.ADDON_DATA_DIR.pjoin('MAME_assets.json')
        self.MAIN_CONTROL_PATH    = self.ADDON_DATA_DIR.pjoin('MAME_control_dic.json')
        self.DEVICES_DB_PATH      = self.ADDON_DATA_DIR.pjoin('MAME_DB_devices.json')
        self.MAIN_DB_PATH         = self.ADDON_DATA_DIR.pjoin('MAME_DB_main.json')
        self.RENDER_DB_PATH       = self.ADDON_DATA_DIR.pjoin('MAME_DB_render.json')
        self.ROMS_DB_PATH         = self.ADDON_DATA_DIR.pjoin('MAME_DB_roms.json')
        self.SHA1_HASH_DB_PATH    = self.ADDON_DATA_DIR.pjoin('MAME_DB_SHA1_hashes.json')
        self.MAIN_PCLONE_DIC_PATH = self.ADDON_DATA_DIR.pjoin('MAME_DB_pclone_dic.json')

        # --- ROM set databases ---
        self.ROM_AUDIT_DB_PATH             = self.ADDON_DATA_DIR.pjoin('ROM_Audit_DB.json')
        self.ROM_SET_MACHINE_FILES_DB_PATH = self.ADDON_DATA_DIR.pjoin('ROM_Set_machine_files.json')
        self.ROM_SET_ROM_LIST_DB_PATH      = self.ADDON_DATA_DIR.pjoin('ROM_Set_ROM_list.json')
        self.ROM_SET_SAM_LIST_DB_PATH      = self.ADDON_DATA_DIR.pjoin('ROM_Set_Sample_list.json')
        self.ROM_SET_CHD_LIST_DB_PATH      = self.ADDON_DATA_DIR.pjoin('ROM_Set_CHD_list.json')

        # >> DAT indices and databases.
        self.HISTORY_IDX_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_History_index.json')
        self.HISTORY_DB_PATH   = self.ADDON_DATA_DIR.pjoin('DAT_History_DB.json')
        self.MAMEINFO_IDX_PATH = self.ADDON_DATA_DIR.pjoin('DAT_MAMEInfo_index.json')
        self.MAMEINFO_DB_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_MAMEInfo_DB.json')
        self.GAMEINIT_IDX_PATH = self.ADDON_DATA_DIR.pjoin('DAT_GameInit_index.json')
        self.GAMEINIT_DB_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_GameInit_DB.json')
        self.COMMAND_IDX_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_Command_index.json')
        self.COMMAND_DB_PATH   = self.ADDON_DATA_DIR.pjoin('DAT_Command_DB.json')

        # >> Most played and Recently played
        self.MAME_MOST_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('most_played_MAME.json')
        self.MAME_RECENT_PLAYED_FILE_PATH = self.ADDON_DATA_DIR.pjoin('recently_played_MAME.json')
        self.SL_MOST_PLAYED_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('most_played_SL.json')
        self.SL_RECENT_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('recently_played_SL.json')

        # >> Disabled. Now there are global properties for this.
        # self.MAIN_PROPERTIES_PATH = self.ADDON_DATA_DIR.pjoin('MAME_properties.json')

        # >> ROM cache
        self.CACHE_DIR        = self.ADDON_DATA_DIR.pjoin('cache')
        self.CACHE_INDEX_PATH = self.ADDON_DATA_DIR.pjoin('MAME_cache_index.json')

        # >> Catalogs
        self.CATALOG_DIR                          = self.ADDON_DATA_DIR.pjoin('catalogs')
        self.CATALOG_MAIN_PARENT_PATH             = self.CATALOG_DIR.pjoin('catalog_main_parents.json')
        self.CATALOG_MAIN_ALL_PATH                = self.CATALOG_DIR.pjoin('catalog_main_all.json')
        self.CATALOG_BINARY_PARENT_PATH           = self.CATALOG_DIR.pjoin('catalog_binary_parents.json')
        self.CATALOG_BINARY_ALL_PATH              = self.CATALOG_DIR.pjoin('catalog_binary_all.json')
        self.CATALOG_CATVER_PARENT_PATH           = self.CATALOG_DIR.pjoin('catalog_catver_parents.json')
        self.CATALOG_CATVER_ALL_PATH              = self.CATALOG_DIR.pjoin('catalog_catver_all.json')
        self.CATALOG_CATLIST_PARENT_PATH          = self.CATALOG_DIR.pjoin('catalog_catlist_parents.json')
        self.CATALOG_CATLIST_ALL_PATH             = self.CATALOG_DIR.pjoin('catalog_catlist_all.json')
        self.CATALOG_GENRE_PARENT_PATH            = self.CATALOG_DIR.pjoin('catalog_genre_parents.json')
        self.CATALOG_GENRE_ALL_PATH               = self.CATALOG_DIR.pjoin('catalog_genre_all.json')
        self.CATALOG_CATEGORY_PARENT_PATH         = self.CATALOG_DIR.pjoin('catalog_category_parents.json')
        self.CATALOG_CATEGORY_ALL_PATH            = self.CATALOG_DIR.pjoin('catalog_category_all.json')
        self.CATALOG_NPLAYERS_PARENT_PATH         = self.CATALOG_DIR.pjoin('catalog_nplayers_parents.json')
        self.CATALOG_NPLAYERS_ALL_PATH            = self.CATALOG_DIR.pjoin('catalog_nplayers_all.json')
        self.CATALOG_BESTGAMES_PARENT_PATH        = self.CATALOG_DIR.pjoin('catalog_bestgames_parents.json')
        self.CATALOG_BESTGAMES_ALL_PATH           = self.CATALOG_DIR.pjoin('catalog_bestgames_all.json')
        self.CATALOG_SERIES_PARENT_PATH           = self.CATALOG_DIR.pjoin('catalog_series_parents.json')
        self.CATALOG_SERIES_ALL_PATH              = self.CATALOG_DIR.pjoin('catalog_series_all.json')
        self.CATALOG_ALLTIME_PARENT_PATH          = self.CATALOG_DIR.pjoin('catalog_alltime_parents.json')
        self.CATALOG_ALLTIME_ALL_PATH             = self.CATALOG_DIR.pjoin('catalog_alltime_all.json')
        self.CATALOG_ARTWORK_PARENT_PATH          = self.CATALOG_DIR.pjoin('catalog_artwork_parents.json')
        self.CATALOG_ARTWORK_ALL_PATH             = self.CATALOG_DIR.pjoin('catalog_artwork_all.json')
        self.CATALOG_VERADDED_PARENT_PATH         = self.CATALOG_DIR.pjoin('catalog_version_parents.json')
        self.CATALOG_VERADDED_ALL_PATH            = self.CATALOG_DIR.pjoin('catalog_version_all.json')

        self.CATALOG_CONTROL_EXPANDED_PARENT_PATH = self.CATALOG_DIR.pjoin('catalog_control_expanded_parents.json')
        self.CATALOG_CONTROL_EXPANDED_ALL_PATH    = self.CATALOG_DIR.pjoin('catalog_control_expanded_all.json')
        self.CATALOG_CONTROL_COMPACT_PARENT_PATH  = self.CATALOG_DIR.pjoin('catalog_control_compact_parents.json')
        self.CATALOG_CONTROL_COMPACT_ALL_PATH     = self.CATALOG_DIR.pjoin('catalog_control_compact_all.json')
        self.CATALOG_DEVICE_EXPANDED_PARENT_PATH  = self.CATALOG_DIR.pjoin('catalog_device_expanded_parents.json')
        self.CATALOG_DEVICE_EXPANDED_ALL_PATH     = self.CATALOG_DIR.pjoin('catalog_device_expanded_all.json')
        self.CATALOG_DEVICE_COMPACT_PARENT_PATH   = self.CATALOG_DIR.pjoin('catalog_device_compact_parents.json')
        self.CATALOG_DEVICE_COMPACT_ALL_PATH      = self.CATALOG_DIR.pjoin('catalog_device_compact_all.json')
        self.CATALOG_DISPLAY_TYPE_PARENT_PATH     = self.CATALOG_DIR.pjoin('catalog_display_type_parents.json')
        self.CATALOG_DISPLAY_TYPE_ALL_PATH        = self.CATALOG_DIR.pjoin('catalog_display_type_all.json')
        self.CATALOG_DISPLAY_VSYNC_PARENT_PATH    = self.CATALOG_DIR.pjoin('catalog_display_vsync_parents.json')
        self.CATALOG_DISPLAY_VSYNC_ALL_PATH       = self.CATALOG_DIR.pjoin('catalog_display_vsync_all.json')
        self.CATALOG_DISPLAY_RES_PARENT_PATH      = self.CATALOG_DIR.pjoin('catalog_display_resolution_parents.json')
        self.CATALOG_DISPLAY_RES_ALL_PATH         = self.CATALOG_DIR.pjoin('catalog_display_resolution_all.json')
        self.CATALOG_CPU_PARENT_PATH              = self.CATALOG_DIR.pjoin('catalog_CPU_parents.json')
        self.CATALOG_CPU_ALL_PATH                 = self.CATALOG_DIR.pjoin('catalog_CPU_all.json')
        self.CATALOG_DRIVER_PARENT_PATH           = self.CATALOG_DIR.pjoin('catalog_driver_parents.json')
        self.CATALOG_DRIVER_ALL_PATH              = self.CATALOG_DIR.pjoin('catalog_driver_all.json')
        self.CATALOG_MANUFACTURER_PARENT_PATH     = self.CATALOG_DIR.pjoin('catalog_manufacturer_parents.json')
        self.CATALOG_MANUFACTURER_ALL_PATH        = self.CATALOG_DIR.pjoin('catalog_manufacturer_all.json')
        self.CATALOG_SHORTNAME_PARENT_PATH        = self.CATALOG_DIR.pjoin('catalog_shortname_parents.json')
        self.CATALOG_SHORTNAME_ALL_PATH           = self.CATALOG_DIR.pjoin('catalog_shortname_all.json')
        self.CATALOG_LONGNAME_PARENT_PATH         = self.CATALOG_DIR.pjoin('catalog_longname_parents.json')
        self.CATALOG_LONGNAME_ALL_PATH            = self.CATALOG_DIR.pjoin('catalog_longname_all.json')
        self.CATALOG_SL_PARENT_PATH               = self.CATALOG_DIR.pjoin('catalog_SL_parents.json')
        self.CATALOG_SL_ALL_PATH                  = self.CATALOG_DIR.pjoin('catalog_SL_all.json')
        self.CATALOG_YEAR_PARENT_PATH             = self.CATALOG_DIR.pjoin('catalog_year_parents.json')
        self.CATALOG_YEAR_ALL_PATH                = self.CATALOG_DIR.pjoin('catalog_year_all.json')

        # >> Distributed hashed database
        self.MAIN_DB_HASH_DIR      = self.ADDON_DATA_DIR.pjoin('hash')
        self.ROMS_DB_HASH_DIR      = self.ADDON_DATA_DIR.pjoin('hash_ROM')
        self.ROM_AUDIT_DB_HASH_DIR = self.ADDON_DATA_DIR.pjoin('hash_ROM_Audit')

        # >> MAME custom filters
        self.FILTERS_DB_DIR     = self.ADDON_DATA_DIR.pjoin('filters')
        self.FILTERS_INDEX_PATH = self.ADDON_DATA_DIR.pjoin('Filter_index.json')

        # >> Software Lists
        self.SL_DB_DIR             = self.ADDON_DATA_DIR.pjoin('SoftwareLists')
        self.SL_NAMES_PATH         = self.ADDON_DATA_DIR.pjoin('SoftwareLists_names.json')
        self.SL_INDEX_PATH         = self.ADDON_DATA_DIR.pjoin('SoftwareLists_index.json')
        self.SL_MACHINES_PATH      = self.ADDON_DATA_DIR.pjoin('SoftwareLists_machines.json')
        self.SL_PCLONE_DIC_PATH    = self.ADDON_DATA_DIR.pjoin('SoftwareLists_pclone_dic.json')
        # >> Disabled. There are global properties
        # self.SL_MACHINES_PROP_PATH = self.ADDON_DATA_DIR.pjoin('SoftwareLists_properties.json')

        # >> Favourites
        self.FAV_MACHINES_PATH = self.ADDON_DATA_DIR.pjoin('Favourite_Machines.json')
        self.FAV_SL_ROMS_PATH  = self.ADDON_DATA_DIR.pjoin('Favourite_SL_ROMs.json')

        # >> ROM/CHD scanner reports. These reports show missing ROM/CHDs only.
        self.REPORTS_DIR                             = self.ADDON_DATA_DIR.pjoin('reports')
        self.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH = self.REPORTS_DIR.pjoin('Scanner_MAME_machine_archives_full.txt')
        self.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH = self.REPORTS_DIR.pjoin('Scanner_MAME_machine_archives_have.txt')
        self.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH = self.REPORTS_DIR.pjoin('Scanner_MAME_machine_archives_miss.txt')
        self.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH     = self.REPORTS_DIR.pjoin('Scanner_MAME_ROM_list_miss.txt')
        self.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH     = self.REPORTS_DIR.pjoin('Scanner_MAME_SAM_list_miss.txt')
        self.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH     = self.REPORTS_DIR.pjoin('Scanner_MAME_CHD_list_miss.txt')

        self.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH   = self.REPORTS_DIR.pjoin('Scanner_SL_item_archives_full.txt')
        self.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH   = self.REPORTS_DIR.pjoin('Scanner_SL_item_archives_have.txt')
        self.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH   = self.REPORTS_DIR.pjoin('Scanner_SL_item_archives_miss.txt')

        # >> Asset scanner reports. These reports show have and missing assets.
        self.REPORT_MAME_ASSETS_PATH = self.REPORTS_DIR.pjoin('Assets_MAME.txt')
        self.REPORT_SL_ASSETS_PATH   = self.REPORTS_DIR.pjoin('Assets_SL.txt')

        # >> Statistics report
        self.REPORT_STATS_PATH = self.REPORTS_DIR.pjoin('Statistics.txt')

        # >> Audit report
        self.REPORT_MAME_AUDIT_FULL_PATH           = self.REPORTS_DIR.pjoin('Audit_MAME_full.txt')
        self.REPORT_MAME_AUDIT_GOOD_PATH           = self.REPORTS_DIR.pjoin('Audit_MAME_good.txt')
        self.REPORT_MAME_AUDIT_ERRORS_PATH         = self.REPORTS_DIR.pjoin('Audit_MAME_errors.txt')
        self.REPORT_MAME_AUDIT_ROM_GOOD_PATH       = self.REPORTS_DIR.pjoin('Audit_MAME_ROMs_good.txt')
        self.REPORT_MAME_AUDIT_ROM_ERRORS_PATH     = self.REPORTS_DIR.pjoin('Audit_MAME_ROMs_errors.txt')
        self.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH   = self.REPORTS_DIR.pjoin('Audit_MAME_SAMPLES_good.txt')
        self.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH = self.REPORTS_DIR.pjoin('Audit_MAME_SAMPLES_errors.txt')
        self.REPORT_MAME_AUDIT_CHD_GOOD_PATH       = self.REPORTS_DIR.pjoin('Audit_MAME_CHDs_good.txt')
        self.REPORT_MAME_AUDIT_CHD_ERRORS_PATH     = self.REPORTS_DIR.pjoin('Audit_MAME_CHDs_errors.txt')

        self.REPORT_SL_AUDIT_FULL_PATH         = self.REPORTS_DIR.pjoin('Audit_SL_full.txt')
        self.REPORT_SL_AUDIT_GOOD_PATH         = self.REPORTS_DIR.pjoin('Audit_SL_good.txt')
        self.REPORT_SL_AUDIT_ERRORS_PATH       = self.REPORTS_DIR.pjoin('Audit_SL_errors.txt')
        self.REPORT_SL_AUDIT_ROMS_GOOD_PATH    = self.REPORTS_DIR.pjoin('Audit_SL_ROMs_good.txt')
        self.REPORT_SL_AUDIT_ROMS_ERRORS_PATH  = self.REPORTS_DIR.pjoin('Audit_SL_ROMs_errors.txt')
        self.REPORT_SL_AUDIT_CHDS_GOOD_PATH    = self.REPORTS_DIR.pjoin('Audit_SL_CHDs_good.txt')
        self.REPORT_SL_AUDIT_CHDS_ERRORS_PATH  = self.REPORTS_DIR.pjoin('Audit_SL_CHDs_errors.txt')

        # >> Custom filters report.
        self.REPORT_CF_XML_SYNTAX_PATH = self.REPORTS_DIR.pjoin('Custom_filter_XML_check.txt')
        self.REPORT_CF_DB_BUILD_PATH   = self.REPORTS_DIR.pjoin('Custom_filter_database_report.txt')
        self.REPORT_CF_HISTOGRAMS_PATH = self.REPORTS_DIR.pjoin('Custom_filter_histogram.txt')

        # >> DEBUG data
        self.REPORT_DEBUG_MAME_ITEM_DATA_PATH       = self.REPORTS_DIR.pjoin('debug_MAME_item_data.txt')
        self.REPORT_DEBUG_MAME_ITEM_ROM_DATA_PATH   = self.REPORTS_DIR.pjoin('debug_MAME_item_ROM_DB_data.txt')
        self.REPORT_DEBUG_MAME_ITEM_AUDIT_DATA_PATH = self.REPORTS_DIR.pjoin('debug_MAME_item_Audit_DB_data.txt')
        self.REPORT_DEBUG_SL_ITEM_DATA_PATH         = self.REPORTS_DIR.pjoin('debug_SL_item_data.txt')
        self.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH     = self.REPORTS_DIR.pjoin('debug_SL_item_ROM_DB_data.txt')
        self.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH   = self.REPORTS_DIR.pjoin('debug_SL_item_Audit_DB_data.txt')
        self.REPORT_DEBUG_MAME_COLLISIONS_PATH      = self.REPORTS_DIR.pjoin('debug_MAME_collisions.txt')
        self.REPORT_DEBUG_SL_COLLISIONS_PATH        = self.REPORTS_DIR.pjoin('debug_SL_collisions.txt')

# --- Global variables ---
g_PATHS = AML_Paths()
g_settings = {}
g_base_url = ''
g_addon_handle = 0
g_content_type = ''
g_time_str = unicode(datetime.datetime.now())

g_mame_icon = ''
g_mame_fanart = ''
g_SL_icon = ''
g_SL_fanart = ''

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin(addon_argv):
    global g_base_url
    global g_addon_handle
    global g_content_type

    # --- Initialise log system ---
    # >> Force DEBUG log level for development.
    # >> Place it before setting loading so settings can be dumped during debugging.
    # set_log_level(LOG_DEBUG)

    # --- Fill in settings dictionary using addon_obj.getSetting() ---
    get_settings()
    set_log_level(g_settings['log_level'])

    # --- Some debug stuff for development ---
    log_debug('---------- Called AML Main::run_plugin() constructor ----------')
    log_debug('sys.platform    {0}'.format(sys.platform))
    log_debug('Python version  ' + sys.version.replace('\n', ''))
    log_debug('__a_id__        {0}'.format(__addon_id__))
    log_debug('__a_version__   {0}'.format(__addon_version__))
    # log_debug('ADDON_DATA_DIR {0}'.format(g_PATHS.ADDON_DATA_DIR.getPath()))
    for i in range(len(addon_argv)): log_debug('addon_argv[{0}] = "{1}"'.format(i, addon_argv[i]))
    # Timestamp to see if this submodule is reinterpreted or not (interpreter uses a cached instance).
    log_debug('submodule global timestamp {0}'.format(g_time_str))

    # --- Addon data paths creation ---
    if not g_PATHS.ADDON_DATA_DIR.exists(): g_PATHS.ADDON_DATA_DIR.makedirs()
    if not g_PATHS.CACHE_DIR.exists(): g_PATHS.CACHE_DIR.makedirs()
    if not g_PATHS.CATALOG_DIR.exists(): g_PATHS.CATALOG_DIR.makedirs()
    if not g_PATHS.MAIN_DB_HASH_DIR.exists(): g_PATHS.MAIN_DB_HASH_DIR.makedirs()
    if not g_PATHS.FILTERS_DB_DIR.exists(): g_PATHS.FILTERS_DB_DIR.makedirs()
    if not g_PATHS.SL_DB_DIR.exists(): g_PATHS.SL_DB_DIR.makedirs()
    if not g_PATHS.REPORTS_DIR.exists(): g_PATHS.REPORTS_DIR.makedirs()

    # --- If control_dic does not exists create an empty one ---
    # >> control_dic will be used for database built checks, etc.
    if not g_PATHS.MAIN_CONTROL_PATH.exists(): fs_create_empty_control_dic(g_PATHS, __addon_version__)

    # --- Process URL ---
    g_base_url = addon_argv[0]
    g_addon_handle = int(addon_argv[1])
    args = urlparse.parse_qs(addon_argv[2][1:])
    # log_debug('args = {0}'.format(args))
    # Interestingly, if plugin is called as type executable then args is empty.
    # However, if plugin is called as type game then Kodi adds the following
    # even for the first call: 'content_type': ['game']
    g_content_type = args['content_type'] if 'content_type' in args else None
    log_debug('content_type = {0}'.format(g_content_type))

    # --- URL routing -------------------------------------------------------------------------
    # Show addon root window.
    args_size = len(args)
    if not 'catalog' in args and not 'command' in args:
        render_root_list()
        log_debug('Advanced MAME Launcher exit (addon root)')
        return

    # Render a list of something.
    elif 'catalog' in args and not 'command' in args:
        catalog_name = args['catalog'][0]
        # --- Software list is a special case ---
        if catalog_name == 'SL' or catalog_name == 'SL_ROM' or \
           catalog_name == 'SL_CHD' or catalog_name == 'SL_ROM_CHD' or \
           catalog_name == 'SL_empty':
            SL_name     = args['category'][0] if 'category' in args else ''
            parent_name = args['parent'][0] if 'parent' in args else ''
            if SL_name and parent_name:
                render_SL_pclone_set(SL_name, parent_name)
            elif SL_name and not parent_name:
                render_SL_ROMs(SL_name)
            else:
                render_SL_list(catalog_name)
        # --- Custom filters ---
        elif catalog_name == 'Custom':
            render_custom_filter_machines(args['category'][0])
        # --- DAT browsing ---
        elif catalog_name == 'History' or catalog_name == 'MAMEINFO' or \
             catalog_name == 'Gameinit' or catalog_name == 'Command':
            category_name = args['category'][0] if 'category' in args else ''
            machine_name = args['machine'][0] if 'machine' in args else ''
            if category_name and machine_name:
                render_DAT_machine_info(catalog_name, category_name, machine_name)
            elif category_name and not machine_name:
                render_DAT_category(catalog_name, category_name)
            else:
                render_DAT_list(catalog_name)
        else:
            category_name = args['category'][0] if 'category' in args else ''
            parent_name   = args['parent'][0] if 'parent' in args else ''
            if category_name and parent_name:
                render_catalog_clone_list(catalog_name, category_name, parent_name)
            elif category_name and not parent_name:
                render_catalog_parent_list(catalog_name, category_name)
            else:
                render_catalog_list(catalog_name)

    # Execute a command.
    elif 'command' in args:
        command = args['command'][0]

        # >> Commands used by skins to render items of the addon root menu.
        if   command == 'SKIN_SHOW_FAV_SLOTS':       render_skin_fav_slots()
        elif command == 'SKIN_SHOW_MAIN_FILTERS':    render_skin_main_filters()
        elif command == 'SKIN_SHOW_BINARY_FILTERS':  render_skin_binary_filters()
        elif command == 'SKIN_SHOW_CATALOG_FILTERS': render_skin_catalog_filters()
        elif command == 'SKIN_SHOW_DAT_SLOTS':       render_skin_dat_slots()
        elif command == 'SKIN_SHOW_SL_FILTERS':      render_skin_SL_filters()

        # >> Auxiliar commands from parent machine context menu
        # >> Not sure if this will cause problems with the concurrent protected code once it's
        #    implemented.
        elif command == 'EXEC_SHOW_MAME_CLONES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            machine_name  = args['parent'][0] if 'parent' in args else ''
            url = misc_url_3_arg('catalog', catalog_name, 'category', category_name, 'parent', machine_name)
            xbmc.executebuiltin('Container.Update({0})'.format(url))

        elif command == 'EXEC_SHOW_SL_CLONES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            machine_name  = args['parent'][0] if 'parent' in args else ''
            url = misc_url_3_arg('catalog', 'SL', 'category', category_name, 'parent', machine_name)
            xbmc.executebuiltin('Container.Update({0})'.format(url))

        # >> If location is not present in the URL default to standard.
        elif command == 'LAUNCH':
            machine  = args['machine'][0]
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            log_info('Launching MAME machine "{0}" in "{1}"'.format(machine, location))
            run_machine(machine, location)
        elif command == 'LAUNCH_SL':
            SL_name  = args['SL'][0]
            ROM_name = args['ROM'][0]
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            log_info('Launching SL machine "{0}" (ROM "{1}")'.format(SL_name, ROM_name))
            run_SL_machine(SL_name, ROM_name, location)

        elif command == 'SETUP_PLUGIN':
            command_context_setup_plugin()

        #
        # Not used at the moment.
        # Instead of per-catalog display mode settings there are global settings.
        #
        elif command == 'DISPLAY_SETTINGS_MAME':
            catalog_name = args['catalog'][0]
            category_name = args['category'][0] if 'category' in args else ''
            command_context_display_settings(catalog_name, category_name)
        elif command == 'DISPLAY_SETTINGS_SL':
            command_context_display_settings_SL(args['category'][0])
        elif command == 'VIEW_DAT':
            machine  = args['machine'][0]  if 'machine'  in args else ''
            SL       = args['SL'][0]       if 'SL'       in args else ''
            ROM      = args['ROM'][0]      if 'ROM'      in args else ''
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            command_context_view_DAT(machine, SL, ROM, location)
        elif command == 'VIEW':
            machine  = args['machine'][0]  if 'machine'  in args else ''
            SL       = args['SL'][0]       if 'SL'       in args else ''
            ROM      = args['ROM'][0]      if 'ROM'      in args else ''
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            command_context_view(machine, SL, ROM, location)
        elif command == 'UTILITIES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            command_context_utilities(catalog_name, category_name)

        # >> MAME Favourites
        elif command == 'ADD_MAME_FAV':
            command_context_add_mame_fav(args['machine'][0])
        elif command == 'MANAGE_MAME_FAV':
            # If called from the root menu machine is empty.
            machine = args['machine'][0] if 'machine' in args else ''
            command_context_manage_mame_fav(machine)
        elif command == 'SHOW_MAME_FAVS':
            command_show_mame_fav()

        # >> Most and Recently played
        elif command == 'SHOW_MAME_MOST_PLAYED':
            command_show_mame_most_played()
        elif command == 'MANAGE_MAME_MOST_PLAYED':
            m_name = args['machine'][0] if 'machine' in args else ''
            command_context_manage_mame_most_played(m_name)

        elif command == 'SHOW_MAME_RECENTLY_PLAYED':
            command_show_mame_recently_played()
        elif command == 'MANAGE_MAME_RECENT_PLAYED':
            m_name = args['machine'][0] if 'machine' in args else ''
            command_context_manage_mame_recent_played(m_name)

        # >> SL Favourites
        elif command == 'ADD_SL_FAV':
            command_context_add_sl_fav(args['SL'][0], args['ROM'][0])
        elif command == 'MANAGE_SL_FAV':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            command_context_manage_sl_fav(SL_name, ROM_name)
        elif command == 'SHOW_SL_FAVS':
            command_show_sl_fav()

        elif command == 'SHOW_SL_MOST_PLAYED':
            command_show_SL_most_played()
        elif command == 'MANAGE_SL_MOST_PLAYED':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            command_context_manage_SL_most_played(SL_name, ROM_name)

        elif command == 'SHOW_SL_RECENTLY_PLAYED':
            command_show_SL_recently_played()
        elif command == 'MANAGE_SL_RECENT_PLAYED':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            command_context_manage_SL_recent_played(SL_name, ROM_name)

        # >> Custom filters
        elif command == 'SHOW_CUSTOM_FILTERS':
            command_show_custom_filters()
        elif command == 'SETUP_CUSTOM_FILTERS':
            command_context_setup_custom_filters()

        # >> Utilities and global reports.
        elif command == 'SHOW_UTILITIES_VLAUNCHERS':
            render_Utilities_vlaunchers()
        elif command == 'SHOW_GLOBALREPORTS_VLAUNCHERS':
            render_GlobalReports_vlaunchers()

        # >> Execute Utilities
        elif command == 'EXECUTE_UTILITY':
            which_utility = args['which'][0]
            command_exec_utility(which_utility)

        # >> Execute View Reports
        elif command == 'EXECUTE_REPORT':
            which_report = args['which'][0]
            command_exec_report(which_report)

        else:
            u = 'Unknown command "{0}"'.format(command)
            log_error(u)
            kodi_dialog_OK(u)
            xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
    else:
        u = 'Error in URL routing'
        log_error(u)
        kodi_dialog_OK(u)
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

    # --- So Long, and Thanks for All the Fish ---
    log_debug('Advanced MAME Launcher exit')

#
# Get Addon Settings
#
def get_settings():
    global g_settings
    global g_mame_icon
    global g_mame_fanart
    global g_SL_icon
    global g_SL_fanart
    o = __addon__

    # --- Main operation ---
    g_settings['op_mode_raw']    = int(o.getSetting('op_mode_raw'))
    g_settings['enable_SL']      = True if o.getSetting('enable_SL') == 'true' else False
    g_settings['mame_prog']      = o.getSetting('mame_prog').decode('utf-8')
    g_settings['SL_hash_path'] = o.getSetting('SL_hash_path').decode('utf-8')

    g_settings['retroarch_prog'] = o.getSetting('retroarch_prog').decode('utf-8')
    g_settings['libretro_dir']   = o.getSetting('libretro_dir').decode('utf-8')
    g_settings['xml_2003_path']  = o.getSetting('xml_2003_path').decode('utf-8')

    # --- Optional paths ---
    g_settings['rom_path']     = o.getSetting('rom_path').decode('utf-8')
    g_settings['assets_path']  = o.getSetting('assets_path').decode('utf-8')
    g_settings['dats_path']    = o.getSetting('dats_path').decode('utf-8')
    g_settings['chd_path']     = o.getSetting('chd_path').decode('utf-8')
    g_settings['samples_path'] = o.getSetting('samples_path').decode('utf-8')
    g_settings['SL_rom_path']  = o.getSetting('SL_rom_path').decode('utf-8')
    g_settings['SL_chd_path']  = o.getSetting('SL_chd_path').decode('utf-8')

    # --- ROM sets ---
    g_settings['mame_rom_set'] = int(o.getSetting('mame_rom_set'))
    g_settings['mame_chd_set'] = int(o.getSetting('mame_chd_set'))
    g_settings['SL_rom_set']   = int(o.getSetting('SL_rom_set'))
    g_settings['SL_chd_set']   = int(o.getSetting('SL_chd_set'))
    g_settings['filter_XML']   = o.getSetting('filter_XML').decode('utf-8')

    # --- Display I ---
    g_settings['display_launcher_notify'] = True if o.getSetting('display_launcher_notify') == 'true' else False
    g_settings['mame_view_mode']          = int(o.getSetting('mame_view_mode'))
    g_settings['sl_view_mode']            = int(o.getSetting('sl_view_mode'))
    g_settings['display_hide_Mature']     = True if o.getSetting('display_hide_Mature') == 'true' else False
    g_settings['display_hide_BIOS']       = True if o.getSetting('display_hide_BIOS') == 'true' else False
    g_settings['display_hide_imperfect']  = True if o.getSetting('display_hide_imperfect') == 'true' else False
    g_settings['display_hide_nonworking'] = True if o.getSetting('display_hide_nonworking') == 'true' else False
    g_settings['display_rom_available']   = True if o.getSetting('display_rom_available') == 'true' else False
    g_settings['display_chd_available']   = True if o.getSetting('display_chd_available') == 'true' else False

    # --- Display II ---
    g_settings['display_main_filters']    = True if o.getSetting('display_main_filters') == 'true' else False
    g_settings['display_binary_filters']  = True if o.getSetting('display_binary_filters') == 'true' else False
    g_settings['display_catalog_filters'] = True if o.getSetting('display_catalog_filters') == 'true' else False
    g_settings['display_DAT_browser']     = True if o.getSetting('display_DAT_browser') == 'true' else False
    g_settings['display_SL_browser']      = True if o.getSetting('display_SL_browser') == 'true' else False
    g_settings['display_custom_filters']  = True if o.getSetting('display_custom_filters') == 'true' else False
    g_settings['display_ROLs']            = True if o.getSetting('display_ROLs') == 'true' else False
    g_settings['display_MAME_favs']       = True if o.getSetting('display_MAME_favs') == 'true' else False
    g_settings['display_MAME_most']       = True if o.getSetting('display_MAME_most') == 'true' else False
    g_settings['display_MAME_recent']     = True if o.getSetting('display_MAME_recent') == 'true' else False
    g_settings['display_SL_favs']         = True if o.getSetting('display_SL_favs') == 'true' else False
    g_settings['display_SL_most']         = True if o.getSetting('display_SL_most') == 'true' else False
    g_settings['display_SL_recent']       = True if o.getSetting('display_SL_recent') == 'true' else False
    g_settings['display_utilities']       = True if o.getSetting('display_utilities') == 'true' else False
    g_settings['display_global_reports']  = True if o.getSetting('display_global_reports') == 'true' else False

    # --- Display ---
    g_settings['artwork_mame_icon']     = int(o.getSetting('artwork_mame_icon'))
    g_settings['artwork_mame_fanart']   = int(o.getSetting('artwork_mame_fanart'))
    g_settings['artwork_SL_icon']       = int(o.getSetting('artwork_SL_icon'))
    g_settings['artwork_SL_fanart']     = int(o.getSetting('artwork_SL_fanart'))
    g_settings['display_hide_trailers'] = True if o.getSetting('display_hide_trailers') == 'true' else False

    # --- Utilities ---
    # Call to RunPlugin() built-in function.

    # --- Advanced ---
    g_settings['media_state_action']             = int(o.getSetting('media_state_action'))
    g_settings['delay_tempo']                    = int(round(float(o.getSetting('delay_tempo'))))
    g_settings['suspend_audio_engine']           = True if o.getSetting('suspend_audio_engine') == 'true' else False
    g_settings['toggle_window']                  = True if o.getSetting('toggle_window') == 'true' else False
    g_settings['log_level']                      = int(o.getSetting('log_level'))
    g_settings['debug_enable_MAME_render_cache'] = True if o.getSetting('debug_enable_MAME_render_cache') == 'true' else False
    g_settings['debug_enable_MAME_asset_cache']  = True if o.getSetting('debug_enable_MAME_asset_cache') == 'true' else False
    g_settings['debug_MAME_item_data']           = True if o.getSetting('debug_MAME_item_data') == 'true' else False
    g_settings['debug_MAME_ROM_DB_data']         = True if o.getSetting('debug_MAME_ROM_DB_data') == 'true' else False
    g_settings['debug_MAME_Audit_DB_data']       = True if o.getSetting('debug_MAME_Audit_DB_data') == 'true' else False
    g_settings['debug_SL_item_data']             = True if o.getSetting('debug_SL_item_data') == 'true' else False
    g_settings['debug_SL_ROM_DB_data']           = True if o.getSetting('debug_SL_ROM_DB_data') == 'true' else False
    g_settings['debug_SL_Audit_DB_data']         = True if o.getSetting('debug_SL_Audit_DB_data') == 'true' else False

    # --- Transform settings data ---
    g_settings['op_mode'] = OP_MODE_LIST[g_settings['op_mode_raw']]

    g_mame_icon   = assets_get_asset_key_MAME_icon(g_settings['artwork_mame_icon'])
    g_mame_fanart = assets_get_asset_key_MAME_fanart(g_settings['artwork_mame_fanart'])
    g_SL_icon     = assets_get_asset_key_SL_icon(g_settings['artwork_SL_icon'])
    g_SL_fanart   = assets_get_asset_key_SL_fanart(g_settings['artwork_SL_fanart'])

    # --- Dump settings for DEBUG ---
    # log_debug('Settings dump BEGIN')
    # for key in sorted(g_settings):
    #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(g_settings[key]), type(g_settings[key])))
    # log_debug('Settings dump END')

# ---------------------------------------------------------------------------------------------
# Root menu rendering
# ---------------------------------------------------------------------------------------------
root_Main = {}
root_Binary = {}
root_categories = {}
root_special = {}
root_SL = {}
root_special_CM = {}

def set_render_root_data():
    global root_Main
    global root_Binary
    global root_categories
    global root_special
    global root_SL
    global root_special_CM

    # Tuple: catalog_name, catalog_key, title, plot
    root_Main = {
        # Main filter Catalog
        'Main_Normal' : [
            'Main', 'Normal',
            'Machines with coin slot (Normal)',
            ('[COLOR orange]Main filter[/COLOR] of MAME machines [COLOR violet]with coin '
             'slot[/COLOR] and normal controls. This list includes the machines you would '
             'typically find in Europe and USA amusement arcades some decades ago.'),
        ],
        'Main_Unusual' : [
            'Main', 'Unusual',
            'Machines with coin slot (Unusual)',
            ('[COLOR orange]Main filter[/COLOR] of MAME machines [COLOR violet]with coin '
             'slot[/COLOR] and Only buttons, Gambling, Hanafuda and Mahjong controls. '
             'This corresponds to slot, gambling and Japanese card and mahjong machines.'),
        ],
        'Main_NoCoin' : [
            'Main', 'NoCoin',
            'Machines with no coin slot',
            ('[COLOR orange]Main filter[/COLOR] of MAME machines [COLOR violet]with no coin '
             'slot[/COLOR]. Here you will find the good old MESS machines, including computers, '
             'video game consoles, hand-held video game consoles, etc.'),
        ],
        'Main_Mechanical' : [
            'Main', 'Mechanical',
            'Mechanical machines',
            ('[COLOR orange]Main filter[/COLOR] of [COLOR violet]mechanical[/COLOR] MAME machines. '
             'These machines have mechanical parts, for example pinballs, and currently do not work with MAME. '
             'They are here for preservation and historical reasons.'),
        ],
        'Main_Dead' : [
            'Main', 'Dead',
            'Dead machines',
            ('[COLOR orange]Main filter[/COLOR] of [COLOR violet]dead[/COLOR] MAME machines. '
             'Dead machines do not work and have no controls, so you cannot interact with them in any way.'),
        ],
        'Main_Devices' : [
            'Main', 'Devices',
            'Device machines',
            ('[COLOR orange]Main filter[/COLOR] of [COLOR violet]device machines[/COLOR]. '
             'Device machines, for example the Zilog Z80 CPU, are components used by other machines '
             'and cannot be run on their own.'),
        ],
    }

    # Tuple: catalog_name, catalog_key, title, plot
    root_Binary = {
        # Binary filters Catalog
        'BIOS' : [
            'Binary', 'BIOS',
            'Machines [BIOS]',
            ('[COLOR orange]Binary filter[/COLOR] of [COLOR violet]BIOS[/COLOR] machines. Some BIOS '
             'machines can be run and usually will display a message like "Game not found".'),
        ],
        'CHD' : [
            'Binary', 'CHD',
            'Machines [with CHDs]',
            ('[COLOR orange]Binary filter[/COLOR] of machines that need one or more '
             '[COLOR violet]CHDs[/COLOR] to run. They may also need ROMs and/or BIOS or not.'),
        ],
        'Samples' : [
            'Binary', 'Samples',
            'Machines [with Samples]',
            ('[COLOR orange]Binary filter[/COLOR] of machines that require '
             '[COLOR violet]samples[/COLOR]. Samples are optional and will increase the quality '
             'of the emulated sound.'),
        ],
        'SoftwareLists' : [
            'Binary', 'SoftwareLists',
            'Machines [with Software Lists]',
            ('[COLOR orange]Binary filter[/COLOR] of machines that have one or more '
             '[COLOR violet]Software Lists[/COLOR] associated.'),
        ],
    }

    # Tuple: title, plot, URL
    root_categories = {
        # Cataloged filters (optional DAT/INI files required)
        'Catver' : [
            'Machines by Category (Catver)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by category. '
             'This filter requires that you configure [COLOR violet]catver.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Catver'),
        ],
        'Catlist' : [
            'Machines by Category (Catlist)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by category. '
             'This filter requires that you configure [COLOR violet]catlist.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Catlist'),
        ],
        'Genre' : [
            'Machines by Category (Genre)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Genre. '
             'This filter requires that you configure [COLOR violet]genre.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Genre'),
        ],
        'Category' : [
            'Machines by Category (MASH)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Category. '
             'This filter requires that you configure [COLOR violet]Category.ini[/COLOR] by MASH.'),
            misc_url_1_arg('catalog', 'Category'),
        ],
        'NPlayers' : [
            'Machines by Number of players',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by the number of '
             'players that can play simultaneously or alternatively. This filter requires '
             'that you configure [COLOR violet]nplayers.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'NPlayers'),
        ],
        'Bestgames' : [
            'Machines by Rating',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by rating. The rating '
             'is subjective but is a good indicator about the quality of the games. '
             'This filter requires that you configure [COLOR violet]bestgames.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Bestgames'),
        ],
        'Series' : [
            'Machines by Series',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by series. '
             'This filter requires that you configure [COLOR violet]series.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Series'),
        ],
        'Alltime' : [
            'Machines by Alltime (MASH)',
            ('[COLOR orange]Catalog filter[/COLOR] of a best-quality machine selection '
             'sorted by year. '
             'This filter requires that you configure [COLOR violet]Alltime.ini[/COLOR] by MASH.'),
            misc_url_1_arg('catalog', 'Alltime'),
        ],
        'Artwork' : [
            'Machines by Artwork (MASH)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Artwork. '
             'This filter requires that you configure [COLOR violet]Artwork.ini[/COLOR] by MASH.'),
            misc_url_1_arg('catalog', 'Artwork'),
        ],
        'Version' : [
            'Machines by Version Added (Catver)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Version Added. '
             'This filter requires that you configure [COLOR violet]catver.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Version'),
        ],

        # Cataloged filters (always there, extracted from MAME XML)
        # NOTE: use the same names as MAME executable
        # -listdevices   list available devices                  XML tag <device_ref>
        # -listslots     list available slots and slot devices   XML tag <slot>
        # -listmedia     list available media for the system     XML tag <device>
        'Controls_Expanded' : [
            'Machines by Controls (Expanded)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by control. '
             'For each machine, all controls are included in the list.'),
            misc_url_1_arg('catalog', 'Controls_Expanded'),
        ],
        'Controls_Compact' : [
            'Machines by Controls (Compact)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by control. '
             'Machines may have additional controls.'),
            misc_url_1_arg('catalog', 'Controls_Compact'),
        ],
        'Devices_Expanded' : [
            'Machines by Pluggable Devices (Expanded)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by pluggable devices. '
             'For each machine, all pluggable devices are included in the list.'),
            misc_url_1_arg('catalog', 'Devices_Expanded'),
        ],
        'Devices_Compact' : [
            'Machines by Pluggable Devices (Compact)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by pluggable devices. '
             'Machines may have additional pluggable devices.'),
            misc_url_1_arg('catalog', 'Devices_Compact'),
        ],
        'Display_Type' : [
            'Machines by Display Type',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by display type '
             'and rotation.'),
            misc_url_1_arg('catalog', 'Display_Type'),
        ],
        'Display_VSync' : [
            'Machines by Display VSync freq',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by the display '
             'vertical synchronisation (VSync) frequency, also known as the display refresh rate or '
             'frames per second (FPS).'),
            misc_url_1_arg('catalog', 'Display_VSync'),
        ],
        'Display_Resolution' : [
            'Machines by Display Resolution',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by display resolution.'),
            misc_url_1_arg('catalog', 'Display_Resolution'),
        ],
        'CPU' : [
            'Machines by CPU',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by the CPU used.'),
            misc_url_1_arg('catalog', 'CPU'),
        ],
        'Driver' : [
            'Machines by Driver',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by driver. '
             'Brother machines have the same driver.'),
            misc_url_1_arg('catalog', 'Driver'),
        ],
        'Manufacturer' : [
            'Machines by Manufacturer',
            ('[COLOR orange]Catalog filter[/COLOR] of MAME machines sorted by '
             'manufacturer.'),
            misc_url_1_arg('catalog', 'Manufacturer'),
        ],
        'ShortName' : [
            'Machines by MAME short name',
            ('[COLOR orange]Catalog filter[/COLOR] of MAME machines sorted alphabetically '
             'by the MAME short name. The short name originated during the old MS-DOS days '
             'where filenames were restricted to 8 ASCII characters.'),
            misc_url_1_arg('catalog', 'ShortName'),
        ],
        'LongName' : [
            'Machines by MAME long name',
            ('[COLOR orange]Catalog filter[/COLOR] of MAME machines sorted alphabetically '
             'by the machine description or long name.'),
            misc_url_1_arg('catalog', 'LongName'),
        ],
        'BySL' : [
            'Machines by Software List',
            ('[COLOR orange]Catalog filter[/COLOR] of the Software Lists and the machines '
             'that run items belonging to that Software List.'),
            misc_url_1_arg('catalog', 'BySL'),
        ],
        'Year' : [
            'Machines by Year',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by release year.'),
            misc_url_1_arg('catalog', 'Year'),
        ],
    }

    # Tuple: title, plot, URL
    root_special = {
        # DAT browser: history.dat, mameinfo.dat, gameinit.dat, command.dat.
        'History' : [
            'History DAT',
            ('Browse the contents of [COLOR orange]history.dat[/COLOR]. Note that '
             'history.dat is also available on the MAME machines and SL items context menu.'),
            misc_url_1_arg('catalog', 'History'),
        ],
        'MAMEINFO' : [
            'MAMEINFO DAT',
            ('Browse the contents of [COLOR orange]mameinfo.dat[/COLOR]. Note that '
             'mameinfo.dat is also available on the MAME machines context menu.'),
            misc_url_1_arg('catalog', 'MAMEINFO'),
        ],
        'Gameinit' : [
            'Gameinit DAT',
            ('Browse the contents of [COLOR orange]gameinit.dat[/COLOR]. Note that '
             'gameinit.dat is also available on the MAME machines context menu.'),
            misc_url_1_arg('catalog', 'Gameinit'),
        ],
        'Command' : [
            'Command DAT',
            ('Browse the contents of [COLOR orange]command.dat[/COLOR]. Note that '
             'command.dat is also available on the MAME machines context menu.'),
            misc_url_1_arg('catalog', 'Command'),
        ],
    }

    # Tuple: title, plot, URL
    root_SL = {
        'SL' : [
            'Software Lists (all)',
            ('Display all [COLOR orange]Software Lists[/COLOR].'),
            misc_url_1_arg('catalog', 'SL'),
        ],
        'SL_ROM' : [
            'Software Lists (with ROMs)',
            ('Display [COLOR orange]Software Lists[/COLOR] that have only ROMs and not CHDs (disks).'),
            misc_url_1_arg('catalog', 'SL_ROM'),
        ],
        'SL_ROM_CHD' : [
            'Software Lists (with ROMs and CHDs)',
            ('Display [COLOR orange]Software Lists[/COLOR] that have both ROMs and CHDs.'),
            misc_url_1_arg('catalog', 'SL_ROM_CHD'),
        ],
        'SL_CHD' : [
            'Software Lists (with CHDs)',
            ('Display [COLOR orange]Software Lists[/COLOR] that have only CHDs and not ROMs.'),
            misc_url_1_arg('catalog', 'SL_CHD'),
        ],
        'SL_empty' : [
            'Software Lists (no ROMs nor CHDs)',
            ('Display [COLOR orange]Software Lists[/COLOR] with no ROMs nor CHDs.'),
            misc_url_1_arg('catalog', 'SL_empty'),
        ],
    }

    # Tuple: title, plot, URL, context_menu_list
    root_special_CM = {
        'MAME_Favs' : [
            '<Favourite MAME machines>',
            ('Display your [COLOR orange]Favourite MAME machines[/COLOR]. '
             'To add machines to the Favourite list use the context menu on any MAME machine list.'),
            misc_url_1_arg('command', 'SHOW_MAME_FAVS'),
            [('Manage Favourites', misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_FAV'))],
        ],
        'MAME_Most' : [
            '{Most Played MAME machines}',
            ('Display the MAME machines that you play most, sorted by the number '
             'of times you have launched them.'),
            misc_url_1_arg('command', 'SHOW_MAME_MOST_PLAYED'),
            [('Manage Most Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_MOST_PLAYED'))],
        ],
        'MAME_Recent' : [
            '{Recently Played MAME machines}',
            ('Display the MAME machines that you have launched recently.'),
            misc_url_1_arg('command', 'SHOW_MAME_RECENTLY_PLAYED'),
            [('Manage Recently Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_RECENT_PLAYED'))],
        ],
        'SL_Favs' : [
            '<Favourite Software Lists ROMs>',
            ('Display your [COLOR orange]Favourite Software List items[/COLOR]. '
             'To add machines to the SL Favourite list use the context menu on any SL item list.'),
            misc_url_1_arg('command', 'SHOW_SL_FAVS'),
            [('Manage SL Favourites', misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_FAV'))],
        ],
        'SL_Most' : [
            '{Most Played SL ROMs}',
            ('Display the Software List itmes that you play most, sorted by the number '
             'of times you have launched them.'),
            misc_url_1_arg('command', 'SHOW_SL_MOST_PLAYED'),
            [('Manage SL Most Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_MOST_PLAYED'))],
        ],
        'SL_Recent' : [
            '{Recently Played SL ROMs}',
            'Display the Software List items that you have launched recently.',
            misc_url_1_arg('command', 'SHOW_SL_RECENTLY_PLAYED'),
            [('Manage SL Recently Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_RECENT_PLAYED'))],
        ],
        'Custom_Filters' : [
            '[Custom MAME filters]',
            ('[COLOR orange]Custom filters[/COLOR] allows to generate machine '
             'listings perfectly tailored to your whises. For example, you can define a filter of all '
             'the machines released in the 1980s that use a joystick. AML includes a fairly '
             'complete default set of filters in XML format which can be edited.'),
            misc_url_1_arg('command', 'SHOW_CUSTOM_FILTERS'),
            [('Setup custom filters', misc_url_1_arg_RunPlugin('command', 'SETUP_CUSTOM_FILTERS'))],
        ],
    }

def render_root_list():
    mame_view_mode = g_settings['mame_view_mode']
    set_render_root_data()

    # ----- Machine count -----
    cache_index_dic = fs_load_JSON_file_dic(g_PATHS.CACHE_INDEX_PATH.getPath())
    SL_index_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())

    # Do not crash if cache_index_dic is corrupted or has missing fields (may happen in
    # upgrades). This function must never crash because the user must have always access to
    # the setup menu.
    try:
        num_m_Main_Normal = cache_index_dic['Main']['Normal']['num_machines']
        num_m_Main_Unusual = cache_index_dic['Main']['Unusual']['num_machines']
        num_m_Main_NoCoin = cache_index_dic['Main']['NoCoin']['num_machines']
        num_m_Main_Mechanical = cache_index_dic['Main']['Mechanical']['num_machines']
        num_m_Main_Dead = cache_index_dic['Main']['Dead']['num_machines']
        num_m_Main_Devices = cache_index_dic['Main']['Devices']['num_machines']
        num_m_Binary_BIOS = cache_index_dic['Binary']['BIOS']['num_machines']
        num_m_Binary_CHD = cache_index_dic['Binary']['CHD']['num_machines']
        num_m_Binary_Samples = cache_index_dic['Binary']['Samples']['num_machines']
        num_m_Binary_SoftwareLists = cache_index_dic['Binary']['SoftwareLists']['num_machines']

        num_p_Main_Normal = cache_index_dic['Main']['Normal']['num_parents']
        num_p_Main_Unusual = cache_index_dic['Main']['Unusual']['num_parents']
        num_p_Main_NoCoin = cache_index_dic['Main']['NoCoin']['num_parents']
        num_p_Main_Mechanical = cache_index_dic['Main']['Mechanical']['num_parents']
        num_p_Main_Dead = cache_index_dic['Main']['Dead']['num_parents']
        num_p_Main_Devices = cache_index_dic['Main']['Devices']['num_parents']
        num_p_Binary_BIOS = cache_index_dic['Binary']['BIOS']['num_parents']
        num_p_Binary_CHD = cache_index_dic['Binary']['CHD']['num_parents']
        num_p_Binary_Samples = cache_index_dic['Binary']['Samples']['num_parents']
        num_p_Binary_SoftwareLists = cache_index_dic['Binary']['SoftwareLists']['num_parents']

        num_cat_Catver = len(cache_index_dic['Catver'])
        num_cat_Catlist = len(cache_index_dic['Catlist'])
        num_cat_Genre = len(cache_index_dic['Genre'])
        num_cat_Category = len(cache_index_dic['Category'])
        num_cat_NPlayers = len(cache_index_dic['NPlayers'])
        num_cat_Bestgames = len(cache_index_dic['Bestgames'])
        num_cat_Series = len(cache_index_dic['Series'])
        num_cat_Alltime = len(cache_index_dic['Alltime'])
        num_cat_Artwork = len(cache_index_dic['Artwork'])
        num_cat_Version = len(cache_index_dic['Version'])

        num_cat_Controls_Expanded = len(cache_index_dic['Controls_Expanded'])
        num_cat_Controls_Compact = len(cache_index_dic['Controls_Compact'])
        num_cat_Devices_Expanded = len(cache_index_dic['Devices_Expanded'])
        num_cat_Devices_Compact = len(cache_index_dic['Devices_Compact'])
        num_cat_Display_Type = len(cache_index_dic['Display_Type'])
        num_cat_Display_VSync = len(cache_index_dic['Display_VSync'])
        num_cat_Display_Resolution = len(cache_index_dic['Display_Resolution'])
        num_cat_CPU = len(cache_index_dic['CPU'])
        num_cat_Driver = len(cache_index_dic['Driver'])
        num_cat_Manufacturer = len(cache_index_dic['Manufacturer'])
        num_cat_ShortName = len(cache_index_dic['ShortName'])
        num_cat_LongName = len(cache_index_dic['LongName'])
        num_cat_BySL = len(cache_index_dic['BySL'])
        num_cat_Year = len(cache_index_dic['Year'])

        counters_available = True
        log_debug('render_root_list() counters_available = True')

    except KeyError as E:
        counters_available = False
        log_debug('render_root_list() counters_available = False')

    try:
        num_SL_all = 0
        num_SL_ROMs = 0
        num_SL_CHDs = 0
        num_SL_mixed = 0
        num_SL_empty = 0
        for l_name, l_dic in SL_index_dic.iteritems():
            num_SL_all += 1
            if l_dic['num_with_ROMs'] > 0 and l_dic['num_with_CHDs'] == 0:
                num_SL_ROMs += 1
            elif l_dic['num_with_ROMs'] == 0 and l_dic['num_with_CHDs'] > 0:
                num_SL_CHDs += 1
            elif l_dic['num_with_ROMs'] > 0 and l_dic['num_with_CHDs'] > 0:
                num_SL_mixed += 1
            elif l_dic['num_with_ROMs'] == 0 and l_dic['num_with_CHDs'] == 0:
                num_SL_empty += 1
            else:
                log_error('Logical error in SL {0}'.format(l_name))
        SL_counters_available = True
        log_debug('render_root_list() SL_counters_available = True')
        # log_debug('There are {0} SL_all lists.'.format(num_SL_all))
        # log_debug('There are {0} SL_ROMs lists.'.format(num_SL_ROMs))
        # log_debug('There are {0} SL_mixed lists.'.format(num_SL_mixed))
        # log_debug('There are {0} SL_CHDs lists.'.format(num_SL_CHDs))
        # log_debug('There are {0} SL_empty lists.'.format(num_SL_empty))

    except KeyError as E:
        SL_counters_available = False
        # num_SL_empty always used to control visibility. If 0 then 'SL empty' is not visible.
        num_SL_empty = 0
        log_debug('render_root_list() SL_counters_available = False')

    # --- Machine counters ---
    if counters_available:
        if mame_view_mode == VIEW_MODE_FLAT:
            a = ' [COLOR orange]({} machines)[/COLOR]'
            root_Main['Main_Normal'][2] += a.format(num_m_Main_Normal)
            root_Main['Main_Unusual'][2] += a.format(num_m_Main_Unusual)
            root_Main['Main_NoCoin'][2] += a.format(num_m_Main_NoCoin)
            root_Main['Main_Mechanical'][2] += a.format(num_m_Main_Mechanical)
            root_Main['Main_Dead'][2] += a.format(num_m_Main_Dead)
            root_Main['Main_Devices'][2] += a.format(num_m_Main_Devices)
            root_Binary['BIOS'][2] += a.format(num_m_Binary_BIOS)
            root_Binary['CHD'][2] += a.format(num_m_Binary_CHD)
            root_Binary['Samples'][2] += a.format(num_m_Binary_Samples)
            root_Binary['SoftwareLists'][2] += a.format(num_m_Binary_SoftwareLists)
        elif mame_view_mode == VIEW_MODE_PCLONE:
            a = ' [COLOR orange]({} parents)[/COLOR]'
            root_Main['Main_Normal'][2] += a.format(num_p_Main_Normal)
            root_Main['Main_Unusual'][2] += a.format(num_p_Main_Unusual)
            root_Main['Main_NoCoin'][2] += a.format(num_p_Main_NoCoin)
            root_Main['Main_Mechanical'][2] += a.format(num_p_Main_Mechanical)
            root_Main['Main_Dead'][2] += a.format(num_p_Main_Dead)
            root_Main['Main_Devices'][2] += a.format(num_p_Main_Devices)
            root_Binary['BIOS'][2] += a.format(num_p_Binary_BIOS)
            root_Binary['CHD'][2] += a.format(num_p_Binary_CHD)
            root_Binary['Samples'][2] += a.format(num_p_Binary_Samples)
            root_Binary['SoftwareLists'][2] += a.format(num_p_Binary_SoftwareLists)

        a = ' [COLOR gold]({} items)[/COLOR]'
        # Optional
        root_categories['Catver'][0] += a.format(num_cat_Catver)
        root_categories['Catlist'][0] += a.format(num_cat_Catlist)
        root_categories['Genre'][0] += a.format(num_cat_Genre)
        root_categories['Category'][0] += a.format(num_cat_Category)
        root_categories['NPlayers'][0] += a.format(num_cat_NPlayers)
        root_categories['Bestgames'][0] += a.format(num_cat_Bestgames)
        root_categories['Series'][0] += a.format(num_cat_Series)
        root_categories['Alltime'][0] += a.format(num_cat_Alltime)
        root_categories['Artwork'][0] += a.format(num_cat_Artwork)
        root_categories['Version'][0] += a.format(num_cat_Version)
        # Always present
        root_categories['Controls_Expanded'][0] += a.format(num_cat_Controls_Expanded)
        root_categories['Controls_Compact'][0] += a.format(num_cat_Controls_Compact)
        root_categories['Devices_Expanded'][0] += a.format(num_cat_Devices_Expanded)
        root_categories['Devices_Compact'][0] += a.format(num_cat_Devices_Compact)
        root_categories['Display_Type'][0] += a.format(num_cat_Display_Type)
        root_categories['Display_VSync'][0] += a.format(num_cat_Display_VSync)
        root_categories['Display_Resolution'][0] += a.format(num_cat_Display_Resolution)
        root_categories['CPU'][0] += a.format(num_cat_CPU)
        root_categories['Driver'][0] += a.format(num_cat_Driver)
        root_categories['Manufacturer'][0] += a.format(num_cat_Manufacturer)
        root_categories['ShortName'][0] += a.format(num_cat_ShortName)
        root_categories['LongName'][0] += a.format(num_cat_LongName)
        root_categories['BySL'][0] += a.format(num_cat_BySL)
        root_categories['Year'][0] += a.format(num_cat_Year)

    if SL_counters_available:
        a = ' [COLOR orange]({} lists)[/COLOR]'
        root_SL['SL'][0] += a.format(num_SL_all)
        root_SL['SL_ROM'][0] += a.format(num_SL_ROMs)
        root_SL['SL_ROM_CHD'][0] += a.format(num_SL_mixed)
        root_SL['SL_CHD'][0] += a.format(num_SL_CHDs)
        root_SL['SL_empty'][0] += a.format(num_SL_empty)

    # If everything deactivated render the main filters so user has access to the context menu.
    big_OR = g_settings['display_main_filters'] or g_settings['display_binary_filters'] or \
             g_settings['display_catalog_filters'] or g_settings['display_DAT_browser'] or \
             g_settings['display_SL_browser'] or g_settings['display_MAME_favs'] or \
             g_settings['display_SL_favs'] or g_settings['display_custom_filters']
    if not big_OR:
        g_settings['display_main_filters'] = True

    # Main filters (Virtual catalog 'Main')
    if g_settings['display_main_filters']:
        render_root_catalog_row(*root_Main['Main_Normal'])
        render_root_catalog_row(*root_Main['Main_Unusual'])
        render_root_catalog_row(*root_Main['Main_NoCoin'])
        render_root_catalog_row(*root_Main['Main_Mechanical'])
        render_root_catalog_row(*root_Main['Main_Dead'])
        render_root_catalog_row(*root_Main['Main_Devices'])

    # Binary filters (Virtual catalog 'Binary')
    if g_settings['display_binary_filters']:
        render_root_catalog_row(*root_Binary['BIOS'])
        render_root_catalog_row(*root_Binary['CHD'])
        render_root_catalog_row(*root_Binary['Samples'])
        render_root_catalog_row(*root_Binary['SoftwareLists'])

    if g_settings['display_catalog_filters']:
        # Optional cataloged filters (depend on a INI file)
        render_root_category_row(*root_categories['Catver'])
        render_root_category_row(*root_categories['Catlist'])
        render_root_category_row(*root_categories['Genre'])
        render_root_category_row(*root_categories['Category'])
        render_root_category_row(*root_categories['NPlayers'])
        render_root_category_row(*root_categories['Bestgames'])
        render_root_category_row(*root_categories['Series'])
        render_root_category_row(*root_categories['Alltime'])
        render_root_category_row(*root_categories['Artwork'])
        render_root_category_row(*root_categories['Version'])

        # Cataloged filters (always there)
        render_root_category_row(*root_categories['Controls_Expanded'])
        render_root_category_row(*root_categories['Controls_Compact'])
        render_root_category_row(*root_categories['Devices_Expanded'])
        render_root_category_row(*root_categories['Devices_Compact'])
        render_root_category_row(*root_categories['Display_Type'])
        render_root_category_row(*root_categories['Display_VSync'])
        render_root_category_row(*root_categories['Display_Resolution'])
        render_root_category_row(*root_categories['CPU'])
        render_root_category_row(*root_categories['Driver'])
        render_root_category_row(*root_categories['Manufacturer'])
        render_root_category_row(*root_categories['ShortName'])
        render_root_category_row(*root_categories['LongName'])
        render_root_category_row(*root_categories['BySL'])
        render_root_category_row(*root_categories['Year'])

    # --- DAT browsers ---
    if g_settings['display_DAT_browser']:
        render_root_category_row(*root_special['History'])
        render_root_category_row(*root_special['MAMEINFO'])
        render_root_category_row(*root_special['Gameinit'])
        render_root_category_row(*root_special['Command'])

    # --- Software lists ---
    if g_settings['display_SL_browser'] and g_settings['enable_SL']:
        render_root_category_row(*root_SL['SL'])
        render_root_category_row(*root_SL['SL_ROM'])
        render_root_category_row(*root_SL['SL_ROM_CHD'])
        render_root_category_row(*root_SL['SL_CHD'])
        if num_SL_empty > 0:
            render_root_category_row(*root_SL['SL_empty'])

    # --- Special launchers ---
    if g_settings['display_custom_filters']:
        render_root_category_row_custom_CM(*root_special_CM['Custom_Filters'])

    if g_settings['display_ROLs']:
        ROLS_plot = ('[COLOR orange]AEL Read Only Launchers[/COLOR] are special launchers '
            'exported to AEL. You can select your Favourite MAME machines or setup a custom '
            'filter to enjoy your MAME games in AEL togheter with other emulators.')
        URL = misc_url_1_arg('command', 'SHOW_AEL_ROLS')
        render_root_category_row('[AEL Read Only Launchers]', ROLS_plot, URL)

    # --- MAME Favourite stuff ---
    if g_settings['display_MAME_favs']:
        render_root_category_row_custom_CM(*root_special_CM['MAME_Favs'])
    if g_settings['display_MAME_most']:
        render_root_category_row_custom_CM(*root_special_CM['MAME_Most'])
    if g_settings['display_MAME_recent']:
        render_root_category_row_custom_CM(*root_special_CM['MAME_Recent'])

    # --- SL Favourite stuff ---
    if g_settings['display_SL_favs']:
        render_root_category_row_custom_CM(*root_special_CM['SL_Favs'])
    if g_settings['display_SL_most']:
        render_root_category_row_custom_CM(*root_special_CM['SL_Most'])
    if g_settings['display_SL_recent']:
        render_root_category_row_custom_CM(*root_special_CM['SL_Recent'])

    # --- Always render these two ---
    if g_settings['display_utilities']:
        Utilities_plot = ('Execute several [COLOR orange]Utilities[/COLOR]. For example, to '
            'check you AML configuration.')
        URL = misc_url_1_arg('command', 'SHOW_UTILITIES_VLAUNCHERS')
        render_root_category_row('Utilities', Utilities_plot, URL)
    if g_settings['display_global_reports']:
        Global_Reports_plot = ('View the [COLOR orange]Global Reports[/COLOR] and '
            'machine and audit [COLOR orange]Statistics[/COLOR].')
        URL = misc_url_1_arg('command', 'SHOW_GLOBALREPORTS_VLAUNCHERS')
        render_root_category_row('Global Reports', Global_Reports_plot, URL)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# These _render_skin_* functions used by skins to display widgets.
# These functions must never fail and be silent in case of error.
# They are called by skin widgets.
#
def render_skin_fav_slots():
    try:
        set_render_root_data()
        # Remove special markers (first and last character)
        rsCM = root_special_CM.copy()
        for key, value in rsCM.iteritems(): value[0] = value[0][1:-1]
        render_root_category_row_custom_CM(*rsCM['MAME_Favs'])
        render_root_category_row_custom_CM(*rsCM['MAME_Most'])
        render_root_category_row_custom_CM(*rsCM['MAME_Recent'])
        render_root_category_row_custom_CM(*rsCM['SL_Favs'])
        render_root_category_row_custom_CM(*rsCM['SL_Most'])
        render_root_category_row_custom_CM(*rsCM['SL_Recent'])
    except:
        log_error('Excepcion in render_skin_fav_slots()')
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_main_filters():
    try:
        set_render_root_data()
        render_root_catalog_row(*root_Main['Main_Normal'])
        render_root_catalog_row(*root_Main['Main_Unusual'])
        render_root_catalog_row(*root_Main['Main_NoCoin'])
        render_root_catalog_row(*root_Main['Main_Mechanical'])
        render_root_catalog_row(*root_Main['Main_Dead'])
        render_root_catalog_row(*root_Main['Main_Devices'])
    except:
        log_error('Excepcion in render_skin_main_filters()')
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_binary_filters():
    try:
        set_render_root_data()
        render_root_catalog_row(*root_Binary['BIOS'])
        render_root_catalog_row(*root_Binary['CHD'])
        render_root_catalog_row(*root_Binary['Samples'])
        render_root_catalog_row(*root_Binary['SoftwareLists'])
    except:
        log_error('Excepcion in render_skin_binary_filters()')
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_catalog_filters():
    try:
        # A mechanism to render only configured filters must be developed.
        set_render_root_data()
        render_root_category_row(*root_categories['Catver'])
        render_root_category_row(*root_categories['Catlist'])
        render_root_category_row(*root_categories['Genre'])
        render_root_category_row(*root_categories['Category'])
        render_root_category_row(*root_categories['NPlayers'])
        render_root_category_row(*root_categories['Bestgames'])
        render_root_category_row(*root_categories['Series'])
        render_root_category_row(*root_categories['Alltime'])
        render_root_category_row(*root_categories['Artwork'])
        render_root_category_row(*root_categories['Version'])
        render_root_category_row(*root_categories['Controls_Expanded'])
        render_root_category_row(*root_categories['Controls_Compact'])
        render_root_category_row(*root_categories['Devices_Expanded'])
        render_root_category_row(*root_categories['Devices_Compact'])
        render_root_category_row(*root_categories['Display_Type'])
        render_root_category_row(*root_categories['Display_VSync'])
        render_root_category_row(*root_categories['Display_Resolution'])
        render_root_category_row(*root_categories['CPU'])
        render_root_category_row(*root_categories['Driver'])
        render_root_category_row(*root_categories['Manufacturer'])
        render_root_category_row(*root_categories['ShortName'])
        render_root_category_row(*root_categories['LongName'])
        render_root_category_row(*root_categories['BySL'])
        render_root_category_row(*root_categories['Year'])
    except:
        log_error('Excepcion in render_skin_catalog_filters()')
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_dat_slots():
    try:
        set_render_root_data()
        render_root_category_row(*root_special['History'])
        render_root_category_row(*root_special['MAMEINFO'])
        render_root_category_row(*root_special['Gameinit'])
        render_root_category_row(*root_special['Command'])
    except:
        log_error('Excepcion in render_skin_dat_slots()')
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_SL_filters():
    if not g_settings['enable_SL']:
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return
    try:
        set_render_root_data()
        render_root_category_row(*root_SL['SL'])
        render_root_category_row(*root_SL['SL_ROM'])
        render_root_category_row(*root_SL['SL_ROM_CHD'])
        render_root_category_row(*root_SL['SL_CHD'])
        render_root_category_row(*root_SL['SL_empty'])
    except:
        log_error('Excepcion in render_skin_SL_filters()')
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# A Catalog is equivalent to a Launcher in AEL.
#
def render_root_catalog_row(catalog_name, catalog_key, display_name, plot_str):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY, 'plot' : plot_str})

    # --- Artwork ---
    icon_path   = g_PATHS.ICON_FILE_PATH.getPath()
    fanart_path = g_PATHS.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    URL_utils = misc_url_3_arg_RunPlugin(
        'command', 'UTILITIES', 'catalog', catalog_name, 'category', catalog_key)
    commands = [
        ('Setup plugin', misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Utilities', URL_utils),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_2_arg('catalog', catalog_name, 'category', catalog_key)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = True)

#
# A Category is equivalent to a Category in AEL. It contains a list of Launchers (catalogs).
#
def render_root_category_row(display_name, plot_str, root_URL):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY, 'plot' : plot_str})

    # --- Artwork ---
    icon_path   = g_PATHS.ICON_FILE_PATH.getPath()
    fanart_path = g_PATHS.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('Setup plugin', misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)
    xbmcplugin.addDirectoryItem(g_addon_handle, root_URL, listitem, isFolder = True)

def render_root_category_row_custom_CM(display_name, plot_str, root_URL, cmenu_list):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY, 'plot' : plot_str})

    # --- Artwork ---
    icon_path   = g_PATHS.ICON_FILE_PATH.getPath()
    fanart_path = g_PATHS.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('Setup plugin', misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    cmenu_list.extend(commands)
    listitem.addContextMenuItems(cmenu_list)
    xbmcplugin.addDirectoryItem(g_addon_handle, root_URL, listitem, isFolder = True)

# -------------------------------------------------------------------------------------------------
# Utilities and Global reports
# -------------------------------------------------------------------------------------------------
def aux_get_generic_listitem(name, plot, commands):
    vcategory_name   = name
    vcategory_plot   = plot
    vcategory_icon   = g_PATHS.ICON_FILE_PATH.getPath()
    vcategory_fanart = g_PATHS.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay': 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.addContextMenuItems(commands)

    return listitem

def render_Utilities_vlaunchers():
    # --- Common context menu for all VLaunchers ---
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]

    # --- Check MAME version ---
    listitem = aux_get_generic_listitem(
        'Check MAME version',
        'Check MAME version',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_MAME_VERSION')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Check AML configuration ---
    listitem = aux_get_generic_listitem(
        'Check AML configuration',
        'Check AML configuration',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_CONFIG')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Check/Update all Favourite objects ---
    listitem = aux_get_generic_listitem(
        'Check/Update all Favourite objects',
        'Check/Update all Favourite objects',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_ALL_FAV_OBJECTS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Check MAME CRC hash collisions ---
    listitem = aux_get_generic_listitem(
        'Check MAME CRC hash collisions',
        'Check MAME CRC hash collisions',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_MAME_COLLISIONS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Check SL CRC hash collisions ---
    listitem = aux_get_generic_listitem(
        'Check SL CRC hash collisions',
        'Check SL CRC hash collisions',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_SL_COLLISIONS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Export MAME ROMs DAT file ---
    listitem = aux_get_generic_listitem(
        'Export MAME ROMs Logiqx XML DAT file',
        'Export MAME ROMs Logiqx XML DAT file', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_MAME_ROM_DAT')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Export MAME CHDs DAT file ---
    listitem = aux_get_generic_listitem(
        'Export MAME CHDs Logiqx XML DAT file',
        'Export MAME CHDs Logiqx XML DAT file', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_MAME_CHD_DAT')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Export SL ROMs DAT file ---
    # In AML 0.9.10 only export MAME XMLs and see how it goes. SL XMLs cause more trouble
    # than MAME.
    # listitem = aux_get_generic_listitem(
    #     'Export SL ROMs Logiqx XML DAT file', 'Export SL ROMs Logiqx XML DAT file', commands)
    # url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_SL_ROM_DAT')
    # xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Export SL CHDs DAT file ---
    # listitem = aux_get_generic_listitem(
    #     'Export SL CHDs Logiqx XML DAT file', 'Export SL CHDs Logiqx XML DAT file', commands)
    # url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_SL_CHD_DAT')
    # xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Kodi BUG: if size of text file to display is 0 then previous text in window is rendered.
# Solution: report files are never empty. Always print a text header in the report.
#
def render_GlobalReports_vlaunchers():
    # --- Common context menu for all VLaunchers ---
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]

    # --- View MAME last execution output --------------------------------------------------------
    if g_PATHS.MAME_OUTPUT_PATH.exists():
        filesize = g_PATHS.MAME_OUTPUT_PATH.fileSize()
        STD_status = '{0} bytes'.format(filesize)
    else:
        STD_status = 'not found'
    listitem = aux_get_generic_listitem(
        'View MAME last execution output ({0})'.format(STD_status),
        'View MAME last execution output', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_EXEC_OUTPUT')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View statistics ------------------------------------------------------------------------
    # --- View main statistics ---
    listitem = aux_get_generic_listitem(
        'View main statistics',
        'View main statistics', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_MAIN')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View scanner statistics ---
    listitem = aux_get_generic_listitem(
        'View scanner statistics',
        'View scanner statistics', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_SCANNER')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View audit statistics ---
    listitem = aux_get_generic_listitem(
        'View audit statistics',
        'View audit statistics', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_AUDIT')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View all statistics ---
    listitem = aux_get_generic_listitem(
        'View all statistics',
        'View all statistics', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_ALL')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Write all statistics to file ---
    listitem = aux_get_generic_listitem(
        'Write all statistics to file',
        'Write all statistics to file', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_WRITE_FILE')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View ROM scanner reports ---------------------------------------------------------------
    listitem = aux_get_generic_listitem(
        'View MAME scanner Full archives report',
        ('Report of all MAME machines and the ROM ZIP files, CHDs and Sample ZIP files required '
         'to run each machine.'),
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ARCH_FULL')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME scanner Have archives report',
        ('Report of all MAME machines where you have all the ROM ZIP files, CHDs and Sample ZIP '
         'files necessary to run each machine.'),
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ARCH_HAVE')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME scanner Missing archives report',
        ('Report of all MAME machines where some of all ROM ZIP files, CHDs or Sample ZIP files '
         'are missing.'),
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ARCH_MISS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME scanner Missing ROM ZIP files',
        'Report a list of all Missing ROM ZIP files.',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ROM_LIST_MISS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME scanner Missing Sample ZIP files',
        'Report a list of all Missing Sample ZIP files.',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_SAM_LIST_MISS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME scanner Missing CHD files',
        'List of all missing CHD files.',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_CHD_LIST_MISS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View Software Lists scanner reports ----------------------------------------------------
    listitem = aux_get_generic_listitem(
        'View Software Lists scanner Full archives report',
        'View Full Software Lists item archives',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_FULL')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists scanner Have archives report',
        'View Have Software Lists item archives',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_HAVE')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists scanner Missing archives report',
        'View Missing Software Lists item archives',
        commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_MISS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- Asset scanner reports ------------------------------------------------------------------
    listitem = aux_get_generic_listitem(
        'View MAME asset scanner report',
        'View MAME asset scanner report', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ASSETS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists asset scanner report',
        'View Software Lists asset scanner report', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_ASSETS')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View MAME Audit reports ----------------------------------------------------------------
    listitem = aux_get_generic_listitem(
        'View MAME audit Machine Full report',
        'View MAME audit report (Full)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_FULL')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit Machine Good report',
        'View MAME audit report (Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit Machine Bad report',
        'View MAME audit report (Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit ROM Good report',
        'View MAME audit report (ROMs Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_ROM_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit ROM Bad report',
        'View MAME audit report (ROM Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_ROM_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit Samples Good report',
        'View MAME audit report (Samples Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_SAM_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit Sample Bad report',
        'View MAME audit report (Sample Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_SAM_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit CHD Good report',
        'View MAME audit report (CHDs Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_CHD_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View MAME audit CHD Bad report',
        'View MAME audit report (CHD Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_CHD_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- View SL Audit reports ------------------------------------------------------------------
    listitem = aux_get_generic_listitem(
        'View Software Lists audit Full report',
        'View SL audit report (Full)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_FULL')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists audit Good report',
        'View SL audit report (Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists audit Bad report',
        'View SL audit report (Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists audit ROM Good report',
        'View SL audit report (ROM Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_ROM_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists audit ROM Errors report',
        'View SL audit report (ROM Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_ROM_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists audit CHD Good report',
        'View SL audit report (CHD Good)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_CHD_GOOD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(
        'View Software Lists audit CHD Errors report',
        'View SL audit report (CHD Errors)', commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_CHD_BAD')
    xbmcplugin.addDirectoryItem(g_addon_handle, url_str, listitem, isFolder = False)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

#----------------------------------------------------------------------------------------------
# Cataloged machines
#----------------------------------------------------------------------------------------------
#
# Renders the Launchers inside a Category for MAME.
#
def render_catalog_list(catalog_name):
    log_debug('render_catalog_list() Starting ...')
    log_debug('render_catalog_list() catalog_name = "{0}"'.format(catalog_name))

    # --- General AML plugin check ---
    # Check if databases have been built, print warning messages, etc. This function returns
    # False if no issues, True if there is issues and a dialog has been printed.
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if not check_MAME_DB_before_rendering_catalog(g_PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render categories in catalog index
    set_Kodi_all_sorting_methods_and_size()
    mame_view_mode = g_settings['mame_view_mode']
    loading_ticks_start = time.time()
    cache_index_dic = fs_load_JSON_file_dic(g_PATHS.CACHE_INDEX_PATH.getPath())
    if mame_view_mode == VIEW_MODE_FLAT:
        catalog_dic = fs_get_cataloged_dic_all(g_PATHS, catalog_name)
    elif mame_view_mode == VIEW_MODE_PCLONE:
        catalog_dic = fs_get_cataloged_dic_parents(g_PATHS, catalog_name)
    if not catalog_dic:
        kodi_dialog_OK('Catalog is empty. Rebuild the MAME databases.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    loading_ticks_end = time.time()
    rendering_ticks_start = time.time()
    for catalog_key in sorted(catalog_dic):
        if mame_view_mode == VIEW_MODE_FLAT:
            num_machines = cache_index_dic[catalog_name][catalog_key]['num_machines']
            if num_machines == 1: machine_str = 'machine'
            else:                 machine_str = 'machines'
        elif mame_view_mode == VIEW_MODE_PCLONE:
            num_machines = cache_index_dic[catalog_name][catalog_key]['num_parents']
            if num_machines == 1: machine_str = 'parent'
            else:                 machine_str = 'parents'
        render_catalog_list_row(catalog_name, catalog_key, num_machines, machine_str)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()

    # --- DEBUG Data loading/rendering statistics ---
    log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
    log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

def render_catalog_list_row(catalog_name, catalog_key, num_machines, machine_str):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    title_str = '{0} [COLOR orange]({1} {2})[/COLOR]'.format(catalog_key, num_machines, machine_str)
    plot_str = 'Catalog {0}\nCategory {1}'.format(catalog_name, catalog_key)
    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str,      'plot' : plot_str,
                               'overlay' : ICON_OVERLAY, 'size' : num_machines})

    # --- Artwork ---
    icon_path   = g_PATHS.ICON_FILE_PATH.getPath()
    fanart_path = g_PATHS.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    URL_utils = misc_url_3_arg_RunPlugin(
        'command', 'UTILITIES', 'catalog', catalog_name, 'category', catalog_key)
    commands = [
        ('Utilities', URL_utils),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_2_arg('catalog', catalog_name, 'category', catalog_key)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = True)

#
# Renders a list of parent MAME machines knowing the catalog name and the category.
# Also renders machine lists in flat mode.
# Display mode: a) parents only b) all machines (flat)
#
def render_catalog_parent_list(catalog_name, category_name):
    # When using threads the performance gain is small: from 0.76 to 0.71, just 20 ms.
    # It's not worth it.
    log_debug('render_catalog_parent_list() catalog_name  = {0}'.format(catalog_name))
    log_debug('render_catalog_parent_list() category_name = {0}'.format(category_name))

    # --- Load ListItem properties (Not used at the moment) ---
    # prop_key = '{0} - {1}'.format(catalog_name, category_name)
    # log_debug('render_catalog_parent_list() Loading props with key "{0}"'.format(prop_key))
    # mame_properties_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_PROPERTIES_PATH.getPath())
    # prop_dic = mame_properties_dic[prop_key]
    # view_mode_property = prop_dic['vm']

    # --- Global properties ---
    view_mode_property = g_settings['mame_view_mode']
    log_debug('render_catalog_parent_list() view_mode_property = {0}'.format(view_mode_property))

    # --- General AML plugin check ---
    # Check if databases have been built, print warning messages, etc.
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if not check_MAME_DB_before_rendering_machines(g_PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Load main MAME info databases and catalog ---
    l_cataloged_dic_start = time.time()
    if view_mode_property == VIEW_MODE_PCLONE:
        catalog_dic = fs_get_cataloged_dic_parents(g_PATHS, catalog_name)
    elif view_mode_property == VIEW_MODE_FLAT:
        catalog_dic = fs_get_cataloged_dic_all(g_PATHS, catalog_name)
    else:
        kodi_dialog_OK('Wrong view_mode_property = "{0}". '.format(view_mode_property) +
                       'This is a bug, please report it.')
        return
    l_cataloged_dic_end = time.time()
    l_render_db_start = time.time()
    if g_settings['debug_enable_MAME_render_cache']:
        cache_index_dic = fs_load_JSON_file_dic(g_PATHS.CACHE_INDEX_PATH.getPath())
        render_db_dic = fs_load_render_dic_all(g_PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME machine cache disabled.')
        render_db_dic = fs_load_JSON_file_dic(g_PATHS.RENDER_DB_PATH.getPath())
    l_render_db_end = time.time()
    l_assets_db_start = time.time()
    if g_settings['debug_enable_MAME_asset_cache']:
        if 'cache_index_dic' not in locals():
            cache_index_dic = fs_load_JSON_file_dic(g_PATHS.CACHE_INDEX_PATH.getPath())
        assets_db_dic = fs_load_assets_all(g_PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME asset cache disabled.')
        assets_db_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_ASSETS_DB_PATH.getPath())
    l_assets_db_end = time.time()
    l_pclone_dic_start = time.time()
    main_pclone_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_PCLONE_DIC_PATH.getPath())
    l_pclone_dic_end = time.time()
    l_favs_start = time.time()
    fav_machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
    l_favs_end = time.time()

    # --- Compute loading times ---
    catalog_t = l_cataloged_dic_end - l_cataloged_dic_start
    render_t = l_render_db_end - l_render_db_start
    assets_t = l_assets_db_end - l_assets_db_start
    pclone_t = l_pclone_dic_end - l_pclone_dic_start
    favs_t   = l_favs_end - l_favs_start
    loading_time = catalog_t + render_t + assets_t + pclone_t + favs_t

    # --- Check if catalog is empty ---
    if not catalog_dic:
        kodi_dialog_OK('Catalog is empty. Check out "Setup plugin" context menu.')
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Process ROMs for rendering ---
    processing_ticks_start = time.time()
    r_list = render_process_machines(catalog_dic, catalog_name, category_name,
        render_db_dic, assets_db_dic, fav_machines, True, main_pclone_dic, False)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    set_Kodi_all_sorting_methods()
    render_commit_machines(r_list)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()
    rendering_time = rendering_ticks_end - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    total_time = loading_time + processing_time + rendering_time
    # log_debug('Loading catalog    {0:.4f} s'.format(catalog_t))
    # log_debug('Loading render db  {0:.4f} s'.format(render_t))
    # log_debug('Loading assets db  {0:.4f} s'.format(assets_t))
    # log_debug('Loading pclone dic {0:.4f} s'.format(pclone_t))
    # log_debug('Loading MAME favs  {0:.4f} s'.format(favs_t))
    log_debug('Loading time       {0:.4f} s'.format(loading_time))
    log_debug('Processing time    {0:.4f} s'.format(processing_time))
    log_debug('Rendering time     {0:.4f} s'.format(rendering_time))
    log_debug('Total time         {0:.4f} s'.format(total_time))

#
# Renders a list of MAME Clone machines (including parent).
# No need to check for DB existance here. If this function is called is because parents and
# hence all ROMs databases exist.
#
def render_catalog_clone_list(catalog_name, category_name, parent_name):
    log_debug('render_catalog_clone_list() catalog_name  = {0}'.format(catalog_name))
    log_debug('render_catalog_clone_list() category_name = {0}'.format(category_name))
    log_debug('render_catalog_clone_list() parent_name   = {0}'.format(parent_name))
    display_hide_Mature = g_settings['display_hide_Mature']
    display_hide_BIOS = g_settings['display_hide_BIOS']
    if catalog_name == 'None' and category_name == 'BIOS': display_hide_BIOS = False
    display_hide_nonworking = g_settings['display_hide_nonworking']
    display_hide_imperfect  = g_settings['display_hide_imperfect']
    view_mode_property = g_settings['mame_view_mode']
    log_debug('render_catalog_clone_list() view_mode_property = {0}'.format(view_mode_property))

    # --- Load main MAME info DB ---
    loading_ticks_start = time.time()
    catalog_dic = fs_get_cataloged_dic_all(g_PATHS, catalog_name)
    if g_settings['debug_enable_MAME_render_cache']:
        cache_index_dic = fs_load_JSON_file_dic(g_PATHS.CACHE_INDEX_PATH.getPath())
        render_db_dic = fs_load_render_dic_all(g_PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME machine cache disabled.')
        render_db_dic = fs_load_JSON_file_dic(g_PATHS.RENDER_DB_PATH.getPath())
    if g_settings['debug_enable_MAME_asset_cache']:
        if 'cache_index_dic' not in locals():
            cache_index_dic = fs_load_JSON_file_dic(g_PATHS.CACHE_INDEX_PATH.getPath())
        assets_db_dic = fs_load_assets_all(g_PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME asset cache disabled.')
        assets_db_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_ASSETS_DB_PATH.getPath())
    main_pclone_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_PCLONE_DIC_PATH.getPath())
    fav_machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
    loading_ticks_end = time.time()
    loading_time = loading_ticks_end - loading_ticks_start

    # --- Process ROMs ---
    processing_ticks_start = time.time()
    machine_dic = catalog_dic[category_name]
    t_catalog_dic = {}
    t_render_dic = {}
    t_assets_dic = {}
    # Render parent first
    t_catalog_dic[category_name] = {parent_name : machine_dic[parent_name]}
    t_render_dic[parent_name] = render_db_dic[parent_name]
    t_assets_dic[parent_name] = assets_db_dic[parent_name]
    # Then clones
    for clone_name in main_pclone_dic[parent_name]:
        t_catalog_dic[category_name][clone_name] = machine_dic[clone_name]
        t_render_dic[clone_name] = render_db_dic[clone_name]
        t_assets_dic[clone_name] = assets_db_dic[clone_name]
    r_list = render_process_machines(t_catalog_dic, catalog_name, category_name,
        t_render_dic, t_assets_dic, fav_machines, False, main_pclone_dic, False)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    set_Kodi_all_sorting_methods()
    render_commit_machines(r_list)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()
    rendering_time = rendering_ticks_end - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    total_time = loading_time + processing_time + rendering_time
    log_debug('Loading     {0:.4f} s'.format(loading_time))
    log_debug('Processing  {0:.4f} s'.format(processing_time))
    log_debug('Rendering   {0:.4f} s'.format(rendering_time))
    log_debug('Total       {0:.4f} s'.format(total_time))

#
# First make this function work OK, then try to optimize it.
# "Premature optimization is the root of all evil." Donald Knuth
# Returns a list of dictionaries:
# r_list = [
#   {
#     'm_name' : str, 'render_name' : str,
#     'info' : {}, 'props' : {}, 'art' : {},
#     'context' : [], 'URL' ; str
#   }, ...
# ]
#
# By default renders a flat list, main_pclone_dic is not needed and filters are ignored.
# These settings are for rendering the custom MAME filters.
#
def render_process_machines(catalog_dic, catalog_name, category_name,
    render_db_dic, assets_dic, fav_machines,
    flag_parent_list = False, main_pclone_dic = None, flag_ignore_filters = True):
    # --- Prepare for processing ---
    display_hide_Mature = g_settings['display_hide_Mature']
    display_hide_BIOS = g_settings['display_hide_BIOS']
    if catalog_name == 'None' and category_name == 'BIOS': display_hide_BIOS = False
    display_hide_nonworking = g_settings['display_hide_nonworking']
    display_hide_imperfect  = g_settings['display_hide_imperfect']
    # >> Think about how to implement these settings ...
    display_rom_available = g_settings['display_rom_available']
    display_chd_available  = g_settings['display_chd_available']

    # --- Traverse machines ---
    r_list = []
    for machine_name, render_name in catalog_dic[category_name].iteritems():
        machine = render_db_dic[machine_name]
        m_assets = assets_dic[machine_name]
        if not flag_ignore_filters:
            if display_hide_Mature and machine['isMature']: continue
            if display_hide_BIOS and machine['isBIOS']: continue
            if display_hide_nonworking and machine['driver_status'] == 'preliminary': continue
            if display_hide_imperfect and machine['driver_status'] == 'imperfect': continue
            if display_rom_available and m_assets['flags'][0] == 'r': continue
            if display_chd_available and m_assets['flags'][1] == 'c': continue

        # --- Add machine to list, set default values ---
        r_dict = {}
        r_dict['m_name'] = machine_name
        AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_FALSE
        AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_NONE

        # main_pclone_dic and num_clones only used when rendering parents.
        if flag_parent_list:
            if machine_name in main_pclone_dic:
                num_clones = len(main_pclone_dic[machine_name])
            else:
                num_clones = 0

        # --- Render a Parent only list ---
        display_name = render_name
        if flag_parent_list and num_clones > 0:
            # NOTE all machines here are parents

            # --- Mark number of clones ---
            display_name += ' [COLOR orange] ({0} clones)[/COLOR]'.format(num_clones)

            # --- Mark Flags, BIOS, Devices, BIOS, Parent/Clone and Driver status ---
            display_name += ' [COLOR skyblue]{0}[/COLOR]'.format(m_assets['flags'])
            if machine['isBIOS']:   display_name += ' [COLOR cyan][BIOS][/COLOR]'
            if machine['isDevice']: display_name += ' [COLOR violet][Dev][/COLOR]'
            if   machine['driver_status'] == 'imperfect':   display_name += ' [COLOR yellow][Imp][/COLOR]'
            elif machine['driver_status'] == 'preliminary': display_name += ' [COLOR red][Pre][/COLOR]'

            # --- Skin flags ---
            if machine_name in fav_machines:
                display_name += ' [COLOR violet][Fav][/COLOR]'
                AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
            AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT
        else:
            # --- Mark Flags, BIOS, Devices, BIOS, Parent/Clone and Driver status ---
            display_name += ' [COLOR skyblue]{0}[/COLOR]'.format(m_assets['flags'])
            if machine['isBIOS']:   display_name += ' [COLOR cyan][BIOS][/COLOR]'
            if machine['isDevice']: display_name += ' [COLOR violet][Dev][/COLOR]'
            if machine['cloneof']:  display_name += ' [COLOR orange][Clo][/COLOR]'
            if   machine['driver_status'] == 'imperfect':   display_name += ' [COLOR yellow][Imp][/COLOR]'
            elif machine['driver_status'] == 'preliminary': display_name += ' [COLOR red][Pre][/COLOR]'

            # --- Skin flags ---
            if machine_name in fav_machines:
                display_name += ' [COLOR violet][Fav][/COLOR]'
                AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
            if machine['cloneof']:
                AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE
            else:
                AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT

        # --- Assets/artwork ---
        icon_path      = m_assets[g_mame_icon] if m_assets[g_mame_icon] else 'DefaultProgram.png'
        fanart_path    = m_assets[g_mame_fanart]
        banner_path    = m_assets['marquee']
        clearlogo_path = m_assets['clearlogo']
        poster_path    = m_assets['3dbox'] if m_assets['3dbox'] else m_assets['flyer']

        # --- Create listitem row ---
        # >> Make all the infolabels compatible with Advanced Emulator Launcher
        ICON_OVERLAY = 6
        r_dict['render_name'] = display_name
        if g_settings['display_hide_trailers']:
            r_dict['info'] = {
                'title'   : display_name,     'year'    : machine['year'],
                'genre'   : machine['genre'], 'studio'  : machine['manufacturer'],
                'plot'    : m_assets['plot'],
                'overlay' : ICON_OVERLAY
            }
        else:
            r_dict['info'] = {
                'title'   : display_name,     'year'    : machine['year'],
                'genre'   : machine['genre'], 'studio'  : machine['manufacturer'],
                'plot'    : m_assets['plot'], 'trailer' : m_assets['trailer'],
                'overlay' : ICON_OVERLAY
            }
        r_dict['props'] = {
            'nplayers' : machine['nplayers'],
            'platform' : 'MAME',
            AEL_PCLONE_STAT_LABEL : AEL_PClone_stat_value,
            AEL_INFAV_BOOL_LABEL : AEL_InFav_bool_value,
        }

        # --- Assets ---
        r_dict['art'] = {
            'title'     : m_assets['title'],   'snap'      : m_assets['snap'],
            'boxfront'  : m_assets['cabinet'], 'boxback'   : m_assets['cpanel'],
            'cartridge' : m_assets['PCB'],     'flyer'     : m_assets['flyer'],
            '3dbox'     : m_assets['3dbox'],
            'icon'      : icon_path,           'fanart'    : fanart_path,
            'banner'    : banner_path,         'clearlogo' : clearlogo_path,
            'poster'    : poster_path
        }

        # --- Create context menu ---
        URL_view_DAT = misc_url_2_arg_RunPlugin('command', 'VIEW_DAT', 'machine', machine_name)
        URL_view     = misc_url_2_arg_RunPlugin('command', 'VIEW', 'machine', machine_name)
        URL_fav      = misc_url_2_arg_RunPlugin('command', 'ADD_MAME_FAV', 'machine', machine_name)
        if flag_parent_list and num_clones > 0:
            URL_clones = misc_url_4_arg_RunPlugin('command', 'EXEC_SHOW_MAME_CLONES', 
                'catalog', catalog_name, 'category', category_name, 'parent', machine_name)
            commands = [
                ('Info / Utils', URL_view_DAT),
                ('View / Audit', URL_view),
                ('Show clones', URL_clones),
                ('Add to MAME Favourites', URL_fav),
                ('Kodi File Manager', 'ActivateWindow(filemanager)'),
                ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
            ]
        else:
            commands = [
                ('Info / Utils', URL_view_DAT),
                ('View / Audit', URL_view),
                ('Add to MAME Favourites', URL_fav),
                ('Kodi File Manager', 'ActivateWindow(filemanager)'),
                ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
            ]
        r_dict['context'] = commands

        # --- Add row to the list ---
        r_dict['URL'] = misc_url_2_arg('command', 'LAUNCH', 'machine', machine_name)
        r_list.append(r_dict)

    return r_list

#
# Renders a processed list of machines/ROMs. Basically, this function only calls the
# Kodi API with the precomputed values.
#
def render_commit_machines(r_list):
    listitem_list = []

    # Kodi Leia and up.
    if kodi_running_version >= KODI_VERSION_LEIA:
        log_debug('Rendering machine list in Kodi Leia and up.')
        for r_dict in r_list:
            # --- New offscreen parameter in Leia ---
            # offscreen increases the performance a bit. For example, for a list with 4058 items:
            # offscreent = True  Rendering time  0.4620 s
            # offscreent = True  Rendering time  0.5780 s
            # See https://forum.kodi.tv/showthread.php?tid=329315&pid=2711937#pid2711937
            # and https://forum.kodi.tv/showthread.php?tid=307394&pid=2531524
            listitem = xbmcgui.ListItem(r_dict['render_name'], offscreen = True)
            listitem.setInfo('video', r_dict['info'])
            listitem.setProperties(r_dict['props'])
            listitem.setArt(r_dict['art'])
            listitem.addContextMenuItems(r_dict['context'])
            listitem_list.append((r_dict['URL'], listitem, False))

    # Kodi Krypton and down.
    else:
        log_debug('Rendering machine list in Kodi Krypton and down.')
        for r_dict in r_list:
            listitem = xbmcgui.ListItem(r_dict['render_name'])
            listitem.setInfo('video', r_dict['info'])
            for prop_name, prop_value in r_dict['props'].iteritems():
                listitem.setProperty(prop_name, prop_value)
            listitem.setArt(r_dict['art'])
            listitem.addContextMenuItems(r_dict['context'])
            listitem_list.append((r_dict['URL'], listitem, False))

    # Add all listitems in one go.
    xbmcplugin.addDirectoryItems(g_addon_handle, listitem_list, len(listitem_list))

#
# Not used at the moment -> There are global display settings in addon settings for this.
#
def command_context_display_settings(catalog_name, category_name):
    # >> Load ListItem properties
    log_debug('command_display_settings() catalog_name  "{0}"'.format(catalog_name))
    log_debug('command_display_settings() category_name "{0}"'.format(category_name))
    prop_key = '{0} - {1}'.format(catalog_name, category_name)
    log_debug('command_display_settings() Loading props with key "{0}"'.format(prop_key))
    mame_properties_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_PROPERTIES_PATH.getPath())
    prop_dic = mame_properties_dic[prop_key]
    if prop_dic['vm'] == VIEW_MODE_NORMAL: dmode_str = 'Parents only'
    else:                                  dmode_str = 'Parents and clones'

    # --- Select menu ---
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Display settings',
                             ['Display mode (currently {0})'.format(dmode_str),
                              'Default Icon',   'Default Fanart',
                              'Default Banner', 'Default Poster',
                              'Default Clearlogo'])
    if menu_item < 0: return
    
    # --- Display settings ---
    if menu_item == 0:
        # >> Krypton feature: preselect the current item.
        # >> NOTE Preselect must be called with named parameter, otherwise it does not work well.
        # See http://forum.kodi.tv/showthread.php?tid=250936&pid=2327011#pid2327011
        if prop_dic['vm'] == VIEW_MODE_NORMAL: p_idx = 0
        else:                                  p_idx = 1
        log_debug('command_display_settings() p_idx = "{0}"'.format(p_idx))
        idx = dialog.select('Display mode', ['Parents only', 'Parents and clones'], preselect = p_idx)
        log_debug('command_display_settings() idx = "{0}"'.format(idx))
        if idx < 0: return
        if idx == 0:   prop_dic['vm'] = VIEW_MODE_NORMAL
        elif idx == 1: prop_dic['vm'] = VIEW_MODE_ALL

    # --- Change default icon ---
    elif menu_item == 1:
        kodi_dialog_OK('Not coded yet. Sorry')

    # >> Changes made. Refreash container
    fs_write_JSON_file(g_PATHS.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    kodi_refresh_container()

#----------------------------------------------------------------------------------------------
# Software Lists
#----------------------------------------------------------------------------------------------
def render_SL_list(catalog_name):
    log_debug('render_SL_list() catalog_name = {}\n'.format(catalog_name))

    # --- General AML plugin check ---
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if not check_SL_DB_before_rendering_catalog(g_PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Load Software List catalog and build render catalog ---
    SL_main_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
    SL_catalog_dic = {}
    if catalog_name == 'SL':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_ROM':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_ROMs'] > 0 and SL_dic['num_with_CHDs'] == 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_CHD':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_ROMs'] == 0 and SL_dic['num_with_CHDs'] > 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_ROM_CHD':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_ROMs'] > 0 and SL_dic['num_with_CHDs'] > 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_empty':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_ROMs'] == 0 and SL_dic['num_with_CHDs'] == 0:
                SL_catalog_dic[SL_name] = SL_dic
    else:
        kodi_dialog_OK('Wrong catalog_name {}'.format(catalog_name))
        return
    log_debug('render_SL_list() len(catalog_name) = {}\n'.format(len(SL_catalog_dic)))

    set_Kodi_all_sorting_methods()
    for SL_name in SL_catalog_dic:
        SL = SL_catalog_dic[SL_name]
        render_SL_list_row(SL_name, SL)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def render_SL_ROMs(SL_name):
    log_debug('render_SL_ROMs() SL_name "{0}"'.format(SL_name))

    # --- General AML plugin check ---
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if not check_SL_DB_before_rendering_machines(g_PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # Load ListItem properties (Not used at the moment)
    # SL_properties_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PROP_PATH.getPath()) 
    # prop_dic = SL_properties_dic[SL_name]
    # Global properties
    view_mode_property = g_settings['sl_view_mode']
    log_debug('render_SL_ROMs() view_mode_property = {0}'.format(view_mode_property))

    # Load Software List ROMs
    SL_PClone_dic = fs_load_JSON_file_dic(g_PATHS.SL_PCLONE_DIC_PATH.getPath())
    SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
    SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(file_name)
    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
    SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
    SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    set_Kodi_all_sorting_methods()
    SL_proper_name = SL_catalog_dic[SL_name]['display_name']
    if view_mode_property == VIEW_MODE_PCLONE:
        # Get list of parents
        log_debug('render_SL_ROMs() Rendering Parent/Clone launcher')
        parent_list = []
        for parent_name in sorted(SL_PClone_dic[SL_name]): parent_list.append(parent_name)
        for parent_name in parent_list:
            ROM        = SL_roms[parent_name]
            assets     = SL_asset_dic[parent_name] if parent_name in SL_asset_dic else fs_new_SL_asset()
            num_clones = len(SL_PClone_dic[SL_name][parent_name])
            ROM['genre'] = SL_proper_name # Add the SL name as 'genre'
            render_SL_ROM_row(SL_name, parent_name, ROM, assets, True, num_clones)
    elif view_mode_property == VIEW_MODE_FLAT:
        log_debug('render_SL_ROMs() Rendering Flat launcher')
        for rom_name in SL_roms:
            ROM    = SL_roms[rom_name]
            assets = SL_asset_dic[rom_name] if rom_name in SL_asset_dic else fs_new_SL_asset()
            ROM['genre'] = SL_proper_name # Add the SL name as 'genre'
            render_SL_ROM_row(SL_name, rom_name, ROM, assets)
    else:
        kodi_dialog_OK('Wrong vm = "{0}". This is a bug, please report it.'.format(prop_dic['vm']))
        return
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_SL_pclone_set(SL_name, parent_name):
    log_debug('render_SL_pclone_set() SL_name     "{0}"'.format(SL_name))
    log_debug('render_SL_pclone_set() parent_name "{0}"'.format(parent_name))
    view_mode_property = g_settings['sl_view_mode']
    log_debug('render_SL_pclone_set() view_mode_property = {0}'.format(view_mode_property))

    # >> Load Software List ROMs
    SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
    SL_PClone_dic = fs_load_JSON_file_dic(g_PATHS.SL_PCLONE_DIC_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
    SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(file_name)
    log_debug('render_SL_pclone_set() ROMs JSON "{0}"'.format(SL_DB_FN.getPath()))
    SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())

    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
    SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    # >> Render parent first
    SL_proper_name = SL_catalog_dic[SL_name]['display_name']
    set_Kodi_all_sorting_methods()
    ROM = SL_roms[parent_name]
    assets = SL_asset_dic[parent_name] if parent_name in SL_asset_dic else fs_new_SL_asset()
    ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
    render_SL_ROM_row(SL_name, parent_name, ROM, assets, False, view_mode_property)

    # >> Render clones belonging to parent in this category
    for clone_name in sorted(SL_PClone_dic[SL_name][parent_name]):
        ROM = SL_roms[clone_name]
        assets = SL_asset_dic[clone_name] if clone_name in SL_asset_dic else fs_new_SL_asset()
        ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
        render_SL_ROM_row(SL_name, clone_name, ROM, assets)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def render_SL_list_row(SL_name, SL):
    # --- Display number of ROMs and CHDs ---
    # if SL['num_with_CHDs'] == 0:
    #     if SL['num_with_ROMs'] == 1: f_str = '{}  [COLOR orange]({} ROM)[/COLOR]'
    #     else:                        f_str = '{}  [COLOR orange]({} ROMs)[/COLOR]'
    #     display_name = f_str.format(SL['display_name'], SL['num_with_ROMs'])
    # elif SL['num_with_ROMs'] == 0:
    #     if SL['num_with_CHDs'] == 1: f_str = '{}  [COLOR orange]({} CHD)[/COLOR]'
    #     else:                        f_str = '{}  [COLOR orange]({} CHDs)[/COLOR]'
    #     display_name = f_str.format(SL['display_name'], SL['num_with_CHDs'])
    # else:
    #     display_name = '{}  [COLOR orange]({} ROMs and {} CHDs)[/COLOR]'.format(
    #         SL['display_name'], SL['num_with_ROMs'], SL['num_with_CHDs'])

    # --- Display Parents or Total SL items ---
    view_mode_property = g_settings['sl_view_mode']
    if view_mode_property == VIEW_MODE_PCLONE:
        if SL['num_parents'] == 1: f_str = '{}  [COLOR orange]({} parent)[/COLOR]'
        else:                      f_str = '{}  [COLOR orange]({} parents)[/COLOR]'
        display_name = f_str.format(SL['display_name'], SL['num_parents'])
    elif view_mode_property == VIEW_MODE_FLAT:
        if SL['num_items'] == 1: f_str = '{}  [COLOR orange]({} item)[/COLOR]'
        else:                    f_str = '{}  [COLOR orange]({} items)[/COLOR]'
        display_name = f_str.format(SL['display_name'], SL['num_items'])
    else:
        raise TypeError('Wrong view_mode_property {}'.format(view_mode_property))

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY } )
    listitem.addContextMenuItems([
        ('Kodi File Manager', 'ActivateWindow(filemanager)' ),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(__addon_id__))
    ])
    URL = misc_url_2_arg('catalog', 'SL', 'category', SL_name)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = True)

def render_SL_ROM_row(SL_name, rom_name, ROM, assets, flag_parent_list = False, num_clones = 0):
    display_name = ROM['description']
    if flag_parent_list and num_clones > 0:
        display_name += ' [COLOR orange] ({0} clones)[/COLOR]'.format(num_clones)
        status = '{0}{1}'.format(ROM['status_ROM'], ROM['status_CHD'])
        display_name += ' [COLOR skyblue]{0}[/COLOR]'.format(status)
    else:
        # --- Mark flags and status ---
        status = '{0}{1}'.format(ROM['status_ROM'], ROM['status_CHD'])
        display_name += ' [COLOR skyblue]{0}[/COLOR]'.format(status)
        if ROM['cloneof']: display_name += ' [COLOR orange][Clo][/COLOR]'

    # --- Assets/artwork ---
    icon_path   = assets[g_SL_icon] if assets[g_SL_icon] else 'DefaultProgram.png'
    fanart_path = assets[g_SL_fanart]
    poster_path = assets['3dbox'] if assets['3dbox'] else assets['boxfront']

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    # >> Make all the infolabels compatible with Advanced Emulator Launcher
    if g_settings['display_hide_trailers']:
        listitem.setInfo('video', {'title'   : display_name,      'year'    : ROM['year'],
                                   'genre'   : ROM['genre'],      'studio'  : ROM['publisher'],
                                   'plot'    : ROM['plot'],       'overlay' : ICON_OVERLAY })
    else:
        listitem.setInfo('video', {'title'   : display_name,      'year'    : ROM['year'],
                                   'genre'   : ROM['genre'],      'studio'  : ROM['publisher'],
                                   'plot'    : ROM['plot'],       'overlay' : ICON_OVERLAY,
                                   'trailer' : assets['trailer'] })
    listitem.setProperty('platform', 'MAME Software List')

    # --- Assets ---
    # >> AEL custom artwork fields
    listitem.setArt({
        'title' : assets['title'], 'snap' : assets['snap'],
        'boxfront' : assets['boxfront'], '3dbox' : assets['3dbox'],
        'icon' : icon_path, 'fanart' : fanart_path, 'poster' : poster_path
    })

    # --- Create context menu ---
    URL_view_DAT = misc_url_3_arg_RunPlugin('command', 'VIEW_DAT', 'SL', SL_name, 'ROM', rom_name)
    URL_view = misc_url_3_arg_RunPlugin('command', 'VIEW', 'SL', SL_name, 'ROM', rom_name)
    URL_fav = misc_url_3_arg_RunPlugin('command', 'ADD_SL_FAV', 'SL', SL_name, 'ROM', rom_name)
    if flag_parent_list and num_clones > 0:
        URL_show_c = misc_url_4_arg_RunPlugin(
            'command', 'EXEC_SHOW_SL_CLONES', 'catalog', 'SL', 'category', SL_name, 'parent', rom_name)
        commands = [
            ('Info / Utils', URL_view_DAT),
            ('View / Audit', URL_view),
            ('Show clones', URL_show_c),
            ('Add ROM to SL Favourites', URL_fav),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    else:
        commands = [
            ('Info / Utils', URL_view_DAT),
            ('View / Audit', URL_view),
            ('Add ROM to SL Favourites', URL_fav),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_3_arg('command', 'LAUNCH_SL', 'SL', SL_name, 'ROM', rom_name)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = False)

#----------------------------------------------------------------------------------------------
# DATs
#
# catalog = 'History'  / category = '32x' / machine = 'sonic'
# catalog = 'MAMEINFO' / category = '32x' / machine = 'sonic'
# catalog = 'Gameinit' / category = 'None' / machine = 'sonic'
# catalog = 'Command'  / category = 'None' / machine = 'sonic'
#----------------------------------------------------------------------------------------------
def render_DAT_list(catalog_name):
    # --- Create context menu ---
    commands = [
        ('View', misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    # --- Unrolled variables ---
    ICON_OVERLAY = 6

    if catalog_name == 'History':
        # Render list of categories.
        DAT_idx_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods()
        for key in DAT_idx_dic:
            category_name = '{} [COLOR lightgray]({})[/COLOR]'.format(DAT_idx_dic[key]['name'], key)
            listitem = xbmcgui.ListItem(category_name)
            listitem.setInfo('video', {'title' : category_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_2_arg('catalog', catalog_name, 'category', key)
            xbmcplugin.addDirectoryItem(g_addon_handle, url = URL, listitem = listitem, isFolder = True)
    elif catalog_name == 'MAMEINFO':
        # Render list of categories.
        DAT_idx_dic = fs_load_JSON_file_dic(g_PATHS.MAMEINFO_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods()
        for key in DAT_idx_dic:
            category_name = '{}'.format(key)
            listitem = xbmcgui.ListItem(category_name)
            listitem.setInfo('video', {'title' : category_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_2_arg('catalog', catalog_name, 'category', key)
            xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = True)
    elif catalog_name == 'Gameinit':
        # Render list of machines.
        DAT_idx_dic = fs_load_JSON_file_dic(g_PATHS.GAMEINIT_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods()
        for machine_key in DAT_idx_dic:
            machine_name = '{} [COLOR lightgray]({})[/COLOR]'.format(DAT_idx_dic[machine_key], machine_key)
            listitem = xbmcgui.ListItem(machine_name)
            listitem.setInfo('video', {'title' : machine_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_3_arg('catalog', catalog_name, 'category', 'None', 'machine', machine_key)
            xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = False)
    elif catalog_name == 'Command':
        # Render list of machines.
        DAT_idx_dic = fs_load_JSON_file_dic(g_PATHS.COMMAND_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods()
        for machine_key in DAT_idx_dic:
            machine_name = '{} [COLOR lightgray]({})[/COLOR]'.format(DAT_idx_dic[machine_key], machine_key)
            listitem = xbmcgui.ListItem(machine_name)
            listitem.setInfo('video', {'title' : machine_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_3_arg('catalog', catalog_name, 'category', 'None', 'machine', machine_key)
            xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = False)
    else:
        kodi_dialog_OK(
            'DAT database file "{}" not found. Check out "Setup plugin" context menu.'.format(catalog_name))
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

# Only History.dat and MAMEinfo.dat have categories.
def render_DAT_category(catalog_name, category_name):
    # Load Software List catalog
    if catalog_name == 'History':
        DAT_catalog_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_IDX_PATH.getPath())
    elif catalog_name == 'MAMEINFO':
        DAT_catalog_dic = fs_load_JSON_file_dic(g_PATHS.MAMEINFO_IDX_PATH.getPath())
    else:
        kodi_dialog_OK('DAT database file "{0}" not found. Check out "Setup plugin" context menu.'.format(catalog_name))
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return
    if not DAT_catalog_dic:
        kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_all_sorting_methods()
    if catalog_name == 'History':
        category_machine_dic = DAT_catalog_dic[category_name]['machines']
        for machine_key in category_machine_dic:
            display_name, db_list, db_machine = category_machine_dic[machine_key].split('|')
            render_DAT_category_row(catalog_name, category_name, machine_key, display_name)
    elif catalog_name == 'MAMEINFO':
        category_machine_dic = DAT_catalog_dic[category_name]
        for machine_key in category_machine_dic:
            display_name = category_machine_dic[machine_key]
            render_DAT_category_row(catalog_name, category_name, machine_key, display_name)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def render_DAT_category_row(catalog_name, category_name, machine_key, display_name):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    display_name = '{} [COLOR lightgray]({})[/COLOR]'.format(display_name, machine_key)
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY } )
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_3_arg('catalog', catalog_name, 'category', category_name, 'machine', machine_key)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = False)

def render_DAT_machine_info(catalog_name, category_name, machine_name):
    log_debug('render_DAT_machine_info() catalog_name "{0}"'.format(catalog_name))
    log_debug('render_DAT_machine_info() category_name "{0}"'.format(category_name))
    log_debug('render_DAT_machine_info() machine_name "{0}"'.format(machine_name))

    if catalog_name == 'History':
        DAT_idx_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_IDX_PATH.getPath())
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_DB_PATH.getPath())
        display_name, db_list, db_machine = DAT_idx_dic[category_name]['machines'][machine_name].split('|')
        t_str = ('History for [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR] '
            '(DB entry [COLOR=orange]{}[/COLOR] / [COLOR=orange]{}[/COLOR])')
        window_title = t_str.format(category_name, machine_name, db_list, db_machine)
        info_text = DAT_dic[db_list][db_machine]
    elif catalog_name == 'MAMEINFO':
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.MAMEINFO_DB_PATH.getPath())
        t_str = 'MAMEINFO information for [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR]'
        window_title = t_str.format(category_name, machine_name)
        info_text = DAT_dic[category_name][machine_name]
    elif catalog_name == 'Gameinit':
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.GAMEINIT_DB_PATH.getPath())
        window_title = 'Gameinit information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        info_text = DAT_dic[machine_name]
    elif catalog_name == 'Command':
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.COMMAND_DB_PATH.getPath())
        window_title = 'Command information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        info_text = DAT_dic[machine_name]
    else:
        kodi_dialog_OK(
            'Wrong catalog_name "{}". This is a bug, please report it.'.format(catalog_name))
        return

    # --- Show information window ---
    display_text_window(window_title, info_text)

#
# Not used at the moment -> There are global display settings.
#
def command_context_display_settings_SL(SL_name):
    log_debug('command_display_settings_SL() SL_name "{0}"'.format(SL_name))

    # --- Load properties DB ---
    SL_properties_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PROP_PATH.getPath())
    prop_dic = SL_properties_dic[SL_name]

    # --- Show menu ---
    if prop_dic['vm'] == VIEW_MODE_NORMAL: dmode_str = 'Parents only'
    else:                                  dmode_str = 'Parents and clones'
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Display settings',
                             ['Display mode (currently {0})'.format(dmode_str),
                              'Default Icon', 'Default Fanart', 
                              'Default Banner', 'Default Poster', 'Default Clearlogo'])
    if menu_item < 0: return

    # --- Change display mode ---
    if menu_item == 0:
        if prop_dic['vm'] == VIEW_MODE_NORMAL: p_idx = 0
        else:                                  p_idx = 1
        log_debug('command_display_settings() p_idx = "{0}"'.format(p_idx))
        idx = dialog.select('Display mode', ['Parents only', 'Parents and clones'], preselect = p_idx)
        log_debug('command_display_settings() idx = "{0}"'.format(idx))
        if idx < 0: return
        if idx == 0:   prop_dic['vm'] = VIEW_MODE_NORMAL
        elif idx == 1: prop_dic['vm'] = VIEW_MODE_ALL

    # --- Change default icon ---
    elif menu_item == 1:
        kodi_dialog_OK('Not coded yet. Sorry')

    # --- Save display settings ---
    fs_write_JSON_file(g_PATHS.SL_MACHINES_PROP_PATH.getPath(), SL_properties_dic)
    kodi_refresh_container()

# ---------------------------------------------------------------------------------------------
# Information display / Utilities
# ---------------------------------------------------------------------------------------------
def command_context_view_DAT(machine_name, SL_name, SL_ROM, location):
    VIEW_MAME_MACHINE = 100
    VIEW_SL_ROM       = 200

    ACTION_VIEW_HISTORY           = 100
    ACTION_VIEW_MAMEINFO          = 200
    ACTION_VIEW_GAMEINIT          = 300
    ACTION_VIEW_COMMAND           = 400
    ACTION_VIEW_FANART            = 500
    ACTION_VIEW_MANUAL            = 600
    ACTION_VIEW_BROTHERS          = 700
    ACTION_VIEW_SAME_GENRE        = 800
    ACTION_VIEW_SAME_MANUFACTURER = 900

    # --- Determine if we are in a category, launcher or ROM ---
    log_debug('command_context_view_DAT() machine_name "{0}"'.format(machine_name))
    log_debug('command_context_view_DAT() SL_name      "{0}"'.format(SL_name))
    log_debug('command_context_view_DAT() SL_ROM       "{0}"'.format(SL_ROM))
    log_debug('command_context_view_DAT() location     "{0}"'.format(location))
    if machine_name:
        view_type = VIEW_MAME_MACHINE
    elif SL_name:
        view_type = VIEW_SL_ROM
    else:
        raise TypeError('Logic error in command_context_view_DAT()')
    log_debug('command_context_view_DAT() view_type = {0}'.format(view_type))

    if view_type == VIEW_MAME_MACHINE:
        # --- Load DAT indices ---
        History_idx_dic   = fs_load_JSON_file_dic(g_PATHS.HISTORY_IDX_PATH.getPath())
        Mameinfo_idx_dic  = fs_load_JSON_file_dic(g_PATHS.MAMEINFO_IDX_PATH.getPath())
        Gameinit_idx_list = fs_load_JSON_file_dic(g_PATHS.GAMEINIT_IDX_PATH.getPath())
        Command_idx_list  = fs_load_JSON_file_dic(g_PATHS.COMMAND_IDX_PATH.getPath())

        # --- Check if DAT information is available for this machine ---
        if History_idx_dic:
            History_str = 'Found' if machine_name in History_idx_dic['mame']['machines'] else 'Not found'
        else:
            History_str = 'Not configured'
        if Mameinfo_idx_dic:
            Mameinfo_str = 'Found' if machine_name in Mameinfo_idx_dic['mame'] else 'Not found'
        else:
            Mameinfo_str = 'Not configured'
        if Gameinit_idx_list:
            Gameinit_str = 'Found' if machine_name in Gameinit_idx_list else 'Not found'
        else:
            Gameinit_str = 'Not configured'
        if Command_idx_list:
            Command_str = 'Found' if machine_name in Command_idx_list else 'Not found'
        else:
            Command_str = 'Not configured'

        # Check Fanart and Manual. Load hashed databases.
        # NOTE A ROM loading factory need to be coded to deal with the different ROM
        #      locations to avoid duplicate code. Have a look at ACTION_VIEW_MACHINE_DATA
        #      in function _command_context_view()
        # Fanart_str = 
        # Manual_str = 

    elif view_type == VIEW_SL_ROM:
        History_idx_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_IDX_PATH.getPath())
        if History_idx_dic:
            if SL_name in History_idx_dic:
                History_str = 'Found' if SL_ROM in History_idx_dic[SL_name]['machines'] else 'Not found'
            else:
                History_str = 'SL not found'
        else:
            History_str = 'Not configured'

        # Check Fanart and Manual.
        # Fanart_str =
        # Manual_str =

    # --- Build menu base on view_type ---
    if view_type == VIEW_MAME_MACHINE:
        d_list = [
          'View History DAT ({})'.format(History_str),
          'View MAMEinfo DAT ({})'.format(Mameinfo_str),
          'View Gameinit DAT ({})'.format(Gameinit_str),
          'View Command DAT ({})'.format(Command_str),
          'View Fanart',
          'View Manual',
          'Display brother machines',
          'Display machines with same Genre',
          'Display machines by same Manufacturer',
        ]
    elif view_type == VIEW_SL_ROM:
        d_list = [
          'View History DAT ({})'.format(History_str),
          'View Fanart',
          'View Manual',
        ]
    else:
        kodi_dialog_OK('Wrong view_type = {0}. This is a bug, please report it.'.format(view_type))
        return
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Polymorphic menu. Determine action to do. ---
    if view_type == VIEW_MAME_MACHINE:
        if   selected_value == 0: action = ACTION_VIEW_HISTORY
        elif selected_value == 1: action = ACTION_VIEW_MAMEINFO
        elif selected_value == 2: action = ACTION_VIEW_GAMEINIT
        elif selected_value == 3: action = ACTION_VIEW_COMMAND
        elif selected_value == 4: action = ACTION_VIEW_FANART
        elif selected_value == 5: action = ACTION_VIEW_MANUAL
        elif selected_value == 6: action = ACTION_VIEW_BROTHERS
        elif selected_value == 7: action = ACTION_VIEW_SAME_GENRE
        elif selected_value == 8: action = ACTION_VIEW_SAME_MANUFACTURER
        else:
            kodi_dialog_OK(
                'view_type == VIEW_MAME_MACHINE and selected_value = {0}. '.format(selected_value) +
                'This is a bug, please report it.')
            return
    elif view_type == VIEW_SL_ROM:
        if   selected_value == 0: action = ACTION_VIEW_HISTORY
        elif selected_value == 1: action = ACTION_VIEW_FANART
        elif selected_value == 2: action = ACTION_VIEW_MANUAL
        else:
            kodi_dialog_OK(
                'view_type == VIEW_SL_ROM and selected_value = {}. '.format(selected_value) +
                'This is a bug, please report it.')
            return

    # --- Execute action ---
    if action == ACTION_VIEW_HISTORY:
        if view_type == VIEW_MAME_MACHINE:
            if machine_name not in History_idx_dic['mame']['machines']:
                kodi_dialog_OK('MAME machine {} not in History DAT'.format(machine_name))
                return
            m_str = History_idx_dic['mame']['machines'][machine_name]
            display_name, db_list, db_machine = m_str.split('|')
            DAT_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_DB_PATH.getPath())
            t_str = ('History DAT for MAME machine [COLOR=orange]{}[/COLOR] '
                '(DB entry [COLOR=orange]{}[/COLOR])')
            window_title = t_str.format(machine_name, db_machine)
        elif view_type == VIEW_SL_ROM:
            if SL_name not in History_idx_dic:
                kodi_dialog_OK('SL {} not found in History DAT'.format(SL_name))
                return
            if SL_ROM not in History_idx_dic[SL_name]['machines']:
                kodi_dialog_OK('SL {} item {} not in History DAT'.format(SL_name, SL_ROM))
                return
            m_str = History_idx_dic[SL_name]['machines'][SL_ROM]
            display_name, db_list, db_machine = m_str.split('|')
            DAT_dic = fs_load_JSON_file_dic(g_PATHS.HISTORY_DB_PATH.getPath())
            t_str = ('History DAT for SL [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR] '
                '(DB entry [COLOR=orange]{}[/COLOR] / [COLOR=orange]{}[/COLOR])')
            window_title = t_str.format(SL_name, SL_ROM, db_list, db_machine)
        display_text_window(window_title, DAT_dic[db_list][db_machine])

    elif action == ACTION_VIEW_MAMEINFO:
        if machine_name not in Mameinfo_idx_dic['mame']:
            kodi_dialog_OK('Machine {} not in Mameinfo DAT'.format(machine_name))
            return
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.MAMEINFO_DB_PATH.getPath())
        t_str = 'MAMEINFO information for [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR]'
        window_title = t_str.format('mame', machine_name)
        display_text_window(window_title, DAT_dic['mame'][machine_name])

    elif action == ACTION_VIEW_GAMEINIT:
        if machine_name not in Gameinit_idx_list:
            kodi_dialog_OK('Machine {} not in Gameinit DAT'.format(machine_name))
            return
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.GAMEINIT_DB_PATH.getPath())
        window_title = 'Gameinit information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        display_text_window(window_title, DAT_dic[machine_name])

    elif action == ACTION_VIEW_COMMAND:
        if machine_name not in Command_idx_list:
            kodi_dialog_OK('Machine {} not in Command DAT'.format(machine_name))
            return
        DAT_dic = fs_load_JSON_file_dic(g_PATHS.COMMAND_DB_PATH.getPath())
        window_title = 'Command information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        display_text_window(window_title, DAT_dic[machine_name])

    # --- View Fanart ---
    elif action == ACTION_VIEW_FANART:
        # >> Open ROM in assets database
        if view_type == VIEW_MAME_MACHINE:
            if location == 'STANDARD':
                assets_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_ASSETS_DB_PATH.getPath())
                m_assets = assets_dic[machine_name]
            else:
                mame_favs_dic = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
                m_assets = mame_favs_dic[machine_name]['assets']
            if not m_assets['fanart']:
                kodi_dialog_OK('Fanart for machine {} not found.'.format(machine_name))
                return
        elif view_type == VIEW_SL_ROM:
            SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            m_assets = SL_asset_dic[SL_ROM]
            if not m_assets['fanart']:
                kodi_dialog_OK('Fanart for SL item {0} not found.'.format(SL_ROM))
                return

        # >> If manual found then display it.
        log_debug('Rendering FS fanart "{}"'.format(m_assets['fanart']))
        xbmc.executebuiltin('ShowPicture("{}")'.format(m_assets['fanart']))

    # --- View Manual ---
    # When Pictures menu is clicked on Home, the window pictures (MyPics.xml) opens.
    # Pictures are browsed with the pictures window. When an image is clicked with ENTER the
    # window changes to slideshow (SlideShow.xml) and the pictures are displayed in full 
    # screen with not pan/zoom effects. Pictures can be changed with the arrow keys (they
    # do not change automatically). The slideshow can also be started from the side menu 
    # "View slideshow". Initiated this way, the slideshow has a pan/zooming effects and all 
    # pictures in the list are changed every few seconds.
    #
    # Use the builtin function SlideShow("{0}",pause) to show a set of pictures in full screen.
    # See https://forum.kodi.tv/showthread.php?tid=329349
    #
    elif action == ACTION_VIEW_MANUAL:
        # --- Slideshow DEBUG snippet ---
        # >> https://kodi.wiki/view/List_of_built-in_functions is outdated!
        # >> See https://github.com/xbmc/xbmc/blob/master/xbmc/interfaces/builtins/PictureBuiltins.cpp
        # >> '\' in path strings must be escaped like '\\'
        # >> Builtin function arguments can be in any order (at least for this function).
        # xbmc.executebuiltin('SlideShow("{0}",pause)'.format(r'E:\\AML-stuff\\AML-assets\\fanarts\\'))

        # >> If manual found then display it.
        # >> First, extract images from the PDF/CBZ.
        # >> Put the extracted images in a directory named MANUALS_DIR/manual_name.pages/
        # >> Check the modification times of the PDF manual file witht the timestamp of
        # >> the first file to regenerate the images if PDF is newer than first extracted img.
        # NOTE CBZ/CBR files are supported by Kodi. It can be extracted with the builtin
        #      function extract. In addition to PDF extension, CBR and CBZ extensions must
        #      also be searched for manuals.
        if view_type == VIEW_MAME_MACHINE:
            log_debug('Displaying Manual for MAME machine {0} ...'.format(machine_name))
            # machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
            assets_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_ASSETS_DB_PATH.getPath())
            if not assets_dic[machine_name]['manual']:
                kodi_dialog_OK('Manual not found in database.')
                return
            man_file_FN = FileName(assets_dic[machine_name]['manual'])
            img_dir_FN = FileName(g_settings['assets_path']).pjoin('manuals').pjoin(machine_name + '.pages')
        elif view_type == VIEW_SL_ROM:
            log_debug('Displaying Manual for SL {0} item {1} ...'.format(SL_name, SL_ROM))
            SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            if not SL_asset_dic[SL_ROM]['manual']:
                kodi_dialog_OK('Manual not found in database.')
                return
            man_file_FN = FileName(SL_asset_dic[SL_ROM]['manual'])
            img_dir_FN = FileName(g_settings['assets_path']).pjoin('manuals_SL').pjoin(SL_name).pjoin(SL_ROM + '.pages')
        log_debug('man_file_FN P "{0}"'.format(man_file_FN.getPath()))
        log_debug('img_dir_FN P  "{0}"'.format(img_dir_FN.getPath()))

        # --- Check for errors ---
        if not man_file_FN.exists():
            kodi_dialog_OK('Manual "{0}" not found.'.format(man_file_FN.getPath()))
            return

        # --- Only PDF files supported at the moment ---
        man_ext = man_file_FN.getExt().lower()
        log_debug('Manual file extension "{0}"'.format(man_ext))
        if not man_ext == '.pdf':
            kodi_dialog_OK('Only PDF files supported at the moment.')
            return

        # --- If output directory does not exist create it ---
        if not img_dir_FN.exists():
            log_info('Creating DIR "{0}"'.format(img_dir_FN.getPath()))
            img_dir_FN.makedirs()

        # OLD CODE
        # pDialog = xbmcgui.DialogProgress()
        # pDialog.create('Advanced MAME Launcher', 'Extracting manual images')
        # pDialog.update(0)
        # status_dic = {
        #     'manFormat' : '', # PDF, CBZ, CBR, ...
        #     'numImages' : 0,
        # }
        # manuals_extract_pages(status_dic, man_file_FN, img_dir_FN)
        # pDialog.update(100)
        # pDialog.close()

        # Check if JSON INFO file exists. If so, read it and compare the timestamp of the
        # extraction of the images with the timestamp of the PDF file. Do not extract
        # the images if the images are newer than the PDF.
        status_dic = manuals_check_img_extraction_needed(man_file_FN, img_dir_FN)
        if status_dic['extraction_needed']:
            log_info('Extracting images from PDF file.')
            # --- Open manual file ---
            manuals_open_PDF_file(status_dic, man_file_FN, img_dir_FN)
            if status_dic['abort_extraction']:
                kodi_dialog_OK('Cannot extract images from file {0}'.format(man_file_FN.getPath()))
                return
            manuals_get_PDF_filter_list(status_dic, man_file_FN, img_dir_FN)

            # --- Extract page by page ---
            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced MAME Launcher', 'Extracting manual images')
            page_counter = 0
            for page_index in range(status_dic['numPages']):
                pDialog.update(int((100*page_counter)/status_dic['numPages']))
                manuals_extract_PDF_page(status_dic, man_file_FN, img_dir_FN, page_index)
                page_counter += 1
            pDialog.update(int((100*page_counter)/status_dic['numPages']))
            pDialog.close()
            manuals_close_PDF_file()

            # --- Create JSON INFO file ---
            manuals_create_INFO_file(status_dic, man_file_FN, img_dir_FN)
        else:
            log_info('Extraction of PDF images skipped.')

        # --- Display page images ---
        if status_dic['numImages'] < 1:
            log_info('No images found. Nothing to show.')
            str_list = [
                'Cannot find images inside the {0} file. '.format(status_dic['manFormat']),
                'Check log for more details.'
            ]
            kodi_dialog_OK(''.join(str_list))
            return
        log_info('Rendering images in "{0}"'.format(img_dir_FN.getPath()))
        xbmc.executebuiltin('SlideShow("{0}",pause)'.format(img_dir_FN.getPath()))

    # --- Display brother machines (same driver) ---
    elif action == ACTION_VIEW_BROTHERS:
        # >> Load ROM Render data from hashed database
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        # >> Some (important) drivers have a different name
        sourcefile_str = machine['sourcefile']
        log_debug('Original driver "{0}"'.format(sourcefile_str))
        if sourcefile_str in mame_driver_name_dic:
            sourcefile_str = mame_driver_name_dic[sourcefile_str]
        log_debug('Final driver    "{0}"'.format(sourcefile_str))

        # --- Replace current window by search window ---
        # When user press Back in search window it returns to the original window (either showing
        # launcher in a cateogory or displaying ROMs in a launcher/virtual launcher).
        #
        # NOTE ActivateWindow() / RunPlugin() / RunAddon() seem not to work here
        url = misc_url_2_arg('catalog', 'Driver', 'category', sourcefile_str)
        log_debug('Container.Update URL "{0}"'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    # --- Display machines with same Genre ---
    elif action == ACTION_VIEW_SAME_GENRE:
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        genre_str = machine['genre']
        url = misc_url_2_arg('catalog', 'Genre', 'category', genre_str)
        log_debug('Container.Update URL {0}'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    # --- Display machines by same Manufacturer ---
    elif action == ACTION_VIEW_SAME_MANUFACTURER:
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        manufacturer_str = machine['manufacturer']
        url = misc_url_2_arg('catalog', 'Manufacturer', 'category', manufacturer_str)
        log_debug('Container.Update URL {0}'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    else:
        kodi_dialog_OK('Unknown action == {0}. '.format(action) +
                       'This is a bug, please report it.')

# ---------------------------------------------------------------------------------------------
# Information display
# ---------------------------------------------------------------------------------------------
def command_context_view(machine_name, SL_name, SL_ROM, location):
    VIEW_MAME_MACHINE = 100
    VIEW_SL_ROM       = 200

    ACTION_VIEW_MACHINE_DATA       = 100
    ACTION_VIEW_SL_ROM_DATA        = 200
    ACTION_VIEW_MACHINE_ROMS       = 300
    ACTION_VIEW_MACHINE_AUDIT_ROMS = 400
    ACTION_VIEW_SL_ROM_ROMS        = 500
    ACTION_VIEW_SL_ROM_AUDIT_ROMS  = 600
    ACTION_VIEW_MANUAL_JSON        = 700
    ACTION_AUDIT_MAME_MACHINE      = 800
    ACTION_AUDIT_SL_MACHINE        = 900

    # --- Determine view type ---
    log_debug('command_context_view() machine_name "{0}"'.format(machine_name))
    log_debug('command_context_view() SL_name      "{0}"'.format(SL_name))
    log_debug('command_context_view() SL_ROM       "{0}"'.format(SL_ROM))
    log_debug('command_context_view() location     "{0}"'.format(location))
    if machine_name:
        view_type = VIEW_MAME_MACHINE
    elif SL_name:
        view_type = VIEW_SL_ROM
    else:
        kodi_dialog_OK(
            'In command_context_view(), undetermined view_type. This is a bug, please report it.')
        return
    log_debug('command_context_view() view_type = {0}'.format(view_type))

    # --- Build menu base on view_type ---
    if view_type == VIEW_MAME_MACHINE:
        d_list = [
          'View MAME machine data',
          'View MAME machine ROMs (ROMs DB)',
          'View MAME machine ROMs (Audit DB)',
          'Audit MAME machine ROMs',
          'View manual INFO file',
        ]
    elif view_type == VIEW_SL_ROM:
        d_list = [
          'View Software List item data',
          'View Software List item ROMs (ROMs DB)',
          'View Software List item ROMs (Audit DB)',
          'Audit Software List item',
        ]
    else:
        kodi_dialog_OK('Wrong view_type = {0}. This is a bug, please report it.'.format(view_type))
        return
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Polymorphic menu. Determine action to do. ---
    if view_type == VIEW_MAME_MACHINE:
        if   selected_value == 0: action = ACTION_VIEW_MACHINE_DATA
        elif selected_value == 1: action = ACTION_VIEW_MACHINE_ROMS
        elif selected_value == 2: action = ACTION_VIEW_MACHINE_AUDIT_ROMS
        elif selected_value == 3: action = ACTION_AUDIT_MAME_MACHINE
        elif selected_value == 4: action = ACTION_VIEW_MANUAL_JSON
        else:
            kodi_dialog_OK('view_type == VIEW_MAME_MACHINE and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_SL_ROM:
        if   selected_value == 0: action = ACTION_VIEW_SL_ROM_DATA
        elif selected_value == 1: action = ACTION_VIEW_SL_ROM_ROMS
        elif selected_value == 2: action = ACTION_VIEW_SL_ROM_AUDIT_ROMS
        elif selected_value == 3: action = ACTION_AUDIT_SL_MACHINE
        else:
            kodi_dialog_OK('view_type == VIEW_SL_ROM and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    else:
        kodi_dialog_OK('Wrong view_type = {0}. '.format(view_type) +
                       'This is a bug, please report it.')
        return
    log_debug('command_context_view() action = {0}'.format(action))

    # --- Execute action ---
    if action == ACTION_VIEW_MACHINE_DATA:
        pDialog = xbmcgui.DialogProgress()
        if location == LOCATION_STANDARD:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'ROM hashed database')
            machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
            pDialog.update(50, pdialog_line1, 'Assets hashed database')
            assets = fs_get_machine_assets_db_hash(g_PATHS, machine_name)
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            window_title = 'MAME Machine Information'

        elif location == LOCATION_MAME_FAVS:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'MAME Favourites database')
            machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            machine = machines[machine_name]
            assets = machine['assets']
            window_title = 'Favourite MAME Machine Information'

        elif location == LOCATION_MAME_MOST_PLAYED:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'MAME Most Played database')
            most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            machine = most_played_roms_dic[machine_name]
            assets = machine['assets']
            window_title = 'Most Played MAME Machine Information'

        elif location == LOCATION_MAME_RECENT_PLAYED:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'MAME Recently Played database')
            recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            machine_index = -1
            for i, recent_rom in enumerate(recent_roms_list):
                if machine_name == recent_rom['name']:
                    machine_index = i
                    break
            if machine_index < 0:
                kodi_dialog_OK('machine_index < 0. Please report this bug.')
                return
            machine = recent_roms_list[machine_index]
            assets = machine['assets']
            window_title = 'Recently Played MAME Machine Information'

        # --- Make information string and display text window ---
        slist = []
        mame_info_MAME_print(slist, location, machine_name, machine, assets)
        display_text_window(window_title, '\n'.join(slist))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_MAME_item_data']:
            log_info('Writing file "{0}"'.format(g_PATHS.REPORT_DEBUG_MAME_ITEM_DATA_PATH.getPath()))
            with open(g_PATHS.REPORT_DEBUG_MAME_ITEM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(slist)
                file.write('\n'.join(slist).encode('utf-8'))

    # --- View Software List ROM Machine data ---
    elif action == ACTION_VIEW_SL_ROM_DATA:
        if location == LOCATION_STANDARD:
            # --- Load databases ---
            SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_items.json')
            roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())

            # --- Prepare data ---
            rom = roms[SL_ROM]
            assets = SL_asset_dic[SL_ROM]
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Software List ROM Information'

        elif location == LOCATION_SL_FAVS:
            # --- Load databases ---
            SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
            fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())

            # --- Prepare data ---
            fav_key = SL_name + '-' + SL_ROM
            rom = fav_SL_roms[fav_key]
            assets = rom['assets']
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Favourite Software List Item Information'

        elif location == LOCATION_SL_MOST_PLAYED:
            SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
            most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())

            # --- Prepare data ---
            fav_key = SL_name + '-' + SL_ROM
            rom = most_played_roms_dic[fav_key]
            assets = rom['assets']
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Most Played SL Item Information'

        elif location == LOCATION_SL_RECENT_PLAYED:
            SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
            recent_roms_list = fs_load_JSON_file_list(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())

            # --- Prepare data ---
            fav_key = SL_name + '-' + SL_ROM
            machine_index = -1
            for i, recent_rom in enumerate(recent_roms_list):
                if fav_key == recent_rom['SL_DB_key']:
                    machine_index = i
                    break
            if machine_index < 0:
                kodi_dialog_OK('machine_index < 0. Please report this bug.')
                return
            rom = recent_roms_list[machine_index]
            assets = rom['assets']
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Recently Played SL Item Information'

        # >> Build information string
        slist = []
        mame_info_SL_print(slist, location, SL_name, SL_ROM, rom, assets, SL_dic, SL_machine_list)
        display_text_window(window_title, '\n'.join(slist))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_SL_item_data']:
            log_info('Writing file "{0}"'.format(g_PATHS.REPORT_DEBUG_SL_ITEM_DATA_PATH.getPath()))
            with open(g_PATHS.REPORT_DEBUG_SL_ITEM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(slist)
                file.write('\n'.join(slist).encode('utf-8'))

    # --- View MAME machine ROMs (ROMs database) ---
    elif action == ACTION_VIEW_MACHINE_ROMS:
        # >> Load machine dictionary, ROM database and Devices database.
        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 3
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machines Main')
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machine ROMs')
        roms_db_dic = fs_load_JSON_file_dic(g_PATHS.ROMS_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machine Devices')
        devices_db_dic = fs_load_JSON_file_dic(g_PATHS.DEVICES_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Make a dictionary with device ROMs ---
        device_roms_list = []
        for device in devices_db_dic[machine_name]:
            device_roms_dic = roms_db_dic[device]
            for rom in device_roms_dic['roms']:
                rom['device_name'] = device
                device_roms_list.append(copy.deepcopy(rom))

        # --- ROM info ---
        info_text = []
        if machine['cloneof'] and machine['romof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0} / '.format(machine['cloneof']) +
                             '[COLOR violet]romof[/COLOR] {0}'.format(machine['romof']))
        elif machine['cloneof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0}'.format(machine['cloneof']))
        elif machine['romof']:
            info_text.append('[COLOR violet]romof[/COLOR] {0}'.format(machine['romof']))
        info_text.append('[COLOR skyblue]isBIOS[/COLOR] {0} / '.format(unicode(machine['isBIOS'])) +
                         '[COLOR skyblue]isDevice[/COLOR] {0}'.format(unicode(machine['isDevice'])))
        info_text.append('')

        # --- Table header ---
        # Table cell padding: left, right
        table_str = [
            ['right', 'left',     'right', 'left',     'left',  'left'],
            ['Type',  'ROM name', 'Size',  'CRC/SHA1', 'Merge', 'BIOS/Device'],
        ]

        # --- Table: Machine ROMs ---
        roms_dic = roms_db_dic[machine_name]
        if roms_dic['roms']:
            for rom in roms_dic['roms']:
                if       rom['bios'] and     rom['merge']: r_type = 'BROM'
                elif     rom['bios'] and not rom['merge']: r_type = 'XROM'
                elif not rom['bios'] and     rom['merge']: r_type = 'MROM'
                elif not rom['bios'] and not rom['merge']: r_type = 'ROM'
                else:                                      r_type = 'ERROR'
                table_row = [r_type, str(rom['name']), str(rom['size']),
                             str(rom['crc']), str(rom['merge']), str(rom['bios'])]
                table_str.append(table_row)

        # --- Table: device ROMs ---
        if device_roms_list:
            for rom in device_roms_list:
                table_row = ['DROM', str(rom['name']), str(rom['size']),
                             str(rom['crc']), str(rom['merge']), str(rom['device_name'])]
                table_str.append(table_row)

        # --- Table: machine CHDs ---
        if roms_dic['disks']:
            for disk in roms_dic['disks']:
                table_row = ['DISK', str(disk['name']), '',
                             str(disk['sha1'])[0:8], str(disk['merge']), '']
                table_str.append(table_row)

        # --- Table: machine Samples ---
        if roms_dic['samples']:
            for sample in roms_dic['samples']:
                table_row = ['SAM', str(sample['name']), '', '', '', '']
                table_str.append(table_row)

        # --- Table: BIOSes ---
        if roms_dic['bios']:
            bios_table_str = []
            bios_table_str.append(['right',     'left'])
            bios_table_str.append(['BIOS name', 'Description'])
            for bios in roms_dic['bios']:
                table_row = [str(bios['name']), str(bios['description'])]
                bios_table_str.append(table_row)

        # --- Render text information window ---
        table_str_list = text_render_table_str(table_str)
        info_text.extend(table_str_list)
        if roms_dic['bios']:
            bios_table_str_list = text_render_table_str(bios_table_str)
            info_text.append('')
            info_text.extend(bios_table_str_list)
        window_title = 'Machine {0} ROMs'.format(machine_name)
        display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_MAME_ROM_DB_data']:
            log_info('Writing file "{0}"'.format(g_PATHS.REPORT_DEBUG_MAME_ITEM_ROM_DATA_PATH.getPath()))
            with open(g_PATHS.REPORT_DEBUG_MAME_ITEM_ROM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View MAME machine ROMs (Audit ROM database) ---
    elif action == ACTION_VIEW_MACHINE_AUDIT_ROMS:
        # --- Load machine dictionary and ROM database ---
        rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][g_settings['mame_rom_set']]
        log_debug('command_context_view() View Machine ROMs (Audit database)\n')
        log_debug('command_context_view() rom_set {0}\n'.format(rom_set))

        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 2
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machine hash')
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME ROM Audit')
        audit_roms_dic = fs_load_JSON_file_dic(g_PATHS.ROM_AUDIT_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Grab data and settings ---
        rom_list = audit_roms_dic[machine_name]
        cloneof = machine['cloneof']
        romof = machine['romof']
        log_debug('command_context_view() machine {0}\n'.format(machine_name))
        log_debug('command_context_view() cloneof {0}\n'.format(cloneof))
        log_debug('command_context_view() romof   {0}\n'.format(romof))

        # --- Generate report ---
        info_text = []
        if machine['cloneof'] and machine['romof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0} / '.format(machine['cloneof']) +
                             '[COLOR violet]romof[/COLOR] {0}'.format(machine['romof']))
        elif machine['cloneof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0}'.format(machine['cloneof']))
        elif machine['romof']:
            info_text.append('[COLOR violet]romof[/COLOR] {0}'.format(machine['romof']))
        info_text.append('[COLOR skyblue]isBIOS[/COLOR] {0} / '.format(unicode(machine['isBIOS'])) +
                         '[COLOR skyblue]isDevice[/COLOR] {0}'.format(unicode(machine['isDevice'])))
        info_text.append('')

        # --- Table header ---
        # Table cell padding: left, right
        # Table columns: Type - ROM name - Size - CRC/SHA1 - Merge - BIOS - Location
        table_str = []
        table_str.append(['right', 'left',     'right', 'left',     'left'])
        table_str.append(['Type',  'ROM name', 'Size',  'CRC/SHA1', 'Location'])

        # --- Table rows ---
        for m_rom in rom_list:
            if m_rom['type'] == ROM_TYPE_DISK:
                sha1_str = str(m_rom['sha1'])[0:8]
                table_row = [str(m_rom['type']), str(m_rom['name']), '', sha1_str, m_rom['location']]
            elif m_rom['type'] == ROM_TYPE_SAMPLE:
                table_row = [str(m_rom['type']), str(m_rom['name']), '', '', str(m_rom['location'])]
            else:
                table_row = [str(m_rom['type']), str(m_rom['name']), str(m_rom['size']),
                             str(m_rom['crc']), str(m_rom['location'])]
            table_str.append(table_row)
        table_str_list = text_render_table_str(table_str)
        info_text.extend(table_str_list)
        window_title = 'Machine {0} ROM audit'.format(machine_name)
        display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_MAME_Audit_DB_data']:
            log_info('Writing file "{0}"'.format(g_PATHS.REPORT_DEBUG_MAME_ITEM_AUDIT_DATA_PATH.getPath()))
            with open(g_PATHS.REPORT_DEBUG_MAME_ITEM_AUDIT_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View SL ROMs ---
    elif action == ACTION_VIEW_SL_ROM_ROMS:
        SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_items.json')
        SL_ROMS_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_ROMs.json')
        # SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
        # SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
        # assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        # SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
        # SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
        # SL_dic = SL_catalog_dic[SL_name]
        # SL_machine_list = SL_machines_dic[SL_name]
        # assets = SL_asset_dic[SL_ROM] if SL_ROM in SL_asset_dic else fs_new_SL_asset()
        roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
        roms_db = fs_load_JSON_file_dic(SL_ROMS_DB_FN.getPath())
        rom = roms[SL_ROM]
        rom_db_list = roms_db[SL_ROM]

        info_text = []
        info_text.append('[COLOR violet]SL_name[/COLOR] {0}'.format(SL_name))
        info_text.append('[COLOR violet]SL_ROM[/COLOR] {0}'.format(SL_ROM))
        info_text.append('[COLOR violet]description[/COLOR] {0}'.format(rom['description']))
        if rom['cloneof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0}'.format(rom['cloneof']))
        info_text.append('')

        table_str = []
        table_str.append(['left',      'left',       'left',      'left',   'left',         'left', 'left'])
        table_str.append(['Part name', 'Part iface', 'Area type', 'A name', 'ROM/CHD name', 'Size', 'CRC/SHA1'])
        # >> Iterate Parts
        for part_dic in rom_db_list:
            part_name = part_dic['part_name']
            part_interface = part_dic['part_interface']
            if 'dataarea' in part_dic:
                # >> Iterate Dataareas
                for dataarea_dic in part_dic['dataarea']:
                    dataarea_name = dataarea_dic['name']
                    # >> Interate ROMs in dataarea
                    for rom_dic in dataarea_dic['roms']:
                        table_row = [part_name, part_interface,
                                     'dataarea', dataarea_name,
                                     rom_dic['name'], str(rom_dic['size']), rom_dic['crc']]
                        table_str.append(table_row)
            if 'diskarea' in part_dic:
                # >> Iterate Diskareas
                for diskarea_dic in part_dic['diskarea']:
                    diskarea_name = diskarea_dic['name']
                    # >> Iterate DISKs in diskarea
                    for rom_dic in diskarea_dic['disks']:
                        table_row = [part_name, part_interface,
                                     'diskarea', diskarea_name,
                                     rom_dic['name'], '', rom_dic['sha1'][0:8]]
                        table_str.append(table_row)
        table_str_list = text_render_table_str(table_str)
        info_text.extend(table_str_list)
        window_title = 'Software List ROM List (ROMs DB)'
        display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_SL_ROM_DB_data']:
            log_info('Writing file "{0}"'.format(g_PATHS.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH.getPath()))
            with open(g_PATHS.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View SL ROM Audit ROMs ---
    elif action == ACTION_VIEW_SL_ROM_AUDIT_ROMS:
        SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_items.json')
        # SL_ROMs_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_roms.json')
        SL_ROM_Audit_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_ROM_audit.json')

        roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
        rom_audit_db = fs_load_JSON_file_dic(SL_ROM_Audit_DB_FN.getPath())
        rom = roms[SL_ROM]
        rom_db_list = rom_audit_db[SL_ROM]

        info_text = []
        info_text.append('[COLOR violet]SL_name[/COLOR] {0}'.format(SL_name))
        info_text.append('[COLOR violet]SL_ROM[/COLOR] {0}'.format(SL_ROM))
        info_text.append('[COLOR violet]description[/COLOR] {0}'.format(rom['description']))
        if rom['cloneof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0}'.format(rom['cloneof']))
        info_text.append('')

        # table_str = [    ['left', 'left',         'left', 'left',     'left'] ]
        # table_str.append(['Type', 'ROM/CHD name', 'Size', 'CRC/SHA1', 'Location'])
        table_str = [    ['left', 'left', 'left',     'left'] ]
        table_str.append(['Type', 'Size', 'CRC/SHA1', 'Location'])
        for rom_dic in rom_db_list:
            if rom_dic['type'] == ROM_TYPE_DISK:
                table_row = [rom_dic['type'], # rom_dic['name'],
                             '', rom_dic['sha1'][0:8], rom_dic['location']]
                table_str.append(table_row)
            else:
                table_row = [rom_dic['type'], # rom_dic['name'],
                             str(rom_dic['size']), rom_dic['crc'], rom_dic['location']]
                table_str.append(table_row)
        table_str_list = text_render_table_str(table_str)
        info_text.extend(table_str_list)
        window_title = 'Software List ROM List (Audit DB)'
        display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_SL_Audit_DB_data']:
            log_info('Writing file "{0}"'.format(g_PATHS.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH.getPath()))
            with open(g_PATHS.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View manual JSON INFO file of a MAME machine ---
    elif action == ACTION_VIEW_MANUAL_JSON:
        pdialog_line1 = 'Loading databases ...'
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(0, pdialog_line1, 'ROM hashed database')
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        pDialog.update(50, pdialog_line1, 'Assets hashed database')
        assets = fs_get_machine_assets_db_hash(g_PATHS, machine_name)
        pDialog.update(100, pdialog_line1)
        pDialog.close()
            
        if not assets['manual']:
            kodi_dialog_OK('Manual not found in database.')
            return
        man_file_FN = FileName(assets['manual'])
        img_dir_FN = FileName(g_settings['assets_path']).pjoin('manuals').pjoin(machine_name + '.pages')
        rom_name = man_file_FN.getBase_noext()
        info_FN = img_dir_FN.pjoin(rom_name + '.json')
        if not info_FN.exists():
            kodi_dialog_OK('Manual JSON INFO file not found. View the manual first.')
            return

        # --- Read stdout and put into a string ---
        window_title = 'MAME machine manual JSON INFO file'
        info_text = ''
        with open(info_FN.getPath(), 'r') as myfile:
            info_text = myfile.read()
        display_text_window(window_title, info_text)

    # --- Audit ROMs of a single machine ---
    elif action == ACTION_AUDIT_MAME_MACHINE:
        # --- Load machine dictionary and ROM database ---
        rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][g_settings['mame_rom_set']]
        log_debug('command_context_view() Auditing Machine ROMs\n')
        log_debug('command_context_view() rom_set {0}\n'.format(rom_set))

        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 2
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machine hash')
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME ROM Audit')
        audit_roms_dic = fs_load_JSON_file_dic(g_PATHS.ROM_AUDIT_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Grab data and settings ---
        rom_list = audit_roms_dic[machine_name]
        cloneof = machine['cloneof']
        romof = machine['romof']
        log_debug('command_context_view() machine {0}\n'.format(machine_name))
        log_debug('command_context_view() cloneof {0}\n'.format(cloneof))
        log_debug('command_context_view() romof   {0}\n'.format(romof))

        # --- Open ZIP file, check CRC32 and also CHDs ---
        audit_dic = fs_new_audit_dic()
        mame_audit_MAME_machine(g_settings, rom_list, audit_dic)

        # --- Generate report ---
        info_text = []
        if machine['cloneof'] and machine['romof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0} / '.format(machine['cloneof']) +
                             '[COLOR violet]romof[/COLOR] {0}'.format(machine['romof']))
        elif machine['cloneof']:
            info_text.append('[COLOR violet]cloneof[/COLOR] {0}'.format(machine['cloneof']))
        elif machine['romof']:
            info_text.append('[COLOR violet]romof[/COLOR] {0}'.format(machine['romof']))
        info_text.append('[COLOR skyblue]isBIOS[/COLOR] {0} / '.format(unicode(machine['isBIOS'])) +
                         '[COLOR skyblue]isDevice[/COLOR] {0}'.format(unicode(machine['isDevice'])))
        info_text.append('')

        # --- Table header ---
        # Table cell padding: left, right
        # Table columns: Type - ROM name - Size - CRC/SHA1 - Merge - BIOS - Location
        table_str = []
        table_str.append(['right', 'left',     'right', 'left',     'left',     'left'])
        table_str.append(['Type',  'ROM name', 'Size',  'CRC/SHA1', 'Location', 'Status'])

        # --- Table rows ---
        for m_rom in rom_list:
            if m_rom['type'] == ROM_TYPE_DISK:
                sha1_srt = m_rom['sha1'][0:8]
                table_row = [m_rom['type'], m_rom['name'], '', sha1_srt,
                             m_rom['location'], m_rom['status_colour']]
            elif m_rom['type'] == ROM_TYPE_SAMPLE:
                table_row = [str(m_rom['type']), str(m_rom['name']), '', '',
                             m_rom['location'], m_rom['status_colour']]
            else:
                table_row = [str(m_rom['type']), str(m_rom['name']),
                             str(m_rom['size']), str(m_rom['crc']),
                             m_rom['location'], m_rom['status_colour']]
            table_str.append(table_row)
        table_str_list = text_render_table_str(table_str)
        info_text.extend(table_str_list)
        window_title = 'Machine {0} ROM audit'.format(machine_name)
        display_text_window(window_title, '\n'.join(info_text))

    # --- Audit ROMs of SL item ---
    elif action == ACTION_AUDIT_SL_MACHINE:
        # --- Load machine dictionary and ROM database ---
        log_debug('command_context_view() Auditing SL Software ROMs\n')
        log_debug('command_context_view() SL_name {0}\n'.format(SL_name))
        log_debug('command_context_view() SL_ROM {0}\n'.format(SL_ROM))

        SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_items.json')
        SL_ROM_Audit_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_ROM_audit.json')

        roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
        roms_audit_db = fs_load_JSON_file_dic(SL_ROM_Audit_DB_FN.getPath())
        rom = roms[SL_ROM]
        rom_db_list = roms_audit_db[SL_ROM]

        # --- Open ZIP file and check CRC32 ---
        audit_dic = fs_new_audit_dic()
        SL_ROM_path_FN = FileName(g_settings['SL_rom_path'])
        SL_CHD_path_FN = FileName(g_settings['SL_chd_path'])
        mame_audit_SL_machine(SL_ROM_path_FN, SL_CHD_path_FN, SL_name, SL_ROM, rom_db_list, audit_dic)

        info_text = []
        info_text.append('[COLOR violet]SL_name[/COLOR] {0}'.format(SL_name))
        info_text.append('[COLOR violet]SL_ROM[/COLOR] {0}'.format(SL_ROM))
        info_text.append('[COLOR violet]description[/COLOR] {0}'.format(rom['description']))
        info_text.append('')

        # --- Table header and rows ---
        # >> Do not render ROM name in SLs, cos they are really long.
        # table_str = [    ['right', 'left',     'right', 'left',     'left',     'left'] ]
        # table_str.append(['Type',  'ROM name', 'Size',  'CRC/SHA1', 'Location', 'Status'])
        table_str = [    ['right', 'right', 'left',     'left',     'left'] ]
        table_str.append(['Type',  'Size',  'CRC/SHA1', 'Location', 'Status'])
        for m_rom in rom_db_list:
            if m_rom['type'] == ROM_TYPE_DISK:
                table_row = [m_rom['type'], # m_rom['name'],
                             '', m_rom['sha1'][0:8], m_rom['location'],
                             m_rom['status_colour']]
                table_str.append(table_row)
            else:
                table_row = [m_rom['type'], # m_rom['name'],
                             str(m_rom['size']), m_rom['crc'], m_rom['location'],
                             m_rom['status_colour']]
                table_str.append(table_row)
        table_str_list = text_render_table_str(table_str)
        info_text.extend(table_str_list)
        window_title = 'SL {0} Software {1} ROM audit'.format(SL_name, SL_ROM)
        display_text_window(window_title, '\n'.join(info_text))

    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_context_utilities(catalog_name, category_name):
    log_debug('command_context_utilities() catalog_name  "{0}"'.format(catalog_name))
    log_debug('command_context_utilities() category_name "{0}"'.format(category_name))

    d_list = [
      'Export AEL Virtual Launcher',
    ]
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Export AEL Virtual Launcher ---
    if selected_value == 0:
        log_debug('command_context_utilities() Export AEL Virtual Launcher')

        # >> Ask user for a path to export the launcher configuration
        vlauncher_str_name = 'AML_VLauncher_' + catalog_name + '_' + category_name + '.xml'
        dir_path = xbmcgui.Dialog().browse(0, 'Select XML export directory', 'files', 
                                           '', False, False).decode('utf-8')
        if not dir_path: return
        export_FN = FileName(dir_path).pjoin(vlauncher_str_name)
        if export_FN.exists():
            ret = kodi_dialog_yesno('Overwrite file {0}?'.format(export_FN.getPath()))
            if not ret:
                kodi_notify_warn('Export of Launcher XML cancelled')
                return

        # --- Open databases and get list of machines of this filter ---
        # >> This can be optimised: load stuff from the cache instead of the main databases.
        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 4
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'Catalog dictionary')
        catalog_dic = fs_get_cataloged_dic_parents(g_PATHS, catalog_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(g_PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(g_PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME machine Assets')
        assets_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Print error message is something goes wrong writing file ---
        try:
            fs_export_Virtual_Launcher(
                export_FN, catalog_dic[category_name], machines, machines_render, assets_dic)
        except Addon_Error as ex:
            kodi_notify_warn('{0}'.format(ex))
        else:
            kodi_notify('Exported Virtual Launcher "{0}"'.format(vlauncher_str_name))

# -------------------------------------------------------------------------------------------------
# MAME Favourites/Recently Played/Most played
# -------------------------------------------------------------------------------------------------
# Favourites use the main hashed database, not the main and render databases.
def command_context_add_mame_fav(machine_name):
    log_debug('command_add_mame_fav() Machine_name "{0}"'.format(machine_name))

    # >> Get Machine database entry
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
    assets = fs_get_machine_assets_db_hash(g_PATHS, machine_name)

    # >> Open Favourite Machines dictionary
    fav_machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())

    # >> If machine already in Favourites ask user if overwrite.
    if machine_name in fav_machines:
        ret = kodi_dialog_yesno(
            'Machine {0} ({1}) '.format(machine['description'], machine_name) +
            'already in MAME Favourites. Overwrite?')
        if ret < 1: return

    # >> Add machine. Add database version to Favourite.
    fav_machine = fs_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic)
    fav_machines[machine_name] = fav_machine
    log_info('command_add_mame_fav() Added machine "{0}"'.format(machine_name))

    # >> Save Favourites
    fs_write_JSON_file(g_PATHS.FAV_MACHINES_PATH.getPath(), fav_machines)
    kodi_notify('Machine {0} added to MAME Favourites'.format(machine_name))
    kodi_refresh_container()

def render_fav_machine_row(m_name, machine, m_assets, location):
    # --- Default values for flags ---
    AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_NONE

    # --- Mark Flags, BIOS, Devices, BIOS, Parent/Clone and Driver status ---
    display_name = machine['description']
    display_name += ' [COLOR skyblue]{0}[/COLOR]'.format(m_assets['flags'])            
    if machine['isBIOS']:   display_name += ' [COLOR cyan][BIOS][/COLOR]'
    if machine['isDevice']: display_name += ' [COLOR violet][Dev][/COLOR]'
    if machine['cloneof']:  display_name += ' [COLOR orange][Clo][/COLOR]'
    if   machine['driver_status'] == 'imperfect':   display_name += ' [COLOR yellow][Imp][/COLOR]'
    elif machine['driver_status'] == 'preliminary': display_name += ' [COLOR red][Pre][/COLOR]'
    # >> Render number of number the ROM has been launched
    if location == LOCATION_MAME_MOST_PLAYED:
        if machine['launch_count'] == 1:
            display_name = '{0} [COLOR orange][{1} time][/COLOR]'.format(display_name, machine['launch_count'])
        else:
            display_name = '{0} [COLOR orange][{1} times][/COLOR]'.format(display_name, machine['launch_count'])

    # --- Skin flags ---
    if machine['cloneof']: AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE
    else:                  AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT

    # --- Assets/artwork ---
    icon_path      = m_assets[g_mame_icon] if m_assets[g_mame_icon] else 'DefaultProgram.png'
    fanart_path    = m_assets[g_mame_fanart]
    banner_path    = m_assets['marquee']
    clearlogo_path = m_assets['clearlogo']
    poster_path    = m_assets['3dbox'] if m_assets['3dbox'] else m_assets['flyer']

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)

    # --- Metadata ---
    # >> Make all the infotables compatible with Advanced Emulator Launcher
    if g_settings['display_hide_trailers']:
        listitem.setInfo('video', {'title'   : display_name,     'year'    : machine['year'],
                                   'genre'   : machine['genre'], 'studio'  : machine['manufacturer'],
                                   'plot'    : m_assets['plot'],
                                   'overlay' : ICON_OVERLAY})
    else:
        listitem.setInfo('video', {'title'   : display_name,     'year'    : machine['year'],
                                   'genre'   : machine['genre'], 'studio'  : machine['manufacturer'],
                                   'plot'    : m_assets['plot'], 'trailer' : m_assets['trailer'],
                                   'overlay' : ICON_OVERLAY})
    listitem.setProperty('nplayers', machine['nplayers'])
    listitem.setProperty('platform', 'MAME')

    # --- Assets ---
    # >> AEL custom artwork fields
    listitem.setArt({
        'title'     : m_assets['title'],   'snap'    : m_assets['snap'],
        'boxfront'  : m_assets['cabinet'], 'boxback' : m_assets['cpanel'],
        'cartridge' : m_assets['PCB'],     'flyer'   : m_assets['flyer'],
        '3dbox'     : m_assets['3dbox'],
        'icon'      : icon_path,           'fanart'    : fanart_path,
        'banner'    : banner_path,         'clearlogo' : clearlogo_path,
        'poster'    : poster_path,
    })

    # --- ROM flags (Skins will use these flags to render icons) ---
    listitem.setProperty(AEL_PCLONE_STAT_LABEL, AEL_PClone_stat_value)

    # --- Create context menu ---
    URL_view_DAT = misc_url_3_arg_RunPlugin('command', 'VIEW_DAT', 'machine', m_name, 'location', location)
    URL_view = misc_url_3_arg_RunPlugin('command', 'VIEW', 'machine', m_name, 'location', location)
    if location == LOCATION_MAME_FAVS:
        URL_manage = misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_FAV', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Favourites', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    elif location == LOCATION_MAME_MOST_PLAYED:
        URL_manage = misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_MOST_PLAYED', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Most Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    elif location == LOCATION_MAME_RECENT_PLAYED:
        URL_manage = misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_RECENT_PLAYED', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Recently Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_3_arg('command', 'LAUNCH', 'machine', m_name, 'location', location)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)

def command_show_mame_fav():
    log_debug('command_show_mame_fav() Starting ...')

    # --- Open Favourite Machines dictionary ---
    fav_machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
    if not fav_machines:
        kodi_dialog_OK('No Favourite MAME machines. Add some machines to MAME Favourites first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Render Favourites ---
    set_Kodi_all_sorting_methods()
    for m_name in fav_machines:
        machine = fav_machines[m_name]
        assets  = machine['assets']
        render_fav_machine_row(m_name, machine, assets, LOCATION_MAME_FAVS)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Context menu "Manage Favourite machines"
#
def command_context_manage_mame_fav(machine_name):
    VIEW_ROOT_MENU   = 100
    VIEW_INSIDE_MENU = 200

    ACTION_DELETE_MACHINE = 100
    ACTION_DELETE_MISSING = 200
    ACTION_DELETE_ALL     = 300

    menus_dic = {
        VIEW_ROOT_MENU : [
            ('Delete missing machines from MAME Favourites', ACTION_DELETE_MISSING),
            ('Delete all machines from MAME Favourites', ACTION_DELETE_ALL),
        ],
        VIEW_INSIDE_MENU : [
            ('Delete machine from MAME Favourites', ACTION_DELETE_MACHINE),
            ('Delete missing machines from MAME Favourites', ACTION_DELETE_MISSING),
            ('Delete all machines from MAME Favourites', ACTION_DELETE_ALL),
        ],
    }

    # --- Determine view type ---
    log_debug('command_context_manage_mame_fav() BEGIN ...')
    log_debug('machine_name "{0}"'.format(machine_name))
    if machine_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {0}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage MAME Favourite machines', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {0}'.format(action))

    # --- Execute actions ---
    if action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_mame_fav() ACTION_DELETE_MACHINE')
        log_debug('machine_name "{0}"'.format(machine_name))
        db_files = [
            ['fav_machines', 'MAME Favourite machines', g_PATHS.FAV_MACHINES_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # --- Ask user for confirmation ---
        desc = db_dic['fav_machines'][machine_name]['description']
        ret = kodi_dialog_yesno('Delete Machine {0} ({1})?'.format(desc, machine_name))
        if ret < 1:
            kodi_notify('MAME Favourites unchanged')
            return

        # --- Delete machine and save DB ---
        del db_dic['fav_machines'][machine_name]
        log_info('Deleted machine "{0}"'.format(machine_name))
        fs_write_JSON_file(g_PATHS.FAV_MACHINES_PATH.getPath(), db_dic['fav_machines'])
        kodi_refresh_container()
        kodi_notify('Machine {0} deleted from MAME Favourites'.format(machine_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_mame_fav() ACTION_DELETE_ALL')
        db_files = [
            ['fav_machines', 'MAME Favourite machines', g_PATHS.FAV_MACHINES_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # Confirm with user
        num_machines = len(db_dic['fav_machines'])
        ret = kodi_dialog_yesno(
            'You have {0} MAME Favourites. Delete them all?'.format(num_machines))
        if ret < 1:
            kodi_notify('MAME Favourites unchanged')
            return

        # Database is an empty dictionary
        fs_write_JSON_file(g_PATHS.FAV_MACHINES_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all MAME Favourites'.format(machine_name))

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_mame_fav() ACTION_DELETE_MISSING')

        # --- Ensure MAME Catalog have been built ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options = check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)
        if not options['condition']:
            kodi_dialog_OK(options['msg'])
            return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['fav_machines', 'MAME Favourite machines', g_PATHS.FAV_MACHINES_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # --- Delete missing MAME machines ---
        line1_str = 'Delete missing MAME Favourites ...'
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher', line1_str)
        num_deleted_machines = 0
        if len(db_dic['fav_machines']) >= 1:
            num_iteration = len(db_dic['fav_machines'])
            iteration = 0
            new_fav_machines = {}
            for fav_key in sorted(db_dic['fav_machines']):
                pDialog.update((iteration*100) // num_iteration, line1_str)
                log_debug('Checking Favourite "{0}"'.format(fav_key))
                if fav_key in db_dic['machines']:
                    new_fav_machines[fav_key] = db_dic['fav_machines'][fav_key]
                else:
                    num_deleted_machines += 1
                iteration += 1
            fs_write_JSON_file(g_PATHS.FAV_MACHINES_PATH.getPath(), new_fav_machines)
            pDialog.update((iteration*100) // num_iteration, line1_str)
        else:
            pDialog.update(100, line1_str)
        pDialog.close()
        kodi_refresh_container()
        if num_deleted_machines > 0:
            kodi_notify('Deleted {0} missing MAME machines'.format(num_deleted_machines))
        else:
            kodi_notify('No missing machines found')

    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_mame_most_played():
    most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if not most_played_roms_dic:
        kodi_dialog_OK('No Most Played MAME machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method()
    sorted_dic = sorted(most_played_roms_dic, key = lambda x : most_played_roms_dic[x]['launch_count'], reverse = True)
    for machine_name in sorted_dic:
        machine = most_played_roms_dic[machine_name]
        render_fav_machine_row(machine['name'], machine, machine['assets'], LOCATION_MAME_MOST_PLAYED)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_mame_most_played(machine_name):
    VIEW_ROOT_MENU   = 100
    VIEW_INSIDE_MENU = 200

    ACTION_DELETE_MACHINE = 100
    ACTION_DELETE_MISSING = 200
    ACTION_DELETE_ALL     = 300

    menus_dic = {
        VIEW_ROOT_MENU : [
            ('Delete missing machines from MAME Most Played', ACTION_DELETE_MISSING),
            ('Delete all machines from MAME Most Played', ACTION_DELETE_ALL),
        ],
        VIEW_INSIDE_MENU : [
            ('Delete machine from MAME Most Played', ACTION_DELETE_MACHINE),
            ('Delete missing machines from MAME Most Played', ACTION_DELETE_MISSING),
            ('Delete all machines from MAME Most Played', ACTION_DELETE_ALL),
        ],
    }

    # --- Determine view type ---
    log_debug('command_context_manage_mame_most_played() BEGIN ...')
    log_debug('machine_name "{0}"'.format(machine_name))
    if machine_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {0}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage MAME Most Played machines', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {0}'.format(action))

    # --- Execute actions ---
    if action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_mame_most_played() ACTION_DELETE_MACHINE')
        db_files = [
            ['most_played_roms', 'MAME Most Played machines', g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # --- Ask user for confirmation ---
        desc = db_dic['most_played_roms'][machine_name]['description']
        ret = kodi_dialog_yesno('Delete Machine {0} ({1})?'.format(desc, machine_name))
        if ret < 1:
            kodi_notify('MAME Most Played unchanged')
            return

        # --- Delete machine and save DB ---
        del db_dic['most_played_roms'][machine_name]
        log_info('Deleted machine "{0}"'.format(machine_name))
        fs_write_JSON_file(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), db_dic['most_played_roms'])
        kodi_refresh_container()
        kodi_notify('Machine {0} deleted from MAME Most Played'.format(machine_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_mame_most_played() ACTION_DELETE_ALL')
        db_files = [
            ['most_played_roms', 'MAME Most Played machines', g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # Confirm with user
        num_machines = len(db_dic['most_played_roms'])
        ret = kodi_dialog_yesno(
            'You have {0} MAME Most Played machines. Delete them all?'.format(num_machines))
        if ret < 1:
            kodi_notify('MAME Most Played unchanged')
            return

        # Database is an empty dictionary
        fs_write_JSON_file(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all MAME Most Played'.format(machine_name))

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_mame_most_played() ACTION_DELETE_MISSING')

        # --- Ensure MAME Catalog have been built ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options = check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)
        if not options['condition']:
            kodi_dialog_OK(options['msg'])
            return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['most_played_roms', 'MAME Most Played machines', g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # --- Delete missing MAME machines ---
        line1_str = 'Delete missing MAME Most Played ...'
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher', line1_str)
        num_deleted_machines = 0
        if len(db_dic['most_played_roms']) >= 1:
            num_iteration = len(db_dic['most_played_roms'])
            iteration = 0
            new_fav_machines = {}
            for fav_key in sorted(db_dic['most_played_roms']):
                pDialog.update((iteration*100) // num_iteration, line1_str)
                log_debug('Checking Favourite "{0}"'.format(fav_key))
                if fav_key in db_dic['machines']:
                    new_fav_machines[fav_key] = db_dic['most_played_roms'][fav_key]
                else:
                    num_deleted_machines += 1
                iteration += 1
            fs_write_JSON_file(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), new_fav_machines)
            pDialog.update((iteration*100) // num_iteration, line1_str)
        else:
            pDialog.update(100, line1_str)
        pDialog.close()
        kodi_refresh_container()
        if num_deleted_machines > 0:
            kodi_notify('Deleted {0} missing MAME machines'.format(num_deleted_machines))
        else:
            kodi_notify('No missing machines found')

    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_mame_recently_played():
    recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    if not recent_roms_list:
        kodi_dialog_OK('No Recently Played MAME machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method()
    for machine in recent_roms_list:
        render_fav_machine_row(machine['name'], machine, machine['assets'], LOCATION_MAME_RECENT_PLAYED)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_mame_recent_played(machine_name):
    VIEW_ROOT_MENU   = 100
    VIEW_INSIDE_MENU = 200

    ACTION_DELETE_MACHINE = 100
    ACTION_DELETE_MISSING = 200
    ACTION_DELETE_ALL     = 300

    menus_dic = {
        VIEW_ROOT_MENU : [
            ('Delete missing machines from MAME Recently Played', ACTION_DELETE_MISSING),
            ('Delete all machines from MAME Recently Played', ACTION_DELETE_ALL),
        ],
        VIEW_INSIDE_MENU : [
            ('Delete machine from MAME Recently Played', ACTION_DELETE_MACHINE),
            ('Delete missing machines from MAME Recently Played', ACTION_DELETE_MISSING),
            ('Delete all machines from MAME Recently Played', ACTION_DELETE_ALL),
        ],
    }

    # --- Determine view type ---
    log_debug('command_context_manage_mame_recent_played() BEGIN ...')
    log_debug('machine_name "{0}"'.format(machine_name))
    if machine_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {0}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage MAME Recently Played machines', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {0}'.format(action))

    # --- Execute actions ---
    if action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_mame_recent_played() ACTION_DELETE_MACHINE')
        log_debug('machine_name "{0}"'.format(machine_name))

        # --- Load Recently Played machine list ---
        recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # --- Search index of this machine in the list ---
        machine_index = fs_locate_idx_by_name(recent_roms_list, machine_name)
        if machine_index < 0:
            a = 'Machine {0} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(machine_name))
            return

        # --- Ask user for confirmation ---
        desc = recent_roms_list[machine_index]['description']
        ret = kodi_dialog_yesno('Delete Machine {0} ({1})?'.format(desc, machine_name))
        if ret < 1:
            kodi_notify('MAME Recently Played unchanged')
            return

        # --- Delete machine and save DB ---
        recent_roms_list.pop(machine_index)
        log_info('Deleted machine "{0}"'.format(machine_name))
        fs_write_JSON_file(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        kodi_refresh_container()
        kodi_notify('Machine {0} deleted from MAME Recently Played'.format(machine_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_mame_recent_played() ACTION_DELETE_ALL')
        recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # Confirm with user
        num_machines = len(recent_roms_list)
        ret = kodi_dialog_yesno(
            'You have {0} MAME Recently Played. Delete them all?'.format(num_machines))
        if ret < 1:
            kodi_notify('MAME Recently Played unchanged')
            return

        # Database is an empty list.
        fs_write_JSON_file(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), list())
        kodi_refresh_container()
        kodi_notify('Deleted all MAME Recently Played'.format(machine_name))

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_mame_recent_played() ACTION_DELETE_MISSING')

        # --- Ensure MAME Catalog have been built ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options = check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)
        if not options['condition']:
            kodi_dialog_OK(options['msg'])
            return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)
        recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # --- Delete missing MAME machines ---
        line1_str = 'Delete missing MAME Recently Played ...'
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher', line1_str)
        num_deleted_machines = 0
        if len(recent_roms_list) >= 1:
            num_iteration = len(recent_roms_list)
            iteration = 0
            new_recent_roms_list = []
            for i, recent_rom in enumerate(recent_roms_list):
                pDialog.update((iteration*100) // num_iteration, line1_str)
                fav_key = recent_rom['name']
                log_debug('Checking Favourite "{0}"'.format(fav_key))
                if fav_key in db_dic['machines']:
                    new_recent_roms_list.append(recent_rom)
                else:
                    num_deleted_machines += 1
                iteration += 1
            fs_write_JSON_file(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), new_recent_roms_list)
            pDialog.update((iteration*100) // num_iteration, line1_str)
        else:
            pDialog.update(100, line1_str)
        pDialog.close()
        kodi_refresh_container()
        if num_deleted_machines > 0:
            kodi_notify('Deleted {0} missing MAME machines'.format(num_deleted_machines))
        else:
            kodi_notify('No missing machines found')

    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

# -------------------------------------------------------------------------------------------------
# SL Favourites/Recently Played/Most played
# -------------------------------------------------------------------------------------------------
def command_context_add_sl_fav(SL_name, ROM_name):
    log_debug('command_add_sl_fav() SL_name  "{0}"'.format(SL_name))
    log_debug('command_add_sl_fav() ROM_name "{0}"'.format(ROM_name))

    # --- Load databases ---
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
    SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(file_name)
    SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(assets_file_name)
    SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    # >> Open Favourite Machines dictionary
    fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
    SL_fav_key = SL_name + '-' + ROM_name
    log_debug('command_add_sl_fav() SL_fav_key "{0}"'.format(SL_fav_key))

    # >> If machine already in Favourites ask user if overwrite.
    if SL_fav_key in fav_SL_roms:
        ret = kodi_dialog_yesno('Machine {0} ({1}) '.format(ROM_name, SL_name) +
                                'already in SL Favourites. Overwrite?')
        if ret < 1: return

    # >> Add machine to SL Favourites
    SL_ROM = SL_roms[ROM_name]
    # SL_assets = SL_assets_dic[ROM_name] if ROM_name in SL_assets_dic else fs_new_SL_asset()
    SL_assets = SL_assets_dic[ROM_name]
    fav_ROM = fs_get_SL_Favourite(SL_name, ROM_name, SL_ROM, SL_assets, control_dic)
    fav_SL_roms[SL_fav_key] = fav_ROM
    log_info('command_add_sl_fav() Added machine "{0}" ("{1}")'.format(ROM_name, SL_name))

    # >> Save Favourites
    fs_write_JSON_file(g_PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
    kodi_notify('ROM {0} added to SL Favourite ROMs'.format(ROM_name))

def render_sl_fav_machine_row(SL_fav_key, ROM, assets, location):
    SL_name  = ROM['SL_name']
    SL_ROM_name = ROM['SL_ROM_name']
    display_name = ROM['description']

    # --- Mark Status and Clones ---
    status = '{0}{1}'.format(ROM['status_ROM'], ROM['status_CHD'])
    display_name += ' [COLOR skyblue]{0}[/COLOR]'.format(status)
    if ROM['cloneof']:  display_name += ' [COLOR orange][Clo][/COLOR]'
    # >> Render number of number the ROM has been launched
    if location == LOCATION_SL_MOST_PLAYED:
        if ROM['launch_count'] == 1:
            display_name = '{0} [COLOR orange][{1} time][/COLOR]'.format(display_name, ROM['launch_count'])
        else:
            display_name = '{0} [COLOR orange][{1} times][/COLOR]'.format(display_name, ROM['launch_count'])

    # --- Assets/artwork ---
    icon_path   = assets[g_SL_icon] if assets[g_SL_icon] else 'DefaultProgram.png'
    fanart_path = assets[g_SL_fanart]
    poster_path = assets['3dbox'] if assets['3dbox'] else assets['boxfront']

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    # >> Make all the infolabels compatible with Advanced Emulator Launcher
    if g_settings['display_hide_trailers']:
        listitem.setInfo('video', {'title'   : display_name,      'year'    : ROM['year'],
                                   'genre'   : ROM['genre'],      'studio'  : ROM['publisher'],
                                   'plot'    : ROM['plot'],       'overlay' : ICON_OVERLAY })
    else:
        listitem.setInfo('video', {'title'   : display_name,      'year'    : ROM['year'],
                                   'genre'   : ROM['genre'],      'studio'  : ROM['publisher'],
                                   'plot'    : ROM['plot'],       'overlay' : ICON_OVERLAY,
                                   'trailer' : assets['trailer'] })
    listitem.setProperty('platform', 'MAME Software List')

    # --- Assets ---
    # >> AEL custom artwork fields
    listitem.setArt({
        'title' : assets['title'], 'snap' : assets['snap'],
        'boxfront' : assets['boxfront'], '3dbox' : assets['3dbox'],
        'icon' : icon_path, 'fanart' : fanart_path, 'poster' : poster_path
    })

    # --- Create context menu ---
    URL_view_DAT = misc_url_4_arg_RunPlugin('command', 'VIEW_DAT', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    URL_view = misc_url_4_arg_RunPlugin('command', 'VIEW', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    if location == LOCATION_SL_FAVS:
        URL_manage = misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_FAV', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils', URL_view_DAT),
            ('View / Audit', URL_view),
            ('Manage SL Favourites', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
        ]
    elif location == LOCATION_SL_MOST_PLAYED:
        URL_manage = misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_MOST_PLAYED', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage SL Most Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    elif location == LOCATION_SL_RECENT_PLAYED:
        URL_manage = misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_RECENT_PLAYED', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage SL Recently Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_4_arg('command', 'LAUNCH_SL', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = False)

def command_show_sl_fav():
    log_debug('command_show_sl_fav() Starting ...')

    # >> Load Software List ROMs
    SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())

    # >> Open Favourite Machines dictionary
    fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
    if not fav_SL_roms:
        kodi_dialog_OK('No Favourite Software Lists ROMs. Add some ROMs to SL Favourites first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render Favourites
    set_Kodi_all_sorting_methods()
    for SL_fav_key in fav_SL_roms:
        SL_fav_ROM = fav_SL_roms[SL_fav_key]
        assets = SL_fav_ROM['assets']
        # >> Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        render_sl_fav_machine_row(SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_FAVS)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# Context menu "Manage SL Favourite ROMs"
#
def command_context_manage_sl_fav(SL_name, ROM_name):
    VIEW_ROOT_MENU   = 100
    VIEW_INSIDE_MENU = 200

    ACTION_DELETE_MACHINE = 100
    ACTION_DELETE_MISSING = 200
    ACTION_DELETE_ALL     = 300
    ACTION_CHOOSE_DEFAULT = 400

    menus_dic = {
        VIEW_ROOT_MENU : [
            ('Delete missing items from SL Favourites', ACTION_DELETE_MISSING),
            ('Delete all machines from SL Favourites', ACTION_DELETE_ALL),
        ],
        VIEW_INSIDE_MENU : [
            ('Choose default machine for SL item', ACTION_CHOOSE_DEFAULT),
            ('Delete item from SL Favourites', ACTION_DELETE_MACHINE),
            ('Delete missing items from SL Favourites', ACTION_DELETE_MISSING),
            ('Delete all machines from SL Favourites', ACTION_DELETE_ALL),
        ],
    }

    # --- Determine view type ---
    log_debug('command_context_manage_sl_fav() BEGIN ...')
    log_debug('SL_name  "{0}" / ROM_name "{1}"'.format(SL_name, ROM_name))
    if SL_name and ROM_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {0}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage SL Favourite itmes', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {0}'.format(action))

    # --- Execute actions ---
    if action == ACTION_CHOOSE_DEFAULT:
        log_debug('command_context_manage_sl_fav() ACTION_CHOOSE_DEFAULT')

        # --- Load Favs ---
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name

        # --- Get a list of machines that can launch this SL ROM. User chooses. ---
        SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
        SL_machine_list = SL_machines_dic[SL_name]
        SL_machine_names_list = []
        SL_machine_desc_list = []
        SL_machine_names_list.append('')
        SL_machine_desc_list.append('[ Not set ]')
        for SL_machine in SL_machine_list: 
            SL_machine_names_list.append(SL_machine['machine'])
            SL_machine_desc_list.append(SL_machine['description'])
        # Krypton feature: preselect current machine.
        # Careful with the preselect bug.
        pre_idx = SL_machine_names_list.index(fav_SL_roms[SL_fav_key]['launch_machine'])
        if pre_idx < 0: pre_idx = 0
        dialog = xbmcgui.Dialog()
        m_index = dialog.select('Select machine', SL_machine_desc_list, preselect = pre_idx)
        if m_index < 0 or m_index == pre_idx: return
        machine_name = SL_machine_names_list[m_index]
        machine_desc = SL_machine_desc_list[m_index]

        # --- Edit and save ---
        fav_SL_roms[SL_fav_key]['launch_machine'] = machine_name
        fs_write_JSON_file(g_PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        kodi_notify('Deafult machine set to {0} ({1})'.format(machine_name, machine_desc))

    # --- Delete ROM from SL Favourites ---
    elif action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_sl_fav() ACTION_DELETE_MACHINE')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{0}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        desc = most_played_roms_dic[SL_fav_key]['description']
        a = 'Delete SL Item {0} ({1} / {2})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1:
            kodi_notify('SL Favourites unchanged')
            return

        # --- Delete machine and save DB ---
        del fav_SL_roms[SL_fav_key]
        log_info('Deleted machine {0} ({1})'.format(SL_name, ROM_name))
        fs_write_JSON_file(g_PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        kodi_refresh_container()
        kodi_notify('SL Item {0}-{1} deleted from SL Favourites'.format(SL_name, ROM_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_sl_fav() ACTION_DELETE_ALL')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{0}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        ret = kodi_dialog_yesno(
            'You have {0} SL Favourites. Delete them all?'.format(len(fav_SL_roms)))
        if ret < 1:
            kodi_notify('SL Favourites unchanged')
            return

        # --- Delete machine and save DB ---
        fs_write_JSON_file(g_PATHS.FAV_SL_ROMS_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all SL Favourites')

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_sl_fav() ACTION_DELETE_MISSING')
        SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
        num_SL_favs = len(fav_SL_roms)
        num_iteration = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher')
        num_items_deleted = 0
        for fav_SL_key in sorted(fav_SL_roms):
            fav_SL_name = fav_SL_roms[fav_SL_key]['SL_name']
            fav_ROM_name = fav_SL_roms[fav_SL_key]['SL_ROM_name']
            log_debug('Checking SL Favourite "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))

            # --- Update progress dialog (BEGIN) ---
            update_number = (num_iteration * 100) // num_SL_favs
            pDialog.update(update_number, 'Checking SL Favourites (ROM "{0}") ...'.format(fav_ROM_name))
            num_iteration += 1

            # --- Load SL ROMs DB and assets ---
            SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_items.json')
            SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

            # --- Check ---
            if fav_ROM_name not in SL_roms:
                num_items_deleted += 1
                del fav_SL_roms[fav_ROM_name]
                log_info('Deleted machine {0} ({1})'.format(fav_SL_name, fav_ROM_name))
            else:
                log_debug('Machine {0} ({1}) OK'.format(fav_SL_name, fav_ROM_name))
        fs_write_JSON_file(g_PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        pDialog.update(100)
        pDialog.close()
        if num_items_deleted > 0:
            kodi_notify('Deleted {0} items'.format(num_items_deleted))
        else:
            kodi_notify('No items deleted')

    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_SL_most_played():
    SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
    most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
    if not most_played_roms_dic:
        kodi_dialog_OK('No Most Played SL machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method()
    sorted_dic = sorted(most_played_roms_dic, key = lambda x : most_played_roms_dic[x]['launch_count'], reverse = True)
    for SL_fav_key in sorted_dic:
        SL_fav_ROM = most_played_roms_dic[SL_fav_key]
        assets = SL_fav_ROM['assets']
        # >> Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        render_sl_fav_machine_row(SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_MOST_PLAYED)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_SL_most_played(SL_name, ROM_name):
    VIEW_ROOT_MENU   = 100
    VIEW_INSIDE_MENU = 200

    ACTION_DELETE_MACHINE = 100
    ACTION_DELETE_MISSING = 200
    ACTION_DELETE_ALL     = 300
    ACTION_CHOOSE_DEFAULT = 400

    menus_dic = {
        VIEW_ROOT_MENU : [
            ('Delete missing items from SL Most Played', ACTION_DELETE_MISSING),
            ('Delete all machines from SL Most Played', ACTION_DELETE_ALL),
        ],
        VIEW_INSIDE_MENU : [
            ('Choose default machine for SL item', ACTION_CHOOSE_DEFAULT),
            ('Delete item from SL Most Played', ACTION_DELETE_MACHINE),
            ('Delete missing items from SL Most Played', ACTION_DELETE_MISSING),
            ('Delete all machines from SL Most Played', ACTION_DELETE_ALL),
        ],
    }

    # --- Determine view type ---
    log_debug('command_context_manage_SL_most_played() BEGIN ...')
    log_debug('SL_name  "{0}" / ROM_name "{1}"'.format(SL_name, ROM_name))
    if SL_name and ROM_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {0}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage SL Most Played', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {0}'.format(action))

    # --- Execute actions ---
    if action == ACTION_CHOOSE_DEFAULT:
        log_debug('command_context_manage_sl_most_played() ACTION_CHOOSE_DEFAULT')
        kodi_dialog_OK('ACTION_CHOOSE_DEFAULT not implemented yet. Sorry.')

    elif action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_sl_most_played() ACTION_DELETE_MACHINE')

        # --- Load Most Played items dictionary ---
        most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{0}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        desc = most_played_roms_dic[SL_fav_key]['description']
        a = 'Delete SL Item {0} ({1} / {2})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1:
            kodi_notify('SL Most Played unchanged')
            return

        # --- Delete machine and save DB ---
        del most_played_roms_dic[SL_fav_key]
        a = 'Deleted SL_name "{0}" / ROM_name "{1}"'
        log_info(a.format(SL_name, ROM_name))
        fs_write_JSON_file(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
        kodi_refresh_container()
        kodi_notify('Item {0}-{1} deleted from SL Most Played'.format(SL_name, ROM_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_sl_most_played() ACTION_DELETE_ALL')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{0}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        ret = kodi_dialog_yesno(
            'You have {0} SL Most Played. Delete them all?'.format(len(fav_SL_roms)))
        if ret < 1:
            kodi_notify('SL Most Played unchanged')
            return

        # --- Delete machine and save DB ---
        fs_write_JSON_file(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all SL Most Played')

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_sl_most_played() ACTION_DELETE_MISSING')
        SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
        num_SL_favs = len(fav_SL_roms)
        num_iteration = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher')
        num_items_deleted = 0
        for fav_SL_key in sorted(fav_SL_roms):
            fav_SL_name = fav_SL_roms[fav_SL_key]['SL_name']
            fav_ROM_name = fav_SL_roms[fav_SL_key]['SL_ROM_name']
            log_debug('Checking SL Most Played "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))

            # --- Update progress dialog (BEGIN) ---
            update_number = (num_iteration * 100) // num_SL_favs
            pDialog.update(update_number, 'Checking SL Most Played (ROM "{0}") ...'.format(fav_ROM_name))
            num_iteration += 1

            # --- Load SL ROMs DB and assets ---
            SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_items.json')
            SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

            # --- Check ---
            if fav_ROM_name not in SL_roms:
                num_items_deleted += 1
                del fav_SL_roms[fav_ROM_name]
                log_info('Deleted machine {0} ({1})'.format(fav_SL_name, fav_ROM_name))
            else:
                log_debug('Machine {0} ({1}) OK'.format(fav_SL_name, fav_ROM_name))
        fs_write_JSON_file(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), fav_SL_roms)
        pDialog.update(100)
        pDialog.close()
        if num_items_deleted > 0:
            kodi_notify('Deleted {0} items'.format(num_items_deleted))
        else:
            kodi_notify('No items deleted')

    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_SL_recently_played():
    SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
    recent_roms_list = fs_load_JSON_file_list(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
    if not recent_roms_list:
        kodi_dialog_OK('No Recently Played SL machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method()
    for SL_fav_ROM in recent_roms_list:
        SL_fav_key = SL_fav_ROM['SL_DB_key']
        assets = SL_fav_ROM['assets']
        # >> Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        render_sl_fav_machine_row(SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_RECENT_PLAYED)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_SL_recent_played(SL_name, ROM_name):
    VIEW_ROOT_MENU   = 100
    VIEW_INSIDE_MENU = 200

    ACTION_DELETE_MACHINE = 100
    ACTION_DELETE_MISSING = 200
    ACTION_DELETE_ALL     = 300
    ACTION_CHOOSE_DEFAULT = 400

    menus_dic = {
        VIEW_ROOT_MENU : [
            ('Delete missing items from SL Recently Played', ACTION_DELETE_MISSING),
            ('Delete all machines from SL Recently Played', ACTION_DELETE_ALL),
        ],
        VIEW_INSIDE_MENU : [
            ('Choose default machine for SL item', ACTION_CHOOSE_DEFAULT),
            ('Delete item from SL Recently Played', ACTION_DELETE_MACHINE),
            ('Delete missing items from SL Recently Played', ACTION_DELETE_MISSING),
            ('Delete all machines from SL Recently Played', ACTION_DELETE_ALL),
        ],
    }

    # --- Determine view type ---
    log_debug('command_context_manage_SL_recent_played() BEGIN ...')
    log_debug('SL_name  "{0}" / ROM_name "{1}"'.format(SL_name, ROM_name))
    if SL_name and ROM_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {0}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage SL Recently Played', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {0}'.format(action))

    # --- Execute actions ---
    if action == ACTION_CHOOSE_DEFAULT:
        log_debug('command_context_manage_SL_recent_played() ACTION_CHOOSE_DEFAULT')
        kodi_dialog_OK('ACTION_CHOOSE_DEFAULT not implemented yet. Sorry.')

    elif action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_SL_recent_played() Delete SL Recently Played machine')

        # --- Load Recently Played machine list ---
        recent_roms_list = fs_load_JSON_file_list(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
        machine_index = fs_locate_idx_by_SL_item_name(recent_roms_list, SL_name, ROM_name)
        if machine_index < 0:
            a = 'Item {0}-{1} cannot be located in SL Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(SL_name, ROM_name))
            return

        # --- Ask user for confirmation ---
        desc = recent_roms_list[machine_index]['description']
        a = 'Delete SL Item {0} ({1} / {2})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1:
            kodi_notify('SL Recently Played unchanged')
            return

        # --- Delete machine and save DB ---
        recent_roms_list.pop(machine_index)
        a = 'Deleted SL_name "{0}" / ROM_name "{1}"'
        log_info(a.format(SL_name, ROM_name))
        fs_write_JSON_file(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        kodi_refresh_container()
        kodi_notify('SL Item {0}-{1} deleted from SL Recently Played'.format(SL_name, ROM_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_SL_recent_played() ACTION_DELETE_ALL')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{0}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        ret = kodi_dialog_yesno(
            'You have {0} SL Recently Played. Delete them all?'.format(len(fav_SL_roms)))
        if ret < 1:
            kodi_notify('SL Recently Played unchanged')
            return

        # --- Delete machine and save DB ---
        fs_write_JSON_file(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), list())
        kodi_refresh_container()
        kodi_notify('Deleted all SL Recently Played')

    elif action == ACTION_DELETE_MISSING:
        # Careful because here fav_SL_roms is a list and not a dictionary.
        log_debug('command_context_manage_SL_recent_played() ACTION_DELETE_MISSING')
        SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
        num_SL_favs = len(fav_SL_roms)
        num_iteration = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher')
        num_items_deleted = 0
        new_fav_SL_roms = []
        # fav_SL_roms is a list, do not sort it!
        for fav_SL_item in fav_SL_roms:
            fav_SL_name = fav_SL_item['SL_name']
            fav_ROM_name = fav_SL_item['SL_ROM_name']
            log_debug('Checking SL Recently Played "{0}" / "{1}"'.format(fav_SL_name, fav_ROM_name))

            # --- Update progress dialog (BEGIN) ---
            update_number = (num_iteration * 100) // num_SL_favs
            pDialog.update(update_number, 'Checking SL Recently Played (ROM "{0}") ...'.format(fav_ROM_name))
            num_iteration += 1

            # --- Load SL ROMs DB and assets ---
            SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_items.json')
            SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

            # --- Check ---
            if fav_ROM_name not in SL_roms:
                num_items_deleted += 1
                log_info('Deleted machine {0} ({1})'.format(fav_SL_name, fav_ROM_name))
            else:
                new_fav_SL_roms.append(fav_SL_item)
                log_debug('Machine {0} ({1}) OK'.format(fav_SL_name, fav_ROM_name))
        fs_write_JSON_file(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), new_fav_SL_roms)
        pDialog.update(100)
        pDialog.close()
        if num_items_deleted > 0:
            kodi_notify('Deleted {0} items'.format(num_items_deleted))
        else:
            kodi_notify('No items deleted')
    else:
        t = 'Wrong action == {0}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

# ---------------------------------------------------------------------------------------------
# Custom MAME filters
# Custom filters behave like standard catalogs.
# Custom filters are defined in a XML file, the XML file is processed and the custom catalogs
# created from the main database.
# Custom filters do not have parent and all machines lists. They are always rendered in flat mode.
# ---------------------------------------------------------------------------------------------
def command_context_setup_custom_filters():
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Setup AML custom filters',
        ['Build custom filter databases',
         'Test custom filter XML',
         'View custom filter XML',
         'View filter histogram report',
         'View filter XML syntax report',
         'View filter database report',
         ])
    if menu_item < 0: return

    # --- Build custom filter databases ---
    if menu_item == 0:
        # --- Open main ROM databases ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        db_files = [
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['assets', 'MAME machine assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
            ['machine_archives', 'Machine archives list', g_PATHS.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)
        # Compatibility with "All in one" code.
        audit_dic = { 'machine_archives' : db_dic['machine_archives'] }

        # --- Make a dictionary of machines to be filtered ---
        # This currently includes all MAME parent machines.
        # However, it must include all machines (parent and clones).
        (main_filter_dic, sets_dic) = filter_get_filter_DB(g_PATHS,
            db_dic['machines'], db_dic['render'], db_dic['assets'], audit_dic['machine_archives'])

        # --- Parse custom filter XML and check for errors ---
        # 1) Check the filter XML syntax and filter semantic errors.
        # 2) Produces report PATHS.REPORT_CF_XML_SYNTAX_PATH
        (filter_list, options_dic) = filter_custom_filters_load_XML(
            g_PATHS, g_settings, control_dic, main_filter_dic, sets_dic)
        # If no filters sayonara
        if len(filter_list) < 1:
            kodi_notify_warn('Filter XML has no filter definitions')
            return
        # If errors found in the XML sayonara
        if options_dic['XML_errors']:
            kodi_dialog_OK('Custom filter database build cancelled because the XML filter '
                'definition file contains errors. Have a look at the XML filter file report, '
                'correct the mistakes and try again.')
            return

        # --- Build filter database ---
        # 1) Saves control_dic (updated custom filter build timestamp).
        # 2) Generates PATHS.REPORT_CF_DB_BUILD_PATH
        filter_build_custom_filters(g_PATHS, g_settings, control_dic,
            filter_list, main_filter_dic, db_dic['machines'], db_dic['render'], db_dic['assets'])

        # --- So long and thanks for all the fish ---
        kodi_notify('Custom filter database built')

    # --- Test custom filter XML ---
    elif menu_item == 1:
        # --- Open main ROM databases ---
        db_files = [
            ['control_dic', 'Control dictionary', g_PATHS.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['assets', 'MAME machine assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
            ['machine_archives', 'Machine archives list', g_PATHS.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # --- Make a dictionary of machines to be filtered ---
        # This currently includes all MAME parent machines.
        # However, it must include all machines (parent and clones).
        (main_filter_dic, sets_dic) = filter_get_filter_DB(
            g_PATHS, db_dic['machines'], db_dic['render'], db_dic['assets'],
            db_dic['machine_archives'])

        # --- Parse custom filter XML and check for errors ---
        # This function also check the filter XML syntax and produces a report.
        (filter_list, options_dic) = filter_custom_filters_load_XML(
            g_PATHS, g_settings, db_dic['control_dic'], main_filter_dic, sets_dic)
        # If no filters sayonara
        if len(filter_list) < 1:
            kodi_notify_warn('Filter XML has no filter definitions')
            return
        # If errors found in the XML sayonara
        elif options_dic['XML_errors']:
            kodi_dialog_OK(
                'The XML filter definition file contains errors. Have a look at the '
                'XML filter file report, fix the mistakes and try again.')
            return
        kodi_notify('Custom filter XML check succesful')

    # --- View custom filter XML ---
    elif menu_item == 2:
        cf_XML_path_str = g_settings['filter_XML']
        log_debug('cf_XML_path_str = "{0}"'.format(cf_XML_path_str))
        if not cf_XML_path_str:
            log_debug('Using default XML custom filter.')
            XML_FN = g_PATHS.CUSTOM_FILTER_PATH
        else:
            log_debug('Using user-defined in addon settings XML custom filter.')
            XML_FN = FileName(cf_XML_path_str)
        log_debug('command_context_setup_custom_filters() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
        if not XML_FN.exists():
            kodi_dialog_OK('Custom filter XML file not found.')
            return
        with open(XML_FN.getPath(), 'r') as myfile:
            display_text_window('Custom filter XML', myfile.read().decode('utf-8'))

    # --- View filter histogram report ---
    elif menu_item == 3:
        XML_FN = g_PATHS.REPORT_CF_HISTOGRAMS_PATH
        log_debug('command_context_setup_custom_filters() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
        if not XML_FN.exists():
            kodi_dialog_OK('Filter histogram report not found.')
            return
        with open(XML_FN.getPath(), 'r') as myfile:
            display_text_window('Filter histogram report', myfile.read().decode('utf-8'))

    # --- View filter XML syntax report ---
    elif menu_item == 4:
        XML_FN = g_PATHS.REPORT_CF_XML_SYNTAX_PATH
        log_debug('command_context_setup_custom_filters() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
        if not XML_FN.exists():
            kodi_dialog_OK('Filter XML filter syntax report not found.')
            return
        with open(XML_FN.getPath(), 'r') as myfile:
            display_text_window('Custom filter XML syntax report', myfile.read().decode('utf-8'))

    # --- View filter report ---
    elif menu_item == 5:
        XML_FN = g_PATHS.REPORT_CF_DB_BUILD_PATH
        log_debug('command_context_setup_custom_filters() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
        if not XML_FN.exists():
            kodi_dialog_OK('Custom filter database report not found.')
            return
        with open(XML_FN.getPath(), 'r') as myfile:
            display_text_window('Custom filter XML syntax report', myfile.read().decode('utf-8'))

def command_show_custom_filters():
    log_debug('command_show_custom_filters() Starting ...')

    # >> Open Custom filter count database and index
    filter_index_dic = fs_load_JSON_file_dic(g_PATHS.FILTERS_INDEX_PATH.getPath())
    if not filter_index_dic:
        kodi_dialog_OK('MAME custom filter index is empty. Please rebuild your filters.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Check if filters need to be rebuilt
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if control_dic['t_Custom_Filter_build'] < control_dic['t_MAME_Catalog_build']:
        kodi_dialog_OK('MAME custom filters need to be rebuilt.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Render Custom Filters, always in flat mode ---
    mame_view_mode = g_settings['mame_view_mode']
    set_Kodi_all_sorting_methods()
    for f_name in sorted(filter_index_dic, key = lambda x: filter_index_dic[x]['order'], reverse = False):
        num_machines = filter_index_dic[f_name]['num_machines']
        if num_machines == 1: machine_str = 'machine'
        else:                 machine_str = 'machines'
        render_custom_filter_item_row(f_name, num_machines, machine_str, filter_index_dic[f_name]['plot'])
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)

def render_custom_filter_item_row(f_name, num_machines, machine_str, plot):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    title_str = '{0} [COLOR orange]({1} {2})[/COLOR]'.format(f_name, num_machines, machine_str)
    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str, 'plot' : plot, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = g_PATHS.ICON_FILE_PATH.getPath()
    fanart_path = g_PATHS.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    # >> Make a list of tuples
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = misc_url_2_arg('catalog', 'Custom', 'category', f_name)
    xbmcplugin.addDirectoryItem(g_addon_handle, URL, listitem, isFolder = True)

#
# Renders a custom filter list of machines, always in flat mode.
#
def render_custom_filter_machines(filter_name):
    log_debug('render_custom_filter_machines() filter_name  = {0}'.format(filter_name))

    # >> Global properties
    view_mode_property = g_settings['mame_view_mode']
    log_debug('render_custom_filter_machines() view_mode_property = {0}'.format(view_mode_property))

    # >> Check id main DB exists
    if not g_PATHS.RENDER_DB_PATH.exists():
        kodi_dialog_OK('MAME database not found. Check out "Setup plugin" context menu.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Load main MAME info DB and catalog
    l_cataloged_dic_start = time.time()
    Filters_index_dic = fs_load_JSON_file_dic(g_PATHS.FILTERS_INDEX_PATH.getPath())
    rom_DB_noext = Filters_index_dic[filter_name]['rom_DB_noext']
    l_cataloged_dic_end = time.time()
    l_render_db_start = time.time()
    render_db_dic = fs_load_JSON_file_dic(g_PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_render.json').getPath())
    l_render_db_end = time.time()
    l_assets_db_start = time.time()
    assets_db_dic = fs_load_JSON_file_dic(g_PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_assets.json').getPath())
    l_assets_db_end = time.time()
    l_favs_start = time.time()
    fav_machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
    l_favs_end = time.time()

    # >> Compute loading times.
    catalog_t = l_cataloged_dic_end - l_cataloged_dic_start
    render_t = l_render_db_end - l_render_db_start
    assets_t = l_assets_db_end - l_assets_db_start
    favs_t   = l_favs_end - l_favs_start
    loading_time = catalog_t + render_t + assets_t + favs_t

    # >> Check if catalog is empty
    if not render_db_dic:
        kodi_dialog_OK('Catalog is empty. Check out "Setup plugin" context menu.')
        xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Process ROMs ---
    processing_ticks_start = time.time()
    catalog_name = 'Custom'
    category_name = filter_name
    c_dic = {}
    for m_name in render_db_dic:
        c_dic[m_name] = render_db_dic[m_name]['description']
    catalog_dic = {category_name : c_dic}
    # Render a flat list and ignore filters.
    r_list = render_process_machines(catalog_dic, catalog_name, category_name,
        render_db_dic, assets_db_dic, fav_machines)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    set_Kodi_all_sorting_methods()
    render_commit_machines(r_list)
    xbmcplugin.endOfDirectory(g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()
    rendering_time = rendering_ticks_end - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    # log_debug('Loading catalog   {0:.4f} s'.format(catalog_t))
    # log_debug('Loading render db {0:.4f} s'.format(render_t))
    # log_debug('Loading assets db {0:.4f} s'.format(assets_t))
    # log_debug('Loading MAME favs {0:.4f} s'.format(favs_t))    
    log_debug('Loading time      {0:.4f} s'.format(loading_time))
    log_debug('Processing time   {0:.4f} s'.format(processing_time))
    log_debug('Rendering time    {0:.4f} s'.format(rendering_ticks_end - rendering_ticks_start))

# -------------------------------------------------------------------------------------------------
# Check AML status
# -------------------------------------------------------------------------------------------------
#
# Recursive function. Conditions are a fall-trough. For example, if user checks
# MAME_MAIN_DB_BUILT but XML has not been extracted/processed then MAME_MAIN_DB_BUILT fails.
#
# Return options dictionary:
# options_dic['condition']  True if condition is met, False otherwise.
# options_dic['msg']        if condition is not met a message to print to the user.
#
def check_MAME_DB_status(condition, control_dic):
    if condition == MAME_XML_EXTRACTED:
        test_XML_EXTRACTED = True if control_dic['t_XML_extraction'] > 0 else False
        if not test_XML_EXTRACTED:
            t = 'MAME.XML has not been extracted. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_MAME_DB_status() MAME_XML_EXTRACTED fails.')
        else:
            options_dic = {'msg' : '', 'condition' : True }
            log_debug('check_MAME_DB_status() Everything OK')
        return options_dic

    elif condition == MAME_MAIN_DB_BUILT:
        test_MAIN_DB_BUILT = True if control_dic['t_MAME_DB_build'] > control_dic['t_XML_extraction'] else False
        if not test_MAIN_DB_BUILT:
            t = 'MAME Main database needs to be built. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_MAME_DB_status() MAME_MAIN_DB_BUILT fails.')
            return options_dic
        else:
            return check_MAME_DB_status(MAME_XML_EXTRACTED, control_dic)

    elif condition == MAME_AUDIT_DB_BUILT:
        test_AUDIT_DB_BUILT = True if control_dic['t_MAME_Audit_DB_build'] > control_dic['t_MAME_DB_build'] else False
        if not test_AUDIT_DB_BUILT:
            t = 'MAME Audit database needs to be built. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_MAME_DB_status() MAME_AUDIT_DB_BUILT fails.')
            return options_dic
        else:
            return check_MAME_DB_status(MAME_MAIN_DB_BUILT, control_dic)

    elif condition == MAME_CATALOG_BUILT:
        test_CATALOG_BUILT = True if control_dic['t_MAME_Catalog_build'] > control_dic['t_MAME_Audit_DB_build'] else False
        if not test_CATALOG_BUILT:
            t = 'MAME Catalog database needs to be built. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_MAME_DB_status() MAME_CATALOG_BUILT fails.')
            return options_dic
        else:
            return check_MAME_DB_status(MAME_AUDIT_DB_BUILT, control_dic)

    elif condition == MAME_MACHINES_SCANNED:
        test_MACHINES_SCANNED = True if control_dic['t_MAME_ROMs_scan'] > control_dic['t_MAME_Catalog_build'] else False
        if not test_MACHINES_SCANNED:
            t = 'MAME machines need to be scanned. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_MAME_DB_status() MAME_MACHINES_SCANNED fails.')
            return options_dic
        else:
            return check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)

    elif condition == MAME_ASSETS_SCANNED:
        test_ASSETS_SCANNED = True if control_dic['t_MAME_assets_scan'] > control_dic['t_MAME_ROMs_scan'] else False
        if not test_ASSETS_SCANNED:
            t = 'MAME assets need to be scanned. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_MAME_DB_status() MAME_ASSETS_SCANNED fails.')
            return options_dic
        else:
            return check_MAME_DB_status(MAME_MACHINES_SCANNED, control_dic)

    else:
        raise ValueError('check_MAME_DB_status() Recursive logic error')

#
# Look at check_MAME_DB_status()
#
def check_SL_DB_status(condition, control_dic):
    # Conditions are a fall-trough. For example, if user checks MAME_MAIN_DB_BUILT but
    # XML has not been extracted/processed then MAME_MAIN_DB_BUILT fails.
    if condition == SL_MAIN_DB_BUILT:
        test_MAIN_DB_BUILT = True if control_dic['t_SL_DB_build'] > control_dic['t_MAME_DB_build'] else False
        if not test_MAIN_DB_BUILT:
            t = 'Software List databases not built or outdated. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_SL_DB_status() SL_MAIN_DB_BUILT fails')
        else:
            options_dic = {'msg' : '', 'condition' : True }
            log_debug('check_SL_DB_status() Everything OK')
        return options_dic

    elif condition == SL_ITEMS_SCANNED:
        test_ITEMS_SCANNED = True if control_dic['t_SL_ROMs_scan'] > control_dic['t_SL_DB_build'] else False
        if not test_ITEMS_SCANNED:
            t = 'Software List items not scanned. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_SL_DB_status() SL_ITEMS_SCANNED fails')
            return options_dic
        else:
            return check_SL_DB_status(SL_MAIN_DB_BUILT, control_dic)

    elif condition == SL_ASSETS_SCANNED:
        test_ASSETS_SCANNED = True if control_dic['t_SL_assets_scan'] > control_dic['t_SL_ROMs_scan'] else False
        if not test_ASSETS_SCANNED:
            t = 'Software List assets not scanned. Use the context menu "Setup plugin" in root window.'
            options_dic = {'msg' : t, 'condition' : False }
            log_debug('check_SL_DB_status() SL_ASSETS_SCANNED fails')
            return options_dic
        else:
            return check_SL_DB_status(SL_ITEMS_SCANNED, control_dic)

    else:
        raise ValueError('check_SL_DB_status() Recursive logic error')

#
# This function is called before rendering a Catalog.
#
def check_MAME_DB_before_rendering_catalog(g_PATHS, settings, control_dic):
    # Check if MAME catalogs are built.
    options = check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)
    if not options['condition']:
        kodi_dialog_OK(options['msg'])
        return False

    # All good!
    log_debug('check_MAME_DB_before_rendering_catalog() All good!')
    return True

#
# This function checks if the database is OK and machines inside a Category can be rendered.
# This function is called before rendering machines.
# This function does not affect MAME Favourites, Recently Played, etc. Those can always be rendered.
# This function relies in the timestamps in control_dic.
#
# Returns True if everything is OK and machines inside a Category can be rendered.
# Returns False and prints warning message if machines inside a category cannot be rendered.
#
def check_MAME_DB_before_rendering_machines(g_PATHS, settings, control_dic):
    # Check if MAME catalogs are built.
    options = check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)
    if not options['condition']:
        kodi_dialog_OK(options['msg'])
        return False

    # If MAME render cache is enabled then check that it is up-to-date.
    if g_settings['debug_enable_MAME_render_cache']:
        if control_dic['t_MAME_render_cache_build'] < control_dic['t_MAME_Catalog_build']:
            log_warning('t_MAME_render_cache_build < t_MAME_Catalog_build')
            t = ('MAME render cache needs to be updated. '
                 'Open the context menu "Setup plugin", then '
                 '"Step by Step", and then "Rebuild MAME machine and asset caches."')
            kodi_dialog_OK(t)
            return False

    if g_settings['debug_enable_MAME_asset_cache']:
        if control_dic['t_MAME_asset_cache_build'] < control_dic['t_MAME_Catalog_build']:
            log_warning('t_MAME_asset_cache_build < t_MAME_Catalog_build')
            t = ('MAME asset cache needs to be updated. '
                 'Open the context menu "Setup plugin", then '
                 '"Step by Step", and then "Rebuild MAME machine and asset caches."')
            kodi_dialog_OK(t)
            return False

    log_debug('check_MAME_DB_before_rendering_machines() All good.')
    return True

#
# Same function for Software Lists. Called before rendering SL Items inside a Software List.
# WARNING This must be completed!!! Look at the MAME functions.
#
def check_SL_DB_before_rendering_catalog(g_PATHS, g_settings, control_dic):
    # Check if SL databases are built.
    options = check_SL_DB_status(SL_MAIN_DB_BUILT, control_dic)
    if not options['condition']:
        kodi_dialog_OK(options['msg'])
        return False

    log_debug('check_SL_DB_before_rendering_catalog() All good.')
    return True

def check_SL_DB_before_rendering_machines(g_PATHS, g_settings, control_dic):
    # Check if SL databases are built.
    options = check_SL_DB_status(SL_MAIN_DB_BUILT, control_dic)
    if not options['condition']:
        kodi_dialog_OK(options['msg'])
        return False

    log_debug('check_SL_DB_before_rendering_machines() All good.')
    return True

# -------------------------------------------------------------------------------------------------
# Setup plugin databases
# -------------------------------------------------------------------------------------------------
def command_context_setup_plugin():
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Setup plugin', [
        'All in one (Extract, Build, Scan, Filters)',
        'All in one (Extract, Build, Scan, Filters, Audit)',
        'Extract/Process MAME.xml',
        'Build all databases',
        'Scan everything and build plots',
        'Build Fanarts/3D Boxes ...',
        'Audit MAME machine ROMs/CHDs',
        'Audit SL ROMs/CHDs',
        'Step by step ...',
    ])
    if menu_item < 0: return

    # --- All in one (Extract, Build, Scan, Filters) ---
    # --- All in one (Extract, Build, Scan, Filters, Audit) ---
    if menu_item == 0 or menu_item == 1:
        DO_AUDIT = True if menu_item == 1 else False
        log_info('command_context_setup_plugin() All in one step starting ...')
        log_info('Operation mode {0}'.format(g_settings['op_mode']))
        log_info('DO_AUDIT {0}'.format(DO_AUDIT))

        # Errors are checked inside the fs_extract*() or fs_process*() functions.
        options_dic = {}
        if g_settings['op_mode'] == OP_MODE_EXTERNAL:
            # Extract MAME.xml from MAME exectuable.
            # Reset control_dic and count the number of MAME machines.
            fs_extract_MAME_XML(g_PATHS, g_settings, __addon_version__, options_dic)
        elif g_settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
            # For MAME 2003 Plus the XML is already there.
            # Reset control_dic and count the number of machines.
            fs_process_RETRO_MAME2003PLUS(g_PATHS, g_settings, __addon_version__, options_dic)
        else:
            log_error('command_context_setup_plugin() Unknown op_mode "{0}"'.format(g_settings['op_mode']))
            kodi_notify_warn('Database not built')
            return
        if options_dic['abort']:
            kodi_dialog_OK(options_dic['msg'])
            return

        # --- Build main MAME database, PClone list and MAME hashed database (mandatory) ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options_dic = mame_check_before_build_MAME_main_database(g_PATHS, g_settings, control_dic)
        if options_dic['abort']: return
        db_dic = mame_build_MAME_main_database(g_PATHS, g_settings, control_dic, __addon_version__)

        # --- Build ROM audit/scanner databases (mandatory) ---
        options_dic = mame_check_before_build_ROM_audit_databases(g_PATHS, g_settings, control_dic)
        if options_dic['abort']: return
        audit_dic = mame_build_ROM_audit_databases(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['devices'], db_dic['roms'])

        # --- Build MAME catalogs (mandatory) ---
        options_dic = mame_check_before_build_MAME_catalogs(g_PATHS, g_settings, control_dic)
        if options_dic['abort']: return
        db_dic['cache_index'] = mame_build_MAME_catalogs(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['roms'],
            db_dic['main_pclone_dic'], db_dic['assets'])

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs (optional) ---
        if g_settings['enable_SL']:
            options_dic = mame_check_before_build_SL_databases(g_PATHS, g_settings, control_dic)
            if not options_dic['abort']:
                SL_dic = mame_build_SoftwareLists_databases(g_PATHS, g_settings, control_dic,
                    db_dic['machines'], db_dic['render'])
            else:
                log_info('Skipping mame_build_SoftwareLists_databases()')
        else:
            log_info('SL disabled. Skipping mame_build_SoftwareLists_databases()')

        # --- Scan ROMs/CHDs/Samples and updates ROM status (optional) ---
        options_dic = mame_check_before_scan_MAME_ROMs(g_PATHS, g_settings, control_dic)
        if not options_dic['abort']:
            mame_scan_MAME_ROMs(g_PATHS, g_settings, control_dic, options_dic,
                db_dic['machines'], db_dic['render'], db_dic['assets'], audit_dic['machine_archives'],
                audit_dic['ROM_ZIP_list'], audit_dic['Sample_ZIP_list'], audit_dic['CHD_archive_list'])
        else:
            log_info('Skipping mame_scan_MAME_ROMs()')

        # --- Scans MAME assets/artwork (optional) ---
        options_dic = mame_check_before_scan_MAME_assets(g_PATHS, g_settings, control_dic)
        if not options_dic['abort']:
            mame_scan_MAME_assets(g_PATHS, g_settings, control_dic,
                db_dic['assets'], db_dic['render'], db_dic['main_pclone_dic'])
        else:
            log_info('Skipping mame_scan_MAME_assets()')

        # --- Scan SL ROMs/CHDs (optional) ---
        if g_settings['enable_SL']:
            options_dic = mame_check_before_scan_SL_ROMs(g_PATHS, g_settings, control_dic)
            if not options_dic['abort']:
                mame_scan_SL_ROMs(g_PATHS, g_settings, control_dic, options_dic, SL_dic['SL_index'])
            else:
                log_info('Skipping mame_scan_SL_ROMs()')
        else:
            log_info('SL disabled. Skipping mame_scan_SL_ROMs()')

        # --- Scan SL assets/artwork (optional) ---
        if g_settings['enable_SL']:
            options_dic = mame_check_before_scan_SL_assets(g_PATHS, g_settings, control_dic)
            if not options_dic['abort']:
                mame_scan_SL_assets(g_PATHS, g_settings, control_dic,
                    SL_dic['SL_index'], SL_dic['SL_PClone_dic'])
            else:
                log_info('Skipping mame_scan_SL_assets()')
        else:
            log_info('SL disabled. Skipping mame_scan_SL_assets()')

        # --- Build MAME machines plot ---
        mame_build_MAME_plots(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['assets'],
            db_dic['history_idx_dic'], db_dic['mameinfo_idx_dic'],
            db_dic['gameinit_idx_list'], db_dic['command_idx_list'])

        # --- Buils Software List items plot ---
        if g_settings['enable_SL']:
            mame_build_SL_plots(g_PATHS, g_settings, control_dic,
                SL_dic['SL_index'], SL_dic['SL_machines'], db_dic['history_idx_dic'])
        else:
            log_info('SL disabled. Skipping mame_build_SL_plots()')

        # --- Regenerate the custom filters ---
        (main_filter_dic, sets_dic) = filter_get_filter_DB(g_PATHS,
            db_dic['machines'], db_dic['render'], db_dic['assets'], audit_dic['machine_archives'])
        (filter_list, options_dic) = filter_custom_filters_load_XML(
            g_PATHS, g_settings, control_dic, main_filter_dic, sets_dic)
        if len(filter_list) >= 1 and not options_dic['XML_errors']:
            filter_build_custom_filters(g_PATHS, g_settings, control_dic,
                filter_list, main_filter_dic, db_dic['machines'], db_dic['render'], db_dic['assets'])
        else:
            log_info('Custom XML filters not built.')

        # --- Regenerate MAME asset hashed database ---
        fs_build_asset_hashed_db(g_PATHS, g_settings, control_dic, db_dic['assets'])

        # --- Regenerate MAME machine render and assets cache ---
        if g_settings['debug_enable_MAME_render_cache']:
            fs_build_render_cache(g_PATHS, g_settings, control_dic,
                db_dic['cache_index'], db_dic['render'])
        if g_settings['debug_enable_MAME_asset_cache']:
            fs_build_asset_cache(g_PATHS, g_settings, control_dic,
                db_dic['cache_index'], db_dic['assets'])

        if DO_AUDIT:
            # --- MAME audit ---
            mame_audit_MAME_all(g_PATHS, g_settings, control_dic,
                db_dic['machines'], db_dic['render'], audit_dic['audit_roms'])

            # --- SL audit ---
            if g_settings['enable_SL']:
                mame_audit_SL_all(g_PATHS, g_settings, control_dic, SL_dic['SL_index'])
            else:
                log_info('SL disabled. Skipping mame_audit_SL_all()')

        # --- So long and thanks for all the fish ---
        if DO_AUDIT:
            kodi_notify('Finished extracting, DB build, scanning, filters and audit')
        else:
            kodi_notify('Finished extracting, DB build, scanning and filters')

    # --- Extract MAME.xml ---
    elif menu_item == 2:
        log_info('command_context_setup_plugin() Extract/Process MAME.xml starting ...')
        options_dic = {}
        if g_settings['op_mode'] == OP_MODE_EXTERNAL:
            # Extract MAME.xml from MAME exectuable.
            # Reset control_dic and count the number of MAME machines.
            fs_extract_MAME_XML(g_PATHS, g_settings, __addon_version__, options_dic)
        elif g_settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
            # For MAME 2003 Plus the XML is already there.
            # Reset control_dic and count the number of machines.
            fs_process_RETRO_MAME2003PLUS(g_PATHS, g_settings, __addon_version__, options_dic)
        else:
            log_error('command_context_setup_plugin() Unknown op_mode "{0}"'.format(g_settings['op_mode']))
            kodi_notify_warn('Database not built')
            return
        if options_dic['abort']:
            kodi_dialog_OK(options_dic['msg'])
            return

        # Inform user everything went well.
        size_MB = options_dic['filesize'] / 1000000
        num_m = options_dic['total_machines']
        kodi_dialog_OK(
            'Extracted MAME XML database. '
            'Size is {0} MB and there are {1} machines.'.format(size_MB, num_m))

    # --- Build everything ---
    elif menu_item == 3:
        log_info('command_context_setup_plugin() Build everything starting ...')

        # --- Build main MAME database, PClone list and hashed database (mandatory) ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options_dic = mame_check_before_build_MAME_main_database(g_PATHS, g_settings, control_dic)
        if options_dic['abort']: return
        db_dic = mame_build_MAME_main_database(g_PATHS, g_settings, control_dic, __addon_version__)

        # --- Build ROM audit/scanner databases (mandatory) ---
        options_dic = mame_check_before_build_ROM_audit_databases(g_PATHS, g_settings, control_dic)
        if options_dic['abort']: return
        audit_dic = mame_build_ROM_audit_databases(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['devices'], db_dic['roms'])

        # --- Release some memory before building the catalog ---
        del db_dic['devices']
        del db_dic['history_idx_dic']
        del db_dic['mameinfo_idx_dic']
        del db_dic['gameinit_idx_list']
        del db_dic['command_idx_list']
        del audit_dic['audit_roms']
        del audit_dic['machine_archives']
        del audit_dic['ROM_ZIP_list']
        del audit_dic['Sample_ZIP_list']
        del audit_dic['CHD_archive_list']

        # --- Build MAME catalogs (mandatory) ---
        options_dic = mame_check_before_build_MAME_catalogs(g_PATHS, g_settings, control_dic)
        if options_dic['abort']: return
        db_dic['cache_index'] = mame_build_MAME_catalogs(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['roms'],
            db_dic['main_pclone_dic'], db_dic['assets'])

        # --- Regenerate the render and assets cache ---
        if g_settings['debug_enable_MAME_render_cache']:
            fs_build_render_cache(g_PATHS, g_settings, control_dic, 
                db_dic['cache_index'], db_dic['render'])
        if g_settings['debug_enable_MAME_asset_cache']:
            fs_build_asset_cache(g_PATHS, g_settings, control_dic,
                db_dic['cache_index'], db_dic['assets'])

        # --- Release some memory before building the SL databases ---
        del db_dic['roms']
        del db_dic['main_pclone_dic']
        del db_dic['assets']
        del db_dic['cache_index']

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs (optional) ---
        if g_settings['enable_SL']:
            options_dic = mame_check_before_build_SL_databases(g_PATHS, g_settings, control_dic)
            if not options_dic['abort']:
                SL_dic = mame_build_SoftwareLists_databases(g_PATHS, g_settings, control_dic,
                    db_dic['machines'], db_dic['render'])
            else:
                log_info('Skipping mame_build_SoftwareLists_databases()')
        else:
            log_info('SL disabled. Skipping mame_build_SoftwareLists_databases()')

        # --- So long and thanks for all the fish ---
        kodi_notify('All databases built')

    # --- Scan everything ---
    elif menu_item == 4:
        log_info('command_setup_plugin() Scanning everything starting ...')

        # --- MAME -------------------------------------------------------------------------------
        db_files = [
            ['control_dic', 'Control dictionary', g_PATHS.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['main_pclone_dic', 'MAME PClone dictionary', g_PATHS.MAIN_PCLONE_DIC_PATH.getPath()],
            ['assets', 'MAME machine assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
            ['machine_archives', 'Machine file list', g_PATHS.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
            ['ROM_ZIP_list', 'ROM List index', g_PATHS.ROM_SET_ROM_LIST_DB_PATH.getPath()],
            ['Sample_ZIP_list', 'ROM List index', g_PATHS.ROM_SET_SAM_LIST_DB_PATH.getPath()],
            ['CHD_archive_list', 'CHD list index', g_PATHS.ROM_SET_CHD_LIST_DB_PATH.getPath()],
            ['cache_index', 'MAME cache index', g_PATHS.CACHE_INDEX_PATH.getPath()],
            ['history_idx_dic', 'History DAT', g_PATHS.HISTORY_IDX_PATH.getPath()],
            ['mameinfo_idx_dic', 'Mameinfo DAT', g_PATHS.MAMEINFO_IDX_PATH.getPath()],
            ['gameinit_idx_list', 'Gameinit DAT', g_PATHS.GAMEINIT_IDX_PATH.getPath()],
            ['command_idx_list', 'Command DAT', g_PATHS.COMMAND_IDX_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)
        # For compatibility with "All in one step" and "Step by step" functions.
        control_dic = db_dic['control_dic']
        audit_dic = {
            'machine_archives' : db_dic['machine_archives'],
            'ROM_ZIP_list'     : db_dic['ROM_ZIP_list'],
            'Sample_ZIP_list'  : db_dic['Sample_ZIP_list'],
            'CHD_archive_list' : db_dic['CHD_archive_list'],
        }

        # --- Scan ROMs/CHDs/Samples and updates ROM status (optional) ---
        options_dic = mame_check_before_scan_MAME_ROMs(g_PATHS, g_settings, control_dic)
        if not options_dic['abort']:
            mame_scan_MAME_ROMs(g_PATHS, g_settings, control_dic, options_dic,
                db_dic['machines'], db_dic['render'], db_dic['assets'], audit_dic['machine_archives'],
                audit_dic['ROM_ZIP_list'], audit_dic['Sample_ZIP_list'], audit_dic['CHD_archive_list'])
        else:
            log_info('Skipping mame_scan_MAME_ROMs()')

        # --- Scans MAME assets/artwork (optional) ---
        options_dic = mame_check_before_scan_MAME_assets(g_PATHS, g_settings, control_dic)
        if not options_dic['abort']:
            mame_scan_MAME_assets(g_PATHS, g_settings, control_dic,
                db_dic['assets'], db_dic['render'], db_dic['main_pclone_dic'])
        else:
            log_info('Skipping mame_scan_MAME_assets()')

        # --- Build MAME machines plot (mandatory) ---
        mame_build_MAME_plots(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['assets'],
            db_dic['history_idx_dic'], db_dic['mameinfo_idx_dic'],
            db_dic['gameinit_idx_list'], db_dic['command_idx_list'])

        # --- Regenerate asset hashed database ---
        fs_build_asset_hashed_db(g_PATHS, g_settings, control_dic, db_dic['assets'])

        # --- Regenerate MAME asset cache ---
        # Note that scanning only changes the assets, never the machines or render DB.
        if g_settings['debug_enable_MAME_asset_cache']:
            fs_build_asset_cache(g_PATHS, g_settings, control_dic,
                db_dic['cache_index'], db_dic['assets'])

        # --- Software Lists ---------------------------------------------------------------------
        if g_settings['enable_SL']:
            # --- Load databases ---
            db_files = [
                ['SL_index', 'Software Lists index', g_PATHS.SL_INDEX_PATH.getPath()],
                ['SL_PClone_dic', 'Software Lists Parent/Clone database', g_PATHS.SL_PCLONE_DIC_PATH.getPath()],
                ['SL_machines', 'Software Lists machines', g_PATHS.SL_MACHINES_PATH.getPath()],
            ]
            SL_dic = fs_load_files(db_files)

            # --- Scan SL ROMs/CHDs (optional) ---
            options_dic = mame_check_before_scan_SL_ROMs(g_PATHS, g_settings, control_dic)
            if not options_dic['abort']:
                mame_scan_SL_ROMs(g_PATHS, g_settings, control_dic,
                    options_dic, SL_dic['SL_index'])
            else:
                log_info('Skipping mame_scan_SL_ROMs()')

            # --- Scan SL assets/artwork (optional) ---
            options_dic = mame_check_before_scan_SL_assets(g_PATHS, g_settings, control_dic)
            if not options_dic['abort']:
                mame_scan_SL_assets(g_PATHS, g_settings, control_dic,
                    SL_dic['SL_index'], SL_dic['SL_PClone_dic'])
            else:
                log_info('Skipping mame_scan_SL_assets()')

            # --- Buils Software List items plot (mandatory) ---
            mame_build_SL_plots(g_PATHS, g_settings, control_dic,
                SL_dic['SL_index'], SL_dic['SL_machines'], db_dic['history_idx_dic'])
        else:
            log_info('SL disabled. Skipping SL scanning and plot building.')

        # --- So long and thanks for all the fish ---
        kodi_notify('All ROM/asset scanning finished')

    # --- Build Fanarts ---
    elif menu_item == 5:
        submenu = dialog.select('Build Fanarts', [
            'Test MAME Fanart',
            'Test Software List item Fanart',
            'Test MAME 3D Box',
            'Test Software List item 3D Box',
            'Build missing MAME Fanarts',
            'Rebuild all MAME Fanarts',
            'Build missing Software Lists Fanarts',
            'Rebuild all Software Lists Fanarts',
            'Build missing MAME 3D Boxes',
            'Rebuild all MAME 3D Boxes',
            'Build missing Software Lists 3D Boxes',
            'Rebuild all Software Lists 3D Boxes',
        ])
        if submenu < 0: return
        # >> Check if Pillow library is available. Abort if not.
        if not PILLOW_AVAILABLE:
            kodi_dialog_OK('Pillow Python library is not available. Aborting Fanart generation.')
            return

        # --- Test MAME Fanart ---
        if submenu == 0:
            log_info('command_context_setup_plugin() Testing MAME Fanart generation ...')
            Template_FN = g_PATHS.ADDON_CODE_DIR.pjoin('templates/AML-MAME-Fanart-template.xml')
            Asset_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin('media/MAME_assets')
            Fanart_FN = g_PATHS.ADDON_DATA_DIR.pjoin('MAME_Fanart.png')
            log_debug('Testing MAME Fanart generation ...')
            log_debug('Template_FN   "{0}"'.format(Template_FN.getPath()))
            log_debug('Fanart_FN     "{0}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN "{0}"'.format(Asset_path_FN.getPath()))

            # --- Load Fanart template from XML file ---
            layout = graphs_load_MAME_Fanart_template(Template_FN)
            if not layout:
                kodi_dialog_OK('Error loading XML MAME Fanart layout.')
                return

            # ---Use hard-coded assets ---
            m_name = 'dino'
            assets_dic = {
                m_name : {
                    'title'      : Asset_path_FN.pjoin('dino_title.png').getPath(),
                    'snap'       : Asset_path_FN.pjoin('dino_snap.png').getPath(),
                    'flyer'      : Asset_path_FN.pjoin('dino_flyer.png').getPath(),
                    'cabinet'    : Asset_path_FN.pjoin('dino_cabinet.png').getPath(),
                    'artpreview' : Asset_path_FN.pjoin('dino_artpreview.png').getPath(),
                    'PCB'        : Asset_path_FN.pjoin('dino_PCB.png').getPath(),
                    'clearlogo'  : Asset_path_FN.pjoin('dino_clearlogo.png').getPath(),
                    'cpanel'     : Asset_path_FN.pjoin('dino_cpanel.png').getPath(),
                    'marquee'    : Asset_path_FN.pjoin('dino_marquee.png').getPath(),
                }
            }
            graphs_build_MAME_Fanart(g_PATHS, layout, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (25, 25, 50), test_flag = True)

            # >> Display Fanart
            log_debug('Rendering fanart "{0}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{0}")'.format(Fanart_FN.getPath()))

        # --- Test SL Fanart ---
        elif submenu == 1:
            log_info('command_context_setup_plugin() Testing SL Fanart generation ...')
            Template_FN = g_PATHS.ADDON_CODE_DIR.pjoin('templates/AML-SL-Fanart-template.xml')
            Asset_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin('media/SL_assets')
            Fanart_FN = g_PATHS.ADDON_DATA_DIR.pjoin('SL_Fanart.png')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('Template_FN   "{0}"'.format(Template_FN.getPath()))
            log_debug('Fanart_FN     "{0}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN "{0}"'.format(Asset_path_FN.getPath()))

            # --- Load Fanart template from XML file ---
            layout = graphs_load_SL_Fanart_template(Template_FN)
            if not layout:
                kodi_dialog_OK('Error loading XML Software List Fanart layout.')
                return

            # --- Use hard-coded assets ---
            SL_name = '32x'
            m_name = 'doom'
            assets_dic = {
                m_name : {
                    'title'    : Asset_path_FN.pjoin('doom_title.png').getPath(),
                    'snap'     : Asset_path_FN.pjoin('doom_snap.png').getPath(),
                    'boxfront' : Asset_path_FN.pjoin('doom_boxfront.png').getPath(),
                }
            }
            graphs_build_SL_Fanart(
                g_PATHS, layout, SL_name, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (50, 50, 75), test_flag = True)

            # --- Display Fanart ---
            log_debug('Displaying image "{0}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{0}")'.format(Fanart_FN.getPath()))

        # --- Test MAME 3D Box ---
        elif submenu == 2:
            log_info('command_context_setup_plugin() Testing MAME 3D Box generation ...')
            Fanart_FN = g_PATHS.ADDON_DATA_DIR.pjoin('MAME_3dbox.png')
            Asset_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin('media/MAME_assets')
            # TProjection_FN = g_PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_56.json')
            TProjection_FN = g_PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_60.json')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('Fanart_FN      "{0}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN  "{0}"'.format(Asset_path_FN.getPath()))
            log_debug('TProjection_FN "{0}"'.format(TProjection_FN.getPath()))

            # Load 3D texture projection matrix
            t_projection = fs_load_JSON_file_dic(TProjection_FN.getPath())

            # Create fake asset dictionaries
            # m_name = 'dino'
            # assets_dic = {
            #     m_name : {
            #         'flyer'      : Asset_path_FN.pjoin('dino_flyer.png').getPath(),
            #         'clearlogo'  : Asset_path_FN.pjoin('dino_clearlogo.png').getPath(),
            #     }
            # }
            SL_name = 'MAME'
            m_name = 'mslug'
            assets_dic = {
                m_name : {
                    'flyer'     : Asset_path_FN.pjoin('mslug_flyer.png').getPath(),
                    'clearlogo' : Asset_path_FN.pjoin('mslug_clearlogo.png').getPath(),
                }
            }

            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced MAME Launcher', 'Generating test MAME 3D Box ... ')
            pDialog.update(15)
            graphs_build_MAME_3DBox(
                g_PATHS, t_projection, SL_name, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (50, 50, 75), test_flag = True)
            pDialog.update(100)
            pDialog.close()

            # --- Display Fanart ---
            log_debug('Displaying image "{0}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{0}")'.format(Fanart_FN.getPath()))

        # --- Test SL 3D Box ---
        elif submenu == 3:
            log_info('command_context_setup_plugin() Testing SL 3D Box generation ...')
            # TProjection_FN = g_PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_56.json')
            TProjection_FN = g_PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_60.json')
            Fanart_FN = g_PATHS.ADDON_DATA_DIR.pjoin('SL_3dbox.png')
            Asset_path_FN = g_PATHS.ADDON_CODE_DIR.pjoin('media/SL_assets')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('TProjection_FN "{0}"'.format(TProjection_FN.getPath()))
            log_debug('Fanart_FN      "{0}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN  "{0}"'.format(Asset_path_FN.getPath()))

            # Load 3D texture projection matrix
            t_projection = fs_load_JSON_file_dic(TProjection_FN.getPath())

            # Create fake asset dictionaries
            # SL items in AML don't have clearlogo, but for testing is OK.
            SL_name = 'genesis'
            m_name = 'sonic3'
            assets_dic = {
                m_name : {
                    'boxfront'  : Asset_path_FN.pjoin('sonic3_boxfront.png').getPath(),
                    'clearlogo' : Asset_path_FN.pjoin('sonic3_clearlogo.png').getPath(),
                }
            }

            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced MAME Launcher', 'Generating test SL 3D Box ... ')
            pDialog.update(15)
            graphs_build_MAME_3DBox(
                g_PATHS, t_projection, SL_name, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (50, 50, 75), test_flag = True)
            pDialog.update(100)
            pDialog.close()

            # --- Display Fanart ---
            log_debug('Displaying image "{0}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{0}")'.format(Fanart_FN.getPath()))

        # --- 4 -> Build missing MAME Fanarts ---
        # --- 5 -> Rebuild all MAME Fanarts ---
        # For a complete MAME artwork collection, rebuilding all Fanarts will take hours!
        elif submenu == 4 or submenu == 5:
            BUILD_MISSING = True if submenu == 4 else False
            if BUILD_MISSING:
                log_info('command_context_setup_plugin() Building missing Fanarts ...')
            else:
                log_info('command_context_setup_plugin() Rebuilding all Fanarts ...')
            data_dic = graphs_load_MAME_Fanart_stuff(g_PATHS, g_settings, BUILD_MISSING)
            if data_dic['abort']: return
            # Kodi notification inside this function.
            graphs_build_MAME_Fanart_all(g_PATHS, g_settings, data_dic)

        # --- 6 -> Missing SL Fanarts ---
        # --- 7 -> Rebuild all SL Fanarts ---
        elif submenu == 6 or submenu == 7:
            BUILD_MISSING = True if submenu == 6 else False
            if BUILD_MISSING:
                log_info('command_context_setup_plugin() Building missing Software Lists Fanarts ...')
            else:
                log_info('command_context_setup_plugin() Rebuilding all Software Lists Fanarts ...')
            data_dic = graphs_load_SL_Fanart_stuff(g_PATHS, g_settings, BUILD_MISSING)
            if data_dic['abort']: return
            graphs_build_SL_Fanart_all(g_PATHS, g_settings, data_dic)

        # --- 8 -> Missing MAME 3D Boxes ---
        # --- 9 -> Rebuild all MAME 3D Boxes ---
        elif submenu == 8 or submenu == 9:
            BUILD_MISSING = True if submenu == 8 else False
            if BUILD_MISSING:
                log_info('command_context_setup_plugin() Building missing MAME 3D Boxes ...')
            else:
                log_info('command_context_setup_plugin() Rebuilding all MAME 3D Boxes ...')
            data_dic = graphs_load_MAME_3DBox_stuff(g_PATHS, g_settings, BUILD_MISSING)
            if data_dic['abort']: return
            graphs_build_MAME_3DBox_all(g_PATHS, g_settings, data_dic)

        # --- 10 -> Missing SL 3D Boxes ---
        # --- 11 -> Rebuild all SL 3D Boxes ---
        elif submenu == 10 or submenu == 11:
            BUILD_MISSING = True if submenu == 10 else False
            if BUILD_MISSING:
                log_info('command_context_setup_plugin() Building missing Software Lists 3D Boxes ...')
            else:
                log_info('command_context_setup_plugin() Rebuilding all Software Lists 3D Boxes ...')
            data_dic = graphs_load_SL_3DBox_stuff(g_PATHS, g_settings, BUILD_MISSING)
            if data_dic['abort']: return
            graphs_build_SL_3DBox_all(g_PATHS, g_settings, data_dic)

    # --- Audit MAME machine ROMs/CHDs ---
    # NOTE It is likekely that this function will take a looong time. It is important that the
    #      audit process can be canceled and a partial report is written.
    elif menu_item == 6:
        log_info('command_context_setup_plugin() Audit MAME machines ROMs/CHDs ...')

        # --- Check for requirements/errors ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())

        # --- Load machines, ROMs and CHDs databases ---
        db_files = [
            ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['audit_roms', 'MAME ROM Audit', g_PATHS.ROM_AUDIT_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # --- Audit all MAME machines ---
        # 1) Updates control_dic statistics and timestamp.
        mame_audit_MAME_all(g_PATHS, g_settings, control_dic,
            db_dic['machines'], db_dic['render'], db_dic['audit_roms'])
        kodi_notify('ROM and CHD audit finished')

    # --- Audit SL ROMs/CHDs ---
    elif menu_item == 7:
        log_info('command_context_setup_plugin() Audit SL ROMs/CHDs ...')

        # --- Check for requirements/errors ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        SL_index = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())

        # --- Audit all Software List items ---
        # 1) Updates control_dic statistics and timestamps and saves it.
        mame_audit_SL_all(g_PATHS, g_settings, control_dic, SL_index)
        kodi_notify('Software Lists audit finished')

    # --- Build Step by Step ---
    elif menu_item == 8:
        submenu = dialog.select('Setup plugin (step by step)', [
            'Build MAME databases',
            'Build MAME Audit/Scanner databases',
            'Build MAME Catalogs',
            'Build Software List databases',
            'Scan MAME ROMs/CHDs/Samples',
            'Scan MAME assets/artwork',
            'Scan Software List ROMs/CHDs',
            'Scan Software List assets/artwork',
            'Build MAME machine plots',
            'Build Software List item plots',
            'Rebuild MAME machine and asset caches',
        ])
        if submenu < 0: return

        # --- Build main MAME database, PClone list and hashed database ---
        if submenu == 0:
            log_info('command_context_setup_plugin() Generating MAME main database and PClone list ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_build_MAME_main_database(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # --- Parse MAME XML and generate main database and PClone list ---
            # 1) Builds all databases.
            # 2) Creates the ROM hashed database.
            # 3) Creates the (empty) Asset cache.
            # 4) Updates control_dic stats and timestamp and saves it.
            #
            # try:
            #     DB = mame_build_MAME_main_database(g_PATHS, g_settings, control_dic)
            # except GeneralError as err:
            #     log_error(err.msg)
            #     raise SystemExit
            #
            data_dic = mame_build_MAME_main_database(g_PATHS, g_settings, control_dic, __addon_version__)
            kodi_notify('Main MAME databases built')

        # --- Build ROM audit/scanner databases ---
        elif submenu == 1:
            log_info('command_context_setup_plugin() Generating ROM audit/scanner databases ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_build_ROM_audit_databases(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # --- Load databases ---
            db_files = [
                ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
                ['devices', 'MAME machine Devices', g_PATHS.DEVICES_DB_PATH.getPath()],
                ['roms', 'MAME machine ROMs', g_PATHS.ROMS_DB_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)

            # --- Generate ROM databases ---
            # 1) Updates control_dic and t_MAME_Audit_DB_build timestamp and saves it.
            mame_build_ROM_audit_databases(g_PATHS, g_settings, control_dic,
                db_dic['machines'], db_dic['render'], db_dic['devices'], db_dic['roms'])
            kodi_notify('ROM audit/scanner databases built')

        # --- Build MAME catalogs ---
        elif submenu == 2:
            log_info('command_context_setup_plugin() Building MAME catalogs ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_build_MAME_catalogs(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # --- Load databases ---
            db_files = [
                ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
                ['roms', 'MAME machine ROMs', g_PATHS.ROMS_DB_PATH.getPath()],
                ['main_pclone_dic', 'MAME PClone dictionary', g_PATHS.MAIN_PCLONE_DIC_PATH.getPath()],
                ['assets', 'MAME machine Assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)

            # --- Build MAME catalog ---
            # At this time the asset database will be empty (scanner has not been run). However, 
            # the asset cache with an empty database is required to render the machines in the catalogs.
            # 1) Creates cache_index_dic and saves it.
            # 2) Updates control_dic and saves it.
            # 3) Does not require to rebuild the render hashed database.
            # 4) Requires rebuilding of the render cache.
            # 5) Requires rebuilding of the asset cache.
            db_dic['cache_index'] = mame_build_MAME_catalogs(g_PATHS, g_settings, control_dic,
                db_dic['machines'], db_dic['render'], db_dic['roms'],
                db_dic['main_pclone_dic'], db_dic['assets'])
            if g_settings['debug_enable_MAME_render_cache']:
                fs_build_render_cache(g_PATHS, g_settings, control_dic,
                    db_dic['cache_index'], db_dic['render'])
            if g_settings['debug_enable_MAME_asset_cache']:
                fs_build_asset_cache(g_PATHS, g_settings, control_dic,
                    db_dic['cache_index'], db_dic['assets'])
            kodi_notify('MAME Catalogs built')

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs ---
        elif submenu == 3:
            log_info('command_context_setup_plugin() Scanning MAME ROMs/CHDs/Samples ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_build_SL_databases(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # --- Read main database and control dic ---
            db_files = [
                ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)

            # --- Build SL databases ---
            # 1) Modifies and saves control_dic
            mame_build_SoftwareLists_databases(g_PATHS, g_settings, control_dic,
                db_dic['machines'], db_dic['render'])
            kodi_notify('Software Lists database built')

        # --- Scan ROMs/CHDs/Samples and updates ROM status ---
        elif submenu == 4:
            log_info('command_context_setup_plugin() Scanning MAME ROMs/CHDs/Samples ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_scan_MAME_ROMs(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # >> Load machine database and control_dic and scan
            db_files = [
                ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
                ['assets', 'MAME machine Assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
                ['machine_archives', 'Machine file list', g_PATHS.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
                ['ROM_ZIP_list', 'ROM List index', g_PATHS.ROM_SET_ROM_LIST_DB_PATH.getPath()],
                ['Sample_ZIP_list', 'ROM List index', g_PATHS.ROM_SET_SAM_LIST_DB_PATH.getPath()],
                ['CHD_archive_list', 'CHD list index', g_PATHS.ROM_SET_CHD_LIST_DB_PATH.getPath()],
                ['cache_index', 'MAME cache index', g_PATHS.CACHE_INDEX_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)
            # For compatibility with "All in one step" menu option
            audit_dic = {
                'machine_archives' : db_dic['machine_archives'],
                'ROM_ZIP_list'     : db_dic['ROM_ZIP_list'],
                'Sample_ZIP_list'  : db_dic['Sample_ZIP_list'],
                'CHD_archive_list' : db_dic['CHD_archive_list'],
            }

            # --- Scan MAME ROMs/CHDs/Samples ---
            # 1) Updates 'flags' field in assets_dic
            # 2) Updates timestamp t_MAME_ROM_scan and statistics in control_dic.
            # 3) Saves control_dic and assets_dic.
            # 4) Requires rebuilding the asset hashed DB.
            # 5) Requires rebuilding the asset cache.
            mame_scan_MAME_ROMs(g_PATHS, g_settings, control_dic, options_dic,
                db_dic['machines'], db_dic['render'], db_dic['assets'], audit_dic['machine_archives'],
                audit_dic['ROM_ZIP_list'], audit_dic['Sample_ZIP_list'], audit_dic['CHD_archive_list'])
            fs_build_asset_hashed_db(g_PATHS, g_settings, control_dic, db_dic['assets'])
            if g_settings['debug_enable_MAME_asset_cache']:
                fs_build_asset_cache(g_PATHS, g_settings, control_dic,
                    db_dic['cache_index'], db_dic['assets'])
            kodi_notify('Scanning of ROMs, CHDs and Samples finished')

        # --- Scans MAME assets/artwork ---
        elif submenu == 5:
            log_info('command_context_setup_plugin() Scanning MAME assets/artwork ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_scan_MAME_assets(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # >> Load machine database and scan
            db_files = [
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
                ['assets', 'MAME machine Assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
                ['main_pclone_dic', 'MAME PClone dictionary', g_PATHS.MAIN_PCLONE_DIC_PATH.getPath()],
                ['cache_index', 'MAME cache index', g_PATHS.CACHE_INDEX_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)

            # --- Scan MAME assets ---
            # 1) Mutates assets_dic and control_dic (timestamp and stats)
            # 2) Saves assets_dic and control_dic.
            # 2) Requires rebuilding of the asset hashed DB.
            # 3) Requires rebuilding of the asset cache.
            mame_scan_MAME_assets(g_PATHS, g_settings, control_dic,
                db_dic['assets'], db_dic['render'], db_dic['main_pclone_dic'])
            fs_build_asset_hashed_db(g_PATHS, g_settings, control_dic, db_dic['assets'])
            if g_settings['debug_enable_MAME_asset_cache']:
                fs_build_asset_cache(g_PATHS, g_settings, control_dic,
                    db_dic['cache_index'], db_dic['assets'])
            kodi_notify('Scanning of assets/artwork finished')

        # --- Scan SL ROMs/CHDs ---
        elif submenu == 6:
            log_info('command_context_setup_plugin() Scanning SL ROMs/CHDs ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_scan_SL_ROMs(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # --- Load SL and scan ROMs/CHDs ---
            db_files = [
                ['SL_index', 'Software Lists index', g_PATHS.SL_INDEX_PATH.getPath()],
            ]
            SL_dic = fs_load_files(db_files)

            # 1) Mutates control_dic (timestamp and statistics)
            # 2) Saves control_dic
            mame_scan_SL_ROMs(g_PATHS, g_settings, control_dic, options_dic, SL_dic['SL_index'])
            kodi_notify('Scanning of SL ROMs finished')

        # --- Scan SL assets/artwork ---
        # >> Database format: ADDON_DATA_DIR/db_SoftwareLists/32x_assets.json
        # >> { 'ROM_name' : {'asset1' : 'path', 'asset2' : 'path', ... }, ... }
        elif submenu == 7:
            log_info('command_context_setup_plugin() Scanning SL assets/artwork ...')

            # --- Check for requirements/errors ---
            control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
            options_dic = mame_check_before_scan_SL_assets(g_PATHS, g_settings, control_dic)
            if options_dic['abort']: return

            # --- Load SL databases ---
            db_files = [
                ['SL_index', 'Software Lists index', g_PATHS.SL_INDEX_PATH.getPath()],
                ['SL_PClone_dic', 'Software Lists Parent/Clone database', g_PATHS.SL_PCLONE_DIC_PATH.getPath()],
            ]
            SL_dic = fs_load_files(db_files)

            # --- Scan SL ---
            # 1) Mutates control_dic (timestamp and statistics) and saves it.
            mame_scan_SL_assets(g_PATHS, g_settings, control_dic, SL_dic['SL_index'], SL_dic['SL_PClone_dic'])
            kodi_notify('Scanning of SL assets finished')

        # --- Build MAME machines plot ---
        elif submenu == 8:
            log_debug('Rebuilding MAME machine plots ...')

            # --- Check for requirements/errors ---

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', g_PATHS.MAIN_CONTROL_PATH.getPath()],
                ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
                ['assets', 'MAME machine Assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
                ['cache_index', 'MAME cache index', g_PATHS.CACHE_INDEX_PATH.getPath()],
                ['history_idx_dic', 'History DAT', g_PATHS.HISTORY_IDX_PATH.getPath()],
                ['mameinfo_idx_dic', 'Mameinfo DAT', g_PATHS.MAMEINFO_IDX_PATH.getPath()],
                ['gameinit_idx_list', 'Gameinit DAT', g_PATHS.GAMEINIT_IDX_PATH.getPath()],
                ['command_idx_list', 'Command DAT', g_PATHS.COMMAND_IDX_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)

            # --- Traverse MAME machines and build plot ---
            # 1) Mutates and saves the assets database
            # 2) Requires rebuilding of the MAME asset hashed DB.
            # 3) Requires rebuilding if the MAME asset cache.
            mame_build_MAME_plots(g_PATHS, g_settings, db_dic['control_dic'],
                db_dic['machines'], db_dic['render'], db_dic['assets'],
                db_dic['history_idx_dic'], db_dic['mameinfo_idx_dic'],
                db_dic['gameinit_idx_list'], db_dic['command_idx_list'])
            fs_build_asset_hashed_db(g_PATHS, g_settings, db_dic['control_dic'], db_dic['assets'])
            if g_settings['debug_enable_MAME_asset_cache']:
                fs_build_asset_cache(g_PATHS, g_settings, db_dic['control_dic'],
                    db_dic['cache_index'], db_dic['assets'])
            kodi_notify('MAME machines plot generation finished')

        # --- Buils Software List items plot ---
        elif submenu == 9:
            log_debug('Rebuilding Software List items plots ...')

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', g_PATHS.MAIN_CONTROL_PATH.getPath()],
                ['SL_index', 'Software Lists index', g_PATHS.SL_INDEX_PATH.getPath()],
                ['SL_machines', 'Software Lists machines', g_PATHS.SL_MACHINES_PATH.getPath()],
                ['history_idx_dic', 'History DAT index', g_PATHS.HISTORY_IDX_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)
            # For compatibility with "All in one step" menu option
            SL_dic = {
                'SL_index'    : db_dic['SL_index'],
                'SL_machines' : db_dic['SL_machines'],
            }

            # --- Build plots ---
            mame_build_SL_plots(g_PATHS, g_settings, db_dic['control_dic'],
                SL_dic['SL_index'], SL_dic['SL_machines'], db_dic['history_idx_dic'])
            kodi_notify('SL item plot generation finished')

        # --- Regenerate MAME machine render and assets cache ---
        elif submenu == 10:
            log_debug('Rebuilding MAME machine and assets cache ...')

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', g_PATHS.MAIN_CONTROL_PATH.getPath()],
                ['cache_index', 'Cache index', g_PATHS.CACHE_INDEX_PATH.getPath()],
                ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
                ['assets', 'MAME machine Assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
            ]
            db_dic = fs_load_files(db_files)

            # --- Regenerate ROM and asset caches ---
            fs_build_render_cache(g_PATHS, g_settings, db_dic['control_dic'],
                db_dic['cache_index'], db_dic['render'])
            fs_build_asset_cache(g_PATHS, g_settings, db_dic['control_dic'],
                db_dic['cache_index'], db_dic['assets'])
            kodi_notify('MAME machine and asset caches rebuilt')

#
# Execute utilities.
#
def command_exec_utility(which_utility):
    log_debug('command_exec_utility() which_utility = "{0}" starting ...'.format(which_utility))

    # Check MAME version
    # Run 'mame -?' and extract version from stdout
    if which_utility == 'CHECK_MAME_VERSION':
        # --- Check for errors ---
        if not g_settings['mame_prog']:
            kodi_dialog_OK('MAME executable is not set.')
            return

        # --- Check MAME version ---
        mame_prog_FN = FileName(g_settings['mame_prog'])
        mame_version_str = fs_extract_MAME_version(g_PATHS, mame_prog_FN)
        kodi_dialog_OK('MAME version is {0}'.format(mame_version_str))

    # Check AML configuration
    elif which_utility == 'CHECK_CONFIG':
        # Functions defined here can see local variables defined in this code block.
        def aux_check_dir_ERR(slist, dir_str, msg):
            if dir_str:
                if FileName(dir_str).exists():
                    slist.append('{0} {1} "{2}"'.format(OK, msg, dir_str))
                else:
                    slist.append('{0} {1} not found'.format(ERR, msg))
            else:
                slist.append('{0} {1} not set'.format(ERR, msg))

        def aux_check_dir_WARN(slist, dir_str, msg):
            if dir_str:
                if FileName(dir_str).exists():
                    slist.append('{0} {1} "{2}"'.format(OK, msg, dir_str))
                else:
                    slist.append('{0} {1} not found'.format(WARN, msg))
            else:
                slist.append('{0} {1} not set'.format(WARN, msg))

        def aux_check_file_WARN(slist, file_str, msg):
            if file_str:
                if FileName(file_str).exists():
                    slist.append('{0} {1} "{2}"'.format(OK, msg, file_str))
                else:
                    slist.append('{0} {1} not found'.format(WARN, msg))
            else:
                slist.append('{0} {1} not set'.format(WARN, msg))

        def aux_check_asset_dir(slist, dir_FN, msg):
            if dir_FN.exists():
                slist.append('{0} Found {1} path "{2}"'.format(OK, msg, dir_FN.getPath()))
            else:
                slist.append('{0} {1} path does not exist'.format(WARN, msg))
                slist.append('     Tried "{0}"'.format(dir_FN.getPath()))

        # Checks AML configuration and informs users of potential problems.
        log_info('command_exec_utility() Checking AML configuration ...')
        OK   = '[COLOR green]OK  [/COLOR]'
        WARN = '[COLOR yellow]WARN[/COLOR]'
        ERR  = '[COLOR red]ERR [/COLOR]'
        slist = []

        # --- Check mandatory stuff ---
        slist.append('[COLOR orange]Mandatory stuff[/COLOR]')
        # MAME executable
        if g_settings['mame_prog']:
            if FileName(g_settings['mame_prog']).exists():
                slist.append('{0} MAME executable "{1}"'.format(OK, g_settings['mame_prog']))
            else:
                slist.append('{0} MAME executable not found'.format(ERR))
        else:
            slist.append('{0} MAME executable not set'.format(ERR))
        # ROM path
        aux_check_dir_ERR(slist, g_settings['rom_path'], 'MAME ROM path')
        slist.append('')

        # --- MAME assets ---
        slist.append('[COLOR orange]MAME assets[/COLOR]')
        if g_settings['assets_path']:
            if FileName(g_settings['assets_path']).exists():
                slist.append('{0} MAME Asset path "{1}"'.format(OK, g_settings['assets_path']))

                # >> Check that artwork subdirectories exist
                Asset_path_FN = FileName(g_settings['assets_path'])

                _3dboxes_FN = Asset_path_FN.pjoin('3dboxes')
                artpreview_FN = Asset_path_FN.pjoin('artpreviews')
                artwork_FN = Asset_path_FN.pjoin('artwork')
                cabinets_FN = Asset_path_FN.pjoin('cabinets')
                clearlogos_FN = Asset_path_FN.pjoin('clearlogos')
                cpanels_FN = Asset_path_FN.pjoin('cpanels')
                fanarts_FN = Asset_path_FN.pjoin('fanarts')
                flyers_FN = Asset_path_FN.pjoin('flyers')
                manuals_FN = Asset_path_FN.pjoin('manuals')
                marquees_FN = Asset_path_FN.pjoin('marquees')
                PCB_FN = Asset_path_FN.pjoin('PCBs')
                snaps_FN = Asset_path_FN.pjoin('snaps')
                titles_FN = Asset_path_FN.pjoin('titles')
                videosnaps_FN = Asset_path_FN.pjoin('videosnaps')

                aux_check_asset_dir(slist, _3dboxes_FN, '3D Boxes')
                aux_check_asset_dir(slist, artpreview_FN, 'Artpreviews')
                aux_check_asset_dir(slist, artwork_FN, 'Artwork')
                aux_check_asset_dir(slist, cabinets_FN, 'Cabinets')
                aux_check_asset_dir(slist, clearlogos_FN, 'Clearlogos')
                aux_check_asset_dir(slist, cpanels_FN, 'CPanels')
                aux_check_asset_dir(slist, fanarts_FN, 'Fanarts')
                aux_check_asset_dir(slist, flyers_FN, 'Flyers')
                aux_check_asset_dir(slist, manuals_FN, 'Manuals')
                aux_check_asset_dir(slist, marquees_FN, 'Marquees')
                aux_check_asset_dir(slist, PCB_FN, 'PCB')
                aux_check_asset_dir(slist, snaps_FN, 'Snaps')
                aux_check_asset_dir(slist, titles_FN, 'Titles')
                aux_check_asset_dir(slist, videosnaps_FN, 'Trailers')
            else:
                slist.append('{0} MAME Asset path not found'.format(ERR))
        else:
            slist.append('{0} MAME Asset path not set'.format(WARN))
        slist.append('')

        # --- CHD path ---
        slist.append('[COLOR orange]MAME optional paths[/COLOR]')
        aux_check_dir_WARN(slist, g_settings['chd_path'], 'MAME CHD path')

        # --- Samples path ---
        aux_check_dir_WARN(slist, g_settings['samples_path'], 'MAME Samples path')
        slist.append('')

        # --- Software Lists paths ---
        slist.append('[COLOR orange]Software List paths[/COLOR]')
        aux_check_dir_WARN(slist, g_settings['SL_hash_path'], 'SL hash path')
        aux_check_dir_WARN(slist, g_settings['SL_rom_path'], 'SL ROM path')
        aux_check_dir_WARN(slist, g_settings['SL_chd_path'], 'SL CHD path')
        slist.append('')

        slist.append('[COLOR orange]Software Lists assets[/COLOR]')
        if g_settings['assets_path']:
            if FileName(g_settings['assets_path']).exists():
                slist.append('{0} MAME Asset path "{1}"'.format(OK, g_settings['assets_path']))

                # >> Check that artwork subdirectories exist
                Asset_path_FN = FileName(g_settings['assets_path'])

                _3dboxes_FN = Asset_path_FN.pjoin('3dboxes_SL')
                covers_FN = Asset_path_FN.pjoin('covers_SL')
                fanarts_FN = Asset_path_FN.pjoin('fanarts_SL')
                manuals_FN = Asset_path_FN.pjoin('manuals_SL')
                snaps_FN = Asset_path_FN.pjoin('snaps_SL')
                titles_FN = Asset_path_FN.pjoin('titles_SL')
                videosnaps_FN = Asset_path_FN.pjoin('videosnaps_SL')

                aux_check_asset_dir(slist, _3dboxes_FN, '3D Boxes')
                aux_check_asset_dir(slist, covers_FN, 'SL Covers')
                aux_check_asset_dir(slist, fanarts_FN, 'SL Fanarts')
                aux_check_asset_dir(slist, manuals_FN, 'SL Manuals')
                aux_check_asset_dir(slist, snaps_FN, 'SL Snaps')
                aux_check_asset_dir(slist, titles_FN, 'SL Titles')
                aux_check_asset_dir(slist, videosnaps_FN, 'SL Trailers')
            else:
                slist.append('{0} MAME Asset path not found'.format(ERR))
        else:
            slist.append('{0} MAME Asset path not set'.format(WARN))
        slist.append('')

        # --- Optional INI files ---
        slist.append('[COLOR orange]INI/DAT files[/COLOR]')
        if g_settings['dats_path']:
            if FileName(g_settings['dats_path']).exists():
                slist.append('{0} MAME INI/DAT path "{1}"'.format(OK, g_settings['dats_path']))

                DATS_dir_FN = FileName(g_settings['dats_path'])
                ALLTIME_FN = DATS_dir_FN.pjoin(ALLTIME_INI)
                ARTWORK_FN = DATS_dir_FN.pjoin(ARTWORK_INI)
                BESTGAMES_FN = DATS_dir_FN.pjoin(BESTGAMES_INI)
                CATEGORY_FN = DATS_dir_FN.pjoin(CATEGORY_INI)
                CATLIST_FN = DATS_dir_FN.pjoin(CATLIST_INI)
                CATVER_FN = DATS_dir_FN.pjoin(CATVER_INI)
                GENRE_FN = DATS_dir_FN.pjoin(GENRE_INI)
                MATURE_FN = DATS_dir_FN.pjoin(MATURE_INI)
                NPLAYERS_FN = DATS_dir_FN.pjoin(NPLAYERS_INI)
                SERIES_FN = DATS_dir_FN.pjoin(SERIES_INI)
                COMMAND_FN = DATS_dir_FN.pjoin(COMMAND_DAT)
                GAMEINIT_FN = DATS_dir_FN.pjoin(GAMEINIT_DAT)
                HISTORY_FN = DATS_dir_FN.pjoin(HISTORY_DAT)
                MAMEINFO_FN = DATS_dir_FN.pjoin(MAMEINFO_DAT)

                aux_check_file_WARN(slist, ALLTIME_FN.getPath(), ALLTIME_INI + ' file')
                aux_check_file_WARN(slist, ARTWORK_FN.getPath(), ARTWORK_INI + ' file')
                aux_check_file_WARN(slist, BESTGAMES_FN.getPath(), BESTGAMES_INI + ' file')
                aux_check_file_WARN(slist, CATEGORY_FN.getPath(), CATEGORY_INI + ' file')
                aux_check_file_WARN(slist, CATLIST_FN.getPath(), CATLIST_INI + ' file')
                aux_check_file_WARN(slist, CATVER_FN.getPath(), CATVER_INI + ' file')
                aux_check_file_WARN(slist, GENRE_FN.getPath(), GENRE_INI + ' file')
                aux_check_file_WARN(slist, MATURE_FN.getPath(), MATURE_INI + ' file')
                aux_check_file_WARN(slist, NPLAYERS_FN.getPath(), NPLAYERS_INI + ' file')
                aux_check_file_WARN(slist, SERIES_FN.getPath(), SERIES_INI + ' file')
                aux_check_file_WARN(slist, COMMAND_FN.getPath(), COMMAND_DAT + ' file')
                aux_check_file_WARN(slist, GAMEINIT_FN.getPath(), GAMEINIT_DAT + ' file')
                aux_check_file_WARN(slist, HISTORY_FN.getPath(), HISTORY_DAT + ' file')
                aux_check_file_WARN(slist, MAMEINFO_FN.getPath(), MAMEINFO_DAT + ' file')
            else:
                slist.append('{0} MAME INI/DAT path not found'.format(ERR))
        else:
            slist.append('{0} MAME INI/DAT path not set'.format(WARN))

        # --- Display info to the user ---
        display_text_window('AML configuration check report', '\n'.join(slist))

    # Check and update all favourite objects.
    # Check if Favourites can be found in current MAME main database. It may happen that
    # a machine is renamed between MAME version although I think this is very unlikely.
    # MAME Favs can not be relinked. If the machine is not found in current database it must
    # be deleted by the user and a new Favourite created.
    # If the machine is found in the main database, then update the Favourite database
    # with data from the main database.
    elif which_utility == 'CHECK_ALL_FAV_OBJECTS':
        log_debug('command_exec_utility() Executing CHECK_ALL_FAV_OBJECTS...')

        # --- Ensure databases are built and assets scanned before updating Favourites ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options = check_MAME_DB_status(MAME_ASSETS_SCANNED, control_dic)
        if not options['condition']:
            kodi_dialog_OK(options['msg'])
            return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['assets', 'MAME machine assets', g_PATHS.MAIN_ASSETS_DB_PATH.getPath()],
            ['SL_index', 'Software Lists index', g_PATHS.SL_INDEX_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        mame_update_MAME_Fav_objects(
            g_PATHS, control_dic, db_dic['machines'], db_dic['render'], db_dic['assets'])
        mame_update_MAME_MostPlay_objects(
            g_PATHS, control_dic, db_dic['machines'], db_dic['render'], db_dic['assets'])
        mame_update_MAME_RecentPlay_objects(
            g_PATHS, control_dic, db_dic['machines'], db_dic['render'], db_dic['assets'])
        mame_update_SL_Fav_objects(g_PATHS, control_dic, db_dic['SL_index'])
        mame_update_SL_MostPlay_objects(g_PATHS, control_dic, db_dic['SL_index'])
        mame_update_SL_RecentPlay_objects(g_PATHS, control_dic, db_dic['SL_index'])
        kodi_refresh_container()
        kodi_notify('All Favourite objects checked')

    # Check MAME and SL CRC 32 hash collisions.
    # The assumption in this function is that there is not SHA1 hash collisions.
    # Implicit ROM merging must not be confused with a collision.
    elif which_utility == 'CHECK_MAME_COLLISIONS':
        log_info('command_check_MAME_CRC_collisions() Initialising ...')

        # --- Check database ---
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        options = check_MAME_DB_status(MAME_CATALOG_BUILT, control_dic)
        if not options['condition']:
            kodi_dialog_OK(options['msg'])
            return False

        # --- Open ROMs database ---
        db_files = [
            ['machine_roms', 'MAME machine ROMs', g_PATHS.ROMS_DB_PATH.getPath()],
            ['roms_sha1_dic', 'MAME ROMs SHA1 dictionary', g_PATHS.SHA1_HASH_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # Detect implicit ROM merging using the SHA1 hash and check for CRC32 collisions for
        # non-implicit merged ROMs.
        pdialog_line1 = 'Checking for MAME CRC32 hash collisions ...'
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        total_machines = len(db_dic['machine_roms'])
        processed_machines = 0
        crc_roms_dic = {}
        sha1_roms_dic = {}
        num_collisions = 0
        table_str = []
        table_str.append(['right',  'left',     'left', 'left', 'left'])
        table_str.append(['Status', 'ROM name', 'Size', 'CRC',  'SHA1'])
        for m_name in sorted(db_dic['machine_roms']):
            pDialog.update((processed_machines*100) // total_machines, pdialog_line1)
            m_roms = db_dic['machine_roms'][m_name]
            for rom in m_roms['roms']:
                rom_nonmerged_location = m_name + '/' + rom['name']
                # >> Skip invalid ROMs (no CRC, no SHA1
                if rom_nonmerged_location not in db_dic['roms_sha1_dic']:
                    continue
                sha1 = db_dic['roms_sha1_dic'][rom_nonmerged_location]
                if sha1 in sha1_roms_dic:
                    # >> ROM implicit merging (using SHA1). No check of CRC32 collision.
                    pass
                else:
                    # >> No ROM implicit mergin. Check CRC32 collision
                    sha1_roms_dic[sha1] = rom_nonmerged_location
                    if rom['crc'] in crc_roms_dic:
                        num_collisions += 1
                        coliding_name = crc_roms_dic[rom['crc']]
                        coliding_crc = rom['crc']
                        coliding_sha1 = db_dic['roms_sha1_dic'][coliding_name]
                        table_str.append(
                            ['Collision', rom_nonmerged_location, str(rom['size']), rom['crc'], sha1])
                        table_str.append(['with', coliding_name, ' ', coliding_crc, coliding_sha1])
                    else:
                        crc_roms_dic[rom['crc']] = rom_nonmerged_location
            processed_machines += 1
        pDialog.update((processed_machines*100) // total_machines, pdialog_line1, ' ')
        pDialog.close()
        log_debug('MAME has {0:,d} valid ROMs in total'.format(len(db_dic['roms_sha1_dic'])))
        log_debug('There are {0} CRC32 collisions'.format(num_collisions))

        # --- Write report and debug file ---
        slist = []
        slist.append('*** AML MAME ROMs CRC32 hash collision report ***')
        slist.append('MAME has {0:,d} valid ROMs in total'.format(len(db_dic['roms_sha1_dic'])))
        slist.append('There are {0} CRC32 collisions'.format(num_collisions))
        slist.append('')
        table_str_list = text_render_table_str(table_str)
        slist.extend(table_str_list)
        display_text_window('AML MAME CRC32 hash collision report', '\n'.join(slist))
        log_info('Writing "{0}"'.format(g_PATHS.REPORT_DEBUG_MAME_COLLISIONS_PATH.getPath()))
        with open(g_PATHS.REPORT_DEBUG_MAME_COLLISIONS_PATH.getPath(), 'w') as file:
            file.write('\n'.join(slist).encode('utf-8'))

    elif which_utility == 'CHECK_SL_COLLISIONS':
        log_info('command_exec_utility() Initialising CHECK_SL_COLLISIONS ...')

        # --- Load SL catalog and check for errors ---
        SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())

        # --- Process all SLs ---
        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Scanning Sofware Lists ROMs/CHDs ...'
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        total_files = len(SL_catalog_dic)
        processed_files = 0
        pDialog.update(0)
        roms_sha1_dic = {}
        crc_roms_dic = {}
        sha1_roms_dic = {}
        num_collisions = 0
        table_str = []
        table_str.append(['right',  'left',     'left', 'left', 'left'])
        table_str.append(['Status', 'ROM name', 'Size', 'CRC',  'SHA1'])
        for SL_name in sorted(SL_catalog_dic):
            # >> Progress dialog
            update_number = (processed_files*100) // total_files
            pDialog.update(update_number, pdialog_line1, 'Software List {0} ...'.format(SL_name))

            # >> Load SL databases
            # SL_SETS_DB_FN = SL_hash_dir_FN.pjoin(SL_name + '.json')
            # sl_sets = fs_load_JSON_file_dic(SL_SETS_DB_FN.getPath(), verbose = False)
            SL_ROMS_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_name + '_ROMs.json')
            sl_roms = fs_load_JSON_file_dic(SL_ROMS_DB_FN.getPath(), verbose = False)

            # >> First step: make a SHA1 dictionary of all SL item hashes
            for set_name in sorted(sl_roms):
                set_rom_list = sl_roms[set_name]
                for area in set_rom_list:
                    if 'dataarea' not in area: continue
                    for da_dict in area['dataarea']:
                        for rom in da_dict['roms']:
                            sha1 = rom['sha1']
                            if sha1:
                                rom_nonmerged_location = SL_name + '/' + set_name + '/' + rom['name']
                                roms_sha1_dic[rom_nonmerged_location] = sha1

            # >> Second step: make
            for set_name in sorted(sl_roms):
                set_rom_list = sl_roms[set_name]
                for area in set_rom_list:
                    if 'dataarea' not in area: continue
                    for da_dict in area['dataarea']:
                        for rom in da_dict['roms']:
                            rom_nonmerged_location = SL_name + '/' + set_name + '/' + rom['name']
                            # >> Skip invalid ROMs (no CRC, no SHA1
                            if rom_nonmerged_location not in roms_sha1_dic:
                                continue
                            sha1 = roms_sha1_dic[rom_nonmerged_location]
                            if sha1 in sha1_roms_dic:
                                # >> ROM implicit merging (using SHA1). No check of CRC32 collision.
                                pass
                            else:
                                # >> No ROM implicit mergin. Check CRC32 collision
                                sha1_roms_dic[sha1] = rom_nonmerged_location
                                if rom['crc'] in crc_roms_dic:
                                    num_collisions += 1
                                    coliding_name = crc_roms_dic[rom['crc']]
                                    coliding_crc = rom['crc']
                                    coliding_sha1 = roms_sha1_dic[coliding_name]
                                    table_str.append([
                                        'Collision', rom_nonmerged_location,
                                        str(rom['size']), rom['crc'], sha1
                                    ])
                                    table_str.append([
                                        'with', coliding_name, ' ',
                                        coliding_crc, coliding_sha1
                                    ])
                                else:
                                    crc_roms_dic[rom['crc']] = rom_nonmerged_location

            # >> Increment file count
            processed_files += 1
        update_number = (processed_files*100) // total_files
        pDialog.update(update_number, pdialog_line1, ' ')
        pDialog.close()
        log_debug('The SL have {0:,d} valid ROMs in total'.format(len(roms_sha1_dic)))
        log_debug('There are {0} CRC32 collisions'.format(num_collisions))

        # --- Write report ---
        slist = []
        slist.append('*** AML SL ROMs CRC32 hash collision report ***')
        slist.append('The Software Lists have {0:,d} valid ROMs in total'.format(len(roms_sha1_dic)))
        slist.append('There are {0} CRC32 collisions'.format(num_collisions))
        slist.append('')
        table_str_list = text_render_table_str(table_str)
        slist.extend(table_str_list)
        display_text_window('AML Software Lists CRC32 hash collision report', '\n'.join(slist))
        log_info('Writing "{0}"'.format(g_PATHS.REPORT_DEBUG_SL_COLLISIONS_PATH.getPath()))
        with open(g_PATHS.REPORT_DEBUG_SL_COLLISIONS_PATH.getPath(), 'w') as file:
            file.write('\n'.join(slist).encode('utf-8'))

    #
    # Export a MAME ROM DAT XML file with Logiqx format.
    # The DAT will be Merged, Split, Non-merged or Fully Non-merged same as the current
    # AML database.
    #
    elif which_utility == 'EXPORT_MAME_ROM_DAT':
        log_info('command_exec_utility() Initialising EXPORT_MAME_ROM_DAT ...')
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())

        # Choose output directory (writable directory).
        dir_path = kodi_dialog_get_wdirectory('Chose directory to write MAME ROMs DAT')
        if not dir_path: return
        out_dir_FN = FileName(dir_path)

        # Open databases.
        db_files = [
            ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['audit_roms', 'MAME ROM Audit', g_PATHS.ROM_AUDIT_DB_PATH.getPath()],
            ['roms_sha1_dic', 'MAME ROMs SHA1 dictionary', g_PATHS.SHA1_HASH_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # Write MAME ROM dat. Notifies the user if successful.
        mame_write_MAME_ROM_XML_DAT(g_PATHS, g_settings, control_dic, out_dir_FN, db_dic)

    elif which_utility == 'EXPORT_MAME_CHD_DAT':
        log_info('command_exec_utility() Initialising EXPORT_MAME_CHD_DAT ...')
        log_info('command_exec_utility() Initialising EXPORT_MAME_ROM_DAT ...')
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())

        # Choose output directory (writable directory).
        # DAT filename: AML 0.xxx ROMs (merged|split|non-merged|fully non-merged).xml
        dir_path = kodi_dialog_get_wdirectory('Chose directory to write MAME CHDs DAT')
        if not dir_path: return
        out_dir_FN = FileName(dir_path)

        # Open databases.
        db_files = [
            ['machines', 'MAME machines Main', g_PATHS.MAIN_DB_PATH.getPath()],
            ['render', 'MAME machines Render', g_PATHS.RENDER_DB_PATH.getPath()],
            ['audit_roms', 'MAME ROM Audit', g_PATHS.ROM_AUDIT_DB_PATH.getPath()],
        ]
        db_dic = fs_load_files(db_files)

        # Write MAME ROM dat. Notifies the user if successful.
        mame_write_MAME_CHD_XML_DAT(g_PATHS, g_settings, control_dic, out_dir_FN, db_dic)

    elif which_utility == 'EXPORT_SL_ROM_DAT':
        log_info('command_exec_utility() Initialising EXPORT_SL_ROM_DAT ...')
        kodi_dialog_OK('EXPORT_SL_ROM_DAT not implemented yet. Sorry.')

    elif which_utility == 'EXPORT_SL_CHD_DAT':
        log_info('command_exec_utility() Initialising EXPORT_SL_CHD_DAT ...')
        kodi_dialog_OK('EXPORT_SL_CHD_DAT not implemented yet. Sorry.')

    else:
        u = 'Utility "{0}" not found. This is a bug, please report it.'.format(which_utility)
        log_error(u)
        kodi_dialog_OK(u)

#
# Execute view reports.
#
def command_exec_report(which_report):
    log_debug('command_exec_report() which_report = "{0}" starting ...'.format(which_report))

    if which_report == 'VIEW_EXEC_OUTPUT':
        if not g_PATHS.MAME_OUTPUT_PATH.exists():
            kodi_dialog_OK('MAME output file not found. Execute MAME and try again.')
            return
        info_text = ''
        with open(g_PATHS.MAME_OUTPUT_PATH.getPath(), 'r') as myfile:
            info_text = myfile.read()
        display_text_window('MAME last execution output', info_text)

    # --- View database information and statistics stored in control dictionary ------------------
    elif which_report == 'VIEW_STATS_MAIN':
        if not g_PATHS.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_main_print_slist(g_settings, info_text, control_dic, __addon_version__)
        display_text_window('Database main statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_SCANNER':
        if not g_PATHS.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_scanner_print_slist(g_settings, info_text, control_dic)
        display_text_window('Scanner statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_AUDIT':
        if not g_PATHS.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_audit_print_slist(g_settings, info_text, control_dic, g_settings)
        display_text_window('Database information and statistics', '\n'.join(info_text))

    # --- All statistics ---
    elif which_report == 'VIEW_STATS_ALL':
        if not g_PATHS.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_main_print_slist(g_settings, info_text, control_dic, __addon_version__)
        info_text.append('')
        mame_stats_scanner_print_slist(g_settings, info_text, control_dic)
        info_text.append('')
        mame_stats_audit_print_slist(g_settings, info_text, control_dic, g_settings)
        display_text_window('Database full statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_WRITE_FILE':
        if not g_PATHS.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())

        # --- Generate stats string and remove Kodi colours ---
        info_text = []
        mame_stats_main_print_slist(g_settings, info_text, control_dic, __addon_version__)
        info_text.append('')
        mame_stats_scanner_print_slist(g_settings, info_text, control_dic)
        info_text.append('')
        mame_stats_audit_print_slist(g_settings, info_text, control_dic, g_settings)
        # text_remove_slist_colours(info_text)

        # --- Write file to disk and inform user ---
        log_info('Writing AML statistics report ...')
        log_info('File "{0}"'.format(g_PATHS.REPORT_STATS_PATH.getPath()))
        with open(g_PATHS.REPORT_STATS_PATH.getPath(), 'w') as f:
            text_remove_color_tags_slist(info_text)
            f.write('\n'.join(info_text).encode('utf-8'))
        kodi_notify('Exported AML statistic')

    # --- MAME scanner reports -------------------------------------------------------------------
    elif which_report == 'VIEW_SCANNER_MAME_ARCH_FULL':
        if not g_PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.exists():
            kodi_dialog_OK('Full MAME machines archives scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), 'r') as myfile:
            display_text_window('Full MAME machines archives scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_MAME_ARCH_HAVE':
        if not g_PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.exists():
            kodi_dialog_OK('Have MAME machines archives scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), 'r') as myfile:
            display_text_window('Have MAME machines archives scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_MAME_ARCH_MISS':
        if not g_PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME machines archives scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), 'r') as myfile:
            display_text_window('Missing MAME machines archives scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_MAME_ROM_LIST_MISS':
        if not g_PATHS.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME ROM ZIP list scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath(), 'r') as myfile:
            display_text_window('Missing MAME ROM ZIP list scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_MAME_SAM_LIST_MISS':
        if not g_PATHS.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME Sample ZIP list scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH.getPath(), 'r') as myfile:
            display_text_window('Missing MAME Sample ZIP list scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_MAME_CHD_LIST_MISS':
        if not g_PATHS.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME CHD list scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath(), 'r') as myfile:
            display_text_window('Missing MAME CHD list scanner report', myfile.read())

    # --- SL scanner reports ---------------------------------------------------------------------
    elif which_report == 'VIEW_SCANNER_SL_FULL':
        if not g_PATHS.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.exists():
            kodi_dialog_OK('Full Software Lists item archives scanner report not found. '
                           'Please scan SL ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), 'r') as myfile:
            display_text_window('Full Software Lists item archives scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_SL_HAVE':
        if not g_PATHS.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.exists():
            kodi_dialog_OK('Have Software Lists item archives scanner report not found. '
                           'Please scan SL ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), 'r') as myfile:
            display_text_window('Have Software Lists item archives scanner report', myfile.read())

    elif which_report == 'VIEW_SCANNER_SL_MISS':
        if not g_PATHS.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.exists():
            kodi_dialog_OK('Missing Software Lists item archives scanner report not found. '
                           'Please scan SL ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), 'r') as myfile:
            display_text_window('Missing Software Lists item archives scanner report', myfile.read())

    # --- Asset scanner reports ------------------------------------------------------------------
    elif which_report == 'VIEW_SCANNER_MAME_ASSETS':
        if not g_PATHS.REPORT_MAME_ASSETS_PATH.exists():
            kodi_dialog_OK('MAME asset report report not found. '
                           'Please scan MAME assets and try again.')
            return
        with open(g_PATHS.REPORT_MAME_ASSETS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME asset report', myfile.read())

    elif which_report == 'VIEW_SCANNER_SL_ASSETS':
            if not g_PATHS.REPORT_SL_ASSETS_PATH.exists():
                kodi_dialog_OK('Software Lists asset report not found. '
                               'Please scan Software List assets and try again.')
                return
            with open(g_PATHS.REPORT_SL_ASSETS_PATH.getPath(), 'r') as myfile:
                display_text_window('Software Lists asset report', myfile.read())

    # --- MAME audit reports ---------------------------------------------------------------------
    elif which_report == 'VIEW_AUDIT_MAME_FULL':
        if not g_PATHS.REPORT_MAME_AUDIT_FULL_PATH.exists():
            kodi_dialog_OK('MAME audit report (Full) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_FULL_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (Full)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_GOOD':
        if not g_PATHS.REPORT_MAME_AUDIT_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_BAD':
        if not g_PATHS.REPORT_MAME_AUDIT_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (Errors)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_ROM_GOOD':
        if not g_PATHS.REPORT_MAME_AUDIT_ROM_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROMs Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_ROM_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (ROMs Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_ROM_BAD':
        if not g_PATHS.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROM Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (ROM Errors)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_SAM_GOOD':
        if not g_PATHS.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (Samples Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (Samples Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_SAM_BAD':
        if not g_PATHS.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (Sample Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (Sample Errors)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_CHD_GOOD':
        if not g_PATHS.REPORT_MAME_AUDIT_CHD_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHDs Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_CHD_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (CHDs Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_MAME_CHD_BAD':
        if not g_PATHS.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHD Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (CHD Errors)', myfile.read())

    # --- SL audit reports -----------------------------------------------------------------------
    elif which_report == 'VIEW_AUDIT_SL_FULL':
        if not g_PATHS.REPORT_SL_AUDIT_FULL_PATH.exists():
            kodi_dialog_OK('SL audit report (Full) not found. '
                           'Please audit your SL ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_FULL_PATH.getPath(), 'r') as myfile:
            display_text_window('SL audit report (Full)', myfile.read())

    elif which_report == 'VIEW_AUDIT_SL_GOOD':
        if not g_PATHS.REPORT_SL_AUDIT_GOOD_PATH.exists():
            kodi_dialog_OK('SL audit report (Good) not found. '
                           'Please audit your SL ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('SL audit report (Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_SL_BAD':
        if not g_PATHS.REPORT_SL_AUDIT_ERRORS_PATH.exists():
            kodi_dialog_OK('SL audit report (Errors) not found. '
                           'Please audit your SL ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('SL audit report (Errors)', myfile.read())

    elif which_report == 'VIEW_AUDIT_SL_ROM_GOOD':
        if not g_PATHS.REPORT_SL_AUDIT_ROMS_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROM Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_ROMS_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (ROM Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_SL_ROM_BAD':
        if not g_PATHS.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROM Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (ROM Errors)', myfile.read())

    elif which_report == 'VIEW_AUDIT_SL_CHD_GOOD':
        if not g_PATHS.REPORT_SL_AUDIT_CHDS_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHD Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_CHDS_GOOD_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (CHD Good)', myfile.read())

    elif which_report == 'VIEW_AUDIT_SL_CHD_BAD':
        if not g_PATHS.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHD Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        with open(g_PATHS.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.getPath(), 'r') as myfile:
            display_text_window('MAME audit report (CHD Errors)', myfile.read())

    # --- Error ----------------------------------------------------------------------------------
    else:
        u = 'Report "{0}" not found. This is a bug, please report it.'.format(which_report)
        log_error(u)
        kodi_dialog_OK(u)

#
# Launch MAME machine. Syntax: $ mame <machine_name> [options]
# Example: $ mame dino
#
def run_machine(machine_name, location):
    log_info('run_machine() Launching MAME machine  "{0}"'.format(machine_name))
    log_info('run_machine() Launching MAME location "{0}"'.format(location))

    # --- Get paths ---
    mame_prog_FN = FileName(g_settings['mame_prog'])

    # --- Load databases ---
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if location == LOCATION_STANDARD:
        log_debug('Reading info from hashed DBs')
        machine = fs_get_machine_main_db_hash(g_PATHS, machine_name)
        assets = fs_get_machine_assets_db_hash(g_PATHS, machine_name)
    elif location == LOCATION_MAME_FAVS:
        log_debug('Reading info from MAME Favourites')
        fav_machines = fs_load_JSON_file_dic(g_PATHS.FAV_MACHINES_PATH.getPath())
        machine = fav_machines[machine_name]
        assets = machine['assets']
    elif location == LOCATION_MAME_MOST_PLAYED:
        log_debug('Reading info from MAME Most Played DB')
        most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
        machine = most_played_roms_dic[machine_name]
        assets = machine['assets']
    elif location == LOCATION_MAME_RECENT_PLAYED:
        log_debug('Reading info from MAME Recently Played DB')
        recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
        # >> Locate ROM in list by name
        machine_index = fs_locate_idx_by_MAME_name(recent_roms_list, machine_name)
        if machine_index < 0:
            a = 'Machine {0} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(machine_name))
            return
        machine = recent_roms_list[machine_index]
        assets = machine['assets']
    else:
        kodi_dialog_OK('Unknown location = "{0}". This is a bug, please report it.'.format(location))
        return

    # >> Check if ROM exist
    if not g_settings['rom_path']:
        kodi_dialog_OK('ROM directory not configured.')
        return
    ROM_path_FN = FileName(g_settings['rom_path'])
    if not ROM_path_FN.isdir():
        kodi_dialog_OK('ROM directory does not exist.')
        return
    ROM_FN = ROM_path_FN.pjoin(machine_name + '.zip')
    # if not ROM_FN.exists():
    #     kodi_dialog_OK('ROM "{0}" not found.'.format(ROM_FN.getBase()))
    #     return

    # >> Choose BIOS (only available for Favourite Machines)
    # Not implemented at the moment
    # if location and location == 'MAME_FAV' and len(machine['bios_name']) > 1:
    #     dialog = xbmcgui.Dialog()
    #     m_index = dialog.select('Select BIOS', machine['bios_desc'])
    #     if m_index < 0: return
    #     BIOS_name = machine['bios_name'][m_index]
    # else:
    #     BIOS_name = ''
    BIOS_name = ''

    # >> Launch machine using subprocess module
    (mame_dir, mame_exec) = os.path.split(mame_prog_FN.getPath())
    log_debug('run_machine() mame_prog_FN "{0}"'.format(mame_prog_FN.getPath()))
    log_debug('run_machine() mame_dir     "{0}"'.format(mame_dir))
    log_debug('run_machine() mame_exec    "{0}"'.format(mame_exec))
    log_debug('run_machine() machine_name "{0}"'.format(machine_name))
    log_debug('run_machine() BIOS_name    "{0}"'.format(BIOS_name))

    # --- Compute ROM recently played list ---
    # >> If the machine is already in the list remove it and place it on the first position.
    MAX_RECENT_PLAYED_ROMS = 100
    recent_rom = fs_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic)
    recent_roms_list = fs_load_JSON_file_list(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    # >> Machine names are unique in this list
    recent_roms_list = [machine for machine in recent_roms_list if machine_name != machine['name']]
    recent_roms_list.insert(0, recent_rom)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('run_machine() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
        log_debug('run_machine() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    fs_write_JSON_file(g_PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if recent_rom['name'] in most_played_roms_dic:
        rom_name = recent_rom['name']
        most_played_roms_dic[rom_name]['launch_count'] += 1
    else:
        # >> Add field launch_count to recent_rom to count how many times have been launched.
        recent_rom['launch_count'] = 1
        most_played_roms_dic[recent_rom['name']] = recent_rom
    fs_write_JSON_file(g_PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)

    # --- Build final arguments to launch MAME ---
    # arg_list = [mame_prog_FN.getPath(), '-window', machine_name]
    arg_list = [mame_prog_FN.getPath(), machine_name]
    if BIOS_name:
        arg_list.extend(['-bios', BIOS_name])
    log_info('arg_list = {0}'.format(arg_list))

    # --- User notification ---
    if g_settings['display_launcher_notify']:
        kodi_notify('Launching MAME machine "{0}"'.format(machine_name))
    if DISABLE_MAME_LAUNCHING:
        log_info('run_machine() MAME launching disabled. Exiting function.')
        return

    # --- Run MAME ---
    run_before_execution()
    run_process(g_PATHS, arg_list, mame_dir)
    run_after_execution()
    # Refresh list so Most Played and Recently played get updated.
    kodi_refresh_container()
    log_info('run_machine() Exiting function.')

#
# Launch a SL machine. See http://docs.mamedev.org/usingmame/usingmame.html
# Complex syntax: $ mame <system> <media> <software> [options]
# Easy syntax: $ mame <system> <software> [options]
# Valid example: $ mame smspal -cart sonic
#
# Software list <part> tag has an 'interface' attribute that tells how to virtually plug the
# cartridge/cassete/disk/etc. into the MAME <device> with same 'interface' attribute. The
# <media> argument in the command line is the <device> <instance> 'name' attribute.
#
# Launching cases:
#   A) Machine has only one device (defined by a <device> tag) with a valid <instance> and
#      SL ROM has only one part (defined by a <part> tag).
#      Valid examples:$ mame smspal -cart sonic
#      Launch as: $ mame machine_name -part_attrib_name SL_ROM_name
#
# <device type="cartridge" tag="slot" interface="sms_cart">
#   <instance name="cartridge" briefname="cart"/>
#   <extension name="bin"/>
#   <extension name="sms"/>
# </device>
# <software name="sonic">
#   <part name="cart" interface="sms_cart">
#     <!-- PCB info based on SMS Power -->
#     <feature name="pcb" value="171-5507" />
#     <feature name="ic1" value="MPR-14271-F" />
#     <dataarea name="rom" size="262144">
#       <rom name="mpr-14271-f.ic1" size="262144" crc="b519e833" sha1="6b9..." offset="000000" />
#     </dataarea>
#   </part>
# </software>
#
#   B) Machine has only one device with a valid <instance> and SL ROM has multiple parts.
#      In this case, user should choose which part to plug.
#      Currently not implemented and launch using easy syntax.
#      Valid examples: 
#      Launch as: $ mame machine_name -part_attrib_name SL_ROM_name
#
#   C) Machine has two or more devices with a valid <instance> and SL ROM has only one part.
#      Traverse the machine devices until there is a match of the <part> interface attribute 
#      with the <machine> interface attribute. After the match is found, check also that
#      SL ROM <part> name attribute matches with machine <device> <intance> briefname attribute.
#      Valid examples:
#        MSX2 cartridge vampkill (in msx2_cart.xml) with MSX machine.
#        vampkill is also in msx_flop SL.xml. MSX2 machines always have two or more interfaces.
#        $ mame hbf700p -cart vampkill
#      Launch as: $ mame machine_name -part_attrib_name SL_ROM_name
#
#   D) Machine has two or more devices with a valid <instance> and SL ROM has two or more parts.
#      In this case it is not clear how to launch the machine.
#      Not implemented and launch using easy syntax.
#
# Most common cases are A) and C).
#
def run_SL_machine(SL_name, SL_ROM_name, location):
    SL_LAUNCH_WITH_MEDIA = 100
    SL_LAUNCH_NO_MEDIA   = 200
    log_info('run_SL_machine() Launching SL machine (location = {0}) ...'.format(location))
    log_info('run_SL_machine() SL_name     "{0}"'.format(SL_name))
    log_info('run_SL_machine() SL_ROM_name "{0}"'.format(SL_ROM_name))

    # --- Get paths ---
    mame_prog_FN = FileName(g_settings['mame_prog'])

    # --- Get a list of launch machine <devices> and SL ROM <parts> ---
    # --- Load SL ROMs and SL assets databases ---
    control_dic = fs_load_JSON_file_dic(g_PATHS.MAIN_CONTROL_PATH.getPath())
    if location == LOCATION_STANDARD:
        # >> Load DBs
        log_info('run_SL_machine() SL ROM is in Standard Location')
        SL_catalog_dic = fs_load_JSON_file_dic(g_PATHS.SL_INDEX_PATH.getPath())
        SL_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json')
        log_info('run_SL_machine() SL ROMs JSON "{0}"'.format(SL_DB_FN.getPath()))
        SL_ROMs = fs_load_JSON_file_dic(SL_DB_FN.getPath())
        SL_asset_DB_FN = g_PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json')
        SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
        # >> Get ROM and assets
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = SL_ROMs[SL_ROM_name]
        SL_assets = SL_asset_dic[SL_ROM_name]
        part_list = SL_ROM['parts']
        # >> Launch machine
        launch_machine_name = ''
        launch_machine_desc = ''
    elif location == LOCATION_SL_FAVS:
        # >> Load DBs
        log_info('run_SL_machine() SL ROM is in Favourites')
        fav_SL_roms = fs_load_JSON_file_dic(g_PATHS.FAV_SL_ROMS_PATH.getPath())
        # >> Get ROM and assets
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = fav_SL_roms[SL_fav_DB_key]
        SL_assets = SL_ROM['assets']
        part_list = fav_SL_roms[SL_fav_DB_key]['parts']
        # >> Launch machine
        launch_machine_name = fav_SL_roms[SL_fav_DB_key]['launch_machine']
        launch_machine_desc = '[ Not available ]'
    elif location == LOCATION_SL_MOST_PLAYED:
        log_debug('Reading info from MAME Most Played DB')
        most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = most_played_roms_dic[SL_fav_DB_key]
        SL_assets = SL_ROM['assets']
        part_list = most_played_roms_dic[SL_fav_DB_key]['parts']
        launch_machine_name = most_played_roms_dic[SL_fav_DB_key]['launch_machine']
        launch_machine_desc = '[ Not available ]'
    elif location == LOCATION_SL_RECENT_PLAYED:
        log_debug('Reading info from MAME Recently Played DB')
        recent_roms_list = fs_load_JSON_file_list(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
        machine_index = fs_locate_idx_by_SL_item_name(recent_roms_list, SL_name, SL_ROM_name)
        if machine_index < 0:
            a = 'SL Item {0} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(SL_fav_DB_key))
            return
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = recent_roms_list[machine_index]
        SL_assets = SL_ROM['assets']
        part_list = recent_roms_list[machine_index]['parts']
        launch_machine_name = recent_roms_list[machine_index]['launch_machine']
        launch_machine_desc = '[ Not available ]'
    else:
        kodi_dialog_OK('Unknown location = "{0}". This is a bug, please report it.'.format(location))
        return
    log_info('run_SL_machine() launch_machine_name = "{0}"'.format(launch_machine_name))
    log_info('run_SL_machine() launch_machine_desc = "{0}"'.format(launch_machine_desc))

    # --- Load SL machines ---
    SL_machines_dic = fs_load_JSON_file_dic(g_PATHS.SL_MACHINES_PATH.getPath())
    SL_machine_list = SL_machines_dic[SL_name]
    if not launch_machine_name:
        # >> Get a list of machines that can launch this SL ROM. User chooses in a select dialog
        log_info('run_SL_machine() User selecting SL run machine ...')
        SL_machine_names_list = []
        SL_machine_desc_list  = []
        SL_machine_devices    = []
        for SL_machine in sorted(SL_machine_list):
            SL_machine_names_list.append(SL_machine['machine'])
            SL_machine_desc_list.append(SL_machine['description'])
            SL_machine_devices.append(SL_machine['devices'])
        m_index = xbmcgui.Dialog().select('Select machine', SL_machine_desc_list)
        if m_index < 0: return
        launch_machine_name    = SL_machine_names_list[m_index]
        launch_machine_desc    = SL_machine_desc_list[m_index]
        launch_machine_devices = SL_machine_devices[m_index]
        log_info('run_SL_machine() User chose machine "{0}" ({1})'.format(launch_machine_name, launch_machine_desc))
    else:
        # >> User configured a machine to launch this SL item. Find the machine in the machine list.
        log_info('run_SL_machine() Searching configured SL item running machine ...')
        machine_found = False
        for SL_machine in SL_machine_list:
            if SL_machine['machine'] == launch_machine_name:
                selected_SL_machine = SL_machine
                machine_found = True
                break
        if machine_found:
            log_info('run_SL_machine() Found machine "{0}"'.format(launch_machine_name))
            launch_machine_desc    = SL_machine['description']
            launch_machine_devices = SL_machine['devices']
        else:
            log_error('run_SL_machine() Machine "{0}" not found'.format(launch_machine_name))
            log_error('run_SL_machine() Aborting launch')
            kodi_dialog_OK('Machine "{0}" not found. Aborting launch.'.format(launch_machine_name))
            return

    # --- DEBUG ---
    log_info('run_SL_machine() Machine "{0}" has {1} interfaces'.format(launch_machine_name, len(launch_machine_devices)))
    log_info('run_SL_machine() SL ROM  "{0}" has {1} parts'.format(SL_ROM_name, len(part_list)))
    for device_dic in launch_machine_devices:
        u = '<device type="{1}" interface="{0}">'.format(device_dic['att_type'], device_dic['att_interface'])
        log_info(u)
    for part_dic in part_list:
        u = '<part name="{1}" interface="{0}">'.format(part_dic['name'], part_dic['interface'])
        log_info(u)

    # --- Select media depending on SL launching case ---
    num_machine_interfaces = len(launch_machine_devices)
    num_SL_ROM_parts = len(part_list)

    # >> Error
    if num_machine_interfaces == 0:
        kodi_dialog_OK('Machine has no inferfaces! Aborting launch.')
        return
    if num_SL_ROM_parts == 0:
        kodi_dialog_OK('SL ROM has no parts! Aborting launch.')
        return

    # >> Case A
    elif num_machine_interfaces == 1 and num_SL_ROM_parts == 1:
        log_info('run_SL_machine() Launch case A)')
        launch_case = SL_LAUNCH_CASE_A
        media_name = launch_machine_devices[0]['instance']['name']
        sl_launch_mode = SL_LAUNCH_WITH_MEDIA

    # >> Case B
    #    User chooses media to launch?
    elif num_machine_interfaces == 1 and num_SL_ROM_parts > 1:
        log_info('run_SL_machine() Launch case B)')
        launch_case = SL_LAUNCH_CASE_B
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    # >> Case C
    elif num_machine_interfaces > 1 and num_SL_ROM_parts == 1:
        log_info('run_SL_machine() Launch case C)')
        launch_case = SL_LAUNCH_CASE_C
        m_interface_found = False
        for device in launch_machine_devices:
            if device['att_interface'] == part_list[0]['interface']:
                media_name = device['instance']['name']
                m_interface_found = True
                break
        if not m_interface_found:
            kodi_dialog_OK('SL launch case C), not machine interface found! Aborting launch.')
            return
        log_info('run_SL_machine() Matched machine device interface "{0}" '.format(device['att_interface']) +
                 'to SL ROM part "{0}"'.format(part_list[0]['interface']))
        sl_launch_mode = SL_LAUNCH_WITH_MEDIA

    # >> Case D.
    # >> User chooses media to launch?
    elif num_machine_interfaces > 1 and num_SL_ROM_parts > 1:
        log_info('run_SL_machine() Launch case D)')
        launch_case = SL_LAUNCH_CASE_D
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    else:
        log_info(unicode(machine_interfaces))
        log_warning('run_SL_machine() Logical error in SL launch case.')
        launch_case = SL_LAUNCH_CASE_ERROR
        kodi_dialog_OK('Logical error in SL launch case. This is a bug, please report it.')
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    # >> Display some DEBUG information.
    kodi_dialog_OK('Launch case {0}. '.format(launch_case) +
                   'Machine has {0} device interface/s and '.format(num_machine_interfaces) +
                   'SL ROM has {0} part/s. '.format(num_SL_ROM_parts) + 
                   'Media name is "{0}"'.format(media_name))

    # --- Launch machine using subprocess module ---
    (mame_dir, mame_exec) = os.path.split(mame_prog_FN.getPath())
    log_debug('run_SL_machine() mame_prog_FN "{0}"'.format(mame_prog_FN.getPath()))    
    log_debug('run_SL_machine() mame_dir     "{0}"'.format(mame_dir))
    log_debug('run_SL_machine() mame_exec    "{0}"'.format(mame_exec))
    log_debug('run_SL_machine() launch_machine_name "{0}"'.format(launch_machine_name))
    log_debug('run_SL_machine() launch_machine_desc "{0}"'.format(launch_machine_desc))
    log_debug('run_SL_machine() media_name          "{0}"'.format(media_name))

    # --- Compute ROM recently played list ---
    # >> If the machine is already in the list remove it and place it on the first position.
    MAX_RECENT_PLAYED_ROMS = 100
    recent_ROM = fs_get_SL_Favourite(SL_name, SL_ROM_name, SL_ROM, SL_assets, control_dic)
    recent_roms_list = fs_load_JSON_file_list(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
    # >> Machine names are unique in this list
    recent_roms_list = [item for item in recent_roms_list if SL_fav_DB_key != item['SL_DB_key']]
    recent_roms_list.insert(0, recent_ROM)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('run_SL_machine() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
        log_debug('run_SL_machine() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    fs_write_JSON_file(g_PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms_dic = fs_load_JSON_file_dic(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
    if SL_fav_DB_key in most_played_roms_dic:
        most_played_roms_dic[SL_fav_DB_key]['launch_count'] += 1
    else:
        # >> Add field launch_count to recent_ROM to count how many times have been launched.
        recent_ROM['launch_count'] = 1
        most_played_roms_dic[SL_fav_DB_key] = recent_ROM
    fs_write_JSON_file(g_PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)

    # --- Build MAME arguments ---
    if sl_launch_mode == SL_LAUNCH_WITH_MEDIA:
        arg_list = [mame_prog_FN.getPath(), launch_machine_name, '-{0}'.format(media_name), SL_ROM_name]
    elif sl_launch_mode == SL_LAUNCH_NO_MEDIA:
        arg_list = [mame_prog_FN.getPath(), launch_machine_name, '{0}:{1}'.format(SL_name, SL_ROM_name)]
    else:
        kodi_dialog_OK('Unknown sl_launch_mode = {0}. This is a bug, please report it.'.format(sl_launch_mode))
        return
    log_info('arg_list = {0}'.format(arg_list))

    # --- User notification ---
    if g_settings['display_launcher_notify']:
        kodi_notify('Launching MAME SL item "{0}"'.format(SL_ROM_name))
    if DISABLE_MAME_LAUNCHING:
        log_info('run_machine() MAME launching disabled. Exiting function.')
        return

    # --- Run MAME ---
    run_before_execution()
    run_process(g_PATHS, arg_list, mame_dir)
    run_after_execution()
    # Refresh list so Most Played and Recently played get updated.
    kodi_refresh_container()
    log_info('run_SL_machine() Exiting function.')

def run_before_execution():
    global g_flag_kodi_was_playing
    global g_flag_kodi_audio_suspended
    global g_flag_kodi_toggle_fullscreen
    log_info('run_before_execution() Function BEGIN ...')

    # --- Stop/Pause Kodi mediaplayer if requested in settings ---
    # >> id="media_state_action" default="0" values="Stop|Pause|Keep playing"
    g_flag_kodi_was_playing = False
    media_state_action = g_settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Keep playing'][media_state_action]
    a = 'run_before_execution() media_state_action is "{0}" ({1})'
    log_verb(a.format(media_state_str, media_state_action))
    kodi_is_playing = xbmc.getCondVisibility('Player.HasMedia')
    if media_state_action == 0 and kodi_is_playing:
        log_verb('run_before_execution() Executing built-in PlayerControl(stop)')
        xbmc.executebuiltin('PlayerControl(stop)')
        xbmc.sleep(100)
        g_flag_kodi_was_playing = True
    elif media_state_action == 1 and kodi_is_playing:
        log_verb('run_before_execution() Executing built-in PlayerControl(pause)')
        xbmc.executebuiltin('PlayerControl(pause)')
        xbmc.sleep(100)
        g_flag_kodi_was_playing = True

    # --- Force audio suspend if requested in "Settings" --> "Advanced"
    # >> See http://forum.kodi.tv/showthread.php?tid=164522
    g_flag_kodi_audio_suspended = False
    if g_settings['suspend_audio_engine']:
        log_verb('run_before_execution() Suspending Kodi audio engine')
        xbmc.audioSuspend()
        xbmc.enableNavSounds(False)
        xbmc.sleep(100)
        g_flag_kodi_audio_suspended = True
    else:
        log_verb('run_before_execution() DO NOT suspend Kodi audio engine')

    # --- Force joystick suspend if requested in "Settings" --> "Advanced"
    # NOT IMPLEMENTED YET.
    # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
    # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
    # >> See https://forum.kodi.tv/showthread.php?tid=313615

    # --- Toggle Kodi windowed/fullscreen if requested ---
    g_flag_kodi_toggle_fullscreen = False
    if g_settings['toggle_window']:
        log_verb('run_before_execution() Toggling Kodi from fullscreen to window')
        kodi_toogle_fullscreen()
        g_flag_kodi_toggle_fullscreen = True
    else:
        log_verb('run_before_execution() Toggling Kodi fullscreen/windowed DISABLED')

    # --- Pause Kodi execution some time ---
    delay_tempo_ms = g_settings['delay_tempo']
    log_verb('run_before_execution() Pausing {0} ms'.format(delay_tempo_ms))
    xbmc.sleep(delay_tempo_ms)
    log_debug('run_before_execution() function ENDS')

def run_process(g_PATHS, arg_list, mame_dir):
    log_info('run_process() Function BEGIN ...')

    # --- Prevent a console window to be shown in Windows. Not working yet! ---
    if sys.platform == 'win32':
        log_info('run_process() Platform is win32. Creating _info structure')
        _info = subprocess.STARTUPINFO()
        _info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        # See https://msdn.microsoft.com/en-us/library/ms633548(v=vs.85).aspx
        # See https://docs.python.org/2/library/subprocess.html#subprocess.STARTUPINFO
        # >> SW_HIDE = 0
        # >> Does not work: MAME console window is not shown, graphical window not shonw either,
        # >> process run in background.
        # _info.wShowWindow = subprocess.SW_HIDE
        # >> SW_SHOWMINIMIZED = 2
        # >> Both MAME console and graphical window minimized.
        # _info.wShowWindow = 2
        # >> SW_SHOWNORMAL = 1
        # >> MAME console window is shown, MAME graphical window on top, Kodi on bottom.
        _info.wShowWindow = 1
    else:
        log_info('run_process() _info is None')
        _info = None

    # --- Run MAME ---
    with open(g_PATHS.MAME_OUTPUT_PATH.getPath(), 'wb') as f:
        p = subprocess.Popen(arg_list, cwd = mame_dir, startupinfo = _info,
                             stdout = f, stderr = subprocess.STDOUT)
    p.wait()
    log_debug('run_process() function ENDS')

def run_after_execution():
    log_info('run_after_execution() Function BEGIN ...')

    # --- Stop Kodi some time ---
    delay_tempo_ms = g_settings['delay_tempo']
    log_verb('run_after_execution() Pausing {0} ms'.format(delay_tempo_ms))
    xbmc.sleep(delay_tempo_ms)

    # --- Toggle Kodi windowed/fullscreen if requested ---
    if g_flag_kodi_toggle_fullscreen:
        log_verb('run_after_execution() Toggling Kodi fullscreen')
        kodi_toogle_fullscreen()
    else:
        log_verb('run_after_execution() Toggling Kodi fullscreen DISABLED')

    # --- Resume joystick engine if it was suspended ---
    # NOT IMPLEMENTED

    # --- Resume audio engine if it was suspended ---
    # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
    # Also produces this in Kodi's log:
    # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
    #   ERROR: ActiveAE::Resume - failed to init
    if g_flag_kodi_audio_suspended:
        log_verb('run_after_execution() Kodi audio engine was suspended before launching')
        log_verb('run_after_execution() Resuming Kodi audio engine')
        xbmc.audioResume()
        xbmc.enableNavSounds(True)
        xbmc.sleep(100)
    else:
        log_verb('run_after_execution() DO NOT resume Kodi audio engine')

    # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
    # >> id="media_state_action" default="0" values="Stop|Pause|Keep playing"
    media_state_action = g_settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Keep playing'][media_state_action]
    a = 'run_after_execution() media_state_action is "{0}" ({1})'
    log_verb(a.format(media_state_str, media_state_action))
    log_verb('run_after_execution() g_flag_kodi_was_playing is {0}'.format(g_flag_kodi_was_playing))
    if g_flag_kodi_was_playing and media_state_action == 1:
        log_verb('run_after_execution() Executing built-in PlayerControl(play)')
        xbmc.executebuiltin('PlayerControl(play)')
    log_debug('run_after_execution() Function ENDS')

# ---------------------------------------------------------------------------------------------
# Misc functions
# ---------------------------------------------------------------------------------------------
def display_text_window(window_title, info_text):
    xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
    dialog = xbmcgui.Dialog()
    dialog.textviewer(window_title, info_text)
    xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

# List of sorting methods here http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcplugin.html#-setSetting
def set_Kodi_unsorted_method():
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

def set_Kodi_all_sorting_methods():
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

def set_Kodi_all_sorting_methods_and_size():
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_SIZE)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

# ---------------------------------------------------------------------------------------------
# Misc URL building functions
# ---------------------------------------------------------------------------------------------
# NOTE '&' must be scaped to '%26' in all URLs
#
# Functions used in xbmcplugin.addDirectoryItem()
#
def misc_url(command):
    command_escaped = command.replace('&', '%26')

    return '{0}?command={1}'.format(g_base_url, command_escaped)

def misc_url_1_arg(arg_name, arg_value):
    arg_value_escaped = arg_value.replace('&', '%26')

    return '{0}?{1}={2}'.format(g_base_url, arg_name, arg_value_escaped)

def misc_url_2_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')

    return '{0}?{1}={2}&{3}={4}'.format(
        g_base_url, arg_name_1, arg_value_1_escaped, arg_name_2, arg_value_2_escaped)

def misc_url_3_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                          arg_name_3, arg_value_3):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')
    arg_value_3_escaped = arg_value_3.replace('&', '%26')

    return '{0}?{1}={2}&{3}={4}&{5}={6}'.format(
        g_base_url,
        arg_name_1, arg_value_1_escaped, arg_name_2, arg_value_2_escaped,
        arg_name_3, arg_value_3_escaped)

def misc_url_4_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                          arg_name_3, arg_value_3, arg_name_4, arg_value_4):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')
    arg_value_3_escaped = arg_value_3.replace('&', '%26')
    arg_value_4_escaped = arg_value_4.replace('&', '%26')

    return '{0}?{1}={2}&{3}={4}&{5}={6}&{7}={8}'.format(
        g_base_url,
        arg_name_1, arg_value_1_escaped, arg_name_2, arg_value_2_escaped,
        arg_name_3, arg_value_3_escaped,arg_name_4, arg_value_4_escaped)

#
# Functions used in context menus, function listitem.addContextMenuItems()
#
def misc_url_RunPlugin(command):
    command_esc = command.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?command={1})'.format(g_base_url, command_esc)

def misc_url_1_arg_RunPlugin(arg_n_1, arg_v_1):
    arg_v_1_esc = arg_v_1.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2})'.format(g_base_url, arg_n_1, arg_v_1_esc)

def misc_url_2_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4})'.format(
        g_base_url, arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc)

def misc_url_3_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2, arg_n_3, arg_v_3):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')
    arg_v_3_esc = arg_v_3.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4}&{5}={6})'.format(
        g_base_url, arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc, arg_n_3, arg_v_3_esc)

def misc_url_4_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2, 
                              arg_n_3, arg_v_3, arg_n_4, arg_v_4):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')
    arg_v_3_esc = arg_v_3.replace('&', '%26')
    arg_v_4_esc = arg_v_4.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4}&{5}={6}&{7}={8})'.format(
        g_base_url,
        arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc, arg_n_3, arg_v_3_esc, arg_n_4, arg_v_4_esc)
