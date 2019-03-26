# -*- coding: utf-8 -*-
#
# Massengeschmack Kodi add-on
# Copyright (C) 2013-2016 by Janek Bevendorff
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

import json
import os
import glob
from datetime import datetime
import time
import resources.lib
from resources.lib.listing import *


class DataSource(object):
    """
    Generic DataSource class.
    This class can either be subclassed or bootstrapped with a JSON definition
    for creating a custom DataSource.
    """

    class Submodule:
        """
        DataSource submodule DTO.
        """
        def __init__(self):
            self.name = None    # type: str
            """Name of the submodule."""

            self.ids = []   # type: list of int
            """Feed IDs contained in this submodule."""

            self.feedName = None    # type: str
            """Custom feed name (overrides automatically generated name from feed IDs)"""

            self.moduleMetaData = {}    # type: dict
            """Metadata for the submodule (int values can be used to reference i18n strings)."""

            self.pagination = True  # type: bool
            """Whether to enable pagination."""

            self.isActive = True    # type: bool
            """Whether this submodule is currently active."""

        def __eq__(self, other):
            if type(other) is str:
                return self.name == other
            return self.name == other.name

        def __hash__(self):
            return self.name.__hash__()

        def getModuleTitle(self):
            """
            Get display title for current submodule.

            @rtype: str
            @return: submodule title to be displayed in listings
            """
            title = self.moduleMetaData.get('title', ADDON.getLocalizedString(30198))
            if not self.isActive:
                # rstrip() for removing workaround white-space for 16 char min-length issue
                # see <http://trac.kodi.tv/ticket/16599>
                title = title.rstrip() + ' ' + ADDON.getLocalizedString(30199)
            return title

    def __init__(self):
        self.id = None  # type: int
        """Numeric ID of the show."""

        self.moduleName = None  # type: str
        """Internal module name."""

        self.sortOrder = 0  # type: int
        """Show listing sort order."""

        self.showStreamInfo = {}    # type: dict
        """Global meta data for the show  (int values can be used to reference i18n strings)."""

        self.availableQualities = []    # type: list
        """Available quality settings for this DataSource."""

        self.bannerPath = None  # type: str
        """Path to banner image file."""

        self.fanartPath = None  # type: str
        """Path to fanart image file."""

        self.isActive = True    # type: bool
        """Whether the show is currently active."""

        self.submodules = []    # type: list of DataSource.Submodule
        """Available submodules."""

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id.__hash__()

    def __getitem__(self, item):
        return self.submodules[item]

    @classmethod
    def bootstrap(cls, jsonFile):
        """
        Bootstrap new DataSource instance from given JSON definition file.

        @type jsonFile: str
        @param jsonFile: path to JSON bootstrap file
        @rtype: DataSource
        @return bootstrapped DataSource
        """

        def __localizeDict(d):
            for k in d:
                d[k] = ADDON.getLocalizedString(d[k]) if type(d[k]) is int else d[k]
            return d

        with open(jsonFile, 'r') as f:
            jd = json.load(f, 'utf-8')

        ds            = cls()
        ds.moduleName = os.path.basename(jsonFile).replace('.json', '')
        ds.id         = jd.get('id', ds.id)
        ds.sortOrder  = jd.get('order', ds.sortOrder)
        ds.isActive   = jd.get('active', ds.isActive)

        ds.availableQualities.extend(jd.get('qualities', []))
        ds.showStreamInfo.update(__localizeDict(jd.get('metadata', {})))

        if 'banner' in jd:
            ds.bannerPath = os.path.join(ADDON_BASE_PATH, 'resources', 'media', jd['banner'])
        else:
            ds.bannerPath = HTTP_BASE_URI + 'img/header/mg_banner_' + str(ds.id) + '.jpg?' + time.strftime('%Y%m%d')

        if 'fanart' in jd:
            ds.fanartPath = os.path.join(ADDON_BASE_PATH, 'resources', 'media', jd['fanart'])

        sm = jd.get('submodules', [])
        for i in sm:
            s = cls.Submodule()
            s.name       = i.get('name', s.name)
            s.feedName   = i.get('feed_name', s.feedName)
            s.pagination = i.get('pagination', s.pagination)
            s.isActive   = i.get('active', s.isActive)
            s.ids.extend(i.get('ids', []))
            s.moduleMetaData.update(__localizeDict(i.get('metadata', {})))
            ds.submodules.append(s)

        return ds

    def getQuality(self):
        """
        Get currently selected quality setting.

        @rtype: str
        @return: quality identifier (best, hd, mobile, audio), None if no quality settings available
        """
        audioOnly = ADDON.getSetting('content.audioOnly')

        quality = None
        if 'true' == audioOnly and 'audio' in self.availableQualities:
            quality = 'audio'
        else:
            qualitySetting = int(ADDON.getSetting('content.quality'))
            if 0 == qualitySetting:
                quality = 'best'
            elif 1 == qualitySetting:
                quality = 'hd'
            elif 2 == qualitySetting:
                quality = 'mobile'

            if quality not in self.availableQualities:
                quality = self.availableQualities[0] if self.availableQualities else None

        return quality

    def getCurrentSubmoduleName(self):
        """
        Get the name of the current submodule.

        @rtype: str
        @return: submodule name or None if we're not in a submodule
        """
        submodule = None
        if 'submodule' in ADDON_ARGS and ADDON_ARGS['submodule'] in self.submodules:
            submodule = ADDON_ARGS['submodule']
        return submodule

    def getContentMode(self):
        """
        Get the content mode for the listing content.

        Content mode is usually either 'tvshows' or 'episodes', but can
        also be any other valid value for xbmcplugin.setContent().

        @rtype: bool
        @return content mode
        """
        return 'episodes'

    def getViewMode(self):
        """
        Get the Kodi view mode for displaying the listing.
        This is one of the numeric view mode IDs for the
        Container.SetViewMode(int) builtin.

        A list of IDs (XML files starting with View_) can be found at
        https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary/xml
        """
        # InfoWall
        return 54

    def getShowTitle(self):
        """
        Get display title for current show.

        @rtype: str
        @return: show title to be displayed in listings
        """
        title = self.showStreamInfo.get('title', ADDON.getLocalizedString(30198))
        if not self.isActive:
            # rstrip() for removing workaround white-space for 16 char min-length issue
            # see <http://trac.kodi.tv/ticket/16599>
            title = title.rstrip() + ' ' + ADDON.getLocalizedString(30199)
        return title

    def buildFeedURL(self, submodule, quality, page=1):
        """
        Build a feed URL which points to an RSS feed which is filtered by the given IDs.

        This method relies on self.id being set properly in derived classes.

        @type submodule: DataSource.Submodule
        @param submodule: submodule for which to generate the feed URL
        @type quality: str
        @param quality: the movie quality (either 'best', 'hd', 'mobile' or 'audio')
        @type page: int
        @param page: page for pagination
        @rtype: str
        @return feed URL string
        """
        url = HTTP_BASE_FEED_URI + '/'

        if submodule.feedName:
            url += submodule.feedName
        else:
            first = True
            for i in submodule.ids:
                if not first:
                    url += 'x'
                first = False
                url += str(self.id) + '-' + str(i)

        url += '/' + quality + '.xml?page=' + str(page)

        return url

    def hasListItems(self):
        """
        Whether the DataSource intends to return a non-empty ListItem generator when calling L{getListItems}.
        You should check the output of this method before creating a sub-listing that depends on the
        returned ListItems from this DataSource.

        @return: True if getListItems will return a non-empty generator
        """
        return True

    def getListItems(self):
        """
        Return a generator object of L{resources.lib.listing.ListItem} objects for the current data source.

        @rtype: generator of resources.lib.listing.ListItem
        @return: generator object
        """
        submoduleName = self.getCurrentSubmoduleName()

        # show selection list if there are several submodules and we're not inside one already
        if len(self.submodules) > 1 and not submoduleName:
            for i in self.__getBaseList():
                yield i
            return

        # if there is only one submodule, don't show a selection list
        if len(self.submodules) == 1 and not submoduleName:
            submoduleName = self.submodules[0].name

        # shouldn't happen
        if submoduleName is None:
            raise RuntimeError("No valid submodule given.")

        currentPage = int(ADDON_ARGS['page']) if 'page' in ADDON_ARGS else 1
        submodule   = next(s for s in self.submodules if s.name == submoduleName)
        data        = resources.lib.parseRSSFeed(self.buildFeedURL(submodule, self.getQuality(), currentPage), True)

        for i in data:
            streamInfo = self.showStreamInfo
            streamInfo.update({
                'title'     : i['title'],
                'premiered' : resources.lib.parseUTCDateString(i['pubdate']).strftime('%Y-%m-%d'),
                'plot'      : i['description'],
                'duration'  : i['duration'],
                'mediatype' : 'episode'
            })
            art = {
                'thumb': i["thumbUrl"]
            }

            yield ListItem(
                self.id,
                i['title'],
                resources.lib.assemblePlayURL(i['url'], i['title'], art=art, streamInfo=streamInfo),
                i["thumbUrl"],
                self.fanartPath,
                streamInfo,
                False
            )

        # forward pagination
        if submodule.pagination and len(data) >= 10:
            yield ListItem(
                self.id,
                ADDON.getLocalizedString(30140),
                resources.lib.assembleListURL(self.moduleName, submodule.name, page=currentPage + 1),
                self.bannerPath,
                self.fanartPath
            )

    def __getBaseList(self):
        # create generator object of submodules with inactive submodules coming last
        for active in (True, False):
            for i in (s for s in self.submodules if s.isActive == active):
                streamInfo = self.showStreamInfo
                streamInfo.update({
                    'title': '',
                    'plot': ''
                })
                streamInfo.update(i.moduleMetaData)
                yield ListItem(
                    self.id,
                    i.getModuleTitle(),
                    resources.lib.assembleListURL(self.moduleName, i.name),
                    self.bannerPath,
                    self.fanartPath,
                    streamInfo
                )


