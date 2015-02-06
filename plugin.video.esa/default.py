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
root_dir = settings.getAddonInfo('path')
lutil.set_fanart_file(root_dir)
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

show_fanart = settings.getSetting('show_fanart') == 'true'

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

root_url = 'http://www.esa.int'


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
    lutil.log("esa.create_index "+repr(params))

    action = 'main_list'

    # All Videos entry
    url = 'http://www.esa.int/spaceinvideos/content/search?SearchText=&result_type=videos_online&sortBy=%s' % sort_method
    title = translation(30107)
    genre = 'All the Videos'
    lutil.log('esa.create_index action=["%s"] title=["All the Videos"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    # Euronews
    url   = 'http://www.esa.int/spaceinvideos/content/search?SearchText=&result_type=euronews&sortBy=published'
    title = 'Euronews'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url, genre=title)

    # Earth from Space
    url   = 'http://www.esa.int/spaceinvideos/content/search?SearchText=%22Earth+from+Space%3A%22&SearchButton=Go'
    title = 'Earth from Space'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url, genre=title)

    # Science@ESA
    url   = 'http://www.esa.int/spaceinvideos/content/search?SearchText=%22Science@ESA%3A%22&sortBy=published&SearchButton=Go'
    title = 'Science@ESA'
    lutil.log('esa.create_index action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
    lutil.addDir(action=action, title=title, url=url, genre=title)

    # Other Categories
    action = 'other_categories'
    url = ''
    title = translation(30108)
    genre = 'Other Categories'
    lutil.log('esa.create_index action=["%s"] title=["Other Categories"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    # Search
    action = 'search'
    url   = ''
    title = translation(30104)
    genre = 'Search'
    lutil.log('esa.create_index action=["%s"] title=["Search"] url=["%s"]' % (action, url))
    lutil.addDir(action=action, title=title, url=url, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=False)

# Other Categories menu
def other_categories(params):
    lutil.log("esa.other_categories "+repr(params))

    action = 'main_list'
    page_url = 'http://www.esa.int/spaceinvideos/Videos'
    buffer_web = lutil.carga_web(page_url)

    category_pattern = '<a href="(/spaceinvideos/Directorates/[^"]*?)">([^<]*?)</a>'

    for category_link, title in lutil.find_multiple(buffer_web, category_pattern):
        url = '%s%s/(sortBy)/%s' % (root_url, category_link, sort_method)
        title = title.replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&')  # Cleanup the title.
        lutil.log('esa.other_categories action=["%s"] title=["%s"] url=["%s"]' % (action, title, url))
        lutil.addDir(action=action, title=title, url=url, genre=title)

    lutil.close_dir(pluginhandle, updateListing=False)


# Main list menu
def main_list(params):
    lutil.log("esa.main_list "+repr(params))

    # Loads the web page from ESA with the video list.
    page_url = params.get("url")
    reset_cache = params.get("reset_cache")
    genre = params.get("genre")

    buffer_web = lutil.carga_web(page_url)
    
    # Extract video items from the html content
    pattern_currentpage = '<span class="current">([^<]*?)</span>'
    pattern_page_url    = '^%s([^\?]+)'
    pattern_nextpage    = '<span class="next"><a href="([^"]*?)">'
    pattern_prevpage    = '<span class="previous"><a href="([^"]*?)">'
    pattern_last        = '<span class="other"><a href="[^"]*?">([^<]+)</a></span>'
    pattern_videos      = '<div class="psr_item_grid">(.*?)</div>'
    pattern_videolink   = '<a href="([^"]*?)"'
    pattern_thumbnail   = '<img src="([^"]*?)"'
    pattern_title       = '<span class="line2hell">([^<]+)</span>'
    pattern_date        = '<span class="date">([^<]*?)</span>'
    pattern_year        = '([0-9]{4})'

    lutil.set_content_list(pluginhandle, 'tvshows')
    lutil.set_plugin_category(pluginhandle, genre)

    page_current        = lutil.find_first(buffer_web, pattern_currentpage) or '1'
    page_url_pref       = lutil.find_first(page_url, pattern_page_url % root_url)

    # We must setup the previous page entry from the second page onwards.
    if page_current != '1':
        prev_page_url = lutil.find_first(buffer_web, pattern_prevpage)
        lutil.log('esa.main_list Value of current_page_url: "%s"' % page_url)
        prev_page_pref = lutil.find_first(prev_page_url, pattern_page_url % '')
        prev_page_url = page_url.replace(page_url_pref, prev_page_pref)
        reset_cache = "yes"
        lutil.addDir(action="main_list", title="<< %s (%s)" % (translation(30106), (int(page_current) - 1)), url=prev_page_url, reset_cache=reset_cache, genre=genre)

    # This is to force ".." option to go back to main index instead of previous page list.
    updateListing = reset_cache == "yes"

    videolist = lutil.find_multiple(buffer_web, pattern_videos)

    for video_entry in videolist:
        video_info             = {}
        video_link             = lutil.find_first(video_entry, pattern_videolink)
        thumbnail_link         = lutil.find_first(video_entry, pattern_thumbnail)
        title                  = lutil.find_first(video_entry, pattern_title)
        title                  = title.replace('&quot;', '"').replace('&#039;', '´').replace('&amp;', '&')  # Cleanup the title.
        date                   = lutil.find_first(video_entry, pattern_date).strip().replace('&nbsp;', '')
        if date:
            video_info['Year'] = lutil.find_first(date, pattern_year)
            title              = '%s (%s)' % (title, date)
        url                    = '%s%s' % (root_url, video_link)
        thumbnail              = '%s%s' % (root_url, thumbnail_link)
        video_info['Genre']    = genre
        video_info['Plot']     = title # The description only appears when we load the link.
        lutil.log('esa.main_list Videolist: URL: "%s" Title: "%s" Thumbnail: "%s"' % (url, title, thumbnail))

        # Appends a new item to the xbmc item list
        lutil.addLink(action="play_video", title=title, url=url, thumbnail=thumbnail, video_info=video_info, show_fanart=show_fanart)
 
    # Here we get the next page URL to add it at the end of the current video list page.
    next_page_url = lutil.find_first(buffer_web, pattern_nextpage)
    if next_page_url:
        next_page_pref = lutil.find_first(next_page_url, pattern_page_url % '')
        last_page      = lutil.find_multiple(buffer_web, pattern_last)[-1] or ''
        lutil.log("esa.main_list Value of last_page: %s" % last_page)
        lutil.log('esa.main_list Value of current_page_url: "%s"' % page_url)
        next_page_url = page_url.replace(page_url_pref, next_page_pref)
        lutil.addDir(action="main_list", title=">> %s (%s/%s)" % (translation(30010), int(page_current) + 1, last_page), url=next_page_url, reset_cache=reset_cache, genre=genre)

    lutil.close_dir(pluginhandle, updateListing=updateListing)


# This function performs a search through all the videos catalogue.
def search(params):
    search_string = lutil.get_keyboard_text(translation(30105))
    if search_string:
        params['url'] = 'http://www.esa.int/spaceinvideos/content/search?SearchText=%s&SearchButton=Go&sortBy=%s' % (lutil.get_url_encoded(search_string), sort_method)
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

    pattern_video = "file: '(http[^']*?)'"
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
