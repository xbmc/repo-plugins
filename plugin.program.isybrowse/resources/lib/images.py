'''
    ISY Browser for XBMC
    Copyright (C) 2012 Ryan M. Kraus

    LICENSE:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    DESCRIPTION:
    This Python Module contains variables and functions neccessary for 
    handling image requests for the ISY Browser XBMC Addon.
    
    WRITTEN:    11/2012
'''

import shared

# define image keys
__images__ = { 
    'folder': 'folder_2.png',
    'node_on': 'node_on_2.png',
    'node_off': 'node_off_2.png',
    'node_0': 'node_0.png',
    'node_20': 'node_20.png',
    'node_40': 'node_40.png',
    'node_60': 'node_60.png',
    'node_80': 'node_80.png',
    'node_100': 'node_100.png',
    'group': 'group.png',
    'program': 'program_2.png',
    '__default__': 'DefaultFolder.png'
    }
    
def getImage(key):
    '''
    getImage(key)
    
    DESCRIPTION:
    This function parses an image key and
    returns the path to the image.
    '''
    try:
        img = shared.__media__ + __images__[key]
    except:
        img = __images__['__default__']
        
    return img