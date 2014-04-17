
#       Copyright (C) 2013-2014
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

import os
import xbmc
import re

def getFavourites(file):
    xml  = '<favourites></favourites>'
    if os.path.exists(file):  
        fav = open(file , 'r')
        xml = fav.read()
        fav.close()

    items = []

    faves = re.compile('<favourite(.+?)</favourite>').findall(xml)
    for fave in faves:
        name  = re.compile('name="(.+?)"').findall(fave)[0]

        try:    thumb = re.compile('thumb="(.+?)"').findall(fave)[0]
        except: thumb = ''

        cmd   = fave.rsplit('>', 1)[-1]
        items.append([name, thumb, cmd])

    return items


def writeFavourites(file, faves):
    f = open(file, mode='w')

    f.write('<favourites>')

    for fave in faves:
        name  = 'name="%s" ' % fave[0]
        thumb = 'thumb="%s">' % fave[1]
        cmd   = fave[2]

        f.write('\n\t<favourite ')
        f.write(name)
        f.write(thumb)
        f.write(cmd)
        f.write('</favourite>')

    f.write('\n</favourites>')            
    f.close()