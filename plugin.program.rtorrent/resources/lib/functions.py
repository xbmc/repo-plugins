'''Assorted functions for the rTorrent plugin'''
import mimetypes
import os
import re
import sys
import urllib.parse
import xbmc
import xbmcgui
from . import globals as g

def get_params():
    '''Parse xbmc parameters string'''
    params_str = sys.argv[2].lstrip('?').rstrip('/')
    params_parsed = urllib.parse.parse_qs(params_str, keep_blank_values=True)
    return  dict(map( lambda x: (x, params_parsed[x][0]), params_parsed))

def run_string(mode, params=None, runplugin=True):
    ''' Creates a xbmc.RunPlugin string from a dict of parameters '''
    params = params or {}
    parameters = {'mode': mode}
    parameters.update(params)
    output = '%s?' % sys.argv[0]
    output += urllib.parse.urlencode(parameters)
    return 'RunPlugin(%s)' % output if runplugin else output

def file_hash(download_hash, file_index):
    ''' Turns a digest and file index into a file hash string '''
    return '%s:f%i' % (download_hash, file_index)

def get_icon(isdir, active, complete, priority):
    '''Get torrent or file status icon'''
    if isdir > 1:
        icon = "dir"
        priority += 3
    elif isdir == 0:
        icon = "file"
    else:
        icon = "file"
        priority += 3
    if active == 1:
        if complete == 1:
            iconcol = "9"
        else:
            switch = {
                # Files
                0: "0", # Don't Download
                1: "3", # Normal
                2: "4", # High
                # Downloads
                3: "1", # Idle
                4: "2", # Low
                5: "3", # Normal
                6: "4" # High
            }
            iconcol = switch.get(priority, "0")
    else:
        iconcol = "0"
    return os.path.join(g.__icondir__, '%s_%s.jpg' % (icon, iconcol))

def d_multicall_dict(view='main', args=None):
    ''' Returns multicalls as a list of dicts '''
    args = args or []
    output = []
    rows =  g.rtc.call('d.multicall2', '', view, *args)
    if g.rtc.success:
        for row in rows:
            row_dict= {}
            for idx, arg in enumerate(args):
                row_dict.update({clean_command(arg): row[idx]})
            output.append(row_dict)
    return output

def clean_command(name):
    ''' Cleans up rtorrent commands to be a dict suitable key '''
    match = re.match(r"^[dft]\.([a-z_]+)=",name)
    return match.group(1) if match else name

def play_file(url):
    ''' Function to determine whether to play video/audio or show an image '''
    mimetype = mimetypes.guess_type(url)[0]
    if mimetype and any(re.findall(r'image|audio|video', mimetype)):
        if 'image' in mimetype:
            xbmc.executebuiltin('ShowPicture(%s)' % url)
        elif 'video' in mimetype or 'audio' in mimetype:
            xbmc.Player().play(url)
    else:
        xbmcgui.Dialog().ok(g.__lang__(30900), g.__lang__(30901))
