# -*- coding: utf-8 -*-
"""
A Kodi add-on for Viaplay
"""
import sys
import urlparse
from datetime import datetime

from resources.lib.kodihelper import KodiHelper

base_url = sys.argv[0]
handle = int(sys.argv[1])
helper = KodiHelper(base_url, handle)


def run():
    try:
        router(sys.argv[2][1:])  # trim the leading '?' from the plugin call paramstring
    except helper.vp.ViaplayError as error:
        if error.value == 'MissingSessionCookieError':
            if helper.authorize():
                router(sys.argv[2][1:])
        else:
            show_error(error.value)


def root_page():
    pages = helper.vp.get_root_page()

    for page in pages:
        params = {
            'action': page['name'],
            'url': page['href']
        }
        helper.add_item(page['title'], params)
    helper.eod()


def start_page(url):
    collections = helper.vp.get_collections(url)

    for i in collections:
        params = {
            'action': 'list_products',
            'url': i['_links']['self']['href']
        }
        helper.add_item(i['title'], params)
    helper.eod()


def vod_page(url):
    """List categories and collections from the VOD pages (movies, series, kids, store)."""
    collections = helper.vp.get_collections(url)

    categories_item(url)
    for i in collections:
        params = {
            'action': 'list_products',
            'url': i['_links']['self']['href']
        }
        helper.add_item(i['title'], params)
    helper.eod()


def categories_page(url):
    categories = helper.vp.make_request(url, 'get')['_links']['viaplay:categoryFilters']

    for i in categories:
        params = {
            'action': 'sortings_page',
            'url': i['href']
        }
        helper.add_item(i['title'], params)
    helper.eod()


def sortings_page(url):
    sortings = helper.vp.make_request(url, 'get')['_links']['viaplay:sortings']

    for i in sortings:
        params = {
            'action': 'list_products',
            'url': i['href']
        }
        helper.add_item(i['title'], params)
    helper.eod()


def sports_page(url):
    collections = helper.vp.get_collections(url)
    schedule_added = False

    for i in collections:
        if 'viaplay:seeTableau' in i['_links'] and not schedule_added:
            params = {
                'action': 'sports_schedule_page',
                'url': i['_links']['viaplay:seeTableau']['href']
            }
            helper.add_item(i['_links']['viaplay:seeTableau']['title'], params)
            schedule_added = True

        if i['totalProductCount'] < 1:
            continue  # hide empty collections
        params = {
            'action': 'list_products',
            'url': i['_links']['self']['href']
        }
        helper.add_item(i['title'], params)
    helper.eod()


def sports_schedule_page(url):
    dates = helper.vp.make_request(url=url, method='get')['_links']['viaplay:days']

    for date in dates:
        params = {
            'action': 'list_products',
            'url': date['href']
        }
        helper.add_item(date['date'], params)
    helper.eod()


def channels_page(url):
    channels_dict = helper.vp.get_channels(url)

    for channel in channels_dict['channels']:
        params = {
            'action': 'list_products',
            'url': channel['_links']['self']['href']
        }
        art = {
            'thumb': channel['content']['images']['fallback']['template'].split('{')[0],
            'fanart': channel['content']['images']['fallback']['template'].split('{')[0]
        }

        for program in channel['_embedded']['viaplay:products']:  # get current live program
            if helper.vp.get_event_status(program) == 'live':
                if 'content' in program:
                    current_program_title = coloring(program['content']['title'].encode('utf-8'), 'live')
                else:  # no broadcast
                    current_program_title = coloring(helper.language(30049).encode('utf-8'), 'no_broadcast')
                break

        list_title = '[B]{0}[/B]: {1}'.format(channel['content']['title'], current_program_title)

        helper.add_item(list_title, params, art=art)

    if channels_dict['next_page']:
        list_next_page(channels_dict['next_page'], 'tve')
    helper.eod()


def categories_item(url):
    title = helper.language(30041)
    params = {
        'action': 'categories_page',
        'url': url
    }
    helper.add_item(title, params)


def list_next_page(url, action):
    title = helper.language(30018)
    params = {
        'action': action,
        'url': url
    }
    helper.add_item(title, params)


def list_products(url, filter_event=False, search_query=None):
    if filter_event:
        filter_event = filter_event.split(', ')

    products_dict = helper.vp.get_products(url, filter_event=filter_event, search_query=search_query)
    for product in products_dict['products']:
        if product['type'] == 'series':
            add_series(product)
        elif product['type'] == 'episode':
            add_episode(product)
        elif product['type'] == 'movie':
            add_movie(product)
        elif product['type'] == 'sport':
            add_sports_event(product)
        elif product['type'] == 'tvEvent':
            add_tv_event(product)
        else:
            helper.log('product type: {0} is not (yet) supported.'.format(product['type']))
            return False

    if products_dict['next_page']:
        list_next_page(products_dict['next_page'], 'list_products')
    helper.eod()


