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

# Advanced MAME Launcher high-level filesystem I/O functions and database model.
#
# In the future this module must strictly use the FileName class for all IO operations and
# not the Python runtime.

# --- AEL packages ---
from .constants import *
from .utils import *

# --- Python standard library ---
import copy
import hashlib
import io
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET

# -------------------------------------------------------------------------------------------------
# Advanced MAME Launcher data model
# -------------------------------------------------------------------------------------------------
# http://xmlwriter.net/xml_guide/attlist_declaration.shtml#CdataEx
# #REQUIRED  The attribute must always be included
# #IMPLIED   The attribute does not have to be included.
#
# Example from MAME 0.190:
#   <!ELEMENT device (instance*, extension*)>
#     <!ATTLIST device type CDATA #REQUIRED>
#     <!ATTLIST device tag CDATA #IMPLIED>
#     <!ATTLIST device fixed_image CDATA #IMPLIED>
#     <!ATTLIST device mandatory CDATA #IMPLIED>
#     <!ATTLIST device interface CDATA #IMPLIED>
#     <!ELEMENT instance EMPTY>
#       <!ATTLIST instance name CDATA #REQUIRED>
#       <!ATTLIST instance briefname CDATA #REQUIRED>
#     <!ELEMENT extension EMPTY>
#       <!ATTLIST extension name CDATA #REQUIRED>
#
# <device> tags. Example of machine aes (Neo Geo AES)
# <device type="memcard" tag="memcard">
#   <instance name="memcard" briefname="memc"/>
#   <extension name="neo"/>
# </device>
# <device type="cartridge" tag="cslot1" interface="neo_cart">
#   <instance name="cartridge" briefname="cart"/>
#   <extension name="bin"/>
# </device>
#
# This is how it is stored:
# devices = [
#   {
#     'att_interface' : string,
#     'att_mandatory' : bool,
#     'att_tag' : string,
#     'att_type' : string,
#     'ext_names' : [string1, string2],
#     'instance' : {'name' : string, 'briefname' : string}
#   }, ...
# ]
#
# Rendering on AML Machine Information text window.
# devices[0]:
#   att_interface: text_type
#   att_mandatory: text_type(bool)
#   att_tag: text_type
#   att_type: text_type
#   ext_names: text_type(string list),
#   instance: text_type(dictionary),
# devices[1]:
#   ...
#
def db_new_machine_dic():
    return {
        # --- <machine> tag attributes ---
        'isMechanical'    : False,
        'romof'           : '',
        'sampleof'        : '',
        'sourcefile'      : '',
        # --- Other tags inside <machine> from MAME XML ---
        # <!ATTLIST chip type (cpu|audio) #REQUIRED>
        # <!ATTLIST chip name CDATA #REQUIRED>
        # Name of the chip when type == 'cpu'
        # Example <chip type="cpu" tag="maincpu" name="Zilog Z80" />
        'chip_cpu_name'   : [],
        'devices'         : [], # List of dictionaries. See comments above.
        'display_height'  : [], # <!ATTLIST display height CDATA #IMPLIED>
        'display_refresh' : [], # <!ATTLIST display refresh CDATA #REQUIRED>
        'display_rotate'  : [], # <!ATTLIST display rotate (0|90|180|270) #IMPLIED>
        'display_type'    : [], # <!ATTLIST display type (raster|vector|lcd|svg|unknown) #REQUIRED>
        'display_width'   : [], # <!ATTLIST display width CDATA #IMPLIED>
        'input'           : {},
        'softwarelists'   : [],
        # --- Custom AML data (from INI files or generated) ---
        'alltime'         : '', # MASH Alltime.ini
        'artwork'         : [], # MASH Artwork.ini
        'bestgames'       : '', # betsgames.ini
        'category'        : [], # MASH category.ini
        'catlist'         : '', # catlist.ini
        'catver'          : '', # catver.ini
        'genre'           : '', # genre.ini
        'series'          : [], # series.ini
        'veradded'        : '', # catver.ini
        # --- AML generated field ---
        'isDead'          : False,
    }

#
# Object used in MAME_render_db.json
#
def db_new_machine_render_dic():
    return {
        # --- <machine> attributes ---
        'cloneof'        : '', # Must be in the render DB to generate the PClone flag
        'isBIOS'         : False,
        'isDevice'       : False,
        # --- Other tags inside <machine> from MAME XML ---
        'description'    : '',
        'year'           : '',
        'manufacturer'   : '',
        'driver_status'  : '',
        # --- Custom AML data (from INI files or generated) ---
        'isMature'       : False, # Taken from mature.ini
        'nplayers'       : '',    # Taken from NPlayers.ini
        # Genre used in AML for the skin
        # Taken from Genre.ini or Catver.ini or Catlist.ini
        'genre'          : '',
    }

#
# Object used in MAME_DB_roms.json
# machine_roms = {
#     'machine_name' : {
#         'bios'  : [ db_new_bios_dic(), ... ],
#         'disks' : [ db_new_disk_dic(), ... ],
#         'roms'  : [ db_new_rom_dic(), ... ],
#     }
# }
#
def db_new_roms_object():
    return {
        'bios'    : [],
        'roms'    : [],
        'disks'   : [],
        'samples' : [],
    }

def db_new_bios_dic():
    return {
        'name'        : '',
        'description' : '',
    }

def db_new_disk_dic():
    return {
        'name'  : '',
        'merge' : '',
        'sha1'  : '', # sha1 allows to know if CHD is valid or not. CHDs don't have crc
    }

def db_new_rom_dic():
    return {
        'name'  : '',
        'merge' : '',
        'bios'  : '',
        'size'  : 0,
        'crc'   : '', # crc allows to know if ROM is valid or not
    }

def db_new_audit_dic():
    return {
        'machine_has_ROMs_or_CHDs' : False,
        'machine_has_ROMs'         : False,
        'machine_has_CHDs'         : False,
        'machine_is_OK'            : True,
        'machine_ROMs_are_OK'      : True,
        'machine_CHDs_are_OK'      : True,
    }

#
# First element is the database dictionary key of the asset, second element is the subdirectory name.
# List used in mame_scan_MAME_assets()
#
ASSET_MAME_T_LIST  = [
    ('3dbox',      '3dboxes'),
    ('artpreview', 'artpreviews'),
    ('artwork',    'artwork'),
    ('cabinet',    'cabinets'),
    ('clearlogo',  'clearlogos'),
    ('cpanel',     'cpanels'),
    ('fanart',     'fanarts'), # Created by AML automatically when building Fanarts.
    ('flyer',      'flyers'),
    ('manual',     'manuals'),
    ('marquee',    'marquees'),
    ('PCB',        'PCBs'),
    ('snap',       'snaps'),
    ('title',      'titles'),
    ('trailer',    'videosnaps'),
]

