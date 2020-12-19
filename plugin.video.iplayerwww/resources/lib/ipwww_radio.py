# -*- coding: utf-8 -*-

import sys
import os
import re
from operator import itemgetter
from ipwww_common import translation, AddMenuEntry, OpenURL, \
                         CheckLogin, CreateBaseDirectory

major_version = sys.version_info.major
import xbmc
if major_version == 3:
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

        programmes = html.split('<li class="grid one-whole">')
        for programme in programmes:

            if not re.search(r'programme--radio', programme):
                continue

            series_id = ''
            series_id_match = re.search(r'data-lazylink-inc="/programmes/(.+?)/episodes/player.inc"', programme)
            if series_id_match:
                series_id = series_id_match.group(1)

            programme_id = ''
            programme_id_match = re.search(r'data-pid="(.+?)"', programme)
            if programme_id_match:
                programme_id = programme_id_match.group(1)

            name = ''
            name_match = re.search(r'<span property="name">(.+?)</span>', programme)
            if name_match:
                name = name_match.group(1)
            else:
                alternative_name_match = re.search(r'<meta property="name" content="([^"]+?)"', programme)
                if alternative_name_match:
                    name = alternative_name_match.group(1)

            image = ''
            image_match = re.search(r'<meta property="image" content="(.+?)" />', programme)
            if image_match:
                image = image_match.group(1)

            synopsis = ''
            synopsis_match = re.search(r'<span property="description">(.+?)<\/span>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)

            station = ''
            station_match = re.search(r'<p class="programme__service.+?<strong>(.+?)<\/strong>.*?<\/p>', programme)
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
                url = "http://www.bbc.co.uk/radio/play/%s" % programme_id
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
            json_data = json.loads(data_match[0])

            for episode in json_data['episode']:
                programme_id = ''
                programme_id = episode['identifier']

                name = ''
                name = episode['name']
                title = "[B]%s[/B] - %s" % (masthead_title, name)

                imafe = ''
                image = episode['image']

                synopsis = ''
                synopsis = episode['description']

                url = "http://www.bbc.co.uk/radio/play/%s" % programme_id
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



def GetCategoryPage(page_url, just_episodes=False):

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

    html = OpenURL(page_url)

    total_pages = 1
    current_page = 1
    page_range = list(range(1))
    paginate = re.search(r'pgn__list',html)
    next_page = 1
    if paginate:
        if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
            current_page_match = re.search(r'page=(\d*)', page_url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
                main_base_url = re.search(r'(.+?)\?.+?', page_url).group(1)
            else:
                main_base_url = page_url
            page_range = list(range(current_page, current_page+1))
            next_page_match = re.search(r'pgn__page--next.*?href="(.*?page=)(.*?)"', html)
            if next_page_match:
                page_base_url = main_base_url + next_page_match.group(1)
                next_page = int(next_page_match.group(2))
            else:
                next_page = current_page
            page_range = list(range(current_page, current_page+1))
        else:
            pages = re.findall(r'<li class="pgn__page.*?</li>', html, flags=(re.DOTALL | re.MULTILINE))
            if pages:
                last = pages[-2]
                last_page = re.search(r'href=".*?page=(.*?)"',last)
                page_base_url = page_url + '?page='
                total_pages = int(last_page.group(1))
            page_range = list(range(1, total_pages+1))

    for page in page_range:

        if page > current_page:
            page_url = page_base_url + str(page)
            html = OpenURL(page_url)

        list_item_num = 1

        programmes = html.split('<div class="programme-item')
        for programme in programmes:

            series_id = ''
            series_id_match = re.search(r'<a class="category-episodes" href="/programmes/(.+?)/episodes"', programme)
            if series_id_match:
                series_id = series_id_match.group(1)

            programme_id = ''
            programme_id_match = re.search(r'href="/programmes/(.+?)"', programme)
            if programme_id_match:
                programme_id = programme_id_match.group(1)

            name = ''
            name_match = re.search(r'<span class="programme-item-title.+?>(.+?)</span>', programme)
            if name_match:
                name = name_match.group(1)

            subtitle = ''
            subtitle_match = re.search(r'<p class="programme-item-subtitle.+?>(.+?)</p>', programme)
            if subtitle_match:
                subtitle = subtitle_match.group(1)

            image = ''
            image_match = re.search(r'class="media__image" src="(.+?)"', programme)
            if image_match:
                image = 'http://' + image_match.group(1)

            synopsis = ''
            synopsis_match = re.search(r'<p class="programme-item-synopsis.+?>(.+?)</p>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)

            station = ''
            station_match = re.search(r'class="programme-item-network.+?>\s*(.+?)\s*</a>', programme)
            if station_match:
                station = station_match.group(1).strip()

            series_title = "[B]%s - %s[/B]" % (station, name)
            title = "[B]%s[/B] - %s %s" % (station, name, subtitle)

            if series_id:
                AddMenuEntry(series_title, series_id, 131, image, synopsis, '')
            elif programme_id: #TODO maybe they are not always mutually exclusive

                url = "http://www.bbc.co.uk/radio/play/%s" % programme_id
                CheckAutoplay(title, url, image, ' ', '')

            percent = int(100*(page+list_item_num/len(programmes))/total_pages)
            pDialog.update(percent,translation(30319),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))


    if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 137, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()



def GetEpisodes(url):
    new_url = 'http://www.bbc.co.uk/programmes/%s/episodes/player' % url
    GetPage(new_url,True)



def AddAvailableLiveStreamItem(name, channelname, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate."""
    providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    location_qualities = {'uk' : ['sbr_vlow', 'sbr_low', 'sbr_med', 'sbr_high'], 'nonuk': ['sbr_vlow', 'sbr_low'] }
    location_settings = ['uk', 'nonuk']

    location = location_settings[int(ADDON.getSetting('radio_location'))]

    for provider_url, provider_name in providers:
        qualities = location_qualities[location]
        max_quality = int(ADDON.getSetting('radio_live_bitrate')) + 1
        max_quality = min(len(qualities),max_quality)
        qualities = qualities[0:max_quality]
        qualities.reverse()
        for quality in qualities:
            url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/%s/%s/%s/%s.m3u8' % (location, quality, provider_url, channelname)

            PlayStream(name, url, iconimage, '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
    """
    providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    location_qualities = {
                          'uk' : ['sbr_vlow', 'sbr_low', 'sbr_med', 'sbr_high'],
                          'nonuk': ['sbr_vlow', 'sbr_low']
                         }
    location_names = {'uk': 'UK', 'nonuk': 'International'}
    quality_colours = {
                       'sbr_vlow': 'ffff0000',
                       'sbr_low': 'ffffa500',
                       'sbr_med': 'ffffff00',
                       'sbr_high': 'ff008000'
                       }
    quality_bitrates = {
                        'sbr_vlow': '48',
                        'sbr_low': '96',
                        'sbr_med': '128',
                        'sbr_high': '320'
                       }

    for location in list(location_qualities.keys()):
        qualities = location_qualities[location]
        qualities.reverse()
        for quality in qualities:
            for provider_url, provider_name in providers:
                url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/%s/%s/%s/%s.m3u8' % (location, quality, provider_url, channelname)

                title = name + ' - [I][COLOR %s]%s Kbps[/COLOR] [COLOR fff1f1f1]%s[/COLOR] [COLOR ffb4b4b4]%s[/COLOR][/I]' % (
                    quality_colours[quality], quality_bitrates[quality] , location_names[location], provider_name)

                AddMenuEntry(title, url, 201, '', '', '')


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
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""

    streams = ParseStreams(stream_id)

    for supplier, bitrate, url, encoding in sorted(streams[0], key=itemgetter(1), reverse=True):
        bitrate = int(bitrate)
        if supplier == 1:
            supplier = 'Akamai'
        elif supplier == 2:
            supplier = 'Limelight'

        if bitrate >= 320:
            color = 'ff008000'
        elif bitrate >= 128:
            color = 'ffffff00'
        elif bitrate >= 96:
            color = 'ffffa500'
        else:
            color = 'ffff0000'

        title = name + ' - [I][COLOR %s]%d Kbps %s[/COLOR] [COLOR ffd3d3d3]%s[/COLOR][/I]' % (
            color, bitrate, encoding, supplier)
        AddMenuEntry(title, url, 201, iconimage, description, '', '')


def AddAvailableStreamItem(name, url, iconimage, description):
    """Play a streamm based on settings for preferred catchup source and bitrate."""
    stream_ids = ScrapeAvailableStreams(url)
    if len(stream_ids) < 1:
        #TODO check CBeeBies for special cases
        xbmcgui.Dialog().ok(translation(30403), translation(30404))
        return
    streams_all = ParseStreams(stream_ids)
    streams = streams_all[0]
    source = int(ADDON.getSetting('radio_source'))
    if source > 0:
        # Case 1: Selected source
        match = [x for x in streams if (x[0] == source)]
        if len(match) == 0:
            # Fallback: Use any source and any bitrate
            match = streams
        match.sort(key=lambda x: x[1], reverse=True)
    else:
        # Case 3: Any source
        # Play highest available bitrate
        match = streams
        match.sort(key=lambda x: x[1], reverse=True)
    PlayStream(name, match[0][2], iconimage, description, '')



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
        url = 'http://www.bbc.co.uk/programmes/a-z/by/%s/player' % url
        AddMenuEntry(name, url, 138, '', '', '')


def ListGenres():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    genres = []
    html = OpenURL('http://www.bbc.co.uk/radio/programmes/genres')
    mains = html.split('<div class="category__box island--vertical">')

    for main in mains:
        current_main_match = re.search(r'<a.+?class="gel-double-pica-bold".+?href="(.+?)">(.+?)</a>',main)
        if current_main_match:
            genres.append((current_main_match.group(1), current_main_match.group(2), True))
            current_sub_match = re.findall(r'<a.+?class="gel-long-primer-bold".+?href="(.+?)">(.+?)</a>',main)
            for sub_match_url, sub_match_name in current_sub_match:
                genres.append((sub_match_url, current_main_match.group(2)+' - '+sub_match_name, False))

    for url, name, group in genres:
        new_url = 'http://www.bbc.co.uk%s' % url
        if group:
            AddMenuEntry("[B]%s[/B]" % name, new_url, 137, '', '', '')
        else:
            AddMenuEntry("%s" % name, new_url, 137, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)


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
        if major_version == 2:
            iconimage = xbmc.translatePath(
                os.path.join('special://home/addons/plugin.video.iplayerwww/media', id + '.png'))
        elif major_version == 3:
            iconimage = xbmcvfs.translatePath(
                os.path.join('special://home/addons/plugin.video.iplayerwww/media', id + '.png'))
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 213, iconimage, '', '')
        else:
            AddMenuEntry(name, id, 133, iconimage, '', '')


def ListListenList(logged_in):
    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('audio')
        return

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


def ListFollowing(logged_in):
    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('audio')
        return

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

    url = 'http://www.bbc.co.uk/radio/programmes/a-z/by/%s/current' % search_entered
    GetPage(url)


def GetAvailableStreams(name, url, iconimage, description):
    """Calls AddAvailableStreamsDirectory based on user settings"""
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids:
        AddAvailableStreamsDirectory(name, stream_ids, iconimage, description)


def ParseStreams(stream_id):
    retlist = []
    # print "Parsing streams for PID: %s"%stream_id[0]
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/apple-ipad-hls/vpid/%s/proto/http?cb=%d" % (stream_id[0], random.randrange(10000,99999)) #NOTE magic from get_iplayer

    html = OpenURL(NEW_URL)

    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'media.+?bitrate="(.+?)".+?encoding="(.+?)"(.+?)<\/media>'
        ).findall(html)
    for bitrate, encoding, connections in match:
        stream = re.compile(
            '<connection.+?href="(.+?)".+?supplier="(.+?)"'
            ).findall(connections)
        for url, supplier in stream:
            if ('akamai' in supplier):
                supplier = 1
            elif ('limelight' in supplier):
                supplier = 2
            retlist.append((supplier, bitrate, url, encoding))

    return retlist, match


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
            # Note: Need to create list for backwards compatibility
            stream_id_st = [json_data['programmes']['current']['id']]
            # print json.dumps(json_data, indent=2, sort_keys=True)
    return stream_id_st


def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 212, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 132, iconimage, plot, '', aired=aired)