class DataSourceRegistry:
    """
    Decorator for registering custom DataSource classes.
    Any non-bootstrapped DataSource that shall be hooked into the DataSource list, needs to be decorated.
    The only exception is L{OverviewDataSource} which is always the root DataSource and
    therefore registered implicitly.
    """

    __dataSources = {}

    def __init__(self, moduleName):
        """
        Register class as DataSource. The specified moduleName will be used to automatically instantiate
        DataSources when that submodule is called via KODI URI.

        @type moduleName: str
        @param moduleName: module name to register for
        @return: decorated DataSource
        """
        self.__moduleName = moduleName

    def __call__(self, cls):
        if self.__moduleName not in self.__dataSources:
            self.__dataSources[self.__moduleName] = cls
        return self.__dataSources[self.__moduleName]

    @classmethod
    def getDataSources(cls):
        """
        Return a set of registered DataSource classes.

        @rtype: set of DataSource
        @return all registered DataSources
        """
        return set(cls.__dataSources.values())

    @classmethod
    def getDataSourceByName(cls, moduleName):
        """
        Get DataSource class by registered module name.

        @param moduleName: module name the DataSource was registered for
        @rtype DataSource
        @return: the DataSource class or None if no DataSource is registered under moduleName
        """
        return cls.__dataSources.get(moduleName, None)