#
# flags -> ROM, CHD, Samples, SoftwareLists, Pluggable Devices
#
# Status flags meaning:
#   -  Machine doesn't have ROMs | Machine doesn't have Software Lists
#   ?  Machine has own ROMs and ROMs not been scanned
#   r  Machine has own ROMs and ROMs doesn't exist
#   R  Machine has own ROMs and ROMs exists | Machine has Software Lists
#
# Status device flag:
#   -  Machine has no devices
#   d  Machine has device/s but are not mandatory (can be booted without the device).
#   D  Machine has device/s and must be plugged in order to boot.
#
def db_new_MAME_asset():
    return {
        '3dbox'      : '',
        'artpreview' : '',
        'artwork'    : '',
        'cabinet'    : '',
        'clearlogo'  : '',
        'cpanel'     : '',
        'fanart'     : '',
        'flags'      : '-----',
        'flyer'      : '',
        'history'    : '',
        'manual'     : '',
        'marquee'    : '',
        'PCB'        : '',
        'plot'       : '',
        'snap'       : '',
        'title'      : '',
        'trailer'    : '',
    }

# Status flags meaning:
#   ?  SL ROM not scanned
#   r  Missing ROM
#   R  Have ROM
def db_new_SL_ROM_part():
    return {
        'name'      : '',
        'interface' : ''
    }

def db_new_SL_ROM():
    return {
        'description' : '',
        'year'        : '',
        'publisher'   : '',
        'plot'        : '', # Generated from other fields
        'cloneof'     : '',
        'parts'       : [],
        'hasROMs'     : False,
        'hasCHDs'     : False,
        'status_ROM'  : '-',
        'status_CHD'  : '-',
    }

def db_new_SL_ROM_audit_dic():
    return {
        'type'     : '',
        'name'     : '',
        'size'     : '',
        'crc'      : '',
        'location' : '',
    }

def db_new_SL_DISK_audit_dic():
    return {
        'type'     : '',
        'name'     : '',
        'sha1'     : '',
        'location' : '',
    }

ASSET_SL_T_LIST = [
    ('3dbox',    '3dboxes_SL'),
    ('title',    'titles_SL'),
    ('snap',     'snaps_SL'),
    ('boxfront', 'covers_SL'),
    ('fanart',   'fanarts_SL'),
    ('trailer',  'videosnaps_SL'),
    ('manual',   'manuals_SL'),
]

def db_new_SL_asset():
    return {
        '3dbox'    : '',
        'title'    : '',
        'snap'     : '',
        'boxfront' : '',
        'fanart'   : '',
        'trailer'  : '',
        'manual'   : '',
    }

# Some fields are used in all working modes.
# Some fields are used in Vanilla MAME mode.
# Some fields are used in MAME 2003 Plus mode.
def db_new_MAME_XML_control_dic():
    return {
        't_XML_extraction' : 0,       # Result of time.time() [float]
        't_XML_preprocessing' : 0,    # Result of time.time() [float]
        'total_machines' : 0,         # [integer]
        'st_size' : 0,                # Bytes [integer]
        'st_mtime' : 0.0,             # seconds [float]
        'ver_mame_int' : 0,           # Allows version comparisons [integer]
        'ver_mame_str' : 'undefined', # [Unicode string]
    }

