#
#      Copyright (C) 2012 Tommy Winther
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
from xml.etree import ElementTree
import os
import sys
import urlparse
import urllib2
import re

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo

REGIONS = ['tv3play.dk', 'tv3play.se', 'tv3play.no', 'tv3play.lt', 'tv3play.lv', 'tv3play.ee', 'viasat4play.no']
RSS = { 301 : 'recent', 302 : 'mostviewed', 303 : 'highestrated', 304 : 'recent?type=clip' }

class TV3PlayException(Exception):
    pass

class TV3PlayAddon(object):
    def listRegions(self):
        items = list()
        for region in REGIONS:
            item = xbmcgui.ListItem(region, iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            items.append((PATH + '?region=%s' % region, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)


    def listPrograms(self, region):
        url = 'http://www.%s/program' % region
        buggalo.addExtraData('url', url)
        html = self.downloadUrl(url)
        if not html:
            raise TV3PlayException(ADDON.getLocalizedString(204))

        items = list()
        for stringId in sorted(RSS.keys()):
            item = xbmcgui.ListItem(ADDON.getLocalizedString(stringId), iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            items.append((PATH + '?region=%s&rss=%s' % (region, stringId), item, True))

        for m in re.finditer('<a href="/program/([^"]+)">([^<]+)</a>', html):
            slug = m.group(1)
            title = m.group(2)
            fanart = self.downloadAndCacheFanart(slug, None)

            item = xbmcgui.ListItem(title, iconImage=fanart)
            item.setProperty('Fanart_Image', fanart)
            items.append((PATH + '?region=%s&program=%s' % (region, slug), item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def listSeasons(self, region, slug):
        url = 'http://www.%s/program/%s' % (region, slug)
        buggalo.addExtraData('url', url)
        html = self.downloadUrl(url)
        if not html:
            raise TV3PlayException(ADDON.getLocalizedString(203))

        fanart = self.downloadAndCacheFanart(slug, html)

        m = re.search('Table body(.*?)</tbody>.*?Table body(.*?)</tbody>', html, re.DOTALL)
        if not m:
            raise TV3PlayException(ADDON.getLocalizedString(203))
        episodesHtml = m.group(1)
        clipsHtml = m.group(2)

        seasons = episodesHtml.split('class="season-head')
        for seasonHtml in seasons:
            m = re.search('<strong>(.*?)</strong>', seasonHtml)
            season = m.group(1)
            videoCount = seasonHtml.count('href="/play/')
            if videoCount > 0:
                item = xbmcgui.ListItem(season, iconImage = ICON)
                if fanart:
                    item.setIconImage(fanart)
                    item.setProperty('Fanart_Image', fanart)
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?region=%s&program=%s&season=%s' % (region, slug, season), item, True, videoCount)

        seasons = clipsHtml.split('class="season-head')
        for seasonHtml in seasons:
            m = re.search('<strong>(.*?)</strong>', seasonHtml)
            season = m.group(1)
            videoCount = seasonHtml.count('href="/play/')
            if videoCount > 0:
                item = xbmcgui.ListItem('%s (%s)' % (season.decode('utf8', 'ignore'), ADDON.getLocalizedString(103)), iconImage = fanart)
                item.setProperty('Fanart_Image', fanart)
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?region=%s&program=%s&season=%s&clips=true' % (region, slug, season), item, True, videoCount)


        xbmcplugin.endOfDirectory(HANDLE)


    def listVideos(self, region, slug, season, clips = False):
        url = 'http://www.%s/program/%s' % (region, slug)
        buggalo.addExtraData('url', url)
        html = self.downloadUrl(url)
        if not html:
            raise TV3PlayException(ADDON.getLocalizedString(204))
        fanart = self.downloadAndCacheFanart(slug, html)

        m = re.search('Table body(.*?)</tbody>.*?Table body(.*?)</tbody>', html, re.DOTALL)
        if clips:
            html = m.group(2)
        else:
            html = m.group(1)

        snip = ''
        seasons = html.split('class="season-head')
        for seasonHtml in seasons:
            if seasonHtml.count(season) > 0:
                snip = seasonHtml
                break

        items = list()
        for m in re.finditer('<a href="/play/([0-9]+)/".*?>([^<]+)<.*?col2">([^<]*)<.*?col3">([^<]+)<.*?col4">([^<]*)<.*?rated-([0-5])', snip, re.DOTALL):
            videoId = m.group(1)
            title = m.group(2)
            episode = m.group(3)
            duration = m.group(4)
            airDate = m.group(5)
            rating = int(m.group(6)) * 2.0

            date = '%s.%s.20%s' % (airDate[0:2], airDate[3:5], airDate[6:8])

            infoLabels = {
                'title' : title,
                'date' : date,
                'studio' : ADDON.getAddonInfo('name'),
                'duration' : duration,
                'rating' : rating
            }
            if episode:
                infoLabels['episode'] = int(episode)

            item = xbmcgui.ListItem(title, iconImage = fanart)
            item.setInfo('video', infoLabels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanart)
            items.append((PATH + '?playVideo=%s' % videoId, item))

        if not clips:
            items.reverse()
            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def listRss(self, region, id):
        url = 'http://www.%s/rss/%s' % (region, RSS[int(id)])
        buggalo.addExtraData('url', url)
        xml = self.downloadUrl(url)
        if not xml:
            raise TV3PlayException(ADDON.getLocalizedString(204))
        doc = ElementTree.fromstring(xml.replace('&', '&amp;'))

        items = list()
        for node in doc.findall('channel/item'):
            videoId = node.findtext('id')
            title = node.findtext('title')
            description = node.findtext('description')
            icon = node.findtext('thumbnailImage')
            infoLabels = {
                'title' : title,
                'plot' : description
            }
            pubDate = node.findtext('pubDate')
            if pubDate:
                infoLabels['year'] = int(pubDate[0:4])
                infoLabels['aired'] = pubDate[0:10]
                infoLabels['date'] = '%s.%s.%s' % (pubDate[8:10], pubDate[5:7], pubDate[0:4])

            item = xbmcgui.ListItem(title, iconImage = icon)
            item.setInfo('video', infoLabels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', FANART)
            items.append((PATH + '?playVideo=%s' % videoId, item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)


    def playVideo(self, videoId):
        doc = self.getPlayProductXml(videoId)
        url = doc.findtext('Product/Videos/Video/Url')
        if not url:
            raise TV3PlayException(ADDON.getLocalizedString(202))
        rtmpUrl = self.getRtmpUrl(url) + ' swfUrl=http://flvplayer.viastream.viasat.tv/play/swf/player111227.swf swfVfy=true'

        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        firstItem = None

        # Preroll
        prerollNode = doc.find('Product/AdCalls/preroll')
        if prerollNode is not None:
            url = prerollNode.get('url')
            node = self.getXml(url).find('Ad')
            if node is not None:
                flvUrl = node.findtext('InLine/Creatives/Creative/Linear/MediaFiles/MediaFile')
                item = xbmcgui.ListItem(ADDON.getLocalizedString(100), iconImage = ICON)
                playlist.add(flvUrl, item)

                firstItem = item

        start = 0
        for idx, node in enumerate(doc.findall('Product/AdCalls/midroll')):
            adXml = self.downloadUrl(node.get('url'))
            if not adXml:
                continue
            adDoc = ElementTree.fromstring(adXml.decode('utf8', 'ignore'))
            adUrl = adDoc.findtext('Ad/InLine/Creatives/Creative/Linear/MediaFiles/MediaFile')
            if not adUrl:
                continue

            stop = int(node.get('time'))
            itemUrl = rtmpUrl + ' start=%d stop=%d' % (start * 1000, stop * 1000)
            featureItem = xbmcgui.ListItem(doc.findtext('Product/Title'), thumbnailImage=doc.findtext('Product/Images/ImageMedia/Url'), path = itemUrl)
            playlist.add(itemUrl, featureItem)
            start = stop

            if firstItem is None:
                firstItem = featureItem

            item = xbmcgui.ListItem(ADDON.getLocalizedString(100), iconImage = ICON)
            playlist.add(adUrl, item)

        itemUrl = rtmpUrl + ' start=%d' % (start * 1000)
        featureItem = xbmcgui.ListItem(doc.findtext('Product/Title'), thumbnailImage=doc.findtext('Product/Images/ImageMedia/Url'), path = itemUrl)
        playlist.add(itemUrl, featureItem)

        # Postroll
        postrollNode = doc.find('Product/AdCalls/postroll')
        if postrollNode is not None:
            url = postrollNode.get('url')
            node = self.getXml(url).find('Ad')
            if node is not None:
                flvUrl = node.findtext('InLine/Creatives/Creative/Linear/MediaFiles/MediaFile')
                item = xbmcgui.ListItem(ADDON.getLocalizedString(100), iconImage = ICON)
                playlist.add(flvUrl, item)

        if firstItem is not None:
            xbmcplugin.setResolvedUrl(HANDLE, True, firstItem)
        else:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

    def getPlayProductXml(self, videoId):
        url = 'http://viastream.viasat.tv/PlayProduct/%s' % videoId
        buggalo.addExtraData('playProductXml', url)
        xml = self.downloadUrl(url)
        if xml:
            xml = re.sub('&[^a]', '&amp;', xml)
            return ElementTree.fromstring(xml)
        else:
            return ElementTree.Element('data-not-loaded') # to avoid unnessecary error handling

    def getRtmpUrl(self, videoUrl):
        if videoUrl[0:4] == 'rtmp':
            return videoUrl.replace(' ', '%20')

        xml = self.downloadUrl(videoUrl)
        if not xml:
            raise TV3PlayException(ADDON.getLocalizedString(202))
        doc = ElementTree.fromstring(xml)

        if doc.findtext('Success') == 'true':
            return doc.findtext('Url').replace(' ', '%20')
        else:
            raise TV3PlayException(doc.findtext('Msg'))

    def getXml(self, url):
        xml = self.downloadUrl(url)
        if xml:
            return ElementTree.fromstring(xml.decode('utf8', 'ignore'))
        else:
            return ElementTree.Element('data-not-loaded') # to avoid unnessecary error handling

    def downloadAndCacheFanart(self, slug, html):
        fanartPath = os.path.join(CACHE_PATH, '%s.jpg' % slug.encode('iso-8859-1', 'replace'))
        if not os.path.exists(fanartPath) and html:
            m = re.search('/play/([0-9]+)/', html)
            if not m:
                return FANART
            xml = self.getPlayProductXml(m.group(1))

            fanartUrl = None
            for node in xml.findall('Product/Images/ImageMedia'):
                if node.findtext('Usage') == 'PlayImage':
                    fanartUrl = node.findtext('Url')
                    break

            if fanartUrl:
                imageData = self.downloadUrl(fanartUrl.replace(' ', '%20'))
                if imageData:
                    f = open(fanartPath, 'wb')
                    f.write(imageData)
                    f.close()

                    return fanartPath

        elif os.path.exists(fanartPath):
            return fanartPath

        return FANART

    def downloadUrl(self, url):
        for retries in range(0, 5):
            try:
                r = urllib2.Request(url.encode('iso-8859-1', 'replace'))
                r.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2')
                u = urllib2.urlopen(r, timeout = 30)
                contents = u.read()
                u.close()
                return contents
            except Exception, ex:
                if retries > 5:
                    raise TV3PlayException(ex)


    def displayError(self, message = 'n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(200)
        line2 = ADDON.getLocalizedString(201)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    tv3PlayAddon = TV3PlayAddon()
    try:
        if PARAMS.has_key('playVideo'):
            tv3PlayAddon.playVideo(PARAMS['playVideo'][0])
        elif PARAMS.has_key('program') and PARAMS.has_key('season'):
            tv3PlayAddon.listVideos(PARAMS['region'][0], PARAMS['program'][0], PARAMS['season'][0], PARAMS.has_key('clips'))
        elif PARAMS.has_key('program'):
            tv3PlayAddon.listSeasons(PARAMS['region'][0], PARAMS['program'][0])
        elif PARAMS.has_key('rss'):
            tv3PlayAddon.listRss(PARAMS['region'][0], PARAMS['rss'][0])
        elif PARAMS.has_key('region'):
            tv3PlayAddon.listPrograms(PARAMS['region'][0])
        else:
            tv3PlayAddon.listRegions()

    except TV3PlayException, ex:
        tv3PlayAddon.displayError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()

