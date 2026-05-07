#!/usr/bin/python

########################

import xbmc
import xbmcgui

from resources.lib.json_map import *
from resources.lib.helper import *

########################


def _use_infotag_api():
    """Check if Kodi version supports InfoTagVideo (Kodi 20+/Nexus+)."""
    try:
        # getInfoTagVideo exists from Kodi 20 (Nexus) onwards
        test = xbmcgui.ListItem(offscreen=True)
        tag = test.getVideoInfoTag()
        return hasattr(tag, 'setMediaType')
    except Exception:
        return False


USE_INFOTAG = _use_infotag_api()


def add_items(li,json_query,type,searchstring=None):
    for item in json_query:
        if type == 'movie':
            handle_movies(li, item, searchstring)
        elif type ==  'tvshow':
            handle_tvshows(li, item, searchstring)
        elif type == 'season':
            handle_seasons(li, item)
        elif type == 'episode':
            handle_episodes(li, item)
        elif type == 'cast':
            handle_cast(li, item)


def handle_movies(li,item,searchstring=None):
    genre = item.get('genre', '')
    studio = item.get('studio', '')
    country = item.get('country', '')
    director = item.get('director', '')
    writer = item.get('writer', '')

    li_item = xbmcgui.ListItem(item['title'], offscreen=True)

    if USE_INFOTAG:
        tag = li_item.getVideoInfoTag()
        tag.setMediaType('movie')
        tag.setTitle(item['title'])
        tag.setOriginalTitle(item['originaltitle'])
        tag.setSortTitle(item['sorttitle'])
        tag.setYear(item['year'])
        tag.setGenres(genre if isinstance(genre, list) else [genre])
        tag.setStudios(studio if isinstance(studio, list) else [studio])
        tag.setCountries(country if isinstance(country, list) else [country])
        tag.setDirectors(director if isinstance(director, list) else [director])
        tag.setWriters(writer if isinstance(writer, list) else [writer])
        tag.setPlot(item['plot'])
        tag.setPlotOutline(item['plotoutline'])
        tag.setDbId(item['movieid'])
        tag.setIMDBNumber(item['imdbnumber'])
        tag.setTagLine(item['tagline'])
        tag.setTags(item['tag'])
        tag.setRating(float(item['rating']))
        tag.setUserRating(int(item['userrating']))
        tag.setVotes(int(item['votes']))
        tag.setMpaa(item['mpaa'])
        tag.setLastPlayed(item['lastplayed'])
        tag.setTrailer(item['trailer'])
        tag.setDateAdded(item['dateadded'])
        tag.setPremiered(item['premiered'])
        tag.setPath(item['file'])
        tag.setPlaycount(item['playcount'])
        tag.setSet(item['set'])
        tag.setSetId(item['setid'])
        tag.setTop250(item['top250'])

        if 'cast' in item:
            actors = []
            for castmember in item['cast']:
                actor = xbmc.Actor(castmember['name'], castmember.get('role', ''), castmember.get('order', 0), castmember.get('thumbnail', ''))
                actors.append(actor)
            tag.setCast(actors)

        _set_ratings_infotag(tag, item['ratings'])

        # Stream details
        hasVideo = False
        for key, value in iter(list(item['streamdetails'].items())):
            for stream in value:
                if 'video' in key:
                    hasVideo = True
                    tag.addVideoStream(xbmc.VideoStreamDetail(
                        width=stream.get('width', 0),
                        height=stream.get('height', 0),
                        codec=stream.get('codec', ''),
                        duration=stream.get('duration', 0)
                    ))
                elif 'audio' in key:
                    tag.addAudioStream(xbmc.AudioStreamDetail(
                        channels=stream.get('channels', 0),
                        codec=stream.get('codec', ''),
                        language=stream.get('language', '')
                    ))
                elif 'subtitle' in key:
                    tag.addSubtitleStream(xbmc.SubtitleStreamDetail(
                        language=stream.get('language', '')
                    ))

        if not hasVideo:
            tag.addVideoStream(xbmc.VideoStreamDetail(duration=item['runtime']))

    else:
        # Legacy path for Kodi < 20
        li_item.setInfo(type='Video', infoLabels={'title': item['title'],
                                                  'originaltitle': item['originaltitle'],
                                                  'sorttitle': item['sorttitle'],
                                                  'year': item['year'],
                                                  'genre': get_joined_items(genre),
                                                  'studio': get_joined_items(studio),
                                                  'country': get_joined_items(country),
                                                  'director': get_joined_items(director),
                                                  'writer': get_joined_items(writer),
                                                  'plot': item['plot'],
                                                  'plotoutline': item['plotoutline'],
                                                  'dbid': item['movieid'],
                                                  'imdbnumber': item['imdbnumber'],
                                                  'tagline': item['tagline'],
                                                  'tag': item['tag'],
                                                  'rating': str(float(item['rating'])),
                                                  'userrating': str(float(item['userrating'])),
                                                  'votes': item['votes'],
                                                  'mpaa': item['mpaa'],
                                                  'lastplayed': item['lastplayed'],
                                                  'mediatype': 'movie',
                                                  'trailer': item['trailer'],
                                                  'dateadded': item['dateadded'],
                                                  'premiered': item['premiered'],
                                                  'path': item['file'],
                                                  'playcount': item['playcount'],
                                                  'set': item['set'],
                                                  'setid': item['setid'],
                                                  'top250': item['top250']
                                                  })

        if 'cast' in item:
            li_item.setCast(item['cast'])

        _set_ratings_legacy(li_item, item['ratings'])

        hasVideo = False
        for key, value in iter(list(item['streamdetails'].items())):
            for stream in value:
                if 'video' in key:
                    hasVideo = True
                li_item.addStreamInfo(key, stream)

        if not hasVideo:
            stream = {'duration': item['runtime']}
            li_item.addStreamInfo('video', stream)

    if 'cast' in item:
        cast_actors = _get_cast(item['cast'])
        _set_unique_properties(li_item,cast_actors[0],'cast')

    _set_unique_properties(li_item,genre,'genre')
    _set_unique_properties(li_item,studio,'studio')
    _set_unique_properties(li_item,country,'country')
    _set_unique_properties(li_item,director,'director')
    _set_unique_properties(li_item,writer,'writer')

    li_item.getVideoInfoTag().setResumePoint(item['resume']['position'], item['resume']['total'])

    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultVideo.png'})

    if searchstring:
        li_item.setProperty('searchstring', searchstring)

    li.append((item['file'], li_item, False))


