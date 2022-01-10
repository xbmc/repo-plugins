# -*- coding: utf-8 -*-
import datetime
import html
import json
import os
import re
import requests

from resources.lib import addonutils
from resources.lib.translate import translatedString as T
from simplecache import SimpleCache


class SkyItalia:
    """
    Class to get content from video.sky.it
    """
    HOME = 'https://video.sky.it/'
    API_BASE_URL = 'https://apid.sky.it/vdp/v1/'
    TOKEN = 'F96WlOd8yoFmLQgiqv6fNQRvHZcsWk5jDaYnDvhbiJk'
    GET_VIDEO_SEARCH = API_BASE_URL + 'getVideoDataSearch?section={section}&subsection={subsection}&page={page}&count=30&token=' + TOKEN
    GET_PLAYLISTS = API_BASE_URL + 'getPlaylistInfo?section={section}&subsection={subsection}&start=0&limit=31&token=' + TOKEN
    GET_PLAYLIST_VIDEO = API_BASE_URL + 'getPlaylistVideoData?id={playlist_id}&token=' + TOKEN
    GET_VIDEO_DATA = API_BASE_URL + 'getVideoData?caller=sky&rendition={rendition}&id={asset_id}&token=' + TOKEN
    GET_LIVESTREAM = API_BASE_URL + 'getLivestream?id={livestream_id}'
    LIVESTREAMS = {
        '1': {
            'label': 'Diretta TG24',
            'icon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Sky_TG24_-_Logo_2021.svg/512px-Sky_TG24_-_Logo_2021.svg.png',
        },
        '2': {
            'label': 'Cielo TV',
            'icon': 'https://upload.wikimedia.org/wikipedia/it/thumb/6/61/Cielo_TV_logo.svg/512px-Cielo_TV_logo.svg.png',
            'no_isa': True,
        },
        # '3': {'label':'Ante Factor','icon':''},
        # '4': {'label':'Le dirette di Sky Sport','icon':''},
        '7': {
            'label': 'TV8',
            'icon': 'https://upload.wikimedia.org/wikipedia/it/thumb/6/6d/TV8_Logo_2016.svg/512px-TV8_Logo_2016.svg.png',
            'no_isa': True,
        },
        '9': {
            'label': 'Le dirette live di Sky',
            'icon': '',
        },
    }
    TIMEOUT = 15
    QUALITIES = ['web_low_url', 'web_med_url', 'web_high_url', 'web_hd_url']

    def __init__(self, devmode=False):
        """
        initialize SimpleCache.
        """
        self.cache = SimpleCache()
        self.DEVMODE = devmode

    def _log(self, msg, level=0):
        """
        Log message
        If DEVMODE is enabled, all debug messages are raised to INFO,
        so everithing from the plugin is visible without
        activating Debug Log in Kodi.

        :param      msg:    The message
        :type       msg:    str
        :param      level:  loglevel
        :type       level:  int
        """
        if self.DEVMODE:
            addonutils.log(msg, 1 if level == 0 else level)
        elif level >= 3:
            addonutils.log(msg, level)

    def _openURL(self, url, hours=24):
        """
        Get url content from cache or from source
        depending if cache is available or not.

        :param      url:    The url
        :type       url:    str
        :param      hours:  cache retention period in hours
        :type       hours:  int

        :returns:   url content
        :rtype:     str
        """
        self._log(f"openURL, url = {url}", 1)
        try:
            cacheresponse = self.cache.get(
                f"{addonutils.ID}._openURL, url = {url}")
            if not cacheresponse:
                self._log('openURL, no cache found')
                response = requests.get(url, timeout=self.TIMEOUT)
                if response.status_code == requests.codes.ok:
                    response.encoding = 'utf-8'
                    self.cache.set(
                        f"{addonutils.ID}._openURL, url = {url}",
                        response.text,
                        expiration=datetime.timedelta(hours=hours))
                else:
                    response.raise_for_status()
            return self.cache.get(f"{addonutils.ID}._openURL, url = {url}")
        except Exception as e:
            self.cache = None
            self._log(f"openURL Failed! {e}", 3)
            addonutils.notify(T('error.openurl'))
            addonutils.endScript()

    def _loadData(self, url, hours=24):
        """
        Loads the JSON data from input url.

        :param      url:    The url
        :type       url:    str
        :param      hours:  cache retention period in hours
        :type       hours:  int

        :returns:   json data
        :rtype:     json
        """
        self._log(f"loadData, url = {url}", 1)
        response = self._openURL(url, hours=hours)

        try:
            # try if the response is json
            items = json.loads(response)
        except:
            # response is html (or other???)
            self._log('loadData, html page found')
            try:
                # section page, search for subsections
                subs = re.findall(
                    r'menu-entry-sub[^"]*"><a href="%s/(.+?)">(.+?)</a>' % url,
                    response, re.S)
                if len(subs) > 0:
                    self._log('loadData, subsections menu found')
                    return subs

                # search the main menu
                main = re.search(
                    r'"content":([\s\S]+?),\s*"highlights"', response).group(1)
                items = json.loads(main)
                self._log(f"loadData, main menu found: {len(items)} items")
            except Exception as e:
                addonutils.notify(T('error.json'))
                self._log(f"loadJsonData, NO JSON DATA FOUND; {e}", 3)
                addonutils.endScript()

        return items

    def _cleanTitle(self, title, remove=''):
        """
        Clean the title from the prefix provided.

        :param      title:   The title
        :type       title:   str
        :param      remove:  prefix to remove
        :type       remove:  str

        :returns:   cleaned title
        :rtype:     str
        """
        title = html.unescape(title)
        title = re.sub(r'^VIDEO:*\s+', '', title)
        title = re.sub(r'^%s\s*-\s+' % remove, '', title)
        return title

    def _iconPath(self, section, subsection=None):
        icon_path = os.path.join(addonutils.IMAGE_PATH_T, 'logos', section)
        if subsection:
            icon_path = os.path.join(icon_path, subsection)
        return f"{icon_path}.png"

    def _getDate(self, date):
        """
        Parses the date in the format DD/MM/YYYY and returns it in
        the format YYYY-MM-DD

        :param      date:  The date
        :type       date:  str
        """
        try:
            dd, mm, yy = re.match(r'(\d{2})/(\d{2})/(\d{4})', date).groups()
        except:
            dd, mm, yy = '01,01,2000'.split(',')
        return f"{yy}-{mm}-{dd}"

    def _getArts(self, icon=None, thumb=None, fanart=None):
        arts = {}
        arts['icon'] = icon or addonutils.ICON
        arts['fanart'] = fanart or addonutils.FANART
        arts['thumb'] = thumb
        return arts

    def _getVideoInfo(self, data, title=None):
        if not title:
            title = self._cleanTitle(
                data.get('title') or data.get('title_norm'))
        return {
            'videoInfo': {
                'mediatype': 'video',
                'title': title,
                'plot': data.get('xml_value') or data.get('short_desc') or data.get('meta_description'),
                'aired': self._getDate(data.get('modify_date') or data.get('create_date')),
            },
            'arts': self._getArts(
                thumb=data.get('thumb') or data.get('video_still')),
        }

    def _getAssets(self, data, title=''):
        """
        Extract assets from the provided JSON data

        :param      data:   The data
        :type       data:   json
        :param      title:  title of the data provided
        :type       title:  str

        :returns:   item
        :rtype:     dict
        """
        self._log(f"getAssets, assets = {len(data['assets'])}", 1)
        for item in data['assets']:
            label = self._cleanTitle(item['title'], title)
            info = {
                'label': label,
                'params': {
                    'asset_id': item['asset_id']
                },
                'videoInfo': {
                    'mediatype': 'video',
                },
                'isPlayable': True,
            }
            info.update(self._getVideoInfo(item, label))
            yield info

    def getMainMenu(self):
        """
        extract the main menu from the website

        :returns:   items
        :rtype:     dict
        """
        self._log(f"getMainMenu, url = {self.HOME}", 1)
        menu = self._loadData(self.HOME)
        for item in menu:
            # yield only active menu elements
            if menu[item]['active'] == 'Y':
                section = item.strip('/')
                yield {
                    'label': menu[item]['label'],
                    'params': {
                        'section': section
                    },
                    'arts': self._getArts(
                        icon=self._iconPath(section)),
                }
        yield {
            'label': T('dirette.title'),
            'params': {
                'live': True
            },
            'arts': self._getArts(),
        }

    def getSection(self, section):
        self._log(f"getSection, section = {section}", 1)
        subsections = self._loadData(f"{self.HOME}{section}")
        for s, t in subsections:
            label = self._cleanTitle(t)
            yield {
                'label': label,
                'params': {
                    'section': section,
                    'subsection': s,
                    'title': label,
                },
                'arts': self._getArts(
                    icon=self._iconPath(section, s)),
            }

    def getSubSection(self, section, subsection, title, page=0):
        self._log(
            f"getSubSection, section/subsection = {section}/{subsection}", 1)
        if self.getPlaylistsCount(section, subsection, True) > 0:
            yield {
                'label': T('playlist.title').format(title=title),
                'params': {
                    'section': section,
                    'subsection': subsection,
                    'playlist': title,
                },
                'arts': self._getArts(
                    icon=self._iconPath(section, subsection)),
            }

        url = self.GET_VIDEO_SEARCH.format(
            section=section,
            subsection=subsection,
            page=str(page))
        data = self._loadData(url, hours=0.5)
        yield from self._getAssets(data, title)

    def getPlaylistsCount(self, section, subsection, test=False):
        self._log(
            f"getPlaylistsCount, section/subsection = {section}/{subsection}", 1)
        url = self.GET_PLAYLISTS.format(
            section=section,
            subsection=subsection)
        data = self._loadData(url)
        length = len(data)
        self._log(f"getPlaylistsCount, data length: {length}")

        return length if test else data

    def getPlaylists(self, section, subsection):
        self._log(
            'getPlaylists, section/subsection = {section}/{subsection}', 1)
        data = self.getPlaylistsCount(section, subsection)

        for item in data:
            yield {
                'label': self._cleanTitle(item['title']),
                'params': {
                    'playlist_id': item['playlist_id'],
                },
                'arts': self._getArts(
                    thumb=item.get('thumb')),
            }

    def getPlaylistContent(self, playlist_id):
        """
        Get the playlist content of the provided playlist_id

        :param      playlist_id:  The playlist identifier
        :type       playlist_id:  str

        :returns:   items
        :rtype:     dict
        """
        self._log(f"getPlaylistContent, playlist_id = {playlist_id}", 1)
        url = self.GET_PLAYLIST_VIDEO.format(
            playlist_id=playlist_id)
        data = self._loadData(url, hours=0.5)
        yield from self._getAssets(data)

    def getLiveStreams(self):
        """
        Gets the live streams.

        :returns:   The live stream infos.
        :rtype:     dicts
        """
        self._log(
            f"getLiveStreams, total {len(self.LIVESTREAMS)} streams found.", 1)
        for i in self.LIVESTREAMS:
            yield {
                'label': self.LIVESTREAMS[i]['label'],
                'params': {
                    'livestream_id': i,
                    'no_isa': self.LIVESTREAMS[i].get('no_isa'),
                },
                'isPlayable': True,
                'arts': self._getArts(
                    thumb=self.LIVESTREAMS[i].get('icon'),
                    icon=self.LIVESTREAMS[i].get('icon')),
            }

    def getLiveStream(self, livestream_id=None):
        """
        Gets the live stream.

        :returns:   The live stream infos.
        :rtype:     dict
        """
        self._log(f"getLiveStream, id = {livestream_id}", 1)
        url = self.GET_LIVESTREAM.format(livestream_id=livestream_id)
        data = self._loadData(url, hours=0.1)
        if data.get('streaming_url'):
            self._log(
                f"getLiveStream, streaming_url = {data['streaming_url']}")

            return {
                'path': data['streaming_url'],
                'videoInfo': {
                    'title': self.LIVESTREAMS[livestream_id]['label'],
                    'plot': data.get('short_desc') or data.get('meta_description'),
                },
                'arts': self._getArts(
                    icon=self.LIVESTREAMS[livestream_id].get('icon')),
            }
        return None

    def getVideo(self, asset_id, isa=False, quality=3):
        """
        Retrieve the media url associated to the provided asset_id
        and according to the quality settings

        :param      asset_id:  The asset identifier
        :type       asset_id:  str

        :returns:   Media url
        :rtype:     str
        """
        rendition = 'hls' if isa else 'web'
        self._log(
            f"getVideo, asset_id = {asset_id}, rendition = {rendition}", 1)
        url = self.GET_VIDEO_DATA.format(
            rendition=rendition,
            asset_id=asset_id)
        data = self._loadData(url, hours=0.1)

        url = None
        if isa:
            url = data.get('hls_url')
        elif isinstance(quality, int):
            self._log(
                f"getPlaylistContent, quality_selected = {self.QUALITIES[quality]}")
            for i in range(quality, -1, -1):
                if self.QUALITIES[i] in data:
                    self._log(
                        f"getPlaylistContent, quality_found = {self.QUALITIES[i]}")
                    url = data[self.QUALITIES[i]]
                    if url:
                        break

        info = {
            'path': url,
            'videoInfo': {
                'mediatype': 'video',
            },
        }
        info.update(self._getVideoInfo(data))
        return info
