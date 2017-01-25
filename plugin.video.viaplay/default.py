# -*- coding: utf-8 -*-
"""
A Kodi add-on for Viaplay
"""
import sys
import os
import urllib
import urlparse
from datetime import datetime

from resources.lib.vialib import vialib

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon()
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
language = addon.getLocalizedString
logging_prefix = '[%s-%s]' % (addon.getAddonInfo('id'), addon.getAddonInfo('version'))

if not xbmcvfs.exists(addon_profile):
    xbmcvfs.mkdir(addon_profile)

_url = sys.argv[0]  # get the plugin url in plugin:// notation
_handle = int(sys.argv[1])  # get the plugin handle as an integer number

username = addon.getSetting('email')
password = addon.getSetting('password')

if addon.getSetting('country') == '0':
    country = 'se'
elif addon.getSetting('country') == '1':
    country = 'dk'
elif addon.getSetting('country') == '2':
    country = 'no'
else:
    country = 'fi'

vp = vialib(username, password, addon_profile, country, debug=True)


def addon_log(string):
    msg = '%s: %s' % (logging_prefix, string)
    xbmc.log(msg=msg, level=xbmc.LOGDEBUG)


def main_menu():
    items = []
    data = vp.make_request(url=vp.base_url, method='get')
    categories = vp.get_categories(input=data, method='data')

    for category in categories:
        category_name = category['name']
        title = category['title']
        if category['type'] != 'editorial':
            if category_name == 'sport':
                parameters = {
                    'action': 'sports_menu',
                    'url': category['href']
                }
            else:
                parameters = {
                    'action': 'list_categories',
                    'url': category['href'],
                    'category_name': category_name
                }

            items = add_item(title, parameters, items=items)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    list_search(data)
    xbmcplugin.endOfDirectory(_handle)


def list_categories(url, category_name):
    items = []
    categories = vp.get_categories(url)

    for category in categories:
        if category_name == 'kids':
            title = '%s: %s' % (category['group']['title'].title(), category['title'])
        else:
            title = category['title']

        parameters = {
            'action': 'list_sortings',
            'url': category['href']
        }
        items = add_item(title, parameters, items=items)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def list_sortings(url):
    items = []
    sortings = vp.get_sortings(url)
    if sortings:
        for sorting in sortings:
            title = sorting['title']
            sorting_url = sorting['href']
            try:
                if sorting['id'] == 'alphabetical':
                    parameters = {
                        'action': 'list_alphabetical_letters',
                        'url': sorting_url
                    }
                else:
                    parameters = {
                        'action': 'list_products',
                        'url': sorting_url
                    }
            except TypeError:
                parameters = {
                    'action': 'list_products',
                    'url': sorting_url
                }

            items = add_item(title, parameters, items=items)
        list_products_alphabetical(url)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def list_products_alphabetical(url):
    """List all products in alphabetical order."""
    title = language(30013)
    parameters = {
        'action': 'list_products',
        'url': url + '?sort=alphabetical'
    }

    add_item(title, parameters)


def list_alphabetical_letters(url):
    items = []
    letters = vp.get_letters(url)

    for letter in letters:
        if letter == '0-9':
            query = '#'  # 0-9 needs to be sent as a number sign
        else:
            query = letter.lower()

        parameters = {
            'action': 'list_products',
            'url': url + '&letter=' + urllib.quote(query)
        }

        items = add_item(letter, parameters, items=items)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def list_next_page(data):
    if vp.get_next_page(data):
        title = language(30018)
        parameters = {
            'action': 'list_products',
            'url': vp.get_next_page(data)
        }

        add_item(title, parameters)


