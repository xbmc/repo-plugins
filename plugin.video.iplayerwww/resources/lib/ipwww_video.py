# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import re
import datetime
import time
import json

from datetime import timedelta
from operator import itemgetter

from resources.lib.ipwww_common import (
    translation, AddMenuEntry, OpenURL, OpenRequest, CheckLogin, CreateBaseDirectory,
    GetCookieJar, ParseImageUrl, download_subtitles, GeoBlockedError, WebRequestError,
    iso_duration_2_seconds, PostJson, strptime, addonid, DeleteUrl, ProgressDlg)
from resources.lib import ipwww_progress

import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
from random import randint

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')


def tp(path):
    return xbmcvfs.translatePath(path)


def RedButtonDialog():
    if ADDON.getSetting('redbutton_warning') == 'true':
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(translation(30405), translation(30406) + "\n" + translation(30407),
                           translation(30409), translation(30408))
        if ret:
            ListRedButton()
    else:
        ListRedButton()


def ListRedButton():
    channel_list = [
        ('sport_stream_01',  'BBC Red Button 1'),
        ('sport_stream_02',  'BBC Red Button 2'),
        ('sport_stream_03',  'BBC Red Button 3'),
        ('sport_stream_04',  'BBC Red Button 4'),
        ('sport_stream_05',  'BBC Red Button 5'),
        ('sport_stream_06',  'BBC Red Button 6'),
        ('sport_stream_07',  'BBC Red Button 7'),
        ('sport_stream_08',  'BBC Red Button 8'),
        ('sport_stream_09',  'BBC Red Button 9'),
        ('sport_stream_10',  'BBC Red Button 10'),
        ('sport_stream_11',  'BBC Red Button 11'),
        ('sport_stream_12',  'BBC Red Button 12'),
        ('sport_stream_13',  'BBC Red Button 13'),
        ('sport_stream_14',  'BBC Red Button 14'),
        ('sport_stream_15',  'BBC Red Button 15'),
        ('sport_stream_16',  'BBC Red Button 16'),
        ('sport_stream_17',  'BBC Red Button 17'),
        ('sport_stream_18',  'BBC Red Button 18'),
        ('sport_stream_19',  'BBC Red Button 19'),
        ('sport_stream_20',  'BBC Red Button 20'),
        ('sport_stream_21',  'BBC Red Button 21'),
        ('sport_stream_22',  'BBC Red Button 22'),
        ('sport_stream_23',  'BBC Red Button 23'),
        ('sport_stream_24',  'BBC Red Button 24'),
        ('sport_stream_01b', 'BBC Red Button 1b'),
        ('sport_stream_02b', 'BBC Red Button 2b'),
        ('sport_stream_03b', 'BBC Red Button 3b'),
        ('sport_stream_04b', 'BBC Red Button 4b'),
        ('sport_stream_05b', 'BBC Red Button 5b'),
        ('sport_stream_06b', 'BBC Red Button 6b'),
        ('sport_stream_07b', 'BBC Red Button 7b'),
        ('sport_stream_08b', 'BBC Red Button 8b'),
        ('sport_stream_09b', 'BBC Red Button 9b'),
        ('sport_stream_10b', 'BBC Red Button 10b'),
        ('sport_stream_11b', 'BBC Red Button 11b'),
        ('sport_stream_12b', 'BBC Red Button 12b'),
        ('sport_stream_13b', 'BBC Red Button 13b'),
        ('sport_stream_14b', 'BBC Red Button 14b'),
        ('sport_stream_15b', 'BBC Red Button 15b'),
        ('sport_stream_16b', 'BBC Red Button 16b'),
        ('sport_stream_17b', 'BBC Red Button 17b'),
        ('sport_stream_18b', 'BBC Red Button 18b'),
        ('sport_stream_19b', 'BBC Red Button 19b'),
        ('sport_stream_20b', 'BBC Red Button 20b'),
        ('sport_stream_21b', 'BBC Red Button 21b'),
        ('sport_stream_22b', 'BBC Red Button 22b'),
        ('sport_stream_23b', 'BBC Red Button 23b'),
        ('sport_stream_24b', 'BBC Red Button 24b'),
    ]
    iconimage = tp('special://home/addons/plugin.video.iplayerwww/media/red_button.png')
    for id, name in channel_list:
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 203, iconimage, '', '')
        else:
            AddMenuEntry(name, id, 123, iconimage, '', '')


def ListUHDTrial():
    channel_list = [
        ('uhd_stream_01',  'UHD Trial 1'),
        ('uhd_stream_02',  'UHD Trial 2'),
        ('uhd_stream_03',  'UHD Trial 3'),
        ('uhd_stream_04',  'UHD Trial 4'),
        ('uhd_stream_05',  'UHD Trial 5'),
    ]
    iconimage = 'resource://resource.images.iplayerwww/media/red_button.png'
    for id, name in channel_list:
        AddMenuEntry(name, id, 205, iconimage, '', '')


def AddAvailableUHDTrialItem(name, channelname):
    source = int(ADDON.getSetting('live_source'))
    if (source == 1):
        provider = "ak"
    elif (source == 2):
        provider = "llnw"
    else:
        provider = "ak"
    
    url = "http://a.files.bbci.co.uk/media/live/manifesto/audio_video/webcast/dash/uk/full/%s/%s.mpd" % (provider,channelname)

    PlayStream(name, url, "", "", "")


