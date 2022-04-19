# _*_ coding: utf-8 _*_

'''
   RNE Podcasts API lib: library functions for RNE Podcast audio add-on.
   Copyright (C) 2015 José Antonio Montes (jamontes)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Description:
   These funtions are called from the main plugin module, aimed to ease
   and simplify the add-on development process.
   Release 0.1.6
'''

import resources.lib.lutil as l

root_url = 'se.evtr.www//:sptth'[::-1]

def set_debug(debug_flag, func_log=l.local_log):
    """This function is a wrapper to setup the debug flag into the lutil module"""
    l.set_debug_mode(debug_flag, func_log)


def get_channels_menu(html_channels):
    """This function makes the program menu parammeters data structure for all the channel menus."""

    channel_pattern   = '<li class="rn."><a href="([^"]*?)" rel="nofollow"><span></span><strong>([^<]*?)</strong></a></li>'

    menu_level = []
    for url, channel in l.find_multiple(html_channels, channel_pattern):
        menu_item   = {
                'action' : 'program_list',
                'title'  : channel,
                'args'   : root_url + url,
                }
        menu_level.append(menu_item)

    return menu_level


def get_create_index():
    """This function gets the the first level index menu."""

    main_url = root_url + 'sanedac#/enr/atracala/'[::-1]

    menu_patterns = (
            ( 'menu_direct',  'href="([^"]*?)".*?([Rr]adio [Ee]n [Dd]irecto)'),
            )

    buffer_url   = l.carga_web(main_url)
    menu_entries = get_channels_menu(buffer_url)

    for action, pattern in menu_patterns:
        url, title = l.find_first(buffer_url, pattern) or ('', '')
        menu_item = {
                'action' : action,
                'title'  : l.clean_title(title),
                'args'   : root_url + url,
                }
        menu_entries.append(menu_item)

    return menu_entries


def get_program_list(menu_url, all_programmes_flag=False, localized=lambda x: x):
    """This function makes programmes list data structure for all the program sections."""

    program_pattern       = '<dd><a title="([^"]*?)" href="([^"]*?)">[^<]*?</a></dd>'
    suffix                = 'zaSP=ldom'[::-1]
    channel_pattern       = '<span class="last">([^<]*?)</span></h1>'
    page_num_pattern      = 'pbq=([0-9]+)'
    page_url_pattern      = 'class="%s">.*?<a name="paginaIR" href="([^"]*?)"'
    last_page_sep         = ' class="ultimo">'
    base_url_pattern      = '(^[^?]*?)\?'
    suffix_pattern        = '([^/]+)/$'
    suffix_string         = 'zaSP=ldom&se=gnal&=adeuqsuBartel&s%=xtc&1=qbp?'[::-1]

    if not suffix in menu_url:
        suffix            = suffix_string % l.find_first(menu_url, suffix_pattern)
        menu_url          = menu_url + suffix

    buffer_url            = l.carga_web(menu_url)
    program_list          = []
    reset_cache           = False
    canal                 = l.find_first(buffer_url, channel_pattern)
    base_url              = l.find_first(menu_url, base_url_pattern)

    curr_page_num         = l.find_first(menu_url, page_num_pattern) or '1'
    if curr_page_num != '1':
        previous_page_url = l.find_first(buffer_url, page_url_pattern % 'anterior')
        prev_page_num     = l.find_first(previous_page_url, page_num_pattern)
        program_entry     = {
                'url'     : base_url + previous_page_url.replace('&amp;', '&'),
                'title'   : '<< %s (%s)' % (localized('Previous page'), prev_page_num),
                'action'  : 'program_list',
                }
        program_list.append(program_entry)
        reset_cache = True

    for title, url in l.find_multiple(buffer_url, program_pattern):
        l.log('Program info. url: "%s" canal: "%s" title: "%s"' % (url, canal, title))
        program_entry     = {
                'url'     : url,
                'title'   : title,
                'comment' : "",
                'genre'   : "",
                'canal'   : canal,
                'program' : title,
                'action'  : 'audio_list'
                }
        program_list.append(program_entry)

    last_page_num         = l.find_first(buffer_url.split(last_page_sep)[1], page_num_pattern) if last_page_sep in buffer_url else ""
    if last_page_num and curr_page_num != last_page_num:
        next_page_url     = l.find_first(buffer_url, page_url_pattern % 'siguiente')
        next_page_num     = l.find_first(next_page_url, page_num_pattern)
        program_entry     = {
                'url'     : base_url + next_page_url.replace('&amp;', '&'),
                'title'   : '>> %s (%s/%s)' % (
                             localized('Next page'),
                             next_page_num,
                             last_page_num
                            ),
                'action'  : 'program_list',
                }
        program_list.append(program_entry)

    return { 'program_list': program_list, 'reset_cache': reset_cache }