def list_products(url, filter_event=False):
    items = []
    data = vp.make_request(url=url, method='get')
    if filter_event:
        filter_event = filter_event.split(', ')

    products = vp.get_products(input=data, method='data', filter_event=filter_event)

    for product in products:
        content = product['type']
        try:
            playid = product['system']['guid']
            streamtype = 'guid'
        except KeyError:
            """The guid is not always available from the category listing.
            Send the self URL and let play_video grab the guid from there instead
            as it always provides more detailed data about each product."""
            playid = product['_links']['self']['href']
            streamtype = 'url'

        parameters = {
            'action': 'play_video',
            'playid': playid.encode('utf-8'),
            'streamtype': streamtype,
            'content': content
        }

        if content == 'episode':
            title = product['content']['series']['episodeTitle']
            playable = True
            watched = True
            set_content = 'episodes'

        elif content == 'sport':
            now = datetime.now()
            date_today = now.date()
            product_name = unicode(product['content']['title'])

            if date_today == product['event_date'].date():
                start_time = '%s %s' % (language(30027), product['event_date'].strftime('%H:%M'))
            else:
                start_time = product['event_date'].strftime('%Y-%m-%d %H:%M')

            title = '[B]%s:[/B] %s' % (coloring(start_time, product['event_status']), product_name)

            if product['event_status'] == 'upcoming':
                parameters = {
                    'action': 'dialog',
                    'dialog_type': 'ok',
                    'heading': language(30017),
                    'message': '%s [B]%s[/B].' % (language(30016), start_time)
                }
                playable = False
            else:
                playable = True

            watched = False
            set_content = 'movies'

        elif content == 'movie':
            movie_name = product['content']['title'].encode('utf-8')
            movie_year = str(product['content']['production']['year'])
            title = '%s (%s)' % (movie_name, movie_year)

            if product['system']['availability']['planInfo']['isRental']:
                title = title + ' *'  # mark rental products with an asterisk

            playable = True
            watched = True
            set_content = 'movies'

        elif content == 'series':
            title = product['content']['series']['title'].encode('utf-8')
            season_url = product['_links']['viaplay:page']['href']
            parameters = {
                'action': 'list_seasons',
                'url': season_url
            }
            playable = False
            watched = True
            set_content = 'tvshows'

        items = add_item(title, parameters, items=items, playable=playable, watched=watched, set_content=set_content,
                         set_info=return_info(product, content), set_art=return_art(product, content))
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    list_next_page(data)
    xbmcplugin.endOfDirectory(_handle)


def list_seasons(url):
    """List all series seasons."""
    seasons = vp.get_seasons(url)
    if len(seasons) == 1:
        # list products if there's only one season
        season_url = seasons[0]['_links']['self']['href']
        list_products(season_url)
    else:
        items = []
        for season in seasons:
            season_url = season['_links']['self']['href']
            title = '%s %s' % (language(30014), season['title'])
            parameters = {
                'action': 'list_products',
                'url': season_url
            }

            items = add_item(title, parameters, items=items)
        xbmcplugin.addDirectoryItems(_handle, items, len(items))
        xbmcplugin.endOfDirectory(_handle)


def return_info(product, content):
    """Return the product information in a xbmcgui.setInfo friendly dict.
    Supported content types: episode, series, movie, sport"""
    cast = []
    mediatype = None
    title = None
    tvshowtitle = None
    season = None
    episode = None
    plot = None
    director = None
    try:
        duration = int(product['content']['duration']['milliseconds']) / 1000
    except KeyError:
        duration = None
    try:
        imdb_code = product['content']['imdb']['id']
    except KeyError:
        imdb_code = None
    try:
        rating = float(product['content']['imdb']['rating'])
    except KeyError:
        rating = None
    try:
        votes = str(product['content']['imdb']['votes'])
    except KeyError:
        votes = None
    try:
        year = int(product['content']['production']['year'])
    except KeyError:
        year = None
    try:
        genres = []
        for genre in product['_links']['viaplay:genres']:
            genres.append(genre['title'])
        genre = ', '.join(genres)
    except KeyError:
        genre = None
    try:
        mpaa = product['content']['parentalRating']
    except KeyError:
        mpaa = None

    if content == 'episode':
        mediatype = 'episode'
        title = product['content']['series']['episodeTitle'].encode('utf-8')
        tvshowtitle = product['content']['series']['title'].encode('utf-8')
        season = int(product['content']['series']['season']['seasonNumber'])
        episode = int(product['content']['series']['episodeNumber'])
        plot = product['content']['synopsis'].encode('utf-8')

    elif content == 'series':
        mediatype = 'tvshow'
        title = product['content']['series']['title'].encode('utf-8')
        tvshowtitle = product['content']['series']['title'].encode('utf-8')
        try:
            plot = product['content']['series']['synopsis'].encode('utf-8')
        except KeyError:
            plot = product['content']['synopsis'].encode('utf-8')  # needed for alphabetical listing

    elif content == 'movie':
        mediatype = 'movie'
        title = product['content']['title'].encode('utf-8')
        plot = product['content']['synopsis'].encode('utf-8')
        try:
            for actor in product['content']['people']['actors']:
                cast.append(actor)
        except KeyError:
            pass
        try:
            directors = []
            for director in product['content']['people']['directors']:
                directors.append(director)
            director = ', '.join(directors)
        except KeyError:
            pass

    elif content == 'sport':
        mediatype = 'video'
        title = product['content']['title'].encode('utf-8')
        plot = product['content']['synopsis'].encode('utf-8')

    info = {
        'mediatype': mediatype,
        'title': title,
        'tvshowtitle': tvshowtitle,
        'season': season,
        'episode': episode,
        'year': year,
        'plot': plot,
        'duration': duration,
        'code': imdb_code,
        'rating': rating,
        'votes': votes,
        'genre': genre,
        'director': director,
        'mpaa': mpaa,
        'cast': cast
    }

    return info


