#!/usr/bin/python
# coding: utf-8

########################

import xbmc
import xbmcgui
import requests
import datetime
import urllib.request as urllib
from urllib.parse import urlencode


from resources.lib.helper import *
from resources.lib.omdb import *
from resources.lib.localdb import *

########################

API_KEY = ADDON.getSettingString('tmdb_api_key')
API_URL = 'https://api.themoviedb.org/3/'
IMAGEPATH = 'https://image.tmdb.org/t/p/original'

########################

def tmdb_query(action,call=None,get=None,get2=None,get3=None,get4=None,params=None,use_language=True,language=DEFAULT_LANGUAGE,show_error=False):
    urlargs = {}
    urlargs['api_key'] = API_KEY

    if use_language:
        urlargs['language'] = language

    if params:
        urlargs.update(params)

    url = urljoin(API_URL ,action, call, get, get2, get3, get4)
    url = '{0}?{1}'.format(url, urlencode(urlargs))

    try:
        request = None

        for i in range(1,4): # loop if heavy server load
            try:
                request = requests.get(url, timeout=5)

                if str(request.status_code).startswith('5'):
                    raise Exception(str(request.status_code))
                else:
                    break

            except Exception:
                xbmc.sleep(500)

        if not request or request.status_code == 404:
            error = ADDON.getLocalizedString(32019)
            raise Exception(error)

        elif request.status_code == 401:
            error = ADDON.getLocalizedString(32022)
            raise Exception(error)

        elif not request.ok:
            raise Exception('Code ' + str(request.status_code))

        result = request.json()

        if show_error:
            if len(result) == 0 or ('results' in result and not len(result['results']) == 0):
                error = ADDON.getLocalizedString(32019)
                raise Exception(error)

        return result

    except Exception as error:
        log('%s --> %s' % (error, url), ERROR)
        if show_error:
            tmdb_error(error)


def tmdb_search(call,query,year=None,include_adult='false'):
    if call == 'person':
        params = {'query': query, 'include_adult': include_adult}

    elif call == 'movie':
        params = {'query': query, 'year': year, 'include_adult': include_adult}

    elif call == 'tv':
        params = {'query': query, 'first_air_date_year': year}

    else:
        return ''

    result = tmdb_query(action='search',
                        call=call,
                        params=params)

    try:
        result = result.get('results')

        if not result:
            raise Exception

        return result

    except Exception:
        tmdb_error(ADDON.getLocalizedString(32019))


def tmdb_find(call,external_id,error_check=True):
    if external_id.startswith('tt'):
        external_source = 'imdb_id'
    else:
        external_source = 'tvdb_id'

    result = tmdb_query(action='find',
                        call=str(external_id),
                        params={'external_source': external_source},
                        use_language=False,
                        show_error=True
                        )
    try:
        if call == 'movie':
            return result.get('movie_results')
        else:
            return result.get('tv_results')

    except AttributeError:
        return

def tmdb_select_dialog(list,call):
    indexlist = []
    selectionlist = []

    # date_field: campo del item a usar para el subtítulo (label2);
    # None significa que call == 'person' y no se muestra label2.
    if call == 'person':
        default_img = 'DefaultActor.png'
        img = 'profile_path'
        label = 'name'
        date_field = None

    elif call == 'movie':
        default_img = 'DefaultVideo.png'
        img = 'poster_path'
        label = 'title'
        date_field = 'release_date'

    elif call == 'tv':
        default_img = 'DefaultVideo.png'
        img = 'poster_path'
        label = 'name'
        date_field = 'first_air_date'

    else:
        return

    index = 0
    for item in list:
        icon = IMAGEPATH + item[img] if item[img] is not None else ''
        list_item = xbmcgui.ListItem(item[label])
        list_item.setArt({'icon': default_img, 'thumb': icon})

        # Mostrar el año como label2 cuando aplica (películas/series)
        if date_field is not None:
            try:
                list_item.setLabel2(str(tmdb_get_year(item.get(date_field, ""))))
            except Exception:
                pass

        selectionlist.append(list_item)
        indexlist.append(index)
        index += 1

    busydialog(close=True)

    selected = DIALOG.select(xbmc.getLocalizedString(424), selectionlist, useDetails=True)

    if selected == -1:
        return -1

    busydialog()

    return indexlist[selected]


def tmdb_select_dialog_small(list):
    indexlist = []
    selectionlist = []

    index = 0
    for item in list:
        list_item = xbmcgui.ListItem(item)
        selectionlist.append(list_item)
        indexlist.append(index)
        index += 1

    busydialog(close=True)

    selected = DIALOG.select(xbmc.getLocalizedString(424), selectionlist, useDetails=False)

    if selected == -1:
        return -1

    busydialog()

    return indexlist[selected]