# ListLive creates menu entries for all live channels.
def ListLive():
    channel_list = [
        ('bbc_one_hd',                       'BBC One',                  'bbc_one_london'),
        ('bbc_two_england',                  'BBC Two',                  'bbc_two_england'),
        ('bbc_three_hd',                     'BBC Three',                'bbc_three'),
        ('bbc_four_hd',                      'BBC Four',                 'bbc_four'),
        ('cbbc_hd',                          'CBBC',                     'cbbc'),
        ('cbeebies_hd',                      'CBeebies',                 'cbeebies'),
        ('bbc_news24',                       'BBC News Channel',         'bbc_news24'),
        ('bbc_parliament',                   'BBC Parliament',           'bbc_parliament'),
        ('bbc_alba',                         'Alba',                     'bbc_alba'),
        ('bbc_scotland_hd',                  'BBC Scotland',             'bbc_scotland'),
        ('s4cpbs',                           'S4C',                      's4cpbs'),
        ('bbc_one_london',                   'BBC One London',           'bbc_one_london'),
        ('bbc_one_scotland_hd',              'BBC One Scotland',         'bbc_one_scotland'),
        ('bbc_one_northern_ireland_hd',      'BBC One Northern Ireland', 'bbc_one_northern_ireland'),
        ('bbc_one_wales_hd',                 'BBC One Wales',            'bbc_one_wales'),
        ('bbc_two_scotland',                 'BBC Two Scotland',         'bbc_two_england'),
        ('bbc_two_northern_ireland_digital', 'BBC Two Northern Ireland', 'bbc_two_northern_ireland_digital'),
        ('bbc_two_wales_digital',            'BBC Two Wales',            'bbc_two_wales_digital'),
        ('bbc_two_england',                  'BBC Two England',          'bbc_two_england'),
        ('bbc_one_cambridge',                'BBC One Cambridge',        'bbc_one_london'),
        ('bbc_one_channel_islands',          'BBC One Channel Islands',  'bbc_one_london'),
        ('bbc_one_east',                     'BBC One East',             'bbc_one_london'),
        ('bbc_one_east_midlands',            'BBC One East Midlands',    'bbc_one_london'),
        ('bbc_one_east_yorkshire',           'BBC One East Yorkshire',   'bbc_one_london'),
        ('bbc_one_north_east',               'BBC One North East',       'bbc_one_london'),
        ('bbc_one_north_west',               'BBC One North West',       'bbc_one_london'),
        ('bbc_one_oxford',                   'BBC One Oxford',           'bbc_one_london'),
        ('bbc_one_south',                    'BBC One South',            'bbc_one_london'),
        ('bbc_one_south_east',               'BBC One South East',       'bbc_one_london'),
        ('bbc_one_south_west',               'BBC One South West',       'bbc_one_london'),
        ('bbc_one_west',                     'BBC One West',             'bbc_one_london'),
        ('bbc_one_west_midlands',            'BBC One West Midlands',    'bbc_one_london'),
        ('bbc_one_yorks',                    'BBC One Yorks',            'bbc_one_london'),
    ]
    from urllib.parse import urlencode
    schedules = GetSchedules(channel_list)
    for id, name, schedule_chan_id in channel_list:
        now_on, schedule = schedules.get(schedule_chan_id, ('', ''))
        title = '{}    [COLOR orange]{}[/COLOR]'.format(name, now_on)
        iconimage = 'resource://resource.images.iplayerwww/media/'+id+'.png'

        if ADDON.getSetting('streams_autoplay') == 'true':
            mode = 203
            restart_action = 'PlayMedia'
        else:
            mode = 123
            restart_action = "Container.Update"
        querystring = urlencode({'name': name,
                                 'url': id,
                                 'mode': mode,
                                 'iconimage': iconimage,
                                 'watch_from_start': 'True'})
        ctx_mnu = [(translation(30603),     # 'Watch from the start'
                    ''.join((restart_action, '(plugin://', addonid, '?', querystring,
                             ', noresume)' if mode == 203 else ')'))
                    )]
        AddMenuEntry(title, id, mode, iconimage, schedule, '', resume_time='0', context_mnu=ctx_mnu)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
    sys.exit()


def ListAtoZ():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    characters = [
        ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
        ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
        ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
        ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
        ('Y', 'y'), ('Z', 'z'), ('0-9', '0-9')]

    if int(ADDON.getSetting('scrape_atoz')) == 1:
        with ProgressDlg(translation(30319)) as pDialog:
            page = 1
            total_pages = len(characters)
            for name, url in characters:
                GetAtoZPage(url)
                percent = int(100*page/total_pages)
                pDialog.update(percent,translation(30319),name)
                page += 1
    else:
        for name, url in characters:
            AddMenuEntry(name, url, 124, '', '', '')

