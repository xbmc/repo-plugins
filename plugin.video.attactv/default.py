# -*- coding: utf-8 -*-

'''
   XBMC attactv plugin.
   Copyright (C) 2013 José Antonio Montes (jamontes)

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

   This is the first trial of the attactv plugin for XBMC.
   This plugins gets the videos from ATTAC TV web site and shows them ordered by appearance.
   This plugin depends on the lutil library functions.
   This plugin depends as well of the external youtube plugin.
'''

import lutil

pluginhandle = int(sys.argv[1])
plugin_id = 'plugin.video.attactv'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting("debug"))
translation = settings.getLocalizedString
language_id = settings.getSetting("language")

# Language options selected from add-on settings.
language_list = ('system', 'es', 'en', 'fr', 'de')
trans_language = {'Spanish' : 'es', 'English' : 'en', 'French' : 'fr', 'German' : 'de'}

# Language gets the the proper value from language_list
try:
    language = language_list[int(language_id)]
except:
    lutil.log("attactv.main Warning: language not defined. fixed to 0")
    settings.setSetting("language", "0")
    language = language_list[0]

if language == 'system':
    # We need to get the system language used by the GUI.
    syslanguage = lutil.get_system_language()
    lutil.log("attactv.main system language: %s" % syslanguage)
    if syslanguage in trans_language:
        language = trans_language[syslanguage]
    else:
        # If the system language is not supported in the attactv site we use the English version for the videos bye default.
        language = 'en'

lutil.log("attactv.main language selected for videos: %s" % language)

entry_url = {   'es' : 'http://www.attac.tv/todos-los-videos',
                'en' : 'http://www.attac.tv/en/all-videos',
                'fr' : 'http://www.attac.tv/fr/toutes-les-videos',
                'de' : 'http://www.attac.tv/de/alle-videos' }


# Entry point
def run():
    lutil.log("attactv.run")

    # Get params
    params = lutil.get_plugin_parms()

    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec action+"(params)"


