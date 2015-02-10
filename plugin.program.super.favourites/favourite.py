
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
import re

import utils


HOMESPECIAL = 'special://home/'
HOMEFULL    = xbmc.translatePath(HOMESPECIAL)

SHOWUNAVAIL = utils.ADDON.getSetting('SHOWUNAVAIL') == 'true'


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
    text = text.replace('&amp;',  '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', '\'')
    text = text.replace('&gt;',   '>')
    text = text.replace('&lt;',   '<')
    return text


def getFavourites(file, limit=10000, validate=True, superSearch=False):
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

        add = False

        if superSearch:
            add = isValid(cmd)
        elif (SHOWUNAVAIL) or (not validate) or isValid(cmd):
            add = True

        if add:
            items.append([name, thumb, cmd])
            if len(items) > limit:
                return items

    return items


def writeFavourites(file, faves):
    f = open(file, mode='w')

    f.write('<favourites>')

    for fave in faves:
        try:
            name  = escape(fave[0])
            thumb = escape(fave[1])
            cmd   = escape(fave[2])

            thumb = convertToHome(thumb)

            name  = 'name="%s" '  % name
            thumb = 'thumb="%s">' % thumb

            f.write('\n\t<favourite ')
            f.write(name)
            f.write(thumb)
            f.write(cmd)
            f.write('</favourite>')
        except:
            pass

    f.write('\n</favourites>')            
    f.close()

    import xbmcgui
    try:    count = int(xbmcgui.Window(10000).getProperty('Super_Favourites_Count'))
    except: count = 0    
    xbmcgui.Window(10000).setProperty('Super_Favourites_Count', str(count+1))


def tidy(cmd):
    cmd = cmd.replace('&quot;', '')
    cmd = cmd.replace('&amp;', '&')
    cmd = removeFanart(cmd)
    cmd = removeWinID(cmd)

    if cmd.startswith('RunScript'):
        cmd = cmd.replace('?content_type=', '&content_type=')
        cmd = re.sub('/&content_type=(.+?)"\)', '")', cmd)

    if cmd.endswith('/")'):
        cmd = cmd.replace('/")', '")')

    if cmd.endswith(')")'):
        cmd = cmd.replace(')")', ')')

    return cmd


def isValid(cmd):
    if len(cmd) == 0:
        return False

    cmd = tidy(cmd)

    if 'PlayMedia' in cmd:
        return utils.verifyPlayMedia(cmd)
        

    if 'plugin' in cmd:        
        if not utils.verifyPlugin(cmd):
            return False

    if 'RunScript' in cmd:
        cmd = re.sub('/&content_type=(.+?)"\)', '")', cmd)
        if not utils.verifyScript(cmd):
            return False
        
    return True


def updateFave(file, update):
    cmd = update[2]
    fave, index, nFaves = findFave(file, cmd)
   
    removeFave(file, cmd)
    return insertFave(file, update, index)


def findFave(file, cmd):
    cmd   = removeFanart(cmd)
    faves = getFavourites(file, validate=False)
    for idx, fave in enumerate(faves):
        if equals(fave[2], cmd):
            return fave, idx, len(faves)

    search = os.path.join(xbmc.translatePath(utils.ROOT), 'Search', utils.FILENAME).lower()

    if file.lower() != search:
        return None, -1, 0

    for idx, fave in enumerate(faves):
        if '[%SF%]' in fave[2]:
            test = fave[2].split('[%SF%]', 1)
            if cmd.startswith(test[0]) and cmd.endswith(test[1]):
                return fave, idx, len(faves)

    return None, -1, 0


def insertFave(file, newFave, index):
    copy = []
    faves = getFavourites(file, validate=False)
    for fave in faves:
        if len(copy) == index:
            copy.append(newFave)
        copy.append(fave)

    if index >= len(copy):
        copy.append(newFave)

    writeFavourites(file, copy)
    return True


def addFave(file, newFave):
    faves = getFavourites(file, validate=False)
    faves.append(newFave)

    writeFavourites(file, faves)
    return True