def handle_tvshows(li,item,searchstring=None):
    genre = item.get('genre', '')
    studio = item.get('studio', '')
    dbid = item['tvshowid']
    season = item['season']
    episode = item['episode']
    watchedepisodes = item['watchedepisodes']
    unwatchedepisodes = get_unwatched(episode,watchedepisodes)

    if not condition('Window.IsVisible(movieinformation)'):
        folder = True
        item['file'] = 'videodb://tvshows/titles/%s/' % dbid
    else:
        folder = False
        item['file'] = 'videodb://tvshows/titles/%s/' % dbid

    li_item = xbmcgui.ListItem(item['title'], offscreen=True)

    if USE_INFOTAG:
        tag = li_item.getVideoInfoTag()
        tag.setMediaType('tvshow')
        tag.setTitle(item['title'])
        tag.setYear(item['year'])
        tag.setTvShowTitle(item['title'])
        tag.setSortTitle(item['sorttitle'])
        tag.setOriginalTitle(item['originaltitle'])
        tag.setGenres(genre if isinstance(genre, list) else [genre])
        tag.setStudios(studio if isinstance(studio, list) else [studio])
        tag.setPlot(item['plot'])
        tag.setRating(float(item['rating']))
        tag.setUserRating(int(item['userrating']))
        tag.setVotes(int(item['votes']))
        tag.setPremiered(item['premiered'])
        tag.setMpaa(item['mpaa'])
        tag.setTags(item['tag'])
        tag.setDbId(dbid)
        tag.setSeason(season)
        tag.setEpisode(episode)
        tag.setIMDBNumber(item['imdbnumber'])
        tag.setLastPlayed(item['lastplayed'])
        tag.setPath(item['file'])
        tag.setDuration(item['runtime'])
        tag.setDateAdded(item['dateadded'])
        tag.setPlaycount(item['playcount'])

        if 'cast' in item:
            actors = []
            for castmember in item['cast']:
                actor = xbmc.Actor(castmember['name'], castmember.get('role', ''), castmember.get('order', 0), castmember.get('thumbnail', ''))
                actors.append(actor)
            tag.setCast(actors)

        _set_ratings_infotag(tag, item['ratings'])

    else:
        li_item.setInfo(type='Video', infoLabels={'title': item['title'],
                                                  'year': item['year'],
                                                  'tvshowtitle': item['title'],
                                                  'sorttitle': item['sorttitle'],
                                                  'originaltitle': item['originaltitle'],
                                                  'genre': get_joined_items(genre),
                                                  'studio': get_joined_items(studio),
                                                  'plot': item['plot'],
                                                  'rating': str(float(item['rating'])),
                                                  'userrating': str(float(item['userrating'])),
                                                  'votes': item['votes'],
                                                  'premiered': item['premiered'],
                                                  'mpaa': item['mpaa'],
                                                  'tag': item['tag'],
                                                  'mediatype': 'tvshow',
                                                  'dbid': dbid,
                                                  'season': season,
                                                  'episode': episode,
                                                  'imdbnumber': item['imdbnumber'],
                                                  'lastplayed': item['lastplayed'],
                                                  'path': item['file'],
                                                  'duration': item['runtime'],
                                                  'dateadded': item['dateadded'],
                                                  'playcount': item['playcount']
                                                  })

        if 'cast' in item:
            li_item.setCast(item['cast'])

        _set_ratings_legacy(li_item, item['ratings'])

    if 'cast' in item:
        cast_actors = _get_cast(item['cast'])
        _set_unique_properties(li_item,cast_actors[0],'cast')

    _set_unique_properties(li_item,genre,'genre')
    _set_unique_properties(li_item,studio,'studio')

    li_item.setProperty('totalseasons', str(season))
    li_item.setProperty('totalepisodes', str(episode))
    li_item.setProperty('watchedepisodes', str(watchedepisodes))
    li_item.setProperty('unwatchedepisodes', str(unwatchedepisodes))

    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultVideo.png'})

    if searchstring:
        li_item.setProperty('searchstring', searchstring)

    li.append((item['file'], li_item, folder))


