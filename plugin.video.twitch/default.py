#!/usr/bin/python
# -*- coding: utf-8 -*-
from converter import JsonListItemConverter
from functools import wraps
from twitch import TwitchTV, TwitchVideoResolver, Keys, TwitchException
from xbmcswift2 import Plugin  # @UnresolvedImport
import sys

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

PLUGIN = Plugin()
CONVERTER = JsonListItemConverter(PLUGIN, LINE_LENGTH)
TWITCHTV = TwitchTV()


def managedTwitchExceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TwitchException as error:
            handleTwitchException(error)
    return wrapper


def handleTwitchException(exception):
    codeTranslations = {TwitchException.NO_STREAM_URL   : 32004,
                        TwitchException.STREAM_OFFLINE  : 32002,
                        TwitchException.HTTP_ERROR      : 32001,
                        TwitchException.JSON_ERROR      : 32008}
    code = exception.code
    title = 31000
    msg = codeTranslations[code]
    PLUGIN.notify(PLUGIN.get_string(title), PLUGIN.get_string(msg))


@PLUGIN.route('/')
def createMainListing():
    items = [
        {'label': PLUGIN.get_string(30005),
         'path': PLUGIN.url_for(endpoint='createListOfFeaturedStreams')
         },
        {'label': PLUGIN.get_string(30001),
         'path': PLUGIN.url_for(endpoint='createListOfGames', index='0')
         },
        {'label': PLUGIN.get_string(30002),
         'path': PLUGIN.url_for(endpoint='createFollowingList')
         },
        {'label': PLUGIN.get_string(30006),
         'path': PLUGIN.url_for(endpoint='createListOfTeams')
         },
        {'label': PLUGIN.get_string(30003),
         'path': PLUGIN.url_for(endpoint='search')
         },
        {'label': PLUGIN.get_string(30004),
         'path': PLUGIN.url_for(endpoint='showSettings')
         }
    ]
    return items


@PLUGIN.route('/createListOfFeaturedStreams/')
@managedTwitchExceptions
def createListOfFeaturedStreams():
    streams = TWITCHTV.getFeaturedStream()
    return [CONVERTER.convertChannelToListItem(element[Keys.STREAM][Keys.CHANNEL])
            for element in streams]


@PLUGIN.route('/createListOfGames/<index>/')
@managedTwitchExceptions
def createListOfGames(index):
    index, offset, limit = calculatePaginationValues(index)

    games = TWITCHTV.getGames(offset, limit)
    items = [CONVERTER.convertGameToListItem(element[Keys.GAME]) for element in games]

    items.append(linkToNextPage('createListOfGames', index))
    return items


@PLUGIN.route('/createListForGame/<gameName>/<index>/')
@managedTwitchExceptions
def createListForGame(gameName, index):
    index, offset, limit = calculatePaginationValues(index)
    items = [CONVERTER.convertChannelToListItem(item[Keys.CHANNEL])for item
             in TWITCHTV.getGameStreams(gameName, offset, limit)]

    items.append(linkToNextPage('createListForGame', index, gameName=gameName))
    return items


@PLUGIN.route('/createFollowingList/')
@managedTwitchExceptions
def createFollowingList():
    username = getUserName()
    streams = TWITCHTV.getFollowingStreams(username)
    return [CONVERTER.convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]


@PLUGIN.route('/search/')
@managedTwitchExceptions
def search():
    query = PLUGIN.keyboard('', PLUGIN.get_string(30101))
    if query:
        target = PLUGIN.url_for(endpoint='searchresults', query=query, index='0')
    else:
        target = PLUGIN.url_for(endpoint='createMainListing')
    PLUGIN.redirect(target)


@PLUGIN.route('/searchresults/<query>/<index>/')
@managedTwitchExceptions
def searchresults(query, index='0'):
    index, offset, limit = calculatePaginationValues(index)
    streams = TWITCHTV.searchStreams(query, offset, limit)

    items = [CONVERTER.convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]
    items.append(linkToNextPage('searchresults', index, query=query))
    return items


@PLUGIN.route('/showSettings/')
def showSettings():
    #there is probably a better way to do this
    PLUGIN.open_settings()


@PLUGIN.route('/playLive/<name>/')
@managedTwitchExceptions
def playLive(name):
    videoQuality = getVideoQuality()
    resolver = TwitchVideoResolver()
    rtmpUrl = resolver.getRTMPUrl(name, videoQuality)
    PLUGIN.set_resolved_url(rtmpUrl)


@PLUGIN.route('/createListOfTeams/')
@managedTwitchExceptions
def createListOfTeams():
    items = [CONVERTER.convertTeamToListItem(item)for item in TWITCHTV.getTeams()]
    return items


@PLUGIN.route('/createListOfTeamStreams/<team>/')
@managedTwitchExceptions
def createListOfTeamStreams(team):
    return [CONVERTER.convertTeamChannelToListItem(channel[Keys.CHANNEL])
            for channel in TWITCHTV.getTeamStreams(team)]


def calculatePaginationValues(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * limit
    return  index, offset, limit


def getUserName():
    username = PLUGIN.get_setting('username', unicode).lower()
    if not username:
        PLUGIN.open_settings()
        username = PLUGIN.get_setting('username', unicode).lower()
    return username


def getVideoQuality():
    chosenQuality = PLUGIN.get_setting('video', unicode)
    qualities = {'0': sys.maxint, '1': 720, '2': 480, '3': 360}
    return qualities.get(chosenQuality, sys.maxint)


def linkToNextPage(target, currentIndex, **kwargs):
    return {'label': PLUGIN.get_string(31001),
            'path': PLUGIN.url_for(target, index=str(currentIndex + 1), **kwargs)
            }

if __name__ == '__main__':
    PLUGIN.run()
