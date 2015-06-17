
#       Copyright (C) 2013-2015
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
import re

import utils

import sfile


HOMESPECIAL = 'special://home/'
HOMEFULL    = xbmc.translatePath(HOMESPECIAL)

SHOWUNAVAIL = utils.ADDON.getSetting('SHOWUNAVAIL') == 'true'


def getFavourites(file, limit=10000, validate=True, superSearch=False):
    import xbmcgui

    xml  = '<favourites></favourites>'
    if sfile.exists(file):
        xml = sfile.read(file)

    items = []

    faves = re.compile('<favourite(.+?)</favourite>').findall(xml)

    for fave in faves:
        fave = fave.replace('&quot;', '&_quot_;')
        fave = fave.replace('\'', '"')
        fave = utils.unescape(fave)

        fave = fave.replace('name=""', '')
        try:    name = re.compile('name="(.+?)"').findall(fave)[0]
        except: name = ''

        try:    thumb = re.compile('thumb="(.+?)"').findall(fave)[0]
        except: thumb = ''

        try:    cmd   = fave.split('>', 1)[-1]
        except: cmd = ''

        #name  = utils.Clean(name.replace( '&_quot_;', '"'))
        name  = name.replace( '&_quot_;', '"')
        thumb = thumb.replace('&_quot_;', '"')
        cmd   = cmd.replace(  '&_quot_;', '"')

        add = False

        if superSearch:
            add = isValid(cmd)
        elif (SHOWUNAVAIL) or (not validate) or isValid(cmd):
            add = True

        if add:
            cmd = upgradeCmd(cmd)

            if cmd.startswith('PlayMedia'):
                option = 'mode'
                try:                        
                    mode = int(favourite.getOption(cmd, option))
                except:
                    win  = xbmcgui.getCurrentWindowId()
                    cmd  = updateSFOption(cmd, 'winID', win)

            cmd = patch(cmd)

            items.append([name, thumb, cmd])
            if len(items) > limit:
                return items

    return items


def patch(cmd):
    cmd = cmd.replace('&quot;,return', 'SF_PATCHING1')
    cmd = cmd.replace('",return',      'SF_PATCHING2')

    cmd = cmd.replace(',return'      ,  '')

    cmd = cmd.replace('SF_PATCHING1'  , '&quot;,return')
    cmd = cmd.replace('SF_PATCHING2'  , '",return')

    return cmd


def upgradeCmd(cmd):
    fanart = _getFanart(cmd)
    winID  = _getWinID(cmd)

    cmd = _removeFanart(cmd)
    cmd = _removeWinID(cmd)

    options = {}
    if fanart:
        options['fanart'] = fanart

    if winID > -1:
        options['winID'] = winID

    if len(options) > 0:
        cmd = updateSFOptions(cmd, options)

    return cmd


def writeFavourites(file, faves):
    kodiFile = os.path.join('special://profile', utils.FILENAME)
    isKodi = xbmc.translatePath(file) == xbmc.translatePath(kodiFile)

    f = sfile.file(file, 'w')

    f.write('<favourites>')

    for fave in faves:
        try:
            name  = utils.escape(fave[0])
            thumb = utils.escape(fave[1])
            cmd   = utils.escape(fave[2])

            if isKodi:
                cmd = removeSFOptions(cmd)

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
    cmd = removeSFOptions(cmd)

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


def replaceFave(file, update, oldCmd):
    fave, index, nFaves = findFave(file, oldCmd)

    if index < 0:
        return addFave(file, update)
   
    removeFave(file, oldCmd)
    return insertFave(file, update, index)


def findFave(file, cmd):
    cmd   = removeSFOptions(cmd)
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
    copy = removeSFOptions(copy[2])

    #if it is already in then just update it
    for idx, fave in enumerate(faves):
        if equals(removeSFOptions(fave[2]), copy):
            updated    = True
            faves[idx] = original
            break

    if not updated:
        faves.append(original)

    writeFavourites(file, faves)
    return True


def removeFave(file, cmd):
    cmd   = removeSFOptions(cmd)
    copy  = []
    faves = getFavourites(file, validate=False)

    for fave in faves:
        if not equals(removeSFOptions(fave[2]), cmd):
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

    fave = removeSFOptions(fave)
    cmd  = removeSFOptions(cmd)

    if fave == cmd:
        return True

    if '[%SF%]' not in fave:
        return False

    test = fave.split('[%SF%]', 1)
    if cmd.startswith(test[0])  and cmd.endswith(test[1]):
        return True

    return False


