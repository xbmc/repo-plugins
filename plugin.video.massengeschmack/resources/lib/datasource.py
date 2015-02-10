# -*- coding: utf-8 -*-
# 
# Massengeschmack XBMC add-on
# Copyright (C) 2013 by Janek Bevendorff
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import xbmcgui
import urllib
import datetime
import re
from globalvars import *
import resources.lib
from resources.lib.listing import *

class DataSource(object):
    id = -1
    """Numeric ID of the show."""
    
    moduleName = ''
    """Internal module name."""
    
    showMetaData = {
        'Title'     : None,
        'Director'  : None,
        'Genre'     : None,
        'Premiered' : None,
        'Country'   : None,
        'Plot'      : None
    }
    """Global meta data for the show."""
    
    def getListItems(self):
        """
        Generate a list of ListItem objects for the current data source.
        """
        return [
            # Fernsehkritik-TV
            ListItem(
                FKTVDataSource.id,
                ADDON.getLocalizedString(30200),
                resources.lib.assembleListURL(FKTVDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + FKTVDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + FKTVDataSource.module + '.jpg',
                FKTVDataSource.showMetaData
            ),
            # Pantoffel-TV
            ListItem(
                PTVDataSource.id,
                ADDON.getLocalizedString(30210),
                resources.lib.assembleListURL(PTVDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + PTVDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + PTVDataSource.module + '.jpg',
                PTVDataSource.showMetaData
            ),
            # Pressesch(l)au
            ListItem(
                PSDataSource.id,
                ADDON.getLocalizedString(30220),
                resources.lib.assembleListURL(PSDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + PSDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + PSDataSource.module + '.jpg',
                PSDataSource.showMetaData
            ),
            # Pasch-TV
            ListItem(
                PaschTVDataSource.id,
                ADDON.getLocalizedString(30240),
                resources.lib.assembleListURL(PaschTVDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + PaschTVDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + PaschTVDataSource.module + '.jpg',
                PaschTVDataSource.showMetaData
            ),
            # Netzprediger
            ListItem(
                NetzpredigerDataSource.id,
                ADDON.getLocalizedString(30250),
                resources.lib.assembleListURL(NetzpredigerDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + NetzpredigerDataSource.module + '_20140310.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + NetzpredigerDataSource.module + '_20140310.jpg',
                NetzpredigerDataSource.showMetaData
            ),
            # Asynchron
            ListItem(
                AsynchronDataSource.id,
                ADDON.getLocalizedString(30260),
                resources.lib.assembleListURL(AsynchronDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + AsynchronDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + AsynchronDataSource.module + '.jpg',
                AsynchronDataSource.showMetaData
            ),
            # Tonangeber
            ListItem(
                TonangeberDataSource.id,
                ADDON.getLocalizedString(30264),
                resources.lib.assembleListURL(TonangeberDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + TonangeberDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + TonangeberDataSource.module + '.jpg',
                TonangeberDataSource.showMetaData
            ),
            # Hoaxilla-TV
            ListItem(
                HoaxillaTVDataSource.id,
                ADDON.getLocalizedString(30400),
                resources.lib.assembleListURL(HoaxillaTVDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + HoaxillaTVDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + HoaxillaTVDataSource.module + '.jpg',
                HoaxillaTVDataSource.showMetaData
            ),
            # Massengeschmack-TV
            ListItem(
                MGTVDataSource.id,
                ADDON.getLocalizedString(30230),
                resources.lib.assembleListURL(MGTVDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + MGTVDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + MGTVDataSource.module + '.jpg',
                MGTVDataSource.showMetaData
            ),
            # Live
            ListItem(
                LiveDataSource.id,
                ADDON.getLocalizedString(30270),
                resources.lib.assembleListURL(LiveDataSource.module),
                ADDON_BASE_PATH + '/resources/media/banner-' + LiveDataSource.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + LiveDataSource.module + '.jpg',
                LiveDataSource.showMetaData
            ),
        ]
    
    def getContentMode(self):
        """
        Get the view mode for the listing content.
        
        Content mode is usually either 'tvshows' or 'episodes', but can
        also be any other valid value for xbmcplugin.setContent().
        
        @return content mode
        """
        return 'tvshows'
    
    def _buildFeedURL(self, ids, quality):
        """
        Build a feed URL which points to an RSS feed filtered by the given IDs.
        
        This method relies on self.id being set properly in derived classes.
        
        @protected
        
        @type ids: list
        @param ids: a list of numeric IDs of all sub shows to filter by
        @type quality: str
        @param quality: the movie quality (either 'hd', 'mobile' or 'audio')
        """
        url = HTTP_BASE_FEED_URI
        
        first = True
        for i in ids:
            if not first:
                url += 'x'
            first = False
            url += str(self.id) + '-' + str(i)
            
        url += '/' + quality + '.xml'
        
        return url


class LiveDataSource(DataSource):
    id           = -9999
    module       = 'live'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30270),
        'Country'  : ADDON.getLocalizedString(30271),
        'Plot'     : ADDON.getLocalizedString(30272)
    }
    
    def __init__(self):
        self.__shows    = resources.lib.getLiveShows()
        self.__current  = []
        self.__upcoming = []
        self.__isLive   = False
        
        for i in self.__shows:
            if i['isLive']:
                self.__isLive = True
                self.__current.append(i)
            else:
                self.__upcoming.append(i)
    
    def getListItems(self):
        listItems = []
        
        if [] != self.__current:
            listItems.append(
                ListItem(
                    self.id,
                    ADDON.getLocalizedString(30273),
                    '#',
                    self.__getThumbnailURL(0),
                    ADDON_BASE_PATH + '/resources/media/fanart-' + LiveDataSource.module + '.jpg',
                    {
                        'Plot' : ADDON.getLocalizedString(30274)
                    }
                )
            )
            
            listItems.extend(self.__createShowListing(self.__current, True))
            
        if [] != self.__upcoming:
            listItems.append(
                ListItem(
                    self.id,
                    ADDON.getLocalizedString(30275),
                    '#',
                    self.__getThumbnailURL(0),
                    ADDON_BASE_PATH + '/resources/media/fanart-' + LiveDataSource.module + '.jpg',
                    {
                        'Plot' : ADDON.getLocalizedString(30276)
                    }
                )
            )
            listItems.extend(self.__createShowListing(self.__upcoming))
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __createShowListing(self, shows, isLive=False):
        listItems = []
        
        for i in shows:
            iconimage = self.__getThumbnailURL(i['pid'])
            plot      = i['oneliner']
            time      = datetime.datetime.fromtimestamp(float(i['begin'])).strftime('%d.%m.%Y, %H:%M:%S')
            date      = datetime.datetime.fromtimestamp(float(i['begin'])).strftime('%d.%m.%Y')
            name      = self.__getShowName(int(i['pid']))
            
            if None == plot:
                plot = ''
            else:
                plot += '\n\n'
            
            plot += ADDON.getLocalizedString(30277).format(name, time)
            
            metaData  = {
                'Title'     : name,
                'Date'      : date,
                'Premiered' : date,
                'Plot'      : plot
            }
            
            listName   = '    ' + name + ' [' + time + ']'
            streamName = name + ' [' + ADDON.getLocalizedString(30270) + ']'
            
            isFolder = True
            if True == isLive:
                isFolder = False
            
            listItems.append(
                ListItem(
                    self.id,
                    listName,
                    resources.lib.assemblePlayURL(self.__getStreamURL(i['showid']), streamName, iconimage, metaData),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    isFolder=isFolder
                )
            )
        
        return listItems
    
    def __getShowName(self, id):
        if -3 == id:
            # Livetalk
            return ADDON.getLocalizedString(30280)
        elif 0 == id:
            # Massengeschmack-TV
            return ADDON.getLocalizedString(30230)
        elif 1 == id:
            # FKTV
            return ADDON.getLocalizedString(30200)
        elif 2 == id:
            # PantoffelTV
            return ADDON.getLocalizedString(30210)
        elif 3 == id:
            # Pressesch(l)au
            return ADDON.getLocalizedString(30220)
        elif 4 == id:
            # Pasch-TV
            return ADDON.getLocalizedString(30240)
        elif 5 == id:
            # Netzprediger
            return ADDON.getLocalizedString(30250)
        elif 6 == id:
            # Asynchron
            return ADDON.getLocalizedString(30260)
        elif 7 == id:
            # Tonangeber
            return ADDON.getLocalizedString(30264)
        elif 8 == id:
            # Hoaxilla-TV
            return ADDON.getLocalizedString(30400)
        else:
            return '-'
    
    def __getStreamURL(self, showid):
        info = resources.lib.getLiveStreamInfo(showid)
        if False == info:
            return '#'
        return info['url']
    
    def __getThumbnailURL(self, id):
        return 'http://massengeschmack.tv/img/logo' + str(id) + '_feed.jpg'
    

class FKTVDataSource(DataSource):
    id           = 1
    module       = 'fktv'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30200),
        'Director' :'Holger Kreymeier, Nils Beckmann, Daniel Gusy',
        'Genre'    : ADDON.getLocalizedString(30201),
        'Premiered':'07.04.2007',
        'Country'  : ADDON.getLocalizedString(30202),
        'Plot'     : ADDON.getLocalizedString(30203)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all'          : DataSource._buildFeedURL(self, [1, 2, 3, 4, 5], 'hd'),
                'episodes'     : DataSource._buildFeedURL(self, [1], 'hd'),
                'postecke'     : DataSource._buildFeedURL(self, [2], 'hd'),
                'interviews'   : DataSource._buildFeedURL(self, [3], 'hd'),
                'extras'       : DataSource._buildFeedURL(self, [4], 'hd'),
                'sendeschluss' : DataSource._buildFeedURL(self, [5], 'hd')
            },
            'mobile' : {
                'all'          : DataSource._buildFeedURL(self, [1, 2, 3, 4, 5], 'mobile'),
                'episodes'     : DataSource._buildFeedURL(self, [1], 'mobile'),
                'postecke'     : DataSource._buildFeedURL(self, [2], 'mobile'),
                'interviews'   : DataSource._buildFeedURL(self, [3], 'mobile'),
                'extras'       : DataSource._buildFeedURL(self, [4], 'mobile'),
                'sendeschluss' : DataSource._buildFeedURL(self, [5], 'mobile')
            },
            'audio' : {
                'all'          : DataSource._buildFeedURL(self, [1, 2, 3, 4, 5], 'audio'),
                'episodes'     : DataSource._buildFeedURL(self, [1], 'audio'),
                'postecke'     : DataSource._buildFeedURL(self, [2], 'audio'),
                'interviews'   : DataSource._buildFeedURL(self, [3], 'audio'),
                'extras'       : DataSource._buildFeedURL(self, [4], 'audio'),
                'sendeschluss' : DataSource._buildFeedURL(self, [5], 'audio')
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        submodule = None
        if 'submodule' in ADDON_ARGS and ADDON_ARGS['submodule'] in self.__urls[quality]:
            submodule = ADDON_ARGS['submodule']
        
        if None == submodule:
            return self.__getBaseList()
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality][submodule], True)
        listItems = []
        
        # in old Postecke category show link to Massengeschmack Direkt
        if 'postecke' == submodule:
            listItems.append(
                ListItem(
                    MGTVDataSource.id,
                    ADDON.getLocalizedString(30367),
                    resources.lib.assembleListURL(MGTVDataSource.module, 'direkt'),
                    ADDON_BASE_PATH + '/resources/media/banner-' + MGTVDataSource.module + 'direkt.png',
                    ADDON_BASE_PATH + '/resources/media/fanart-' + MGTVDataSource.module + '.jpg',
                    {
                        'Title' : ADDON.getLocalizedString(30367),
                        'Plot'  : ADDON.getLocalizedString(30368)
                    }
                )
            )
        
        for i in data:
            iconimage = i["thumbUrl"]
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30201),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30232),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        if 'submodule' in ADDON_ARGS:
            return 'episodes'
        
        return 'tvshows'
    
    def __getThumbnailURL(self, guid):
        basePath1 = 'http://fernsehkritik.tv/images/magazin/'
        basePath2 = 'http://massengeschmack.tv/img/mag/'
        basePath3 = 'http://dl.massengeschmack.tv/img/mag/'

        if 'fktv' == guid[:4]:
            # if new Postecke or new FKTV episode
            if -1 != guid[4:].find('-') or re.match(r'^fktv(\d+)interview\d+', guid) or 128 < int(guid[4:]):
                return basePath3 + guid + '.jpg'
            return basePath1 + 'folge' + guid[4:] + '@2x.jpg'
        elif 'postecke' == guid[:8]:
            # if newer Postecke
            if 128 < int(guid[8:]):
                return basePath3 + guid + '.jpg'
            return basePath2 + 'postecke.jpg'
        elif 'interview-' == guid[:10]:
            # ugly fixes for single episodes
            if 'remote' == guid[10:]:
                return basePath2 + 'remotecontrol.jpg'
            elif 'weber' == guid[10:]:
                return basePath3 + 'interview-' + guid[10:] + '.jpg'
            
            return basePath2 + guid[10:] + '.jpg'
        elif 'sendeschluss' == guid[:12] and 14 < int(guid[12:]):
            return basePath3 + guid + '.jpg'
        
        return basePath2 + guid + '.jpg'
    
    def __getBaseList(self):
        return [
            # All
            ListItem(
                self.id,
                ADDON.getLocalizedString(30300),
                resources.lib.assembleListURL(self.module, 'all'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30300),
                    'Plot': ADDON.getLocalizedString(30350)
                }
            ),
            # Episodes
            ListItem(
                self.id,
                ADDON.getLocalizedString(30301),
                resources.lib.assembleListURL(self.module, 'episodes'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30301),
                    'Plot': ADDON.getLocalizedString(30351)
                }
            ),
            # Sendeschluss
            ListItem(
                self.id,
                ADDON.getLocalizedString(30356),
                resources.lib.assembleListURL(self.module, 'sendeschluss'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30356),
                    'Plot': ADDON.getLocalizedString(30357)
                }
            ),
            # Postecke
            ListItem(
                self.id,
                ADDON.getLocalizedString(30352),
                resources.lib.assembleListURL(self.module, 'postecke'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30352),
                    'Plot': ADDON.getLocalizedString(30353)
                }
            ),
            # Interviews
            ListItem(
                self.id,
                ADDON.getLocalizedString(30302),
                resources.lib.assembleListURL(self.module, 'interviews'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30302),
                    'Plot': ADDON.getLocalizedString(30354)
                }
            ),
            # Extras
            ListItem(
                self.id,
                ADDON.getLocalizedString(30303),
                resources.lib.assembleListURL(self.module, 'extras') ,
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30303),
                    'Plot': ADDON.getLocalizedString(30355)
                }
            )
        ]


