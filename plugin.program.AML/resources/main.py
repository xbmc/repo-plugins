# -*- coding: utf-8 -*-
#
# Advanced MAME Launcher main script file
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
# Division operator: https://www.python.org/dev/peps/pep-0238/
from __future__ import unicode_literals
from __future__ import division
import os
import urlparse
import subprocess
import copy
from datetime import datetime

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
# Addon module dependencies:
#   main <-- mame <-- disk_IO <-- assets, utils, utils_kodi, constants
#   ReaderPDF <-- utils, utils_kodi
#   filters <- mame <-- utils, utils_kodi
#   manuals <- utils, utils_kodi
from constants import *
from assets import *
from utils import *
from utils_kodi import *
from disk_IO import *
from mame import *
from filters import *
from manuals import *

# --- Addon object (used to access settings) ---
__addon__         = xbmcaddon.Addon()
__addon_id__      = __addon__.getAddonInfo('id').decode('utf-8')
__addon_name__    = __addon__.getAddonInfo('name').decode('utf-8')
__addon_version__ = __addon__.getAddonInfo('version').decode('utf-8')
__addon_author__  = __addon__.getAddonInfo('author').decode('utf-8')
__addon_profile__ = __addon__.getAddonInfo('profile').decode('utf-8')
__addon_type__    = __addon__.getAddonInfo('type').decode('utf-8')

# --- Addon paths and constant definition ---
# _PATH is a filename | _DIR is a directory
ADDONS_DATA_DIR      = FileName('special://profile/addon_data')
PLUGIN_DATA_DIR      = ADDONS_DATA_DIR.pjoin(__addon_id__)
BASE_DIR             = FileName('special://profile')
HOME_DIR             = FileName('special://home')
KODI_FAV_PATH        = FileName('special://profile/favourites.xml')
ADDONS_DIR           = HOME_DIR.pjoin('addons')
AML_ADDON_DIR        = ADDONS_DIR.pjoin(__addon_id__)
AML_ICON_FILE_PATH   = AML_ADDON_DIR.pjoin('media/icon.png')
AML_FANART_FILE_PATH = AML_ADDON_DIR.pjoin('media/fanart.jpg')

# --- Plugin database indices ---
class AML_Paths:
    def __init__(self):
        # >> MAME stdout/strderr files
        self.MAME_STDOUT_PATH     = PLUGIN_DATA_DIR.pjoin('log_stdout.log')
        self.MAME_STDERR_PATH     = PLUGIN_DATA_DIR.pjoin('log_stderr.log')
        self.MAME_STDOUT_VER_PATH = PLUGIN_DATA_DIR.pjoin('log_version_stdout.log')
        self.MAME_STDERR_VER_PATH = PLUGIN_DATA_DIR.pjoin('log_version_stderr.log')
        self.MAME_OUTPUT_PATH     = PLUGIN_DATA_DIR.pjoin('log_output.log')
        self.MONO_FONT_PATH       = AML_ADDON_DIR.pjoin('fonts/Inconsolata.otf')

        # >> MAME XML, main database and main PClone list.
        self.MAME_XML_PATH        = PLUGIN_DATA_DIR.pjoin('MAME.xml')
        self.MAIN_ASSETS_DB_PATH  = PLUGIN_DATA_DIR.pjoin('MAME_assets.json')
        self.MAIN_CONTROL_PATH    = PLUGIN_DATA_DIR.pjoin('MAME_control_dic.json')
        self.DEVICES_DB_PATH      = PLUGIN_DATA_DIR.pjoin('MAME_DB_devices.json')
        self.MAIN_DB_PATH         = PLUGIN_DATA_DIR.pjoin('MAME_DB_main.json')
        self.RENDER_DB_PATH       = PLUGIN_DATA_DIR.pjoin('MAME_DB_render.json')
        self.ROMS_DB_PATH         = PLUGIN_DATA_DIR.pjoin('MAME_DB_roms.json')
        self.MAIN_PCLONE_DIC_PATH = PLUGIN_DATA_DIR.pjoin('MAME_DB_pclone_dic.json')

        # >> ROM set databases
        self.ROM_AUDIT_DB_PATH                = PLUGIN_DATA_DIR.pjoin('ROM_Audit_DB.json')
        self.ROM_SET_MACHINE_ARCHIVES_DB_PATH = PLUGIN_DATA_DIR.pjoin('ROM_Set_machine_archives.json')
        self.ROM_SET_ROM_ARCHIVES_DB_PATH     = PLUGIN_DATA_DIR.pjoin('ROM_Set_ROM_archives.json')
        self.ROM_SET_CHD_ARCHIVES_DB_PATH     = PLUGIN_DATA_DIR.pjoin('ROM_Set_CHD_archives.json')
        self.ROM_SHA1_HASH_DB_PATH            = PLUGIN_DATA_DIR.pjoin('ROM_SHA1_hashes.json')

        # >> DAT indices and databases.
        self.HISTORY_IDX_PATH  = PLUGIN_DATA_DIR.pjoin('DAT_History_index.json')
        self.HISTORY_DB_PATH   = PLUGIN_DATA_DIR.pjoin('DAT_History_DB.json')
        self.MAMEINFO_IDX_PATH = PLUGIN_DATA_DIR.pjoin('DAT_MAMEInfo_index.json')
        self.MAMEINFO_DB_PATH  = PLUGIN_DATA_DIR.pjoin('DAT_MAMEInfo_DB.json')
        self.GAMEINIT_IDX_PATH = PLUGIN_DATA_DIR.pjoin('DAT_GameInit_index.json')
        self.GAMEINIT_DB_PATH  = PLUGIN_DATA_DIR.pjoin('DAT_GameInit_DB.json')
        self.COMMAND_IDX_PATH  = PLUGIN_DATA_DIR.pjoin('DAT_Command_index.json')
        self.COMMAND_DB_PATH   = PLUGIN_DATA_DIR.pjoin('DAT_Command_DB.json')

        # >> Most played and Recently played
        self.MAME_MOST_PLAYED_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('most_played_MAME.json')
        self.MAME_RECENT_PLAYED_FILE_PATH = PLUGIN_DATA_DIR.pjoin('recently_played_MAME.json')
        self.SL_MOST_PLAYED_FILE_PATH     = PLUGIN_DATA_DIR.pjoin('most_played_SL.json')
        self.SL_RECENT_PLAYED_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('recently_played_SL.json')

        # >> Disabled. Now there are global properties for this.
        # self.MAIN_PROPERTIES_PATH = PLUGIN_DATA_DIR.pjoin('MAME_properties.json')

        # >> ROM cache
        self.CACHE_DIR        = PLUGIN_DATA_DIR.pjoin('cache')
        self.CACHE_INDEX_PATH = PLUGIN_DATA_DIR.pjoin('MAME_cache_index.json')

        # >> Catalogs
        self.CATALOG_DIR                          = PLUGIN_DATA_DIR.pjoin('catalogs')
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
        self.CATALOG_NPLAYERS_PARENT_PATH         = self.CATALOG_DIR.pjoin('catalog_nplayers_parents.json')
        self.CATALOG_NPLAYERS_ALL_PATH            = self.CATALOG_DIR.pjoin('catalog_nplayers_all.json')
        self.CATALOG_BESTGAMES_PARENT_PATH        = self.CATALOG_DIR.pjoin('catalog_bestgames_parents.json')
        self.CATALOG_BESTGAMES_ALL_PATH           = self.CATALOG_DIR.pjoin('catalog_bestgames_all.json')
        self.CATALOG_SERIES_PARENT_PATH           = self.CATALOG_DIR.pjoin('catalog_series_parents.json')
        self.CATALOG_SERIES_ALL_PATH              = self.CATALOG_DIR.pjoin('catalog_series_all.json')
        self.CATALOG_MANUFACTURER_PARENT_PATH     = self.CATALOG_DIR.pjoin('catalog_manufacturer_parents.json')
        self.CATALOG_MANUFACTURER_ALL_PATH        = self.CATALOG_DIR.pjoin('catalog_manufacturer_all.json')
        self.CATALOG_YEAR_PARENT_PATH             = self.CATALOG_DIR.pjoin('catalog_year_parents.json')
        self.CATALOG_YEAR_ALL_PATH                = self.CATALOG_DIR.pjoin('catalog_year_all.json')
        self.CATALOG_DRIVER_PARENT_PATH           = self.CATALOG_DIR.pjoin('catalog_driver_parents.json')
        self.CATALOG_DRIVER_ALL_PATH              = self.CATALOG_DIR.pjoin('catalog_driver_all.json')
        self.CATALOG_CONTROL_EXPANDED_PARENT_PATH = self.CATALOG_DIR.pjoin('catalog_control_expanded_parents.json')
        self.CATALOG_CONTROL_EXPANDED_ALL_PATH    = self.CATALOG_DIR.pjoin('catalog_control_expanded_all.json')
        self.CATALOG_CONTROL_COMPACT_PARENT_PATH  = self.CATALOG_DIR.pjoin('catalog_control_compact_parents.json')
        self.CATALOG_CONTROL_COMPACT_ALL_PATH     = self.CATALOG_DIR.pjoin('catalog_control_compact_all.json')
        self.CATALOG_DISPLAY_TAG_PARENT_PATH      = self.CATALOG_DIR.pjoin('catalog_display_tag_parents.json')
        self.CATALOG_DISPLAY_TAG_ALL_PATH         = self.CATALOG_DIR.pjoin('catalog_display_tag_all.json')
        self.CATALOG_DISPLAY_TYPE_PARENT_PATH     = self.CATALOG_DIR.pjoin('catalog_display_type_parents.json')
        self.CATALOG_DISPLAY_TYPE_ALL_PATH        = self.CATALOG_DIR.pjoin('catalog_display_type_all.json')
        self.CATALOG_DISPLAY_ROTATE_PARENT_PATH   = self.CATALOG_DIR.pjoin('catalog_display_rotate_parents.json')
        self.CATALOG_DISPLAY_ROTATE_ALL_PATH      = self.CATALOG_DIR.pjoin('catalog_display_rotate_all.json')
        self.CATALOG_DEVICE_EXPANDED_PARENT_PATH  = self.CATALOG_DIR.pjoin('catalog_device_expanded_parents.json')
        self.CATALOG_DEVICE_EXPANDED_ALL_PATH     = self.CATALOG_DIR.pjoin('catalog_device_expanded_all.json')
        self.CATALOG_DEVICE_COMPACT_PARENT_PATH   = self.CATALOG_DIR.pjoin('catalog_device_compact_parents.json')
        self.CATALOG_DEVICE_COMPACT_ALL_PATH      = self.CATALOG_DIR.pjoin('catalog_device_compact_all.json')
        self.CATALOG_SL_PARENT_PATH               = self.CATALOG_DIR.pjoin('catalog_SL_parents.json')
        self.CATALOG_SL_ALL_PATH                  = self.CATALOG_DIR.pjoin('catalog_SL_all.json')
        self.CATALOG_SHORTNAME_PARENT_PATH        = self.CATALOG_DIR.pjoin('catalog_shortname_parents.json')
        self.CATALOG_SHORTNAME_ALL_PATH           = self.CATALOG_DIR.pjoin('catalog_shortname_all.json')
        self.CATALOG_LONGNAME_PARENT_PATH         = self.CATALOG_DIR.pjoin('catalog_longname_parents.json')
        self.CATALOG_LONGNAME_ALL_PATH            = self.CATALOG_DIR.pjoin('catalog_longname_all.json')

        # >> Distributed hashed database
        self.MAIN_DB_HASH_DIR      = PLUGIN_DATA_DIR.pjoin('hash')
        self.ROMS_DB_HASH_DIR      = PLUGIN_DATA_DIR.pjoin('hash_ROM')
        self.ROM_AUDIT_DB_HASH_DIR = PLUGIN_DATA_DIR.pjoin('hash_ROM_Audit')

        # >> MAME custom filters
        self.FILTERS_DB_DIR     = PLUGIN_DATA_DIR.pjoin('filters')
        self.FILTERS_INDEX_PATH = PLUGIN_DATA_DIR.pjoin('Filter_index.json')

        # >> Software Lists
        self.SL_DB_DIR             = PLUGIN_DATA_DIR.pjoin('SoftwareLists')
        self.SL_NAMES_PATH         = PLUGIN_DATA_DIR.pjoin('SoftwareLists_names.json')
        self.SL_INDEX_PATH         = PLUGIN_DATA_DIR.pjoin('SoftwareLists_index.json')
        self.SL_MACHINES_PATH      = PLUGIN_DATA_DIR.pjoin('SoftwareLists_machines.json')
        self.SL_PCLONE_DIC_PATH    = PLUGIN_DATA_DIR.pjoin('SoftwareLists_pclone_dic.json')
        # >> Disabled. There are global properties
        # self.SL_MACHINES_PROP_PATH = PLUGIN_DATA_DIR.pjoin('SoftwareLists_properties.json')

        # >> Favourites
        self.FAV_MACHINES_PATH = PLUGIN_DATA_DIR.pjoin('Favourite_Machines.json')
        self.FAV_SL_ROMS_PATH  = PLUGIN_DATA_DIR.pjoin('Favourite_SL_ROMs.json')

        # >> ROM/CHD scanner reports. These reports show missing ROM/CHDs only.
        self.REPORTS_DIR                             = PLUGIN_DATA_DIR.pjoin('reports')
        self.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH = self.REPORTS_DIR.pjoin('Scanner_MAME_machine_archives_full.txt')
        self.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH = self.REPORTS_DIR.pjoin('Scanner_MAME_machine_archives_have.txt')
        self.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH = self.REPORTS_DIR.pjoin('Scanner_MAME_machine_archives_miss.txt')

        self.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH     = self.REPORTS_DIR.pjoin('Scanner_MAME_ROM_list_miss.txt')
        self.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH     = self.REPORTS_DIR.pjoin('Scanner_MAME_CHD_list_miss.txt')

        self.REPORT_MAME_SCAN_SAMP_FULL_PATH         = self.REPORTS_DIR.pjoin('Scanner_Samples_full.txt')
        self.REPORT_MAME_SCAN_SAMP_HAVE_PATH         = self.REPORTS_DIR.pjoin('Scanner_Samples_have.txt')
        self.REPORT_MAME_SCAN_SAMP_MISS_PATH         = self.REPORTS_DIR.pjoin('Scanner_Samples_miss.txt')

        self.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH   = self.REPORTS_DIR.pjoin('Scanner_SL_item_archives_full.txt')
        self.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH   = self.REPORTS_DIR.pjoin('Scanner_SL_item_archives_have.txt')
        self.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH   = self.REPORTS_DIR.pjoin('Scanner_SL_item_archives_miss.txt')

        self.REPORT_SL_SCAN_ROM_LIST_MISS_PATH       = self.REPORTS_DIR.pjoin('Scanner_SL_ROM_list_miss.txt')
        self.REPORT_SL_SCAN_CHD_LIST_MISS_PATH       = self.REPORTS_DIR.pjoin('Scanner_SL_CHD_list_miss.txt')

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
PATHS = AML_Paths()
g_settings = {}
g_base_url = ''
g_addon_handle = 0
g_content_type = ''
g_time_str = unicode(datetime.now())

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
    _get_settings()
    set_log_level(g_settings['log_level'])

    # --- Some debug stuff for development ---
    log_debug('---------- Called AML Main::run_plugin() constructor ----------')
    log_debug('sys.platform {0}'.format(sys.platform))
    log_debug('Python version ' + sys.version.replace('\n', ''))
    log_debug('__addon_version__ {0}'.format(__addon_version__))
    for i in range(len(addon_argv)): log_debug('addon_argv[{0}] = "{1}"'.format(i, addon_argv[i]))
    # >> Timestamp to see if this submodule is reinterpreted or not.
    log_debug('submodule global timestamp {0}'.format(g_time_str))

    # --- Addon data paths creation ---
    if not PLUGIN_DATA_DIR.exists(): PLUGIN_DATA_DIR.makedirs()
    if not PATHS.CACHE_DIR.exists(): PATHS.CACHE_DIR.makedirs()
    if not PATHS.CATALOG_DIR.exists(): PATHS.CATALOG_DIR.makedirs()
    if not PATHS.MAIN_DB_HASH_DIR.exists(): PATHS.MAIN_DB_HASH_DIR.makedirs()
    if not PATHS.FILTERS_DB_DIR.exists(): PATHS.FILTERS_DB_DIR.makedirs()
    if not PATHS.SL_DB_DIR.exists(): PATHS.SL_DB_DIR.makedirs()
    if not PATHS.REPORTS_DIR.exists(): PATHS.REPORTS_DIR.makedirs()

    # --- If control_dic does not exists create an empty one ---
    # >> control_dic will be used for database built checks, etc.
    if not PATHS.MAIN_CONTROL_PATH.exists(): fs_create_empty_control_dic(PATHS)

    # --- Process URL ---
    g_base_url = addon_argv[0]
    g_addon_handle = int(addon_argv[1])
    args = urlparse.parse_qs(addon_argv[2][1:])
    # log_debug('args = {0}'.format(args))
    # Interestingly, if plugin is called as type executable then args is empty.
    # However, if plugin is called as type video then Kodi adds the following
    # even for the first call: 'content_type': ['video']
    g_content_type = args['content_type'] if 'content_type' in args else None
    log_debug('content_type = {0}'.format(g_content_type))

    # --- URL routing -------------------------------------------------------------------------
    args_size = len(args)
    if args_size == 0:
        _render_root_list()
        log_debug('Advanced MAME Launcher exit (addon root)')
        return

    elif 'catalog' in args and not 'command' in args:
        catalog_name = args['catalog'][0]
        # --- Software list is a special case ---
        if catalog_name == 'SL' or catalog_name == 'SL_ROM' or \
           catalog_name == 'SL_CHD' or catalog_name == 'SL_ROM_CHD':
            SL_name     = args['category'][0] if 'category' in args else ''
            parent_name = args['parent'][0] if 'parent' in args else ''
            if SL_name and parent_name:
                _render_SL_pclone_set(SL_name, parent_name)
            elif SL_name and not parent_name:
                _render_SL_ROMs(SL_name)
            else:
                _render_SL_list(catalog_name)
        # --- Custom filters ---
        elif catalog_name == 'Custom':
            filter_name = args['category'][0] if 'category' in args else ''
            parent_name = args['parent'][0] if 'parent' in args else ''
            if filter_name and parent_name:
                _render_custom_filter_machines_clones(filter_name, parent_name)
            else:
                _render_custom_filter_machines_parents(filter_name)
        # --- DAT browsing ---
        elif catalog_name == 'History' or catalog_name == 'MAMEINFO' or \
             catalog_name == 'Gameinit' or catalog_name == 'Command':
            category_name = args['category'][0] if 'category' in args else ''
            machine_name = args['machine'][0] if 'machine' in args else ''
            if category_name and machine_name:
                _render_DAT_machine_info(catalog_name, category_name, machine_name)
            elif category_name and not machine_name:
                _render_DAT_category(catalog_name, category_name)
            else:
                _render_DAT_list(catalog_name)
        else:
            category_name = args['category'][0] if 'category' in args else ''
            parent_name   = args['parent'][0] if 'parent' in args else ''
            if category_name and parent_name:
                _render_catalog_clone_list(catalog_name, category_name, parent_name)
            elif category_name and not parent_name:
                _render_catalog_parent_list(catalog_name, category_name)
            else:
                _render_catalog_list(catalog_name)

    elif 'command' in args:
        command = args['command'][0]

        # >> Commands used by skins to render items of the addon root menu.
        if   command == 'SKIN_SHOW_FAV_SLOTS':       _render_skin_fav_slots()
        elif command == 'SKIN_SHOW_MAIN_FILTERS':    _render_skin_main_filters()
        elif command == 'SKIN_SHOW_BINARY_FILTERS':  _render_skin_binary_filters()
        elif command == 'SKIN_SHOW_CATALOG_FILTERS': _render_skin_catalog_filters()
        elif command == 'SKIN_SHOW_DAT_SLOTS':       _render_skin_dat_slots()
        elif command == 'SKIN_SHOW_SL_FILTERS':      _render_skin_SL_filters()

        # >> Auxiliar commands from parent machine context menu
        # >> Not sure if this will cause problems with the concurrent protected code once it's
        #    implemented.
        elif command == 'EXEC_SHOW_MAME_CLONES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            machine_name  = args['parent'][0] if 'parent' in args else ''
            url = _misc_url_3_arg('catalog', catalog_name, 'category', category_name, 'parent', machine_name)
            xbmc.executebuiltin('Container.Update({0})'.format(url))

        elif command == 'EXEC_SHOW_SL_CLONES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            machine_name  = args['parent'][0] if 'parent' in args else ''
            url = _misc_url_3_arg('catalog', 'SL', 'category', category_name, 'parent', machine_name)
            xbmc.executebuiltin('Container.Update({0})'.format(url))

        # >> If location is not present in the URL default to standard.
        elif command == 'LAUNCH':
            machine  = args['machine'][0]
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            log_info('Launching MAME machine "{0}" in "{1}"'.format(machine, location))
            _run_machine(machine, location)
        elif command == 'LAUNCH_SL':
            SL_name  = args['SL'][0]
            ROM_name = args['ROM'][0]
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            log_info('Launching SL machine "{0}" (ROM "{1}")'.format(SL_name, ROM_name))
            _run_SL_machine(SL_name, ROM_name, location)

        elif command == 'SETUP_PLUGIN':
            _command_context_setup_plugin()

        #
        # Not used at the moment.
        # Instead of per-catalog, per-category display mode there are global settings.
        #
        elif command == 'DISPLAY_SETTINGS_MAME':
            catalog_name = args['catalog'][0]
            category_name = args['category'][0] if 'category' in args else ''
            _command_context_display_settings(catalog_name, category_name)
        elif command == 'DISPLAY_SETTINGS_SL':
            _command_context_display_settings_SL(args['category'][0])
        elif command == 'VIEW_DAT':
            machine  = args['machine'][0]  if 'machine'  in args else ''
            SL       = args['SL'][0]       if 'SL'       in args else ''
            ROM      = args['ROM'][0]      if 'ROM'      in args else ''
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            _command_context_view_DAT(machine, SL, ROM, location)
        elif command == 'VIEW':
            machine  = args['machine'][0]  if 'machine'  in args else ''
            SL       = args['SL'][0]       if 'SL'       in args else ''
            ROM      = args['ROM'][0]      if 'ROM'      in args else ''
            location = args['location'][0] if 'location' in args else LOCATION_STANDARD
            _command_context_view(machine, SL, ROM, location)
        elif command == 'UTILITIES':
            catalog_name  = args['catalog'][0] if 'catalog' in args else ''
            category_name = args['category'][0] if 'category' in args else ''
            _command_context_utilities(catalog_name, category_name)

        # >> MAME Favourites
        elif command == 'ADD_MAME_FAV':
            _command_context_add_mame_fav(args['machine'][0])
        elif command == 'MANAGE_MAME_FAV':
            machine = args['machine'][0] if 'machine' in args else ''
            _command_context_manage_mame_fav(machine)
        elif command == 'SHOW_MAME_FAVS':
            _command_show_mame_fav()

        # >> SL Favourites
        elif command == 'ADD_SL_FAV':
            _command_context_add_sl_fav(args['SL'][0], args['ROM'][0])
        elif command == 'MANAGE_SL_FAV':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            _command_context_manage_sl_fav(SL_name, ROM_name)
        elif command == 'SHOW_SL_FAVS':
            _command_show_sl_fav()

        # >> Most and Recently played
        elif command == 'SHOW_MAME_MOST_PLAYED':
            _command_show_mame_most_played()
        elif command == 'MANAGE_MAME_MOST_PLAYED':
            m_name = args['machine'][0] if 'machine' in args else ''
            _command_context_manage_mame_most_played(m_name)

        elif command == 'SHOW_MAME_RECENTLY_PLAYED':
            _command_show_mame_recently_played()
        elif command == 'MANAGE_MAME_RECENT_PLAYED':
            m_name = args['machine'][0] if 'machine' in args else ''
            _command_context_manage_mame_recent_played(m_name)

        elif command == 'SHOW_SL_MOST_PLAYED':
            _command_show_SL_most_played()
        elif command == 'MANAGE_SL_MOST_PLAYED':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            _command_context_manage_SL_most_played(SL_name, ROM_name)

        elif command == 'SHOW_SL_RECENTLY_PLAYED':
            _command_show_SL_recently_played()
        elif command == 'MANAGE_SL_RECENT_PLAYED':
            SL_name = args['SL'][0] if 'SL' in args else ''
            ROM_name = args['ROM'][0] if 'ROM' in args else ''
            _command_context_manage_SL_recent_played(SL_name, ROM_name)

        # >> Custom filters
        elif command == 'SHOW_CUSTOM_FILTERS':
            _command_show_custom_filters()
        elif command == 'SETUP_CUSTOM_FILTERS':
            _command_context_setup_custom_filters()

        # >> Check and update all MAME and SL Favourite objects
        elif command == 'CHECK_ALL_OBJECTS':
            _command_check_all_Favourite_objects()

        # >> Check AML config
        elif command == 'CHECK_CONFIG':
            _command_check_AML_configuration()

        # >> Utilities to check CRC hash collisions.
        elif command == 'CHECK_MAME_COLLISIONS':
            _command_check_MAME_CRC_collisions()
        elif command == 'CHECK_SL_COLLISIONS':
            _command_check_SL_CRC_collisions()

        else:
            u = 'Unknown command "{0}"'.format(command)
            log_error(u)
            kodi_dialog_OK(u)
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    else:
        u = 'Error in URL routing'
        log_error(u)
        kodi_dialog_OK(u)
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

    # --- So Long, and Thanks for All the Fish ---
    log_debug('Advanced MAME Launcher exit')