def handle_seasons(li,item):
    tvshowdbid = item['tvshowid']
    season = item['season']
    episode = item['episode']
    watchedepisodes = item['watchedepisodes']
    unwatchedepisodes = get_unwatched(episode,watchedepisodes)

    if season == 0:
        title = '%s' % (xbmc.getLocalizedString(20381))
        special = 'true'
    else:
        title = '%s %s' % (xbmc.getLocalizedString(20373), season)
        special = 'false'

    if not condition('Window.IsVisible(movieinformation)'):
        folder = True
        file = 'videodb://tvshows/titles/%s/%s/' % (tvshowdbid, season)
    else:
        folder = False
        file = 'videodb://tvshows/titles/%s/%s/' % (tvshowdbid, season)

    li_item = xbmcgui.ListItem(title, offscreen=True)

    if USE_INFOTAG:
        tag = li_item.getVideoInfoTag()
        tag.setMediaType('season')
        tag.setTitle(title)
        tag.setSeason(season)
        tag.setEpisode(episode)
        tag.setTvShowTitle(item['showtitle'])
        tag.setPlaycount(item['playcount'])
        tag.setDbId(item['seasonid'])
    else:
        li_item.setInfo(type='Video', infoLabels={'title': title,
                                                  'season': season,
                                                  'episode': episode,
                                                  'tvshowtitle': item['showtitle'],
                                                  'playcount': item['playcount'],
                                                  'mediatype': 'season',
                                                  'dbid': item['seasonid']
                                                  })

    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultVideo.png',
                    'fanart': item['art'].get('tvshow.fanart', '')
                    })

    li_item.setProperty('watchedepisodes', str(watchedepisodes))
    li_item.setProperty('unwatchedepisodes', str(unwatchedepisodes))
    li_item.setProperty('isspecial', special)
    li_item.setProperty('season_label', item.get('label', ''))

    li.append((file, li_item, folder))