def db_new_control_dic():
    return {
        # --- Filed in when extracting/preprocessing MAME XML ---
        # Operation mode when the database is created. If the OP mode is changed database
        # must be rebuilt.
        'op_mode_raw' : 0,
        'op_mode' : '',
        'stats_total_machines' : 0,

        # --- Timestamps ---
        # MAME
        't_MAME_DB_build' : 0.0,
        't_MAME_Audit_DB_build' : 0.0,
        't_MAME_Catalog_build' : 0.0,
        't_MAME_ROMs_scan' : 0.0,
        't_MAME_assets_scan' : 0.0,
        't_MAME_plots_build' : 0.0,
        't_MAME_fanart_build' : 0.0,
        't_MAME_3dbox_build' : 0.0,
        't_MAME_machine_hash' : 0.0,
        't_MAME_asset_hash' : 0.0,
        't_MAME_render_cache_build' : 0.0,
        't_MAME_asset_cache_build' : 0.0,
        # Software Lists
        't_SL_DB_build' : 0.0,
        't_SL_ROMs_scan' : 0.0,
        't_SL_assets_scan' : 0.0,
        't_SL_plots_build' : 0.0,
        't_SL_fanart_build' : 0.0,
        't_SL_3dbox_build' : 0.0,
        # Misc
        't_Custom_Filter_build' : 0.0,
        't_MAME_audit' : 0.0,
        't_SL_audit' : 0.0,

        # --- Filed in when building main MAME database ---
        'ver_AML_int' : 0,
        'ver_AML_str' : 'Undefined',
        # Numerical MAME version. Allows for comparisons like ver_mame >= MAME_VERSION_0190
        # MAME string version, as reported by the executable stdout. Example: '0.194 (mame0194)'
        'ver_mame_int' : 0,
        'ver_mame_str' : 'Undefined',
        # INI files
        'ver_alltime'   : 'MAME database not built',
        'ver_artwork'   : 'MAME database not built',
        'ver_bestgames' : 'MAME database not built',
        'ver_category'  : 'MAME database not built',
        'ver_catlist'   : 'MAME database not built',
        'ver_catver'    : 'MAME database not built',
        'ver_genre'     : 'MAME database not built',
        'ver_mature'    : 'MAME database not built',
        'ver_nplayers'  : 'MAME database not built',
        'ver_series'    : 'MAME database not built',

        # DAT files
        'ver_command'   : 'MAME database not built',
        'ver_gameinit'  : 'MAME database not built',
        'ver_history'   : 'MAME database not built',
        'ver_mameinfo'  : 'MAME database not built',

        # Basic stats
        'stats_processed_machines' : 0,
        'stats_parents'            : 0,
        'stats_clones'             : 0,
        # Excluding devices machines (devices are not runnable)
        'stats_runnable'           : 0,
        'stats_runnable_parents'   : 0,
        'stats_runnable_clones'    : 0,
        # Main filters
        'stats_coin'               : 0,
        'stats_coin_parents'       : 0,
        'stats_coin_clones'        : 0,
        'stats_nocoin'             : 0,
        'stats_nocoin_parents'     : 0,
        'stats_nocoin_clones'      : 0,
        'stats_mechanical'         : 0,
        'stats_mechanical_parents' : 0,
        'stats_mechanical_clones'  : 0,
        'stats_dead'               : 0,
        'stats_dead_parents'       : 0,
        'stats_dead_clones'        : 0,
        'stats_devices'            : 0,
        'stats_devices_parents'    : 0,
        'stats_devices_clones'     : 0,
        # Binary filters
        'stats_BIOS'               : 0,
        'stats_BIOS_parents'       : 0,
        'stats_BIOS_clones'        : 0,
        'stats_samples'            : 0,
        'stats_samples_parents'    : 0,
        'stats_samples_clones'     : 0,

        # --- Main filter statistics ---
        # Filed in when building the MAME catalogs in mame_build_MAME_catalogs()
        # driver_status for device machines is always the empty string ''
        'stats_MF_Normal_Total'          : 0, 'stats_MF_Normal_Total_parents'          : 0,
        'stats_MF_Normal_Good'           : 0, 'stats_MF_Normal_Good_parents'           : 0,
        'stats_MF_Normal_Imperfect'      : 0, 'stats_MF_Normal_Imperfect_parents'      : 0,
        'stats_MF_Normal_Nonworking'     : 0, 'stats_MF_Normal_Nonworking_parents'     : 0,
        'stats_MF_Unusual_Total'         : 0, 'stats_MF_Unusual_Total_parents'         : 0,
        'stats_MF_Unusual_Good'          : 0, 'stats_MF_Unusual_Good_parents'          : 0,
        'stats_MF_Unusual_Imperfect'     : 0, 'stats_MF_Unusual_Imperfect_parents'     : 0,
        'stats_MF_Unusual_Nonworking'    : 0, 'stats_MF_Unusual_Nonworking_parents'    : 0,
        'stats_MF_Nocoin_Total'          : 0, 'stats_MF_Nocoin_Total_parents'          : 0,
        'stats_MF_Nocoin_Good'           : 0, 'stats_MF_Nocoin_Good_parents'           : 0,
        'stats_MF_Nocoin_Imperfect'      : 0, 'stats_MF_Nocoin_Imperfect_parents'      : 0,
        'stats_MF_Nocoin_Nonworking'     : 0, 'stats_MF_Nocoin_Nonworking_parents'     : 0,
        'stats_MF_Mechanical_Total'      : 0, 'stats_MF_Mechanical_Total_parents'      : 0,
        'stats_MF_Mechanical_Good'       : 0, 'stats_MF_Mechanical_Good_parents'       : 0,
        'stats_MF_Mechanical_Imperfect'  : 0, 'stats_MF_Mechanical_Imperfect_parents'  : 0,
        'stats_MF_Mechanical_Nonworking' : 0, 'stats_MF_Mechanical_Nonworking_parents' : 0,
        'stats_MF_Dead_Total'            : 0, 'stats_MF_Dead_Total_parents'            : 0,
        'stats_MF_Dead_Good'             : 0, 'stats_MF_Dead_Good_parents'             : 0,
        'stats_MF_Dead_Imperfect'        : 0, 'stats_MF_Dead_Imperfect_parents'        : 0,
        'stats_MF_Dead_Nonworking'       : 0, 'stats_MF_Dead_Nonworking_parents'       : 0,

        # --- Filed in when building the ROM audit databases ---
        'stats_audit_MAME_machines_runnable' : 0,
        # Number of ROM ZIP files in the Merged, Split or Non-merged sets.
        'stats_audit_MAME_ROM_ZIP_files' : 0,
        # Number of Sample ZIP files.
        'stats_audit_MAME_Sample_ZIP_files' : 0,
        # Number of CHD files in the Merged, Split or Non-merged sets.
        'stats_audit_MAME_CHD_files' : 0,

        # Number of machines that require one or more ROM ZIP archives to run
        'stats_audit_machine_archives_ROM'         : 0,
        'stats_audit_machine_archives_ROM_parents' : 0,
        'stats_audit_machine_archives_ROM_clones'  : 0,
        # Number of machines that require one or more CHDs to run
        'stats_audit_machine_archives_CHD'         : 0,
        'stats_audit_machine_archives_CHD_parents' : 0,
        'stats_audit_machine_archives_CHD_clones'  : 0,
        # Number of machines that require Sample ZIPs
        'stats_audit_machine_archives_Samples'         : 0,
        'stats_audit_machine_archives_Samples_parents' : 0,
        'stats_audit_machine_archives_Samples_clones'  : 0,
        # ROM less machines do not need any ZIP archive or CHD to run
        'stats_audit_archive_less'         : 0,
        'stats_audit_archive_less_parents' : 0,
        'stats_audit_archive_less_clones'  : 0,

        # ROM statistics (not implemented yet)
        'stats_audit_ROMs_total'      : 0,
        'stats_audit_ROMs_valid'      : 0,
        'stats_audit_ROMs_invalid'    : 0,
        'stats_audit_ROMs_unique'     : 0, # Not implemented
        'stats_audit_ROMs_SHA_merged' : 0, # Not implemented
        'stats_audit_CHDs_total'      : 0,
        'stats_audit_CHDs_valid'      : 0,
        'stats_audit_CHDs_invalid'    : 0,

        # --- Filed in when auditing the MAME machines ---
        # >> Machines with ROMs/CHDs archives that are OK or not
        'audit_MAME_machines_with_arch'        : 0,
        'audit_MAME_machines_with_arch_OK'     : 0,
        'audit_MAME_machines_with_arch_BAD'    : 0,
        'audit_MAME_machines_without'          : 0,
        # >> Machines with ROM archives that are OK or not
        'audit_MAME_machines_with_ROMs'        : 0,
        'audit_MAME_machines_with_ROMs_OK'     : 0,
        'audit_MAME_machines_with_ROMs_BAD'    : 0,
        'audit_MAME_machines_without_ROMs'     : 0,
        # >> Machines with Samples archives that are OK or not
        'audit_MAME_machines_with_SAMPLES'     : 0,
        'audit_MAME_machines_with_SAMPLES_OK'  : 0,
        'audit_MAME_machines_with_SAMPLES_BAD' : 0,
        'audit_MAME_machines_without_SAMPLES'  : 0,
        # >> Machines with CHDs that are OK or not
        'audit_MAME_machines_with_CHDs'        : 0,
        'audit_MAME_machines_with_CHDs_OK'     : 0,
        'audit_MAME_machines_with_CHDs_BAD'    : 0,
        'audit_MAME_machines_without_CHDs'     : 0,

        # --- Filed in when building the SL item databases ---
        # Number of SL databases (equal to the number of XML files).
        'stats_SL_XML_files' : 0,
        'stats_SL_software_items' : 0,
        # Number of SL items that require one or more ROM ZIP archives to run
        'stats_SL_items_with_ROMs' : 0,
        # Number of SL items that require one or more CHDs to run
        'stats_SL_items_with_CHDs' : 0,

        # --- Filed in when building the SL audit databases ---
        'stats_audit_SL_items_runnable'      : 0,
        'stats_audit_SL_items_with_arch'     : 0, # ROM ZIP or CHD or both
        'stats_audit_SL_items_with_arch_ROM' : 0, # At least ROM ZIP (and maybe CHD)
        'stats_audit_SL_items_with_CHD'      : 0, # At least CHD (and maybe ROM ZIP)

        # --- Filed in when auditing the SL items ---
        'audit_SL_items_runnable'          : 0,
        'audit_SL_items_with_arch'         : 0,
        'audit_SL_items_with_arch_OK'      : 0,
        'audit_SL_items_with_arch_BAD'     : 0,
        'audit_SL_items_without_arch'      : 0,
        'audit_SL_items_with_arch_ROM'     : 0,
        'audit_SL_items_with_arch_ROM_OK'  : 0,
        'audit_SL_items_with_arch_ROM_BAD' : 0,
        'audit_SL_items_without_arch_ROM'  : 0,
        'audit_SL_items_with_CHD'          : 0,
        'audit_SL_items_with_CHD_OK'       : 0,
        'audit_SL_items_with_CHD_BAD'      : 0,
        'audit_SL_items_without_CHD'       : 0,

        # --- Filed in by the MAME ROM/CHD/Samples scanner ---
        # ROM_Set_ROM_list.json database
        # Number of ROM ZIP files, including device ROMs.
        'scan_ROM_ZIP_files_total'   : 0,
        'scan_ROM_ZIP_files_have'    : 0,
        'scan_ROM_ZIP_files_missing' : 0,

        # ROM_Set_Sample_list.json
        # Number of Samples ZIP files.
        'scan_Samples_ZIP_total'   : 0,
        'scan_Samples_ZIP_have'    : 0,
        'scan_Samples_ZIP_missing' : 0,

        # ROM_Set_CHD_list.json database
        # Number of CHD files.
        'scan_CHD_files_total'   : 0,
        'scan_CHD_files_have'    : 0,
        'scan_CHD_files_missing' : 0,

        # ROM_Set_machine_files.json database
        # Number of runnable machines that need one or more ROM ZIP file to run (excluding devices).
        # Number of machines you can run, excluding devices.
        # Number of machines you cannot run, excluding devices.
        'scan_machine_archives_ROM_total'   : 0,
        'scan_machine_archives_ROM_have'    : 0,
        'scan_machine_archives_ROM_missing' : 0,

        # Sames with Samples
        'scan_machine_archives_Samples_total'   : 0,
        'scan_machine_archives_Samples_have'    : 0,
        'scan_machine_archives_Samples_missing' : 0,

        # Number of machines that need one or more CHDs to run.
        # Number of machines with CHDs you can run.
        # Number of machines with CHDs you cannot run.
        'scan_machine_archives_CHD_total'   : 0,
        'scan_machine_archives_CHD_have'    : 0,
        'scan_machine_archives_CHD_missing' : 0,

        # --- Filed in by the SL ROM/CHD scanner ---
        'scan_SL_archives_ROM_total'   : 0,
        'scan_SL_archives_ROM_have'    : 0,
        'scan_SL_archives_ROM_missing' : 0,
        'scan_SL_archives_CHD_total'   : 0,
        'scan_SL_archives_CHD_have'    : 0,
        'scan_SL_archives_CHD_missing' : 0,

        # --- Filed in by the MAME asset scanner ---
        'assets_num_MAME_machines'    : 0,
        'assets_3dbox_have'           : 0,
        'assets_3dbox_missing'        : 0,
        'assets_3dbox_alternate'      : 0,
        'assets_artpreview_have'      : 0,
        'assets_artpreview_missing'   : 0,
        'assets_artpreview_alternate' : 0,
        'assets_artwork_have'         : 0,
        'assets_artwork_missing'      : 0,
        'assets_artwork_alternate'    : 0,
        'assets_cabinets_have'        : 0,
        'assets_cabinets_missing'     : 0,
        'assets_cabinets_alternate'   : 0,
        'assets_clearlogos_have'      : 0,
        'assets_clearlogos_missing'   : 0,
        'assets_clearlogos_alternate' : 0,
        'assets_cpanels_have'         : 0,
        'assets_cpanels_missing'      : 0,
        'assets_cpanels_alternate'    : 0,
        'assets_fanarts_have'         : 0,
        'assets_fanarts_missing'      : 0,
        'assets_fanarts_alternate'    : 0,
        'assets_flyers_have'          : 0,
        'assets_flyers_missing'       : 0,
        'assets_flyers_alternate'     : 0,
        'assets_manuals_have'         : 0,
        'assets_manuals_missing'      : 0,
        'assets_manuals_alternate'    : 0,
        'assets_marquees_have'        : 0,
        'assets_marquees_missing'     : 0,
        'assets_marquees_alternate'   : 0,
        'assets_PCBs_have'            : 0,
        'assets_PCBs_missing'         : 0,
        'assets_PCBs_alternate'       : 0,
        'assets_snaps_have'           : 0,
        'assets_snaps_missing'        : 0,
        'assets_snaps_alternate'      : 0,
        'assets_titles_have'          : 0,
        'assets_titles_missing'       : 0,
        'assets_titles_alternate'     : 0,
        'assets_trailers_have'        : 0,
        'assets_trailers_missing'     : 0,
        'assets_trailers_alternate'   : 0,

        # --- Filed in by the SL asset scanner ---
        'assets_SL_num_items'           : 0,
        'assets_SL_3dbox_have'          : 0,
        'assets_SL_3dbox_missing'       : 0,
        'assets_SL_3dbox_alternate'     : 0,
        'assets_SL_titles_have'         : 0,
        'assets_SL_titles_missing'      : 0,
        'assets_SL_titles_alternate'    : 0,
        'assets_SL_snaps_have'          : 0,
        'assets_SL_snaps_missing'       : 0,
        'assets_SL_snaps_alternate'     : 0,
        'assets_SL_boxfronts_have'      : 0,
        'assets_SL_boxfronts_missing'   : 0,
        'assets_SL_boxfronts_alternate' : 0,
        'assets_SL_fanarts_have'        : 0,
        'assets_SL_fanarts_missing'     : 0,
        'assets_SL_fanarts_alternate'   : 0,
        'assets_SL_trailers_have'       : 0,
        'assets_SL_trailers_missing'    : 0,
        'assets_SL_trailers_alternate'  : 0,
        'assets_SL_manuals_have'        : 0,
        'assets_SL_manuals_missing'     : 0,
        'assets_SL_manuals_alternate'   : 0,
    }