def tmdb_calc_age(birthday,deathday=None):
    if deathday is not None:
        ref_day = deathday.split("-")

    elif birthday:
        date = datetime.date.today()
        ref_day = [date.year, date.month, date.day]

    else:
        return ''

    born = birthday.split('-')
    age = int(ref_day[0]) - int(born[0])

    if len(born) > 1:
        diff_months = int(ref_day[1]) - int(born[1])
        diff_days = int(ref_day[2]) - int(born[2])

        if diff_months < 0 or (diff_months == 0 and diff_days < 0):
            age -= 1

    return age


def tmdb_error(message=ADDON.getLocalizedString(32019)):
    busydialog(close=True)
    DIALOG.ok(ADDON.getLocalizedString(32000), str(message))


def tmdb_studios(list_item,item,key):
    if key == 'production':
        key_name = 'production_companies'
        prop_name = 'studio'
    elif key == 'network':
        key_name = 'networks'
        prop_name = 'network'
    else:
        return

    i = 0
    for studio in item[key_name]:
        icon = IMAGEPATH + studio['logo_path'] if studio['logo_path'] is not None else ''
        if icon:
            list_item.setProperty(prop_name + '.' + str(i), studio['name'])
            list_item.setProperty(prop_name + '.icon.' + str(i), icon)
            i += 1


def tmdb_check_localdb(local_items,title,originaltitle,year,imdbnumber=False):
    found_local = False
    local = {'dbid': -1, 'playcount': 0, 'watchedepisodes': '', 'episodes': '', 'unwatchedepisodes': '', 'file': ''}

    if local_items:
        for item in local_items:
            dbid = item['dbid']
            playcount = item['playcount']
            episodes = item.get('episodes', '')
            watchedepisodes = item.get('watchedepisodes', '')
            file = item.get('file', '')

            if imdbnumber and item['imdbnumber'] == imdbnumber:
                found_local = True
                break

            try:
                tmdb_year = int(tmdb_get_year(year))
                item_year = int(item['year'])

                if item_year == tmdb_year:
                    if item['originaltitle'] == originaltitle or item['title'] == originaltitle or item['title'] == title:
                        found_local = True
                        break
                elif tmdb_year in [item_year-2, item_year-1, item_year+1, item_year+2]:
                    if item['title'] == title and item['originaltitle'] == originaltitle:
                        found_local = True
                        break

            except ValueError:
                pass

    if found_local:
        local['dbid'] = dbid
        local['file'] = file
        local['playcount'] = playcount
        local['episodes'] = episodes
        local['watchedepisodes'] = watchedepisodes
        local['unwatchedepisodes'] = episodes - watchedepisodes if episodes else ''

    return local


def tmdb_handle_person(item):
    if item.get('gender') == 2:
        gender = 'male'
    elif item.get('gender') == 1:
        gender = 'female'
    else:
        gender = ''

    icon = IMAGEPATH + item['profile_path'] if item['profile_path'] is not None else ''
    list_item = xbmcgui.ListItem(label=item['name'])
    list_item.setProperty('birthyear', date_year(item.get('birthday', '')))
    list_item.setProperty('birthday', date_format(item.get('birthday', '')))
    list_item.setProperty('deathday', date_format(item.get('deathday', '')))
    list_item.setProperty('age', str(tmdb_calc_age(item.get('birthday', ''), item.get('deathday'))))
    list_item.setProperty('biography', tmdb_fallback_info(item, 'biography'))
    list_item.setProperty('place_of_birth', item.get('place_of_birth').strip() if item.get('place_of_birth') else '')
    list_item.setProperty('known_for_department', item.get('known_for_department', ''))
    list_item.setProperty('gender', gender)
    list_item.setProperty('id', str(item.get('id', '')))
    list_item.setProperty('call', 'person')
    list_item.setArt({'icon': 'DefaultActor.png', 'thumb': icon, 'poster': icon})

    return list_item


