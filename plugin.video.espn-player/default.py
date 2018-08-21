# -*- coding: utf-8 -*-
"""
A Kodi plugin for ESPN Player
"""
import sys
import os
import urllib
import urlparse
import re
from datetime import datetime

from resources.lib.espnlib import espnlib

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
cookie_file = os.path.join(addon_profile, 'cookie_file')

if addon.getSetting('debug') == 'false':
    debug = False
else:
    debug = True

if addon.getSetting('verify_ssl') == 'false':
    verify_ssl = False
else:
    verify_ssl = True

espn = espnlib(cookie_file, debug, verify_ssl)


def addon_log(string):
    if debug:
        xbmc.log('%s: %s' % (logging_prefix, string))


def services_menu():
    services = espn.get_services()
    if len(services) == 1:
        # list main menu directly if one service is found
        main_menu(services.values()[0])
    else:
        for name, service in services.items():
            parameters = {'action': 'main_menu', 'service': service}
            add_item(name, parameters)
        xbmcplugin.endOfDirectory(_handle)


def main_menu(service):
    listing = []
    items = [language(30018), language(30016), language(30017), language(30019)]

    for item in items:
        if item == language(30018):
            parameters = {'action': 'list_today', 'service': service}
        elif item == language(30019):
            parameters = {'action': 'list_channels', 'service': service}
        else:
            if item == language(30016):
                day = 'upcoming'
            else:
                day = 'archive'
            parameters = {'action': 'list_dates', 'service': service, 'day': day}

        add_item(item, parameters)
    xbmcplugin.endOfDirectory(_handle)


def list_today(service):
    now = datetime.now()
    date_today = now.date()
    items = [language(30015), language(30016), language(30017)]

    for item in items:
        if item == language(30015):
            parameters = {'action': 'list_games', 'filter_games': 'inplay', 'service': service, 'filter_date': 'false'}
        else:
            if item == language(30016):
                game_type = 'upcoming'
            else:
                game_type = 'archive'
            parameters = {'action': 'list_games', 'service': service, 'filter_date': date_today,
                          'filter_games': game_type}

        add_item(item, parameters)
    xbmcplugin.endOfDirectory(_handle)


def list_dates(service, day):
    dates = espn.get_gamedates(service, day)
    for date in dates:
        title = date.strftime('%Y-%m-%d')
        parameters = {'action': 'list_games', 'service': service, 'filter_date': date, 'filter_games': 'false'}
        add_item(title, parameters)
    xbmcplugin.endOfDirectory(_handle)


def list_games(service, filter_date, filter_games):
    items = []
    if filter_date == 'false':
        filter_date = False
    if filter_games == 'false':
        filter_games = False

    games = espn.get_games(service, filter_date=filter_date, filter_games=filter_games)

    for game in games:
        team_names = True
        game_datetime = espn.parse_datetime(game['dateTimeGMT'], localize=True)
        time = game_datetime.strftime('%H:%M')
        time_and_date = game_datetime.strftime('%Y-%m-%d %H:%M')
        category = game['sportId']

        try:
            home_team = '%s' % (game['homeTeam']['name'])
            away_team = '%s' % (game['awayTeam']['name'])
        except KeyError:
            # try to extract team names from full title
            teampattern = re.search(r'(.+)( vs. )(.+)( \()', game['name'])
            if teampattern:
                home_team = teampattern.group(3)
                away_team = teampattern.group(1)
            else:
                team_names = False

        if 'availablePrograms' not in game:
            playable = False
            parameters = {'action': 'null'}
        else:
            playable = True
            parameters = {'action': 'play_video', 'airingId': game['statsId']}

        if team_names:
            title = '[B]%s[/B] vs. [B]%s[/B]' % (away_team, home_team)
            list_title = '[B]%s[/B] %s: [B]%s[/B] vs. [B]%s[/B]' % (coloring(time, 'time'), coloring(category, 'cat'), away_team, home_team)

        else:
            title = '[B]%s[/B]' % game['name']
            list_title = '[B]%s[/B] %s: [B]%s[/B]' % (coloring(time, 'time'), coloring(category, 'cat'), game['name'])

        game_image = game['image'].split('.jpg')[0] + '.jpg'

        art = {
            'thumb': game_image,
            'fanart': game_image,
            'cover': game_image,
        }

        info = {
            'title': title,
            'genre': category,
            'plot': game['name']
        }

        items = add_item(list_title, parameters, items=items, playable=playable, folder=False, set_art=art,
                         set_info=info)
    xbmcplugin.addDirectoryItems(_handle, items, len(items))
    xbmcplugin.endOfDirectory(_handle)