def get_audio_list(program_url, localized=lambda x: x):
    """This function makes the emissions list data structure for all the programmes."""

    audio_section_sep     = '<span class="col_tit" '
    audio_fecha_pattern   = '<span class="col_fec">([^<]*?)</span>'
    audio_dur_pattern     = '<span class="col_dur">([^<]*?)</span>'
    audio_title_pattern   = '<span class="titulo-tooltip"><a href="[^"]*?" title="[^>]*?>([^<]*?)</a></span>'
    audio_desc_pattern    = '<span class="detalle">(.*?)</span>'
    audio_link_pattern    = '<span class="col_tip">.*?<a href="(http.*?mp[34])"'
    audio_rating_pattern  = '<span class="col_pop"><span title="([^"]*?)" class="pc([0-9]*?)">'
    audio_year_pattern    = '([0-9]{4})'
    page_num_pattern      = 'pbq=([0-9]+)'
    last_page_sep         = ' class="ultimo">'
    page_url_pattern      = 'class="%s">.*?<a name="paginaIR" href="([^"]*?)"'
    url_options           = ')ung-xunil(02%4.91.1F2%tegW=tnegA-resU|'[::-1]

    buffer_url            = l.carga_web(program_url)

    audio_list            = []
    reset_cache           = False
    this_year             = l.get_this_year()

    curr_page_num         = l.find_first(program_url, page_num_pattern) or '1'
    if curr_page_num != '1':
        previous_page_url = l.find_first(buffer_url, page_url_pattern % 'anterior')
        prev_page_num     = l.find_first(previous_page_url, page_num_pattern)
        audio_entry       = {
                'url'        : root_url + previous_page_url.replace('&amp;', '&').replace(' ', '%20'),
                'title'      : '<< %s (%s)' % (localized('Previous page'), prev_page_num),
                'action'     : 'audio_list',
                'IsPlayable' : False
                }
        audio_list.append(audio_entry)
        reset_cache = True
    else:
        first_page_url = l.find_first(buffer_url, page_url_pattern % 'primero')
        if not 'titleFilter' in first_page_url:
            audio_entry       = {
                    'url'        : root_url + first_page_url.replace('&amp;', '&') + '&titleFilter=%s',
                    'title'      : localized('Search'),
                    'action'     : 'search_program',
                    'IsPlayable' : False
                    }
            audio_list.append(audio_entry)

    for audio_section in buffer_url.split(audio_section_sep)[1:]:
        date              = l.find_first(audio_section, audio_fecha_pattern)
        duration          = l.find_first(audio_section, audio_dur_pattern) or '00:00:00'
        title             = l.find_first(audio_section, audio_title_pattern)
        desc              = l.find_first(audio_section, audio_desc_pattern)
        url               = l.find_first(audio_section, audio_link_pattern)
        rtlabel, rating   = l.find_first(audio_section, audio_rating_pattern) or ('', '1')
        year              = int(l.find_first(date, audio_year_pattern) or '0') or this_year

        tduration         = duration.split(':')
        if len(tduration) == 3:
            seconds = str(int(tduration[-3] or '0') * 3600 + int(tduration[-2] or '0') * 60 + int(tduration[-1] or '0'))
        elif len(tduration) == 2:
            seconds = str(int(tduration[-2] or '0') * 60 + int(tduration[-1] or '0'))
        else:
            seconds = tduration[-1]

        l.log('Podcast info. url: "%s" duration: "%s" seconds: "%s" title: "%s" rating: "%s" date: "%s"' % (
                url, duration, seconds, title, rating, date))

        audio_entry       = {
                'url'        : url + url_options,
                'title'      : "%s (%s)" % (
                                l.clean_title(title),
                                date,
                               ),
                'comment'    : "%s\n%s - %s - %s" % (
                                l.clean_title(desc),
                                duration,
                                date,
                                rtlabel,
                               ),
                'rating'     : int(rating)//20, # Rating goes from 0 to 5 in audio media.
                'duration'   : seconds,
                'year'       : year,
                'action'     : 'play_audio',
                'IsPlayable' : True,
                }
        if url: # This is to make sure the URL is valid.
            audio_list.append(audio_entry)

    last_page_num     = l.find_first(buffer_url.split(last_page_sep)[1], page_num_pattern) if last_page_sep in buffer_url else ""
    if last_page_num and curr_page_num != last_page_num:
        next_page_url = l.find_first(buffer_url, page_url_pattern % 'siguiente')
        next_page_num = l.find_first(next_page_url, page_num_pattern)
        audio_entry   = {
                'url'        : root_url + next_page_url.replace('&amp;', '&').replace(' ', '%20'),
                'title'      : '>> %s (%s/%s)' % (localized('Next page'), next_page_num, last_page_num),
                'action'     : 'audio_list',
                'IsPlayable' : False
                }
        audio_list.append(audio_entry)

    return { 'audio_list': audio_list, 'reset_cache': reset_cache }