def return_art(product, content):
    """Return the available art in a xbmcgui.setArt friendly dict."""
    try:
        boxart = product['content']['images']['boxart']['url'].split('.jpg')[0] + '.jpg'
    except KeyError:
        boxart = None
    try:
        hero169 = product['content']['images']['hero169']['template'].split('.jpg')[0] + '.jpg'
    except KeyError:
        hero169 = None
    try:
        coverart23 = product['content']['images']['coverart23']['template'].split('.jpg')[0] + '.jpg'
    except KeyError:
        coverart23 = None
    try:
        coverart169 = product['content']['images']['coverart23']['template'].split('.jpg')[0] + '.jpg'
    except KeyError:
        coverart169 = None
    try:
        landscape = product['content']['images']['landscape']['url'].split('.jpg')[0] + '.jpg'
    except KeyError:
        landscape = None

    if content == 'episode' or content == 'sport':
        thumbnail = landscape
    else:
        thumbnail = boxart
    fanart = hero169
    banner = landscape
    cover = coverart23
    poster = boxart

    art = {
        'thumb': thumbnail,
        'fanart': fanart,
        'banner': banner,
        'cover': cover,
        'poster': poster
    }

    return art


def list_search(data):
    title = data['_links']['viaplay:search']['title']
    parameters = {
        'action': 'search',
        'url': data['_links']['viaplay:search']['href']
    }

    add_item(title, parameters)


