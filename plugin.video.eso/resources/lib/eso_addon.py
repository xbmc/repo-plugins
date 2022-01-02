# -*- coding: utf-8 -*-

'''
   KODI ESO video add-on.
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

   This is the first trial of the ESO video add-on for KODI.
   This add-on gets the videos from ESO web site and shows them properly ordered.
   You can choose the preferred subtitled language for the videos, if it is available.
   This plugin depends on the lutil library functions.
'''

import resources.lib.lutil as lutil

pluginhandle = lutil.get_plugin_handle()
plugin_id = 'plugin.video.eso'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting("debug"))
translation = settings.getLocalizedString
root_dir = settings.getAddonInfo('path')
lutil.set_fanart_file(root_dir)
st_release = settings.getSetting('version')
current_release = settings.getAddonInfo('version')
sort_url_param = '' if settings.getSetting("rated") == "true" else '?sort=-release_date'
update_settings = False

# This is to make it sure that settings are correctly setup on every addon update or on first run.
if not st_release:
    lutil.log("eso Warning: First run. Update settings.")
    settings.openSettings()
    settings.setSetting('version', current_release)
elif st_release != current_release:
    lutil.log("eso Warning: updated release. Check for update settings.")
    if update_settings:
        settings.openSettings()
    settings.setSetting('version', current_release)

# Gets the quality for videos from settings
try:
    quality = int(settings.getSetting('quality'))
except:
    settings.setSetting('quality', '0')
    quality = 0

lutil.log('eso quality setup to "%s"' % ('SD', 'HD', 'UltraHD')[quality])

eso_url  = 'http://www.eso.org'
space_url = 'http://www.spacetelescope.org'

# Entry point
def run():
    lutil.log("eso.run")

    # Get params
    params = lutil.get_plugin_parms()

    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec(action+"(params)")


