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


def get_videolist(url, localized=lambda x: x):
    """This function gets the video list from the FFA website and returns them in a pretty data format."""
    video_entry_sep        = '<div class="content-view view-horizontal clearfix ">'
    video_urls_pattern     = '<div class="content-image-wrapper">[^<]*?<a href=\'([^"]*?)\'><img class="[^"]*?" data-original="([^"]*?)"'
    video_title_pattern    = '<div class="content-name">[^<]*?<a href="[^"]*?">([^<]*?)</a>'
    video_plot_pattern     = '<div class="content-text">([^<]*?)</div>'
    video_info_pattern     = '<div class="content-info"><a href="[^>]*?>([^<]*?)</a>([^<]*?)<a href="[^>]*?>([^<]*?)</a></div>'
    video_duration_pattern = ' ([0-9]*?) min '
    video_rating_pattern   = ' ([0-9.]*?) stars '
    page_count_pattern     = '<span id="C_SR_LabelResultsCount[^"]*?">([0-9]*?)-([0-9]*?) of ([0-9]*?) [^<]*?</span>'
    prev_page_pattern      = '<div style="float:left">[^<]*?<a href="([^"]*?)"><img id="C_SR_IPrevious"'
    next_page_pattern      = '<div style="float:right">[^<]*?<a href="([^"]*?)"><img id="C_SR_INext"'

    buffer_url = l.carga_web(url)

    video_list = []

    first_video, last_video, total_videos = l.find_first(buffer_url, page_count_pattern) or ('0', '0', '0')
    current_page = (int(first_video) / 50) + 1
    last_page = (int(total_videos) / 50) + 1
    next_page_num = current_page + 1 if current_page < last_page else 0
    prev_page_num = current_page - 1
    reset_cache = False

    if prev_page_num:
        previous_page_url = l.find_first(buffer_url, prev_page_pattern)
        video_entry = { 'url': previous_page_url, 'title': '<< %s (%d)' % (localized('Previous page'), prev_page_num), 'IsPlayable': False }
        video_list.append(video_entry)
        reset_cache = True

    for video_section in buffer_url.split(video_entry_sep):
        url, thumb = l.find_first(video_section, video_urls_pattern) or ('', '')
        title = l.find_first(video_section, video_title_pattern)
        plot  = l.find_first(video_section, video_plot_pattern)
        category, info, author = l.find_first(video_section, video_info_pattern) or ('', '', '')
        l.log('Video info. url: "%s" thumb: "%s" title: "%s" category: "%s"' % (url, thumb, title, category))
        if category in ('Video', 'Short Film', 'Trailer', 'Documentary', 'Presentation'): # This is to avoid blog posts yielded from Search.
            duration = l.find_first(info, video_duration_pattern)
            rating = l.find_first(info, video_rating_pattern)
            video_entry = { 
                    'url': root_url + url,
                    'title': title.strip(),
                    'thumbnail': root_url + thumb,
                    'plot': "%s\n%s%s%s" % (plot.strip(), category, info.replace('&middot;', '-'), author),
                    'duration': int(duration) if duration else 0,
                    'rating': rating,
                    'genre': category,
                    'credits': author,
                    'IsPlayable': True
                    }
            video_list.append(video_entry)

    if next_page_num:
        next_page_url = l.find_first(buffer_url, next_page_pattern)
        video_entry = { 'url': next_page_url, 'title': '>> %s (%d/%d)' % (localized('Next page'), next_page_num, last_page), 'IsPlayable': False }
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
            ('disclosetv1', ' src="(http://www.disclose.tv/embed/[^"]*?)"', 'disclosetv'),
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
    This is a workaround to avoid the problem found with the Vimeo Add-on running on Gotham. Under Frodo, calling the Vimeo Add-on with the video_id works great."""
    video_pattern_sd = '"sd":{.*?,"url":"([^"]*?)"'
    video_info_url   = 'https://player.vimeo.com/video/' + video_id

    buffer_link = l.carga_web(video_info_url)
    return l.find_first(buffer_link, video_pattern_sd)


def get_playable_youtube_url(video_id):
    """This function returns the URL path to call the Youtube add-on with the video_id retrieved."""
    return 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + video_id


def get_playable_dailymotion_url(video_id):
    """This function returns the playable URL for the Dalymotion embedded video from the video_id retrieved."""
    pattern_daily_video = '"stream_h264_hq_url":"(.+?)"'

    daily_url = 'http://www.dailymotion.com/embed/video/' + video_id
    buffer_link = l.carga_web(daily_url)
    video_url = l.find_first(buffer_link, pattern_daily_video)
    if video_url:
        return video_url.replace('\\','')


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


def get_playable_disclosetv_url(disclose_url):
    """This function returns the playable URL for the Disclose TV  embedded video from the video link retrieved."""
    pattern_disclose_location = 'location.href="(.+?)"'
    pattern_disclose_video = '{ url: "(.+?)"'

    buffer_link = l.carga_web(disclose_url)
    location_link = l.find_first(buffer_link, pattern_disclose_location)
    if location_link:
        location_url = 'http://www.disclose.tv%s1280&height=720&flash=11&url=' % location_link
        buffer_link = l.carga_web(location_url)
        return l.find_first(buffer_link, pattern_disclose_video)