def tmdb_handle_movie(item,local_items=None,full_info=False,mediatype='movie'):
    icon = IMAGEPATH + item['poster_path'] if item['poster_path'] is not None else ''
    backdrop = IMAGEPATH + item['backdrop_path'] if item['backdrop_path'] is not None else ''

    label = item['title'] or item['original_title']
    originaltitle = item.get('original_title', '')
    imdbnumber = item.get('imdb_id', '')
    collection = item.get('belongs_to_collection', '')
    duration = item.get('runtime') * 60 if item.get('runtime', 0) > 0 else ''

    premiered = item.get('release_date')
    if premiered in ['2999-01-01', '1900-01-01']:
        premiered = ''

    local_info = tmdb_check_localdb(local_items, label, originaltitle, premiered, imdbnumber)
    dbid = local_info['dbid']
    is_local = True if dbid > 0 else False

    list_item = xbmcgui.ListItem(label=label)
    set_video_info(list_item, {'title': label,
                                'originaltitle': originaltitle,
                                'dbid': dbid,
                                'playcount': local_info['playcount'],
                                'imdbnumber': imdbnumber,
                                'rating': item.get('vote_average', ''),
                                'votes': item.get('vote_count', ''),
                                'premiered': premiered,
                                'mpaa': tmdb_get_cert(item),
                                'tagline': item.get('tagline', ''),
                                'duration': duration,
                                'status': item.get('status', ''),
                                'plot': tmdb_fallback_info(item, 'overview'),
                                'director': tmdb_join_items_by(item.get('crew', ''), key_is='job', value_is='Director'),
                                'writer': tmdb_join_items_by(item.get('crew', ''), key_is='department', value_is='Writing'),
                                'country': tmdb_join_items(item.get('production_countries', '')),
                                'genre': tmdb_join_items(item.get('genres', '')),
                                'studio': tmdb_join_items(item.get('production_companies', '')),
                                'mediatype': mediatype}
                                 )
    list_item.setArt({'icon': 'DefaultVideo.png', 'thumb': icon, 'poster': icon, 'fanart': backdrop})
    list_item.setProperty('role', item.get('character', ''))
    list_item.setProperty('budget', format_currency(item.get('budget')))
    list_item.setProperty('revenue', format_currency(item.get('revenue')))
    list_item.setProperty('homepage', item.get('homepage', ''))
    list_item.setProperty('file', local_info.get('file', ''))
    list_item.setProperty('id', str(item.get('id', '')))
    list_item.setProperty('call', 'movie')

    if full_info:
        tmdb_studios(list_item, item, 'production')
        omdb_properties(list_item, imdbnumber)

        region_release = tmdb_get_region_release(item)
        if premiered != region_release:
            list_item.setProperty('region_release', date_format(region_release))

        if collection:
            list_item.setProperty('collection', collection['name'])
            list_item.setProperty('collection_id', str(collection['id']))
            list_item.setProperty('collection_poster', IMAGEPATH + collection['poster_path'] if collection['poster_path'] is not None else '')
            list_item.setProperty('collection_fanart', IMAGEPATH + collection['backdrop_path'] if collection['backdrop_path'] is not None else '')

    return list_item, is_local