# Safe way of change a dictionary without adding new fields.
def db_safe_edit(my_dic, field, value):
    if field in my_dic:
        my_dic[field] = value
    else:
        raise TypeError('Field {} not in dictionary'.format(field))

#
# Favourite MAME object creation.
# Simple means the main data and assets are used to created the Favourite.
# Full means that the main data, the render data and the assets are used to create the Favourite.
#
# Both functioncs create a complete Favourite. When simple() is used the machine is taken from
# the hashed database, which includes both the main and render machine data.
#
# Changes introduced in 0.9.6
# 1) fav_machine['name'] = machine_name
#
def db_get_MAME_Favourite_simple(machine_name, machine, assets, control_dic):
    fav_machine = {}

    fav_machine = copy.deepcopy(machine)
    fav_machine['name']         = machine_name
    fav_machine['ver_mame_int'] = control_dic['ver_mame_int']
    fav_machine['ver_mame_str'] = control_dic['ver_mame_str']
    fav_machine['assets']       = copy.deepcopy(assets)

    return fav_machine

def db_get_MAME_Favourite_full(machine_name, machine, machine_render, assets, control_dic):
    fav_machine = {}

    fav_machine = copy.deepcopy(machine)
    fav_machine.update(machine_render)
    fav_machine['name']         = machine_name
    fav_machine['ver_mame_int'] = control_dic['ver_mame_int']
    fav_machine['ver_mame_str'] = control_dic['ver_mame_str']
    fav_machine['assets']       = copy.deepcopy(assets)

    return fav_machine

