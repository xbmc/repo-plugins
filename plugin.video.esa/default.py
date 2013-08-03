# -*- coding: utf-8 -*-

'''
   XBMC ESA video add-on.
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
   
   This is the first trial of the ESA video add-on for XBMC.
   This add-on gets the videos from ESA web site and shows them properly ordered.
   You can choose the preferred language for the videos, if it is available.
   This plugin depends on the lutil library functions.
'''

import lutil

pluginhandle = int(sys.argv[1])
plugin_id = 'plugin.video.esa'

settings = lutil.get_plugin_settings(plugin_id)
lutil.set_debug_mode(settings.getSetting("debug"))
translation = settings.getLocalizedString
language_id = settings.getSetting("language")

# Language options selected from add-on settings.
language_list = ('system', 'cz', 'en', 'es', 'fr', 'de', 'gr', 'it', 'nl', 'pt')
sort_list = ('published', 'view_count', 'rating', 'votes')
trans_language =    {'Czech' : 'cz', 'English' : 'en', 'Spanish' : 'es',
                    'French' : 'fr', 'German' : 'de', 'Greek' : 'gr',
                    'Italian' : 'it', 'Dutch' : 'nl', 'Portuguese' : 'pt'}

# Language gets the the proper value from language_list
try:
    language = language_list[int(language_id)]
except:
    settings.openSettings()
    language_id = settings.getSetting("language")
    language = language_list[int(language_id)]

if language == 'system':
    # We need to get the system language used by the GUI.
    syslanguage = lutil.get_system_language()
    lutil.log("esa.main system language: %s" % syslanguage)
    if syslanguage in trans_language:
        language = trans_language[syslanguage]
    else:
        # If the system language is not supported by the ESA site we use the English version for the videos by default.
        language = 'en'

sort_criteria = settings.getSetting("sort")
sort_method = sort_list[int(sort_criteria)]

lutil.log("esa.main language selected for videos: %s" % language)
lutil.log("esa.main sort method selected for videos: %s" % sort_method)

root_url = 'http://spaceinvideos.esa.int'


# Entry point
def run():
    lutil.log("esa.run")
    
    # Get params
    params = lutil.get_plugin_parms()
    
    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec action+"(params)"
    