def moveFave(src, dst, fave):
    if not copyFave(dst, fave):
        return False
    return removeFave(src, fave[2])


def copyFave(file, original):
    faves   = getFavourites(file, validate=False)
    updated = False

    copy = list(original)
    copy = removeFanart(copy[2])

    #if it is already in then just update it
    for idx, fave in enumerate(faves):
        if equals(removeFanart(fave[2]), copy):
            updated    = True
            faves[idx] = original
            break

    if not updated:
        faves.append(original)

    writeFavourites(file, faves)
    return True


def removeFave(file, cmd):
    cmd   = removeFanart(cmd)
    copy  = []
    faves = getFavourites(file, validate=False)

    for fave in faves:
        if not equals(removeFanart(fave[2]), cmd):
            copy.append(fave)

    if len(copy) == len(faves):       
        return False

    writeFavourites(file, copy)
    return True


def shiftFave(file, cmd, up):
    fave, index, nFaves = findFave(file, cmd)
    max = nFaves - 1
    if up:
        index -= 1
        if index < 0:
            index = max
    else: #down
        index += 1
        if index > max:
            index = 0

    removeFave(file, cmd)
    return insertFave(file, fave, index)


def renameFave(file, cmd, newName):
    copy = []
    faves = getFavourites(file, validate=False)
    for fave in faves:
        if equals(fave[2], cmd):
            fave[0] = newName

        copy.append(fave)

    writeFavourites(file, copy)
    return True


def equals(fave, cmd):
    if fave == cmd:
        return True

    if 'sf_fanart' in fave:
        fave = removeFanart(fave)

    if 'sf_fanart' in cmd:
        cmd = removeFanart(cmd)

    if fave == cmd:
        return True

    if '[%SF%]' not in fave:
        return False

    test = fave.split('[%SF%]', 1)
    if cmd.startswith(test[0])  and cmd.endswith(test[1]):
        return True

    return False


def getFanart(cmd):
    cmd = cmd.replace(',return', '')

    import urllib 
    try:    return urllib.unquote_plus(re.compile('sf_fanart=(.+?)_"\)').search(cmd).group(1))
    except: pass

    cmd = urllib.unquote_plus(cmd)
    cmd = cmd.replace(',return', '')
    try:    return urllib.unquote_plus(re.compile('sf_fanart=(.+?)_"\)').search(cmd).group(1))
    except: pass

    return ''       


def addFanart(cmd, fanart):
    import urllib 

    hasReturn = False
    if cmd.endswith(',return)'):
        hasReturn = True
        cmd = cmd.replace(',return', '')

    cmd = removeFanart(cmd)

    if cmd.endswith('")'):
        cmd = cmd.rsplit('")', 1)[0]

    if '?' in cmd:   
        cmd += '&'
    else:
        cmd += '?'

    cmd += 'sf_fanart=%s_")' % urllib.quote_plus(convertToHome(fanart))

    if hasReturn:
        cmd = cmd.replace(')', ',return)')

    return cmd


def removeFanart(cmd):
    if 'sf_fanart=' not in cmd:
        return cmd

    cmd = cmd.replace('?sf_fanart=', '&sf_fanart=')
    cmd = cmd.replace('&sf_fanart=', '&sf_fanart=X') #in case no fanart

    cmd = re.sub('&sf_fanart=(.+?)_"\)', '")',               cmd)
    cmd = re.sub('&sf_fanart=(.+?)_",return\)', '",return)', cmd)
    cmd = re.sub('&sf_fanart=(.+?)_',    '',                 cmd)

    cmd = cmd.replace('/")', '")')

    return cmd


def removeWinID(cmd):
    if 'sf_win_id' not in cmd:
        return cmd

    cmd = cmd.replace('?sf_win_id=', '&sf_win_id=')
    cmd = cmd.replace('&sf_win_id=', '&sf_win_id=X') #in case no win_id
    cmd = re.sub('&sf_win_id=(.+?)_"\)', '")', cmd)

    return cmd


def convertToHome(text):
    if text.startswith(HOMEFULL):
        text = text.replace(HOMEFULL, HOMESPECIAL)

    return text
