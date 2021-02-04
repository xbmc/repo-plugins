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

# Advanced MAME Launcher miscellaneous MAME functions.
#
# Functions in this module only depend on the Python standard library.
# This module can be loaded anywhere without creating circular dependencies.
# Optionally this module can include utils.py to use the log_*() functions.

# --- Be prepared for the future ---
from __future__ import unicode_literals
from __future__ import division

# --- AEL packages ---

# --- Python standard library ---
import hashlib

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
# Builds a string separated by a | character. Replaces | occurrences with _
# The string can be separated with text_type.split('|')
def misc_build_db_str_3(str1, str2, str3):
    if str1.find('|') >= 0: str1 = str1.replace('|', '_')
    if str2.find('|') >= 0: str2 = str2.replace('|', '_')
    if str3.find('|') >= 0: str3 = str3.replace('|', '_')

    return '{}|{}|{}'.format(str1, str2, str3)

# Used in mame_build_MAME_plots()
def misc_get_mame_control_str(control_type_list):
    control_set = set()
    improved_c_type_list = misc_improve_mame_control_type_list(control_type_list)
    for control in improved_c_type_list: control_set.add(control)
    control_str = ', '.join(list(sorted(control_set)))

    return control_str

# Used here in misc_get_mame_screen_str()
def misc_get_mame_screen_rotation_str(display_rotate):
    if display_rotate == '0' or display_rotate == '180':
        screen_str = 'horizontal'
    elif display_rotate == '90' or display_rotate == '270':
        screen_str = 'vertical'
    else:
        raise TypeError

    return screen_str

# Used in mame_build_MAME_plots()
def misc_get_mame_screen_str(machine_name, machine):
    d_list = machine['display_type']
    if d_list:
        if len(d_list) == 1:
            rotation_str = misc_get_mame_screen_rotation_str(machine['display_rotate'][0])
            screen_str = 'One {} {} screen'.format(d_list[0], rotation_str)
        elif len(d_list) == 2:
            if d_list[0] == 'lcd' and d_list[1] == 'raster':
                r_str_1 = misc_get_mame_screen_rotation_str(machine['display_rotate'][0])
                r_str_2 = misc_get_mame_screen_rotation_str(machine['display_rotate'][1])
                screen_str = 'One LCD {} screen and one raster {} screen'.format(r_str_1, r_str_2)
            elif d_list[0] == 'raster' and d_list[1] == 'raster':
                r_str = misc_get_mame_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Two raster {} screens'.format(r_str)
            elif d_list[0] == 'svg' and d_list[1] == 'svg':
                r_str = misc_get_mame_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Two SVG {} screens'.format(r_str)
            elif d_list[0] == 'unknown' and d_list[1] == 'unknown':
                screen_str = 'Two unknown screens'
            else:
                screen_str = 'Two unrecognised screens'
        elif len(d_list) == 3:
            if d_list[0] == 'raster' and d_list[1] == 'raster' and d_list[2] == 'raster':
                r_str = misc_get_mame_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Three raster {} screens'.format(r_str)
            elif d_list[0] == 'raster' and d_list[1] == 'lcd' and d_list[2] == 'lcd':
                screen_str = 'Three screens special case'
            else:
                screen_str = 'Three unrecognised screens'
        elif len(d_list) == 4:
            if d_list[0] == 'raster' and d_list[1] == 'raster' and d_list[2] == 'raster' and d_list[3] == 'raster':
                r_str = misc_get_mame_screen_rotation_str(machine['display_rotate'][0])
                screen_str = 'Four raster {} screens'.format(r_str)
            else:
                screen_str = 'Four unrecognised screens'
        elif len(d_list) == 5:
            screen_str = 'Five unrecognised screens'
        elif len(d_list) == 6:
            screen_str = 'Six unrecognised screens'
        else:
            log_error('mame_get_screen_str() d_list = {}'.format(text_type(d_list)))
            raise TypeError
    else:
        screen_str = 'No screen'

    return screen_str

def misc_get_mame_display_type(display_str):
    if   display_str == 'lcd':    display_name = 'LCD'
    elif display_str == 'raster': display_name = 'Raster'
    elif display_str == 'svg':    display_name = 'SVG'
    elif display_str == 'vector': display_name = 'Vector'
    else:                         display_name = display_str

    return display_name