def get_direct_channels():
    """This function makes the direct channels menu."""

    direct_url  = '8u3m.niam_s%_enr/ten.deziamaka.3vmaertsevilevtr//:sptth'[::-1]
    direct_url2 = '8u3m.retsam/s%/i/ten.dhiamaka.hl-0lgdmaevilslh//:sptth'[::-1]

    channel_list  = (
            ( 'Radio Nacional',   'r1'),
            ( 'Radio Clásica',    'r2'),
            ( 'Radio 3',          'r3'),
            ( 'Ràdio 4',          'r4'),
            ( 'Radio 5',          'r5_madrid'),
            )

    channel_list2  = (
            ( 'Radio Exterior',   'rneree_1@793572'),
            )

    menu_entries  = []
    for channel, playlist in channel_list:
        menu_item = {
                'action' : 'play_audio',
                'title'  : channel,
                'url'    : direct_url % playlist,
        }
        menu_entries.append(menu_item)

    for channel, playlist in channel_list2:
        menu_item = {
                'action' : 'play_audio',
                'title'  : channel,
                'url'    : direct_url2 % playlist,
        }
        menu_entries.append(menu_item)

    return menu_entries


def get_playable_url(url):
    """This function gets the stream url for direct channels."""

    playable_url_pattern = '(http[^#]+)'

    buffer_url           = l.carga_web(url)
    stream_url           = l.find_first(buffer_url, playable_url_pattern)
    l.log('get_playable_url has found this URL for direct playback. url: "%s"' % stream_url)

    return stream_url


def get_playable_search_url(url):
    """This function gets the media url from the search url link."""

    playable_url_pattern = '<link rel="audio_src" href="([^"]*?)"'
    url_options          = ')ung-xunil(02%4.91.1F2%tegW=tnegA-resU|'[::-1]

    buffer_url           = l.carga_web(url)
    media_url            = l.find_first(buffer_url, playable_url_pattern)
    l.log('get_playable_search_url has found this URL for playback. url: "%s"' % media_url)

    return media_url + url_options


def get_search_url(searchtext):
    """This returns the search url for search the audios into the posdcast."""

    search_prefix = '/rodacsub/se.evtr.www//:ptth'[::-1] + '=q?telvreSelgooG'[::-1]
    search_suffix = (
                    '=rartlif_timbus&oidar=etis&=atsah&=edsed&'[::-1] +\
                    'soidua=tnoc&ecnaveler=tros&1=trats&'[::-1]
                    )

    return  search_prefix + l.get_url_encoded(searchtext) + search_suffix


def get_search_list(search_url, localized=lambda x: x):
    """This function gets the list of items returned by the search engine."""

    search_section_sep    = '<div class="txtBox">'
    search_link_pattern   = '<a href="([^"]*?)"'
    search_title_pattern  = '<span class="maintitle">(.*?)</span>'
    search_desc_pattern   = '<div class="auxBox">[^<]*?<p>(.*?)</p>'
    search_year_pattern   = '<span class="datpub">[0-9]+.[0-9]+.([0-9]+)</span>'
    page_num_pattern      = 'start=([0-9]+)' # Starts by 1.
    page_url_pattern      = 'start=%d&'

    buffer_url            = l.carga_web(search_url)

    search_list           = []
    reset_cache           = False

    current_page_num      = int(l.find_first(search_url, page_num_pattern) or '1')
    if current_page_num  != 1:
        prev_page_num     = current_page_num - 1
        previous_page_url = search_url.replace(
                page_url_pattern % current_page_num,
                page_url_pattern % prev_page_num
                )
        search_entry      = {
                'url'        : previous_page_url,
                'title'      : '<< %s (%d)' % (localized('Previous page'), prev_page_num),
                'action'     : 'search_list',
                'IsPlayable' : False
                }
        search_list.append(search_entry)
        reset_cache = True

    for search_section in buffer_url.split(search_section_sep)[1:]:
        year              = l.find_first(search_section, search_year_pattern)
        title             = l.find_first(search_section, search_title_pattern)
        desc              = l.find_first(search_section, search_desc_pattern)
        url               = l.find_first(search_section, search_link_pattern)

        l.log('Podcast info. url: "%s"  title: "%s"' % (
                url, l.clean_title(title)))

        search_entry      = {
                'url'        : url,
                'title'      : l.clean_title(title),
                'comment'    : l.clean_title(desc),
                'year'       : year,
                'action'     : 'play_search',
                'IsPlayable' : True,
                }
        search_list.append(search_entry)

    next_page_num         = current_page_num + 1
    if l.find_first(buffer_url, page_url_pattern % next_page_num):
        next_page_url     = search_url.replace(
                page_url_pattern % current_page_num,
                page_url_pattern % next_page_num
                )
        search_entry      = {
                'url'        : next_page_url,
                'title'      : '>> %s (%d)' % (localized('Next page'), next_page_num),
                'action'     : 'search_list',
                'IsPlayable' : False
                }
        search_list.append(search_entry)

    return { 'search_list': search_list, 'reset_cache': reset_cache }