def addFanart(cmd, fanart):
    return updateSFOption(cmd, 'fanart', convertToHome(fanart))


def updateSFOption(cmd, option, value):
    options = getSFOptions(cmd)

    options[option] = value

    return updateSFOptions(cmd, options)

    
def updateSFOptions(cmd, options):
    cmd = removeSFOptions(cmd)

    if len(options) == 0:
        return cmd

    import urllib 

    hasReturn = False
    if cmd.endswith(',return)'):
        hasReturn = True
        cmd = cmd.replace(',return', '')

    if cmd.endswith('")'):
        cmd = cmd.rsplit('")', 1)[0]

    suffix = '?'
    if '?' in cmd:   
        suffix = '&'

    values = ''
    for key in options.keys():
        value = str(options[key])
        if len(value) > 0:
            values += '%s=%s&' % (key, value)
        
    if len(values) > 0:
        cmd += suffix + 'sf_options=%s_options_sf"' % urllib.quote_plus(values)
    else:
        cmd += '"'

    if hasReturn:
        cmd += ',return)'
    else:
        cmd += ')'

    return cmd


def getSFOptions(cmd):
    import urllib 

    try:    options = urllib.unquote_plus(re.compile('sf_options=(.+?)_options_sf').search(cmd).group(1))
    except: return {}

    return get_params(options)


def removeSFOptions(cmd):
    if 'sf_options=' not in cmd:
        return cmd

    cmd = cmd.replace('?sf_options=', '&sf_options=')

    cmd = re.sub('&sf_options=(.+?)_options_sf"\)', '")',               cmd)
    cmd = re.sub('&sf_options=(.+?)_options_sf",return\)', '",return)', cmd)
    cmd = re.sub('&sf_options=(.+?)_options_sf',    '',                 cmd)

    cmd = cmd.replace('/")', '")')

    return cmd


def convertToHome(text):
    if text.startswith(HOMEFULL):
        text = text.replace(HOMEFULL, HOMESPECIAL)

    return text


def getFanart(cmd):
    return getOption(cmd, 'fanart')


def getOption(cmd, option):
    options = getSFOptions(cmd)

    try:    return options[option]
    except: return ''


def get_params(p):
    param=[]
    paramstring=p
    if len(paramstring)>=2:
        params=p
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
           params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param


#used only during upgrade process
def _removeFanart(cmd):
    if 'sf_fanart=' not in cmd:
        return cmd

    cmd = cmd.replace('?sf_fanart=', '&sf_fanart=')
    cmd = cmd.replace('&sf_fanart=', '&sf_fanart=X') #in case no fanart

    cmd = re.sub('&sf_fanart=(.+?)_"\)', '")',               cmd)
    cmd = re.sub('&sf_fanart=(.+?)_",return\)', '",return)', cmd)
    cmd = re.sub('&sf_fanart=(.+?)_',    '',                 cmd)

    cmd = cmd.replace('/")', '")')

    return cmd


#used only during upgrade process
def _getFanart(cmd):
    cmd = cmd.replace(',return', '')

    import urllib 
    try:    return urllib.unquote_plus(re.compile('sf_fanart=(.+?)_"\)').search(cmd).group(1))
    except: pass

    cmd = urllib.unquote_plus(cmd)
    cmd = cmd.replace(',return', '')

    try:    return urllib.unquote_plus(re.compile('sf_fanart=(.+?)_"\)').search(cmd).group(1))
    except: pass

    return ''       


#used only during upgrade process
def _removeWinID(cmd):
    if 'sf_win_id' not in cmd:
        return cmd

    cmd = cmd.replace('?sf_win_id=', '&sf_win_id=')
    cmd = cmd.replace('&sf_win_id=', '&sf_win_id=X') #in case no win_id
    cmd = re.sub('&sf_win_id=(.+?)_"\)', '")', cmd)

    return cmd


#used only during upgrade process
def _getWinID(cmd):
    if 'sf_win_id' not in cmd:
        return -1

    try:    return int(re.compile('sf_win_id=(.+?)_').search(cmd).group(1))
    except: pass

    return -1