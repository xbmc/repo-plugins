# -*- coding: utf-8 -*-
"""
A Kodi add-on for Viaplay
"""
import sys
from datetime import datetime

from resources.lib.kodihelper import KodiHelper

import xbmc
import routing

base_url = sys.argv[0]
handle = int(sys.argv[1])
helper = KodiHelper(base_url, handle)
plugin = routing.Plugin()


def run():
    try:
        plugin.run()
    except helper.vp.ViaplayError as error:
        if error.value == 'MissingSessionCookieError':
            if helper.authorize():
                plugin.run()
        else:
            show_error(error.value)


@plugin.route('/')
def root():
    pages = helper.vp.get_root_page()
    supported_pages = {
        'viaplay:root': start,
        'viaplay:search': search,
        'viaplay:logout': log_out,
        'viaplay:starred': list_products,
        'viaplay:watched': list_products,
        'viaplay:purchased': list_products,
        'series': vod,
        'movie': vod,
        'kids': vod,
        'rental': vod,
        'sport': sport,
        'tve': channels,
        'channels': channels
    }

    for page in pages:
        if page['name'] in supported_pages:
            helper.add_item(page['title'], plugin.url_for(supported_pages[page['name']], url=page['href']))
        elif 'type' in page and page['type'] in supported_pages:  # weird channels listing fix on some subscriptions
            helper.add_item(page['title'], plugin.url_for(supported_pages[page['type']], url=page['href']))
        else:
            helper.log('Unsupported page found: %s' % page['name'])
    helper.eod()


@plugin.route('/start')
def start():
    collections = helper.vp.get_collections(plugin.args['url'][0])
    for i in collections:
        helper.add_item(i['title'], plugin.url_for(list_products, url=i['_links']['self']['href']))
    helper.eod()


@plugin.route('/search')
def search():
    query = helper.get_user_input(helper.language(30015))
    if query:
        list_products(plugin.args['url'][0], search_query=query)


@plugin.route('/vod')
def vod():
    """List categories and collections from the VOD pages (movies, series, kids, store)."""
    helper.add_item(helper.language(30041), plugin.url_for(categories, url=plugin.args['url'][0]))
    collections = helper.vp.get_collections(plugin.args['url'][0])
    for i in collections:
        helper.add_item(i['title'], plugin.url_for(list_products, url=i['_links']['self']['href']))
    helper.eod()


@plugin.route('/sport')
def sport():
    collections = helper.vp.get_collections(plugin.args['url'][0])
    schedule_added = False

    for i in collections:
        if 'viaplay:seeTableau' in i['_links'] and not schedule_added:
            plugin_url = plugin.url_for(sports_schedule, url=i['_links']['viaplay:seeTableau']['href'])
            helper.add_item(i['_links']['viaplay:seeTableau']['title'], plugin_url)
            schedule_added = True

        if i['totalProductCount'] < 1:
            continue  # hide empty collections
        helper.add_item(i['title'], plugin.url_for(list_products, url=i['_links']['self']['href']))
    helper.eod()


@plugin.route('/channels')
def channels():
    channels_dict = helper.vp.get_channels(plugin.args['url'][0])

    for channel in channels_dict['channels']:
        plugin_url = plugin.url_for(list_products, url=channel['_links']['self']['href'])
        if 'fallback' in channel['content']['images']:
            channel_image = channel['content']['images']['fallback']['template'].split('{')[0]
        else:
            channel_image = channel['content']['images']['logo']['template'].split('{')[0]
        art = {
            'thumb': channel_image,
            'fanart': channel_image
        }

        for program in channel['_embedded']['viaplay:products']:  # get current live program
            if helper.vp.get_event_status(program) == 'live':
                if 'content' in program:
                    current_program_title = coloring(program['content']['title'].encode('utf-8'), 'live')
                else:  # no broadcast
                    current_program_title = coloring(helper.language(30049).encode('utf-8'), 'no_broadcast')
                break

        list_title = '[B]{0}[/B]: {1}'.format(channel['content']['title'], current_program_title)

        helper.add_item(list_title, plugin_url, art=art)

    if channels_dict['next_page']:
        helper.add_item(helper.language(30018), plugin.url_for(channels, url=channels_dict['next_page']))
    helper.eod()


@plugin.route('/log_out')
def log_out():
    confirm = helper.dialog('yesno', helper.language(30042), helper.language(30043))
    if confirm:
        helper.vp.log_out()
        # send Kodi back to home screen
        xbmc.executebuiltin('XBMC.Container.Update(path, replace)')
        xbmc.executebuiltin('XBMC.ActivateWindow(Home)')