def misc_get_mame_display_rotation(d_str):
    if d_str == '0' or d_str == '180':
        rotation_letter = 'Hor'
    elif d_str == '90' or d_str == '270':
        rotation_letter = 'Ver'
    else:
        raise TypeError('Wrong display rotate "{}"'.format(d_str))

    return rotation_letter

def misc_get_display_type_catalog_key(display_type_list, display_rotate_list):
    if len(display_type_list) == 0:
        catalog_key = '[ No display ]'
    else:
        display_list = []
        for dis_index in range(len(display_type_list)):
            display_name = misc_get_mame_display_type(display_type_list[dis_index])
            display_rotation = misc_get_mame_display_rotation(display_rotate_list[dis_index])
            display_list.append('{} {}'.format(display_name, display_rotation))
        catalog_key = " / ".join(display_list)

    return catalog_key

def misc_get_display_resolution_catalog_key(display_width, display_height):
    if len(display_width) > 1 or len(display_height) > 1:
        catalog_key = '{} displays'.format(len(display_width))
    elif len(display_width) == 0 and len(display_height) == 1:
        catalog_key = 'Empty x {}'.format(display_height[0])
    elif len(display_width) == 1 and len(display_height) == 0:
        catalog_key = '{} x Empty'.format(display_width[0])
    elif len(display_width) == 0 and len(display_height) == 0:
        catalog_key = 'Empty x Empty'
    else:
        catalog_key = '{} x {}'.format(display_width[0], display_height[0])

    return catalog_key

#
# A) Capitalise every list item
# B) Substitute Only_buttons -> Only buttons
#
def misc_improve_mame_control_type_list(control_type_list):
    out_list = []
    for control_str in control_type_list:
        capital_str = control_str.title()
        if capital_str == 'Only_Buttons': capital_str = 'Only Buttons'
        out_list.append(capital_str)

    return out_list

#
# A) Capitalise every list item
#
def misc_improve_mame_device_list(control_type_list):
    out_list = []
    for control_str in control_type_list: out_list.append(control_str.title())

    return out_list

#
# A) Substitute well know display types with fancier names.
#
def misc_improve_mame_display_type_list(display_type_list):
    out_list = []
    for dt in display_type_list:
        if   dt == 'lcd':    out_list.append('LCD')
        elif dt == 'raster': out_list.append('Raster')
        elif dt == 'svg':    out_list.append('SVG')
        elif dt == 'vector': out_list.append('Vector')
        else:                out_list.append(dt)

    return out_list

#
# See tools/test_compress_item_list.py for reference
# Input/Output examples:
# 1) ['dial']                 ->  ['dial']
# 2) ['dial', 'dial']         ->  ['2 x dial']
# 3) ['dial', 'dial', 'joy']  ->  ['2 x dial', 'joy']
# 4) ['joy', 'dial', 'dial']  ->  ['joy', '2 x dial']
#
def misc_compress_mame_item_list(item_list):
    reduced_list = []
    num_items = len(item_list)
    if num_items == 0 or num_items == 1: return item_list
    previous_item = item_list[0]
    item_count = 1
    for i in range(1, num_items):
        current_item = item_list[i]
        # log_debug('{} | item_count {} | previous_item "{2:>8}" | current_item "{3:>8}"'.format(
        #     i, item_count, previous_item, current_item))
        if current_item == previous_item:
            item_count += 1
        else:
            if item_count == 1: reduced_list.append('{}'.format(previous_item))
            else:               reduced_list.append('{} {}'.format(item_count, previous_item))
            item_count = 1
            previous_item = current_item
        # >> Last elemnt of the list
        if i == num_items - 1:
            if current_item == previous_item:
                if item_count == 1: reduced_list.append('{}'.format(current_item))
                else:               reduced_list.append('{} {}'.format(item_count, current_item))
            else:
               reduced_list.append('{}'.format(current_item))

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
def misc_compress_mame_item_list_compact(item_list):
    num_items = len(item_list)
    if num_items == 0 or num_items == 1: return item_list
    item_set = set(item_list)
    reduced_list = list(item_set)
    reduced_list_sorted = sorted(reduced_list)

    return reduced_list_sorted

# -------------------------------------------------------------------------------------------------
# Helper functions to build catalogs.
# -------------------------------------------------------------------------------------------------
# Add clones to the all catalog dictionary catalog_all_dic.
# catalog_all_dic is modified by refence.
def mame_catalog_add_clones(parent_name, main_pclone_dic, machines_render, catalog_all_dic):
    for clone_name in main_pclone_dic[parent_name]:
        catalog_all_dic[clone_name] = machines_render[clone_name]['description']