def ListChannelAtoZ():
    """List programmes for each channel based on alphabetical order.

    Only creates the corresponding directories for each channel.
    """
    channel_list = [
        ('bbcone',           'bbc_one_hd',              'BBC One'),
        ('bbctwo',           'bbc_two_hd',              'BBC Two'),
        ('tv/bbcthree',      'bbc_three_hd',          'BBC Three'),
        ('bbcfour',          'bbc_four_hd',            'BBC Four'),
        ('tv/cbbc',          'cbbc_hd',                    'CBBC'),
        ('tv/cbeebies',      'cbeebies_hd',            'CBeebies'),
        ('tv/bbcnews',       'bbc_news24',     'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament',   'BBC Parliament'),
        ('tv/bbcalba',       'bbc_alba',                   'Alba'),
        ('tv/bbcscotland',   'bbc_scotland_hd',    'BBC Scotland'),
        ('tv/s4c',           's4cpbs',                      'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = 'resource://resource.images.iplayerwww/media/'+img+'.png'
        url = "https://www.bbc.co.uk/%s/a-z" % id
        AddMenuEntry(name, url, 134, iconimage, '', '')


def GetAtoZPage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    if int(ADDON.getSetting('scrape_atoz')) == 1:
        GetSingleAtoZPage(url)
    else:
        with ProgressDlg(translation(30319)) as pDialog:
            GetSingleAtoZPage(url,pDialog)


def GetSingleAtoZPage(url, pDialog=None):
    current_url = 'https://www.bbc.co.uk/iplayer/a-z/%s' % url
    # print("Opening "+current_url)
    try:
        html = OpenURL(current_url)
    except WebRequestError as err:
        # Ignore missing pages; there are simply no programmes starting with this letter.
        if err.status_code == 404:
            return
        else:
            raise

    total_pages = 1
    current_page = 1
    page_range = list(range(1))

    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, current_url)
        if 'pagination' in json_data:
            current_page = int(json_data['pagination']['currentPage'])
            total_pages = int(json_data['pagination']['totalPages'])
            if pDialog:
                percent = int(100*current_page/total_pages)
                pDialog.update(percent,translation(30319))
            # print('Current page: %s'%current_page)
            # print('Total pages: %s'%total_pages)
            if current_page<total_pages:
                split_page_url = current_url.split('?')
                page_base_url = split_page_url[0]
                for part in split_page_url[1:len(split_page_url)]:
                    if not part.startswith('page'):
                        page_base_url = page_base_url+'?'+part
                if '?' in page_base_url:
                    page_base_url = page_base_url+'&page='
                else:
                    page_base_url = page_base_url+'?page='
                for i in range(current_page+1,total_pages+1):
                    current_url = page_base_url+str(i)
                    # print("Opening "+current_url)
                    html = OpenURL(current_url)

                    json_data = ScrapeJSON(html)
                    if json_data:
                        ParseJSON(json_data, current_url)
                    if pDialog:
                        percent = int(100*i/total_pages)
                        pDialog.update(percent,translation(30319))
        else:
            ParseJSON(json_data, current_url)


def GetMultipleEpisodes(url):
    GetEpisodes(url)


def ParseAired(aired):
    """Parses a string format %d %b %Y to %d/%n/%Y otherwise empty string."""
    if aired:
        try:
            # Need to use equivelent for datetime.strptime() due to weird TypeError.
            return datetime.datetime(*(time.strptime(aired[0], '%d %b %Y')[0:6])).strftime('%d/%m/%Y')
        except ValueError:
            pass
    return ''


def FirstShownToAired(first_shown):
    """Converts the 'First shown' tag to %Y %m %d format."""
    release_parts = first_shown.split(' ')

    if len(release_parts) == 1:
        month = '01'
        day = '01'
        year = first_shown
    else:
        year = release_parts[-1]
        month = release_parts[-2]
        monthDict={
            'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
            'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
        if month in monthDict:
            month = monthDict[month]
            day = release_parts[-3].rjust(2,'0')
        else:
            month = '01'
            day = '01'
    aired = year + '-' + month + '-' + day
    return aired


def GetEpisodes(url):
    new_url = 'https://www.bbc.co.uk/iplayer/episodes/%s' % url
    ScrapeEpisodes(new_url)


def GetGroup(url):
    new_url = "https://www.bbc.co.uk/iplayer/group/%s" % url
    ScrapeEpisodes(new_url)


def ScrapeEpisodes(page_url):
    """Creates a list of programmes on one standard HTML page.

    ScrapeEpisodes contains a number of special treatments, which are only needed for
    specific pages, e.g. Search, but allows to use a single function for all kinds
    of pages.
    """

    with ProgressDlg(translation(30319)) as pDialog:
        html = OpenURL(page_url)

        total_pages = 1
        current_page = 1
        page_range = list(range(1))
        paginate = re.search(r'<ol class="paginat.*?</ol>', html, re.DOTALL)
        if not paginate:
            paginate = re.search(r'<div class="paginate.*?</div>', html, re.DOTALL)
        next_page = 1
        if paginate:
            if int(ADDON.getSetting('paginate_episodes')) == 0:
                current_page_match = re.search(r'page=(\d*)', page_url)
                if current_page_match:
                    current_page = int(current_page_match.group(1))
                pages = re.findall(r'<li class="pag.*?</li>',paginate.group(0),re.DOTALL)
                if pages:
                    last = pages[-1]
                    last_page = re.search(r'page=(\d*)', last)
                    if last_page:
                        total_pages = int(last_page.group(1))
                    else:
                        total_pages = current_page
                if current_page<total_pages:
                    split_page_url = page_url.replace('&','?').split('?')
                    page_base_url = split_page_url[0]
                    for part in split_page_url[1:len(split_page_url)]:
                        if not part.startswith('page'):
                            page_base_url = page_base_url+'?'+part
                    if '?' in page_base_url:
                        page_base_url = page_base_url.replace('https://www.bbc.co.uk','')+'&page='
                    else:
                        page_base_url = page_base_url.replace('https://www.bbc.co.uk','')+'?page='
                    next_page = current_page+1
                else:
                    next_page = current_page
                page_range = list(range(current_page, current_page+1))
            else:
                pages = re.findall(r'<li class="pag.*?</li>',paginate.group(0),re.DOTALL)
                if pages:
                    last = pages[-1]
                    last_page = re.search(r'page=(\d*)', last)
                    split_page_url = page_url.replace('&','?').split('?')
                    page_base_url = split_page_url[0]
                    for part in split_page_url[1:len(split_page_url)]:
                        if not part.startswith('page'):
                            page_base_url = page_base_url+'?'+part
                    if '?' in page_base_url:
                        page_base_url = page_base_url.replace('https://www.bbc.co.uk','')+'&page='
                    else:
                        page_base_url = page_base_url.replace('https://www.bbc.co.uk','')+'?page='
                    total_pages = int(last_page.group(1))
                page_range = list(range(1, total_pages+1))

        for page in page_range:

            if page > current_page:
                page_url = 'https://www.bbc.co.uk' + page_base_url + str(page)
                html = OpenURL(page_url)

            json_data = ScrapeJSON(html)
            if json_data:
                ParseJSON(json_data, page_url)

            percent = int(100*page/total_pages)
            pDialog.update(percent,translation(30319))

        if int(ADDON.getSetting('paginate_episodes')) == 0:
            if current_page < next_page:
                page_url = 'https://www.bbc.co.uk' + page_base_url + str(next_page)
                AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 128, '', '', '')


def ScrapeAtoZEpisodes(page_url):
    """Creates a list of programmes on one standard HTML page.

    ScrapeEpisodes contains a number of special treatments, which are only needed for
    specific pages, e.g. Search, but allows to use a single function for all kinds
    of pages.
    """

    with ProgressDlg(translation(30319)) as pDialog:
        html = OpenURL(page_url)

        total_pages = 1
        current_page = 1
        page_range = list(range(1))

        json_data = ScrapeJSON(html)
        if json_data:

            last_page = 1
            current_page = 1
            if 'pagination' in json_data:
                page_base_url_match = re.search(r'(.+?)page=', page_url)
                if page_base_url_match:
                    page_base_url = page_base_url_match.group(0)
                else:
                    page_base_url = page_url+"?page="
                current_page = json_data['pagination'].get('currentPage')
                last_page = json_data['pagination'].get('totalPages')
                if int(ADDON.getSetting('paginate_episodes')) == 0:
                    current_page_match = re.search(r'page=(\d*)', page_url)
                    if current_page_match:
                        current_page = int(current_page_match.group(1))
                    page_base_url_match = re.search(r'(.+?)page=', page_url)
                    if page_base_url_match:
                        page_base_url = page_base_url_match.group(0)
                    else:
                        page_base_url = page_url+"?page="
                    if current_page < last_page:
                        next_page = current_page+1
                    else:
                       next_page = current_page
                    page_range = list(range(current_page, current_page+1))
                else:
                    page_range = list(range(1, last_page+1))

            for page in page_range:

                if page > current_page:
                    page_url = page_base_url + str(page)
                    html = OpenURL(page_url)

                json_data = ScrapeJSON(html)
                if json_data:
                    ParseJSON(json_data, page_url)

                percent = int(100*page/last_page)
                pDialog.update(percent,translation(30319))

        if int(ADDON.getSetting('paginate_episodes')) == 0:
            if current_page < next_page:
                page_url = page_base_url + str(next_page)
                AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 134, '', '', '')


def ListCategories():
    """Parses the available categories and creates directories for selecting one of them.
    The category names are scraped from the website.
    """
    html = OpenURL('https://www.bbc.co.uk/iplayer')
    match = re.compile(
        '<a href="/iplayer/categories/(.+?)/featured".*?><span class="lnk__label">(.+?)</span>'
        ).findall(html)
    for url, name in match:
        if ((name == "View all") or (name == "A-Z")):
            continue
        AddMenuEntry(name, url, 126, '', '', '')


def ListCategoryFilters(url):
    """Parses the available category filters (if available) and creates directories for selcting them.
    If there are no filters available, all programmes will be listed using GetFilteredCategory.
    """
    url = url.split('/')[0]
    NEW_URL = 'https://www.bbc.co.uk/iplayer/categories/%s/a-z' % url

    # Read selected category's page.
    html = OpenURL(NEW_URL)
    # Some categories offer filters, we want to provide these filters as options.
    match1 = re.findall(
        '<a href="/iplayer/categories/(.+?)/a-z".*?>(.+?)</a>',
        html,
        re.DOTALL)
    if match1:
        AddMenuEntry('All', url, 126, '', '', '')
        for url, name in match1:
            AddMenuEntry(name, url, 126, '', '', '')
    else:
        GetFilteredCategory(url)


def GetFilteredCategory(url):
    """Parses the programmes available in the category view."""
    NEW_URL = 'https://www.bbc.co.uk/iplayer/categories/%s/a-z' % url

    ScrapeEpisodes(NEW_URL)