#
# Get Addon Settings
#
def _get_settings():
    global g_settings
    global g_mame_icon
    global g_mame_fanart
    global g_SL_icon
    global g_SL_fanart
    o = __addon__

    # --- Paths ---
    g_settings['mame_prog']    = o.getSetting('mame_prog').decode('utf-8')

    g_settings['rom_path']     = o.getSetting('rom_path').decode('utf-8')
    g_settings['assets_path']  = o.getSetting('assets_path').decode('utf-8')
    g_settings['chd_path']     = o.getSetting('chd_path').decode('utf-8')
    g_settings['samples_path'] = o.getSetting('samples_path').decode('utf-8')
    g_settings['SL_hash_path'] = o.getSetting('SL_hash_path').decode('utf-8')
    g_settings['SL_rom_path']  = o.getSetting('SL_rom_path').decode('utf-8')
    g_settings['SL_chd_path']  = o.getSetting('SL_chd_path').decode('utf-8')

    # --- DAT paths (order alpahbetically) ---
    g_settings['bestgames_path'] = o.getSetting('bestgames_path').decode('utf-8')
    g_settings['catlist_path']   = o.getSetting('catlist_path').decode('utf-8')
    g_settings['catver_path']    = o.getSetting('catver_path').decode('utf-8')
    g_settings['command_path']   = o.getSetting('command_path').decode('utf-8')
    g_settings['gameinit_path']  = o.getSetting('gameinit_path').decode('utf-8')
    g_settings['genre_path']     = o.getSetting('genre_path').decode('utf-8')
    g_settings['history_path']   = o.getSetting('history_path').decode('utf-8')
    g_settings['mameinfo_path']  = o.getSetting('mameinfo_path').decode('utf-8')
    g_settings['mature_path']    = o.getSetting('mature_path').decode('utf-8')
    g_settings['nplayers_path']  = o.getSetting('nplayers_path').decode('utf-8')
    g_settings['series_path']    = o.getSetting('series_path').decode('utf-8')

    # --- ROM sets ---
    g_settings['mame_rom_set'] = int(o.getSetting('mame_rom_set'))
    g_settings['mame_chd_set'] = int(o.getSetting('mame_chd_set'))
    g_settings['SL_rom_set']   = int(o.getSetting('SL_rom_set'))
    g_settings['SL_chd_set']   = int(o.getSetting('SL_chd_set'))
    g_settings['filter_XML']   = o.getSetting('filter_XML').decode('utf-8')

    # --- Display ---
    g_settings['display_launcher_notify'] = True if o.getSetting('display_launcher_notify') == 'true' else False
    g_settings['mame_view_mode']          = int(o.getSetting('mame_view_mode'))
    g_settings['sl_view_mode']            = int(o.getSetting('sl_view_mode'))
    g_settings['display_hide_Mature']     = True if o.getSetting('display_hide_Mature') == 'true' else False
    g_settings['display_hide_BIOS']       = True if o.getSetting('display_hide_BIOS') == 'true' else False
    g_settings['display_hide_nonworking'] = True if o.getSetting('display_hide_nonworking') == 'true' else False
    g_settings['display_hide_imperfect']  = True if o.getSetting('display_hide_imperfect') == 'true' else False
    g_settings['display_rom_available']   = True if o.getSetting('display_rom_available') == 'true' else False
    g_settings['display_chd_available']   = True if o.getSetting('display_chd_available') == 'true' else False

    g_settings['display_main_filters']    = True if o.getSetting('display_main_filters') == 'true' else False
    g_settings['display_binary_filters']  = True if o.getSetting('display_binary_filters') == 'true' else False
    g_settings['display_catalog_filters'] = True if o.getSetting('display_catalog_filters') == 'true' else False
    g_settings['display_DAT_browser']     = True if o.getSetting('display_DAT_browser') == 'true' else False
    g_settings['display_SL_browser']      = True if o.getSetting('display_SL_browser') == 'true' else False
    g_settings['display_MAME_favs']       = True if o.getSetting('display_MAME_favs') == 'true' else False
    g_settings['display_SL_favs']         = True if o.getSetting('display_SL_favs') == 'true' else False
    g_settings['display_custom_filters']  = True if o.getSetting('display_custom_filters') == 'true' else False
    g_settings['display_MAME_most']       = True if o.getSetting('display_MAME_most') == 'true' else False
    g_settings['display_MAME_recent']     = True if o.getSetting('display_MAME_recent') == 'true' else False
    g_settings['display_SL_most']         = True if o.getSetting('display_SL_most') == 'true' else False
    g_settings['display_SL_recent']       = True if o.getSetting('display_SL_recent') == 'true' else False

    # --- Display ---
    g_settings['artwork_mame_icon']     = int(o.getSetting('artwork_mame_icon'))
    g_settings['artwork_mame_fanart']   = int(o.getSetting('artwork_mame_fanart'))
    g_settings['artwork_SL_icon']       = int(o.getSetting('artwork_SL_icon'))
    g_settings['artwork_SL_fanart']     = int(o.getSetting('artwork_SL_fanart'))
    g_settings['display_hide_trailers'] = True if o.getSetting('display_hide_trailers') == 'true' else False

    # --- Utilities ---

    # --- Advanced ---
    g_settings['media_state_action']              = int(o.getSetting('media_state_action'))
    g_settings['delay_tempo']                     = int(round(float(o.getSetting('delay_tempo'))))
    g_settings['suspend_audio_engine']            = True if o.getSetting('suspend_audio_engine') == 'true' else False
    g_settings['toggle_window']                   = True if o.getSetting('toggle_window') == 'true' else False
    g_settings['log_level']                       = int(o.getSetting('log_level'))
    g_settings['debug_enable_MAME_machine_cache'] = True if o.getSetting('debug_enable_MAME_machine_cache') == 'true' else False
    g_settings['debug_enable_MAME_asset_cache']   = True if o.getSetting('debug_enable_MAME_asset_cache') == 'true' else False
    g_settings['debug_MAME_item_data']            = True if o.getSetting('debug_MAME_item_data') == 'true' else False
    g_settings['debug_MAME_ROM_DB_data']          = True if o.getSetting('debug_MAME_ROM_DB_data') == 'true' else False
    g_settings['debug_MAME_Audit_DB_data']        = True if o.getSetting('debug_MAME_Audit_DB_data') == 'true' else False
    g_settings['debug_SL_item_data']              = True if o.getSetting('debug_SL_item_data') == 'true' else False
    g_settings['debug_SL_ROM_DB_data']            = True if o.getSetting('debug_SL_ROM_DB_data') == 'true' else False
    g_settings['debug_SL_Audit_DB_data']          = True if o.getSetting('debug_SL_Audit_DB_data') == 'true' else False

    # --- Transform settings data ---
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
def _render_root_list():
    mame_view_mode = g_settings['mame_view_mode']

    # ----- Machine count -----
    cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())

    # >> Do not crash if cache_index_dic is corrupted or has missing fields (may happen in
    # >> upgrades). This function must never crash because the user must have always access to
    # >> the setup menu.
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
        num_cat_NPlayers = len(cache_index_dic['NPlayers'])
        num_cat_Bestgames = len(cache_index_dic['Bestgames'])
        num_cat_Series = len(cache_index_dic['Series'])
        num_cat_Controls_Expanded = len(cache_index_dic['Controls_Expanded'])
        num_cat_Controls_Compact = len(cache_index_dic['Controls_Compact'])
        num_cat_Devices_Expanded = len(cache_index_dic['Devices_Expanded'])
        num_cat_Devices_Compact = len(cache_index_dic['Devices_Compact'])
        num_cat_Display_Rotate = len(cache_index_dic['Display_Rotate'])
        num_cat_Display_Type = len(cache_index_dic['Display_Type'])
        num_cat_Driver = len(cache_index_dic['Driver'])
        num_cat_Manufacturer = len(cache_index_dic['Manufacturer'])
        num_cat_ShortName = len(cache_index_dic['ShortName'])
        num_cat_LongName = len(cache_index_dic['LongName'])
        num_cat_BySL = len(cache_index_dic['BySL'])
        num_cat_Year = len(cache_index_dic['Year'])

        counters_available = True
        log_debug('_render_root_list() counters_available = True')

    except KeyError as E:
        counters_available = False
        log_debug('_render_root_list() counters_available = False')

    # >> Main filter
    machines_n_str = 'Machines with coin slot (Normal)'
    machines_u_str = 'Machines with coin slot (Unusual)'
    nocoin_str     = 'Machines with no coin slot'
    mecha_str      = 'Mechanical machines'
    dead_str       = 'Dead machines'
    devices_str    = 'Device machines'

    # >> Binary filters
    bios_str       = 'Machines [BIOS]'
    chd_str        = 'Machines [with CHDs]'
    samples_str    = 'Machines [with Samples]'
    softlists_str  = 'Machines [with Software Lists]'

    # >> Cataloged filters (optional)
    catver_str   = 'Machines by Category (Catver)'
    catlist_str  = 'Machines by Category (Catlist)'
    genre_str    = 'Machines by Category (Genre)'
    NPLayers_str = 'Machines by Number of players'
    score_str    = 'Machines by Score'
    series_str   = 'Machines by Series'

    # >> Cataloged filters (always there)
    # NOTE: use the same names as MAME executable
    # -listdevices   list available devices                  XML tag <device_ref>
    # -listslots     list available slots and slot devices   XML tag <slot>
    # -listmedia     list available media for the system     XML tag <device>
    ctype_expanded_str  = 'Machines by Controls (Expanded)'
    ctype_compact_str   = 'Machines by Controls (Compact)'
    device_expanded_str = 'Machines by Device (Expanded)'
    device_compact_str  = 'Machines by Device (Compact)'
    drotation_str       = 'Machines by Display Rotation'
    dtype_str           = 'Machines by Display Type'
    driver_str          = 'Machines by Driver'
    manufacturer_str    = 'Machines by Manufacturer'
    shortname_str       = 'Machines by MAME short name'
    longname_str        = 'Machines by MAME long name'
    SL_str              = 'Machines by Software List'
    year_str            = 'Machines by Year'

    if counters_available and mame_view_mode == VIEW_MODE_FLAT:
        a = ' [COLOR orange]({0} machines)[/COLOR]'
        machines_n_str += a.format(num_m_Main_Normal)
        machines_u_str += a.format(num_m_Main_Unusual)
        nocoin_str     += a.format(num_m_Main_NoCoin)
        mecha_str      += a.format(num_m_Main_Mechanical)
        dead_str       += a.format(num_m_Main_Dead)
        devices_str    += a.format(num_m_Main_Devices)
        bios_str       += a.format(num_m_Binary_BIOS)
        chd_str        += a.format(num_m_Binary_CHD)
        samples_str    += a.format(num_m_Binary_Samples)
        softlists_str  += a.format(num_m_Binary_SoftwareLists)
    elif counters_available and mame_view_mode == VIEW_MODE_PCLONE:
        a = ' [COLOR orange]({0} parents)[/COLOR]'
        machines_n_str += a.format(num_p_Main_Normal)
        machines_u_str += a.format(num_p_Main_Unusual)
        nocoin_str     += a.format(num_p_Main_NoCoin)
        mecha_str      += a.format(num_p_Main_Mechanical)
        dead_str       += a.format(num_p_Main_Dead)
        devices_str    += a.format(num_p_Main_Devices)
        bios_str       += a.format(num_p_Binary_BIOS)
        chd_str        += a.format(num_p_Binary_CHD)
        samples_str    += a.format(num_p_Binary_Samples)
        softlists_str  += a.format(num_p_Binary_SoftwareLists)

    if counters_available:
        a = ' [COLOR gold]({0} items)[/COLOR]'
        # >> Optional
        catver_str          += a.format(num_cat_Catver)
        catlist_str         += a.format(num_cat_Catlist)
        genre_str           += a.format(num_cat_Genre)
        NPLayers_str        += a.format(num_cat_NPlayers)
        score_str           += a.format(num_cat_Bestgames)
        series_str          += a.format(num_cat_Series)
        # >> Always there
        ctype_expanded_str  += a.format(num_cat_Controls_Expanded)
        ctype_compact_str   += a.format(num_cat_Controls_Compact)
        device_expanded_str += a.format(num_cat_Devices_Expanded)
        device_compact_str  += a.format(num_cat_Devices_Compact)
        drotation_str       += a.format(num_cat_Display_Rotate)
        dtype_str           += a.format(num_cat_Display_Type)
        driver_str          += a.format(num_cat_Driver)
        manufacturer_str    += a.format(num_cat_Manufacturer)
        shortname_str       += a.format(num_cat_ShortName)
        longname_str        += a.format(num_cat_LongName)
        SL_str              += a.format(num_cat_BySL)
        year_str            += a.format(num_cat_Year)

    # >> If everything deactivated render the main filters so user has access to the context menu.
    big_OR = g_settings['display_main_filters'] or g_settings['display_binary_filters'] or \
             g_settings['display_catalog_filters'] or g_settings['display_DAT_browser'] or \
             g_settings['display_SL_browser'] or g_settings['display_MAME_favs'] or \
             g_settings['display_SL_favs'] or g_settings['display_custom_filters']
    if not big_OR:
        g_settings['display_main_filters'] = True

    # >> Main filters (Virtual catalog 'Main')
    if g_settings['display_main_filters']:
        _render_root_list_row_catalog(machines_n_str, 'Main', 'Normal')
        _render_root_list_row_catalog(machines_u_str, 'Main', 'Unusual')
        _render_root_list_row_catalog(nocoin_str, 'Main', 'NoCoin')
        _render_root_list_row_catalog(mecha_str, 'Main', 'Mechanical')
        _render_root_list_row_catalog(dead_str, 'Main', 'Dead')
        _render_root_list_row_catalog(devices_str, 'Main', 'Devices')

    # >> Binary filters (Virtual catalog 'Binary')
    if g_settings['display_binary_filters']:
        _render_root_list_row_catalog(bios_str, 'Binary', 'BIOS')
        _render_root_list_row_catalog(chd_str, 'Binary', 'CHD')
        _render_root_list_row_catalog(samples_str, 'Binary', 'Samples')
        _render_root_list_row_catalog(softlists_str, 'Binary', 'SoftwareLists')

    if g_settings['display_catalog_filters']:
        # >> Optional cataloged filters (depend on a INI file)
        _render_root_list_row_standard(catver_str, _misc_url_1_arg('catalog', 'Catver'))
        _render_root_list_row_standard(catlist_str, _misc_url_1_arg('catalog', 'Catlist'))
        _render_root_list_row_standard(genre_str, _misc_url_1_arg('catalog', 'Genre'))
        _render_root_list_row_standard(NPLayers_str, _misc_url_1_arg('catalog', 'NPlayers'))
        _render_root_list_row_standard(score_str, _misc_url_1_arg('catalog', 'Bestgames'))
        _render_root_list_row_standard(series_str, _misc_url_1_arg('catalog', 'Series'))
        # >> Cataloged filters (always there)
        _render_root_list_row_standard(ctype_expanded_str, _misc_url_1_arg('catalog', 'Controls_Expanded'))
        _render_root_list_row_standard(ctype_compact_str, _misc_url_1_arg('catalog', 'Controls_Compact'))
        _render_root_list_row_standard(device_expanded_str, _misc_url_1_arg('catalog', 'Devices_Expanded'))
        _render_root_list_row_standard(device_compact_str, _misc_url_1_arg('catalog', 'Devices_Compact'))
        _render_root_list_row_standard(drotation_str, _misc_url_1_arg('catalog', 'Display_Rotate'))
        _render_root_list_row_standard(dtype_str, _misc_url_1_arg('catalog', 'Display_Type'))
        _render_root_list_row_standard(driver_str, _misc_url_1_arg('catalog', 'Driver'))
        _render_root_list_row_standard(manufacturer_str, _misc_url_1_arg('catalog', 'Manufacturer'))
        _render_root_list_row_standard(shortname_str, _misc_url_1_arg('catalog', 'ShortName'))
        _render_root_list_row_standard(longname_str, _misc_url_1_arg('catalog', 'LongName'))
        _render_root_list_row_standard(SL_str, _misc_url_1_arg('catalog', 'BySL'))
        _render_root_list_row_standard(year_str, _misc_url_1_arg('catalog', 'Year'))

    # >> history.dat, mameinfo.dat, gameinit.dat, command.dat
    if g_settings['display_DAT_browser']:
        _render_root_list_row_standard('History DAT', _misc_url_1_arg('catalog', 'History'))
        _render_root_list_row_standard('MAMEINFO DAT', _misc_url_1_arg('catalog', 'MAMEINFO'))
        _render_root_list_row_standard('Gameinit DAT', _misc_url_1_arg('catalog', 'Gameinit'))
        _render_root_list_row_standard('Command DAT', _misc_url_1_arg('catalog', 'Command'))

    # >> Software lists
    if g_settings['display_SL_browser']:
        _render_root_list_row_standard('Software Lists (with ROMs)',
                                       _misc_url_1_arg('catalog', 'SL_ROM'))
        _render_root_list_row_standard('Software Lists (with ROMs and CHDs)',
                                       _misc_url_1_arg('catalog', 'SL_ROM_CHD'))
        _render_root_list_row_standard('Software Lists (with CHDs)',
                                       _misc_url_1_arg('catalog', 'SL_CHD'))

    # >> Special launchers
    if g_settings['display_MAME_favs']:
        CM_title = 'Manage Favourites'
        CM_URL = _misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_FAV')
        _render_root_list_row_custom_CM('<Favourite MAME machines>', 
                                        _misc_url_1_arg('command', 'SHOW_MAME_FAVS'),
                                        CM_title, CM_URL)
    if g_settings['display_SL_favs']:
        CM_title = 'Manage SL Favourites'
        CM_URL = _misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_FAV')
        _render_root_list_row_custom_CM('<Favourite Software Lists ROMs>',
                                        _misc_url_1_arg('command', 'SHOW_SL_FAVS'),
                                        CM_title, CM_URL)

    if g_settings['display_custom_filters']:
        _render_root_custom_filter_row('[Custom MAME filters]',
                                       _misc_url_1_arg('command', 'SHOW_CUSTOM_FILTERS'))

    if g_settings['display_MAME_most']:
        CM_title = 'Manage Most Played'
        CM_URL = URL_manage = _misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_MOST_PLAYED')
        _render_root_list_row_custom_CM('{Most Played MAME machines}',
                                        _misc_url_1_arg('command', 'SHOW_MAME_MOST_PLAYED'),
                                        CM_title, CM_URL)

    if g_settings['display_MAME_recent']:
        CM_title = 'Manage Recently Played'
        CM_URL = URL_manage = _misc_url_1_arg_RunPlugin('command', 'MANAGE_MAME_RECENT_PLAYED')
        _render_root_list_row_custom_CM('{Recently Played MAME machines}',
                                        _misc_url_1_arg('command', 'SHOW_MAME_RECENTLY_PLAYED'),
                                        CM_title, CM_URL)

    if g_settings['display_SL_most']:
        CM_title = 'Manage SL Most Played'
        CM_URL = URL_manage = _misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_MOST_PLAYED')
        _render_root_list_row_custom_CM('{Most Played SL ROMs}',
                                        _misc_url_1_arg('command', 'SHOW_SL_MOST_PLAYED'),
                                        CM_title, CM_URL)

    if g_settings['display_SL_recent']:
        CM_title = 'Manage SL Recently Played'
        CM_URL = URL_manage = _misc_url_1_arg_RunPlugin('command', 'MANAGE_SL_RECENT_PLAYED')
        _render_root_list_row_custom_CM('{Recently Played SL ROMs}',
                                        _misc_url_1_arg('command', 'SHOW_SL_RECENTLY_PLAYED'),
                                        CM_title, CM_URL)

    # --- End of directory ---
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

#
# These _render_skin_* functions used by skins to display widgets.
#
def _render_skin_fav_slots():
    _render_root_list_row_standard('Favourite MAME machines', _misc_url_1_arg('command', 'SHOW_MAME_FAVS'))
    _render_root_list_row_standard('Favourite Software Lists ROMs', _misc_url_1_arg('command', 'SHOW_SL_FAVS'))
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_skin_main_filters():
    machines_n_str = 'Machines with coin slot (Normal)'
    machines_u_str = 'Machines with coin slot (Unusual)'
    nocoin_str = 'Machines with no coin slot'
    mecha_str = 'Mechanical machines'
    dead_str = 'Dead machines'
    devices_str = 'Device machines'

    _render_root_list_row_standard(machines_n_str, _misc_url_2_arg('catalog', 'Main', 'category', 'Normal'))
    _render_root_list_row_standard(machines_u_str, _misc_url_2_arg('catalog', 'Main', 'category', 'Unusual'))
    _render_root_list_row_standard(nocoin_str,     _misc_url_2_arg('catalog', 'Main', 'category', 'NoCoin'))
    _render_root_list_row_standard(mecha_str,      _misc_url_2_arg('catalog', 'Main', 'category', 'Mechanical'))
    _render_root_list_row_standard(dead_str,       _misc_url_2_arg('catalog', 'Main', 'category', 'Dead'))
    _render_root_list_row_standard(devices_str,    _misc_url_2_arg('catalog', 'Main', 'category', 'Devices'))
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_skin_binary_filters():
    chd_str = 'Machines [with CHDs]'
    samples_str = 'Machines [with Samples]'
    softlists_str  = 'Machines [with Software Lists]'
    bios_str = 'Machines [BIOS]'

    _render_root_list_row_standard(bios_str,       _misc_url_2_arg('catalog', 'Binary', 'category', 'BIOS'))
    _render_root_list_row_standard(chd_str,        _misc_url_2_arg('catalog', 'Binary', 'category', 'CHD'))
    _render_root_list_row_standard(samples_str,    _misc_url_2_arg('catalog', 'Binary', 'category', 'Samples'))
    _render_root_list_row_standard(softlists_str,  _misc_url_2_arg('catalog', 'Binary', 'category', 'SoftwareLists'))
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_skin_catalog_filters():
    if g_settings['catver_path']:
        _render_root_list_row_standard('Machines by Category (Catver)',  _misc_url_1_arg('catalog', 'Catver'))
    if g_settings['catlist_path']:
        _render_root_list_row_standard('Machines by Category (Catlist)', _misc_url_1_arg('catalog', 'Catlist'))
    if g_settings['genre_path']:
        _render_root_list_row_standard('Machines by Category (Genre)',   _misc_url_1_arg('catalog', 'Genre'))
    if g_settings['nplayers_path']:
        _render_root_list_row_standard('Machines by Number of players',  _misc_url_1_arg('catalog', 'NPlayers'))
    if g_settings['bestgames_path']:
        _render_root_list_row_standard('Machines by Score',              _misc_url_1_arg('catalog', 'Bestgames'))
    if g_settings['series_path']:
        _render_root_list_row_standard('Machines by Series',             _misc_url_1_arg('catalog', 'Series'))

    _render_root_list_row_standard('Machines by Controls (Expanded)', _misc_url_1_arg('catalog', 'Controls_Expanded'))
    _render_root_list_row_standard('Machines by Controls (Compact)',  _misc_url_1_arg('catalog', 'Controls_Compact'))
    _render_root_list_row_standard('Machines by Device (Expanded)',   _misc_url_1_arg('catalog', 'Devices_Expanded'))
    _render_root_list_row_standard('Machines by Device (Compact)',    _misc_url_1_arg('catalog', 'Devices_Compact'))
    _render_root_list_row_standard('Machines by Display Rotation',    _misc_url_1_arg('catalog', 'Display_Rotate'))
    _render_root_list_row_standard('Machines by Display Type',        _misc_url_1_arg('catalog', 'Display_Type'))
    _render_root_list_row_standard('Machines by Driver',              _misc_url_1_arg('catalog', 'Driver'))
    _render_root_list_row_standard('Machines by Manufacturer',        _misc_url_1_arg('catalog', 'Manufacturer'))
    _render_root_list_row_standard('Machines by MAME short name',     _misc_url_1_arg('catalog', 'ShortName'))
    _render_root_list_row_standard('Machines by MAME long name',      _misc_url_1_arg('catalog', 'LongName'))
    _render_root_list_row_standard('Machines by Software List',       _misc_url_1_arg('catalog', 'BySL'))
    _render_root_list_row_standard('Machines by Year',                _misc_url_1_arg('catalog', 'Year'))
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_skin_dat_slots():
    _render_root_list_row_standard('History DAT',  _misc_url_1_arg('catalog', 'History'))
    _render_root_list_row_standard('MAMEINFO DAT', _misc_url_1_arg('catalog', 'MAMEINFO'))
    _render_root_list_row_standard('Gameinit DAT', _misc_url_1_arg('catalog', 'Gameinit'))
    _render_root_list_row_standard('Command DAT',  _misc_url_1_arg('catalog', 'Command'))
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_skin_SL_filters():
    if g_settings['SL_hash_path']:
        _render_root_list_row_standard('Software Lists (with ROMs)', _misc_url_1_arg('catalog', 'SL_ROM'))
        _render_root_list_row_standard('Software Lists (with ROMs and CHDs)', _misc_url_1_arg('catalog', 'SL_ROM_CHD'))
        _render_root_list_row_standard('Software Lists (with CHDs)', _misc_url_1_arg('catalog', 'SL_CHD'))
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_root_list_row_catalog(display_name, catalog_name, catalog_key):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = AML_ICON_FILE_PATH.getPath()
    fanart_path = AML_FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    URL_utils = _misc_url_3_arg_RunPlugin('command', 'UTILITIES',
                                          'catalog', catalog_name, 'category', catalog_key)
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Setup plugin', _misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Utilities', URL_utils),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_2_arg('catalog', catalog_name, 'category', catalog_key)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = True)