# Main menu
def create_index(params):
    lutil.log("eso.create_index "+repr(params))

    action = 'main_list'

    # All Videos entry
    url =  params.get("url", 'http://www.eso.org/public/videos/list/1/') + sort_url_param
    title = translation(30107)
    genre = 'All the Videos'
    lutil.log('eso.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    array_index = 0 if eso_url in url else 1
    root_url = (eso_url, space_url)[array_index]
    buffer_web = lutil.carga_web(url)
    pattern_genre= ('<a href="(/public/videos/archive/category/[^"]+)">([^<]+)</a>', '<a href="(/videos/archive/category/[^"]+)">([^<]+)</a>')[array_index]

    # Category list
    # This is a hack to avoid repeat the category list at the same time it uses the old order list.
    category_list = []
    for genre_url, genre_title in lutil.find_multiple(buffer_web, pattern_genre):
        url = '%s%s%s' % (root_url, genre_url, '' if 'sort=' in genre_url else sort_url_param)
        title = genre_title.strip().replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&')  # Cleanup the title.
        if title not in category_list:
            category_list.append(title)
            lutil.log('eso.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
            lutil.addDir(action=action, title=title, url=url, genre=title)

    # Spacetelescope web site
    if root_url == eso_url:
        action = 'create_index'
        url = 'http://www.spacetelescope.org/videos/'
        title = 'Hubble Space Telescope'
        lutil.log('eso.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
        lutil.addDir(action=action, title=title, url=url, genre=title)

    # Search
    action = 'search'
    url   = ('http://www.eso.org/public/videos/?search=', 'http://www.spacetelescope.org/videos/?search=')[array_index]
    title = translation(30104)
    genre = 'Search'
    lutil.log('eso.create_index action=["%s"] title=["Search"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=False)


# Main list menu
def main_list(params):
    lutil.log("eso.main_list "+repr(params))

    # Loads the web page from ESO with the video list.
    page_url = params.get("url")
    reset_cache = params.get("reset_cache")
    genre = params.get("genre")
    array_index = 0 if eso_url in page_url else 1
    root_url = (eso_url, space_url)[array_index]

    buffer_web = lutil.carga_web(page_url)

    # Extract video items from the html content
    pattern_nextpage    = '<a href="([^"]*?)">Next</a>'
    pattern_prevpage    = '<a href="([^"]*?)">Previous</a>'
    pattern_lastpage    = '<a href="[^"]*?">([0-9]+)</a>'
    pattern_pagenum     = '/([0-9]+)/'
    pattern_videos      = ('</span><img src="([^"]+)" class="[^"]+" alt="([^"]+)">.*?<a href="(/public/videos/[^"]*?)">',
                           '</span><img src="([^"]+)" class="[^"]+" alt="([^"]+)">.*?<a href="(/videos/[^"]*?)">')[array_index]

    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    # We must setup the previous page entry from the second page onwards.
    prev_page_url = lutil.find_first(buffer_web, pattern_prevpage)
    if prev_page_url:
        prev_page = lutil.find_first(prev_page_url, pattern_pagenum)
        lutil.log('eso.main_list Value of prev_page: %s prev_page_url: "%s%s"' % (prev_page, root_url, prev_page_url))
        prev_page_url = "%s%s" % (root_url, prev_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        reset_cache = "yes"
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30106), prev_page), url=prev_page_url, reset_cache=reset_cache, genre=genre)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    for thumbnail, title, video_link in lutil.find_multiple(buffer_web, pattern_videos):
        video_info     = {}
        url            = '%s%s' % (root_url, video_link)
        if not thumbnail.startswith('http'):
            thumbnail  = '%s%s' % (root_url, thumbnail)
        title          = title.strip().replace('&quot;', '"').replace('&#39;', '´').replace('&amp;', '&')  # Cleanup the title.
        video_info['Genre']   = genre
        video_info['Plot']    = title
        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, url=url, thumbnail=thumbnail, video_info=video_info)

    # Here we get the next page URL to add it at the end of the current video list page.
    next_page_url = lutil.find_first(buffer_web, pattern_nextpage)
    if next_page_url:
        last_page = lutil.find_multiple(buffer_web, pattern_lastpage)[-1]
        next_page = lutil.find_first(next_page_url, pattern_pagenum)
        lutil.log('eso.main_list Value of next_page: %s last_page: %s next_page_url: "%s%s"' % (next_page, last_page, root_url, next_page_url))
        next_page_url = "%s%s" % (root_url, next_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), next_page, last_page), url=next_page_url, reset_cache=reset_cache, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30105))
    if search_string:
        params['url'] += lutil.get_url_encoded(search_string) + sort_url_param.replace('?', '&')
        lutil.log("eso.search Value of search url: %s" % params['url'])
        return main_list(params)

    return lutil.close_dir(pluginhandle)


# This function search into the URL link to get the video link from the different sources.
def play_video(params):
    lutil.log("eso.play "+repr(params))

    page_url = params.get("url")
    buffer_link = lutil.carga_web(page_url)
    pattern_video = '<span class="archive_dl_text"><a href="([^"]*?)"'
    quality_list = { 'UltraHD' : 'ultra_hd/', 'HD' : 'hd_and_apple', 'SD': 'medium_podcast' }

    video_list = [url for url in lutil.find_multiple(buffer_link, pattern_video) if not url.endswith(('zip','srt','pdf','mxf','wav'))]
    lutil.log("eso.play video list"+repr(video_list))
    video_options = dict((vquality, url) for url in video_list for vquality in quality_list.keys() if quality_list[vquality] in url)
    lutil.log("eso.play video options"+repr(video_options))

    video_url = video_options.get('%s' % ('SD', 'HD', 'UltraHD')[quality], '') or video_options.get('SD', '') or video_list[0] if len(video_list) else ''
    if video_url:
        if video_url.startswith('//'):
            video_url = "%s%s" % ('http:', video_url)
        elif video_url.startswith('/'):
            root_url = eso_url if eso_url in page_url else space_url
            video_url = "%s%s" % (root_url, video_url)
        try:
            lutil.log("eso.play: We have found this video: '%s' and let's going to play it!" % video_url)
            return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
        except:
            lutil.log('eso.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
            return lutil.showWarning(translation(30012))
    else:
        lutil.log('eso.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
        return lutil.showWarning(translation(30011))


run()