def ListChannelHighlights():
    """Creates a list directories linked to the highlights section of each channel."""
    channel_list = [
        ('bbcone',           'bbc_one_hd',              'BBC One'),
        ('bbctwo',           'bbc_two_hd',              'BBC Two'),
        ('tv/bbcthree',      'bbc_three_hd',          'BBC Three'),
        ('bbcfour',          'bbc_four_hd',            'BBC Four'),
        ('tv/cbbc',          'cbbc_hd',                    'CBBC'),
        ('tv/cbeebies',      'cbeebies_hd',            'CBeebies'),
        ('tv/bbcnews',       'bbc_news24',     'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament',   'BBC Parliament'),
        ('tv/bbcalba',       'bbc_alba',                   'Alba'),
        ('tv/bbcscotland',   'bbc_scotland_hd',    'BBC Scotland'),
        ('tv/s4c',           's4cpbs',                      'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = 'resource://resource.images.iplayerwww/media/'+img+'.png'
        AddMenuEntry(name, id, 106, iconimage, '', '')


def ParseSingleJSON(meta, item, name, added_playables, added_directories):
    main_url = None
    episodes_url = ''
    episodes_title = ''
    num_episodes = None
    synopsis = ''
    icon = ''
    aired = ''
    title = ''

    if 'episode' in item:
        subitem = item['episode']
        if 'id' in subitem:
            main_url = 'https://www.bbc.co.uk/iplayer/episode/' + subitem.get('id')
        if subitem.get('subtitle'):
            if 'default' in subitem.get('subtitle'):
                sub = subitem['subtitle'].get('default')
                if sub is not None:
                    sub = ' - '+sub
                else:
                    sub = ''
                if 'title' in subitem:
                    if 'default' in subitem.get('title'):
                        title = '%s%s' % (subitem['title'].get('default'), sub)
                else:
                     title = '%s%s' % (name, sub)
        elif subitem.get('title'):
            if 'default' in subitem.get('title'):
                title = subitem['title'].get('default')
        else:
            title = name
        if subitem.get('synopsis'):
            if 'small' in subitem.get('synopsis'):
                synopsis = subitem['synopsis'].get('small')
        if subitem.get('image'):
            if 'default' in subitem.get('image'):
                icon = subitem['image'].get('default').replace("{recipe}","832x468")
    else:
        if 'count' in item:
            if item['count']>1:
                num_episodes = str(item['count'])
                if 'id' in item:
                    main_url = 'https://www.bbc.co.uk/iplayer/episodes/' + item.get('id')
            elif 'id' in item:
                main_url = 'https://www.bbc.co.uk/iplayer/episode/' + item.get('id')
        elif 'id' in item:
            if 'initial_children' in item:
                for ic in item['initial_children']:
                    if 'id' in ic:
                        if item['id'] == ic['id']:
                            # This is just a playable, do not create a directory.
                            # Use the initial children to create the entry as it normally contains more information.
                            ParseSingleJSON(meta, ic, name, added_playables, added_directories)
                        else:
                            # There is a directory, and an initial episode.
                            # We need to create one directory and one playable.
                            ParseSingleJSON(meta, ic, name, added_playables, added_directories)
                            episodes_url = 'https://www.bbc.co.uk/iplayer/episodes/' + item.get('id')
                    else:
                        # Never seen this, but seems possible. This is just a directory.
                        episodes_url = 'https://www.bbc.co.uk/iplayer/episodes/' + item.get('id')
            else:
                main_url = 'https://www.bbc.co.uk/iplayer/episode/' + item.get('id')
        elif 'href' in item:
            # Some strings already contain the full URL, need to work around this.
            url = item['href'].replace('http://www.bbc.co.uk','')
            url = url.replace('https://www.bbc.co.uk','')
            if url:
                if meta == 'tleo-item':
                    episodes_url = 'https://www.bbc.co.uk' + url
                    # print(episodes_url)
                else:
                    main_url = 'https://www.bbc.co.uk' + url

        if 'secondaryHref' in item:
            # Some strings already contain the full URL, need to work around this.
            url = item['secondaryHref'].replace('http://www.bbc.co.uk','')
            url = url.replace('https://www.bbc.co.uk','')
            if url:
                episodes_url = 'https://www.bbc.co.uk' + url
                episodes_title = item["title"]
        elif meta:
            if 'secondaryHref' in meta:
                # Some strings already contain the full URL, need to work around this.
                url = meta['secondaryHref'].replace('http://www.bbc.co.uk','')
                url = url.replace('https://www.bbc.co.uk','')
                if url:
                    episodes_url = 'https://www.bbc.co.uk' + url
                    episodes_title = item["title"]
            if 'episodesAvailable' in meta:
                if meta['episodesAvailable'] > 1:
                    num_episodes = str(meta['episodesAvailable'])

        if 'subtitle' in item:
            if 'title' in item:
                title = "%s - %s" % (item['title'], item['subtitle'])
            else:
                title = name
        elif 'title' in item:
            title = item['title']
        else:
            title = name

        if 'synopsis' in item:
            synopsis = item['synopsis']
        if 'synopses' in item:
            if 'editorial' in item['synopses']:
                synopsis = item['synopses']['editorial']
            elif 'large' in item['synopses']:
                synopsis = item['synopses']['large']
            elif 'medium' in item['synopses']:
                synopsis = item['synopses']['medium']
            elif 'small' in item['synopses']:
                synopsis = item['synopses']['small']

        if 'imageTemplate' in item:
            icon = item['imageTemplate'].replace("{recipe}","832x468")
        if 'images' in item:
            icon = item['images']['standard'].replace("{recipe}","832x468")
        elif 'sources' in item:
            temp = item['sources'][0]['srcset'].split()[0]
            icon = re.sub(r'ic/.+?/','ic/832x468/',temp)


    if num_episodes:
        if not main_url in added_directories:
            title = '[B]'+item['title']+'[/B] - '+num_episodes+' episodes available'
            AddMenuEntry(title, main_url, 139, icon, synopsis, '')
            added_directories.append(main_url)

    elif episodes_url:
        if not episodes_url in added_directories:
            if episodes_title=='':
                episodes_title = title
            AddMenuEntry('[B]%s[/B]' % (episodes_title),
                         episodes_url, 128, icon, synopsis, '')
            added_directories.append(main_url)
    elif main_url:
        if not main_url in added_playables:
            CheckAutoplay(title , main_url, icon, synopsis, aired)
            added_playables.append(main_url)


def ParseJSON(programme_data, current_url):
    """Parses the JSON data containing programme information of a page. Contains a lot of fallbacks
    """

    added_playables = []
    added_directories = []

    if programme_data:
        name = ''
        if 'header' in programme_data:
            if 'title' in programme_data['header']:
                name = programme_data['header']['title']
            url_split = current_url.replace('&','?').split('?')
            is_paginated = False
            """ Avoid duplicate entries by checking if we are on page >1
            """
            for part in url_split:
                if part.startswith('page'):
                    is_paginated = True
            if not is_paginated:
                if 'availableSlices' in programme_data['header']:
                    current_series = programme_data['header']['currentSliceId']
                    slices = programme_data['header']['availableSlices']
                    if slices is not None:
                        for series in slices:
                            if series['id'] == current_series:
                                continue
                            base_url = url_split[0]
                            series_url = base_url + '?seriesId=' + series['id']
                            AddMenuEntry('[B]%s: %s[/B]' % (name, series['title']),
                                         series_url, 128, '', '', '')

        programmes = None
        if 'currentLetter' in programme_data:
            # This must be an A-Z page.
            current_letter = programme_data['currentLetter']
            programmes = programme_data['programmes'][current_letter]['entities']
        elif 'entities' in programme_data:
            if 'elements' in programme_data['entities']:
                programmes = programme_data['entities']['elements']
            if 'results' in programme_data['entities']:
                programmes = programme_data['entities']['results']
        elif 'relatedEpisodes' in programme_data:
            if 'episodes' in programme_data['relatedEpisodes']:
                programmes = programme_data['relatedEpisodes']['episodes']
            if 'slices' in programme_data['relatedEpisodes']:
                if programme_data['relatedEpisodes']['slices'] is not None:
                    if 'episode' in programme_data:
                        if 'title' in programme_data['episode']:
                            name = programme_data['episode']['title']
                    url_split = current_url.replace('&','?').split('?')
                    current_series = programme_data['relatedEpisodes']['currentSliceId']
                    for series in programme_data['relatedEpisodes']['slices']:
                        if series['id'] == current_series:
                            continue
                        base_url = url_split[0]
                        series_url = base_url + '?seriesId=' + series['id']
                        AddMenuEntry('[B]%s: %s[/B]' % (name, series['title']['default']),
                                     series_url, 128, '', '', '')
        elif 'items' in programme_data:
            # This must be Watchlist or Continue Watching.
            programmes = programme_data['items']

        if programmes:
            for item in programmes:
                meta = None
                if 'props' in item:
                    meta = item.get('meta')
                    item = item.get('props')
                elif 'contentItemProps' in item:
                    meta = item.get('type')
                    item = item.get('contentItemProps')
                ParseSingleJSON(meta, item, name, added_playables, added_directories)

        # The next section is for global and channel highlights. They are a bit tricky.
        groups = None
        highlights = None
        bundles = None
        if 'groups' in programme_data:
            groups = programme_data.get('groups')
            for entity in groups:
                for item in entity['entities']:
                    if 'props' in item:
                        item = item.get("props")
                    ParseSingleJSON(None, item, None, added_playables, added_directories)

                title = ''
                id = ''
                title = entity.get('title')
                id = entity.get('id')
                if (title and id):
                    episodes_url = 'https://www.bbc.co.uk/iplayer/group/%s' % id
                    if not episodes_url in added_directories:
                        AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                     episodes_url, 128, '', '', '')

        if 'highlights' in programme_data:
            highlights = programme_data.get('highlights')
            entity = highlights.get("items")
            if entity:
                for item in entity:
                    if 'props' in item:
                        item = item.get("props")
                    ParseSingleJSON(None, item, None, added_playables, added_directories)

        if 'bundles' in programme_data:
            bundles = programme_data.get('bundles')
            for bundle in bundles:
                entity = ''
                entity = bundle.get('entities')
                if entity:
                    for item in entity:
                        ParseSingleJSON(None, item, None, added_playables, added_directories)
                journey = ''
                journey = bundle.get('journey')
                if journey:
                    id = ''
                    id = journey.get('id')
                    type = ''
                    type = journey.get('type')
                    title = ''
                    title = bundle.get('title').get('default')
                    if title:
                        if (id and (type == 'group')):
                            if (id == 'popular'):
                                AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                             'url', 105, '', '', '')
                            else:
                                episodes_url = 'https://www.bbc.co.uk/iplayer/group/%s' % id
                                if not episodes_url in added_directories:
                                    AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                                 episodes_url, 128, '', '', '')
                        if (id and (type == 'category')):
                            AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                         id, 126, '', '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)


