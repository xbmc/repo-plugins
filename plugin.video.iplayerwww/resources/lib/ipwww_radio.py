# -*- coding: utf-8 -*-

import sys
import os
import re
from operator import itemgetter
from resources.lib.ipwww_common import translation, AddMenuEntry, OpenURL, \
                                       CheckLogin, CreateBaseDirectory

import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
import random
import json

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')

def GetAtoZPage(page_url, just_episodes=False):
    """   Generic Radio page scraper.   """

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))
    html = OpenURL(page_url)
    total_pages = 1
    current_page = 1
    page_range = list(range(1))
    paginate = re.search(r'<ol class="pagination">.*?</ol>', html, re.DOTALL)
    next_page = 1
    if paginate:
        if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
            current_page_match = re.search(r'page=(\d*)', page_url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
            page_range = list(range(current_page, current_page+1))
            next_page_match = re.search(r'<li class="pagination__next"><a href="(.*?page=)(.*?)">', paginate.group(0))
            if next_page_match:
                page_base_url = next_page_match.group(1)
                next_page = int(next_page_match.group(2))
            else:
                next_page = current_page
            page_range = list(range(current_page, current_page+1))
        else:
            pages = re.findall(r'<li.+?class="pagination__page.*?</li>',paginate.group(0),re.DOTALL)
            if pages:
                last = pages[-1]
                last_page = re.search(r'<a.+?href="(.*?=)(.*?)"',last)
                page_base_url = page_url+last_page.group(1)
                total_pages = int(last_page.group(2))
            page_range = list(range(1, total_pages+1))

    for page in page_range:

        if page > current_page:
            page_url = page_base_url + str(page)
            html = OpenURL(page_url)

        masthead_title = ''
        masthead_title_match = re.search(r'<div.+?id="programmes-main-content".*?<span property="name">(.+?)</span>', html)
        if masthead_title_match:
            masthead_title = masthead_title_match.group(1)
        else:
            alternative_masthead_title_match = re.search(r'<div class="br-masthead__title">.*?<a href="[^"]+">([^<]+?)</a>', html, re.M | re.S)
            if alternative_masthead_title_match:
                masthead_title = alternative_masthead_title_match.group(1)

        list_item_num = 1

        programmes = html.split('<li class="grid 1/1 atoz-title">')
        for programme in programmes:

            if not re.search(r'programme--radio', programme):
                continue

            series_id = ''
            series_id_match = re.search(r'/programmes/(.+?)/episodes/player', programme)
            if series_id_match:
                series_id = series_id_match.group(1)

            programme_id = ''
            programme_id_match = re.search(r'data-pid="(.+?)"', programme)
            if programme_id_match:
                programme_id = programme_id_match.group(1)

            name = ''
            name_match = re.search(r'<span class="programme__title delta"><span>(.+?)</span>', programme)
            if name_match:
                name = name_match.group(1)
            else:
                alternative_name_match = re.search(r'<meta property="name" content="([^"]+?)"', programme)
                if alternative_name_match:
                    name = alternative_name_match.group(1)

            image = ''
            image_match = re.search(r'data-src="(.+?)" />', programme)
            if image_match:
                image = image_match.group(1)

            synopsis = ''
            synopsis_match = re.search(r'p class="programme__synopsis.*?<span>(.+?)<\/span>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)

            station = ''
            station_match = re.search(r'<p class="programme__service micro text--subtle">(.+?)<\/p>', programme)
            if station_match:
                station = station_match.group(1).strip()

            series_title = "[B]%s - %s[/B]" % (station, name)
            if just_episodes:
                title = "[B]%s[/B] - %s" % (masthead_title, name)
            else:
                title = "[B]%s[/B] - %s" % (station, name)

            if series_id:
                AddMenuEntry(series_title, series_id, 131, image, synopsis, '')
            elif programme_id: #TODO maybe they are not always mutually exclusive
                url = "https://www.bbc.co.uk/sounds/play/%s" % programme_id
                CheckAutoplay(title, url, image, ' ', '')

            percent = int(100*(page+list_item_num/len(programmes))/total_pages)
            pDialog.update(percent,translation(30319),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))


    if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 138, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()


def GetPage(page_url, just_episodes=False):
    """   Generic Radio page scraper.   """

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

    html = OpenURL(page_url)

    total_pages = 1
    current_page = 1
    page_range = list(range(1))
    paginate = re.search(r'<ol.+?class="pagination.*?</ol>',html)
    next_page = 1
    if paginate:
        if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
            current_page_match = re.search(r'page=(\d*)', page_url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
            page_range = list(range(current_page, current_page+1))
            next_page_match = re.search(r'<li class="pagination__next"><a href="(.*?page=)(.*?)">', paginate.group(0))
            if next_page_match:
                page_base_url = next_page_match.group(1)
                next_page = int(next_page_match.group(2))
            else:
                next_page = current_page
            page_range = list(range(current_page, current_page+1))
        else:
            pages = re.findall(r'<li.+?class="pagination__page.*?</li>',paginate.group(0))
            if pages:
                last = pages[-1]
                last_page = re.search(r'<a.+?href="(.*?=)(.*?)"',last)
                page_base_url = last_page.group(1)
                total_pages = int(last_page.group(2))
            page_range = list(range(1, total_pages+1))

    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)

        masthead_title = ''
        masthead_title_match = re.search(r'<div.+?id="programmes-main-content".*?<span property="name">(.+?)</span>', html)
        if masthead_title_match:
            masthead_title = masthead_title_match.group(1)
        else:
            alternative_masthead_title_match = re.search(r'<div class="br-masthead__title">.*?<a href="[^"]+">([^<]+?)</a>', html, re.M | re.S)
            if alternative_masthead_title_match:
                masthead_title = alternative_masthead_title_match.group(1)

        list_item_num = 1
        data = ''
        data_match = re.findall(r'<script type="application\/ld\+json">(.*?)<\/script>',
                                html, re.S)
        if data_match:
            for matches in data_match:
                json_data = json.loads(matches)
                if 'episode' in json_data:
                    for episode in json_data['episode']:
                        programme_id = ''
                        programme_id = episode['identifier']

                        name = ''
                        name = episode['name']
                        title = "[B]%s[/B] - %s" % (masthead_title, name)

                        image = ''
                        image = episode['image']

                        synopsis = ''
                        synopsis = episode['description']

                        url = "https://www.bbc.co.uk/sounds/play/%s" % programme_id
                        CheckAutoplay(title, url, image, synopsis, '')

                        percent = int(100*(page+list_item_num/len(json_data['episode']))/total_pages)
                        pDialog.update(percent,translation(30319),name)

                        list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))


    if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 136, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()