# Do not store the number of categories in a catalog. If necessary, calculate it on the fly.
# I think Python len() on dictionaries is very fast.
# [August 2020] Why???
def mame_cache_index_builder(cat_name, cache_index_dic, catalog_all, catalog_parents):
    for cat_key in catalog_all:
        key_str = '{} - {}'.format(cat_name, cat_key)
        cache_index_dic[cat_name][cat_key] = {
            'num_parents'  : len(catalog_parents[cat_key]),
            'num_machines' : len(catalog_all[cat_key]),
            # Make sure this key is the same as db_render_cache_get_hash()
            'hash'         : hashlib.md5(key_str.encode('utf-8')).hexdigest(),
        }

# Helper functions to get the catalog key.
def mame_catalog_key_Catver(parent_name, machines, machines_render):
    return [ machines[parent_name]['catver'] ]

def mame_catalog_key_Catlist(parent_name, machines, machines_render):
    return [ machines[parent_name]['catlist'] ]

def mame_catalog_key_Genre(parent_name, machines, machines_render):
    return [ machines[parent_name]['genre'] ]

def mame_catalog_key_Category(parent_name, machines, machines_render):
    # Already a list.
    return machines[parent_name]['category']

def mame_catalog_key_NPlayers(parent_name, machines, machines_render):
    return [ machines[parent_name]['nplayers'] ]

def mame_catalog_key_Bestgames(parent_name, machines, machines_render):
    return [ machines[parent_name]['bestgames'] ]

def mame_catalog_key_Series(parent_name, machines, machines_render):
    # Already a list.
    return machines[parent_name]['series']

def mame_catalog_key_Alltime(parent_name, machines, machines_render):
    # log_debug('Machine {}, key {}'.format(parent_name, machines[parent_name]['alltime']))
    return [ machines[parent_name]['alltime'] ]

def mame_catalog_key_Artwork(parent_name, machines, machines_render):
    # Already a list.
    return machines[parent_name]['artwork']

def mame_catalog_key_VerAdded(parent_name, machines, machines_render):
    return [ machines[parent_name]['veradded'] ]

def mame_catalog_key_Controls_Expanded(parent_name, machines, machines_render):
    machine = machines[parent_name]
    machine_render = machines_render[parent_name]
    # Order alphabetically the list
    # In MAME 2003 Plus machine['input'] may be an empty dictionary.
    if machine['input'] and machine['input']['control_list']:
        control_list = [ctrl_dic['type'] for ctrl_dic in machine['input']['control_list']]
        pretty_control_type_list = misc_improve_mame_control_type_list(control_list)
        sorted_control_type_list = sorted(pretty_control_type_list)
        # Maybe a setting should be added for compact or non-compact control list.
        # sorted_control_type_list = misc_compress_mame_item_list(sorted_control_type_list)
        sorted_control_type_list = misc_compress_mame_item_list_compact(sorted_control_type_list)
        catalog_key_list = [ " / ".join(sorted_control_type_list) ]
    else:
        catalog_key_list = [ '[ No controls ]' ]

    return catalog_key_list

def mame_catalog_key_Controls_Compact(parent_name, machines, machines_render):
    machine = machines[parent_name]
    machine_render = machines_render[parent_name]
    # Order alphabetically the list
    # In MAME 2003 Plus machine['input'] may be an empty dictionary.
    if machine['input'] and machine['input']['control_list']:
        control_list = [ctrl_dic['type'] for ctrl_dic in machine['input']['control_list']]
        pretty_control_type_list = misc_improve_mame_control_type_list(control_list)
        sorted_control_type_list = sorted(pretty_control_type_list)
        catalog_key_list = misc_compress_mame_item_list_compact(sorted_control_type_list)
    else:
        catalog_key_list = [ '[ No controls ]' ]

    return catalog_key_list

