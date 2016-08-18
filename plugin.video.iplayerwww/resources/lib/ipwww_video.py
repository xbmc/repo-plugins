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
        ('bbc_one_hd',                       'bbc_one',                                   'BBC One'),
        ('bbc_two_hd',                       'bbc_two',                                   'BBC Two'),
        ('bbc_four_hd',                      'bbc_four',                                 'BBC Four'),
        ('cbbc_hd',                          'cbbc',                                         'CBBC'),
        ('cbeebies_hd',                      'cbeebies',                                 'CBeebies'),
        ('bbc_news24',                       'bbc_news24',                       'BBC News Channel'),
        ('bbc_parliament',                   'bbc_parliament',                     'BBC Parliament'),
        ('bbc_alba',                         'bbc_alba',                                     'Alba'),
        ('s4cpbs',                           's4c',                                           'S4C'),
        ('bbc_one_london',                   'bbc_one',                            'BBC One London'),
        ('bbc_one_scotland_hd',              'bbc_one_scotland',                 'BBC One Scotland'),
        ('bbc_one_northern_ireland_hd',      'bbc_one_northern_ireland', 'BBC One Northern Ireland'),
        ('bbc_one_wales_hd',                 'bbc_one_wales',                       'BBC One Wales'),
        ('bbc_two_scotland',                 'bbc_two',                          'BBC Two Scotland'),
        ('bbc_two_northern_ireland_digital', 'bbc_two',                  'BBC Two Northern Ireland'),
        ('bbc_two_wales_digital',            'bbc_two',                             'BBC Two Wales'),
        ('bbc_two_england',                  'bbc_two',                          'BBC Two England',),
        ('bbc_one_cambridge',                'bbc_one',                        'BBC One Cambridge',),
        ('bbc_one_channel_islands',          'bbc_one',                  'BBC One Channel Islands',),
        ('bbc_one_east',                     'bbc_one',                             'BBC One East',),
        ('bbc_one_east_midlands',            'bbc_one',                    'BBC One East Midlands',),
        ('bbc_one_east_yorkshire',           'bbc_one',                   'BBC One East Yorkshire',),
        ('bbc_one_north_east',               'bbc_one',                       'BBC One North East',),
        ('bbc_one_north_west',               'bbc_one',                       'BBC One North West',),
        ('bbc_one_oxford',                   'bbc_one',                           'BBC One Oxford',),
        ('bbc_one_south',                    'bbc_one',                            'BBC One South',),
        ('bbc_one_south_east',               'bbc_one',                       'BBC One South East',),
        ('bbc_one_west',                     'bbc_one',                             'BBC One West',),
        ('bbc_one_west_midlands',            'bbc_one',                    'BBC One West Midlands',),
        ('bbc_one_yorks',                    'bbc_one',                            'BBC One Yorks',),
    ]
    for id, img, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
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
        ('bbcone', 'bbc_one', 'BBC One'),
        ('bbctwo', 'bbc_two', 'BBC Two'),
        ('tv/bbcthree', 'bbc_three', 'BBC Three'),
        ('bbcfour', 'bbc_four', 'BBC Four'),
        ('tv/cbbc', 'cbbc', 'CBBC'),
        ('tv/cbeebies', 'cbeebies', 'CBeebies'),
        ('tv/bbcnews', 'bbc_news24', 'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament', 'BBC Parliament'),
        ('tv/bbcalba', 'bbc_alba', 'Alba'),
        ('tv/s4c', 's4c', 'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
        url = "http://www.bbc.co.uk/%s/a-z" % id
        AddMenuEntry(name, url, 128, iconimage, '', '')


def GetAtoZPage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    link = OpenURL('http://www.bbc.co.uk/iplayer/a-z/%s' % url)
    match = re.compile(
        '<a href="/iplayer/brand/(.+?)".+?<span class="title">(.+?)</span>',
        re.DOTALL).findall(link)
    for programme_id, name in match:
        AddMenuEntry(name, programme_id, 121, '', '', '')


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
    new_url = 'http://www.bbc.co.uk/iplayer/episodes/%s' % url
    ScrapeEpisodes(new_url)


def GetGroup(url):
    new_url = "http://www.bbc.co.uk/iplayer/group/%s" % url
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
    page_range = range(1)
    paginate = re.search(r'<div class="paginate.*?</div>', html, re.DOTALL)
    next_page = 1
    if paginate:
        if int(ADDON.getSetting('paginate_episodes')) == 0:
            current_page_match = re.search(r'page=(\d*)', page_url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
            page_range = range(current_page, current_page+1)
            next_page_match = re.search(r'<span class="next txt">.+?href="(.*?page=)(.*?)"',
                                        paginate.group(0),
                                        re.DOTALL)
            if next_page_match:
                page_base_url = next_page_match.group(1)
                next_page = int(next_page_match.group(2))
            else:
                next_page = current_page
            page_range = range(current_page, current_page+1)
        else:
            pages = re.findall(r'<li class="page.*?</li>',paginate.group(0),re.DOTALL)
            if pages:
                last = pages[-1]
                last_page = re.search(r'<a href="(.*?page=)(.*?)"',last)
                page_base_url = last_page.group(1)
                total_pages = int(last_page.group(2))
            page_range = range(1, total_pages+1)

    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
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
                '<li class="list-item.*?unavailable.*?"',
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
                if url:
                    main_url = 'http://www.bbc.co.uk' + url

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
            # data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p026vl1q.jpg">
            # <div class="r-image"  data-ip-type="group"
            # data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p037ty9z.jpg">
            image_match = re.search(
                r'<div class="r-image".+?data-ip-type="(.*?)".+?data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/(.*?)\.jpg"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if image_match:
                type = image_match.group(1)
                image = image_match.group(2)
                if image:
                    icon = "http://ichef.bbci.co.uk/images/ic/832x468/" + image + ".jpg"

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
                episodes_url = 'http://www.bbc.co.uk' + episodes
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

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(30319))

    if int(ADDON.getSetting('paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry(" [COLOR ffffa500]%s >>[/COLOR]" % translation(30320), page_url, 128, '', '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

    pDialog.close()


def ListCategories():
    """Parses the available categories and creates directories for selecting one of them.
    The category names are scraped from the website.
    """
    html = OpenURL('http://www.bbc.co.uk/iplayer')
    match = re.compile(
        '<a href="/iplayer/categories/(.+?)" class="stat">(.+?)</a>'
        ).findall(html)
    for url, name in match:
        AddMenuEntry(name, url, 125, '', '', '')


def ListCategoryFilters(url):
    """Parses the available category filters (if available) and creates directories for selcting them.
    If there are no filters available, all programmes will be listed using GetFilteredCategory.
    """
    NEW_URL = 'http://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz' % url
    # Read selected category's page.
    html = OpenURL(NEW_URL)
    # Some categories offer filters, we want to provide these filters as options.
    match1 = re.findall(
        '<li class="filter"> <a class="name" href="/iplayer/categories/(.+?)"> (.+?)</a>',
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
    NEW_URL = 'http://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz' % url

    ScrapeEpisodes(NEW_URL)


def ListChannelHighlights():
    """Creates a list directories linked to the highlights section of each channel."""
    channel_list = [
        ('bbcone', 'bbc_one', 'BBC One'),
        ('bbctwo', 'bbc_two', 'BBC Two'),
        ('tv/bbcthree', 'bbc_three', 'BBC Three'),
        ('bbcfour', 'bbc_four', 'BBC Four'),
        ('tv/cbbc', 'cbbc', 'CBBC'),
        ('tv/cbeebies', 'cbeebies', 'CBeebies'),
        ('tv/bbcnews', 'bbc_news24', 'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament', 'BBC Parliament'),
        ('tv/bbcalba', 'bbc_alba', 'Alba'),
        ('tv/s4c', 's4c', 'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
        AddMenuEntry(name, id, 106, iconimage, '', '')


def ListHighlights(highlights_url):
    """Creates a list of the programmes in the highlights section.
    """

    html = OpenURL('http://www.bbc.co.uk/%s' % highlights_url)

    inner_anchors = re.findall(r'<a.*?(?!<a).*?</a>',html,flags=(re.DOTALL | re.MULTILINE))

    # First find all groups as we need to store some properties of groups for later reuse.
    group_properties = []

    # NOTE find episode count first
    episode_count = dict()
    groups = [a for a in inner_anchors if re.match(
        r'<a[^<]*?class="grouped-items__cta.*?data-object-type="group-list-link".*?',
        a, flags=(re.DOTALL | re.MULTILINE))]
    for group in groups:

        href = ''
        href_match = re.match(
            r'<a[^<]*?href="(.*?)"',
            group, flags=(re.DOTALL | re.MULTILINE))
        if href_match:
            href = href_match.group(1)

        count_match = re.search(
            r'>View all ([0-9]*).*?</a>',
            group, flags=(re.DOTALL | re.MULTILINE))
        if count_match:
            count = count_match.group(1)
            episode_count[href] = count

    groups = [a for a in inner_anchors if re.match(
        r'<a[^<]*?class="grouped-items__title.*?data-object-type="group-list-link".*?',
        a, flags=(re.DOTALL | re.MULTILINE))]
    for group in groups:

        href = ''
        href_match = re.match(
            r'<a[^<]*?href="(.*?)"',
            group, flags=(re.DOTALL | re.MULTILINE))
        if href_match:
            href = href_match.group(1)

        name = ''
        name_match = re.search(
            r'<strong>(.*?)</strong>',
            group, flags=(re.DOTALL | re.MULTILINE))
        if name_match:
            name = name_match.group(1)

        count = ''
        if href in episode_count:
            count = episode_count[href]

        url = 'http://www.bbc.co.uk' + href

        # Unfortunately, the group type is not inside the links, so we need to search the whole HTML.
        group_type = ''
        group_type_match = re.search(
            r'data-group-name="'+name+'".+?data-group-type="(.+?)"',
            html, flags=(re.DOTALL | re.MULTILINE))
        if group_type_match:
            group_type = group_type_match.group(1)

        position = ''
        position_match = re.search(
            r'data-object-position="(.+?)-ALL"',
            group, flags=(re.DOTALL | re.MULTILINE))
        if position_match:
            group_properties.append(
                             [position_match.group(1),
                             name, group_type])

        AddMenuEntry('[B]%s: %s[/B] - %s %s' % (translation(30314), name, count, translation(30315)),
                     url, 128, '', '', '')

    # Some programmes show up twice in HTML, once inside the groups, once outside.
    # We need to parse both to avoid duplicates and to make sure we get all of them.
    episodelist = []

    # <a\n    href="/iplayer/episode/b06tr74y/eastenders-24122015"\n    class="grouped-items__list-link
    listeds = [a for a in inner_anchors if re.search(
        r'class="grouped-items__list-link',
        a, flags=(re.DOTALL | re.MULTILINE))]

    for listed in listeds:

        episode_id = ''
        # <a\n    href="/iplayer/episode/b06tr74y/eastenders-24122015"
        id_match = re.match(
            r'<a.*?href="/iplayer/episode/(.*?)/',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if id_match:
            episode_id = id_match.group(1)

        name = ''
        # <p class="grouped-items__title grouped-items__title--item typo typo--skylark">
        # <strong>EastEnders</strong></p>
        title_match = re.search(
            r'<.*?class="grouped-items__title.*?<strong>(.*?)</strong>',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if title_match:
            name = title_match.group(1)
            name = re.compile(r'<.*?>', flags=(re.DOTALL | re.MULTILINE)).sub('', name)

        # <p class="grouped-items__subtitle typo typo--canary">24/12/2015</p>
        subtitle_match = re.search(
            r'<.*?class="grouped-items__subtitle.*?>(.*?)<',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if subtitle_match:
            name = name + ' - ' + subtitle_match.group(1)

        # Assign correct group based on the position of the episode
        position = ''
        position_match = re.search(
            r'data-object-position="(.+?)"',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if position_match:
            for n,i in enumerate(group_properties):
                if re.match(i[0], position_match.group(1), flags=(re.DOTALL | re.MULTILINE)):
                    position = i[1]
                    # For series-catchup groups, we need to modify the title.
                    if i[2] == 'series-catchup':
                        name = i[1]+': '+name

        episodelist.append(
                    [episode_id,
                    name,
                    "%s %s" % (translation(30316), position),
                    'DefaultVideo.png',
                    '']
                    )

    # < a\nhref="/iplayer/episode/p036gq3z/bbc-music-introducing-from-buddhist-monk-to-rock-star"\n
    # class="single-item stat"
    singles = [a for a in inner_anchors if re.search(
        r'class="single-item',
        a, flags=(re.DOTALL | re.MULTILINE))]

    for single in singles:

        object_type = ''
        # data-object-type="episode-backfill"
        data_object_type = re.search(
            r'data-object-type="(.*?)"',
            single, flags=(re.DOTALL | re.MULTILINE))
        if data_object_type:
            object_type = data_object_type.group(1)
            if object_type == "episode-backfill":
                if (highlights_url not in ['tv/bbcnews', 'tv/bbcparliament', 'tv/s4c']):
                    continue

        episode_id = ''
        url = ''
        # <a\nhref="/iplayer/episode/p036gq3z/bbc-music-introducing-from-buddhist-monk-to-rock-star"
        if object_type == "editorial-promo":
            id_match = re.match(
                r'<a.*?href="(.*?)"',
                single, flags=(re.DOTALL | re.MULTILINE))
        else:
            id_match = re.match(
                r'<a.*?href="/iplayer/episode/(.*?)/',
                single, flags=(re.DOTALL | re.MULTILINE))
        if id_match:
            episode_id = id_match.group(1)
            url = 'http://www.bbc.co.uk/iplayer/episode/' + episode_id

        name = ''
        # <h3 class="single-item__title typo typo--skylark"><strong>BBC Music Introducing</strong></h3>
        title_match = re.search(
            r'<.*?class="single-item__title.*?<strong>(.*?)</strong>',
            single, flags=(re.DOTALL | re.MULTILINE))
        if title_match:
            name = title_match.group(1)
            name = re.compile(r'<.*?>', flags=(re.DOTALL | re.MULTILINE)).sub('', name)

        # <p class="single-item__subtitle typo typo--canary">From Buddhist Monk to Rock Star</p>
        subtitle_match = re.search(
            r'<.*?class="single-item__subtitle.*?>(.*?)<',
            single, flags=(re.DOTALL | re.MULTILINE))
        if subtitle_match:
            name = name + ' - ' + subtitle_match.group(1)

        icon = ''
        # <div class="r-image"  data-ip-type="episode"
        # data-ip-src="http://ichef.bbci.co.uk/images/ic/406x228/p036gtc5.jpg">
        image_match = re.search(
            r'<.*?class="r-image.*?data-ip-src="(.*?)"',
            single, flags=(re.DOTALL | re.MULTILINE))
        if image_match:
            icon = image_match.group(1)

        desc = ''
        # <p class="item-overlay__text__inner typo typo--canary">
        # A hospital visit reveals devastating news for Jasmin and Dev.
        # </p>
        desc_match = re.search(
            r'<.*?class="item-overlay__text__inner.*?>(.*?)<',
            single, flags=(re.DOTALL | re.MULTILINE))
        if desc_match:
            desc = desc_match.group(1)

        aired = ''
        # <p class="single-item__overlay__subtitle">First shown: 4 Nov 2015</p>
        release_match = re.search(
            r'<.*?class="single-item__overlay__subtitle">First shown: (.*?)<',
            single, flags=(re.DOTALL | re.MULTILINE))
        if release_match:
            release = release_match.group(1)
            if release:
                aired = FirstShownToAired(release)

        add_entry = True
        for n,i in enumerate(episodelist):
            if i[0]==episode_id:
                episodelist[n][2]=desc
                episodelist[n][3]=icon
                episodelist[n][4]=aired
                add_entry = False
        if add_entry:
            if object_type == "editorial-promo":
                if episode_id:
                    AddMenuEntry('[B]%s[/B]' % (name), episode_id, 128, icon, '', '')
            else:
                if url:
                    CheckAutoplay(name, url, icon, desc, aired)

    # Finally add all programmes which have been identified as part of a group before.
    for episode in episodelist:
        episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % episode[0]
        if ((ADDON.getSetting('suppress_incomplete') == 'false') or (not episode[4] == '')):
            if episode[0]:
                CheckAutoplay(episode[1], episode_url, episode[3], episode[2], episode[4])

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

def ListMostPopular():
    """Scrapes all episodes of the most popular page."""
    ScrapeEpisodes("http://www.bbc.co.uk/iplayer/group/most-popular")


def AddAvailableStreamItem(name, url, iconimage, description):
    """Play a streamm based on settings for preferred catchup source and bitrate."""
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids['stream_id_ad']:
        streams_all = ParseStreams(stream_ids['stream_id_ad'])
    elif stream_ids['stream_id_sl']:
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
                    match = [x for x in streams if (x[0] == source) and (x[1] in range(1, bitrate))]
                    match.sort(key=lambda x: x[1], reverse=True)
                    if len(match) == 0:
                        # Third Fallback: Use any lower bitrate from any source.
                        match = [x for x in streams if (x[1] in range(1, bitrate))]
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
                match = [x for x in streams if (x[1] in range(1, bitrate))]
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
    AddAvailableStreamsDirectory(name, stream_ids['stream_id_st'], iconimage, description)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad']:
        AddAvailableStreamsDirectory(name + ' - (Audio Described)', stream_ids['stream_id_ad'], iconimage, description)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl']:
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

    NEW_URL = 'http://www.bbc.co.uk/iplayer/search?q=%s' % search_entered
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

    identity_cookie = None
    cookie_jar = None
    cookie_jar = GetCookieJar()
    for cookie in cookie_jar:
        if (cookie.name == 'IDENTITY'):
            identity_cookie = cookie.value
            break
    url = "https://ibl.api.bbci.co.uk/ibl/v1/user/watching?identity_cookie=%s" % identity_cookie
    html = OpenURL(url)
    json_data = json.loads(html)
    watching_list = json_data.get('watching').get('elements')
    for watching in watching_list:
        programme = watching.get('programme')
        episode = watching.get('episode')
        title = episode.get('title')
        subtitle = episode.get('subtitle')
        if(subtitle):
            title += ", " + subtitle
        episode_id = episode.get('id')
        plot = episode.get('synopses').get('large') or " "
        aired = episode.get('release_date')
        image_url = ParseImageUrl(episode.get('images').get('standard'))
        aired = ParseAired(aired)
        url="http://www.bbc.co.uk/iplayer/episode/%s" % (episode_id)
        CheckAutoplay(title, url, image_url, plot, aired)


def ListFavourites(logged_in):

    if(CheckLogin(logged_in) == False):
        CreateBaseDirectory('video')
        return

    """Scrapes all episodes of the favourites page."""
    identity_cookie = None
    cookie_jar = None
    cookie_jar = GetCookieJar()
    for cookie in cookie_jar:
        if (cookie.name == 'IDENTITY'):
            identity_cookie = cookie.value
            break
    url = "https://ibl.api.bbci.co.uk/ibl/v1/user/added?identity_cookie=%s" % identity_cookie
    html = OpenURL(url)
    json_data = json.loads(html)
    favourites_list = json_data.get('added').get('elements')
    for favourite in favourites_list:
        programme = favourite.get('programme')
        id = programme.get('id')
        url = "http://www.bbc.co.uk/iplayer/brand/%s" % (id)
        title = programme.get('title')
        initial_child = programme.get('initial_children')[0]
        subtitle = initial_child.get('subtitle')
        episode_title = title
        if subtitle:
            episode_title = title + ' - ' + subtitle
        image=initial_child.get('images')
        image_url=ParseImageUrl(image.get('standard'))
        synopses = initial_child.get('synopses')
        plot = synopses.get('small')
        try:
            aired = FirstShownToAired(initial_child.get('release_date'))
        except:
            aired = ''
        CheckAutoplay(episode_title, url, image_url, plot, aired)
        more = programme.get('count')
        if more:
            episodes_url = "http://www.bbc.co.uk/iplayer/episodes/" + id
            AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(30313)),
                         episodes_url, 128, image_url, '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)


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
    streams = ParseStreams(stream_id)
    # print streams
    if streams[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    suppliers = ['', 'Akamai', 'Limelight', 'Level3']
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
    # print "Parsing streams for PID: %s"%stream_id[0]
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id[0]
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'connection authExpires=".+?href="(.+?)".+?supplier="mf_(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    for m3u8_url, supplier, transfer_format in match:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_uk_hls':
                tmp_sup = 1
            elif supplier == 'limelight_uk_hls':
                tmp_sup = 2
            m3u8_breakdown = re.compile('(.+?)iptv.+?m3u8(.+?)$').findall(m3u8_url)
            #print m3u8_breakdown
            # print m3u8_url
            m3u8_html = OpenURL(m3u8_url)
            m3u8_match = re.compile('BANDWIDTH=(.+?),.+?RESOLUTION=(.+?)(?:,.+?\n|\n)(.+?)\n').findall(m3u8_html)
            for bandwidth, resolution, stream in m3u8_match:
                # print bandwidth
                # print resolution
                #print stream
                url = "%s%s%s" % (m3u8_breakdown[0][0], stream, m3u8_breakdown[0][1])
                #print url
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
    # print match
    unique = []
    [unique.append(item) for item in match if item not in unique]
    # print unique
    for m3u8_url, supplier, transfer_format in unique:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_hls_open':
                tmp_sup = 1
            elif supplier == 'limelight_hls_open':
                tmp_sup = 2
            m3u8_breakdown = re.compile('.+?master.m3u8(.+?)$').findall(m3u8_url)
        # print m3u8_url
        # print m3u8_breakdown
        m3u8_html = OpenURL(m3u8_url)
        # print m3u8_html
        m3u8_match = re.compile('BANDWIDTH=(.+?),RESOLUTION=(.+?),.+?\n(.+?)\n').findall(m3u8_html)
        # print m3u8_match
        for bandwidth, resolution, stream in m3u8_match:
            # print bandwidth
            # print resolution
            # print stream
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
    # print match
    unique = []
    [unique.append(item) for item in match if item not in unique]
    # print unique
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
                           'bbc_one_south', 'bbc_one_south_east', 'bbc_one_west',
                           'bbc_one_west_midlands', 'bbc_one_yorks']:
            device = 'hls_tablet'
        else:
            device = 'abr_hdtv'

        if channelname.startswith('sport_stream_'):
            cast = "webcast"
        else:
            cast = "simulcast"

        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio_video/%s/hls/uk/%s/%s/%s.m3u8' \
              % (cast, device, provider_url, channelname)
        html = OpenURL(url)
        match = re.compile('#EXT-X-STREAM-INF:PROGRAM-ID=(.+?),BANDWIDTH=(.+?),CODECS="(.*?)",RESOLUTION=(.+?)\s*(.+?.m3u8)').findall(html)

        # Add provider name to the stream list.
        streams.extend([list(stream) + [provider_name] for stream in match])

    # Convert bitrate to Mbps for further processing
    for i in range(len(streams)):
        streams[i][1] = round(int(streams[i][1])/1000000.0, 1)

    # Return list sorted by bitrate
    return sorted(streams, key=lambda x: (x[1]), reverse=True)


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    # Search for standard programmes.
    stream_id_st = re.compile('"vpid":"(.+?)"').findall(html)
    # Optionally, Signed programmes can be searched for. These have a different ID.
    if ADDON.getSetting('search_signed') == 'true':
        stream_id_sl = re.compile('data-download-sl="bbc-ipd:download/.+?/(.+?)/sd/').findall(html)
    else:
        stream_id_sl = []
    # Optionally, Audio Described programmes can be searched for. These have a different ID.
    if ADDON.getSetting('search_ad') == 'true':
        url_ad = re.compile('<a href="(.+?)" class="version link watch-ad-on"').findall(html)
        url_tmp = "http://www.bbc.co.uk%s" % url_ad[0]
        html = OpenURL(url_tmp)
        stream_id_ad = re.compile('"vpid":"(.+?)"').findall(html)
        # print stream_id_ad
    else:
        stream_id_ad = []
    return {'stream_id_st': stream_id_st, 'stream_id_sl': stream_id_sl, 'stream_id_ad': stream_id_ad}


def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 202, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 122, iconimage, plot, '', aired=aired)