def SetSortMethods(*additional_methods):
    """Set a few standard sort methods and optional additional methods"""
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,
                    xbmcplugin.SORT_METHOD_TITLE,
                    xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE]
    sort_methods.extend(additional_methods)
    handle = int(sys.argv[1])
    for method in sort_methods:
        xbmcplugin.addSortMethod(handle, method)


def SelectSynopsis(synopses):
    if synopses is None:
        return ''
    return (synopses.get('editorial')
            or synopses.get('medium')
            or synopses.get('large')
            or synopses.get('small')
            or synopses.get('programme_small', ''))


def SelectImage(images):
    if not images:
        return 'DefaultFolder.png'
    return(images.get('standard')
           or images.get('promotional')
           or images.get('promotional_with_logo')
           or images.get('portrait', 'DefaultFolder.png')).replace('{recipe}', '832x468')


def ParseProgramme(progr_data):
    return {
        'url': 'https://www.bbc.co.uk/iplayer/episodes/' + progr_data['id'],
        'name': '[B]{}[/B] - {} episodes available'.format(progr_data['title'], progr_data['count']),
        'iconimage': progr_data.get('images', {}).get('standard', 'DefaultFolder.png').replace('{recipe}', '832x468'),
        'description': SelectSynopsis(progr_data['synopses'])
    }


def ParseEpisode(episode_data):
    title = episode_data.get('title', '')
    subtitle = episode_data.get('subtitle')
    if subtitle:
        title = ' - '.join((title, subtitle))
    version_data = episode_data['versions'][0]
    description = SelectSynopsis(episode_data.get('synopses'))

    return {
        'url': 'https://www.bbc.co.uk/iplayer/episode/' + episode_data['id'],
        'name': title,
        'iconimage': SelectImage(episode_data.get('images')),
        'description': description,
        'aired': episode_data.get('release_date_time', '').split('T')[0],
        # 'total_time': str(iso_duration_2_seconds(version_data['duration']['value']))
    }


def ListHighlights(highlights_url):
    """Creates a list of the programmes in the highlights section.
    """

    current_url = 'https://www.bbc.co.uk/%s' % highlights_url
    html = OpenURL(current_url)

    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, current_url)


def ListMostPopular():
    """Scrapes all episodes of the most popular page."""
    current_url = 'https://www.bbc.co.uk/iplayer/group/most-popular'
    html = OpenURL(current_url)

    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, current_url)


def AddAvailableStreamItem(name, url, iconimage, description):
    """Play a streamm based on settings for preferred catchup source and bitrate."""
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids['name']:
        name = stream_ids['name']
    if not iconimage or iconimage == u"DefaultVideo.png" and stream_ids['image']:
        iconimage = stream_ids['image']
    if stream_ids['description']:
        description = stream_ids['description']
    if ((not stream_ids['stream_id_st']) or (ADDON.getSetting('search_ad') == 'true')) and stream_ids['stream_id_ad']:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_ad'])
        strm_id = stream_ids['stream_id_ad']
    elif ((not stream_ids['stream_id_st']) or (ADDON.getSetting('search_signed') == 'true')) and stream_ids['stream_id_sl']:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_sl'])
        strm_id = stream_ids['stream_id_sl']
    else:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_st'])
        strm_id = stream_ids['stream_id_st']
    if streams_all[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams_all[1][0][1]
        # print subtitles_url
    else:
        subtitles_url = ''
    streams = streams_all[0]
    source = int(ADDON.getSetting('catchup_source'))
    # print "Selected source is %s"%source
    # print streams
    if source > 0:
        match = [x for x in streams if (x[0] == source)]
    else:
        match = streams
    PlayStream(name, match[0][2], iconimage, description, subtitles_url,
               episode_id=stream_ids['episode_id'], stream_id=strm_id)


def GetAvailableStreams(name, url, iconimage, description, resume_time='', total_time=''):
    """Calls AddAvailableStreamsDirectory based on user settings"""
    #print url
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids['name']:
        name = stream_ids['name']
    if stream_ids['image']:
        iconimage = stream_ids['image']
    if stream_ids['description']:
        description = stream_ids['description']
    # If we found standard streams, append them to the list.
    if stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name, stream_ids['stream_id_st'], iconimage, description,
                                     stream_ids['episode_id'], resume_time, total_time)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad'] or not stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name + ' - (Audio Described)', stream_ids['stream_id_ad'], iconimage,
                                     description, stream_ids['episode_id'], resume_time, total_time)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl'] or not stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name + ' - (Signed)', stream_ids['stream_id_sl'], iconimage,
                                     description, stream_ids['episode_id'], resume_time, total_time)