def tmdb_handle_tvshow(item,local_items=None,full_info=False,mediatype='tvshow'):
    icon = IMAGEPATH + item['poster_path'] if item['poster_path'] is not None else ''
    backdrop = IMAGEPATH + item['backdrop_path'] if item['backdrop_path'] is not None else ''

    label = item['name'] or item['original_name']
    originaltitle = item.get('original_name', '')
    imdbnumber = item['external_ids']['imdb_id'] if item.get('external_ids') else ''
    next_episode = item.get('next_episode_to_air', '')
    last_episode = item.get('last_episode_to_air', '')
    tvdb_id = item['external_ids']['tvdb_id'] if item.get('external_ids') else ''

    premiered = item.get('first_air_date')
    if premiered in ['2999-01-01', '1900-01-01']:
        premiered = ''

    local_info = tmdb_check_localdb(local_items, label, originaltitle, premiered, tvdb_id)
    dbid = local_info['dbid']
    is_local = True if dbid > 0 else False

    list_item = xbmcgui.ListItem(label=label)
    set_video_info(list_item, {'title': label,
                                'originaltitle': originaltitle,
                                'dbid': dbid,
                                'playcount': local_info['playcount'],
                                'status': item.get('status', ''),
                                'rating': item.get('vote_average', ''),
                                'votes': item.get('vote_count', ''),
                                'imdbnumber': imdbnumber,
                                'premiered': premiered,
                                'mpaa': tmdb_get_cert(item),
                                'season': str(item.get('number_of_seasons', '')),
                                'episode': str(item.get('number_of_episodes', '')),
                                'plot': tmdb_fallback_info(item, 'overview'),
                                'director': tmdb_join_items(item.get('created_by', '')),
                                'genre': tmdb_join_items(item.get('genres', '')),
                                'studio': tmdb_join_items(item.get('networks', '')),
                                'mediatype': mediatype}
                                )
    list_item.setArt({'icon': 'DefaultVideo.png', 'thumb': icon, 'poster': icon, 'fanart': backdrop})
    list_item.setProperty('TotalEpisodes', str(local_info['episodes']))
    list_item.setProperty('WatchedEpisodes', str(local_info['watchedepisodes']))
    list_item.setProperty('UnWatchedEpisodes', str(local_info['unwatchedepisodes']))
    list_item.setProperty('homepage', item.get('homepage', ''))
    list_item.setProperty('role', item.get('character', ''))
    list_item.setProperty('tvdb_id', str(tvdb_id))
    list_item.setProperty('id', str(item.get('id', '')))
    list_item.setProperty('call', 'tv')

    if full_info:
        tmdb_studios(list_item,item, 'production')
        tmdb_studios(list_item,item, 'network')
        omdb_properties(list_item, imdbnumber)

        if last_episode:
            list_item.setProperty('lastepisode', last_episode.get('name'))
            list_item.setProperty('lastepisode_plot', last_episode.get('overview'))
            list_item.setProperty('lastepisode_number', str(last_episode.get('episode_number')))
            list_item.setProperty('lastepisode_season', str(last_episode.get('season_number')))
            list_item.setProperty('lastepisode_date', date_format(last_episode.get('air_date')))
            list_item.setProperty('lastepisode_thumb', IMAGEPATH + last_episode['still_path'] if last_episode['still_path'] is not None else '')

        if next_episode:
            list_item.setProperty('nextepisode', next_episode.get('name'))
            list_item.setProperty('nextepisode_plot', next_episode.get('overview'))
            list_item.setProperty('nextepisode_number', str(next_episode.get('episode_number')))
            list_item.setProperty('nextepisode_season', str(next_episode.get('season_number')))
            list_item.setProperty('nextepisode_date', date_format(next_episode.get('air_date')))
            list_item.setProperty('nextepisode_thumb', IMAGEPATH + next_episode['still_path'] if next_episode['still_path'] is not None else '')

    return list_item, is_local


def tmdb_handle_season(item,tvshow_details,full_info=False):
    backdrop = IMAGEPATH + tvshow_details['backdrop_path'] if tvshow_details['backdrop_path'] is not None else ''
    icon = IMAGEPATH + item['poster_path'] if item['poster_path'] is not None else ''
    if not icon and tvshow_details['poster_path']:
        icon = IMAGEPATH + tvshow_details['poster_path']

    imdbnumber = tvshow_details['external_ids']['imdb_id'] if tvshow_details.get('external_ids') else ''
    season_nr = str(item.get('season_number', ''))
    tvshow_label = tvshow_details['name'] or tvshow_details['original_name']

    episodes_count = 0
    for episode in item.get('episodes', ''):
        episodes_count += 1

    list_item = xbmcgui.ListItem(label=tvshow_label)
    set_video_info(list_item, {'title': item['name'],
                               'tvshowtitle': tvshow_label,
                               'premiered': item.get('air_date', ''),
                               'episode': episodes_count,
                               'season': season_nr,
                               'plot': item.get('overview', ''),
                               'genre': tmdb_join_items(tvshow_details.get('genres', '')),
                               'rating': tvshow_details.get('vote_average', ''),
                               'votes': tvshow_details.get('vote_count', ''),
                               'mpaa': tmdb_get_cert(tvshow_details),
                               'mediatype': 'season'})
    list_item.setArt({'icon': 'DefaultVideo.png', 'thumb': icon, 'poster': icon, 'fanart': backdrop})
    list_item.setProperty('TotalEpisodes', str(episodes_count))
    list_item.setProperty('id', str(tvshow_details['id']))
    list_item.setProperty('call', 'tv')
    list_item.setProperty('call_season', season_nr)

    if full_info:
        tmdb_studios(list_item,tvshow_details, 'production')
        tmdb_studios(list_item,tvshow_details, 'network')
        omdb_properties(list_item, imdbnumber)

    return list_item


def tmdb_fallback_info(item,key):
    if FALLBACK_LANGUAGE == DEFAULT_LANGUAGE:
        try:
            key_value = item.get(key, '').replace('&amp;', '&').strip()
        except Exception:
            key_value = ''

    else:
        key_value = tmdb_get_translation(item, key, DEFAULT_LANGUAGE)

    # Default language is empty in the translations dict? Fall back to EN
    if not key_value:
        key_value = tmdb_get_translation(item, key, FALLBACK_LANGUAGE)

    return key_value