def get_user_input(heading):
    keyboard = xbmc.Keyboard('', heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        user_input = keyboard.getText()
        addon_log('User input string: %s' % user_input)
    else:
        user_input = None

    if user_input and len(user_input) > 0:
        return user_input
    else:
        return None


def get_numeric_input(heading):
    dialog = xbmcgui.Dialog()
    numeric_input = dialog.numeric(0, heading)

    if len(numeric_input) > 0:
        return str(numeric_input)
    else:
        return None


def search(url):
    query = get_user_input(language(30015))
    if query:
        url = '%s?query=%s' % (url, urllib.quote(query))
        list_products(url)


def play_video(input, streamtype, content, pincode=None):
    if streamtype == 'url':
        url = input
        guid = vp.get_products(input=url, method='url')['system']['guid']
    else:
        guid = input

    try:
        video_urls = vp.get_video_urls(guid, pincode=pincode)
        if video_urls:
            if content == 'sport':
                # sports uses HLS v4 so we can't parse the manifest as audio is supplied externally
                stream_url = video_urls['manifest_url']
            else:
                bitrate = select_bitrate(video_urls['bitrates'].keys())
                if bitrate:
                    stream_url = video_urls['bitrates'][bitrate]
                else:
                    stream_url = False

            if stream_url:
                playitem = xbmcgui.ListItem(path=stream_url)
                playitem.setProperty('IsPlayable', 'true')
                if addon.getSetting('subtitles') == 'true':
                    playitem.setSubtitles(vp.download_subtitles(video_urls['subtitle_urls']))
                xbmcplugin.setResolvedUrl(_handle, True, listitem=playitem)
        else:
            dialog(dialog_type='ok', heading=language(30005), message=language(30038))

    except vp.AuthFailure as error:
        if error.value == 'ParentalGuidancePinChallengeNeededError':
            if pincode:
                dialog(dialog_type='ok', heading=language(30033), message=language(30034))
            else:
                pincode = get_numeric_input(language(30032))
                if pincode:
                    play_video(input, streamtype, content, pincode)
        else:
            show_auth_error(error.value)
    except vp.LoginFailure:
        dialog(dialog_type='ok', heading=language(30005), message=language(30006))


def sports_menu(url):
    items = []
    event_date = ['today', 'upcoming', 'archive']

    for date in event_date:
        if date == 'today':
            title = language(30027)
        elif date == 'upcoming':
            title = language(30028)
        else:
            title = language(30029)
        if date == 'today':
            parameters = {
                'action': 'list_sports_today',
                'url': url
            }
        else:
            parameters = {
                'action': 'list_sports_dates',
                'url': url,
                'event_date': date
            }

        items = add_item(title, parameters, items=items)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def list_sports_today(url):
    items = []
    event_status = [language(30037), language(30031)]
    for status in event_status:
        if status == language(30037):
            filter = 'live, upcoming'
        else:
            filter = 'archive'
        parameters = {
            'action': 'list_products_sports_today',
            'url': url,
            'filter_sports_event': filter
        }

        items = add_item(status, parameters, items=items)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def list_sports_dates(url, event_date):
    items = []
    dates = vp.get_sports_dates(url, event_date)
    for date in dates:
        title = date['date']
        parameters = {
            'action': 'list_products',
            'url': date['href']
        }

        items = add_item(title, parameters, items=items)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def ask_bitrate(bitrates):
    """Presents a dialog for user to select from a list of bitrates.
    Returns the value of the selected bitrate."""
    options = []
    for bitrate in bitrates:
        options.append(bitrate + ' Kbps')
    selected_bitrate = dialog('select', language(30026), options=options)
    if selected_bitrate is not None:
        return bitrates[selected_bitrate]
    else:
        return None


def select_bitrate(manifest_bitrates=None):
    """Returns a bitrate while honoring the user's preference."""
    bitrate_setting = int(addon.getSetting('preferred_bitrate'))
    if bitrate_setting == 0:
        preferred_bitrate = 'highest'
    elif bitrate_setting == 1:
        preferred_bitrate = 'limit'
    else:
        preferred_bitrate = 'ask'

    manifest_bitrates.sort(key=int, reverse=True)
    if preferred_bitrate == 'highest':
        return manifest_bitrates[0]
    elif preferred_bitrate == 'limit':
        allowed_bitrates = []
        max_bitrate_allowed = int(addon.getSetting('max_bitrate_allowed'))
        for bitrate in manifest_bitrates:
            if max_bitrate_allowed >= int(bitrate):
                allowed_bitrates.append(str(bitrate))
        if allowed_bitrates:
            return allowed_bitrates[0]
        else:
            addon_log('No bitrate in stream matched the maximum bitrate allowed.')
            return None
    else:
        return ask_bitrate(manifest_bitrates)


def dialog(dialog_type, heading, message=None, options=None, nolabel=None, yeslabel=None):
    dialog = xbmcgui.Dialog()
    if dialog_type == 'ok':
        dialog.ok(heading, message)
    elif dialog_type == 'yesno':
        return dialog.yesno(heading, message, nolabel=nolabel, yeslabel=yeslabel)
    elif dialog_type == 'select':
        ret = dialog.select(heading, options)
        if ret > -1:
            return ret
        else:
            return None


def add_item(title, parameters, items=False, folder=True, playable=False, set_info=False, set_art=False,
             watched=False, set_content=False):
    listitem = xbmcgui.ListItem(label=title)
    if playable:
        listitem.setProperty('IsPlayable', 'true')
        folder = False
    if set_art:
        listitem.setArt(set_art)
    else:
        listitem.setArt({'icon': os.path.join(addon_path, 'resources', 'art', 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'resources', 'art', 'fanart.jpg')})
    if set_info:
        listitem.setInfo('video', set_info)
    if not watched:
        listitem.addStreamInfo('video', {'duration': 0})
    if set_content:
        xbmcplugin.setContent(_handle, set_content)

    recursive_url = _url + '?' + urllib.urlencode(parameters)

    if items is False:
        xbmcplugin.addDirectoryItem(_handle, recursive_url, listitem, folder)
    else:
        items.append((recursive_url, listitem, folder))
        return items


def coloring(text, meaning):
    """Return the text wrapped in appropriate color markup."""
    if meaning == 'live':
        color = 'FF03F12F'
    elif meaning == 'upcoming':
        color = 'FFF16C00'
    elif meaning == 'archive':
        color = 'FFFF0EE0'
    colored_text = '[COLOR=%s]%s[/COLOR]' % (color, text)
    return colored_text


def show_auth_error(error):
    if error == 'UserNotAuthorizedForContentError':
        message = language(30020)
    elif error == 'PurchaseConfirmationRequiredError':
        message = language(30021)
    elif error == 'UserNotAuthorizedRegionBlockedError':
        message = language(30022)
    else:
        message = error

    dialog(dialog_type='ok', heading=language(30017), message=message)


def router(paramstring):
    """Router function that calls other functions depending on the provided paramstring."""
    params = dict(urlparse.parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_categories':
            list_categories(params['url'], params['category_name'])
        elif params['action'] == 'sports_menu':
            sports_menu(params['url'])
        elif params['action'] == 'list_seasons':
            list_seasons(params['url'])
        elif params['action'] == 'list_products':
            list_products(params['url'])
        elif params['action'] == 'list_sports_today':
            list_sports_today(params['url'])
        elif params['action'] == 'list_products_sports_today':
            list_products(params['url'], params['filter_sports_event'])
        elif params['action'] == 'play_video':
            play_video(params['playid'], params['streamtype'], params['content'])
        elif params['action'] == 'list_sortings':
            list_sortings(params['url'])
        elif params['action'] == 'list_alphabetical_letters':
            list_alphabetical_letters(params['url'])
        elif params['action'] == 'search':
            search(params['url'])
        elif params['action'] == 'list_sports_dates':
            list_sports_dates(params['url'], params['event_date'])
        elif params['action'] == 'dialog':
            dialog(params['dialog_type'], params['heading'], params['message'])
    else:
        main_menu()


if __name__ == '__main__':
    router(sys.argv[2][1:])  # trim the leading '?' from the plugin call paramstring