def handle_episodes(li,item):
    director = item.get('director', '')
    writer = item.get('writer', '')

    if item['episode'] < 10:
      label = '0%s. %s' % (item['episode'], item['title'])
    else:
      label = '%s. %s' % (item['episode'], item['title'])

    if item['season'] == '0':
      label = 'S' + label
    else:
      label = '%sx%s' % (item['season'], label)

    li_item = xbmcgui.ListItem(label, offscreen=True)

    if USE_INFOTAG:
        tag = li_item.getVideoInfoTag()
        tag.setMediaType('episode')
        tag.setTitle(item['title'])
        tag.setEpisode(item['episode'])
        tag.setSeason(int(item['season']))
        tag.setPremiered(item['firstaired'])
        tag.setDbId(item['episodeid'])
        tag.setPlot(item['plot'])
        tag.setTvShowTitle(item['showtitle'])
        tag.setOriginalTitle(item['originaltitle'])
        tag.setLastPlayed(item['lastplayed'])
        tag.setRating(float(item['rating']))
        tag.setUserRating(int(item['userrating']))
        tag.setVotes(int(item['votes']))
        tag.setPlaycount(item['playcount'])
        tag.setDirectors(director if isinstance(director, list) else [director])
        tag.setWriters(writer if isinstance(writer, list) else [writer])
        tag.setPath(item['file'])
        tag.setDateAdded(item['dateadded'])

        if 'cast' in item:
            actors = []
            for castmember in item['cast']:
                actor = xbmc.Actor(castmember['name'], castmember.get('role', ''), castmember.get('order', 0), castmember.get('thumbnail', ''))
                actors.append(actor)
            tag.setCast(actors)

        _set_ratings_infotag(tag, item['ratings'])

        # Stream details
        hasVideo = False
        for key, value in iter(list(item['streamdetails'].items())):
            for stream in value:
                if 'video' in key:
                    hasVideo = True
                    tag.addVideoStream(xbmc.VideoStreamDetail(
                        width=stream.get('width', 0),
                        height=stream.get('height', 0),
                        codec=stream.get('codec', ''),
                        duration=stream.get('duration', 0)
                    ))
                elif 'audio' in key:
                    tag.addAudioStream(xbmc.AudioStreamDetail(
                        channels=stream.get('channels', 0),
                        codec=stream.get('codec', ''),
                        language=stream.get('language', '')
                    ))
                elif 'subtitle' in key:
                    tag.addSubtitleStream(xbmc.SubtitleStreamDetail(
                        language=stream.get('language', '')
                    ))

        if not hasVideo:
            tag.addVideoStream(xbmc.VideoStreamDetail(duration=item['runtime']))

    else:
        li_item.setInfo(type='Video', infoLabels={'title': item['title'],
                                                  'episode': item['episode'],
                                                  'season': item['season'],
                                                  'premiered': item['firstaired'],
                                                  'dbid': item['episodeid'],
                                                  'plot': item['plot'],
                                                  'tvshowtitle': item['showtitle'],
                                                  'originaltitle': item['originaltitle'],
                                                  'lastplayed': item['lastplayed'],
                                                  'rating': str(float(item['rating'])),
                                                  'userrating': str(float(item['userrating'])),
                                                  'votes': item['votes'],
                                                  'playcount': item['playcount'],
                                                  'director': get_joined_items(director),
                                                  'writer': get_joined_items(writer),
                                                  'path': item['file'],
                                                  'dateadded': item['dateadded'],
                                                  'mediatype': 'episode'
                                                  })

        if 'cast' in item:
            li_item.setCast(item['cast'])

        _set_ratings_legacy(li_item, item['ratings'])

        hasVideo = False
        for key, value in iter(list(item['streamdetails'].items())):
            for stream in value:
                if 'video' in key:
                    hasVideo = True
                li_item.addStreamInfo(key, stream)

        if not hasVideo:
            stream = {'duration': item['runtime']}
            li_item.addStreamInfo('video', stream)

    if 'cast' in item:
        cast_actors = _get_cast(item['cast'])
        _set_unique_properties(li_item,cast_actors[0],'cast')

    _set_unique_properties(li_item,director,'director')
    _set_unique_properties(li_item,writer,'writer')

    li_item.getVideoInfoTag().setResumePoint(item['resume']['position'], item['resume']['total'])
    li_item.setProperty('season_label', item.get('season_label', ''))

    li_item.setArt({'icon': 'DefaultTVShows.png',
                    'fanart': item['art'].get('tvshow.fanart', ''),
                    'poster': item['art'].get('tvshow.poster', ''),
                    'banner': item['art'].get('tvshow.banner', ''),
                    'clearlogo': item['art'].get('tvshow.clearlogo') or item['art'].get('tvshow.logo') or '',
                    'landscape': item['art'].get('tvshow.landscape', ''),
                    'clearart': item['art'].get('tvshow.clearart', '')
                    })
    li_item.setArt(item['art'])

    if item['season'] == '0':
        li_item.setProperty('IsSpecial', 'true')

    li.append((item['file'], li_item, False))


