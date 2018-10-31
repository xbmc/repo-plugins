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
from random import randint

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')


def CheckInputStreamAdaptiveAvailability():
    # If DASH is selected as stream_protocol, we need to check if inputstream.adaptive
    # is available and the version is correct.
    if xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)"):
        if (xbmcaddon.Addon(id='inputstream.adaptive').getAddonInfo('version') < "1.0.6"):
            # Version is smaller than 1.0.6, fall back to HLS
            ADDON.setSetting('stream_protocol','1')
            return False
        else:
            return True
    else:
        # inputstream.adaptive is not available, fall back to HLS
        ADDON.setSetting('stream_protocol','1')
        return False


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


def ListUHDTrial():
    channel_list = [
        ('uhd_stream_01',  'UHD Trial 1'),
        ('uhd_stream_02',  'UHD Trial 2'),
        ('uhd_stream_03',  'UHD Trial 3'),
        ('uhd_stream_04',  'UHD Trial 4'),
        ('uhd_stream_05',  'UHD Trial 5'),
    ]

    if int(ADDON.getSetting("stream_protocol")) == 1:
        xbmcgui.Dialog().notification(translation(30400), translation(30411), xbmcgui.NOTIFICATION_ERROR)
        return

    ia_available = CheckInputStreamAdaptiveAvailability()
    if ia_available:
        iconimage = xbmc.translatePath('special://home/addons/plugin.video.iplayerwww/media/red_button.png')
        for id, name in channel_list:
            AddMenuEntry(name, id, 205, iconimage, '', '')
    else:
        xbmcgui.Dialog().notification(translation(30400), translation(30411), xbmcgui.NOTIFICATION_ERROR)
        return


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
        ('bbc_one_hd',                       'BBC One'),
        ('bbc_two_hd',                       'BBC Two'),
        ('bbc_four_hd',                      'BBC Four'),
        ('cbbc_hd',                          'CBBC'),
        ('cbeebies_hd',                      'CBeebies'),
        ('bbc_news24',                       'BBC News Channel'),
        ('bbc_parliament',                   'BBC Parliament'),
        ('bbc_alba',                         'Alba'),
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
    html = OpenURL('https://www.bbc.co.uk/iplayer/a-z/%s' % url)

    # There is a new layout for episodes, scrape it from the JSON received as part of the page
    match = re.search(
              r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);',
              html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        # print json.dumps(json_data, indent=2, sort_keys=True)

        current_letter = json_data['appStoreState']['currentLetter']

        for item in json_data['appStoreState']['programmes'][current_letter]['entities']:
            meta = item.get("meta")
            item = item.get("props")
            if not item:
                continue

            main_url = None
            if 'href' in item:
                # Some strings already contain the full URL, need to work around this.
                url = item['href'].replace('http://www.bbc.co.uk','')
                url = url.replace('https://www.bbc.co.uk','')
                if url:
                    main_url = 'https://www.bbc.co.uk' + url

            num_episodes = None
            if 'episodesAvailable' in meta:
                if meta['episodesAvailable'] > 1:
                    num_episodes = str(meta['episodesAvailable'])

            title = ''
            if 'title' in item:
                if num_episodes:
                    title = item['title']+' - '+num_episodes+' episodes available'
                else:
                    title = item['title']

            synopsis = ''
            if 'synopsis' in item:
                synopsis = item['synopsis']

            icon = ''
            if 'imageTemplate' in item:
                icon = item['imageTemplate'].replace("{recipe}","832x468")

            if num_episodes:
                AddMenuEntry(title, main_url, 139, icon, synopsis, '')
            else:
                CheckAutoplay(title , main_url, icon, synopsis, '')