def GetCategoryPage(category, just_episodes=False):

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

    page_base_url = category
    page_url = page_base_url+'?sort=title'
    # print('Opening '+page_url)
    html = OpenURL(page_url)

    total_pages = 1
    current_page = 1
    page_range = list(range(1))
    paginate = re.search(r'pagination-button__number',html)
    next_page = 1
    if paginate:
        pages = re.findall(r'class="sc-c-pagination-button__number.*?</li>', html, flags=(re.DOTALL | re.MULTILINE))
        if pages:
            last = pages[-1]
            last_page = re.search(r'<span>(.*?)</span>',last)
            total_pages = int(last_page.group(1))
            page_range = list(range(1, total_pages+1))

    for page in page_range:
        # print('Processing page '+str(page))
        if page > current_page:
            page_url = page_base_url+'?page='+str(page)+'&sort=title'
            # print(page_url)
            html = OpenURL(page_url)
        match = re.search(r'window.__PRELOADED_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
        if match:
            data = match.group(1)
            json_data = json.loads(data)
            # print(json_data)
            if 'modules' in json_data:
                # print('Has modules')
                if 'data' in json_data['modules']:
                    # print('Has data')
                    for data in json_data['modules']['data']:
                        # print('Data-ID: '+data['id'])
                        if ('id' in data and data['id'] == 'container_list'):
                            if 'data' in data:
                               for programme in data['data']:
                                   # print(programme)
                                   pro_name = []
                                   pro_url = []
                                   pro_icon = []
                                   pro_syn = []
                                   pro_brand = []
                                   pro_brand_url = []
                                   pro_brand_syn = []
                                   if 'titles' in programme:
                                       pro_name = programme['titles']['primary']
                                   if ('secondary' in programme['titles'] and programme['titles']['secondary'] is not None):
                                       pro_name += ' - '+programme['titles']['secondary']
                                   if ('tertiary' in programme['titles'] and programme['titles']['tertiary'] is not None):
                                       pro_name += ' - '+programme['titles']['tertiary']
                                   if 'image_url' in programme:
                                       pro_icon = programme['image_url'].replace("{recipe}","624x624")
                                   if 'urn' in programme:
                                       pro_url = 'https://www.bbc.co.uk/sounds/play/'+programme['urn'][-8:]
                                   if 'synopses' in programme:
                                       if ('long' in programme['synopses'] and programme['synopses']['long'] is not None):
                                           pro_syn = programme['synopses']['long']
                                       elif ('medium' in programme['synopses'] and programme['synopses']['medium'] is not None):
                                           pro_syn = programme['synopses']['medium']
                                       elif ('short' in programme['synopses'] and programme['synopses']['short'] is not None):
                                           pro_syn = programme['synopses']['short']
                                   # print(pro_name)
                                   # print(pro_icon)
                                   # print(pro_url)
                                   # print(pro_syn)
                                   CheckAutoplay(pro_name, pro_url, pro_icon, pro_syn, '')
                                   if ('container' in programme and programme['container'] is not None):
                                       # print('Has container')
                                       if programme['container']['type'] == 'brand':
                                           pro_brand = '[B]'+programme['container']['title']+'[/B]'
                                           pro_brand_url = 'https://www.bbc.co.uk/sounds/brand/'+programme['container']['id']
                                           # print(pro_brand_url)
                                           if 'synopses' in programme['container']:
                                               if ('long' in programme['container']['synopses'] and
                                                   programme['container']['synopses']['long'] is not None):
                                                    pro_brand_syn = programme['container']['synopses']['long']
                                               elif ('medium' in programme['container']['synopses'] and
                                                     programme['container']['synopses']['medium'] is not None):
                                                    pro_brand_syn = programme['container']['synopses']['medium']
                                               elif ('short' in programme['container']['synopses'] and
                                                     programme['container']['synopses']['short'] is not None):
                                                   pro_brand_syn = programme['container']['synopses']['short']
                                           if not(page_base_url.startswith(pro_brand_url)):
                                               AddMenuEntry(pro_brand, pro_brand_url, 137, pro_icon, pro_brand_syn, '')
        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)