class PTVDataSource(DataSource):
    id           = 2
    module       = 'ptv'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30210),
        'Director' :'Holger Kreymeier, Jenny von Gagern, Steven Gräwe, Michael Stock',
        'Genre'    : ADDON.getLocalizedString(30211),
        'Premiered':'17.06.2013',
        'Country'  : ADDON.getLocalizedString(30212),
        'Plot'     : ADDON.getLocalizedString(30213)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30211),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30232),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        # if old PTV episode
        if 13 > int(guid[4:]):
            episodeNumber = '1'
            if 'ptv-pilot' == guid[:9]:
                if 'ptv-pilot' != guid:
                    # if not very first episode
                    episodeNumber= guid[9:]
            else:
                episodeNumber = guid[4:]
            
            return 'http://pantoffel.tv/img/thumbs/ptv' + episodeNumber + '_shot1@2x.jpg'
        
        return 'http://dl.massengeschmack.tv/img/mag/' + guid + '.jpg'


class PSDataSource(DataSource):
    id           = 3
    module       = 'ps'
    showMetaData = {
        'Title'     : ADDON.getLocalizedString(30220),
        'Director'  :'Holger Kreymeier, Steven Gräwe, Daniel Gusy',
        'Genre'     : ADDON.getLocalizedString(30221),
        'Premiered' :'01.08.2013',
        'Country'   : ADDON.getLocalizedString(30222),
        'Plot'      : ADDON.getLocalizedString(30223)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30221),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30232),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        baseURL = 'http://dl.massengeschmack.tv/img/mag/'
        
        if 'ps-pilot' == guid:
            guid = 'ps1'
        
        if 11 > int(guid[2:]):
            baseURL = 'http://massengeschmack.tv/img/ps/'
        
        return baseURL + guid + '.jpg'


