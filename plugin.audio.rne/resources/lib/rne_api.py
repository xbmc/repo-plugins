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

import lutil as l

root_url = 'se.evtr.www//:ptth'[::-1]

def set_debug(debug_flag):
    """This function is a wrapper to setup the debug flag into the lutil module"""
    l.set_debug_mode(debug_flag)


def get_clean_title(title):
    """This function returns the title or desc cleaned.
       ref: http://www.thesauruslex.com/typo/eng/enghtml.htm"""

    return title.\
        replace('&aacute;',   'á').\
        replace('&agrave;',   'á').\
        replace('&eacute;',   'é').\
        replace('&egrave;',   'è').\
        replace('&iacute;',   'í').\
        replace('&oacute;',   'ó').\
        replace('&ograve;',   'ò').\
        replace('&uacute;',   'ú').\
        replace('&auml;',     'ä').\
        replace('&iuml;',     'ï').\
        replace('&ouml;',     'ö').\
        replace('&uuml;',     'ü').\
        replace('&szlig;',    'ß').\
        replace('&ntilde;',   'ñ').\
        replace('&ccedil;',   'ç').\
        replace('&Aacute;',   'Á').\
        replace('&Agrave;',   'À').\
        replace('&Eacute;',   'É').\
        replace('&Egrave;',   'È').\
        replace('&Iacute;',   'Í').\
        replace('&Oacute;',   'Ó').\
        replace('&Ograve;',   'Ò').\
        replace('&Uacute;',   'Ú').\
        replace('&Auml;',     'Ä').\
        replace('&Iuml;',     'Ï').\
        replace('&Ouml;',     'Ö').\
        replace('&Uuml;',     'Ü').\
        replace('&Ntilde;',   'Ñ').\
        replace('&Ccedil;',   'Ç').\
        replace('&#034;',     '"').\
        replace('&#34;',      '"').\
        replace('&#039;',     "´").\
        replace('&#39;',      "´").\
        replace('&#160;',     " ").\
        replace('&#8211;',     '').\
        replace('&#8217;',    "'").\
        replace('&#8220;',    '"').\
        replace('&#8221;',    '"').\
        replace('&#8223;',    "'").\
        replace('&#8230;',     '').\
        replace('&rsquo;',    "´").\
        replace('&laquo;',    '"').\
        replace('&ldquo;',    '"').\
        replace('&raquo;',    '"').\
        replace('&rdquo;',    '"').\
        replace('&iexcl;',    '¡').\
        replace('&iinte;',    '¿').\
        replace('&amp;',      '&').\
        replace('&nbsp;',      '').\
        replace('&quot;',     '"').\
        replace('&ordf',      'ª').\
        replace('&ordm',      'º').\
        replace('&middot;',   '·').\
        replace('&hellip;', '...').\
        replace('<br />',      '').\
        replace('<b>',         '').\
        replace('</b>',        '').\
        strip()


def get_two_level_menu(html):
    """This function makes the two level menu parammeters data structure for all the menu sections."""

    menu_pattern   = '<span>(Podcasts por [gc][^<]*?)</span>(.*?)</div></div></div>'
    menu_entry_pat = '<li> <a href="([^"]*?)" [^>]*?>([^<]*?)</a>'

    menu_level = []
    for menu_title, menu_body in l.find_multiple(html, menu_pattern):
        nested_menu = '¡'.join(['%s¿%s' % (url, get_clean_title(label)) for url, label in l.find_multiple(menu_body, menu_entry_pat)])
        menu_item   = {
                'action' : 'menu_sec',
                'title'  : get_clean_title(menu_title),
                'args'   : nested_menu,
                }
        menu_level.append(menu_item)

    return menu_level


def get_create_index():
    """This function gets the the first level index menu."""

    main_url = root_url + '/tsacdop/oidar/'[::-1]

    menu_patterns = (
            ( 'program_list', '<a href="([^"]*?)" title="(Listado de programas)"><span>'),
            ( 'menu_direct',  'href="([^"]*?)".*?([Ee]n [Dd]irecto)'),
            )

    buffer_url   = l.carga_web(main_url)
    menu_entries = get_two_level_menu(buffer_url)

    for action, pattern in menu_patterns:
        url, title = l.find_first(buffer_url, pattern) or ('', '')
        if url:
            menu_item = {
                'action' : action,
                'title'  : get_clean_title(title).capitalize(),
                'args'   : url,
                }
            menu_entries.append(menu_item)

    return menu_entries