def db_get_SL_Favourite(SL_name, ROM_name, ROM, assets, control_dic):
    fav_SL_item = {}

    SL_DB_key = SL_name + '-' + ROM_name
    fav_SL_item = copy.deepcopy(ROM)
    fav_SL_item['SL_name']        = SL_name
    fav_SL_item['SL_ROM_name']    = ROM_name
    fav_SL_item['SL_DB_key']      = SL_DB_key
    fav_SL_item['ver_mame_int']   = control_dic['ver_mame_int']
    fav_SL_item['ver_mame_str']   = control_dic['ver_mame_str']
    fav_SL_item['launch_machine'] = ''
    fav_SL_item['assets']         = copy.deepcopy(assets)

    return fav_SL_item

# Get Catalog databases
def db_get_cataloged_dic_parents(cfg, catalog_name):
    if catalog_name == 'Main':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_MAIN_PARENT_PATH.getPath())
    elif catalog_name == 'Binary':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_BINARY_PARENT_PATH.getPath())
    elif catalog_name == 'Catver':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CATVER_PARENT_PATH.getPath())
    elif catalog_name == 'Catlist':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CATLIST_PARENT_PATH.getPath())
    elif catalog_name == 'Genre':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_GENRE_PARENT_PATH.getPath())
    elif catalog_name == 'Category':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CATEGORY_PARENT_PATH.getPath())
    elif catalog_name == 'NPlayers':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_NPLAYERS_PARENT_PATH.getPath())
    elif catalog_name == 'Bestgames':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_BESTGAMES_PARENT_PATH.getPath())
    elif catalog_name == 'Series':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_SERIES_PARENT_PATH.getPath())
    elif catalog_name == 'Alltime':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_ALLTIME_PARENT_PATH.getPath())
    elif catalog_name == 'Artwork':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_ARTWORK_PARENT_PATH.getPath())
    elif catalog_name == 'Version':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_VERADDED_PARENT_PATH.getPath())
    elif catalog_name == 'Controls_Expanded':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CONTROL_EXPANDED_PARENT_PATH.getPath())
    elif catalog_name == 'Controls_Compact':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CONTROL_COMPACT_PARENT_PATH.getPath())
    elif catalog_name == 'Devices_Expanded':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DEVICE_EXPANDED_PARENT_PATH.getPath())
    elif catalog_name == 'Devices_Compact':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DEVICE_COMPACT_PARENT_PATH.getPath())
    elif catalog_name == 'Display_Type':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DISPLAY_TYPE_PARENT_PATH.getPath())
    elif catalog_name == 'Display_VSync':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DISPLAY_VSYNC_PARENT_PATH.getPath())
    elif catalog_name == 'Display_Resolution':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DISPLAY_RES_PARENT_PATH.getPath())
    elif catalog_name == 'CPU':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CPU_PARENT_PATH.getPath())
    elif catalog_name == 'Driver':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DRIVER_PARENT_PATH.getPath())
    elif catalog_name == 'Manufacturer':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_MANUFACTURER_PARENT_PATH.getPath())
    elif catalog_name == 'ShortName':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_SHORTNAME_PARENT_PATH.getPath())
    elif catalog_name == 'LongName':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_LONGNAME_PARENT_PATH.getPath())
    elif catalog_name == 'BySL':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_SL_PARENT_PATH.getPath())
    elif catalog_name == 'Year':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_YEAR_PARENT_PATH.getPath())
    else:
        log_error('db_get_cataloged_dic_parents() Unknown catalog_name = "{}"'.format(catalog_name))

    return catalog_dic

def db_get_cataloged_dic_all(cfg, catalog_name):
    if catalog_name == 'Main':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_MAIN_ALL_PATH.getPath())
    elif catalog_name == 'Binary':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_BINARY_ALL_PATH.getPath())
    elif catalog_name == 'Catver':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CATVER_ALL_PATH.getPath())
    elif catalog_name == 'Catlist':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CATLIST_ALL_PATH.getPath())
    elif catalog_name == 'Genre':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_GENRE_ALL_PATH.getPath())
    elif catalog_name == 'Category':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CATEGORY_ALL_PATH.getPath())
    elif catalog_name == 'NPlayers':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_NPLAYERS_ALL_PATH.getPath())
    elif catalog_name == 'Bestgames':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_BESTGAMES_ALL_PATH.getPath())
    elif catalog_name == 'Series':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_SERIES_ALL_PATH.getPath())
    elif catalog_name == 'Alltime':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_ALLTIME_ALL_PATH.getPath())
    elif catalog_name == 'Artwork':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_ARTWORK_ALL_PATH.getPath())
    elif catalog_name == 'Version':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_VERADDED_ALL_PATH.getPath())
    elif catalog_name == 'Controls_Expanded':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CONTROL_EXPANDED_ALL_PATH.getPath())
    elif catalog_name == 'Controls_Compact':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CONTROL_COMPACT_ALL_PATH.getPath())
    elif catalog_name == 'Devices_Expanded':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DEVICE_EXPANDED_ALL_PATH.getPath())
    elif catalog_name == 'Devices_Compact':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DEVICE_COMPACT_ALL_PATH.getPath())
    elif catalog_name == 'Display_Type':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DISPLAY_TYPE_ALL_PATH.getPath())
    elif catalog_name == 'Display_VSync':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DISPLAY_VSYNC_ALL_PATH.getPath())
    elif catalog_name == 'Display_Resolution':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DISPLAY_RES_ALL_PATH.getPath())
    elif catalog_name == 'CPU':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_CPU_ALL_PATH.getPath())
    elif catalog_name == 'Driver':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_DRIVER_ALL_PATH.getPath())
    elif catalog_name == 'Manufacturer':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_MANUFACTURER_ALL_PATH.getPath())
    elif catalog_name == 'ShortName':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_SHORTNAME_ALL_PATH.getPath())
    elif catalog_name == 'LongName':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_LONGNAME_ALL_PATH.getPath())
    elif catalog_name == 'BySL':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_SL_ALL_PATH.getPath())
    elif catalog_name == 'Year':
        catalog_dic = utils_load_JSON_file(cfg.CATALOG_YEAR_ALL_PATH.getPath())
    else:
        log_error('db_get_cataloged_dic_all() Unknown catalog_name = "{}"'.format(catalog_name))

    return catalog_dic

