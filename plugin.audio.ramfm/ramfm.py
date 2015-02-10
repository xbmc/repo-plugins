#
#      Copyright (C) 2013 Sean Poyser
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

import urllib
import urllib2
import re
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import datetime
import time
import os
import common

ADDONID = 'plugin.audio.ramfm'
ADDON   = xbmcaddon.Addon(ADDONID)
GETTEXT = ADDON.getLocalizedString
URL     = 'http://www.ramfm.org/index.php'

def GetHTML(url=URL, artist=None):
    if artist:
       url += '?' + artist

    html = common.GetHTML(url)
    html = html.replace('&quot', '')

    return html


#Remove Tags method from
#http://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string

TAG_RE = re.compile('<.*?>')
def RemoveTags(html):
    return TAG_RE.sub('', html)


def Clean(text):
    try:
        text = text.replace('&#8211;', '-' )
        text = text.replace('&#8216;', '\'')
        text = text.replace('&#8217;', '\'')
        text = text.replace('&#8220;', '"' )
        text = text.replace('&#8221;', '"' )
        text = text.replace('&#39;',   '\'')
        text = text.replace('&amp;',   '&' )
        text = text.replace('\xe2',    ''  )
        text = text.replace('\x80',    ''  )
        text = text.replace('\x93',    ''  )

        if '\xe9' in text:
            text = text.decode('latin-1')
    except:
        pass

    return text


def GetStrapline(html):
    try:
        match = re.compile('<div align="center">(.+?)</div>').search(html)       
        text  = RemoveTags(match.group(1))
        length = -1
        while len(text) != length:
            length = len(text)
            text   = text.replace('  ', ' ')
    except Exception, e:
        pass
        text = GETTEXT(30017)

    return text


def GetMainLogo(html):
    try:
        match = re.compile('<img src="(.+?)"').search(html)
        return match.group(1)
    except Exception, e:
        pass

    return 'http://ramfm.org/images/logo_top.png'


def GetNowOnAir(html):
    #NEEDS FIXING
    np = dict()
    np['mode'] = 'NowOnAir'

    match  = re.compile('<a onmouseover=(.+?)</a>').findall(html)[2]

    image  = re.compile('<img src=;(.+?);').findall(match)
    track  = match.split('<b>')

    np['artist']   = track[2].split('</b>',   1)[0]
    np['track']    = track[3].split('</b>',   1)[0]
    np['year']     = track[3].split('<br />', 2)[1]
    np['last']     = track[6].split('</b>',   1)[0].replace('<br/>',  ' ')        
    np['image']    = image[0]
    np['format']   = image[1]
    np['wiki']     = ''#re.compile('ref="(.+?)"').search(match).group(1)

    try:    np['rotation'] = track[12].split('</b>',  1)[0].replace('&nbsp;', ' ')
    except: np['rotation'] = ''

    try:    np['request']  = track[9].split('</b>',   1)[0].replace('&nbsp;', ' ')
    except: np['request']  = ''

    info = html.split('Now On Air')[1]
    info = info.split('<table')[0]
    info = info.replace('\n', '')
    print info
    info = re.compile('pt">(.+?)<').findall(info)
    print info

    np['artist']   = info[0]
    np['track']    = info[1]
    np['year']     = ''
    np['last']     = 'Sunday October 20th 17:29'
    np['image']    = 'image'
    np['format']   = 'format'
    np['wiki']     = 'wiki'
    np['rotation'] = 'rotation'
    np['request']  = 'rotation'

    return np


def GetNowPlaying(html):
    if 'Now On Air' in html:
        return GetNowOnAir(html)
    np = dict()
    np['mode'] = 'NowPlaying'
    try:
        match  = re.compile('<a onmouseover=(.+?)</a>').search(html).group(1)
        image  = re.compile('<img src=;(.+?);').findall(match)
        track  = match.split('<b>')

        np['artist']   = track[2].split('</b>',   1)[0] #http://ramfm.org/artistpic/na.gif, http://ramfm.org/randim.php
        np['track']    = track[3].split('</b>',   1)[0]
        np['year']     = track[3].split('<br />', 2)[1]
        np['last']     = track[6].split('</b>',   1)[0].replace('<br/>',  ' ')        
        np['image']    = image[0]
        np['format']   = image[1]
        np['wiki']     = re.compile('ref="(.+?)"').search(match).group(1)

        try:
            np['request']  = track[9].split('</b>',   1)[0].replace('&nbsp;', ' ')
        except:
            np['request']  = '-1'

        try:
            np['rotation'] = track[12].split('</b>',  1)[0].replace('&nbsp;', ' ')
        except:
            np['rotation'] = np['request']
            np['request']  = -1

        np['artist'] = Clean(np['artist'])
        np['track']  = Clean(np['track'])
        
    except Exception, e:
        pass

    return np


def GetBiography(url):
    list = []
    if url == '':
        return list

    try:
        html = GetHTML(url)
        bio = html
        bio = bio.split('<div id="wiki">')[1]
        bio = bio.split('<!-- #wiki -->')[0]
        bio = RemoveTags(bio)
        bio = Clean(bio)
        bio = bio.split('\n')
    
        for para in bio:
            para = para.strip()
            if len(para) > 0:
                list.append(para)
    except:
        pass

    return list