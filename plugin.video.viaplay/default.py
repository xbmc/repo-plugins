# -*- coding: utf-8 -*-
"""
A Kodi plugin for Viaplay
"""
import sys
import os
import urllib
import urlparse
from datetime import datetime
import time

import dateutil.parser
from dateutil import tz

from resources.lib.vialib import vialib

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon()
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
tempdir = os.path.join(addon_profile, 'tmp')
language = addon.getLocalizedString
logging_prefix = '[%s-%s]' % (addon.getAddonInfo('id'), addon.getAddonInfo('version'))

if not xbmcvfs.exists(addon_profile):
    xbmcvfs.mkdir(addon_profile)
if not xbmcvfs.exists(tempdir):
    xbmcvfs.mkdir(tempdir)

_url = sys.argv[0]  # get the plugin url in plugin:// notation
_handle = int(sys.argv[1])  # get the plugin handle as an integer number

username = addon.getSetting('email')
password = addon.getSetting('password')
cookie_file = os.path.join(addon_profile, 'cookie_file')
deviceid_file = os.path.join(addon_profile, 'deviceId')

if addon.getSetting('disable_ssl') == 'true':
    ssl = False
else:
    ssl = True

if addon.getSetting('debug') == 'false':
    debug = False
else:
    debug = True

if addon.getSetting('country') == '0':
    country = 'se'
elif addon.getSetting('country') == '1':
    country = 'dk'
elif addon.getSetting('country') == '2':
    country = 'no'
else:
    country = 'fi'

vp = vialib(username, password, cookie_file, deviceid_file, tempdir, country, ssl, debug)


def addon_log(string):
    if debug:
        xbmc.log("%s: %s" % (logging_prefix, string))


def display_auth_message(error):
    if error.value == 'UserNotAuthorizedForContentError':
        message = language(30020)
    elif error.value == 'PurchaseConfirmationRequiredError':
        message = language(30021)
    elif error.value == 'UserNotAuthorizedRegionBlockedError':
        message = language(30022)
    else:
        message = error.value
    dialog = xbmcgui.Dialog()
    dialog.ok(language(30017), message)


def root_menu():
    data = vp.make_request(url=vp.base_url, method='get')
    categories = vp.get_categories(input=data, method='data')
    listing = []

    for category in categories:
        categorytype = category['type']
        videotype = category['name']
        title = category['title']
        if categorytype != 'editorial':
            listitem = xbmcgui.ListItem(label=title)
            listitem.setProperty('IsPlayable', 'false')
            listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
            listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
            if videotype == 'series':
                parameters = {'action': 'series_menu', 'url': category['href']}
            elif videotype == 'movie' or videotype == 'rental':
                parameters = {'action': 'movies_menu', 'url': category['href']}
            elif videotype == 'sport':
                parameters = {'action': 'sports_menu', 'url': category['href']}
            elif videotype == 'kids':
                parameters = {'action': 'kids_menu', 'url': category['href']}
            else:
                addon_log('Unsupported videotype found: %s' % videotype)
                parameters = {'action': 'showmessage', 'message': 'This type (%s) is not yet supported.' % videotype}
            recursive_url = _url + '?' + urllib.urlencode(parameters)
            is_folder = True
            listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    list_search(data)
    xbmcplugin.endOfDirectory(_handle)


def movies_menu(url):
    categories = vp.get_categories(url)
    listing = []

    for category in categories:
        title = category['title']
        listitem = xbmcgui.ListItem(label=title)
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        parameters = {'action': 'sortings_menu', 'url': category['href']}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def series_menu(url):
    categories = vp.get_categories(url)
    listing = []

    for category in categories:
        title = category['title']
        listitem = xbmcgui.ListItem(label=title)
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        parameters = {'action': 'sortings_menu', 'url': category['href']}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def kids_menu(url):
    categories = vp.get_categories(url)
    listing = []

    for category in categories:
        title = '%s: %s' % (category['group']['title'].title(), category['title'])
        listitem = xbmcgui.ListItem(label=title)
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        parameters = {'action': 'list_products', 'url': category['href']}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def sortings_menu(url):
    sortings = vp.get_sortings(url)
    listing = []

    for sorting in sortings:
        title = sorting['title']
        listitem = xbmcgui.ListItem(label=title)
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        try:
            if sorting['id'] == 'alphabetical':
                parameters = {'action': 'alphabetical_letters_menu', 'url': sorting['href']}
            else:
                parameters = {'action': 'list_products', 'url': sorting['href']}
        except TypeError:
            parameters = {'action': 'list_products', 'url': sorting['href']}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))

    list_products_alphabetical(url)
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def list_products_alphabetical(url):
    """List all products in alphabetical order."""
    listitem = xbmcgui.ListItem(label=language(30013))
    listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
    listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
    parameters = {'action': 'list_products', 'url': url + '?sort=alphabetical'}
    recursive_url = _url + '?' + urllib.urlencode(parameters)
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, recursive_url, listitem, is_folder)