def tmdb_get_translation(item,key,language):
    key_value_iso_639_1 = ""
    try:
        language_iso_639_1 = language[:2]
        language_iso_3166_1 = language[3:] if len(language)>3 else None

        for translation in item['translations']['translations']:
            if translation.get('iso_639_1') == language_iso_639_1 and translation['data'][key]:
                key_value = translation['data'][key]
                if key_value:
                    key_value = key_value.replace('&amp;', '&').strip()
                    if not language_iso_3166_1 or language_iso_3166_1 == translation.get('iso_3166_1'):
                        return key_value
                    else:
                        key_value_iso_639_1 = key_value
    except Exception:
        pass

    return key_value_iso_639_1


def tmdb_handle_images(item):
    icon = IMAGEPATH + item['file_path'] if item['file_path'] is not None else ''
    list_item = xbmcgui.ListItem(label=str(item['width']) + 'x' + str(item['height']) + 'px')
    list_item.setArt({'icon': 'DefaultPicture.png', 'thumb': icon})
    list_item.setProperty('call', 'image')

    return list_item


def tmdb_handle_credits(item):
    icon = IMAGEPATH + item['profile_path'] if item['profile_path'] is not None else ''
    list_item = xbmcgui.ListItem(label=item['name'])
    list_item.setLabel2(item['label2'])
    list_item.setArt({'icon': 'DefaultActor.png', 'thumb': icon, 'poster': icon})
    list_item.setProperty('id', str(item.get('id', '')))
    list_item.setProperty('call', 'person')

    return list_item


def tmdb_handle_yt_videos(item):
    icon = 'https://img.youtube.com/vi/%s/0.jpg' % str(item['key'])
    list_item = xbmcgui.ListItem(label=item['name'])
    list_item.setLabel2(item.get('type', ''))
    list_item.setArt({'icon': 'DefaultVideo.png', 'thumb': icon, 'landscape': icon})
    list_item.setProperty('ytid', str(item['key']))
    list_item.setProperty('call', 'youtube')

    return list_item


def tmdb_join_items_by(item,key_is,value_is,key='name'):
    values = []
    for value in item:
        if value[key_is] == value_is:
            values.append(value[key])

    return get_joined_items(values)


def tmdb_join_items(item,key='name'):
    values = []
    for value in item:
        values.append(value[key])

    return get_joined_items(values)


def tmdb_get_year(item):
    try:
        year = str(item)[:-6]
        return year
    except Exception:
        return ''


def tmdb_get_region_release(item):
    try:
        for release in item['release_dates']['results']:
            if release['iso_3166_1'] == COUNTRY_CODE:
                date = release['release_dates'][0]['release_date']
                return date[:-14]

    except Exception:
        return ''


def tmdb_get_cert(item):
    prefix = 'FSK ' if COUNTRY_CODE == 'DE' else ''
    mpaa = ''
    mpaa_fallback = ''

    if item.get('content_ratings'):
        for cert in item['content_ratings']['results']:
            if cert['iso_3166_1'] == COUNTRY_CODE:
                mpaa = cert['rating']
                break
            elif cert['iso_3166_1'] == 'US':
                mpaa_fallback = cert['rating']

    elif item.get('release_dates'):
        for cert in item['release_dates']['results']:
            if cert['iso_3166_1'] == COUNTRY_CODE:
                mpaa = cert['release_dates'][0]['certification']
                break
            elif cert['iso_3166_1'] == 'US':
                mpaa_fallback = cert['release_dates'][0]['certification']

    if mpaa:
        return prefix + mpaa

    return mpaa_fallback


def omdb_properties(list_item,imdbnumber):
    if OMDB_API_KEY and imdbnumber:
        omdb = omdb_api(imdbnumber)
        if omdb:
            list_item.setProperty('rating.metacritic', omdb.get('metacritic', ''))
            list_item.setProperty('rating.rotten', omdb.get('tomatometerallcritics', ''))
            list_item.setProperty('rating.rotten_avg', omdb.get('tomatometerallcritics_avg', ''))
            list_item.setProperty('votes.rotten', omdb.get('tomatometerallcritics_votes', ''))
            list_item.setProperty('rating.rotten_user', omdb.get('tomatometerallaudience', ''))
            list_item.setProperty('rating.rotten_user_avg', omdb.get('tomatometerallaudience_avg', ''))
            list_item.setProperty('votes.rotten_user', omdb.get('tomatometerallaudience_votes', ''))
            list_item.setProperty('rating.imdb', omdb.get('imdbRating', ''))
            list_item.setProperty('votes.imdb', omdb.get('imdbVotes', ''))
            list_item.setProperty('awards', omdb.get('awards', ''))
            list_item.setProperty('release', omdb.get('DVD', ''))