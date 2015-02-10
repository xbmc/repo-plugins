# -*- coding: utf-8 -*-

'''
   XBMC tv5monde plugin.
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

   This is the first trial of the tv5monde plugin for XBMC.
   This plugins gets the videos from TV5MONDE+ web site and shows them ordered by category.
   This plugin depends on the lutil library functions.
'''

import lutil

pluginhandle = int(sys.argv[1])
plugin_id = 'plugin.video.tv5monde'

settings = lutil.get_plugin_settings(plugin_id)
translation = settings.getLocalizedString

lutil.set_debug_mode(settings.getSetting("debug"))

# Entry point
def run():
    lutil.log("tv5monde.run!! handle = [" + str(pluginhandle) + "]")
    
    # Get params
    params = lutil.get_plugin_parms()
    
    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec action+"(params)"

def create_index(params):
    lutil.log("tv5monde.create_index "+repr(params))

    action = 'genre_index'
    title  = 'Les Genres'
    url    = 'http://www.tv5mondeplus.com/videos'
    lutil.log('tv5monde.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url)

    action = 'emission_index'
    title  = 'Les Emissions'
    url    = 'http://www.tv5mondeplus.com/emissions'
    lutil.log('tv5monde.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url)

    action = 'monde7_index'
    title  = 'TV5MONDE+7'
    url    = 'http://www.tv5mondeplus.com/grilles'
    lutil.log('tv5monde.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url)

    lutil.close_dir(pluginhandle)


# This function generate the video index ordered by category.
def genre_index(params):
    lutil.log("tv5monde.genre_index "+repr(params))

    url = 'http://www.tv5mondeplus.com/videos'
    buffer_html = lutil.carga_web(url)
    list_pattern = '<div id="tri-par-genre"(.+?)</ul>'
    lista_genre = lutil.find_first(buffer_html, list_pattern)
    genre_pattern = '<li><a id="([0-9]+)" [^>]+>([^<]+)<'

    for genre, label in lutil.find_multiple(lista_genre, genre_pattern):
        genre_url = 'http://www.tv5mondeplus.com/get/videos?pg=0&type=genre&sort=%s&loadpg=false&order=date' %  genre
        lutil.log('tv5monde.genre_index url=["%s"] genre=["%s"]' % (genre_url, label))
        lutil.addDir(action="genre_list", title=label, url=genre_url)

    lutil.close_dir(pluginhandle)

# This function generate the video index ordered by category.
def emission_index(params):
    lutil.log("tv5monde.emission_index "+repr(params))

    url = params.get("url")
    emi_pattern_block = '<div id="liste-emission">(.*?)</div></div>'
    emi_pattern       = '<a href="([^"]+)">([^<]+)</a>'

    buffer_html = lutil.carga_web(url)
    cacho_html = lutil.find_first(buffer_html, emi_pattern_block)
    for url, title in lutil.find_multiple(cacho_html, emi_pattern):
        url = 'http://www.tv5mondeplus.com%s' % url
        action = 'emission_first_list'
        lutil.log('tv5monde.emission_index action=["%s"] url=["%s"]' % (action, url))
        lutil.addDir(action=action, title=title, url=url)

    lutil.close_dir(pluginhandle)

# This function generate the video index ordered by category.
def monde7_index(params):
    lutil.log("tv5monde.monde7_index "+repr(params))

    url = params.get("url")
    buffer_html = lutil.carga_web(url)
    grille_pattern_block = '<ul id="grille-floater">(.*?)</ul>'
    grille_pattern ='<li name="[^"]+".*?rel="([^"]+)"><span class="titre">([^<]+)</span><span class="date">([^<]+)</span></a></li>'
    block_grille = lutil.find_first(buffer_html, grille_pattern_block)

    if block_grille:
        lista_grille = [('http://www.tv5mondeplus.com/grilles/calendar?ajx=1&pg=0&classes=%s&slot=&sig=0&onoff=1' % rel, '%s, %s' % (weekday, date)) for rel, weekday, date in lutil.find_multiple(block_grille, grille_pattern)]
        lista_grille.reverse()

        for monde7_url, label in lista_grille:
            lutil.log('tv5monde.monde7_index url=["%s"]' % monde7_url)
            lutil.addDir(action="monde7_list", title=label, url=monde7_url)

        lutil.close_dir(pluginhandle)


def emission_first_list(params):
    lutil.log("tv5monde.emission_first_list "+repr(params))

    url = params.get("url")
    nid_pattern       = '<input id="nid" type="hidden" value="([^"]+)" />'
    vid_pattern       = '<input id="vid" type="hidden" value="([^"]+)" />'
    emiid_pattern     = '<input id="emi_string" type="hidden" value="([^"]+)" />'

    mi_html = lutil.carga_web(url)
    mi_nid  = lutil.find_first(mi_html, nid_pattern)
    mi_vid  = lutil.find_first(mi_html, vid_pattern)
    mi_emi  = lutil.find_first(mi_html, emiid_pattern)
    url_query = 'http://www.tv5mondeplus.com/get/video_emi?pg=0&emi=%s&nid=%s&vid=%s' % (mi_emi, mi_nid, mi_vid)
    params['referer'] = url
    params['url'] = url_query

    return emission_list(params)


def emission_list(params):
    lutil.log("tv5monde.emission_list "+repr(params))

    url = params.get("url")
    referer = params.get("referer")

    mi_headers = {  'Accept'            : 'application/json, text/javascript, */*',
                    'Accept-Encoding'   : 'deflate',
                    'X-Requested-With'  : 'XMLHttpRequest',
                    'Referer'           :  referer,
                    'Cookie'            : 'ns_cookietest=true; ns_session=true'
                }

    buffer_html = lutil.carga_web(params.get("url"), mi_headers)
    buffer_json = lutil.get_json_dict(buffer_html)
    pattern_videos = '<a title="([^"]+)" href=".+?nid=([^"]+)"> <img src="([^"]+)".*?<p class="date">([^<]+)</p>'
    videolist = lutil.find_multiple(buffer_json['content'], pattern_videos)
    for title, videoid, thumbnail, date in videolist:
        video_url = 'http://www.tv5mondeplus.com/video-xml/get/%s' % videoid
        title = title.replace('&quot;', '"')
        fecha = lutil.limpia_fecha(date)
        lutil.log('videolist: URL: "%s" Date: "%s" Thumbnail: "%s"' % (video_url, fecha, thumbnail))

        plot = title
        lutil.addLink(action="play_video", title='%s %s' % (title, fecha), plot=plot, url=video_url, thumbnail=thumbnail)
    
    pattern_next = '<li class="item suivante hide">.+?<a rel="address:([^"]+)"'
    next_page = lutil.find_first(buffer_json['content'], pattern_next)
    if next_page:
        next_page_url = 'http://www.tv5mondeplus.com%s' % next_page
        lutil.log('next_page_url="%s"' %  next_page_url)
        lutil.addDir(action="emission_list", title=">> %s" % translation(30010), url=next_page_url, referer=referer)

    lutil.close_dir(pluginhandle)


# This function generates the list of videos available on each category, ordered by date.
def genre_list(params):
    lutil.log("tv5monde.genre_list "+repr(params))

    # Loads the list of videos of the selected category based on the json object retrieved from the server.
    mi_headers = {  'Accept'            : 'application/json, text/javascript, */*',
                    'Accept-Encoding'   : 'deflate',
                    'X-Requested-With'  : 'XMLHttpRequest',
                    'Referer'           : 'http://www.tv5mondeplus.com/videos',
                    'Cookie'            : 'ns_cookietest=true; ns_session=true'
                }

    url = params.get("url")
    buffer_html = lutil.carga_web(url, mi_headers)
    buffer_json = lutil.get_json_dict(buffer_html)
    pattern_videos = '<a title="([^"]+)" href="/video/([^/]+)/[^"]+"> <img src="([^"]+)" .*?<div class="bookmark" id="book_([0-9]+)">'
    videolist = lutil.find_multiple(buffer_json['content'], pattern_videos)

    for title, day, thumbnail, videoid in videolist:
        video_url = 'http://www.tv5mondeplus.com/video-xml/get/%s' % videoid
        title = title.replace('&quot;', '"')
        lutil.log('videolist: URL: "%s" Descripcion: "%s" Date: "%s" Thumbnail: "%s"' % (video_url, title, day, thumbnail))

        plot = title
        lutil.addLink(action="play_video", title='%s (%s)' % (title, day), plot=plot, url=video_url, thumbnail=thumbnail)
    
    if buffer_json['pager'] is not None:
        pattern_page = 'pg=([0-9]+)'
        pattern_total = '<ul class="pager" total="([0-9]+)"'
        pattern_genre = 'sort=([0-9]+)'
        last_page = int(lutil.find_first(buffer_json['pager'], pattern_total)) - 1
        current_page = int(lutil.find_first(url, pattern_page))
        if last_page > current_page:
            next_page = current_page + 1
            genre = lutil.find_first(url, pattern_genre)
            next_page_url = 'http://www.tv5mondeplus.com/get/videos?pg=%s&type=genre&sort=%s&loadpg=false&order=date' %  (next_page, genre)
            lutil.log('current_page=%s last_page=%s next_page_url="%s"' % (current_page, last_page, next_page_url))
            lutil.addDir(action="genre_list", title=">> %s" % translation(30010), url=next_page_url)

    lutil.close_dir(pluginhandle)


# This function generates the list of videos available on each day.
def monde7_list(params):
    lutil.log("tv5monde.monde7_list "+repr(params))

    # Loads the list of videos of the selected category based on the json object retrieved from the server.
    mi_headers = {  'Accept'            : 'application/json, text/javascript, */*',
                    'Accept-Encoding'   : 'deflate',
                    'X-Requested-With'  : 'XMLHttpRequest',
                    'Referer'           : 'http://www.tv5mondeplus.com/grilles',
                    'Cookie'            : 'ns_cookietest=true; ns_session=true'
                }

    url = params.get("url")
    buffer_html = lutil.carga_web(url, mi_headers)
    buffer_json = lutil.get_json_dict(buffer_html)

    pattern_videos = '<li class="item hide">.*? <div class="ivid">.*?<div class="image-tv">.*?<a href="/video/([^/]+)/.*?<img src="([^"]+)".*?<span>(.*?)</span><a href="[^>]+?>([^<]+?)<.*?<div class="bookmark" id="book_([0-9]+)">.*?</li>' 
    videolist = lutil.find_multiple(buffer_json['output'], pattern_videos)

    for date, thumbnail, time, title, videoid in videolist:
        title = title.replace('&quot;', '"')
        mi_title = '%s (%s %s)' % (title, date, time[:5])
        video_url = 'http://www.tv5mondeplus.com/video-xml/get/%s' % videoid
        lutil.log('videolist: URL: "%s" Descripcion: "%s" Thumbnail: "%s"' % (video_url, title, thumbnail))

        plot = title
        lutil.addLink(action="play_video", title=mi_title, plot=plot, url=video_url, thumbnail=thumbnail)
    
    if buffer_json['pager'] is not None:
        pattern_page = 'pg=([0-9]+)'
        pattern_total = '<ul class="pager" total="([0-9]+)"'
        pattern_class = 'classes=([0-9-]+)'
        last_page = int(lutil.find_first(buffer_json['pager'], pattern_total)) - 1
        current_page = int(lutil.find_first(url, pattern_page))
        if last_page > current_page:
            next_page = current_page + 1
            mi_class = lutil.find_first(url, pattern_class)
            next_page_url = 'http://www.tv5mondeplus.com/grilles/calendar?ajx=1&pg=%s&classes=%s&slot=&sig=0&onoff=1'  %  (next_page, mi_class)
            lutil.log('current_page=%s last_page=%s next_page_url="%s"' % (current_page, last_page, next_page_url))
            lutil.addDir(action="monde7_list", title=">> %s" % translation(30010), url=next_page_url)

    lutil.close_dir(pluginhandle)


# This function searchs on the web server (up to 2 times) in order to get the video link and then reproduces the video.
def play_video(params):
    lutil.log("tv5monde.play_video "+repr(params))

    buffer_link = lutil.carga_web(params.get("url"))
    pattern_player  = '<videoUrl>([^<]+)</videoUrl>.*?<appleStreamingUrl>([^<]*)</appleStreamingUrl>'
    smil_url, video_url = lutil.find_first(buffer_link, pattern_player)
    if video_url:
        lutil.log('tv5monde.play_video: We have found the URL of the video file: "%s" and going to play it!!' % video_url)
        return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
    else:
        lutil.log('tv5monde.play: We did not find the video file URL because it is very old. We have to load the smil URL and get the info from there: "%s"' % smil_url)
        buffer_smil = lutil.carga_web(smil_url)
        pattern_smil = '<video src="(tv5mondeplus/hq/[^"]+)"'
        video_source = lutil.find_first(buffer_smil, pattern_smil)
        if video_source:
            video_smil = 'http://dlhd.tv5monde.com/%s' % video_source
            lutil.log('tv5monde.play_video: We have found the URL of the video file: "%s" and going to play it!!' % video_smil)
            return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_smil)
        else:
            lutil.log("tv5monde.play_video: We did not find the video file URL from the smil info. We cannot play it!!")
            lutil.showWarning(translation(30011))

# This function is the entry point to the plugin execution.
run()