@plugin.route('/list_products')
def list_products(url=None, search_query=None):
    if not url:
        url = plugin.args['url'][0]
    products_dict = helper.vp.get_products(url, search_query=search_query)
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
        helper.add_item(helper.language(30018), plugin.url_for(list_products, url=products_dict['next_page']))
    helper.eod()


@plugin.route('/sports_schedule')
def sports_schedule():
    dates = helper.vp.make_request(url=plugin.args['url'][0], method='get')['_links']['viaplay:days']
    for date in dates:
        helper.add_item(date['date'], plugin.url_for(list_products, url=date['href']))
    helper.eod()


@plugin.route('/seasons_page')
def seasons_page():
    """List all series seasons."""
    seasons = helper.vp.get_seasons(plugin.args['url'][0])
    if len(seasons) == 1:  # list products if there's only one season
        list_products(seasons[0]['_links']['self']['href'])
    else:
        for season in seasons:
            title = helper.language(30014).format(season['title'])
            helper.add_item(title, plugin.url_for(list_products, url=season['_links']['self']['href']))
        helper.eod()


@plugin.route('/categories')
def categories():
    categories_data = helper.vp.make_request(plugin.args['url'][0], 'get')['_links']['viaplay:categoryFilters']
    for i in categories_data:
        helper.add_item(i['title'], plugin.url_for(sortings, url=i['href']))
    helper.eod()


@plugin.route('/sortings')
def sortings():
    sortings_data = helper.vp.make_request(plugin.args['url'][0], 'get')['_links']['viaplay:sortings']
    for i in sortings_data:
        helper.add_item(i['title'], plugin.url_for(list_products, url=i['href']))
    helper.eod()


@plugin.route('/play')
def play():
    helper.play(guid=plugin.args['guid'][0], url=plugin.args['url'][0], tve=plugin.args['tve'][0])


@plugin.route('/dialog')
def dialog():
    helper.dialog(dialog_type=plugin.args['dialog_type'][0],
                  heading=plugin.args['heading'][0],
                  message=plugin.args['message'][0])


@plugin.route('/ia_settings')
def ia_settings():
    helper.ia_settings()


def add_movie(movie):
    if movie['system'].get('guid'):
        guid = movie['system']['guid']
        url = None
    else:
        guid = None
        url = movie['_links']['self']['href']

    plugin_url = plugin.url_for(play, guid=guid, url=url, tve='false')
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

    helper.add_item(movie_info['title'], plugin_url, info=movie_info, art=add_art(details['images'], 'movie'),
                    content='movies', playable=True)


def add_series(show):
    plugin_url = plugin.url_for(seasons_page, url=show['_links']['viaplay:page']['href'])
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

    helper.add_item(series_info['title'], plugin_url, folder=True, info=series_info,
                    art=add_art(details['images'], 'series'), content='tvshows')


def add_episode(episode):
    plugin_url = plugin.url_for(play, guid=episode['system']['guid'], url=None, tve='false')
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

    helper.add_item(episode_info['list_title'], plugin_url, info=episode_info,
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

    if event_status != 'upcoming':
        plugin_url = plugin.url_for(play, guid=event['system']['guid'], url=None, tve='false')
        playable = True
    else:
        plugin_url = plugin.url_for(dialog, dialog_type='ok',
                             heading=helper.language(30017),
                             message=helper.language(30016).format(start_time))
        playable = False

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

    helper.add_item(event_info['list_title'], plugin_url, playable=playable, info=event_info,
                    art=add_art(details['images'], 'sport'), content='episodes')


def add_tv_event(event):
    now = datetime.now()
    date_today = now.date()
    start_time_obj = helper.vp.parse_datetime(event['epg']['startTime'], localize=True)
    event_status = helper.vp.get_event_status(event)

    # hide non-available catchup items
    if now > helper.vp.parse_datetime(event['system']['catchupAvailability']['end'], localize=True):
        return
    if date_today == start_time_obj.date():
        start_time = '{0} {1}'.format(helper.language(30027), start_time_obj.strftime('%H:%M'))
    else:
        start_time = start_time_obj.strftime('%Y-%m-%d %H:%M')

    if event_status != 'upcoming':
        plugin_url = plugin.url_for(play, guid=event['system']['guid'], url=None, tve='true')
        playable = True
    else:
        plugin_url = plugin.url_for(dialog, dialog_type='ok',
                             heading=helper.language(30017),
                             message=helper.language(30016).format(start_time))
        playable = False

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

    helper.add_item(event_info['list_title'], plugin_url, playable=playable, info=event_info, art=art, content='episodes')


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
            if content_type != 'sport':
                artwork['poster'] = image_url
        elif i == 'coverart169':
            artwork['cover'] = image_url
        elif i == 'boxart':
            if content_type != 'episode' or content_type != 'sport':
                artwork['thumb'] = image_url

    return artwork


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
