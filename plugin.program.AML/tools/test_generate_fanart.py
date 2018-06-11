#!/usr/bin/python
#
#
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

#
# Scales and centers img into a box of size (box_x_size, box_y_size).
# Scaling keeps original img aspect ratio.
# Returns an image of size (box_x_size, box_y_size)
#
def PIL_resize_proportional(img, layout, dic_key):
    # CANVAS_COLOR = (25, 255, 25)
    CANVAS_COLOR = (0, 0, 0)
    box_x_size = layout[dic_key]['x_size']
    box_y_size = layout[dic_key]['y_size']
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
        layout[dic_key]['x_pos'],
        layout[dic_key]['y_pos'], 
        layout[dic_key]['x_pos'] + layout[dic_key]['x_size'],
        layout[dic_key]['y_pos'] + layout[dic_key]['y_size']
    )
    img.paste(img_title, box)

    return img

# --- Fanart layout ---
layout = {
    'title'      : {'x_size' : 450, 'y_size' : 450, 'x_pos' : 50,   'y_pos' : 50},
    'snap'       : {'x_size' : 450, 'y_size' : 450, 'x_pos' : 50,   'y_pos' : 550},
    'flyer'      : {'x_size' : 450, 'y_size' : 450, 'x_pos' : 1420, 'y_pos' : 50},
    'cabinet'    : {'x_size' : 300, 'y_size' : 425, 'x_pos' : 1050, 'y_pos' : 625},
    'artpreview' : {'x_size' : 450, 'y_size' : 550, 'x_pos' : 550,  'y_pos' : 500},
    'PCB'        : {'x_size' : 300, 'y_size' : 300, 'x_pos' : 1500, 'y_pos' : 525},
    'clearlogo'  : {'x_size' : 450, 'y_size' : 200, 'x_pos' : 1400, 'y_pos' : 850},
    'cpanel'     : {'x_size' : 300, 'y_size' : 100, 'x_pos' : 1050, 'y_pos' : 500},
    'marquee'    : {'x_size' : 800, 'y_size' : 275, 'x_pos' : 550,  'y_pos' : 200},
    'text'       : {                                'x_pos' : 550,  'y_pos' : 50, 'size' : 72},
}

# --- Create fanart canvas ---
img = Image.new('RGB', (1920, 1080), (0, 0, 0))
draw = ImageDraw.Draw(img)
font_mono = ImageFont.truetype('../fonts/Inconsolata.otf', layout['text']['size'])

# --- Title and Snap (colour rectangle for placement) ---
# img_title = Image.new('RGB', (TITLE_X_SIZE, TITLE_Y_SIZE), (25, 25, 25))
# img_snap = Image.new('RGB', (SNAP_X_SIZE, SNAP_Y_SIZE), (0, 200, 0))
# print('Title X_size = {0} | img Y_size = {1}'.format(img_title.size[0], img_title.size[1]))
# print(img_title.format, img_title.size, img_title.mode)

# --- Title and Snap (open PNG actual screenshot) ---
img_title = Image.open('dino_title.png')
img_snap = Image.open('dino_snap.png')
img_artpreview = Image.open('dino_artpreview.png')
img_cabinet = Image.open('dino_cabinet.png')
img_clearlogo = Image.open('dino_clearlogo.png')
img_cpanel = Image.open('dino_cpanel.png')
img_flyer = Image.open('dino_flyer.png')
img_marquee = Image.open('dino_marquee.png')
img_PCB = Image.open('dino_PCB.png')

# --- Resize keeping aspect ratio ---
img_title = PIL_resize_proportional(img_title, layout, 'title')
img_snap = PIL_resize_proportional(img_snap, layout, 'snap')
img_artpreview = PIL_resize_proportional(img_artpreview, layout, 'artpreview')
img_cabinet = PIL_resize_proportional(img_cabinet, layout, 'cabinet')
img_clearlogo = PIL_resize_proportional(img_clearlogo, layout, 'clearlogo')
img_cpanel = PIL_resize_proportional(img_cpanel, layout, 'cpanel')
img_flyer = PIL_resize_proportional(img_flyer, layout, 'flyer')
img_marquee = PIL_resize_proportional(img_marquee, layout, 'marquee')
img_PCB = PIL_resize_proportional(img_PCB, layout, 'PCB')

# --- Compsite fanart ---
# NOTE The box dimensions must have the same size as the pasted image.
img = PIL_paste_image(img, img_title, layout, 'title')
img = PIL_paste_image(img, img_snap, layout, 'snap')
img = PIL_paste_image(img, img_artpreview, layout, 'artpreview')
img = PIL_paste_image(img, img_cabinet, layout, 'cabinet')
img = PIL_paste_image(img, img_clearlogo, layout, 'clearlogo')
img = PIL_paste_image(img, img_cpanel, layout, 'cpanel')
img = PIL_paste_image(img, img_flyer, layout, 'flyer')
img = PIL_paste_image(img, img_marquee, layout, 'marquee')
img = PIL_paste_image(img, img_PCB, layout, 'PCB')

# --- Print machine name ---
draw.text((layout['text']['x_pos'], layout['text']['y_pos']),
          'dino', (255, 255, 255), font = font_mono)

# --- Save test fanart ---
img.save('fanart.png')