class MGTVDataSource(DataSource):
    id           = 0
    module       = 'mgtv'
    showMetaData = {
        'Title'     : ADDON.getLocalizedString(30230),
        'Director'  :'Holger Kreymeier',
        'Genre'     : ADDON.getLocalizedString(30231),
        'Premiered' :'05.08.2013',
        'Country'   : ADDON.getLocalizedString(30232),
        'Plot'      : ADDON.getLocalizedString(30233)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all'      : DataSource._buildFeedURL(self, [1, 2, 3], 'hd'),
                'internal' : DataSource._buildFeedURL(self, [1], 'hd'),
                'studio'   : DataSource._buildFeedURL(self, [2], 'hd'),
                'direkt'   : DataSource._buildFeedURL(self, [3], 'hd')
            },
            'mobile' : {
                'all'      : DataSource._buildFeedURL(self, [1, 2, 3], 'mobile'),
                'internal' : DataSource._buildFeedURL(self, [1], 'mobile'),
                'studio'   : DataSource._buildFeedURL(self, [2], 'mobile'),
                'direkt'   : DataSource._buildFeedURL(self, [3], 'mobile')
            },
            'audio' : {
                'all'      : DataSource._buildFeedURL(self, [1, 2, 3], 'audio'),
                'internal' : DataSource._buildFeedURL(self, [1], 'audio'),
                'studio'   : DataSource._buildFeedURL(self, [2], 'audio'),
                'direkt'   : DataSource._buildFeedURL(self, [3], 'audio')
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        submodule = None
        if 'submodule' in ADDON_ARGS and ADDON_ARGS['submodule'] in self.__urls[quality]:
            submodule = ADDON_ARGS['submodule']
        
        if None == submodule:
            return self.__getBaseList()
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality][submodule], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30231),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30232),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        if 'submodule' in ADDON_ARGS:
            return 'episodes'
        
        return 'tvshows'
    
    def __getThumbnailURL(self, guid):
        # if 'studio-' == guid[:7]:
        #     return 'http://massengeschmack.tv/img/mag/studio' + guid[7:] + '.jpg'
        
        # return 'http://massengeschmack.tv/img/mgfeedlogo.jpg'
        return 'http://dl.massengeschmack.tv/img/mag/' + guid + '.jpg'
    
    def __getBaseList(self):
        return [
            # All
            ListItem(
                self.id,
                ADDON.getLocalizedString(30300),
                resources.lib.assembleListURL(self.module, 'all'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '_20140818.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30300),
                    'Plot': ADDON.getLocalizedString(30361)
                }
            ),
            # Das Studio
            ListItem(
                self.id,
                ADDON.getLocalizedString(30360),
                resources.lib.assembleListURL(self.module, 'studio'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + 'studio.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30360),
                    'Plot': ADDON.getLocalizedString(30362)
                }
            ),
            # Massengeschmack Direkt
            ListItem(
                self.id,
                ADDON.getLocalizedString(30365),
                resources.lib.assembleListURL(self.module, 'direkt'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + 'direkt.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30365),
                    'Plot': ADDON.getLocalizedString(30366)
                }
            ),
            # Massengeschmack Internal
            ListItem(
                self.id,
                ADDON.getLocalizedString(30363),
                resources.lib.assembleListURL(self.module, 'internal'),
                ADDON_BASE_PATH + '/resources/media/banner-' + self.module + '_20140818.png',
                ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                {
                    'Title': ADDON.getLocalizedString(30363),
                    'Plot': ADDON.getLocalizedString(30364)
                }
            )
        ]