def get_program_list(menu_url, all_programmes_flag=False, localized=lambda x: x):
    """This function makes programmes list data structure for all the program sections."""

    program_section_sep   = '<span class="col_tit"'
    program_fecha_pattern = '<span class="col_fec">([^<]*?)</span>'
    program_canal_pattern = "title=\"Ir a portada de '([^']*?)'"
    program_desc_pattern  = '<span class="detalle">(.*?)</span>'
    program_link_pattern  = '<span class="titulo-tooltip"><a href="([^"]*?)" title="[^>]*?>([^<]*?)</a></span>'
    program_genre_pattern = '<span class="col_cat">([^<]*?)</span>'
    page_num_pattern      = '/([0-9]+)/'
    page_url_pattern      = '<a name="paginaIR" href="([^"]*?)"><span>%s'
    page_num_url_pattern  = '<a name="paginaIR" href=".*?/([0-9]+)/[^"]*?"><span>%s'

    # This toggles between only on emission and all the programmes filter option selected from the add-on setings.
    filter_flag           = 'lla=retliFnoissime'[::-1]
    menu_url              = menu_url + '&csa=airetirc&1=redro?'[::-1] + filter_flag if all_programmes_flag and \
                                not filter_flag in menu_url else menu_url

    buffer_url            = l.carga_web(menu_url)

    program_list          = []
    reset_cache           = False

    curr_page_num = l.find_first(menu_url, page_num_pattern) or '1'
    if curr_page_num != '1':
        previous_page_url = l.find_first(buffer_url, page_url_pattern % 'Anterior')
        prev_page_num     = l.find_first(previous_page_url, page_num_pattern)
        program_entry     = {
                'url'     : root_url + previous_page_url.replace('&amp;', '&'),
                'title'   : '<< %s (%s)' % (localized('Previous page'), prev_page_num),
                'action'  : 'program_list',
                }
        program_list.append(program_entry)
        reset_cache = True


    for program_section in buffer_url.split(program_section_sep)[1:]:
        date              = l.find_first(program_section, program_fecha_pattern)
        desc              = l.find_first(program_section, program_desc_pattern)
        url, title        = l.find_first(program_section, program_link_pattern) or ('', '')
        genre             = l.find_first(program_section, program_genre_pattern)
        canal             = l.find_first(program_section, program_canal_pattern)
        title             = get_clean_title(title)
        l.log('Program info. url: "%s" canal: "%s" title: "%s" genre: "%s" date: "%s"' % (
                url, canal, title, genre, date))

        program_entry     = {
                'url'     : root_url + url,
                'title'   : "%s (%s | %s | %s)" % (
                             title,
                             canal,
                             genre,
                             date,
                            ),
                'comment' : "%s\n%s - %s" % (
                             desc.strip(),
                             genre,
                             date,
                            ),
                'genre'   : genre,
                'canal'   : canal,
                'program' : title,
                'action'  : 'audio_list'
                }
        program_list.append(program_entry)


    last_page_num = l.find_first(buffer_url, page_num_url_pattern % 'Último')
    if last_page_num and curr_page_num != last_page_num:
        next_page_url     = l.find_first(buffer_url, page_url_pattern % 'Siguiente')
        next_page_num     = l.find_first(next_page_url, page_num_pattern)
        program_entry     = {
                'url'     : root_url + next_page_url.replace('&amp;', '&'),
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
    page_url_pattern      = '<a name="paginaIR" href="([^"]*?)"><span>%s'
    page_num_url_pattern  = '<a name="paginaIR" href=".*?pbq=([0-9]+)[^"]*?"><span>%s'
    url_pref              = 'tlvl.dovm'[::-1]

    buffer_url            = l.carga_web(program_url)

    audio_list            = []
    reset_cache           = False
    this_year             = l.get_this_year()

    curr_page_num         = l.find_first(program_url, page_num_pattern) or '1'
    if curr_page_num != '1':
        previous_page_url = l.find_first(buffer_url, page_url_pattern % 'Anterior')
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
        first_page_url = l.find_first(buffer_url, page_url_pattern % 'Primero')
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
        # This is a workaround to use the coriginal links as the current ones
        # refuse the HTTP HEAD method required by Kodi to play the file.
        url               = l.find_first(audio_section, audio_link_pattern).replace(url_pref, 'www')
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
                'url'        : url,
                'title'      : "%s (%s)" % (
                                get_clean_title(title),
                                date,
                               ),
                'comment'    : "%s\n%s - %s - %s" % (
                                get_clean_title(desc),
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

    last_page_num     = l.find_first(buffer_url, page_num_url_pattern % 'Último')
    if last_page_num and curr_page_num != last_page_num:
        next_page_url = l.find_first(buffer_url, page_url_pattern % 'Siguiente')
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

    direct_url = 'u3m.3pm.s%/evtr/moc.noitomulf.evtr-3pm-eviloidar//:ptth'[::-1]

    channel_list  = (
            ( 'Radio Nacional',   'rne'),
            ( 'Radio Clásica',    'radioclasica'),
            ( 'Radio 3',          'radio3'),
            ( 'Ràdio 4',          'radio4'),
            ( 'Radio 5',          'radio5'),
            ( 'Radio Exterior',   'radioexterior'),
            )

    menu_entries  = []
    for channel, playlist in channel_list:
        menu_item = {
                'action' : 'play_audio',
                'title'  : channel,
                'url'    : direct_url % playlist,
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

    buffer_url           = l.carga_web(url)
    media_url            = l.find_first(buffer_url, playable_url_pattern)
    l.log('get_playable_search_url has found this URL for playback. url: "%s"' % media_url)

    return media_url


def get_search_url(searchtext):
    """This returns the search url for search the audios into the posdcast."""

    search_prefix = '/rodacsub/se.evtr.www//:ptth'[::-1] + '=q?telvreSelgooG'[::-1]
    search_suffix = (
                    'oidua=tnoc&0=nr&oidar=etis&=atsah&=edsed&'[::-1] +\
                    'oiduaE25252%EVTR=sdleifderiuqer&'[::-1]
                    )

    return  search_prefix + l.get_url_encoded(searchtext) + search_suffix


def get_search_list(search_url, localized=lambda x: x):
    """This function gets the list of items returned by the search engine."""

    search_section_sep    = '<div class="txtBox">'
    search_link_pattern   = '<a href="([^"]*?)"'
    search_title_pattern  = '<span class="maintitle">(.*?)</span>'
    search_desc_pattern   = '<div class="auxBox">[^<]*?<p>(.*?)</p>'
    search_year_pattern   = '<span class="datpub">[0-9]+.[0-9]+.([0-9]+)</span>'
    page_url_pattern      = '<li class="be_on"><span class="ico arrow %s_"><a href="([^"]*?)"'
    page_num_pattern      = 'start=([0-9]+)' # Starts by 0 and the results goes from 10 to 10.

    search_root           = '/rodacsub/se.evtr.www//:ptth'[::-1]
    buffer_url            = l.carga_web(search_url)

    search_list           = []
    reset_cache           = False

    previous_page_url     = l.find_first(buffer_url, page_url_pattern % 'back')
    if previous_page_url:
        prev_page_num     = int(l.find_first(previous_page_url, page_num_pattern))/10 + 1
        search_entry      = {
                'url'        : search_root + previous_page_url.replace('&amp;', '&'),
                'title'      : '<< %s (%d)' % (localized('Previous page'), prev_page_num),
                'action'     : 'search_list',
                'IsPlayable' : False
                }
        search_list.append(search_entry)
        reset_cache = True

    for search_section in buffer_url.split(search_section_sep)[1:]:
        year              = l.find_first(search_section, search_year_pattern)
        title             = l.find_first(search_section, search_title_pattern).strip()
        desc              = l.find_first(search_section, search_desc_pattern).strip()
        url               = l.find_first(search_section, search_link_pattern)

        l.log('Podcast info. url: "%s"  title: "%s"' % (
                url, get_clean_title(title)))

        search_entry      = {
                'url'        : url,
                'title'      : get_clean_title(title),
                'comment'    : get_clean_title(desc.replace('&amp;', '&')),
                'year'       : year,
                'action'     : 'play_search',
                'IsPlayable' : True,
                }
        search_list.append(search_entry)

    next_page_url         = l.find_first(buffer_url, page_url_pattern % 'next')
    if next_page_url:
        next_page_num     = int(l.find_first(next_page_url, page_num_pattern))/10 + 1
        search_entry      = {
                'url'        : search_root + next_page_url.replace('&amp;', '&'),
                'title'      : '>> %s (%d)' % (localized('Next page'), next_page_num),
                'action'     : 'search_list',
                'IsPlayable' : False
                }
        search_list.append(search_entry)

    return { 'search_list': search_list, 'reset_cache': reset_cache }