#
# Locates object index in a list of dictionaries by 'name' field.
# Returns -1 if object cannot be found. Uses a linear search (slow!).
#
def db_locate_idx_by_MAME_name(object_list, object_name):
    object_index = -1
    for i, machine in enumerate(object_list):
        if object_name == machine['name']:
            object_index = i
            break

    return object_index

#
# Same as previous function but on a list of Software List items
#
def db_locate_idx_by_SL_item_name(object_list, SL_name, SL_ROM_name):
    SL_fav_DB_key = SL_name + '-' + SL_ROM_name
    object_index = -1
    for i, machine in enumerate(object_list):
        if SL_fav_DB_key == machine['SL_DB_key']:
            object_index = i
            break

    return object_index

# Valid ROM: ROM has CRC hash
# Valid CHD: CHD has SHA1 hash
def db_initial_flags(machine, machine_render, m_roms):
    # Machine has own ROMs (at least one ROM is valid and has empty 'merge' attribute)
    has_own_ROMs = False
    for rom in m_roms['roms']:
        if not rom['merge'] and rom['crc']:
            has_own_ROMs = True
            break
    flag_ROM = '?' if has_own_ROMs else '-'

    # Machine has own CHDs
    has_own_CHDs = False
    for rom in m_roms['disks']:
        if not rom['merge'] and rom['sha1']:
            has_own_CHDs = True
            break
    flag_CHD = '?' if has_own_CHDs else '-'

    # Samples flag
    flag_Samples = '?' if machine['sampleof'] else '-'

    # Software List flag
    flag_SL = 'L' if machine['softwarelists'] else '-'

    # Pluggable Devices flag
    if machine['devices']:
        num_dev_mandatory = 0
        for device in machine['devices']:
            if device['att_mandatory']:
                flag_Devices = 'D'
                num_dev_mandatory += 1
            else:
                flag_Devices  = 'd'
        if num_dev_mandatory > 2:
            message = 'Machine {} has {} mandatory devices'.format(machine_name, num_dev_mandatory)
            raise CriticalError(message)
    else:
        flag_Devices  = '-'

    return '{}{}{}{}{}'.format(flag_ROM, flag_CHD, flag_Samples, flag_SL, flag_Devices)

#
# Update m_dic using Python pass by assignment.
# Remember that strings are inmutable!
#
def db_set_ROM_flag(m_dic, new_ROM_flag):
    flag_ROM = m_dic['flags'][0]
    flag_CHD = m_dic['flags'][1]
    flag_Samples = m_dic['flags'][2]
    flag_SL = m_dic['flags'][3]
    flag_Devices = m_dic['flags'][4]
    flag_ROM = new_ROM_flag
    m_dic['flags'] = '{}{}{}{}{}'.format(flag_ROM, flag_CHD, flag_Samples, flag_SL, flag_Devices)

def db_set_CHD_flag(m_dic, new_CHD_flag):
    flag_ROM = m_dic['flags'][0]
    flag_CHD = m_dic['flags'][1]
    flag_Samples = m_dic['flags'][2]
    flag_SL = m_dic['flags'][3]
    flag_Devices = m_dic['flags'][4]
    flag_CHD      = new_CHD_flag
    m_dic['flags'] = '{}{}{}{}{}'.format(flag_ROM, flag_CHD, flag_Samples, flag_SL, flag_Devices)

def db_set_Sample_flag(m_dic, new_Sample_flag):
    flag_ROM = m_dic['flags'][0]
    flag_CHD = m_dic['flags'][1]
    flag_Samples = m_dic['flags'][2]
    flag_SL = m_dic['flags'][3]
    flag_Devices = m_dic['flags'][4]
    flag_Samples  = new_Sample_flag
    m_dic['flags'] = '{}{}{}{}{}'.format(flag_ROM, flag_CHD, flag_Samples, flag_SL, flag_Devices)