def Search(search_entered):
    """Simply calls the online search function. The search is then evaluated in EvaluateSearch."""
    if search_entered is None:
        keyboard = xbmc.Keyboard('', 'Search iPlayer')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText() .replace(' ', '%20')  # sometimes you need to replace spaces with + or %20

    if search_entered is None:
        return False

    NEW_URL = 'https://www.bbc.co.uk/iplayer/search?q=%s' % search_entered
    ScrapeEpisodes(NEW_URL)


def AddAvailableLiveStreamItemSelector(name, channelname, iconimage, watch_from_start=False):
    return AddAvailableLiveDASHStreamItem(name, channelname, iconimage, watch_from_start)


def AddAvailableLiveDASHStreamItem(name, channelname, iconimage, watch_from_start=False):
    streams = ParseLiveDASHStreams(channelname)

    source = int(ADDON.getSetting('live_source'))
    if source > 0:
        match = [x for x in streams if (x[0] == source)]
        if len(match) == 0:
            match = streams
    else:
        match = streams
    if watch_from_start:
        PlayStream(name, match[0][2], iconimage, '', '', replay_chan_id=channelname)
    else:
        PlayStream(name, match[0][2], iconimage, '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage, watch_from_start=False):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
        watch_from_start: True if the current programme is to be played from the start.
    """
    streams = ParseLiveDASHStreams(channelname)
    suppliers = ['', 'Akamai', 'Limelight', 'Bidi','Cloudfront']
    for supplier, bitrate, url, resolution in streams:
        title = name + ' - [I][COLOR fff1f1f1]%s[/COLOR][/I]' % (suppliers[supplier])
        if watch_from_start:
            AddMenuEntry(title, url, 201, iconimage, resume_time='0', replay_chan_id=channelname)
        else:
            AddMenuEntry(title, url, 201, iconimage, resume_time='0')


def GetJsonDataWithBBCid(url, retry=True):
    html = OpenURL(url)
    json_data = ScrapeJSON(html)
    if not json_data:
        xbmc.log(f"[ipwww_video] [Warning] No JSON data on page '{url}'.")
        return
    if json_data['id']['signedIn']:
        return json_data

    if retry:
        if CheckLogin():
            return GetJsonDataWithBBCid(url, retry=False)
        else:
            CreateBaseDirectory('video')
    else:
        xbmc.log('[ipwww_video] [Error] GetJsonDataWithBBCid(): still not signed in at second attempt')
        return


def ListWatching():
    url = "https://www.bbc.co.uk/iplayer/continue-watching"
    data = GetJsonDataWithBBCid(url)
    if not data:
        return

    for watching_item in data['items']['elements']:
        episode = watching_item['episode']
        programme = watching_item['programme']
        item_data = ParseEpisode(episode)

        # Lacking a field synopses, a watching item's description is empty. Since the
        # remaining playtime is presented in the title instead of the usual episode name,
        # place the original title/sub-title in the description.
        item_data['description'] = item_data['name']
        remaining_seconds = watching_item.get('remaining')
        if remaining_seconds:
            total_seconds = int(remaining_seconds * 100 / (100 - watching_item.get('progress', 0)))
            item_data['name'] = '{} - [I]{} min left[/I]'.format(episode.get('title', ''), int(remaining_seconds / 60))
            # Resume a little bit earlier, so it's easier to recognise where you've left off.
            item_data['resume_time'] = str(max(total_seconds - remaining_seconds - 10, 0))
            item_data['total_time'] = str(total_seconds)
        else:
            item_data['name'] = '{} - [I]next episode[/I]'.format(episode.get('title', ''))

        item_data['context_mnu'] = ct_menus = []
        programme_id = episode.get('tleo_id')

        if episode.get('id') != programme_id:
            # A programme with multiple episodes; add a 'View all episodes' context menu item.
            all_episodes_link = 'https://www.bbc.co.uk/iplayer/episodes/' + programme['id']
            ct_menus.append((translation(30600),
                             f'Container.Update(plugin://plugin.video.iplayerwww/?mode=128&url={all_episodes_link})'))

        if programme_id:
            # Add a context menu item 'Remove'
            ct_menus.append((translation(30601),
                             f'RunPlugin(plugin://plugin.video.iplayerwww?mode=301&episode_id={programme_id}&url=url)'))

        CheckAutoplay(**item_data)


def RemoveWatching(episode_id):
    """Remove an item from the 'Continue Watching' list.
    Handler for the context menu option 'Remove' on list items in 'Continue watching'.

    """
    PostJson('https://user.ibl.api.bbc.co.uk/ibl/v1/user/hides',
             {'id': episode_id})
    xbmc.executebuiltin('Container.Refresh')


def ListFavourites():
    """AKA 'Watchlist', FKA 'Added'."""
    data = GetJsonDataWithBBCid("https://www.bbc.co.uk/iplayer/added")
    if not data:
        return
    has_episodes = False
    for added_item in data['items']['elements']:
        programme = added_item['programme']
        ct_mnu = [('Remove',
                   f'RunPlugin(plugin://plugin.video.iplayerwww?mode=302&episode_id={programme["id"]}&url=url)')]
        if programme['count'] == 1:
            CheckAutoplay(context_mnu=ct_mnu, **ParseEpisode(programme['initial_children'][0]))
            has_episodes = True
        else:
            AddMenuEntry(mode=128, subtitles_url='', context_mnu=ct_mnu, **ParseProgramme(programme))
    if has_episodes:
        SetSortMethods(xbmcplugin.SORT_METHOD_DATE)
    else:
        SetSortMethods()


def RemoveFavourite(programme_id):
    """Remove an item from the Watchlist.
    Handler for the context menu option 'Remove' on list items in 'Watchlist'.

    Delete will never fail, even if programme_id is not on the list, or does not exist at all.
    """
    DeleteUrl('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + programme_id)
    xbmc.executebuiltin('Container.Refresh')


def ListRecommendations():
    data = GetJsonDataWithBBCid('https://www.bbc.co.uk/iplayer/recommendations')
    if not data:
        return
    for recommended_item in data['items']['elements']:
        episode = recommended_item['episode']
        item_data = ParseEpisode(episode)
        if not item_data:
            continue
        tleo_id = episode['tleo_id']
        if tleo_id != episode['id']:
            all_episodes_link = 'https://www.bbc.co.uk/iplayer/episodes/' + tleo_id
            item_data['context_mnu'] = [
                (translation(30600),
                 f'Container.Update(plugin://plugin.video.iplayerwww/?mode=128&url={all_episodes_link})')]
        CheckAutoplay(**item_data)
    SetSortMethods(xbmcplugin.SORT_METHOD_DATE)


def PlayStream(name, url, iconimage, description='', subtitles_url='', episode_id=None, stream_id=None, replay_chan_id=''):
    if iconimage == '':
        iconimage = 'DefaultVideo.png'
    html = OpenURL(url)
    check_geo = re.search(
        '<H1>Access Denied</H1>', html)
    if check_geo or not html:
        # print "Geoblock detected, raising error message"
        raise GeoBlockedError(translation(30401))
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon':'DefaultVideo.png', 'thumb':iconimage})
    liz.setInfo(type='Video', infoLabels={'Title': name})
    liz.setProperty("IsPlayable", "true")
    liz.setPath(url)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        # print "Downloading subtitles"
        subtitles_file = download_subtitles(subtitles_url)
        liz.setSubtitles([subtitles_file])
    if replay_chan_id:
        resume_point = GetLiveStartPosition(replay_chan_id)
        if resume_point is not None:
            liz.setProperties({'ResumeTime': str(resume_point),
                               'TotalTime': '7200',
                               'inputstream.adaptive.play_timeshift_buffer': 'true'})
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    ipwww_progress.monitor_progress(episode_id, stream_id)


def GetLiveStartPosition(chan_id):
    """Return the start position of the current programme relative to the beginning of the stream.

    :returns: The start position in seconds, or None if the start position is not available.
    """
    if not chan_id:
        return

    from datetime import datetime, timezone

    # Apart from bbc_one_hd, schedules from HD channels must be requested by their non-HD counterpart.
    if chan_id.endswith('_hd') and not chan_id.startswith('bbc_one'):
        chan_id = chan_id[:-3]

    now = datetime.now(timezone.utc)
    resp = None
    try:
        # Get schedules of the current channel to obtain the start time of the current programme.
        url = (f'https://ibl.api.bbc.co.uk/ibl/v1/channels/{chan_id}/broadcasts?per_page=2&from_date=' +
               now.strftime('%Y-%m-%dT%H:%M'))
        resp = OpenRequest('get', url)
        data = json.loads(resp)
        cur_broadcast = data['broadcasts']['elements'][0]
        # transmission_start is more accurate, but not always available.
        start = cur_broadcast.get('transmission_start') or cur_broadcast['scheduled_start']
        start_dt = strptime(start, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    except Exception as e:
        xbmcgui.Dialog().ok(translation(30400), translation(30415)) # Error msg start time not available.
        xbmc.log(f'[ipwww_video] [Error] Failed to get live resume point: {e!r}\n{resp}')
        return
    # Need to get the start of the current programme relative to the start of the stream.
    # Since a live stream has a 2 hrs timeshift window, the live edge is at 7200 seconds from the start.
    start_position = 7200 - (now - start_dt).total_seconds()
    if start_position < 0:
        if xbmcgui.Dialog().yesno(
                translation(30405),             # warning
                translation(30416),             # msg program started too long ago
                yeslabel=translation(30417),    # play from 2hrs back
                nolabel=translation(30418)):    # play live
            start_position = 0
        else:
            return
    return start_position


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description, episode_id, resume_time="", total_time=""):
    """Will create one menu entry for each available stream of a particular stream_id"""
    # print("Stream ID: %s"%stream_id)
    streams = ParseStreamsHLSDASH(stream_id)
    # print(streams)
    if streams[1]:
        # print("Setting subtitles URL")
        subtitles_url = streams[1][0][1]
        # print(subtitles_url)
    else:
        subtitles_url = ''
    suppliers = ['', 'Akamai', 'Limelight', 'Bidi','Cloudfront']
    for supplier, bitrate, url, resolution, protocol in streams[0]:
        title = name + ' - [I][COLOR ffd3d3d3]%s[/COLOR][/I]' % (suppliers[supplier])
        AddMenuEntry(title, url, 201, iconimage, description, subtitles_url, resolution=resolution,
                     episode_id=episode_id, stream_id=stream_id, resume_time=resume_time, total_time=total_time)


def ParseMediaselector(stream_id):
    streams = []
    subtitles = []
    # print("Parsing streams for PID: %s"%stream_id)
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = 'https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/%s/format/json/cors/1' % stream_id 
    html = OpenURL(NEW_URL)
    json_data = json.loads(html)
    if json_data:
        # print(json.dumps(json_data, sort_keys=True, indent=2))
        if 'media' in json_data:
            for media in json_data['media']:
                if 'kind' in media:
                    if media['kind'] == 'captions':
                        if 'connection' in media:
                            for connection in media['connection']:
                                href = ''
                                protocol = ''
                                supplier = ''
                                if 'href' in connection:
                                    href = connection['href']
                                if 'protocol' in connection:
                                    protocol = connection['protocol']
                                if 'supplier' in connection:
                                    supplier = connection['supplier']
                                if protocol == 'https':
                                    subtitles.append((href, protocol, supplier))
                    elif media['kind'].startswith('video'):
                        if 'connection' in media:
                            for connection in media['connection']:
                                href = ''
                                protocol = ''
                                supplier = ''
                                transfer_format = ''
                                if 'href' in connection:
                                    href = connection['href']
                                if 'protocol' in connection:
                                    protocol = connection['protocol']
                                if 'supplier' in connection:
                                    supplier = connection['supplier']
                                if 'transferFormat' in connection:
                                    transfer_format = connection['transferFormat']
                                if protocol == 'https':
                                    streams.append((href, protocol, supplier, transfer_format))
        elif 'result' in json_data:
            if json_data['result'] == 'geolocation':
                # print "Geoblock detected, raising error message"
                raise GeoBlockedError(translation(30401))
    # print("Found streams:")
    # print(streams)
    # print(subtitles)
    return streams, subtitles


def ParseStreamsHLSDASH(stream_id):
    return ParseDASHStreams(stream_id)


def ParseDASHStreams(stream_id):
    streams = []
    subtitles = []
    # print "Parsing streams for PID: %s"%stream_id
    mediaselector = ParseMediaselector(stream_id)
    # Open the page with the actual strem information and display the various available streams.
    source = int(ADDON.getSetting('catchup_source'))
    for url, protocol, supplier, transfer_format in mediaselector[0]:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'dash':
            if 'akamai' in supplier and source in [0,1]:
                tmp_sup = 1
            elif 'limelight' in supplier and source in [0,2]:
                tmp_sup = 2
            elif 'bidi' in supplier and source in [0,3]:
                tmp_sup = 3
            elif 'cloudfront' in supplier and source in [0,4]:
                tmp_sup = 4
            else:
                continue
            streams.append((tmp_sup, 1, url, '1280x720', protocol))
    source = int(ADDON.getSetting('subtitle_source'))
    for href, protocol, supplier in mediaselector[1]:
        if 'akamai' in supplier and source in [0,1]:
            tmp_sup = 1
        elif 'limelight' in supplier and source in [0,2]:
            tmp_sup = 2
        elif 'bidi' in supplier and source in [0,3]:
            tmp_sup = 3
        elif 'cloudfront' in supplier and source in [0,4]:
            tmp_sup = 4
        else:
            continue
        subtitles.append((tmp_sup, href, protocol))
    # print streams
    # print subtitles
    return streams, subtitles


def ParseLiveDASHStreams(channelname):
    streams = []
    mediaselector = ParseMediaselector(channelname)
    # print mediaselector
    for provider_url, protocol, provider_name, transfer_format in mediaselector[0]:
        if transfer_format == 'dash':
            tmp_sup = ''
            if 'akamai' in provider_name:
                tmp_sup = 1
            elif 'll' in provider_name or 'limelight' in provider_name:
                tmp_sup = 2
            elif 'bidi' in provider_name:
                tmp_sup = 3
            elif 'cloudfront' in provider_name:
                tmp_sup = 4
            else:
                continue
            streams.append((tmp_sup, 1, provider_url, '1280x720'))
    # print streams
    return streams


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    name = None
    image = None
    description = None
    stream_id_st = []
    stream_id_sl = []
    stream_id_ad = []

    json_data = ScrapeJSON(html)
    # print(json.dumps(json_data, indent=2, sort_keys=True))
    if json_data:
        if 'title' in json_data['episode']:
            name = json_data['episode']['title']
        if 'synopses' in json_data['episode']:
            synopses = json_data['episode']['synopses']
            if 'large' in synopses:
                description = synopses['large']
            elif 'medium' in synopses:
                description = synopses['medium']
            elif 'small' in synopses:
                description = synopses['small']
            elif 'editorial' in synopses:
                description = synopses['editorial']
        if 'standard' in json_data['episode']['images']:
            image = json_data['episode']['images']['standard'].replace('{recipe}','832x468')
        st = []
        ty = []
        for stream in json_data['versions']:
            if (stream['kind'] == 'original'):
                st.append(stream['id'])
                ty.append(1)
            elif (stream['kind'] == 'iplayer-version'):
                st.append(stream['id'])
                ty.append(2)
            elif (stream['kind'] == 'technical-replacement'):
                st.append(stream['id'])
                ty.append(0)
            elif (stream['kind'] == 'editorial'):
                st.append(stream['id'])
                ty.append(2)
            elif (stream['kind'] == 'shortened'):
                st.append(stream['id'])
                ty.append(3)
            elif (stream['kind'] == 'webcast'):
                st.append(stream['id'])
                ty.append(2)
            elif (stream['kind'] == 'signed'):
                stream_id_sl = stream['id']
            elif (stream['kind'] == 'audio-described'):
                stream_id_ad = stream['id']
            else:
                xbmc.log("iPlayer WWW warning: New stream kind: %s" % stream['kind'])
                stream_id_st = stream['id']

            if st:
                st_st = [x for _,x in sorted(zip(ty,st))]
                stream_id_st = st_st[0]

    return {'stream_id_st': stream_id_st, 'stream_id_sl': stream_id_sl, 'stream_id_ad': stream_id_ad,
            'name': name, 'image':image, 'description': description, 'episode_id': json_data['episode'].get('id', '')}


def ScrapeJSON(html):
    json_data = None
    format = 1
    match = re.search(r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);', html, re.DOTALL)
    if not match:
        format = 2
        match = re.search(r'window.__IPLAYER_REDUX_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        if format == 1:
            if 'appStoreState' in json_data:
                json_data = json_data.get('appStoreState')
            elif 'initialState' in json_data:
                json_data = json_data.get('initialState')
        # print json.dumps(json_data, indent=2, sort_keys=True)
    return json_data


def CheckAutoplay(name, url, iconimage, description, aired=None, resume_time="", total_time="", context_mnu=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        mode = 202
    else:
        mode = 122
    AddMenuEntry(name, url, mode, iconimage, description, '', aired=aired,
                 resume_time=resume_time, total_time=total_time, context_mnu=context_mnu)


def GetSchedules(channel_list):
    """Obtain the schedule for each channel in channel_list.

    :param channel_list: A list of tuples like defined in ListLive().
        The third item of each tuple is to be the channel_id used to obtain the schedule.
    :returns: A mapping of channel_id's to schedules.

    The schedules of the regional BBC one channels only differ in the title of the
    regional news. This function renames this titel of BBC One London to a more
    generic "BBC News where you are". This way the schedules of BBC One London can be
    used for all regional BBC One channels, which will greatly reduce the number of
    HTTP request.

    Schedules for each channel is a tuple with two elements. The first is the title of the
    programme that is now on, the second is single multi-line string, with the
    time and name of each programme on a separate line. These strings are intended
    to be used in the info fields of the ListItems of live channels.

    """
    import pytz
    from concurrent import futures

    utc_tz = pytz.utc
    utc_now = datetime.datetime.now(utc_tz)
    utc_tomorrow = utc_now + timedelta(hours=20)

    try:
        # Get local timezone from Kodi's settings
        cmd_str = '{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": ["locale.timezone"], "id": 1}'
        resp_data = json.loads(xbmc.executeJSONRPC(cmd_str))
        local_tz = pytz.timezone(resp_data['result']['value'])
    except(KeyError, json.JSONDecodeError):
        # Get from tzlocal as fallback if something fails.
        from tzlocal import get_localzone
        local_tz = get_localzone()

    # Use the user's local time format without seconds. Fix weird kodi formatting for 12-hour clock.
    local_time_format = xbmc.getRegion('time').replace(':%S', '').replace('%I%I:', '%I:')

    def get_schedule(channel):
        try:
            url = ''.join(('https://ibl.api.bbc.co.uk/ibl/v1/channels/',
                          channel,
                          '/broadcasts?per_page=12&from_date=',
                          utc_now.strftime('%Y-%m-%dT%H:%M')))
            resp = OpenRequest('get', url)
            schedule_list = json.loads(resp)['broadcasts']['elements']
            text_items = []
            now_on = schedule_list[0]['episode']['title']
            for item in schedule_list:
                start_t = utc_tz.localize(strptime(item['scheduled_start'], '%Y-%m-%dT%H:%M:%S.%fZ'))
                if start_t >= utc_tomorrow:
                    break
                title = item['episode']['title']
                subtitle = item['episode'].get('subtitle', '')
                if title == 'BBC London' and 'News' in subtitle:
                    title = 'BBC News where You Are'
                text_items.append(' - '.join((start_t.astimezone(local_tz).strftime(local_time_format), title)))
            return now_on, '\n'.join(text_items)
        except Exception as e:
            xbmc.log(f"Failed to get schedule of channel {channel}: {e!r}")
            return '', ''

    schedule_channels = list({item[2] for item in channel_list})

    with futures.ThreadPoolExecutor(max_workers=16) as executor:
        res = [executor.submit(get_schedule, chan) for chan in schedule_channels]
        futures.wait(res)
    return dict(zip(schedule_channels, (r.result() for r in res)))
