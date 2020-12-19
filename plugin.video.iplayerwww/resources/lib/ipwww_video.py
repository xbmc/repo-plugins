# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import re
import datetime
import time
import json
from operator import itemgetter
from ipwww_common import translation, AddMenuEntry, OpenURL, \
                         CheckLogin, CreateBaseDirectory, GetCookieJar, \
                         ParseImageUrl, download_subtitles

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')


def RedButtonDialog():
    if ADDON.getSetting('redbutton_warning') == 'true':
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(translation(30405), translation(30406), '',
                           translation(30407), translation(30409), translation(30408))
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
    iconimage = xbmc.translatePath('special://home/addons/plugin.video.iplayerwww/media/red_button.png')
    for id, name in channel_list:
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 203, iconimage, '', '')
        else:
            AddMenuEntry(name, id, 123, iconimage, '', '')


# ListLive creates menu entries for all live channels.
def ListLive():
    channel_list = [
        ('bbc_one_hd',                       'BBC One'),
        ('bbc_two_hd',                       'BBC Two'),
        ('bbc_four_hd',                      'BBC Four'),
        ('cbbc_hd',                          'CBBC'),
        ('cbeebies_hd',                      'CBeebies'),
        ('bbc_news24',                       'BBC News Channel'),
        ('bbc_parliament',                   'BBC Parliament'),
        ('bbc_alba',                         'Alba'),
        ('bbc_scotland_hd',                  'BBC Scotland',),
        ('s4cpbs',                           'S4C'),
        ('bbc_one_london',                   'BBC One London'),
        ('bbc_one_scotland_hd',              'BBC One Scotland'),
        ('bbc_one_northern_ireland_hd',      'BBC One Northern Ireland'),
        ('bbc_one_wales_hd',                 'BBC One Wales'),
        ('bbc_two_scotland',                 'BBC Two Scotland'),
        ('bbc_two_northern_ireland_digital', 'BBC Two Northern Ireland'),
        ('bbc_two_wales_digital',            'BBC Two Wales'),
        ('bbc_two_england',                  'BBC Two England',),
        ('bbc_one_cambridge',                'BBC One Cambridge',),
        ('bbc_one_channel_islands',          'BBC One Channel Islands',),
        ('bbc_one_east',                     'BBC One East',),
        ('bbc_one_east_midlands',            'BBC One East Midlands',),
        ('bbc_one_east_yorkshire',           'BBC One East Yorkshire',),
        ('bbc_one_north_east',               'BBC One North East',),
        ('bbc_one_north_west',               'BBC One North West',),
        ('bbc_one_oxford',                   'BBC One Oxford',),
        ('bbc_one_south',                    'BBC One South',),
        ('bbc_one_south_east',               'BBC One South East',),
        ('bbc_one_south_west',               'BBC One South West',),
        ('bbc_one_west',                     'BBC One West',),
        ('bbc_one_west_midlands',            'BBC One West Midlands',),
        ('bbc_one_yorks',                    'BBC One Yorks',),
    ]
    for id, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', id + '.png'))
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 203, iconimage, '', '')
        else:
            AddMenuEntry(name, id, 123, iconimage, '', '')


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
        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create(translation(30319))
        page = 1
        total_pages = len(characters)
        for name, url in characters:
            GetAtoZPage(url)
            percent = int(100*page/total_pages)
            pDialog.update(percent,translation(30319),name)
            page += 1
        pDialog.close()
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
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
        url = "https://www.bbc.co.uk/%s/a-z" % id
        AddMenuEntry(name, url, 134, iconimage, '', '')


def GetAtoZPage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    current_url = 'https://www.bbc.co.uk/iplayer/a-z/%s' % url
    html = OpenURL(current_url)

    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, current_url)


def GetMultipleEpisodes(url):
    html = OpenURL(url)
    # There is a new layout for episodes, scrape it from the JSON received as part of the page
    json_data = ScrapeJSON(html)

    if json_data['episode']['tleoId']:
        GetEpisodes(json_data['episode']['tleoId'])


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

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

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

    pDialog.close()