def _render_root_list_row_standard(root_name, root_URL):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(root_name)
    listitem.setInfo('video', {'title' : root_name, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = AML_ICON_FILE_PATH.getPath()
    fanart_path = AML_FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Setup plugin', _misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = root_URL, listitem = listitem, isFolder = True)

def _render_root_list_row_custom_CM(root_name, root_URL, CM_title, CM_URL):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(root_name)
    listitem.setInfo('video', {'title' : root_name, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = AML_ICON_FILE_PATH.getPath()
    fanart_path = AML_FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        (CM_title, CM_URL),
        ('Setup plugin', _misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = root_URL, listitem = listitem, isFolder = True)

def _render_root_custom_filter_row(root_name, root_URL):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(root_name)
    listitem.setInfo('video', {'title' : root_name, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = AML_ICON_FILE_PATH.getPath()
    fanart_path = AML_FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Setup custom filters', _misc_url_1_arg_RunPlugin('command', 'SETUP_CUSTOM_FILTERS')),
        ('Setup plugin', _misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = root_URL, listitem = listitem, isFolder = True)

#----------------------------------------------------------------------------------------------
# Cataloged machines
#----------------------------------------------------------------------------------------------
# Renders the category names in a catalog.
def _render_catalog_list(catalog_name):
    log_debug('_render_catalog_list() Starting ...')
    log_debug('_render_catalog_list() catalog_name = "{0}"'.format(catalog_name))

    # --- General AML plugin check ---
    # >> Check if databases have been built, print warning messages, etc. This function returns
    # >> False if no issues, True if there is issues and a dialog has been printed.
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if not _check_AML_MAME_status(PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render categories in catalog index
    _set_Kodi_all_sorting_methods_and_size()
    mame_view_mode = g_settings['mame_view_mode']
    loading_ticks_start = time.time()
    cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
    if mame_view_mode == VIEW_MODE_FLAT:
        catalog_dic = fs_get_cataloged_dic_all(PATHS, catalog_name)
    elif mame_view_mode == VIEW_MODE_PCLONE:
        catalog_dic = fs_get_cataloged_dic_parents(PATHS, catalog_name)
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
        _render_catalog_list_row(catalog_name, catalog_key, num_machines, machine_str)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()

    # --- DEBUG Data loading/rendering statistics ---
    log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
    log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

def _render_catalog_list_row(catalog_name, catalog_key, num_machines, machine_str):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    title_str = '{0} [COLOR orange]({1} {2})[/COLOR]'.format(catalog_key, num_machines, machine_str)
    plot_str = 'Catalog {0}\nCategory {1}'.format(catalog_name, catalog_key)
    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str,      'plot' : plot_str,
                               'overlay' : ICON_OVERLAY, 'size' : num_machines})

    # --- Artwork ---
    icon_path   = AML_ICON_FILE_PATH.getPath()
    fanart_path = AML_FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    URL_utils = _misc_url_3_arg_RunPlugin('command', 'UTILITIES',
                                          'catalog', catalog_name, 'category', catalog_key)
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Utilities', URL_utils),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_2_arg('catalog', catalog_name, 'category', catalog_key)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = True)

#
# Renders a list of parent MAME machines knowing the catalog name and the category.
# Display mode: a) parents only b) all machines (flat)
#
def _render_catalog_parent_list(catalog_name, category_name):
    # When using threads the performance gain is small: from 0.76 to 0.71, just 20 ms.
    # It's not worth it.
    log_debug('_render_catalog_parent_list() catalog_name  = {0}'.format(catalog_name))
    log_debug('_render_catalog_parent_list() category_name = {0}'.format(category_name))

    # >> Load ListItem properties (Not used at the moment)
    # prop_key = '{0} - {1}'.format(catalog_name, category_name)
    # log_debug('_render_catalog_parent_list() Loading props with key "{0}"'.format(prop_key))
    # mame_properties_dic = fs_load_JSON_file_dic(PATHS.MAIN_PROPERTIES_PATH.getPath())
    # prop_dic = mame_properties_dic[prop_key]
    # view_mode_property = prop_dic['vm']
    # >> Global properties
    view_mode_property = g_settings['mame_view_mode']
    log_debug('_render_catalog_parent_list() view_mode_property = {0}'.format(view_mode_property))

    # --- General AML plugin check ---
    # >> Check if databases have been built, print warning messages, etc. This function returns
    # >> False if no issues, True if there is issues and a dialog has been printed.
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if not _check_AML_MAME_status(PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Load main MAME info DB and catalog
    l_cataloged_dic_start = time.time()
    if view_mode_property == VIEW_MODE_PCLONE:
        catalog_dic = fs_get_cataloged_dic_parents(PATHS, catalog_name)
    elif view_mode_property == VIEW_MODE_FLAT:
        catalog_dic = fs_get_cataloged_dic_all(PATHS, catalog_name)
    else:
        kodi_dialog_OK('Wrong view_mode_property = "{0}". '.format(view_mode_property) +
                       'This is a bug, please report it.')
        return
    l_cataloged_dic_end = time.time()
    l_render_db_start = time.time()
    if g_settings['debug_enable_MAME_machine_cache']:
        cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
        render_db_dic = fs_load_roms_all(PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME machine cache disabled.')
        render_db_dic = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
    l_render_db_end = time.time()
    l_assets_db_start = time.time()
    if g_settings['debug_enable_MAME_asset_cache']:
        if 'cache_index_dic' not in locals():
            cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
        assets_db_dic = fs_load_assets_all(PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME asset cache disabled.')
        assets_db_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
    l_assets_db_end = time.time()
    l_pclone_dic_start = time.time()
    main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
    l_pclone_dic_end = time.time()
    l_favs_start = time.time()
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    l_favs_end = time.time()

    # >> Compute loading times.
    catalog_t = l_cataloged_dic_end - l_cataloged_dic_start
    render_t = l_render_db_end - l_render_db_start
    assets_t = l_assets_db_end - l_assets_db_start
    pclone_t = l_pclone_dic_end - l_pclone_dic_start
    favs_t   = l_favs_end - l_favs_start
    loading_time = catalog_t + render_t + assets_t + pclone_t + favs_t

    # >> Check if catalog is empty
    if not catalog_dic:
        kodi_dialog_OK('Catalog is empty. Check out "Setup plugin" context menu.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Process ROMs ---
    processing_ticks_start = time.time()
    r_list = _render_process_machines(catalog_dic, catalog_name, category_name,
                                     render_db_dic, assets_db_dic,
                                     main_pclone_dic, fav_machines)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    _set_Kodi_all_sorting_methods()
    _render_commit_machines(r_list)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()
    rendering_time = rendering_ticks_end - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    total_time = loading_time + processing_time + rendering_time
    # log_debug('Loading catalog    {0:.4f} s'.format(catalog_t))
    log_debug('Loading render db  {0:.4f} s'.format(render_t))
    log_debug('Loading assets db  {0:.4f} s'.format(assets_t))
    # log_debug('Loading pclone dic {0:.4f} s'.format(pclone_t))
    # log_debug('Loading MAME favs  {0:.4f} s'.format(favs_t))
    log_debug('Loading            {0:.4f} s'.format(loading_time))
    log_debug('Processing         {0:.4f} s'.format(processing_time))
    log_debug('Rendering          {0:.4f} s'.format(rendering_time))
    log_debug('Total              {0:.4f} s'.format(total_time))

#
# Renders a list of MAME Clone machines (including parent).
# No need to check for DB existance here. If this function is called is because parents and
# hence all ROMs databases exist.
#
def _render_catalog_clone_list(catalog_name, category_name, parent_name):
    log_debug('_render_catalog_clone_list() catalog_name  = {0}'.format(catalog_name))
    log_debug('_render_catalog_clone_list() category_name = {0}'.format(category_name))
    log_debug('_render_catalog_clone_list() parent_name   = {0}'.format(parent_name))
    display_hide_Mature = g_settings['display_hide_Mature']
    display_hide_BIOS = g_settings['display_hide_BIOS']
    if catalog_name == 'None' and category_name == 'BIOS': display_hide_BIOS = False
    display_hide_nonworking = g_settings['display_hide_nonworking']
    display_hide_imperfect  = g_settings['display_hide_imperfect']
    view_mode_property = g_settings['mame_view_mode']
    log_debug('_render_catalog_clone_list() view_mode_property = {0}'.format(view_mode_property))

    # >> Load main MAME info DB
    loading_ticks_start = time.time()
    catalog_dic = fs_get_cataloged_dic_all(PATHS, catalog_name)
    if g_settings['debug_enable_MAME_machine_cache']:
        cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
        render_db_dic = fs_load_roms_all(PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME machine cache disabled.')
        render_db_dic = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
    if g_settings['debug_enable_MAME_asset_cache']:
        if 'cache_index_dic' not in locals():
            cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
        assets_db_dic = fs_load_assets_all(PATHS, cache_index_dic, catalog_name, category_name)
    else:
        log_debug('MAME asset cache disabled.')
        assets_db_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
    main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    loading_ticks_end = time.time()
    loading_time = loading_ticks_end - loading_ticks_start

    # --- Process ROMs ---
    processing_ticks_start = time.time()
    machine_dic = catalog_dic[category_name]
    t_catalog_dic = {}
    t_render_dic = {}
    t_assets_dic = {}
    # >> Render parent first
    t_catalog_dic[category_name] = {parent_name : machine_dic[parent_name]}
    t_render_dic[parent_name] = render_db_dic[parent_name]
    t_assets_dic[parent_name] = assets_db_dic[parent_name]
    # >> Then clones
    for clone_name in main_pclone_dic[parent_name]:
        t_catalog_dic[category_name][clone_name] = machine_dic[clone_name]
        t_render_dic[clone_name] = render_db_dic[clone_name]
        t_assets_dic[clone_name] = assets_db_dic[clone_name]
    r_list = _render_process_machines(t_catalog_dic, catalog_name, category_name,
                                     t_render_dic, t_assets_dic, main_pclone_dic,
                                     fav_machines, False)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    _set_Kodi_all_sorting_methods()
    _render_commit_machines(r_list)
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
# "Premature optimization is the root of all evil." DK
# Returns a list of dictionaries
# r_list = [
#   {
#     'm_name' : str, 'render_name' : str,
#     'info' : {}, 'props' : {}, 'art' : {},
#     'context' : [], 'URL' ; str
#   }, ...
# ]
#
def _render_process_machines(catalog_dic, catalog_name, category_name,
                             render_db_dic, assets_dic, main_pclone_dic, fav_machines,
                             flag_parent_list = True, flag_ignore_filters = False):
    # --- Prepare for processing ---
    display_hide_Mature = g_settings['display_hide_Mature']
    display_hide_BIOS = g_settings['display_hide_BIOS']
    if catalog_name == 'None' and category_name == 'BIOS': display_hide_BIOS = False
    display_hide_nonworking = g_settings['display_hide_nonworking']
    display_hide_imperfect  = g_settings['display_hide_imperfect']
    # >> Think about how to implement this settings ...
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
        poster_path    = m_assets['flyer']

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
            'icon'      : icon_path,           'fanart'    : fanart_path,
            'banner'    : banner_path,         'clearlogo' : clearlogo_path,
            'poster' : poster_path
        }

        # --- Create context menu ---
        URL_view_DAT = _misc_url_2_arg_RunPlugin('command', 'VIEW_DAT', 'machine', machine_name)
        URL_view     = _misc_url_2_arg_RunPlugin('command', 'VIEW', 'machine', machine_name)
        URL_fav      = _misc_url_2_arg_RunPlugin('command', 'ADD_MAME_FAV', 'machine', machine_name)
        if flag_parent_list and num_clones > 0:
            URL_clones = _misc_url_4_arg_RunPlugin('command', 'EXEC_SHOW_MAME_CLONES', 
                                                   'catalog', catalog_name,
                                                   'category', category_name, 'parent', machine_name)
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

        # --- Add row ---
        r_dict['URL'] = _misc_url_2_arg('command', 'LAUNCH', 'machine', machine_name)
        r_list.append(r_dict)

    return r_list

def _render_commit_machines(r_list):
    for r_dict in r_list:
        # >> Krypton
        listitem = xbmcgui.ListItem(r_dict['render_name'])
        # >> Leia (much faster rendering). See changelog.
        # listitem = xbmcgui.ListItem(r_dict['render_name'], offscreen = True)

        listitem.setInfo('video', r_dict['info'])

        # >> Kodi Krypton
        for prop_name, prop_value in r_dict['props'].iteritems():
            listitem.setProperty(prop_name, prop_value)
        # >> In Kodi Leia use setProperties(). See https://github.com/xbmc/xbmc/pull/13952
        # listitem.setProperties(r_dict['props'])

        listitem.setArt(r_dict['art'])
        listitem.addContextMenuItems(r_dict['context'])
        xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = r_dict['URL'],
                                    listitem = listitem, isFolder = False)

#
# Not used at the moment -> There are global display settings.
#
def _command_context_display_settings(catalog_name, category_name):
    # >> Load ListItem properties
    log_debug('_command_display_settings() catalog_name  "{0}"'.format(catalog_name))
    log_debug('_command_display_settings() category_name "{0}"'.format(category_name))
    prop_key = '{0} - {1}'.format(catalog_name, category_name)
    log_debug('_command_display_settings() Loading props with key "{0}"'.format(prop_key))
    mame_properties_dic = fs_load_JSON_file_dic(PATHS.MAIN_PROPERTIES_PATH.getPath())
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
        log_debug('_command_display_settings() p_idx = "{0}"'.format(p_idx))
        idx = dialog.select('Display mode', ['Parents only', 'Parents and clones'], preselect = p_idx)
        log_debug('_command_display_settings() idx = "{0}"'.format(idx))
        if idx < 0: return
        if idx == 0:   prop_dic['vm'] = VIEW_MODE_NORMAL
        elif idx == 1: prop_dic['vm'] = VIEW_MODE_ALL

    # --- Change default icon ---
    elif menu_item == 1:
        kodi_dialog_OK('Not coded yet. Sorry')

    # >> Changes made. Refreash container
    fs_write_JSON_file(PATHS.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    kodi_refresh_container()

#----------------------------------------------------------------------------------------------
# Software Lists
#----------------------------------------------------------------------------------------------
def _render_SL_list(catalog_name):
    log_debug('_render_SL_list() catalog_name = {0}\n'.format(catalog_name))

    # --- General AML plugin check ---
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if not _check_AML_SL_status(PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Load Software List catalog
    SL_main_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

    # >> Build SL
    SL_catalog_dic = {}
    if catalog_name == 'SL_ROM':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_ROMs'] > 0 and SL_dic['num_with_CHDs'] == 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_CHD':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_CHDs'] > 0 and SL_dic['num_with_ROMs'] == 0:
                SL_catalog_dic[SL_name] = SL_dic
    elif catalog_name == 'SL_ROM_CHD':
        for SL_name, SL_dic in SL_main_catalog_dic.iteritems():
            if SL_dic['num_with_ROMs'] > 0 and SL_dic['num_with_CHDs'] > 0:
                SL_catalog_dic[SL_name] = SL_dic
    else:
        kodi_dialog_OK('Wrong catalog_name {0}'.format(catalog_name))
        return
    log_debug('_render_SL_list() len(catalog_name) = {0}\n'.format(len(SL_catalog_dic)))

    _set_Kodi_all_sorting_methods()
    for SL_name in SL_catalog_dic:
        SL = SL_catalog_dic[SL_name]
        _render_SL_list_row(SL_name, SL)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_SL_ROMs(SL_name):
    log_debug('_render_SL_ROMs() SL_name "{0}"'.format(SL_name))

    # --- General AML plugin check ---
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if not _check_AML_SL_status(PATHS, g_settings, control_dic):
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Load ListItem properties (Not used at the moment)
    # SL_properties_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PROP_PATH.getPath()) 
    # prop_dic = SL_properties_dic[SL_name]
    # >> Global properties
    view_mode_property = g_settings['sl_view_mode']
    log_debug('_render_SL_ROMs() view_mode_property = {0}'.format(view_mode_property))

    # >> Load Software List ROMs
    SL_PClone_dic = fs_load_JSON_file_dic(PATHS.SL_PCLONE_DIC_PATH.getPath())
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '.json'
    SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
    SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
    SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    _set_Kodi_all_sorting_methods()
    SL_proper_name = SL_catalog_dic[SL_name]['display_name']
    if view_mode_property == VIEW_MODE_PCLONE:
        log_debug('_render_SL_ROMs() Rendering Parent/Clone launcher')
        # >> Get list of parents
        parent_list = []
        for parent_name in sorted(SL_PClone_dic[SL_name]): parent_list.append(parent_name)
        for parent_name in parent_list:
            ROM        = SL_roms[parent_name]
            assets     = SL_asset_dic[parent_name] if parent_name in SL_asset_dic else fs_new_SL_asset()
            num_clones = len(SL_PClone_dic[SL_name][parent_name])
            ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
            _render_SL_ROM_row(SL_name, parent_name, ROM, assets, True, num_clones)
    elif view_mode_property == VIEW_MODE_FLAT:
        log_debug('_render_SL_ROMs() Rendering Flat launcher')
        for rom_name in SL_roms:
            ROM    = SL_roms[rom_name]
            assets = SL_asset_dic[rom_name] if rom_name in SL_asset_dic else fs_new_SL_asset()
            ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
            _render_SL_ROM_row(SL_name, rom_name, ROM, assets)
    else:
        kodi_dialog_OK('Wrong vm = "{0}". This is a bug, please report it.'.format(prop_dic['vm']))
        return
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_SL_pclone_set(SL_name, parent_name):
    log_debug('_render_SL_pclone_set() SL_name     "{0}"'.format(SL_name))
    log_debug('_render_SL_pclone_set() parent_name "{0}"'.format(parent_name))
    view_mode_property = g_settings['sl_view_mode']
    log_debug('_render_SL_pclone_set() view_mode_property = {0}'.format(view_mode_property))

    # >> Load Software List ROMs
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    SL_PClone_dic = fs_load_JSON_file_dic(PATHS.SL_PCLONE_DIC_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '.json'
    SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
    log_debug('_render_SL_pclone_set() ROMs JSON "{0}"'.format(SL_DB_FN.getPath()))
    SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())

    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
    SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

    # >> Render parent first
    SL_proper_name = SL_catalog_dic[SL_name]['display_name']
    _set_Kodi_all_sorting_methods()
    ROM = SL_roms[parent_name]
    assets = SL_asset_dic[parent_name] if parent_name in SL_asset_dic else fs_new_SL_asset()
    ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
    _render_SL_ROM_row(SL_name, parent_name, ROM, assets, False, view_mode_property)

    # >> Render clones belonging to parent in this category
    for clone_name in sorted(SL_PClone_dic[SL_name][parent_name]):
        ROM = SL_roms[clone_name]
        assets = SL_asset_dic[clone_name] if clone_name in SL_asset_dic else fs_new_SL_asset()
        ROM['genre'] = SL_proper_name # >> Add the SL name as 'genre'
        _render_SL_ROM_row(SL_name, clone_name, ROM, assets)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_SL_list_row(SL_name, SL):
    if SL['num_with_CHDs'] == 0:
        if SL['num_with_ROMs'] == 1:
            display_name = '{0}  [COLOR orange]({1} ROM)[/COLOR]'.format(SL['display_name'], SL['num_with_ROMs'])
        else:
            display_name = '{0}  [COLOR orange]({1} ROMs)[/COLOR]'.format(SL['display_name'], SL['num_with_ROMs'])
    elif SL['num_with_ROMs'] == 0:
        if SL['num_with_CHDs'] == 1:
            display_name = '{0}  [COLOR orange]({1} CHD)[/COLOR]'.format(SL['display_name'], SL['num_with_CHDs'])
        else:
            display_name = '{0}  [COLOR orange]({1} CHDs)[/COLOR]'.format(SL['display_name'], SL['num_with_CHDs'])
    else:
        display_name = '{0}  [COLOR orange]({1} ROMs and {2} CHDs)[/COLOR]'.format(SL['display_name'], SL['num_with_ROMs'], SL['num_with_CHDs'])

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY } )

    # --- Create context menu ---
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)' ),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_2_arg('catalog', 'SL', 'category', SL_name)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = True)

def _render_SL_ROM_row(SL_name, rom_name, ROM, assets, flag_parent_list = False, num_clones = 0):
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
    poster_path = assets['boxfront']

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
    listitem.setArt({'title' : assets['title'], 'snap' : assets['snap'], 'boxfront' : assets['boxfront'],
                     'icon' : icon_path, 'fanart' : fanart_path, 'poster' : poster_path})

    # --- Create context menu ---
    URL_view_DAT = _misc_url_3_arg_RunPlugin('command', 'VIEW_DAT', 'SL', SL_name, 'ROM', rom_name)
    URL_view = _misc_url_3_arg_RunPlugin('command', 'VIEW', 'SL', SL_name, 'ROM', rom_name)
    URL_fav = _misc_url_3_arg_RunPlugin('command', 'ADD_SL_FAV', 'SL', SL_name, 'ROM', rom_name)
    if flag_parent_list and num_clones > 0:
        URL_show_c = _misc_url_4_arg_RunPlugin('command', 'EXEC_SHOW_SL_CLONES', 
                                                    'catalog', 'SL', 'category', SL_name, 'parent', rom_name)
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
    URL = _misc_url_3_arg('command', 'LAUNCH_SL', 'SL', SL_name, 'ROM', rom_name)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)

#----------------------------------------------------------------------------------------------
# DATs
#
# catalog = 'History'  / category = '32x' / machine = 'sonic'
# catalog = 'MAMEINFO' / category = '32x' / machine = 'sonic'
# catalog = 'Gameinit' / category = 'None' / machine = 'sonic'
# catalog = 'Command'  / category = 'None' / machine = 'sonic'
#----------------------------------------------------------------------------------------------
def _render_DAT_list(catalog_name):
    # --- Create context menu ---
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    # --- Unrolled variables ---
    ICON_OVERLAY = 6

    # >> Load Software List catalog
    if catalog_name == 'History':
        DAT_idx_dic = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        _set_Kodi_all_sorting_methods()
        for key in DAT_idx_dic:
            category_name = '{0} [COLOR lightgray]({1})[/COLOR]'.format(DAT_idx_dic[key]['name'], key)
            listitem = xbmcgui.ListItem(category_name)
            listitem.setInfo('video', {'title' : category_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = _misc_url_2_arg('catalog', catalog_name, 'category', key)
            xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = True)
    elif catalog_name == 'MAMEINFO':
        DAT_idx_dic = fs_load_JSON_file_dic(PATHS.MAMEINFO_IDX_PATH.getPath())
        if not DAT_idx_dic:
            kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        _set_Kodi_all_sorting_methods()
        for key in DAT_idx_dic:
            category_name = '{0}'.format(key)
            listitem = xbmcgui.ListItem(category_name)
            listitem.setInfo('video', {'title' : category_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = _misc_url_2_arg('catalog', catalog_name, 'category', key)
            xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = True)
    elif catalog_name == 'Gameinit':
        DAT_idx_list = fs_load_JSON_file_dic(PATHS.GAMEINIT_IDX_PATH.getPath())
        if not DAT_idx_list:
            kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        _set_Kodi_all_sorting_methods()
        for machine_name_list in DAT_idx_list:
            machine_name = '{0} [COLOR lightgray]({1})[/COLOR]'.format(machine_name_list[1], machine_name_list[0])
            listitem = xbmcgui.ListItem(machine_name)
            listitem.setInfo('video', {'title' : machine_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = _misc_url_3_arg('catalog', catalog_name, 'category', 'None', 'machine', machine_name_list[0])
            xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)
    elif catalog_name == 'Command':
        DAT_idx_list = fs_load_JSON_file_dic(PATHS.COMMAND_IDX_PATH.getPath())
        if not DAT_idx_list:
            kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
            xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
            return
        _set_Kodi_all_sorting_methods()
        for machine_name_list in DAT_idx_list:
            machine_name = '{0} [COLOR lightgray]({1})[/COLOR]'.format(machine_name_list[1], machine_name_list[0])
            listitem = xbmcgui.ListItem(machine_name)
            listitem.setInfo('video', {'title' : machine_name, 'overlay' : ICON_OVERLAY } )
            listitem.addContextMenuItems(commands)
            URL = _misc_url_3_arg('catalog', catalog_name, 'category', 'None', 'machine', machine_name_list[0])
            xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)
    else:
        kodi_dialog_OK('DAT database file "{0}" not found. Check out "Setup plugin" context menu.'.format(catalog_name))
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_DAT_category(catalog_name, category_name):
    # >> Load Software List catalog
    if catalog_name == 'History':
        DAT_catalog_dic = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
    elif catalog_name == 'MAMEINFO':
        DAT_catalog_dic = fs_load_JSON_file_dic(PATHS.MAMEINFO_IDX_PATH.getPath())
    else:
        kodi_dialog_OK('DAT database file "{0}" not found. Check out "Setup plugin" context menu.'.format(catalog_name))
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return
    if not DAT_catalog_dic:
        kodi_dialog_OK('DAT database file "{0}" empty.'.format(catalog_name))
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return
    _set_Kodi_all_sorting_methods()
    if catalog_name == 'History':
        category_machine_list = DAT_catalog_dic[category_name]['machines']
        for machine_tuple in category_machine_list:
            _render_DAT_category_row(catalog_name, category_name, machine_tuple)
    elif catalog_name == 'MAMEINFO':
        category_machine_list = DAT_catalog_dic[category_name]
        for machine_tuple in category_machine_list:
            _render_DAT_category_row(catalog_name, category_name, machine_tuple)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_DAT_category_row(catalog_name, category_name, machine_tuple):
    display_name = '{0} [COLOR lightgray]({1})[/COLOR]'.format(machine_tuple[1], machine_tuple[0])

    # --- Create listitem row ---
    ICON_OVERLAY = 6
    listitem = xbmcgui.ListItem(display_name)
    listitem.setInfo('video', {'title' : display_name, 'overlay' : ICON_OVERLAY } )

    # --- Create context menu ---
    commands = [
        ('View', _misc_url_1_arg_RunPlugin('command', 'VIEW')),
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_3_arg('catalog', catalog_name, 'category', category_name, 'machine', machine_tuple[0])
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)

def _render_DAT_machine_info(catalog_name, category_name, machine_name):
    log_debug('_render_DAT_machine_info() catalog_name "{0}"'.format(catalog_name))
    log_debug('_render_DAT_machine_info() category_name "{0}"'.format(category_name))
    log_debug('_render_DAT_machine_info() machine_name "{0}"'.format(machine_name))

    # >> Load Software List catalog
    if catalog_name == 'History':
        DAT_dic = fs_load_JSON_file_dic(PATHS.HISTORY_DB_PATH.getPath())
        info_str = DAT_dic[category_name][machine_name]
        info_text = info_str
    elif catalog_name == 'MAMEINFO':
        DAT_dic = fs_load_JSON_file_dic(PATHS.MAMEINFO_DB_PATH.getPath())
        info_str = DAT_dic[category_name][machine_name]
        info_text = info_str
    elif catalog_name == 'Gameinit':
        DAT_dic = fs_load_JSON_file_dic(PATHS.GAMEINIT_DB_PATH.getPath())
        info_str = DAT_dic[machine_name]
        info_text = info_str
    elif catalog_name == 'Command':
        DAT_dic = fs_load_JSON_file_dic(PATHS.COMMAND_DB_PATH.getPath())
        info_str = DAT_dic[machine_name]
        info_text = info_str
    else:
        kodi_dialog_OK('Wrong catalog_name "{0}". '.format(catalog_name) +
                       'This is a bug, please report it.')
        return

    # --- Show information window ---
    window_title = '{0} information'.format(catalog_name)
    _display_text_window(window_title, info_text)

#
# Not used at the moment -> There are global display settings.
#
def _command_context_display_settings_SL(SL_name):
    log_debug('_command_display_settings_SL() SL_name "{0}"'.format(SL_name))

    # --- Load properties DB ---
    SL_properties_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PROP_PATH.getPath())
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
        log_debug('_command_display_settings() p_idx = "{0}"'.format(p_idx))
        idx = dialog.select('Display mode', ['Parents only', 'Parents and clones'], preselect = p_idx)
        log_debug('_command_display_settings() idx = "{0}"'.format(idx))
        if idx < 0: return
        if idx == 0:   prop_dic['vm'] = VIEW_MODE_NORMAL
        elif idx == 1: prop_dic['vm'] = VIEW_MODE_ALL

    # --- Change default icon ---
    elif menu_item == 1:
        kodi_dialog_OK('Not coded yet. Sorry')

    # --- Save display settings ---
    fs_write_JSON_file(PATHS.SL_MACHINES_PROP_PATH.getPath(), SL_properties_dic)
    kodi_refresh_container()

# ---------------------------------------------------------------------------------------------
# Information display / Utilities
# ---------------------------------------------------------------------------------------------
def _command_context_view_DAT(machine_name, SL_name, SL_ROM, location):
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
    log_debug('_command_context_view_DAT() machine_name "{0}"'.format(machine_name))
    log_debug('_command_context_view_DAT() SL_name      "{0}"'.format(SL_name))
    log_debug('_command_context_view_DAT() SL_ROM       "{0}"'.format(SL_ROM))
    log_debug('_command_context_view_DAT() location     "{0}"'.format(location))
    if machine_name:
        view_type = VIEW_MAME_MACHINE
    elif SL_name:
        view_type = VIEW_SL_ROM
    log_debug('_command_context_view_DAT() view_type = {0}'.format(view_type))

    if view_type == VIEW_MAME_MACHINE:
        # >> Load DAT indices
        History_idx_dic   = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
        Mameinfo_idx_dic  = fs_load_JSON_file_dic(PATHS.MAMEINFO_IDX_PATH.getPath())
        Gameinit_idx_list = fs_load_JSON_file_dic(PATHS.GAMEINIT_IDX_PATH.getPath())
        Command_idx_list  = fs_load_JSON_file_dic(PATHS.COMMAND_IDX_PATH.getPath())

        # >> Check if DAT information is available for this machine
        if History_idx_dic:
            # >> Python Set Comprehension
            History_MAME_set = { machine[0] for machine in History_idx_dic['mame']['machines'] }
            if machine_name in History_MAME_set: History_str = 'Found'
            else:                                History_str = 'Not found'
        else:
            History_str = 'Not configured'
        if Mameinfo_idx_dic:
            Mameinfo_MAME_set = { machine[0] for machine in Mameinfo_idx_dic['mame'] }
            if machine_name in Mameinfo_MAME_set: Mameinfo_str = 'Found'
            else:                                 Mameinfo_str = 'Not found'
        else:
            Mameinfo_str = 'Not configured'
        if Gameinit_idx_list:
            Gameinit_MAME_set = { machine[0] for machine in Gameinit_idx_list }
            if machine_name in Gameinit_MAME_set: Gameinit_str = 'Found'
            else:                                 Gameinit_str = 'Not found'
        else:
            Gameinit_str = 'Not configured'
        if Command_idx_list:
            Command_MAME_set = { machine[0] for machine in Command_idx_list }
            if machine_name in Command_MAME_set: Command_str = 'Found'
            else:                                Command_str = 'Not found'
        else:
            Command_str = 'Not configured'
    elif view_type == VIEW_SL_ROM:
        History_idx_dic   = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
        if History_idx_dic:
            if SL_name in History_idx_dic:
                History_MAME_set = { machine[0] for machine in History_idx_dic[SL_name]['machines'] }
                if SL_ROM in History_MAME_set: History_str = 'Found'
                else:                          History_str = 'Not found'
            else:
                History_str = 'SL not found'
        else:
            History_str = 'Not configured'

    # --- Build menu base on view_type ---
    if view_type == VIEW_MAME_MACHINE:
        d_list = [
          'View History DAT ({0})'.format(History_str),
          'View MAMEinfo DAT ({0})'.format(Mameinfo_str),
          'View Gameinit DAT ({0})'.format(Gameinit_str),
          'View Command DAT ({0})'.format(Command_str),
          'View Fanart',
          'View Manual',
          'Display brother machines',
          'Display machines with same Genre',
          'Display machines by same Manufacturer',
        ]
    elif view_type == VIEW_SL_ROM:
        d_list = [
          'View History DAT ({0})'.format(History_str),
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
            kodi_dialog_OK('view_type == VIEW_MAME_MACHINE and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_SL_ROM:
        if   selected_value == 0: action = ACTION_VIEW_HISTORY
        elif selected_value == 1: action = ACTION_VIEW_FANART
        elif selected_value == 2: action = ACTION_VIEW_MANUAL
        else:
            kodi_dialog_OK('view_type == VIEW_SL_ROM and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return

    # --- Execute action ---
    if action == ACTION_VIEW_HISTORY:
        if view_type == VIEW_MAME_MACHINE:
            if machine_name not in History_MAME_set:
                kodi_dialog_OK('MAME machine {0} not in History DAT'.format(machine_name))
                return
            DAT_dic = fs_load_JSON_file_dic(PATHS.HISTORY_DB_PATH.getPath())
            window_title = 'History DAT for MAME machine {0}'.format(machine_name)
            info_text = DAT_dic['mame'][machine_name]
        elif view_type == VIEW_SL_ROM:
            if SL_ROM not in History_MAME_set:
                kodi_dialog_OK('SL item {0} not in History DAT'.format(SL_ROM))
                return
            DAT_dic = fs_load_JSON_file_dic(PATHS.HISTORY_DB_PATH.getPath())
            window_title = 'History DAT for SL item {0}'.format(SL_ROM)
            info_text = DAT_dic[SL_name][SL_ROM]
        _display_text_window(window_title, info_text)

    elif action == ACTION_VIEW_MAMEINFO:
        if machine_name not in Mameinfo_MAME_set:
            kodi_dialog_OK('Machine {0} not in Mameinfo DAT'.format(machine_name))
            return
        DAT_dic = fs_load_JSON_file_dic(PATHS.MAMEINFO_DB_PATH.getPath())
        info_text = DAT_dic['mame'][machine_name]

        window_title = 'MAMEinfo DAT for machine {0}'.format(machine_name)
        _display_text_window(window_title, info_text)

    elif action == ACTION_VIEW_GAMEINIT:
        if machine_name not in Gameinit_MAME_set:
            kodi_dialog_OK('Machine {0} not in Gameinit DAT'.format(machine_name))
            return
        DAT_dic = fs_load_JSON_file_dic(PATHS.GAMEINIT_DB_PATH.getPath())
        window_title = 'Gameinit DAT for machine {0}'.format(machine_name)
        info_text = DAT_dic[machine_name]
        _display_text_window(window_title, info_text)

    elif action == ACTION_VIEW_COMMAND:
        if machine_name not in Command_MAME_set:
            kodi_dialog_OK('Machine {0} not in Command DAT'.format(machine_name))
            return
        DAT_dic = fs_load_JSON_file_dic(PATHS.COMMAND_DB_PATH.getPath())
        window_title = 'Command DAT for machine {0}'.format(machine_name)
        info_text = DAT_dic[machine_name]
        _display_text_window(window_title, info_text)

    # --- View Fanart ---
    elif action == ACTION_VIEW_FANART:
        # >> Open ROM in assets database
        if view_type == VIEW_MAME_MACHINE:
            if location == 'STANDARD':
                assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
                m_assets = assets_dic[machine_name]
            else:
                mame_favs_dic = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
                m_assets = mame_favs_dic[machine_name]['assets']
            if not m_assets['fanart']:
                kodi_dialog_OK('Fanart for machine {0} not found.'.format(machine_name))
                return
        elif view_type == VIEW_SL_ROM:
            SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            m_assets = SL_asset_dic[SL_ROM]
            if not m_assets['fanart']:
                kodi_dialog_OK('Fanart for SL item {0} not found.'.format(SL_ROM))
                return

        # >> If manual found then display it.
        log_debug('Rendering FS fanart "{0}"'.format(m_assets['fanart']))
        xbmc.executebuiltin('ShowPicture("{0}")'.format(m_assets['fanart']))

    # --- View Manual ---
    # For the PDF viewer implementation look at https://github.com/i96751414/plugin.image.pdfreader
    #
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
            # machine = fs_get_machine_main_db_hash(PATHS, machine_name)
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            if not assets_dic[machine_name]['manual']:
                kodi_dialog_OK('Manual not found in database.')
                return
            man_file_FN = FileName(assets_dic[machine_name]['manual'])
            img_dir_FN = FileName(g_settings['assets_path']).pjoin('manuals').pjoin(machine_name + '.pages')
        elif view_type == VIEW_SL_ROM:
            log_debug('Displaying Manual for SL {0} item {1} ...'.format(SL_name, SL_ROM))
            SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
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

        # --- If output directory does not exist create it ---
        if not img_dir_FN.exists():
            log_info('Creating DIR "{0}"'.format(img_dir_FN.getPath()))
            img_dir_FN.makedirs()

        # --- Extract images of manual ---
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced MAME Launcher', 'Extracting manual images')
        pDialog.update(0)
        status_dic = {
            'manFormat' : '', # PDF, CBZ, CBR, ...
            'numImages' : 0,
        }
        manuals_extract_pages(status_dic, man_file_FN, img_dir_FN)
        pDialog.update(100)
        pDialog.close()

        # --- Display page images ---
        if status_dic['numImages'] < 1:
            str_list = [
                'Cannot find images inside the {0} file. '.format(status_dic['manFormat']),
                'Check log for more details.'
            ]
            kodi_dialog_OK(''.join(str_list))
            return
        log_debug('Rendering images in "{0}"'.format(img_dir_FN.getPath()))
        xbmc.executebuiltin('SlideShow("{0}",pause)'.format(img_dir_FN.getPath()))

    # --- Display brother machines (same driver) ---
    elif action == ACTION_VIEW_BROTHERS:
        # >> Load ROM Render data from hashed database
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
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
        url = _misc_url_2_arg('catalog', 'Driver', 'category', sourcefile_str)
        log_debug('Container.Update URL "{0}"'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    # --- Display machines with same Genre ---
    elif action == ACTION_VIEW_SAME_GENRE:
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
        genre_str = machine['genre']
        url = _misc_url_2_arg('catalog', 'Genre', 'category', genre_str)
        log_debug('Container.Update URL {0}'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    # --- Display machines by same Manufacturer ---
    elif action == ACTION_VIEW_SAME_MANUFACTURER:
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
        manufacturer_str = machine['manufacturer']
        url = _misc_url_2_arg('catalog', 'Manufacturer', 'category', manufacturer_str)
        log_debug('Container.Update URL {0}'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    else:
        kodi_dialog_OK('Unknown action == {0}. '.format(action) +
                       'This is a bug, please report it.')

# ---------------------------------------------------------------------------------------------
# Information display
# ---------------------------------------------------------------------------------------------
def _command_context_view(machine_name, SL_name, SL_ROM, location):
    VIEW_SIMPLE       = 100
    VIEW_MAME_MACHINE = 200
    VIEW_SL_ROM       = 300

    ACTION_VIEW_MACHINE_DATA       = 100
    ACTION_VIEW_MACHINE_ROMS       = 200
    ACTION_VIEW_MACHINE_AUDIT_ROMS = 300
    ACTION_VIEW_SL_ROM_DATA        = 400
    ACTION_VIEW_SL_ROM_ROMS        = 500
    ACTION_VIEW_SL_ROM_AUDIT_ROMS  = 600
    ACTION_VIEW_DB_STATS           = 700
    ACTION_VIEW_EXEC_OUTPUT        = 800
    ACTION_VIEW_REPORT_SCANNER     = 900
    ACTION_VIEW_REPORT_AUDIT       = 1000
    ACTION_AUDIT_MAME_MACHINE      = 1100
    ACTION_AUDIT_SL_MACHINE        = 1200

    # --- Determine if we are in a category, launcher or ROM ---
    log_debug('_command_context_view() machine_name "{0}"'.format(machine_name))
    log_debug('_command_context_view() SL_name      "{0}"'.format(SL_name))
    log_debug('_command_context_view() SL_ROM       "{0}"'.format(SL_ROM))
    log_debug('_command_context_view() location     "{0}"'.format(location))
    if not machine_name and not SL_name:
        view_type = VIEW_SIMPLE
    elif machine_name:
        view_type = VIEW_MAME_MACHINE
    elif SL_name:
        view_type = VIEW_SL_ROM
    log_debug('_command_context_view() view_type = {0}'.format(view_type))

    # --- Build menu base on view_type ---
    if PATHS.MAME_OUTPUT_PATH.exists():
        filesize = PATHS.MAME_OUTPUT_PATH.fileSize()
        STD_status = '{0} bytes'.format(filesize)
    else:
        STD_status = 'not found'

    if view_type == VIEW_SIMPLE:
        d_list = [
          'View database statistics ...',
          'View scanner reports ...',
          'View audit reports ...',
          'View MAME last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_MAME_MACHINE:
        d_list = [
          'View MAME machine data',
          'View MAME machine ROMs (ROMs DB)',
          'View MAME machine ROMs (Audit DB)',
          'Audit MAME machine ROMs',
          'View database statistics ...',
          'View scanner reports ...',
          'View audit reports ...',
          'View MAME last execution output ({0})'.format(STD_status),
        ]
    elif view_type == VIEW_SL_ROM:
        d_list = [
          'View Software List item data',
          'View Software List ROMs (ROMs DB)',
          'View Software List ROMs (Audit DB)',
          'Audit Software List ROMs',
          'View database statistics ...',
          'View scanner reports ...',
          'View audit reports ...',
          'View MAME last execution output ({0})'.format(STD_status),
        ]
    else:
        kodi_dialog_OK('Wrong view_type = {0}. This is a bug, please report it.'.format(view_type))
        return
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Polymorphic menu. Determine action to do. ---
    if view_type == VIEW_SIMPLE:
        if   selected_value == 0: action = ACTION_VIEW_DB_STATS
        elif selected_value == 1: action = ACTION_VIEW_REPORT_SCANNER
        elif selected_value == 2: action = ACTION_VIEW_REPORT_AUDIT
        elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_SIMPLE and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_MAME_MACHINE:
        if   selected_value == 0: action = ACTION_VIEW_MACHINE_DATA
        elif selected_value == 1: action = ACTION_VIEW_MACHINE_ROMS
        elif selected_value == 2: action = ACTION_VIEW_MACHINE_AUDIT_ROMS
        elif selected_value == 3: action = ACTION_AUDIT_MAME_MACHINE
        elif selected_value == 4: action = ACTION_VIEW_DB_STATS
        elif selected_value == 5: action = ACTION_VIEW_REPORT_SCANNER
        elif selected_value == 6: action = ACTION_VIEW_REPORT_AUDIT
        elif selected_value == 7: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_MAME_MACHINE and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    elif view_type == VIEW_SL_ROM:
        if   selected_value == 0: action = ACTION_VIEW_SL_ROM_DATA
        elif selected_value == 1: action = ACTION_VIEW_SL_ROM_ROMS
        elif selected_value == 2: action = ACTION_VIEW_SL_ROM_AUDIT_ROMS
        elif selected_value == 3: action = ACTION_AUDIT_SL_MACHINE
        elif selected_value == 4: action = ACTION_VIEW_DB_STATS
        elif selected_value == 5: action = ACTION_VIEW_REPORT_SCANNER
        elif selected_value == 6: action = ACTION_VIEW_REPORT_AUDIT
        elif selected_value == 7: action = ACTION_VIEW_EXEC_OUTPUT
        else:
            kodi_dialog_OK('view_type == VIEW_SL_ROM and selected_value = {0}. '.format(selected_value) +
                           'This is a bug, please report it.')
            return
    else:
        kodi_dialog_OK('Wrong view_type = {0}. '.format(view_type) +
                       'This is a bug, please report it.')
        return
    log_debug('_command_context_view() action = {0}'.format(action))

    # --- Execute action ---
    if action == ACTION_VIEW_MACHINE_DATA:
        pDialog = xbmcgui.DialogProgress()
        if location == LOCATION_STANDARD:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'ROM hashed database')
            machine = fs_get_machine_main_db_hash(PATHS, machine_name)
            pDialog.update(50, pdialog_line1, 'Assets hashed database')
            assets = fs_get_machine_assets_db_hash(PATHS, machine_name)
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            window_title = 'MAME Machine Information'

        elif location == LOCATION_MAME_FAVS:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'MAME Favourites database')
            machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            machine = machines[machine_name]
            assets = machine['assets']
            window_title = 'Favourite MAME Machine Information'

        elif location == LOCATION_MAME_MOST_PLAYED:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'MAME Most Played database')
            most_played_roms_dic = fs_load_JSON_file_dic(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
            pDialog.update(100, pdialog_line1)
            pDialog.close()
            machine = most_played_roms_dic[machine_name]
            assets = machine['assets']
            window_title = 'Most Played MAME Machine Information'

        elif location == LOCATION_MAME_RECENT_PLAYED:
            pdialog_line1 = 'Loading databases ...'
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(0, pdialog_line1, 'MAME Recently Played database')
            recent_roms_list = fs_load_JSON_file_list(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
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
        _display_text_window(window_title, '\n'.join(slist))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_MAME_item_data']:
            log_info('Writing file "{0}"'.format(PATHS.REPORT_DEBUG_MAME_ITEM_DATA_PATH.getPath()))
            with open(PATHS.REPORT_DEBUG_MAME_ITEM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(slist)
                file.write('\n'.join(slist).encode('utf-8'))

    # --- View Software List ROM Machine data ---
    elif action == ACTION_VIEW_SL_ROM_DATA:
        if location == LOCATION_STANDARD:
            # --- Load databases ---
            kodi_busydialog_ON()
            SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
            SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
            SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
            SL_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '.json')
            roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
            kodi_busydialog_OFF()

            # --- Prepare data ---
            rom = roms[SL_ROM]
            assets = SL_asset_dic[SL_ROM]
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Software List ROM Information'

        elif location == LOCATION_SL_FAVS:
            # --- Load databases ---
            kodi_busydialog_ON()
            SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
            kodi_busydialog_OFF()

            # --- Prepare data ---
            fav_key = SL_name + '-' + SL_ROM
            rom = fav_SL_roms[fav_key]
            assets = rom['assets']
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Favourite Software List Item Information'

        elif location == LOCATION_SL_MOST_PLAYED:
            kodi_busydialog_ON()
            SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            most_played_roms_dic = fs_load_JSON_file_dic(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
            kodi_busydialog_OFF()

            # --- Prepare data ---
            fav_key = SL_name + '-' + SL_ROM
            rom = most_played_roms_dic[fav_key]
            assets = rom['assets']
            SL_dic = SL_catalog_dic[SL_name]
            SL_machine_list = SL_machines_dic[SL_name]
            window_title = 'Most Played SL Item Information'

        elif location == LOCATION_SL_RECENT_PLAYED:
            kodi_busydialog_ON()
            SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
            SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            recent_roms_list = fs_load_JSON_file_list(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
            kodi_busydialog_OFF()

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
        _display_text_window(window_title, '\n'.join(slist))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_SL_item_data']:
            log_info('Writing file "{0}"'.format(PATHS.REPORT_DEBUG_SL_ITEM_DATA_PATH.getPath()))
            with open(PATHS.REPORT_DEBUG_SL_ITEM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(slist)
                file.write('\n'.join(slist).encode('utf-8'))

    # --- View database information and statistics stored in control dictionary ---
    elif action == ACTION_VIEW_DB_STATS:
        d = xbmcgui.Dialog()
        type_sub = d.select('View scanner reports',
                            ['View main statistics',
                             'View scanner statistics',
                             'View audit statistics',
                             'View all statistics',
                             'Write all statistics to file'])
        if type_sub < 0: return

        # --- Main stats ---
        if type_sub == 0:
            # --- Warn user if error ---
            if not PATHS.MAIN_CONTROL_PATH.exists():
                kodi_dialog_OK('MAME database not found. Please setup the addon first.')
                return
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            info_text = []
            mame_stats_main_print_slist(info_text, control_dic, __addon_version__)
            _display_text_window('Database main statistics', '\n'.join(info_text))

        # --- Scanner statistics ---
        elif type_sub == 1:
            # --- Warn user if error ---
            if not PATHS.MAIN_CONTROL_PATH.exists():
                kodi_dialog_OK('MAME database not found. Please setup the addon first.')
                return
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            info_text = []
            mame_stats_scanner_print_slist(info_text, control_dic)
            _display_text_window('Scanner statistics', '\n'.join(info_text))

        # --- Audit statistics ---
        elif type_sub == 2:
            # --- Warn user if error ---
            if not PATHS.MAIN_CONTROL_PATH.exists():
                kodi_dialog_OK('MAME database not found. Please setup the addon first.')
                return
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            info_text = []
            mame_stats_audit_print_slist(info_text, control_dic, g_settings)
            _display_text_window('Database information and statistics', '\n'.join(info_text))

        # --- All statistics ---
        elif type_sub == 3:
            # --- Warn user if error ---
            if not PATHS.MAIN_CONTROL_PATH.exists():
                kodi_dialog_OK('MAME database not found. Please setup the addon first.')
                return
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            info_text = []
            mame_stats_main_print_slist(info_text, control_dic, __addon_version__)
            info_text.append('')
            mame_stats_scanner_print_slist(info_text, control_dic)
            info_text.append('')
            mame_stats_audit_print_slist(info_text, control_dic, g_settings)
            _display_text_window('Database full statistics', '\n'.join(info_text))

        # --- Write statistics to disk ---
        elif type_sub == 4:
            # --- Warn user if error ---
            if not PATHS.MAIN_CONTROL_PATH.exists():
                kodi_dialog_OK('MAME database not found. Please setup the addon first.')
                return
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())

            # --- Generate stats string and remove Kodi colours ---
            info_text = []
            mame_stats_main_print_slist(info_text, control_dic, __addon_version__)
            info_text.append('')
            mame_stats_scanner_print_slist(info_text, control_dic)
            info_text.append('')
            mame_stats_audit_print_slist(info_text, control_dic, g_settings)
            # text_remove_slist_colours(info_text)

            # --- Write file to disk and inform user ---
            log_info('Writing AML statistics report ...')
            log_info('File "{0}"'.format(PATHS.REPORT_STATS_PATH.getPath()))
            with open(PATHS.REPORT_STATS_PATH.getPath(), 'w') as f:
                text_remove_color_tags_slist(info_text)
                f.write('\n'.join(info_text).encode('utf-8'))
            kodi_notify('Exported AML statistic')

    # --- View MAME machine ROMs (ROMs database) ---
    elif action == ACTION_VIEW_MACHINE_ROMS:
        # >> Load machine dictionary, ROM database and Devices database.
        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 3
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machines Main')
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machine ROMs')
        roms_db_dic = fs_load_JSON_file_dic(PATHS.ROMS_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machine Devices')
        devices_db_dic = fs_load_JSON_file_dic(PATHS.DEVICES_DB_PATH.getPath())
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
        # Table columns: Type - ROM name - Size - CRC/SHA1 - Merge - BIOS - Location
        table_str = []
        table_str.append(['right', 'left',     'right', 'left',     'left',  'left'])
        table_str.append(['Type',  'ROM name', 'Size',  'CRC/SHA1', 'Merge', 'BIOS/Device'])

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
        _display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_MAME_ROM_DB_data']:
            log_info('Writing file "{0}"'.format(PATHS.REPORT_DEBUG_MAME_ITEM_ROM_DATA_PATH.getPath()))
            with open(PATHS.REPORT_DEBUG_MAME_ITEM_ROM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View MAME machine ROMs (Audit ROM database) ---
    elif action == ACTION_VIEW_MACHINE_AUDIT_ROMS:
        # --- Load machine dictionary and ROM database ---
        rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][g_settings['mame_rom_set']]
        log_debug('_command_context_view() View Machine ROMs (Audit database)\n')
        log_debug('_command_context_view() rom_set {0}\n'.format(rom_set))

        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 2
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machine hash')
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME ROM Audit')
        audit_roms_dic = fs_load_JSON_file_dic(PATHS.ROM_AUDIT_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Grab data and settings ---
        rom_list = audit_roms_dic[machine_name]
        cloneof = machine['cloneof']
        romof = machine['romof']
        log_debug('_command_context_view() machine {0}\n'.format(machine_name))
        log_debug('_command_context_view() cloneof {0}\n'.format(cloneof))
        log_debug('_command_context_view() romof   {0}\n'.format(romof))

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
        _display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_MAME_Audit_DB_data']:
            log_info('Writing file "{0}"'.format(PATHS.REPORT_DEBUG_MAME_ITEM_AUDIT_DATA_PATH.getPath()))
            with open(PATHS.REPORT_DEBUG_MAME_ITEM_AUDIT_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View SL ROMs ---
    elif action == ACTION_VIEW_SL_ROM_ROMS:
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '.json')
        SL_ROMS_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '_ROMs.json')
        # kodi_busydialog_ON()
        # SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
        # SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
        # assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        # SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        # SL_asset_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
        # kodi_busydialog_OFF()
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
        _display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_SL_ROM_DB_data']:
            log_info('Writing file "{0}"'.format(PATHS.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH.getPath()))
            with open(PATHS.REPORT_DEBUG_SL_ITEM_ROM_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View SL ROM Audit ROMs ---
    elif action == ACTION_VIEW_SL_ROM_AUDIT_ROMS:
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '.json')
        # SL_ROMs_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '_roms.json')
        SL_ROM_Audit_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '_ROM_audit.json')

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
        _display_text_window(window_title, '\n'.join(info_text))

        # --- Write DEBUG TXT file ---
        if g_settings['debug_SL_Audit_DB_data']:
            log_info('Writing file "{0}"'.format(PATHS.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH.getPath()))
            with open(PATHS.REPORT_DEBUG_SL_ITEM_AUDIT_DATA_PATH.getPath(), 'w') as file:
                text_remove_color_tags_slist(info_text)
                file.write('\n'.join(info_text).encode('utf-8'))

    # --- View MAME stdout/stderr ---
    elif action == ACTION_VIEW_EXEC_OUTPUT:
        if not PATHS.MAME_OUTPUT_PATH.exists():
            kodi_dialog_OK('MAME output file not found. Execute MAME and try again.')
            return

        # --- Read stdout and put into a string ---
        window_title = 'MAME last execution output'
        info_text = ''
        with open(PATHS.MAME_OUTPUT_PATH.getPath(), 'r') as myfile:
            info_text = myfile.read()
        _display_text_window(window_title, info_text)

    # --- Audit ROMs of a single machine ---
    elif action == ACTION_AUDIT_MAME_MACHINE:
        # --- Load machine dictionary and ROM database ---
        rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][g_settings['mame_rom_set']]
        log_debug('_command_context_view() Auditing Machine ROMs\n')
        log_debug('_command_context_view() rom_set {0}\n'.format(rom_set))

        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 2
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machine hash')
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME ROM Audit')
        audit_roms_dic = fs_load_JSON_file_dic(PATHS.ROM_AUDIT_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Grab data and settings ---
        rom_list = audit_roms_dic[machine_name]
        cloneof = machine['cloneof']
        romof = machine['romof']
        log_debug('_command_context_view() machine {0}\n'.format(machine_name))
        log_debug('_command_context_view() cloneof {0}\n'.format(cloneof))
        log_debug('_command_context_view() romof   {0}\n'.format(romof))

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
        _display_text_window(window_title, '\n'.join(info_text))

    # --- Audit ROMs of SL item ---
    elif action == ACTION_AUDIT_SL_MACHINE:
        # --- Load machine dictionary and ROM database ---
        log_debug('_command_context_view() Auditing SL Software ROMs\n')
        log_debug('_command_context_view() SL_name {0}\n'.format(SL_name))
        log_debug('_command_context_view() SL_ROM {0}\n'.format(SL_ROM))

        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '.json')
        SL_ROM_Audit_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '_ROM_audit.json')

        roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
        roms_audit_db = fs_load_JSON_file_dic(SL_ROM_Audit_DB_FN.getPath())
        rom = roms[SL_ROM]
        rom_db_list = roms_audit_db[SL_ROM]

        # --- Open ZIP file and check CRC32 ---
        audit_dic = fs_new_audit_dic()
        mame_audit_SL_machine(g_settings, rom_db_list, audit_dic)

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
        _display_text_window(window_title, '\n'.join(info_text))

    # --- View ROM scanner reports ---
    elif action == ACTION_VIEW_REPORT_SCANNER:
        d = xbmcgui.Dialog()
        type_sub = d.select('View scanner reports',
                            ['View Full MAME machines archives',
                             'View Have MAME machines archives',
                             'View Missing MAME machines archives',
                             'View Missing MAME ROM list',
                             'View Missing MAME CHD list',
                             'View Full MAME Samples report',
                             'View Have MAME Samples report',
                             'View Missing MAME Samples report',
                             'View Full Software Lists item archives',
                             'View Have Software Lists item archives',
                             'View Missing Software Lists item archives',
                             'View Missing Software Lists ROM list',
                             'View Missing Software Lists CHD list',
                             'View MAME asset report',
                             'View Software Lists asset report'])
        if type_sub < 0: return

        # >> Kodi BUG: if size of file is 0 then previous text in window is rendered.
        # >> Solution: report files are never empty. Always print a text header in the report.

        # --- View Full MAME machines archives ---
        if type_sub == 0:
            if not PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.exists():
                kodi_dialog_OK('Full MAME machines archives scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), 'r') as myfile:
                _display_text_window('Full MAME machines archives scanner report', myfile.read())

        # --- View Have MAME machines archives ---
        elif type_sub == 1:
            if not PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.exists():
                kodi_dialog_OK('Have MAME machines archives scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), 'r') as myfile:
                _display_text_window('Have MAME machines archives scanner report', myfile.read())

        # --- View Missing MAME machines archives ---
        elif type_sub == 2:
            if not PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.exists():
                kodi_dialog_OK('Missing MAME machines archives scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing MAME machines archives scanner report', myfile.read())

        # --- View Missing MAME ROM list ---
        elif type_sub == 3:
            if not PATHS.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.exists():
                kodi_dialog_OK('Missing MAME ROM list scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing MAME ROM list scanner report', myfile.read())

        # --- View Missing MAME CHD list ---
        elif type_sub == 4:
            if not PATHS.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.exists():
                kodi_dialog_OK('Missing MAME CHD list scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing MAME CHD list scanner report', myfile.read())

        # --- View Full MAME Samples report ---
        elif type_sub == 5:
            if not PATHS.REPORT_MAME_SCAN_SAMP_FULL_PATH.exists():
                kodi_dialog_OK('Full MAME Samples report scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_SAMP_FULL_PATH.getPath(), 'r') as myfile:
                _display_text_window('Full MAME Samples report scanner report', myfile.read())

        # --- View Have MAME Samples report ---
        elif type_sub == 6:
            if not PATHS.REPORT_MAME_SCAN_SAMP_HAVE_PATH.exists():
                kodi_dialog_OK('Have MAME Samples scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_SAMP_HAVE_PATH.getPath(), 'r') as myfile:
                _display_text_window('Have MAME Samples scanner report', myfile.read())

        # --- View Missing MAME Samples report ---
        elif type_sub == 7:
            if not PATHS.REPORT_MAME_SCAN_SAMP_MISS_PATH.exists():
                kodi_dialog_OK('Missing MAME Samples scanner report not found. '
                               'Please scan MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_SCAN_SAMP_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing MAME Samples scanner report', myfile.read())

        # --- View Full Software Lists item archives ---
        elif type_sub == 8:
            if not PATHS.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.exists():
                kodi_dialog_OK('Full Software Lists item archives scanner report not found. '
                               'Please scan SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), 'r') as myfile:
                _display_text_window('Full Software Lists item archives scanner report', myfile.read())

        # --- View Have Software Lists item archives ---
        elif type_sub == 9:
            if not PATHS.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.exists():
                kodi_dialog_OK('Have Software Lists item archives scanner report not found. '
                               'Please scan SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), 'r') as myfile:
                _display_text_window('Have Software Lists item archives scanner report', myfile.read())

        # --- View Missing Software Lists item archives ---
        elif type_sub == 10:
            if not PATHS.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.exists():
                kodi_dialog_OK('Missing Software Lists item archives scanner report not found. '
                               'Please scan SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing Software Lists item archives scanner report', myfile.read())

        # --- View Missing Software Lists ROM list ---
        elif type_sub == 11:
            if not PATHS.REPORT_SL_SCAN_ROM_LIST_MISS_PATH.exists():
                kodi_dialog_OK('Missing Software Lists ROM list scanner report not found. '
                               'Please scan SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_SCAN_ROM_LIST_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing Software Lists ROM list scanner report', myfile.read())

        # --- View Missing Software Lists CHD list ---
        elif type_sub == 12:
            if not PATHS.REPORT_SL_SCAN_CHD_LIST_MISS_PATH.exists():
                kodi_dialog_OK('Missing Software Lists CHD list scanner report not found. '
                               'Please scan SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_SCAN_CHD_LIST_MISS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Missing Software Lists CHD list scanner report', myfile.read())

        # --- View MAME asset report ---
        elif type_sub == 13:
            if not PATHS.REPORT_MAME_ASSETS_PATH.exists():
                kodi_dialog_OK('MAME asset report report not found. '
                               'Please scan MAME assets and try again.')
                return
            with open(PATHS.REPORT_MAME_ASSETS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME asset report', myfile.read())

        # --- View Software Lists asset report ---
        elif type_sub == 14:
            if not PATHS.REPORT_SL_ASSETS_PATH.exists():
                kodi_dialog_OK('Software Lists asset report not found. '
                               'Please scan Software List assets and try again.')
                return
            with open(PATHS.REPORT_SL_ASSETS_PATH.getPath(), 'r') as myfile:
                _display_text_window('Software Lists asset report', myfile.read())

    # --- View audit reports ---
    elif action == ACTION_VIEW_REPORT_AUDIT:
        d = xbmcgui.Dialog()
        type_sub = d.select('View audit reports',
                            ['View MAME audit report (Full)',
                             'View MAME audit report (Good)',
                             'View MAME audit report (Errors)',
                             'View MAME audit report (ROMs Good)',
                             'View MAME audit report (ROM Errors)',
                             'View MAME audit report (Samples Good)',
                             'View MAME audit report (Sample Errors)',
                             'View MAME audit report (CHDs Good)',
                             'View MAME audit report (CHD Errors)',
                             'View SL audit report (Full)',
                             'View SL audit report (Good)',
                             'View SL audit report (Errors)',
                             'View SL audit report (ROM Good)',
                             'View SL audit report (ROM Errors)',
                             'View SL audit report (CHD Good)',
                             'View SL audit report (CHD Errors)'
                             ])
        if type_sub < 0: return

        # >> MAME audit reports
        if type_sub == 0:
            if not PATHS.REPORT_MAME_AUDIT_FULL_PATH.exists():
                kodi_dialog_OK('MAME audit report (Full) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_FULL_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (Full)', myfile.read())

        elif type_sub == 1:
            if not PATHS.REPORT_MAME_AUDIT_GOOD_PATH.exists():
                kodi_dialog_OK('MAME audit report (Good) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (Good)', myfile.read())

        elif type_sub == 2:
            if not PATHS.REPORT_MAME_AUDIT_ERRORS_PATH.exists():
                kodi_dialog_OK('MAME audit report (Errors) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (Errors)', myfile.read())

        elif type_sub == 3:
            if not PATHS.REPORT_MAME_AUDIT_ROM_GOOD_PATH.exists():
                kodi_dialog_OK('MAME audit report (ROMs Good) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_ROM_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (ROMs Good)', myfile.read())

        elif type_sub == 4:
            if not PATHS.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.exists():
                kodi_dialog_OK('MAME audit report (ROM Errors) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (ROM Errors)', myfile.read())

        elif type_sub == 5:
            if not PATHS.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.exists():
                kodi_dialog_OK('MAME audit report (Samples Good) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (Samples Good)', myfile.read())

        elif type_sub == 6:
            if not PATHS.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.exists():
                kodi_dialog_OK('MAME audit report (Sample Errors) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (Sample Errors)', myfile.read())

        elif type_sub == 7:
            if not PATHS.REPORT_MAME_AUDIT_CHD_GOOD_PATH.exists():
                kodi_dialog_OK('MAME audit report (CHDs Good) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_CHD_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (CHDs Good)', myfile.read())

        elif type_sub == 8:
            if not PATHS.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.exists():
                kodi_dialog_OK('MAME audit report (CHD Errors) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (CHD Errors)', myfile.read())

        # >> SL audit reports
        elif type_sub == 9:
            if not PATHS.REPORT_SL_AUDIT_FULL_PATH.exists():
                kodi_dialog_OK('SL audit report (Full) not found. '
                               'Please audit your SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_FULL_PATH.getPath(), 'r') as myfile:
                _display_text_window('SL audit report (Full)', myfile.read())

        elif type_sub == 10:
            if not PATHS.REPORT_SL_AUDIT_GOOD_PATH.exists():
                kodi_dialog_OK('SL audit report (Good) not found. '
                               'Please audit your SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('SL audit report (Good)', myfile.read())

        elif type_sub == 11:
            if not PATHS.REPORT_SL_AUDIT_ERRORS_PATH.exists():
                kodi_dialog_OK('SL audit report (Errors) not found. '
                               'Please audit your SL ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('SL audit report (Errors)', myfile.read())

        elif type_sub == 12:
            if not PATHS.REPORT_SL_AUDIT_ROMS_GOOD_PATH.exists():
                kodi_dialog_OK('MAME audit report (ROM Good) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_ROMS_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (ROM Good)', myfile.read())

        elif type_sub == 13:
            if not PATHS.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.exists():
                kodi_dialog_OK('MAME audit report (ROM Errors) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (ROM Errors)', myfile.read())

        elif type_sub == 14:
            if not PATHS.REPORT_SL_AUDIT_CHDS_GOOD_PATH.exists():
                kodi_dialog_OK('MAME audit report (CHD Good) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_CHDS_GOOD_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (CHD Good)', myfile.read())

        elif type_sub == 15:
            if not PATHS.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.exists():
                kodi_dialog_OK('MAME audit report (CHD Errors) not found. '
                               'Please audit your MAME ROMs and try again.')
                return
            with open(PATHS.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.getPath(), 'r') as myfile:
                _display_text_window('MAME audit report (CHD Errors)', myfile.read())

    else:
        kodi_dialog_OK('Wrong action == {0}. This is a bug, please report it.'.format(action))

def _command_context_utilities(catalog_name, category_name):
    log_debug('_command_context_utilities() catalog_name  "{0}"'.format(catalog_name))
    log_debug('_command_context_utilities() category_name "{0}"'.format(category_name))

    d_list = [
      'Export AEL Virtual Launcher',
    ]
    selected_value = xbmcgui.Dialog().select('View', d_list)
    if selected_value < 0: return

    # --- Export AEL Virtual Launcher ---
    if selected_value == 0:
        log_debug('_command_context_utilities() Export AEL Virtual Launcher')

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
        catalog_dic = fs_get_cataloged_dic_parents(PATHS, catalog_name)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME machine Assets')
        assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Print error message is something goes wrong writing file ---
        try:
            fs_export_Virtual_Launcher(export_FN, catalog_dic[category_name],
                                       machines, machines_render, assets_dic)
        except Addon_Error as ex:
            kodi_notify_warn('{0}'.format(ex))
        else:
            kodi_notify('Exported Virtual Launcher "{0}"'.format(vlauncher_str_name))

# ---------------------------------------------------------------------------------------------
# Favourites
# ---------------------------------------------------------------------------------------------
# >> Favourites use the main hashed database, not the main and render databases.
def _command_context_add_mame_fav(machine_name):
    log_debug('_command_add_mame_fav() Machine_name "{0}"'.format(machine_name))

    # >> Get Machine database entry
    kodi_busydialog_ON()
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    machine = fs_get_machine_main_db_hash(PATHS, machine_name)
    assets = fs_get_machine_assets_db_hash(PATHS, machine_name)
    kodi_busydialog_OFF()

    # >> Open Favourite Machines dictionary
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    
    # >> If machine already in Favourites ask user if overwrite.
    if machine_name in fav_machines:
        ret = kodi_dialog_yesno('Machine {0} ({1}) '.format(machine['description'], machine_name) +
                                'already in MAME Favourites. Overwrite?')
        if ret < 1: return

    # >> Add machine. Add database version to Favourite.
    fav_machine = fs_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic)
    fav_machines[machine_name] = fav_machine
    log_info('_command_add_mame_fav() Added machine "{0}"'.format(machine_name))

    # >> Save Favourites
    fs_write_JSON_file(PATHS.FAV_MACHINES_PATH.getPath(), fav_machines)
    kodi_notify('Machine {0} added to MAME Favourites'.format(machine_name))
    kodi_refresh_container()

#
# Context menu "Manage Favourite machines"
#   * UNIMPLEMENTED. IS IT USEFUL?
#     'Scan all ROMs/CHDs/Samples'
#     Scan Favourite machines ROM ZIPs and CHDs and update flags of the Favourites 
#     database JSON.
#
#   * UNIMPLEMENTED. IS IT USEFUL?
#     'Scan all assets/artwork'
#     Scan Favourite machines assets/artwork and update MAME Favourites database JSON.
#
#   * 'Check/Update all MAME Favourites'
#     Checks that all MAME Favourite machines exist in current database. If the ROM exists,
#     then update information from current MAME database. If the machine doesn't exist, then
#     delete it from MAME Favourites (prompt the user about this).
#
#   * 'Delete machine from MAME Favourites'
#
def _command_context_manage_mame_fav(machine_name):
    dialog = xbmcgui.Dialog()
    if machine_name:
        idx = dialog.select('Manage MAME Favourites',
                           ['Check/Update all MAME Favourites',
                            'Delete machine from MAME Favourites'])
    else:
        idx = dialog.select('Manage MAME Favourites',
                           ['Check/Update all MAME Favourites'])
    if idx < 0: return

    # --- Check/Update all MAME Favourites ---
    # >> Check if Favourites can be found in current MAME main database. It may happen that
    # >> a machine is renamed between MAME version although I think this is very unlikely.
    # >> MAME Favs can not be relinked. If the machine is not found in current database it must
    # >> be deleted by the user and a new Favourite created.
    # >> If the machine is found in the main database, then update the Favourite database
    # >> with data from the main database.
    if idx == 0:
        # --- Load databases ---
        pDialog = xbmcgui.DialogProgress()
        num_items = 4
        pDialog.create('Advanced MAME Launcher')
        line1_str = 'Loading databases ...'
        pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine Assets')
        assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Check/Update MAME Favourite machines ---
        mame_update_MAME_Fav_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog)

        # >> Save MAME Favourites DB
        kodi_refresh_container()
        kodi_notify('MAME Favourite checked and updated')

    # --- Delete machine from MAME Favourites ---
    elif idx == 1:
        log_debug('_command_context_manage_mame_fav() Delete MAME Favourite machine')
        log_debug('_command_context_manage_mame_fav() Machine_name "{0}"'.format(machine_name))

        # >> Open Favourite Machines dictionary
        fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())

        # >> Ask user for confirmation.
        desc = fav_machines[machine_name]['description']
        ret = kodi_dialog_yesno('Delete Machine {0} ({1})?'.format(desc, machine_name))
        if ret < 1: return

        # >> Delete machine
        del fav_machines[machine_name]
        log_info('_command_context_manage_mame_fav() Deleted machine "{0}"'.format(machine_name))

        # >> Save Favourites
        fs_write_JSON_file(PATHS.FAV_MACHINES_PATH.getPath(), fav_machines)
        kodi_refresh_container()
        kodi_notify('Machine {0} deleted from MAME Favourites'.format(machine_name))

def _command_show_mame_fav():
    log_debug('_command_show_mame_fav() Starting ...')

    # >> Open Favourite Machines dictionary
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    if not fav_machines:
        kodi_dialog_OK('No Favourite MAME machines. Add some machines to MAME Favourites first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render Favourites
    _set_Kodi_all_sorting_methods()
    for m_name in fav_machines:
        machine = fav_machines[m_name]
        assets  = machine['assets']
        _render_fav_machine_row(m_name, machine, assets, LOCATION_MAME_FAVS)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_fav_machine_row(m_name, machine, m_assets, location):
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
    poster_path    = m_assets['flyer']

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
    listitem.setArt({'title'     : m_assets['title'],   'snap'    : m_assets['snap'],
                     'boxfront'  : m_assets['cabinet'], 'boxback' : m_assets['cpanel'],
                     'cartridge' : m_assets['PCB'],     'flyer'   : m_assets['flyer'],
                     'icon'      : icon_path,           'fanart'    : fanart_path,
                     'banner'    : banner_path,         'clearlogo' : clearlogo_path,
                     'poster'    : poster_path})

    # --- ROM flags (Skins will use these flags to render icons) ---
    listitem.setProperty(AEL_PCLONE_STAT_LABEL, AEL_PClone_stat_value)

    # --- Create context menu ---
    URL_view_DAT = _misc_url_3_arg_RunPlugin('command', 'VIEW_DAT', 'machine', m_name, 'location', location)
    URL_view = _misc_url_3_arg_RunPlugin('command', 'VIEW', 'machine', m_name, 'location', location)
    if location == LOCATION_MAME_FAVS:
        URL_manage = _misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_FAV', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Favourites', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    elif location == LOCATION_MAME_MOST_PLAYED:
        URL_manage = _misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_MOST_PLAYED', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Most Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    elif location == LOCATION_MAME_RECENT_PLAYED:
        URL_manage = _misc_url_2_arg_RunPlugin('command', 'MANAGE_MAME_RECENT_PLAYED', 'machine', m_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage Recently Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_3_arg('command', 'LAUNCH', 'machine', m_name, 'location', location)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)

def _command_context_add_sl_fav(SL_name, ROM_name):
    log_debug('_command_add_sl_fav() SL_name  "{0}"'.format(SL_name))
    log_debug('_command_add_sl_fav() ROM_name "{0}"'.format(ROM_name))

    # --- Load databases ---
    kodi_busydialog_ON()
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '.json'
    SL_DB_FN = PATHS.SL_DB_DIR.pjoin(file_name)
    SL_roms = fs_load_JSON_file_dic(SL_DB_FN.getPath())
    assets_file_name =  SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
    SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
    SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())
    kodi_busydialog_OFF()

    # >> Open Favourite Machines dictionary
    fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
    SL_fav_key = SL_name + '-' + ROM_name
    log_debug('_command_add_sl_fav() SL_fav_key "{0}"'.format(SL_fav_key))

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
    log_info('_command_add_sl_fav() Added machine "{0}" ("{1}")'.format(ROM_name, SL_name))

    # >> Save Favourites
    fs_write_JSON_file(PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
    kodi_notify('ROM {0} added to SL Favourite ROMs'.format(ROM_name))

#
# Context menu "Manage SL Favourite ROMs"
#   * 'Choose default machine for SL ROM'
#      Allows to set the default machine to launch each SL ROM.
#
#   * (UNIMPLEMENTED, IS IT USEFUL?)
#     'Scan all SL Favourite ROMs/CHDs'
#      Scan SL ROM ZIPs and CHDs and update flags of the SL Favourites database JSON.
#
#   * (UNIMPLEMENTED, IS IT USEFUL?)
#     'Scan all SL Favourite assets/artwork'
#      Scan SL ROMs assets/artwork and update SL Favourites database JSON.
#
#   * 'Check/Update all SL Favourites ROMs'
#      Checks that all SL Favourite ROMs exist in current database. If the ROM exists,
#      then update information from current SL database. If the ROM doesn't exist, then
#      delete it from SL Favourites (prompt the user about this).
#
#   * 'Delete ROM from SL Favourites'
#
def _command_context_manage_sl_fav(SL_name, ROM_name):
    dialog = xbmcgui.Dialog()
    if SL_name and ROM_name:
        idx = dialog.select('Manage Software Lists Favourites',
                           ['Check/Update all SL Favourite items',
                            'Choose default machine for SL item',
                            'Delete ROM from SL Favourites'])
    else:
        idx = dialog.select('Manage Software Lists Favourites',
                           ['Check/Update all SL Favourites items'])
    if idx < 0: return

    # --- Check/Update SL Favourites ---
    if idx == 0:
        # --- Load databases ---
        pDialog = xbmcgui.DialogProgress()
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

        # --- Check/Update SL Favourite ROMs ---
        mame_update_SL_Fav_objects(PATHS, control_dic, SL_catalog_dic, pDialog)

        # --- Notify user ---
        kodi_refresh_container()
        kodi_notify('SL Favourite ROMs checked and updated')

    # --- Choose default machine for SL ROM ---
    elif idx == 1:
        # >> Load Favs
        fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name

        # >> Get a list of machines that can launch this SL ROM. User chooses.
        SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
        SL_machine_list = SL_machines_dic[SL_name]
        SL_machine_names_list = []
        SL_machine_desc_list = []
        SL_machine_names_list.append('')
        SL_machine_desc_list.append('[ Not set ]')
        for SL_machine in SL_machine_list: 
            SL_machine_names_list.append(SL_machine['machine'])
            SL_machine_desc_list.append(SL_machine['description'])
        # >> Krypton feature: preselect current machine
        pre_idx = SL_machine_names_list.index(fav_SL_roms[SL_fav_key]['launch_machine'])
        if pre_idx < 0: pre_idx = 0
        dialog = xbmcgui.Dialog()
        m_index = dialog.select('Select machine', SL_machine_desc_list, preselect = pre_idx)
        if m_index < 0 or m_index == pre_idx: return
        machine_name = SL_machine_names_list[m_index]
        machine_desc = SL_machine_desc_list[m_index]

        # >> Edit and save
        fav_SL_roms[SL_fav_key]['launch_machine'] = machine_name
        fs_write_JSON_file(PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        kodi_notify('Deafult machine set to {0} ({1})'.format(machine_name, machine_desc))

    # --- Delete ROM from SL Favourites ---
    elif idx == 2:
        log_debug('_command_context_manage_sl_fav() Delete SL Favourite ROM')
        log_debug('_command_context_manage_sl_fav() SL_name  "{0}"'.format(SL_name))
        log_debug('_command_context_manage_sl_fav() ROM_name "{0}"'.format(ROM_name))

        # >> Open Favourite Machines dictionary
        fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('_command_delete_sl_fav() SL_fav_key "{0}"'.format(SL_fav_key))

        # >> Ask user for confirmation.
        desc = most_played_roms_dic[SL_fav_key]['description']
        a = 'Delete SL Item {0} ({1} / {2})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1: return

        # >> Delete machine
        del fav_SL_roms[SL_fav_key]
        log_info('_command_delete_sl_fav() Deleted machine {0} ({1})'.format(SL_name, ROM_name))

        # >> Save Favourites
        fs_write_JSON_file(PATHS.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
        kodi_refresh_container()
        kodi_notify('SL Item {0}-{1} deleted from SL Favourites'.format(SL_name, ROM_name))

def _command_show_sl_fav():
    log_debug('_command_show_sl_fav() Starting ...')

    # >> Load Software List ROMs
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

    # >> Open Favourite Machines dictionary
    fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
    if not fav_SL_roms:
        kodi_dialog_OK('No Favourite Software Lists ROMs. Add some ROMs to SL Favourites first.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render Favourites
    _set_Kodi_all_sorting_methods()
    for SL_fav_key in fav_SL_roms:
        SL_fav_ROM = fav_SL_roms[SL_fav_key]
        assets = SL_fav_ROM['assets']
        # >> Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        _render_sl_fav_machine_row(SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_FAVS)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_sl_fav_machine_row(SL_fav_key, ROM, assets, location):
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
    poster_path = assets['boxfront']

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
    listitem.setArt({'title' : assets['title'], 'snap' : assets['snap'], 'boxfront' : assets['boxfront'],
                     'icon' : icon_path, 'fanart' : fanart_path, 'poster' : poster_path})

    # --- Create context menu ---
    URL_view_DAT = _misc_url_4_arg_RunPlugin('command', 'VIEW_DAT', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    URL_view = _misc_url_4_arg_RunPlugin('command', 'VIEW', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    if location == LOCATION_SL_FAVS:
        URL_manage = _misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_FAV', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils', URL_view_DAT),
            ('View / Audit', URL_view),
            ('Manage SL Favourites', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__)),
        ]
    elif location == LOCATION_SL_MOST_PLAYED:
        URL_manage = _misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_MOST_PLAYED', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage SL Most Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    elif location == LOCATION_SL_RECENT_PLAYED:
        URL_manage = _misc_url_3_arg_RunPlugin('command', 'MANAGE_SL_RECENT_PLAYED', 'SL', SL_name, 'ROM', SL_ROM_name)
        commands = [
            ('Info / Utils',  URL_view_DAT),
            ('View / Audit',  URL_view),
            ('Manage SL Recently Played', URL_manage),
            ('Kodi File Manager', 'ActivateWindow(filemanager)'),
            ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
        ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_4_arg('command', 'LAUNCH_SL', 'SL', SL_name, 'ROM', SL_ROM_name, 'location', location)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = False)

# ---------------------------------------------------------------------------------------------
# Most/Recently Played MAME/SL machines/SL items
# ---------------------------------------------------------------------------------------------
def _command_show_mame_most_played():
    most_played_roms_dic = fs_load_JSON_file_dic(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if not most_played_roms_dic:
        kodi_dialog_OK('No Most Played MAME machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    _set_Kodi_unsorted_method()
    sorted_dic = sorted(most_played_roms_dic, key = lambda x : most_played_roms_dic[x]['launch_count'], reverse = True)
    for machine_name in sorted_dic:
        machine = most_played_roms_dic[machine_name]
        _render_fav_machine_row(machine['name'], machine, machine['assets'], LOCATION_MAME_MOST_PLAYED)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _command_context_manage_mame_most_played(machine_name):
    dialog = xbmcgui.Dialog()
    if machine_name:
        idx = dialog.select('Manage MAME Most Played', 
                           ['Check/Update all MAME Most Played machines',
                            'Delete machine from MAME Most Played machines'])
    else:
        idx = dialog.select('Manage MAME Most Played', 
                           ['Check/Update all MAME Most Played machines'])
    if idx < 0: return

    # --- Check/Update all MAME Most Played machines ---
    if idx == 0:
        pDialog = xbmcgui.DialogProgress()
        line1_str = 'Loading databases ...'
        num_items = 4
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine Assets')
        assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Check/Update MAME Most Played machines ---
        mame_update_MAME_MostPlay_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog)

        # --- Save MAME Most Played machines DB ---
        kodi_refresh_container()
        kodi_notify('MAME Favourite checked and updated')

    # --- Delete machine from MAME Most Played machines ---
    elif idx == 1:
        log_debug('_command_context_manage_mame_most_played() Delete MAME machine')
        log_debug('_command_context_manage_mame_most_played() Machine_name "{0}"'.format(machine_name))

        # >> Load Most Played machines dictionary
        most_played_roms_dic = fs_load_JSON_file_dic(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())

        # >> Ask user for confirmation.
        desc = most_played_roms_dic[machine_name]['description']
        ret = kodi_dialog_yesno('Delete Machine {0} ({1})?'.format(desc, machine_name))
        if ret < 1: return

        # >> Delete machine
        del most_played_roms_dic[machine_name]
        log_info('_command_context_manage_mame_most_played() Deleted machine "{0}"'.format(machine_name))

        # >> Save Favourites
        fs_write_JSON_file(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
        kodi_refresh_container()
        kodi_notify('Machine {0} deleted from MAME Most Played'.format(machine_name))

def _command_show_mame_recently_played():
    recent_roms_list = fs_load_JSON_file_list(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    if not recent_roms_list:
        kodi_dialog_OK('No Recently Played MAME machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    _set_Kodi_unsorted_method()
    for machine in recent_roms_list:
        _render_fav_machine_row(machine['name'], machine, machine['assets'], LOCATION_MAME_RECENT_PLAYED)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _command_context_manage_mame_recent_played(machine_name):
    dialog = xbmcgui.Dialog()
    if machine_name:
        idx = dialog.select('Manage MAME Recently Played', 
                           ['Check/Update all MAME Recently Played machines',
                            'Delete machine from MAME Recently Played machines'])
    else:
        idx = dialog.select('Manage MAME Recently Played', 
                           ['Check/Update all MAME Recently Played machines'])
    if idx < 0: return

    # --- Check/Update all MAME Recently Played machines ---
    if idx == 0:
        # --- Load databases ---
        pDialog = xbmcgui.DialogProgress()
        line1_str = 'Loading databases ...'
        num_items = 4
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine Assets')
        assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Check/Update MAME Recently Played machines ---
        mame_update_MAME_RecentPlay_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog)

        # --- Save MAME Favourites DB ---
        kodi_refresh_container()
        kodi_notify('MAME Recently Played machines checked and updated')

    # --- Delete machine from MAME Recently Played machine list ---
    elif idx == 1:
        log_debug('_command_context_manage_mame_recent_played() Delete MAME Recently Played machine')
        log_debug('_command_context_manage_mame_recent_played() Machine_name "{0}"'.format(machine_name))

        # >> Load Recently Played machine list
        recent_roms_list = fs_load_JSON_file_list(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())

        # >> Search index of this machine in the list
        machine_index = fs_locate_idx_by_name(recent_roms_list, machine_name)
        if machine_index < 0:
            a = 'Machine {0} cannot be located in Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(machine_name))
            return

        # >> Ask user for confirmation.
        desc = recent_roms_list[machine_index]['description']
        ret = kodi_dialog_yesno('Delete Machine {0} ({1})?'.format(desc, machine_name))
        if ret < 1: return

        # >> Delete machine
        recent_roms_list.pop(machine_index)
        log_info('_command_context_manage_mame_recent_played() Deleted machine "{0}"'.format(machine_name))

        # >> Save Recently Played machine list
        fs_write_JSON_file(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        kodi_refresh_container()
        kodi_notify('Machine {0} deleted from MAME Recently Played'.format(machine_name))

def _command_show_SL_most_played():
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    most_played_roms_dic = fs_load_JSON_file_dic(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
    if not most_played_roms_dic:
        kodi_dialog_OK('No Most Played SL machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    _set_Kodi_unsorted_method()
    sorted_dic = sorted(most_played_roms_dic, key = lambda x : most_played_roms_dic[x]['launch_count'], reverse = True)
    for SL_fav_key in sorted_dic:
        SL_fav_ROM = most_played_roms_dic[SL_fav_key]
        assets = SL_fav_ROM['assets']
        # >> Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        _render_sl_fav_machine_row(SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_MOST_PLAYED)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _command_context_manage_SL_most_played(SL_name, ROM_name):
    dialog = xbmcgui.Dialog()
    if SL_name and ROM_name:
        idx = dialog.select('Manage SL Most Played items', 
                           ['Check/Update all SL Most Played items',
                            'Delete machine from SL Most Played items'])
    else:
        idx = dialog.select('Manage SL Most Played items', 
                           ['Check/Update all SL Most Played items'])
    if idx < 0: return

    # --- Check/Update all SL Most Played items ---
    if idx == 0:
        # --- Load databases ---
        pDialog = xbmcgui.DialogProgress()
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

        # --- Check/Update SL Favourite ROMs ---
        mame_update_SL_MostPlay_objects(PATHS, control_dic, SL_catalog_dic, pDialog)

        # --- Save MAME Most Played items DB ---
        kodi_refresh_container()
        kodi_notify('SL Most Played items checked and updated')

    # --- Delete machine from SL Most Played items ---
    elif idx == 1:
        log_debug('_command_context_manage_sl_most_played() Delete SL Most Played machine')
        log_debug('_command_context_manage_sl_most_played() SL_name  "{0}"'.format(SL_name))
        log_debug('_command_context_manage_sl_most_played() ROM_name "{0}"'.format(ROM_name))

        # >> Load Most Played items dictionary
        most_played_roms_dic = fs_load_JSON_file_dic(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_key = SL_name + '-' + ROM_name
        log_debug('_command_context_manage_sl_most_played() SL_fav_key "{0}"'.format(SL_fav_key))

        # >> Ask user for confirmation.
        desc = most_played_roms_dic[SL_fav_key]['description']
        a = 'Delete SL Item {0} ({1} / {2})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1: return

        # >> Delete machine
        del most_played_roms_dic[SL_fav_key]
        a = '_command_context_manage_sl_most_played() Deleted SL_name "{0}" / ROM_name "{1}"'
        log_info(a.format(SL_name, ROM_name))

        # >> Save Favourites
        fs_write_JSON_file(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
        kodi_refresh_container()
        kodi_notify('SL Item {0}-{1} deleted from SL Most Played'.format(SL_name, ROM_name))

def _command_show_SL_recently_played():
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    recent_roms_list = fs_load_JSON_file_list(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
    if not recent_roms_list:
        kodi_dialog_OK('No Recently Played SL machines. Play a bit and try later.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    _set_Kodi_unsorted_method()
    for SL_fav_ROM in recent_roms_list:
        SL_fav_key = SL_fav_ROM['SL_DB_key']
        assets = SL_fav_ROM['assets']
        # >> Add the SL name as 'genre'
        SL_name = SL_fav_ROM['SL_name']
        SL_fav_ROM['genre'] = SL_catalog_dic[SL_name]['display_name']
        _render_sl_fav_machine_row(SL_fav_key, SL_fav_ROM, assets, LOCATION_SL_RECENT_PLAYED)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _command_context_manage_SL_recent_played(SL_name, ROM_name):
    dialog = xbmcgui.Dialog()
    if SL_name and ROM_name:
        idx = dialog.select('Manage SL Recently Played items', 
                           ['Check/Update all SL Recently Played items',
                            'Delete machine from SL Recently Played items'])
    else:
        idx = dialog.select('Manage SL Recently Played', 
                           ['Check/Update all MAME Recently Played items'])
    if idx < 0: return

    # --- Check/Update all MAME Recently Played items ---
    if idx == 0:
        # --- Load databases ---
        pDialog = xbmcgui.DialogProgress()
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

        # --- Check/Update SL Favourite ROMs ---
        mame_update_SL_RecentPlay_objects(PATHS, control_dic, SL_catalog_dic, pDialog)

        # --- Save MAME Favourites DB ---
        kodi_refresh_container()
        kodi_notify('SL Recently Played items checked and updated')

    # --- Delete machine from MAME Recently Played machine list ---
    elif idx == 1:
        log_debug('_command_context_manage_SL_recent_played() Delete SL Recently Played machine')
        log_debug('_command_context_manage_SL_recent_played() SL_name  "{0}"'.format(SL_name))
        log_debug('_command_context_manage_SL_recent_played() ROM_name "{0}"'.format(ROM_name))

        # >> Load Recently Played machine list
        recent_roms_list = fs_load_JSON_file_list(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
        machine_index = fs_locate_idx_by_SL_item_name(recent_roms_list, SL_name, SL_ROM_name)
        if machine_index < 0:
            a = 'Item {0}-{1} cannot be located in SL Recently Played list. This is a bug.'
            kodi_dialog_OK(a.format(SL_name, ROM_name))
            return

        # >> Ask user for confirmation.
        desc = recent_roms_list[machine_index]['description']
        a = 'Delete SL Item {0} ({1} / {2})?'
        ret = kodi_dialog_yesno(a.format(desc, SL_name, ROM_name))
        if ret < 1: return

        # >> Delete machine
        recent_roms_list.pop(machine_index)
        a = '_command_context_manage_SL_recent_played() Deleted SL_name "{0}" / ROM_name "{1}"'
        log_info(a.format(SL_name, ROM_name))

        # >> Save Recently Played machine list
        fs_write_JSON_file(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
        kodi_refresh_container()
        kodi_notify('SL Item {0}-{1} deleted from SL Recently Played'.format(SL_name, ROM_name))

# ---------------------------------------------------------------------------------------------
# Custom MAME filters
# Custom filters behave like standard catalogs.
# Custom filters are defined in a XML file, the XML file is processed and the custom catalogs
# created from the main database.
# ---------------------------------------------------------------------------------------------
def _command_show_custom_filters():
    log_debug('_command_show_custom_filters() Starting ...')

    # >> Open Custom filter count database and index
    filter_index_dic = fs_load_JSON_file_dic(PATHS.FILTERS_INDEX_PATH.getPath())
    if not filter_index_dic:
        kodi_dialog_OK('MAME custom filter index is empty. Please rebuild your filters.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Check if filters need to be rebuilt
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if control_dic['t_Custom_Filter_build'] < control_dic['t_MAME_Catalog_build']:
        kodi_dialog_OK('MAME custom filters need to be rebuilt.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Render Custom Filters
    mame_view_mode = g_settings['mame_view_mode']
    _set_Kodi_all_sorting_methods()
    for f_name in sorted(filter_index_dic, key = lambda x: filter_index_dic[x]['order'], reverse = False):
        if mame_view_mode == VIEW_MODE_FLAT:
            num_machines = filter_index_dic[f_name]['num_machines']
            if num_machines == 1: machine_str = 'machine'
            else:                 machine_str = 'machines'
        elif mame_view_mode == VIEW_MODE_PCLONE:
            num_machines = filter_index_dic[f_name]['num_parents']
            if num_machines == 1: machine_str = 'parent'
            else:                 machine_str = 'parents'
        _render_custom_filter_item_row(f_name, num_machines, machine_str, filter_index_dic[f_name]['plot'])
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)

def _render_custom_filter_item_row(f_name, num_machines, machine_str, plot):
    # --- Create listitem row ---
    ICON_OVERLAY = 6
    title_str = '{0} [COLOR orange]({1} {2})[/COLOR]'.format(f_name, num_machines, machine_str)
    listitem = xbmcgui.ListItem(title_str)
    listitem.setInfo('video', {'title' : title_str, 'plot' : plot, 'overlay' : ICON_OVERLAY})

    # --- Artwork ---
    icon_path   = AML_ICON_FILE_PATH.getPath()
    fanart_path = AML_FANART_FILE_PATH.getPath()
    listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

    # --- Create context menu ---
    # >> Make a list of tuples
    commands = [
        ('Kodi File Manager', 'ActivateWindow(filemanager)'),
        ('AML addon settings', 'Addon.OpenSettings({0})'.format(__addon_id__))
    ]
    listitem.addContextMenuItems(commands)

    # --- Add row ---
    URL = _misc_url_2_arg('catalog', 'Custom', 'category', f_name)
    xbmcplugin.addDirectoryItem(handle = g_addon_handle, url = URL, listitem = listitem, isFolder = True)

#
# Renders a Parent or Flat machine list
#
def _render_custom_filter_machines_parents(filter_name):
    log_debug('_render_custom_filter_ROMs() filter_name  = {0}'.format(filter_name))

    # >> Global properties
    view_mode_property = g_settings['mame_view_mode']
    log_debug('_render_custom_filter_ROMs() view_mode_property = {0}'.format(view_mode_property))

    # >> Check id main DB exists
    if not PATHS.RENDER_DB_PATH.exists():
        kodi_dialog_OK('MAME database not found. Check out "Setup plugin" context menu.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # >> Load main MAME info DB and catalog
    l_cataloged_dic_start = time.time()
    Filters_index_dic = fs_load_JSON_file_dic(PATHS.FILTERS_INDEX_PATH.getPath())
    rom_DB_noext = Filters_index_dic[filter_name]['rom_DB_noext']
    if view_mode_property == VIEW_MODE_PCLONE:
        DB_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_parents.json')
        machines_dic = fs_load_JSON_file_dic(DB_FN.getPath())
    elif view_mode_property == VIEW_MODE_FLAT:
        DB_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_all.json')
        machines_dic = fs_load_JSON_file_dic(DB_FN.getPath())
    else:
        kodi_dialog_OK('Wrong view_mode_property = "{0}". '.format(view_mode_property) +
                       'This is a bug, please report it.')
        return
    l_cataloged_dic_end = time.time()
    l_render_db_start = time.time()
    render_db_dic = fs_load_JSON_file_dic(PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_ROMs.json').getPath())
    l_render_db_end = time.time()
    l_assets_db_start = time.time()
    assets_db_dic = fs_load_JSON_file_dic(PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_assets.json').getPath())
    l_assets_db_end = time.time()
    l_pclone_dic_start = time.time()
    main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
    l_pclone_dic_end = time.time()
    l_favs_start = time.time()
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    l_favs_end = time.time()

    # >> Compute loading times.
    catalog_t = l_cataloged_dic_end - l_cataloged_dic_start
    render_t = l_render_db_end - l_render_db_start
    assets_t = l_assets_db_end - l_assets_db_start
    pclone_t = l_pclone_dic_end - l_pclone_dic_start
    favs_t   = l_favs_end - l_favs_start
    loading_time = catalog_t + render_t + assets_t + pclone_t + favs_t

    # >> Check if catalog is empty
    if not machines_dic:
        kodi_dialog_OK('Catalog is empty. Check out "Setup plugin" context menu.')
        xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
        return

    # --- Process ROMs ---
    processing_ticks_start = time.time()
    catalog_name = 'Custom'
    category_name = filter_name
    catalog_dic = {category_name : machines_dic}
    r_list = _render_process_machines(catalog_dic, catalog_name, category_name,
                                      render_db_dic, assets_db_dic, main_pclone_dic, fav_machines,
                                      True, True)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    _set_Kodi_all_sorting_methods()
    _render_commit_machines(r_list)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()
    rendering_time = rendering_ticks_end - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    # log_debug('Loading catalog     {0:.4f} s'.format(catalog_t))
    log_debug('Loading render db   {0:.4f} s'.format(render_t))
    log_debug('Loading assets db   {0:.4f} s'.format(assets_t))
    # log_debug('Loading pclone dic  {0:.4f} s'.format(pclone_t))
    # log_debug('Loading MAME favs  {0:.4f} s'.format(favs_t))    
    log_debug('Loading             {0:.4f} s'.format(loading_time))
    log_debug('Rendering           {0:.4f} s'.format(rendering_ticks_end - rendering_ticks_start))

#
# No need to check for DB existance here. If this function is called is because parents and
# hence all ROMs databases exist.
#
def _render_custom_filter_machines_clones(filter_name, parent_name):
    log_debug('_render_custom_filter_clones() Starting ...')

    # >> Load main MAME info DB
    loading_ticks_start = time.time()
    Filters_index_dic = fs_load_JSON_file_dic(PATHS.FILTERS_INDEX_PATH.getPath())
    rom_DB_noext = Filters_index_dic[filter_name]['rom_DB_noext']
    catalog_dic = fs_load_JSON_file_dic(PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_all.json').getPath())
    render_db_dic = fs_load_JSON_file_dic(PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_ROMs.json').getPath())
    assets_db_dic = fs_load_JSON_file_dic(PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_assets.json').getPath())
    main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
    fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
    view_mode_property = g_settings['mame_view_mode']
    log_debug('_render_custom_filter_clones() view_mode_property = {0}'.format(view_mode_property))
    loading_ticks_end = time.time()
    loading_time = loading_ticks_end - loading_ticks_start

    # --- Process ROMs ---
    processing_ticks_start = time.time()
    catalog_name = 'Custom'
    machines_dic = catalog_dic
    t_catalog_dic = {}
    t_render_dic = {}
    t_assets_dic = {}
    # >> Render parent first
    t_catalog_dic[filter_name] = {parent_name : machines_dic[parent_name]}
    t_render_dic[parent_name] = render_db_dic[parent_name]
    t_assets_dic[parent_name] = assets_db_dic[parent_name]
    # >> Then clones
    for clone_name in main_pclone_dic[parent_name]:
        t_catalog_dic[filter_name][clone_name] = machines_dic[clone_name]
        t_render_dic[clone_name] = render_db_dic[clone_name]
        t_assets_dic[clone_name] = assets_db_dic[clone_name]
    r_list = _render_process_machines(t_catalog_dic, catalog_name, filter_name,
                                      t_render_dic, t_assets_dic, main_pclone_dic, fav_machines,
                                      False, True)
    processing_ticks_end = time.time()
    processing_time = processing_ticks_end - processing_ticks_start

    # --- Commit ROMs ---
    rendering_ticks_start = time.time()
    _set_Kodi_all_sorting_methods()
    _render_commit_machines(r_list)
    xbmcplugin.endOfDirectory(handle = g_addon_handle, succeeded = True, cacheToDisc = False)
    rendering_ticks_end = time.time()
    rendering_time = rendering_ticks_end - rendering_ticks_start

    # --- DEBUG Data loading/rendering statistics ---
    total_time = loading_time + processing_time + rendering_time
    log_debug('Loading     {0:.4f} s'.format(loading_time))
    log_debug('Processing  {0:.4f} s'.format(processing_time))
    log_debug('Rendering   {0:.4f} s'.format(rendering_time))
    log_debug('Total       {0:.4f} s'.format(total_time))

def _command_context_setup_custom_filters():
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Setup AML custom filters',
                             ['Build custom filter databases',
                              'View custom filter XML'])
    if menu_item < 0: return

    # --- Update custom filters ---
    # filter_index_dic = {
    #     'name' : {
    #         'display_name' : str,
    #         'num_machines' : int,
    #         'num_parents' : int,
    #         'order' : int,
    #         'plot' : str,
    #         'rom_DB_noext' : str,
    #     }
    # }
    #
    # AML_DATA_DIR/filters/'rom_DB_noext'_all.json -> machine_list = {
    #     'machine1' : 'display_name1', 'machine2' : 'display_name2', ...
    # }
    #
    # AML_DATA_DIR/filters/'rom_DB_noext'_parents.json -> machine_list = {
    #     'machine1' : 'display_name1', 'machine2' : 'display_name2', ...
    # }
    #
    # AML_DATA_DIR/filters/'rom_DB_noext'_ROMs.json -> machine_render = {}
    #
    # AML_DATA_DIR/filters/'rom_DB_noext'_assets.json -> asset_dic = {}
    #
    if menu_item == 0:
        # --- Open custom filter XML and parse it ---
        try:
            filters_list = filter_parse_XML(g_settings['filter_XML'])
        except Addon_Error as ex:
            kodi_notify_warn('{0}'.format(ex))
            return
        else:
            log_debug('Filter XML read succesfully.')

        # --- If no filters sayonara ---
        if len(filters_list) < 1:
            kodi_notify_warn('Filter XML has 0 filter definitions')
            return

        # --- Open main ROM databases ---
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False
        pdialog_line1 = 'Loading databases ...'
        num_items = 5
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'Machines Main')
        machine_main_dic = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'Machines Render')
        machine_render_dic = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'Machine assets')
        assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), pdialog_line1, 'Parent/Clone')
        main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
        pDialog.update(int((4*100) / num_items), pdialog_line1, 'Machine archives')
        machine_archives_dic = fs_load_JSON_file_dic(PATHS.ROM_SET_MACHINE_ARCHIVES_DB_PATH.getPath())
        pDialog.update(int((5*100) / num_items), pdialog_line1, ' ')
        pDialog.close()

        # --- Make a dictionary of objects to be filtered ---
        main_filter_dic = filter_get_filter_DB(machine_main_dic, machine_render_dic,
                                               assets_dic, main_pclone_dic, machine_archives_dic,
                                               pDialog)

        # --- Clean 'filters' directory JSON files ---
        log_info('Cleaning dir "{0}"'.format(PATHS.FILTERS_DB_DIR.getPath()))
        pDialog.create('Advanced MAME Launcher', 'Cleaning old filter JSON files ...')
        pDialog.update(0)
        file_list = os.listdir(PATHS.FILTERS_DB_DIR.getPath())
        num_files = len(file_list)
        if num_files < 1:
            log_info('Found {0} files'.format(num_files))
            processed_items = 0
            for file in file_list:
                pDialog.update((processed_items*100) // num_files)
                if file.endswith('.json'):
                    full_path = os.path.join(PATHS.FILTERS_DB_DIR.getPath(), file)
                    # log_debug('UNLINK "{0}"'.format(full_path))
                    os.unlink(full_path)
                processed_items += 1
        pDialog.update(100)
        pDialog.close()

        # --- Traverse list of filters, build filter index and compute filter list ---
        pdialog_line1 = 'Building custom MAME filters'
        pDialog.create('Advanced MAME Launcher', pdialog_line1)
        Filters_index_dic = {}
        total_items = len(filters_list)
        processed_items = 0
        for f_definition in filters_list:
            # --- Initialise ---
            f_name = f_definition['name']
            log_debug('_command_context_setup_custom_filters() Processing filter "{0}"'.format(f_name))
            # log_debug('f_definition = {0}'.format(unicode(f_definition)))

            # --- Initial progress ---
            pDialog.update((processed_items*100) // total_items, pdialog_line1, 'Filter "{0}" ...'.format(f_name))

            # --- Do filtering ---
            filtered_machine_dic = mame_filter_Default(main_filter_dic)
            filtered_machine_dic = mame_filter_Options_tag(filtered_machine_dic, f_definition)
            filtered_machine_dic = mame_filter_Driver_tag(filtered_machine_dic, f_definition)
            filtered_machine_dic = mame_filter_Manufacturer_tag(filtered_machine_dic, f_definition)
            filtered_machine_dic = mame_filter_Genre_tag(filtered_machine_dic, f_definition)
            filtered_machine_dic = mame_filter_Controls_tag(filtered_machine_dic, f_definition)
            filtered_machine_dic = mame_filter_Devices_tag(filtered_machine_dic, f_definition)
            filtered_machine_dic = mame_filter_Year_tag(filtered_machine_dic, f_definition)
            # >> filtered_machine_dic = mame_filter_Include_tag(filtered_machine_dic, f_definition)
            # >> filtered_machine_dic = mame_filter_Exclude_tag(filtered_machine_dic, f_definition)
            # >> filtered_machine_dic = mame_filter_Change_tag(filtered_machine_dic, f_definition)

            # --- Make indexed catalog ---
            filtered_machine_parents_dic = {}
            filtered_machine_all_dic = {}
            filtered_render_ROMs = {}
            filtered_assets_dic = {}
            for p_name in sorted(filtered_machine_dic.keys()):
                # >> Add parents
                filtered_machine_parents_dic[p_name] = machine_render_dic[p_name]['description']
                filtered_machine_all_dic[p_name] = machine_render_dic[p_name]['description']
                filtered_render_ROMs[p_name] = machine_render_dic[p_name]
                filtered_assets_dic[p_name] = assets_dic[p_name]
                # >> Add clones
                for c_name in main_pclone_dic[p_name]:
                    filtered_machine_all_dic[c_name] = machine_render_dic[c_name]['description']
                    filtered_render_ROMs[c_name] = machine_render_dic[c_name]
                    filtered_assets_dic[c_name] = assets_dic[c_name]
            rom_DB_noext = hashlib.md5(f_name).hexdigest()
            this_filter_idx_dic = {
                'display_name' : f_definition['name'],
                'num_parents'  : len(filtered_machine_parents_dic),
                'num_machines' : len(filtered_machine_all_dic),
                'order'        : processed_items,
                'plot'         : f_definition['plot'],
                'rom_DB_noext' : rom_DB_noext
            }
            Filters_index_dic[f_name] = this_filter_idx_dic

            # --- Save filter database ---
            writing_ticks_start = time.time()
            output_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_parents.json')
            fs_write_JSON_file(output_FN.getPath(), filtered_machine_parents_dic, verbose = False)
            output_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_all.json')
            fs_write_JSON_file(output_FN.getPath(), filtered_machine_all_dic, verbose = False)
            output_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_ROMs.json')
            fs_write_JSON_file(output_FN.getPath(), filtered_render_ROMs, verbose = False)
            output_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_assets.json')
            fs_write_JSON_file(output_FN.getPath(), filtered_assets_dic, verbose = False)
            writing_ticks_end = time.time()
            writing_time = writing_ticks_end - writing_ticks_start
            log_debug('JSON writing time {0:.4f} s'.format(writing_time))

            # --- Final progress ---
            processed_items += 1
        pDialog.update(100, pdialog_line1, ' ')
        pDialog.close()
        # >> Save custom filter index.
        fs_write_JSON_file(PATHS.FILTERS_INDEX_PATH.getPath(), Filters_index_dic)
        # >> Update timestamp
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        change_control_dic(control_dic, 't_Custom_Filter_build', time.time())
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        kodi_notify('Custom filter database built')

    # --- View custom filter XML ---
    elif menu_item == 1:
        XML_FN = FileName(g_settings['filter_XML'])
        log_debug('_command_context_setup_custom_filters() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
        log_debug('_command_context_setup_custom_filters() Reading XML  P "{0}"'.format(XML_FN.getPath()))
        if not XML_FN.exists():
            kodi_dialog_OK('Custom filter XML file not found.')
            return
        with open(XML_FN.getPath(), 'r') as myfile:
            info_text = myfile.read().decode('utf-8')
            _display_text_window('Custom filter XML', info_text)

# -------------------------------------------------------------------------------------------------
# Check AML status
# -------------------------------------------------------------------------------------------------
# This function checks if the database is OK and machines inside a Category can be rendered.
# This function is called before rendering machines.
# This function does not affect MAME Favourites, Recently Played, etc. Those can always be rendered.
# This function relies in the timestamps in control_dic.
#
# Returns True if everything is OK and machines inside a Category can be rendered.
# Returns False and prints warning message if machines inside a category cannot be rendered.
#
def _check_AML_MAME_status(PATHS, settings, control_dic):
    # >> Check if MAME executable path has been configured.
    if not g_settings['mame_prog']:
        t = 'MAME executable not configured. ' \
            'Open AML addon settings and configure the location of the MAME executable in the ' \
            '"Paths" tab.'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME executable exists.
    mame_prog_FN = FileName(g_settings['mame_prog'])
    if not mame_prog_FN.exists():
        t = 'MAME executable configured but not found. ' \
            'Open AML addon settings and configure the location of the MAME executable in the ' \
            '"Paths" tab.'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME XML has been extracted.
    if control_dic['t_XML_extraction'] == 0:
        t = 'MAME.XML has not been extracted. ' \
            'In AML root window open the context menu, select "Setup plugin" and then ' \
            'click on "Extract MAME.xml".'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME Main DB has been built and is more recent than the XML.
    if control_dic['t_MAME_DB_build'] < control_dic['t_XML_extraction']:
        t = 'MAME Main database needs to be built. ' \
            'In AML root window open the context menu, select "Setup plugin" and then ' \
            'click on "Build all databases".'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME Audit DB has been built and is more recent than the Main DB.
    if control_dic['t_MAME_Audit_DB_build'] < control_dic['t_MAME_DB_build']:
        t = 'MAME Audit database needs to be built. ' \
            'In AML root window open the context menu, select "Setup plugin" and then ' \
            'click on "Build all databases".'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME Catalog DB has been built and is more recent than the Main DB.
    if control_dic['t_MAME_Catalog_build'] < control_dic['t_MAME_Audit_DB_build']:
        t = 'MAME Catalog database needs to be built. ' \
            'In AML root window open the context menu, select "Setup plugin" and then ' \
            'click on "Build all databases".'
        kodi_dialog_OK(t)
        return False

    # >> All good!
    log_debug('_check_AML_MAME_status() All good!')
    return True

#
# Same function for Software Lists. Called before rendering SL Items inside a Software List.
#
def _check_AML_SL_status(PATHS, g_settings, control_dic):
    # >> Check if MAME executable path has been configured.
    if not g_settings['mame_prog']:
        t = 'MAME executable not configured. ' \
            'Open AML addon settings and configure the location of the MAME executable in the ' \
            '"Paths" tab.'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME executable exists.
    mame_prog_FN = FileName(g_settings['mame_prog'])
    if not mame_prog_FN.exists():
        t = 'MAME executable configured but not found. ' \
            'Open AML addon settings and configure the location of the MAME executable in the ' \
            '"Paths" tab.'
        kodi_dialog_OK(t)
        return False

    # >> Check if MAME Main DB has been built and is more recent than the XML.
    # >> The SL DB relies on the MAME Main DB (verify this).
    if control_dic['t_MAME_DB_build'] < control_dic['t_XML_extraction']:
        t = 'MAME Main database needs to be built. ' \
            'In AML root window open the context menu, select "Setup plugin" and then ' \
            'click on "Build all databases".'
        kodi_dialog_OK(t)
        return False

    # >> Check if SL Main DB has been built and is more recent than the MAME database.
    if control_dic['t_SL_DB_build'] < control_dic['t_MAME_DB_build']:
        t = 'Software List database needs to be built. ' \
            'In AML root window open the context menu, select "Setup plugin" and then ' \
            'click on "Build all databases".'
        kodi_dialog_OK(t)
        return False

    # >> All good!
    log_debug('_check_AML_SL_status() All good!')
    return True

# -------------------------------------------------------------------------------------------------
# Setup plugin databases
# -------------------------------------------------------------------------------------------------
def _command_context_setup_plugin():
    dialog = xbmcgui.Dialog()
    menu_item = dialog.select('Setup plugin',
                             ['Check MAME version',
                              'Extract MAME.xml',
                              'Build all databases',
                              'Scan everything and build plots',
                              'Build Fanarts ...',
                              'Audit MAME machine ROMs/CHDs',
                              'Audit SL ROMs/CHDs',
                              'Step by step ...'])
    if menu_item < 0: return

    # --- Check MAME version ---
    # >> Run 'mame -?' and extract version from stdout
    if menu_item == 0:
        if not g_settings['mame_prog']:
            kodi_dialog_OK('MAME executable is not set.')
            return
        mame_prog_FN = FileName(g_settings['mame_prog'])
        mame_version_str = fs_extract_MAME_version(PATHS, mame_prog_FN)
        kodi_dialog_OK('MAME version is {0}'.format(mame_version_str))

    # --- Extract MAME.xml ---
    elif menu_item == 1:
        if not g_settings['mame_prog']:
            kodi_dialog_OK('MAME executable is not set.')
            return
        mame_prog_FN = FileName(g_settings['mame_prog'])

        # --- Extract MAME XML ---
        (filesize, total_machines) = fs_extract_MAME_XML(PATHS, mame_prog_FN)
        kodi_dialog_OK('Extracted MAME XML database. '
                       'Size is {0} MB and there are {1} machines.'.format(filesize / 1000000, total_machines))

    # --- Build everything ---
    elif menu_item == 2:
        if not PATHS.MAME_XML_PATH.exists():
            kodi_dialog_OK('MAME XML not found. Execute "Extract MAME.xml" first.')
            return

        pDialog = xbmcgui.DialogProgress()
        line1_str = 'Loading databases ...'
        num_items = 1
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        pDialog.update(int((1*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Build all databases ---
        # 1) Creates the ROM hashed database.
        # 2) Creates the (empty) Asset cache.
        # 3) Updates control_dic and t_MAME_DB_build timestamp.
        DB = mame_build_MAME_main_database(PATHS, g_settings, control_dic)
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

        # --- Build and save everything ---
        # 1) Updates control_dic and t_MAME_Audit_DB_build timestamp.
        # 2) machine_roms is mutated to save memory!!! Do not save it after this point.
        mame_build_ROM_audit_databases(PATHS, g_settings, control_dic,
                                       DB.machines, DB.machines_render,
                                       DB.devices_db_dic, DB.machine_roms)
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

        # --- Release some memory ---
        DB.devices_db_dic  = None

        # --- Build MAME catalog ---
        # >> At this time the asset database will be empty (scanner has not been run). However, 
        # >> the asset cache with an empty database is required to render the machines in the catalogs.
        # 1) Creates cache_index_dic and SAVES it.
        # 2) Requires rebuilding of the ROM cache.
        # 3) Requires rebuilding of the asset cache.
        # 4) Updates control_dic and t_MAME_Catalog_build timestamp.
        mame_build_MAME_catalogs(PATHS, g_settings, control_dic,
                                 DB.machines, DB.machines_render,
                                 DB.machine_roms, DB.main_pclone_dic, DB.assets_dic)
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        if g_settings['debug_enable_MAME_machine_cache']:
            cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
            fs_build_ROM_cache(PATHS, DB.machines, DB.machines_render, cache_index_dic, pDialog)
        if g_settings['debug_enable_MAME_asset_cache']:
            if 'cache_index_dic' not in locals():
                cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
            fs_build_asset_cache(PATHS, DB.assets_dic, cache_index_dic, pDialog)

        # --- Release some memory before building the SLs ---
        DB.machine_roms    = None
        DB.main_pclone_dic = None
        DB.assets_dic      = None

        # 1) Updates control_dic and the t_SL_DB_build timestamp.
        mame_build_SoftwareLists_databases(PATHS, g_settings, control_dic,
                                           DB.machines, DB.machines_render)
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        kodi_notify('All databases built')

    # --- Scan everything ---
    elif menu_item == 3:
        log_info('_command_setup_plugin() Scanning everything ...')

        # --- MAME Machines -------------------------------------------------------------------
        # NOTE Here only check for abort conditions. Optinal conditions must be check
        #      inside the function.
        # >> Get paths and check they exist
        if not g_settings['rom_path']:
            kodi_dialog_OK('ROM directory not configured. Aborting.')
            return
        ROM_path_FN = FileName(g_settings['rom_path'])
        if not ROM_path_FN.isdir():
            kodi_dialog_OK('ROM directory does not exist. Aborting.')
            return

        scan_CHDs = False
        if g_settings['chd_path']:
            CHD_path_FN = FileName(g_settings['chd_path'])
            if not CHD_path_FN.isdir():
                kodi_dialog_OK('CHD directory does not exist. CHD scanning disabled.')
            else:
                scan_CHDs = True
        else:
            kodi_dialog_OK('CHD directory not configured. CHD scanning disabled.')
            CHD_path_FN = FileName('')

        scan_Samples = False
        if g_settings['samples_path']:
            Samples_path_FN = FileName(g_settings['samples_path'])
            if not Samples_path_FN.isdir():
                kodi_dialog_OK('Samples directory does not exist. Samples scanning disabled.')
            else:
                scan_Samples = True
        else:
            kodi_dialog_OK('Samples directory not configured. Samples scanning disabled.')
            Samples_path_FN = FileName('')

        # >> Load machine database and control_dic
        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 12
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'Control dic')
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME machine Assets')
        assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), pdialog_line1, 'MAME Parent/Clone')
        main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
        pDialog.update(int((5*100) / num_items), pdialog_line1, 'MAME machine archives')
        machine_archives_dic = fs_load_JSON_file_dic(PATHS.ROM_SET_MACHINE_ARCHIVES_DB_PATH.getPath())
        pDialog.update(int((6*100) / num_items), pdialog_line1, 'MAME ROM list')
        ROM_archive_list = fs_load_JSON_file_dic(PATHS.ROM_SET_ROM_ARCHIVES_DB_PATH.getPath())
        pDialog.update(int((7*100) / num_items), pdialog_line1, 'MAME CHD list')
        CHD_archive_list = fs_load_JSON_file_dic(PATHS.ROM_SET_CHD_ARCHIVES_DB_PATH.getPath())
        pDialog.update(int((8*100) / num_items), pdialog_line1, 'History DAT index')
        history_idx_dic = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
        pDialog.update(int((9*100) / num_items), pdialog_line1, 'Mameinfo DAT index')
        mameinfo_idx_dic = fs_load_JSON_file_dic(PATHS.MAMEINFO_IDX_PATH.getPath())
        pDialog.update(int((10*100) / num_items), pdialog_line1, 'Gameinit DAT index')
        gameinit_idx_list = fs_load_JSON_file_dic(PATHS.GAMEINIT_IDX_PATH.getPath())
        pDialog.update(int((11*100) / num_items), pdialog_line1, 'Command DAT index')
        command_idx_list = fs_load_JSON_file_dic(PATHS.COMMAND_IDX_PATH.getPath())
        pDialog.update(int((12*100) / num_items), ' ', ' ')
        pDialog.close()

        # 1) Updates 'flags' field in assets_dic
        # 2) Updates timestamp t_MAME_ROM_scan in control_dic
        mame_scan_MAME_ROMs(PATHS, g_settings, control_dic,
                            machines, machines_render, assets_dic,
                            machine_archives_dic, ROM_archive_list, CHD_archive_list,
                            ROM_path_FN, CHD_path_FN, Samples_path_FN,
                            scan_CHDs, scan_Samples)

        # >> Get assets directory. Abort if not configured/found.
        do_MAME_asset_scan = True
        if not g_settings['assets_path']:
            kodi_dialog_OK('Asset directory not configured. Aborting.')
            do_MAME_asset_scan = False
        Asset_path_FN = FileName(g_settings['assets_path'])
        if not Asset_path_FN.isdir():
            kodi_dialog_OK('Asset directory does not exist. Aborting.')
            do_MAME_asset_scan = False

        if do_MAME_asset_scan:
            # 1) Mutates assets_dic and control_dic
            mame_scan_MAME_assets(PATHS, assets_dic, control_dic, pDialog,
                                  machines_render, main_pclone_dic, Asset_path_FN)

        # >> Traverse MAME machines and build plot. Updates assets_dic
        mame_build_MAME_plots(machines, machines_render, assets_dic, pDialog,
                              history_idx_dic, mameinfo_idx_dic, gameinit_idx_list, command_idx_list)

        pdialog_line1 = 'Saving databases ...'
        num_items = 2
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'Control dictionary')
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machine Assets')
        fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), assets_dic)
        pDialog.update(int((2*100) / num_items))
        pDialog.close()

        # --- assets_dic has changed. Rebuild hashed database ---
        fs_build_asset_hashed_db(PATHS, assets_dic, pDialog)

        # --- Regenerate asset cache ---
        if g_settings['debug_enable_MAME_asset_cache']:
            cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
            fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)

        # --- Software Lists ------------------------------------------------------------------
        # >> Abort if SL hash path not configured.
        do_SL_ROM_scan = True
        if not g_settings['SL_hash_path']:
            kodi_dialog_OK('Software Lists hash path not set. SL scanning disabled.')
            do_SL_ROM_scan = False
        SL_hash_dir_FN = PATHS.SL_DB_DIR
        log_info('_command_setup_plugin() SL hash dir OP {0}'.format(SL_hash_dir_FN.getOriginalPath()))
        log_info('_command_setup_plugin() SL hash dir  P {0}'.format(SL_hash_dir_FN.getPath()))

        # >> Abort if SL ROM dir not configured.
        if not g_settings['SL_rom_path']:
            kodi_dialog_OK('Software Lists ROM path not set. SL scanning disabled.')
            do_SL_ROM_scan = False
        SL_ROM_dir_FN = FileName(g_settings['SL_rom_path'])
        log_info('_command_setup_plugin() SL ROM dir OP {0}'.format(SL_ROM_dir_FN.getOriginalPath()))
        log_info('_command_setup_plugin() SL ROM dir  P {0}'.format(SL_ROM_dir_FN.getPath()))

        # >> SL CHDs scanning is optional
        scan_SL_CHDs = False
        if g_settings['SL_chd_path']:
            SL_CHD_path_FN = FileName(g_settings['SL_chd_path'])
            if not SL_CHD_path_FN.isdir():
                kodi_dialog_OK('SL CHD directory does not exist. SL CHD scanning disabled.')
            else:
                scan_SL_CHDs = True
        else:
            kodi_dialog_OK('SL CHD directory not configured. SL CHD scanning disabled.')
            SL_CHD_path_FN = FileName('')

        # >> Load SL catalog and PClone dictionary
        pdialog_line1 = 'Loading databases ...'
        num_items = 4
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'Software Lists index')
        SL_index_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'Software Lists machines')
        SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'Software Lists Parent/Clone dictionary')
        SL_pclone_dic = fs_load_JSON_file_dic(PATHS.SL_PCLONE_DIC_PATH.getPath())
        pDialog.update(int((3*100) / num_items), pdialog_line1, 'History DAT index')
        History_idx_dic = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        if do_SL_ROM_scan:
            mame_scan_SL_ROMs(PATHS, control_dic, SL_index_dic, SL_hash_dir_FN,
                              SL_ROM_dir_FN, scan_SL_CHDs, SL_CHD_path_FN)

        # >> Get assets directory. Abort if not configured/found.
        do_SL_asset_scan = True
        if not g_settings['assets_path']:
            kodi_dialog_OK('Asset directory not configured. Aborting.')
            do_SL_asset_scan = False
        Asset_path_FN = FileName(g_settings['assets_path'])
        if not Asset_path_FN.isdir():
            kodi_dialog_OK('Asset directory does not exist. Aborting.')
            do_SL_asset_scan = False

        if do_SL_asset_scan: 
            mame_scan_SL_assets(PATHS, control_dic, SL_index_dic, SL_pclone_dic, Asset_path_FN)

        # >> Build Software Lists plots
        mame_build_SL_plots(PATHS, SL_index_dic, SL_machines_dic, History_idx_dic, pDialog)

        # >> Save control_dic (has been updated in the SL scanner functions).
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        kodi_notify('All ROM/asset scanning finished')

    # --- Build Fanarts ---
    elif menu_item == 4:
        submenu = dialog.select('Build Fanarts',
                               ['Test MAME Fanart',
                                'Test Software List item Fanart',
                                'Build missing MAME Fanarts',
                                'Rebuild all MAME Fanarts',
                                'Build missing Software Lists Fanarts',
                                'Rebuild all Software Lists Fanarts',
                                ])
        if submenu < 0: return
        # >> Check if Pillow library is available. Abort if not.
        if not PILLOW_AVAILABLE:
            kodi_dialog_OK('Pillow Python library is not available. Aborting Fanart generation.')
            return

        # --- Test MAME Fanart ---
        if submenu == 0:
            Template_FN = AML_ADDON_DIR.pjoin('AML-MAME-Fanart-template.xml')
            Asset_path_FN = AML_ADDON_DIR.pjoin('media/MAME_assets')
            Fanart_FN = PLUGIN_DATA_DIR.pjoin('Fanart_MAME.png')
            log_debug('Testing MAME Fanart generation ...')
            log_debug('Template_FN   "{0}"'.format(Template_FN.getPath()))
            log_debug('Fanart_FN     "{0}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN "{0}"'.format(Asset_path_FN.getPath()))

            # >> Load Fanart template from XML file
            layout = mame_load_MAME_Fanart_template(Template_FN)
            # log_debug(unicode(layout))
            if not layout:
                kodi_dialog_OK('Error loading XML MAME Fanart layout.')
                return

            # >> Use hard-coded assets
            m_name = 'dino'
            assets_dic = {
                m_name : {
                    'title' :      Asset_path_FN.pjoin('dino_title.png').getPath(),
                    'snap' :       Asset_path_FN.pjoin('dino_snap.png').getPath(),
                    'flyer' :      Asset_path_FN.pjoin('dino_flyer.png').getPath(),
                    'cabinet' :    Asset_path_FN.pjoin('dino_cabinet.png').getPath(),
                    'artpreview' : Asset_path_FN.pjoin('dino_artpreview.png').getPath(),
                    'PCB' :        Asset_path_FN.pjoin('dino_PCB.png').getPath(),
                    'clearlogo' :  Asset_path_FN.pjoin('dino_clearlogo.png').getPath(),
                    'cpanel' :     Asset_path_FN.pjoin('dino_cpanel.png').getPath(),
                    'marquee' :    Asset_path_FN.pjoin('dino_marquee.png').getPath(),
                }
            }
            mame_build_fanart(PATHS, layout, m_name, assets_dic, Fanart_FN, CANVAS_COLOR = (25, 25, 50))

            # >> Display Fanart
            log_debug('Rendering fanart "{0}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{0}")'.format(Fanart_FN.getPath()))

        # --- Test SL Fanart ---
        elif submenu == 1:
            Template_FN = AML_ADDON_DIR.pjoin('AML-SL-Fanart-template.xml')
            Fanart_FN = PLUGIN_DATA_DIR.pjoin('Fanart_SL.png')
            Asset_path_FN = AML_ADDON_DIR.pjoin('media/SL_assets')
            log_debug('Testing Software List Fanart generation ...')
            log_debug('Template_FN   "{0}"'.format(Template_FN.getPath()))
            log_debug('Fanart_FN     "{0}"'.format(Fanart_FN.getPath()))
            log_debug('Asset_path_FN "{0}"'.format(Asset_path_FN.getPath()))

            # >> Load Fanart template from XML file
            layout = mame_load_SL_Fanart_template(Template_FN)
            # log_debug(unicode(layout))
            if not layout:
                kodi_dialog_OK('Error loading XML Software List Fanart layout.')
                return

            # >> Use hard-coded assets
            SL_name = '32x'
            m_name = 'doom'
            assets_dic = {
                m_name : {
                    'title' :    Asset_path_FN.pjoin('doom_title.png').getPath(),
                    'snap' :     Asset_path_FN.pjoin('doom_snap.png').getPath(),
                    'boxfront' : Asset_path_FN.pjoin('doom_boxfront.png').getPath(),
                }
            }
            mame_build_SL_fanart(PATHS, layout, SL_name, m_name, assets_dic, Fanart_FN, CANVAS_COLOR = (50, 50, 75))

            # >> Display Fanart
            log_debug('Rendering fanart "{0}"'.format(Fanart_FN.getPath()))
            xbmc.executebuiltin('ShowPicture("{0}")'.format(Fanart_FN.getPath()))

        # --- 2 -> Build missing MAME Fanarts ---
        # --- 3 -> Rebuild all MAME Fanarts ---
        # >> For a complete MAME artwork collection rebuilding all Fanarts will take hours!
        elif submenu == 2 or submenu == 3:
            BUILD_MISSING = True if submenu == 2 else False
            if BUILD_MISSING: log_info('_command_setup_plugin() Building missing Fanarts ...')
            else:             log_info('_command_setup_plugin() Rebuilding all Fanarts ...')

            # >> If artwork directory not configured abort.
            if not g_settings['assets_path']:
                kodi_dialog_OK('Asset directory not configured. Aborting Fanart generation.')
                return

            # >> If fanart directory doesn't exist create it.
            Template_FN = AML_ADDON_DIR.pjoin('AML-MAME-Fanart-template.xml')
            Asset_path_FN = FileName(g_settings['assets_path'])
            Fanart_path_FN = Asset_path_FN.pjoin('fanarts')
            if not Fanart_path_FN.isdir():
                log_info('Creating Fanart dir "{0}"'.format(Fanart_path_FN.getPath()))
                Fanart_path_FN.makedirs()

            # >> Load Fanart template from XML file
            layout = mame_load_MAME_Fanart_template(Template_FN)
            # log_debug(unicode(layout))
            if not layout:
                kodi_dialog_OK('Error loading XML MAME Fanart layout.')
                return

            # >> Load Assets DB
            pDialog_canceled = False
            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced MAME Launcher', 'Loading assets database ... ')
            pDialog.update(0)
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            pDialog.update(100)
            pDialog.close()

            # >> Traverse all machines and build fanart from other pieces of artwork
            total_machines = len(assets_dic)
            processed_machines = 0
            pDialog.create('Advanced MAME Launcher', 'Building MAME machine Fanarts ... ')
            for m_name in sorted(assets_dic):
                pDialog.update((processed_machines * 100) // total_machines)
                if pDialog.iscanceled():
                    pDialog_canceled = True
                    # kodi_dialog_OK('Fanart generation was cancelled by the user.')
                    break
                # >> If build missing Fanarts was chosen only build fanart if file cannot
                # >> be found.
                Fanart_FN = Fanart_path_FN.pjoin('{0}.png'.format(m_name))
                if BUILD_MISSING:
                    if Fanart_FN.exists():
                        assets_dic[m_name]['fanart'] = Fanart_FN.getPath()
                    else:
                        mame_build_fanart(PATHS, layout, m_name, assets_dic, Fanart_FN)
                else:
                    mame_build_fanart(PATHS, layout, m_name, assets_dic, Fanart_FN)
                processed_machines += 1
            pDialog.update(100)
            pDialog.close()

            # --- Save assets DB ---
            pDialog.create('Advanced MAME Launcher', 'Saving asset database ... ')
            pDialog.update(0)
            fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), assets_dic)
            pDialog.update(100)
            pDialog.close()
            
            # --- assets_dic has changed. Rebuild hashed database ---
            fs_build_asset_hashed_db(PATHS, assets_dic, pDialog)

            # --- Rebuild asset cache ---
            if g_settings['debug_enable_MAME_asset_cache']:
                cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
                fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)
            if pDialog_canceled: kodi_notify('MAME fanarts building stopped. Partial progress saved.')
            else:                kodi_notify('MAME fanarts building finished')

        # --- 4 -> Missing SL Fanarts ---
        # --- 5 -> Rebuild all SL Fanarts ---
        elif submenu == 4 or submenu == 5:
            BUILD_MISSING = True if submenu == 4 else False
            if BUILD_MISSING: log_info('_command_setup_plugin() Building missing Software Lists Fanarts ...')
            else:             log_info('_command_setup_plugin() Rebuilding all Software Lists Fanarts ...')

            # >> If artwork directory not configured abort.
            if not g_settings['assets_path']:
                kodi_dialog_OK('Asset directory not configured. Aborting Fanart generation.')
                return

            # >> Load Fanart template from XML file
            Template_FN = AML_ADDON_DIR.pjoin('AML-SL-Fanart-template.xml')
            layout = mame_load_SL_Fanart_template(Template_FN)
            # log_debug(unicode(layout))
            if not layout:
                kodi_dialog_OK('Error loading XML Software List Fanart layout.')
                return

            # >> Load SL index
            SL_index_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

            # >> Traverse all SL and on each SL every item
            pDialog_canceled = False
            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced MAME Launcher')
            SL_number = len(SL_index_dic)
            SL_count = 1
            for SL_name in sorted(SL_index_dic):
                # >> Update progres dialog
                pdialog_line1 = 'Processing SL {0} ({1} of {2})...'.format(SL_name, SL_count, SL_number)
                pdialog_line2 = ' '
                pDialog.update(0, pdialog_line1, pdialog_line2)

                # >> If fanart directory doesn't exist create it.
                Asset_path_FN = FileName(g_settings['assets_path'])
                Fanart_path_FN = Asset_path_FN.pjoin('fanarts_SL/{0}'.format(SL_name))
                if not Fanart_path_FN.isdir():
                    log_info('Creating SL Fanart dir "{0}"'.format(Fanart_path_FN.getPath()))
                    Fanart_path_FN.makedirs()

                # >> Load Assets DB
                pdialog_line2 = 'Loading SL asset database ... '
                pDialog.update(0, pdialog_line1, pdialog_line2)
                assets_file_name =  SL_index_dic[SL_name]['rom_DB_noext'] + '_assets.json'
                SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
                SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

                # >> Traverse all SL items and build fanart from other pieces of artwork
                total_SL_items = len(SL_assets_dic)
                processed_SL_items = 0
                for m_name in sorted(SL_assets_dic):
                    pdialog_line2 = 'SL item {0}'.format(m_name)
                    update_number = (processed_SL_items * 100) // total_SL_items
                    pDialog.update(update_number, pdialog_line1, pdialog_line2)
                    if pDialog.iscanceled():
                        pDialog_canceled = True
                        # kodi_dialog_OK('SL Fanart generation was cancelled by the user.')
                        break
                    # >> If build missing Fanarts was chosen only build fanart if file cannot
                    # >> be found.
                    Fanart_FN = Fanart_path_FN.pjoin('{0}.png'.format(m_name))
                    if BUILD_MISSING:
                        if Fanart_FN.exists():
                            SL_assets_dic[m_name]['fanart'] = Fanart_FN.getPath()
                        else:
                            mame_build_SL_fanart(PATHS, layout, SL_name, m_name, SL_assets_dic, Fanart_FN)
                    else:
                        mame_build_SL_fanart(PATHS, layout, SL_name, m_name, SL_assets_dic, Fanart_FN)
                    processed_SL_items += 1

                # >> Save assets DB
                pdialog_line2 = 'Saving SL {0} asset database ... '.format(SL_name)
                pDialog.update(100, pdialog_line1, pdialog_line2)
                fs_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic)

                # >> Update progress
                SL_count += 1
                if pDialog_canceled: break
            pDialog.close()
            if pDialog_canceled: kodi_notify('SL Fanart building stopped. Partial progress saved.')
            else:                kodi_notify('SL Fanart building finished')

    # --- Audit MAME machine ROMs/CHDs ---
    # NOTE It is likekely that this function will take a looong time. It is important that the
    #      audit process can be canceled and a partial report is written.
    elif menu_item == 5:
        log_info('_command_setup_plugin() Audit MAME machines ROMs/CHDs ...')

        # --- Load machines, ROMs and CHDs databases ---
        pDialog = xbmcgui.DialogProgress()
        pdialog_line1 = 'Loading databases ...'
        num_items = 4
        pDialog.create('Advanced MAME Launcher')
        pDialog.update(int((0*100) / num_items), pdialog_line1, 'Control dic')
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
        pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Main')
        machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
        pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machines Render')
        machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
        pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME ROM Audit')
        audit_roms_dic = fs_load_JSON_file_dic(PATHS.ROM_AUDIT_DB_PATH.getPath())
        pDialog.update(int((4*100) / num_items), ' ', ' ')
        pDialog.close()

        # --- Audit all MAME machines ---
        # 1) Updates control_dic statistics and timestamp.
        mame_audit_MAME_all(PATHS, pDialog, g_settings, control_dic,
                            machines, machines_render, audit_roms_dic)
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        kodi_notify('ROM and CHD audit finished')

    # --- Audit SL ROMs/CHDs ---
    elif menu_item == 6:
        log_info('_command_setup_plugin() Audit SL ROMs/CHDs ...')

        # --- Load stuff ---
        control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())

        # --- Audit all Software List items ---
        # 1) Updates control_dic statistics and timestamps.
        mame_audit_SL_all(PATHS, g_settings, control_dic)
        fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
        kodi_notify('Software Lists audit finished')

    # --- Build Step by Step ---
    elif menu_item == 7:
        submenu = dialog.select('Setup plugin (step by step)', [
                                    'Build MAME databases',
                                    'Build MAME Audit/Scanner databases',
                                    'Build MAME catalogs',
                                    'Build Software Lists databases',
                                    'Scan MAME ROMs/CHDs/Samples',
                                    'Scan MAME assets/artwork',
                                    'Scan Software Lists ROMs/CHDs',
                                    'Scan Software Lists assets/artwork',
                                    'Build MAME machines plots',
                                    'Build SL items plots',
                                    'Rebuild MAME machine and asset cache',
                                ])
        if submenu < 0: return

        # --- Build main MAME database, PClone list and hashed database ---
        if submenu == 0:
            # --- Error checks ---
            # >> Check that MAME_XML_PATH exists
            if not PATHS.MAME_XML_PATH.exists():
                kodi_dialog_OK('MAME XML not found. Execute "Extract MAME.xml" first.')
                return

            # --- Parse MAME XML and generate main database and PClone list ---
            log_info('_command_setup_plugin() Generating MAME main database and PClone list ...')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            # 1) Builds the ROM hashed database.
            # 2) Updates control_dic stats and timestamp.
            # try:
            #     DB = mame_build_MAME_main_database(PATHS, g_settings, control_dic)
            # except GeneralError as err:
            #     log_error(err.msg)
            #     raise SystemExit
            DB = mame_build_MAME_main_database(PATHS, g_settings, control_dic)
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            kodi_notify('Main MAME databases built')

        # --- Build ROM audit/scanner databases ---
        elif submenu == 1:
            log_info('_command_setup_plugin() Generating ROM audit/scanner databases ...')
            # --- Error checks ---
            # >> Check that MAME_XML_PATH exists
            # if not PATHS.MAME_XML_PATH.exists():
            #     kodi_dialog_OK('MAME XML not found. Execute "Extract MAME.xml" first.')
            #     return

            # --- Load databases ---
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ...'
            num_items = 5
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
            machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine Devices')
            devices_db_dic = fs_load_JSON_file_dic(PATHS.DEVICES_DB_PATH.getPath())
            pDialog.update(int((4*100) / num_items), line1_str, 'MAME machine ROMs')
            machine_roms = fs_load_JSON_file_dic(PATHS.ROMS_DB_PATH.getPath())
            # >> Kodi BUG: when the progress dialog is closed and reopened again, the
            # >> second line of the previous dialog is not deleted (still printed).
            pDialog.update(int((5*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- Generate ROM databases ---
            # 1) Updates control_dic and t_MAME_Audit_DB_build timestamp.
            mame_build_ROM_audit_databases(PATHS, g_settings, control_dic,
                                           machines, machines_render, devices_db_dic,
                                           machine_roms)
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            kodi_notify('ROM audit/scanner databases built')

        # --- Build MAME catalogs ---
        elif submenu == 2:
            log_info('_command_setup_plugin() Building MAME catalogs ...')
            # --- Error checks ---
            # >> Check that main MAME database exists

            # --- Load databases ---
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ...'
            num_items = 6
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
            machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine ROMs')
            machine_roms = fs_load_JSON_file_dic(PATHS.ROMS_DB_PATH.getPath())
            pDialog.update(int((4*100) / num_items), line1_str, 'MAME PClone dictionary')
            main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
            pDialog.update(int((5*100) / num_items), line1_str, 'MAME machine Assets')
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            pDialog.update(int((6*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- Build MAME catalog ---
            # >> At this time the asset database will be empty (scanner has not been run). However, 
            # >> the asset cache with an empty database is required to render the machines in the catalogs.
            # 1) Creates cache_index_dic and SAVES it.
            # 2) Requires rebuilding of the ROM cache.
            # 3) Requires rebuilding of the asset cache.
            # 4) Updates control_dic and t_MAME_Catalog_build timestamp.
            mame_build_MAME_catalogs(PATHS, g_settings, control_dic,
                                     machines, machines_render, machine_roms,
                                     main_pclone_dic, assets_dic)
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            if g_settings['debug_enable_MAME_machine_cache']:
                cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
                fs_build_ROM_cache(PATHS, machines, machines_render, cache_index_dic, pDialog)
            if g_settings['debug_enable_MAME_asset_cache']:
                if 'cache_index_dic' not in locals():
                    cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
                fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)
            kodi_notify('MAME Catalogs built')

        # --- Build Software Lists ROM/CHD databases, SL indices and SL catalogs ---
        elif submenu == 3:
            # --- Error checks ---
            if not g_settings['SL_hash_path']:
                t = 'Software Lists hash path not set. ' \
                    'Open AML addon settings and configure the location of the MAME hash path in the ' \
                    '"Paths" tab.'
                kodi_dialog_OK(t)
                return
            if not PATHS.MAIN_DB_PATH.exists():
                t = 'MAME Main database not found. ' \
                    'Open AML addon settings and configure the location of the MAME executable in the ' \
                    '"Paths" tab.'
                kodi_dialog_OK(t)
                return False

            # --- Read main database and control dic ---
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ...'
            num_items = 3
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
            machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- Build SL databases ---
            mame_build_SoftwareLists_databases(PATHS, g_settings, control_dic,
                                               machines, machines_render)
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            kodi_notify('Software Lists database built')

        # --- Scan ROMs/CHDs/Samples and updates ROM status ---
        elif submenu == 4:
            log_info('_command_setup_plugin() Scanning MAME ROMs/CHDs/Samples ...')

            # >> Get paths and check they exist
            if not g_settings['rom_path']:
                kodi_dialog_OK('ROM directory not configured. Aborting.')
                return
            ROM_path_FN = FileName(g_settings['rom_path'])
            if not ROM_path_FN.isdir():
                kodi_dialog_OK('ROM directory does not exist. Aborting.')
                return

            scan_CHDs = False
            if g_settings['chd_path']:
                CHD_path_FN = FileName(g_settings['chd_path'])
                if not CHD_path_FN.isdir():
                    kodi_dialog_OK('CHD directory does not exist. CHD scanning disabled.')
                else:
                    scan_CHDs = True
            else:
                kodi_dialog_OK('CHD directory not configured. CHD scanning disabled.')
                CHD_path_FN = FileName('')

            scan_Samples = False
            if g_settings['samples_path']:
                Samples_path_FN = FileName(g_settings['samples_path'])
                if not Samples_path_FN.isdir():
                    kodi_dialog_OK('Samples directory does not exist. Samples scanning disabled.')
                else:
                    scan_Samples = True
            else:
                kodi_dialog_OK('Samples directory not configured. Samples scanning disabled.')
                Samples_path_FN = FileName('')

            # >> Load machine database and control_dic and scan
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ...'
            num_items = 7
            pDialog.create('Advanced MAME Launcher', line1_str)
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
            machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine Assets')
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            pDialog.update(int((4*100) / num_items), line1_str, 'Machine archives list')
            machine_archives_dic = fs_load_JSON_file_dic(PATHS.ROM_SET_MACHINE_ARCHIVES_DB_PATH.getPath())
            pDialog.update(int((5*100) / num_items), line1_str, 'ROM List index')
            ROM_archive_list = fs_load_JSON_file_dic(PATHS.ROM_SET_ROM_ARCHIVES_DB_PATH.getPath())
            pDialog.update(int((6*100) / num_items), line1_str, 'CHD list index')
            CHD_archive_list = fs_load_JSON_file_dic(PATHS.ROM_SET_CHD_ARCHIVES_DB_PATH.getPath())
            pDialog.update(int((7*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- Scan MAME ROMs/CHDs/Samples ---
            # 1) Updates 'flags' field in assets_dic
            # 2) Updates timestamp t_MAME_ROM_scan in control_dic
            # 3) Requires rebuilding of the asset cache.
            mame_scan_MAME_ROMs(PATHS, g_settings, control_dic,
                                machines, machines_render, assets_dic,
                                machine_archives_dic, ROM_archive_list, CHD_archive_list,
                                ROM_path_FN, CHD_path_FN, Samples_path_FN,
                                scan_CHDs, scan_Samples)

            # >> Save databases
            line1_str = 'Saving databases ...'
            num_items = 2
            pDialog.create('Advanced MAME Launcher', line1_str)
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machine Assets')
            fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), assets_dic)
            pDialog.update(int((2*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- assets have changed. Rebuild hashed database ---
            fs_build_asset_hashed_db(PATHS, assets_dic, pDialog)

            # --- assets_dic has changed. Update asset cache ---
            if g_settings['debug_enable_MAME_asset_cache']:
                cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
                fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)
            kodi_notify('Scanning of ROMs, CHDs and Samples finished')

        # --- Scans MAME assets/artwork ---
        elif submenu == 5:
            log_info('_command_setup_plugin() Scanning MAME assets/artwork ...')

            # >> Get assets directory. Abort if not configured/found.
            if not g_settings['assets_path']:
                kodi_dialog_OK('Asset directory not configured. Aborting.')
                return
            Asset_path_FN = FileName(g_settings['assets_path'])
            if not Asset_path_FN.isdir():
                kodi_dialog_OK('Asset directory does not exist. Aborting.')
                return

            # >> Load machine database and scan
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ... '
            num_items = 4
            pDialog.create('Advanced MAME Launcher', line1_str)
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), line1_str, 'MAME machine Assets')
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), line1_str, 'MAME PClone dictionary')
            main_pclone_dic = fs_load_JSON_file_dic(PATHS.MAIN_PCLONE_DIC_PATH.getPath())
            pDialog.update(int((4*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- Scan MAME assets ---
            # 1) Mutates assets_dic and control_dic (timestamp and stats)
            # 2) Requires rebuilding of the asset cache.
            mame_scan_MAME_assets(PATHS, assets_dic, control_dic, pDialog,
                                  machines_render, main_pclone_dic, Asset_path_FN)

            # >> Save asset DB and control dic
            line1_str = 'Saving databases ...'
            num_items = 2
            pDialog.create('Advanced MAME Launcher', line1_str)
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            pDialog.update(int((1*100) / num_items), line1_str, 'MAME machine Assets')
            fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), assets_dic)
            pDialog.update(int((2*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- assets have changed. Rebuild hashed database ---
            fs_build_asset_hashed_db(PATHS, assets_dic, pDialog)

            # --- Asset cache must be regenerated ---
            if g_settings['debug_enable_MAME_asset_cache']:
                cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
                fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)
            kodi_notify('Scanning of assets/artwork finished')

        # --- Scan SL ROMs/CHDs ---
        elif submenu == 6:
            log_info('_command_setup_plugin() Scanning SL ROMs/CHDs ...')

            # >> Abort if SL hash path not configured.
            if not g_settings['SL_hash_path']:
                kodi_dialog_OK('Software Lists hash path not set. Scanning aborted.')
                return
            SL_hash_dir_FN = PATHS.SL_DB_DIR
            log_info('_command_setup_plugin() SL hash dir OP {0}'.format(SL_hash_dir_FN.getOriginalPath()))
            log_info('_command_setup_plugin() SL hash dir  P {0}'.format(SL_hash_dir_FN.getPath()))

            # >> Abort if SL ROM dir not configured.
            if not g_settings['SL_rom_path']:
                kodi_dialog_OK('Software Lists ROM path not set. Scanning aborted.')
                return
            SL_ROM_dir_FN = FileName(g_settings['SL_rom_path'])
            log_info('_command_setup_plugin() SL ROM dir OP {0}'.format(SL_ROM_dir_FN.getOriginalPath()))
            log_info('_command_setup_plugin() SL ROM dir  P {0}'.format(SL_ROM_dir_FN.getPath()))

            # >> SL CHDs scanning is optional
            scan_SL_CHDs = False
            if g_settings['SL_chd_path']:
                SL_CHD_path_FN = FileName(g_settings['SL_chd_path'])
                if not SL_CHD_path_FN.isdir():
                    kodi_dialog_OK('SL CHD directory does not exist. SL CHD scanning disabled.')
                else:
                    scan_SL_CHDs = True
            else:
                kodi_dialog_OK('SL CHD directory not configured. SL CHD scanning disabled.')
                SL_CHD_path_FN = FileName('')

            # >> Load SL and scan ROMs/CHDs. fs_scan_SL_ROMs() updates each SL database.
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ...'
            num_items = 2
            pDialog.create('Advanced MAME Launcher', line1_str)
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'Software Lists index')
            SL_index_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            pDialog.update(int((2*100) / num_items), ' ', ' ')
            pDialog.close()

            # 1) Mutates control_dic (timestamp and statistics)
            mame_scan_SL_ROMs(PATHS, control_dic, SL_index_dic, SL_hash_dir_FN,
                              SL_ROM_dir_FN, scan_SL_CHDs, SL_CHD_path_FN)
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            kodi_notify('Scanning of SL ROMs finished')

        # --- Scan SL assets/artwork ---
        # >> Database format: ADDON_DATA_DIR/db_SoftwareLists/32x_assets.json
        # >> { 'ROM_name' : {'asset1' : 'path', 'asset2' : 'path', ... }, ... }
        elif submenu == 7:
            log_info('_command_setup_plugin() Scanning SL assets/artwork ...')

            # >> Get assets directory. Abort if not configured/found.
            if not g_settings['assets_path']:
                kodi_dialog_OK('Asset directory not configured. Aborting.')
                return
            Asset_path_FN = FileName(g_settings['assets_path'])
            if not Asset_path_FN.isdir():
                kodi_dialog_OK('Asset directory does not exist. Aborting.')
                return

            # >> Load SL database and scan
            pDialog = xbmcgui.DialogProgress()
            line1_str = 'Loading databases ...'
            num_items = 3
            pDialog.create('Advanced MAME Launcher', line1_str)
            pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), line1_str, 'Software Lists index')
            SL_index_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            pDialog.update(int((2*100) / num_items), line1_str, 'Software Lists Parent/Clone dictionary')
            SL_pclone_dic = fs_load_JSON_file_dic(PATHS.SL_PCLONE_DIC_PATH.getPath())
            pDialog.update(int((3*100) / num_items), ' ', ' ')
            pDialog.close()

            # 1) Mutates control_dic (timestamp and statistics)
            mame_scan_SL_assets(PATHS, control_dic, SL_index_dic, SL_pclone_dic, Asset_path_FN)
            fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)
            kodi_notify('Scanning of SL assets finished')

        # --- Build MAME machines plot ---
        elif submenu == 8:
            log_debug('Rebuilding MAME machine plots ...')

            # >> Load machine database and control_dic
            pDialog = xbmcgui.DialogProgress()
            pdialog_line1 = 'Loading databases ...'
            num_items = 8
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), pdialog_line1, 'Control dic')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Main')
            machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME machine Assets')
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            pDialog.update(int((4*100) / num_items), pdialog_line1, 'History DAT')
            history_idx_dic = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
            pDialog.update(int((5*100) / num_items), pdialog_line1, 'Mameinfo DAT')
            mameinfo_idx_dic = fs_load_JSON_file_dic(PATHS.MAMEINFO_IDX_PATH.getPath())
            pDialog.update(int((6*100) / num_items), pdialog_line1, 'Gameinit DAT')
            gameinit_idx_list = fs_load_JSON_file_dic(PATHS.GAMEINIT_IDX_PATH.getPath())
            pDialog.update(int((7*100) / num_items), pdialog_line1, 'Command DAT')
            command_idx_list = fs_load_JSON_file_dic(PATHS.COMMAND_IDX_PATH.getPath())
            pDialog.update(int((8*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- Traverse MAME machines and build plot ---
            # 1) Mutates assets_dic
            # 2) Requires rebuilding of the asset cache.
            mame_build_MAME_plots(machines, machines_render, assets_dic, pDialog,
                                  history_idx_dic, mameinfo_idx_dic,
                                  gameinit_idx_list, command_idx_list)

            # >> Update hashed DBs and save DBs
            # >> cache_index_dic built in fs_build_MAME_catalogs()
            pdialog_line1 = 'Saving databases ...'
            num_items = 1
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), pdialog_line1, 'MAME machine Assets')
            fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), assets_dic)
            pDialog.update(int((1*100) / num_items), ' ', ' ')
            pDialog.close()

            # --- assets have changed. Rebuild hashed database ---
            fs_build_asset_hashed_db(PATHS, assets_dic, pDialog)

            # --- Asset cache must be regenerated ---
            if g_settings['debug_enable_MAME_asset_cache']:
                cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
                fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)
            kodi_notify('MAME machines plot generation finished')

        # --- Buils Software List items plot ---
        elif submenu == 9:
            log_debug('Rebuilding Software List items plots ...')

            # >> Load SL index and SL machine index.
            pDialog = xbmcgui.DialogProgress()
            pdialog_line1 = 'Loading databases ...'
            num_items = 3
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), pdialog_line1, 'Software Lists index')
            SL_index_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
            pDialog.update(int((1*100) / num_items), pdialog_line1, 'Software Lists machines')
            SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
            pDialog.update(int((2*100) / num_items), pdialog_line1, 'History DAT index')
            History_idx_dic = fs_load_JSON_file_dic(PATHS.HISTORY_IDX_PATH.getPath())
            pDialog.update(int((3*100) / num_items), ' ', ' ')
            pDialog.close()

            mame_build_SL_plots(PATHS, SL_index_dic, SL_machines_dic, History_idx_dic, pDialog)
            kodi_notify('SL item plot generation finished')

        # --- Regenerate MAME machine and assets cache ---
        elif submenu == 10:
            log_debug('Rebuilding MAME machine and assets cache ...')

            # --- Load databases ---
            pDialog = xbmcgui.DialogProgress()
            pdialog_line1 = 'Loading databases ...'
            num_items = 4
            pDialog.create('Advanced MAME Launcher')
            pDialog.update(int((0*100) / num_items), pdialog_line1, 'Control dic')
            control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
            pDialog.update(int((1*100) / num_items), pdialog_line1, 'MAME machines Main')
            machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
            pDialog.update(int((2*100) / num_items), pdialog_line1, 'MAME machines Render')
            machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
            pDialog.update(int((3*100) / num_items), pdialog_line1, 'MAME machine Assets')
            assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
            pDialog.update(int((4*100) / num_items), pdialog_line1, 'MAME Parent/Clone')
            pDialog.close()

            # --- Regenerate caches ---
            cache_index_dic = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
            fs_build_ROM_cache(PATHS, machines, machines_render, cache_index_dic, pDialog)
            fs_build_asset_cache(PATHS, assets_dic, cache_index_dic, pDialog)
            kodi_notify('MAME machine and asset caches rebuilt')

#
# Checks and updates all MAME and SL Favourite object. This function is useful for plugin
# upgrades.
#
def _command_check_all_Favourite_objects():
    # --- Load databases ---
    pDialog = xbmcgui.DialogProgress()
    num_items = 5
    pDialog.create('Advanced MAME Launcher')
    line1_str = 'Loading databases ...'
    pDialog.update(int((0*100) / num_items), line1_str, 'Control dictionary')
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    pDialog.update(int((1*100) / num_items), line1_str, 'MAME machines Main')
    machines = fs_load_JSON_file_dic(PATHS.MAIN_DB_PATH.getPath())
    pDialog.update(int((2*100) / num_items), line1_str, 'MAME machines Render')
    machines_render = fs_load_JSON_file_dic(PATHS.RENDER_DB_PATH.getPath())
    pDialog.update(int((3*100) / num_items), line1_str, 'MAME machine Assets')
    assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
    pDialog.update(int((4*100) / num_items), line1_str, 'SL index catalog')
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    pDialog.update(int((5*100) / num_items), ' ', ' ')
    pDialog.close()

    # --- Check/Update MAME Favourite machines ---
    mame_update_MAME_Fav_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog)

    # --- Check/Update MAME Most Played machines ---
    mame_update_MAME_MostPlay_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog)

    # --- Check/Update MAME Recently Played machines ---
    mame_update_MAME_RecentPlay_objects(PATHS, control_dic, machines, machines_render, assets_dic, pDialog)

    # --- Check/Update SL Favourite ROMs ---
    mame_update_SL_Fav_objects(PATHS, control_dic, SL_catalog_dic, pDialog)

    # --- Check/Update SL Most Played machines ---
    mame_update_SL_MostPlay_objects(PATHS, control_dic, SL_catalog_dic, pDialog)

    # --- Check/Update SL Recently Played machines ---
    mame_update_SL_RecentPlay_objects(PATHS, control_dic, SL_catalog_dic, pDialog)

    # --- Notify the user ---
    kodi_refresh_container()
    kodi_notify('All MAME Favourite objects checked')

#
# Checks AML configuration and informs users of potential problems.
# OK
# WARN
# ERR
#
def _command_check_AML_configuration():
    def check_dir_ERR(slist, dir_str, msg):
        if dir_str:
            if FileName(dir_str).exists():
                slist.append('{0} {1} "{2}"'.format(OK, msg, dir_str))
            else:
                slist.append('{0} {1} not found'.format(ERR, msg))
        else:
            slist.append('{0} {1} not set'.format(ERR, msg))

    def check_dir_WARN(slist, dir_str, msg):
        if dir_str:
            if FileName(dir_str).exists():
                slist.append('{0} {1} "{2}"'.format(OK, msg, dir_str))
            else:
                slist.append('{0} {1} not found'.format(WARN, msg))
        else:
            slist.append('{0} {1} not set'.format(WARN, msg))

    def check_file_WARN(slist, file_str, msg):
        if file_str:
            if FileName(file_str).exists():
                slist.append('{0} {1} "{2}"'.format(OK, msg, file_str))
            else:
                slist.append('{0} {1} not found'.format(WARN, msg))
        else:
            slist.append('{0} {1} not set'.format(WARN, msg))

    def check_asset_dir(slist, dir_FN, msg):
        if dir_FN.exists():
            slist.append('{0} Found {1} path "{2}"'.format(OK, msg, dir_FN.getPath()))
        else:
            slist.append('{0} {1} path does not exist'.format(WARN, msg))
            slist.append('     Tried "{0}"'.format(dir_FN.getPath()))

    log_info('_command_check_AML_configuration() Checking AML configuration ...')
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
    check_dir_ERR(slist, g_settings['rom_path'], 'MAME ROM path')
    slist.append('')

    # --- MAME assets ---
    slist.append('[COLOR orange]MAME assets[/COLOR]')
    if g_settings['assets_path']:
        if FileName(g_settings['assets_path']).exists():
            slist.append('{0} MAME Asset path "{1}"'.format(OK, g_settings['assets_path']))

            # >> Check that artwork subdirectories exist
            Asset_path_FN = FileName(g_settings['assets_path'])

            PCB_FN = Asset_path_FN.pjoin('PCBs')
            artpreview_FN = Asset_path_FN.pjoin('artpreviews')
            artwork_FN = Asset_path_FN.pjoin('artwork')
            cabinets_FN = Asset_path_FN.pjoin('cabinets')
            clearlogos_FN = Asset_path_FN.pjoin('clearlogos')
            cpanels_FN = Asset_path_FN.pjoin('cpanels')
            flyers_FN = Asset_path_FN.pjoin('flyers')
            manuals_FN = Asset_path_FN.pjoin('manuals')
            marquees_FN = Asset_path_FN.pjoin('marquees')
            snaps_FN = Asset_path_FN.pjoin('snaps')
            titles_FN = Asset_path_FN.pjoin('titles')
            videosnaps_FN = Asset_path_FN.pjoin('videosnaps')

            check_asset_dir(slist, PCB_FN, 'PCB')
            check_asset_dir(slist, artpreview_FN, 'Artpreviews')
            check_asset_dir(slist, artwork_FN, 'Artwork')
            check_asset_dir(slist, cabinets_FN, 'Cabinets')
            check_asset_dir(slist, clearlogos_FN, 'Clearlogos')
            check_asset_dir(slist, cpanels_FN, 'CPanels')
            check_asset_dir(slist, flyers_FN, 'Flyers')
            check_asset_dir(slist, manuals_FN, 'Manuals')
            check_asset_dir(slist, marquees_FN, 'Marquees')
            check_asset_dir(slist, snaps_FN, 'Snaps')
            check_asset_dir(slist, titles_FN, 'Titles')
            check_asset_dir(slist, videosnaps_FN, 'Trailers')
        else:
            slist.append('{0} MAME Asset path not found'.format(ERR))
    else:
        slist.append('{0} MAME Asset path not set'.format(WARN))
    slist.append('')

    # --- CHD path ---
    slist.append('[COLOR orange]MAME optional paths[/COLOR]')
    check_dir_WARN(slist, g_settings['chd_path'], 'MAME CHD path')

    # --- Samples path ---
    check_dir_WARN(slist, g_settings['samples_path'], 'MAME Samples path')
    slist.append('')

    # --- Software Lists paths ---
    slist.append('[COLOR orange]Software List paths[/COLOR]')
    check_dir_WARN(slist, g_settings['SL_hash_path'], 'SL hash path')
    check_dir_WARN(slist, g_settings['SL_rom_path'], 'SL ROM path')
    check_dir_WARN(slist, g_settings['SL_chd_path'], 'SL CHD path')
    slist.append('')

    slist.append('[COLOR orange]Software Lists assets[/COLOR]')
    if g_settings['assets_path']:
        if FileName(g_settings['assets_path']).exists():
            slist.append('{0} MAME Asset path "{1}"'.format(OK, g_settings['assets_path']))

            # >> Check that artwork subdirectories exist
            Asset_path_FN = FileName(g_settings['assets_path'])

            covers_FN = Asset_path_FN.pjoin('covers_SL')
            manuals_FN = Asset_path_FN.pjoin('manuals_SL')
            snaps_FN = Asset_path_FN.pjoin('snaps_SL')
            titles_FN = Asset_path_FN.pjoin('titles_SL')
            videosnaps_FN = Asset_path_FN.pjoin('videosnaps_SL')

            check_asset_dir(slist, covers_FN, 'SL Covers')
            check_asset_dir(slist, manuals_FN, 'SL Manuals')
            check_asset_dir(slist, snaps_FN, 'SL Snaps')
            check_asset_dir(slist, titles_FN, 'SL Titles')
            check_asset_dir(slist, videosnaps_FN, 'SL Trailers')
        else:
            slist.append('{0} MAME Asset path not found'.format(ERR))
    else:
        slist.append('{0} MAME Asset path not set'.format(WARN))
    slist.append('')

    # --- Optional INI files ---
    slist.append('[COLOR orange]INI files[/COLOR]')
    check_file_WARN(slist, g_settings['catver_path'], 'Catver.ini file')
    check_file_WARN(slist, g_settings['catlist_path'], 'Catlist.ini file')
    check_file_WARN(slist, g_settings['genre_path'], 'Genre.ini file')
    check_file_WARN(slist, g_settings['nplayers_path'], 'NPlayers.ini file')
    check_file_WARN(slist, g_settings['bestgames_path'], 'bestgames.ini file')
    check_file_WARN(slist, g_settings['series_path'], 'series.ini file')
    slist.append('')

    # --- Optional DAT files ---
    slist.append('[COLOR orange]DAT files[/COLOR]')
    check_file_WARN(slist, g_settings['history_path'], 'History.dat file')
    check_file_WARN(slist, g_settings['mameinfo_path'], 'MameINFO.dat file')
    check_file_WARN(slist, g_settings['gameinit_path'], 'Gameinit.dat file')
    check_file_WARN(slist, g_settings['command_path'], 'Command.dat file')

    # --- Display info to the user ---
    _display_text_window('AML configuration check report', '\n'.join(slist))

#
# Check MAME and SL CRC 32 hash collisions.
# The assumption in this function is that there is not SHA1 hash collisions.
# Implicit ROM merging must not be confused with a collision.
#
def _command_check_MAME_CRC_collisions():
    log_info('_command_check_MAME_CRC_collisions() Initialising ...')

    # >> Open ROMs database.
    pDialog = xbmcgui.DialogProgress()
    line1_str = 'Loading databases ...'
    num_items = 2
    pDialog.create('Advanced MAME Launcher')
    pDialog.update(int((0*100) / num_items), line1_str, 'MAME machine ROMs')
    machines_roms = fs_load_JSON_file_dic(PATHS.ROMS_DB_PATH.getPath())
    pDialog.update(int((1*100) / num_items), line1_str, 'MAME ROMs SHA1 dictionary')
    roms_sha1_dic = fs_load_JSON_file_dic(PATHS.ROM_SHA1_HASH_DB_PATH.getPath())
    pDialog.update(int((2*100) / num_items), ' ', ' ')
    pDialog.close()

    # >> Detect implicit ROM merging using the SHA1 hash and check for CRC32 collisions for
    # >> non-implicit merged ROMs.
    pdialog_line1 = 'Checking for MAME CRC32 hash collisions ...'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    total_machines = len(machines_roms)
    processed_machines = 0
    crc_roms_dic = {}
    sha1_roms_dic = {}
    num_collisions = 0
    table_str = []
    table_str.append(['right',  'left',     'left', 'left', 'left'])
    table_str.append(['Status', 'ROM name', 'Size', 'CRC',  'SHA1'])
    for m_name in sorted(machines_roms):
        pDialog.update((processed_machines*100) // total_machines, pdialog_line1)
        m_roms = machines_roms[m_name]
        for rom in m_roms['roms']:
            rom_nonmerged_location = m_name + '/' + rom['name']
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
                    table_str.append(['Collision', rom_nonmerged_location, str(rom['size']), rom['crc'], sha1])
                    table_str.append(['with', coliding_name, ' ', coliding_crc, coliding_sha1])
                else:
                    crc_roms_dic[rom['crc']] = rom_nonmerged_location
        processed_machines += 1
    pDialog.update((processed_machines*100) // total_machines, pdialog_line1, ' ')
    pDialog.close()
    log_debug('MAME has {0:,d} valid ROMs in total'.format(len(roms_sha1_dic)))
    log_debug('There are {0} CRC32 collisions'.format(num_collisions))

    # >> Write report and debug file
    slist = []
    slist.append('*** AML MAME ROMs CRC32 hash collision report ***')
    slist.append('MAME has {0:,d} valid ROMs in total'.format(len(roms_sha1_dic)))
    slist.append('There are {0} CRC32 collisions'.format(num_collisions))
    slist.append('')
    table_str_list = text_render_table_str(table_str)
    slist.extend(table_str_list)
    _display_text_window('AML MAME CRC32 hash collision report', '\n'.join(slist))
    log_info('Writing "{0}"'.format(PATHS.REPORT_DEBUG_MAME_COLLISIONS_PATH.getPath()))
    with open(PATHS.REPORT_DEBUG_MAME_COLLISIONS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(slist).encode('utf-8'))

def _command_check_SL_CRC_collisions():
    log_info('_command_check_SL_CRC_collisions() Initialising ...')

    # >> Load SL catalog and check for errors.
    SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())

    # >> Process all SLs
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
        SL_ROMS_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_name + '_ROMs.json')
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

    # >> Write report
    slist = []
    slist.append('*** AML SL ROMs CRC32 hash collision report ***')
    slist.append('The Software Lists have {0:,d} valid ROMs in total'.format(len(roms_sha1_dic)))
    slist.append('There are {0} CRC32 collisions'.format(num_collisions))
    slist.append('')
    table_str_list = text_render_table_str(table_str)
    slist.extend(table_str_list)
    _display_text_window('AML Software Lists CRC32 hash collision report', '\n'.join(slist))
    log_info('Writing "{0}"'.format(PATHS.REPORT_DEBUG_SL_COLLISIONS_PATH.getPath()))
    with open(PATHS.REPORT_DEBUG_SL_COLLISIONS_PATH.getPath(), 'w') as file:
        file.write('\n'.join(slist).encode('utf-8'))

#
# Launch MAME machine. Syntax: $ mame <machine_name> [options]
# Example: $ mame dino
#
def _run_machine(machine_name, location):
    log_info('_run_machine() Launching MAME machine  "{0}"'.format(machine_name))
    log_info('_run_machine() Launching MAME location "{0}"'.format(location))

    # --- Get paths ---
    mame_prog_FN = FileName(g_settings['mame_prog'])

    # --- Load databases ---
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if location == LOCATION_STANDARD:
        log_debug('Reading info from hashed DBs')
        machine = fs_get_machine_main_db_hash(PATHS, machine_name)
        assets = fs_get_machine_assets_db_hash(PATHS, machine_name)
    elif location == LOCATION_MAME_FAVS:
        log_debug('Reading info from MAME Favourites')
        fav_machines = fs_load_JSON_file_dic(PATHS.FAV_MACHINES_PATH.getPath())
        machine = fav_machines[machine_name]
        assets = machine['assets']
    elif location == LOCATION_MAME_MOST_PLAYED:
        log_debug('Reading info from MAME Most Played DB')
        most_played_roms_dic = fs_load_JSON_file_dic(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
        machine = most_played_roms_dic[machine_name]
        assets = machine['assets']
    elif location == LOCATION_MAME_RECENT_PLAYED:
        log_debug('Reading info from MAME Recently Played DB')
        recent_roms_list = fs_load_JSON_file_list(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
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
    log_debug('_run_machine() mame_prog_FN "{0}"'.format(mame_prog_FN.getPath()))
    log_debug('_run_machine() mame_dir     "{0}"'.format(mame_dir))
    log_debug('_run_machine() mame_exec    "{0}"'.format(mame_exec))
    log_debug('_run_machine() machine_name "{0}"'.format(machine_name))
    log_debug('_run_machine() BIOS_name    "{0}"'.format(BIOS_name))

    # --- Compute ROM recently played list ---
    # >> If the machine is already in the list remove it and place it on the first position.
    MAX_RECENT_PLAYED_ROMS = 100
    recent_rom = fs_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic)
    recent_roms_list = fs_load_JSON_file_list(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath())
    # >> Machine names are unique in this list
    recent_roms_list = [machine for machine in recent_roms_list if machine_name != machine['name']]
    recent_roms_list.insert(0, recent_rom)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('_run_machine() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
        log_debug('_run_machine() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    fs_write_JSON_file(PATHS.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms_dic = fs_load_JSON_file_dic(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if recent_rom['name'] in most_played_roms_dic:
        rom_name = recent_rom['name']
        most_played_roms_dic[rom_name]['launch_count'] += 1
    else:
        # >> Add field launch_count to recent_rom to count how many times have been launched.
        recent_rom['launch_count'] = 1
        most_played_roms_dic[recent_rom['name']] = recent_rom
    fs_write_JSON_file(PATHS.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)

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
        log_info('_run_machine() MAME launching disabled. Exiting function.')
        return

    # --- Run MAME ---
    _run_before_execution()
    _run_process(PATHS, arg_list, mame_dir)
    _run_after_execution()
    log_info('_run_machine() Exiting function.')

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
def _run_SL_machine(SL_name, SL_ROM_name, location):
    SL_LAUNCH_WITH_MEDIA = 100
    SL_LAUNCH_NO_MEDIA   = 200
    log_info('_run_SL_machine() Launching SL machine (location = {0}) ...'.format(location))
    log_info('_run_SL_machine() SL_name     "{0}"'.format(SL_name))
    log_info('_run_SL_machine() SL_ROM_name "{0}"'.format(SL_ROM_name))

    # --- Get paths ---
    mame_prog_FN = FileName(g_settings['mame_prog'])

    # --- Get a list of launch machine <devices> and SL ROM <parts> ---
    # --- Load SL ROMs and SL assets databases ---
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    if location == LOCATION_STANDARD:
        # >> Load DBs
        log_info('_run_SL_machine() SL ROM is in Standard Location')
        SL_catalog_dic = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
        SL_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[SL_name]['rom_DB_noext'] + '.json')
        log_info('_run_SL_machine() SL ROMs JSON "{0}"'.format(SL_DB_FN.getPath()))
        SL_ROMs = fs_load_JSON_file_dic(SL_DB_FN.getPath())
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json')
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
        log_info('_run_SL_machine() SL ROM is in Favourites')
        fav_SL_roms = fs_load_JSON_file_dic(PATHS.FAV_SL_ROMS_PATH.getPath())
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
        most_played_roms_dic = fs_load_JSON_file_dic(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
        SL_fav_DB_key = SL_name + '-' + SL_ROM_name
        SL_ROM = most_played_roms_dic[SL_fav_DB_key]
        SL_assets = SL_ROM['assets']
        part_list = most_played_roms_dic[SL_fav_DB_key]['parts']
        launch_machine_name = most_played_roms_dic[SL_fav_DB_key]['launch_machine']
        launch_machine_desc = '[ Not available ]'
    elif location == LOCATION_SL_RECENT_PLAYED:
        log_debug('Reading info from MAME Recently Played DB')
        recent_roms_list = fs_load_JSON_file_list(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
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
    log_info('_run_SL_machine() launch_machine_name = "{0}"'.format(launch_machine_name))
    log_info('_run_SL_machine() launch_machine_desc = "{0}"'.format(launch_machine_desc))

    # --- Load SL machines ---
    SL_machines_dic = fs_load_JSON_file_dic(PATHS.SL_MACHINES_PATH.getPath())
    SL_machine_list = SL_machines_dic[SL_name]
    if not launch_machine_name:
        # >> Get a list of machines that can launch this SL ROM. User chooses in a select dialog
        log_info('_run_SL_machine() User selecting SL run machine ...')
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
        log_info('_run_SL_machine() User chose machine "{0}" ({1})'.format(launch_machine_name, launch_machine_desc))
    else:
        # >> User configured a machine to launch this SL item. Find the machine in the machine list.
        log_info('_run_SL_machine() Searching configured SL item running machine ...')
        machine_found = False
        for SL_machine in SL_machine_list:
            if SL_machine['machine'] == launch_machine_name:
                selected_SL_machine = SL_machine
                machine_found = True
                break
        if machine_found:
            log_info('_run_SL_machine() Found machine "{0}"'.format(launch_machine_name))
            launch_machine_desc    = SL_machine['description']
            launch_machine_devices = SL_machine['devices']
        else:
            log_error('_run_SL_machine() Machine "{0}" not found'.format(launch_machine_name))
            log_error('_run_SL_machine() Aborting launch')
            kodi_dialog_OK('Machine "{0}" not found. Aborting launch.'.format(launch_machine_name))
            return

    # --- DEBUG ---
    log_info('_run_SL_machine() Machine "{0}" has {1} interfaces'.format(launch_machine_name, len(launch_machine_devices)))
    log_info('_run_SL_machine() SL ROM  "{0}" has {1} parts'.format(SL_ROM_name, len(part_list)))
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
        log_info('_run_SL_machine() Launch case A)')
        launch_case = SL_LAUNCH_CASE_A
        media_name = launch_machine_devices[0]['instance']['name']
        sl_launch_mode = SL_LAUNCH_WITH_MEDIA

    # >> Case B
    #    User chooses media to launch?
    elif num_machine_interfaces == 1 and num_SL_ROM_parts > 1:
        log_info('_run_SL_machine() Launch case B)')
        launch_case = SL_LAUNCH_CASE_B
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    # >> Case C
    elif num_machine_interfaces > 1 and num_SL_ROM_parts == 1:
        log_info('_run_SL_machine() Launch case C)')
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
        log_info('_run_SL_machine() Matched machine device interface "{0}" '.format(device['att_interface']) +
                 'to SL ROM part "{0}"'.format(part_list[0]['interface']))
        sl_launch_mode = SL_LAUNCH_WITH_MEDIA

    # >> Case D.
    # >> User chooses media to launch?
    elif num_machine_interfaces > 1 and num_SL_ROM_parts > 1:
        log_info('_run_SL_machine() Launch case D)')
        launch_case = SL_LAUNCH_CASE_D
        media_name = ''
        sl_launch_mode = SL_LAUNCH_NO_MEDIA

    else:
        log_info(unicode(machine_interfaces))
        log_warning('_run_SL_machine() Logical error in SL launch case.')
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
    log_debug('_run_SL_machine() mame_prog_FN "{0}"'.format(mame_prog_FN.getPath()))    
    log_debug('_run_SL_machine() mame_dir     "{0}"'.format(mame_dir))
    log_debug('_run_SL_machine() mame_exec    "{0}"'.format(mame_exec))
    log_debug('_run_SL_machine() launch_machine_name "{0}"'.format(launch_machine_name))
    log_debug('_run_SL_machine() launch_machine_desc "{0}"'.format(launch_machine_desc))
    log_debug('_run_SL_machine() media_name          "{0}"'.format(media_name))

    # --- Compute ROM recently played list ---
    # >> If the machine is already in the list remove it and place it on the first position.
    MAX_RECENT_PLAYED_ROMS = 100
    recent_ROM = fs_get_SL_Favourite(SL_name, SL_ROM_name, SL_ROM, SL_assets, control_dic)
    recent_roms_list = fs_load_JSON_file_list(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath())
    # >> Machine names are unique in this list
    recent_roms_list = [item for item in recent_roms_list if SL_fav_DB_key != item['SL_DB_key']]
    recent_roms_list.insert(0, recent_ROM)
    if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
        log_debug('_run_SL_machine() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
        log_debug('_run_SL_machine() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
        temp_list = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
        recent_roms_list = temp_list
    fs_write_JSON_file(PATHS.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)

    # --- Compute most played ROM statistics ---
    most_played_roms_dic = fs_load_JSON_file_dic(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath())
    if SL_fav_DB_key in most_played_roms_dic:
        most_played_roms_dic[SL_fav_DB_key]['launch_count'] += 1
    else:
        # >> Add field launch_count to recent_ROM to count how many times have been launched.
        recent_ROM['launch_count'] = 1
        most_played_roms_dic[SL_fav_DB_key] = recent_ROM
    fs_write_JSON_file(PATHS.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)

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
        log_info('_run_machine() MAME launching disabled. Exiting function.')
        return

    # --- Run MAME ---
    _run_before_execution()
    _run_process(PATHS, arg_list, mame_dir)
    _run_after_execution()
    log_info('_run_SL_machine() Exiting function.')

def _run_before_execution():
    global g_flag_kodi_was_playing
    global g_flag_kodi_audio_suspended
    global g_flag_kodi_toggle_fullscreen
    log_info('_run_before_execution() Function BEGIN ...')

    # --- Stop/Pause Kodi mediaplayer if requested in settings ---
    # >> id="media_state_action" default="0" values="Stop|Pause|Keep playing"
    g_flag_kodi_was_playing = False
    media_state_action = g_settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Keep playing'][media_state_action]
    a = '_run_before_execution() media_state_action is "{0}" ({1})'
    log_verb(a.format(media_state_str, media_state_action))
    if media_state_action == 0 and xbmc.Player().isPlaying():
        log_verb('_run_before_execution() Calling xbmc.Player().stop()')
        xbmc.Player().stop()
        xbmc.sleep(100)
        g_flag_kodi_was_playing = True
    elif media_state_action == 1 and xbmc.Player().isPlaying():
        log_verb('_run_before_execution() Calling xbmc.Player().pause()')
        xbmc.Player().pause()
        xbmc.sleep(100)
        g_flag_kodi_was_playing = True

    # --- Force audio suspend if requested in "Settings" --> "Advanced"
    # >> See http://forum.kodi.tv/showthread.php?tid=164522
    g_flag_kodi_audio_suspended = False
    if g_settings['suspend_audio_engine']:
        log_verb('_run_before_execution() Suspending Kodi audio engine')
        xbmc.audioSuspend()
        xbmc.enableNavSounds(False)
        xbmc.sleep(100)
        g_flag_kodi_audio_suspended = True
    else:
        log_verb('_run_before_execution() DO NOT suspend Kodi audio engine')

    # --- Force joystick suspend if requested in "Settings" --> "Advanced"
    # NOT IMPLEMENTED YET.
    # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
    # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
    # >> See https://forum.kodi.tv/showthread.php?tid=313615

    # --- Toggle Kodi windowed/fullscreen if requested ---
    g_flag_kodi_toggle_fullscreen = False
    if g_settings['toggle_window']:
        log_verb('_run_before_execution() Toggling Kodi from fullscreen to window')
        kodi_toogle_fullscreen()
        g_flag_kodi_toggle_fullscreen = True
    else:
        log_verb('_run_before_execution() Toggling Kodi fullscreen/windowed DISABLED')

    # --- Pause Kodi execution some time ---
    delay_tempo_ms = g_settings['delay_tempo']
    log_verb('_run_before_execution() Pausing {0} ms'.format(delay_tempo_ms))
    xbmc.sleep(delay_tempo_ms)
    log_debug('_run_before_execution() function ENDS')

def _run_process(PATHS, arg_list, mame_dir):
    log_info('_run_process() Function BEGIN ...')

    # --- Prevent a console window to be shown in Windows. Not working yet! ---
    if sys.platform == 'win32':
        log_info('_run_process() Platform is win32. Creating _info structure')
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
        log_info('_run_process() _info is None')
        _info = None

    # --- Run MAME ---
    with open(PATHS.MAME_OUTPUT_PATH.getPath(), 'wb') as f:
        p = subprocess.Popen(arg_list, cwd = mame_dir, startupinfo = _info,
                             stdout = f, stderr = subprocess.STDOUT)
    p.wait()
    log_debug('_run_process() function ENDS')

def _run_after_execution():
    log_info('_run_after_execution() Function BEGIN ...')

    # --- Stop Kodi some time ---
    delay_tempo_ms = g_settings['delay_tempo']
    log_verb('_run_after_execution() Pausing {0} ms'.format(delay_tempo_ms))
    xbmc.sleep(delay_tempo_ms)

    # --- Toggle Kodi windowed/fullscreen if requested ---
    if g_flag_kodi_toggle_fullscreen:
        log_verb('_run_after_execution() Toggling Kodi fullscreen')
        kodi_toogle_fullscreen()
    else:
        log_verb('_run_after_execution() Toggling Kodi fullscreen DISABLED')

    # --- Resume joystick engine if it was suspended ---
    # NOT IMPLEMENTED

    # --- Resume audio engine if it was suspended ---
    # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
    # Also produces this in Kodi's log:
    # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
    #   ERROR: ActiveAE::Resume - failed to init
    if g_flag_kodi_audio_suspended:
        log_verb('_run_after_execution() Kodi audio engine was suspended before launching')
        log_verb('_run_after_execution() Resuming Kodi audio engine')
        xbmc.audioResume()
        xbmc.enableNavSounds(True)
        xbmc.sleep(100)
    else:
        log_verb('_run_after_execution() DO NOT resume Kodi audio engine')

    # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
    # >> id="media_state_action" default="0" values="Stop|Pause|Keep playing"
    media_state_action = g_settings['media_state_action']
    media_state_str = ['Stop', 'Pause', 'Keep playing'][media_state_action]
    a = '_run_after_execution() media_state_action is "{0}" ({1})'
    log_verb(a.format(media_state_str, media_state_action))
    log_verb('_run_after_execution() g_flag_kodi_was_playing is {0}'.format(g_flag_kodi_was_playing))
    if g_flag_kodi_was_playing and media_state_action == 1:
        log_verb('_run_after_execution() Calling xbmc.Player().play()')
        xbmc.Player().play()
    log_debug('_run_after_execution() Function ENDS')

# ---------------------------------------------------------------------------------------------
# Misc functions
# ---------------------------------------------------------------------------------------------
def _display_text_window(window_title, info_text):
    xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
    dialog = xbmcgui.Dialog()
    dialog.textviewer(window_title, info_text)
    xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

# List of sorting methods here http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcplugin.html#-setSetting
def _set_Kodi_unsorted_method():
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

def _set_Kodi_all_sorting_methods():
    if g_addon_handle < 0: return
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle=g_addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

def _set_Kodi_all_sorting_methods_and_size():
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
# Used in xbmcplugin.addDirectoryItem()
#
def _misc_url_1_arg(arg_name, arg_value):
    arg_value_escaped = arg_value.replace('&', '%26')

    return '{0}?{1}={2}'.format(g_base_url, arg_name, arg_value_escaped)

def _misc_url_2_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')

    return '{0}?{1}={2}&{3}={4}'.format(g_base_url, 
                                        arg_name_1, arg_value_1_escaped,
                                        arg_name_2, arg_value_2_escaped)

def _misc_url_3_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                          arg_name_3, arg_value_3):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')
    arg_value_3_escaped = arg_value_3.replace('&', '%26')

    return '{0}?{1}={2}&{3}={4}&{5}={6}'.format(g_base_url,
                                                arg_name_1, arg_value_1_escaped,
                                                arg_name_2, arg_value_2_escaped,
                                                arg_name_3, arg_value_3_escaped)

def _misc_url_4_arg(arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                          arg_name_3, arg_value_3, arg_name_4, arg_value_4):
    arg_value_1_escaped = arg_value_1.replace('&', '%26')
    arg_value_2_escaped = arg_value_2.replace('&', '%26')
    arg_value_3_escaped = arg_value_3.replace('&', '%26')
    arg_value_4_escaped = arg_value_4.replace('&', '%26')

    return '{0}?{1}={2}&{3}={4}&{5}={6}&{7}={8}'.format(g_base_url,
                                                        arg_name_1, arg_value_1_escaped,
                                                        arg_name_2, arg_value_2_escaped,
                                                        arg_name_3, arg_value_3_escaped,
                                                        arg_name_4, arg_value_4_escaped)

#
# Used in context menus
#
def _misc_url_1_arg_RunPlugin(arg_n_1, arg_v_1):
    arg_v_1_esc = arg_v_1.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2})'.format(g_base_url, arg_n_1, arg_v_1_esc)

def _misc_url_2_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4})'.format(g_base_url, arg_n_1, arg_v_1_esc, arg_n_2, arg_v_2_esc)

def _misc_url_3_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2, arg_n_3, arg_v_3):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')
    arg_v_3_esc = arg_v_3.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4}&{5}={6})'.format(g_base_url,
                                                                arg_n_1, arg_v_1_esc,
                                                                arg_n_2, arg_v_2_esc,
                                                                arg_n_3, arg_v_3_esc)

def _misc_url_4_arg_RunPlugin(arg_n_1, arg_v_1, arg_n_2, arg_v_2, 
                              arg_n_3, arg_v_3, arg_n_4, arg_v_4):
    arg_v_1_esc = arg_v_1.replace('&', '%26')
    arg_v_2_esc = arg_v_2.replace('&', '%26')
    arg_v_3_esc = arg_v_3.replace('&', '%26')
    arg_v_4_esc = arg_v_4.replace('&', '%26')

    return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4}&{5}={6}&{7}={8})'.format(g_base_url,
                                                                        arg_n_1, arg_v_1_esc,
                                                                        arg_n_2, arg_v_2_esc,
                                                                        arg_n_3, arg_v_3_esc, 
                                                                        arg_n_4, arg_v_4_esc)