class PaschTVDataSource(DataSource):
    id           = 4
    module       = 'paschtv'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30240),
        'Director' :'Holger Kreymeier,',
        'Genre'    : ADDON.getLocalizedString(30241),
        'Premiered':'10.10.2013',
        'Country'  : ADDON.getLocalizedString(30242),
        'Plot'     : ADDON.getLocalizedString(30243)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30241),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30242),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        baseURL = 'http://dl.massengeschmack.tv/img/mag/'
        
        if 6 > int(guid[5:]):
            baseURL = 'http://massengeschmack.tv/img/mag/'
        
        if 'pasch2' == guid:
            guid = 'paschtv2'
        
        return baseURL + guid + '.jpg'

class NetzpredigerDataSource(DataSource):
    id           = 5
    module       = 'netzprediger'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30250),
        'Director' :'Holger Kreymeier',
        'Genre'    : ADDON.getLocalizedString(30251),
        'Premiered':'10.10.2013',
        'Country'  : ADDON.getLocalizedString(30252),
        'Plot'     : ADDON.getLocalizedString(30253)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30251),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30252),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '_20140310.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        # if old Netzprediger episode
        if 6 > int(guid[13:]):
            name    = guid[:12]
            episode = guid[13:]
            return 'http://massengeschmack.tv/img/mag/' + name + episode + '.jpg'
        
        return 'http://dl.massengeschmack.tv/img/mag/' + guid + '.jpg'