def mame_catalog_key_Devices_Expanded(parent_name, machines, machines_render):
    machine = machines[parent_name]
    machine_render = machines_render[parent_name]
    # Order alphabetically the list
    device_list = [device['att_type'] for device in machine['devices']]
    pretty_device_list = misc_improve_mame_device_list(device_list)
    sorted_device_list = sorted(pretty_device_list)
    # Maybe a setting should be added for compact or non-compact control list
    # sorted_device_list = misc_compress_mame_item_list(sorted_device_list)
    sorted_device_list = misc_compress_mame_item_list_compact(sorted_device_list)
    catalog_key = " / ".join(sorted_device_list)
    # Change category name for machines with no devices
    if catalog_key == '':
        catalog_key = '[ No devices ]'

    return [catalog_key]

def mame_catalog_key_Devices_Compact(parent_name, machines, machines_render):
    machine = machines[parent_name]
    machine_render = machines_render[parent_name]
    # Order alphabetically the list
    device_list = [ device['att_type'] for device in machine['devices'] ]
    pretty_device_list = misc_improve_mame_device_list(device_list)
    sorted_device_list = sorted(pretty_device_list)
    compressed_device_list = misc_compress_mame_item_list_compact(sorted_device_list)
    if not compressed_device_list:
        compressed_device_list = [ '[ No devices ]' ]

    return compressed_device_list

def mame_catalog_key_Display_Type(parent_name, machines, machines_render):
    # Compute the catalog_key. display_type and display_rotate main DB entries used.
    catalog_key = misc_get_display_type_catalog_key(
        machines[parent_name]['display_type'], machines[parent_name]['display_rotate'])

    return [catalog_key]

def mame_catalog_key_Display_VSync(parent_name, machines, machines_render):
    catalog_list = []
    # machine['display_refresh'] is a list.
    # Change string '60.12346' to 1 decimal only to avoid having a log of keys in this catalog.
    # An empty machine['display_refresh'] means no display.
    if len(machines[parent_name]['display_refresh']) == 0:
        catalog_list.append('No display')
    else:
        for display_str in machines[parent_name]['display_refresh']:
            vsync = float(display_str)
            catalog_list.append('{0:.1f} Hz'.format(vsync))

    return catalog_list

def mame_catalog_key_Display_Resolution(parent_name, machines, machines_render):
    # Move code of this function here???
    catalog_key = misc_get_display_resolution_catalog_key(
        machines[parent_name]['display_width'], machines[parent_name]['display_height'])

    return [catalog_key]

def mame_catalog_key_CPU(parent_name, machines, machines_render):
    # machine['chip_cpu_name'] is a list.
    return machines[parent_name]['chip_cpu_name']

# Some drivers get a prettier name.
# def mame_catalog_key_Driver(parent_name, machines, machines_render):
#     c_key = machines[parent_name]['sourcefile']
#     c_key = mame_driver_name_dic[c_key] if c_key in mame_driver_name_dic else c_key
#
#     return [c_key]

def mame_catalog_key_Manufacturer(parent_name, machines, machines_render):
    return [machines_render[parent_name]['manufacturer']]

# This is a special catalog, not easy to automatise.
# def mame_catalog_key_ShortName(parent_name, machines, machines_render):
#     return [machines_render[parent_name]['year']]

def mame_catalog_key_LongName(parent_name, machines, machines_render):
    return [machines_render[parent_name]['description'][0]]

# This is a special catalog, not easy to automatise.
# def mame_catalog_key_BySL(parent_name, machines, machines_render):
#     return [machines_render[parent_name]['year']]

def mame_catalog_key_Year(parent_name, machines, machines_render):
    return [machines_render[parent_name]['year']]

# Uses a "function pointer" to obtain the catalog_key.
# catalog_key is a list that has one element for most catalogs.
# In some catalogs (Controls_Compact) this list has sometimes more than one item, for example
# one parent machine may have more than one control.
def mame_build_catalog_helper(catalog_parents, catalog_all,
    machines, machines_render, main_pclone_dic, catalog_key_function):
    for parent_name in main_pclone_dic:
        render = machines_render[parent_name]
        if render['isDevice']: continue # Skip device machines in catalogs.
        catalog_key_list = catalog_key_function(parent_name, machines, machines_render)
        for catalog_key in catalog_key_list:
            if catalog_key in catalog_parents:
                catalog_parents[catalog_key][parent_name] = render['description']
                catalog_all[catalog_key][parent_name] = render['description']
            else:
                catalog_parents[catalog_key] = { parent_name : render['description'] }
                catalog_all[catalog_key] = { parent_name : render['description'] }
            for clone_name in main_pclone_dic[parent_name]:
                catalog_all[catalog_key][clone_name] = machines_render[clone_name]['description']