def GetEpisodes(url):
    new_url = 'https://www.bbc.co.uk/programmes/%s/episodes/player' % url
    GetPage(new_url,True)


def AddAvailableLiveStreamItem(name, channelname, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate."""
    streams = ParseStreams(channelname)
    # print('Located live streams')
    # print(streams)
    source = int(ADDON.getSetting('radio_source'))
    if source > 0:
        # Case 1: Selected source
        match = [x for x in streams if (x[2] == source)]
        if len(match) == 0:
            # Fallback: Use any source and any bitrate
            match = streams
    else:
        # Case 3: Any source
        # Play highest available bitrate
        match = streams
    PlayStream(name, match[0][0], iconimage, '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage):
    streams = ParseStreams(channelname)
    suppliers = ['', 'Akamai', 'Limelight', 'Cloudfront']
    for href, protocol, supplier, transfer_format, bitrate in streams:
        title = name + ' - [I][COLOR ffd3d3d3]%s - %s kbps[/COLOR][/I]' % (suppliers[supplier], bitrate)
        AddMenuEntry(title, href, 211, iconimage, '', '', '')


def PlayStream(name, url, iconimage, description, subtitles_url):
    html = OpenURL(url)

    check_geo = re.search(
        '<H1>Access Denied</H1>', html)
    if check_geo or not html:
        # print "Geoblock detected, raising error message"
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30400), translation(30401))
        raise
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon':'DefaultVideo.png', 'thumb':iconimage})

    liz.setInfo(type='Audio', infoLabels={'Title': name})
    liz.setProperty("IsPlayable", "true")
    liz.setPath(url)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""

    streams = ParseStreams(stream_id)
    suppliers = ['', 'Akamai', 'Limelight', 'Cloudfront']
    for href, protocol, supplier, transfer_format, bitrate in streams:
        title = name + ' - [I][COLOR ffd3d3d3]%s - %s kbps[/COLOR][/I]' % (suppliers[supplier], bitrate)
        AddMenuEntry(title, href, 211, iconimage, description, '', '')


def AddAvailableStreamItem(name, url, iconimage, description):
    """Play a streamm based on settings for preferred catchup source and bitrate."""
    stream_ids = ScrapeAvailableStreams(url)
    if len(stream_ids) < 1:
        #TODO check CBeeBies for special cases
        xbmcgui.Dialog().ok(translation(30403), translation(30404))
        return
    streams = ParseStreams(stream_ids)
    source = int(ADDON.getSetting('radio_source'))
    if source > 0:
        # Case 1: Selected source
        match = [x for x in streams if (x[2] == source)]
        if len(match) == 0:
            # Fallback: Use any source and any bitrate
            match = streams
    else:
        # Case 3: Any source
        # Play highest available bitrate
        match = streams
    PlayStream(name, match[0][0], iconimage, description, '')



def ListAtoZ():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    characters = [
        ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
        ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
        ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
        ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
        ('Y', 'y'), ('Z', 'z'), ('0-9', '@')]

    for name, url in characters:
        url = 'https://www.bbc.co.uk/programmes/a-z/by/%s/player' % url
        AddMenuEntry(name, url, 138, '', '', '')


def ListGenres():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    genres = []
    html = OpenURL('https://www.bbc.co.uk/sounds/categories')
    match = re.search(r'window.__PRELOADED_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        # print(json_data)
        if 'modules' in json_data:
            if 'data' in json_data['modules']:
                for type_id in json_data['modules']['data']:
                    # print(type_id)
                    if 'data' in type_id:
                        for category in type_id['data']:
                            # print(category)
                            cat_name = []
                            cat_image = []
                            cat_url = []
                            if 'titles' in category:
                                cat_name = category['titles']['primary']
                                if ('secondary' in category['titles'] and category['titles']['secondary'] is not None):
                                    cat_name += ' - '+category['titles']['secondary']
                                if ('tertiary' in category['titles'] and category['titles']['tertiary'] is not None):
                                    cat_name += ' - '+category['titles']['tertiary']
                            if 'image_url' in category:
                                cat_image = category['image_url'].replace("{recipe}","624x624")
                            if 'id' in category:
                                cat_url = 'https://www.bbc.co.uk/sounds/category/'+category['id']
                            # print(cat_name)
                            # print(cat_image)
                            # print(cat_url)
                            AddMenuEntry(cat_name, cat_url, 137, cat_image, '', '')


def ListLive():
    channel_list = [
        ('bbc_radio_one', 'BBC Radio 1'),
        ('bbc_1xtra', 'BBC Radio 1Xtra'),
        ('bbc_radio_two', 'BBC Radio 2'),
        ('bbc_radio_three', 'BBC Radio 3'),
        ('bbc_radio_fourfm', 'BBC Radio 4 FM'),
        ('bbc_radio_fourlw', 'BBC Radio 4 LW'),
        ('bbc_radio_four_extra', 'BBC Radio 4 Extra'),
        ('bbc_radio_five_live', 'BBC Radio 5 live'),
        ('bbc_radio_five_live_sports_extra', 'BBC Radio 5 live sports extra'),
        ('bbc_6music', 'BBC Radio 6 Music'),
        ('bbc_asian_network', 'BBC Asian Network'),
        ('bbc_radio_scotland_fm', 'BBC Radio Scotland'),
        ('bbc_radio_nan_gaidheal', u'BBC Radio nan Gàidheal'),
        ('bbc_radio_ulster', 'BBC Radio Ulster'),
        ('bbc_radio_foyle', 'BBC Radio Foyle'),
        ('bbc_radio_wales_fm', 'BBC Radio Wales'),
        ('bbc_radio_cymru', 'BBC Radio Cymru'),
        ('bbc_radio_berkshire', 'BBC Radio Berkshire'),
        ('bbc_radio_bristol', 'BBC Radio Bristol'),
        ('bbc_radio_cambridge', 'BBC Radio Cambridgeshire'),
        ('bbc_radio_cornwall', 'BBC Radio Cornwall'),
        ('bbc_radio_coventry_warwickshire', 'BBC Coventry & Warwickshire'),
        ('bbc_radio_cumbria', 'BBC Radio Cumbria'),
        ('bbc_radio_derby', 'BBC Radio Derby'),
        ('bbc_radio_devon', 'BBC Radio Devon'),
        ('bbc_radio_essex', 'BBC Essex'),
        ('bbc_radio_gloucestershire', 'BBC Radio Gloucestershire'),
        ('bbc_radio_guernsey', 'BBC Radio Guernsey'),
        ('bbc_radio_hereford_worcester', 'BBC Hereford & Worcester'),
        ('bbc_radio_humberside', 'BBC Radio Humberside'),
        ('bbc_radio_jersey', 'BBC Radio Jersey'),
        ('bbc_radio_kent', 'BBC Radio Kent'),
        ('bbc_radio_lancashire', 'BBC Radio Lancashire'),
        ('bbc_radio_leeds', 'BBC Radio Leeds'),
        ('bbc_radio_leicester', 'BBC Radio Leicester'),
        ('bbc_radio_lincolnshire', 'BBC Radio Lincolnshire'),
        ('bbc_london', 'BBC Radio London'),
        ('bbc_radio_manchester', 'BBC Radio Manchester'),
        ('bbc_radio_merseyside', 'BBC Radio Merseyside'),
        ('bbc_radio_newcastle', 'BBC Newcastle'),
        ('bbc_radio_norfolk', 'BBC Radio Norfolk'),
        ('bbc_radio_northampton', 'BBC Radio Northampton'),
        ('bbc_radio_nottingham', 'BBC Radio Nottingham'),
        ('bbc_radio_oxford', 'BBC Radio Oxford'),
        ('bbc_radio_sheffield', 'BBC Radio Sheffield'),
        ('bbc_radio_shropshire', 'BBC Radio Shropshire'),
        ('bbc_radio_solent', 'BBC Radio Solent'),
        ('bbc_radio_somerset_sound', 'BBC Somerset'),
        ('bbc_radio_stoke', 'BBC Radio Stoke'),
        ('bbc_radio_suffolk', 'BBC Radio Suffolk'),
        ('bbc_radio_surrey', 'BBC Surrey'),
        ('bbc_radio_sussex', 'BBC Sussex'),
        ('bbc_tees', 'BBC Tees'),
        ('bbc_three_counties_radio', 'BBC Three Counties Radio'),
        ('bbc_radio_wiltshire', 'BBC Wiltshire'),
        ('bbc_wm', 'BBC WM 95.6'),
        ('bbc_radio_york', 'BBC Radio York'),
    ]
    for id, name in channel_list:
        iconimage = 'resource://resource.images.iplayerwww/media/'+id+'.png'
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 213, iconimage, '', '')
        else:
            AddMenuEntry(name, id, 133, iconimage, '', '')


def ListListenList():
    """Scrapes all episodes of the favourites page."""
    html = OpenURL('http://www.bbc.co.uk/radio/favourites')

    programmes = html.split('<div class="favourites box-link favourite ')
    for programme in programmes:

        if not programme.startswith('media'):
            continue

        data_available_match = re.search(r'data-is-available="(.*?)"', programme)
        if ((not data_available_match) or (data_available_match.group(1) == '')):
            continue

        series_id = ''
        series_name = ''
        series_id_match = re.search(r'<a href="/programmes/(.*?)" class="media__meta-row size-f clr-light-grey text--single-line">\s*(.*?)\s*</a>',programme)
        if series_id_match:
            series_name = series_id_match.group(2)
            series_id = series_id_match.group(1)

        episode_name = ''
        episode_id = ''
        episode_id_match = re.search(r'<a aria-label="(.*?) Duration: (.*?)" class="favourites__brand-link(.*?)" href="/programmes/(.*?)#play">',programme)
        if episode_id_match:
            episode_name = episode_id_match.group(1)
            episode_id = episode_id_match.group(4)

        episode_image = ''
        episode_image_match = re.search(r'<img alt="" class="favourites__brand-image media__image " src="(.*?)"',programme)
        if episode_image_match:
            episode_image = "http:%s" % episode_image_match.group(1)

        series_image = ''
        series_image_match = re.search(r'<img class="media__image avatar-image--small" src="(.*?)">',programme)
        if series_image_match:
            series_image = "http:%s" % series_image_match.group(1)
            series_image = re.sub(r'96x96','640x360',series_image)

        station = ''
        station_match = re.search(r'<span class="favourites__network-name.*?<a href="(.*?)" class="clr-light-grey">\s+?(.*?)\s+?<',programme, flags=(re.DOTALL | re.MULTILINE))
        if station_match:
            station = station_match.group(2).strip()

        description = ''
        description_match = re.search(r'<p class="favourites__description media__meta-row size-f clr-white.*?">\s+?(.*?)\s+?</p>',programme, flags=(re.DOTALL | re.MULTILINE))
        if description_match:
            description = description_match.group(1).strip()

        if series_id:
            series_title = "[B]%s - %s[/B]" % (station, series_name)
            AddMenuEntry(series_title, series_id, 131, series_image, description, '')

        if episode_id:
            if series_name:
                episode_title = "[B]%s[/B] - %s - %s" % (station, series_name, episode_name)
                episode_url = "http://www.bbc.co.uk/programmes/%s" % episode_id
            else:
                episode_title = "[B]%s[/B] - %s" % (station, episode_name)
                episode_url = "http://www.bbc.co.uk/radio/play/%s" % episode_id
            # xbmc.log(episode_url)
            CheckAutoplay(episode_title, episode_url, episode_image, ' ', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)


def ListFollowing():
    """Scrapes all episodes of the favourites page."""
    html = OpenURL('https://www.bbc.co.uk/radio/favourites/programmes')

    programmes = html.split('<div class="favourites follow ')
    for programme in programmes:

        if not programme.startswith('media'):
            continue

        series_id = ''
        series_name = ''
        series_id_match = re.search(r'<a aria-label="(.*?)" class="follows__image-link" href="http://www.bbc.co.uk/programmes/(.*?)">',programme)
        if series_id_match:
            series_name = series_id_match.group(1)
            series_id = series_id_match.group(2)

        episode_name = ''
        episode_id = ''
        episode_id_match = re.search(r'<a aria-label="(.*?)" class="size-e clr-white" href="http://www.bbc.co.uk/programmes/(.*?)#play"',programme)
        if episode_id_match:
            episode_name = episode_id_match.group(1)
            episode_id = episode_id_match.group(2)

        episode_image = ''
        series_image = ''
        series_image_match = re.search(r'<img class="media__image" src="(.*?)"',programme)
        if series_image_match:
            series_image = "https:%s" % series_image_match.group(1)
            episode_image = series_image

        station = ''
        station_match = re.search(r'<a href="(.*?)" class="clr-light-grey">\s*(.*?)\s*</a>',programme, flags=(re.DOTALL | re.MULTILINE))
        if station_match:
            station = station_match.group(2).strip()

        description = ''

        if series_id:
            series_title = "[B]%s - %s[/B]" % (station, series_name)
            AddMenuEntry(series_title, series_id, 131, series_image, description, '')

        if episode_id:
            if series_name:
                episode_title = "[B]%s[/B] - %s - %s" % (station, series_name, episode_name)
            else:
                episode_title = "[B]%s[/B] - %s" % (station, episode_name)
            episode_url = "http://www.bbc.co.uk/programmes/%s" % episode_id
            # xbmc.log(episode_url)
            CheckAutoplay(episode_title, episode_url, episode_image, ' ', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)


def ListMostPopular():
    html = OpenURL('http://www.bbc.co.uk/radio/popular')

    programmes = re.split(r'<li class="(episode|clip) typical-list-item', html)
    for programme in programmes:

        if not programme.startswith(" item-idx-"):
            continue

        programme_id = ''
        programme_id_match = re.search(r'<a href="/programmes/(.*?)"', programme)
        if programme_id_match:
            programme_id = programme_id_match.group(1)

        name = ''
        name_match = re.search(r'<img src=".*?" alt="(.*?)"', programme)
        if name_match:
            name = name_match.group(1)

        subtitle = ''
        subtitle_match = re.search(r'<span class="subtitle">\s*(.+?)\s*</span>', programme)
        if subtitle_match:
            if subtitle_match.group(1).strip():
                subtitle = "(%s)" % subtitle_match.group(1)

        image = ''
        image_match = re.search(r'<img src="(.*?)"', programme)
        if image_match:
            image = image_match.group(1)

        station = ''
        station_match = re.search(r'<span class="service_title">\s*(.+?)\s*</span>', programme)
        if station_match:
            station = station_match.group(1)

        title = "[B]%s[/B] - %s %s" % (station, name, subtitle)

        if programme_id and title and image:
            url = "http://www.bbc.co.uk/radio/play/%s" % programme_id
            CheckAutoplay(title, url, image, ' ', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)



def Search(search_entered):
    """Simply calls the online search function. The search is then evaluated in EvaluateSearch."""
    if search_entered is None:
        keyboard = xbmc.Keyboard('', 'Search iPlayer')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText()

    if search_entered is None:
        return False

    url = 'https://www.bbc.co.uk/sounds/search?q=%s' % search_entered
    html = OpenURL(url)

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

    total_pages = 1
    current_page = 1
    page_range = list(range(1))
    pages = re.findall(r'<div class="ssrcss-16didf7-StyledButtonContent e1b2sq420">(.+?)</div>',html)
    next_page = 1
    if pages:
        total_pages = int(pages[-2])
        page_base_url = url+'&page='
        page_range = list(range(1, total_pages+1))

    for page in page_range:

        if page > current_page:
            page_url = page_base_url + str(page)
            html = OpenURL(page_url)

        match = re.search(r'window.__INITIAL_DATA__=(.*?);\s*</script>', html, re.DOTALL)

        if match:
            data = match.group(1)
            json_data = json.loads(data)
            # print(json_data)
            if 'data' in json_data:
                # print('Has data')
                for data in json_data['data']:
                    if data.startswith('search-results'):
                        data = json_data['data'][data]
                    # print(data)
                    if ('name' in data and data['name'] == 'search-results'):
                        # print(data['name'])
                        if 'data' in data:
                           if 'initialResults' in data['data']:
                               if 'items' in data['data']['initialResults']:
                                   for programme in data['data']['initialResults']['items']:
                                       pro_name = []
                                       pro_url = []
                                       pro_icon = []
                                       pro_syn = []
                                       if 'headline' in programme:
                                           pro_name = programme['headline']
                                       if 'image' in programme:
                                           if 'src' in programme['image']:
                                               pro_icon = programme['image']['src'].replace("314x176","416x234")
                                       if 'url' in programme:
                                           pro_url = 'https://www.bbc.co.uk/sounds/play/'+programme['url'][-8:]
                                       if 'description' in programme:
                                           pro_syn = programme['description']
                                       # print(pro_name)
                                       # print(pro_icon)
                                       # print(pro_url)
                                       # print(pro_syn)
                                       CheckAutoplay(pro_name, pro_url, pro_icon, pro_syn, '')

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))


    if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 136, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()



def GetAvailableStreams(name, url, iconimage, description):
    """Calls AddAvailableStreamsDirectory based on user settings"""
    stream_ids = ScrapeAvailableStreams(url)
    # print('Scraped streams for '+url)
    # print(stream_ids)
    if stream_ids:
        AddAvailableStreamsDirectory(name, stream_ids, iconimage, description)


def ParseStreams(stream_id):
    retlist = []
    # print('Parsing streams for PID:')
    # print(stream_id)
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = 'https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/%s/format/json/jsfunc/JS_callbacks0' % stream_id
    # print(NEW_URL)
    html = OpenURL(NEW_URL)

    match = re.search(r'JS_callbacks0.*?\((.*?)\);', html, re.DOTALL)
    if match:
        json_data = json.loads(match.group(1))
        if json_data:
            # print(json.dumps(json_data, sort_keys=True, indent=2))
            if 'media' in json_data:
                for media in json_data['media']:
                    if 'kind' in media:
                        if media['kind'].startswith('audio'):
                            bitrate = ''
                            if 'bitrate' in media:
                                bitrate = media['bitrate']
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
                                        if ('akamai' in supplier):
                                            supplier = 1
                                        elif ('limelight' in supplier or 'll' in supplier):
                                            supplier = 2
                                        elif ('cloudfront' in supplier):
                                            supplier = 3
                                        else:
                                            supplier = 0
                                    if 'transferFormat' in connection:
                                        transfer_format = connection['transferFormat']
                                    if transfer_format == 'dash':
                                        retlist.append((href, protocol, supplier, transfer_format, bitrate))
            elif 'result' in json_data:
                if json_data['result'] == 'geolocation':
                    # print "Geoblock detected, raising error message"
                    dialog = xbmcgui.Dialog()
                    dialog.ok(translation(30400), translation(30401))
                    raise
    return retlist


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    stream_id_st = None
    # Search for standard programmes.
    stream_id_st = re.compile('"vpid":"(.+?)"').findall(html)
    if not stream_id_st:
        match = re.search(r'window.__PRELOADED_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
        if match:
            data = match.group(1)
            json_data = json.loads(data)
            stream_id_st = json_data['programmes']['current']['id']
            # print json.dumps(json_data, indent=2, sort_keys=True)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30400), translation(30412))
            raise
    return stream_id_st


def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 212, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 132, iconimage, plot, '', aired=aired)