class AsynchronDataSource(DataSource):
    id           = 6
    module       = 'asynchron'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30260),
        'Director' :'Evgenij Cernov',
        'Genre'    : ADDON.getLocalizedString(30261),
        'Premiered':'26.02.2014',
        'Country'  : ADDON.getLocalizedString(30262),
        'Plot'     : ADDON.getLocalizedString(30263)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30261),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30262),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        if '1' == guid[10:]:
            return 'http://dl.massengeschmack.tv/img/screens/' + guid + '.jpg'
        return 'http://dl.massengeschmack.tv/img/mag/' + guid + '.jpg'

class TonangeberDataSource(DataSource):
    id           = 7
    module       = 'tonangeber'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30264),
        'Director' : 'Nils Beckmann, Holger Kreymeier',
        'Genre'    : ADDON.getLocalizedString(30265),
        'Premiered': '17.06.2014',
        'Country'  : ADDON.getLocalizedString(30266),
        'Plot'     : ADDON.getLocalizedString(30267)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30265),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30266),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        return 'http://dl.massengeschmack.tv/img/mag/' + guid + '.jpg'

class HoaxillaTVDataSource(DataSource):
    id           = 8
    module       = 'hoaxillatv'
    showMetaData = {
        'Title'    : ADDON.getLocalizedString(30400),
        'Director' : 'Alexa Waschkau, Alexander Waschkau, Holger Kreymeier',
        'Genre'    : ADDON.getLocalizedString(30401),
        'Premiered': '17.06.2014',
        'Country'  : ADDON.getLocalizedString(30402),
        'Plot'     : ADDON.getLocalizedString(30403)
    }
    
    def __init__(self):
        self.__urls = {
            'hd' : {
                'all' : DataSource._buildFeedURL(self, [1], 'hd'),
            },
            'mobile' : {
                'all' : DataSource._buildFeedURL(self, [1], 'mobile'),
            },
            'audio' : {
                'all' : DataSource._buildFeedURL(self, [1], 'audio'),
            }
        }
    
    def getListItems(self):
        audioOnly = ADDON.getSetting('content.audioOnly')
        
        quality = None
        if 'true' == audioOnly:
            quality = 'audio'
        else:
            if 0 == int(ADDON.getSetting('content.quality')):
                quality = 'hd'
            else:
                quality = 'mobile'
        
        data      = resources.lib.parseRSSFeed(self.__urls[quality]['all'], True)
        listItems = []
        
        for i in data:
            iconimage = i['thumbUrl']
            date      = resources.lib.parseUTCDateString(i['pubdate']).strftime('%d.%m.%Y')
            metaData  = {
                'Title'     : i['title'],
                'Genre'     : ADDON.getLocalizedString(30401),
                'Date'      : date,
                'Premiered' : date,
                'Country'   : ADDON.getLocalizedString(30402),
                'Plot'      : i['description'],
                'Duration'  : int(i['duration']) / 60
            }
            streamInfo = {
                'duration' : i['duration']
            }
            
            listItems.append(
                ListItem(
                    self.id,
                    i['title'],
                    resources.lib.assemblePlayURL(i['url'], i['title'], iconimage, metaData, streamInfo),
                    iconimage,
                    ADDON_BASE_PATH + '/resources/media/fanart-' + self.module + '.jpg',
                    metaData,
                    streamInfo,
                    False
                )
            )
        
        return listItems
    
    def getContentMode(self):
        return 'episodes'
    
    def __getThumbnailURL(self, guid):
        return 'http://dl.massengeschmack.tv/img/mag/' + guid + '.jpg'

def createDataSource(module=''):
    """
    Create a data source object based on the magazine name.
    If left empty, an overview data source will be generated.
    
    @type module: str
    @keyword module: the magazine name (fktv, ptv, ps, mgtv, paschtv, netzprediger, asynchron)
    @return: DataSource instance
    """
    if 'live' == module:
        return LiveDataSource()
    elif 'fktv' == module:
        return FKTVDataSource()
    elif 'ptv' == module:
        return PTVDataSource()
    elif 'ps' == module:
        return PSDataSource()
    elif 'mgtv' == module:
        return MGTVDataSource()
    elif 'paschtv' == module:
        return PaschTVDataSource()
    elif 'netzprediger' == module:
        return NetzpredigerDataSource()
    elif 'asynchron' == module:
        return AsynchronDataSource()
    elif 'tonangeber' == module:
        return TonangeberDataSource()
    elif 'hoaxillatv' == module:
        return HoaxillaTVDataSource()
    else:
        return DataSource()
