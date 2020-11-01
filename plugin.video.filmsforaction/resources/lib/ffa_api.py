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

import resources.lib.lutil as l

root_url = 'https://www.filmsforaction.org'

def set_debug(debug_flag, func_log=l.local_log):
    """This function is a wrapper to setup the debug flag into the lutil module"""
    l.set_debug_mode(debug_flag, func_log)


def get_categories():
    """This function gets the categories list from the FFA website."""
    category_pattern = "'topic', '([0-9]+)'[^>]+?>([^<]+?)</a>"
    category_url = 'https://www.filmsforaction.org/library/?category=all+videos&topic=%s'

    buffer_url = l.carga_web(root_url)
    category_list = []
    topic_list = []
    for topic, category_name in l.find_multiple(buffer_url, category_pattern):
        if topic not in topic_list:
            url = category_url % topic
            category_list.append((url, category_name))
            topic_list.append(topic)

    return category_list


def get_videolist(url, cat_menu=""):
    """This function gets the video list from the FFA website and returns them in a pretty data format."""
    video_entry_sep        = 'content-view'
    video_url_pattern      = '["\'](/watch/[^/]*?/)'
    video_thumb_pattern    = '["\'](/img/[^"\']*?)["\']'
    video_title_pattern    = '<a href=["\']/watch/[^/]*?/["\'][ ]*?>([^<]+?)</a>'
    video_plot_pattern     = '<span class="content-description">([^<]*?)</span>'
    video_duration_pattern = '([0-9]+[ ]+[Mm]in)'
    video_rating_pattern   = '([0-9.]+[ ]+[Ss]tars)'
    video_views_pattern    = '([0-9,]+[ ]+[Vv]iews)'
    page_num_pattern       = 'href=["\']/library/([0-9]+)/'
    page_num_url_pattern   = 'href=["\'](/library/%d/[^"\']*?)["\']'
    page_num_cur_pattern   = '/library/([0-9]+)/'

    buffer_url = l.carga_web(url)

    video_list = []

    reset_cache = False
    current_page_num = int(l.find_first(url, page_num_cur_pattern) or '1')
    last_page_num = int(max(l.find_multiple(buffer_url, page_num_pattern) or ('1',), key=int))

    if current_page_num != 1:
        prev_page_num = current_page_num - 1
        previous_page_url = root_url + l.find_first(buffer_url, page_num_url_pattern % prev_page_num)
        video_entry = { 'url': previous_page_url, 'title': '<< %s (%d)' % (cat_menu, prev_page_num), 'IsPlayable': False }
        video_list.append(video_entry)
        reset_cache = True

    category = "Video" # The category is no longer included in the latest website change.
    for video_section in buffer_url.split(video_entry_sep)[1:]:
        url           = l.find_first(video_section, video_url_pattern)
        if not url:
            continue  # Sometimes in the search menu can appear articles and other sort of entries rather than videos.
        thumb         = l.find_first(video_section, video_thumb_pattern)
        title         = l.find_first(video_section, video_title_pattern)
        plot          = l.find_first(video_section, video_plot_pattern)
        duration      = l.find_first(video_section, video_duration_pattern)
        rating        = l.find_first(video_section, video_rating_pattern)
        views         = l.find_first(video_section, video_views_pattern)
        l.log('Video info. url: "%s" thumb: "%s" title: "%s"' % (url, thumb, title))
        l.log('Video tags. duration: "%s" rating: "%s" views: "%s"' % (duration, rating, views))
        video_entry = {
            'url'        : root_url + url,
            'title'      : title.strip() or '.',
            'thumbnail'  : root_url + thumb,
            'plot'       : "%s\n%s - %s - %s" % (
                            plot.strip(),
                            duration,
                            views,
                            rating,
                            ),
            'duration'   : int(duration.split()[0]) * 60 if duration else 0,
            'rating'     : rating.split()[0] if rating else '',
            'genre'      : category,
            'IsPlayable' : True
            }
        video_list.append(video_entry)

    if current_page_num < last_page_num:
        next_page_num = current_page_num + 1
        next_page_url = root_url + l.find_first(buffer_url, page_num_url_pattern % next_page_num)
        video_entry = { 'url': next_page_url, 'title': '>> %s (%d/%d)' % (cat_menu, next_page_num, last_page_num), 'IsPlayable': False }
        video_list.append(video_entry)

    return { 'video_list': video_list, 'reset_cache': reset_cache }