# Main menu
def create_index(params):
    lutil.log("greenpeace.create_index "+repr(params))

    action = 'main_list'

    # All Videos entry
    url = 'http://spaceinvideos.esa.int/content/search?SearchText=&result_type=videos_online&sortBy=%s' % sort_method
    title = translation(30107)
    lutil.log('esa.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url)

    # Euronews
    url   = 'http://spaceinvideos.esa.int/content/search?SearchText=&result_type=euronews&sortBy=published'
    title = 'Euronews'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url)

    # Earth from Space
    url   = 'http://spaceinvideos.esa.int/content/search?SearchText=%22Earth+from+Space%3A%22&SearchButton=Go'
    title = 'Earth from Space'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url)

    # Science@ESA
    url   = 'http://spaceinvideos.esa.int/content/search?SearchText=%22Science@ESA%3A%22&SearchButton=Go'
    title = 'Science@ESA'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url)

    # Search
    action = 'search'
    url   = ''
    title = translation(30104)
    lutil.log('esa.create_index action=["%s"] title=["Search"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url)

    lutil.close_dir(pluginhandle, updateListing=False)


# Main list menu
def main_list(params):
    lutil.log("esa.main_list "+repr(params))

    # Loads the web page from ESA with the video list.
    page_url = params.get("url")
    reset_cache = params.get("reset_cache")

    buffer_web = lutil.carga_web(page_url)
    
    # Extract video items from the html content
    pattern_videos = '<div class="psr_image arrow">[^<]+<a href="([^"]*?)">[^<]+<img src="([^"]*?)".*?<li><a href="[^"]*?">([^<]+)</a></li>'
    pattern_released = '<li>Released: ([^<]+)</li>'
    pattern_nextpage = '<span class="next"><a href="([^"]*?)">'
    pattern_next = '/content/search/\(offset\)/([0-9]+)'
    pattern_last = '<span class="other">\.\.\.</span><span class="other"><a href="[^"]*?">([^<]+)</a></span>'
    pattern_no_last = '<span class="other"><a href="[^"]*?">([^<]+)</a></span>'
    pattern_search_text = '\?SearchText=(.+)\&result_type='

    page_offset = lutil.find_first(page_url, pattern_next)

    # We must setup the previous page entry from the second page onwards.
    if page_offset:
        if page_offset == '10':
            prev_page_url = page_url.replace('/content/search/(offset)/10', '/content/search')
        else:
            prev_page_url = page_url.replace(page_offset, "%s" % (int(page_offset) - 10))

        lutil.log("esa.main_list Value of prev_page_url: %s" % prev_page_url)
        reset_cache = "yes"
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30106), (int(page_offset) / 10)), url=prev_page_url, reset_cache=reset_cache)

    # This is to force ".." option to go back to main index instead of previous page list.
    if reset_cache == "yes":
        updateListing = True
    else:
        updateListing = False

    videolist = lutil.find_multiple(buffer_web,pattern_videos)

    for video_link, thumbnail_link, title in videolist:
        title = title.replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&')  # Cleanup the title.
        url = '%s%s' % (root_url, video_link)
        thumbnail = '%s%s' % (root_url, thumbnail_link)
        lutil.log('esa.main_list Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))
        
        plot = title # The description only appears when we load the link, so a this point we copy the description with the title content.
        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, plot=plot, url=url,thumbnail=thumbnail)
 
    # Here we get the next page URL to add it at the end of the current video list page.
    next_page_url = lutil.find_first(buffer_web, pattern_nextpage)
    if next_page_url:
        next_page = lutil.find_first(next_page_url, pattern_next)
        last_page = lutil.find_first(buffer_web, pattern_last)
        if last_page == "": 
            page_arr = []
            page_arr = lutil.find_multiple(buffer_web, pattern_no_last)
            last_page = page_arr[-1]
            lutil.log("esa.main_list Value of last_page alt: %s" % last_page)

        lutil.log("esa.main_list Value of next_page_url original: %s" % next_page_url)
        next_page_url = "%s%s" % (root_url, next_page_url.replace('&amp;', '&').replace('&quot;', '"'))
        search_text = lutil.find_first(next_page_url, pattern_search_text)
        if search_text:
            encoded_text = lutil.get_url_encoded(search_text)
            lutil.log("esa.main_list Value of search_text original: '%s' encoded: '%s'" % (search_text, encoded_text))
            next_page_url = next_page_url.replace(search_text, encoded_text)

        lutil.log("esa.main_list Value of next_page_url: %s" % next_page_url)
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), int(next_page)/10 + 1, last_page), url=next_page_url, reset_cache=reset_cache)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30105))
    if search_string:
        params['url'] = 'http://spaceinvideos.esa.int/content/search?SearchText=%s&SearchButton=Go' % lutil.get_url_encoded(search_string)
        lutil.log("esa.search Value of search url: %s" % params['url'])
        return main_list(params)

    return lutil.close_dir(pluginhandle)


# This funtion search into the URL link to get the video link from the different sources.
def play_video(params):
    lutil.log("esa.play "+repr(params))

    buffer_link = lutil.carga_web(params.get("url"))
    if language != 'en':
        pattern_lang = '<li><a href="([^\(]*?\(lang\)/%s)" >' % language
        video_link = lutil.find_first(buffer_link, pattern_lang)
        if video_link:
            lang_url = '%s%s' % (root_url, video_link)
            lutil.log("esa.play: We have found this alt video URL for '%s' language: '%s'" % (language, lang_url))
            buffer_link = lutil.carga_web(lang_url)

    pattern_video = '<a id="download_link" href="([^"]*?)"'
    video_url = lutil.find_first(buffer_link, pattern_video)
    if video_url:
        try:
            lutil.log("esa.play: We have found this video: '%s' and let's going to play it!" % video_url)
            return lutil.play_resolved_url(pluginhandle = pluginhandle, url = video_url)
        except:
            lutil.log('esa.play ERROR: we cannot reproduce this video URL: "%s"' % video_url)
            return lutil.showWarning(translation(30012))

    lutil.log('esa.play ERROR: we cannot play the video from this source yet: "%s"' % params.get("url"))
    return lutil.showWarning(translation(30011))

run()
