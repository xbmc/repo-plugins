#
#       Copyright (C) 2014-2015
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import xbmc
import os
import urllib

import utils
import favourite
import sfile

ROOT     = utils.ROOT
FILEPATH = os.path.join(ROOT, 'H')
FILENAME = os.path.join(FILEPATH, utils.FILENAME)


def exists():
    return len(browse()) > 0


def browse():
    items = favourite.getFavourites(FILENAME, validate=False)
    items.sort()
    return items
    

def contains(keyword):
    if len(keyword) < 1:
        return True

    keyword = keyword.lower()
    history = browse()
    for item in history:
        if item[0].lower() == keyword:
            return True

    return False


def add(keyword, image, fanart):
    if not exists():
        try:
            sfile.makedirs(FILEPATH)
        except:
            pass    

    if contains(keyword):
        return False

    newFave = []

    newFave.append(keyword)
    newFave.append(image)
    newFave.append('%s?sf_options=fanart=%s_options_sf' % (keyword, urllib.quote_plus(fanart)))

    return favourite.addFave(FILENAME, newFave)


def remove(name):
    if not contains(name):
        return False

    return favourite.removeFave(FILENAME, name)