def add_movie(movie):
    params = {}
    if movie['system'].get('guid'):
        params['guid'] = movie['system']['guid']
    else:
        params['url'] = movie['_links']['self']['href']
    params['action'] = 'play'

    details = movie['content']

    movie_info = {
        'mediatype': 'movie',
        'title': details['title'],
        'plot': details.get('synopsis'),
        'genre': ', '.join([x['title'] for x in movie['_links']['viaplay:genres']]),
        'year': details['production'].get('year'),
        'duration': int(details['duration'].get('milliseconds')) // 1000 if 'duration' in details else None,
        'cast': details['people'].get('actors', []) if 'people' in details else [],
        'director': ', '.join(details['people'].get('directors', [])) if 'people' in details else [],
        'mpaa': details.get('parentalRating'),
        'rating': float(details['imdb'].get('rating')) if 'imdb' in details else None,
        'votes': str(details['imdb'].get('votes')) if 'imdb' in details else None,
        'code': details['imdb'].get('id') if 'imdb' in details else None
    }

    helper.add_item(movie_info['title'], params=params, info=movie_info, art=add_art(details['images'], 'movie'),
                    content='movies', playable=True)


def add_series(show):
    params = {
        'action': 'seasons_page',
        'url': show['_links']['viaplay:page']['href']
    }

    details = show['content']

    series_info = {
        'mediatype': 'tvshow',
        'title': details['series']['title'],
        'tvshowtitle': details['series']['title'],
        'plot': details['synopsis'] if details.get('synopsis') else details['series'].get('synopsis'),
        'genre': ', '.join([x['title'] for x in show['_links']['viaplay:genres']]),
        'year': details['production'].get('year') if 'production' in details else None,
        'cast': details['people'].get('actors', []) if 'people' in details else [],
        'director': ', '.join(details['people'].get('directors', [])) if 'people' in details else None,
        'mpaa': details.get('parentalRating'),
        'rating': float(details['imdb'].get('rating')) if 'imdb' in details else None,
        'votes': str(details['imdb'].get('votes')) if 'imdb' in details else None,
        'code': details['imdb'].get('id') if 'imdb' in details else None,
        'season': int(details['series']['seasons']) if details['series'].get('seasons') else None
    }

    helper.add_item(series_info['title'], params=params, folder=True, info=series_info,
                    art=add_art(details['images'], 'series'), content='tvshows')


def add_episode(episode):
    params = {
        'action': 'play',
        'guid': episode['system']['guid']
    }

    details = episode['content']

    episode_info = {
        'mediatype': 'episode',
        'title': details.get('title'),
        'list_title': details['series']['episodeTitle'] if details['series'].get('episodeTitle') else details.get(
            'title'),
        'tvshowtitle': details['series'].get('title'),
        'plot': details['synopsis'] if details.get('synopsis') else details['series'].get('synopsis'),
        'duration': details['duration']['milliseconds'] // 1000 if 'duration' in details else None,
        'genre': ', '.join([x['title'] for x in episode['_links']['viaplay:genres']]),
        'year': details['production'].get('year') if 'production' in details else None,
        'cast': details['people'].get('actors', []) if 'people' in details else [],
        'director': ', '.join(details['people'].get('directors', [])) if 'people' in details else None,
        'mpaa': details.get('parentalRating'),
        'rating': float(details['imdb'].get('rating')) if 'imdb' in details else None,
        'votes': str(details['imdb'].get('votes')) if 'imdb' in details else None,
        'code': details['imdb'].get('id') if 'imdb' in details else None,
        'season': int(details['series']['season'].get('seasonNumber')),
        'episode': int(details['series'].get('episodeNumber'))
    }

    helper.add_item(episode_info['list_title'], params=params, info=episode_info,
                    art=add_art(details['images'], 'episode'), content='episodes', playable=True)


def add_sports_event(event):
    now = datetime.now()
    date_today = now.date()
    event_date = helper.vp.parse_datetime(event['epg']['start'], localize=True)
    event_status = helper.vp.get_event_status(event)

    if date_today == event_date.date():
        start_time = '{0} {1}'.format(helper.language(30027), event_date.strftime('%H:%M'))
    else:
        start_time = event_date.strftime('%Y-%m-%d %H:%M')

    if event_status == 'upcoming':
        params = {
            'action': 'dialog',
            'dialog_type': 'ok',
            'heading': helper.language(30017),
            'message': helper.language(30016).format(start_time)
        }
        playable = False
    else:
        params = {
            'action': 'play',
            'guid': event['system']['guid']
        }
        playable = True

    details = event['content']

    event_info = {
        'mediatype': 'video',
        'title': details.get('title'),
        'plot': details['synopsis'],
        'year': int(details['production'].get('year')),
        'genre': details['format'].get('title'),
        'list_title': '[B]{0}:[/B] {1}'.format(coloring(start_time, event_status),
                                               details.get('title').encode('utf-8'))
    }

    helper.add_item(event_info['list_title'], params=params, playable=playable, info=event_info,
                    art=add_art(details['images'], 'sport'), content='episodes')