def coloring(text, meaning):
    """Return the text wrapped in appropriate color markup."""
    if meaning == 'cat':
        color = 'FF0DF214'
    elif meaning == 'time':
        color = 'FFF16C00'
    colored_text = '[COLOR=%s]%s[/COLOR]' % (color, text)
    return colored_text


def list_channels(service):
    """List all channels from the returned dict."""
    channels = espn.get_channels(service)

    for name, channel_id in channels.items():
        listitem = xbmcgui.ListItem(label=name)
        listitem.setProperty('IsPlayable', 'true')
        art = {'thumb': 'http://a.espncdn.com/prod/assets/watchespn/appletv/images/channels-carousel/%s.png' % channel_id}
        # airingId is seoName for live channels
        parameters = {'action': 'play_channel', 'airingId': channel_id, 'channel': channel_id}
        add_item(name, parameters, playable=True, set_art=art)
    xbmcplugin.endOfDirectory(_handle)


def play_video(airingId, channel=None):
    try:
      espn.login(username, password)
    except espn.LoginFailure:
      addon_log('login failed')
      dialog = xbmcgui.Dialog()
      dialog.ok(language(30005),
                language(30006))

    if channel:
        stream_url = espn.get_stream_url(airingId, channel)
    else:
        stream_url = espn.get_stream_url(airingId)
    if stream_url['bitrates']:
        bitrate = select_bitrate(stream_url['bitrates'].keys())
        if bitrate:
            play_url = stream_url['bitrates'][bitrate]
            playitem = xbmcgui.ListItem(path=play_url)
            playitem.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(_handle, True, listitem=playitem)
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok(language(30005), language(30013))


def ask_bitrate(bitrates):
    """Presents a dialog for user to select from a list of bitrates.
    Returns the value of the selected bitrate."""
    options = []
    for bitrate in bitrates:
        options.append(bitrate + ' Kbps')
    dialog = xbmcgui.Dialog()
    ret = dialog.select(language(30010), options)
    if ret > -1:
        return bitrates[ret]


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
        return ask_bitrate(manifest_bitrates)


def add_item(title, parameters, items=False, folder=True, playable=False, set_info=False, set_art=False,
             watched=False, set_content=False):
    listitem = xbmcgui.ListItem(label=title)
    if playable:
        listitem.setProperty('IsPlayable', 'true')
        folder = False
    if set_art:
        listitem.setArt(set_art)
    else:
        listitem.setArt({'icon': os.path.join(addon_path, 'icon.png')})
        listitem.setArt({'fanart': os.path.join(addon_path, 'fanart.jpg')})
    if set_info:
        listitem.setInfo('video', set_info)
    if not watched:
        listitem.addStreamInfo('video', {'duration': 0})
    if set_content:
        xbmcplugin.setContent(_handle, set_content)

    listitem.setContentLookup(False)  # allows sending custom headers/cookies to ffmpeg
    recursive_url = _url + '?' + urllib.urlencode(parameters)

    if items is False:
        xbmcplugin.addDirectoryItem(_handle, recursive_url, listitem, folder)
    else:
        items.append((recursive_url, listitem, folder))
        return items


def router(paramstring):
    """Router function that calls other functions depending on the provided paramstring."""
    params = dict(urlparse.parse_qsl(paramstring))
    if params:
        if params['action'] == 'main_menu':
            main_menu(params['service'])
        elif params['action'] == 'list_channels':
            list_channels(params['service'])
        elif params['action'] == 'list_games':
            list_games(params['service'], params['filter_date'], params['filter_games'])
            addon_log(params)
        elif params['action'] == 'play_video':
            play_video(params['airingId'])
        elif params['action'] == 'play_channel':
            play_video(params['airingId'], params['channel'])
        elif params['action'] == 'list_dates':
            list_dates(params['service'], params['day'])
        elif params['action'] == 'list_today':
            list_today(params['service'])

    else:
        try:
            espn.login(username, password)
            services_menu()
        except espn.LoginFailure:
            addon_log('login failed')
            dialog = xbmcgui.Dialog()
            dialog.ok(language(30005),
                      language(30006))

            sys.exit(0)


if __name__ == '__main__':
    router(sys.argv[2][1:])  # trim the leading '?' from the plugin call paramstring