def ScrapeAtoZEpisodes(page_url):
    """Creates a list of programmes on one standard HTML page.

    ScrapeEpisodes contains a number of special treatments, which are only needed for
    specific pages, e.g. Search, but allows to use a single function for all kinds
    of pages.
    """

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

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
                    next_page = curent_page+1
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

    pDialog.close()


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
    NEW_URL = 'https://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz' % url

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
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
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
                if 'title' in subitem:
                    if 'default' in subitem.get('title'):
                        title = '%s - %s' % (subitem['title'].get('default'), subitem['subtitle'].get('default'))
                else:
                     title = '%s - %s' % (name, subitem['subtitle'].get('default'))
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
        if 'href' in item:
            # Some strings already contain the full URL, need to work around this.
            url = item['href'].replace('http://www.bbc.co.uk','')
            url = url.replace('https://www.bbc.co.uk','')
            if url:
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

        if 'imageTemplate' in item:
            icon = item['imageTemplate'].replace("{recipe}","832x468")

    if main_url:
        if not main_url in added_playables:
            CheckAutoplay(title , main_url, icon, synopsis, aired)
            added_playables.append(main_url)

    if num_episodes:
        if not main_url in added_directories:
            title = '[B]'+item['title']+'[/B] - '+num_episodes+' episodes available'
            AddMenuEntry(title, main_url, 139, icon, synopsis, '')
            added_directories.append(main_url)

    if episodes_url:
        if not main_url in added_directories:
            AddMenuEntry('[B]%s[/B]' % (episodes_title),
                         episodes_url, 128, icon, synopsis, '')
            added_directories.append(main_url)


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
            # This must be a category or most popular.
            programmes = programme_data['entities']
        elif 'items' in programme_data:
            # This must be Added or Watching.
            programmes = programme_data['items']

        if programmes:
            for item in programmes:
                meta = None
                if 'props' in item:
                    meta = item.get('meta')
                    item = item.get('props')
                ParseSingleJSON(meta, item, name, added_playables, added_directories)

        # The next section is for global and channel highlights. They are a bit tricky.
        groups = None
        highlights = None
        bundles = None
        if 'groups' in programme_data:
            groups = programme_data.get('groups')
            for entity in groups:
                for item in entity['entities']:
                    item = item.get("props")
                    if not item:
                        continue
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
                    item = item.get("props")
                    if not item:
                        continue
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
        streams_all = ParseStreams(stream_ids['stream_id_ad'])
    elif ((not stream_ids['stream_id_st']) or (ADDON.getSetting('search_signed') == 'true')) and stream_ids['stream_id_sl']:
        streams_all = ParseStreams(stream_ids['stream_id_sl'])
    else:
        streams_all = ParseStreams(stream_ids['stream_id_st'])
    if streams_all[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams_all[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    streams = streams_all[0]
    source = int(ADDON.getSetting('catchup_source'))
    bitrate = int(ADDON.getSetting('catchup_bitrate'))
    # print "Selected source is %s"%source
    # print "Selected bitrate is %s"%bitrate
    # print streams
    if source > 0:
        if bitrate > 0:
            # Case 1: Selected source and selected bitrate
            match = [x for x in streams if ((x[0] == source) and (x[1] == bitrate))]
            if len(match) == 0:
                # Fallback: Use same bitrate but different supplier.
                match = [x for x in streams if (x[1] == bitrate)]
                if len(match) == 0:
                    # Second Fallback: Use any lower bitrate from selected source.
                    match = [x for x in streams if (x[0] == source) and (x[1] in list(range(1, bitrate)))]
                    match.sort(key=lambda x: x[1], reverse=True)
                    if len(match) == 0:
                        # Third Fallback: Use any lower bitrate from any source.
                        match = [x for x in streams if (x[1] in list(range(1, bitrate)))]
                        match.sort(key=lambda x: x[1], reverse=True)
        else:
            # Case 2: Selected source and any bitrate
            match = [x for x in streams if (x[0] == source)]
            if len(match) == 0:
                # Fallback: Use any source and any bitrate
                match = streams
            match.sort(key=lambda x: x[1], reverse=True)
    else:
        if bitrate > 0:
            # Case 3: Any source and selected bitrate
            match = [x for x in streams if (x[1] == bitrate)]
            if len(match) == 0:
                # Fallback: Use any source and any lower bitrate
                match = streams
                match = [x for x in streams if (x[1] in list(range(1, bitrate)))]
                match.sort(key=lambda x: x[1], reverse=True)
        else:
            # Case 4: Any source and any bitrate
            # Play highest available bitrate
            match = streams
            match.sort(key=lambda x: x[1], reverse=True)
    PlayStream(name, match[0][2], iconimage, description, subtitles_url)


def GetAvailableStreams(name, url, iconimage, description):
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
        AddAvailableStreamsDirectory(name, stream_ids['stream_id_st'], iconimage, description)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad'] or not stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name + ' - (Audio Described)', stream_ids['stream_id_ad'], iconimage, description)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl'] or not stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name + ' - (Signed)', stream_ids['stream_id_sl'], iconimage, description)


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


