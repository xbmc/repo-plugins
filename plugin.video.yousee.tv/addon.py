#
#      Copyright (C) 2014 Tommy Winther
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
import os
import sys
import urlparse
import urllib2
import StringIO

import ysapi
import buggalo

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin


class YouSeeTv(object):
    def showLiveTVChannels(self):
        api = ysapi.YouSeeLiveTVApi()
        channels = api.allowedChannels()
        if not channels:
            self._showError()
            xbmcplugin.endOfDirectory(HANDLE, False)
            return

        try:
            self._generateChannelIcons(channels)
        except Exception:
            xbmc.log("Caught exception while generating channel icons!")

        for channel in channels:
            if channel['encrypted']:
                continue

            iconImage = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
            if not os.path.exists(iconImage):
                iconImage = channel['logos']['large']
            item = xbmcgui.ListItem(channel['nicename'], iconImage=iconImage, thumbnailImage=iconImage)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            item.setProperty('IsPlayable', 'true')
            url = PATH + '?channel=' + str(channel['id'])
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.endOfDirectory(HANDLE, succeeded=len(channels) > 0)

    def playLiveTVChannel(self, channelId):
        api = ysapi.YouSeeLiveTVApi()
        channel = api.channel(channelId)
        stream = api.streamUrl(channelId, 'iphone')
        if not stream or not 'url' in stream or not stream['url']:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

            if stream and 'error' in stream:
                self._showError(stream['error'])
            else:
                self._showError()
            return

        url = self.getBestStream(stream['url'])

        thumbnailImage = os.path.join(CACHE_PATH, str(channelId) + '.png')
        if not os.path.exists(thumbnailImage):
            thumbnailImage = channel['logos']['large']
        item = xbmcgui.ListItem(channel['nicename'], path=url, thumbnailImage=thumbnailImage)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def getBestStream(self, url):
        u = urllib2.urlopen(url)
        m3u8 = u.read()
        u.close()

        lines = m3u8.splitlines()
        bestBitrate = 0
        path = ''
        for idx in range(0, len(lines)):
            pos = lines[idx].rfind('BANDWIDTH')
            if pos >= 0:
                bandwidth = lines[idx][pos + 10:]
                pos = bandwidth.find(',')
                if pos >= 0:
                    bandwidth = bandwidth[:pos]
                print bandwidth
                bitrate = int(bandwidth)
                if bitrate > bestBitrate:
                    bestBitrate = bitrate
                    path = lines[idx + 1]

        if path[0] == '/':  # absolute path
            host = url[0:url.find('/', 8)]
            playUrl = host + path
        else:  # relative
            playUrl = url[0:url.rfind('/') + 1] + path
        return playUrl

    def _anyChannelIconsMissing(self, channels):
        for channel in channels:
            path = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
            if not os.path.exists(path):
                return True
        return False

    def _generateChannelIcons(self, channels):
        """
        Generates a pretty 256x256 channel icon by downloading the channel graphics
        and pasting in onto the channel_bg.png. The result is cached.

        In case the PIL library is not available the URL
        for the channel graphics is used directly.
        """

        if self._anyChannelIconsMissing(channels):
            import PIL.Image

            sys.modules['Image'] = PIL.Image  # http://projects.scipy.org/scipy/ticket/1374
            iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'channel_bg.png')

            for channel in channels:
                path = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
                xbmc.log("Generating image for " + channel['nicename'] + "...")

                u = urllib2.urlopen(channel['logos']['large'])
                data = u.read()
                u.close()

                image = PIL.Image.open(StringIO.StringIO(data))
                (width, height) = image.size

                out = PIL.Image.open(iconImage)

                x = (256 - width) / 2
                y = (256 - height) / 2
                if image.mode == 'RGBA':
                    out.paste(image, (x, y), image)
                else:
                    out.paste(image, (x, y))

                out.save(path)

    def isYouSeeIP(self):
        api = ysapi.YouSeeUsersApi()
        try:
            isYouSeeIP = api.isYouSeeIP()['status'] == 1
        except Exception:
            isYouSeeIP = False

        if not isYouSeeIP and ADDON.getSetting('warn.if.not.yousee.ip') == 'true':
            heading = ADDON.getLocalizedString(30970)
            line1 = ADDON.getLocalizedString(30971)
            line2 = ADDON.getLocalizedString(30972)
            line3 = ADDON.getLocalizedString(309973)
            nolabel = ADDON.getLocalizedString(30974)
            yeslabel = ADDON.getLocalizedString(30975)
            if xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel):
                ADDON.setSetting('warn.if.not.yousee.ip', 'false')

    def _showError(self, description=None):
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        if description is None:
            description = ADDON.getLocalizedString(30053)
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30050), ADDON.getLocalizedString(30051),
                            ADDON.getLocalizedString(30052), description)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART_IMAGE = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    ytv = YouSeeTv()
    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        if 'channel' in PARAMS:
            ytv.playLiveTVChannel(PARAMS['channel'][0])

        else:
            ytv.isYouSeeIP()
            ytv.showLiveTVChannels()

    except ysapi.YouSeeApiException, ex:
        ytv._showError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
