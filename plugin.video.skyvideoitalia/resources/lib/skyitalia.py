# -*- coding: utf-8 -*-
import datetime
import html
import json
import os
import re
import requests

from resources.lib import addonutils
from simplecache import SimpleCache


class SkyItalia:
    """
    Class to get content from video.sky.it
    """
    HOME = 'https://video.sky.it/'
    GET_VIDEO_SEARCH = 'https://video.sky.it/be/getVideoDataSearch?token={token}&section={section}&subsection={subsection}&page={page}&count=30'  # noqa: E501
    GET_PLAYLISTS = 'https://video.sky.it/be/getPlaylistInfo?token={token}&section={section}&subsection={subsection}&start=0&limit=31'  # noqa: E501
    GET_PLAYLIST_VIDEO = 'https://video.sky.it/be/getPlaylistVideoData?token={token}&id={id}'  # noqa: E501
    GET_VIDEO_DATA = 'https://apid.sky.it/vdp/v1/getVideoData?token={token}&caller=sky&rendition=web&id={id}'  # noqa: E501
    GET_LIVESTREAM = 'https://apid.sky.it/vdp/v1/getLivestream?id=%s'
    LIVESTREAMS = {
        '1': {
            'label': 'Diretta TG24',
            'icon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Sky_TG24_-_Logo_2021.svg/512px-Sky_TG24_-_Logo_2021.svg.png'
        },
        '2': {
            'label': 'Cielo TV',
            'icon': 'https://upload.wikimedia.org/wikipedia/it/thumb/6/61/Cielo_TV_logo.svg/512px-Cielo_TV_logo.svg.png'
        },
        # '3': {'label':'Ante Factor','icon':''},
        # '4': {'label':'Le dirette di Sky Sport','icon':''},
        '7': {
            'label': 'TV8',
            'icon': 'https://upload.wikimedia.org/wikipedia/it/thumb/6/6d/TV8_Logo_2016.svg/512px-TV8_Logo_2016.svg.png'
        },
        '9': {
            'label': 'Le dirette live di Sky',
            'icon': ''
        },
    }
    TOKEN = 'F96WlOd8yoFmLQgiqv6fNQRvHZcsWk5jDaYnDvhbiJk'
    TIMEOUT = 15
    DEBUG = addonutils.getSettingAsBool('Debug')
    LOGLEVEL = addonutils.getSettingAsInt('LogLevel')
    QUALITY = addonutils.getSettingAsInt('Quality')
    QUALITIES = ['web_low_url', 'web_med_url', 'web_high_url', 'web_hd_url']
    LOCAL_MAP = {
        'error.openurl': 31000,
        'error.json': 31001,
        'error.json.decode': 31002,
        'playlist.title': 32001,
        'dirette.title': 32002,
    }

    def __init__(self):
        """
        initialize SimpleCache.
        """
        self.cache = SimpleCache()

    def _log(self, msg, level=0):
        """
        Log message
        If DEBUG is selected, all messages are forced to ERROR,
        so everithing from the plugin is visible without
        activating Debug Log in Kodi.

        :param      msg:    The message
        :type       msg:    str
        :param      level:  loglevel
        :type       level:  int
        """
        if self.DEBUG:
            addonutils.log(msg, 3)
        elif level >= self.LOGLEVEL:
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
        self._log('openURL, url = %s' % url, 1)
        try:
            cacheresponse = self.cache.get(
                '%s._openURL, url = %s' % (addonutils.ID, url))
            if not cacheresponse:
                self._log('openURL, no cache found')
                response = requests.get(url, timeout=self.TIMEOUT)
                if response.status_code == requests.codes.ok:
                    response.encoding = 'utf-8'
                    self.cache.set(
                        '%s._openURL, url = %s' % (addonutils.ID, url),
                        response.text,
                        expiration=datetime.timedelta(hours=hours))
                else:
                    response.raise_for_status()
            return self.cache.get('%s._openURL, url = %s' % (addonutils.ID, url))
        except Exception as e:
            self.cache = None
            self._log("openURL Failed! " + str(e), 3)
            addonutils.notify(addonutils.LANGUAGE(self.LOCAL_MAP['error.openurl']))
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
        self._log('loadData, url = %s' % url, 1)
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
                self._log('loadData, main menu found: %d items' % len(items))
            except Exception as e:
                addonutils.notify(addonutils.LANGUAGE(self.LOCAL_MAP['error.json']))
                self._log('loadJsonData, NO JSON DATA FOUND; ' + str(e), 3)
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
        return icon_path + '.png'
        
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
        self._log('getAssets, assets = %d' % len(data['assets']), 1)
        for item in data['assets']:
            label = self._cleanTitle(item['title'], title)
            yield {
                'label': label,
                'params': {
                    'asset_id': item['asset_id']
                },
                'arts': {
                    'thumb': item.get('video_still') or item.get('thumb'),
                    'fanart': addonutils.FANART,
                },
                'videoInfo': {
                    'mediatype': 'video',
                    'title': label,
                },
                'isPlayable': True,
            }

    def getMainMenu(self):
        """
        extract the main menu from the website

        :returns:   items
        :rtype:     dict
        """
        self._log('getMainMenu, url = %s' % self.HOME, 1)
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
                    'arts': {
                        'icon': self._iconPath(section),
                        'fanart': addonutils.FANART,
                    },
                }
        yield {
            'label': addonutils.LANGUAGE(self.LOCAL_MAP['dirette.title']),
            'params': {
                'live': True
            },
            'arts': {
                'icon': addonutils.ICON,
                'fanart': addonutils.FANART,
            },
        }

    def getSection(self, section):
        self._log('getSection, section = %s' % section, 1)
        subsections = self._loadData('%s%s' % (self.HOME, section))
        for s, t in subsections:
            label = self._cleanTitle(t)
            yield {
                'label': label,
                'params': {
                    'section': section,
                    'subsection': s,
                    'title': label,
                },
                'arts': {
                    'icon': self._iconPath(section, s),
                    'fanart': addonutils.FANART,
                },
            }

    def getSubSection(self, section, subsection, title, page=0):
        self._log('getSubSection, section/subsection = %s/%s' % (section, subsection), 1)
        if self.getPlaylistsCount(section, subsection, True) > 0:
            yield {
                'label': addonutils.LANGUAGE(self.LOCAL_MAP['playlist.title']) % title,
                'params': {
                    'section': section,
                    'subsection': subsection,
                    'playlist': title,
                },
                'arts': {
                    'icon': '%s%s\\%s.png' % (
                        self.LOGOSDIR, section, subsection),
                    'fanart': addonutils.FANART,
                },
            }

        url = self.GET_VIDEO_SEARCH
        url = url.replace('{token}', self.TOKEN)
        url = url.replace('{section}', section)
        url = url.replace('{subsection}', subsection)
        url = url.replace('{page}', str(page))
        data = self._loadData(url, hours=0.5)
        yield from self._getAssets(data, title)

    def getPlaylistsCount(self, section, subsection, test=False):
        self._log('getPlaylistsCount, section/subsection = %s/%s' % (section, subsection), 1)
        url = self.GET_PLAYLISTS
        url = url.replace('{token}', self.TOKEN)
        url = url.replace('{section}', section)
        url = url.replace('{subsection}', subsection)
        data = self._loadData(url)
        length = len(data)
        self._log('getPlaylistsCount, data length:%d' % length)

        return length if test else data

    def getPlaylists(self, section, subsection):
        self._log('getPlaylists, section/subsection = %s/%s' % (section, subsection), 1)
        data = self.getPlaylistsCount(section, subsection)

        for item in data:
            yield {
                'label': self._cleanTitle(item['title']),
                'params': {
                    'playlist_id': item['playlist_id'],
                },
                'arts': {
                    'thumb': item['thumb'],
                    'fanart': addonutils.FANART,
                },
            }

    def getPlaylistContent(self, playlist_id):
        """
        Get the playlist content of the provided playlist_id

        :param      playlist_id:  The playlist identifier
        :type       playlist_id:  str

        :returns:   items
        :rtype:     dict
        """
        self._log('getPlaylistContent, playlist_id = %s' % playlist_id, 1)
        url = self.GET_PLAYLIST_VIDEO
        url = url.replace('{token}', self.TOKEN)
        url = url.replace('{id}', playlist_id)
        data = self._loadData(url, hours=0.5)
        yield from self._getAssets(data)

    def getLiveStreams(self):
        """
        Gets the live streams.

        :returns:   The live stream infos.
        :rtype:     dicts
        """
        self._log('getLiveStreams, total %d streams found.' % len(self.LIVESTREAMS), 1)
        for i in self.LIVESTREAMS:
            yield {
                'label': self.LIVESTREAMS[i]['label'],
                'params': {
                    'livestream_id': i,
                },
                'arts': {
                    'icon': self.LIVESTREAMS[i].get('icon'),
                    'thumb': self.LIVESTREAMS[i].get('icon'),
                    'fanart': addonutils.FANART,
                },
                'isPlayable': True,
            }

    def getLiveStream(self, livestream_id=None):
        """
        Gets the live stream.

        :returns:   The live stream infos.
        :rtype:     dict
        """
        self._log('getLiveStream, id = %s' % livestream_id, 1)
        data = self._loadData(
            self.GET_LIVESTREAM % livestream_id, hours=0.1)
        if data.get('streaming_url'):
            self._log('getLiveStream, streaming_url = %s' % data['streaming_url'])

            return {
                'path': data['streaming_url'],
                'videoInfo': {
                    'title': self.LIVESTREAMS[livestream_id]['label'],
                    'plot': data.get('short_desc') or data.get('meta_description'),
                },
                'arts': {
                    'icon': self.LIVESTREAMS[livestream_id].get('icon'),
                }
            }
        return None

    def getVideo(self, asset_id):
        """
        Retrieve the media url associated to the provided asset_id
        and according to the quality settings

        :param      asset_id:  The asset identifier
        :type       asset_id:  str

        :returns:   Media url
        :rtype:     str
        """
        self._log('getVideo, asset_id = %s' % asset_id, 1)
        url = self.GET_VIDEO_DATA
        url = url.replace('{token}', self.TOKEN)
        url = url.replace('{id}', asset_id)
        data = self._loadData(url)

        url = None
        self._log('getPlaylistContent, quality_selected = %s' % self.QUALITIES[self.QUALITY])
        for i in range(int(self.QUALITY), 0, -1):
            if self.QUALITIES[i] in data:
                self._log('getPlaylistContent, quality_found = %s' % self.QUALITIES[i])
                url = data[self.QUALITIES[i]]
                if url:
                    break

        return url
