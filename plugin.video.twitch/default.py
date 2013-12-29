# -*- coding: utf-8 -*-
from converter import JsonListItemConverter
from functools import wraps
from twitch import TwitchTV, TwitchVideoResolver, Keys, TwitchException
from xbmcswift2 import Plugin  # @UnresolvedImport
import urllib2, json, sys

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

PLUGIN = Plugin()
CONVERTER = JsonListItemConverter(PLUGIN, LINE_LENGTH)
TWITCHTV = TwitchTV(PLUGIN.log)


def managedTwitchExceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TwitchException as error:
            handleTwitchException(error)
    return wrapper


def handleTwitchException(exception):
    codeTranslations = {TwitchException.NO_STREAM_URL   : 30023,
                        TwitchException.STREAM_OFFLINE  : 30021,
                        TwitchException.HTTP_ERROR      : 30020,
                        TwitchException.JSON_ERROR      : 30027}
    code = exception.code
    title = 30010
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
         'path': PLUGIN.url_for(endpoint='createListOfTeams', index='0')
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
    featuredStreams = TWITCHTV.getFeaturedStream()
    return [CONVERTER.convertStreamToListItem(featuredStream[Keys.STREAM])
            for featuredStream in featuredStreams]


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
    items = [CONVERTER.convertStreamToListItem(stream) for stream
             in TWITCHTV.getGameStreams(gameName, offset, limit)]

    items.append(linkToNextPage('createListForGame', index, gameName=gameName))
    return items


@PLUGIN.route('/createFollowingList/')
@managedTwitchExceptions
def createFollowingList():
    username = getUserName()
    streams = TWITCHTV.getFollowingStreams(username)
    liveStreams = [CONVERTER.convertStreamToListItem(stream) for stream in streams['live']]
    liveStreams.insert(0,{'path': PLUGIN.url_for(endpoint='createFollowingList'), 'icon': u'', 'is_playable': False, 'label': PLUGIN.get_string(30012)})
    liveStreams.append({'path': PLUGIN.url_for(endpoint='createFollowingList'), 'icon': u'', 'is_playable': False, 'label': PLUGIN.get_string(30013)})
    liveStreams.extend([CONVERTER.convertFollowersToListItem(follower) for follower in streams['others']])
    return liveStreams


@PLUGIN.route('/channelVideos/<name>/')
@managedTwitchExceptions
def channelVideos(name):
    items = [
        {'label': 'Past Broadcasts',
         'path': PLUGIN.url_for(endpoint='channelVideosList', name=name, index=0, past='true')
        },
        {'label': 'Video Highlights',
         'path': PLUGIN.url_for(endpoint='channelVideosList', name=name, index=0, past='false')
        }
    ]
    return items
    
    
@PLUGIN.route('/channelVideosList/<name>/<index>/<past>/')
@managedTwitchExceptions
def channelVideosList(name,index,past):
    index = int(index)
    offset = index * 8
    videos = TWITCHTV.getFollowerVideos(name,offset,past)
    items = [CONVERTER.convertVideoListToListItem(video) for video in videos[Keys.VIDEOS]]
    if videos[Keys.TOTAL] > (offset + 8):
        items.append(linkToNextPage('channelVideosList', index, name=name, past=past))
    return items
    
    
@PLUGIN.route('/playVideo/<id>/')
@managedTwitchExceptions
def playVideo(id):
    
    playList = TWITCHTV.getVideoChunksPlaylist(id)
    
    # Doesn't fullscreen video, might be because of xbmcswift
    #xbmc.Player().play(playlist) 
    
    try:
        # Gotta wrap this in a try/except, xbmcswift causes an error when passing a xbmc.PlayList()
        # but still plays the playlist properly
        PLUGIN.set_resolved_url(playlist)
    except:
        pass
    
    
@PLUGIN.route('/search/')
@managedTwitchExceptions
def search():
    query = PLUGIN.keyboard('', PLUGIN.get_string(30007))
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

    items = [CONVERTER.convertStreamToListItem(stream) for stream in streams]
    items.append(linkToNextPage('searchresults', index, query=query))
    return items


@PLUGIN.route('/showSettings/')
def showSettings():
    #there is probably a better way to do this
    PLUGIN.open_settings()
    
    
@PLUGIN.route('/playLive/<name>/')
@managedTwitchExceptions
def playLive(name):
    
    #Get Required Quality From Settings
    videoQuality = getVideoQuality()
    
    plpath = xbmc.translatePath('special://temp') + 'hlsplaylist.m3u8'
    resolver = TwitchVideoResolver(PLUGIN.log)
    resolver.saveHLSToPlaylist(name,videoQuality,plpath)
    #Play Custom Playlist
    xbmc.Player().play(plpath)
    PLUGIN.set_resolved_url(plpath)


@PLUGIN.route('/createListOfTeams/<index>/')
@managedTwitchExceptions
def createListOfTeams(index):
    index = int(index)
    teams = TWITCHTV.getTeams(index)
    items = [CONVERTER.convertTeamToListItem(item)for item in teams]
    if len(teams) == 25:
        items.append(linkToNextPage('createListOfTeams', index))
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
    qualities = {'0': 0, '1': 1, '2': 2, '3': 3}
    return qualities.get(chosenQuality, sys.maxint)


def linkToNextPage(target, currentIndex, **kwargs):
    return {'label': PLUGIN.get_string(30011),
            'path': PLUGIN.url_for(target, index=str(currentIndex + 1), **kwargs)
            }

if __name__ == '__main__':
    PLUGIN.run()
