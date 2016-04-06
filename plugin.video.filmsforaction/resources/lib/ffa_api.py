# _*_ coding: utf-8 _*_

'''
   Films For Action API lib: library functions for Films For Action add-on.
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

root_url = 'http://www.filmsforaction.org'

def set_debug(debug_flag):
    """This function is a wrapper to setup the debug flag into the lutil module"""
    l.set_debug_mode(debug_flag)


def get_categories():
    """This function gets the categories list from the FFA website."""
    catalog_pattern  = '<div class="DarkGray clearfix">(.*?)</div>'
    category_pattern = '<a href="([^"]*?)">([^<]*?)</a>'
    category_url = 'http://www.filmsforaction.org/films/'

    buffer_url = l.carga_web(category_url)
    catalog = l.find_first(buffer_url, catalog_pattern)
    category_list = []
    for category_url, category_name in l.find_multiple(catalog, category_pattern):
        url = root_url + category_url
        category_list.append((url, category_name))

    return category_list


def get_videolist(url, cat_menu=""):
    """This function gets the video list from the FFA website and returns them in a pretty data format."""
    video_entry_sep        = 'view-horizontal'
    video_url_pattern      = '["\'](/watch/[^/]*?/)'
    video_thumb_pattern    = '["\'](/img/[^"\']*?)["\']'
    video_title_pattern    = '<a href=["\']/watch/[^/]*?/["\'][ ]*?>([^<]+?)</a>'
    video_plot_pattern     = '<div class="content-text">([^<]*?)</div>'
    video_cat_pattern      = '>(Video|Short Film|Trailer|Documentary|Presentation)<'
    video_duration_pattern = '([0-9]+[ ]+[Mm]in)'
    video_rating_pattern   = '([0-9.]+[ ]+[Ss]tars)'
    video_views_pattern    = '([0-9,]+[ ]+[Vv]iews)'
    video_author_pattern   = '([Aa]dded by).*?<a href=["\']/[^/]*?/["\'][ ]*?>([^<]*?)</a>'
    page_num_pattern       = 'href=["\'][^"\']*?p=([0-9]+)'
    page_num_url_pattern   = 'href=["\']([^"\']*?p=%d[^"\']*?)["\']'
    page_num_cur_pattern   = 'p=([0-9]+)'

    buffer_url = l.carga_web(url)

    video_list = []

    reset_cache = False
    current_page_num = int(l.find_first(url, page_num_cur_pattern) or '1')
    last_page_num = int(max(l.find_multiple(buffer_url, page_num_pattern) or ('1',), key=int))

    if current_page_num != 1:
        prev_page_num = current_page_num - 1
        previous_page_url = l.find_first(buffer_url, page_num_url_pattern % prev_page_num)
        if not "http" in previous_page_url:
            previous_page_url = root_url + previous_page_url
        video_entry = { 'url': previous_page_url, 'title': '<< %s (%d)' % (cat_menu, prev_page_num), 'IsPlayable': False }
        video_list.append(video_entry)
        reset_cache = True

    for video_section in buffer_url.split(video_entry_sep)[1:]:
        category = l.find_first(video_section, video_cat_pattern)
        if category:
            url           = l.find_first(video_section, video_url_pattern)
            thumb         = l.find_first(video_section, video_thumb_pattern)
            title         = l.find_first(video_section, video_title_pattern)
            plot          = l.find_first(video_section, video_plot_pattern)
            duration      = l.find_first(video_section, video_duration_pattern)
            rating        = l.find_first(video_section, video_rating_pattern)
            views         = l.find_first(video_section, video_views_pattern)
            label, author = l.find_first(video_section, video_author_pattern) or ('', '')
            l.log('Video info. url: "%s" thumb: "%s" title: "%s" category: "%s"' % (url, thumb, title, category))
            l.log('Video tags. duration: "%s" rating: "%s" views: "%s" author: "%s %s"' % (duration, rating, views, label, author))
            video_entry = {
                'url'        : root_url + url,
                'title'      : title.strip() or '.',
                'thumbnail'  : root_url + thumb,
                'plot'       : "%s\n%s - %s - %s - %s\n%s %s" % (
                                plot.strip(),
                                category,
                                duration,
                                views,
                                rating,
                                label,
                                author,
                                ),
                'duration'   : int(duration.split()[0]) if duration else 0,
                'rating'     : rating.split()[0] if rating else '',
                'genre'      : category,
                'credits'    : author,
                'IsPlayable' : True
                }
            video_list.append(video_entry)

    if current_page_num < last_page_num:
        next_page_num = current_page_num + 1
        next_page_url = l.find_first(buffer_url, page_num_url_pattern % next_page_num)
        if not "http" in next_page_url:
            next_page_url = root_url + next_page_url
        video_entry = { 'url': next_page_url, 'title': '>> %s (%d/%d)' % (cat_menu, next_page_num, last_page_num), 'IsPlayable': False }
        video_list.append(video_entry)

    return { 'video_list': video_list, 'reset_cache': reset_cache }


def get_search_url(search_string):
    """This function returns the search encoded URL to find the videos from the input search string"""
    return 'http://www.filmsforaction.org/search/?s=' + l.get_url_encoded(search_string)


def get_playable_url(url):
    """This function returns a playable URL parsing the different video sources available from the iframe link"""
    video_patterns = (
            ('vimeo1', 'vimeo.com/video/([0-9]+)', 'vimeo'),
            ('vimeo2', 'vimeo.com%2Fvideo%2F([0-9]+)', 'vimeo'),
            ('youtube1', 'videoId: "([0-9A-Za-z_-]{11})', 'youtube'),
            ('youtube2', 'youtube.com%2Fembed%2F([0-9A-Za-z_-]{11})', 'youtube'),
            ('youtube3', 'youtube.com/embed/([0-9A-Za-z_-]{11})', 'youtube'),
            ('dailymotion1', ' src="[htp:]*?//www.dailymotion.com/embed/video/([^"]*?)"', 'dailymotion'),
            ('dailymotion2', 'www.dailymotion.com%2Fembed%2Fvideo%2F(.*?)%', 'dailymotion'),
            ('archiveorg1', ' src="(https://archive.org/embed/[^"]*?)"', 'archiveorg'),
            ('snagfilms1', ' src="http://embed.snagfilms.com/embed/player\?filmId=([^"]*?)"', 'snagfilms'),
            ('kickstarter1', ' src="(https://www.kickstarter.com/[^"]*?)"', 'kickstarter'),
            ('tagtele1', ' src="(http://www.tagtele.com/embed/[^"]*?)"', 'tagtele'),
            ('disclosetv1', ' src="http://www.disclose.tv/embed/([^"]*?)"', 'disclosetv'),
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
    """This function returns the playable URL for the Vimeo embedded video from the video_id retrieved."""
    video_quality_pattern = '"profile":[0-9]+,"width":([0-9]+),.*?,"url":"([^"]*?)"'
    quality_list          = ('640', '480', '1280')

    video_info_url   = 'https://player.vimeo.com/video/' + video_id
    buffer_link = l.carga_web(video_info_url)
    video_options  = dict((quality, video) for quality, video in l.find_multiple(buffer_link, video_quality_pattern))
    l.log("List of video options: "+repr(video_options))
    for quality in quality_list:
        if quality in video_options:
            return video_options.get(quality)

    return ""


def get_playable_youtube_url(video_id):
    """This function returns the URL path to call the Youtube add-on with the video_id retrieved."""
    return 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + video_id


def get_playable_dailymotion_url(video_id):
    """This function returns the playable URL for the Dalymotion embedded video from the video_id retrieved."""
    daily_video_pattern = '"%s":\[{"type":"video\\\/mp4","url":"(.+?)"'
    daily_video_qualities = ('480', '720', '380', '240')

    daily_url = 'http://www.dailymotion.com/embed/video/' + video_id
    buffer_link = l.carga_web(daily_url)
    for video_quality in daily_video_qualities:
        video_url = l.find_first(buffer_link, daily_video_pattern % video_quality)
        if video_url:
            return video_url.replace('\\', '')
    return ""


def get_playable_archiveorg_url(archive_url):
    """This function returns the playable URL for the Archive.org embedded video from the video link retrieved."""
    pattern_archive_video = '<meta property="og:video" content="(.+?)"'

    buffer_link = l.carga_web(archive_url)
    return l.find_first(buffer_link, pattern_archive_video)


def get_playable_snagfilms_url(video_id):
    """This function returns the URL path to call the SnagFilms add-on with the video_id retrieved."""
    return 'plugin://plugin.video.snagfilms/?mode=GV&url=%s' % l.get_url_encoded(video_id)


def get_playable_kickstarter_url(kickstarter_url):
    """This function returns the playable URL for the Kickstarter embedded video from the video link retrieved."""
    pattern_kickstarter_video = ' data-video-url="(.+?)"'

    buffer_link = l.carga_web(kickstarter_url)
    return l.find_first(buffer_link, pattern_kickstarter_video)


def get_playable_tagtele_url(tagtele_url):
    """This function returns the playable URL for the Tagtele embedded video from the video link retrieved."""
    pattern_tagtele_video = " file: '(.+?)'"

    buffer_link = l.carga_web(tagtele_url)
    return l.find_first(buffer_link, pattern_tagtele_video)


def get_playable_disclosetv_url(video_id):
    """This function returns the URL path to call the Disclose TV add-on with the video_id retrieved."""
    return 'plugin://plugin.video.disclose_tv/video/' + video_id

