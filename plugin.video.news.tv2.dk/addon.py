#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
from htmlentitydefs import name2codepoint
import os
import sys
import urlparse
import urllib2
import re
import buggalo
import xbmcgui
import xbmcaddon
import xbmcplugin
import simplejson
import datetime

# http://nyhederne.tv2.dk/video/data/tag/nyheder/
# http://nyhederne.tv2.dk/video/data/tag/nyh0600/day/0/staticjsonp/staticjsonp_148f9/

TAGS = ['nyheder', 'most-viewed', 'nyh0600', 'nyh0900', 'nyh1700', 'nyh1900', 'nyh2200', 'station2', 'newsmagasiner']

VIDEO_DATA_URL = "http://nyhederne.tv2.dk/video/data/tag/%s/"
PLAYLIST_URL = 'http://common.tv2.dk/mpx/player.php/adtech_alias-player_nyhederne/adtech_group-441/autoplay-1/guid-%s/player_id-video_nyhederne.html'
FLASH_PLAYLIST_URL = 'http://common.tv2.dk/flashplayer/playlist.xml.php/clipid-%s.xml'


class TV2NewsAddon(object):

    def listTags(self):
        for idx, tag in enumerate(TAGS):
            title = ADDON.getLocalizedString(30000 + idx)

            item = xbmcgui.ListItem(title, iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?tag=' + tag
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)

    def listClips(self, tag):
        try:
            u = urllib2.urlopen(VIDEO_DATA_URL % tag)
            data = u.read()
            u.close()
            clips = simplejson.loads(data.decode('iso-8859-1'))
        except Exception as ex:
            heading = buggalo.getRandomHeading()
            line1 = ADDON.getLocalizedString(30900)
            line2 = ADDON.getLocalizedString(30901)
            xbmcgui.Dialog().ok(heading, line1, line2, str(ex))
            return

        for clip in clips:
            if 'section' in clip:
                title = self._decodeHtmlEntities('%s: %s' % (clip['section'], clip['title']))
            else:
                title = self._decodeHtmlEntities(clip['title'])
            date = datetime.date.fromtimestamp(clip['created'])

            item = xbmcgui.ListItem(title, iconImage=clip['img'])
            item.setInfo('video', {
                'title': title,
                'studio': ADDON.getAddonInfo('name'),
                'plot': self._decodeHtmlEntities(clip['description']),
                'date': date.strftime('%d.%m.%Y')
            })

            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?id=' + str(clip['id'])
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playClip(self, clipId):
        try:
            u = urllib2.urlopen(PLAYLIST_URL % clipId)
            html = u.read()
            u.close()

            m = re.match(".*var releaseUrl = '([^']+)'", html, re.DOTALL)
            if m:  # new style playlist
                u = urllib2.urlopen(m.group(1))
                playlist = u.read()
                u.close()

                m = re.match('.*<video src="([^"]+)"', playlist, re.DOTALL)
                url = m.group(1)
            else:  # flash playlist
                u = urllib2.urlopen(FLASH_PLAYLIST_URL % clipId)
                xml = u.read()
                u.close()

                m = re.match('.*video="([^"]+)"', xml, re.DOTALL)
                url = m.group(1)

        except Exception as ex:
            heading = buggalo.getRandomHeading()
            line1 = ADDON.getLocalizedString(30900)
            line2 = ADDON.getLocalizedString(30901)
            xbmcgui.Dialog().ok(heading, line1, line2, str(ex))

            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            return

        item = xbmcgui.ListItem(thumbnailImage=ICON)
        if url:
            item.setPath(url)

        xbmcplugin.setResolvedUrl(HANDLE, succeeded=url is not None, listitem=item)

    def _decodeHtmlEntities(self, string):
        """Decodes the HTML entities found in the string and returns the modified string.

        Both decimal (&#000;) and hexadecimal (&x00;) are supported as well as HTML entities,
        such as &aelig;

        Keyword arguments:
        string -- the string with HTML entities

        """
        if type(string) not in [str, unicode]:
            return string

        def substituteEntity(match):
            ent = match.group(3)
            if match.group(1) == "#":
                # decoding by number
                if match.group(2) == '':
                    # number is in decimal
                    return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x'+ent, 16))
            else:
                # they were using a name
                cp = name2codepoint.get(ent)
                if cp:
                    return unichr(cp)
                else:
                    return match.group()

        entity_re = re.compile(r'&(#?)(x?)(\w+);')
        return entity_re.subn(substituteEntity, string)[0]


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        tv2News = TV2NewsAddon()
        if 'tag' in PARAMS:
            tv2News.listClips(PARAMS['tag'][0])
        elif 'id' in PARAMS:
            tv2News.playClip(PARAMS['id'][0])
        else:
            tv2News.listTags()
    except Exception:
        buggalo.onExceptionRaised()