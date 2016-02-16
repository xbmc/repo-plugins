# -*- coding: utf-8 -*-

import sys
import re
from operator import itemgetter
from ipwww_common import translation, AddMenuEntry, OpenURL, \
                         CheckLogin, CreateBaseDirectory

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')


def GetPage(page_url, just_episodes=False):
    """   Generic Radio page scraper.   """

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

    html = OpenURL(page_url)

    total_pages = 1
    current_page = 1
    page_range = range(1)
    paginate = re.search(r'<ol.+?class="pagination.*?</ol>',html)
    next_page = 1
    if paginate:
        if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
            current_page_match = re.search(r'page=(\d*)', page_url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
            page_range = range(current_page, current_page+1)
            next_page_match = re.search(r'<li class="pagination__next"><a href="(.*?page=)(.*?)">', paginate.group(0))
            if next_page_match:
                page_base_url = next_page_match.group(1)
                next_page = int(next_page_match.group(2))
            else:
                next_page = current_page
            page_range = range(current_page, current_page+1)
        else:
            pages = re.findall(r'<li.+?class="pagination__page.*?</li>',paginate.group(0))
            if pages:
                last = pages[-1]
                last_page = re.search(r'<a.+?href="(.*?=)(.*?)"',last)
                page_base_url = last_page.group(1)
                total_pages = int(last_page.group(2))
            page_range = range(1, total_pages+1)

    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)

        masthead_title = ''
        masthead_title_match = re.search(r'<div.+?id="programmes-main-content".*?<span property="name">(.+?)</span>', html)
        if masthead_title_match:
            masthead_title = masthead_title_match.group(1)

        list_item_num = 1

        programmes = html.split('<div class="programme ')
        for programme in programmes:

            if not programme.startswith("programme--radio"):
                continue

            if "available" not in programme: #TODO find a more robust test
                continue

            series_id = ''
            series_id_match = re.search(r'<a class="iplayer-text js-lazylink__link" href="/programmes/(.+?)/episodes/player"', programme)
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

            subtitle = ''
            subtitle_match = re.search(r'<span class="programme__subtitle.+?property="name">(.*?)</span>(.*?property="name">(.*?)</span>)?', programme)
            if subtitle_match:
                series = subtitle_match.group(1)
                episode = subtitle_match.group(3)
                if episode:
                    subtitle = "(%s, %s)" % (series, episode)
                else:
                    if series.strip():
                        subtitle = "(%s)" % series

            image = ''
            image_match = re.search(r'<meta property="image" content="(.+?)" />', programme)
            if image_match:
                image = image_match.group(1)

            synopsis = ''
            synopsis_match = re.search(r'<span property="description">(.+?)</span>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)

            station = ''
            station_match = re.search(r'<p class="programme__service.+?<strong>(.+?)</strong>.*?</p>', programme)
            if station_match:
                station = station_match.group(1).strip()

            series_title = "[B]%s - %s[/B]" % (station, name)
            if just_episodes:
                title = "[B]%s[/B] - %s" % (masthead_title, name)
            else:
                title = "[B]%s[/B] - %s %s" % (station, name, subtitle)

            if series_id:
                AddMenuEntry(series_title, series_id, 131, image, synopsis, '')
            elif programme_id: #TODO maybe they are not always mutually exclusive

                url = "http://www.bbc.co.uk/programmes/%s" % programme_id
                CheckAutoplay(title, url, image, ' ', '')

            percent = int(100*(page+list_item_num/len(programmes))/total_pages)
            pDialog.update(percent,translation(30319),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))

    if int(ADDON.getSetting('radio_paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry(" [COLOR orange]%s >>[/COLOR]" % translation(30320), page_url, 136, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()



def GetEpisodes(url):
    new_url = 'http://www.bbc.co.uk/programmes/%s/episodes/player' % url
    GetPage(new_url,True)



def AddAvailableLiveStreamItem(name, channelname, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate."""
    
    stream_bitrates = [128] #TODO add more bitrates
    if int(ADDON.getSetting('radio_source')) == 1:
        providers = [('ak', 'Akamai')]
    elif int(ADDON.getSetting('radio_source')) == 2:
        providers = [('llnw', 'Limelight')]
    else:
        providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    bitrate_selected = 0 #TODO int(ADDON.getSetting('live_bitrate'))
    for provider_url, provider_name in providers:
        # First we query the available streams from this website

        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hds/uk/high/%s/%s.f4m' % (provider_url, channelname)
        html = OpenURL(url)
        # Use regexp to get the different versions using various bitrates
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html)
        streams_available = []
        for address, bitrate in match:
            url = address.replace('f4m', 'm3u8')
            streams_available.append((int(bitrate), url))
        streams_available.sort(key=lambda x: x[0], reverse=True)

        # Play the prefered option
        if bitrate_selected > 0:
            match = [x for x in streams_available if (x[0] == stream_bitrates[bitrate_selected])]
            if len(match) == 0:
                # Fallback: Use any lower bitrate from any source.
                match = [x for x in streams_available if (x[0] in range(1, stream_bitrates[bitrate_selected - 1] + 1))]
                match.sort(key=lambda x: x[0], reverse=True)

            PlayStream(name, match[0][1], iconimage, '', '')
        # Play the fastest available stream of the preferred provider
        else:
            PlayStream(name, streams_available[0][1], iconimage, '', '')


def AddAvailableLiveStreamItemHQ(name, channelname, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate."""

    if int(ADDON.getSetting('radio_source')) == 1:
        providers = [('ak', 'Akamai')]
    elif int(ADDON.getSetting('radio_source')) == 2:
        providers = [('llnw', 'Limelight')]
    else:
        providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]

    for provider_url, provider_name in providers:
        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/uk/sbr_high/%s/%s.m3u8' % (provider_url, channelname)
        PlayStream(name, url, iconimage, '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
    """
    providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    streams = []
    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        #TODO add high bitrate streams
        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hds/uk/high/%s/%s.f4m' % (provider_url, channelname)
        html = OpenURL(url)

        # Use regexp to get the different versions using various bitrates
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html)
        # Add provider name to the stream list.
        streams.extend([list(stream) + [provider_name] for stream in match])

    # Add each stream to the Kodi selection menu.
    for address, bitrate, provider_name in sorted(streams, key=lambda x: int(x[1]), reverse=True):
        url = address.replace('f4m', 'm3u8')
        # For easier selection use colors to indicate high and low bitrate streams
        bitrate = int(bitrate)
        if bitrate > 192:
            color = 'green'
        elif bitrate > 128:
            color = 'yellow'
        elif bitrate > 64:
            color = 'orange'
        else:
            color = 'red'

        title = name + ' - [I][COLOR %s]%d Kbps[/COLOR] [COLOR white]%s[/COLOR][/I]' % (
            color, bitrate , provider_name)
        # Finally add them to the selection menu.
        #TODO find radio icons
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
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Audio', infoLabels={'Title': name})
    liz.setProperty("IsPlayable", "true")
    liz.setPath(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""

    streams = ParseStreams(stream_id)

    suppliers = ['', 'Akamai', 'Limelight', 'Level3']
    for supplier, bitrate, url, encoding in sorted(streams[0], key=itemgetter(1), reverse=True):
        bitrate = int(bitrate)
        if bitrate >= 320:
            color = 'green'
        elif bitrate >= 192:
            color = 'blue'
        elif bitrate >= 128:
            color = 'yellow'
        else:
            color = 'orange'
        title = name + ' - [I][COLOR %s]%d Kbps %s[/COLOR] [COLOR lightgray]%s[/COLOR][/I]' % (
            color, bitrate, encoding, suppliers[supplier])
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
        url = 'http://www.bbc.co.uk/radio/programmes/a-z/by/%s/current' % url
        AddMenuEntry(name, url, 136, '', '', '')


def ListGenres():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    genres = []
    html = OpenURL('http://www.bbc.co.uk/radio/programmes/genres')
    mains = html.split('<li class="category br-keyline highlight-box--list">')

    for main in mains:
        current_main_match = re.search(r'<a.+?class="beta box-link".+?href="(.+?)">(.+?)</a>',main)
        if current_main_match:
            genres.append((current_main_match.group(1), current_main_match.group(2), True))
            current_sub_match = re.findall(r'<a.+?class="box-link".+?href="(.+?)">(.+?)</a>',main)
            for sub_match_url, sub_match_name in current_sub_match:
                genres.append((sub_match_url, current_main_match.group(2)+' - '+sub_match_name, False))

    for url, name, group in genres:
        new_url = 'http://www.bbc.co.uk%s/player/episodes' % url
        if group:
            AddMenuEntry("[B]%s[/B]" % name, new_url, 136, '', '', '')
        else:
            AddMenuEntry("%s" % name, new_url, 136, '', '', '')

    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)


def ListLive():
    channel_list = [
        ('bbc_radio_one', 'BBC Radio 1'),
        ('bbc_1xtra', 'BBC Radio 1Xtra'),
        ('bbc_radio_two', 'BBC Radio 2'),
        ('bbc_radio_three', 'BBC Radio 3'),
        ('bbc_radio_fourfm', 'BBC Radio 4'),
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
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 213, '', '', '')
        else:
            AddMenuEntry(name, id, 133, '', '', '')


def ListLiveHQ():
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
    ]
    for id, name in channel_list:
        AddMenuEntry(name, id, 214, '', '', '')



def ListFavourites(logged_in):
    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('audio')
        return

    """Scrapes all episodes of the favourites page."""
    html = OpenURL('http://www.bbc.co.uk/radio/favourites')

    programmes = html.split('<li class="my-item" data-appid="radio" ')
    for programme in programmes:

        if not programme.startswith('data-type="tlec"'):
            continue

        series_id = ''
        series_id_match = re.search(r'data-id="(.*?)"', programme)
        if series_id_match:
            series = series_id_match.group(1)

        programme_id = ''
        programme_id_match = re.search(r'<a href="http://www.bbc.co.uk/programmes/(.*?)"', programme)
        if programme_id_match:
            programme_id = programme_id_match.group(1)

        name = ''
        name_match = re.search(r'<span class="my-episode-brand" itemprop="name">(.*?)</span>', programme)
        if name_match:
            name = name_match.group(1)

        episode = ''
        episode_match = re.search(r'<span class="my-episode" itemprop="name">(.*?)</span>', programme)
        if episode_match:
            episode = "(%s)" % episode_match.group(1)

        image = ''
        image_match = re.search(r'itemprop="image" src="(.*?)"', programme)
        if image_match:
            image = image_match.group(1)

        synopsis = ''
        synopsis_match = re.search(r'<span class="my-item-info">(.*?)</span>', programme)
        if synopsis_match:
            synopsis = synopsis_match.group(1)

        station = ''
        station_match = re.search(r'<span class="my-episode-broadcaster" itemprop="name">(.*?)\.</span>', programme)
        if station_match:
            station = station_match.group(1).strip()

        title = "[B]%s - %s[/B]" % (station, name)
        episode_title = "[B]%s[/B] - %s %s" % (station, name, episode)

        if series:
            AddMenuEntry(title, series, 131, image, synopsis, '')

        if programme_id:
            url = "http://www.bbc.co.uk/programmes/%s" % programme_id
            CheckAutoplay(episode_title, url, image, ' ', '')

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
            url = "http://www.bbc.co.uk/programmes/%s" % programme_id
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
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id[0]
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'media.+?bitrate="(.+?)".+?encoding="(.+?)".+?connection.+?href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    for bitrate, encoding, m3u8_url, supplier, transfer_format in match:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_hls_open':
                tmp_sup = 1
            elif supplier == 'limelight_hls_open': #NOTE: just guessing?
                tmp_sup = 2

            m3u8_html = OpenURL(m3u8_url)
            m3u8_match = re.compile('BANDWIDTH=(.+?),.*?CODECS="(.+?)"\n(.+?)\n').findall(m3u8_html)
            for bandwidth, codecs, stream in m3u8_match:
                url = stream
                retlist.append((tmp_sup, bitrate, url, encoding))

    return retlist, match


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    # Search for standard programmes.
    stream_id_st = re.compile('"vpid":"(.+?)"').findall(html)
    return stream_id_st


def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 212, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 132, iconimage, plot, '', aired=aired)