def AddAvailableLiveStreamItem(name, channelname, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate."""
    stream_bitrates = [9999, 0.1, 0.2, 0.3, 0.6, 1.0, 1.8, 3.1, 5.5]

    if int(ADDON.getSetting('live_source')) == 1:
        providers = [('ak', 'Akamai')]
    elif int(ADDON.getSetting('live_source')) == 2:
        providers = [('llnw', 'Limelight')]
    else:
        providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    bitrate_selected = int(ADDON.getSetting('live_bitrate'))
    if bitrate_selected > len(stream_bitrates) - 1:
        bitrate_selected = 0
        ADDON.setSetting('live_bitrate', str(bitrate_selected))

    streams_available = ParseLiveStreams(channelname, providers)

    # print streams_available
    # Play the prefered option
    if bitrate_selected > 0:
        match = [x for x in streams_available if (x[1] == stream_bitrates[bitrate_selected])]
        if len(match) == 0:
            # Fallback: Use any bitrate lower than the selected from any source.
            match = [x for x in streams_available if (x[1] <= stream_bitrates[bitrate_selected] )]
            match.sort(key=lambda x: x[1], reverse=True)
            if len(match) == 0:
                # Fallback: Selected bitrate is too low. Use lowest available bitrate.
                match = sorted(streams_available, key=lambda x: x[1], reverse=False)
        # print "Selected bitrate is %s"%stream_bitrates[bitrate_selected]
        # print match
        # print "Playing %s from %s with bitrate %s"%(name, match[0][4], match [0][1])
        if len(match) > 0: #TODO error message
            PlayStream(name, match[0][4], iconimage, '', '')
    # Play the fastest available stream of the preferred provider
    else:
        PlayStream(name, streams_available[0][4], iconimage, '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
    """
    streams = ParseLiveStreams(channelname, '')

    # Add each stream to the Kodi selection menu.
    for id, bitrate, codecs, resolution, url, provider_name in streams:
        # For easier selection use colors to indicate high and low bitrate streams
        if bitrate > 2.1:
            color = 'ff008000'
        elif bitrate > 1.0:
            color = 'ffffff00'
        elif bitrate > 0.6:
            color = 'ffffa500'
        else:
            color = 'ffff0000'

        title = name + ' - [I][COLOR %s]%0.1f Mbps[/COLOR] [COLOR fff1f1f1]%s[/COLOR][/I]' % (
            color, bitrate, provider_name)
        # Finally add them to the selection menu.
        AddMenuEntry(title, url, 201, iconimage, '', '')


def ListWatching(logged_in):

    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('video')
        return

    cookie_jar = None
    cookie_jar = GetCookieJar()
    url = "https://www.bbc.co.uk/iplayer/watching"
    html = OpenURL(url)
    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, url)


def ListFavourites(logged_in):

    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('video')
        return

    cookie_jar = None
    cookie_jar = GetCookieJar()
    url = "https://www.bbc.co.uk/iplayer/added"
    html = OpenURL(url)
    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, url)


def PlayStream(name, url, iconimage, description, subtitles_url):
    if iconimage == '':
        iconimage = 'DefaultVideo.png'
    html = OpenURL(url)
    check_geo = re.search(
        '<H1>Access Denied</H1>', html)
    if check_geo or not html:
        # print "Geoblock detected, raising error message"
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30400), translation(30401))
        raise
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels={'Title': name})
    liz.setProperty("IsPlayable", "true")
    liz.setPath(url)
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        subtitles_file = download_subtitles(subtitles_url)
        liz.setSubtitles([subtitles_file])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

def AddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""
    # print "Stream ID: %s"%stream_id
    streams = ParseStreams(stream_id)
    # print streams
    if streams[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    suppliers = ['', 'Akamai', 'Limelight', 'Bidi']
    bitrates = [0, 800, 1012, 1500, 1800, 2400, 3116, 5510]
    for supplier, bitrate, url, resolution in sorted(streams[0], key=itemgetter(1), reverse=True):
        if bitrate in (5, 7):
            color = 'ff008000'
        elif bitrate == 6:
            color = 'ff0084ff'
        elif bitrate in (3, 4):
            color = 'ffffff00'
        else:
            color = 'ffffa500'
        title = name + ' - [I][COLOR %s]%0.1f Mbps[/COLOR] [COLOR ffd3d3d3]%s[/COLOR][/I]' % (
            color, bitrates[bitrate] / 1000, suppliers[supplier])
        AddMenuEntry(title, url, 201, iconimage, description, subtitles_url, resolution=resolution)


def ParseStreams(stream_id):
    retlist = []
    # print "Parsing streams for PID: %s"%stream_id
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "https://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'connection authExpires=".+?href="(.+?)".+?supplier="mf_(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    source = int(ADDON.getSetting('catchup_source'))
    for m3u8_url, supplier, transfer_format in match:
        if m3u8_url.startswith('https') and (ADDON.getSetting('streams_ignore_https') == 'true'):
            continue
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier.startswith('akamai') and source in [0,1]:
                tmp_sup = 1
            elif supplier.startswith('limelight') and source in [0,2]:
                tmp_sup = 2
            elif supplier.startswith('bidi') and source in [0,3]:
                tmp_sup = 3
            else:
                continue
            m3u8_breakdown = re.compile('(.+?)iptv.+?m3u8(.+?)$').findall(m3u8_url)
            m3u8_html = OpenURL(m3u8_url)
            m3u8_match = re.compile('BANDWIDTH=(.+?),.+?RESOLUTION=(.+?)(?:,.+?\n|\n)(.+?)\n').findall(m3u8_html)
            for bandwidth, resolution, stream in m3u8_match:
                url = "%s%s%s" % (m3u8_breakdown[0][0], stream, m3u8_breakdown[0][1])
                if 1000000 <= int(bandwidth) <= 1100000:
                    tmp_br = 2
                elif 1790000 <= int(bandwidth) <= 1800000:
                    tmp_br = 4
                elif 3100000 <= int(bandwidth) <= 3120000:
                    tmp_br = 6
                elif int(bandwidth) >= 5500000:
                    tmp_br = 7
                retlist.append((tmp_sup, tmp_br, url, resolution))
    # It may be useful to parse these additional streams as a default as they offer additional bandwidths.
    match = re.compile(
        'kind="video".+?connection href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    unique = []
    [unique.append(item) for item in match if item not in unique]
    for m3u8_url, supplier, transfer_format in unique:
        if m3u8_url.startswith('https') and (ADDON.getSetting('streams_ignore_https') == 'true'):
            continue
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier.startswith('akamai_hls_open') and source in [0,1]:
                tmp_sup = 1
            elif supplier.startswith('limelight_hls_open') and source in [0,2]:
                tmp_sup = 2
            else:
                continue
            m3u8_breakdown = re.compile('.+?master.m3u8(.+?)$').findall(m3u8_url)
        m3u8_html = OpenURL(m3u8_url)
        m3u8_match = re.compile('BANDWIDTH=(.+?),RESOLUTION=(.+?),.+?\n(.+?)\n').findall(m3u8_html)
        for bandwidth, resolution, stream in m3u8_match:
            url = "%s%s" % (stream, m3u8_breakdown[0][0])
            # This is not entirely correct, displayed bandwidth may be higher or lower than actual bandwidth.
            if int(bandwidth) <= 801000:
                tmp_br = 1
            elif int(bandwidth) <= 1510000:
                tmp_br = 3
            elif int(bandwidth) <= 2410000:
                tmp_br = 5
            retlist.append((tmp_sup, tmp_br, url, resolution))
    # Some events have special live streams which show up as normal programmes.
    # They need to be parsed separately.
    match = re.compile(
        'connection.+?href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    unique = []
    [unique.append(item) for item in match if item not in unique]
    for m3u8_url, supplier, transfer_format in unique:
        if m3u8_url.startswith('https') and (ADDON.getSetting('streams_ignore_https') == 'true'):
            continue
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_hls_live':
                tmp_sup = 1
            elif supplier == 'll_hls_live':
                tmp_sup = 2
            else:
                # This is not a live stream, skip code to avoid unnecessary loading of playlists.
                continue
            html = OpenURL(m3u8_url)
            match = re.compile('#EXT-X-STREAM-INF:PROGRAM-ID=(.+?),BANDWIDTH=(.+?),CODECS="(.*?)",RESOLUTION=(.+?)\s*(.+?.m3u8)').findall(html)
            for stream_id, bandwidth, codecs, resolution, url in match:
                # Note: This is not entirely correct as these bandwidths relate to live programmes,
                # not catchup.
                if int(bandwidth) <= 1000000:
                    tmp_br = 1
                elif int(bandwidth) <= 1100000:
                    tmp_br = 2
                elif 1700000 <= int(bandwidth) <= 1900000:
                    tmp_br = 4
                elif 3100000 <= int(bandwidth) <= 3120000:
                    tmp_br = 6
                elif int(bandwidth) >= 5500000:
                    tmp_br = 7
                retlist.append((tmp_sup, tmp_br, url, resolution))
    match = re.compile('service="captions".+?connection href="(.+?)"').findall(html)
    # print "Subtitle URL: %s"%match
    # print retlist
    if not match:
        # print "No streams found"
        check_geo = re.search(
            '<error id="geolocation"/>', html)
        if check_geo:
            # print "Geoblock detected, raising error message"
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30400), translation(30401))
            raise
    return retlist, match


def ParseLiveStreams(channelname, providers):
    if providers == '':
        providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    streams = []

    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        if channelname in ['bbc_parliament', 'bbc_alba', 's4cpbs', 'bbc_one_london',
                           'bbc_two_wales_digital', 'bbc_two_northern_ireland_digital',
                           'bbc_two_scotland', 'bbc_one_cambridge', 'bbc_one_channel_islands',
                           'bbc_one_east', 'bbc_one_east_midlands', 'bbc_one_east_yorkshire',
                           'bbc_one_north_east', 'bbc_one_north_west', 'bbc_one_oxford',
                           'bbc_one_south', 'bbc_one_south_east', 'bbc_one_south_west',
                           'bbc_one_west', 'bbc_one_west_midlands', 'bbc_one_yorks',
                           'bbc_scotland']:
            device = 'hls_tablet'
        else:
            device = 'abr_hdtv'

        if channelname.startswith('sport_stream_'):
            cast = "webcast"
        else:
            cast = "simulcast"

        url = 'https://a.files.bbci.co.uk/media/live/manifesto/audio_video/%s/hls/uk/%s/%s/%s.m3u8' \
              % (cast, device, provider_url, channelname)
        html = OpenURL(url)
        match = re.compile('#EXT-X-STREAM-INF:PROGRAM-ID=(.+?),BANDWIDTH=(.+?),CODECS="(.*?)",RESOLUTION=(.+?)\s*(.+?.m3u8)').findall(html)

        # Add provider name to the stream list.
        streams.extend([list(stream) + [provider_name] for stream in match])

    # Convert bitrate to Mbps for further processing
    for i in list(range(len(streams))):
        streams[i][1] = round(int(streams[i][1])/1000000.0, 1)

    # Return list sorted by bitrate
    return sorted(streams, key=lambda x: (x[1]), reverse=True)


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
        for stream in json_data['versions']:
            if ((stream['kind'] == 'original') or
               (stream['kind'] == 'iplayer-version') or
               (stream['kind'] == 'technical-replacement') or
               (stream['kind'] == 'editorial') or
               (stream['kind'] == 'shortened') or
               (stream['kind'] == 'webcast')):
                stream_id_st = stream['id']
            elif (stream['kind'] == 'signed'):
                stream_id_sl = stream['id']
            elif (stream['kind'] == 'audio-described'):
                stream_id_ad = stream['id']
            else:
                xbmc.log("iPlayer WWW warning: New stream kind: %s" % stream['kind'])
                stream_id_st = stream['id']

    return {'stream_id_st': stream_id_st, 'stream_id_sl': stream_id_sl, 'stream_id_ad': stream_id_ad, 'name': name, 'image':image, 'description': description}


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


def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 202, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 122, iconimage, plot, '', aired=aired)

