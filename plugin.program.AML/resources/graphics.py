# -*- coding: utf-8 -*-

# Advanced MAME Launcher graphics plotting functions.

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

# --- Python standard library ---
# Division operator: https://www.python.org/dev/peps/pep-0238/
from __future__ import unicode_literals
from __future__ import division
from collections import OrderedDict
import time
import xml.etree.ElementTree as ET
try:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
    PILLOW_AVAILABLE = True
except:
    PILLOW_AVAILABLE = False

# --- Modules/packages in this addon ---
from .constants import *
from .disk_IO import *
from .utils import *
from .utils_kodi import *

# ------------------------------------------------------------------------------------------------
# ETA
# ------------------------------------------------------------------------------------------------
# Global variables to keep ETA status.
ETA_total_items = 0
ETA_actual_processed_items = 0
ETA_total_build_time = 0.0
ETA_average_build_time = 0.0

#
# Returns initial ETA_str
#
def ETA_reset(total_items):
    global ETA_total_items
    global ETA_actual_processed_items
    global ETA_total_build_time
    global ETA_average_build_time

    ETA_total_items = total_items
    ETA_actual_processed_items = 0
    ETA_total_build_time = 0.0
    ETA_average_build_time = 0.0

    return 'calculating'

#
# BUILD_SUCCESS True if image was generated correctly (time is accurate)
#
def ETA_update(build_OK_flag, total_processed_items, build_time):
    global ETA_actual_processed_items
    global ETA_total_build_time
    global ETA_average_build_time

    if build_OK_flag:
        ETA_actual_processed_items += 1
        ETA_total_build_time += build_time
        ETA_average_build_time = ETA_total_build_time / ETA_actual_processed_items
    remaining_items = ETA_total_items - total_processed_items
    # log_debug('build_time                 {0}'.format(build_time))
    # log_debug('ETA_average_build_time     {0}'.format(ETA_average_build_time))
    # log_debug('ETA_actual_processed_items {0}'.format(ETA_actual_processed_items))
    # log_debug('total_processed_items      {0}'.format(total_processed_items))
    # log_debug('remaining items            {0}'.format(remaining_items))
    if ETA_average_build_time > 0:
        ETA_s = remaining_items * ETA_average_build_time
        hours, minutes, seconds = int(ETA_s // 3600), int((ETA_s % 3600) // 60), int(ETA_s % 60)
        ETA_str = '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)
    else:
        ETA_str = 'calculating'

    return ETA_str

# ------------------------------------------------------------------------------------------------
# Math functions
# ------------------------------------------------------------------------------------------------
# Here is a more elegant and scalable solution, imo. It'll work for any nxn matrix and 
# you may find use for the other methods. Note that getMatrixInverse(m) takes in an 
# array of arrays as input.
def math_MatrixTranspose(X):
    # return map(list, zip(*X))
    return [[X[j][i] for j in range(len(X))] for i in range(len(X[0]))]

def math_MatrixMinor(m, i, j):
    return [row[:j] + row[j+1:] for row in (m[:i]+m[i+1:])]

def math_MatrixDeterminant(m):
    # Base case for 2x2 matrix
    if len(m) == 2:
        return m[0][0]*m[1][1]-m[0][1]*m[1][0]

    determinant = 0
    for c in range(len(m)):
        determinant += ((-1)**c)*m[0][c]*math_MatrixDeterminant(math_MatrixMinor(m,0,c))

    return determinant

def math_MatrixInverse(m):
    determinant = math_MatrixDeterminant(m)

    # Special case for 2x2 matrix:
    if len(m) == 2:
        return [
            [m[1][1]/determinant, -1*m[0][1]/determinant],
            [-1*m[1][0]/determinant, m[0][0]/determinant],
        ]

    # Find matrix of cofactors
    cofactors = []
    for r in range(len(m)):
        cofactorRow = []
        for c in range(len(m)):
            minor = math_MatrixMinor(m,r,c)
            cofactorRow.append(((-1)**(r+c)) * math_MatrixDeterminant(minor))
        cofactors.append(cofactorRow)
    cofactors = math_MatrixTranspose(cofactors)
    for r in range(len(cofactors)):
        for c in range(len(cofactors)):
            cofactors[r][c] = cofactors[r][c]/determinant

    return cofactors

# Both A and B have sizes NxM where N, M >= 2 (list of lists of floats).
def math_MatrixProduct(A, B):
    return [[sum(a*b for a,b in zip(A_row, B_col)) for B_col in zip(*B)] for A_row in A]

# A is a MxN matrix, B is a Nx1 matrix, result is a Mx1 matrix given as a list.
# Returns a list with the result. Note that this list corresponds to a column matrix.
def math_MatrixProduct_Column(A, B):
    return [sum(a*b for a,b in zip(A_row, B)) for A_row in A]

# ------------------------------------------------------------------------------------------------
# Auxiliar functions
# ------------------------------------------------------------------------------------------------
#
# Scales and centers img into a box of size (box_x_size, box_y_size).
# Scaling keeps original img aspect ratio.
# Returns an image of size (box_x_size, box_y_size)
#
def resize_proportional(img, layout, dic_key, CANVAS_COLOR = (0, 0, 0)):
    box_x_size = layout[dic_key]['width']
    box_y_size = layout[dic_key]['height']
    # log_debug('resize_proportional() Initialising ...')
    # log_debug('img X_size = {0} | Y_size = {1}'.format(img.size[0], img.size[1]))
    # log_debug('box X_size = {0} | Y_size = {1}'.format(box_x_size, box_y_size))

    # --- First try to fit X dimension ---
    # log_debug('resize_proportional() Fitting X dimension')
    wpercent = (box_x_size / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    r_x_size = box_x_size
    r_y_size = hsize
    x_offset = 0
    y_offset = int((box_y_size - r_y_size) / 2)
    # log_debug('resize X_size = {0} | Y_size = {1}'.format(r_x_size, r_y_size))
    # log_debug('resize x_offset = {0} | y_offset = {1}'.format(x_offset, y_offset))

    # --- Second try to fit Y dimension ---
    if y_offset < 0:
        # log_debug('Fitting Y dimension')
        hpercent = (box_y_size / float(img.size[1]))
        wsize = int((float(img.size[0]) * float(hpercent)))
        r_x_size = wsize
        r_y_size = box_y_size
        x_offset = int((box_x_size - r_x_size) / 2)
        y_offset = 0
        # log_debug('resize X_size = {0} | Y_size = {1}'.format(r_x_size, r_y_size))
        # log_debug('resize x_offset = {0} | y_offset = {1}'.format(x_offset, y_offset))

    # >> Create a new image and paste original image centered.
    canvas_img = Image.new('RGB', (box_x_size, box_y_size), CANVAS_COLOR)
    # >> Resize and paste
    img = img.resize((r_x_size, r_y_size), Image.ANTIALIAS)
    canvas_img.paste(img, (x_offset, y_offset, x_offset + r_x_size, y_offset + r_y_size))

    return canvas_img

def paste_image(img, img_title, layout, dic_key):
    box = (
        layout[dic_key]['left'],
        layout[dic_key]['top'], 
        layout[dic_key]['left'] + layout[dic_key]['width'],
        layout[dic_key]['top']  + layout[dic_key]['height']
    )
    img.paste(img_title, box)

    return img

# source_coords is the four vertices in the current plane and target_coords contains
# four vertices in the resulting plane.
# coords is a list of tuples (x, y)
#
def perspective_coeffs(source_coords, target_coords):
    A = []
    for s, t in zip(source_coords, target_coords):
        s = [float(i) for i in s]
        t = [float(i) for i in t]
        A.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        A.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    # print('A =\n{0}'.format(pprint.pformat(A)))

    B = [float(item) for sublist in source_coords for item in sublist]
    # print('B =\n{0}'.format(pprint.pformat(B)))

    A_T = math_MatrixTranspose(A)
    A_T_A = math_MatrixProduct(A_T, A)
    A_T_A_inv = math_MatrixInverse(A_T_A)
    A_T_A_inv_A_T = math_MatrixProduct(A_T_A_inv, A_T)
    res = math_MatrixProduct_Column(A_T_A_inv_A_T, B)
    # print('res =\n{0}'.format(pprint.pformat(res)))

    return res

def project_texture(img_boxfront, coordinates, CANVAS_SIZE, rotate = False):
    # print('project_texture() BEGIN ...')

    # --- Rotate 90 degress clockwise ---
    if rotate:
        # print('Rotating image 90 degress clockwise')
        img_boxfront = img_boxfront.rotate(-90, expand = True)
        # img_boxfront.save('rotated.png')

    # --- Info ---
    width, height = img_boxfront.size
    # print('Image width {0}, height {1}'.format(width, height))

    # --- Transform ---
    # Conver list of lists to list of tuples
    n_coords = [(int(c[0]), int(c[1])) for c in coordinates]
    # top/left, top/right, bottom/right, bottom/left
    coeffs = perspective_coeffs([(0, 0), (width, 0), (width, height), (0, height)], n_coords)
    # print(coeffs)
    img_t = img_boxfront.transform(CANVAS_SIZE, Image.PERSPECTIVE, coeffs, Image.BICUBIC)

    # --- Add polygon with alpha channel for blending ---
    # In the alpha channel 0 means transparent and 255 opaque.
    mask = Image.new('L', CANVAS_SIZE, color = 0)
    draw = ImageDraw.Draw(mask)
    # print(n_coords)
    draw.polygon(n_coords, fill = 255)
    img_t.putalpha(mask)

    return img_t

# ------------------------------------------------------------------------------------------------
# Default templates and cached data
# ------------------------------------------------------------------------------------------------
# Cache font objects in global variables.
# Used in mame.py, mame_build_fanart() and mame_build_SL_fanart()
font_mono = None
font_mono_SL = None
font_mono_item = None
font_mono_debug = None

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

# ------------------------------------------------------------------------------------------------
# Graphics high level interface functions
# ------------------------------------------------------------------------------------------------
#
# Rebuild Fanart for a given MAME machine.
# Returns True if the Fanart was built succesfully, False if error.
#
def graphs_build_MAME_Fanart(PATHS, layout, m_name, assets_dic,
    Fanart_FN, CANVAS_COLOR = (0, 0, 0), test_flag = False):
    global font_mono
    global font_mono_debug
    canvas_size = (1920, 1080)
    canvas_bg_color = (0, 0, 0)
    color_white = (255, 255, 255)
    t_color_fg = (255, 255, 0)
    t_color_bg = (102, 102, 0)

    # Quickly check if machine has valid assets, and skip fanart generation if not.
    # log_debug('graphs_build_MAME_Fanart() Building fanart for machine {0}'.format(m_name))
    machine_has_valid_assets = False
    for asset_key, asset_db_name in MAME_layout_assets.iteritems():
        m_assets = assets_dic[m_name]
        if m_assets[asset_db_name]:
            machine_has_valid_assets = True
            break
    if not machine_has_valid_assets: return False

    # --- If font object does not exists open font an cache it. ---
    if not font_mono:
        log_debug('graphs_build_MAME_Fanart() Creating font_mono object')
        log_debug('graphs_build_MAME_Fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), layout['MachineName']['fontsize'])
    if not font_mono_debug:
        log_debug('graphs_build_MAME_Fanart() Creating font_mono_debug object')
        log_debug('graphs_build_MAME_Fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_debug = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), 44)

    # --- Create fanart canvas ---
    fanart_img = Image.new('RGB', canvas_size, canvas_bg_color)
    draw = ImageDraw.Draw(fanart_img)

    # --- Draw assets according to layout ---
    # layout is an ordered dictionary, so the assets are draw in the order they appear
    # in the XML file.
    img_index = 1
    # log_debug(unicode(layout))
    for asset_key in layout:
        # log_debug('{0:<11} initialising'.format(asset_key))
        m_assets = assets_dic[m_name]
        if asset_key == 'MachineName':
            t_left = layout['MachineName']['left']
            t_top = layout['MachineName']['top']
            draw.text((t_left, t_top), m_name, color_white, font_mono)
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
            # Sometimes PIL_resize_proportional() fails.
            #   File "~/plugin.program.AML.dev/resources/mame.py", line 3017, in PIL_resize_proportional
            #   img = img.resize((r_x_size, r_y_size), Image.ANTIALIAS)
            #   File "/usr/lib/python2.7/dist-packages/PIL/Image.py", line 1804, in resize
            #   self.load()
            #   File "/usr/lib/python2.7/dist-packages/PIL/ImageFile.py", line 252, in load
            #   self.load_end()
            #   File "/usr/lib/python2.7/dist-packages/PIL/PngImagePlugin.py", line 680, in load_end
            #   self.png.call(cid, pos, length)
            #   File "/usr/lib/python2.7/dist-packages/PIL/PngImagePlugin.py", line 140, in call
            #   return getattr(self, "chunk_" + cid.decode('ascii'))(pos, length)
            #   AttributeError: 'PngStream' object has no attribute 'chunk_tIME'
            # If so, report the machine that produces the fail and do not generate the
            # Fanart.
            try:
                img_asset = Image.open(Asset_FN.getPath())
                img_asset = resize_proportional(img_asset, layout, asset_key, CANVAS_COLOR)
            except AttributeError:
                a = 'graphs_build_MAME_Fanart() Exception AttributeError'
                b = 'in m_name {0}, asset_key {1}'.format(m_name, asset_key)
                log_error(a)
                log_error(b)
            else:
                fanart_img = paste_image(fanart_img, img_asset, layout, asset_key)
            # In debug mode print asset name and draw order.
            if test_flag:
                t_off = 15
                bg_off = 2
                t_bg_coord = (
                    layout[asset_key]['left'] + t_off + bg_off,
                    layout[asset_key]['top'] + t_off + bg_off)
                t_coord = (layout[asset_key]['left'] + t_off, layout[asset_key]['top'] + t_off)
                debug_text = '{0} {1}'.format(img_index, asset_key)
                # Draw text background first, then front text to create a nice effect.
                draw.text(t_bg_coord, debug_text, t_color_bg, font_mono_debug)
                draw.text(t_coord, debug_text, t_color_fg, font_mono_debug)
            img_index += 1

    # --- Save fanart and update database ---
    # log_debug('graphs_build_MAME_Fanart() Saving Fanart "{0}"'.format(Fanart_FN.getPath()))
    fanart_img.save(Fanart_FN.getPath())
    assets_dic[m_name]['fanart'] = Fanart_FN.getPath()

    # Fanart succesfully built.
    return True

#
# Rebuild Fanart for a given SL item
# Returns True if the Fanart was built succesfully, False if error.
#
def graphs_build_SL_Fanart(PATHS, layout, SL_name, m_name, assets_dic,
    Fanart_FN, CANVAS_COLOR = (0, 0, 0), test_flag = False):
    global font_mono_SL
    global font_mono_item
    global font_mono_debug
    canvas_size = (1920, 1080)
    canvas_bg_color = (0, 0, 0)
    color_white = (255, 255, 255)
    t_color_fg = (255, 255, 0)
    t_color_bg = (102, 102, 0)

    # Quickly check if machine has valid assets, and skip fanart generation if not.
    # log_debug('graphs_build_SL_Fanart() Building fanart for SL {0} item {1}'.format(SL_name, m_name))
    machine_has_valid_assets = False
    for asset_key, asset_db_name in SL_layout_assets.iteritems():
        m_assets = assets_dic[m_name]
        if m_assets[asset_db_name]:
            machine_has_valid_assets = True
            break
    if not machine_has_valid_assets: return False

    # If font object does not exists open font an cache it.
    if not font_mono_SL:
        log_debug('graphs_build_SL_Fanart() Creating font_mono_SL object')
        log_debug('graphs_build_SL_Fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_SL = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), layout['SLName']['fontsize'])
    if not font_mono_item:
        log_debug('graphs_build_SL_Fanart() Creating font_mono_item object')
        log_debug('graphs_build_SL_Fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_item = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), layout['ItemName']['fontsize'])
    if not font_mono_debug:
        log_debug('graphs_build_SL_Fanart() Creating font_mono_debug object')
        log_debug('graphs_build_SL_Fanart() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_debug = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), 44)

    # --- Create fanart canvas ---
    fanart_img = Image.new('RGB', canvas_size, canvas_bg_color)
    draw = ImageDraw.Draw(fanart_img)

    # --- Draw assets according to layout ---
    # layout is an ordered dictionary, so the assets are draw in the order they appear
    # in the XML file.
    img_index = 1
    for asset_key in layout:
        # log_debug('{0:<10} initialising'.format(asset_key))
        m_assets = assets_dic[m_name]
        if asset_key == 'SLName' or asset_key == 'ItemName':
            t_left = layout[asset_key]['left']
            t_top = layout[asset_key]['top']
            if asset_key == 'SLName': name = SL_name
            elif asset_key == 'ItemName': name = m_name
            else: raise TypeError
            draw.text((t_left, t_top), name, color_white, font_mono_SL)
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
            img_asset = resize_proportional(img_asset, layout, asset_key, CANVAS_COLOR)
            fanart_img = paste_image(fanart_img, img_asset, layout, asset_key)
            # In debug mode print asset name and draw order.
            if test_flag:
                t_off = 15
                bg_off = 2
                t_bg_coord = (
                    layout[asset_key]['left'] + t_off + bg_off,
                    layout[asset_key]['top'] + t_off + bg_off)
                t_coord = (layout[asset_key]['left'] + t_off, layout[asset_key]['top'] + t_off)
                debug_text = '{0} {1}'.format(img_index, asset_key)
                # Draw text background first, then front text to create a nice effect.
                draw.text(t_bg_coord, debug_text, t_color_bg, font_mono_debug)
                draw.text(t_coord, debug_text, t_color_fg, font_mono_debug)
            img_index += 1
    # --- Save fanart and update database ---
    # log_debug('graphs_build_SL_Fanart() Saving Fanart "{0}"'.format(Fanart_FN.getPath()))
    fanart_img.save(Fanart_FN.getPath())
    assets_dic[m_name]['fanart'] = Fanart_FN.getPath()

    # Fanart succesfully built.
    return True

#
# Builds a MAME or SL 3D Box.
#
def graphs_build_MAME_3DBox(PATHS, coord_dic, SL_name, m_name, assets_dic,
    image_FN, CANVAS_COLOR = (0, 0, 0), test_flag = False):
    global font_mono
    global font_mono_debug
    FONT_SIZE = 90
    CANVAS_SIZE = (1000, 1500)
    # CANVAS_BG_COLOR = (50, 50, 75) if test_flag else (0, 0, 0)
    CANVAS_BG_COLOR = (0, 0, 0)
    FRONTBOX_BG_COLOR = (200, 100, 100)
    SPINE_BG_COLOR = (100, 200, 100)
    MAME_logo_FN = PATHS.ADDON_CODE_DIR.pjoin('media/MAME_clearlogo.png')

    # --- If font object does not exists open font an cache it. ---
    if not font_mono:
        log_debug('graphs_build_MAME_3DBox() Creating font_mono object')
        log_debug('graphs_build_MAME_3DBox() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), 90)
    if test_flag and not font_mono_debug:
        log_debug('graphs_build_MAME_3DBox() Creating font_mono_debug object')
        log_debug('graphs_build_MAME_3DBox() Loading "{0}"'.format(PATHS.MONO_FONT_PATH.getPath()))
        font_mono_debug = ImageFont.truetype(PATHS.MONO_FONT_PATH.getPath(), 40)

    # --- Open assets ---
    # MAME 3D Box requires Flyer and (Clearlogo or Marquee)
    # SL 3D Box requires Boxfront (not clearlogos available for SLs).
    if SL_name == 'MAME':
        # Check Flyer exists.
        # Check Clearlogo or Marquee exists.
        if not assets_dic[m_name]['flyer']: return False
        if not assets_dic[m_name]['clearlogo'] and not assets_dic[m_name]['marquee']:
            return False
        # Try to open the Flyer.
        try:
            img_flyer = Image.open(assets_dic[m_name]['flyer'])
        except:
            return False
        # Try to open the Clearlogo or Marquee if Clearlogo not available.
        try:
            img_clearlogo = Image.open(assets_dic[m_name]['clearlogo'])
        except:
            try:
                img_clearlogo = Image.open(assets_dic[m_name]['marquee'])
            except:
                return False
    else:
        # Check Boxfront exists.
        if not assets_dic[m_name]['boxfront']: return False
        # Try to open the Boxfront as flyer.
        try:
            img_flyer = Image.open(assets_dic[m_name]['boxfront'])
        except:
            return False

    # --- Create 3dbox canvas ---
    # Create RGB image with alpha channel.
    # Canvas size of destination transformation must have the same size as the final canvas.
    canvas = Image.new('RGBA', CANVAS_SIZE, CANVAS_BG_COLOR)

    # --- Frontbox ---
    img_front = Image.new('RGBA', CANVAS_SIZE, FRONTBOX_BG_COLOR)
    img_t = project_texture(img_front, coord_dic['Frontbox'], CANVAS_SIZE)
    canvas.paste(img_t, mask = img_t)

    # --- Spine ---
    img_spine = Image.new('RGBA', CANVAS_SIZE, SPINE_BG_COLOR)
    img_t = project_texture(img_spine, coord_dic['Spine'], CANVAS_SIZE)
    canvas.paste(img_t, mask = img_t)

    # --- Flyer image ---
    # At this point img_flyer is present and opened.
    img_t = project_texture(img_flyer, coord_dic['Flyer'], CANVAS_SIZE)
    try:
        canvas.paste(img_t, mask = img_t)
    except ValueError:
        log_error('graphs_build_MAME_3DBox() Exception ValueError in Front Flyer')
        log_error('SL_name = {0}, m_name = {1}'.format(SL_name, m_name))

    # --- Spine game clearlogo ---
    # Skip Spine Clearlogo in SLs 3D Boxes.
    if SL_name == 'MAME':
        img_t = project_texture(img_clearlogo, coord_dic['Clearlogo'], CANVAS_SIZE, rotate = True)
        try:
            canvas.paste(img_t, mask = img_t)
        except ValueError:
            log_error('graphs_build_MAME_3DBox() Exception ValueError in Spine Clearlogo')
            log_error('SL_name = {0}, m_name = {1}'.format(SL_name, m_name))

    # --- MAME background ---
    img_mame = Image.open(MAME_logo_FN.getPath())
    img_t = project_texture(img_mame, coord_dic['Clearlogo_MAME'], CANVAS_SIZE, rotate = True)
    canvas.paste(img_t, mask = img_t)

    # --- Machine name ---
    img_name = Image.new('RGBA', (1000, 100), (0, 0, 0))
    draw = ImageDraw.Draw(img_name)
    draw.text((5, 0), '{0} {1}'.format(SL_name, m_name), (255, 255, 255), font = font_mono)
    img_t = project_texture(img_name, coord_dic['Front_Title'], CANVAS_SIZE)
    canvas.paste(img_t, mask = img_t)

    # --- Model data in debug mode ---
    if test_flag:
        data = coord_dic['data']
        C_WHITE = (255, 255, 255)
        C_BLACK = (0, 0, 0)
        BOX_SIZE = (300, 200)
        PASTE_POINT = (680, 1280)
        img_name = Image.new('RGBA', BOX_SIZE, C_BLACK)
        draw = ImageDraw.Draw(img_name)
        draw.text((10, 0), 'angleX {0}'.format(data['angleX']), C_WHITE, font = font_mono_debug)
        draw.text((10, 35), 'angleY {0}'.format(data['angleY']), C_WHITE, font = font_mono_debug)
        draw.text((10, 70), 'angleZ {0}'.format(data['angleZ']), C_WHITE, font = font_mono_debug)
        draw.text((10, 105), 'FOV {0}'.format(data['fov']), C_WHITE, font = font_mono_debug)
        draw.text((10, 140), 'd {0}'.format(data['viewer_distance']), C_WHITE, font = font_mono_debug)
        box = (PASTE_POINT[0], PASTE_POINT[1], PASTE_POINT[0]+BOX_SIZE[0], PASTE_POINT[1]+BOX_SIZE[1])
        canvas.paste(img_name, box, mask = img_name)

    # --- Save fanart and update database ---
    # log_debug('graphs_build_MAME_3DBox() Saving Fanart "{0}"'.format(image_FN.getPath()))
    canvas.save(image_FN.getPath())
    assets_dic[m_name]['3dbox'] = image_FN.getPath()

    # 3D Box was sucessfully generated. Return true to estimate ETA.
    return True

#
# Returns an Ordered dictionary with the layout of the fanart.
# The Ordered dictionary is to keep the order of the tags in the XML
#
def graphs_load_MAME_Fanart_template(Template_FN):
    # --- Load XML file ---
    layout = OrderedDict()
    if not os.path.isfile(Template_FN.getPath()): return None
    log_debug('graphs_load_MAME_Fanart_template() Loading XML "{0}"'.format(Template_FN.getPath()))
    try:
        xml_tree = ET.parse(Template_FN.getPath())
    except IOError as E:
        return None
    xml_root = xml_tree.getroot()

    # --- Parse XML file ---
    art_list = ['Title', 'Snap', 'Flyer', 'Cabinet', 'Artpreview', 'PCB', 'Clearlogo', 'CPanel', 'Marquee']
    art_tag_list = ['width', 'height', 'left', 'top']
    text_list = ['MachineName']
    test_tag_list = ['left', 'top', 'fontsize']
    for root_element in xml_root:
        # log_debug('Root child {0}'.format(root_element.tag))
        if root_element.tag in art_list:
            art_dic = {key : 0 for key in art_tag_list}
            for art_child in root_element:
                if art_child.tag in art_tag_list:
                    art_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = art_dic
        elif root_element.tag in text_list:
            text_dic = {key : 0 for key in test_tag_list}
            for art_child in root_element:
                if art_child.tag in test_tag_list:
                    text_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = text_dic
        else:
            log_error('Unknown root tag <{0}>'.format(root_element.tag))
            return None

    return layout

# Returns a dictionary with all the data necessary to build the fanarts.
# The dictionary has the 'abort' field if an error was detected.
def graphs_load_MAME_Fanart_stuff(PATHS, settings, BUILD_MISSING):
    data_dic = {
        'abort' : False,
        'BUILD_MISSING' : BUILD_MISSING,
    }

    # If artwork directory not configured abort.
    if not settings['assets_path']:
        kodi_dialog_OK('Asset directory not configured. Aborting Fanart generation.')
        data_dic['abort'] = True
        return data_dic

    # --- If fanart directory doesn't exist create it ---
    Asset_path_FN = FileName(settings['assets_path'])
    Fanart_path_FN = Asset_path_FN.pjoin('fanarts')
    if not Fanart_path_FN.isdir():
        log_info('Creating MAME Fanart dir "{0}"'.format(Fanart_path_FN.getPath()))
        Fanart_path_FN.makedirs()
    data_dic['Fanart_path_FN'] = Fanart_path_FN

    # --- Load Fanart template from XML file ---
    Template_FN = PATHS.ADDON_CODE_DIR.pjoin('templates/AML-MAME-Fanart-template.xml')
    layout = graphs_load_MAME_Fanart_template(Template_FN)
    # log_debug(unicode(layout))
    if not layout:
        kodi_dialog_OK('Error loading XML MAME Fanart layout.')
        data_dic['abort'] = True
        return data_dic
    else:
        data_dic['layout'] = layout

    # --- Load Assets DB ---
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher', 'Loading MAME asset database ... ')
    pDialog.update(0)
    assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
    pDialog.update(100)
    pDialog.close()
    data_dic['assets_dic'] = assets_dic

    return data_dic

# Builds or rebuilds missing MAME Fanarts.
def graphs_build_MAME_Fanart_all(PATHS, settings, data_dic):
    # >> Traverse all machines and build fanart from other pieces of artwork
    pDialog_canceled = False
    pDialog = xbmcgui.DialogProgress()
    pDialog_line1 = 'Building MAME machine Fanarts ...'
    pDialog.create('Advanced MAME Launcher', pDialog_line1)
    total_machines, processed_machines = len(data_dic['assets_dic']), 0
    ETA_str = ETA_reset(total_machines)
    for m_name in sorted(data_dic['assets_dic']):
        build_time_start = time.time()
        pDialog.update((processed_machines * 100) // total_machines, pDialog_line1,
            'ETA {0} machine {1}'.format(ETA_str, m_name))
        if pDialog.iscanceled():
            pDialog_canceled = True
            # kodi_dialog_OK('Fanart generation was cancelled by the user.')
            break
        # >> If build missing Fanarts was chosen only build fanart if file cannot
        # >> be found.
        Fanart_FN = data_dic['Fanart_path_FN'].pjoin('{0}.png'.format(m_name))
        if data_dic['BUILD_MISSING']:
            if Fanart_FN.exists():
                data_dic['assets_dic'][m_name]['fanart'] = Fanart_FN.getPath()
                build_OK_flag = False
            else:
                build_OK_flag = graphs_build_MAME_Fanart(
                    PATHS, data_dic['layout'], m_name, data_dic['assets_dic'], Fanart_FN)
        else:
            build_OK_flag = graphs_build_MAME_Fanart(
                PATHS, data_dic['layout'], m_name, data_dic['assets_dic'], Fanart_FN)
        processed_machines += 1
        build_time_end = time.time()
        build_time = build_time_end - build_time_start
        # Only update ETA if 3DBox was sucesfully build.
        ETA_str = ETA_update(build_OK_flag, processed_machines, build_time)
    pDialog.update(100, ' ', ' ')
    pDialog.close()

    # --- Save assets DB ---
    pDialog.create('Advanced MAME Launcher', 'Saving MAME asset database ... ')
    pDialog.update(1)
    fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), data_dic['assets_dic'])
    pDialog.update(100)
    pDialog.close()

    # --- MAME Fanart build timestamp ---
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    change_control_dic(control_dic, 't_MAME_fanart_build', time.time())
    fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

    # --- assets_dic has changed. Rebuild hashed database ---
    fs_build_asset_hashed_db(PATHS, settings, control_dic, data_dic['assets_dic'])

    # --- Rebuild MAME asset cache ---
    if settings['debug_enable_MAME_asset_cache']:
        cache_index = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
        fs_build_asset_cache(PATHS, settings, control_dic, cache_index, data_dic['assets_dic'])

    # --- Inform user ---
    if pDialog_canceled:
        kodi_notify('MAME Fanart building stopped. Partial progress saved.')
    else:
        kodi_notify('MAME Fanart building finished')

#
# Returns an Ordered dictionary with the layout of the fanart.
# The Ordered dictionary is to keep the order of the tags in the XML
#
def graphs_load_SL_Fanart_template(Template_FN):
    # --- Load XML file ---
    layout = OrderedDict()
    if not os.path.isfile(Template_FN.getPath()): return None
    log_debug('mame_load_SL_Fanart_template() Loading XML "{0}"'.format(Template_FN.getPath()))
    try:
        xml_tree = ET.parse(Template_FN.getPath())
    except IOError as E:
        return None
    xml_root = xml_tree.getroot()

    # --- Parse file ---
    art_list = ['Title', 'Snap', 'BoxFront']
    art_tag_list = ['width', 'height', 'left', 'top']
    text_list = ['SLName', 'ItemName']
    test_tag_list = ['left', 'top', 'fontsize']
    for root_element in xml_root:
        # log_debug('Root child {0}'.format(root_element.tag))
        if root_element.tag in art_list:
            # Default size tags to 0
            art_dic = {key : 0 for key in art_tag_list}
            for art_child in root_element:
                if art_child.tag in art_tag_list:
                    art_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = art_dic
        elif root_element.tag in text_list:
            text_dic = {key : 0 for key in test_tag_list}
            for art_child in root_element:
                if art_child.tag in test_tag_list:
                    text_dic[art_child.tag] = int(art_child.text)
                else:
                    log_error('Inside root tag <{0}>'.format(root_element.tag))
                    log_error('Unknown tag <{0}>'.format(art_child.tag))
                    return None
            layout[root_element.tag] = text_dic
        else:
            log_error('Unknown root tag <{0}>'.format(root_element.tag))
            return None

    return layout

# Returns a dictionary with all the data necessary to build the fanarts.
# The dictionary has the 'abort' field if an error was detected.
def graphs_load_SL_Fanart_stuff(PATHS, settings, BUILD_MISSING):
    data_dic = {
        'abort' : False,
        'BUILD_MISSING' : BUILD_MISSING,
    }

    # If artwork directory not configured abort.
    # SL Fanart directories are created later in graphs_build_SL_Fanart_all()
    if not settings['assets_path']:
        kodi_dialog_OK('Asset directory not configured. Aborting Fanart generation.')
        data_dic['abort'] = True
        return

    # --- Load Fanart template from XML file ---
    Template_FN = PATHS.ADDON_CODE_DIR.pjoin('templates/AML-SL-Fanart-template.xml')
    layout = graphs_load_SL_Fanart_template(Template_FN)
    # log_debug(unicode(layout))
    if not layout:
        kodi_dialog_OK('Error loading XML Software List Fanart layout.')
        data_dic['abort'] = True
        return
    else:
        data_dic['layout'] = layout

    # --- Load SL index ---
    SL_index = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    data_dic['SL_index'] = SL_index

    return data_dic

# Builds or rebuilds missing SL Fanarts.
def graphs_build_SL_Fanart_all(PATHS, settings, data_dic):
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())

    # >> Traverse all SL and on each SL every item
    pDialog_canceled = False
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher')
    SL_number, SL_count = len(data_dic['SL_index']), 1
    total_SL_items, total_processed_SL_items = control_dic['stats_SL_software_items'], 0
    ETA_str = ETA_reset(total_SL_items)
    log_debug('graphs_build_SL_Fanart_all() total_SL_items = {0}'.format(total_SL_items))
    for SL_name in sorted(data_dic['SL_index']):
        # >> Update progres dialog
        pdialog_line1 = 'Processing SL {0} ({1} of {2})...'.format(SL_name, SL_count, SL_number)
        pdialog_line2 = ' '
        pDialog.update(0, pdialog_line1, pdialog_line2)

        # >> If fanart directory doesn't exist create it.
        Asset_path_FN = FileName(settings['assets_path'])
        Fanart_path_FN = Asset_path_FN.pjoin('fanarts_SL/{0}'.format(SL_name))
        if not Fanart_path_FN.isdir():
            log_info('Creating SL Fanart dir "{0}"'.format(Fanart_path_FN.getPath()))
            Fanart_path_FN.makedirs()

        # >> Load Assets DB
        pdialog_line2 = 'Loading SL asset database ... '
        pDialog.update(0, pdialog_line1, pdialog_line2)
        assets_file_name =  data_dic['SL_index'][SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

        # Traverse all SL items and build fanart from other pieces of artwork
        # Last slot of the progress bar is to save the JSON database.
        total_SL_items, processed_SL_items = len(SL_assets_dic) + 1, 0
        for m_name in sorted(SL_assets_dic):
            build_time_start = time.time()
            pdialog_line2 = 'ETA {0} SL item {1}'.format(ETA_str, m_name)
            update_number = (processed_SL_items * 100) // total_SL_items
            pDialog.update(update_number, pdialog_line1, pdialog_line2)
            if pDialog.iscanceled():
                pDialog_canceled = True
                # kodi_dialog_OK('SL Fanart generation was cancelled by the user.')
                break
            # If build missing Fanarts was chosen only build fanart if file cannot be found.
            Fanart_FN = Fanart_path_FN.pjoin('{0}.png'.format(m_name))
            if data_dic['BUILD_MISSING']:
                if Fanart_FN.exists():
                    SL_assets_dic[m_name]['fanart'] = Fanart_FN.getPath()
                    build_OK_flag = False
                else:
                    build_OK_flag = graphs_build_SL_Fanart(
                        PATHS, data_dic['layout'], SL_name, m_name, SL_assets_dic, Fanart_FN)
            else:
                build_OK_flag = graphs_build_SL_Fanart(
                    PATHS, data_dic['layout'], SL_name, m_name, SL_assets_dic, Fanart_FN)
            processed_SL_items += 1
            processed_SL_items += 1 # For current list progress dialog
            total_processed_SL_items += 1 # For total ETA calculation
            build_time_end = time.time()
            build_time = build_time_end - build_time_start
            # Only update ETA if 3DBox was sucesfully build.
            ETA_str = ETA_update(build_OK_flag, total_processed_SL_items, build_time)
        # --- Save SL assets DB ---
        pdialog_line2 = 'Saving SL {0} asset database ... '.format(SL_name)
        pDialog.update(100, pdialog_line1, pdialog_line2)
        fs_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic)

        # --- Update progress ---
        SL_count += 1
        if pDialog_canceled: break
    pDialog.close()

    # --- SL Fanart build timestamp ---
    change_control_dic(control_dic, 't_SL_fanart_build', time.time())
    fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

    # --- Inform user ---
    if pDialog_canceled:
        kodi_notify('SL Fanart building stopped. Partial progress saved.')
    else:
        kodi_notify('SL Fanart building finished')

# Returns a dictionary with all the data necessary to build the fanarts.
# The dictionary has the 'abort' field if an error was detected.
def graphs_load_MAME_3DBox_stuff(PATHS, settings, BUILD_MISSING):
    data_dic = {
        'abort' : False,
        'BUILD_MISSING' : BUILD_MISSING,
    }

    # If artwork directory not configured abort.
    if not settings['assets_path']:
        kodi_dialog_OK('Asset directory not configured. Aborting MAME 3D box generation.')
        data_dic['abort'] = True
        return data_dic

    # --- If fanart directory doesn't exist create it ---
    Asset_path_FN = FileName(settings['assets_path'])
    Boxes_path_FN = Asset_path_FN.pjoin('3dboxes')
    if not Boxes_path_FN.isdir():
        log_info('Creating Fanart dir "{0}"'.format(Boxes_path_FN.getPath()))
        Boxes_path_FN.makedirs()
    data_dic['Boxes_path_FN'] = Boxes_path_FN

    # --- Load Fanart template from XML file ---
    # TProjection_FN = PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_56.json')
    TProjection_FN = PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_60.json')
    t_projection = fs_load_JSON_file_dic(TProjection_FN.getPath())
    data_dic['t_projection'] = t_projection

    # --- Load Assets DB ---
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher', 'Loading MAME asset database ... ')
    pDialog.update(0)
    assets_dic = fs_load_JSON_file_dic(PATHS.MAIN_ASSETS_DB_PATH.getPath())
    pDialog.update(100)
    pDialog.close()
    data_dic['assets_dic'] = assets_dic

    return data_dic

# Builds or rebuilds missing MAME Fanarts.
def graphs_build_MAME_3DBox_all(PATHS, settings, data_dic):
    # Traverse all machines and build 3D boxes from other pieces of artwork
    SL_name = 'MAME'
    pDialog_canceled = False
    pDialog = xbmcgui.DialogProgress()
    pDialog_line1 = 'Building MAME machine 3D Boxes ...'
    pDialog.create('Advanced MAME Launcher', pDialog_line1)
    total_machines, processed_machines = len(data_dic['assets_dic']), 0
    ETA_str = ETA_reset(total_machines)
    for m_name in sorted(data_dic['assets_dic']):
        build_time_start = time.time()
        pDialog.update(
            (processed_machines * 100) // total_machines, pDialog_line1,
            'ETA {0} machine {1}'.format(ETA_str, m_name))
        if pDialog.iscanceled():
            pDialog_canceled = True
            break
        Image_FN = data_dic['Boxes_path_FN'].pjoin('{0}.png'.format(m_name))
        if data_dic['BUILD_MISSING']:
            if Image_FN.exists():
                data_dic['assets_dic'][m_name]['3dbox'] = Image_FN.getPath()
                build_OK_flag = False
            else:
                build_OK_flag = graphs_build_MAME_3DBox(
                    PATHS, data_dic['t_projection'], SL_name, m_name, data_dic['assets_dic'], Image_FN)
        else:
            build_OK_flag = graphs_build_MAME_3DBox(
                PATHS, data_dic['t_projection'], SL_name, m_name, data_dic['assets_dic'], Image_FN)
        processed_machines += 1
        build_time_end = time.time()
        build_time = build_time_end - build_time_start
        # Only update ETA if 3DBox was sucesfully build.
        ETA_str = ETA_update(build_OK_flag, processed_machines, build_time)
    pDialog.update(100, ' ', ' ')
    pDialog.close()

    # --- Save assets DB ---
    pDialog.create('Advanced MAME Launcher', 'Saving MAME asset database ... ')
    pDialog.update(1)
    fs_write_JSON_file(PATHS.MAIN_ASSETS_DB_PATH.getPath(), data_dic['assets_dic'])
    pDialog.update(100)
    pDialog.close()

    # --- MAME Fanart build timestamp ---
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())
    change_control_dic(control_dic, 't_MAME_3dbox_build', time.time())
    fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

    # --- assets_dic has changed. Rebuild hashed database ---
    fs_build_asset_hashed_db(PATHS, settings, control_dic, data_dic['assets_dic'])

    # --- Rebuild MAME asset cache ---
    if settings['debug_enable_MAME_asset_cache']:
        cache_index = fs_load_JSON_file_dic(PATHS.CACHE_INDEX_PATH.getPath())
        fs_build_asset_cache(PATHS, settings, control_dic, cache_index, data_dic['assets_dic'])

    # --- Inform user ---
    if pDialog_canceled:
        kodi_notify('MAME 3D Boxes building stopped. Partial progress saved.')
    else:
        kodi_notify('MAME 3D Boxes building finished')

# Called before building all SL 3D Boxes.
def graphs_load_SL_3DBox_stuff(PATHS, settings, BUILD_MISSING):
    data_dic = {
        'abort' : False,
        'BUILD_MISSING' : BUILD_MISSING,
    }

    # If artwork directory not configured abort.
    # SL 3dbox directories are created later in graphs_build_SL_3DBox_all()
    if not settings['assets_path']:
        kodi_dialog_OK('Asset directory not configured. Aborting Fanart generation.')
        data_dic['abort'] = True
        return

    # --- Load 3D projection template from XML file ---
    # TProjection_FN = PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_56.json')
    TProjection_FN = PATHS.ADDON_CODE_DIR.pjoin('templates/3dbox_angleY_60.json')
    t_projection = fs_load_JSON_file_dic(TProjection_FN.getPath())
    data_dic['t_projection'] = t_projection

    # --- Load SL index ---
    SL_index = fs_load_JSON_file_dic(PATHS.SL_INDEX_PATH.getPath())
    data_dic['SL_index'] = SL_index

    return data_dic

# Builds or rebuilds missing SL Fanarts.
def graphs_build_SL_3DBox_all(PATHS, settings, data_dic):
    control_dic = fs_load_JSON_file_dic(PATHS.MAIN_CONTROL_PATH.getPath())

    # >> Traverse all SL and on each SL every item
    pDialog_canceled = False
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher')
    SL_number, SL_count = len(data_dic['SL_index']), 1
    total_SL_items, total_processed_SL_items = control_dic['stats_SL_software_items'], 0
    ETA_str = ETA_reset(total_SL_items)
    log_debug('graphs_build_SL_3DBox_all() total_SL_items = {0}'.format(total_SL_items))
    for SL_name in sorted(data_dic['SL_index']):
        # >> Update progres dialog
        pdialog_line1 = 'Processing SL {0} ({1} of {2})...'.format(SL_name, SL_count, SL_number)
        pdialog_line2 = ' '
        pDialog.update(0, pdialog_line1, pdialog_line2)

        # >> If fanart directory doesn't exist create it.
        Asset_path_FN = FileName(settings['assets_path'])
        Boxes_path_FN = Asset_path_FN.pjoin('3dboxes_SL/{0}'.format(SL_name))
        if not Boxes_path_FN.isdir():
            log_info('Creating SL 3D Box dir "{0}"'.format(Boxes_path_FN.getPath()))
            Boxes_path_FN.makedirs()

        # >> Load Assets DB
        pdialog_line2 = 'Loading SL asset database ... '
        pDialog.update(0, pdialog_line1, pdialog_line2)
        assets_file_name =  data_dic['SL_index'][SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = PATHS.SL_DB_DIR.pjoin(assets_file_name)
        SL_assets_dic = fs_load_JSON_file_dic(SL_asset_DB_FN.getPath())

        # Traverse all SL items and build fanart from other pieces of artwork
        # Last slot of the progress bar is to save the JSON database.
        SL_items, processed_SL_items = len(SL_assets_dic) + 1, 0
        for m_name in sorted(SL_assets_dic):
            build_time_start = time.time()
            pdialog_line2 = 'ETA {0} SL item {1}'.format(ETA_str, m_name)
            update_number = (processed_SL_items * 100) // SL_items
            pDialog.update(update_number, pdialog_line1, pdialog_line2)
            if pDialog.iscanceled():
                pDialog_canceled = True
                break
            Image_FN = Boxes_path_FN.pjoin('{0}.png'.format(m_name))
            if data_dic['BUILD_MISSING']:
                if Image_FN.exists():
                    SL_assets_dic[m_name]['3dbox'] = Image_FN.getPath()
                    build_OK_flag = False
                else:
                    build_OK_flag = graphs_build_MAME_3DBox(
                        PATHS, data_dic['t_projection'], SL_name, m_name, SL_assets_dic, Image_FN)
            else:
                build_OK_flag = graphs_build_MAME_3DBox(
                    PATHS, data_dic['t_projection'], SL_name, m_name, SL_assets_dic, Image_FN)
            processed_SL_items += 1 # For current list progress dialog
            total_processed_SL_items += 1 # For total ETA calculation
            build_time_end = time.time()
            build_time = build_time_end - build_time_start
            # Only update ETA if 3DBox was sucesfully build.
            ETA_str = ETA_update(build_OK_flag, total_processed_SL_items, build_time)
        # --- Save SL assets DB ---
        pdialog_line2 = 'Saving SL {0} asset database ... '.format(SL_name)
        pDialog.update(100, pdialog_line1, pdialog_line2)
        fs_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic)

        # --- Update progress ---
        SL_count += 1
        if pDialog_canceled: break
    pDialog.close()

    # --- SL Fanart build timestamp ---
    change_control_dic(control_dic, 't_SL_3dbox_build', time.time())
    fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

    # --- Inform user ---
    if pDialog_canceled:
        kodi_notify('SL 3D Boxes building stopped. Partial progress saved.')
    else:
        kodi_notify('SL 3D Boxes building finished')
