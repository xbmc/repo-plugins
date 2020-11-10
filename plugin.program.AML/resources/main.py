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

# Advanced MAME Launcher main script file.

# First include modules in this package. 
# Then include Kodi modules.
# Finally include standard library modules.

# --- Modules/packages in this plugin ---
# Addon module dependencies:
#   main <-- mame <-- disk_IO <-- assets, misc, utils, constants
#   mame <-- filters <-- misc, utils, constants
#   manuals <- misc, utils, constants
#   graphics <- misc, utils, constants
from .constants import *
from .assets import *
from .utils import *
from .db import *
from .filters import *
from .mame import *
from .manuals import *
from .graphics import *

# --- Kodi stuff ---
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# --- Python standard library ---
import copy
import datetime
import os
import subprocess
if ADDON_RUNNING_PYTHON_2:
    import urlparse
elif ADDON_RUNNING_PYTHON_3:
    import urllib.parse
else:
    raise TypeError('Undefined Python runtime version.')

# --- Plugin database indices ---
# _PATH is a filename | _DIR is a directory
class Configuration:
    def __init__(self):
        # --- Kodi-related variables and data ---
        # Addon object (used to access settings).
        self.__addon__         = xbmcaddon.Addon()
        self.__addon_id__      = self.__addon__.getAddonInfo('id')
        self.__addon_name__    = self.__addon__.getAddonInfo('name')
        self.__addon_version__ = self.__addon__.getAddonInfo('version')
        self.__addon_author__  = self.__addon__.getAddonInfo('author')
        self.__addon_profile__ = self.__addon__.getAddonInfo('profile')
        self.__addon_type__    = self.__addon__.getAddonInfo('type')

        # --- File and directory names ---
        self.HOME_DIR         = FileName('special://home')
        self.PROFILE_DIR      = FileName('special://profile')
        self.ADDON_CODE_DIR   = self.HOME_DIR.pjoin('addons/' + self.__addon_id__)
        self.ADDON_DATA_DIR   = self.PROFILE_DIR.pjoin('addon_data/' + self.__addon_id__)
        self.ICON_FILE_PATH   = self.ADDON_CODE_DIR.pjoin('media/icon.png')
        self.FANART_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/fanart.jpg')

        # MAME stdout/strderr files.
        self.MAME_STDOUT_PATH     = self.ADDON_DATA_DIR.pjoin('log_stdout.log')
        self.MAME_STDERR_PATH     = self.ADDON_DATA_DIR.pjoin('log_stderr.log')
        self.MAME_STDOUT_VER_PATH = self.ADDON_DATA_DIR.pjoin('log_version_stdout.log')
        self.MAME_STDERR_VER_PATH = self.ADDON_DATA_DIR.pjoin('log_version_stderr.log')
        self.MAME_OUTPUT_PATH     = self.ADDON_DATA_DIR.pjoin('log_output.log')
        self.MONO_FONT_PATH       = self.ADDON_CODE_DIR.pjoin('fonts/Inconsolata.otf')
        self.CUSTOM_FILTER_PATH   = self.ADDON_CODE_DIR.pjoin('filters/AML-MAME-filters.xml')

        # Addon control databases.
        self.MAME_XML_PATH = self.ADDON_DATA_DIR.pjoin('MAME.xml')
        self.MAME_XML_CONTROL_PATH = self.ADDON_DATA_DIR.pjoin('XML_control_MAME.json')
        self.MAME_2003_PLUS_XML_CONTROL_PATH = self.ADDON_DATA_DIR.pjoin('XML_control_MAME_2003_plus.json')
        self.MAIN_CONTROL_PATH = self.ADDON_DATA_DIR.pjoin('MAME_control_dic.json')
        # Main MAME databases.
        self.MAIN_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_DB_main.json')
        self.ROMS_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_DB_roms.json')
        self.DEVICES_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_DB_devices.json')
        self.SHA1_HASH_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_DB_SHA1_hashes.json')
        self.MAIN_PCLONE_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_DB_pclone_dic.json')
        # Databases used for rendering.
        self.RENDER_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_renderdb.json')
        self.ASSET_DB_PATH = self.ADDON_DATA_DIR.pjoin('MAME_assetdb.json')

        # Audit and ROM Set databases.
        self.ROM_AUDIT_DB_PATH = self.ADDON_DATA_DIR.pjoin('ROM_Audit_DB.json')
        self.ROM_SET_MACHINE_FILES_DB_PATH = self.ADDON_DATA_DIR.pjoin('ROM_Set_machine_files.json')

        # DAT indices and databases.
        self.HISTORY_IDX_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_History_index.json')
        self.HISTORY_DB_PATH   = self.ADDON_DATA_DIR.pjoin('DAT_History_DB.json')
        self.MAMEINFO_IDX_PATH = self.ADDON_DATA_DIR.pjoin('DAT_MAMEInfo_index.json')
        self.MAMEINFO_DB_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_MAMEInfo_DB.json')
        self.GAMEINIT_IDX_PATH = self.ADDON_DATA_DIR.pjoin('DAT_GameInit_index.json')
        self.GAMEINIT_DB_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_GameInit_DB.json')
        self.COMMAND_IDX_PATH  = self.ADDON_DATA_DIR.pjoin('DAT_Command_index.json')
        self.COMMAND_DB_PATH   = self.ADDON_DATA_DIR.pjoin('DAT_Command_DB.json')

        # Most played and Recently played
        self.MAME_MOST_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('most_played_MAME.json')
        self.MAME_RECENT_PLAYED_FILE_PATH = self.ADDON_DATA_DIR.pjoin('recently_played_MAME.json')
        self.SL_MOST_PLAYED_FILE_PATH     = self.ADDON_DATA_DIR.pjoin('most_played_SL.json')
        self.SL_RECENT_PLAYED_FILE_PATH   = self.ADDON_DATA_DIR.pjoin('recently_played_SL.json')

        # Disabled. Now there are global properties for this.
        # self.MAIN_PROPERTIES_PATH = self.ADDON_DATA_DIR.pjoin('MAME_properties.json')

        # ROM cache.
        self.CACHE_DIR = self.ADDON_DATA_DIR.pjoin('cache')
        self.CACHE_INDEX_PATH = self.ADDON_DATA_DIR.pjoin('MAME_cache_index.json')

        # Catalogs.
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

        # Distributed hashed database.
        self.MAIN_DB_HASH_DIR      = self.ADDON_DATA_DIR.pjoin('hash')
        self.ROMS_DB_HASH_DIR      = self.ADDON_DATA_DIR.pjoin('hash_ROM')
        self.ROM_AUDIT_DB_HASH_DIR = self.ADDON_DATA_DIR.pjoin('hash_ROM_Audit')

        # MAME custom filters.
        self.FILTERS_DB_DIR     = self.ADDON_DATA_DIR.pjoin('filters')
        self.FILTERS_INDEX_PATH = self.ADDON_DATA_DIR.pjoin('Filter_index.json')

        # Software Lists.
        self.SL_DB_DIR             = self.ADDON_DATA_DIR.pjoin('SoftwareLists')
        self.SL_NAMES_PATH         = self.ADDON_DATA_DIR.pjoin('SoftwareLists_names.json')
        self.SL_INDEX_PATH         = self.ADDON_DATA_DIR.pjoin('SoftwareLists_index.json')
        self.SL_MACHINES_PATH      = self.ADDON_DATA_DIR.pjoin('SoftwareLists_machines.json')
        self.SL_PCLONE_DIC_PATH    = self.ADDON_DATA_DIR.pjoin('SoftwareLists_pclone_dic.json')
        # Disabled. Not used at the moment.
        # self.SL_MACHINES_PROP_PATH = self.ADDON_DATA_DIR.pjoin('SoftwareLists_properties.json')

        # Favourites.
        self.FAV_MACHINES_PATH = self.ADDON_DATA_DIR.pjoin('Favourite_Machines.json')
        self.FAV_SL_ROMS_PATH  = self.ADDON_DATA_DIR.pjoin('Favourite_SL_ROMs.json')

        # ROM/CHD scanner reports. These reports show missing ROM/CHDs only.
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

        # Asset scanner reports. These reports show have and missing assets.
        self.REPORT_MAME_ASSETS_PATH = self.REPORTS_DIR.pjoin('Assets_MAME.txt')
        self.REPORT_SL_ASSETS_PATH   = self.REPORTS_DIR.pjoin('Assets_SL.txt')

        # Statistics report.
        self.REPORT_STATS_PATH = self.REPORTS_DIR.pjoin('Statistics.txt')

        # Audit report.
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

        # Custom filters report.
        self.REPORT_CF_XML_SYNTAX_PATH = self.REPORTS_DIR.pjoin('Custom_filter_XML_check.txt')
        self.REPORT_CF_DB_BUILD_PATH   = self.REPORTS_DIR.pjoin('Custom_filter_database_report.txt')
        self.REPORT_CF_HISTOGRAMS_PATH = self.REPORTS_DIR.pjoin('Custom_filter_histogram.txt')

        # DEBUG data
        self.REPORT_DEBUG_MAME_MACHINE_DATA_PATH = self.REPORTS_DIR.pjoin('debug_MAME_machine_data.txt')
        self.REPORT_DEBUG_MAME_MACHINE_ROM_DATA_PATH = self.REPORTS_DIR.pjoin('debug_MAME_machine_ROM_DB_data.txt')
        self.REPORT_DEBUG_MAME_MACHINE_AUDIT_DATA_PATH = self.REPORTS_DIR.pjoin('debug_MAME_machine_Audit_DB_data.txt')
        self.REPORT_DEBUG_SL_ITEM_DATA_PATH = self.REPORTS_DIR.pjoin('debug_SL_item_data.txt')
        self.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH = self.REPORTS_DIR.pjoin('debug_SL_item_ROM_DB_data.txt')
        self.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH = self.REPORTS_DIR.pjoin('debug_SL_item_Audit_DB_data.txt')
        self.REPORT_DEBUG_MAME_COLLISIONS_PATH = self.REPORTS_DIR.pjoin('debug_MAME_collisions.txt')
        self.REPORT_DEBUG_SL_COLLISIONS_PATH = self.REPORTS_DIR.pjoin('debug_SL_collisions.txt')

        # --- Former global variables ---
        self.settings = {}
        self.base_url = ''
        self.addon_handle = 0
        self.content_type = ''
        # Map of AEL artwork types to Kodi standard types,
        self.mame_icon = ''
        self.mame_fanart = ''
        self.SL_icon = ''
        self.SL_fanart = ''

# --- Global variables ---
# Use functional programming as much as possible and avoid global variables.
# g_base_url must be a global variable because it is used in the misc_url_*() functions.
g_base_url = ''
# Module loading time. This variable is read only (only modified here).
g_time_str = text_type(datetime.datetime.now())

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin(addon_argv):
    global g_base_url

    # Unify all global variables into an object to simplify function calling.
    # Keep compatibility with legacy code until all addon has been refactored.
    # Instead of using a global variable create an instance of the cfg object here
    # and pass as first argument of all functions. Long live to functional programming!
    cfg = Configuration()

    # --- Initialize log system ---
    # Force DEBUG log level for development.
    # Place it before setting loading so settings can be dumped during debugging.
    # set_log_level(LOG_DEBUG)

    # --- Fill in settings dictionary using addon_obj.getSetting() ---
    get_settings(cfg)
    set_log_level(cfg.settings['log_level'])

    # --- Some debug stuff for development ---
    log_debug('---------- Called AML Main::run_plugin() constructor ----------')
    log_debug('sys.platform    {}'.format(sys.platform))
    log_debug('Python version  ' + sys.version.replace('\n', ''))
    log_debug('__a_id__        {}'.format(cfg.__addon_id__))
    log_debug('__a_version__   {}'.format(cfg.__addon_version__))
    # log_debug('ADDON_DATA_DIR {}'.format(cfg.ADDON_DATA_DIR.getPath()))
    for i in range(len(addon_argv)): log_debug('addon_argv[{}] = "{}"'.format(i, addon_argv[i]))
    # Timestamp to see if this submodule is reinterpreted or not (interpreter uses a cached instance).
    log_debug('submodule global timestamp {}'.format(g_time_str))
    # log_debug('recursionlimit {}'.format(sys.getrecursionlimit()))

    # --- Secondary setting processing ---
    get_settings_log_enabled(cfg)
    log_debug('Operation mode "{}"'.format(cfg.settings['op_mode']))
    log_debug('SL global enable is {}'.format(cfg.settings['global_enable_SL']))

    # --- Playground and testing code ---
    # kodi_get_screensaver_mode()

    # --- Addon data paths creation ---
    if not cfg.ADDON_DATA_DIR.exists(): cfg.ADDON_DATA_DIR.makedirs()
    if not cfg.CACHE_DIR.exists(): cfg.CACHE_DIR.makedirs()
    if not cfg.CATALOG_DIR.exists(): cfg.CATALOG_DIR.makedirs()
    if not cfg.MAIN_DB_HASH_DIR.exists(): cfg.MAIN_DB_HASH_DIR.makedirs()
    if not cfg.FILTERS_DB_DIR.exists(): cfg.FILTERS_DB_DIR.makedirs()
    if not cfg.SL_DB_DIR.exists(): cfg.SL_DB_DIR.makedirs()
    if not cfg.REPORTS_DIR.exists(): cfg.REPORTS_DIR.makedirs()

    # --- Process URL ---
    cfg.base_url = addon_argv[0]
    g_base_url = cfg.base_url
    cfg.addon_handle = int(addon_argv[1])
    if ADDON_RUNNING_PYTHON_2:
        args = urlparse.parse_qs(addon_argv[2][1:])
    elif ADDON_RUNNING_PYTHON_3:
        args = urllib.parse.parse_qs(addon_argv[2][1:])
    else:
        raise TypeError('Undefined Python runtime version.')
    # log_debug('args = {}'.format(args))
    # Interestingly, if plugin is called as type executable then args is empty.
    # However, if plugin is called as type game then Kodi adds the following
    # even for the first call: 'content_type': ['game']
    cfg.content_type = args['content_type'] if 'content_type' in args else None
    log_debug('content_type = {}'.format(cfg.content_type))

    # --- URL routing -------------------------------------------------------------------------
    # Show addon root window.
    args_size = len(args)
    if not 'catalog' in args and not 'command' in args:
        render_root_list(cfg)
        log_debug('Advanced MAME Launcher exit (addon root)')
        return

    # Render a list of something.
    elif 'catalog' in args and not 'command' in args:
        catalog_name = args['catalog'][0]
        # --- Software list is a special case ---
        if catalog_name == 'SL' or catalog_name == 'SL_ROM' or \
            catalog_name == 'SL_CHD' or catalog_name == 'SL_ROM_CHD' or \
            catalog_name == 'SL_empty':
            SL_name = args['category'][0] if 'category' in args else ''
            parent_name = args['parent'][0] if 'parent' in args else ''
            if SL_name and parent_name:
                render_SL_pclone_set(cfg, SL_name, parent_name)
            elif SL_name and not parent_name:
                render_SL_ROMs(cfg, SL_name)
            else:
                render_SL_list(cfg, catalog_name)
        # --- Custom filters ---
        elif catalog_name == 'Custom':
            render_custom_filter_machines(cfg, args['category'][0])
        # --- DAT browsing ---
        elif catalog_name == 'History' or catalog_name == 'MAMEINFO' or \
            catalog_name == 'Gameinit' or catalog_name == 'Command':
            category_name = args['category'][0] if 'category' in args else ''
            machine_name = args['machine'][0] if 'machine' in args else ''
            if category_name and machine_name:
                render_DAT_machine_info(cfg, catalog_name, category_name, machine_name)
            elif category_name and not machine_name:
                render_DAT_category(cfg, catalog_name, category_name)
            else:
                render_DAT_list(cfg, catalog_name)
        else:
            category_name = args['category'][0] if 'category' in args else ''
            parent_name   = args['parent'][0] if 'parent' in args else ''
            if category_name and parent_name:
                render_catalog_clone_list(cfg, catalog_name, category_name, parent_name)
            elif category_name and not parent_name:
                render_catalog_parent_list(cfg, catalog_name, category_name)
            else:
                render_catalog_list(cfg, catalog_name)

    # Execute a command.
    elif 'command' in args:
        command = args['command'][0]

        # Commands used by skins to render items of the addon root menu.
        if   command == 'SKIN_SHOW_FAV_SLOTS':       render_skin_fav_slots()
        elif command == 'SKIN_SHOW_MAIN_FILTERS':    render_skin_main_filters()
        elif command == 'SKIN_SHOW_BINARY_FILTERS':  render_skin_binary_filters()
        elif command == 'SKIN_SHOW_CATALOG_FILTERS': render_skin_catalog_filters()
        elif command == 'SKIN_SHOW_DAT_SLOTS':       render_skin_dat_slots()
        elif command == 'SKIN_SHOW_SL_FILTERS':      render_skin_SL_filters()

        # Auxiliar commands from parent machine context menu
        # Not sure if this will cause problems with the concurrent protected code once it's implemented.
        elif command == 'EXEC_SHOW_MAME_CLONES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            machine_name  = args['parent'][0] if 'parent' in args else ''
            url = misc_url_3_arg('catalog', catalog_name, 'category', category_name, 'parent', machine_name)
            xbmc.executebuiltin('Container.Update({})'.format(url))

        elif command == 'EXEC_SHOW_SL_CLONES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            machine_name  = args['parent'][0] if 'parent' in args else ''
            url = misc_url_3_arg('catalog', 'SL', 'category', category_name, 'parent', machine_name)
            xbmc.executebuiltin('Container.Update({})'.format(url))

        # If location is not present in the URL default to standard.
        elif command == 'LAUNCH':
            machine  = args['machine'][0]
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            log_info('Launching MAME machine "{}" in "{}"'.format(machine, location))
            run_machine(cfg, machine, location)
        elif command == 'LAUNCH_SL':
            SL_name  = args['SL'][0]
            ROM_name = args['ROM'][0]
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            log_info('Launching SL machine "{}" (ROM "{}")'.format(SL_name, ROM_name))
            run_SL_machine(cfg, SL_name, ROM_name, location)

        elif command == 'SETUP_PLUGIN':
            command_context_setup_plugin(cfg)

        # Not used at the moment.
        # Instead of per-catalog display mode settings there are global settings.
        elif command == 'DISPLAY_SETTINGS_MAME':
            catalog_name = args['catalog'][0]
            category_name = args['category'][0] if 'category' in args else ''
            command_context_display_settings(cfg, catalog_name, category_name)
        elif command == 'DISPLAY_SETTINGS_SL':
            command_context_display_settings_SL(cfg, args['category'][0])
        elif command == 'VIEW_DAT':
            machine  = args['machine'][0]  if 'machine'  in args else ''
            SL       = args['SL'][0]       if 'SL'       in args else ''
            ROM      = args['ROM'][0]      if 'ROM'      in args else ''
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            command_context_info_utils(cfg, machine, SL, ROM, location)
        elif command == 'VIEW':
            machine  = args['machine'][0]  if 'machine'  in args else ''
            SL       = args['SL'][0]       if 'SL'       in args else ''
            ROM      = args['ROM'][0]      if 'ROM'      in args else ''
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            command_context_view_audit(cfg, machine, SL, ROM, location)
        elif command == 'UTILITIES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            command_context_utilities(cfg, catalog_name, category_name)

        # MAME Favourites
        elif command == 'ADD_MAME_FAV':
            command_context_add_mame_fav(cfg, args['machine'][0])
        elif command == 'MANAGE_MAME_FAV':
            # If called from the root menu machine is empty.
            machine = args['machine'][0] if 'machine' in args else ''
            command_context_manage_mame_fav(cfg, machine)
        elif command == 'SHOW_MAME_FAVS':
            command_show_mame_fav(cfg)

        # Most and Recently played
        elif command == 'SHOW_MAME_MOST_PLAYED':
            command_show_mame_most_played(cfg)
        elif command == 'MANAGE_MAME_MOST_PLAYED':
            m_name = args['machine'][0] if 'machine' in args else ''
            command_context_manage_mame_most_played(cfg, m_name)

        elif command == 'SHOW_MAME_RECENTLY_PLAYED':
            command_show_mame_recently_played(cfg)
        elif command == 'MANAGE_MAME_RECENT_PLAYED':
            m_name = args['machine'][0] if 'machine' in args else ''
            command_context_manage_mame_recent_played(cfg, m_name)

        # SL Favourites
        elif command == 'ADD_SL_FAV':
            command_context_add_sl_fav(cfg, args['SL'][0], args['ROM'][0])
        elif command == 'MANAGE_SL_FAV':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            command_context_manage_sl_fav(cfg, SL_name, ROM_name)
        elif command == 'SHOW_SL_FAVS':
            command_show_sl_fav(cfg)

        elif command == 'SHOW_SL_MOST_PLAYED':
            command_show_SL_most_played(cfg)
        elif command == 'MANAGE_SL_MOST_PLAYED':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            command_context_manage_SL_most_played(cfg, SL_name, ROM_name)

        elif command == 'SHOW_SL_RECENTLY_PLAYED':
            command_show_SL_recently_played(cfg)
        elif command == 'MANAGE_SL_RECENT_PLAYED':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            command_context_manage_SL_recent_played(cfg, SL_name, ROM_name)

        elif command == 'SHOW_CUSTOM_FILTERS':
            command_show_custom_filters(cfg)
        elif command == 'SETUP_CUSTOM_FILTERS':
            command_context_setup_custom_filters(cfg)

        elif command == 'SHOW_UTILITIES_VLAUNCHERS':
            render_Utilities_vlaunchers(cfg)
        elif command == 'SHOW_GLOBALREPORTS_VLAUNCHERS':
            render_GlobalReports_vlaunchers(cfg)

        elif command == 'EXECUTE_UTILITY':
            which_utility = args['which'][0]
            command_exec_utility(cfg, which_utility)

        elif command == 'EXECUTE_REPORT':
            which_report = args['which'][0]
            command_exec_report(cfg, which_report)

        else:
            u = 'Unknown command "{}"'.format(command)
            log_error(u)
            kodi_dialog_OK(u)
            xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
    else:
        u = 'Error in URL routing'
        log_error(u)
        kodi_dialog_OK(u)
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

    # --- So Long, and Thanks for All the Fish ---
    log_debug('Advanced MAME Launcher exit')

# Get Addon Settings. log_*() functions cannot be used here during normal operation.
def get_settings(cfg):
    settings = cfg.settings

    # --- Main operation ---
    settings['op_mode_raw'] = kodi_get_int_setting(cfg, 'op_mode_raw')
    # Vanilla MAME settings.
    settings['rom_path_vanilla'] = kodi_get_str_setting(cfg, 'rom_path_vanilla')
    settings['enable_SL'] = kodi_get_bool_setting(cfg, 'enable_SL')
    settings['mame_prog'] = kodi_get_str_setting(cfg, 'mame_prog')
    settings['SL_hash_path'] = kodi_get_str_setting(cfg, 'SL_hash_path')
    # MAME 2003 Plus settings.
    settings['rom_path_2003_plus'] = kodi_get_str_setting(cfg, 'rom_path_2003_plus')
    settings['retroarch_prog'] = kodi_get_str_setting(cfg, 'retroarch_prog')
    settings['libretro_dir'] = kodi_get_str_setting(cfg, 'libretro_dir')
    settings['xml_2003_path'] = kodi_get_str_setting(cfg, 'xml_2003_path')

    # --- Optional paths ---
    settings['assets_path'] = kodi_get_str_setting(cfg, 'assets_path')
    settings['dats_path'] = kodi_get_str_setting(cfg, 'dats_path')
    settings['chd_path'] = kodi_get_str_setting(cfg, 'chd_path')
    settings['samples_path'] = kodi_get_str_setting(cfg, 'samples_path')
    settings['SL_rom_path'] = kodi_get_str_setting(cfg, 'SL_rom_path')
    settings['SL_chd_path'] = kodi_get_str_setting(cfg, 'SL_chd_path')

    # --- ROM sets ---
    settings['mame_rom_set'] = kodi_get_int_setting(cfg, 'mame_rom_set')
    settings['mame_chd_set'] = kodi_get_int_setting(cfg, 'mame_chd_set')
    settings['SL_rom_set'] = kodi_get_int_setting(cfg, 'SL_rom_set')
    settings['SL_chd_set'] = kodi_get_int_setting(cfg, 'SL_chd_set')

    # Misc separator
    settings['filter_XML'] = kodi_get_str_setting(cfg, 'filter_XML')
    settings['generate_history_infolabel'] = kodi_get_bool_setting(cfg, 'generate_history_infolabel')

    # --- Display I ---
    settings['display_launcher_notify'] = kodi_get_bool_setting(cfg, 'display_launcher_notify')
    settings['mame_view_mode'] = kodi_get_int_setting(cfg, 'mame_view_mode')
    settings['sl_view_mode'] = kodi_get_int_setting(cfg, 'sl_view_mode')
    settings['display_hide_Mature'] = kodi_get_bool_setting(cfg, 'display_hide_Mature')
    settings['display_hide_BIOS'] = kodi_get_bool_setting(cfg, 'display_hide_BIOS')
    settings['display_hide_imperfect'] = kodi_get_bool_setting(cfg, 'display_hide_imperfect')
    settings['display_hide_nonworking'] = kodi_get_bool_setting(cfg, 'display_hide_nonworking')
    settings['display_rom_available'] = kodi_get_bool_setting(cfg, 'display_rom_available')
    settings['display_chd_available'] = kodi_get_bool_setting(cfg, 'display_chd_available')
    settings['display_SL_items_available'] = kodi_get_bool_setting(cfg, 'display_SL_items_available')
    settings['display_MAME_flags'] = kodi_get_bool_setting(cfg, 'display_MAME_flags')
    settings['display_SL_flags'] = kodi_get_bool_setting(cfg, 'display_SL_flags')

    # --- Display II ---
    settings['display_main_filters'] = kodi_get_bool_setting(cfg, 'display_main_filters')
    settings['display_binary_filters'] = kodi_get_bool_setting(cfg, 'display_binary_filters')
    settings['display_catalog_filters'] = kodi_get_bool_setting(cfg, 'display_catalog_filters')
    settings['display_DAT_browser'] = kodi_get_bool_setting(cfg, 'display_DAT_browser')
    settings['display_SL_browser'] = kodi_get_bool_setting(cfg, 'display_SL_browser')
    settings['display_custom_filters'] = kodi_get_bool_setting(cfg, 'display_custom_filters')
    settings['display_ROLs'] = kodi_get_bool_setting(cfg, 'display_ROLs')
    settings['display_MAME_favs'] = kodi_get_bool_setting(cfg, 'display_MAME_favs')
    settings['display_MAME_most'] = kodi_get_bool_setting(cfg, 'display_MAME_most')
    settings['display_MAME_recent'] = kodi_get_bool_setting(cfg, 'display_MAME_recent')
    settings['display_SL_favs'] = kodi_get_bool_setting(cfg, 'display_SL_favs')
    settings['display_SL_most'] = kodi_get_bool_setting(cfg, 'display_SL_most')
    settings['display_SL_recent'] = kodi_get_bool_setting(cfg, 'display_SL_recent')
    settings['display_utilities'] = kodi_get_bool_setting(cfg, 'display_utilities')
    settings['display_global_reports'] = kodi_get_bool_setting(cfg, 'display_global_reports')

    # --- Artwork / Assets ---
    settings['display_hide_trailers'] = kodi_get_bool_setting(cfg, 'display_hide_trailers')
    settings['artwork_mame_icon'] = kodi_get_int_setting(cfg, 'artwork_mame_icon')
    settings['artwork_mame_fanart'] = kodi_get_int_setting(cfg, 'artwork_mame_fanart')
    settings['artwork_SL_icon'] = kodi_get_int_setting(cfg, 'artwork_SL_icon')
    settings['artwork_SL_fanart'] = kodi_get_int_setting(cfg, 'artwork_SL_fanart')

    # --- Advanced ---
    settings['media_state_action'] = kodi_get_int_setting(cfg, 'media_state_action')
    settings['delay_tempo'] = kodi_get_int_setting(cfg, 'delay_tempo')
    settings['suspend_audio_engine'] = kodi_get_bool_setting(cfg, 'suspend_audio_engine')
    settings['suspend_screensaver'] = kodi_get_bool_setting(cfg, 'suspend_screensaver')
    settings['toggle_window'] = kodi_get_bool_setting(cfg, 'toggle_window')
    settings['log_level'] = kodi_get_int_setting(cfg, 'log_level')
    settings['debug_enable_MAME_render_cache'] = kodi_get_bool_setting(cfg, 'debug_enable_MAME_render_cache')
    settings['debug_enable_MAME_asset_cache'] = kodi_get_bool_setting(cfg, 'debug_enable_MAME_asset_cache')
    settings['debug_MAME_machine_data'] = kodi_get_bool_setting(cfg, 'debug_MAME_machine_data')
    settings['debug_MAME_ROM_DB_data'] = kodi_get_bool_setting(cfg, 'debug_MAME_ROM_DB_data')
    settings['debug_MAME_Audit_DB_data'] = kodi_get_bool_setting(cfg, 'debug_MAME_Audit_DB_data')
    settings['debug_SL_item_data'] = kodi_get_bool_setting(cfg, 'debug_SL_item_data')
    settings['debug_SL_ROM_DB_data'] = kodi_get_bool_setting(cfg, 'debug_SL_ROM_DB_data')
    settings['debug_SL_Audit_DB_data'] = kodi_get_bool_setting(cfg, 'debug_SL_Audit_DB_data')

    # --- Dump settings for DEBUG ---
    # log_debug('Settings dump BEGIN')
    # for key in sorted(settings):
    #     log_debug('{} --> {:10s} {}'.format(key.rjust(21), text_type(settings[key]), type(settings[key])))
    # log_debug('Settings dump END')

#
# Called after log is enabled. Process secondary settings.
#
def get_settings_log_enabled(cfg):
    # Convenience data
    cfg.__addon_version_int__ = misc_addon_version_str_to_int(cfg.__addon_version__)

    # Additional settings.
    cfg.settings['op_mode'] = OP_MODE_LIST[cfg.settings['op_mode_raw']]

    # Map AML artwork to Kodi standard artwork.
    cfg.mame_icon = assets_get_asset_key_MAME_icon(cfg.settings['artwork_mame_icon'])
    cfg.mame_fanart = assets_get_asset_key_MAME_fanart(cfg.settings['artwork_mame_fanart'])
    cfg.SL_icon = assets_get_asset_key_SL_icon(cfg.settings['artwork_SL_icon'])
    cfg.SL_fanart = assets_get_asset_key_SL_fanart(cfg.settings['artwork_SL_fanart'])

    # Enable or disable Software List depending on settings.
    if cfg.settings['op_mode'] == OP_MODE_VANILLA and cfg.settings['enable_SL'] == True:
        cfg.settings['global_enable_SL'] = True
    elif cfg.settings['op_mode'] == OP_MODE_VANILLA and cfg.settings['enable_SL'] == False:
        cfg.settings['global_enable_SL'] = False
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        cfg.settings['global_enable_SL'] = False
    else:
        raise TypeError('Wrong cfg.settings["op_mode"] = {}'.format(cfg.settings['op_mode']))

# ---------------------------------------------------------------------------------------------
# Misc URL building functions. Placed here because these functions are used for building
# global read-only variables using in the addon.
# NOTE '&' must be scaped to '%26' in all URLs
# ---------------------------------------------------------------------------------------------
# Functions used in xbmcplugin.addDirectoryItem()
def misc_url(command):
    command_escaped = command.replace('&', '%26')

    return '{}?command={}'.format(g_base_url, command_escaped)

def misc_url_1_arg(arg_name, arg_value):
    arg_value_escaped = arg_value.replace('&', '%26')

    return '{}?{}={}'.format(g_base_url, arg_name, arg_value_escaped)

def misc_url_2_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')

    return '{}?{}={}&{}={}'.format(g_base_url,
        arg_name_1, arg_value_1_escaped, arg_name_2, arg_value_2_escaped)

def misc_url_3_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2, arg_name_3, arg_value_3):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')
    arg_value_3_escaped = arg_value_3.replace('&', '%26')

    return '{}?{}={}&{}={}&{}={}'.format(g_base_url,
        arg_name_1, arg_value_1_escaped, arg_name_2, arg_value_2_escaped, arg_name_3, arg_value_3_escaped)

def misc_url_4_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2, arg_name_3, arg_value_3, arg_name_4, arg_value_4):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')
    arg_value_3_escaped = arg_value_3.replace('&', '%26')
    arg_value_4_escaped = arg_value_4.replace('&', '%26')

    return '{}?{}={}&{}={}&{}={}&{}={}'.format(g_base_url,
        arg_name_1, arg_value_1_escaped, arg_name_2, arg_value_2_escaped,
        arg_name_3, arg_value_3_escaped,arg_name_4, arg_value_4_escaped)

# Functions used in context menus, in listitem.addContextMenuItems()
def misc_url_RunPlugin(command):
    command_esc = command.replace('&', '%26')

    return 'RunPlugin({}?command={})'.format(g_base_url, command_esc)

def misc_url_1_arg_RunPlugin(arg_n_1, arg_v_1):
    arg_v_1_esc = arg_v_1.replace('&', '%26')

    return 'RunPlugin({}?{}={})'.format(g_base_url, arg_n_1, arg_v_1_esc)

def misc_url_2_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')

    return 'RunPlugin({}?{}={}&{}={})'.format(g_base_url,
        arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc)

def misc_url_3_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2, arg_n_3, arg_v_3):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')
    arg_v_3_esc = arg_v_3.replace('&', '%26')

    return 'RunPlugin({}?{}={}&{}={}&{}={})'.format(g_base_url,
        arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc, arg_n_3, arg_v_3_esc)

def misc_url_4_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2, arg_n_3, arg_v_3, arg_n_4, arg_v_4):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')
    arg_v_3_esc = arg_v_3.replace('&', '%26')
    arg_v_4_esc = arg_v_4.replace('&', '%26')

    return 'RunPlugin({}?{}={}&{}={}&{}={}&{}={})'.format(g_base_url,
        arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc, arg_n_3, arg_v_3_esc, arg_n_4, arg_v_4_esc)

# List of sorting methods here http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcplugin.html#-setSetting
def set_Kodi_unsorted_method(cfg):
    if cfg.addon_handle < 0: return
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

def set_Kodi_all_sorting_methods(cfg):
    if cfg.addon_handle < 0: return
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

