# _*_ coding: utf-8 _*_

'''
   LaTeleLibre.fr API lib: library functions for LaTeleLibre.fr add-on.
   Copyright (C) 2014 José Antonio Montes (jamontes)
   
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

root_url = 'http://latelelibre.fr'

def set_debug(debug_flag):
    """This function is a wrapper to setup the debug flag into the lutil module"""
    l.set_debug_mode(debug_flag)


def get_clean_title(title):
    """This function returns the title or plot cleaned."""
    return title.\
        replace('&#8211;',  '').\
        replace('&#8230;',  '').\
        replace('&#039;',   "´").\
        replace('&rsquo;',  "´").\
        replace('&laquo;',  '"').\
        replace('&raquo;',  '"').\
        replace('&nbsp;',   '').\
        replace('&quot;',   '"').\
        replace('&hellip;', '...').\
        replace('<br />',   '').\
        strip()


def get_post_data_encoded(params):
    """This function encodes the data parammeters to send the post HTTP"""

    themes_arg = 'themes=' if params['theme'] == 'all' else 'themes%5B%5D='
    if params.get('exclude'):
        exclude_list = '&'.join([ "exclude%5B%5D=" + id_video for id_video in params.get('exclude').split(';') ])
        return 'type=%s&%s%s&sorting=%s&%s&limit=%s' % (
                                                        params['type'],
                                                        themes_arg,
                                                        params['theme'],
                                                        params['sorting'],
                                                        exclude_list,
                                                        params['limit'],
                                                        )

    return 'type=%s&%s%s&sorting=%s&limit=%s' % (
                                                params['type'],
                                                themes_arg,
                                                params['theme'],
                                                params['sorting'],
                                                params['limit'],
                                                )


def parse_video_list(html):
    """This function parses the video list from the HTML content retrieved from the website"""

    item_sep = 'data-id'
    video_entry_pattern ='^="([0-9]+?)" data-title="([^"]*?)" data-type="[^"]*?" data-theme="([^"]*?)" data-timestamp="[^"]*?" data-views="([^"]*?)" data-comments="[^"]*?" data-rating="([^"]*?)">'
    video_entry_url     = '<div class="illustration">[^<]*?<a href="([^"]*?)"><img width="[^"]*?" height="[^"]*?" src="([^"]*?)"'
    video_entry_plot    = '<div class="chapeau">.*?<p>(.*?)</p>'
    video_entry_date    = '<p class="date"><span class="for-reader">(.*?)</span><time datetime="([^T]*?)T[^"]*?">(.*?)</time>'
    video_entry_author  = ' rel="author">(.*?)</a>'
    video_author_label  = '<p class="author">(.*?)<'
    video_views_label   = '<li class="views"><span>.*?<span class="for-reader">(.*?)</span></span></li>'

    video_ids    = []
    video_list   = []
    author_label = get_clean_title(l.find_first(html, video_author_label)) or '=>'
    views_label  = l.find_first(html, video_views_label)  or '(0)'

    for video_section in html.split(item_sep):
        video_id, title, theme, views, rating = l.find_first(video_section, video_entry_pattern) or ('', '', '', '0', '0')
        if video_id:
            video_ids.append(video_id) 
            url, thumb = l.find_first(video_section, video_entry_url) or ('', '')
            l.log('Video info. video_id: "%s" url: "%s" thumb: "%s" title: "%s" category: "%s" views: "%s" rating: "%s"' % (video_id, url, thumb, title, theme, views, rating))
            plot = l.find_first(video_section, video_entry_plot)
            date_text, timestamp, date = l.find_first(video_section, video_entry_date) or ('', '', '')
            year, month, day = timestamp.split('-') or ('', '', '')
            author = l.find_first(video_section, video_entry_author)
            l.log('Video info. plot: "%s"\ndate_text: "%s" timestamp: "%s" date: "%s" author: "%s"' % (plot, date_text, timestamp, date, author))
            video_entry = {
                    'url'        : url,
                    'title'      : "%s (%s/%s/%s)" % (
                                    get_clean_title(title),
                                    day,
                                    month,
                                    year,
                                   ),
                    'thumbnail'  : thumb,
                    'plot'       : "%s\n%s%s\n%s  %s%s  %s*  %s %s" % (
                                    get_clean_title(plot),
                                    date_text,
                                    date,
                                    theme,
                                    views,
                                    views_label,
                                    rating,
                                    author_label,
                                    author,
                                   ),
                    'rating'     : rating,
                    'genre'      : theme,
                    'year'       : year,
                    'credits'    : author,
                    'IsPlayable' : True
                    }
            video_list.append(video_entry)

    return video_list, video_ids


def parse_menu_hackaround(source_url, html_buffer):
    """This function is a'hackaround to parse and extract the video list info from the 'Un Bien Belge Histoire' program,
    due to its special contents.
    """

    title_pattern       = '<meta property="og:title" content="(.*?)"'
    plot_pattern        = '<meta property="og:description" content="(.*?)"'
    thumb_pattern       = '<meta property="og:image" content="(.*?)"'
    video_block_pattern = '<h2>Sur le même sujet</h2>[^<]*?<ul>(.*?)</ul>'
    url_item_pattern    = '<a href="(.*?)"'
    thumb_item_pattern  = '<img src="(.*?)"'
    title_item_pattern  = '<span>(.*?)</span>'

    video_list = [ {
        'url'        : source_url,
        'title'      : get_clean_title(l.find_first(html_buffer, title_pattern)),
        'plot'       : get_clean_title(l.find_first(html_buffer, plot_pattern)),
        'thumbnail'  : l.find_first(html_buffer, thumb_pattern),
        'IsPlayable' : True,
        }, ]

    video_block = l.find_first(html_buffer, video_block_pattern)

    for video_item in video_block.split('</a>'):
        item = {
            'url'        : l.find_first(video_item, url_item_pattern),
            'title'      : get_clean_title(l.find_first(video_item, title_item_pattern)),
            'thumbnail'  : l.find_first(video_item, thumb_item_pattern),
            'IsPlayable' : True,
            }
        video_list.append(item)

    return video_list


def get_video_items(cookies='', params='', localized=lambda x: x):
    """This function gets the video items from the LTL website and returns them in a pretty data format."""

    if not params:
        params = {
            'type'    : 'all',
            'theme'   : 'all',
            'sorting' : 'timestamp',
            'exclude' : '',
            'limit'   : '15',
            }

    l.log('api.get_video_items Value of params: "%s"' % repr(params))
    post_data = get_post_data_encoded(params)
    l.log('api.get_video_items Value of post_data: "%s"' % post_data)

    url_post = 'http://latelelibre.fr/ajax/catalog.php'
    my_headers = {
                    'Accept'               : '*/*',
                    'Accept-Language'      : 'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
                    'Accept-Encoding'      : 'deflate',
                    'Content-type'         : 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With'     : 'XMLHttpRequest',
                    'Referer'              : 'http://latelelibre.fr/',
                    'Cookie'               :  cookies,
                    'Pragma'               : 'no-cache',
                    'Cache-Control'        : 'no-cache',
                }



    buffer_web, cookies_web = l.send_post_data(url_post, my_headers, post_data)

    reset_cache = False

    video_list, videoids = parse_video_list(buffer_web)

    if len(videoids) >= int(params['limit']) - 3:
        if params.get('exclude'):
            exclude_list = params.get('exclude') + ';' + ';'.join(videoids)
        else:
            exclude_list = ';'.join(videoids) 

        video_entry = {
                    'title'      : '>> %s' % localized('Next page'),
                    'exclude'    : exclude_list,
                    'type'       : params.get('type') or 'emission',
                    'theme'      : params.get('theme') or 'all',
                    'sorting'    : params.get('sorting') or 'timestamp',
                    'limit'      : params.get('limit') or '8',
                    'IsPlayable' : False,
                    }
        video_list.append(video_entry)

    return { 'video_list': video_list, 'reset_cache': reset_cache }


def get_two_level_menu(html):
    """This function makes the two level menu parammeters data structure for all the menu sections."""

    pattern_list = (
            ('catalogue',   '<input name="catalog-themes\[\]" type="radio" value="([^"]*?)"[^>]*?><span>(.*?)</span>'),
            ('order',       '<input name="catalog-sorting" type="radio" value="([^"]*?)"[^>]*?><span>(.*?)</span>'),
            ('emissions',   '<a href="(/emissions/[^"]+?)">(.*?)</a>'),
            ('chroniques',  '<a href="(/chroniques/[^"]+?)">(.*?)</a>'),
            ('series',      '<a href="(/series/[^"]+?)">(.*?)</a>'),
            )

    level_parms = {}
    for lparam, lpattern in pattern_list:
        level_parms[lparam] = '¡'.join(['%s¿%s' % (section, label) for section, label in l.find_multiple(html, lpattern)])

    return level_parms


def get_create_index():
    """This function gets the the first level index menu."""

    root_url = 'http://latelelibre.fr'
    menu_entries = (
            ( 'menu_grille',   '<label class="all selected">.*?<span>(.*?)</span></label>', 'all'), 
            ( 'menu_grille',   '<label class="news">.*?<span>(.*?)</span></label>',         'reportage'), 
            ( 'menu_sec',      '<a href="/emissions/">(.*?)</a>',                           'emissions'), 
            ( 'menu_sec',      '<a href="/chroniques/">(.*?)</a>',                          'chroniques'), 
            ( 'menu_sec',      '<a href="/series/">(.*?)</a>',                              'series'), 
            ( 'video_docs',    '<h1 class="tt">(Les Docs)</h1>',                            ''), 
            ( 'search_videos', '<a href="#recherche">(.*?)</a>',                            ''), 
            )
    
    buffer_url = l.carga_web(root_url)
    level_options = get_two_level_menu(buffer_url)

    menu_list = []
    for action, menu_pattern, menu_opt in menu_entries:
        title = l.find_first(buffer_url, menu_pattern)
        if title:
            menu_entry = {
                'action'     : action,
                'title'      : title,
                }
            if action == 'menu_grille':
                menu_entry['themes']  = level_options['catalogue']
                menu_entry['sorting'] = level_options['order']
                menu_entry['ctype']   = menu_opt
            if action == 'menu_sec':
                menu_entry['menus']   = level_options[menu_opt]

            menu_list.append(menu_entry)

    l.log('valor de menu_list:\n%s' % repr(menu_list))
    return menu_list


def get_video_sec(url):
    """This function gets the video list for Emissions, Chroniques, Series, and Search sections."""
    pattern_next = '<li class="next"><a href="([^"]*?)">(.*?)</a></li>'

    buffer_url = l.carga_web(url)
    video_list, video_ids = parse_video_list(buffer_url)
    if not len(video_list): # This is a "kackaround" for "Un Bien Belge Histoire" special menu.
        video_list = parse_menu_hackaround(url, buffer_url)
    # This section is for the Search menu Next Page entry.
    next_url, next_label = l.find_first(buffer_url, pattern_next) or ('', '')
    if next_url:
        item_next = {
            'url'        : next_url,
            'title'      : ">> %s" % next_label,
            'IsPlayable' : False,
            }
        video_list.append(item_next)

    return video_list


def get_video_docs():
    """This function gets the Documentals video list from the main page website."""

    section_sep        = '<div id="docs">'
    entry_pattern      = '<article class="illustrated">(.*?)</article>'
    video_entry_title  = '<h2><a href="[^>]*?>(.*?)</a></h2>'
    video_entry_themes = ' rel="tag">(.*?)</a>'
    video_entry_views  = '<li class="views"><span>(.*?)<span class="for-reader">(.*?)</span></span></li>'
    video_entry_rating = 'ratings_off\(([^,]*?)'
    video_entry_url    = '<a href="([^"]*?)"><img width="[^"]*?" height="[^"]*?" src="([^"]*?)"'
    video_entry_plot   = '<div class="chapeau">.*?<p>(.*?)</p>'
    video_entry_date   = '<span class="date"><time datetime="([^T]*?)T[^"]*?">(.*?)</time>'
    video_entry_author = '<span class="author">(.*?)<a href="[^>]*?>(.*?)</a>'

    root_url   = 'http://latelelibre.fr/'
    buffer_url = l.carga_web(root_url)

    video_list    = []
    docs_contents = buffer_url.split(section_sep)[1] or ''
    for video_entry in l.find_multiple(docs_contents, entry_pattern):
        title                = l.find_first(video_entry, video_entry_title)
        url, thumb           = l.find_first(video_entry, video_entry_url)    or ('', '')
        views                = "%s%s" % l.find_first(video_entry, video_entry_views) or ('', '')
        rating               = l.find_first(video_entry, video_entry_rating)
        plot                 = l.find_first(video_entry, video_entry_plot)
        timestamp, date      = l.find_first(video_entry, video_entry_date)   or ('', '')
        author_label, author = l.find_first(video_entry, video_entry_author) or ('', '')
        theme_list           = ''
        for itheme in l.find_multiple(video_entry, video_entry_themes):
            theme_list   = '%s %s' % (theme_list, itheme)
        year, month, day = timestamp.split('-') or ('', '', '')
        l.log('Video info. title: "%s"\nviews: "%s" timestamp: "%s" date: "%s" author: "%s"' % (title, views, timestamp, date, author))
        video_entry = {
                'url'        : url,
                'title'      : "%s (%s/%s/%s)" % (
                                get_clean_title(title),
                                day,
                                month,
                                year,
                               ),
                'thumbnail'  : thumb,
                'plot'       : "%s\n%s\n%s %s %s %s %s" % (
                                get_clean_title(plot),
                                date,
                                theme_list,
                                views,
                                rating,
                                get_clean_title(author_label),
                                author
                               ),
                'rating'     : rating,
                'genre'      : theme_list.strip(),
                'year'       : year,
                'credits'    : author,
                'IsPlayable' : True
                }
        video_list.append(video_entry)

    return video_list


def get_search_url(search_string):
    """This function returns the search encoded URL to find the videos from the input search string"""
    return 'http://latelelibre.fr/archives/%s/' % l.get_url_encoded(search_string)


def get_playable_url(url):
    """This function returns a playable URL parsing the different video sources available from the iframe link"""
    video_patterns = (
            ('dailymotion1', '"[htp:]*?//www.dailymotion.com[/]+?video/([^"]*?)"',   'dailymotion'),
            ('dailymotion2', '"[htp:]*?//www.dailymotion.com/embed/video/([^"]*?)"', 'dailymotion'),
            ('dailymotion3', 'www.dailymotion.com%2Fembed%2Fvideo%2F(.*?)%',         'dailymotion'),
            ('youtube1',     'videoId: "([0-9A-Za-z_-]{11})',                        'youtube'),
            ('youtube2',     'youtube.com/watch\?v=([0-9A-Za-z_-]{11})',             'youtube'),
            ('youtube3',     'youtube.com%2Fembed%2F([0-9A-Za-z_-]{11})',            'youtube'),
            ('youtube4',     'youtube.com/embed/([0-9A-Za-z_-]{11})',                'youtube'),
            ('vimeo1',       'vimeo.com/video/([0-9]+)',                             'vimeo'),
            ('vimeo2',       'vimeo.com%2Fvideo%2F([0-9]+)',                         'vimeo'),
            ('arte1',        'json_url=(http://arte.tv/.*?json)',                    'arte'),
            )
    
    buffer_url = l.carga_web(url)

    for pattern_name, pattern, source in video_patterns:
        video_id = l.find_first(buffer_url, pattern)
        if video_id:
            l.log('We have found this video_id "%s" using the pattern: "%s"' % (video_id, pattern_name))
            playable_url = eval("get_playable_%s_url(video_id)" % source)
            break
    else:
        l.log("Sorry, but we cannot support the type of video for this link yet:\n'%s'" % url)
        playable_url = ''

    return playable_url


def get_playable_vimeo_url(video_id):
    """This function returns the playable URL for the Vimeo embedded video from the video_id retrieved.
    This is a workaround to avoid the problem found with the Vimeo Add-on running on Gotham.
    On Frodo, calling the Vimeo Add-on with the video_id works great."""
    video_pattern_sd = '"sd":{.*?,"url":"([^"]*?)"'
    video_info_url   = 'https://player.vimeo.com/video/' + video_id

    buffer_link = l.carga_web(video_info_url)
    return l.find_first(buffer_link, video_pattern_sd)


def get_playable_youtube_url(video_id):
    """This function returns the URL path to call the Youtube add-on with the video_id retrieved."""
    return 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + video_id


def get_playable_dailymotion_url(video_id):
    """This function returns the playable URL for the Dalymotion embedded video from the video_id retrieved."""
    daily_video_patterns = (
        '"stream_h264_hq_url":"(.+?)"',
        '"stream_h264_url":"(.+?)"',
        '"stream_h264_ld_url":"(.+?)"',
        )

    daily_url = 'http://www.dailymotion.com/embed/video/' + video_id
    buffer_link = l.carga_web(daily_url)
    for pattern_daily_video in daily_video_patterns:
        video_url = l.find_first(buffer_link, pattern_daily_video)
        if video_url:
            return video_url.replace('\\','')
    return ''


def get_playable_arte_url(json_url):
    """This function returns the playable URL for the Arte TV embedded video from the video_id retrieved.
    Credits and thanks to AddonScriptorDE for his Arte.tv add-on and let me learn from his code how to do it.
    Unfortunately, I cannot call his add-on directly due to the way the video URL is already encoded into the
    LTL website iframe, so I have to reproduce a custom version of the scraper here to let the Vox Pop to work.
    """

    # Note: the following two lines are learned from AddonScriptorDE's Arte.tv add-on code.
    video_pattern_sd = '"HBBTV","VQU":"EQ","VMT":"mp4","VUR":"(.+?)"'
    arte_url = json_url.replace('/player/', '/')

    buffer_link = l.carga_web(arte_url)
    return l.find_first(buffer_link, video_pattern_sd)