def GetMultipleEpisodes(url):
    html = OpenURL(url)
    # There is a new layout for episodes, scrape it from the JSON received as part of the page
    match = re.search(
              r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);',
              html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        # print json.dumps(json_data, indent=2, sort_keys=True)

        if json_data['episode']['tleo_id']:
            GetEpisodes(json_data['episode']['tleo_id'])


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
                split_page_url = page_url.split('?')
                page_base_url = split_page_url[0]
                for part in split_page_url[1:len(split_page_url)-1]:
                    if not part.startswith('page'):
                        page_base_url = page_base_url+'?'+part
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
                split_page_url = page_url.split('?')
                page_base_url = split_page_url[0]
                for part in split_page_url[1:len(split_page_url)-1]:
                    if not part.startswith('page'):
                        page_base_url = page_base_url+'?'+part
                page_base_url = page_base_url.replace('https://www.bbc.co.uk','')+'?page='
                total_pages = int(last_page.group(1))
            page_range = list(range(1, total_pages+1))

    for page in page_range:

        if page > current_page:
            page_url = 'https://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)

        # NOTE remove inner li to match outer li

        # <li data-version-type="hd">
        html = re.compile(r'<li data-version-type.*?</li>',
                          flags=(re.DOTALL | re.MULTILINE)).sub('', html)

        # <li class="list-item programme"  data-ip-id="p026f2t4">
        list_items = re.findall(r'<li class="list-item.*?</li>', html, flags=(re.DOTALL | re.MULTILINE))

        list_item_num = 1

        for li in list_items:
            # <li class="list-item unavailable"  data-ip-id="b06sq9xj">
            unavailable_match = re.search(
                'data-timeliness-type="unavailable"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if unavailable_match:
                continue

            # <li class="list-item search-group"  data-ip-id="b06rdtx0">
            search_group = False
            search_group_match = re.search(
                '<li class="list-item.*?search-group.*?"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if search_group_match:
                search_group = True

            main_url = None
            # <a href="/iplayer/episode/p026gmw9/world-of-difference-the-models"
            # title="World of Difference, The Models" class="list-item-link stat"
            url_match = re.search(
                r'<a.*?href="(.*?)".*?list-item-link.*?>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if url_match:
                url = url_match.group(1)
                # Some strings already contain the full URL, need to work around this.
                url = url.replace('http://www.bbc.co.uk','')
                url = url.replace('https://www.bbc.co.uk','')
                if url:
                    main_url = 'https://www.bbc.co.uk' + url

            name = ''
            title = ''
            #<div class="title top-title">World of Difference</div>
            title_match = re.search(
                r'<div class="title top-title">\s*(.*?)\s*</div>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if title_match:
                title = title_match.group(1)
                name = title

            subtitle = None
            #<div class="subtitle">The Models</div>
            subtitle_match = re.search(
                r'<div class="subtitle">\s*(.*?)\s*</div>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if subtitle_match:
                subtitle = subtitle_match.group(1)
                if subtitle:
                    name = name + " - " + subtitle

            icon = ''
            # <source srcset="http://ichef.bbci.co.uk/images/ic/336x189/p04cd999.jpg"
            icon_match = re.search(
                r'<source.*?srcset="https://ichef.bbci.co.uk/images/ic/.*?/(.*?)\.jpg"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if icon_match:
                image = icon_match.group(1)
                if image:
                    icon = "https://ichef.bbci.co.uk/images/ic/832x468/" + image + ".jpg"


            type = None
            # <div class="r-image"  data-ip-type="episode"
            # data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p026vl1q.jpg">
            # <div class="r-image"  data-ip-type="group"
            # data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p037ty9z.jpg">
            image_match = re.search(
                r'<div class="r-image".+?data-ip-type="(.*?)"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if image_match:
                type = image_match.group(1)

            synopsis = ''
            # <p class="synopsis">What was it like to be a top fashion model 30 years ago? (1978)</p>
            synopsis_match = re.search(
                r'<p class="synopsis">\s*(.*?)\s*</p>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if synopsis_match:
                synopsis = synopsis_match.group(1)

            aired = ''
            # <span class="release">\nFirst shown: 8 Jun 1967\n</span>
            release_match = re.search(
                r'<span class="release">.*?First shown:\s*(.*?)\n.*?</span>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if release_match:
                release = release_match.group(1)
                if release:
                    aired = FirstShownToAired(release)

            episodes = None
            # <a class="view-more-container avail stat" href="/iplayer/episodes/p00db1jf" data-progress-state="">
            # <a class="view-more-container sibling stat"
            #  href="/iplayer/search?q=doctor&amp;search_group_id=urn:bbc:programmes:b06qbs4n">
            episodes_match = re.search(
                r'<a class="view-more-container.+?stat".+?href="(.*?)"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if episodes_match:
                episodes = episodes_match.group(1)

            more = None
            # <em class="view-more-heading">27</em>
            more_match = re.search(
                r'<em class="view-more-heading">(.*?)</em>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if more_match:
                more = more_match.group(1)

            if episodes:
                episodes_url = 'https://www.bbc.co.uk' + episodes
                if search_group:
                    AddMenuEntry('[B]%s[/B] - %s' % (title, translation(30318)),
                                 episodes_url, 128, icon, '', '')
                else:
                    AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(30313)),
                                 episodes_url, 128, icon, '', '')
            elif more:
                AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(30313)),
                             main_url, 128, icon, '', '')

            if type != "group":
                CheckAutoplay(name , main_url, icon, synopsis, aired)

            percent = int(100*(page+list_item_num/len(list_items))/total_pages)
            pDialog.update(percent,translation(30319),name)

            list_item_num += 1

        # There is a new layout for episodes, scrape it from the JSON received as part of the page
        match = re.search(
                  r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);',
                  html, re.DOTALL)
        if match:
            data = match.group(1)
            json_data = json.loads(data)
            # print json.dumps(json_data, indent=2, sort_keys=True)

            list_item_num = 1

            name = ''
            if 'title' in json_data['appStoreState']['header']:
                name = json_data['appStoreState']['header']['title']

            for item in json_data['appStoreState']['entities']:
                meta = item.get("meta")
                item = item.get("props")
                if not item:
                    continue

                main_url = None
                if 'href' in item:
                    # Some strings already contain the full URL, need to work around this.
                    url = item['href'].replace('http://www.bbc.co.uk','')
                    url = url.replace('https://www.bbc.co.uk','')
                    if url:
                        main_url = 'https://www.bbc.co.uk' + url

                episodes_url = ""
                episodes_title = ""
                if 'secondaryHref' in meta:
                    # Some strings already contain the full URL, need to work around this.
                    url = meta['secondaryHref'].replace('http://www.bbc.co.uk','')
                    url = url.replace('https://www.bbc.co.uk','')
                    if url:
                        episodes_url = 'https://www.bbc.co.uk' + url
                        episodes_title = item["title"]

                # Single episodes in A-Z now come without a title in the entity.
                # Use the main title instead.
                if 'subtitle' in item:
                    if 'title' in item:
                        title = "%s - %s" % (item['title'], item['subtitle'])
                    else:
                        title = name
                elif 'title' in item:
                    title = item['title']
                else:
                    title = name

                synopsis = ''
                if 'synopsis' in item:
                    synopsis = item['synopsis']

                icon = ''
                if 'imageTemplate' in item:
                    icon = item['imageTemplate'].replace("{recipe}","832x468")

                aired = ''

                CheckAutoplay(title , main_url, icon, synopsis, aired)

                if episodes_url:
                    AddMenuEntry('[B]%s[/B]' % (episodes_title),
                                 episodes_url, 128, icon, '', '')

                percent = int(100*(page+list_item_num/len(item))/total_pages)
                pDialog.update(percent,translation(30319),name)

                list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))

    if int(ADDON.getSetting('paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'https://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 128, '', '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

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

    # There is a new layout for episodes, scrape it from the JSON received as part of the page
    match = re.search(
              r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);',
              html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        # print json.dumps(json_data, indent=2, sort_keys=True)

        last_page = 1
        current_page = 1
        if 'pagination' in json_data['appStoreState']:
            page_base_url_match = re.search(r'(.+?)page=', page_url)
            if page_base_url_match:
                page_base_url = page_base_url_match.group(0)
            else:
                page_base_url = page_url+"?page="
            current_page = json_data['appStoreState']['pagination'].get('currentPage')
            last_page = json_data['appStoreState']['pagination'].get('totalPages')
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

            match = re.search(
                      r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);',
                      html, re.DOTALL)
            if match:
                data = match.group(1)
                json_data = json.loads(data)

                index = 1
                for entity in json_data['appStoreState']['entities']:
                    item = entity.get("props")
                    meta = entity.get("meta")
                    if not item:
                        continue
                    ParseHighlightsJSON(item, meta)

                    percent = int(100*(page+index/len(json_data['appStoreState']['entities']))/last_page)
                    pDialog.update(percent,translation(30319))
                    index += 1

            percent = int(100*page/last_page)
            pDialog.update(percent,translation(30319))

    if int(ADDON.getSetting('paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 134, '', '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

    pDialog.close()


def ScrapeMarkup(markup):
    """Creates a list of programmes of a markup response.

    """
    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(30319))

    # <li class="list-item programme"  data-ip-id="p026f2t4">
    list_items = re.findall(r'<li class="list-item.*?</li>', markup, flags=(re.DOTALL | re.MULTILINE))

    list_item_num = 1

    for li in list_items:
        main_url = None
        # <a href="/iplayer/episode/p026gmw9/world-of-difference-the-models"
        # title="World of Difference, The Models" class="list-item-link stat"
        url_match = re.search(
            r'<a.*?href="(.*?)".*?list-item-link.*?>',
                li, flags=(re.DOTALL | re.MULTILINE))
        if url_match:
            tmp_url = url_match.group(1)
            if tmp_url.startswith('http'):
                main_url = tmp_url
            else:
                main_url = 'https://www.bbc.co.uk' + tmp_url

        name = ''
        title = ''
        #<div class="title top-title">World of Difference</div>
        title_match = re.search(
            r'<div class="title top-title">\s*(.*?)\s*</div>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if title_match:
            title = title_match.group(1)
            name = title

        subtitle = None
        #<div class="subtitle">The Models</div>
        subtitle_match = re.search(
            r'<div class="subtitle">\s*(.*?)\s*</div>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if subtitle_match:
            subtitle = subtitle_match.group(1)
            if subtitle:
                name = name + " - " + subtitle

        icon = ''
        type = None
        # <div class="r-image"  data-ip-type="episode"
        # data-ip-src="https://ichef.bbci.co.uk/images/ic/336x189/p033s1dh.jpg">

        image_match = re.search(
            r'srcset="https://ichef.bbci.co.uk/images/ic/.*?/(.*?).jpg"',
            li, flags=(re.DOTALL | re.MULTILINE))
        if image_match:
            image = image_match.group(1)
            if image:
                icon = "https://ichef.bbci.co.uk/images/ic/832x468/" + image + ".jpg"

        synopsis = ''
        # <p class="synopsis">What was it like to be a top fashion model 30 years ago? (1978)</p>
        synopsis_match = re.search(
            r'<p class="synopsis">\s*(.*?)\s*</p>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if synopsis_match:
            synopsis = synopsis_match.group(1)

        # There is no aired date available
        aired = ''

        episodes_url = None
        # <a class="view-more-container avail stat" href="/iplayer/episodes/p00db1jf" data-progress-state="">
        # <a class="view-more-container sibling stat"
        #  href="/iplayer/search?q=doctor&amp;search_group_id=urn:bbc:programmes:b06qbs4n">
        episodes_match = re.search(
            r'<a class="view-more-container.+?stat".+?href="(.*?)"',
            li, flags=(re.DOTALL | re.MULTILINE))
        if episodes_match:
            tmp_url = episodes_match.group(1)
            if tmp_url.startswith('http'):
                episodes_url = tmp_url
            else:
                episodes_url = 'https://www.bbc.co.uk' + tmp_url

        more = None
        # <em class="view-more-heading">27</em>
        more_match = re.search(
            r'<em class="view-more-heading">(.*?)</em>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if more_match:
            more = more_match.group(1)

        if episodes_url:
            AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(30313)),
                         episodes_url, 128, icon, '', '')
        elif more:
            AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(30313)),
                         main_url, 128, icon, '', '')

        if type != "group":
            CheckAutoplay(name , main_url, icon, synopsis, aired)

        percent = int(100*(list_item_num/len(list_items)))
        pDialog.update(percent,translation(30319),name)

        list_item_num += 1

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

    pDialog.close()


def ListCategories():
    """Parses the available categories and creates directories for selecting one of them.
    The category names are scraped from the website.
    """
    html = OpenURL('https://www.bbc.co.uk/iplayer')
    match = re.compile(
        '<a href="/iplayer/categories/(.+?)/featured".*?>(.+?)</a>'
        ).findall(html)
    for url, name in match:
        if name == "View all":
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
        ('tv/s4c',           's4cpbs',                      'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
        AddMenuEntry(name, id, 106, iconimage, '', '')


def ParseHighlightsJSON(item, meta):
    main_url = None
    if 'href' in item:
        # Some strings already contain the full URL, need to work around this.
        url = item['href'].replace('http://www.bbc.co.uk','')
        url = url.replace('https://www.bbc.co.uk','')
        if url:
            main_url = 'https://www.bbc.co.uk' + url

    episodes_url = ""
    episodes_title = ""
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

    if 'subtitle' in item:
        title = "%s - %s" % (item['title'], item['subtitle'])
    else:
        title = item['title']

    synopsis = ''
    if 'synopsis' in item:
        synopsis = item['synopsis']

    icon = ''
    if 'imageTemplate' in item:
        icon = item['imageTemplate'].replace("{recipe}","832x468")

    aired = ''

    CheckAutoplay(title , main_url, icon, synopsis, aired)

    if episodes_url:
        AddMenuEntry('[B]%s[/B]' % (episodes_title),
                     episodes_url, 128, icon, '', '')


def ListHighlights(highlights_url):
    """Creates a list of the programmes in the highlights section.
    """

    html = OpenURL('https://www.bbc.co.uk/%s' % highlights_url)

    # There is a new layout for episodes, scrape it from the JSON received as part of the page
    match = re.search(
              r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);',
              html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        # xbmc.log(json.dumps(json_data, indent=2, sort_keys=True))
        list_item_num = 1

        groups = ''
        groups = json_data['appStoreState'].get('groups')
        if groups:
            for entity in json_data['appStoreState']['groups']:
                for item in entity['entities']:
                    item = item.get("props")
                    if not item:
                        continue
                    ParseHighlightsJSON(item, None)

                title = ''
                id = ''
                title = entity.get('title')
                id = entity.get('id')
                if (title and id):
                    episodes_url = 'https://www.bbc.co.uk/iplayer/group/%s' % id
                    AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                 episodes_url, 128, '', '', '')

        highlights = ''
        highlights = json_data['appStoreState'].get('highlights')
        if highlights:
            entity = json_data['appStoreState']['highlights'].get("items")
            if entity:
                for item in entity:
                    item = item.get("props")
                    if not item:
                        continue
                    ParseHighlightsJSON(item, None)

        bundles = ''
        bundles = json_data['appStoreState'].get('bundles')
        if bundles:
            for bundle in bundles:
                entity = ''
                entity = bundle.get('entities')
                if entity:
                    for item in entity:
                        ParseHighlightsJSON(item, None)
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
                                AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                             episodes_url, 128, '', '', '')
                        if (id and (type == 'category')):
                            AddMenuEntry('[B]%s: %s[/B]' % (translation(30314), title),
                                         id, 126, '', '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)


def ListMostPopular():
    """Scrapes all episodes of the most popular page."""
    html = OpenURL("https://www.bbc.co.uk/iplayer/group/most-popular")

    # <li class="most-popular__item gel-layout__item gel-1/2 gel-1/3@m">
    list_items = re.findall(r'<li class="most-popular.*?</li>', html, flags=(re.DOTALL | re.MULTILINE))

    list_item_num = 1

    for li in list_items:
        # NOTE remove useless hrefs

        # href="#gel-icon-iplayer"
        li = re.compile(r'href="#.*?"',
                          flags=(re.DOTALL | re.MULTILINE)).sub('', li)

        main_url = None
        # <a class="content-item__link gel-layout gel-layout--flush"
        # href="/iplayer/episode/b09k9n93/eastenders-21122017"
        url_match = re.search(
            r'href="(.*?)"',
            li, flags=(re.DOTALL | re.MULTILINE))
        if url_match:
            url = url_match.group(1)
            # Some strings already contain the full URL, need to work around this.
            url = url.replace('http://www.bbc.co.uk','')
            url = url.replace('https://www.bbc.co.uk','')
            if url:
                main_url = 'https://www.bbc.co.uk' + url

        name = ''
        title = ''
        # <div class="content-item__title typo typo--skylark typo--bold">EastEnders</div>
        title_match = re.search(
            r'<div class="content-item__title.*?>\s*(.*?)\s*</div>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if title_match:
            title = title_match.group(1)
            name = title

        subtitle = None
        # <div class="content-item__info__primary"><div class="content-item__description
        # typo typo--bullfinch">21/21 Crowning the champion</div>
        subtitle_match = re.search(
            r'<div class="content-item__info__primary">.*?>\s*(.*?)\s*</div>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if subtitle_match:
            subtitle = subtitle_match.group(1)
            if subtitle:
                name = name + " - " + subtitle

        icon = ''
        # <source srcset="http://ichef.bbci.co.uk/images/ic/336x189/p04cd999.jpg"
        icon_match = re.search(
            r'https://ichef.bbci.co.uk/images/ic/.*?/(.*?)\.jpg',
            li, flags=(re.DOTALL | re.MULTILINE))
        if icon_match:
            image = icon_match.group(1)
            if image:
                icon = "https://ichef.bbci.co.uk/images/ic/832x468/" + image + ".jpg"

        type = None
        synopsis = ''
        # <div class="content-item__info__secondary"><div class="content-item__description typo
        # typo--bullfinch">Linda gets more than she bargained for when looking for her Christmas
        # present.</div>
        synopsis_match = re.search(
            r'<div class="content-item__info__secondary">.*?>\s*(.*?)\s*</div>',
            li, flags=(re.DOTALL | re.MULTILINE))
        if synopsis_match:
            synopsis = synopsis_match.group(1)

        aired = ''
        episodes = None
        more = None

        CheckAutoplay(name , main_url, icon, synopsis, aired)

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)



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
    elif ((not stream_ids['stream_id_st']) or (ADDON.getSetting('search_signed') == 'true')) and stream_ids['stream_id_sl']:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_sl'])
    else:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_st'])
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


def AddAvailableLiveStreamItemSelector(name, channelname, iconimage):
    if ((int(ADDON.getSetting('stream_protocol')) == 1) or
        (channelname.startswith('sport_stream_'))):
        return AddAvailableLiveStreamItem(name, channelname, iconimage)
    elif int(ADDON.getSetting('stream_protocol')) == 0:
        ia_available = CheckInputStreamAdaptiveAvailability()
        if ia_available:
            return AddAvailableLiveDASHStreamItem(name, channelname, iconimage)
        else:
            return AddAvailableLiveStreamItem(name, channelname, iconimage)


def AddAvailableLiveDASHStreamItem(name, channelname, iconimage):

    streams = ParseLiveDASHStreams(channelname)

    source = int(ADDON.getSetting('live_source'))
    if source > 0:
        match = [x for x in streams if (x[0] == source)]
        if len(match) == 0:
            match = [x for x in streams if (x[1] in range(1, bitrate))]
            match.sort(key=lambda x: x[1], reverse=True)
    else:
        match = streams
        match.sort(key=lambda x: x[1], reverse=True)
    PlayStream(name, match[0][2], iconimage, '', '')


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
    if ((int(ADDON.getSetting('stream_protocol')) == 1) or
        (channelname.startswith('sport_stream_'))):
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

    elif int(ADDON.getSetting('stream_protocol')) == 0:
        ia_available = CheckInputStreamAdaptiveAvailability()
        if ia_available:
            streams = ParseLiveDASHStreams(channelname)
            suppliers = ['', 'Akamai', 'Limelight', 'Bidi']
            for supplier, bitrate, url, resolution in streams:
                title = name + ' - [I][COLOR fff1f1f1]%s[/COLOR][/I]' % (suppliers[supplier])
                AddMenuEntry(title, url, 201, iconimage, '', '')
        else:
            # In this case, we reset the stream_protocol setting and the easiest way is
            # to call this function recursively to avoid doubling a lot of code.
            AddAvailableLiveStreamsDirectory(name, channelname, iconimage)


def ListWatching(logged_in):

    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('video')
        return

    cookie_jar = None
    cookie_jar = GetCookieJar()
    url = "https://component.iplayer.api.bbc.co.uk/v1/user/lists/watching"
    html = OpenURL(url)
    json_data = json.loads(html)
    markup = json_data.get('markup')
    ScrapeMarkup(markup)


def ListFavourites(logged_in):

    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('video')
        return

    cookie_jar = None
    cookie_jar = GetCookieJar()
    url = "https://component.iplayer.api.bbc.co.uk/v1/user/lists/added"
    html = OpenURL(url)
    json_data = json.loads(html)
    markup = json_data.get('markup')
    ScrapeMarkup(markup)


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
    if ADDON.getSetting('stream_protocol') == '0':
        liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        subtitles_file = download_subtitles(subtitles_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        # Successfully started playing something?
        while True:
            if xbmc.Player().isPlaying():
                break
            else:
                xbmc.sleep(500)
        xbmc.Player().setSubtitles(subtitles_file)


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""
    # print "Stream ID: %s"%stream_id
    streams = ParseStreamsHLSDASH(stream_id)
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
        if int(ADDON.getSetting('stream_protocol')) == 1:
            title = name + ' - [I][COLOR %s]%0.1f Mbps[/COLOR] [COLOR ffd3d3d3]%s[/COLOR][/I]' % (
                color, bitrates[bitrate] / 1000, suppliers[supplier])
        else:
            title = name + ' - [I][COLOR ffd3d3d3]%s[/COLOR][/I]' % (suppliers[supplier])
        AddMenuEntry(title, url, 201, iconimage, description, subtitles_url, resolution=resolution)


def ParseStreamsHLSDASH(stream_id):
    if int(ADDON.getSetting('stream_protocol')) == 1:
        return ParseStreams(stream_id)
    elif int(ADDON.getSetting('stream_protocol')) == 0:
        ia_available = CheckInputStreamAdaptiveAvailability()
        if ia_available:
            return ParseDASHStreams(stream_id)
        else:
            return ParseStreams(stream_id)


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


def ParseDASHStreams(stream_id):
    retlist = []
    # print "Parsing streams for PID: %s"%stream_id
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id
    html = OpenURL(NEW_URL)

    # Check if this is a webcast.
    check_webcast = re.search('webcast', html)
    if check_webcast:
        # This appears to be a webcast. Load PC mediaselector to get DASH streams.
        NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/%s" % stream_id
        html = OpenURL(NEW_URL)
        # Parse the different streams and add them as new directory entries.
        match = re.compile(
              'connection.+?href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
            ).findall(html)
        unique = []
        [unique.append(item) for item in match if item not in unique]
        for mpd_url, supplier, transfer_format in unique:
            tmp_sup = 0
            tmp_br = 0
            if transfer_format == 'dash':
                if supplier in ['akamai_dash_live', 'akamai_dash_live_https']:
                    tmp_sup = 1
                elif supplier in ['ll_dash_live', 'll_dash_live_https']:
                    tmp_sup = 2
                retlist.append((tmp_sup, 1, mpd_url, '1280x720'))

        if not match:
            # print "No streams found"
            check_geo = re.search(
                '<error id="geolocation"/>', html)
            if check_geo:
                # print "Geoblock detected, raising error message"
                dialog = xbmcgui.Dialog()
                dialog.ok(translation(30400), translation(30401))
                raise
        return retlist, []

    # Parse the different streams and add them as new directory entries.
    match = re.compile(
          'connection authExpires=".+?href="(.+?)".+?supplier="mf_(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    for mpd_url, supplier, transfer_format in match:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'dash':
            if supplier in ['akamai_uk_dash', 'akamai_uk_dash_https']:
                tmp_sup = 1
            elif supplier in ['limelight_uk_dash', 'limelight_uk_dash_https']:
                tmp_sup = 2
            elif supplier in ['bidi_uk_dash', 'bidi_uk_dash_https']:
                tmp_sup = 3
            retlist.append((tmp_sup, 1, mpd_url, '1280x720'))

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
                           'bbc_one_west', 'bbc_one_west_midlands', 'bbc_one_yorks']:
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


def ParseLiveDASHStreams(channelname):
    streams = []

    url = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/%s" % channelname
    html = OpenURL(url)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
          'connection.+?href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    unique = []
    [unique.append(item) for item in match if item not in unique]
    for mpd_url, supplier, transfer_format in unique:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'dash':
            if supplier.startswith('akamai_dash'):
                tmp_sup = 1
            elif supplier.startswith('ll_dash'):
                tmp_sup = 2
            streams.append((tmp_sup, 1, mpd_url, '1280x720'))

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

    match = re.search(r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);', html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        # print json.dumps(json_data, indent=2, sort_keys=True)
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
        for stream in json_data['episode']['versions']:
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


def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 202, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 122, iconimage, plot, '', aired=aired)