class OverviewDataSource(DataSource):
    """
    Overview DataSource for displaying an overview of all registered show DataSources.
    This is the root DataSource that is displayed at top level.
    """

    @classmethod
    def bootstrap(cls, jsonFile):
        raise NotImplementedError

    def getListItems(self):
        dataSources = []

        # add all registered DataSources to the list
        for i in DataSourceRegistry.getDataSources():
            dataSources.append(i())

        # boostrap any remaining DataSources from available bootstrap files
        bootstrapFiles = glob.glob(ADDON_BOOTSTRAP_PATH + '/*.json')
        for i in bootstrapFiles:
            dataSources.append(DataSource.bootstrap(i))

        # sort DataSources as defined in each DataSource's sortOrder property
        dataSources.sort(key=lambda x: x.sortOrder)

        # create generator object of shows with inactive submodules coming last
        for active in (True, False):
            for i in (s for s in dataSources if s.isActive == active):
                yield ListItem(
                    i.id,
                    i.getShowTitle(),
                    resources.lib.assembleListURL(i.moduleName),
                    i.bannerPath,
                    i.fanartPath,
                    i.showStreamInfo
                )

    def getContentMode(self):
        return "tvshows"

    def getViewMode(self):
        # Banner
        return 501


@DataSourceRegistry('live')
class LiveDataSource(DataSource):
    """
    Custom DataSource for LIVE streams.
    """

    def __init__(self):
        super(LiveDataSource, self).__init__()

        self.id           = -9999
        self.moduleName   = 'live'
        self.sortOrder    = 600
        self.showStreamInfo = {
            'title'    : ADDON.getLocalizedString(30270),
            'country'  : ADDON.getLocalizedString(30202),
            'plot'     : ADDON.getLocalizedString(30272)
        }
        self.bannerPath = os.path.join(ADDON_BASE_PATH, 'resources', 'media', 'banner-massengeschmack-20160220.png')
        self.fanartPath = os.path.join(ADDON_BASE_PATH, 'resources', 'media', 'fanart-massengeschmack-20160220.jpg')
        self.isActive   = True

        self.isLive     = False

        # if we're about to play a stream, don't continue with querying data about other streams from the server
        if 'playStream' in ADDON_ARGS:
            info = resources.lib.getLiveStreamInfo(ADDON_ARGS['playStream'])
            resources.lib.playVideoStream(info['url'],
                                          ADDON_ARGS.get('streamName', ''),
                                          json.loads(ADDON_ARGS.get('art', '{}')),
                                          json.loads(ADDON_ARGS.get('streamInfo', '{}')))
            return

        # otherwise continue with regular listing
        self.__shows      = resources.lib.getLiveShows()
        self.__recordings = []
        self.__current    = []
        self.__upcoming   = []

        for i in self.__shows:
            if i['isLive']:
                self.isLive = True
                self.__current.append(i)
            else:
                self.__upcoming.append(i)

        # if there is a show live on air, mark it in the list and move it to the top
        if self.isLive:
            self.sortOrder = -10000
            self.showStreamInfo['title'] = self.showStreamInfo['title'].rstrip() + ' ' + ADDON.getLocalizedString(30278)

    @classmethod
    def bootstrap(cls, jsonFile):
        raise NotImplementedError

    def getContentMode(self):
        return 'episodes'

    def getViewMode(self):
        # InfoWall
        return 54

    def hasListItems(self):
        return 'playStream' not in ADDON_ARGS

    def getListItems(self):
        # don't generate a listing when we're about to play a live stream or recording
        # we should never end here because hasListItems() should be checked before calling this method,
        # but exit method here just in case
        if 'playStream' in ADDON_ARGS:
            return

        # otherwise ask for list of recordings additionally to the already queried live and upcoming streams
        self.__recordings = resources.lib.getLiveShows(True)

        # start building listing
        if self.__current:
            yield ListItem(
                self.id,
                ADDON.getLocalizedString(30273),
                '#',
                self.__getThumbnailURL(0),
                self.fanartPath,
            )

            for i in self.__createShowListing(self.__current, 'live'):
                yield i

        if self.__upcoming:
            yield ListItem(
                self.id,
                ADDON.getLocalizedString(30275),
                '#',
                self.__getThumbnailURL(0),
                self.fanartPath,
            )

            for i in self.__createShowListing(self.__upcoming, 'upcoming'):
                yield i

        if self.__recordings:
            yield ListItem(
                self.id,
                ADDON.getLocalizedString(30281),
                '#',
                self.__getThumbnailURL(0),
                self.fanartPath,
            )

            for i in self.__createShowListing(self.__recordings, 'recording'):
                yield i

    def __createShowListing(self, shows, mode):
        for i in shows:
            iconImage = self.__getThumbnailURL(i['pid'])
            time      = datetime.fromtimestamp(float(i['begin'])).strftime('%d.%m.%Y, %H:%M:%S')
            date      = datetime.fromtimestamp(float(i['begin'])).strftime('%d.%m.%Y')
            name      = i['oneliner']
            plot      = ADDON.getLocalizedString(30277).format(name, time)

            streamName = name
            if mode == 'live':
                # add [ON AIR] if stream is live
                streamName += ' ' + ADDON.getLocalizedString(30278)
                listName = name
            else:
                if mode == 'upcoming':
                    # add "Starts on..."
                    dateString = ADDON.getLocalizedString(30279).format(time)
                else:
                    # add "Recorded on..."
                    dateString = ADDON.getLocalizedString(30292).format(time)
                    streamName += ' ' + ADDON.getLocalizedString(30294)

                listName = '    ' + name + ' -> ' + dateString

            streamInfo  = {
                'title'     : streamName,
                'date'      : date,
                'plot'      : plot
            }

            if mode == 'live' or mode == 'recording':
                listUrl = resources.lib.assembleListURL(self.moduleName, playStream=i['showid'], streamName=streamName,
                                                        art=json.dumps({"thumb": iconImage}),
                                                        streamInfo=json.dumps(streamInfo))
            else:
                # don't create a real list URL for upcoming shows
                listUrl = '#'

            yield ListItem(
                self.id,
                listName,
                listUrl,
                iconImage,
                self.fanartPath,
                streamInfo,
                isFolder=(mode == 'upcoming')
            )

    @staticmethod
    def __getThumbnailURL(id):
        return HTTP_BASE_URI + '/img/logo' + str(id) + '_feed.jpg'


def createDataSource(module=None):
    """
    Create a L{DataSource} object based on the given module name.
    If no module name is given, an overview DataSource will be generated.

    @type module: str
    @keyword module: the magazine name, None or empty string for overview
    @rtype: DataSource
    @return: generated DataSource
    """
    if not module:
        return OverviewDataSource()

    bootstrapFile = ADDON_BOOTSTRAP_PATH + '/' + module + '.json'
    if os.path.isfile(bootstrapFile):
        return DataSource.bootstrap(bootstrapFile)
    else:
        ds = DataSourceRegistry.getDataSourceByName(module)
        if ds is None:
            raise RuntimeError("Invalid module {}".format(module))
        return ds()