# -------------------------------------------------------------------------------------------------
# MAME hashed databases. Useful when only one item in a big dictionary is required.
# -------------------------------------------------------------------------------------------------
# Hash database with 256 elements (2 hex digits)
def db_build_main_hashed_db(cfg, control_dic, machines, machines_render):
    log_info('db_build_main_hashed_db() Building main hashed database...')

    # machine_name -> MD5 -> take two letters -> aa.json, ab.json, ...
    # A) First create an index
    #    db_main_hash_idx = { 'machine_name' : 'aa', ... }
    # B) Then traverse a list [0, 1, ..., f] and write the machines in that sub database section.
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Building main hashed database...', len(machines))
    db_main_hash_idx = {}
    for key in machines:
        pDialog.updateProgressInc()
        md5_str = hashlib.md5(key.encode('utf-8')).hexdigest()
        db_name = md5_str[0:2] # WARNING Python slicing does not work like in C/C++!
        db_main_hash_idx[key] = db_name
        # log_debug('Machine {:20s} / hash {} / db file {}'.format(key, md5_str, db_name))
    pDialog.endProgress()

    hex_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    distributed_db_files = []
    for u in range(len(hex_digits)):
        for v in range(len(hex_digits)):
            distributed_db_files.append('{}{}'.format(hex_digits[u], hex_digits[v]))
    pDialog.startProgress('Building main hashed database JSON files...', len(distributed_db_files))
    for db_prefix in distributed_db_files:
        pDialog.updateProgressInc()
        # log_debug('db prefix {}'.format(db_prefix))
        # --- Generate dictionary in this JSON file ---
        hashed_db_dic = {}
        for key in db_main_hash_idx:
            if db_main_hash_idx[key] == db_prefix:
                machine_dic = machines[key].copy()
                # >> returns None because it mutates machine_dic
                machine_dic.update(machines_render[key])
                hashed_db_dic[key] = machine_dic
        # --- Save JSON file ---
        hash_DB_FN = cfg.MAIN_DB_HASH_DIR.pjoin(db_prefix + '_machines.json')
        utils_write_JSON_file(hash_DB_FN.getPath(), hashed_db_dic, verbose = False)
    pDialog.endProgress()

    # Update timestamp in control_dic.
    db_safe_edit(control_dic, 't_MAME_machine_hash', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

#
# Retrieves machine from distributed database.
# This is very quick for retrieving individual machines, very slow for multiple machines.
#
def db_get_machine_main_hashed_db(cfg, machine_name):
    log_debug('db_get_machine_main_hashed_db() machine {}'.format(machine_name))
    md5_str = hashlib.md5(machine_name.encode('utf-8')).hexdigest()
    # WARNING Python slicing does not work like in C/C++!
    hash_DB_FN = cfg.MAIN_DB_HASH_DIR.pjoin(md5_str[0:2] + '_machines.json')
    hashed_db_dic = utils_load_JSON_file(hash_DB_FN.getPath())

    return hashed_db_dic[machine_name]

# MAME hash database with 256 elements (2 hex digits)
def db_build_asset_hashed_db(cfg, control_dic, assets_dic):
    log_info('db_build_asset_hashed_db() Building assets hashed database ...')

    # machine_name -> MD5 -> take two letters -> aa.json, ab.json, ...
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Building asset hashed database...', len(assets_dic))
    db_main_hash_idx = {}
    for key in assets_dic:
        pDialog.updateProgressInc()
        md5_str = hashlib.md5(key.encode('utf-8')).hexdigest()
        db_name = md5_str[0:2] # WARNING Python slicing does not work like in C/C++!
        db_main_hash_idx[key] = db_name
        # log_debug('Machine {:20s} / hash {} / db file {}'.format(key, md5_str, db_name))
    pDialog.endProgress()

    hex_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    distributed_db_files = []
    for u in range(len(hex_digits)):
        for v in range(len(hex_digits)):
            distributed_db_files.append('{}{}'.format(hex_digits[u], hex_digits[v]))
    pDialog.startProgress('Building asset hashed database JSON files...', len(distributed_db_files))
    for db_prefix in distributed_db_files:
        pDialog.updateProgressInc()
        hashed_db_dic = {}
        for key in db_main_hash_idx:
            if db_main_hash_idx[key] == db_prefix:
                hashed_db_dic[key] = assets_dic[key]
        hash_DB_FN = cfg.MAIN_DB_HASH_DIR.pjoin(db_prefix + '_assets.json')
        utils_write_JSON_file(hash_DB_FN.getPath(), hashed_db_dic, verbose = False)
    pDialog.endProgress()

    # --- Timestamp ---
    db_safe_edit(control_dic, 't_MAME_asset_hash', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

#
# Retrieves machine from distributed hashed database.
# This is very quick for retrieving individual machines, slow for multiple machines.
#
def db_get_machine_assets_hashed_db(cfg, machine_name):
    log_debug('db_get_machine_assets_hashed_db() machine {}'.format(machine_name))
    md5_str = hashlib.md5(machine_name.encode('utf-8')).hexdigest()
    hash_DB_FN = cfg.MAIN_DB_HASH_DIR.pjoin(md5_str[0:2] + '_assets.json')
    hashed_db_dic = utils_load_JSON_file(hash_DB_FN.getPath())

    return hashed_db_dic[machine_name]

# -------------------------------------------------------------------------------------------------
# MAME machine render cache
# Creates a separate MAME render and assets databases for each catalog to speed up
# access of ListItems when rendering machine lists.
# -------------------------------------------------------------------------------------------------
def db_cache_get_key(catalog_name, category_name):
    return hashlib.md5('{} - {}'.format(catalog_name, category_name).encode('utf-8')).hexdigest()

def db_build_render_cache(cfg, control_dic, cache_index_dic, machines_render, force_build = False):
    log_info('db_build_render_cache() Initialising...')
    log_debug('debug_enable_MAME_render_cache is {}'.format(cfg.settings['debug_enable_MAME_render_cache']))
    log_debug('force_build is {}'.format(force_build))
    if not cfg.settings['debug_enable_MAME_render_cache'] and not force_build:
        log_info('db_build_render_cache() Render cache disabled.')
        return
    # Notify user this is a forced build.
    if not cfg.settings['debug_enable_MAME_render_cache'] and force_build:
        t = 'MAME render cache disabled but forcing rebuilding.'
        log_info(t)
        kodi_dialog_OK(t)

    # --- Clean 'cache' directory JSON ROM files ---
    log_info('Cleaning dir "{}"'.format(cfg.CACHE_DIR.getPath()))
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Listing render cache JSON files...')
    file_list = os.listdir(cfg.CACHE_DIR.getPath())
    log_info('Found {} files'.format(len(file_list)))
    deleted_items = 0
    pDialog.resetProgress('Cleaning render cache JSON files...', len(file_list))
    for file in file_list:
        pDialog.updateProgressInc()
        if not file.endswith('_render.json'): continue
        full_path = os.path.join(cfg.CACHE_DIR.getPath(), file)
        # log_debug('UNLINK "{}"'.format(full_path))
        os.unlink(full_path)
        deleted_items += 1
    pDialog.endProgress()
    log_info('Deleted {} files'.format(deleted_items))

    # --- Build ROM cache ---
    num_catalogs = len(cache_index_dic)
    catalog_count = 1
    pDialog.startProgress('Building MAME render cache')
    for catalog_name in sorted(cache_index_dic):
        catalog_index_dic = cache_index_dic[catalog_name]
        catalog_all = db_get_cataloged_dic_all(cfg, catalog_name)
        diag_t = 'Building MAME [COLOR orange]{}[/COLOR] render cache ({} of {})...'.format(
            catalog_name, catalog_count, num_catalogs)
        pDialog.resetProgress(diag_t, len(catalog_index_dic))
        for catalog_key in catalog_index_dic:
            pDialog.updateProgressInc()
            hash_str = catalog_index_dic[catalog_key]['hash']
            # log_debug('db_build_ROM_cache() Catalog "{}" --- Key "{}"'.format(catalog_name, catalog_key))
            # log_debug('db_build_ROM_cache() hash {}'.format(hash_str))

            # Build all machines cache
            m_render_all_dic = {}
            for machine_name in catalog_all[catalog_key]:
                m_render_all_dic[machine_name] = machines_render[machine_name]
            ROMs_all_FN = cfg.CACHE_DIR.pjoin(hash_str + '_render.json')
            utils_write_JSON_file(ROMs_all_FN.getPath(), m_render_all_dic, verbose = False)
        catalog_count += 1
    pDialog.endProgress()

    # --- Timestamp ---
    db_safe_edit(control_dic, 't_MAME_render_cache_build', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

def db_get_render_cache_row(cfg, cache_index_dic, catalog_name, category_name):
    hash_str = cache_index_dic[catalog_name][category_name]['hash']
    ROMs_all_FN = cfg.CACHE_DIR.pjoin(hash_str + '_render.json')

    return utils_load_JSON_file(ROMs_all_FN.getPath())

# -------------------------------------------------------------------------------------------------
# MAME asset cache
# -------------------------------------------------------------------------------------------------
def db_build_asset_cache(cfg, control_dic, cache_index_dic, assets_dic, force_build = False):
    log_info('db_build_asset_cache() Initialising...')
    log_debug('debug_enable_MAME_asset_cache is {}'.format(cfg.settings['debug_enable_MAME_asset_cache']))
    log_debug('force_build is {}'.format(force_build))
    if not cfg.settings['debug_enable_MAME_asset_cache'] and not force_build:
        log_info('db_build_asset_cache() Asset cache disabled.')
        return
    # Notify user this is a forced build.
    if not cfg.settings['debug_enable_MAME_render_cache'] and force_build:
        t = 'MAME asset cache disabled but forcing rebuilding.'
        log_info(t)
        kodi_dialog_OK(t)

    # --- Clean 'cache' directory JSON Asset files ---
    log_info('Cleaning dir "{}"'.format(cfg.CACHE_DIR.getPath()))
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Listing asset cache JSON files...')
    file_list = os.listdir(cfg.CACHE_DIR.getPath())
    log_info('Found {} files'.format(len(file_list)))
    deleted_items = 0
    pDialog.resetProgress('Cleaning asset cache JSON files...', len(file_list))
    for file in file_list:
        pDialog.updateProgressInc()
        if not file.endswith('_assets.json'): continue
        full_path = os.path.join(cfg.CACHE_DIR.getPath(), file)
        # log_debug('UNLINK "{}"'.format(full_path))
        os.unlink(full_path)
        deleted_items += 1
    pDialog.endProgress()
    log_info('Deleted {} files'.format(deleted_items))

    # --- Build MAME asset cache ---
    num_catalogs = len(cache_index_dic)
    catalog_count = 1
    pDialog.startProgress('Building MAME asset cache')
    for catalog_name in sorted(cache_index_dic):
        catalog_index_dic = cache_index_dic[catalog_name]
        catalog_all = db_get_cataloged_dic_all(cfg, catalog_name)
        diag_t = 'Building MAME [COLOR orange]{}[/COLOR] asset cache ({} of {})...'.format(
            catalog_name, catalog_count, num_catalogs)
        pDialog.resetProgress(diag_t, len(catalog_index_dic))
        for catalog_key in catalog_index_dic:
            pDialog.updateProgressInc()
            hash_str = catalog_index_dic[catalog_key]['hash']
            # log_debug('db_build_asset_cache() Catalog "{}" --- Key "{}"'.format(catalog_name, catalog_key))
            # log_debug('db_build_asset_cache() hash {}'.format(hash_str))

            # Build all machines cache
            m_assets_all_dic = {}
            for machine_name in catalog_all[catalog_key]:
                m_assets_all_dic[machine_name] = assets_dic[machine_name]
            ROMs_all_FN = cfg.CACHE_DIR.pjoin(hash_str + '_assets.json')
            utils_write_JSON_file(ROMs_all_FN.getPath(), m_assets_all_dic, verbose = False)
        catalog_count += 1
    pDialog.endProgress()

    # Update timestamp and save control_dic.
    db_safe_edit(control_dic, 't_MAME_asset_cache_build', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

def db_get_asset_cache_row(cfg, cache_index_dic, catalog_name, category_name):
    hash_str = cache_index_dic[catalog_name][category_name]['hash']
    ROMs_all_FN = cfg.CACHE_DIR.pjoin(hash_str + '_assets.json')

    return utils_load_JSON_file(ROMs_all_FN.getPath())

# -------------------------------------------------------------------------------------------------
# Load and save a bunch of JSON files
# -------------------------------------------------------------------------------------------------
#
# Accepts a list of JSON files to be loaded. Displays a progress dialog.
# Returns a dictionary with the context of the loaded files.
#
def db_load_files(db_files):
    log_debug('db_load_files() Loading {} JSON database files...'.format(len(db_files)))
    db_dic = {}
    d_text = 'Loading databases...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(d_text, len(db_files))
    for f_item in db_files:
        dict_key, db_name, db_path = f_item
        pDialog.updateProgressInc('{}\nDatabase [COLOR orange]{}[/COLOR]'.format(d_text, db_name))
        db_dic[dict_key] = utils_load_JSON_file(db_path)
    pDialog.endProgress()

    return db_dic

def db_save_files(db_files, json_write_func = utils_write_JSON_file):
    log_debug('db_save_files() Saving {} JSON database files...'.format(len(db_files)))
    d_text = 'Saving databases...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(d_text, len(db_files))
    for f_item in db_files:
        dict_data, db_name, db_path = f_item
        pDialog.updateProgressInc('{}\nDatabase [COLOR orange]{}[/COLOR]'.format(d_text, db_name))
        json_write_func(db_path, dict_data)
    pDialog.endProgress()

# -------------------------------------------------------------------------------------------------
# Export stuff
# -------------------------------------------------------------------------------------------------
def db_export_Read_Only_Launcher(export_FN, catalog_dic, machines, machines_render, assets_dic):
    log_debug('db_export_Read_Only_Launcher() File "{}"'.format(export_FN.getPath()))

    # Create list of strings.
    sl = []
    sl.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')
    sl.append('<!-- Exported by AML on {} -->'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    sl.append('<advanced_MAME_launcher_virtual_launcher>')
    for m_name, r_name in catalog_dic.items():
        sl.append('<machine>')
        sl.append(XML_text('name', m_name))
        sl.append(XML_text('description', machines_render[m_name]['description']))
        sl.append(XML_text('genre', machines_render[m_name]['genre']))
        sl.append(XML_text('year', machines_render[m_name]['year']))
        sl.append(XML_text('cabinet', assets_dic[m_name]['cabinet']))
        sl.append('</machine>')
    sl.append('</advanced_MAME_launcher_virtual_launcher>')
    utils_write_str_list_to_file(sl, export_FN)
