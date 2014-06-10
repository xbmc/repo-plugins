
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

import HTMLParser


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def escape(text):
    return ''.join(html_escape_table.get(c,c) for c in text)


def unescape(text):
    #return text
    text = text.replace('&amp;',  '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', '\'')
    text = text.replace('&gt;',   '>')
    text = text.replace('&lt;',   '<')
    return text

    try:
        return HTMLParser.HTMLParser().unescape(text)
    except Exception, e:
        print str(e)
        pass

    newText    = ''
    ignoreNext = False

    for c in text:
        if ord(c) < 127:
            newText   += c
            ignoreNext = False
        elif ignoreNext:
            ignoreNext = False
        else:
            newText   += ' '
            ignoreNext = True

    return unescape(newText)


def getFavourites(file):
    xml  = '<favourites></favourites>'
    if os.path.exists(file):  
        fav = open(file , 'r')
        xml = fav.read()
        fav.close()

    items = []

    faves = re.compile('<favourite(.+?)</favourite>').findall(xml)
    for fave in faves:
        fave = fave.replace('&quot;', '&_quot_;')
        fave = fave.replace('\'', '"')
        fave = unescape(fave)

        try:    name = re.compile('name="(.+?)"').findall(fave)[0]
        except: name = ''

        try:    thumb = re.compile('thumb="(.+?)"').findall(fave)[0]
        except: thumb = ''

        try:    cmd   = fave.rsplit('>', 1)[-1]
        except: cmd = ''

        name  = name.replace( '&_quot_;', '"')
        thumb = thumb.replace('&_quot_;', '"')
        cmd   = cmd.replace(  '&_quot_;', '"')


        if len(cmd) > 0:
            items.append([name, thumb, cmd])

    return items


def writeFavourites(file, faves):
    f = open(file, mode='w')

    f.write('<favourites>')

    for fave in faves:
        try:
            name  = 'name="%s" '  % escape(fave[0])
            thumb = 'thumb="%s">' % escape(fave[1])
            cmd   = escape(fave[2])

            f.write('\n\t<favourite ')
            f.write(name)
            f.write(thumb)
            f.write(cmd)
            f.write('</favourite>')
        except:
            pass

    f.write('\n</favourites>')            
    f.close()