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
   This plugins depends as well of external plugins: youtube, vimeo and bliptv from TheCreative.
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
language = language_list[int(language_id)]

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
        main_list(params)
    else:
        action = params.get("action")
        exec action+"(params)"
    

# Main menu
def main_list(params):
    lutil.log("attactv.main_list "+repr(params))

    # On the first page, pagination parameters are fixed per language with the "all the videos" list.
    if params.get('url') is None:
        params['url'] = entry_url[language] 

    # Loads the web page from attac.tv with the video list.
    buffer_web = lutil.carga_web(params.get("url"))
    
    # Extract video items from the html content
    pattern_videos = '<a href="([^"]*?)" rel="bookmark" title="Permanent Link: ([^"]*?)"><img width="[^"]*?" height="[^"]*?" src="([^"]*?)" class="attachment-miniatura wp-post-image" alt="[^"]*?" title="[^"]*?" /></a>'
    videolist = lutil.find_multiple(buffer_web,pattern_videos)

    for url, title, thumbnail in videolist:
        title = title.replace('&quot;', '"').replace('&#039;', '´')  # Cleanup the title.
        lutil.log('Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))
        
        plot = title # The description only appears when we load the link, so a this point we copy the description with the title content.
        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, plot=plot, url=url,thumbnail=thumbnail)
 
    # Here we get the next page URL to add it at the end of the current video list page.
    pattern_nextpage = '<a class="next page-numbers" href="([^"]*?)">'
    next_page_url = lutil.find_first(buffer_web, pattern_nextpage)
    if next_page_url:
        lutil.log("Value of next_page_url: %s" % next_page_url)
        lutil.addDir(action="main_list", title=">> %s" % translation(30010), url=next_page_url)

    lutil.close_dir(pluginhandle)


# This funtion search into the URL link to get the video link from the different sources.
# Right now it can play the videos from the following sources: Youtube, Vimeo, BlipTV, and KontextTV
def play_video(params):
    lutil.log("attactv.play "+repr(params))

    # Here we define the list of video sources supported.
    video_sources = ('youtube', 'vimeo', 'bliptv', 'kontexttv', 'dailymotion')
    buffer_link = lutil.carga_web(params.get("url"))
    for  source in video_sources:
        video_url = eval("get_playable_%s_url(buffer_link)" % source)
        if video_url:
            try:
                return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
            except:
                lutil.log('attactv.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
                return lutil.showWarning(translation(30012))

    lutil.log('attactv.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011))


# This function try to get a Youtube playable URL from the weblink and returns it ready to call the Youtube plugin.
def get_playable_youtube_url(html):
    pattern_youtube1 = '<param name="movie" value="http://www.youtube.com/v/([0-9A-Za-z_-]{11})[^>]+>'
    pattern_youtube2 = ' src="http://www.youtube.com/embed/([0-9A-Za-z_-]{11})"'

    video_id = lutil.find_first(html, pattern_youtube1)
    if video_id:
        lutil.log("attactv.play: We have found this Youtube video with pattern1: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    video_id = lutil.find_first(html, pattern_youtube2)
    if video_id:
        lutil.log("attactv.play: We have found this Youtube video with pattern2: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    return ""


# This function try to get a Vimeo playable URL from the weblink and returns it ready to call the Vimeo plugin.
def get_playable_vimeo_url(html):
    pattern_vimeo1 = ' value="http://vimeo.com/moogaloop.swf\?clip_id=([0-9]+)'
    pattern_vimeo2 = '<a href="http://vimeo.com/([0-9]+)">'
    pattern_vimeo3 = ' src="http://player.vimeo.com/video/([0-9]+)'

    video_id = lutil.find_first(html, pattern_vimeo1)
    if video_id:
        lutil.log("attactv.play: We have found this Vimeo video with pattern1: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    video_id = lutil.find_first(html, pattern_vimeo2)
    if video_id:
        lutil.log("attactv.play: We have found this Vimeo video with pattern2: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    video_id = lutil.find_first(html, pattern_vimeo3)
    if video_id:
        lutil.log("attactv.play: We have found this Vimeo video with pattern3: %s and let's going to play it!" % video_id)
        video_url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + video_id
        return video_url

    return ""


# This function try to get a BlipTV playable URL from the weblink and returns it ready to call the BlipTV plugin.
def get_playable_bliptv_url(html):
    pattern_bliptv1 = '<iframe src="(http://blip.tv/play/[0-9A-Za-z_-]+.html)'
    pattern_bliptv2 = '<embed src="(http://blip.tv/play/[^"]*?)"'
    pattern_blipid  = 'file=http%3A%2F%2Fblip.tv%2Frss%2Fflash%2F([0-9]+)'

    iframe_url = lutil.find_first(html, pattern_bliptv1)
    if iframe_url:
        lutil.log("attactv.play: found BlipTV video with pattern1 URL: %s" % iframe_url)
        buffer_redirect = lutil.get_redirect(iframe_url)
        video_id = lutil.find_first(buffer_redirect, pattern_blipid)
        if video_id:
            lutil.log("attactv.play: We have found this BlipTV video: %s and let's going to play it!" % video_id)
            video_url = "plugin://plugin.video.bliptv/?path=/root/video&action=play_video&videoid=" + video_id
            return video_url
    
    embed_url = lutil.find_first(html, pattern_bliptv2)
    if embed_url:
        lutil.log("attactv.play: found BlipTV video with pattern2 URL: %s" % embed_url)
        buffer_redirect = lutil.get_redirect(embed_url)
        video_id = lutil.find_first(buffer_redirect, pattern_blipid)
        if video_id:
            lutil.log("attactv.play: We have found this BlipTV video: %s and let's going to play it!" % video_id)
            video_url = "plugin://plugin.video.bliptv/?path=/root/video&action=play_video&videoid=" + video_id
            return video_url
    
    return ""
        

# This function try to get a KontextTV playable URL from the weblink and returns it ready to play it directly.
def get_playable_kontexttv_url(html):
    pattern_kontexttv = '(http://www.kontext-tv.de/sites/default/files/.*?flv)'

    video_url = lutil.find_first(html, pattern_kontexttv)
    if video_url:
        lutil.log("attactv.play: We have found this KontextTV video: %s and let's going to play it!" % video_url)
        return video_url

    return ""


# This function try to get a Dailymotion playable URL from the weblink and returns it reay to play it directly.
def get_playable_dailymotion_url(html):
    pattern_dailymotion = ' src="http://www.dailymotion.com/embed/video/([^"]*?)"'
    #pattern_daily_video = '"hd720URL":"(.+?)"'
    pattern_daily_video = '"hqURL":"(.+?)"'

    video_id = lutil.find_first(html, pattern_dailymotion)
    if video_id:
        lutil.log("attactv.play: We have found a Dailymotion video with id: '%s'" % video_id)
        daily_url = "http://www.dailymotion.com/sequence/%s" % video_id
        buffer_link = lutil.carga_web_dailymotion(daily_url)
        video_url = lutil.find_first(buffer_link, pattern_daily_video)
        if video_url:
            video_url = video_url.replace('\\','')
            lutil.log("attactv.play: We have found this Dailymotion video: '%s' and let's going to play it!" % video_url)
            return video_url

    return ""
        

run()