def get_search_url(search_string):
    """This function returns the search encoded URL to find the videos from the input search string"""
    return 'https://www.filmsforaction.org/library/?search=' + l.get_url_encoded(search_string)


def get_playable_url(url):
    """This function returns a playable URL parsing the different video sources available from the iframe link"""
    video_patterns = (
            ('vimeo1',       'vimeo.com/video/([0-9]+)',                                        'vimeo'),
            ('vimeo2',       'vimeo.com%2Fvideo%2F([0-9]+)',                                    'vimeo'),
            ('youtube1',     'videoId: "([0-9A-Za-z_-]{11})',                                   'youtube'),
            ('youtube2',     'youtube.com%2Fwatch%3Fv%3D([0-9A-Za-z_-]{11})',                   'youtube'),
            ('youtube3',     'youtube.com%2Fembed%2F([0-9A-Za-z_-]{11})',                       'youtube'),
            ('youtube4',     'youtube.com/embed/([0-9A-Za-z_-]{11})',                           'youtube'),
            ('dailymotion1', ' src="[htp:]*?//www.dailymotion.com/embed/video/([0-9a-zA-Z]+)',  'dailymotion'),
            ('dailymotion2', 'www.dailymotion.com%2Fembed%2Fvideo%2F(.*?)%',                    'dailymotion'),
            ('archiveorg1',  ' src="(https://archive.org/embed/[^"]*?)"',                       'archiveorg'),
            ('kickstarter1', ' src="(https://www.kickstarter.com/[^"]*?)"',                     'kickstarter'),
            ('tagtele1',     ' src="(http://www.tagtele.com/embed/[^"]*?)"',                    'tagtele'),
            )

    buffer_url = l.carga_web(url)

    for pattern_name, pattern, source in video_patterns:
        video_id = l.find_first(buffer_url, pattern)
        if video_id:
            l.log('We have found this video_id "%s" using the pattern: "%s"' % (video_id, pattern_name))
            try:
                playable_url = eval("get_playable_%s_url(video_id)" % source)
                break
            except:
                l.log("There was a problem using the pattern '%s' on this video link: '%s'\n" % (pattern_name, url))
                return ''
    else:
        l.log("Sorry, but we cannot support the type of video for this link yet:\n'%s'" % url)
        playable_url = ''

    return playable_url


def get_playable_vimeo_url(video_id):
    """This function returns the playable URL for the Vimeo embedded video from the video_id retrieved."""
    video_quality_pattern = '"profile":[0-9]+,"width":([0-9]+),.*?,"url":"([^"]*?)"'
    quality_list          = ('640', '720', '480', '320', '960', '1280', '1920')

    video_info_url   = 'https://player.vimeo.com/video/' + video_id
    buffer_link = l.carga_web(video_info_url)
    video_options  = dict((quality, video) for quality, video in l.find_multiple(buffer_link, video_quality_pattern))
    if len(video_options):
        l.log("List of video options: "+repr(video_options))
        for quality in quality_list:
            if quality in video_options:
                return video_options.get(quality)

        # This quality isn't normalized as it doesn't appear into the quality_list.
        return video_options.get(list(video_options.keys())[0])

    return ""


def get_playable_youtube_url(video_id):
    """This function returns the URL path to call the Youtube add-on with the video_id retrieved."""
    return 'plugin://plugin.video.youtube/play/?video_id=' + video_id


def get_playable_dailymotion_url(video_id):
    """This function returns the playable URL for the Dalymotion embedded video from the video_id retrieved."""
    daily_video_pattern   = '"([0-9]+)":\[[^]]*?{"type":"video\\\/mp4","url":"([^"]+?)"'
    daily_video_qualities = ('480', '720', '380', '240')

    daily_url = 'http://www.dailymotion.com/embed/video/' + video_id
    buffer_link = l.carga_web(daily_url)
    video_options  = dict((quality, video) for quality, video in l.find_multiple(buffer_link, daily_video_pattern))
    l.log("List of video options: "+repr(video_options))
    for quality_option in daily_video_qualities:
        if quality_option in video_options:
            video_url = video_options.get(quality_option).replace('\\','')
            return video_url

    return ""


def get_playable_archiveorg_url(archive_url):
    """This function returns the playable URL for the Archive.org embedded video from the video link retrieved."""
    pattern_archive_video = '<meta property="og:video" content="(.+?)"'

    buffer_link = l.carga_web(archive_url)
    return l.find_first(buffer_link, pattern_archive_video)


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