def set_Kodi_all_sorting_methods_and_size(cfg):
    if cfg.addon_handle < 0: return
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_SIZE)
    xbmcplugin.addSortMethod(handle = cfg.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

# ---------------------------------------------------------------------------------------------
# Root menu rendering
# ---------------------------------------------------------------------------------------------
# Returns a dictionary rd (render data).
def set_render_root_data():
    # Tuple: catalog_name, catalog_key, title, plot, render colour.
    root_Main = {
        # Main filter Catalog
        'Main_Normal' : [
            'Main', 'Normal',
            'Machines with coin slot (Normal)',
            ('[COLOR orange]Main filter[/COLOR] of MAME machines [COLOR violet]with coin '
             'slot[/COLOR] and normal controls. This list includes the machines you would '
             'typically find in Europe and USA amusement arcades some decades ago.'),
            COLOR_FILTER_MAIN,
        ],
        'Main_Unusual' : [
            'Main', 'Unusual',
            'Machines with coin slot (Unusual)',
            ('[COLOR orange]Main filter[/COLOR] of MAME machines [COLOR violet]with coin '
             'slot[/COLOR] and Only buttons, Gambling, Hanafuda and Mahjong controls. '
             'This corresponds to slot, gambling and Japanese card and mahjong machines.'),
            COLOR_FILTER_MAIN,
        ],
        'Main_NoCoin' : [
            'Main', 'NoCoin',
            'Machines with no coin slot',
            ('[COLOR orange]Main filter[/COLOR] of MAME machines [COLOR violet]with no coin '
             'slot[/COLOR]. Here you will find the good old MESS machines, including computers, '
             'video game consoles, hand-held video game consoles, etc.'),
            COLOR_FILTER_MAIN,
        ],
        'Main_Mechanical' : [
            'Main', 'Mechanical',
            'Mechanical machines',
            ('[COLOR orange]Main filter[/COLOR] of [COLOR violet]mechanical[/COLOR] MAME machines. '
             'These machines have mechanical parts, for example pinballs, and currently do not work with MAME. '
             'They are here for preservation and historical reasons.'),
            COLOR_FILTER_MAIN,
        ],
        'Main_Dead' : [
            'Main', 'Dead',
            'Dead machines',
            ('[COLOR orange]Main filter[/COLOR] of [COLOR violet]dead[/COLOR] MAME machines. '
             'Dead machines do not work and have no controls, so you cannot interact with them in any way.'),
            COLOR_FILTER_MAIN,
        ],
        'Main_Devices' : [
            'Main', 'Devices',
            'Device machines',
            ('[COLOR orange]Main filter[/COLOR] of [COLOR violet]device machines[/COLOR]. '
             'Device machines, for example the Zilog Z80 CPU, are components used by other machines '
             'and cannot be run on their own.'),
            COLOR_FILTER_MAIN,
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
            COLOR_FILTER_BINARY,
        ],
        'CHD' : [
            'Binary', 'CHD',
            'Machines [with CHDs]',
            ('[COLOR orange]Binary filter[/COLOR] of machines that need one or more '
             '[COLOR violet]CHDs[/COLOR] to run. They may also need ROMs and/or BIOS or not.'),
            COLOR_FILTER_BINARY,
        ],
        'Samples' : [
            'Binary', 'Samples',
            'Machines [with Samples]',
            ('[COLOR orange]Binary filter[/COLOR] of machines that require '
             '[COLOR violet]samples[/COLOR]. Samples are optional and will increase the quality '
             'of the emulated sound.'),
            COLOR_FILTER_BINARY,
        ],
        'SoftwareLists' : [
            'Binary', 'SoftwareLists',
            'Machines [with Software Lists]',
            ('[COLOR orange]Binary filter[/COLOR] of machines that have one or more '
             '[COLOR violet]Software Lists[/COLOR] associated.'),
            COLOR_FILTER_BINARY,
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
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Catlist' : [
            'Machines by Category (Catlist)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by category. '
             'This filter requires that you configure [COLOR violet]catlist.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Catlist'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Genre' : [
            'Machines by Category (Genre)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Genre. '
             'This filter requires that you configure [COLOR violet]genre.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Genre'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Category' : [
            'Machines by Category (MASH)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Category. '
             'This filter requires that you configure [COLOR violet]Category.ini[/COLOR] by MASH.'),
            misc_url_1_arg('catalog', 'Category'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'NPlayers' : [
            'Machines by Number of players',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by the number of '
             'players that can play simultaneously or alternatively. This filter requires '
             'that you configure [COLOR violet]nplayers.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'NPlayers'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Bestgames' : [
            'Machines by Rating',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by rating. The rating '
             'is subjective but is a good indicator about the quality of the games. '
             'This filter requires that you configure [COLOR violet]bestgames.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Bestgames'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Series' : [
            'Machines by Series',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by series. '
             'This filter requires that you configure [COLOR violet]series.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Series'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Alltime' : [
            'Machines by Alltime (MASH)',
            ('[COLOR orange]Catalog filter[/COLOR] of a best-quality machine selection '
             'sorted by year. '
             'This filter requires that you configure [COLOR violet]Alltime.ini[/COLOR] by MASH.'),
            misc_url_1_arg('catalog', 'Alltime'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Artwork' : [
            'Machines by Artwork (MASH)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Artwork. '
             'This filter requires that you configure [COLOR violet]Artwork.ini[/COLOR] by MASH.'),
            misc_url_1_arg('catalog', 'Artwork'),
            COLOR_FILTER_CATALOG_DAT,
        ],
        'Version' : [
            'Machines by Version Added (Catver)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by Version Added. '
             'This filter requires that you configure [COLOR violet]catver.ini[/COLOR].'),
            misc_url_1_arg('catalog', 'Version'),
            COLOR_FILTER_CATALOG_DAT,
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
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Controls_Compact' : [
            'Machines by Controls (Compact)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by control. '
             'Machines may have additional controls.'),
            misc_url_1_arg('catalog', 'Controls_Compact'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Devices_Expanded' : [
            'Machines by Pluggable Devices (Expanded)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by pluggable devices. '
             'For each machine, all pluggable devices are included in the list.'),
            misc_url_1_arg('catalog', 'Devices_Expanded'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Devices_Compact' : [
            'Machines by Pluggable Devices (Compact)',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by pluggable devices. '
             'Machines may have additional pluggable devices.'),
            misc_url_1_arg('catalog', 'Devices_Compact'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Display_Type' : [
            'Machines by Display Type',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by display type '
             'and rotation.'),
            misc_url_1_arg('catalog', 'Display_Type'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Display_VSync' : [
            'Machines by Display VSync freq',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by the display '
             'vertical synchronisation (VSync) frequency, also known as the display refresh rate or '
             'frames per second (FPS).'),
            misc_url_1_arg('catalog', 'Display_VSync'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Display_Resolution' : [
            'Machines by Display Resolution',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by display resolution.'),
            misc_url_1_arg('catalog', 'Display_Resolution'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'CPU' : [
            'Machines by CPU',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by the CPU used.'),
            misc_url_1_arg('catalog', 'CPU'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Driver' : [
            'Machines by Driver',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by driver. '
             'Brother machines have the same driver.'),
            misc_url_1_arg('catalog', 'Driver'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Manufacturer' : [
            'Machines by Manufacturer',
            ('[COLOR orange]Catalog filter[/COLOR] of MAME machines sorted by '
             'manufacturer.'),
            misc_url_1_arg('catalog', 'Manufacturer'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'ShortName' : [
            'Machines by MAME short name',
            ('[COLOR orange]Catalog filter[/COLOR] of MAME machines sorted alphabetically '
             'by the MAME short name. The short name originated during the old MS-DOS days '
             'where filenames were restricted to 8 ASCII characters.'),
            misc_url_1_arg('catalog', 'ShortName'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'LongName' : [
            'Machines by MAME long name',
            ('[COLOR orange]Catalog filter[/COLOR] of MAME machines sorted alphabetically '
             'by the machine description or long name.'),
            misc_url_1_arg('catalog', 'LongName'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'BySL' : [
            'Machines by Software List',
            ('[COLOR orange]Catalog filter[/COLOR] of the Software Lists and the machines '
             'that run items belonging to that Software List.'),
            misc_url_1_arg('catalog', 'BySL'),
            COLOR_FILTER_CATALOG_NODAT,
        ],
        'Year' : [
            'Machines by Year',
            ('[COLOR orange]Catalog filter[/COLOR] of machines sorted by release year.'),
            misc_url_1_arg('catalog', 'Year'),
            COLOR_FILTER_CATALOG_NODAT,
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
            COLOR_MAME_DAT_BROWSER,
        ],
        'MAMEINFO' : [
            'MAMEINFO DAT',
            ('Browse the contents of [COLOR orange]mameinfo.dat[/COLOR]. Note that '
             'mameinfo.dat is also available on the MAME machines context menu.'),
            misc_url_1_arg('catalog', 'MAMEINFO'),
            COLOR_MAME_DAT_BROWSER,
        ],
        'Gameinit' : [
            'Gameinit DAT',
            ('Browse the contents of [COLOR orange]gameinit.dat[/COLOR]. Note that '
             'gameinit.dat is also available on the MAME machines context menu.'),
            misc_url_1_arg('catalog', 'Gameinit'),
            COLOR_MAME_DAT_BROWSER,
        ],
        'Command' : [
            'Command DAT',
            ('Browse the contents of [COLOR orange]command.dat[/COLOR]. Note that '
             'command.dat is also available on the MAME machines context menu.'),
            misc_url_1_arg('catalog', 'Command'),
            COLOR_MAME_DAT_BROWSER,
        ],
    }

    # Tuple: title, plot, URL
    root_SL = {
        'SL' : [
            'Software Lists (all)',
            ('Display all [COLOR orange]Software Lists[/COLOR].'),
            misc_url_1_arg('catalog', 'SL'),
            COLOR_SOFTWARE_LISTS,
        ],
        'SL_ROM' : [
            'Software Lists (with ROMs)',
            ('Display [COLOR orange]Software Lists[/COLOR] that have only ROMs and not CHDs (disks).'),
            misc_url_1_arg('catalog', 'SL_ROM'),
            COLOR_SOFTWARE_LISTS,
        ],
        'SL_ROM_CHD' : [
            'Software Lists (with ROMs and CHDs)',
            ('Display [COLOR orange]Software Lists[/COLOR] that have both ROMs and CHDs.'),
            misc_url_1_arg('catalog', 'SL_ROM_CHD'),
            COLOR_SOFTWARE_LISTS,
        ],
        'SL_CHD' : [
            'Software Lists (with CHDs)',
            ('Display [COLOR orange]Software Lists[/COLOR] that have only CHDs and not ROMs.'),
            misc_url_1_arg('catalog', 'SL_CHD'),
            COLOR_SOFTWARE_LISTS,
        ],
        'SL_empty' : [
            'Software Lists (no ROMs nor CHDs)',
            ('Display [COLOR orange]Software Lists[/COLOR] with no ROMs nor CHDs.'),
            misc_url_1_arg('catalog', 'SL_empty'),
            COLOR_SOFTWARE_LISTS,
        ],
    }

    root_filters_CM = {
        'Custom_Filters' : [
            '[Custom MAME filters]',
            ('[COLOR orange]Custom filters[/COLOR] allows to generate machine '
             'listings perfectly tailored to your whises. For example, you can define a filter of all '
             'the machines released in the 1980s that use a joystick. AML includes a fairly '
             'complete default set of filters in XML format which can be edited.'),
            misc_url_1_arg('command', 'SHOW_CUSTOM_FILTERS'),
            [('Setup custom filters', misc_url_1_arg_RunPlugin('command', 'SETUP_CUSTOM_FILTERS'))],
            COLOR_MAME_CUSTOM_FILTERS,
        ],
    }

    root_ROLs_CM = {
        'ROLs' : [
            '[AEL Read Only Launchers]',
            ('[COLOR orange]AEL Read Only Launchers[/COLOR] are special launchers '
             'exported to AEL. You can select your Favourite MAME machines or setup a custom '
             'filter to enjoy your MAME games in AEL togheter with other emulators.'),
            misc_url_1_arg('command', 'SHOW_AEL_ROLS'),
            [('Setup ROLs', misc_url_1_arg_RunPlugin('command', 'SETUP_AEL_ROLS'))],
            COLOR_AEL_ROLS,
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
            COLOR_MAME_SPECIAL,
        ],
        'MAME_Most' : [
            '{Most Played MAME machines}',
            ('Display the MAME machines that you play most, sorted by the number '
             'of times you have launched them.'),
            misc_url_1_arg('command', 'SHOW_MAME_MOST_PLAYED'),
            [('Manage Most Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_MOST_PLAYED'))],
            COLOR_MAME_SPECIAL,
        ],
        'MAME_Recent' : [
            '{Recently Played MAME machines}',
            ('Display the MAME machines that you have launched recently.'),
            misc_url_1_arg('command', 'SHOW_MAME_RECENTLY_PLAYED'),
            [('Manage Recently Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_RECENT_PLAYED'))],
            COLOR_MAME_SPECIAL,
        ],
        'SL_Favs' : [
            '<Favourite Software Lists ROMs>',
            ('Display your [COLOR orange]Favourite Software List items[/COLOR]. '
             'To add machines to the SL Favourite list use the context menu on any SL item list.'),
            misc_url_1_arg('command', 'SHOW_SL_FAVS'),
            [('Manage SL Favourites', misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_FAV'))],
            COLOR_SL_SPECIAL,
        ],
        'SL_Most' : [
            '{Most Played SL ROMs}',
            ('Display the Software List itmes that you play most, sorted by the number '
             'of times you have launched them.'),
            misc_url_1_arg('command', 'SHOW_SL_MOST_PLAYED'),
            [('Manage SL Most Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_MOST_PLAYED'))],
            COLOR_SL_SPECIAL,
        ],
        'SL_Recent' : [
            '{Recently Played SL ROMs}',
            'Display the Software List items that you have launched recently.',
            misc_url_1_arg('command', 'SHOW_SL_RECENTLY_PLAYED'),
            [('Manage SL Recently Played', misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_RECENT_PLAYED'))],
            COLOR_SL_SPECIAL,
        ],
    }

    rd = {
        'root_Main' : root_Main,
        'root_Binary' : root_Binary,
        'root_categories' : root_categories,
        'root_special' : root_special,
        'root_SL' : root_SL,
        'root_filters_CM' : root_filters_CM,
        'root_ROLs_CM' : root_ROLs_CM,
        'root_special_CM' : root_special_CM,
    }

    return rd

def render_root_list(cfg):
    mame_view_mode = cfg.settings['mame_view_mode']
    rd = set_render_root_data()

    # MAME machine count.
    cache_index_dic = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())

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

        MAME_counters_available = True
    except KeyError:
        MAME_counters_available = False
    log_debug('render_root_list() MAME_counters_available = {}'.format(MAME_counters_available))

    # --- SL item count ---
    if cfg.settings['global_enable_SL']:
        SL_index_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        try:
            num_SL_all = 0
            num_SL_ROMs = 0
            num_SL_CHDs = 0
            num_SL_mixed = 0
            num_SL_empty = 0
            for l_name, l_dic in SL_index_dic.items():
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
                    log_error('Logical error in SL {}'.format(l_name))
            SL_counters_available = True
            # log_debug('There are {} SL_all lists.'.format(num_SL_all))
            # log_debug('There are {} SL_ROMs lists.'.format(num_SL_ROMs))
            # log_debug('There are {} SL_mixed lists.'.format(num_SL_mixed))
            # log_debug('There are {} SL_CHDs lists.'.format(num_SL_CHDs))
            # log_debug('There are {} SL_empty lists.'.format(num_SL_empty))
        except KeyError as E:
            SL_counters_available = False
            # num_SL_empty always used to control visibility. If 0 then 'SL empty' is not visible.
            num_SL_empty = 0
    else:
        SL_counters_available = False
    log_debug('render_root_list() SL_counters_available = {}'.format(SL_counters_available))

    # --- Machine counters ---
    if MAME_counters_available:
        if mame_view_mode == VIEW_MODE_FLAT:
            a = ' [COLOR orange]({} machines)[/COLOR]'
            rd['root_Main']['Main_Normal'][2] += a.format(num_m_Main_Normal)
            rd['root_Main']['Main_Unusual'][2] += a.format(num_m_Main_Unusual)
            rd['root_Main']['Main_NoCoin'][2] += a.format(num_m_Main_NoCoin)
            rd['root_Main']['Main_Mechanical'][2] += a.format(num_m_Main_Mechanical)
            rd['root_Main']['Main_Dead'][2] += a.format(num_m_Main_Dead)
            rd['root_Main']['Main_Devices'][2] += a.format(num_m_Main_Devices)
            rd['root_Binary']['BIOS'][2] += a.format(num_m_Binary_BIOS)
            rd['root_Binary']['CHD'][2] += a.format(num_m_Binary_CHD)
            rd['root_Binary']['Samples'][2] += a.format(num_m_Binary_Samples)
            rd['root_Binary']['SoftwareLists'][2] += a.format(num_m_Binary_SoftwareLists)
        elif mame_view_mode == VIEW_MODE_PCLONE:
            a = ' [COLOR orange]({} parents)[/COLOR]'
            rd['root_Main']['Main_Normal'][2] += a.format(num_p_Main_Normal)
            rd['root_Main']['Main_Unusual'][2] += a.format(num_p_Main_Unusual)
            rd['root_Main']['Main_NoCoin'][2] += a.format(num_p_Main_NoCoin)
            rd['root_Main']['Main_Mechanical'][2] += a.format(num_p_Main_Mechanical)
            rd['root_Main']['Main_Dead'][2] += a.format(num_p_Main_Dead)
            rd['root_Main']['Main_Devices'][2] += a.format(num_p_Main_Devices)
            rd['root_Binary']['BIOS'][2] += a.format(num_p_Binary_BIOS)
            rd['root_Binary']['CHD'][2] += a.format(num_p_Binary_CHD)
            rd['root_Binary']['Samples'][2] += a.format(num_p_Binary_Samples)
            rd['root_Binary']['SoftwareLists'][2] += a.format(num_p_Binary_SoftwareLists)

        a = ' [COLOR gold]({} items)[/COLOR]'
        # Optional
        rd['root_categories']['Catver'][0] += a.format(num_cat_Catver)
        rd['root_categories']['Catlist'][0] += a.format(num_cat_Catlist)
        rd['root_categories']['Genre'][0] += a.format(num_cat_Genre)
        rd['root_categories']['Category'][0] += a.format(num_cat_Category)
        rd['root_categories']['NPlayers'][0] += a.format(num_cat_NPlayers)
        rd['root_categories']['Bestgames'][0] += a.format(num_cat_Bestgames)
        rd['root_categories']['Series'][0] += a.format(num_cat_Series)
        rd['root_categories']['Alltime'][0] += a.format(num_cat_Alltime)
        rd['root_categories']['Artwork'][0] += a.format(num_cat_Artwork)
        rd['root_categories']['Version'][0] += a.format(num_cat_Version)
        # Always present
        rd['root_categories']['Controls_Expanded'][0] += a.format(num_cat_Controls_Expanded)
        rd['root_categories']['Controls_Compact'][0] += a.format(num_cat_Controls_Compact)
        rd['root_categories']['Devices_Expanded'][0] += a.format(num_cat_Devices_Expanded)
        rd['root_categories']['Devices_Compact'][0] += a.format(num_cat_Devices_Compact)
        rd['root_categories']['Display_Type'][0] += a.format(num_cat_Display_Type)
        rd['root_categories']['Display_VSync'][0] += a.format(num_cat_Display_VSync)
        rd['root_categories']['Display_Resolution'][0] += a.format(num_cat_Display_Resolution)
        rd['root_categories']['CPU'][0] += a.format(num_cat_CPU)
        rd['root_categories']['Driver'][0] += a.format(num_cat_Driver)
        rd['root_categories']['Manufacturer'][0] += a.format(num_cat_Manufacturer)
        rd['root_categories']['ShortName'][0] += a.format(num_cat_ShortName)
        rd['root_categories']['LongName'][0] += a.format(num_cat_LongName)
        rd['root_categories']['BySL'][0] += a.format(num_cat_BySL)
        rd['root_categories']['Year'][0] += a.format(num_cat_Year)

    if SL_counters_available:
        a = ' [COLOR orange]({} lists)[/COLOR]'
        rd['root_SL']['SL'][0] += a.format(num_SL_all)
        rd['root_SL']['SL_ROM'][0] += a.format(num_SL_ROMs)
        rd['root_SL']['SL_ROM_CHD'][0] += a.format(num_SL_mixed)
        rd['root_SL']['SL_CHD'][0] += a.format(num_SL_CHDs)
        rd['root_SL']['SL_empty'][0] += a.format(num_SL_empty)

    # If everything deactivated render the main filters so user has access to the context menu.
    big_OR = cfg.settings['display_main_filters'] or cfg.settings['display_binary_filters'] or \
        cfg.settings['display_catalog_filters'] or cfg.settings['display_DAT_browser'] or \
        cfg.settings['display_SL_browser'] or cfg.settings['display_MAME_favs'] or \
        cfg.settings['display_SL_favs'] or cfg.settings['display_custom_filters']
    if not big_OR:
        cfg.settings['display_main_filters'] = True

    # Main filters (Virtual catalog 'Main')
    if cfg.settings['display_main_filters']:
        render_root_catalog_row(cfg, *rd['root_Main']['Main_Normal'])
        render_root_catalog_row(cfg, *rd['root_Main']['Main_Unusual'])
        render_root_catalog_row(cfg, *rd['root_Main']['Main_NoCoin'])
        render_root_catalog_row(cfg, *rd['root_Main']['Main_Mechanical'])
        render_root_catalog_row(cfg, *rd['root_Main']['Main_Dead'])
        render_root_catalog_row(cfg, *rd['root_Main']['Main_Devices'])

    # Binary filters (Virtual catalog 'Binary')
    if cfg.settings['display_binary_filters']:
        render_root_catalog_row(cfg, *rd['root_Binary']['BIOS'])
        render_root_catalog_row(cfg, *rd['root_Binary']['CHD'])
        render_root_catalog_row(cfg, *rd['root_Binary']['Samples'])
        if cfg.settings['global_enable_SL']:
            render_root_catalog_row(cfg, *rd['root_Binary']['SoftwareLists'])

    if cfg.settings['display_catalog_filters']:
        # Optional cataloged filters (depend on a INI file)
        render_root_category_row(cfg, *rd['root_categories']['Catver'])
        render_root_category_row(cfg, *rd['root_categories']['Catlist'])
        render_root_category_row(cfg, *rd['root_categories']['Genre'])
        render_root_category_row(cfg, *rd['root_categories']['Category'])
        render_root_category_row(cfg, *rd['root_categories']['NPlayers'])
        render_root_category_row(cfg, *rd['root_categories']['Bestgames'])
        render_root_category_row(cfg, *rd['root_categories']['Series'])
        render_root_category_row(cfg, *rd['root_categories']['Alltime'])
        render_root_category_row(cfg, *rd['root_categories']['Artwork'])
        render_root_category_row(cfg, *rd['root_categories']['Version'])

        # Cataloged filters (always there)
        render_root_category_row(cfg, *rd['root_categories']['Controls_Expanded'])
        render_root_category_row(cfg, *rd['root_categories']['Controls_Compact'])
        render_root_category_row(cfg, *rd['root_categories']['Devices_Expanded'])
        render_root_category_row(cfg, *rd['root_categories']['Devices_Compact'])
        render_root_category_row(cfg, *rd['root_categories']['Display_Type'])
        render_root_category_row(cfg, *rd['root_categories']['Display_VSync'])
        render_root_category_row(cfg, *rd['root_categories']['Display_Resolution'])
        render_root_category_row(cfg, *rd['root_categories']['CPU'])
        render_root_category_row(cfg, *rd['root_categories']['Driver'])
        render_root_category_row(cfg, *rd['root_categories']['Manufacturer'])
        render_root_category_row(cfg, *rd['root_categories']['ShortName'])
        render_root_category_row(cfg, *rd['root_categories']['LongName'])
        if cfg.settings['global_enable_SL']:
            render_root_category_row(cfg, *rd['root_categories']['BySL'])
        render_root_category_row(cfg, *rd['root_categories']['Year'])

    # --- DAT browsers ---
    if cfg.settings['display_DAT_browser']:
        render_root_category_row(cfg, *rd['root_special']['History'])
        render_root_category_row(cfg, *rd['root_special']['MAMEINFO'])
        render_root_category_row(cfg, *rd['root_special']['Gameinit'])
        render_root_category_row(cfg, *rd['root_special']['Command'])

    # --- Software lists ---
    # If SL are globally disabled do not render SL browser.
    # If SL are globally enabled, SL databases are built but the user may choose to not
    # render the SL browser.
    if cfg.settings['display_SL_browser'] and cfg.settings['global_enable_SL']:
        render_root_category_row(cfg, *rd['root_SL']['SL'])
        render_root_category_row(cfg, *rd['root_SL']['SL_ROM'])
        render_root_category_row(cfg, *rd['root_SL']['SL_ROM_CHD'])
        render_root_category_row(cfg, *rd['root_SL']['SL_CHD'])
        if num_SL_empty > 0:
            render_root_category_row(cfg, *rd['root_SL']['SL_empty'])

    # --- Special launchers ---
    if cfg.settings['display_custom_filters']:
        render_root_category_row_custom_CM(cfg, *rd['root_filters_CM']['Custom_Filters'])

    if cfg.settings['display_ROLs']:
        render_root_category_row_custom_CM(cfg, *rd['root_ROLs_CM']['ROLs'])

    # --- MAME Favourite stuff ---
    if cfg.settings['display_MAME_favs']:
        render_root_category_row_custom_CM(cfg, *rd['root_special_CM']['MAME_Favs'])
    if cfg.settings['display_MAME_most']:
        render_root_category_row_custom_CM(cfg, *rd['root_special_CM']['MAME_Most'])
    if cfg.settings['display_MAME_recent']:
        render_root_category_row_custom_CM(cfg, *rd['root_special_CM']['MAME_Recent'])

    # --- SL Favourite stuff ---
    if cfg.settings['display_SL_favs'] and cfg.settings['global_enable_SL']:
        render_root_category_row_custom_CM(cfg, *rd['root_special_CM']['SL_Favs'])
    if cfg.settings['display_SL_most'] and cfg.settings['global_enable_SL']:
        render_root_category_row_custom_CM(cfg, *rd['root_special_CM']['SL_Most'])
    if cfg.settings['display_SL_recent'] and cfg.settings['global_enable_SL']:
        render_root_category_row_custom_CM(cfg, *rd['root_special_CM']['SL_Recent'])

    # Utilities and Reports special menus.
    if cfg.settings['display_utilities']:
        Utilities_plot = ('Execute several [COLOR orange]Utilities[/COLOR]. For example, to '
            'check you AML configuration.')
        URL = misc_url_1_arg('command', 'SHOW_UTILITIES_VLAUNCHERS')
        render_root_category_row(cfg, 'Utilities', Utilities_plot, URL, COLOR_UTILITIES)
    if cfg.settings['display_global_reports']:
        Global_Reports_plot = ('View the [COLOR orange]Global Reports[/COLOR] and '
            'machine and audit [COLOR orange]Statistics[/COLOR].')
        URL = misc_url_1_arg('command', 'SHOW_GLOBALREPORTS_VLAUNCHERS')
        render_root_category_row(cfg, 'Global Reports', Global_Reports_plot, URL, COLOR_GLOBAL_REPORTS)

    # End of directory.
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

#
# These _render_skin_* functions used by skins to display widgets.
# These functions must never fail and be silent in case of error.
# They are called by skin widgets.
#
def render_skin_fav_slots(cfg):
    try:
        rd = set_render_root_data()
        # Remove special markers (first and last character)
        rsCM = root_special_CM.copy()
        for key, value in rsCM.items(): value[0] = value[0][1:-1]
        render_root_category_row_custom_CM(*rd['rsCM']['MAME_Favs'])
        render_root_category_row_custom_CM(*rd['rsCM']['MAME_Most'])
        render_root_category_row_custom_CM(*rd['rsCM']['MAME_Recent'])
        render_root_category_row_custom_CM(*rd['rsCM']['SL_Favs'])
        render_root_category_row_custom_CM(*rd['rsCM']['SL_Most'])
        render_root_category_row_custom_CM(*rd['rsCM']['SL_Recent'])
    except:
        log_error('Excepcion in render_skin_fav_slots()')
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_main_filters(cfg):
    try:
        rd = set_render_root_data()
        render_root_catalog_row(*rd['root_Main']['Main_Normal'])
        render_root_catalog_row(*rd['root_Main']['Main_Unusual'])
        render_root_catalog_row(*rd['root_Main']['Main_NoCoin'])
        render_root_catalog_row(*rd['root_Main']['Main_Mechanical'])
        render_root_catalog_row(*rd['root_Main']['Main_Dead'])
        render_root_catalog_row(*rd['root_Main']['Main_Devices'])
    except:
        log_error('Excepcion in render_skin_main_filters()')
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_binary_filters(cfg):
    try:
        rd = set_render_root_data()
        render_root_catalog_row(*rd['root_Binary']['BIOS'])
        render_root_catalog_row(*rd['root_Binary']['CHD'])
        render_root_catalog_row(*rd['root_Binary']['Samples'])
        render_root_catalog_row(*rd['root_Binary']['SoftwareLists'])
    except:
        log_error('Excepcion in render_skin_binary_filters()')
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_catalog_filters(cfg):
    try:
        # A mechanism to render only configured filters must be developed.
        rd = set_render_root_data()
        render_root_category_row(*rd['root_categories']['Catver'])
        render_root_category_row(*rd['root_categories']['Catlist'])
        render_root_category_row(*rd['root_categories']['Genre'])
        render_root_category_row(*rd['root_categories']['Category'])
        render_root_category_row(*rd['root_categories']['NPlayers'])
        render_root_category_row(*rd['root_categories']['Bestgames'])
        render_root_category_row(*rd['root_categories']['Series'])
        render_root_category_row(*rd['root_categories']['Alltime'])
        render_root_category_row(*rd['root_categories']['Artwork'])
        render_root_category_row(*rd['root_categories']['Version'])
        render_root_category_row(*rd['root_categories']['Controls_Expanded'])
        render_root_category_row(*rd['root_categories']['Controls_Compact'])
        render_root_category_row(*rd['root_categories']['Devices_Expanded'])
        render_root_category_row(*rd['root_categories']['Devices_Compact'])
        render_root_category_row(*rd['root_categories']['Display_Type'])
        render_root_category_row(*rd['root_categories']['Display_VSync'])
        render_root_category_row(*rd['root_categories']['Display_Resolution'])
        render_root_category_row(*rd['root_categories']['CPU'])
        render_root_category_row(*rd['root_categories']['Driver'])
        render_root_category_row(*rd['root_categories']['Manufacturer'])
        render_root_category_row(*rd['root_categories']['ShortName'])
        render_root_category_row(*rd['root_categories']['LongName'])
        render_root_category_row(*rd['root_categories']['BySL'])
        render_root_category_row(*rd['root_categories']['Year'])
    except:
        log_error('Excepcion in render_skin_catalog_filters()')
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_dat_slots():
    try:
        rd = set_render_root_data()
        render_root_category_row(*rd['root_special']['History'])
        render_root_category_row(*rd['root_special']['MAMEINFO'])
        render_root_category_row(*rd['root_special']['Gameinit'])
        render_root_category_row(*rd['root_special']['Command'])
    except:
        log_error('Excepcion in render_skin_dat_slots()')
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_skin_SL_filters(cfg):
    if not cfg.settings['enable_SL']:
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return
    try:
        rd = set_render_root_data()
        render_root_category_row(*rd['root_SL']['SL'])
        render_root_category_row(*rd['root_SL']['SL_ROM'])
        render_root_category_row(*rd['root_SL']['SL_ROM_CHD'])
        render_root_category_row(*rd['root_SL']['SL_CHD'])
        render_root_category_row(*rd['root_SL']['SL_empty'])
    except:
        log_error('Excepcion in render_skin_SL_filters()')
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

#
# A Catalog is equivalent to a Launcher in AEL.
#
def render_root_catalog_row(cfg, catalog_name, catalog_key, display_name, plot_str, color_str = COLOR_DEFAULT):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem('{}{}{}'.format(color_str, display_name, COLOR_END))
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY, 'plot' : plot_str})

    # --- Artwork ---
    icon_path = cfg.ICON_FILE_PATH.getPath()
    fanart_path = cfg.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    URL_utils = misc_url_3_arg_RunPlugin(
        'command', 'UTILITIES', 'catalog', catalog_name, 'category', catalog_key)
    commands = [
        ('Setup addon', misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Utilities', URL_utils),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_2_arg('catalog', catalog_name, 'category', catalog_key)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = True)

#
# A Category is equivalent to a Category in AEL. It contains a list of Launchers (catalogs).
#
def render_root_category_row(cfg, display_name, plot_str, root_URL, color_str = COLOR_DEFAULT):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem('{}{}{}'.format(color_str, display_name, COLOR_END))
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY, 'plot' : plot_str})

    # --- Artwork ---
    icon_path = cfg.ICON_FILE_PATH.getPath()
    fanart_path = cfg.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('Setup addon', misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, root_URL, listitem, isFolder = True)

def render_root_category_row_custom_CM(cfg, display_name, plot_str, root_URL, cmenu_list, color_str = COLOR_DEFAULT):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem('{}{}{}'.format(color_str, display_name, COLOR_END))
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY, 'plot' : plot_str})

    # --- Artwork ---
    icon_path = cfg.ICON_FILE_PATH.getPath()
    fanart_path = cfg.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('Setup addon', misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]
    cmenu_list.extend(commands)
    listitem.addContextMenuItems(cmenu_list)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, root_URL, listitem, isFolder = True)

# -------------------------------------------------------------------------------------------------
# Utilities and Global reports
# -------------------------------------------------------------------------------------------------
def aux_get_generic_listitem(cfg, name, plot, commands):
    vcategory_name   = name
    vcategory_plot   = plot
    vcategory_icon   = cfg.ICON_FILE_PATH.getPath()
    vcategory_fanart = cfg.FANART_FILE_PATH.getPath()
    listitem = xbmcgui.ListItem(vcategory_name)
    listitem.setInfo('video', {'title': vcategory_name, 'plot' : vcategory_plot, 'overlay' : 4})
    listitem.setArt({'icon' : vcategory_icon, 'fanart' : vcategory_fanart})
    listitem.addContextMenuItems(commands)

    return listitem

def render_Utilities_vlaunchers(cfg):
    # --- Common context menu for all VLaunchers ---
    common_commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]

    # --- Check MAME version ---
    t = 'Check MAME version'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_MAME_VERSION')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Check AML configuration ---
    t = 'Check AML configuration'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_CONFIG')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Check/Update all Favourite objects ---
    t = 'Check/Update all Favourite objects'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_ALL_FAV_OBJECTS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Check MAME CRC hash collisions ---
    t = 'Check MAME CRC hash collisions'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_MAME_COLLISIONS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Check SL CRC hash collisions ---
    t = 'Check SL CRC hash collisions'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'CHECK_SL_COLLISIONS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Check SL CRC hash collisions ---
    t = 'Show machines with biggest ROMs'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'SHOW_BIGGEST_ROMS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Check SL CRC hash collisions ---
    t = 'Show machines with smallest ROMs'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'SHOW_SMALLEST_ROMS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Export MAME ROMs DAT file ---
    t = 'Export MAME info in Billyc999 XML format'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_MAME_INFO_BILLYC999_XML')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Export MAME ROMs DAT file ---
    t = 'Export MAME ROMs Logiqx XML DAT file'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_MAME_ROM_DAT')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Export MAME CHDs DAT file ---
    t = 'Export MAME CHDs Logiqx XML DAT file'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_MAME_CHD_DAT')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Export SL ROMs DAT file ---
    # In AML 0.9.10 only export MAME XMLs and see how it goes. SL XMLs cause more trouble
    # than MAME.
    # listitem = aux_get_generic_listitem(cfg, 
    #     'Export SL ROMs Logiqx XML DAT file', 'Export SL ROMs Logiqx XML DAT file', commands)
    # url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_SL_ROM_DAT')
    # xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Export SL CHDs DAT file ---
    # listitem = aux_get_generic_listitem(cfg, 
    #     'Export SL CHDs Logiqx XML DAT file', 'Export SL CHDs Logiqx XML DAT file', commands)
    # url_str = misc_url_2_arg('command', 'EXECUTE_UTILITY', 'which', 'EXPORT_SL_CHD_DAT')
    # xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

#
# Kodi BUG: if size of text file to display is 0 then previous text in window is rendered.
# Solution: report files are never empty. Always print a text header in the report.
#
def render_GlobalReports_vlaunchers(cfg):
    # --- Common context menu for all VLaunchers ---
    common_commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]

    # --- View MAME last execution output --------------------------------------------------------
    if cfg.MAME_OUTPUT_PATH.exists():
        filesize = cfg.MAME_OUTPUT_PATH.fileSize()
        STD_status = '{} bytes'.format(filesize)
    else:
        STD_status = 'not found'
    listitem = aux_get_generic_listitem(cfg,
        'View MAME last execution output ({})'.format(STD_status),
        'View MAME last execution output', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_EXEC_OUTPUT')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View statistics ------------------------------------------------------------------------
    # --- View main statistics ---
    t = 'View main statistics'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_MAIN')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View scanner statistics ---
    t = 'View scanner statistics'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_SCANNER')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # View audit statistics.
    t = 'View audit statistics'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_AUDIT')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # View timestamps and DAT/INI version.
    t = 'View timestamps'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_TIMESTAMPS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View all statistics ---
    t = 'View all statistics'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_ALL')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Write all statistics to file ---
    t = 'Write all statistics to file'
    listitem = aux_get_generic_listitem(cfg, t, t, common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_STATS_WRITE_FILE')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View ROM scanner reports ---------------------------------------------------------------
    listitem = aux_get_generic_listitem(cfg,
        'View MAME scanner Full archives report',
        ('Report of all MAME machines and the ROM ZIP files, CHDs and Sample ZIP files required '
         'to run each machine.'),
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ARCH_FULL')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME scanner Have archives report',
        ('Report of all MAME machines where you have all the ROM ZIP files, CHDs and Sample ZIP '
         'files necessary to run each machine.'),
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ARCH_HAVE')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME scanner Missing archives report',
        ('Report of all MAME machines where some of all ROM ZIP files, CHDs or Sample ZIP files '
         'are missing.'),
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ARCH_MISS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME scanner Missing ROM ZIP files',
        'Report a list of all Missing ROM ZIP files.',
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ROM_LIST_MISS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME scanner Missing Sample ZIP files',
        'Report a list of all Missing Sample ZIP files.',
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_SAM_LIST_MISS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME scanner Missing CHD files',
        'List of all missing CHD files.',
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_CHD_LIST_MISS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View Software Lists scanner reports ----------------------------------------------------
    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists scanner Full archives report',
        'View Full Software Lists item archives',
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_FULL')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists scanner Have archives report',
        'View Have Software Lists item archives',
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_HAVE')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists scanner Missing archives report',
        'View Missing Software Lists item archives',
        common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_MISS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- Asset scanner reports ------------------------------------------------------------------
    listitem = aux_get_generic_listitem(cfg,
        'View MAME asset scanner report',
        'View MAME asset scanner report', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_MAME_ASSETS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists asset scanner report',
        'View Software Lists asset scanner report', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_SCANNER_SL_ASSETS')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View MAME Audit reports ----------------------------------------------------------------
    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit Machine Full report',
        'View MAME audit report (Full)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_FULL')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit Machine Good report',
        'View MAME audit report (Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit Machine Bad report',
        'View MAME audit report (Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit ROM Good report',
        'View MAME audit report (ROMs Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_ROM_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit ROM Bad report',
        'View MAME audit report (ROM Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_ROM_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit Samples Good report',
        'View MAME audit report (Samples Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_SAM_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit Sample Bad report',
        'View MAME audit report (Sample Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_SAM_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit CHD Good report',
        'View MAME audit report (CHDs Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_CHD_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View MAME audit CHD Bad report',
        'View MAME audit report (CHD Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_MAME_CHD_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- View SL Audit reports ------------------------------------------------------------------
    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit Full report',
        'View SL audit report (Full)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_FULL')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit Good report',
        'View SL audit report (Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit Bad report',
        'View SL audit report (Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit ROM Good report',
        'View SL audit report (ROM Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_ROM_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit ROM Errors report',
        'View SL audit report (ROM Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_ROM_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit CHD Good report',
        'View SL audit report (CHD Good)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_CHD_GOOD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    listitem = aux_get_generic_listitem(cfg,
        'View Software Lists audit CHD Errors report',
        'View SL audit report (CHD Errors)', common_commands)
    url_str = misc_url_2_arg('command', 'EXECUTE_REPORT', 'which', 'VIEW_AUDIT_SL_CHD_BAD')
    xbmcplugin.addDirectoryItem(cfg.addon_handle, url_str, listitem, isFolder = False)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

#----------------------------------------------------------------------------------------------
# Cataloged machines
#----------------------------------------------------------------------------------------------
#
# Renders the Launchers inside a Category for MAME.
#
def render_catalog_list(cfg, catalog_name):
    log_debug('render_catalog_list() Starting...')
    log_debug('render_catalog_list() catalog_name = "{}"'.format(catalog_name))

    # --- General AML plugin check ---
    # Check if databases have been built, print warning messages, etc. This function returns
    # False if no issues, True if there is issues and a dialog has been printed.
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    st_dic = kodi_new_status_dic()
    check_MAME_DB_before_rendering_catalog(cfg, st_dic, control_dic)
    if kodi_is_error_status(st_dic):
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        kodi_display_status_message(st_dic)
        return

    # Render categories in catalog index
    set_Kodi_all_sorting_methods_and_size(cfg)
    mame_view_mode = cfg.settings['mame_view_mode']
    loading_ticks_start = time.time()
    cache_index_dic = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
    if mame_view_mode == VIEW_MODE_FLAT:
        catalog_dic = db_get_cataloged_dic_all(cfg, catalog_name)
    elif mame_view_mode == VIEW_MODE_PCLONE:
        catalog_dic = db_get_cataloged_dic_parents(cfg, catalog_name)
    if not catalog_dic:
        kodi_dialog_OK('Catalog is empty. Rebuild the MAME databases.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    loading_ticks_end = time.time()
    rendering_ticks_start = time.time()
    for catalog_key in sorted(catalog_dic):
        if mame_view_mode == VIEW_MODE_FLAT:
            num_machines = cache_index_dic[catalog_name][catalog_key]['num_machines']
            machine_str = 'machine' if num_machines == 1 else 'machines'
        elif mame_view_mode == VIEW_MODE_PCLONE:
            num_machines = cache_index_dic[catalog_name][catalog_key]['num_parents']
            machine_str = 'parent' if num_machines == 1 else 'parents'
        render_catalog_list_row(cfg, catalog_name, catalog_key, num_machines, machine_str)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()

    # DEBUG Data loading/rendering statistics.
    log_debug('Loading seconds   {}'.format(loading_ticks_end - loading_ticks_start))
    log_debug('Rendering seconds {}'.format(rendering_ticks_end - rendering_ticks_start))

def render_catalog_list_row(cfg, catalog_name, catalog_key, num_machines, machine_str):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    title_str = '{} [COLOR orange]({} {})[/COLOR]'.format(catalog_key, num_machines, machine_str)
    plot_str = 'Catalog {}\nCategory {}'.format(catalog_name, catalog_key)
    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {
        'title' : title_str,      'plot' : plot_str,
        'overlay' : ICON_OVERLAY, 'size' : num_machines
    })

    # --- Artwork ---
    icon_path = cfg.ICON_FILE_PATH.getPath()
    fanart_path = cfg.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    URL_utils = misc_url_3_arg_RunPlugin(
        'command', 'UTILITIES', 'catalog', catalog_name, 'category', catalog_key)
    commands = [
        ('Utilities', URL_utils),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_2_arg('catalog', catalog_name, 'category', catalog_key)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = True)

#
# Renders a list of parent MAME machines knowing the catalog name and the category.
# Also renders machine lists in flat mode.
# Display mode: a) parents only b) all machines (flat)
#
def render_catalog_parent_list(cfg, catalog_name, category_name):
    # When using threads the performance gain is small: from 0.76 to 0.71, just 20 ms.
    # It's not worth it.
    log_debug('render_catalog_parent_list() catalog_name  = {}'.format(catalog_name))
    log_debug('render_catalog_parent_list() category_name = {}'.format(category_name))

    # --- Load ListItem properties (Not used at the moment) ---
    # prop_key = '{} - {}'.format(catalog_name, category_name)
    # log_debug('render_catalog_parent_list() Loading props with key "{}"'.format(prop_key))
    # mame_properties_dic = utils_load_JSON_file_dic(cfg.MAIN_PROPERTIES_PATH.getPath())
    # prop_dic = mame_properties_dic[prop_key]
    # view_mode_property = prop_dic['vm']

    # --- Global properties ---
    view_mode_property = cfg.settings['mame_view_mode']
    log_debug('render_catalog_parent_list() view_mode_property = {}'.format(view_mode_property))

    # --- General AML plugin check ---
    # Check if databases have been built, print warning messages, etc.
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    st_dic = kodi_new_status_dic()
    check_MAME_DB_before_rendering_machines(cfg, st_dic, control_dic)
    if kodi_is_error_status(st_dic):
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        kodi_display_status_message(st_dic)
        return

    # --- Load main MAME info databases and catalog ---
    l_cataloged_dic_start = time.time()
    if view_mode_property == VIEW_MODE_PCLONE:
        catalog_dic = db_get_cataloged_dic_parents(cfg, catalog_name)
    elif view_mode_property == VIEW_MODE_FLAT:
        catalog_dic = db_get_cataloged_dic_all(cfg, catalog_name)
    else:
        kodi_dialog_OK('Wrong view_mode_property = "{}". '.format(view_mode_property) +
                       'This is a bug, please report it.')
        return
    l_cataloged_dic_end = time.time()
    l_render_db_start = time.time()
    if cfg.settings['debug_enable_MAME_render_cache']:
        cache_index_dic = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
        render_db_dic = db_get_render_cache_row(cfg, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME machine cache disabled.')
        render_db_dic = utils_load_JSON_file_dic(cfg.RENDER_DB_PATH.getPath())
    l_render_db_end = time.time()
    l_assets_db_start = time.time()
    if cfg.settings['debug_enable_MAME_asset_cache']:
        if 'cache_index_dic' not in locals():
            cache_index_dic = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
        assets_db_dic = db_get_asset_cache_row(cfg, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME asset cache disabled.')
        assets_db_dic = utils_load_JSON_file_dic(cfg.ASSET_DB_PATH.getPath())
    l_assets_db_end = time.time()
    l_pclone_dic_start = time.time()
    main_pclone_dic = utils_load_JSON_file_dic(cfg.MAIN_PCLONE_DB_PATH.getPath())
    l_pclone_dic_end = time.time()
    l_favs_start = time.time()
    fav_machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
    l_favs_end = time.time()

    # --- Compute loading times ---
    catalog_t = l_cataloged_dic_end - l_cataloged_dic_start
    render_t  = l_render_db_end - l_render_db_start
    assets_t  = l_assets_db_end - l_assets_db_start
    pclone_t  = l_pclone_dic_end - l_pclone_dic_start
    favs_t    = l_favs_end - l_favs_start
    loading_time = catalog_t + render_t + assets_t + pclone_t + favs_t

    # --- Check if catalog is empty ---
    if not catalog_dic:
        kodi_dialog_OK('Catalog is empty. Check out "Setup addon" in the context menu.')
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Process ROMs for rendering ---
    processing_ticks_start = time.time()
    r_list = render_process_machines(cfg, catalog_dic, catalog_name, category_name,
        render_db_dic, assets_db_dic, fav_machines, True, main_pclone_dic, False)
    processing_time = time.time() - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    set_Kodi_all_sorting_methods(cfg)
    render_commit_machines(cfg, r_list)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
    rendering_time = time.time() - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    total_time = loading_time + processing_time + rendering_time
    # log_debug('Loading catalog     {0:.4f} s'.format(catalog_t))
    # log_debug('Loading render db   {0:.4f} s'.format(render_t))
    # log_debug('Loading assets db   {0:.4f} s'.format(assets_t))
    # log_debug('Loading pclone dic  {0:.4f} s'.format(pclone_t))
    # log_debug('Loading MAME favs   {0:.4f} s'.format(favs_t))
    log_debug('Loading time        {0:.4f} s'.format(loading_time))
    log_debug('Processing time     {0:.4f} s'.format(processing_time))
    log_debug('Rendering time      {0:.4f} s'.format(rendering_time))
    log_debug('Total time          {0:.4f} s'.format(total_time))

#
# Renders a list of MAME Clone machines (including parent).
# No need to check for DB existance here. If this function is called is because parents and
# hence all ROMs databases exist.
#
def render_catalog_clone_list(cfg, catalog_name, category_name, parent_name):
    log_debug('render_catalog_clone_list() catalog_name  = {}'.format(catalog_name))
    log_debug('render_catalog_clone_list() category_name = {}'.format(category_name))
    log_debug('render_catalog_clone_list() parent_name   = {}'.format(parent_name))
    display_hide_Mature = cfg.settings['display_hide_Mature']
    display_hide_BIOS = cfg.settings['display_hide_BIOS']
    if catalog_name == 'None' and category_name == 'BIOS': display_hide_BIOS = False
    display_hide_nonworking = cfg.settings['display_hide_nonworking']
    display_hide_imperfect  = cfg.settings['display_hide_imperfect']
    view_mode_property = cfg.settings['mame_view_mode']
    log_debug('render_catalog_clone_list() view_mode_property = {}'.format(view_mode_property))

    # --- Load main MAME info DB ---
    loading_ticks_start = time.time()
    catalog_dic = db_get_cataloged_dic_all(cfg, catalog_name)
    if cfg.settings['debug_enable_MAME_render_cache']:
        cache_index_dic = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
        render_db_dic = db_get_render_cache_row(cfg, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME machine cache disabled.')
        render_db_dic = utils_load_JSON_file_dic(cfg.RENDER_DB_PATH.getPath())
    if cfg.settings['debug_enable_MAME_asset_cache']:
        if 'cache_index_dic' not in locals():
            cache_index_dic = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
        assets_db_dic = db_get_asset_cache_row(cfg, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME asset cache disabled.')
        assets_db_dic = utils_load_JSON_file_dic(cfg.ASSET_DB_PATH.getPath())
    main_pclone_dic = utils_load_JSON_file_dic(cfg.MAIN_PCLONE_DB_PATH.getPath())
    fav_machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
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
    r_list = render_process_machines(cfg, t_catalog_dic, catalog_name, category_name,
        t_render_dic, t_assets_dic, fav_machines, False, main_pclone_dic, False)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    set_Kodi_all_sorting_methods(cfg)
    render_commit_machines(cfg, r_list)
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
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
#     'm_name' : text_type, 'render_name' : text_type,
#     'info' : {}, 'props' : {}, 'art' : {},
#     'context' : [], 'URL' ; text_type
#   }, ...
# ]
#
# By default renders a flat list, main_pclone_dic is not needed and filters are ignored.
# These settings are for rendering the custom MAME filters.
#
def render_process_machines(cfg, catalog_dic, catalog_name, category_name,
    render_db_dic, assets_dic, fav_machines,
    flag_parent_list = False, main_pclone_dic = None, flag_ignore_filters = True):
    # --- Prepare for processing ---
    display_hide_Mature = cfg.settings['display_hide_Mature']
    display_hide_BIOS = cfg.settings['display_hide_BIOS']
    if catalog_name == 'None' and category_name == 'BIOS': display_hide_BIOS = False
    display_hide_nonworking = cfg.settings['display_hide_nonworking']
    display_hide_imperfect  = cfg.settings['display_hide_imperfect']
    display_rom_available = cfg.settings['display_rom_available']
    display_chd_available = cfg.settings['display_chd_available']
    display_MAME_flags = cfg.settings['display_MAME_flags']

    # --- Traverse machines ---
    r_list = []
    for machine_name, render_name in catalog_dic[category_name].items():
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
            num_clones = len(main_pclone_dic[machine_name]) if machine_name in main_pclone_dic else 0

        # --- Render machine name string ---
        display_name = render_name
        if display_MAME_flags:
            # Mark Flags, BIOS, Devices, BIOS, Parent/Clone and Driver status.
            flags_str = ' [COLOR skyblue]{}[/COLOR]'.format(m_assets['flags'])
            if machine['isBIOS']: flags_str += ' [COLOR cyan][BIOS][/COLOR]'
            if machine['isDevice']: flags_str += ' [COLOR violet][Dev][/COLOR]'
            if machine['driver_status'] == 'imperfect':
                flags_str += ' [COLOR yellow][Imp][/COLOR]'
            elif machine['driver_status'] == 'preliminary':
                flags_str += ' [COLOR red][Pre][/COLOR]'
        else:
            flags_str = ''
        if flag_parent_list and num_clones > 0:
            # All machines here are parents. Mark number of clones.
            display_name += ' [COLOR orange] ({} clones)[/COLOR]'.format(num_clones)
            # Machine flags.
            if flags_str: display_name += flags_str
            # Skin flags.
            if machine_name in fav_machines:
                display_name += ' [COLOR violet][Fav][/COLOR]'
                AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
            AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT
        else:
            if flags_str: display_name += flags_str
            if machine_name in fav_machines:
                display_name += ' [COLOR violet][Fav][/COLOR]'
                AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
            if machine['cloneof']:
                display_name += ' [COLOR orange][Clo][/COLOR]'
                AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE
            else:
                AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT

        # --- Assets/artwork ---
        icon_path      = m_assets[cfg.mame_icon] if m_assets[cfg.mame_icon] else 'DefaultProgram.png'
        fanart_path    = m_assets[cfg.mame_fanart]
        banner_path    = m_assets['marquee']
        clearlogo_path = m_assets['clearlogo']
        poster_path    = m_assets['3dbox'] if m_assets['3dbox'] else m_assets['flyer']

        # --- Create listitem row ---
        # Make all the infolabels compatible with Advanced Emulator Launcher
        ICON_OVERLAY = 6
        r_dict['render_name'] = display_name
        if cfg.settings['display_hide_trailers']:
            r_dict['info'] = {
                'title' : display_name, 'year' : machine['year'],
                'genre' : machine['genre'], 'studio' : machine['manufacturer'],
                'plot' : m_assets['plot'], 'overlay' : ICON_OVERLAY,
            }
        else:
            r_dict['info'] = {
                'title' : display_name, 'year' : machine['year'],
                'genre' : machine['genre'], 'studio' : machine['manufacturer'],
                'plot' : m_assets['plot'], 'overlay' : ICON_OVERLAY,
                'trailer' : m_assets['trailer'],
            }
        r_dict['props'] = {
            'nplayers' : machine['nplayers'],
            'platform' : 'MAME',
            'history' : m_assets['history'],
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
                ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
            ]
        else:
            commands = [
                ('Info / Utils', URL_view_DAT),
                ('View / Audit', URL_view),
                ('Add to MAME Favourites', URL_fav),
                ('Kodi File Manager', 'ActivateWindow(filemanager)'),
                ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
            ]
        r_dict['context'] = commands

        # Add row to the list.
        r_dict['URL'] = misc_url_2_arg('command', 'LAUNCH', 'machine', machine_name)
        r_list.append(r_dict)

    return r_list

#
# Renders a processed list of machines/ROMs. Basically, this function only calls the
# Kodi API with the precomputed values.
#
def render_commit_machines(cfg, r_list):
    listitem_list = []

    if kodi_running_version >= KODI_VERSION_LEIA:
        # Kodi Leia and up.
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
    else:
        # Kodi Krypton and down.
        log_debug('Rendering machine list in Kodi Krypton and down.')
        for r_dict in r_list:
            listitem = xbmcgui.ListItem(r_dict['render_name'])
            listitem.setInfo('video', r_dict['info'])
            for prop_name, prop_value in r_dict['props'].items():
                listitem.setProperty(prop_name, prop_value)
            listitem.setArt(r_dict['art'])
            listitem.addContextMenuItems(r_dict['context'])
            listitem_list.append((r_dict['URL'], listitem, False))

    # Add all listitems in one go.
    xbmcplugin.addDirectoryItems(cfg.addon_handle, listitem_list, len(listitem_list))

#
# Not used at the moment -> There are global display settings in addon settings for this.
#
def command_context_display_settings(cfg, catalog_name, category_name):
    # Load ListItem properties.
    log_debug('command_display_settings() catalog_name  "{}"'.format(catalog_name))
    log_debug('command_display_settings() category_name "{}"'.format(category_name))
    prop_key = '{} - {}'.format(catalog_name, category_name)
    log_debug('command_display_settings() Loading props with key "{}"'.format(prop_key))
    mame_properties_dic = utils_load_JSON_file_dic(cfg.MAIN_PROPERTIES_PATH.getPath())
    prop_dic = mame_properties_dic[prop_key]
    dmode_str = 'Parents only' if prop_dic['vm'] == VIEW_MODE_NORMAL else 'Parents and clones'

    # Select menu.
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Display settings', [
        'Display mode (currently {})'.format(dmode_str),
        'Default Icon',
        'Default Fanart',
        'Default Banner',
        'Default Poster',
        'Default Clearlogo'
    ])
    if menu_item < 0: return

    # --- Display settings ---
    if menu_item == 0:
        # Krypton feature: preselect the current item.
        # NOTE Preselect must be called with named parameter, otherwise it does not work well.
        # See http://forum.kodi.tv/showthread.php?tid=250936&pid=2327011#pid2327011
        p_idx = 0 if prop_dic['vm'] == VIEW_MODE_NORMAL else 1
        log_debug('command_display_settings() p_idx = "{}"'.format(p_idx))
        idx = dialog.select('Display mode', ['Parents only', 'Parents and clones'], preselect = p_idx)
        log_debug('command_display_settings() idx = "{}"'.format(idx))
        if idx < 0: return
        if idx == 0:   prop_dic['vm'] = VIEW_MODE_NORMAL
        elif idx == 1: prop_dic['vm'] = VIEW_MODE_ALL

    # --- Change default icon ---
    elif menu_item == 1:
        kodi_dialog_OK('Not coded yet. Sorry')

    # Changes made. Refresh container.
    utils_write_JSON_file(cfg.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    kodi_refresh_container()

#----------------------------------------------------------------------------------------------
# Software Lists
#----------------------------------------------------------------------------------------------
def render_SL_list(cfg, catalog_name):
    log_debug('render_SL_list() catalog_name = {}\n'.format(catalog_name))

    # --- General AML plugin check ---
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    st_dic = kodi_new_status_dic()
    check_SL_DB_before_rendering_catalog(cfg, st_dic, control_dic)
    if kodi_is_error_status(st_dic):
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        kodi_display_status_message(st_dic)
        return

    # --- Load Software List catalog and build render catalog ---
    SL_main_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    SL_catalog_dic = {}
    if catalog_name == 'SL':
        for SL_name, SL_dic in SL_main_catalog_dic.items():
            SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_ROM':
        for SL_name, SL_dic in SL_main_catalog_dic.items():
            if SL_dic['num_with_ROMs'] > 0 and SL_dic['num_with_CHDs'] == 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_CHD':
        for SL_name, SL_dic in SL_main_catalog_dic.items():
            if SL_dic['num_with_ROMs'] == 0 and SL_dic['num_with_CHDs'] > 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_ROM_CHD':
        for SL_name, SL_dic in SL_main_catalog_dic.items():
            if SL_dic['num_with_ROMs'] > 0 and SL_dic['num_with_CHDs'] > 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_empty':
        for SL_name, SL_dic in SL_main_catalog_dic.items():
            if SL_dic['num_with_ROMs'] == 0 and SL_dic['num_with_CHDs'] == 0:
                SL_catalog_dic[SL_name] = SL_dic
    else:
        kodi_dialog_OK('Wrong catalog_name {}'.format(catalog_name))
        return
    log_debug('render_SL_list() len(catalog_name) = {}\n'.format(len(SL_catalog_dic)))

    set_Kodi_all_sorting_methods(cfg)
    for SL_name in SL_catalog_dic:
        SL = SL_catalog_dic[SL_name]
        render_SL_list_row(cfg, SL_name, SL)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_SL_ROMs(cfg, SL_name):
    log_debug('render_SL_ROMs() SL_name "{}"'.format(SL_name))

    # --- General AML plugin check ---
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    st_dic = kodi_new_status_dic()
    check_SL_DB_before_rendering_machines(cfg, st_dic, control_dic)
    if kodi_is_error_status(st_dic):
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        kodi_display_status_message(st_dic)
        return

    # Load ListItem properties (Not used at the moment)
    # SL_properties_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PROP_PATH.getPath())
    # prop_dic = SL_properties_dic[SL_name]
    # Global properties
    view_mode_property = cfg.settings['sl_view_mode']
    log_debug('render_SL_ROMs() view_mode_property = {}'.format(view_mode_property))

    # Load Software List ROMs
    SL_PClone_dic = utils_load_JSON_file_dic(cfg.SL_PCLONE_DIC_PATH.getPath())
    SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
    SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
    SL_roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())
    SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    set_Kodi_all_sorting_methods(cfg)
    SL_proper_name = SL_catalog_dic[SL_name]['display_name']
    if view_mode_property == VIEW_MODE_PCLONE:
        # Get list of parents
        log_debug('render_SL_ROMs() Rendering Parent/Clone launcher')
        parent_list = []
        for parent_name in sorted(SL_PClone_dic[SL_name]): parent_list.append(parent_name)
        for parent_name in parent_list:
            ROM        = SL_roms[parent_name]
            assets     = SL_asset_dic[parent_name] if parent_name in SL_asset_dic else db_new_SL_asset()
            num_clones = len(SL_PClone_dic[SL_name][parent_name])
            ROM['genre'] = SL_proper_name # Add the SL name as 'genre'
            render_SL_ROM_row(cfg, SL_name, parent_name, ROM, assets, True, num_clones)
    elif view_mode_property == VIEW_MODE_FLAT:
        log_debug('render_SL_ROMs() Rendering Flat launcher')
        for rom_name in SL_roms:
            ROM    = SL_roms[rom_name]
            assets = SL_asset_dic[rom_name] if rom_name in SL_asset_dic else db_new_SL_asset()
            ROM['genre'] = SL_proper_name # Add the SL name as 'genre'
            render_SL_ROM_row(cfg, SL_name, rom_name, ROM, assets)
    else:
        kodi_dialog_OK('Wrong vm = "{}". This is a bug, please report it.'.format(prop_dic['vm']))
        return
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_SL_pclone_set(cfg, SL_name, parent_name):
    log_debug('render_SL_pclone_set() SL_name     "{}"'.format(SL_name))
    log_debug('render_SL_pclone_set() parent_name "{}"'.format(parent_name))
    view_mode_property = cfg.settings['sl_view_mode']
    log_debug('render_SL_pclone_set() view_mode_property = {}'.format(view_mode_property))

    # Load Software List ROMs.
    SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    SL_PClone_dic = utils_load_JSON_file_dic(cfg.SL_PCLONE_DIC_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
    SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
    log_debug('render_SL_pclone_set() ROMs JSON "{}"'.format(SL_DB_FN.getPath()))
    SL_roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())

    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
    SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    # Render parent first.
    SL_proper_name = SL_catalog_dic[SL_name]['display_name']
    set_Kodi_all_sorting_methods(cfg)
    ROM = SL_roms[parent_name]
    assets = SL_asset_dic[parent_name] if parent_name in SL_asset_dic else db_new_SL_asset()
    ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
    render_SL_ROM_row(cfg, SL_name, parent_name, ROM, assets, False, view_mode_property)

    # Render clones belonging to parent in this category.
    for clone_name in sorted(SL_PClone_dic[SL_name][parent_name]):
        ROM = SL_roms[clone_name]
        assets = SL_asset_dic[clone_name] if clone_name in SL_asset_dic else db_new_SL_asset()
        ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
        render_SL_ROM_row(cfg, SL_name, clone_name, ROM, assets)
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_SL_list_row(cfg, SL_name, SL):
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
    view_mode_property = cfg.settings['sl_view_mode']
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
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
    ])
    URL = misc_url_2_arg('catalog', 'SL', 'category', SL_name)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = True)

# TODO: render flag if SL item is in Favourites.
def render_SL_ROM_row(cfg, SL_name, rom_name, ROM, assets, flag_parent_list = False, num_clones = 0):
    only_display_SL_items_available = cfg.settings['display_SL_items_available']
    display_SL_flags = cfg.settings['display_SL_flags']

    # Skip SL item rendering if not available. Only skip SL items when the scanner
    # has been done, always render if status is unknown.
    item_not_available = ROM['status_ROM'] == 'r' or ROM['status_CHD'] == 'c'
    if only_display_SL_items_available and item_not_available: return
    display_name = ROM['description']
    if flag_parent_list and num_clones > 0:
        # Print (n clones) and '--' flags.
        display_name += ' [COLOR orange] ({} clones)[/COLOR]'.format(num_clones)
        if display_SL_flags:
            status = '{}{}'.format(ROM['status_ROM'], ROM['status_CHD'])
            display_name += ' [COLOR skyblue]{}[/COLOR]'.format(status)
    else:
        # Print '--' flags and '[Clo]' flag.
        if display_SL_flags:
            status = '{}{}'.format(ROM['status_ROM'], ROM['status_CHD'])
            display_name += ' [COLOR skyblue]{}[/COLOR]'.format(status)
        if ROM['cloneof']: display_name += ' [COLOR orange][Clo][/COLOR]'

    # --- Assets/artwork ---
    icon_path   = assets[cfg.SL_icon] if assets[cfg.SL_icon] else 'DefaultProgram.png'
    fanart_path = assets[cfg.SL_fanart]
    poster_path = assets['3dbox'] if assets['3dbox'] else assets['boxfront']

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    # Make all the infolabels compatible with Advanced Emulator Launcher
    if cfg.settings['display_hide_trailers']:
        listitem.setInfo('video', {
            'title'   : display_name,      'year'    : ROM['year'],
            'genre'   : ROM['genre'],      'studio'  : ROM['publisher'],
            'plot'    : ROM['plot'],       'overlay' : ICON_OVERLAY
        })
    else:
        listitem.setInfo('video', {
            'title'   : display_name,      'year'    : ROM['year'],
            'genre'   : ROM['genre'],      'studio'  : ROM['publisher'],
            'plot'    : ROM['plot'],       'overlay' : ICON_OVERLAY,
            'trailer' : assets['trailer']
        })
    listitem.setProperty('platform', 'MAME Software List')

    # --- Assets ---
    # AEL custom artwork fields.
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
        URL_show_c = misc_url_4_arg_RunPlugin('command', 'EXEC_SHOW_SL_CLONES',
            'catalog', 'SL', 'category', SL_name, 'parent', rom_name)
        commands = [
            ('Info / Utils', URL_view_DAT),
            ('View / Audit', URL_view),
            ('Show clones', URL_show_c),
            ('Add ROM to SL Favourites', URL_fav),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    else:
        commands = [
            ('Info / Utils', URL_view_DAT),
            ('View / Audit', URL_view),
            ('Add ROM to SL Favourites', URL_fav),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_3_arg('command', 'LAUNCH_SL', 'SL', SL_name, 'ROM', rom_name)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = False)

#----------------------------------------------------------------------------------------------
# DATs
#
# catalog = 'History'  / category = '32x' / machine = 'sonic'
# catalog = 'MAMEINFO' / category = '32x' / machine = 'sonic'
# catalog = 'Gameinit' / category = 'None' / machine = 'sonic'
# catalog = 'Command'  / category = 'None' / machine = 'sonic'
#----------------------------------------------------------------------------------------------
def render_DAT_list(cfg, catalog_name):
    # --- Create context menu ---
    commands = [
        ('View', misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
    ]
    # --- Unrolled variables ---
    ICON_OVERLAY = 6

    if catalog_name == 'History':
        # Render list of categories.
        DAT_idx_dic = utils_load_JSON_file_dic(cfg.HISTORY_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods(cfg)
        for key in DAT_idx_dic:
            category_name = '{} [COLOR lightgray]({})[/COLOR]'.format(DAT_idx_dic[key]['name'], key)
            listitem = xbmcgui.ListItem(category_name)
            listitem.setInfo('video', {'title' : category_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_2_arg('catalog', catalog_name, 'category', key)
            xbmcplugin.addDirectoryItem(cfg.addon_handle, url = URL, listitem = listitem, isFolder = True)
    elif catalog_name == 'MAMEINFO':
        # Render list of categories.
        DAT_idx_dic = utils_load_JSON_file_dic(cfg.MAMEINFO_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods(cfg)
        for key in DAT_idx_dic:
            category_name = '{}'.format(key)
            listitem = xbmcgui.ListItem(category_name)
            listitem.setInfo('video', {'title' : category_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_2_arg('catalog', catalog_name, 'category', key)
            xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = True)
    elif catalog_name == 'Gameinit':
        # Render list of machines.
        DAT_idx_dic = utils_load_JSON_file_dic(cfg.GAMEINIT_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods(cfg)
        for machine_key in DAT_idx_dic:
            machine_name = '{} [COLOR lightgray]({})[/COLOR]'.format(DAT_idx_dic[machine_key], machine_key)
            listitem = xbmcgui.ListItem(machine_name)
            listitem.setInfo('video', {'title' : machine_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_3_arg('catalog', catalog_name, 'category', 'None', 'machine', machine_key)
            xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = False)
    elif catalog_name == 'Command':
        # Render list of machines.
        DAT_idx_dic = utils_load_JSON_file_dic(cfg.COMMAND_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
            return
        set_Kodi_all_sorting_methods(cfg)
        for machine_key in DAT_idx_dic:
            machine_name = '{} [COLOR lightgray]({})[/COLOR]'.format(DAT_idx_dic[machine_key], machine_key)
            listitem = xbmcgui.ListItem(machine_name)
            listitem.setInfo('video', {'title' : machine_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = misc_url_3_arg('catalog', catalog_name, 'category', 'None', 'machine', machine_key)
            xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = False)
    else:
        kodi_dialog_OK(
            'DAT database file "{}" not found. Check out "Setup addon" in the context menu.'.format(catalog_name))
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

# Only History.dat and MAMEinfo.dat have categories.
def render_DAT_category(catalog_name, category_name):
    # Load Software List catalog
    if catalog_name == 'History':
        DAT_catalog_dic = utils_load_JSON_file_dic(cfg.HISTORY_IDX_PATH.getPath())
    elif catalog_name == 'MAMEINFO':
        DAT_catalog_dic = utils_load_JSON_file_dic(cfg.MAMEINFO_IDX_PATH.getPath())
    else:
        kodi_dialog_OK('DAT database file "{}" not found. Check out "Setup addon" in the context menu.'.format(catalog_name))
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return
    if not DAT_catalog_dic:
        kodi_dialog_OK('DAT database file "{}" empty.'.format(catalog_name))
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_all_sorting_methods(cfg)
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
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_DAT_category_row(cfg, catalog_name, category_name, machine_key, display_name):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    display_name = '{} [COLOR lightgray]({})[/COLOR]'.format(display_name, machine_key)
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY } )
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('Add-on Settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
    ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_3_arg('catalog', catalog_name, 'category', category_name, 'machine', machine_key)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = False)

def render_DAT_machine_info(cfg, catalog_name, category_name, machine_name):
    log_debug('render_DAT_machine_info() catalog_name "{}"'.format(catalog_name))
    log_debug('render_DAT_machine_info() category_name "{}"'.format(category_name))
    log_debug('render_DAT_machine_info() machine_name "{}"'.format(machine_name))

    if catalog_name == 'History':
        DAT_idx_dic = utils_load_JSON_file_dic(cfg.HISTORY_IDX_PATH.getPath())
        DAT_dic = utils_load_JSON_file_dic(cfg.HISTORY_DB_PATH.getPath())
        display_name, db_list, db_machine = DAT_idx_dic[category_name]['machines'][machine_name].split('|')
        t_str = ('History for [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR] '
            '(DB entry [COLOR=orange]{}[/COLOR] / [COLOR=orange]{}[/COLOR])')
        window_title = t_str.format(category_name, machine_name, db_list, db_machine)
        info_text = DAT_dic[db_list][db_machine]
    elif catalog_name == 'MAMEINFO':
        DAT_dic = utils_load_JSON_file_dic(cfg.MAMEINFO_DB_PATH.getPath())
        t_str = 'MAMEINFO information for [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR]'
        window_title = t_str.format(category_name, machine_name)
        info_text = DAT_dic[category_name][machine_name]
    elif catalog_name == 'Gameinit':
        DAT_dic = utils_load_JSON_file_dic(cfg.GAMEINIT_DB_PATH.getPath())
        window_title = 'Gameinit information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        info_text = DAT_dic[machine_name]
    elif catalog_name == 'Command':
        DAT_dic = utils_load_JSON_file_dic(cfg.COMMAND_DB_PATH.getPath())
        window_title = 'Command information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        info_text = DAT_dic[machine_name]
    else:
        kodi_dialog_OK(
            'Wrong catalog_name "{}". This is a bug, please report it.'.format(catalog_name))
        return

    # --- Show information window ---
    kodi_display_text_window_mono(window_title, info_text)

#
# Not used at the moment -> There are global display settings.
#
def command_context_display_settings_SL(cfg, SL_name):
    log_debug('command_display_settings_SL() SL_name "{}"'.format(SL_name))

    # --- Load properties DB ---
    SL_properties_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PROP_PATH.getPath())
    prop_dic = SL_properties_dic[SL_name]

    # --- Show menu ---
    dmode_str = 'Parents only' if prop_dic['vm'] == VIEW_MODE_NORMAL else 'Parents and clones'
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Display settings', [
        'Display mode (currently {})'.format(dmode_str),
        'Default Icon', 'Default Fanart',
        'Default Banner', 'Default Poster', 'Default Clearlogo'
    ])
    if menu_item < 0: return

    # --- Change display mode ---
    if menu_item == 0:
        p_idx = 0 if prop_dic['vm'] == VIEW_MODE_NORMAL else 1
        log_debug('command_display_settings() p_idx = "{}"'.format(p_idx))
        idx = dialog.select('Display mode', ['Parents only', 'Parents and clones'], preselect = p_idx)
        log_debug('command_display_settings() idx = "{}"'.format(idx))
        if idx < 0: return
        prop_dic['vm'] = VIEW_MODE_NORMAL if idx == 0 else VIEW_MODE_ALL

    # --- Change default icon ---
    elif menu_item == 1:
        kodi_dialog_OK('Not coded yet. Sorry')

    # --- Save display settings ---
    utils_write_JSON_file(cfg.SL_MACHINES_PROP_PATH.getPath(), SL_properties_dic)
    kodi_refresh_container()

# ---------------------------------------------------------------------------------------------
# Information display / Utilities
# ---------------------------------------------------------------------------------------------
def command_context_info_utils(cfg, machine_name, SL_name, SL_ROM, location):
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
    log_debug('command_context_info_utils() machine_name "{}"'.format(machine_name))
    log_debug('command_context_info_utils() SL_name      "{}"'.format(SL_name))
    log_debug('command_context_info_utils() SL_ROM       "{}"'.format(SL_ROM))
    log_debug('command_context_info_utils() location     "{}"'.format(location))
    if machine_name:
        view_type = VIEW_MAME_MACHINE
    elif SL_name:
        view_type = VIEW_SL_ROM
    else:
        raise TypeError('Logic error in command_context_info_utils()')
    log_debug('command_context_info_utils() view_type = {}'.format(view_type))

    if view_type == VIEW_MAME_MACHINE:
        # --- Load DAT indices ---
        History_idx_dic   = utils_load_JSON_file_dic(cfg.HISTORY_IDX_PATH.getPath())
        Mameinfo_idx_dic  = utils_load_JSON_file_dic(cfg.MAMEINFO_IDX_PATH.getPath())
        Gameinit_idx_list = utils_load_JSON_file_dic(cfg.GAMEINIT_IDX_PATH.getPath())
        Command_idx_list  = utils_load_JSON_file_dic(cfg.COMMAND_IDX_PATH.getPath())

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
        History_idx_dic = utils_load_JSON_file_dic(cfg.HISTORY_IDX_PATH.getPath())
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
        kodi_dialog_OK('Wrong view_type = {}. This is a bug, please report it.'.format(view_type))
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
                'view_type == VIEW_MAME_MACHINE and selected_value = {}. '.format(selected_value) +
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
            History_DAT_dic = utils_load_JSON_file_dic(cfg.HISTORY_DB_PATH.getPath())
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
            History_DAT_dic = utils_load_JSON_file_dic(cfg.HISTORY_DB_PATH.getPath())
            t_str = ('History DAT for SL [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR] '
                '(DB entry [COLOR=orange]{}[/COLOR] / [COLOR=orange]{}[/COLOR])')
            window_title = t_str.format(SL_name, SL_ROM, db_list, db_machine)
        kodi_display_text_window_mono(window_title, History_DAT_dic[db_list][db_machine])

    elif action == ACTION_VIEW_MAMEINFO:
        if machine_name not in Mameinfo_idx_dic['mame']:
            kodi_dialog_OK('Machine {} not in Mameinfo DAT'.format(machine_name))
            return
        DAT_dic = utils_load_JSON_file_dic(cfg.MAMEINFO_DB_PATH.getPath())
        t_str = 'MAMEINFO information for [COLOR=orange]{}[/COLOR] item [COLOR=orange]{}[/COLOR]'
        window_title = t_str.format('mame', machine_name)
        kodi_display_text_window_mono(window_title, DAT_dic['mame'][machine_name])

    elif action == ACTION_VIEW_GAMEINIT:
        if machine_name not in Gameinit_idx_list:
            kodi_dialog_OK('Machine {} not in Gameinit DAT'.format(machine_name))
            return
        DAT_dic = utils_load_JSON_file_dic(cfg.GAMEINIT_DB_PATH.getPath())
        window_title = 'Gameinit information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        kodi_display_text_window_mono(window_title, DAT_dic[machine_name])

    elif action == ACTION_VIEW_COMMAND:
        if machine_name not in Command_idx_list:
            kodi_dialog_OK('Machine {} not in Command DAT'.format(machine_name))
            return
        DAT_dic = utils_load_JSON_file_dic(cfg.COMMAND_DB_PATH.getPath())
        window_title = 'Command information for [COLOR=orange]{}[/COLOR]'.format(machine_name)
        kodi_display_text_window_mono(window_title, DAT_dic[machine_name])

    # --- View Fanart ---
    elif action == ACTION_VIEW_FANART:
        if view_type == VIEW_MAME_MACHINE:
            if location == 'STANDARD':
                assets_dic = utils_load_JSON_file_dic(cfg.ASSET_DB_PATH.getPath())
                m_assets = assets_dic[machine_name]
            else:
                mame_favs_dic = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
                m_assets = mame_favs_dic[machine_name]['assets']
            if not m_assets['fanart']:
                kodi_dialog_OK('Fanart for machine {} not found.'.format(machine_name))
                return
        elif view_type == VIEW_SL_ROM:
            SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            m_assets = SL_asset_dic[SL_ROM]
            if not m_assets['fanart']:
                kodi_dialog_OK('Fanart for SL item {} not found.'.format(SL_ROM))
                return

        # If manual found then display it.
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
    # Use the builtin function SlideShow("{}",pause) to show a set of pictures in full screen.
    # See https://forum.kodi.tv/showthread.php?tid=329349
    #
    elif action == ACTION_VIEW_MANUAL:
        # --- Slideshow DEBUG snippet ---
        # https://kodi.wiki/view/List_of_built-in_functions is outdated!
        # See https://github.com/xbmc/xbmc/blob/master/xbmc/interfaces/builtins/PictureBuiltins.cpp
        # '\' in path strings must be escaped like '\\'
        # Builtin function arguments can be in any order (at least for this function).
        # xbmc.executebuiltin('SlideShow("{}",pause)'.format(r'E:\\AML-stuff\\AML-assets\\fanarts\\'))

        # If manual found then display it.
        # First, extract images from the PDF/CBZ.
        # Put the extracted images in a directory named MANUALS_DIR/manual_name.pages/
        # Check the modification times of the PDF manual file witht the timestamp of
        # the first file to regenerate the images if PDF is newer than first extracted img.
        # NOTE CBZ/CBR files are supported by Kodi. It can be extracted with the builtin
        #      function extract. In addition to PDF extension, CBR and CBZ extensions must
        #      also be searched for manuals.
        if view_type == VIEW_MAME_MACHINE:
            log_debug('Displaying Manual for MAME machine {} ...'.format(machine_name))
            # machine = db_get_machine_main_hashed_db(cfg, machine_name)
            assets_dic = utils_load_JSON_file_dic(cfg.ASSET_DB_PATH.getPath())
            if not assets_dic[machine_name]['manual']:
                kodi_dialog_OK('Manual not found in database.')
                return
            man_file_FN = FileName(assets_dic[machine_name]['manual'])
            img_dir_FN = FileName(cfg.settings['assets_path']).pjoin('manuals').pjoin(machine_name + '.pages')
        elif view_type == VIEW_SL_ROM:
            log_debug('Displaying Manual for SL {} item {} ...'.format(SL_name, SL_ROM))
            SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            if not SL_asset_dic[SL_ROM]['manual']:
                kodi_dialog_OK('Manual not found in database.')
                return
            man_file_FN = FileName(SL_asset_dic[SL_ROM]['manual'])
            img_dir_FN = FileName(cfg.settings['assets_path']).pjoin('manuals_SL').pjoin(SL_name).pjoin(SL_ROM + '.pages')
        log_debug('man_file_FN P "{}"'.format(man_file_FN.getPath()))
        log_debug('img_dir_FN P  "{}"'.format(img_dir_FN.getPath()))

        # --- Check for errors ---
        if not man_file_FN.exists():
            kodi_dialog_OK('Manual "{}" not found.'.format(man_file_FN.getPath()))
            return

        # --- Only PDF files supported at the moment ---
        man_ext = man_file_FN.getExt().lower()
        log_debug('Manual file extension "{}"'.format(man_ext))
        if not man_ext == '.pdf':
            kodi_dialog_OK('Only PDF files supported at the moment.')
            return

        # --- If output directory does not exist create it ---
        if not img_dir_FN.exists():
            log_info('Creating DIR "{}"'.format(img_dir_FN.getPath()))
            img_dir_FN.makedirs()

        # OLD CODE
        # status_dic = {
        #     'manFormat' : '', # PDF, CBZ, CBR, ...
        #     'numImages' : 0,
        # }
        # manuals_extract_pages(status_dic, man_file_FN, img_dir_FN)

        # Check if JSON INFO file exists. If so, read it and compare the timestamp of the
        # extraction of the images with the timestamp of the PDF file. Do not extract
        # the images if the images are newer than the PDF.
        status_dic = manuals_check_img_extraction_needed(man_file_FN, img_dir_FN)
        if status_dic['extraction_needed']:
            # Disable PDF image extracion in Python 3 until the problems with the pdfrw library
            # are solved.
            if ADDON_RUNNING_PYTHON_3:
                log_error('Image extraction from PDF files is disabled in Python 3. Exiting.')
                kodi_dialog_OK('Image extraction from PDF files is disabled in Python 3. '
                    'This feature will be ported to Python 3 as soon as possible.')
                return

            log_info('Extracting images from PDF file.')
            # --- Open manual file ---
            manuals_open_PDF_file(status_dic, man_file_FN, img_dir_FN)
            if status_dic['abort_extraction']:
                kodi_dialog_OK('Cannot extract images from file {}'.format(man_file_FN.getPath()))
                return
            manuals_get_PDF_filter_list(status_dic, man_file_FN, img_dir_FN)

            # --- Extract page by page ---
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Extracting manual images...', status_dic['numPages'])
            for page_index in range(status_dic['numPages']):
                pDialog.updateProgressInc()
                manuals_extract_PDF_page(status_dic, man_file_FN, img_dir_FN, page_index)
            manuals_close_PDF_file()
            pDialog.endProgress()

            # --- Create JSON INFO file ---
            manuals_create_INFO_file(status_dic, man_file_FN, img_dir_FN)
        else:
            log_info('Extraction of PDF images skipped.')

        # --- Display page images ---
        if status_dic['numImages'] < 1:
            log_info('No images found. Nothing to show.')
            str_list = [
                'Cannot find images inside the {} file. '.format(status_dic['manFormat']),
                'Check log for more details.'
            ]
            kodi_dialog_OK(''.join(str_list))
            return
        log_info('Rendering images in "{}"'.format(img_dir_FN.getPath()))
        xbmc.executebuiltin('SlideShow("{}",pause)'.format(img_dir_FN.getPath()))

    # --- Display brother machines (same driver) ---
    elif action == ACTION_VIEW_BROTHERS:
        machine = db_get_machine_main_hashed_db(cfg, machine_name)
        # Some (important) drivers have a different name
        sourcefile = machine['sourcefile']
        log_debug('Original driver "{}"'.format(sourcefile))
        mdbn_dic = mame_driver_better_name_dic
        sourcefile = mdbn_dic[sourcefile] if sourcefile in mdbn_dic else sourcefile
        log_debug('Final driver    "{}"'.format(sourcefile))

        # --- Replace current window by search window ---
        # When user press Back in search window it returns to the previous window.
        # NOTE ActivateWindow() / RunPlugin() / RunAddon() seem not to work here
        url = misc_url_2_arg('catalog', 'Driver', 'category', sourcefile)
        log_debug('Container.Update URL "{}"'.format(url))
        xbmc.executebuiltin('Container.Update({})'.format(url))

    # --- Display machines with same Genre ---
    elif action == ACTION_VIEW_SAME_GENRE:
        machine = db_get_machine_main_hashed_db(cfg, machine_name)
        genre_str = machine['genre']
        url = misc_url_2_arg('catalog', 'Genre', 'category', genre_str)
        log_debug('Container.Update URL {}'.format(url))
        xbmc.executebuiltin('Container.Update({})'.format(url))

    # --- Display machines by same Manufacturer ---
    elif action == ACTION_VIEW_SAME_MANUFACTURER:
        machine = db_get_machine_main_hashed_db(cfg, machine_name)
        manufacturer_str = machine['manufacturer']
        url = misc_url_2_arg('catalog', 'Manufacturer', 'category', manufacturer_str)
        log_debug('Container.Update URL {}'.format(url))
        xbmc.executebuiltin('Container.Update({})'.format(url))

    else:
        kodi_dialog_OK('Unknown action == {}. This is a bug, please report it.'.format(action))

# ---------------------------------------------------------------------------------------------
# Information display
# ---------------------------------------------------------------------------------------------
def command_context_view_audit(cfg, machine_name, SL_name, SL_ROM, location):
    VIEW_MAME_MACHINE = 100
    VIEW_SL_ROM       = 200

    ACTION_VIEW_MACHINE_DATA       = 100
    ACTION_VIEW_SL_ITEM_DATA       = 200
    ACTION_VIEW_MACHINE_ROMS       = 300
    ACTION_VIEW_MACHINE_AUDIT_ROMS = 400
    ACTION_VIEW_SL_ITEM_ROMS       = 500
    ACTION_VIEW_SL_ITEM_AUDIT_ROMS = 600
    ACTION_VIEW_MANUAL_JSON        = 700
    ACTION_AUDIT_MAME_MACHINE      = 800
    ACTION_AUDIT_SL_ITEM           = 900

    # --- Determine view type ---
    log_debug('command_context_view_audit() machine_name "{}"'.format(machine_name))
    log_debug('command_context_view_audit() SL_name      "{}"'.format(SL_name))
    log_debug('command_context_view_audit() SL_ROM       "{}"'.format(SL_ROM))
    log_debug('command_context_view_audit() location     "{}"'.format(location))
    if machine_name:
        view_type = VIEW_MAME_MACHINE
    elif SL_name:
        view_type = VIEW_SL_ROM
    else:
        kodi_dialog_OK(
            'In command_context_view_audit(), undetermined view_type. This is a bug, please report it.')
        return
    log_debug('command_context_view_audit() view_type = {}'.format(view_type))

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
        kodi_dialog_OK('Wrong view_type = {}. This is a bug, please report it.'.format(view_type))
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
            kodi_dialog_OK('view_type == VIEW_MAME_MACHINE and selected_value = {}. '.format(selected_value) +
                'This is a bug, please report it.')
            return
    elif view_type == VIEW_SL_ROM:
        if   selected_value == 0: action = ACTION_VIEW_SL_ITEM_DATA
        elif selected_value == 1: action = ACTION_VIEW_SL_ITEM_ROMS
        elif selected_value == 2: action = ACTION_VIEW_SL_ITEM_AUDIT_ROMS
        elif selected_value == 3: action = ACTION_AUDIT_SL_ITEM
        else:
            kodi_dialog_OK('view_type == VIEW_SL_ROM and selected_value = {}. '.format(selected_value) +
                'This is a bug, please report it.')
            return
    else:
        kodi_dialog_OK('Wrong view_type = {}. This is a bug, please report it.'.format(view_type))
        return
    log_debug('command_context_view_audit() action = {}'.format(action))

    # --- Execute action ---
    if action == ACTION_VIEW_MACHINE_DATA:
        action_view_machine_data(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_VIEW_SL_ITEM_DATA:
        action_view_sl_item_data(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_VIEW_MACHINE_ROMS:
        action_view_machine_roms(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_VIEW_MACHINE_AUDIT_ROMS:
        action_view_machine_audit_roms(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_VIEW_SL_ITEM_ROMS:
        action_view_sl_item_roms(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_VIEW_SL_ITEM_AUDIT_ROMS:
        action_view_sl_item_audit_roms(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_AUDIT_MAME_MACHINE:
        action_audit_mame_machine(cfg, machine_name, SL_name, SL_ROM, location)

    elif action == ACTION_AUDIT_SL_ITEM:
        action_audit_sl_item(cfg, machine_name, SL_name, SL_ROM, location)

    # --- View manual JSON INFO file of a MAME machine ---
    elif action == ACTION_VIEW_MANUAL_JSON:
        d_text = 'Loading databases ...'
        pDialog = KodiProgressDialog()
        pDialog.startProgress('{}\n{}'.format(d_text, 'ROM hashed database'), 2)
        machine = db_get_machine_main_hashed_db(cfg, machine_name)
        pDialog.updateProgressInc('{}\n{}'.format(d_text, 'Assets hashed database'))
        assets = db_get_machine_assets_hashed_db(cfg, machine_name)
        pDialog.endProgress()

        if not assets['manual']:
            kodi_dialog_OK('Manual not found in database.')
            return
        man_file_FN = FileName(assets['manual'])
        img_dir_FN = FileName(cfg.settings['assets_path']).pjoin('manuals').pjoin(machine_name + '.pages')
        rom_name = man_file_FN.getBase_noext()
        info_FN = img_dir_FN.pjoin(rom_name + '.json')
        if not info_FN.exists():
            kodi_dialog_OK('Manual JSON INFO file not found. View the manual first.')
            return

        # --- Read stdout and put into a string ---
        window_title = 'MAME machine manual JSON INFO file'
        info_text = utils_load_file_to_str(info_FN.getPath())
        kodi_display_text_window_mono(window_title, info_text)

    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def action_view_machine_data(cfg, machine_name, SL_name, SL_ROM, location):
    pDialog = KodiProgressDialog()
    d_text = 'Loading databases...'
    if location == LOCATION_STANDARD:
        pDialog.startProgress('{}\n{}'.format(d_text, 'ROM hashed database'), 2)
        machine = db_get_machine_main_hashed_db(cfg, machine_name)
        pDialog.updateProgress(1, '{}\n{}'.format(d_text, 'Assets hashed database'))
        assets = db_get_machine_assets_hashed_db(cfg, machine_name)
        pDialog.endProgress()
        window_title = 'MAME Machine Information'

    elif location == LOCATION_MAME_FAVS:
        pDialog.startProgress('{}\n{}'.format(d_text, 'MAME Favourites database'))
        machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
        pDialog.endProgress()
        machine = machines[machine_name]
        assets = machine['assets']
        window_title = 'Favourite MAME Machine Information'

    elif location == LOCATION_MAME_MOST_PLAYED:
        pDialog.startProgress('{}\n{}'.format(d_text, 'MAME Most Played database'))
        most_played_roms_dic = utils_load_JSON_file_dic(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath())
        pDialog.endProgress()
        machine = most_played_roms_dic[machine_name]
        assets = machine['assets']
        window_title = 'Most Played MAME Machine Information'

    elif location == LOCATION_MAME_RECENT_PLAYED:
        pDialog.startProgress('{}\n{}'.format(d_text, 'MAME Recently Played database'))
        recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())
        pDialog.endProgress()
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
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

    # --- Write DEBUG TXT file ---
    if cfg.settings['debug_MAME_machine_data']:
        log_info('Writing file "{}"'.format(cfg.REPORT_DEBUG_MAME_MACHINE_DATA_PATH.getPath()))
        text_remove_color_tags_slist(slist)
        utils_write_slist_to_file(cfg.REPORT_DEBUG_MAME_MACHINE_DATA_PATH.getPath(), slist)

def action_view_sl_item_data(cfg, machine_name, SL_name, SL_ROM, location):
    if location == LOCATION_STANDARD:
        # --- Load databases ---
        SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
        SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_items.json')
        roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())

        # --- Prepare data ---
        rom = roms[SL_ROM]
        assets = SL_asset_dic[SL_ROM]
        SL_dic = SL_catalog_dic[SL_name]
        SL_machine_list = SL_machines_dic[SL_name]
        window_title = 'Software List ROM Information'

    elif location == LOCATION_SL_FAVS:
        # --- Load databases ---
        SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())

        # --- Prepare data ---
        fav_key = SL_name + '-' + SL_ROM
        rom = fav_SL_roms[fav_key]
        assets = rom['assets']
        SL_dic = SL_catalog_dic[SL_name]
        SL_machine_list = SL_machines_dic[SL_name]
        window_title = 'Favourite Software List Item Information'

    elif location == LOCATION_SL_MOST_PLAYED:
        SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        most_played_roms_dic = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())

        # --- Prepare data ---
        fav_key = SL_name + '-' + SL_ROM
        rom = most_played_roms_dic[fav_key]
        assets = rom['assets']
        SL_dic = SL_catalog_dic[SL_name]
        SL_machine_list = SL_machines_dic[SL_name]
        window_title = 'Most Played SL Item Information'

    elif location == LOCATION_SL_RECENT_PLAYED:
        SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        recent_roms_list = utils_load_JSON_file_list(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())

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

    # Build information string.
    slist = []
    mame_info_SL_print(slist, location, SL_name, SL_ROM, rom, assets, SL_dic, SL_machine_list)
    kodi_display_text_window_mono(window_title, '\n'.join(slist))

    # --- Write DEBUG TXT file ---
    if cfg.settings['debug_SL_item_data']:
        log_info('Writing file "{}"'.format(cfg.REPORT_DEBUG_SL_ITEM_DATA_PATH.getPath()))
        text_remove_color_tags_slist(slist)
        utils_write_slist_to_file(cfg.REPORT_DEBUG_SL_ITEM_DATA_PATH.getPath(), slist)

def action_view_machine_roms(cfg, machine_name, SL_name, SL_ROM, location):
    # Load machine dictionary, ROM database and Devices database.
    d_text = 'Loading databases ...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress('{}\n{}'.format(d_text, 'MAME machines main'), 3)
    machine = db_get_machine_main_hashed_db(cfg, machine_name)
    pDialog.updateProgressInc('{}\n{}'.format(d_text, 'MAME machine ROMs'))
    roms_db_dic = utils_load_JSON_file_dic(cfg.ROMS_DB_PATH.getPath())
    pDialog.updateProgressInc('{}\n{}'.format(d_text, 'MAME machine Devices'))
    devices_db_dic = utils_load_JSON_file_dic(cfg.DEVICES_DB_PATH.getPath())
    pDialog.endProgress()

    # --- Make a dictionary with device ROMs ---
    device_roms_list = []
    for device in devices_db_dic[machine_name]:
        device_roms_dic = roms_db_dic[device]
        for rom in device_roms_dic['roms']:
            rom['device_name'] = device
            device_roms_list.append(copy.deepcopy(rom))

    # --- ROM info ---
    info_text = []
    cloneof = machine['cloneof'] if machine['cloneof'] else 'None'
    romof = machine['romof'] if machine['romof'] else 'None'
    info_text.append('[COLOR violet]cloneof[/COLOR] {} / '.format(cloneof) +
        '[COLOR violet]romof[/COLOR] {} / '.format(romof) +
        '[COLOR skyblue]isBIOS[/COLOR] {} / '.format(text_type(machine['isBIOS'])) +
        '[COLOR skyblue]isDevice[/COLOR] {}'.format(text_type(machine['isDevice'])))
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
            table_row = [r_type, text_type(rom['name']), text_type(rom['size']),
                text_type(rom['crc']), text_type(rom['merge']), text_type(rom['bios'])]
            table_str.append(table_row)

    # --- Table: device ROMs ---
    if device_roms_list:
        for rom in device_roms_list:
            table_row = ['DROM', text_type(rom['name']), text_type(rom['size']),
                text_type(rom['crc']), text_type(rom['merge']), text_type(rom['device_name'])]
            table_str.append(table_row)

    # --- Table: machine CHDs ---
    if roms_dic['disks']:
        for disk in roms_dic['disks']:
            table_row = ['DISK', text_type(disk['name']), '', text_type(disk['sha1'])[0:8],
                text_type(disk['merge']), '']
            table_str.append(table_row)

    # --- Table: machine Samples ---
    if roms_dic['samples']:
        for sample in roms_dic['samples']:
            table_row = ['SAM', text_type(sample['name']), '', '', '', '']
            table_str.append(table_row)

    # --- Table: BIOSes ---
    if roms_dic['bios']:
        bios_table_str = []
        bios_table_str.append(['right',     'left'])
        bios_table_str.append(['BIOS name', 'Description'])
        for bios in roms_dic['bios']:
            table_row = [text_type(bios['name']), text_type(bios['description'])]
            bios_table_str.append(table_row)

    # --- Render text information window ---
    table_str_list = text_render_table_str(table_str)
    info_text.extend(table_str_list)
    if roms_dic['bios']:
        bios_table_str_list = text_render_table_str(bios_table_str)
        info_text.append('')
        info_text.extend(bios_table_str_list)
    window_title = 'Machine {} ROMs'.format(machine_name)
    kodi_display_text_window_mono(window_title, '\n'.join(info_text))

    # --- Write DEBUG TXT file ---
    if cfg.settings['debug_MAME_ROM_DB_data']:
        log_info('Writing file "{}"'.format(cfg.REPORT_DEBUG_MAME_MACHINE_ROM_DATA_PATH.getPath()))
        text_remove_color_tags_slist(info_text)
        utils_write_slist_to_file(cfg.REPORT_DEBUG_MAME_MACHINE_ROM_DATA_PATH.getPath(), info_text)

def action_view_machine_audit_roms(cfg, machine_name, SL_name, SL_ROM, location):
    log_debug('command_context_view() View Machine ROMs (Audit database)')
    d_text = 'Loading databases...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress('{}\n{}'.format(d_text, 'MAME machine hash'), 3)
    machine = db_get_machine_main_hashed_db(cfg, machine_name)
    pDialog.updateProgressInc('{}\n{}'.format(d_text, 'MAME ROM Audit'))
    audit_roms_dic = utils_load_JSON_file_dic(cfg.ROM_AUDIT_DB_PATH.getPath())
    pDialog.updateProgressInc('{}\n{}'.format(d_text, 'Machine archives'))
    machine_archives = utils_load_JSON_file_dic(cfg.ROM_SET_MACHINE_FILES_DB_PATH.getPath())
    pDialog.endProgress()

    # --- Grab data and settings ---
    rom_list = audit_roms_dic[machine_name]
    cloneof = machine['cloneof']
    romof = machine['romof']
    rom_set = ROMSET_NAME_LIST[cfg.settings['mame_rom_set']]
    chd_set = CHDSET_NAME_LIST[cfg.settings['mame_chd_set']]
    log_debug('command_context_view() machine {}'.format(machine_name))
    log_debug('command_context_view() cloneof {}'.format(cloneof))
    log_debug('command_context_view() romof   {}'.format(romof))
    log_debug('command_context_view() rom_set {}'.format(rom_set))
    log_debug('command_context_view() chd_set {}'.format(chd_set))

    # --- Generate report ---
    info_text = []
    cloneof = machine['cloneof'] if machine['cloneof'] else 'None'
    romof = machine['romof'] if machine['romof'] else 'None'
    info_text.append('[COLOR violet]cloneof[/COLOR] {} / '.format(cloneof) +
        '[COLOR violet]romof[/COLOR] {} / '.format(romof) +
        '[COLOR skyblue]isBIOS[/COLOR] {} / '.format(text_type(machine['isBIOS'])) +
        '[COLOR skyblue]isDevice[/COLOR] {}'.format(text_type(machine['isDevice'])))
    info_text.append('MAME ROM set [COLOR orange]{}[/COLOR] / '.format(rom_set) +
        'MAME CHD set [COLOR orange]{}[/COLOR]'.format(chd_set))
    info_text.append('')

    # --- Audit ROM table ---
    # Table cell padding: left, right
    # Table columns: Type - ROM name - Size - CRC/SHA1 - Merge - BIOS - Location
    table_str = [
        ['right', 'left', 'right', 'left', 'left'],
        ['Type', 'ROM name', 'Size', 'CRC/SHA1', 'Location'],
    ]
    for m_rom in rom_list:
        if m_rom['type'] == ROM_TYPE_DISK:
            sha1_str = text_type(m_rom['sha1'])[0:8]
            table_row = [text_type(m_rom['type']), text_type(m_rom['name']), '', sha1_str, m_rom['location']]
        elif m_rom['type'] == ROM_TYPE_SAMPLE:
            table_row = [text_type(m_rom['type']), text_type(m_rom['name']), '', '', text_type(m_rom['location'])]
        else:
            table_row = [text_type(m_rom['type']), text_type(m_rom['name']), text_type(m_rom['size']),
                text_type(m_rom['crc']), text_type(m_rom['location'])]
        table_str.append(table_row)
    info_text.extend(text_render_table_str(table_str))
    info_text.append('')

    # --- ZIP/CHD/Sample file list ---
    table_str = [
        ['right', 'left'],
        ['Type', 'File name'],
    ]
    for m_file in machine_archives[machine_name]['ROMs']:
        table_str.append(['ROM', '[COLOR orange]ROM_path[/COLOR]/' + m_file + '.zip'])
    for m_file in machine_archives[machine_name]['CHDs']:
        table_str.append(['CHD', '[COLOR orange]CHD_path[/COLOR]/' + m_file + '.chd'])
    for m_file in machine_archives[machine_name]['Samples']:
        table_str.append(['Sample', '[COLOR orange]Samples_path[/COLOR]/' + m_file + '.zip'])
    info_text.extend(text_render_table_str(table_str))

    window_title = 'Machine {} ROM audit'.format(machine_name)
    kodi_display_text_window_mono(window_title, '\n'.join(info_text))

    # --- Write DEBUG TXT file ---
    if cfg.settings['debug_MAME_Audit_DB_data']:
        log_info('Writing file "{}"'.format(cfg.REPORT_DEBUG_MAME_MACHINE_AUDIT_DATA_PATH.getPath()))
        text_remove_color_tags_slist(info_text)
        utils_write_slist_to_file(cfg.REPORT_DEBUG_MAME_MACHINE_AUDIT_DATA_PATH.getPath(), info_text)

def action_view_sl_item_roms(cfg, machine_name, SL_name, SL_ROM, location):
    SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_items.json')
    SL_ROMS_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_ROMs.json')
    # SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    # SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
    # assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    # SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
    # SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())
    # SL_dic = SL_catalog_dic[SL_name]
    # SL_machine_list = SL_machines_dic[SL_name]
    # assets = SL_asset_dic[SL_ROM] if SL_ROM in SL_asset_dic else db_new_SL_asset()
    roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())
    roms_db = utils_load_JSON_file_dic(SL_ROMS_DB_FN.getPath())
    rom = roms[SL_ROM]
    rom_db_list = roms_db[SL_ROM]

    cloneof = rom['cloneof'] if rom['cloneof'] else 'None'
    info_text = []
    info_text.append('[COLOR violet]SL_name[/COLOR] {}'.format(SL_name))
    info_text.append('[COLOR violet]SL_ROM[/COLOR] {}'.format(SL_ROM))
    info_text.append('[COLOR violet]description[/COLOR] {}'.format(rom['description']))
    info_text.append('[COLOR violet]cloneof[/COLOR] {}'.format(cloneof))
    info_text.append('')

    table_str = []
    table_str.append(['left',      'left',       'left',      'left',   'left',         'left', 'left'])
    table_str.append(['Part name', 'Part iface', 'Area type', 'A name', 'ROM/CHD name', 'Size', 'CRC/SHA1'])
    # Iterate Parts
    for part_dic in rom_db_list:
        part_name = part_dic['part_name']
        part_interface = part_dic['part_interface']
        if 'dataarea' in part_dic:
            # Iterate Dataareas
            for dataarea_dic in part_dic['dataarea']:
                dataarea_name = dataarea_dic['name']
                # Interate ROMs in dataarea
                for rom_dic in dataarea_dic['roms']:
                    table_row = [part_name, part_interface, 'dataarea', dataarea_name,
                        rom_dic['name'], text_type(rom_dic['size']), rom_dic['crc']]
                    table_str.append(table_row)
        if 'diskarea' in part_dic:
            # Iterate Diskareas
            for diskarea_dic in part_dic['diskarea']:
                diskarea_name = diskarea_dic['name']
                # Iterate DISKs in diskarea
                for rom_dic in diskarea_dic['disks']:
                    table_row = [part_name, part_interface, 'diskarea', diskarea_name,
                        rom_dic['name'], '', rom_dic['sha1'][0:8]]
                    table_str.append(table_row)
    table_str_list = text_render_table_str(table_str)
    info_text.extend(table_str_list)
    window_title = 'Software List ROM List (ROMs DB)'
    kodi_display_text_window_mono(window_title, '\n'.join(info_text))

    # --- Write DEBUG TXT file ---
    if cfg.settings['debug_SL_ROM_DB_data']:
        log_info('Writing file "{}"'.format(cfg.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH.getPath()))
        text_remove_color_tags_slist(info_text)
        utils_write_slist_to_file(cfg.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH.getPath(), info_text)

def action_view_sl_item_audit_roms(cfg, machine_name, SL_name, SL_ROM, location):
    SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_items.json')
    # SL_ROMs_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_roms.json')
    SL_ROM_Audit_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_ROM_audit.json')

    roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())
    rom_audit_db = utils_load_JSON_file_dic(SL_ROM_Audit_DB_FN.getPath())
    rom = roms[SL_ROM]
    rom_db_list = rom_audit_db[SL_ROM]

    cloneof = rom['cloneof'] if rom['cloneof'] else 'None'
    info_text = []
    info_text.append('[COLOR violet]SL_name[/COLOR] {}'.format(SL_name))
    info_text.append('[COLOR violet]SL_ROM[/COLOR] {}'.format(SL_ROM))
    info_text.append('[COLOR violet]description[/COLOR] {}'.format(rom['description']))
    info_text.append('[COLOR violet]cloneof[/COLOR] {}'.format(cloneof))
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
                text_type(rom_dic['size']), rom_dic['crc'], rom_dic['location']]
            table_str.append(table_row)
    table_str_list = text_render_table_str(table_str)
    info_text.extend(table_str_list)
    window_title = 'Software List ROM List (Audit DB)'
    kodi_display_text_window_mono(window_title, '\n'.join(info_text))

    # --- Write DEBUG TXT file ---
    if cfg.settings['debug_SL_Audit_DB_data']:
        log_info('Writing file "{}"'.format(cfg.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH.getPath()))
        text_remove_color_tags_slist(info_text)
        utils_write_slist_to_file(cfg.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH.getPath(), info_text)

def action_audit_mame_machine(cfg, machine_name, SL_name, SL_ROM, location):
    # --- Load machine dictionary and ROM database ---
    rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][cfg.settings['mame_rom_set']]
    log_debug('command_context_view() Auditing Machine ROMs\n')
    log_debug('command_context_view() rom_set {}\n'.format(rom_set))

    d_text = 'Loading databases...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress('{}\n{}'.format(d_text, 'MAME machine hash'), 2)
    machine = db_get_machine_main_hashed_db(cfg, machine_name)
    pDialog.updateProgressInc('{}\n{}'.format(d_text, 'MAME ROM Audit'))
    audit_roms_dic = utils_load_JSON_file_dic(cfg.ROM_AUDIT_DB_PATH.getPath())
    pDialog.endProgress()

    # --- Grab data and settings ---
    rom_list = audit_roms_dic[machine_name]
    cloneof = machine['cloneof']
    romof = machine['romof']
    log_debug('command_context_view() machine {}\n'.format(machine_name))
    log_debug('command_context_view() cloneof {}\n'.format(cloneof))
    log_debug('command_context_view() romof   {}\n'.format(romof))

    # --- Open ZIP file, check CRC32 and also CHDs ---
    audit_dic = db_new_audit_dic()
    mame_audit_MAME_machine(cfg, rom_list, audit_dic)

    # --- Generate report ---
    info_text = []
    cloneof = machine['cloneof'] if machine['cloneof'] else 'None'
    romof = machine['romof'] if machine['romof'] else 'None'
    info_text.append('[COLOR violet]cloneof[/COLOR] {} / '.format(cloneof) +
        '[COLOR violet]romof[/COLOR] {} / '.format(romof) +
        '[COLOR skyblue]isBIOS[/COLOR] {} / '.format(text_type(machine['isBIOS'])) +
        '[COLOR skyblue]isDevice[/COLOR] {}'.format(text_type(machine['isDevice'])))
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
            table_row = [text_type(m_rom['type']), text_type(m_rom['name']), '', '',
                m_rom['location'], m_rom['status_colour']]
        else:
            table_row = [text_type(m_rom['type']), text_type(m_rom['name']),
                text_type(m_rom['size']), text_type(m_rom['crc']), m_rom['location'], m_rom['status_colour']]
        table_str.append(table_row)
    table_str_list = text_render_table_str(table_str)
    info_text.extend(table_str_list)
    window_title = 'Machine {} ROM audit'.format(machine_name)
    kodi_display_text_window_mono(window_title, '\n'.join(info_text))

def action_audit_sl_item(cfg, machine_name, SL_name, SL_ROM, location):
    # --- Load machine dictionary and ROM database ---
    log_debug('command_context_view() Auditing SL Software ROMs\n')
    log_debug('command_context_view() SL_name {}\n'.format(SL_name))
    log_debug('command_context_view() SL_ROM {}\n'.format(SL_ROM))

    SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_items.json')
    SL_ROM_Audit_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_ROM_audit.json')

    roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())
    roms_audit_db = utils_load_JSON_file_dic(SL_ROM_Audit_DB_FN.getPath())
    rom = roms[SL_ROM]
    rom_db_list = roms_audit_db[SL_ROM]

    # --- Open ZIP file and check CRC32 ---
    audit_dic = db_new_audit_dic()
    SL_ROM_path_FN = FileName(cfg.settings['SL_rom_path'])
    SL_CHD_path_FN = FileName(cfg.settings['SL_chd_path'])
    mame_audit_SL_machine(SL_ROM_path_FN, SL_CHD_path_FN, SL_name, SL_ROM, rom_db_list, audit_dic)

    info_text = [
        '[COLOR violet]SL_name[/COLOR] {}'.format(SL_name),
        '[COLOR violet]SL_ROM[/COLOR] {}'.format(SL_ROM),
        '[COLOR violet]description[/COLOR] {}'.format(rom['description']),
        '',
    ]

    # --- Table header and rows ---
    # Do not render ROM name in SLs, cos they are really long.
    # table_str = [    ['right', 'left',     'right', 'left',     'left',     'left'] ]
    # table_str.append(['Type',  'ROM name', 'Size',  'CRC/SHA1', 'Location', 'Status'])
    table_str = [    ['right', 'right', 'left',     'left',     'left'] ]
    table_str.append(['Type',  'Size',  'CRC/SHA1', 'Location', 'Status'])
    for m_rom in rom_db_list:
        if m_rom['type'] == ROM_TYPE_DISK:
            table_row = [m_rom['type'], # m_rom['name'],
                '', m_rom['sha1'][0:8], m_rom['location'], m_rom['status_colour']]
            table_str.append(table_row)
        else:
            table_row = [m_rom['type'], # m_rom['name'],
                text_type(m_rom['size']), m_rom['crc'], m_rom['location'], m_rom['status_colour']]
            table_str.append(table_row)
    table_str_list = text_render_table_str(table_str)
    info_text.extend(table_str_list)
    window_title = 'SL {} Software {} ROM audit'.format(SL_name, SL_ROM)
    kodi_display_text_window_mono(window_title, '\n'.join(info_text))

def command_context_utilities(cfg, catalog_name, category_name):
    log_debug('command_context_utilities() catalog_name  "{}"'.format(catalog_name))
    log_debug('command_context_utilities() category_name "{}"'.format(category_name))

    d_list = [
      'Export AEL Virtual Launcher',
    ]
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Export AEL Virtual Launcher ---
    if selected_value == 0:
        log_debug('command_context_utilities() Export AEL Virtual Launcher')

        # Ask user for a path to export the launcher configuration
        vlauncher_str_name = 'AML_VLauncher_' + catalog_name + '_' + category_name + '.xml'
        dir_path = kodi_dialog_get_directory('Select XML export directory')
        if not dir_path: return
        export_FN = FileName(dir_path).pjoin(vlauncher_str_name)
        if export_FN.exists():
            ret = kodi_dialog_yesno('Overwrite file {}?'.format(export_FN.getPath()))
            if not ret:
                kodi_notify_warn('Export of Launcher XML cancelled')
                return

        kodi_dialog_OK('Not implemented yet, sorry!')
        return

        # --- Open databases and get list of machines of this filter ---
        # This can be optimized: load stuff from the cache instead of the main databases.
        db_files = [
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Print error message is something goes wrong writing file ---
        try:
            catalog_dic = db_get_cataloged_dic_parents(cfg, catalog_name)
            db_export_Virtual_Launcher(export_FN, catalog_dic[category_name],
                db_dic['machines'], db_dic['renderdb'], db_dic['assetsdb'])
        except KodiAddonError as ex:
            kodi_display_exception(ex)
        else:
            kodi_notify('Exported Virtual Launcher "{}"'.format(vlauncher_str_name))

# -------------------------------------------------------------------------------------------------
# MAME Favorites/Recently Played/Most played
# -------------------------------------------------------------------------------------------------
# Favorites use the main hashed database, not the main and render databases.
def command_context_add_mame_fav(cfg, machine_name):
    log_debug('command_add_mame_fav() Machine_name "{}"'.format(machine_name))

    # Get Machine database entry. Use MAME hashed database for speed.
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    machine = db_get_machine_main_hashed_db(cfg, machine_name)
    assets = db_get_machine_assets_hashed_db(cfg, machine_name)
    fav_machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())

    # If machine already in Favourites ask user if overwrite.
    if machine_name in fav_machines:
        ret = kodi_dialog_yesno('Machine {} ({}) '.format(machine['description'], machine_name) +
            'already in MAME Favourites. Overwrite?')
        if ret < 1: return

    # Add machine. Add database version to Favourite.
    fav_machine = db_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic)
    fav_machines[machine_name] = fav_machine
    log_info('command_add_mame_fav() Added machine "{}"'.format(machine_name))

    # Save Favourites
    utils_write_JSON_file(cfg.FAV_MACHINES_PATH.getPath(), fav_machines)
    kodi_notify('Machine {} added to MAME Favourites'.format(machine_name))
    kodi_refresh_container()

def render_fav_machine_row(cfg, m_name, machine, m_assets, location):
    # --- Default values for flags ---
    AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_NONE

    # --- Mark Flags, BIOS, Devices, BIOS, Parent/Clone and Driver status ---
    display_name = machine['description']
    display_name += ' [COLOR skyblue]{}[/COLOR]'.format(m_assets['flags'])
    if machine['isBIOS']:   display_name += ' [COLOR cyan][BIOS][/COLOR]'
    if machine['isDevice']: display_name += ' [COLOR violet][Dev][/COLOR]'
    if machine['cloneof']:  display_name += ' [COLOR orange][Clo][/COLOR]'
    if   machine['driver_status'] == 'imperfect':   display_name += ' [COLOR yellow][Imp][/COLOR]'
    elif machine['driver_status'] == 'preliminary': display_name += ' [COLOR red][Pre][/COLOR]'
    # Render number of number the ROM has been launched
    if location == LOCATION_MAME_MOST_PLAYED:
        if machine['launch_count'] == 1:
            display_name = '{} [COLOR orange][{} time][/COLOR]'.format(display_name, machine['launch_count'])
        else:
            display_name = '{} [COLOR orange][{} times][/COLOR]'.format(display_name, machine['launch_count'])

    # --- Skin flags ---
    AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE if machine['cloneof'] else AEL_PCLONE_STAT_VALUE_PARENT

    # --- Assets/artwork ---
    icon_path      = m_assets[cfg.mame_icon] if m_assets[cfg.mame_icon] else 'DefaultProgram.png'
    fanart_path    = m_assets[cfg.mame_fanart]
    banner_path    = m_assets['marquee']
    clearlogo_path = m_assets['clearlogo']
    poster_path    = m_assets['3dbox'] if m_assets['3dbox'] else m_assets['flyer']

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)

    # --- Metadata ---
    # Make all the infotables compatible with Advanced Emulator Launcher
    if cfg.settings['display_hide_trailers']:
        listitem.setInfo('video', {
            'title'   : display_name,     'year'    : machine['year'],
            'genre'   : machine['genre'], 'studio'  : machine['manufacturer'],
            'plot'    : m_assets['plot'],
            'overlay' : ICON_OVERLAY
        })
    else:
        listitem.setInfo('video', {
            'title'   : display_name,     'year'    : machine['year'],
            'genre'   : machine['genre'], 'studio'  : machine['manufacturer'],
            'plot'    : m_assets['plot'], 'trailer' : m_assets['trailer'],
            'overlay' : ICON_OVERLAY
        })
    listitem.setProperty('nplayers', machine['nplayers'])
    listitem.setProperty('platform', 'MAME')

    # --- Assets ---
    # AEL custom artwork fields
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
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    elif location == LOCATION_MAME_MOST_PLAYED:
        URL_manage = misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_MOST_PLAYED', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Most Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    elif location == LOCATION_MAME_RECENT_PLAYED:
        URL_manage = misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_RECENT_PLAYED', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Recently Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_3_arg('command', 'LAUNCH', 'machine', m_name, 'location', location)
    xbmcplugin.addDirectoryItem(handle = cfg.addon_handle, url = URL, listitem = listitem, isFolder = False)

def command_show_mame_fav(cfg):
    log_debug('command_show_mame_fav() Starting ...')

    # --- Open Favourite Machines dictionary ---
    fav_machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
    if not fav_machines:
        kodi_dialog_OK('No Favourite MAME machines. Add some machines to MAME Favourites first.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Render Favourites ---
    set_Kodi_all_sorting_methods(cfg)
    for m_name in fav_machines:
        machine = fav_machines[m_name]
        assets  = machine['assets']
        render_fav_machine_row(cfg, m_name, machine, assets, LOCATION_MAME_FAVS)
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

#
# Context menu "Manage Favourite machines"
#
def command_context_manage_mame_fav(cfg, machine_name):
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
    log_debug('machine_name "{}"'.format(machine_name))
    if machine_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage MAME Favourite machines', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {}'.format(action))

    # --- Execute actions ---
    if action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_mame_fav() ACTION_DELETE_MACHINE')
        log_debug('machine_name "{}"'.format(machine_name))
        db_files = [
            ['fav_machines', 'MAME Favourite machines', cfg.FAV_MACHINES_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Ask user for confirmation ---
        desc = db_dic['fav_machines'][machine_name]['description']
        ret = kodi_dialog_yesno('Delete Machine {} ({})?'.format(desc, machine_name))
        if ret < 1:
            kodi_notify('MAME Favourites unchanged')
            return

        # --- Delete machine and save DB ---
        del db_dic['fav_machines'][machine_name]
        log_info('Deleted machine "{}"'.format(machine_name))
        utils_write_JSON_file(cfg.FAV_MACHINES_PATH.getPath(), db_dic['fav_machines'])
        kodi_refresh_container()
        kodi_notify('Machine {} deleted from MAME Favourites'.format(machine_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_mame_fav() ACTION_DELETE_ALL')
        db_files = [
            ['fav_machines', 'MAME Favourite machines', cfg.FAV_MACHINES_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # Confirm with user
        ret = kodi_dialog_yesno(
            'You have {} MAME Favourites. Delete them all?'.format(len(db_dic['fav_machines'])))
        if ret < 1:
            kodi_notify('MAME Favourites unchanged')
            return

        # Database is an empty dictionary
        utils_write_JSON_file(cfg.FAV_MACHINES_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all MAME Favourites')

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_mame_fav() ACTION_DELETE_MISSING')

        # --- Ensure MAME Catalog have been built ---
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        st_dic = kodi_new_status_dic()
        options = check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, control_dic)
        if kodi_display_status_message(st_dic): return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['fav_machines', 'MAME Favourite machines', cfg.FAV_MACHINES_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Delete missing MAME machines ---
        num_deleted_machines = 0
        if len(db_dic['fav_machines']) >= 1:
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Delete missing MAME Favourites...', len(db_dic['fav_machines']))
            new_fav_machines = {}
            for fav_key in sorted(db_dic['fav_machines']):
                pDialog.updateProgressInc()
                log_debug('Checking Favourite "{}"'.format(fav_key))
                if fav_key in db_dic['machines']:
                    new_fav_machines[fav_key] = db_dic['fav_machines'][fav_key]
                else:
                    num_deleted_machines += 1
            utils_write_JSON_file(cfg.FAV_MACHINES_PATH.getPath(), new_fav_machines)
            pDialog.endProgress()
            kodi_refresh_container()
        if num_deleted_machines > 0:
            kodi_notify('Deleted {} missing MAME machines'.format(num_deleted_machines))
        else:
            kodi_notify('No missing machines found')

    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_mame_most_played(cfg):
    most_played_roms_dic = utils_load_JSON_file_dic(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if not most_played_roms_dic:
        kodi_dialog_OK('No Most Played MAME machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method(cfg)
    sorted_dic = sorted(most_played_roms_dic, key = lambda x : most_played_roms_dic[x]['launch_count'], reverse = True)
    for machine_name in sorted_dic:
        machine = most_played_roms_dic[machine_name]
        render_fav_machine_row(cfg, machine['name'], machine, machine['assets'], LOCATION_MAME_MOST_PLAYED)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_mame_most_played(cfg, machine_name):
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
    log_debug('machine_name "{}"'.format(machine_name))
    if machine_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage MAME Most Played machines', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {}'.format(action))

    # --- Execute actions ---
    if action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_mame_most_played() ACTION_DELETE_MACHINE')
        db_files = [
            ['most_played_roms', 'MAME Most Played machines', cfg.MAME_MOST_PLAYED_FILE_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Ask user for confirmation ---
        desc = db_dic['most_played_roms'][machine_name]['description']
        ret = kodi_dialog_yesno('Delete Machine {} ({})?'.format(desc, machine_name))
        if ret < 1:
            kodi_notify('MAME Most Played unchanged')
            return

        # --- Delete machine and save DB ---
        del db_dic['most_played_roms'][machine_name]
        log_info('Deleted machine "{}"'.format(machine_name))
        utils_write_JSON_file(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath(), db_dic['most_played_roms'])
        kodi_refresh_container()
        kodi_notify('Machine {} deleted from MAME Most Played'.format(machine_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_mame_most_played() ACTION_DELETE_ALL')
        db_files = [
            ['most_played_roms', 'MAME Most Played machines', cfg.MAME_MOST_PLAYED_FILE_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # Confirm with user
        num_machines = len(db_dic['most_played_roms'])
        ret = kodi_dialog_yesno(
            'You have {} MAME Most Played machines. Delete them all?'.format(num_machines))
        if ret < 1:
            kodi_notify('MAME Most Played unchanged')
            return

        # Database is an empty dictionary
        utils_write_JSON_file(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all MAME Most Played'.format(machine_name))

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_mame_most_played() ACTION_DELETE_MISSING')

        # --- Ensure MAME Catalog have been built ---
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        st_dic = kodi_new_status_dic()
        options = check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, control_dic)
        if kodi_display_status_message(st_dic): return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['most_played_roms', 'MAME Most Played machines', cfg.MAME_MOST_PLAYED_FILE_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Delete missing MAME machines ---
        num_deleted_machines = 0
        if len(db_dic['most_played_roms']) >= 1:
            pDialog = xbmcgui.DialogProgress()
            pDialog.startProgress('Delete missing MAME Most Played...', len(db_dic['most_played_roms']))
            new_fav_machines = {}
            for fav_key in sorted(db_dic['most_played_roms']):
                pDialog.updateProgressInc()
                log_debug('Checking Favourite "{}"'.format(fav_key))
                if fav_key in db_dic['machines']:
                    new_fav_machines[fav_key] = db_dic['most_played_roms'][fav_key]
                else:
                    num_deleted_machines += 1
            utils_write_JSON_file(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath(), new_fav_machines)
            pDialog.endProgress()
            kodi_refresh_container()
        if num_deleted_machines > 0:
            kodi_notify('Deleted {} missing MAME machines'.format(num_deleted_machines))
        else:
            kodi_notify('No missing machines found')
    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_mame_recently_played(cfg):
    recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    if not recent_roms_list:
        kodi_dialog_OK('No Recently Played MAME machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method(cfg)
    for machine in recent_roms_list:
        render_fav_machine_row(cfg, machine['name'], machine, machine['assets'], LOCATION_MAME_RECENT_PLAYED)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_mame_recent_played(cfg, machine_name):
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
    log_debug('machine_name "{}"'.format(machine_name))
    if machine_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage MAME Recently Played machines', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {}'.format(action))

    # --- Execute actions ---
    if action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_mame_recent_played() ACTION_DELETE_MACHINE')
        log_debug('machine_name "{}"'.format(machine_name))

        # --- Load Recently Played machine list ---
        recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # --- Search index of this machine in the list ---
        machine_index = db_locate_idx_by_name(recent_roms_list, machine_name)
        if machine_index < 0:
            a = 'Machine {} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(machine_name))
            return

        # --- Ask user for confirmation ---
        desc = recent_roms_list[machine_index]['description']
        ret = kodi_dialog_yesno('Delete Machine {} ({})?'.format(desc, machine_name))
        if ret < 1:
            kodi_notify('MAME Recently Played unchanged')
            return

        # --- Delete machine and save DB ---
        recent_roms_list.pop(machine_index)
        log_info('Deleted machine "{}"'.format(machine_name))
        utils_write_JSON_file(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        kodi_refresh_container()
        kodi_notify('Machine {} deleted from MAME Recently Played'.format(machine_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_mame_recent_played() ACTION_DELETE_ALL')
        recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # Confirm with user
        num_machines = len(recent_roms_list)
        ret = kodi_dialog_yesno(
            'You have {} MAME Recently Played. Delete them all?'.format(num_machines))
        if ret < 1:
            kodi_notify('MAME Recently Played unchanged')
            return

        # Database is an empty list.
        utils_write_JSON_file(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath(), list())
        kodi_refresh_container()
        kodi_notify('Deleted all MAME Recently Played'.format(machine_name))

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_mame_recent_played() ACTION_DELETE_MISSING')

        # --- Ensure MAME Catalog have been built ---
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        st_dic = kodi_new_status_dic()
        options = check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, control_dic)
        if kodi_display_status_message(st_dic): return False

        # --- Load databases ---
        db_files = [
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)
        recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # --- Delete missing MAME machines ---
        num_deleted_machines = 0
        if len(recent_roms_list) >= 1:
            pDialog = KodiProgressDialog()
            pDialog.startProgress('Delete missing MAME Recently Played...', len(recent_roms_list))
            new_recent_roms_list = []
            for i, recent_rom in enumerate(recent_roms_list):
                pDialog.updateProgressInc()
                fav_key = recent_rom['name']
                log_debug('Checking Favourite "{}"'.format(fav_key))
                if fav_key in db_dic['machines']:
                    new_recent_roms_list.append(recent_rom)
                else:
                    num_deleted_machines += 1
            utils_write_JSON_file(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath(), new_recent_roms_list)
            pDialog.endProgress()
            kodi_refresh_container()
        if num_deleted_machines > 0:
            kodi_notify('Deleted {} missing MAME machines'.format(num_deleted_machines))
        else:
            kodi_notify('No missing machines found')

    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

# -------------------------------------------------------------------------------------------------
# SL Favourites/Recently Played/Most played
# -------------------------------------------------------------------------------------------------
def command_context_add_sl_fav(cfg, SL_name, ROM_name):
    log_debug('command_add_sl_fav() SL_name  "{}"'.format(SL_name))
    log_debug('command_add_sl_fav() ROM_name "{}"'.format(ROM_name))

    # --- Load databases ---
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
    SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
    SL_roms = utils_load_JSON_file_dic(SL_DB_FN.getPath())
    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
    SL_assets_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    # Open Favourite Machines dictionary.
    fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
    SL_fav_key = SL_name + '-' + ROM_name
    log_debug('command_add_sl_fav() SL_fav_key "{}"'.format(SL_fav_key))

    # >> If machine already in Favourites ask user if overwrite.
    if SL_fav_key in fav_SL_roms:
        ret = kodi_dialog_yesno('Machine {} ({}) '.format(ROM_name, SL_name) +
                                'already in SL Favourites. Overwrite?')
        if ret < 1: return

    # Add machine to SL Favourites.
    SL_ROM = SL_roms[ROM_name]
    # SL_assets = SL_assets_dic[ROM_name] if ROM_name in SL_assets_dic else db_new_SL_asset()
    SL_assets = SL_assets_dic[ROM_name]
    fav_ROM = db_get_SL_Favourite(SL_name, ROM_name, SL_ROM, SL_assets, control_dic)
    fav_SL_roms[SL_fav_key] = fav_ROM
    log_info('command_add_sl_fav() Added machine "{}" ("{}")'.format(ROM_name, SL_name))

    # Save Favourites
    utils_write_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
    kodi_notify('ROM {} added to SL Favourite ROMs'.format(ROM_name))

def render_sl_fav_machine_row(cfg, SL_fav_key, ROM, assets, location):
    SL_name  = ROM['SL_name']
    SL_ROM_name = ROM['SL_ROM_name']
    display_name = ROM['description']

    # --- Mark Status and Clones ---
    status = '{}{}'.format(ROM['status_ROM'], ROM['status_CHD'])
    display_name += ' [COLOR skyblue]{}[/COLOR]'.format(status)
    if ROM['cloneof']:  display_name += ' [COLOR orange][Clo][/COLOR]'
    # Render number of number the ROM has been launched
    if location == LOCATION_SL_MOST_PLAYED:
        if ROM['launch_count'] == 1:
            display_name = '{} [COLOR orange][{} time][/COLOR]'.format(display_name, ROM['launch_count'])
        else:
            display_name = '{} [COLOR orange][{} times][/COLOR]'.format(display_name, ROM['launch_count'])

    # --- Assets/artwork ---
    icon_path   = assets[cfg.SL_icon] if assets[cfg.SL_icon] else 'DefaultProgram.png'
    fanart_path = assets[cfg.SL_fanart]
    poster_path = assets['3dbox'] if assets['3dbox'] else assets['boxfront']

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    # Make all the infolabels compatible with Advanced Emulator Launcher
    if cfg.settings['display_hide_trailers']:
        listitem.setInfo('video', {
            'title' : display_name, 'year' : ROM['year'],
            'genre' : ROM['genre'], 'studio' : ROM['publisher'],
            'plot' : ROM['plot'], 'overlay' : ICON_OVERLAY,
        })
    else:
        listitem.setInfo('video', {
            'title' : display_name, 'year' : ROM['year'],
            'genre' : ROM['genre'], 'studio' : ROM['publisher'],
            'plot' : ROM['plot'], 'overlay' : ICON_OVERLAY,
            'trailer' : assets['trailer'],
        })
    listitem.setProperty('platform', 'MAME Software List')

    # --- Assets ---
    # AEL custom artwork fields
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
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__)),
        ]
    elif location == LOCATION_SL_MOST_PLAYED:
        URL_manage = misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_MOST_PLAYED', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage SL Most Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    elif location == LOCATION_SL_RECENT_PLAYED:
        URL_manage = misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_RECENT_PLAYED', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage SL Recently Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
        ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_4_arg('command', 'LAUNCH_SL', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = False)

def command_show_sl_fav(cfg):
    log_debug('command_show_sl_fav() Starting ...')

    SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
    if not fav_SL_roms:
        kodi_dialog_OK('No Favourite Software Lists ROMs. Add some ROMs to SL Favourites first.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    # Render Favourites
    set_Kodi_all_sorting_methods(cfg)
    for SL_fav_key in fav_SL_roms:
        SL_fav_ROM = fav_SL_roms[SL_fav_key]
        assets = SL_fav_ROM['assets']
        # Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        render_sl_fav_machine_row(cfg, SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_FAVS)
    xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)

#
# Context menu "Manage SL Favourite ROMs"
#
def command_context_manage_sl_fav(cfg, SL_name, ROM_name):
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
    log_debug('SL_name  "{}" / ROM_name "{}"'.format(SL_name, ROM_name))
    if SL_name and ROM_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage SL Favourite itmes', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {}'.format(action))

    # --- Execute actions ---
    if action == ACTION_CHOOSE_DEFAULT:
        log_debug('command_context_manage_sl_fav() ACTION_CHOOSE_DEFAULT')

        # --- Load Favs ---
        fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name

        # --- Get a list of machines that can launch this SL ROM. User chooses. ---
        SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
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
        utils_write_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        kodi_notify('Deafult machine set to {} ({})'.format(machine_name, machine_desc))

    # --- Delete ROM from SL Favourites ---
    elif action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_sl_fav() ACTION_DELETE_MACHINE')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        desc = most_played_roms_dic[SL_fav_key]['description']
        a = 'Delete SL Item {} ({} / {})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1:
            kodi_notify('SL Favourites unchanged')
            return

        # --- Delete machine and save DB ---
        del fav_SL_roms[SL_fav_key]
        log_info('Deleted machine {} ({})'.format(SL_name, ROM_name))
        utils_write_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        kodi_refresh_container()
        kodi_notify('SL Item {}-{} deleted from SL Favourites'.format(SL_name, ROM_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_sl_fav() ACTION_DELETE_ALL')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        ret = kodi_dialog_yesno(
            'You have {} SL Favourites. Delete them all?'.format(len(fav_SL_roms)))
        if ret < 1:
            kodi_notify('SL Favourites unchanged')
            return

        # --- Delete machine and save DB ---
        utils_write_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all SL Favourites')

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_sl_fav() ACTION_DELETE_MISSING BEGIN...')
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
        if len(fav_SL_roms) < 1:
            kodi_notify('SL Favourites empty')
            return
        pDialog = KodiProgressDialog()
        pDialog.startProgress('Advanced MAME Launcher', len(fav_SL_roms))
        num_items_deleted = 0
        for fav_SL_key in sorted(fav_SL_roms):
            fav_SL_name = fav_SL_roms[fav_SL_key]['SL_name']
            fav_ROM_name = fav_SL_roms[fav_SL_key]['SL_ROM_name']
            log_debug('Checking SL Favourite "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))

            # Update progress dialog.
            pDialog.updateProgressInc('Checking SL Favourites...\nItem "{}"'.format(fav_ROM_name))

            # --- Load SL ROMs DB and assets ---
            SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_items.json')
            SL_roms = utils_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

            # --- Check ---
            if fav_ROM_name not in SL_roms:
                num_items_deleted += 1
                del fav_SL_roms[fav_ROM_name]
                log_info('Deleted machine {} ({})'.format(fav_SL_name, fav_ROM_name))
            else:
                log_debug('Machine {} ({}) OK'.format(fav_SL_name, fav_ROM_name))
        utils_write_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        pDialog.close()
        if num_items_deleted > 0:
            kodi_notify('Deleted {} items'.format(num_items_deleted))
        else:
            kodi_notify('No items deleted')

    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_SL_most_played(cfg):
    SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    most_played_roms_dic = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
    if not most_played_roms_dic:
        kodi_dialog_OK('No Most Played SL machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method(cfg)
    sorted_dic = sorted(most_played_roms_dic, key = lambda x : most_played_roms_dic[x]['launch_count'], reverse = True)
    for SL_fav_key in sorted_dic:
        SL_fav_ROM = most_played_roms_dic[SL_fav_key]
        assets = SL_fav_ROM['assets']
        # Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        render_sl_fav_machine_row(cfg, SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_MOST_PLAYED)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_SL_most_played(cfg, SL_name, ROM_name):
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
    log_debug('SL_name  "{}" / ROM_name "{}"'.format(SL_name, ROM_name))
    if SL_name and ROM_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage SL Most Played', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {}'.format(action))

    # --- Execute actions ---
    if action == ACTION_CHOOSE_DEFAULT:
        log_debug('command_context_manage_sl_most_played() ACTION_CHOOSE_DEFAULT')
        kodi_dialog_OK('ACTION_CHOOSE_DEFAULT not implemented yet. Sorry.')

    elif action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_sl_most_played() ACTION_DELETE_MACHINE')

        # --- Load Most Played items dictionary ---
        most_played_roms_dic = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        desc = most_played_roms_dic[SL_fav_key]['description']
        a = 'Delete SL Item {} ({} / {})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1:
            kodi_notify('SL Most Played unchanged')
            return

        # --- Delete machine and save DB ---
        del most_played_roms_dic[SL_fav_key]
        a = 'Deleted SL_name "{}" / ROM_name "{}"'
        log_info(a.format(SL_name, ROM_name))
        utils_write_JSON_file(cfg.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
        kodi_refresh_container()
        kodi_notify('Item {}-{} deleted from SL Most Played'.format(SL_name, ROM_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_sl_most_played() ACTION_DELETE_ALL')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        ret = kodi_dialog_yesno(
            'You have {} SL Most Played. Delete them all?'.format(len(fav_SL_roms)))
        if ret < 1:
            kodi_notify('SL Most Played unchanged')
            return

        # --- Delete machine and save DB ---
        utils_write_JSON_file(cfg.SL_MOST_PLAYED_FILE_PATH.getPath(), dict())
        kodi_refresh_container()
        kodi_notify('Deleted all SL Most Played')

    elif action == ACTION_DELETE_MISSING:
        log_debug('command_context_manage_sl_most_played() ACTION_DELETE_MISSING')
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        fav_SL_roms = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
        if len(fav_SL_roms) < 1:
            kodi_notify('SL Most Played empty')
            return
        d_text = 'Checking SL Most Played...'
        pDialog = KodiProgressDialog()
        pDialog.startProgress(d_text, len(fav_SL_roms))
        num_items_deleted = 0
        for fav_SL_key in sorted(fav_SL_roms):
            fav_SL_name = fav_SL_roms[fav_SL_key]['SL_name']
            fav_ROM_name = fav_SL_roms[fav_SL_key]['SL_ROM_name']
            log_debug('Checking SL Most Played "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
            pDialog.updateProgressInc('{}\nItem "{}"'.format(d_text, fav_ROM_name))

            # --- Load SL ROMs DB and assets ---
            SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_items.json')
            SL_roms = utils_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

            # --- Check ---
            if fav_ROM_name not in SL_roms:
                num_items_deleted += 1
                del fav_SL_roms[fav_ROM_name]
                log_info('Deleted machine {} ({})'.format(fav_SL_name, fav_ROM_name))
            else:
                log_debug('Machine {} ({}) OK'.format(fav_SL_name, fav_ROM_name))
        utils_write_JSON_file(cfg.SL_MOST_PLAYED_FILE_PATH.getPath(), fav_SL_roms)
        pDialog.endProgress()
        if num_items_deleted > 0:
            kodi_notify('Deleted {} items'.format(num_items_deleted))
        else:
            kodi_notify('No items deleted')

    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

def command_show_SL_recently_played(cfg):
    SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
    recent_roms_list = utils_load_JSON_file_list(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())
    if not recent_roms_list:
        kodi_dialog_OK('No Recently Played SL machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    set_Kodi_unsorted_method(cfg)
    for SL_fav_ROM in recent_roms_list:
        SL_fav_key = SL_fav_ROM['SL_DB_key']
        assets = SL_fav_ROM['assets']
        # Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        render_sl_fav_machine_row(cfg, SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_RECENT_PLAYED)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def command_context_manage_SL_recent_played(cfg, SL_name, ROM_name):
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
    log_debug('SL_name  "{}" / ROM_name "{}"'.format(SL_name, ROM_name))
    if SL_name and ROM_name:
        view_type = VIEW_INSIDE_MENU
    else:
        view_type = VIEW_ROOT_MENU
    log_debug('view_type = {}'.format(view_type))

    # --- Build menu base on view_type (Polymorphic menu, determine action) ---
    d_list = [menu[0] for menu in menus_dic[view_type]]
    selected_value = xbmcgui.Dialog().select('Manage SL Recently Played', d_list)
    if selected_value < 0: return
    action = menus_dic[view_type][selected_value][1]
    log_debug('action = {}'.format(action))

    # --- Execute actions ---
    if action == ACTION_CHOOSE_DEFAULT:
        log_debug('command_context_manage_SL_recent_played() ACTION_CHOOSE_DEFAULT')
        kodi_dialog_OK('ACTION_CHOOSE_DEFAULT not implemented yet. Sorry.')

    elif action == ACTION_DELETE_MACHINE:
        log_debug('command_context_manage_SL_recent_played() Delete SL Recently Played machine')

        # --- Load Recently Played machine list ---
        recent_roms_list = utils_load_JSON_file_list(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())
        machine_index = db_locate_idx_by_SL_item_name(recent_roms_list, SL_name, ROM_name)
        if machine_index < 0:
            a = 'Item {}-{} cannot be located in SL Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(SL_name, ROM_name))
            return

        # --- Ask user for confirmation ---
        desc = recent_roms_list[machine_index]['description']
        a = 'Delete SL Item {} ({} / {})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1:
            kodi_notify('SL Recently Played unchanged')
            return

        # --- Delete machine and save DB ---
        recent_roms_list.pop(machine_index)
        a = 'Deleted SL_name "{}" / ROM_name "{}"'
        log_info(a.format(SL_name, ROM_name))
        utils_write_JSON_file(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        kodi_refresh_container()
        kodi_notify('SL Item {}-{} deleted from SL Recently Played'.format(SL_name, ROM_name))

    elif action == ACTION_DELETE_ALL:
        log_debug('command_context_manage_SL_recent_played() ACTION_DELETE_ALL')

        # --- Open Favourite Machines dictionary ---
        fav_SL_roms = utils_load_JSON_file_dic(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('SL_fav_key "{}"'.format(SL_fav_key))

        # --- Ask user for confirmation ---
        ret = kodi_dialog_yesno(
            'You have {} SL Recently Played. Delete them all?'.format(len(fav_SL_roms)))
        if ret < 1:
            kodi_notify('SL Recently Played unchanged')
            return

        # --- Delete machine and save DB ---
        utils_write_JSON_file(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath(), list())
        kodi_refresh_container()
        kodi_notify('Deleted all SL Recently Played')

    elif action == ACTION_DELETE_MISSING:
        # Careful because here fav_SL_roms is a list and not a dictionary.
        log_debug('command_context_manage_SL_recent_played() ACTION_DELETE_MISSING')
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        fav_SL_roms = utils_load_JSON_file_dic(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())
        if len(fav_SL_roms) < 1:
            kodi_notify_warn('SL Recently Played empty')
            return
        d_text = 'Checking SL Recently Played...'
        pDialog = KodiProgressDialog()
        pDialog.startProgress(d_text, len(fav_SL_roms))
        num_items_deleted = 0
        new_fav_SL_roms = []
        # fav_SL_roms is a list, do not sort it!
        for fav_SL_item in fav_SL_roms:
            fav_SL_name = fav_SL_item['SL_name']
            fav_ROM_name = fav_SL_item['SL_ROM_name']
            log_debug('Checking SL Recently Played "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
            pDialog.updateProgressInc('{}\nItem "{}"'.format(d_text, fav_ROM_name))

            # --- Load SL ROMs DB and assets ---
            SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_catalog_dic[fav_SL_name]['rom_DB_noext'] + '_items.json')
            SL_roms = utils_load_JSON_file_dic(SL_DB_FN.getPath(), verbose = False)

            # --- Check ---
            if fav_ROM_name not in SL_roms:
                num_items_deleted += 1
                log_info('Deleted machine {} ({})'.format(fav_SL_name, fav_ROM_name))
            else:
                new_fav_SL_roms.append(fav_SL_item)
                log_debug('Machine {} ({}) OK'.format(fav_SL_name, fav_ROM_name))
        utils_write_JSON_file(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath(), new_fav_SL_roms)
        pDialog.endProgress()
        if num_items_deleted > 0:
            kodi_notify('Deleted {} items'.format(num_items_deleted))
        else:
            kodi_notify('No items deleted')
    else:
        t = 'Wrong action == {}. This is a bug, please report it.'.format(action)
        log_error(t)
        kodi_dialog_OK(t)

# ---------------------------------------------------------------------------------------------
# Custom MAME filters
# Custom filters behave like standard catalogs.
# Custom filters are defined in a XML file, the XML file is processed and the custom catalogs
# created from the main database.
# Custom filters do not have parent and all machines lists. They are always rendered in flat mode.
# ---------------------------------------------------------------------------------------------
def command_context_setup_custom_filters(cfg):
    menu_item = xbmcgui.Dialog().select('Setup AML custom filters', [
        'Build custom filter databases',
        'Test custom filter XML',
        'View custom filter XML',
        'View filter histogram report',
        'View filter XML syntax report',
        'View filter database report',
    ])
    if menu_item < 0: return

    # --- Build custom filter databases ---
    if menu_item == 0:
        # Open main ROM databases
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME machines render', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME machine assets', cfg.ASSET_DB_PATH.getPath()],
            ['machine_archives', 'Machine archives', cfg.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)
        # Compatibility with "All in one" code.
        audit_dic = { 'machine_archives' : db_dic['machine_archives'] }

        # --- Make a dictionary of machines to be filtered ---
        (main_filter_dic, sets_dic) = filter_get_filter_DB(cfg, db_dic)

        # --- Parse custom filter XML and check for errors ---
        # 1) Check the filter XML syntax and filter semantic errors.
        # 2) Produces report cfg.REPORT_CF_XML_SYNTAX_PATH
        (filter_list, f_st_dic) = filter_custom_filters_load_XML(cfg, db_dic, main_filter_dic, sets_dic)
        # If no filters defined sayonara.
        if len(filter_list) < 1:
            kodi_notify_warn('Filter XML has no filter definitions')
            return
        # If errors found in the XML sayonara.
        if f_st_dic['XML_errors']:
            kodi_dialog_OK('Custom filter database build cancelled because the XML filter '
                'definition file contains errors. Have a look at the XML filter file report, '
                'correct the mistakes and try again.')
            return

        # --- Build filter database ---
        # 1) Saves control_dic (updated custom filter build timestamp).
        # 2) Generates cfg.REPORT_CF_DB_BUILD_PATH
        filter_build_custom_filters(cfg, db_dic, filter_list, main_filter_dic)

        # --- So long and thanks for all the fish ---
        kodi_notify('Custom filter database built')

    # --- Test custom filter XML ---
    elif menu_item == 1:
        # Open main ROM databases
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME machines render', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME machine assets', cfg.ASSET_DB_PATH.getPath()],
            ['machine_archives', 'Machine archives list', cfg.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Make a dictionary of machines to be filtered ---
        # This currently includes all MAME parent machines.
        # However, it must include all machines (parent and clones).
        (main_filter_dic, sets_dic) = filter_get_filter_DB(cfg, db_dic)

        # --- Parse custom filter XML and check for errors ---
        # This function also check the filter XML syntax and produces a report.
        (filter_list, f_st_dic) = filter_custom_filters_load_XML(cfg, db_dic, main_filter_dic, sets_dic)
        # If no filters sayonara
        if len(filter_list) < 1:
            kodi_notify_warn('Filter XML has no filter definitions')
            return
        # If errors found in the XML sayonara
        elif f_st_dic['XML_errors']:
            kodi_dialog_OK(
                'The XML filter definition file contains errors. Have a look at the '
                'XML filter file report, fix the mistakes and try again.')
            return
        kodi_notify('Custom filter XML check succesful')

    # --- View custom filter XML ---
    elif menu_item == 2:
        cf_XML_path_str = cfg.settings['filter_XML']
        log_debug('cf_XML_path_str = "{}"'.format(cf_XML_path_str))
        if not cf_XML_path_str:
            log_debug('Using default XML custom filter.')
            XML_FN = cfg.CUSTOM_FILTER_PATH
        else:
            log_debug('Using user-defined in addon settings XML custom filter.')
            XML_FN = FileName(cf_XML_path_str)
        log_debug('command_context_setup_custom_filters() Displaying "{}"'.format(XML_FN.getOriginalPath()))
        if not XML_FN.exists():
            kodi_dialog_OK('Custom filter XML file not found.')
            return
        kodi_display_text_window_mono('Custom filter XML', utils_load_file_to_str(XML_FN.getPath()))

    # --- View filter histogram report ---
    elif menu_item == 3:
        filename_FN = cfg.REPORT_CF_HISTOGRAMS_PATH
        log_debug('command_context_setup_custom_filters() Displaying "{}"'.format(filename_FN.getOriginalPath()))
        if not filename_FN.exists():
            kodi_dialog_OK('Filter histogram report not found.')
            return
        kodi_display_text_window_mono('Filter histogram report', utils_load_file_to_str(filename_FN.getPath()))

    # --- View filter XML syntax report ---
    elif menu_item == 4:
        filename_FN = cfg.REPORT_CF_XML_SYNTAX_PATH
        log_debug('command_context_setup_custom_filters() Displaying "{}"'.format(filename_FN.getOriginalPath()))
        if not filename_FN.exists():
            kodi_dialog_OK('Filter XML filter syntax report not found.')
            return
        fstring = utils_load_file_to_str(filename_FN.getPath())
        kodi_display_text_window_mono('Custom filter XML syntax report', fstring)

    # --- View filter report ---
    elif menu_item == 5:
        filename_FN = cfg.REPORT_CF_DB_BUILD_PATH
        log_debug('command_context_setup_custom_filters() Displaying "{}"'.format(filename_FN.getOriginalPath()))
        if not filename_FN.exists():
            kodi_dialog_OK('Custom filter database report not found.')
            return
        fstring = utils_load_file_to_str(filename_FN.getPath())
        kodi_display_text_window_mono('Custom filter XML syntax report', fstring)

def command_show_custom_filters(cfg):
    log_debug('command_show_custom_filters() Starting ...')

    # Open Custom filter count database and index
    filter_index_dic = utils_load_JSON_file_dic(cfg.FILTERS_INDEX_PATH.getPath())
    if not filter_index_dic:
        kodi_dialog_OK('MAME custom filter index is empty. Please rebuild your filters.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    # Check if filters need to be rebuilt
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    if control_dic['t_Custom_Filter_build'] < control_dic['t_MAME_Catalog_build']:
        kodi_dialog_OK('MAME custom filters need to be rebuilt.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Render Custom Filters, always in flat mode ---
    mame_view_mode = cfg.settings['mame_view_mode']
    set_Kodi_all_sorting_methods(cfg)
    for f_name in sorted(filter_index_dic, key = lambda x: filter_index_dic[x]['order'], reverse = False):
        num_machines = filter_index_dic[f_name]['num_machines']
        machine_str = 'machine' if num_machines == 1 else 'machines'
        render_custom_filter_item_row(cfg, f_name, num_machines, machine_str, filter_index_dic[f_name]['plot'])
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)

def render_custom_filter_item_row(cfg, f_name, num_machines, machine_str, plot):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    title_str = '{} [COLOR orange]({} {})[/COLOR]'.format(f_name, num_machines, machine_str)
    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str, 'plot' : plot, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = cfg.ICON_FILE_PATH.getPath()
    fanart_path = cfg.FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({})'.format(cfg.__addon_id__))
    ]
    listitem.addContextMenuItems(commands)
    URL = misc_url_2_arg('catalog', 'Custom', 'category', f_name)
    xbmcplugin.addDirectoryItem(cfg.addon_handle, URL, listitem, isFolder = True)

#
# Renders a custom filter list of machines, always in flat mode.
#
def render_custom_filter_machines(cfg, filter_name):
    log_debug('render_custom_filter_machines() filter_name  = {}'.format(filter_name))

    # Global properties.
    view_mode_property = cfg.settings['mame_view_mode']
    log_debug('render_custom_filter_machines() view_mode_property = {}'.format(view_mode_property))

    # Check id main DB exists.
    if not cfg.RENDER_DB_PATH.exists():
        kodi_dialog_OK('MAME database not found. Check out "Setup addon" in the context menu.')
        xbmcplugin.endOfDirectory(handle = cfg.addon_handle, succeeded = True, cacheToDisc = False)
        return

    # Load main MAME info DB and catalog.
    l_cataloged_dic_start = time.time()
    Filters_index_dic = utils_load_JSON_file_dic(cfg.FILTERS_INDEX_PATH.getPath())
    rom_DB_noext = Filters_index_dic[filter_name]['rom_DB_noext']
    l_cataloged_dic_end = time.time()
    l_render_db_start = time.time()
    render_db_dic = utils_load_JSON_file_dic(cfg.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_render.json').getPath())
    l_render_db_end = time.time()
    l_assets_db_start = time.time()
    assets_db_dic = utils_load_JSON_file_dic(cfg.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_assets.json').getPath())
    l_assets_db_end = time.time()
    l_favs_start = time.time()
    fav_machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
    l_favs_end = time.time()

    # Compute loading times.
    catalog_t = l_cataloged_dic_end - l_cataloged_dic_start
    render_t = l_render_db_end - l_render_db_start
    assets_t = l_assets_db_end - l_assets_db_start
    favs_t   = l_favs_end - l_favs_start
    loading_time = catalog_t + render_t + assets_t + favs_t

    # Check if catalog is empty
    if not render_db_dic:
        kodi_dialog_OK('Catalog is empty. Check out "Setup addon" in the context menu.')
        xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
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
    r_list = render_process_machines(cfg, catalog_dic, catalog_name, category_name,
        render_db_dic, assets_db_dic, fav_machines)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    set_Kodi_all_sorting_methods(cfg)
    render_commit_machines(cfg, r_list)
    xbmcplugin.endOfDirectory(cfg.addon_handle, succeeded = True, cacheToDisc = False)
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
def check_MAME_DB_status(st_dic, condition, ctrl_dic):
    if not ctrl_dic:
        log_debug('check_MAME_DB_status() ERROR: Control dictionary empty.')
        t = ('MAME control file not found. You need to build the MAME main database '
            'using the context menu "Setup addon" in the AML main window.')
        kodi_set_error_status(st_dic, t)
    elif condition == MAME_MAIN_DB_BUILT:
        test_MAIN_DB_BUILT = True if ctrl_dic['t_MAME_DB_build'] > 0.0 else False
        if not test_MAIN_DB_BUILT:
            log_debug('check_MAME_DB_status() ERROR: MAME_MAIN_DB_BUILT fails.')
            t = 'MAME Main database needs to be built. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_MAME_DB_status() MAME_MAIN_DB_BUILT OK')
    elif condition == MAME_AUDIT_DB_BUILT:
        test_AUDIT_DB_BUILT = True if ctrl_dic['t_MAME_Audit_DB_build'] > ctrl_dic['t_MAME_DB_build'] else False
        if not test_AUDIT_DB_BUILT:
            log_debug('check_MAME_DB_status() ERROR: MAME_AUDIT_DB_BUILT fails.')
            t = 'MAME Audit database needs to be built. Use the context menu "Setup addon " in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_MAME_DB_status() MAME_AUDIT_DB_BUILT OK')
            check_MAME_DB_status(st_dic, MAME_MAIN_DB_BUILT, ctrl_dic)
    elif condition == MAME_CATALOG_BUILT:
        test_CATALOG_BUILT = True if ctrl_dic['t_MAME_Catalog_build'] > ctrl_dic['t_MAME_Audit_DB_build'] else False
        if not test_CATALOG_BUILT:
            log_debug('check_MAME_DB_status() ERROR: MAME_CATALOG_BUILT fails.')
            t = 'MAME Catalog database needs to be built. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_MAME_DB_status() MAME_CATALOG_BUILT OK')
            check_MAME_DB_status(st_dic, MAME_AUDIT_DB_BUILT, ctrl_dic)
    elif condition == MAME_MACHINES_SCANNED:
        test_MACHINES_SCANNED = True if ctrl_dic['t_MAME_ROMs_scan'] > ctrl_dic['t_MAME_Catalog_build'] else False
        if not test_MACHINES_SCANNED:
            log_debug('check_MAME_DB_status() ERROR: MAME_MACHINES_SCANNED fails.')
            t = 'MAME machines need to be scanned. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_MAME_DB_status() MAME_MACHINES_SCANNED OK')
            check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, ctrl_dic)
    elif condition == MAME_ASSETS_SCANNED:
        test_ASSETS_SCANNED = True if ctrl_dic['t_MAME_assets_scan'] > ctrl_dic['t_MAME_ROMs_scan'] else False
        if not test_ASSETS_SCANNED:
            log_debug('check_MAME_DB_status() ERROR: MAME_ASSETS_SCANNED fails.')
            t = 'MAME assets need to be scanned. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_MAME_DB_status() MAME_ASSETS_SCANNED OK')
            check_MAME_DB_status(st_dic, MAME_MACHINES_SCANNED, ctrl_dic)

    else:
        raise ValueError('check_MAME_DB_status() Recursive logic error. condition = {}'.format(condition))

#
# Look at check_MAME_DB_status()
#
def check_SL_DB_status(st_dic, condition, ctrl_dic):
    if not ctrl_dic:
        log_debug('check_SL_DB_status() ERROR: Control dictionary empty.')
        t = ('MAME control file not found. You need to build the MAME main database '
            'using the context menu "Setup addon" in the AML main window.')
        kodi_set_error_status(st_dic, t)
    elif condition == SL_MAIN_DB_BUILT:
        test_MAIN_DB_BUILT = True if ctrl_dic['t_SL_DB_build'] > ctrl_dic['t_MAME_DB_build'] else False
        if not test_MAIN_DB_BUILT:
            log_debug('check_SL_DB_status() SL_MAIN_DB_BUILT fails')
            t = 'Software List databases not built or outdated. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_SL_DB_status() SL_MAIN_DB_BUILT OK')
    elif condition == SL_ITEMS_SCANNED:
        test_ITEMS_SCANNED = True if ctrl_dic['t_SL_ROMs_scan'] > ctrl_dic['t_SL_DB_build'] else False
        if not test_ITEMS_SCANNED:
            log_debug('check_SL_DB_status() SL_ITEMS_SCANNED fails')
            t = 'Software List items not scanned. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_SL_DB_status() SL_ITEMS_SCANNED OK')
            check_SL_DB_status(st_dic, SL_MAIN_DB_BUILT, ctrl_dic)
    elif condition == SL_ASSETS_SCANNED:
        test_ASSETS_SCANNED = True if ctrl_dic['t_SL_assets_scan'] > ctrl_dic['t_SL_ROMs_scan'] else False
        if not test_ASSETS_SCANNED:
            log_debug('check_SL_DB_status() SL_ASSETS_SCANNED fails')
            t = 'Software List assets not scanned. Use the context menu "Setup addon" in the main window.'
            kodi_set_error_status(st_dic, t)
        else:
            log_debug('check_SL_DB_status() SL_ASSETS_SCANNED OK')
            check_SL_DB_status(st_dic, SL_ITEMS_SCANNED, ctrl_dic)
    else:
        raise ValueError('check_SL_DB_status() Recursive logic error. condition = {}'.format(condition))

# This function is called before rendering a Catalog.
def check_MAME_DB_before_rendering_catalog(cfg, st_dic, control_dic):
    # Check if MAME catalogs are built.
    check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, control_dic)
    if kodi_is_error_status(st_dic): return
    log_debug('check_MAME_DB_before_rendering_catalog() All good!')

# This function checks if the database is OK and machines inside a Category can be rendered.
# This function is called before rendering machines.
# This function does not affect MAME Favourites, Recently Played, etc. Those can always be rendered.
# This function relies in the timestamps in control_dic.
#
# Returns True if everything is OK and machines inside a Category can be rendered.
# Returns False and prints warning message if machines inside a category cannot be rendered.
def check_MAME_DB_before_rendering_machines(cfg, st_dic, control_dic):
    # Check if MAME catalogs are built.
    check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, control_dic)
    if kodi_is_error_status(st_dic): return

    # If MAME render cache is enabled then check that it is up-to-date.
    if cfg.settings['debug_enable_MAME_render_cache'] and \
        (control_dic['t_MAME_render_cache_build'] < control_dic['t_MAME_Catalog_build']):
        log_warning('t_MAME_render_cache_build < t_MAME_Catalog_build')
        t = ('MAME render cache needs to be updated. '
            'Open the context menu "Setup addon", then '
            '"Step by Step", and then "Rebuild MAME machine and asset caches."')
        kodi_set_error_status(st_dic, t)
        return

    if cfg.settings['debug_enable_MAME_asset_cache'] and \
        (control_dic['t_MAME_asset_cache_build'] < control_dic['t_MAME_Catalog_build']):
        log_warning('t_MAME_asset_cache_build < t_MAME_Catalog_build')
        t = ('MAME asset cache needs to be updated. '
            'Open the context menu "Setup addon", then '
            '"Step by Step", and then "Rebuild MAME machine and asset caches."')
        kodi_set_error_status(st_dic, t)
        return

    log_debug('check_MAME_DB_before_rendering_machines() All good.')

# Same functions for Software Lists. Called before rendering SL Items inside a Software List.
# WARNING This must be completed!!! Look at the MAME functions.
def check_SL_DB_before_rendering_catalog(cfg, st_dic, control_dic):
    # Check if SL databases are built.
    check_SL_DB_status(st_dic, SL_MAIN_DB_BUILT, control_dic)
    if kodi_is_error_status(st_dic): return
    log_debug('check_SL_DB_before_rendering_catalog() All good.')

def check_SL_DB_before_rendering_machines(cfg, st_dic, control_dic):
    # Check if SL databases are built.
    check_SL_DB_status(st_dic, SL_MAIN_DB_BUILT, control_dic)
    if kodi_is_error_status(st_dic): return
    log_debug('check_SL_DB_before_rendering_machines() All good.')

# -------------------------------------------------------------------------------------------------
# Setup plugin databases
# -------------------------------------------------------------------------------------------------
def command_context_setup_plugin(cfg):
    menu_item = xbmcgui.Dialog().select('Setup AML addon', [
        'All in one (Build DB, Scan, Plots, Filters)',
        'All in one (Build DB, Scan, Plots, Filters, Audit)',
        'Build all databases',
        'Scan everything and build plots',
        'Build missing Fanarts and 3D boxes',
        'Audit MAME machine ROMs/CHDs',
        'Audit SL ROMs/CHDs',
        'Step by step ...',
        'Build Fanarts/3D Boxes ...',
    ])
    if menu_item < 0: return

    # --- All in one (Build, Scan, Plots, Filters) ---
    # --- All in one (Build, Scan, Plots, Filters, Audit) ---
    if menu_item == 0 or menu_item == 1:
        DO_AUDIT = True if menu_item == 1 else False
        log_info('command_context_setup_plugin() All in one step starting ...')
        log_info('Operation mode {}'.format(cfg.settings['op_mode']))
        log_info('DO_AUDIT {}'.format(DO_AUDIT))

        # --- Build main MAME database, PClone list and MAME hashed database (mandatory) ---
        # control_dic is created or reseted in this function.
        # This uses the modern GUI error reporting functions.
        st_dic = kodi_new_status_dic()
        db_dic = mame_build_MAME_main_database(cfg, st_dic)
        if kodi_display_status_message(st_dic): return

        # --- Build ROM audit/scanner databases (mandatory) ---
        mame_check_before_build_ROM_audit_databases(cfg, st_dic, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return

        mame_build_ROM_audit_databases(cfg, st_dic, db_dic)
        if kodi_display_status_message(st_dic): return

        # --- Build MAME catalogs (mandatory) ---
        mame_check_before_build_MAME_catalogs(cfg, st_dic, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return

        mame_build_MAME_catalogs(cfg, st_dic, db_dic)
        if kodi_display_status_message(st_dic): return

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs (optional) ---
        if cfg.settings['global_enable_SL']:
            mame_check_before_build_SL_databases(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return
            mame_build_SoftwareLists_databases(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return
        else:
            log_info('SL disabled. Skipping mame_build_SoftwareLists_databases()')

        # --- Scan ROMs/CHDs/Samples and updates ROM status (optional) ---
        # Abort if ROM path not found. CHD and Samples paths are optional.
        options_dic = {}
        mame_check_before_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return

        mame_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic)
        if kodi_display_status_message(st_dic): return

        # --- Scans MAME assets/artwork (optional) ---
        mame_check_before_scan_MAME_assets(cfg, st_dic, db_dic['control_dic'])
        if not kodi_display_status_message(st_dic):
            # Scanning of assets is optional.
            mame_scan_MAME_assets(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return

        # --- Scan SL ROMs/CHDs (optional) ---
        if cfg.settings['global_enable_SL']:
            options_dic = {}
            mame_check_before_scan_SL_ROMs(cfg, st_dic, options_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return
            mame_scan_SL_ROMs(cfg, st_dic, options_dic, db_dic)
            if kodi_display_status_message(st_dic): return
        else:
            log_info('SL disabled. Skipping mame_scan_SL_ROMs()')

        # --- Scan SL assets/artwork (optional) ---
        if cfg.settings['global_enable_SL']:
            mame_check_before_scan_SL_assets(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return
            mame_scan_SL_assets(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return
        else:
            log_info('SL disabled. Skipping mame_scan_SL_assets()')

        # --- Build MAME machine plots ---
        mame_build_MAME_plots(cfg, db_dic)

        # --- Build Software List items plot ---
        if cfg.settings['global_enable_SL']:
            mame_build_SL_plots(cfg, db_dic)
        else:
            log_info('SL disabled. Skipping mame_build_SL_plots()')

        # --- Regenerate the custom filters ---
        (main_filter_dic, sets_dic) = filter_get_filter_DB(cfg, db_dic)
        (filter_list, f_st_dic) = filter_custom_filters_load_XML(cfg, db_dic, main_filter_dic, sets_dic)
        if len(filter_list) >= 1 and not f_st_dic['XML_errors']:
            filter_build_custom_filters(cfg, db_dic, filter_list, main_filter_dic)
        else:
            log_info('Custom XML filters not built.')

        # --- Regenerate MAME asset hashed database ---
        db_build_asset_hashed_db(cfg, db_dic['control_dic'], db_dic['assetdb'])

        # --- Regenerate MAME machine render and assets cache ---
        db_build_render_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['renderdb'])
        db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])

        if DO_AUDIT:
            mame_audit_MAME_all(cfg, db_dic)
            if cfg.settings['global_enable_SL']:
                mame_audit_SL_all(cfg, db_dic)
            else:
                log_info('SL disabled. Skipping mame_audit_SL_all()')

        # --- So long and thanks for all the fish ---
        if DO_AUDIT:
            kodi_notify('Finished extracting, DB build, scanning, filters and audit')
        else:
            kodi_notify('Finished extracting, DB build, scanning and filters')

    # --- Build all databases ---
    elif menu_item == 2:
        log_info('command_context_setup_plugin() Build everything starting...')

        # --- Build main MAME database, PClone list and hashed database (mandatory) ---
        # Extract/process MAME.xml, creates XML control file, resets control_dic and creates
        # main MAME databases.
        st_dic = kodi_new_status_dic()
        db_dic = mame_build_MAME_main_database(cfg, st_dic)
        if kodi_display_status_message(st_dic): return

        # --- Build ROM audit/scanner databases (mandatory) ---
        mame_check_before_build_ROM_audit_databases(cfg, st_dic, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return

        mame_build_ROM_audit_databases(cfg, st_dic, db_dic)
        if kodi_display_status_message(st_dic): return

        # --- Release some memory before building the catalogs ---
        del db_dic['devices']
        del db_dic['history_idx_dic']
        del db_dic['mameinfo_idx_dic']
        del db_dic['gameinit_idx_list']
        del db_dic['command_idx_list']
        del db_dic['audit_roms']
        del db_dic['machine_archives']
        # Force garbage collection here to free memory?

        # --- Build MAME catalogs (mandatory) ---
        mame_check_before_build_MAME_catalogs(cfg, st_dic, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return

        mame_build_MAME_catalogs(cfg, st_dic, db_dic)
        if kodi_display_status_message(st_dic): return

        # --- Regenerate the render and assets cache ---
        # Check whether cache must be rebuilt is done internally.
        db_build_render_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['renderdb'])
        db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])

        # --- Release some memory before building the SL databases ---
        del db_dic['assetdb']
        del db_dic['roms']
        del db_dic['main_pclone_dic']
        del db_dic['cache_index']

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs (optional) ---
        if cfg.settings['global_enable_SL']:
            mame_check_before_build_SL_databases(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return
            mame_build_SoftwareLists_databases(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return
        else:
            log_info('SL globally disabled. Skipping mame_build_SoftwareLists_databases()')

        # So long and thanks for all the fish.
        kodi_notify('All databases built')

    # --- Scan everything ---
    elif menu_item == 3:
        log_info('command_setup_plugin() Scanning everything starting...')

        # --- MAME -------------------------------------------------------------------------------
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
            ['main_pclone_dic', 'MAME PClone dictionary', cfg.MAIN_PCLONE_DB_PATH.getPath()],
            ['machine_archives', 'Machine file list', cfg.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
            ['cache_index', 'MAME cache index', cfg.CACHE_INDEX_PATH.getPath()],
            ['history_idx_dic', 'History DAT index', cfg.HISTORY_IDX_PATH.getPath()],
            ['mameinfo_idx_dic', 'Mameinfo DAT index', cfg.MAMEINFO_IDX_PATH.getPath()],
            ['gameinit_idx_list', 'Gameinit DAT index', cfg.GAMEINIT_IDX_PATH.getPath()],
            ['command_idx_list', 'Command DAT index', cfg.COMMAND_IDX_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Scan MAME ROMs/CHDs/Samples and updates ROM status (optional) ---
        st_dic = kodi_new_status_dic()
        options_dic = {}
        mame_check_before_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return

        mame_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic)
        if kodi_display_status_message(st_dic): return

        # --- Scans MAME assets/artwork (optional) ---
        mame_check_before_scan_MAME_assets(cfg, st_dic, db_dic['control_dic'])
        if not kodi_display_status_message(st_dic):
            # Scanning of assets is optional.
            mame_scan_MAME_assets(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return

        # --- Build MAME machines plot (mandatory) ---
        mame_build_MAME_plots(cfg, db_dic)

        # --- Regenerate asset hashed database ---
        db_build_asset_hashed_db(cfg, db_dic['control_dic'], db_dic['assetdb'])

        # --- Regenerate MAME asset cache ---
        # Note that scanning only changes the assets, never the machines or render DBs.
        db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])

        # --- Software Lists ---------------------------------------------------------------------
        if cfg.settings['global_enable_SL']:
            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['SL_index', 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
                ['SL_PClone_dic', 'Software Lists Parent/Clone database', cfg.SL_PCLONE_DIC_PATH.getPath()],
                ['SL_machines', 'Software Lists machines', cfg.SL_MACHINES_PATH.getPath()],
                ['history_idx_dic', 'History DAT index', cfg.HISTORY_IDX_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Scan SL ROMs/CHDs (optional) ---
            mame_check_before_scan_SL_ROMs(cfg, st_dic, db_dic['control_dic'], db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return
            mame_scan_SL_ROMs(cfg, st_dic, db_dic['control_dic'], db_dic)
            if kodi_display_status_message(st_dic): return

            # --- Scan SL assets/artwork (optional) ---
            mame_check_before_scan_SL_assets(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return
            mame_scan_SL_assets(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return

            # --- Build Software List items plot (mandatory) ---
            mame_build_SL_plots(cfg, db_dic)
        else:
            log_info('SL globally disabled. Skipping SL scanning and plot building.')

        # --- So long and thanks for all the fish ---
        kodi_notify('All ROM/asset scanning finished')

    # --- Build missing Fanarts and 3D boxes ---
    elif menu_item == 4:
        BUILD_MISSING = True
        log_info('command_context_setup_plugin() Building missing Fanarts and 3D boxes...')
        st_dic = kodi_new_status_dic()

        # Check if Pillow library is available. Abort if not.
        if not PILLOW_AVAILABLE:
            kodi_dialog_OK('Pillow Python library is not available. Aborting image generation.')
            return

        # Build mussing Fanarts and 3DBoxes.
        data_dic = graphs_load_MAME_Fanart_stuff(cfg, st_dic, BUILD_MISSING)
        if kodi_display_status_message(st_dic): return
        graphs_build_MAME_Fanart_all(cfg, st_dic, data_dic)
        if kodi_display_status_message(st_dic): return

        data_dic = graphs_load_MAME_3DBox_stuff(cfg, st_dic, BUILD_MISSING)
        if kodi_display_status_message(st_dic): return
        graphs_build_MAME_3DBox_all(cfg, st_dic, data_dic)
        if kodi_display_status_message(st_dic): return

        # MAME asset DB has changed so rebuild MAME asset hashed database and MAME asset cache.
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        db_build_asset_hashed_db(cfg, control_dic, data_dic['assetdb'])
        cache_index = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
        db_build_asset_cache(cfg, control_dic, cache_index, data_dic['assetdb'])

        if cfg.settings['global_enable_SL']:
            data_dic_SL = graphs_load_SL_Fanart_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_SL_Fanart_all(cfg, st_dic, data_dic_SL)
            if kodi_display_status_message(st_dic): return

            data_dic_SL = graphs_load_SL_3DBox_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_SL_3DBox_all(cfg, st_dic, data_dic_SL)
            if kodi_display_status_message(st_dic): return
        else:
            log_info('SL globally disabled. Skipping SL Fanart and 3DBox generation.')

    # --- Audit MAME machine ROMs/CHDs ---
    # It is likely that this function will take a looong time. It is important that the
    # audit process can be canceled and a partial report is written.
    elif menu_item == 5:
        log_info('command_context_setup_plugin() Audit MAME machines ROMs/CHDs ...')

        # --- Load machines, ROMs and CHDs databases ---
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ['audit_roms', 'MAME ROM Audit', cfg.ROM_AUDIT_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Check for requirements/errors ---

        # --- Audit all MAME machines ---
        # 1) Updates control_dic statistics and timestamp.
        mame_audit_MAME_all(cfg, db_dic)
        kodi_notify('MAME audit finished')

    # --- Audit SL ROMs/CHDs ---
    elif menu_item == 6:
        log_info('command_context_setup_plugin() Audit SL ROMs/CHDs ...')

        # Load databases.
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['SL_index', 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Check for requirements/errors ---

        # --- Audit all Software List items ---
        # 1) Updates control_dic statistics and timestamps and saves it.
        mame_audit_SL_all(cfg, db_dic)
        kodi_notify('Software Lists audit finished')

    # --- Build Step by Step (database and scanner) ---
    elif menu_item == 7:
        submenu = xbmcgui.Dialog().select('Setup AML addon (step by step)', [
            'Extract/Process MAME.xml',
            'Build MAME main database',
            'Build MAME audit/scanner databases',
            'Build MAME catalogs',
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

        # --- Extract/Process MAME.xml ---
        if submenu == 0:
            st_dic = kodi_new_status_dic()
            MAME_XML_path, XML_control_FN = mame_init_MAME_XML(cfg, st_dic)
            if kodi_display_status_message(st_dic): return
            XML_control_dic = utils_load_JSON_file_dic(XML_control_FN.getPath())
            # Give user some data.
            mame_v_str = XML_control_dic['ver_mame_str']
            size_MB = int(XML_control_dic['st_size'] / 1000000)
            num_m = XML_control_dic['total_machines']
            t = ('MAME XML version [COLOR orange]{}[/COLOR], size is [COLOR orange]{}[/COLOR] MB '
                'and there are [COLOR orange]{:,}[/COLOR] machines.')
            kodi_dialog_OK(t.format(mame_v_str, size_MB, num_m))

        # --- Build main MAME database, PClone list and hashed database ---
        elif submenu == 1:
            log_info('command_context_setup_plugin() Generating MAME main database and PClone list...')
            # Extract/process MAME.xml, creates XML control file, resets control_dic and creates
            # main MAME databases.
            # 1) Creates control_dic.
            st_dic = kodi_new_status_dic()
            db_dic = mame_build_MAME_main_database(cfg, st_dic)
            if kodi_display_status_message(st_dic): return
            kodi_notify('Main MAME databases built')

        # --- Build ROM audit/scanner databases ---
        elif submenu == 2:
            log_info('command_context_setup_plugin() Generating ROM audit/scanner databases...')

            # Load databases.
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
                ['devices', 'MAME machine devices', cfg.DEVICES_DB_PATH.getPath()],
                ['roms', 'MAME machine ROMs', cfg.ROMS_DB_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # Check for requirements/errors.
            st_dic = kodi_new_status_dic()
            mame_check_before_build_ROM_audit_databases(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # Generate ROM audit databases.
            # 1) Updates db_dic and saves databases on disk.
            # 2) Updates t_MAME_Audit_DB_build and control_dic and saves it.
            mame_build_ROM_audit_databases(cfg, st_dic, db_dic)
            kodi_notify('ROM audit/scanner databases built')

        # --- Build MAME catalogs ---
        elif submenu == 3:
            log_info('command_context_setup_plugin() Building MAME catalogs...')

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
                ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
                ['roms', 'MAME machine ROMs', cfg.ROMS_DB_PATH.getPath()],
                ['main_pclone_dic', 'MAME PClone dictionary', cfg.MAIN_PCLONE_DB_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Check for requirements/errors ---
            st_dic = kodi_new_status_dic()
            mame_check_before_build_MAME_catalogs(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # --- Build MAME catalog ---
            # At this time the asset database will be empty (scanner has not been run). However,
            # the asset cache with an empty database is required to render the machines in the catalogs.
            # 1) Updates db_dic (adds cache_index field).
            # 2) Creates cache_index_dic and saves it.
            # 3) Updates control_dic and saves it.
            # 4) Does not require to rebuild the render hashed database.
            # 5) Requires rebuilding of the render cache.
            # 6) Requires rebuilding of the asset cache.
            mame_build_MAME_catalogs(cfg, st_dic, db_dic)
            if kodi_display_status_message(st_dic): return
            # Check whether cache must be rebuilt is done internally.
            db_build_render_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['renderdb'])
            db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])
            kodi_notify('MAME Catalogs built')

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs ---
        elif submenu == 4:
            log_info('command_context_setup_plugin() Building Software Lists ROM/CHD databases, SL indices and SL catalogs...')
            if not cfg.settings['global_enable_SL']:
                kodi_dialog_OK('Software Lists globally disabled.')
                return

            # Read main database and control dic.
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # Check for requirements/errors.
            st_dic = kodi_new_status_dic()
            mame_check_before_build_SL_databases(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # Build SL databases.
            # 1) Updates db_dic (adds cache_index field).
            # 2) Modifies and saves control_dic
            mame_build_SoftwareLists_databases(cfg, st_dic, db_dic)
            kodi_notify('Software Lists database built')

        # --- Scan ROMs/CHDs/Samples and updates ROM status ---
        elif submenu == 5:
            log_info('command_context_setup_plugin() Scanning MAME ROMs/CHDs/Samples...')

            # Load machine database and control_dic and scan
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['cache_index', 'MAME cache index', cfg.CACHE_INDEX_PATH.getPath()],
                ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
                ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
                ['machine_archives', 'Machine archive list', cfg.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # Check for requirements/errors.
            st_dic = kodi_new_status_dic()
            options_dic = {}
            mame_check_before_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # --- Scan MAME ROMs/CHDs/Samples ---
            # 1) Updates 'flags' field in assets_dic
            # 2) Updates timestamp t_MAME_ROM_scan and statistics in control_dic.
            # 3) Saves control_dic and assets_dic.
            # 4) Requires rebuilding the asset hashed DB.
            # 5) Requires rebuilding the asset cache.
            mame_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic)
            db_build_asset_hashed_db(cfg, db_dic['control_dic'], db_dic['assetdb'])
            db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])
            kodi_notify('Scanning of MAME ROMs, CHDs and Samples finished')

        # --- Scans MAME assets/artwork ---
        elif submenu == 6:
            log_info('command_context_setup_plugin() Scanning MAME assets/artwork ...')

            # Load machine database and scan.
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
                ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
                ['main_pclone_dic', 'MAME PClone dictionary', cfg.MAIN_PCLONE_DB_PATH.getPath()],
                ['cache_index', 'MAME cache index', cfg.CACHE_INDEX_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Check for requirements/errors ---
            st_dic = kodi_new_status_dic()
            mame_check_before_scan_MAME_assets(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # --- Scan MAME assets ---
            # 1) Mutates assets_dic and control_dic (timestamp and stats)
            # 2) Saves assets_dic and control_dic.
            # 2) Requires rebuilding of the asset hashed DB.
            # 3) Requires rebuilding of the asset cache.
            mame_scan_MAME_assets(cfg, st_dic, db_dic)
            db_build_asset_hashed_db(cfg, db_dic['control_dic'], db_dic['assetdb'])
            db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])
            kodi_notify('Scanning of assets/artwork finished')

        # --- Scan SL ROMs/CHDs ---
        elif submenu == 7:
            log_info('command_context_setup_plugin() Scanning SL ROMs/CHDs...')
            if not cfg.settings['global_enable_SL']:
                kodi_dialog_OK('Software Lists globally disabled.')
                return

            # --- Load SL and scan ROMs/CHDs ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['SL_index', 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Check for requirements/errors ---
            st_dic = kodi_new_status_dic()
            options_dic = {}
            mame_check_before_scan_SL_ROMs(cfg, st_dic, options_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # 1) Mutates control_dic (timestamp and statistics)
            # 2) Saves control_dic
            mame_scan_SL_ROMs(cfg, st_dic, options_dic, db_dic)
            kodi_notify('Scanning of SL ROMs finished')

        # --- Scan SL assets/artwork ---
        # Database format: ADDON_DATA_DIR/db_SoftwareLists/32x_assets.json
        # { 'ROM_name' : {'asset1' : 'path', 'asset2' : 'path', ... }, ... }
        elif submenu == 8:
            log_info('command_context_setup_plugin() Scanning SL assets/artwork...')
            if not cfg.settings['global_enable_SL']:
                kodi_dialog_OK('Software Lists globally disabled.')
                return

            # --- Load SL databases ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['SL_index', 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
                ['SL_PClone_dic', 'Software Lists Parent/Clone database', cfg.SL_PCLONE_DIC_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Check for requirements/errors ---
            st_dic = kodi_new_status_dic()
            mame_check_before_scan_SL_assets(cfg, st_dic, db_dic['control_dic'])
            if kodi_display_status_message(st_dic): return

            # --- Scan SL ---
            # 1) Mutates control_dic (timestamp and statistics) and saves it.
            mame_scan_SL_assets(cfg, st_dic, db_dic)
            kodi_notify('Scanning of SL assets finished')

        # --- Build MAME machines plot ---
        elif submenu == 9:
            log_debug('Rebuilding MAME machine plots...')

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
                ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
                ['cache_index', 'MAME cache index', cfg.CACHE_INDEX_PATH.getPath()],
                ['history_idx_dic', 'History DAT index', cfg.HISTORY_IDX_PATH.getPath()],
                ['mameinfo_idx_dic', 'Mameinfo DAT index', cfg.MAMEINFO_IDX_PATH.getPath()],
                ['gameinit_idx_list', 'Gameinit DAT index', cfg.GAMEINIT_IDX_PATH.getPath()],
                ['command_idx_list', 'Command DAT index', cfg.COMMAND_IDX_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Check for requirements/errors ---

            # --- Traverse MAME machines and build plot ---
            # 1) Mutates and saves the assets database
            # 2) Requires rebuilding of the MAME asset hashed DB.
            # 3) Requires rebuilding if the MAME asset cache.
            mame_build_MAME_plots(cfg, db_dic)
            db_build_asset_hashed_db(cfg, db_dic['control_dic'], db_dic['assetdb'])
            db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'])
            kodi_notify('MAME machines plot generation finished')

        # --- Buils Software List items plot ---
        elif submenu == 10:
            log_debug('Rebuilding Software List items plots...')

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['SL_index', 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
                ['SL_machines', 'Software Lists machines', cfg.SL_MACHINES_PATH.getPath()],
                ['history_idx_dic', 'History DAT index', cfg.HISTORY_IDX_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Check for requirements/errors ---

            # --- Build SL plots ---
            mame_build_SL_plots(cfg, db_dic)
            kodi_notify('SL item plot generation finished')

        # --- Regenerate MAME machine render and assets cache ---
        elif submenu == 11:
            log_debug('Rebuilding MAME machine and assets cache ...')

            # --- Load databases ---
            db_files = [
                ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
                ['cache_index', 'Cache index', cfg.CACHE_INDEX_PATH.getPath()],
                ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
                ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
            ]
            db_dic = db_load_files(db_files)

            # --- Regenerate ROM and asset caches ---
            db_build_render_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['renderdb'], force_build = True)
            db_build_asset_cache(cfg, db_dic['control_dic'], db_dic['cache_index'], db_dic['assetdb'], force_build = True)
            kodi_notify('MAME machine and asset caches rebuilt')

        else:
            kodi_dialog_OK('In command_context_setup_plugin() wrong submenu = {}'.format(submenu))

    # --- Build Fanarts/3D boxes ---
    elif menu_item == 8:
        submenu = xbmcgui.Dialog().select('Build Fanarts', [
            'Test MAME Fanart',
            'Test Software List item Fanart',
            'Test MAME 3D Box',
            'Test Software List item 3D Box',
            'Build all missing Fanarts',
            'Build all missing 3D boxes',
            'Build missing MAME Fanarts',
            'Build missing Software Lists Fanarts',
            'Build missing MAME 3D Boxes',
            'Build missing Software Lists 3D Boxes',
            'Rebuild all MAME Fanarts',
            'Rebuild all Software Lists Fanarts',
            'Rebuild all MAME 3D Boxes',
            'Rebuild all Software Lists 3D Boxes',
        ])
        if submenu < 0: return

        # Check if Pillow library is available. Abort if not.
        if not PILLOW_AVAILABLE:
            kodi_dialog_OK('Pillow Python library is not available. Aborting Fanart generation.')
            return

        # --- Test MAME Fanart ---
        if submenu == 0:
            log_info('command_context_setup_plugin() Testing MAME Fanart generation...')
            Template_FN = cfg.ADDON_CODE_DIR.pjoin('templates/AML-MAME-Fanart-template.xml')
            Asset_path_FN = cfg.ADDON_CODE_DIR.pjoin('media/MAME_assets')
            Fanart_FN = cfg.ADDON_DATA_DIR.pjoin('MAME_Fanart.png')
            log_debug('Testing MAME Fanart generation ...')
            log_debug('Template_FN   "{}"'.format(Template_FN.getPath()))
            log_debug('Fanart_FN     "{}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN "{}"'.format(Asset_path_FN.getPath()))

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
            graphs_build_MAME_Fanart(cfg, layout, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (25, 25, 50), test_flag = True)

            # Display Fanart
            log_debug('Rendering fanart "{}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{}")'.format(Fanart_FN.getPath()))

        # --- Test SL Fanart ---
        elif submenu == 1:
            log_info('command_context_setup_plugin() Testing SL Fanart generation...')
            Template_FN = cfg.ADDON_CODE_DIR.pjoin('templates/AML-SL-Fanart-template.xml')
            Asset_path_FN = cfg.ADDON_CODE_DIR.pjoin('media/SL_assets')
            Fanart_FN = cfg.ADDON_DATA_DIR.pjoin('SL_Fanart.png')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('Template_FN   "{}"'.format(Template_FN.getPath()))
            log_debug('Fanart_FN     "{}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN "{}"'.format(Asset_path_FN.getPath()))

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
            graphs_build_SL_Fanart(cfg, layout, SL_name, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (50, 50, 75), test_flag = True)

            # --- Display Fanart ---
            log_debug('Displaying image "{}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{}")'.format(Fanart_FN.getPath()))

        # --- Test MAME 3D Box ---
        elif submenu == 2:
            log_info('command_context_setup_plugin() Testing MAME 3D Box generation ...')
            Fanart_FN = cfg.ADDON_DATA_DIR.pjoin('MAME_3dbox.png')
            Asset_path_FN = cfg.ADDON_CODE_DIR.pjoin('media/MAME_assets')
            # TProjection_FN = cfg.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_56.json')
            TProjection_FN = cfg.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_60.json')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('Fanart_FN      "{}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN  "{}"'.format(Asset_path_FN.getPath()))
            log_debug('TProjection_FN "{}"'.format(TProjection_FN.getPath()))

            # Load 3D texture projection matrix
            t_projection = utils_load_JSON_file_dic(TProjection_FN.getPath())

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

            pDialog = KodiProgressDialog()
            pDialog.startProgress('Generating test MAME 3D Box...')
            graphs_build_MAME_3DBox(cfg, t_projection, SL_name, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (50, 50, 75), test_flag = True)
            pDialog.endProgress()

            # --- Display Fanart ---
            log_debug('Displaying image "{}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{}")'.format(Fanart_FN.getPath()))

        # --- Test SL 3D Box ---
        elif submenu == 3:
            log_info('command_context_setup_plugin() Testing SL 3D Box generation ...')
            # TProjection_FN = cfg.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_56.json')
            TProjection_FN = cfg.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_60.json')
            Fanart_FN = cfg.ADDON_DATA_DIR.pjoin('SL_3dbox.png')
            Asset_path_FN = cfg.ADDON_CODE_DIR.pjoin('media/SL_assets')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('TProjection_FN "{}"'.format(TProjection_FN.getPath()))
            log_debug('Fanart_FN      "{}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN  "{}"'.format(Asset_path_FN.getPath()))

            # Load 3D texture projection matrix
            t_projection = utils_load_JSON_file_dic(TProjection_FN.getPath())

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

            pDialog = KodiProgressDialog()
            pDialog.startProgress('Generating test SL 3D Box...')
            graphs_build_MAME_3DBox(cfg, t_projection, SL_name, m_name, assets_dic, Fanart_FN,
                CANVAS_COLOR = (50, 50, 75), test_flag = True)
            pDialog.endProgress()

            # --- Display Fanart ---
            log_debug('Displaying image "{}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{}")'.format(Fanart_FN.getPath()))

        # --- Build all missing Fanarts ---
        elif submenu == 4:
            BUILD_MISSING = True
            log_info('command_context_setup_plugin() Building all missing Fanarts...')
            st_dic = kodi_new_status_dic()
            if not PILLOW_AVAILABLE:
                kodi_dialog_OK('Pillow Python library is not available. Aborting image generation.')
                return

            # Kodi notifications inside graphs_build_*() functions.
            data_dic = graphs_load_MAME_Fanart_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_MAME_Fanart_all(cfg, st_dic, data_dic)
            if kodi_display_status_message(st_dic): return

            # MAME asset DB has changed so rebuild MAME asset hashed database and MAME asset cache.
            control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
            db_build_asset_hashed_db(cfg, control_dic, data_dic['assetdb'])
            cache_index = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
            db_build_asset_cache(cfg, control_dic, cache_index, data_dic['assetdb'])

            if cfg.settings['global_enable_SL']:
                data_dic_SL = graphs_load_SL_Fanart_stuff(cfg, st_dic, BUILD_MISSING)
                if kodi_display_status_message(st_dic): return
                graphs_build_SL_Fanart_all(cfg, st_dic, data_dic_SL)
                if kodi_display_status_message(st_dic): return
            else:
                log_info('SL globally disabled. Skipping SL Fanart generation.')

        # --- Build all missing 3D boxes ---
        elif submenu == 5:
            BUILD_MISSING = True
            log_info('command_context_setup_plugin() Building all missing 3D boxes...')
            st_dic = kodi_new_status_dic()
            if not PILLOW_AVAILABLE:
                kodi_dialog_OK('Pillow Python library is not available. Aborting image generation.')
                return

            # Kodi notifications inside graphs_build_*() functions.
            data_dic = graphs_load_MAME_3DBox_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_MAME_3DBox_all(cfg, st_dic, data_dic)
            if kodi_display_status_message(st_dic): return

            # MAME asset DB has changed so rebuild MAME asset hashed database and MAME asset cache.
            control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
            db_build_asset_hashed_db(cfg, control_dic, data_dic['assetdb'])
            cache_index = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
            db_build_asset_cache(cfg, control_dic, cache_index, data_dic['assetdb'])

            if cfg.settings['global_enable_SL']:
                data_dic_SL = graphs_load_SL_3DBox_stuff(cfg, st_dic, BUILD_MISSING)
                if kodi_display_status_message(st_dic): return
                graphs_build_SL_3DBox_all(cfg, st_dic, data_dic_SL)
                if kodi_display_status_message(st_dic): return
            else:
                log_info('SL globally disabled. Skipping SL Fanart generation.')

        # --- Build missing/Rebuild all MAME Fanarts ---
        # For a complete MAME artwork collection, rebuilding all Fanarts will take hours!
        elif submenu == 6 or submenu == 10:
            BUILD_MISSING = True if submenu == 6 else False
            log_info('command_context_setup_plugin() Build missing/Rebuild all MAME Fanarts...')
            log_info('BUILD_MISSING is {}'.format(BUILD_MISSING))
            st_dic = kodi_new_status_dic()
            data_dic = graphs_load_MAME_Fanart_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_MAME_Fanart_all(cfg, st_dic, data_dic)
            if kodi_display_status_message(st_dic): return
            # MAME asset DB has changed so rebuild MAME asset hashed database and MAME asset cache.
            control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
            db_build_asset_hashed_db(cfg, control_dic, data_dic['assetdb'])
            cache_index = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
            db_build_asset_cache(cfg, control_dic, cache_index, data_dic['assetdb'])

        # --- Build missing/Rebuild all SL Fanarts ---
        elif submenu == 7 or submenu == 11:
            BUILD_MISSING = True if submenu == 7 else False
            log_info('command_context_setup_plugin() Build missing/Rebuild all Software Lists Fanarts...')
            log_info('BUILD_MISSING is {}'.format(BUILD_MISSING))
            st_dic = kodi_new_status_dic()
            if not cfg.settings['global_enable_SL']:
                kodi_dialog_OK('SL globally disabled. Skipping image generation.')
                return
            data_dic_SL = graphs_load_SL_Fanart_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_SL_Fanart_all(cfg, st_dic, data_dic_SL)
            if kodi_display_status_message(st_dic): return

        # --- Build missing/Rebuild all MAME 3D Boxes ---
        elif submenu == 8 or submenu == 12:
            BUILD_MISSING = True if submenu == 8 else False
            log_info('command_context_setup_plugin() Rebuilding all MAME 3D Boxes...')
            log_info('BUILD_MISSING is {}'.format(BUILD_MISSING))
            st_dic = kodi_new_status_dic()
            data_dic = graphs_load_MAME_3DBox_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_MAME_3DBox_all(cfg, st_dic, data_dic)
            if kodi_display_status_message(st_dic): return
            # MAME asset DB has changed so rebuild MAME asset hashed database and MAME asset cache.
            control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
            db_build_asset_hashed_db(cfg, control_dic, data_dic['assetdb'])
            cache_index = utils_load_JSON_file_dic(cfg.CACHE_INDEX_PATH.getPath())
            db_build_asset_cache(cfg, control_dic, cache_index, data_dic['assetdb'])

        # --- Build missing/Rebuild all SL 3D Boxes ---
        elif submenu == 9 or submenu == 13:
            BUILD_MISSING = True if submenu == 9 else False
            log_info('command_context_setup_plugin() Rebuilding all Software Lists 3D Boxes...')
            log_info('BUILD_MISSING is {}'.format(BUILD_MISSING))
            st_dic = kodi_new_status_dic()
            if not cfg.settings['global_enable_SL']:
                kodi_dialog_OK('SL globally disabled. Skipping image generation.')
                return
            data_dic_SL = graphs_load_SL_3DBox_stuff(cfg, st_dic, BUILD_MISSING)
            if kodi_display_status_message(st_dic): return
            graphs_build_SL_3DBox_all(cfg, st_dic, data_dic_SL)
            if kodi_display_status_message(st_dic): return

        else:
            kodi_dialog_OK('In command_context_setup_plugin() wrong submenu = {}'.format(submenu))

    else:
        kodi_dialog_OK('In command_context_setup_plugin() wrong menu_item = {}'.format(menu_item))

#
# Execute utilities.
#
def command_exec_utility(cfg, which_utility):
    log_debug('command_exec_utility() which_utility = "{}" starting ...'.format(which_utility))

    # Check MAME version
    # Run 'mame -version' and extract version from stdout
    if which_utility == 'CHECK_MAME_VERSION':
        # --- Check for errors ---
        if not cfg.settings['mame_prog']:
            kodi_dialog_OK('MAME executable is not set.')
            return

        # Check MAME version.
        mame_prog_FN = FileName(cfg.settings['mame_prog'])
        if not mame_prog_FN.exists():
            kodi_dialog_OK('Vanilla MAME executable not found.')
            return
        mame_version_str = mame_get_MAME_exe_version(cfg, mame_prog_FN)
        kodi_dialog_OK('MAME version is {}'.format(mame_version_str))

    # Check AML configuration
    elif which_utility == 'CHECK_CONFIG':
        # Functions defined here can see local variables defined in this code block.
        def aux_check_dir_ERR(slist, dir_str, msg):
            if dir_str:
                if FileName(dir_str).exists():
                    slist.append('{} {} "{}"'.format(OK, msg, dir_str))
                else:
                    slist.append('{} {} not found'.format(ERR, msg))
            else:
                slist.append('{} {} not set'.format(ERR, msg))

        def aux_check_dir_WARN(slist, dir_str, msg):
            if dir_str:
                if FileName(dir_str).exists():
                    slist.append('{} {} "{}"'.format(OK, msg, dir_str))
                else:
                    slist.append('{} {} not found'.format(WARN, msg))
            else:
                slist.append('{} {} not set'.format(WARN, msg))

        def aux_check_file_WARN(slist, file_str, msg):
            if file_str:
                if FileName(file_str).exists():
                    slist.append('{} {} "{}"'.format(OK, msg, file_str))
                else:
                    slist.append('{} {} not found'.format(WARN, msg))
            else:
                slist.append('{} {} not set'.format(WARN, msg))

        def aux_check_asset_dir(slist, dir_FN, msg):
            if dir_FN.exists():
                slist.append('{} Found {} path "{}"'.format(OK, msg, dir_FN.getPath()))
            else:
                slist.append('{} {} path does not exist'.format(WARN, msg))
                slist.append('     Tried "{}"'.format(dir_FN.getPath()))

        # Checks AML configuration and informs users of potential problems.
        log_info('command_exec_utility() Checking AML configuration ...')
        OK   = '[COLOR green]OK  [/COLOR]'
        WARN = '[COLOR yellow]WARN[/COLOR]'
        ERR  = '[COLOR red]ERR [/COLOR]'
        slist = []

        # --- Check main stuff ---
        slist.append('Operation mode [COLOR orange]{}[/COLOR]'.format(cfg.settings['op_mode']))
        if cfg.settings['global_enable_SL']:
            slist.append('Software Lists [COLOR orange]enabled[/COLOR]')
        else:
            slist.append('Software Lists [COLOR orange]disabled[/COLOR]')
        slist.append('')

        # --- Mandatory stuff ---
        slist.append('[COLOR orange]MAME executable[/COLOR]')
        if cfg.settings['op_mode'] == OP_MODE_VANILLA:
            # ROM path is mandatory.
            aux_check_dir_ERR(slist, cfg.settings['rom_path_vanilla'], 'MAME ROM path')
            # Vanilla MAME checks.
            if cfg.settings['mame_prog']:
                if FileName(cfg.settings['mame_prog']).exists():
                    slist.append('{} MAME executable "{}"'.format(OK, cfg.settings['mame_prog']))
                else:
                    slist.append('{} MAME executable not found'.format(ERR))
            else:
                slist.append('{} MAME executable not set'.format(ERR))
        elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
            # MAME 2003 Plus checks.
            # ROM path is mandatory.
            aux_check_dir_ERR(slist, cfg.settings['rom_path_2003_plus'], 'MAME ROM path')
            # Retroarch executable.
            if cfg.settings['retroarch_prog']:
                if FileName(cfg.settings['retroarch_prog']).exists():
                    slist.append('{} Retroarch executable "{}"'.format(OK, cfg.settings['retroarch_prog']))
                else:
                    slist.append('{} Retroarch executable not found'.format(ERR))
            else:
                slist.append('{} Retroarch executable not set'.format(ERR))
            # Libretro directory.
            if cfg.settings['libretro_dir']:
                if FileName(cfg.settings['libretro_dir']).exists():
                    slist.append('{} Libretro directory "{}"'.format(OK, cfg.settings['libretro_dir']))
                else:
                    slist.append('{} Libretro directory not found'.format(ERR))
            else:
                slist.append('{} Libretro directory not set'.format(ERR))
            # MAME XML path.
            if cfg.settings['xml_2003_path']:
                if FileName(cfg.settings['xml_2003_path']).exists():
                    slist.append('{} MAME 2003 Plus XML "{}"'.format(OK, cfg.settings['xml_2003_path']))
                else:
                    slist.append('{} MAME 2003 Plus XML not found'.format(ERR))
            else:
                slist.append('{} MAME 2003 Plus XML not set'.format(ERR))
        else:
            slist.append('{} Unknown op_mode {}'.format(ERR, cfg.settings['op_mode']))
        slist.append('')

        slist.append('[COLOR orange]MAME optional paths[/COLOR]')
        aux_check_dir_WARN(slist, cfg.settings['chd_path'], 'MAME CHD path')
        aux_check_dir_WARN(slist, cfg.settings['samples_path'], 'MAME Samples path')
        slist.append('')

        # --- MAME assets ---
        slist.append('[COLOR orange]MAME assets[/COLOR]')
        if cfg.settings['assets_path']:
            if FileName(cfg.settings['assets_path']).exists():
                slist.append('{} MAME Asset path "{}"'.format(OK, cfg.settings['assets_path']))

                # Check that artwork subdirectories exist
                Asset_path_FN = FileName(cfg.settings['assets_path'])

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
                slist.append('{} MAME Asset path not found'.format(ERR))
        else:
            slist.append('{} MAME Asset path not set'.format(WARN))
        slist.append('')

        # --- Software Lists paths ---
        if cfg.settings['global_enable_SL']:
            slist.append('[COLOR orange]Software List paths[/COLOR]')
            aux_check_dir_WARN(slist, cfg.settings['SL_hash_path'], 'SL hash path')
            aux_check_dir_WARN(slist, cfg.settings['SL_rom_path'], 'SL ROM path')
            aux_check_dir_WARN(slist, cfg.settings['SL_chd_path'], 'SL CHD path')
            slist.append('')

            slist.append('[COLOR orange]Software Lists assets[/COLOR]')
            if cfg.settings['assets_path']:
                if FileName(cfg.settings['assets_path']).exists():
                    slist.append('{} MAME Asset path "{}"'.format(OK, cfg.settings['assets_path']))

                    # >> Check that artwork subdirectories exist
                    Asset_path_FN = FileName(cfg.settings['assets_path'])

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
                    slist.append('{} MAME Asset path not found'.format(ERR))
            else:
                slist.append('{} MAME Asset path not set'.format(WARN))
            slist.append('')

        # --- Optional INI files ---
        slist.append('[COLOR orange]INI/DAT files[/COLOR]')
        if cfg.settings['dats_path']:
            if FileName(cfg.settings['dats_path']).exists():
                slist.append('{} MAME INI/DAT path "{}"'.format(OK, cfg.settings['dats_path']))

                DATS_dir_FN = FileName(cfg.settings['dats_path'])
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
                slist.append('{} MAME INI/DAT path not found'.format(ERR))
        else:
            slist.append('{} MAME INI/DAT path not set'.format(WARN))

        # --- Display info to the user ---
        kodi_display_text_window_mono('AML configuration check report', '\n'.join(slist))

    # Check and update all favourite objects.
    # Check if Favourites can be found in current MAME main database. It may happen that
    # a machine is renamed between MAME version although I think this is very unlikely.
    # MAME Favs can not be relinked. If the machine is not found in current database it must
    # be deleted by the user and a new Favourite created.
    # If the machine is found in the main database, then update the Favourite database
    # with data from the main database.
    elif which_utility == 'CHECK_ALL_FAV_OBJECTS':
        log_debug('command_exec_utility() Executing CHECK_ALL_FAV_OBJECTS...')

        # --- Load databases ---
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME machines render', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME machine assets', cfg.ASSET_DB_PATH.getPath()],
            ['SL_index', 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # --- Ensure databases are built and assets scanned before updating Favourites ---
        st_dic = kodi_new_status_dic()
        check_MAME_DB_status(st_dic, MAME_ASSETS_SCANNED, db_dic['control_dic'])
        if kodi_display_status_message(st_dic): return False

        mame_update_MAME_Fav_objects(cfg, db_dic)
        mame_update_MAME_MostPlay_objects(cfg, db_dic)
        mame_update_MAME_RecentPlay_objects(cfg, db_dic)
        mame_update_SL_Fav_objects(cfg, db_dic)
        mame_update_SL_MostPlay_objects(cfg, db_dic)
        mame_update_SL_RecentPlay_objects(cfg, db_dic)
        kodi_notify('All Favourite objects checked')
        kodi_refresh_container()

    # Check MAME and SL CRC 32 hash collisions.
    # The assumption in this function is that there is not SHA1 hash collisions.
    # Implicit ROM merging must not be confused with a collision.
    elif which_utility == 'CHECK_MAME_COLLISIONS':
        log_info('command_check_MAME_CRC_collisions() Initialising ...')

        # --- Check database ---
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        st_dic = kodi_new_status_dic()
        options = check_MAME_DB_status(st_dic, MAME_CATALOG_BUILT, control_dic)
        if kodi_display_status_message(st_dic): return False

        # --- Open ROMs database ---
        db_files = [
            ['machine_roms', 'MAME machine ROMs', cfg.ROMS_DB_PATH.getPath()],
            ['roms_sha1_dic', 'MAME ROMs SHA1 dictionary', cfg.SHA1_HASH_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # Detect implicit ROM merging using the SHA1 hash and check for CRC32 collisions for
        # non-implicit merged ROMs.
        pDialog = KodiProgressDialog()
        pDialog.startProgress('Checking for MAME CRC32 hash collisions...', len(db_dic['machine_roms']))
        crc_roms_dic = {}
        sha1_roms_dic = {}
        num_collisions = 0
        table_str = []
        table_str.append(['right',  'left',     'left', 'left', 'left'])
        table_str.append(['Status', 'ROM name', 'Size', 'CRC',  'SHA1'])
        for m_name in sorted(db_dic['machine_roms']):
            pDialog.updateProgressInc()
            m_roms = db_dic['machine_roms'][m_name]
            for rom in m_roms['roms']:
                rom_nonmerged_location = m_name + '/' + rom['name']
                # Skip invalid ROMs (no CRC, no SHA1
                if rom_nonmerged_location not in db_dic['roms_sha1_dic']:
                    continue
                sha1 = db_dic['roms_sha1_dic'][rom_nonmerged_location]
                if sha1 in sha1_roms_dic:
                    # ROM implicit merging (using SHA1). No check of CRC32 collision.
                    pass
                else:
                    # No ROM implicit mergin. Check CRC32 collision
                    sha1_roms_dic[sha1] = rom_nonmerged_location
                    if rom['crc'] in crc_roms_dic:
                        num_collisions += 1
                        coliding_name = crc_roms_dic[rom['crc']]
                        coliding_crc = rom['crc']
                        coliding_sha1 = db_dic['roms_sha1_dic'][coliding_name]
                        table_str.append(
                            ['Collision', rom_nonmerged_location, text_type(rom['size']), rom['crc'], sha1])
                        table_str.append(['with', coliding_name, ' ', coliding_crc, coliding_sha1])
                    else:
                        crc_roms_dic[rom['crc']] = rom_nonmerged_location
        pDialog.endProgress()
        log_debug('MAME has {:,d} valid ROMs in total'.format(len(db_dic['roms_sha1_dic'])))
        log_debug('There are {} CRC32 collisions'.format(num_collisions))

        # --- Write report and debug file ---
        slist = [
            '*** AML MAME ROMs CRC32 hash collision report ***',
            'MAME has {:,d} valid ROMs in total'.format(len(db_dic['roms_sha1_dic'])),
            'There are {} CRC32 collisions'.format(num_collisions),
            '',
        ]
        table_str_list = text_render_table_str(table_str)
        slist.extend(table_str_list)
        kodi_display_text_window_mono('AML MAME CRC32 hash collision report', '\n'.join(slist))
        log_info('Writing "{}"'.format(cfg.REPORT_DEBUG_MAME_COLLISIONS_PATH.getPath()))
        utils_write_slist_to_file(cfg.REPORT_DEBUG_MAME_COLLISIONS_PATH.getPath(), slist)

    elif which_utility == 'CHECK_SL_COLLISIONS':
        log_info('command_exec_utility() Initialising CHECK_SL_COLLISIONS ...')

        # --- Load SL catalog and check for errors ---
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        st_dic = kodi_new_status_dic()
        options = check_SL_DB_status(st_dic, SL_MAIN_DB_BUILT, control_dic)
        if kodi_display_status_message(st_dic): return False
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())

        # --- Process all SLs ---
        d_text = 'Scanning Sofware Lists ROMs/CHDs...'
        pDialog = KodiProgressDialog()
        pDialog.startProgress(d_text, len(SL_catalog_dic))
        roms_sha1_dic = {}
        crc_roms_dic = {}
        sha1_roms_dic = {}
        num_collisions = 0
        table_str = []
        table_str.append(['right',  'left',     'left', 'left', 'left'])
        table_str.append(['Status', 'ROM name', 'Size', 'CRC',  'SHA1'])
        for SL_name in sorted(SL_catalog_dic):
            pDialog.updateProgressInc('{}\nSoftware List "{}"'.format(d_text, SL_name))

            # Load SL databases
            # SL_SETS_DB_FN = SL_hash_dir_FN.pjoin(SL_name + '.json')
            # sl_sets = utils_load_JSON_file_dic(SL_SETS_DB_FN.getPath(), verbose = False)
            SL_ROMS_DB_FN = cfg.SL_DB_DIR.pjoin(SL_name + '_ROMs.json')
            sl_roms = utils_load_JSON_file_dic(SL_ROMS_DB_FN.getPath(), verbose = False)

            # First step: make a SHA1 dictionary of all SL item hashes.
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

            # Second step: make.
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
                                        text_type(rom['size']), rom['crc'], sha1
                                    ])
                                    table_str.append([
                                        'with', coliding_name, ' ',
                                        coliding_crc, coliding_sha1
                                    ])
                                else:
                                    crc_roms_dic[rom['crc']] = rom_nonmerged_location
        pDialog.endProgress()
        log_debug('The SL have {:,d} valid ROMs in total'.format(len(roms_sha1_dic)))
        log_debug('There are {} CRC32 collisions'.format(num_collisions))

        # --- Write report ---
        slist = [
            '*** AML SL ROMs CRC32 hash collision report ***',
            'The Software Lists have {:,d} valid ROMs in total'.format(len(roms_sha1_dic)),
            'There are {} CRC32 collisions'.format(num_collisions),
            '',
        ]
        table_str_list = text_render_table_str(table_str)
        slist.extend(table_str_list)
        kodi_display_text_window_mono('AML Software Lists CRC32 hash collision report', '\n'.join(slist))
        log_info('Writing "{}"'.format(cfg.REPORT_DEBUG_SL_COLLISIONS_PATH.getPath()))
        utils_write_slist_to_file(cfg.REPORT_DEBUG_SL_COLLISIONS_PATH.getPath(), slist)

    # Open the ROM audit database and calculate the size of all ROMs.
    # Sort the list by size and print it.
    elif which_utility == 'SHOW_BIGGEST_ROMS' or which_utility == 'SHOW_SMALLEST_ROMS':
        show_BIG = True if which_utility == 'SHOW_BIGGEST_ROMS' else False
        log_info('command_exec_utility() Initialising SHOW_BIGGEST_ROMS/SHOW_SMALLEST_ROMS...')
        log_info('command_exec_utility() show_BIG {}'.format(show_BIG))
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['renderdb', 'MAME machines Render', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME machine Assets', cfg.ASSET_DB_PATH.getPath()],
            ['roms', 'MAME machine ROMs', cfg.ROMS_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        st_dic = kodi_new_status_dic()
        options = check_MAME_DB_status(st_dic, MAME_MAIN_DB_BUILT, control_dic)
        if kodi_display_status_message(st_dic): return False

        # { mname : size (int), ... }
        m_size_dic = {}
        for mname in db_dic['renderdb']:
            roms = db_dic['roms'][mname]
            ROMs_size = 0
            invalid_ROMs = False
            for rom_dic in roms['roms']:
                ROMs_size += rom_dic['size']
            # If total size of ROMs is 0 is because all ROMs are invalid.
            # Do not add this machine to the dictionary.
            if ROMs_size == 0: continue
            m_size_dic[mname] = ROMs_size

        table_str = []
        table_str.append(['right', 'left', 'left', 'right'])
        NUM_MACHINES = 512
        DESC_MAX_LENGTH = 64
        machine_i = 0
        sorted_machine_list = []
        if show_BIG:
            table_str.append(['Short name', 'Flags', 'Long name', 'Size (MiB)'])
            for mname in sorted(m_size_dic, key = lambda item: m_size_dic[item], reverse = True):
                sorted_machine_list.append(mname)
                machine_i += 1
                if machine_i >= NUM_MACHINES: break
            for mname in sorted_machine_list:
                table_str.append([mname, db_dic['assetdb'][mname]['flags'],
                    text_limit_string(db_dic['renderdb'][mname]['description'], DESC_MAX_LENGTH),
                    '{:7.2f}'.format(m_size_dic[mname] / 1024**2),
                ])
        else:
            table_str.append(['Short name', 'Flags', 'Long name', 'Size'])
            for mname in sorted(m_size_dic, key = lambda item: m_size_dic[item], reverse = False):
                sorted_machine_list.append(mname)
                machine_i += 1
                if machine_i >= NUM_MACHINES: break
            for mname in sorted_machine_list:
                table_str.append([mname, db_dic['assetdb'][mname]['flags'],
                    text_limit_string(db_dic['renderdb'][mname]['description'], DESC_MAX_LENGTH),
                    '{:,d}'.format(m_size_dic[mname]),
                ])

        # --- Write report ---
        slist = []
        table_str_list = text_render_table_str(table_str)
        slist.extend(table_str_list)
        if show_BIG:
            window_title = 'MAME machines with biggest ROMs'
        else:
            window_title = 'MAME machines with smallest ROMs'
        kodi_display_text_window_mono(window_title, '\n'.join(slist))

    # Export MAME information in Billyc999 XML format to use with RCB.
    elif which_utility == 'EXPORT_MAME_INFO_BILLYC999_XML':
        log_info('command_exec_utility() Initialising EXPORT_MAME_INFO_BILLYC999_XML...')
        dir_path = kodi_dialog_get_wdirectory('Chose directory to write MAME info XML')
        if not dir_path: return
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ['assetdb', 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)
        mame_write_MAME_ROM_Billyc999_XML(cfg, FileName(dir_path), db_dic)

    # Export a MAME ROM DAT XML file with Logiqx format.
    # The DAT will be Merged, Split, Non-merged or Fully Non-merged same as the current
    # AML database.
    elif which_utility == 'EXPORT_MAME_ROM_DAT':
        log_info('command_exec_utility() Initialising EXPORT_MAME_ROM_DAT...')
        dir_path = kodi_dialog_get_wdirectory('Chose directory to write MAME ROMs DAT')
        if not dir_path: return

        # Open databases.
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ['audit_roms', 'MAME ROM Audit', cfg.ROM_AUDIT_DB_PATH.getPath()],
            ['roms_sha1_dic', 'MAME ROMs SHA1 dictionary', cfg.SHA1_HASH_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # Write MAME ROM dat. Notifies the user if successful.
        mame_write_MAME_ROM_XML_DAT(cfg, FileName(dir_path), db_dic)

    elif which_utility == 'EXPORT_MAME_CHD_DAT':
        log_info('command_exec_utility() Initialising EXPORT_MAME_CHD_DAT ...')
        dir_path = kodi_dialog_get_wdirectory('Chose directory to write MAME CHDs DAT')
        if not dir_path: return

        # Open databases.
        db_files = [
            ['control_dic', 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
            ['machines', 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
            ['renderdb', 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
            ['audit_roms', 'MAME ROM Audit', cfg.ROM_AUDIT_DB_PATH.getPath()],
        ]
        db_dic = db_load_files(db_files)

        # Write MAME ROM dat. Notifies the user if successful.
        mame_write_MAME_CHD_XML_DAT(cfg, FileName(dir_path), db_dic)

    elif which_utility == 'EXPORT_SL_ROM_DAT':
        log_info('command_exec_utility() Initialising EXPORT_SL_ROM_DAT ...')
        kodi_dialog_OK('EXPORT_SL_ROM_DAT not implemented yet. Sorry.')

    elif which_utility == 'EXPORT_SL_CHD_DAT':
        log_info('command_exec_utility() Initialising EXPORT_SL_CHD_DAT ...')
        kodi_dialog_OK('EXPORT_SL_CHD_DAT not implemented yet. Sorry.')

    else:
        u = 'Utility "{}" not found. This is a bug, please report it.'.format(which_utility)
        log_error(u)
        kodi_dialog_OK(u)

#
# Execute view reports.
#
def command_exec_report(cfg, which_report):
    log_debug('command_exec_report() which_report = "{}" starting ...'.format(which_report))

    if which_report == 'VIEW_EXEC_OUTPUT':
        if not cfg.MAME_OUTPUT_PATH.exists():
            kodi_dialog_OK('MAME output file not found. Execute MAME and try again.')
            return
        info_text = utils_load_file_to_str(cfg.MAME_OUTPUT_PATH.getPath())
        kodi_display_text_window_mono('MAME last execution output', info_text)

    # --- View database information and statistics stored in control dictionary ------------------
    elif which_report == 'VIEW_STATS_MAIN':
        if not cfg.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        if cfg.settings['op_mode'] == OP_MODE_VANILLA:
            XML_ctrl_dic = utils_load_JSON_file_dic(cfg.MAME_XML_CONTROL_PATH.getPath())
        elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
            XML_ctrl_dic = utils_load_JSON_file_dic(cfg.MAME_2003_PLUS_XML_CONTROL_PATH.getPath())
        else:
            XML_ctrl_dic = db_new_MAME_XML_control_dic()
        info_text = []
        mame_stats_main_print_slist(cfg, info_text, control_dic, XML_ctrl_dic)
        kodi_display_text_window_mono('Database main statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_SCANNER':
        if not cfg.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_scanner_print_slist(cfg, info_text, control_dic)
        kodi_display_text_window_mono('Scanner statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_AUDIT':
        if not cfg.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_audit_print_slist(cfg, info_text, control_dic)
        kodi_display_text_window_mono('Database information and statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_TIMESTAMPS':
        if not cfg.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        info_text = []
        mame_stats_timestamps_slist(cfg, info_text, control_dic)
        kodi_display_text_window_mono('Database information and statistics', '\n'.join(info_text))

    # --- All statistics ---
    elif which_report == 'VIEW_STATS_ALL':
        if not cfg.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        if cfg.settings['op_mode'] == OP_MODE_VANILLA:
            XML_ctrl_dic = utils_load_JSON_file_dic(cfg.MAME_XML_CONTROL_PATH.getPath())
        elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
            XML_ctrl_dic = utils_load_JSON_file_dic(cfg.MAME_2003_PLUS_XML_CONTROL_PATH.getPath())
        else:
            XML_ctrl_dic = db_new_MAME_XML_control_dic()

        info_text = []
        mame_stats_main_print_slist(cfg, info_text, control_dic, XML_ctrl_dic)
        info_text.append('')
        mame_stats_scanner_print_slist(cfg, info_text, control_dic)
        info_text.append('')
        mame_stats_audit_print_slist(cfg, info_text, control_dic)
        info_text.append('')
        mame_stats_timestamps_slist(cfg, info_text, control_dic)
        kodi_display_text_window_mono('Database full statistics', '\n'.join(info_text))

    elif which_report == 'VIEW_STATS_WRITE_FILE':
        if not cfg.MAIN_CONTROL_PATH.exists():
            kodi_dialog_OK('MAME database not found. Please setup the addon first.')
            return
        control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
        if cfg.settings['op_mode'] == OP_MODE_VANILLA:
            XML_ctrl_dic = utils_load_JSON_file_dic(cfg.MAME_XML_CONTROL_PATH.getPath())
        elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
            XML_ctrl_dic = utils_load_JSON_file_dic(cfg.MAME_2003_PLUS_XML_CONTROL_PATH.getPath())
        else:
            XML_ctrl_dic = db_new_MAME_XML_control_dic()

        # --- Generate stats string and remove Kodi colours ---
        info_text = []
        mame_stats_main_print_slist(cfg, info_text, control_dic, XML_ctrl_dic)
        info_text.append('')
        mame_stats_scanner_print_slist(cfg, info_text, control_dic)
        info_text.append('')
        mame_stats_audit_print_slist(cfg, info_text, control_dic)
        info_text.append('')
        mame_stats_timestamps_slist(cfg, info_text, control_dic)

        # --- Write file to disk and inform user ---
        log_info('Writing AML statistics report...')
        log_info('File "{}"'.format(cfg.REPORT_STATS_PATH.getPath()))
        text_remove_color_tags_slist(info_text)
        utils_write_slist_to_file(cfg.REPORT_STATS_PATH.getPath(), info_text)
        kodi_notify('Exported AML statistics')

    # --- MAME scanner reports -------------------------------------------------------------------
    elif which_report == 'VIEW_SCANNER_MAME_ARCH_FULL':
        if not cfg.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.exists():
            kodi_dialog_OK('Full MAME machines archives scanner report not found. '
                'Please scan MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath())
        kodi_display_text_window_mono('Full MAME machines archives scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_MAME_ARCH_HAVE':
        if not cfg.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.exists():
            kodi_dialog_OK('Have MAME machines archives scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath())
        kodi_display_text_window_mono('Have MAME machines archives scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_MAME_ARCH_MISS':
        if not cfg.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME machines archives scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath())
        kodi_display_text_window_mono('Missing MAME machines archives scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_MAME_ROM_LIST_MISS':
        if not cfg.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME ROM ZIP list scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath())
        kodi_display_text_window_mono('Missing MAME ROM ZIP list scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_MAME_SAM_LIST_MISS':
        if not cfg.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME Sample ZIP list scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH.getPath())
        kodi_display_text_window_mono('Missing MAME Sample ZIP list scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_MAME_CHD_LIST_MISS':
        if not cfg.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.exists():
            kodi_dialog_OK('Missing MAME CHD list scanner report not found. '
                           'Please scan MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath())
        kodi_display_text_window_mono('Missing MAME CHD list scanner report', fstring)

    # --- SL scanner reports ---------------------------------------------------------------------
    elif which_report == 'VIEW_SCANNER_SL_FULL':
        if not cfg.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.exists():
            kodi_dialog_OK('Full Software Lists item archives scanner report not found. '
                           'Please scan SL ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath())
        kodi_display_text_window_mono('Full Software Lists item archives scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_SL_HAVE':
        if not cfg.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.exists():
            kodi_dialog_OK('Have Software Lists item archives scanner report not found. '
                           'Please scan SL ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath())
        kodi_display_text_window_mono('Have Software Lists item archives scanner report', fstring)

    elif which_report == 'VIEW_SCANNER_SL_MISS':
        if not cfg.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.exists():
            kodi_dialog_OK('Missing Software Lists item archives scanner report not found. '
                           'Please scan SL ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath())
        kodi_display_text_window_mono('Missing Software Lists item archives scanner report', fstring)

    # --- Asset scanner reports ------------------------------------------------------------------
    elif which_report == 'VIEW_SCANNER_MAME_ASSETS':
        if not cfg.REPORT_MAME_ASSETS_PATH.exists():
            kodi_dialog_OK('MAME asset report report not found. '
                           'Please scan MAME assets and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_ASSETS_PATH.getPath())
        kodi_display_text_window_mono('MAME asset report', fstring)

    elif which_report == 'VIEW_SCANNER_SL_ASSETS':
        if not cfg.REPORT_SL_ASSETS_PATH.exists():
            kodi_dialog_OK('Software Lists asset report not found. '
                           'Please scan Software List assets and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_ASSETS_PATH.getPath())
        kodi_display_text_window_mono('Software Lists asset report', fstring)

    # --- MAME audit reports ---------------------------------------------------------------------
    elif which_report == 'VIEW_AUDIT_MAME_FULL':
        if not cfg.REPORT_MAME_AUDIT_FULL_PATH.exists():
            kodi_dialog_OK('MAME audit report (Full) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_FULL_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (Full)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_GOOD':
        if not cfg.REPORT_MAME_AUDIT_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_GOOD_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (Good)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_BAD':
        if not cfg.REPORT_MAME_AUDIT_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (Errors)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_ROM_GOOD':
        if not cfg.REPORT_MAME_AUDIT_ROM_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROMs Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_ROM_GOOD_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (ROMs Good)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_ROM_BAD':
        if not cfg.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROM Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (ROM Errors)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_SAM_GOOD':
        if not cfg.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (Samples Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (Samples Good)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_SAM_BAD':
        if not cfg.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (Sample Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (Sample Errors)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_CHD_GOOD':
        if not cfg.REPORT_MAME_AUDIT_CHD_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHDs Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_CHD_GOOD_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (CHDs Good)', fstring)

    elif which_report == 'VIEW_AUDIT_MAME_CHD_BAD':
        if not cfg.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHD Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (CHD Errors)', fstring)

    # --- SL audit reports -----------------------------------------------------------------------
    elif which_report == 'VIEW_AUDIT_SL_FULL':
        if not cfg.REPORT_SL_AUDIT_FULL_PATH.exists():
            kodi_dialog_OK('SL audit report (Full) not found. '
                           'Please audit your SL ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_FULL_PATH.getPath())
        kodi_display_text_window_mono('SL audit report (Full)', fstring)

    elif which_report == 'VIEW_AUDIT_SL_GOOD':
        if not cfg.REPORT_SL_AUDIT_GOOD_PATH.exists():
            kodi_dialog_OK('SL audit report (Good) not found. '
                           'Please audit your SL ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_GOOD_PATH.getPath())
        kodi_display_text_window_mono('SL audit report (Good)', fstring)

    elif which_report == 'VIEW_AUDIT_SL_BAD':
        if not cfg.REPORT_SL_AUDIT_ERRORS_PATH.exists():
            kodi_dialog_OK('SL audit report (Errors) not found. '
                           'Please audit your SL ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('SL audit report (Errors)', fstring)

    elif which_report == 'VIEW_AUDIT_SL_ROM_GOOD':
        if not cfg.REPORT_SL_AUDIT_ROMS_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROM Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_ROMS_GOOD_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (ROM Good)', fstring)

    elif which_report == 'VIEW_AUDIT_SL_ROM_BAD':
        if not cfg.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (ROM Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (ROM Errors)', fstring)

    elif which_report == 'VIEW_AUDIT_SL_CHD_GOOD':
        if not cfg.REPORT_SL_AUDIT_CHDS_GOOD_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHD Good) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_CHDS_GOOD_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (CHD Good)', fstring)

    elif which_report == 'VIEW_AUDIT_SL_CHD_BAD':
        if not cfg.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.exists():
            kodi_dialog_OK('MAME audit report (CHD Errors) not found. '
                           'Please audit your MAME ROMs and try again.')
            return
        fstring = utils_load_file_to_str(cfg.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.getPath())
        kodi_display_text_window_mono('MAME audit report (CHD Errors)', fstring)

    # --- Error ----------------------------------------------------------------------------------
    else:
        u = 'Report "{}" not found. This is a bug, please report it.'.format(which_report)
        log_error(u)
        kodi_dialog_OK(u)

#
# Launch MAME machine. Syntax: $ mame <machine_name> [options]
# Example: $ mame dino
#
def run_machine(cfg, machine_name, location):
    log_info('run_machine() Launching MAME machine  "{}"'.format(machine_name))
    log_info('run_machine() Launching MAME location "{}"'.format(location))

    # --- Load databases ---
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    if location == LOCATION_STANDARD:
        log_debug('Reading info from hashed DBs')
        machine = db_get_machine_main_hashed_db(cfg, machine_name)
        assets = db_get_machine_assets_hashed_db(cfg, machine_name)
    elif location == LOCATION_MAME_FAVS:
        log_debug('Reading info from MAME Favourites')
        fav_machines = utils_load_JSON_file_dic(cfg.FAV_MACHINES_PATH.getPath())
        machine = fav_machines[machine_name]
        assets = machine['assets']
    elif location == LOCATION_MAME_MOST_PLAYED:
        log_debug('Reading info from MAME Most Played DB')
        most_played_roms_dic = utils_load_JSON_file_dic(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath())
        machine = most_played_roms_dic[machine_name]
        assets = machine['assets']
    elif location == LOCATION_MAME_RECENT_PLAYED:
        log_debug('Reading info from MAME Recently Played DB')
        recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())
        machine_index = db_locate_idx_by_MAME_name(recent_roms_list, machine_name)
        if machine_index < 0:
            a = 'Machine {} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(machine_name))
            return
        machine = recent_roms_list[machine_index]
        assets = machine['assets']
    else:
        kodi_dialog_OK('Unknown location = "{}". This is a bug, please report it.'.format(location))
        return

    # Check if ROM ZIP file exists.
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        rom_path = cfg.settings['rom_path_vanilla']
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        rom_path = cfg.settings['rom_path_2003_plus']
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
    if not rom_path:
        kodi_dialog_OK('ROM directory not configured.')
        return
    ROM_path_FN = FileName(rom_path)
    if not ROM_path_FN.isdir():
        kodi_dialog_OK('ROM directory does not exist.')
        return
    ROM_FN = ROM_path_FN.pjoin(machine_name + '.zip')
    # if not ROM_FN.exists():
    #     kodi_dialog_OK('ROM "{}" not found.'.format(ROM_FN.getBase()))
    #     return

    # Choose BIOS (only available for Favourite Machines).
    # Not implemented at the moment
    # if location and location == 'MAME_FAV' and len(machine['bios_name']) > 1:
    #     dialog = xbmcgui.Dialog()
    #     m_index = dialog.select('Select BIOS', machine['bios_desc'])
    #     if m_index < 0: return
    #     BIOS_name = machine['bios_name'][m_index]
    # else:
    #     BIOS_name = ''
    BIOS_name = ''

    # Launch machine using subprocess module.
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        mame_prog_FN = FileName(cfg.settings['mame_prog'])
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        mame_prog_FN = FileName(cfg.settings['retroarch_prog'])
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
    (mame_dir, mame_exec) = os.path.split(mame_prog_FN.getPath())
    log_debug('run_machine() mame_prog_FN "{}"'.format(mame_prog_FN.getPath()))
    log_debug('run_machine() mame_dir     "{}"'.format(mame_dir))
    log_debug('run_machine() mame_exec    "{}"'.format(mame_exec))
    log_debug('run_machine() machine_name "{}"'.format(machine_name))
    log_debug('run_machine() BIOS_name    "{}"'.format(BIOS_name))

    # --- Compute ROM recently played list ---
    # If the machine is already in the list remove it and place it on the first position.
    MAX_RECENT_PLAYED_ROMS = 100
    recent_rom = db_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic)
    recent_roms_list = utils_load_JSON_file_list(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    # Machine names are unique in this list.
    recent_roms_list = [machine for machine in recent_roms_list if machine_name != machine['name']]
    recent_roms_list.insert(0, recent_rom)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('run_machine() len(recent_roms_list) = {}'.format(len(recent_roms_list)))
        log_debug('run_machine() Trimming list to {} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    utils_write_JSON_file(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms_dic = utils_load_JSON_file_dic(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if recent_rom['name'] in most_played_roms_dic:
        rom_name = recent_rom['name']
        most_played_roms_dic[rom_name]['launch_count'] += 1
    else:
        # Add field launch_count to recent_rom to count how many times have been launched.
        recent_rom['launch_count'] = 1
        most_played_roms_dic[recent_rom['name']] = recent_rom
    utils_write_JSON_file(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)

    # --- Build final arguments to launch MAME ---
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        # arg_list = [mame_prog_FN.getPath(), '-window', machine_name]
        arg_list = [mame_prog_FN.getPath(), machine_name]
        if BIOS_name: arg_list.extend(['-bios', BIOS_name])
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        if is_windows():
            core_path = os.path.join(cfg.settings['libretro_dir'], 'mame2003_plus_libretro.dll')
        elif is_linux():
            core_path = os.path.join(cfg.settings['libretro_dir'], 'mame2003_plus_libretro.so')
        else:
            raise TypeError('Unsupported platform "{}"'.format(cached_sys_platform))
        machine_path = os.path.join(cfg.settings['rom_path_2003_plus'], machine_name + '.zip')
        arg_list = [mame_prog_FN.getPath(), '-L', core_path, machine_path]
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
    log_info('arg_list = {}'.format(arg_list))

    # --- User notification ---
    if cfg.settings['display_launcher_notify']:
        kodi_notify('Launching MAME machine "{}"'.format(machine_name))
    if DISABLE_MAME_LAUNCHING:
        log_info('run_machine() MAME launching disabled. Exiting function.')
        return

    # --- Run MAME ---
    run_before_execution(cfg)
    run_process(cfg, arg_list, mame_dir)
    run_after_execution(cfg)
    # Refresh list so Most Played and Recently played get updated.
    log_info('run_machine() Exiting function.')
    kodi_refresh_container()

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
def run_SL_machine(cfg, SL_name, SL_ROM_name, location):
    SL_LAUNCH_WITH_MEDIA = 100
    SL_LAUNCH_NO_MEDIA   = 200
    log_info('run_SL_machine() Launching SL machine (location = {}) ...'.format(location))
    log_info('run_SL_machine() SL_name     "{}"'.format(SL_name))
    log_info('run_SL_machine() SL_ROM_name "{}"'.format(SL_ROM_name))

    # --- Get paths ---
    mame_prog_FN = FileName(cfg.settings['mame_prog'])

    # --- Get a list of launch machine <devices> and SL ROM <parts> ---
    # --- Load SL ROMs and SL assets databases ---
    control_dic = utils_load_JSON_file_dic(cfg.MAIN_CONTROL_PATH.getPath())
    if location == LOCATION_STANDARD:
        # >> Load DBs
        log_info('run_SL_machine() SL ROM is in Standard Location')
        SL_catalog_dic = utils_load_JSON_file_dic(cfg.SL_INDEX_PATH.getPath())
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json')
        log_info('run_SL_machine() SL ROMs JSON "{}"'.format(SL_DB_FN.getPath()))
        SL_ROMs = utils_load_JSON_file_dic(SL_DB_FN.getPath())
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json')
        SL_asset_dic = utils_load_JSON_file_dic(SL_asset_DB_FN.getPath())
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
        fav_SL_roms = utils_load_JSON_file_dic(cfg.FAV_SL_ROMS_PATH.getPath())
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
        most_played_roms_dic = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = most_played_roms_dic[SL_fav_DB_key]
        SL_assets = SL_ROM['assets']
        part_list = most_played_roms_dic[SL_fav_DB_key]['parts']
        launch_machine_name = most_played_roms_dic[SL_fav_DB_key]['launch_machine']
        launch_machine_desc = '[ Not available ]'
    elif location == LOCATION_SL_RECENT_PLAYED:
        log_debug('Reading info from MAME Recently Played DB')
        recent_roms_list = utils_load_JSON_file_list(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())
        machine_index = db_locate_idx_by_SL_item_name(recent_roms_list, SL_name, SL_ROM_name)
        if machine_index < 0:
            a = 'SL Item {} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(SL_fav_DB_key))
            return
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = recent_roms_list[machine_index]
        SL_assets = SL_ROM['assets']
        part_list = recent_roms_list[machine_index]['parts']
        launch_machine_name = recent_roms_list[machine_index]['launch_machine']
        launch_machine_desc = '[ Not available ]'
    else:
        kodi_dialog_OK('Unknown location = "{}". This is a bug, please report it.'.format(location))
        return
    log_info('run_SL_machine() launch_machine_name = "{}"'.format(launch_machine_name))
    log_info('run_SL_machine() launch_machine_desc = "{}"'.format(launch_machine_desc))

    # --- Load SL machines ---
    SL_machines_dic = utils_load_JSON_file_dic(cfg.SL_MACHINES_PATH.getPath())
    SL_machine_list = SL_machines_dic[SL_name]
    if not launch_machine_name:
        # >> Get a list of machines that can launch this SL ROM. User chooses in a select dialog
        log_info('run_SL_machine() User selecting SL run machine ...')
        SL_machine_names_list = []
        SL_machine_desc_list  = []
        SL_machine_devices    = []
        for SL_machine in sorted(SL_machine_list, key = lambda x: x['description'].lower()):
            SL_machine_names_list.append(SL_machine['machine'])
            SL_machine_desc_list.append(SL_machine['description'])
            SL_machine_devices.append(SL_machine['devices'])
        m_index = xbmcgui.Dialog().select('Select machine', SL_machine_desc_list)
        if m_index < 0: return
        launch_machine_name    = SL_machine_names_list[m_index]
        launch_machine_desc    = SL_machine_desc_list[m_index]
        launch_machine_devices = SL_machine_devices[m_index]
        log_info('run_SL_machine() User chose machine "{}" ({})'.format(launch_machine_name, launch_machine_desc))
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
            log_info('run_SL_machine() Found machine "{}"'.format(launch_machine_name))
            launch_machine_desc    = SL_machine['description']
            launch_machine_devices = SL_machine['devices']
        else:
            log_error('run_SL_machine() Machine "{}" not found'.format(launch_machine_name))
            log_error('run_SL_machine() Aborting launch')
            kodi_dialog_OK('Machine "{}" not found. Aborting launch.'.format(launch_machine_name))
            return

    # --- DEBUG ---
    log_info('run_SL_machine() Machine "{}" has {} interfaces'.format(launch_machine_name, len(launch_machine_devices)))
    log_info('run_SL_machine() SL ROM  "{}" has {} parts'.format(SL_ROM_name, len(part_list)))
    for device_dic in launch_machine_devices:
        u = '<device type="{}" interface="{}">'.format(device_dic['att_type'], device_dic['att_interface'])
        log_info(u)
    for part_dic in part_list:
        u = '<part name="{}" interface="{}">'.format(part_dic['name'], part_dic['interface'])
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
        log_info('run_SL_machine() Matched machine device interface "{}" '.format(device['att_interface']) +
                 'to SL ROM part "{}"'.format(part_list[0]['interface']))
        sl_launch_mode = SL_LAUNCH_WITH_MEDIA

    # >> Case D.
    # >> User chooses media to launch?
    elif num_machine_interfaces > 1 and num_SL_ROM_parts > 1:
        log_info('run_SL_machine() Launch case D)')
        launch_case = SL_LAUNCH_CASE_D
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    else:
        log_info(text_type(machine_interfaces))
        log_warning('run_SL_machine() Logical error in SL launch case.')
        launch_case = SL_LAUNCH_CASE_ERROR
        kodi_dialog_OK('Logical error in SL launch case. This is a bug, please report it.')
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    # >> Display some DEBUG information.
    kodi_dialog_OK('Launch case {}. '.format(launch_case) +
        'Machine has {} device interface/s and '.format(num_machine_interfaces) +
        'SL ROM has {} part/s. '.format(num_SL_ROM_parts) +
        'Media name is "{}"'.format(media_name))

    # --- Launch machine using subprocess module ---
    (mame_dir, mame_exec) = os.path.split(mame_prog_FN.getPath())
    log_debug('run_SL_machine() mame_prog_FN "{}"'.format(mame_prog_FN.getPath()))
    log_debug('run_SL_machine() mame_dir     "{}"'.format(mame_dir))
    log_debug('run_SL_machine() mame_exec    "{}"'.format(mame_exec))
    log_debug('run_SL_machine() launch_machine_name "{}"'.format(launch_machine_name))
    log_debug('run_SL_machine() launch_machine_desc "{}"'.format(launch_machine_desc))
    log_debug('run_SL_machine() media_name          "{}"'.format(media_name))

    # --- Compute ROM recently played list ---
    # If the machine is already in the list remove it and place it on the first position.
    MAX_RECENT_PLAYED_ROMS = 100
    recent_ROM = db_get_SL_Favourite(SL_name, SL_ROM_name, SL_ROM, SL_assets, control_dic)
    recent_roms_list = utils_load_JSON_file_list(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath())
    # Machine names are unique in this list
    recent_roms_list = [item for item in recent_roms_list if SL_fav_DB_key != item['SL_DB_key']]
    recent_roms_list.insert(0, recent_ROM)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('run_SL_machine() len(recent_roms_list) = {}'.format(len(recent_roms_list)))
        log_debug('run_SL_machine() Trimming list to {} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    utils_write_JSON_file(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms_dic = utils_load_JSON_file_dic(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
    if SL_fav_DB_key in most_played_roms_dic:
        most_played_roms_dic[SL_fav_DB_key]['launch_count'] += 1
    else:
        # >> Add field launch_count to recent_ROM to count how many times have been launched.
        recent_ROM['launch_count'] = 1
        most_played_roms_dic[SL_fav_DB_key] = recent_ROM
    utils_write_JSON_file(cfg.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)

    # --- Build MAME arguments ---
    if sl_launch_mode == SL_LAUNCH_WITH_MEDIA:
        arg_list = [mame_prog_FN.getPath(), launch_machine_name, '-{}'.format(media_name), SL_ROM_name]
    elif sl_launch_mode == SL_LAUNCH_NO_MEDIA:
        arg_list = [mame_prog_FN.getPath(), launch_machine_name, '{}:{}'.format(SL_name, SL_ROM_name)]
    else:
        kodi_dialog_OK('Unknown sl_launch_mode = {}. This is a bug, please report it.'.format(sl_launch_mode))
        return
    log_info('arg_list = {}'.format(arg_list))

    # --- User notification ---
    if cfg.settings['display_launcher_notify']:
        kodi_notify('Launching MAME SL item "{}"'.format(SL_ROM_name))
    if DISABLE_MAME_LAUNCHING:
        log_info('run_machine() MAME launching disabled. Exiting function.')
        return

    # --- Run MAME ---
    run_before_execution(cfg)
    run_process(cfg, arg_list, mame_dir)
    run_after_execution(cfg)
    # Refresh list so Most Played and Recently played get updated.
    kodi_refresh_container()
    log_info('run_SL_machine() Exiting function.')

def run_before_execution(cfg):
    global g_flag_kodi_was_playing
    global g_flag_kodi_audio_suspended
    global g_flag_kodi_toggle_fullscreen
    log_info('run_before_execution() Function BEGIN ...')

    # --- Stop/Pause Kodi mediaplayer if requested in settings ---
    # id = "media_state_action" default = "0" values = "Stop|Pause|Keep playing"
    g_flag_kodi_was_playing = False
    media_state_action = cfg.settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Keep playing'][media_state_action]
    a = 'run_before_execution() media_state_action is "{}" ({})'
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
    if cfg.settings['suspend_audio_engine']:
        log_verb('run_before_execution() Suspending Kodi audio engine')
        xbmc.audioSuspend()
        xbmc.enableNavSounds(False)
        xbmc.sleep(100)
        g_flag_kodi_audio_suspended = True
    else:
        log_verb('run_before_execution() DO NOT suspend Kodi audio engine')

    # --- Force joystick suspend if requested in "Settings" --> "Advanced"
    # NOT IMPLEMENTED YET.
    # See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
    # See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
    # See https://forum.kodi.tv/showthread.php?tid=313615

    # --- Toggle Kodi windowed/fullscreen if requested ---
    g_flag_kodi_toggle_fullscreen = False
    if cfg.settings['toggle_window']:
        log_verb('run_before_execution() Toggling Kodi from fullscreen to window')
        kodi_toogle_fullscreen()
        g_flag_kodi_toggle_fullscreen = True
    else:
        log_verb('run_before_execution() Toggling Kodi fullscreen/windowed DISABLED')

    # Disable screensaver
    if cfg.settings['suspend_screensaver']:
        kodi_disable_screensaver()
    else:
        screensaver_mode = kodi_get_screensaver_mode()
        log_debug('run_before_execution() Screensaver status "{}"'.format(screensaver_mode))

    # --- Pause Kodi execution some time ---
    delay_tempo_ms = cfg.settings['delay_tempo']
    log_verb('run_before_execution() Pausing {} ms'.format(delay_tempo_ms))
    xbmc.sleep(delay_tempo_ms)
    log_debug('run_before_execution() function ENDS')

def run_process(cfg, arg_list, mame_dir):
    log_info('run_process() Function BEGIN...')

    # --- Prevent a console window to be shown in Windows. Not working yet! ---
    if is_windows():
        log_info('run_process() Platform is win32. Creating _info structure')
        _info = subprocess.STARTUPINFO()
        _info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        # See https://msdn.microsoft.com/en-us/library/ms633548(v=vs.85).aspx
        # See https://docs.python.org/2/library/subprocess.html#subprocess.STARTUPINFO
        # SW_HIDE = 0
        # Does not work: MAME console window is not shown, graphical window not shown either,
        # process run in background.
        # _info.wShowWindow = subprocess.SW_HIDE
        # SW_SHOWMINIMIZED = 2
        # Both MAME console and graphical window minimized.
        # _info.wShowWindow = 2
        # SW_SHOWNORMAL = 1
        # MAME console window is shown, MAME graphical window on top, Kodi on bottom.
        _info.wShowWindow = 1
    elif is_linux():
        log_info('run_process() _info is None')
        _info = None
    else:
        raise TypeError('Unsupported platform "{}"'.format(cached_sys_platform))

    # --- Run MAME ---
    f = io.open(cfg.MAME_OUTPUT_PATH.getPath(), 'wb')
    p = subprocess.Popen(arg_list, cwd = mame_dir, startupinfo = _info, stdout = f, stderr = subprocess.STDOUT)
    p.wait()
    f.close()
    log_debug('run_process() function ENDS')

def run_after_execution(cfg):
    log_info('run_after_execution() Function BEGIN ...')

    # --- Stop Kodi some time ---
    delay_tempo_ms = cfg.settings['delay_tempo']
    log_verb('run_after_execution() Pausing {} ms'.format(delay_tempo_ms))
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

    # Restore screensaver status.
    if cfg.settings['suspend_screensaver']:
        kodi_restore_screensaver()
    else:
        screensaver_mode = kodi_get_screensaver_mode()
        log_debug('run_after_execution() Screensaver status "{}"'.format(screensaver_mode))

    # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
    # >> id="media_state_action" default="0" values="Stop|Pause|Keep playing"
    media_state_action = cfg.settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Keep playing'][media_state_action]
    a = 'run_after_execution() media_state_action is "{}" ({})'
    log_verb(a.format(media_state_str, media_state_action))
    log_verb('run_after_execution() g_flag_kodi_was_playing is {}'.format(g_flag_kodi_was_playing))
    if g_flag_kodi_was_playing and media_state_action == 1:
        log_verb('run_after_execution() Executing built-in PlayerControl(play)')
        # When Kodi is in "pause" mode, resume is used to continue play.
        xbmc.executebuiltin('PlayerControl(resume)')
    log_debug('run_after_execution() Function ENDS')