# Main index menu
def create_index(params):
    lutil.log("attactv.create_index "+repr(params))

    # All Videos entry
    action = 'main_list'
    url = entry_url[language]
    title = translation(30014)
    lutil.log('attactv.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url)

    # Search
    action = 'search'
    url   = ''
    title = translation(30015)
    lutil.log('attactv.create_index action=["%s"] title=["Search"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url)

    lutil.close_dir(pluginhandle, updateListing=False)

# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30015))
    if search_string:
        if language == 'es':
            params['url'] = 'http://www.attac.tv/?s=%s&lang=%s' % (lutil.get_url_encoded(search_string), language)
        else:
            params['url'] = 'http://www.attac.tv/%s/?s=%s&lang=%s' % (language, lutil.get_url_encoded(search_string), language)
        lutil.log("attactv.search Value of search url: %s" % params['url'])
        return main_list(params)
    else:
        return lutil.close_dir(pluginhandle)


# Main menu
def main_list(params):
    lutil.log("attactv.main_list "+repr(params))

    # Loads the web page from attac.tv with the video list.
    page_url = params.get("url")
    reset_cache = params.get("reset_cache")

    buffer_web = lutil.carga_web(page_url)

    pattern_videos = '<a href="([^"]*?)" rel="bookmark" title="Permanent Link: ([^"]*?)"><img width="[^"]*?" height="[^"]*?" src="([^"]*?)" class="attachment-miniatura wp-post-image" alt="[^"]*?" title="[^"]*?" /></a>'
    pattern_video_excerpt = '<div id="feature-video-excerpt">'
    pattern_page_num = '/page/([0-9]+)'
    pattern_prevpage = '<a class="prev page-numbers" href="([^"]*?)">'
    pattern_nextpage = '<a class="next page-numbers" href="([^"]*?)">'
    pattern_lastpage_num = "<a class='page-numbers' href='[^']*?'>([^<]*?)</a>"
    pattern_featured = '<h1><a href="([^"]*?)" rel="bookmark">([^<]*?)</a></h1>'

    # We check that there is no empty search result:
    if lutil.find_first(buffer_web, pattern_video_excerpt):
        lutil.log("attactv.main_list We have found an empty search result page page_url: %s" % page_url)
        lutil.close_dir(pluginhandle)
        return

    # We must setup the previous page entry from the second page onwards.
    prev_page_url  = lutil.find_first(buffer_web, pattern_prevpage)
    if prev_page_url:
        prev_page_url = prev_page_url.replace('&#038;', '&') # Fixup prev_page on search.
        prev_page_num = lutil.find_first(prev_page_url, pattern_page_num)
        reset_cache = "yes"
        lutil.log("attactv.main_list Value of prev_page_url: %s" % prev_page_url)
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30013), prev_page_num), url=prev_page_url, reset_cache=reset_cache)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    # Check for featured video in search result as first video in list.
    for featured_video, featured_title in lutil.find_multiple(buffer_web, pattern_featured):
        title = featured_title.replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&').strip()  # Cleanup the title.
        url = featured_video
        lutil.log('Featured video in search result: URL: "%s" Title: "%s"' % (url, title))
        lutil.addLink(action="play_video", title=title, url=url)


    # Extract video items from the html content
    videolist = lutil.find_multiple(buffer_web,pattern_videos)

    for url, title, thumbnail in videolist:
        title = title.replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&').strip()  # Cleanup the title.
        lutil.log('Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))

        plot = title # The description only appears when we load the link, so a this point we copy the description with the title content.
        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, plot=plot, url=url,thumbnail=thumbnail)

    # Here we get the next page URL to add it at the end of the current video list page.
    next_page_url = lutil.find_first(buffer_web, pattern_nextpage)
    if next_page_url:
        next_page_num = lutil.find_first(next_page_url, pattern_page_num)
        last_page = lutil.find_multiple(buffer_web, pattern_lastpage_num)[-1]
        next_page_url = next_page_url.replace('&#038;', '&') # Fixup next_page on search.
        lutil.log('Value of next page: "(%s/%s)" next_page_url: "%s"' % (next_page_num, last_page, next_page_url))
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), next_page_num, last_page), url=next_page_url, reset_cache=reset_cache)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This funtion search into the URL link to get the video link from the different sources.
# Right now it can play the videos from the following sources: Youtube, Vimeo, Dailymotion, and KontextTV
def play_video(params):
    lutil.log("attactv.play "+repr(params))

    # Here we define the list of video sources supported.
    video_sources = ('dailymotion', 'youtube', 'vimeo', 'kontexttv', 'wsftv')
    buffer_link = lutil.carga_web(params.get("url"))
    for  source in video_sources:
        video_url = eval("get_playable_%s_url(buffer_link)" % source)
        if video_url:
            try:
                return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
            except:
                lutil.log('attactv.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
                return lutil.showWarning(translation(30012))
        elif video_url is False:
            lutil.log('attactv.play ERROR False: we cannot reproduce this video URL: "%s"' % video_url)
            return lutil.showWarning(translation(30012))

    lutil.log('attactv.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011))


# This function try to get a Youtube playable URL from the weblink and returns it ready to call the Youtube plugin.
def get_playable_youtube_url(html):
    youtube_video_patterns = (
            ('<param name="movie" value="[htps:]*?//www.youtube.com/v/([0-9A-Za-z_-]{11})', 'youtube1'),
            (' src="[htps:]*?//www.youtube.com/embed/([0-9A-Za-z_-]{11})',                  'youtube2'),
            )

    for video_pattern, pattern_name in youtube_video_patterns:
        video_id = lutil.find_first(html, video_pattern)
        if video_id:
            lutil.log("attactv.play: We have found this Youtube video with pattern %s: %s and let's going to play it!" % (pattern_name, video_id))
            video_url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + video_id
            return video_url

    return ""


# This function try to get a Vimeo playable URL from the weblink and returns it ready to play it.
def get_playable_vimeo_url(html):
    video_quality_pattern = '"profile":[0-9]+,"width":([0-9]+),.*?,"url":"([^"]*?)"'
    quality_list          = ('640', '720', '480', '320', '960', '1280', '1920')
    vimeo_video_patterns  = (
        (' value="[htps:]*?//vimeo.com/moogaloop.swf\?clip_id=([0-9]+)', 'vimeo1'),
        ('<a href="[htps:]*?//vimeo.com/([0-9]+)">',                     'vimeo2'),
        (' src="[htps:]*?//player.vimeo.com/video/([0-9]+)',             'vimeo3'),
        )

    for video_pattern, pattern_name in vimeo_video_patterns:
        video_id = lutil.find_first(html, video_pattern)
        if video_id:
            lutil.log("attactv.play: We have found this Vimeo video with pattern %s: %s and let's going to play it!" % (pattern_name, video_id))
            video_info_url = 'https://player.vimeo.com/video/' + video_id
            buffer_link    = lutil.carga_web(video_info_url)
            video_options  = dict((quality, video) for quality, video in lutil.find_multiple(buffer_link, video_quality_pattern))
            lutil.log("attactv.play: list of video options: "+repr(video_options))
            for quality in quality_list:
                if quality in video_options:
                    return video_options.get(quality)
            else:
                if len(video_options):
                    lutil.log("attactv.play: this Vimeo video hasn't got an standard resolution!")
                    return video_options.get(video_options.keys()[0])
                else:
                    return False

    return ""


# This function try to get a KontextTV playable URL from the weblink and returns it ready to play it directly.
def get_playable_kontexttv_url(html):
    pattern_kontexttv = '[htp:]*?(//kontext-tv.org/videos/.*?mp4)'

    video_url = lutil.find_first(html, pattern_kontexttv)
    if video_url:
        lutil.log("attactv.play: We have found this KontextTV video: http:%s and let's going to play it!" % video_url)
        # This is a hack to fix the lack of the "http:" sometimes into the video URL on the HTML code.
        return "http:" + video_url

    return ""

# This function try to get a World Social Forum TV playable URL from the weblink and returns it ready to play it directly.
def get_playable_wsftv_url(html):
    wsftv_patterns = (" src='[htps:]*?(//wsftv.net/[^']*?)'", " src='[htps:]*?(//www.wsftv.net/[^']*?)'")
    wsftv_video_pattern = "'clip'[: ]+'(http[^']*?)'"

    for pattern_wsftv in wsftv_patterns:
        wsftv_url = lutil.find_first(html, pattern_wsftv)
        if wsftv_url:
            # This is a hack to fix the lack of the "http:" sometimes into the video URL on the HTML code.
            wsftv_url = "http:" + wsftv_url
            lutil.log("attactv.play: We have found a WSFTV video with URL: '%s'" % wsftv_url)
            buffer_link = lutil.carga_web(wsftv_url)
            video_url = lutil.find_first(buffer_link, wsftv_video_pattern)
            if video_url:
                lutil.log("attactv.play: We have found this WSFTV video: '%s' and let's going to play it!" % video_url)
                return video_url
            else:
                return False

    return ""


# This function try to get a Dailymotion playable URL from the weblink and returns it ready to play it directly.
def get_playable_dailymotion_url(html):
    pattern_dailymotion   = ' src="[htp:]*?(//www.dailymotion.com/embed/video/[0-9a-zA-Z]+)'
    video_quality_pattern = '"([0-9]+)":\[[^]]*?{"type":"video\\\/mp4","url":"([^"]+?)"'
    quality_list          = ('480', '720', '380', '240')

    daily_url = lutil.find_first(html, pattern_dailymotion)
    if daily_url:
        # This is a hack to fix the lack of the "http:" sometimes into the video URL on the HTML code.
        daily_url = "http:" + daily_url
        lutil.log("attactv.play: We have found a Dailymotion video with URL: '%s'" % daily_url)
        buffer_link = lutil.carga_web(daily_url)
        video_options  = dict((quality, video) for quality, video in lutil.find_multiple(buffer_link, video_quality_pattern))
        lutil.log("attactv.play: list of video options: "+repr(video_options))
        for quality in quality_list:
            if quality in video_options:
                video_url = video_options.get(quality).replace('\\','')
                lutil.log("attactv.play: We have found this Dailymotion video: '%s' and let's going to play it!" % video_url)
                return video_url
        else:
            return False

    return ""


run()