def alphabetical_letters_menu(url):
    letters = vp.get_letters(url)
    listing = []

    for letter in letters:
        title = letter.encode('utf-8')
        if letter == '0-9':
            # 0-9 needs to be sent as a pound-sign
            letter = '#'
        else:
            letter = title.lower()
        listitem = xbmcgui.ListItem(label=title)
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        parameters = {'action': 'list_products', 'url': url + '&letter=' + urllib.quote(letter)}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def list_next_page(data):
    if vp.get_next_page(data):
        listitem = xbmcgui.ListItem(label=language(30018))
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        parameters = {'action': 'list_products', 'url': vp.get_next_page(data)}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, recursive_url, listitem, is_folder)


def list_products(url, *display):
    data = vp.make_request(url=url, method='get')
    products = vp.get_products(input=data, method='data')
    listing = []
    sort = None

    for item in products:
        type = item['type']
        try:
            playid = item['system']['guid']
            streamtype = 'guid'
        except KeyError:
            """The guid is not always available from the category listing.
            Send the self URL and let play_video grab the guid from there instead
            as it always provides more detailed data about each product."""
            playid = item['_links']['self']['href']
            streamtype = 'url'
        parameters = {'action': 'play_video', 'playid': playid.encode('utf-8'), 'streamtype': streamtype,
                      'content': type}
        recursive_url = _url + '?' + urllib.urlencode(parameters)

        if type == 'episode':
            title = item['content']['series']['episodeTitle']
            is_folder = False
            is_playable = 'true'
            listitem = xbmcgui.ListItem(label=title)
            listitem.setProperty('IsPlayable', is_playable)
            listitem.setInfo('video', item_information(item))
            listitem.setArt(art(item))
            listing.append((recursive_url, listitem, is_folder))

        if type == 'sport':
            local_tz = tz.tzlocal()
            startdate_utc = dateutil.parser.parse(item['epg']['start'])
            startdate_local = startdate_utc.astimezone(local_tz)
            status = vp.get_sports_status(item)
            if status == 'archive':
                title = 'Archive: %s' % item['content']['title'].encode('utf-8')
                is_playable = 'true'
            else:
                title = '%s (%s)' % (item['content']['title'].encode('utf-8'), startdate_local.strftime("%H:%M"))
                is_playable = 'true'
            if status == 'upcoming':
                parameters = {'action': 'showmessage',
                              'message': '%s %s.' % (language(30016), startdate_local.strftime("%Y-%m-%d %H:%M"))}
                recursive_url = _url + '?' + urllib.urlencode(parameters)
                is_playable = 'false'
            is_folder = False
            listitem = xbmcgui.ListItem(label=title)
            listitem.setProperty('IsPlayable', is_playable)
            listitem.setInfo('video', item_information(item))
            listitem.setArt(art(item))
            if 'live' in display:
                if status == 'live':
                    listing.append((recursive_url, listitem, is_folder))
            elif 'upcoming' in display:
                if status == 'upcoming':
                    listing.append((recursive_url, listitem, is_folder))
            elif 'archive' in display:
                if status == 'archive':
                    listing.append((recursive_url, listitem, is_folder))
            else:
                listing.append((recursive_url, listitem, is_folder))

        elif type == 'movie':
            title = '%s (%s)' % (item['content']['title'].encode('utf-8'), str(item['content']['production']['year']))
            if item['system']['availability']['planInfo']['isRental'] is True:
                title = title + ' *'  # mark rental products with an asterisk
            is_folder = False
            is_playable = 'true'
            listitem = xbmcgui.ListItem(label=title)
            listitem.setProperty('IsPlayable', is_playable)
            listitem.setInfo('video', item_information(item))
            listitem.setArt(art(item))
            listing.append((recursive_url, listitem, is_folder))

        elif type == 'series':
            title = item['content']['series']['title'].encode('utf-8')
            self_url = item['_links']['viaplay:page']['href']
            parameters = {'action': 'list_seasons', 'url': self_url}
            recursive_url = _url + '?' + urllib.urlencode(parameters)
            is_folder = True
            is_playable = 'false'
            listitem = xbmcgui.ListItem(label=title)
            listitem.setProperty('IsPlayable', is_playable)
            listitem.setInfo('video', item_information(item))
            listitem.setArt(art(item))
            listing.append((recursive_url, listitem, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    if sort is True:
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    list_next_page(data)
    # xbmc.executebuiltin("Container.SetViewMode(500)") - force media view
    xbmcplugin.endOfDirectory(_handle)


def list_seasons(url):
    """List all series seasons."""
    seasons = vp.get_seasons(url)
    if len(seasons) == 1:
        # list products if there's only one season
        season_url = seasons[0]['_links']['self']['href']
        list_products(season_url)
    else:
        listing = []
        for season in seasons:
            season_url = season['_links']['self']['href']
            title = '%s %s' % (language(30014), season['title'])
            listitem = xbmcgui.ListItem(label=title)
            listitem.setProperty('IsPlayable', 'false')
            listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
            listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
            parameters = {'action': 'list_products', 'url': season_url}
            recursive_url = _url + '?' + urllib.urlencode(parameters)
            is_folder = True
            listing.append((recursive_url, listitem, is_folder))
        xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
        xbmcplugin.endOfDirectory(_handle)


def item_information(item):
    """Return the product information in a xbmcgui.setInfo friendly dict.
    Supported content types: episode, series, movie, sport"""
    type = item['type']
    mediatype = None
    title = None
    tvshowtitle = None
    season = None
    episode = None
    plot = None
    director = None
    cast = []
    try:
        duration = int(item['content']['duration']['milliseconds']) / 1000
    except KeyError:
        duration = None
    try:
        imdb_code = item['content']['imdb']['id']
    except KeyError:
        imdb_code = None
    try:
        rating = float(item['content']['imdb']['rating'])
    except KeyError:
        rating = None
    try:
        votes = str(item['content']['imdb']['votes'])
    except KeyError:
        votes = None
    try:
        year = int(item['content']['production']['year'])
    except KeyError:
        year = None
    try:
        genres = []
        for genre in item['_links']['viaplay:genres']:
            genres.append(genre['title'])
        genre = ', '.join(genres)
    except KeyError:
        genre = None
    try:
        mpaa = item['content']['parentalRating']
    except KeyError:
        mpaa = None

    if type == 'episode':
        mediatype = 'episode'
        title = item['content']['series']['episodeTitle'].encode('utf-8')
        tvshowtitle = item['content']['series']['title'].encode('utf-8')
        season = int(item['content']['series']['season']['seasonNumber'])
        episode = int(item['content']['series']['episodeNumber'])
        plot = item['content']['synopsis'].encode('utf-8')
        xbmcplugin.setContent(_handle, 'episodes')
    elif type == 'series':
        mediatype = 'tvshow'
        title = item['content']['series']['title'].encode('utf-8')
        tvshowtitle = item['content']['series']['title'].encode('utf-8')
        try:
            plot = item['content']['series']['synopsis'].encode('utf-8')
        except KeyError:
            plot = item['content']['synopsis'].encode('utf-8')  # needed for alphabetical listing
        xbmcplugin.setContent(_handle, 'tvshows')
    elif type == 'movie':
        mediatype = 'movie'
        title = item['content']['title'].encode('utf-8')
        plot = item['content']['synopsis'].encode('utf-8')
        try:
            for actor in item['content']['people']['actors']:
                cast.append(actor)
        except KeyError:
            pass
        try:
            directors = []
            for director in item['content']['people']['directors']:
                directors.append(director)
            director = ', '.join(directors)
        except KeyError:
            pass
        xbmcplugin.setContent(_handle, 'movies')
    elif type == 'sport':
        mediatype = 'video'
        title = item['content']['title'].encode('utf-8')
        plot = item['content']['synopsis'].encode('utf-8')
        xbmcplugin.setContent(_handle, 'episodes')
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


def art(item):
    """Return the available art in a xbmcgui.setArt friendly dict."""
    type = item['type']
    try:
        boxart = item['content']['images']['boxart']['url'].split('.jpg')[0] + '.jpg'
    except KeyError:
        boxart = None
    try:
        hero169 = item['content']['images']['hero169']['template'].split('.jpg')[0] + '.jpg'
    except KeyError:
        hero169 = None
    try:
        coverart23 = item['content']['images']['coverart23']['template'].split('.jpg')[0] + '.jpg'
    except KeyError:
        coverart23 = None
    try:
        coverart169 = item['content']['images']['coverart23']['template'].split('.jpg')[0] + '.jpg'
    except KeyError:
        coverart169 = None
    try:
        landscape = item['content']['images']['landscape']['url'].split('.jpg')[0] + '.jpg'
    except KeyError:
        landscape = None

    if type == 'episode' or type == 'sport':
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
    listitem = xbmcgui.ListItem(label=data['_links']['viaplay:search']['title'])
    listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
    listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
    parameters = {'action': 'search', 'url': data['_links']['viaplay:search']['href']}
    recursive_url = _url + '?' + urllib.urlencode(parameters)
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, recursive_url, listitem, is_folder)


def get_userinput(title):
    query = None
    keyboard = xbmc.Keyboard('', title)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
        addon_log('User input string: %s' % query)
    return query


def search(url):
    try:
        query = get_userinput(language(30015))
        if len(query) > 0:
            url = '%s?query=%s' % (url, urllib.quote(query))
            list_products(url)
    except TypeError:
        pass


def play_video(input, streamtype, content):
    if streamtype == 'url':
        url = input
        guid = vp.get_products(input=url, method='url')['system']['guid']
    else:
        guid = input

    try:
        video_urls = vp.get_video_urls(guid)
    except vp.AuthFailure as error:
        video_urls = False
        display_auth_message(error)
    except vp.LoginFailure:
        video_urls = False
        dialog = xbmcgui.Dialog()
        dialog.ok(language(30005),
                  language(30006))

    if video_urls:
        if content == 'sport':
            # sports uses HLS v4 so we can't parse the manifest as audio is supplied externally
            stream_url = video_urls['manifest_url']
            playitem = xbmcgui.ListItem(path=stream_url)
            playitem.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(_handle, True, listitem=playitem)
        else:
            bitrate = select_bitrate(video_urls['bitrates'].keys())
            if bitrate:
                stream_url = video_urls['bitrates'][bitrate]
                playitem = xbmcgui.ListItem(path=stream_url)
                playitem.setProperty('IsPlayable', 'true')
                if addon.getSetting('subtitles') == 'true':
                    playitem.setSubtitles(vp.download_subtitles(video_urls['subtitle_urls']))
                xbmcplugin.setResolvedUrl(_handle, True, listitem=playitem)


def sports_menu(url):
    listing = []
    categories = vp.get_categories(url)
    now = datetime.now()

    for category in categories:
        date_object = datetime(
            *(time.strptime(category['date'], '%Y-%m-%d')[0:6]))  # http://forum.kodi.tv/showthread.php?tid=112916
        title = category['date']
        listitem = xbmcgui.ListItem(label=title)
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        if date_object.date() == now.date():
            parameters = {'action': 'sports_today_menu', 'url': category['href']}
        else:
            parameters = {'action': 'list_products', 'url': category['href']}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def sports_today_menu(url):
    types = ['live', 'upcoming', 'archive']
    listing = []
    for type in types:
        listitem = xbmcgui.ListItem(label=type.title())
        listitem.setProperty('IsPlayable', 'false')
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
        parameters = {'action': 'list_products_sports_today', 'url': url, 'display': type}
        recursive_url = _url + '?' + urllib.urlencode(parameters)
        is_folder = True
        listing.append((recursive_url, listitem, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def ask_bitrate(bitrates):
    """Presents a dialog for user to select from a list of bitrates.
    Returns the value of the selected bitrate."""
    options = []
    for bitrate in bitrates:
        options.append(bitrate + ' Kbps')
    dialog = xbmcgui.Dialog()
    ret = dialog.select(language(30026), options)
    if ret > -1:
        return bitrates[ret]


def select_bitrate(manifest_bitrates=None):
    """Returns a bitrate while honoring the user's preference."""
    bitrate_setting = int(addon.getSetting('preferred_bitrate'))
    if bitrate_setting == 0:
        preferred_bitrate = 'highest'
    else:
        preferred_bitrate = 'ask'

    manifest_bitrates.sort(key=int, reverse=True)
    if preferred_bitrate == 'highest':
        return manifest_bitrates[0]
    else:
        return ask_bitrate(manifest_bitrates)


def router(paramstring):
    """Router function that calls other functions depending on the provided paramstring."""
    params = dict(urlparse.parse_qsl(paramstring))
    if params:
        if params['action'] == 'movies_menu':
            movies_menu(params['url'])
        elif params['action'] == 'kids_menu':
            kids_menu(params['url'])
        elif params['action'] == 'series_menu':
            series_menu(params['url'])
        elif params['action'] == 'sports_menu':
            sports_menu(params['url'])
        elif params['action'] == 'list_seasons':
            list_seasons(params['url'])
        elif params['action'] == 'list_products':
            list_products(params['url'])
        elif params['action'] == 'sports_today_menu':
            sports_today_menu(params['url'])
        elif params['action'] == 'list_products_sports_today':
            list_products(params['url'], params['display'])
        elif params['action'] == 'play_video':
            play_video(params['playid'], params['streamtype'], params['content'])
        elif params['action'] == 'sortings_menu':
            sortings_menu(params['url'])
        elif params['action'] == 'alphabetical_letters_menu':
            alphabetical_letters_menu(params['url'])
        elif params['action'] == 'search':
            search(params['url'])
        elif params['action'] == 'showmessage':
            dialog = xbmcgui.Dialog()
            dialog.ok(language(30017),
                      params['message'])
    else:
        root_menu()


if __name__ == '__main__':
    router(sys.argv[2][1:])  # trim the leading '?' from the plugin call paramstring
