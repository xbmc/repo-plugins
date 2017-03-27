#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Contributors:
#      Tommy Winther
#      Anders Norman
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
import re
import urllib

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo
import time

from mtgapi import MtgApi, MtgApiException

class TV3PlayAddon(object):
    def __init__(self, region):
        self.region = region
        self.api = MtgApi(region)

    def _build_url(self, query):
        if not 'region' in query.keys():
            query['region'] = self.region
        return PATH + '?' + urllib.urlencode(query)

    def listRegions(self):
        items = list()
        for region in MtgApi.REGIONS:
            item = xbmcgui.ListItem(region, iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            url = self._build_url({'region': region})
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def listChannels(self):
        items = list()
        for channel_id, channel_name in self.api.get_channels().iteritems():
            item = xbmcgui.ListItem(channel_name, iconImage=self.api.get_channel_icon(channel_id))
            item.setProperty('Fanart_Image', FANART)
            url = self._build_url({'channel': channel_id})
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def listShows(self, channel):
        items = list()

        shows = self.api.get_shows(channel)
        if not shows:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            self.displayError(ADDON.getLocalizedString(30205))
            return

        for show in shows:
            fanart = show['image']

            infoLabels = {
                'title': show['title']
                #'plot': show['description']
            }

            item = xbmcgui.ListItem(show['title'], iconImage=fanart)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', fanart)
            url = self._build_url({'seasons_url': show['_links']['seasons']['href']})
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def listSeasons(self, seasons_url):
        seasons = self.api.get_seasons(seasons_url)

        for season in seasons:
            fanart = season['_links']['image']['href'].format(size='500x500')

            item = xbmcgui.ListItem(season['title'], iconImage=fanart)
            item.setProperty('Fanart_Image', fanart)
            url = self._build_url({'episodes_url': season['_links']['videos']['href']})
            xbmcplugin.addDirectoryItem(HANDLE,
                                        url,
                                        item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def listEpisodes(self, episodes_url):
        items = list()

        episodes = self.api.get_episodes(episodes_url)

        for episode in episodes:
            fanart = episode['_links']['image']['href'].format(size='500x500')

            info_labels = {
                'title': episode['title'],
                'studio': ADDON.getAddonInfo('name'),
                'plot': episode['description'],
                'plotoutline': episode['summary'],
                'tvshowtitle': episode['format_title']
            }
            if 'duration' in episode and episode['duration'] is not None:
                info_labels['duration'] = int(episode['duration'])

            if 'broadcasts' in episode:
                if 'air_at' in episode['broadcasts'] and episode['broadcasts']['air_at'] is not None:
                    airdate = episode['air_at']
                    info_labels['date'] = '%s.%s.%s' % (airdate[8:10], airdate[5:7], airdate[0:4])
                    info_labels['year'] = int(airdate[0:4])

            if 'format_position' in episode:
                if episode['format_position']['is_episodic'] == 'true':
                    if 'episode' in episode['format_position'] and episode['format_position']['episode'] is not None:
                        info_labels['episode'] = int(episode['episode'])

            item = xbmcgui.ListItem(episode['title'], iconImage=fanart)
            item.setInfo('episode', info_labels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanart)

            streams = self.api.get_streams(episode)
            url = ""
            if 'hls' in streams and streams['hls'] is not None:
                url = streams['hls']
            elif 'high' in streams and streams['high'] is not None:
                url = streams['high']
            elif 'medium' in streams and streams['medium'] is not None:
                url = streams['medium']
            elif 'low' in streams and streams['low'] is not None:
                url = streams['low']
            url = self._build_url({'action': 'playVideo', 'playVideo': url, 'title': episode['title']})
            items.append((url, item))
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def getSubtitles(self, videoUrl):
        videoPath = videoUrl.replace('playlist.m3u8', '')

        playListFile = urllib.urlopen(videoUrl).read()
        playListFile = playListFile.encode('utf-8')
        srtFile = None
        subsFile = None
        vttSubs = None
        for line in playListFile.splitlines(True):
            subsearch = re.match(r'^#EXT-X-MEDIA:.*ID="subs".*AUTOSELECT=YES.*URI="(\w*.m3u8)', line)
            if subsearch:
                subsFile = subsearch.group(1)
                break
        if subsFile:
            subsFile = urllib.urlopen(videoPath + subsFile).read()
            subsFile = subsFile.encode('utf8')
            vttSubs = ''
            for line in subsFile.splitlines(True):
                chunk = re.match(r"(.*).webvtt", line)
                if chunk:
                    vttSubs = vttSubs + '\n'
                    vttSubs = vttSubs + urllib.urlopen(videoPath + chunk.group()).read()
        if vttSubs:
            srtFile = os.path.join(xbmc.translatePath("special://temp"), 'tv3play.srt')
            srtSubs = [line.replace('.',',') for line in vttSubs.splitlines(True)]
            fh = open(srtFile, 'w')
            try:
                fh.writelines(srtSubs[3:])
            finally:
                fh.close()

        return srtFile

    def playVideo(self, videoUrl, videoTitle):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add(videoUrl, xbmcgui.ListItem(videoTitle, iconImage=ICON))
        xbmcplugin.setResolvedUrl(HANDLE, True, playlist[0])

        player = xbmc.Player();
        subs_file = self.getSubtitles(videoUrl)
        if subs_file:
            start_time = time.time();
            while not player.isPlaying() and time.time() - start_time < 30:
                time.sleep(1);
            if player.isPlaying():
                xbmc.Player().setSubtitles(subs_file)

    def displayError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30200)
        line2 = ADDON.getLocalizedString(30201)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    xbmc.log("{0}{1}".format(sys.argv[0], sys.argv[2]))
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    r = None
    if 'region' in PARAMS:
        r = PARAMS['region'][0]
    elif ADDON.getSetting('region') in MtgApi.REGIONS:
        r = ADDON.getSetting('region')

    buggalo.SUBMIT_URL = 'http://buggalo.ext.norman.info/submit.php'
    tv3PlayAddon = TV3PlayAddon(r)
    try:
        if 'playVideo' in PARAMS:
            tv3PlayAddon.playVideo(PARAMS['playVideo'][0], PARAMS['title'][0])
        elif 'episodes_url' in PARAMS:
            tv3PlayAddon.listEpisodes(PARAMS['episodes_url'][0])
        elif 'seasons_url' in PARAMS:
            tv3PlayAddon.listSeasons(PARAMS['seasons_url'][0])
        elif 'channel' in PARAMS:
            tv3PlayAddon.listShows(PARAMS['channel'][0])
        elif r:
            tv3PlayAddon.listChannels()
        else:
            tv3PlayAddon.listRegions()

    except MtgApiException as ex:
        tv3PlayAddon.displayError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