def add_tv_event(event):
    now = datetime.now()
    date_today = now.date()
    start_time_obj = helper.vp.parse_datetime(event['epg']['startTime'], localize=True)
    event_status = helper.vp.get_event_status(event)

    if date_today == start_time_obj.date():
        start_time = '{0} {1}'.format(helper.language(30027), start_time_obj.strftime('%H:%M'))
    else:
        start_time = start_time_obj.strftime('%Y-%m-%d %H:%M')

    if event_status == 'upcoming':
        params = {
            'action': 'dialog',
            'dialog_type': 'ok',
            'heading': helper.language(30017),
            'message': helper.language(30016).format(start_time)
        }
        playable = False
    else:
        params = {
            'action': 'play',
            'guid': event['system']['guid']
        }
        playable = True

    details = event['content']
    event_info = {
        'mediatype': 'video',
        'title': details.get('title'),
        'plot': details.get('synopsis'),
        'year': details['production'].get('year'),
        'list_title': '[B]{0}:[/B] {1}'.format(coloring(start_time, event_status),
                                               details.get('title').encode('utf-8'))
    }
    art = {
        'thumb': event['content']['images']['landscape']['template'].split('{')[0] if 'landscape' in details['images'] else None,
        'fanart': event['content']['images']['landscape']['template'].split('{')[0] if 'landscape' in details['images'] else None
    }

    helper.add_item(event_info['list_title'], params=params, playable=playable, info=event_info, art=art, content='episodes')



def seasons_page(url):
    """List all series seasons."""
    seasons = helper.vp.get_seasons(url)
    if len(seasons) == 1:  # list products if there's only one season
        list_products(seasons[0]['_links']['self']['href'])
    else:
        for season in seasons:
            title = helper.language(30014).format(season['title'])
            parameters = {
                'action': 'list_products',
                'url': season['_links']['self']['href']
            }

            helper.add_item(title, parameters)
        helper.eod()


def add_art(images, content_type):
    artwork = {}

    for i in images:
        image_url = images[i]['template'].split('{')[0]  # get rid of template

        if i == 'landscape':
            if content_type == 'episode' or 'sport':
                artwork['thumb'] = image_url
            artwork['banner'] = image_url
        elif i == 'hero169':
            artwork['fanart'] = image_url
        elif i == 'coverart23':
            artwork['cover'] = image_url
        elif i == 'boxart':
            if content_type != 'episode' or 'sport':
                artwork['thumb'] = image_url
            artwork['poster'] = image_url

    return artwork


def search(url):
    query = helper.get_user_input(helper.language(30015))
    if query:
        list_products(url, search_query=query)


def coloring(text, meaning):
    """Return the text wrapped in appropriate color markup."""
    if meaning == 'live':
        color = 'FF03F12F'
    elif meaning == 'upcoming':
        color = 'FFF16C00'
    elif meaning == 'archive':
        color = 'FFFF0EE0'
    elif meaning == 'no_broadcast':
        color = 'FFFF3333'
    colored_text = '[COLOR=%s]%s[/COLOR]' % (color, text)
    return colored_text


def show_error(error):
    if error == 'UserNotAuthorizedForContentError':
        message = helper.language(30020)
    elif error == 'PurchaseConfirmationRequiredError':
        message = helper.language(30021)
    elif error == 'UserNotAuthorizedRegionBlockedError':
        message = helper.language(30022)
    elif error == 'ConcurrentStreamsLimitReachedError':
        message = helper.language(30050)
    else:
        message = error

    helper.dialog(dialog_type='ok', heading=helper.language(30017), message=message)


def router(paramstring):
    """Router function that calls other functions depending on the provided paramstring."""
    params = dict(urlparse.parse_qsl(paramstring))
    vod_pages = ['series', 'movie', 'kids', 'rental']
    products_pages = ['viaplay:starred', 'viaplay:watched', 'viaplay:purchased']

    if 'action' in params:
        if params['action'] in vod_pages:
            vod_page(params['url'])
        elif params['action'] in products_pages:
            list_products(params['url'])
        elif params['action'] == 'sport':
            sports_page(params['url'])
        elif params['action'] == 'tve':
            channels_page(params['url'])
        elif params['action'] == 'categories_page':
            categories_page(params['url'])
        elif params['action'] == 'sortings_page':
            sortings_page(params['url'])
        if params['action'] == 'viaplay:root':
            start_page(params['url'])
        elif params['action'] == 'viaplay:search':
            search(params['url'])
        elif params['action'] == 'viaplay:logout':
            helper.log_out()
        elif params['action'] == 'sports_schedule_page':
            sports_schedule_page(params['url'])
        elif params['action'] == 'play':
            helper.play(guid=params.get('guid'), url=params.get('url'))
        elif params['action'] == 'seasons_page':
            seasons_page(params['url'])
        elif params['action'] == 'list_products':
            list_products(params['url'])
        elif params['action'] == 'dialog':
            helper.dialog(params['dialog_type'], params['heading'], params['message'])
    else:
        root_page()