def handle_cast(li,item):
    li_item = xbmcgui.ListItem(item['name'], offscreen=True)
    li_item.setLabel(item['name'])
    li_item.setLabel2(item['role'])
    li_item.setProperty('role', item['role'])

    li_item.setArt({'icon': 'DefaultActor.png',
                    'thumb': item.get('thumbnail', '')
                    })

    li.append(('', li_item, False))


def get_unwatched(episode,watchedepisodes):
    if episode > watchedepisodes:
        unwatchedepisodes = episode - watchedepisodes
        return unwatchedepisodes
    else:
        return 0


def _get_cast(castData):
    listcast = []
    listcastandrole = []

    for castmember in castData:
        listcast.append(castmember['name'])
        listcastandrole.append((castmember['name'], castmember['role']))

    return [listcast, listcastandrole]


def _set_unique_properties(li_item,item,prop):
    try:
        i = 0
        for value in item:
            li_item.setProperty('%s.%s' % (prop,i), value)
            i += 1
    except Exception:
        pass

    return li_item


def _set_ratings_infotag(tag,item):
    """Set ratings using InfoTagVideo API (Kodi 20+)."""
    for key in item:
        try:
            rating = item[key]['rating']
            votes = item[key]['votes'] or 0
            default = True if key == 'default' or len(item) == 1 else False

            if rating > 100:
                raise Exception
            elif rating > 10:
                rating = rating / 10

            tag.setRating(float(rating), int(votes), key, default)

        except Exception:
            pass


def _set_ratings_legacy(li_item,item):
    """Set ratings using legacy setRating API (Kodi < 20)."""
    for key in item:
        try:
            rating = item[key]['rating']
            votes = item[key]['votes'] or 0
            default = True if key == 'default' or len(item) == 1 else False

            if rating > 100:
                raise Exception
            elif rating > 10:
                rating = rating / 10

            li_item.setRating(key, float(rating), votes, default)

        except Exception:
            pass

    return li_item
